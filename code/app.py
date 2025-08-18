from __future__ import annotations
import sys

from PyQt6.QtWidgets import QApplication
from services.counter_services import CounterService
from widgets.main_window import MainWindow

def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(MainWindow.APP)
    app.setOrganizationName(MainWindow.ORG)

    service = CounterService(start=0)
    window = MainWindow(service)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
