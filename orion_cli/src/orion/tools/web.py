"""Outils web — web_fetch et web_search (local, sans Google API)."""

from typing import Annotated

from langchain_core.tools import tool


@tool
def web_fetch(
    url: Annotated[str, "URL à récupérer et analyser"],
    prompt: Annotated[str, "Ce que tu cherches dans la page"] = "Résume le contenu",
) -> str:
    """Récupère le contenu d'une URL et le retourne en texte brut."""
    try:
        import httpx
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; OrionCLI/1.0)",
            "Accept": "text/html,application/xhtml+xml,text/plain,*/*",
        }
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")

            if "text/html" in content_type:
                # HTML → texte brut (stripping tags basic)
                text = _html_to_text(response.text)
            else:
                text = response.text

            # Tronque si trop long
            if len(text) > 8000:
                text = text[:8000] + "\n\n[... content truncated ...]"
            return f"URL: {url}\n\n{text}"
    except Exception as e:
        return f"Error fetching {url}: {e}"


def _html_to_text(html: str) -> str:
    """Conversion HTML → texte simple sans dépendances lourdes."""
    import re
    # Supprime les scripts et styles
    html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remplace les balises de structure par des sauts de ligne
    html = re.sub(r"<(br|p|div|h[1-6]|li|tr)[^>]*>", "\n", html, flags=re.IGNORECASE)
    # Supprime toutes les balises restantes
    html = re.sub(r"<[^>]+>", "", html)
    # Décode les entités HTML basiques
    html = html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    html = html.replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'")
    # Nettoie les espaces multiples
    html = re.sub(r"\n{3,}", "\n\n", html)
    html = re.sub(r"[ \t]{2,}", " ", html)
    return html.strip()


@tool
def web_search(
    query: Annotated[str, "Requête de recherche"],
    max_results: Annotated[int, "Nombre maximum de résultats (1-10)"] = 5,
) -> str:
    """Effectue une recherche web via DuckDuckGo (100% local, sans clé API)."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return f"No results found for: {query}"
        lines = [f"Search results for: {query}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. [{r.get('title', 'No title')}]({r.get('href', '')})")
            lines.append(f"   {r.get('body', '')}\n")
        return "\n".join(lines)
    except ImportError:
        return "Error: ddgs not installed. Run: pip install ddgs"
    except Exception as e:
        return f"Search error: {e}"
