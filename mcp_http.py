import uvicorn
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from mcp_server import build_server


class MCPASGIApp:
    def __init__(self, manager: StreamableHTTPSessionManager):
        self.manager = manager
        self._cm = None

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                msg = await receive()
                if msg["type"] == "lifespan.startup":
                    self._cm = self.manager.run()
                    await self._cm.__aenter__()
                    await send({"type": "lifespan.startup.complete"})
                elif msg["type"] == "lifespan.shutdown":
                    if self._cm:
                        await self._cm.__aexit__(None, None, None)
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        else:
            await self.manager.handle_request(scope, receive, send)


def main() -> None:
    server = build_server()
    # stateless=True, чтобы MCP-Session-Id не требовался на старте
    manager = StreamableHTTPSessionManager(server, stateless=True)
    app = MCPASGIApp(manager)
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")


if __name__ == "__main__":
    main()
