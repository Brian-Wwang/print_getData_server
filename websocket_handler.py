from printer_utils import save_base64_pdf, print_pdf_file
from logger import print_log
from data_receiver import register_websocket

import json
import base64
from datetime import datetime
import websockets

# ✅ 你应该已有这些函数：
# print_log(message)      # 日志记录函数
# get_desktop_path()      # 返回桌面路径
# print_pdf_file(path, printer_name)  # 跨平台统一打印
# register_websocket(websocket)      # 用于记录连接对象
# save_base64_pdf(base64_str)        # 将 base64 保存为 PDF，并返回路径

async def websocket_handler(websocket, printer_name):
    print_log("🌐 WebSocket 客户端已连接")
    register_websocket(websocket)  # ✅ 添加这行

    time_info = None  # 用于保存最近一次收到的时间信息

    try:
        await websocket.send(json.dumps({"type": "connection", "data": "WebSocket 连接成功！"}))

        async for message in websocket:
            print_log("📥 收到消息")  # ⬅️ 每次收到任何消息，先打个收到了的日志

            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    if not isinstance(data, dict):
                        print_log("⚠️ 非法 JSON 消息")
                        continue

                    if data.get("type") == "printWithTime":
                        time_info = data.get("timeInfo", {})
                        print_log(f"🕒 接口花费时间: {time_info.get('apiTime', '未知')} 毫秒")
                        print_log(f"🕒 准备耗时: {time_info.get('prepareTime', '未知')} 毫秒")
                    else:
                        print_log(f"⚠️ 未知消息类型: {data.get('type')}")
                except Exception as e:
                    print_log(f"❌ JSON 解析错误: {e}")

            elif isinstance(message, bytes):
                try:
                    path = save_base64_pdf(base64.b64encode(message).decode())
                    success = print_pdf_file(path, printer_name)
                    finish_time = datetime.now()

                    status = "✅ 成功" if success else "❌ 失败"
                    await websocket.send(json.dumps({"type": "print_status", "data": status}))
                    start_timestamp_ms = time_info.get('startTime', 0)
                    start_dt = datetime.fromtimestamp(start_timestamp_ms / 1000)
                    total_duration = (finish_time - start_dt).total_seconds() * 1000
                    print_log(f"📊 总耗时: {total_duration:.1f} 毫秒")

                except Exception as e:
                    print_log(f"❌ 打印失败: {e}")
                    await websocket.send(json.dumps({"type": "print_status", "data": "❌ 打印失败"}))
            else:
                print_log("⚠️ 未知消息格式")
    except websockets.exceptions.ConnectionClosed:
        print_log("❌ WebSocket 连接断开")
    except Exception as e:
        print_log(f"❌ WebSocket 错误: {e}")