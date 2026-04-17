"""Client MCP (Model Context Protocol) pour Orion CLI.

Supporte deux types de serveurs MCP :
- stdio : serveur lancé comme sous-processus (commande locale)
- http/sse : serveur distant via HTTP + SSE

Référence spec: https://spec.modelcontextprotocol.io/
"""

import asyncio
import json
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict
    server_name: str


@dataclass
class MCPServer:
    name: str
    transport: str  # "stdio" | "http"
    command: list[str] = field(default_factory=list)   # Pour stdio
    url: str = ""                                        # Pour http
    env: dict[str, str] = field(default_factory=dict)
    tools: list[MCPTool] = field(default_factory=list)
    connected: bool = False


class MCPStdioTransport:
    """Transport stdio — communique avec un serveur MCP via stdin/stdout."""

    def __init__(self, command: list[str], env: dict[str, str] | None = None):
        self.command = command
        self.env = env or {}
        self._process: subprocess.Popen | None = None
        self._request_id = 0
        self._lock = threading.Lock()

    def start(self) -> None:
        import os
        proc_env = os.environ.copy()
        proc_env.update(self.env)
        self._process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=proc_env,
        )

    def stop(self) -> None:
        if self._process:
            self._process.terminate()
            self._process = None

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def send_request(self, method: str, params: dict | None = None) -> dict:
        """Envoie une requête JSON-RPC et retourne la réponse."""
        if not self._process:
            raise RuntimeError("Transport not started")

        req_id = self._next_id()
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {},
        }

        with self._lock:
            try:
                line = json.dumps(request) + "\n"
                self._process.stdin.write(line)
                self._process.stdin.flush()
                response_line = self._process.stdout.readline()
                return json.loads(response_line)
            except (OSError, json.JSONDecodeError) as e:
                return {"error": {"message": str(e)}}

    def initialize(self) -> dict:
        return self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "orion-cli", "version": "0.1.0"},
        })

    def list_tools(self) -> list[dict]:
        resp = self.send_request("tools/list")
        return resp.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> Any:
        resp = self.send_request("tools/call", {"name": name, "arguments": arguments})
        result = resp.get("result", {})
        content = result.get("content", [])
        # Extrait le texte des content blocks
        texts = [block.get("text", "") for block in content if block.get("type") == "text"]
        return "\n".join(texts) if texts else str(result)


class MCPHTTPTransport:
    """Transport HTTP+SSE pour serveurs MCP distants."""

    def __init__(self, url: str):
        self.base_url = url.rstrip("/")
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def send_request(self, method: str, params: dict | None = None) -> dict:
        try:
            import httpx
            req_id = self._next_id()
            payload = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params or {},
            }
            with httpx.Client(timeout=15) as client:
                resp = client.post(f"{self.base_url}/mcp", json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"error": {"message": str(e)}}

    def list_tools(self) -> list[dict]:
        resp = self.send_request("tools/list")
        return resp.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> Any:
        resp = self.send_request("tools/call", {"name": name, "arguments": arguments})
        result = resp.get("result", {})
        content = result.get("content", [])
        texts = [block.get("text", "") for block in content if block.get("type") == "text"]
        return "\n".join(texts) if texts else str(result)


