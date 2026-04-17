"""Agent Orion CLI — LangGraph ReAct agent avec Ollama."""

import re
from pathlib import Path
from typing import Any, Callable, Generator, Optional, TYPE_CHECKING

# Modèles connus pour produire des balises <think>...</think>
REASONING_MODEL_PATTERNS = [
    "deepseek-r1",
    "deepseek-r2",
    "qwq",
    "qwen3",
    "skywork-o1",
    "marco-o1",
    "thinker",
    "r1-distill",
    "hunyuan",
]


def is_reasoning_model(model_name: str) -> bool:
    """Retourne True si le modèle est connu pour produire des balises <think>."""
    name = model_name.lower()
    return any(p in name for p in REASONING_MODEL_PATTERNS)

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel
else:
    BaseChatModel = Any
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from orion.config.providers import get_llm
from orion.config.settings import Settings
from orion.memory.manager import MemoryManager
from orion.mcp.client import MCPClient
from orion.session.checkpoint import CheckpointManager
from orion.session.manager import SessionManager
from orion.tools import build_tools
from orion.ui import renderer


# Fallback si IDENTITY.md est introuvable
_DEFAULT_IDENTITY = """You are Orion, a powerful AI agent running locally via Ollama.
Be direct, technical, honest, and proactive. Use tools to verify before answering.
Complete all required steps of a task before returning control to the user.
Respond in the user's language."""

SYSTEM_PROMPT_TEMPLATE = """{identity}

You have access to tools to:
- Read, write, edit, search files and directories
- Execute shell commands
- Search the web (DuckDuckGo)
- Fetch web content
- Save memories for future sessions
- Plan and track todos

After using a tool, always confirm what you did and present the result clearly in your response.
Example: "J'ai exécuté `ls -la src/` — voici le résultat : ..."
Example: "Fichier `config.py` lu. Voici son contenu : ..."
Keep confirmations brief and factual, consistent with your direct personality.

{memory_context}

Workspace: {workspace}
Current date: {date}
"""


