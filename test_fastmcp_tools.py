from entelechy_api import MemoryEngine
from entelechy_api.api.mcp import create_mcp_servers
import asyncio

async def test():
    memory = MemoryEngine()
    mb_server, sb_server, mb_app, sb_app = create_mcp_servers(memory)
    tools = await mb_server.list_tools()
    print("Tools:", [t.name for t in tools])
    try:
        res = await mb_server.call_tool("list_banks", {})
        print("Call tool list_banks:", res)
    except Exception as e:
        print("Error calling tool:", e)

asyncio.run(test())
