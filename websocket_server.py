import asyncio
import platform
import websockets
from logger import init_logger
from websocket_handler import websocket_handler

async def run_websocket_server(port, printer_name):
    host = "localhost" if platform.system() == "Windows" else "0.0.0.0"
    async with websockets.serve(lambda ws: websocket_handler(ws, printer_name), host=host, port=port, max_size=None):
        await asyncio.Future()

def start_server_process(port, printer_name, queue):
    init_logger(queue)
    asyncio.run(run_websocket_server(port, printer_name))
