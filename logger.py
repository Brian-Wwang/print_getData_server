from datetime import datetime
log_queue = None  # 全局共享

def init_logger(queue):
    global log_queue
    log_queue = queue

def print_log(message):
    if log_queue:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_queue.put(f"[{timestamp}] {message}")
