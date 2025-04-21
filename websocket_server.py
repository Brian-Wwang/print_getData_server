# websocket_server.py
import asyncio
import platform
import websockets
from logger import init_logger
from websocket_handler import websocket_handler

async def run_websocket_server(port, printer_name, stop_event):
    host = "localhost" if platform.system() == "Windows" else "0.0.0.0"
    async with websockets.serve(lambda ws: websocket_handler(ws, printer_name), host=host, port=port, max_size=None):
        print("✅ WebSocket server started")
        while not stop_event.is_set():
            await asyncio.sleep(0.5)  # 每 0.5 秒检查一次是否停止
        print("🛑 WebSocket server stopping...")

def start_server_process(port, printer_name, queue, stop_event):
    init_logger(queue)
    asyncio.run(run_websocket_server(port, printer_name, stop_event))

