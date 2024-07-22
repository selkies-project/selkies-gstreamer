import asyncio
from aiohttp import web
import websockets
import pathlib

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            await ws.send_str("Echo: " + msg.data)
        elif msg.type == web.WSMsgType.CLOSED:
            break

    return ws

app = web.Application()
app.router.add_get("/ws", websocket_handler)

# Serve static files
current_path = pathlib.Path(__file__).parent
static_path = current_path / "static"
print(static_path)
app.router.add_static("/", path=static_path, name="static")

if __name__ == '__main__':
    web.run_app(app, port=8080)