class OrionAgent:
    """Agent principal Orion CLI — propulsé par LangGraph + Ollama."""

    def __init__(
        self,
        settings: Settings,
        workspace: Path,
        memory_manager: MemoryManager,
        session_manager: SessionManager,
        mcp_client: Optional[MCPClient] = None,
        checkpoint_manager: Optional[CheckpointManager] = None,
    ):
        self.settings = settings
        self.workspace = workspace
        self.memory_manager = memory_manager
        self.session_manager = session_manager
        self.mcp_client = mcp_client
        self.checkpoint_manager = checkpoint_manager
        self._llm: Optional[BaseChatModel] = None
        self._agent = None
        self._tools: list = []

    def _get_llm(self) -> BaseChatModel:
        """Get LLM instance using provider factory."""
        if self._llm is None:
            self._llm = get_llm(self.settings)
        return self._llm

    def _build_agent(self):
        """Construit l'agent ReAct via langgraph.prebuilt."""
        from langgraph.prebuilt import create_react_agent

        confirm_fn = None
        if self.settings.get("show_tool_confirmations", True) and not self.settings.get("auto_accept_edits", False):
            confirm_fn = renderer.confirm_tool_action

        self._tools = build_tools(
            workspace=self.workspace,
            settings=self.settings,
            memory_manager=self.memory_manager,
            confirm_fn=confirm_fn,
            checkpoint_manager=self.checkpoint_manager,
        )

        # Outils MCP additionnels
        if self.mcp_client:
            self._tools.extend(self.mcp_client.to_langchain_tools())

        llm = self._get_llm()

        self._agent = create_react_agent(
            model=llm,
            tools=self._tools,
            prompt=self._build_system_prompt(),
        )
        return self._agent

    def _load_identity(self) -> str:
        """Charge IDENTITY.md (package > global > projet, le dernier trouvé gagne)."""
        # Ordre de priorité croissante (le dernier trouvé écrase)
        candidates = [
            Path(__file__).parent.parent.parent / "IDENTITY.md",          # orion_cli/IDENTITY.md
            Path.home() / ".config" / "orion" / "IDENTITY.md",            # global
            self.workspace / "IDENTITY.md",                                # projet
        ]
        content = _DEFAULT_IDENTITY
        for path in candidates:
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8").strip()
                except OSError:
                    pass
        return content

    def _build_system_prompt(self) -> str:
        from datetime import date
        memory_ctx = self.memory_manager.load_context()
        memory_block = f"\n## Your Memory\n{memory_ctx}\n" if memory_ctx else ""
        return SYSTEM_PROMPT_TEMPLATE.format(
            identity=self._load_identity(),
            memory_context=memory_block,
            workspace=str(self.workspace),
            date=date.today().isoformat(),
        )

    def _extract_output(self, result: dict) -> tuple[str, list]:
        """
        Extrait la réponse finale et les tool calls depuis le résultat langgraph.
        result["messages"] est une liste de HumanMessage, AIMessage, ToolMessage.
        """
        messages = result.get("messages", [])
        tool_calls = []
        final_output = ""

        for msg in messages:
            if isinstance(msg, AIMessage):
                # Enregistre les tool calls intermédiaires
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_calls.append((tc["name"], tc["args"]))
                # La dernière AIMessage sans tool_call est la réponse finale
                if not msg.tool_calls and msg.content:
                    final_output = msg.content if isinstance(msg.content, str) else str(msg.content)
            elif isinstance(msg, ToolMessage):
                # Résultat d'un outil — associe au dernier tool_call enregistré
                if tool_calls:
                    tool_calls[-1] = (tool_calls[-1][0], tool_calls[-1][1], str(msg.content))

        return final_output, tool_calls

    def chat(self, user_input: str) -> str:
        """Envoie un message et retourne la réponse (mode agent ReAct complet)."""
        if self._agent is None:
            self._build_agent()

        self.session_manager.add_message("user", user_input)

        # Construit l'historique complet pour le contexte
        history = self.session_manager.get_langchain_messages()

        try:
            result = self._agent.invoke({"messages": history})
            output, tool_calls = self._extract_output(result)

            # Affiche les tool calls dans le terminal
            for tc in tool_calls:
                name = tc[0]
                args = tc[1]
                obs = tc[2] if len(tc) > 2 else ""
                renderer.print_tool_call(name, args)
                if obs:
                    renderer.print_tool_result(obs[:300])

            if not output:
                output = "(No response)"

            self.session_manager.add_message("assistant", output)
            self.session_manager.update_token_count(
                len(user_input.split()) + len(output.split())
            )
            return output

        except Exception as e:
            return f"Agent error: {e}"

    def _extract_thinking(self, content: str) -> tuple[str, str]:
        """
        Extrait le contenu <think>...</think> s'il est présent.
        Retourne (thinking, response_nettoyée).
        """
        match = re.search(r'<think>(.*?)</think>', content, re.DOTALL | re.IGNORECASE)
        if match:
            thinking = match.group(1).strip()
            response = (content[:match.start()] + content[match.end():]).strip()
            return thinking, response
        return "", content

    def _stream_with_thinking(
        self,
        llm,
        messages: list,
        on_token: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
    ) -> tuple[str, str]:
        """
        Stream tokens en séparant <think>...</think> de la réponse.
        Retourne (full_response, full_thinking).
        """
        OPEN = "<think>"
        CLOSE = "</think>"

        def _safe_len(buf: str, tag: str) -> int:
            """Nombre de caractères sûrs à émettre (évite de couper un tag partiel)."""
            for i in range(len(tag) - 1, 0, -1):
                if buf.endswith(tag[:i]):
                    return len(buf) - i
            return len(buf)

        in_think = False
        buffer = ""
        full_response = ""
        full_thinking = ""

        for chunk in llm.stream(messages):
            text = chunk.content or ""
            if not text:
                continue
            buffer += text

            while True:
                if not in_think:
                    idx = buffer.find(OPEN)
                    if idx >= 0:
                        before = buffer[:idx]
                        if before:
                            if on_token:
                                on_token(before)
                            full_response += before
                        buffer = buffer[idx + len(OPEN):]
                        in_think = True
                    else:
                        safe = _safe_len(buffer, OPEN)
                        if safe > 0:
                            emit = buffer[:safe]
                            if on_token:
                                on_token(emit)
                            full_response += emit
                            buffer = buffer[safe:]
                        break
                else:
                    idx = buffer.find(CLOSE)
                    if idx >= 0:
                        think_part = buffer[:idx]
                        if think_part:
                            if on_thinking:
                                on_thinking(think_part)
                            full_thinking += think_part
                        buffer = buffer[idx + len(CLOSE):]
                        in_think = False
                    else:
                        safe = _safe_len(buffer, CLOSE)
                        if safe > 0:
                            emit = buffer[:safe]
                            if on_thinking:
                                on_thinking(emit)
                            full_thinking += emit
                            buffer = buffer[safe:]
                        break

        # Flush du buffer restant
        if buffer:
            if in_think:
                if on_thinking:
                    on_thinking(buffer)
                full_thinking += buffer
            else:
                if on_token:
                    on_token(buffer)
                full_response += buffer

        return full_response.strip(), full_thinking.strip()

    def _repair_json(self, raw: str) -> Optional[dict]:
        """
        Tente de réparer un JSON malformé issu d'un modèle (guillemets non échappés, etc.).
        Retourne le dict parsé ou None si impossible.
        """
        import json, re

        # Essai 1 : parse direct
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            pass

        # Essai 2 : json_repair si disponible
        try:
            import json_repair  # type: ignore
            return json_repair.loads(raw)
        except Exception:
            pass

        # Essai 3 : remplacement naïf — échappe les guillemets non échappés
        # dans les valeurs de string en remplaçant " par \" sauf aux bornes JSON
        try:
            # Remplace les guillemets doubles internes dans les valeurs de strings
            fixed = re.sub(
                r'(?<=[:{,\[])\s*"(.*?)"(?=\s*[,}\]])',
                lambda m: '"' + m.group(1).replace('"', '\\"') + '"',
                raw,
                flags=re.DOTALL,
            )
            return json.loads(fixed)
        except (json.JSONDecodeError, ValueError):
            pass

        return None

    def _parse_tool_call_error(self, error_str: str) -> Optional[dict]:
        """
        Extrait et répare le JSON brut depuis un message d'erreur de type
        "error parsing tool call: raw='...', err=...".
        """
        import re
        match = re.search(r"raw='(.+?)',\s*err=", error_str, re.DOTALL)
        if not match:
            # Essai sans virgule finale (fin de chaîne)
            match = re.search(r"raw='(.+)'$", error_str, re.DOTALL)
        if match:
            raw_json = match.group(1)
            repaired = self._repair_json(raw_json)
            if repaired and isinstance(repaired, dict):
                return repaired
        return None

    def _detect_text_tool_call(self, content: str) -> Optional[dict]:
        """Détecte un appel outil émis comme JSON texte (modèles sans tool calling natif)."""
        import json

        stripped = content.strip()
        try:
            data = json.loads(stripped)
            if isinstance(data, dict):
                name = data.get("name") or data.get("tool") or data.get("function")
                args = (
                    data.get("arguments")
                    or data.get("args")
                    or data.get("parameters")
                    or {}
                )
                if name and isinstance(name, str) and isinstance(args, dict):
                    return {"name": name, "args": args}
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    def _text_tool_continuation(
        self, original_history: list, extra_messages: list, tool_map: dict
    ) -> Generator[dict, None, None]:
        """Continue la boucle ReAct manuellement après détection d'appels outil en texte."""
        import uuid
        llm = self._get_llm()
        messages = list(original_history) + extra_messages
        final_output = ""

        for _ in range(8):
            response = llm.invoke(messages)
            if not isinstance(response, AIMessage):
                break

            content = response.content if isinstance(response.content, str) else str(response.content)
            tc = self._detect_text_tool_call(content)

            if tc and tc["name"] in tool_map:
                call_id = str(uuid.uuid4())
                yield {"type": "tool_call", "id": call_id, "name": tc["name"], "args": tc["args"]}
                try:
                    result = tool_map[tc["name"]].invoke(tc["args"])
                    result_str = str(result)
                except Exception as e:
                    result_str = f"Tool error: {e}"
                yield {"type": "tool_result", "id": call_id, "name": tc["name"], "result": result_str}
                messages = messages + [
                    response,
                    ToolMessage(content=result_str, tool_call_id="fallback", name=tc["name"]),
                ]
            else:
                final_output = content
                yield {"type": "response", "content": final_output}
                break

        if not final_output:
            final_output = "(No response)"

        self.session_manager.add_message("assistant", final_output)
        self.session_manager.update_token_count(len(final_output.split()))

    def stream_events(self, user_input: str) -> Generator[dict, None, None]:
        """
        Génère des événements en temps réel pendant que l'agent travaille.

        Événements possibles :
        - {"type": "tool_call",   "id": str, "name": str, "args": dict}
        - {"type": "tool_result", "id": str, "name": str, "result": str}
        - {"type": "response",    "content": str}
        - {"type": "error",       "content": str}
        """
        if self._agent is None:
            self._build_agent()

        import uuid
        # Record the user's message and build the history used by the agent
        self.session_manager.add_message("user", user_input)
        history = self.session_manager.get_langchain_messages()
        call_id_to_name: dict = {}
        final_output = ""
        tool_map = {t.name: t for t in self._tools}
        extra_messages: list = []  # messages accumulés pour le fallback manuel
        all_stream_messages: list = []  # tous les messages du stream pour le nudge

        try:
            for chunk in self._agent.stream({"messages": history}, stream_mode="updates"):
                # ── Nœud agent (LLM) ──────────────────────────────────────
                if "agent" in chunk:
                    for msg in chunk["agent"].get("messages", []):
                        all_stream_messages.append(msg)
                        if not isinstance(msg, AIMessage):
                            continue
                        if msg.tool_calls:
                            for tc in msg.tool_calls:
                                call_id_to_name[tc["id"]] = tc["name"]
                                yield {"type": "tool_call", "id": tc["id"], "name": tc["name"], "args": tc["args"]}
                        elif msg.content:
                            content = msg.content if isinstance(msg.content, str) else str(msg.content)
                            # Extrait la réflexion <think>...</think> si présente
                            thinking, clean_content = self._extract_thinking(content)
                            if thinking and self.settings.get("show_thinking", True):
                                yield {"type": "thinking", "content": thinking}
                            effective_content = clean_content if thinking else content
                            # Fallback : détecte appel outil émis en JSON texte
                            tc = self._detect_text_tool_call(effective_content)
                            if tc and tc["name"] in tool_map:
                                call_id = str(uuid.uuid4())
                                yield {"type": "tool_call", "id": call_id, "name": tc["name"], "args": tc["args"]}
                                try:
                                    result = tool_map[tc["name"]].invoke(tc["args"])
                                    result_str = str(result)
                                except Exception as e:
                                    result_str = f"Tool error: {e}"
                                yield {"type": "tool_result", "id": call_id, "name": tc["name"], "result": result_str}
                                extra_messages.append(msg)
                                extra_messages.append(
                                    ToolMessage(
                                        content=result_str,
                                        tool_call_id=call_id,
                                        name=tc["name"],
                                    )
                                )
                            else:
                                final_output = effective_content
                                yield {"type": "response", "content": final_output}

                # ── Nœud tools (résultats) ─────────────────────────────────
                elif "tools" in chunk:
                    for msg in chunk["tools"].get("messages", []):
                        all_stream_messages.append(msg)
                        if not isinstance(msg, ToolMessage):
                            continue
                        name = call_id_to_name.get(msg.tool_call_id, "tool")
                        result_str = str(msg.content)
                        yield {"type": "tool_result", "id": msg.tool_call_id, "name": name, "result": result_str}

        except Exception as e:
            err_str = str(e)
            # Tentative de récupération sur JSON malformé (modèles comme gpt-oss:20b)
            if "error parsing tool call" in err_str:
                repaired = self._parse_tool_call_error(err_str)
                if repaired:
                    # Construit un faux tool call à partir du JSON réparé
                    name = repaired.get("name") or repaired.get("tool") or repaired.get("function")
                    args = (
                        repaired.get("arguments")
                        or repaired.get("args")
                        or repaired.get("parameters")
                        or repaired  # dernier recours : le dict entier sauf "name"
                    )
                    if isinstance(args, dict) and "name" in args:
                        args = {k: v for k, v in args.items() if k != "name"}
                    if name and name in tool_map:
                        call_id = str(uuid.uuid4())
                        yield {"type": "tool_call", "id": call_id, "name": name, "args": args}
                        try:
                            result = tool_map[name].invoke(args)
                            result_str = str(result)
                        except Exception as tool_err:
                            result_str = f"Tool error: {tool_err}"
                        yield {"type": "tool_result", "id": call_id, "name": name, "result": result_str}
                        extra_messages.append(
                            ToolMessage(content=result_str, tool_call_id=call_id, name=name)
                        )
                        # Pas de yield error — on continue
                        e = None  # type: ignore[assignment]
            if e is not None:
                final_output = f"Agent error: {e}"
                yield {"type": "error", "content": str(e)}

        # ── Continuation manuelle si appels outil textuels détectés ─────────
        if extra_messages and not final_output:
            yield from self._text_tool_continuation(history, extra_messages, tool_map)
            return  # session update géré dans _text_tool_continuation

        # ── Nudge fallback : tool calls faits mais aucune réponse finale ────
        # Certains modèles (ex: gpt-oss:20b) s'arrêtent après les tool calls
        # sans générer de synthèse. On les "nudge" directement via le LLM.
        if not final_output and call_id_to_name and all_stream_messages:
            try:
                llm = self._get_llm()
                nudge_messages = (
                    list(history)
                    + all_stream_messages
                    + [HumanMessage(content="Based on the tool results above, please provide your complete answer to the original question.")]
                )
                nudge_resp = llm.invoke(nudge_messages)
                nudge_content = nudge_resp.content if isinstance(nudge_resp.content, str) else str(nudge_resp.content)
                if nudge_content and nudge_content.strip():
                    thinking, clean_nudge = self._extract_thinking(nudge_content)
                    if thinking and self.settings.get("show_thinking", True):
                        yield {"type": "thinking", "content": thinking}
                    final_output = clean_nudge if thinking else nudge_content
                    yield {"type": "response", "content": final_output}
            except Exception:
                pass

        if not final_output:
            final_output = "(No response)"

        self.session_manager.add_message("assistant", final_output)
        self.session_manager.update_token_count(
            len(user_input.split()) + len(final_output.split())
        )

    def stream_chat(
        self,
        user_input: str,
        on_token: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Streaming token-par-token (sans tool-calling).
        Détecte et sépare les balises <think>...</think> des modèles de raisonnement.
        Chaque token de réponse est passé à on_token, chaque token de réflexion à on_thinking.
        Retourne la réponse complète (sans les balises <think>).
        """
        llm = self._get_llm()
        system = self._build_system_prompt()

        messages: list = [SystemMessage(content=system)]
        for msg in self.session_manager.get_langchain_messages():
            messages.append(msg)
        messages.append(HumanMessage(content=user_input))

        self.session_manager.add_message("user", user_input)

        full_response, _ = self._stream_with_thinking(
            llm, messages, on_token=on_token, on_thinking=on_thinking
        )

        self.session_manager.add_message("assistant", full_response)
        self.session_manager.update_token_count(
            len(user_input.split()) + len(full_response.split())
        )
        return full_response

    def reset(self) -> None:
        """Réinitialise l'agent (reload tools + prompt au prochain appel)."""
        self._agent = None
        self._llm = None

    def list_tools(self) -> list[tuple[str, str]]:
        """Retourne les outils disponibles (nom, description courte)."""
        if not self._tools:
            self._tools = build_tools(
                workspace=self.workspace,
                settings=self.settings,
                memory_manager=self.memory_manager,
                confirm_fn=None,
                checkpoint_manager=self.checkpoint_manager,
            )
        return [(t.name, t.description.split("\n")[0]) for t in self._tools]

    def get_model_info(self) -> dict:
        """Retourne les infos sur le modèle courant."""
        try:
            import ollama
            model_name = self.settings.get("model", "qwen2.5-coder:14b")
            info = ollama.show(model_name)
            return {
                "model": model_name,
                "size": getattr(info, "size", "unknown"),
                "family": getattr(info, "details", {}).get("family", "unknown") if hasattr(info, "details") else "unknown",
            }
        except Exception:
            return {"model": self.settings.get("model", "unknown")}