class MCPClient:
    """
    Client MCP Orion CLI.

    Gère plusieurs serveurs MCP et expose leurs outils comme
    des LangChain tools dynamiques.
    """

    def __init__(self):
        self._servers: dict[str, MCPServer] = {}
        self._transports: dict[str, MCPStdioTransport | MCPHTTPTransport] = {}

    def load_from_settings(self, mcp_config: dict) -> None:
        """
        Charge la config MCP depuis settings.json.

        Format attendu:
        {
          "my-server": {
            "transport": "stdio",
            "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
          },
          "remote-server": {
            "transport": "http",
            "url": "http://localhost:3000"
          }
        }
        """
        for name, cfg in mcp_config.items():
            transport = cfg.get("transport", "stdio")
            server = MCPServer(
                name=name,
                transport=transport,
                command=cfg.get("command", []),
                url=cfg.get("url", ""),
                env=cfg.get("env", {}),
            )
            self._servers[name] = server

    def connect(self, server_name: str) -> tuple[bool, str]:
        """Connecte un serveur MCP et découvre ses outils."""
        server = self._servers.get(server_name)
        if not server:
            return False, f"Server '{server_name}' not configured."

        try:
            if server.transport == "stdio":
                if not server.command:
                    return False, f"Server '{server_name}': no command configured."
                transport = MCPStdioTransport(server.command, server.env)
                transport.start()
                transport.initialize()
            elif server.transport in ("http", "sse"):
                if not server.url:
                    return False, f"Server '{server_name}': no URL configured."
                transport = MCPHTTPTransport(server.url)
            else:
                return False, f"Unknown transport: {server.transport}"

            # Découverte des outils
            raw_tools = transport.list_tools()
            server.tools = [
                MCPTool(
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                    server_name=server_name,
                )
                for t in raw_tools
            ]
            server.connected = True
            self._transports[server_name] = transport
            return True, f"Connected to '{server_name}' ({len(server.tools)} tools)"

        except Exception as e:
            return False, f"Failed to connect '{server_name}': {e}"

    def connect_all(self) -> dict[str, str]:
        """Connecte tous les serveurs configurés."""
        results = {}
        for name in self._servers:
            ok, msg = self.connect(name)
            results[name] = msg
        return results

    def disconnect(self, server_name: str) -> None:
        transport = self._transports.pop(server_name, None)
        if isinstance(transport, MCPStdioTransport):
            transport.stop()
        server = self._servers.get(server_name)
        if server:
            server.connected = False

    def disconnect_all(self) -> None:
        for name in list(self._transports.keys()):
            self.disconnect(name)

    def list_servers(self) -> list[MCPServer]:
        return list(self._servers.values())

    def list_all_tools(self) -> list[MCPTool]:
        tools = []
        for server in self._servers.values():
            if server.connected:
                tools.extend(server.tools)
        return tools

    def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Appelle un outil MCP par son nom."""
        for server_name, server in self._servers.items():
            if not server.connected:
                continue
            for tool in server.tools:
                if tool.name == tool_name:
                    transport = self._transports.get(server_name)
                    if transport:
                        return transport.call_tool(tool_name, arguments)
        return f"Error: Tool '{tool_name}' not found in any connected MCP server."

    def to_langchain_tools(self) -> list:
        """Convertit les outils MCP en LangChain tools."""
        from langchain_core.tools import StructuredTool
        lc_tools = []
        for mcp_tool in self.list_all_tools():
            # Fermeture pour capturer mcp_tool par valeur
            def make_fn(t: MCPTool):
                def fn(**kwargs) -> str:
                    return str(self.call_tool(t.name, kwargs))
                fn.__name__ = t.name
                fn.__doc__ = t.description
                return fn

            lc_tools.append(StructuredTool.from_function(
                func=make_fn(mcp_tool),
                name=f"mcp_{mcp_tool.server_name}_{mcp_tool.name}",
                description=f"[MCP:{mcp_tool.server_name}] {mcp_tool.description}",
            ))
        return lc_tools

    def status_report(self) -> str:
        """Rapport d'état pour /mcp."""
        if not self._servers:
            return "No MCP servers configured."
        lines = [f"MCP Servers ({len(self._servers)}):"]
        for name, server in self._servers.items():
            status = "connected" if server.connected else "disconnected"
            n_tools = len(server.tools) if server.connected else 0
            transport_info = server.url if server.transport == "http" else " ".join(server.command[:2])
            lines.append(f"  {name} [{status}] — {server.transport} — {transport_info} — {n_tools} tools")
            if server.connected and server.tools:
                for t in server.tools[:5]:
                    lines.append(f"    • {t.name}: {t.description[:60]}")
                if len(server.tools) > 5:
                    lines.append(f"    ... ({len(server.tools) - 5} more)")
        return "\n".join(lines)
