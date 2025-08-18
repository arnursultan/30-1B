from __future__ import annotations
from typing import Optional

from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QKeySequence, QCloseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QSpinBox,
    QHBoxLayout, QVBoxLayout, QMessageBox, QToolBar, QStatusBar
)

from services.counter_services import CounterService


class MainWindow(QMainWindow):

    ORG = "Geeks"
    APP = "PyQtCounterQMainWindow"

    def __init__(self, service: CounterService, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._service = service
        self.setWindowTitle("Счётчик — QMainWindow (PyQt6)")
        self._settings = QSettings(self.ORG, self.APP)

        self._init_central_widget()
        self._init_actions()
        self._init_menubar()
        self._init_toolbar()
        self._init_statusbar()

        self._restore_settings()

    def _init_central_widget(self) -> None:
        cw = QWidget(self)
        self.setCentralWidget(cw)

        self.value_label = QLabel(self._fmt_value())
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 20px;")

        self.step_label = QLabel("Шаг:")
        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 1000)
        self.step_spin.setValue(1)

        self.btn_dec = QPushButton("➖ Уменьшить")
        self.btn_reset = QPushButton("↺ Сброс")
        self.btn_inc = QPushButton("➕ Увеличить")

        row_step = QHBoxLayout()
        row_step.addWidget(self.step_label)
        row_step.addWidget(self.step_spin)

        row_btn = QHBoxLayout()
        row_btn.addWidget(self.btn_dec)
        row_btn.addWidget(self.btn_reset)
        row_btn.addWidget(self.btn_inc)

        root = QVBoxLayout(cw)
        root.addWidget(self.value_label)
        root.addLayout(row_step)
        root.addLayout(row_btn)

        self.btn_inc.clicked.connect(self._act_inc_triggered)
        self.btn_dec.clicked.connect(self._act_dec_triggered)
        self.btn_reset.clicked.connect(self._act_reset_triggered)

        cw.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _init_actions(self) -> None:
        self.act_new = QAction("Новый (Сброс)", self)
        self.act_new.setShortcut(QKeySequence.StandardKey.New)
        self.act_new.triggered.connect(self._act_reset_triggered)

        self.act_exit = QAction("Выход", self)
        self.act_exit.setShortcut(QKeySequence.StandardKey.Quit)
        self.act_exit.triggered.connect(self.close)

        self.act_inc = QAction("Увеличить", self)
        self.act_inc.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Equal))
        self.act_inc.triggered.connect(self._act_inc_triggered)

        self.act_dec = QAction("Уменьшить", self)
        self.act_dec.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Minus))
        self.act_dec.triggered.connect(self._act_dec_triggered)

        self.act_reset = QAction("Сброс", self)
        self.act_reset.setShortcut(QKeySequence("Ctrl+0"))
        self.act_reset.triggered.connect(self._act_reset_triggered)

        self.act_toggle_toolbar = QAction("Показать/скрыть панель инструментов", self, checkable=True, checked=True)
        self.act_toggle_toolbar.triggered.connect(self._toggle_toolbar)

        self.act_toggle_statusbar = QAction("Показать/скрыть строку состояния", self, checkable=True, checked=True)
        self.act_toggle_statusbar.triggered.connect(self._toggle_statusbar)

        self.act_about = QAction("О программе", self)
        self.act_about.setMenuRole(QAction.MenuRole.AboutRole)
        self.act_about.triggered.connect(self._show_about)

    def _init_menubar(self) -> None:
        menubar = self.menuBar()

        m_file = menubar.addMenu("&Файл")
        m_file.addAction(self.act_new)
        m_file.addSeparator()
        m_file.addAction(self.act_exit)

        m_edit = menubar.addMenu("&Правка")
        m_edit.addAction(self.act_inc)
        m_edit.addAction(self.act_dec)
        m_edit.addSeparator()
        m_edit.addAction(self.act_reset)

        m_view = menubar.addMenu("&Вид")
        m_view.addAction(self.act_toggle_toolbar)
        m_view.addAction(self.act_toggle_statusbar)

        m_help = menubar.addMenu("&Справка")
        m_help.addAction(self.act_about)

    def _init_toolbar(self) -> None:
        self.toolbar = QToolBar("Панель инструментов", self)
        self.toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(self.toolbar)

        self.toolbar.addAction(self.act_dec)
        self.toolbar.addAction(self.act_reset)
        self.toolbar.addAction(self.act_inc)

    def _init_statusbar(self) -> None:
        self._status = QStatusBar(self)
        self.setStatusBar(self._status)
        self._status.showMessage("Готово", 2000)

    def _act_inc_triggered(self) -> None:
        step = self.step_spin.value()
        self._service.increment(step)
        self._update_ui()
        self.statusBar().showMessage(f"+{step} → {self._service.value}", 1500)

    def _act_dec_triggered(self) -> None:
        step = self.step_spin.value()
        self._service.decrement(step)
        self._update_ui()
        self.statusBar().showMessage(f"−{step} → {self._service.value}", 1500)

    def _act_reset_triggered(self) -> None:
        self._service.reset()
        self._update_ui()
        self.statusBar().showMessage("Сброс", 1500)

    def _toggle_toolbar(self, checked: bool) -> None:
        self.toolbar.setVisible(checked)

    def _toggle_statusbar(self, checked: bool) -> None:
        self.statusBar().setVisible(checked)

    def _show_about(self) -> None:
        QMessageBox.information(
            self,
            "О программе",
            "Счётчик на PyQt6\n"
            "Версия с QMainWindow, меню и статус-баром.\n"
            "© Учебный проект"
        )

    def _fmt_value(self) -> str:
        return f"Значение: {self._service.value}"

    def _update_ui(self) -> None:
        self.value_label.setText(self._fmt_value())

    def _restore_settings(self) -> None:
        geom = self._settings.value("window/geometry", None)
        if geom is not None:
            self.restoreGeometry(geom)
        else:
            self.resize(520, 220)

        step = self._settings.value("counter/step", 1, int)
        self.step_spin.setValue(step)

    def _save_settings(self) -> None:
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("counter/step", self.step_spin.value())

    def closeEvent(self, event: QCloseEvent) -> None:
        self._save_settings()
        event.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Right:
            self._act_inc_triggered()
        elif event.key() == Qt.Key.Key_Left:
            self._act_dec_triggered()
        elif event.key() == Qt.Key.Key_Backspace:
            self._act_reset_triggered()
        else:
            super().keyPressEvent(event)
