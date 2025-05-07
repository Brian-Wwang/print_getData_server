import os, platform, base64, subprocess
from logger import print_log

def get_desktop_path():
    return os.path.join(os.path.expanduser("~"), "Desktop")

def get_available_printers():
    system = platform.system()
    printers, default_printer = [], None
    try:
        if system == "Windows":
            import win32print
            printers = [p[2] for p in win32print.EnumPrinters(2)]
            default_printer = win32print.GetDefaultPrinter()
        elif system in ["Darwin", "Linux"]:
            import cups
            conn = cups.Connection()
            printers = list(conn.getPrinters().keys())
            default_printer = conn.getDefault()
    except Exception as e:
        print_log(f"⚠️ 获取打印机失败: {e}")
    return printers, default_printer

def save_base64_pdf(base64_data, filename="print_document.pdf"):
    path = os.path.join(get_desktop_path(), filename)
    with open(path, "wb") as f:
        f.write(base64.b64decode(base64_data))
    return path

def print_pdf_file(path, printer_name):
    print(f"打印 PDF 文件: {path}")
    print(f"打印机名称: {printer_name}")
    system = platform.system()
    try:
        if system == "Windows":
            try:
                import win32print
                import win32api
            except ImportError:
                print_log("❌ 未安装 pywin32，请运行 pip install pywin32")
                return False

            print_log(f"📤 发送 PDF 到打印机: {printer_name} (Windows)")
            win32api.ShellExecute(0, "print", path, f'/d:"{printer_name}"', ".", 0)

        else:
            print_log(f"📤 发送 PDF 到打印机: {printer_name} (Linux/macOS)")
            process = subprocess.Popen(["lp", "-d", printer_name, path],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                print_log(f"❌ 打印失败: {stderr.decode().strip()}")
                return False

        print_log("✅ 打印完成")
        return True

    except Exception as e:
        print_log(f"❌ 打印失败: {e}")
        return False
