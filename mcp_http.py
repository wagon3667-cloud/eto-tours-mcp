import asyncio
import sys

from mcp_server import build_server


def _load_http_transport():
    try:
        from mcp.server.streamable_http import streamable_http_server
        return streamable_http_server
    except Exception:
        try:
            from mcp.server.sse import sse_server
            return sse_server
        except Exception:
            return None


async def main() -> None:
    transport = _load_http_transport()
    if transport is None:
        raise RuntimeError(
            "MCP HTTP transport не найден. Установи mcp с поддержкой HTTP (streamable_http/sse) или обнови пакет."
        )

    server = build_server()
    app = transport(server)

    try:
        import uvicorn
    except Exception as e:
        raise RuntimeError("uvicorn не установлен. Установи: pip install uvicorn") from e

    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")


if __name__ == "__main__":
    asyncio.run(main())
