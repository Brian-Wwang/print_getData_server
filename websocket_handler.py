import base64
import json
from datetime import datetime
from printer_utils import save_base64_pdf, print_pdf_file
from logger import print_log
from data_receiver import register_websocket

async def websocket_handler(websocket, printer_name):
    register_websocket(websocket)  # 添加此行
    print_log("🌐 客户端已连接")
    start_api_dt = None

    try:
        await websocket.send(json.dumps({"type": "connection", "data": "连接成功！"}))
        async for message in websocket:
            if isinstance(message, bytes):
                path = save_base64_pdf(base64.b64encode(message).decode())
                start = datetime.now()
                success = print_pdf_file(path, printer_name)
                await websocket.send(json.dumps({"type": "print_status", "data": "✅" if success else "❌"}))
                print_log(f"🖨️ 耗时 {(datetime.now() - start).total_seconds():.3f}s")
            else:
                # JSON 消息
                try:
                    data = json.loads(message)
                    if data.get("type") == "print_base64":
                        pdf = data.get("data", "")
                        path = save_base64_pdf(pdf)
                        success = print_pdf_file(path, printer_name)
                        await websocket.send(json.dumps({"type": "print_status", "data": "✅" if success else "❌"}))
                except Exception as e:
                    print_log(f"❌ JSON 处理失败: {e}")
    except Exception as e:
        print_log(f"❌ WebSocket 错误: {e}")
