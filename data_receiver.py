import json
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer

# 全局状态共享容器
state = {
    "websocket": None,
    "loop": None,
    "httpd": None,
    "buffer": {}  # 缓存数据 { 单号: {"weightData": {}, "imageData": {}} }
}

def register_websocket(ws):
    state["websocket"] = ws
    try:
        state["loop"] = asyncio.get_running_loop()
    except RuntimeError:
        pass

def stop_http_server():
    if state.get("httpd"):
        state["httpd"].shutdown()
        state["httpd"] = None

def start_http_server(addr, log_queue):
    class RequestHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode())
                log_queue.put(f"📥 接收数据: {data}")

                # 提取关键字段
                key = data.get("ticketsNum") or data.get("expressNo")
                if not key:
                    raise ValueError("请求中未包含有效的单号（ticketsNum 或 expressNo）")

                if key not in state["buffer"]:
                    state["buffer"][key] = {}

                # 判断数据类型并缓存
                if "file" in data:
                    state["buffer"][key]["imageData"] = data
                    log_queue.put(f"🖼 图片数据已缓存: {key}")
                else:
                    state["buffer"][key]["weightData"] = data
                    log_queue.put(f"⚖️ 称重数据已缓存: {key}")

                # 两种数据都收到了，合并并推送
                if "weightData" in state["buffer"][key] and "imageData" in state["buffer"][key]:
                    weight_data = state["buffer"][key]["weightData"]
                    image_data = state["buffer"][key]["imageData"]

                    data_to_send = {
                        "expressNo": key,
                        "weight": weight_data.get("weight"),
                        "length": weight_data.get("length"),
                        "width": weight_data.get("width"),
                        "height": weight_data.get("height"),
                        "file": image_data.get("file")
                    }

                    merged_data = {
                        "type": "external_data",
                        "data": data_to_send
                    }

                    async def forward():
                        try:
                            await state["websocket"].send(json.dumps(merged_data))
                            log_queue.put(f"📤 WebSocket 已推送 external_data: {key}")
                        except Exception as e:
                            log_queue.put(f"⚠️ WebSocket 推送失败: {e}")

                    if state["websocket"] and state["loop"]:
                        state["loop"].call_soon_threadsafe(asyncio.create_task, forward())
                    else:
                        log_queue.put(f"⚠️ 无 WebSocket 客户端连接: {state['websocket']=}, {state['loop']=}")

                    # 清除缓存
                    del state["buffer"][key]

                # 成功响应
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                if "file" in data:
                    self.wfile.write(json.dumps({ "isOk": 1 }).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps({ "result": "true", "message": "" }).encode('utf-8'))

            except Exception as e:
                log_queue.put(f"❌ 处理失败: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "code": 400,
                    "error": str(e)
                }).encode('utf-8'))

    try:
        if addr.startswith("http://"):
            addr = addr.replace("http://", "")
        addr = addr.split("/")[0]
        host, port = addr.split(":")[0], int(addr.split(":")[1])

        httpd = HTTPServer((host, port), RequestHandler)
        state["httpd"] = httpd
        log_queue.put(f"🌐 HTTP监听启动: http://{host}:{port}")
        httpd.serve_forever()
    except Exception as e:
        log_queue.put(f"❌ 无法启动 HTTP 服务: {e}")
