"""
FastMCP server for Contaixt GraphRAG.

Exposes query, vault, and workspace tools over Streamable HTTP
so that MCP clients (Claude Desktop, Cursor, etc.) can use
Contaixt as a context source.
"""

from fastmcp import FastMCP

mcp = FastMCP(
    name="Contaixt",
    instructions=(
        "Contaixt is a GraphRAG platform. Use the provided tools to search "
        "documents, retrieve knowledge graph context, and manage workspaces "
        "and vaults. Always provide a workspace_id. Vault IDs are optional "
        "filters — omit them to search the entire workspace."
    ),
)

# Import tools and resources so decorators register on the mcp instance.
import app.mcp.resources  # noqa: F401, E402
import app.mcp.tools  # noqa: F401, E402


def get_mcp_app():
    """Return the Starlette ASGI app for mounting into FastAPI."""
    return mcp.http_app(path="/", stateless_http=True)
