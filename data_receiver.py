import json
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer

# 全局状态共享容器
state = {
    "websocket": None,
    "loop": None,
    "httpd": None
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

                if state["websocket"] and state["loop"]:
                    async def forward():
                        try:
                            await state["websocket"].send(json.dumps({
                                "type": "external_data",
                                "data": data
                            }))
                            log_queue.put("📤 WebSocket 已推送")
                        except Exception as e:
                            log_queue.put(f"⚠️ WebSocket 发送失败: {e}")
                    state["loop"].call_soon_threadsafe(asyncio.create_task, forward())
                else:
                    log_queue.put(f"⚠️ 无 WebSocket 客户端连接: {state['websocket']=}, {state['loop']=}")
            except Exception as e:
                log_queue.put(f"❌ JSON 解析失败: {e}")
            self.send_response(200)
            self.end_headers()

    try:
        if addr.startswith("http://"):
            addr = addr.replace("http://", "")
        addr = addr.split("/")[0]
        host, port = addr.split(":")[0], int(addr.split(":")[1])

        httpd = HTTPServer((host, port), RequestHandler)
        state["httpd"] = httpd  # ✅ 保存 httpd 引用
        log_queue.put(f"🌐 HTTP监听启动: http://{host}:{port}")
        httpd.serve_forever()
    except Exception as e:
        log_queue.put(f"❌ 无法启动 HTTP 服务: {e}")
