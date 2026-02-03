import asyncio
import json
import os
import traceback
from typing import Dict, List

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, Tool, TextContent

from eto_client import search_tours

LOG_FILE = os.path.expanduser("~/eto-tours-mcp.log")


def log(msg: str) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def build_server() -> Server:
    server = Server("eto-tours")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name="search_tours",
                description=(
                    "Принимает параметры поиска (country/city_from лучше строкой: \"Египет\", \"Москва\"), делает modsearch → несколько запросов modresult, "
                    "ждёт появления data.block и возвращает JSON."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date_from": {"type": "string"},
                        "date_to": {"type": "string"},
                        "nights": {"type": "integer"},
                        "adults": {"type": "integer"},
                        "country": {"type": ["integer", "string"]},
                        "city_from": {"type": ["integer", "string"]},
                        "referrer": {"type": "string"},
                        "session": {"type": "string"},
                        "limit": {"type": "integer"},
                        "requestid": {"type": "string"},
                        "unique_hotels": {"type": "boolean"},
                        "refresh_hotels": {"type": "boolean"},
                    },
                    "additionalProperties": True,
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict) -> CallToolResult:
        try:
            if name == "search_tours":
                result = await asyncio.to_thread(search_tours, arguments)
            else:
                result = {"success": False, "error": f"Unknown tool: {name}"}

            if isinstance(result, dict) and result.get("success") is True:
                text = json.dumps(result.get("tours", []), ensure_ascii=False, indent=2)
            else:
                text = json.dumps(result, ensure_ascii=False, indent=2)
            return CallToolResult(content=[TextContent(type="text", text=text)])
        except Exception as e:
            log(f"call_tool error: {e}\n{traceback.format_exc()}")
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))]
            )

    return server


async def main_stdio() -> None:
    server = build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="eto-tours",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main_stdio())
