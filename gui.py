import multiprocessing
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QComboBox, QTextEdit, QCheckBox, QHBoxLayout, QGroupBox, QGridLayout, QSizePolicy, QFrame
)
from printer_utils import get_available_printers
from websocket_server import start_server_process
from data_receiver import start_http_server
import threading


class WebSocketServerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.server_process = None
        self.log_queue = multiprocessing.Queue()
        self.init_ui()
        self.timer = self.startTimer(500)

    def init_ui(self):
        self.setWindowTitle("跨平台 PDF 打印服务器")
        self.setFixedSize(720, 680)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)

        # 功能选择卡片
        func_card = QGroupBox()
        func_card.setTitle("功能选择  🛠")
        func_card.setStyleSheet(
            "QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; padding: 10px; }")
        func_layout = QHBoxLayout()
        self.print_checkbox = QCheckBox("自动打印")
        self.data_checkbox = QCheckBox("获取数据")
        self.print_checkbox.setChecked(True)
        self.data_checkbox.setChecked(True)
        self.print_checkbox.stateChanged.connect(self.toggle_modules)
        self.data_checkbox.stateChanged.connect(self.toggle_modules)
        func_layout.addWidget(self.print_checkbox)
        func_layout.addWidget(self.data_checkbox)
        func_card.setLayout(func_layout)
        main_layout.addWidget(func_card)

        # 自动打印配置卡片
        self.print_group = QGroupBox("自动打印配置  🖨")
        self.print_group.setStyleSheet(
            "QGroupBox { border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; padding: 10px; }")
        print_layout = QGridLayout()
        print_layout.setHorizontalSpacing(15)
        print_layout.setVerticalSpacing(10)

        self.port_input = QLineEdit("8765")
        self.port_input.setPlaceholderText("默认端口 8765")
        self.printer_combo = QComboBox()
        printers, default_printer = get_available_printers()
        self.printer_combo.addItems(printers)
        if default_printer:
            self.printer_combo.setCurrentText(default_printer)

        print_layout.addWidget(QLabel("打印端口 (8000-65535):"), 0, 0)
        print_layout.addWidget(self.port_input, 0, 1)
        print_layout.addWidget(QLabel("选择打印机:"), 1, 0)
        print_layout.addWidget(self.printer_combo, 1, 1)

        self.print_group.setLayout(print_layout)
        main_layout.addWidget(self.print_group)

        # 获取数据配置卡片
        self.data_group = QGroupBox("获取数据配置  🌐")
        self.data_group.setStyleSheet(
            "QGroupBox { border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; padding: 10px; }")
        data_layout = QGridLayout()
        data_layout.setHorizontalSpacing(15)
        data_layout.setVerticalSpacing(10)

        self.addr_input = QLineEdit("localhost:13213/callback")
        self.addr_input.setPlaceholderText("默认地址 localhost:13213/callback")
        data_layout.addWidget(QLabel("数据获取地址:"), 0, 0)
        data_layout.addWidget(self.addr_input, 0, 1)

        self.data_group.setLayout(data_layout)
        main_layout.addWidget(self.data_group)

        # 启动/停止服务器
        self.start_btn = QPushButton("启动服务器")
        self.start_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.start_btn.clicked.connect(self.toggle_server)
        main_layout.addWidget(self.start_btn)

        self.status_label = QLabel("状态：就绪 🟢")
        main_layout.addWidget(self.status_label)

        # 日志显示
        log_label = QLabel("日志输出 📋")
        log_label.setStyleSheet("font-weight: bold")
        main_layout.addWidget(log_label)

        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setStyleSheet("background-color: #f5f5f5; font-family: Consolas, monospace;")
        main_layout.addWidget(self.log_window)

        self.setLayout(main_layout)
        self.toggle_modules()

    def toggle_modules(self):
        self.print_group.setVisible(self.print_checkbox.isChecked())
        self.data_group.setVisible(self.data_checkbox.isChecked())

    def toggle_server(self):
        if self.server_process and self.server_process.is_alive():
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        if self.data_checkbox.isChecked():
            threading.Thread(
                target=start_http_server,
                args=(self.addr_input.text(), self.log_queue),
                daemon=True
            ).start()

        try:
            port = int(self.port_input.text())
            if port < 8000 or port > 65535:
                QMessageBox.warning(self, "错误", "端口号必须在 8000-65535 之间")
                return
            printer = self.printer_combo.currentText()
            self.ws_thread = threading.Thread(
                target=start_server_process,
                args=(port, printer, self.log_queue),
                daemon=True
            )
            self.ws_thread.start()
            self.port_input.setDisabled(True)
            self.printer_combo.setDisabled(True)
            self.addr_input.setDisabled(True)
            self.start_btn.setText("停止服务器")
            self.status_label.setText("✅ 打印服务启动中...")
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的端口号")

    def stop_server(self):
        from data_receiver import stop_http_server
        stop_http_server()  # ✅ 停止 HTTP Server

        if self.server_process:
            self.server_process.terminate()
            self.server_process.join()
            self.server_process = None

        self.port_input.setDisabled(False)
        self.printer_combo.setDisabled(False)
        self.start_btn.setText("启动服务器")
        self.status_label.setText("❌ 打印服务已停止")

    def timerEvent(self, event):
        while not self.log_queue.empty():
            log_message = self.log_queue.get()
            self.log_window.append(log_message)
            self.log_window.moveCursor(self.log_window.textCursor().MoveOperation.End)
