import sys
import multiprocessing
from PyQt6.QtWidgets import QApplication
from gui import WebSocketServerGUI

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    gui = WebSocketServerGUI()
    gui.show()
    sys.exit(app.exec())
