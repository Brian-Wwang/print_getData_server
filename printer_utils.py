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
    system = platform.system()
    try:
        if system == "Windows":
            import win32api
            print_log(f"📤 Windows 打印 {path}")
            win32api.ShellExecute(0, "print", path, f'/d:"{printer_name}"', ".", 0)
        else:
            subprocess.run(["lp", "-d", printer_name, path], check=True)
        print_log("✅ 打印完成")
        return True
    except Exception as e:
        print_log(f"❌ 打印失败: {e}")
        return False
