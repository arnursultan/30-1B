from __future__ import annotations
import sys
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox
)

class CounterWindow(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Счётчик — простой пример (PyQt6)")
        self.value = 0

        self.value_label = QLabel(f"Значение: {self.value}")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 18px;")

        self.step_label = QLabel("Шаг:")
        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 1000)
        self.step_spin.setValue(1)

        self.btn_inc = QPushButton("➕ Увеличить")
        self.btn_dec = QPushButton("➖ Уменьшить")
        self.btn_reset = QPushButton("↺ Сброс")

        root = QVBoxLayout(self)

        root.addWidget(self.value_label)

        step_row = QHBoxLayout()
        step_row.addWidget(self.step_label)
        step_row.addWidget(self.step_spin)
        root.addLayout(step_row)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_dec)
        buttons.addWidget(self.btn_reset)
        buttons.addWidget(self.btn_inc)
        root.addLayout(buttons)

        self.btn_inc.clicked.connect(self.on_inc)
        self.btn_dec.clicked.connect(self.on_dec)
        self.btn_reset.clicked.connect(self.on_reset)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def on_inc(self) -> None:
        step = self.step_spin.value()
        self.value += step
        self._refresh()

    def on_dec(self) -> None:
        step = self.step_spin.value()
        self.value -= step
        self._refresh()

    def on_reset(self) -> None:
        self.value = 0
        self._refresh()

    def _refresh(self) -> None:
        self.value_label.setText(f"Значение: {self.value}")

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Right:
            self.on_inc()
        elif event.key() == Qt.Key.Key_Left:
            self.on_dec()
        elif event.key() == Qt.Key.Key_Backspace:
            self.on_reset()
        else:
            super().keyPressEvent(event)

def main() -> None:
    app = QApplication(sys.argv)
    win = CounterWindow()
    win.resize(420, 180)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    