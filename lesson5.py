import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableView, QLabel, QMessageBox, QStatusBar
)
from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel


DB_NAME = "app.db"
TABLE_NAME = "contacts"


def init_db() -> QSqlDatabase:
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(DB_NAME)

    if not db.open():
        raise RuntimeError(f"Не удалось открыть БД: {db.lastError().text()}")

    query = QSqlQuery(db)
    ok = query.exec(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT
        )
        """
    )
    if not ok:
        raise RuntimeError(f"Не удалось создать таблицу: {query.lastError().text()}")

    return db


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.db = init_db()

        self.model = QSqlTableModel(self, self.db)
        self.model.setTable(TABLE_NAME)
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.model.select()
        self.model.setHeaderData(0, Qt.Orientation.Horizontal, "ID")
        self.model.setHeaderData(1, Qt.Orientation.Horizontal, "Имя")
        self.model.setHeaderData(2, Qt.Orientation.Horizontal, "Email")
        self.model.setHeaderData(3, Qt.Orientation.Horizontal, "Телефон")

        self.setWindowTitle("CRUD — Create & Read")
        self.resize(820, 520)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        form = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Имя (обязательно)")
        self.email_edit.setPlaceholderText("Email (уникально)")
        self.phone_edit.setPlaceholderText("Телефон")
        form.addWidget(QLabel("Имя"))
        form.addWidget(self.name_edit, 2)
        form.addWidget(QLabel("Email"))
        form.addWidget(self.email_edit, 2)
        form.addWidget(QLabel("Телефон"))
        form.addWidget(self.phone_edit, 2)

        buttons = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.reload_btn = QPushButton("Обновить")
        buttons.addWidget(self.add_btn)
        buttons.addWidget(self.reload_btn)
        buttons.addStretch()

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        root.addLayout(form)
        root.addLayout(buttons)
        root.addWidget(self.table)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.add_btn.clicked.connect(self.on_add_clicked)
        self.reload_btn.clicked.connect(self.reload)

    def on_add_clicked(self):
        name = self.name_edit.text().strip()
        email = self.email_edit.text().strip() or None
        phone = self.phone_edit.text().strip() or None

        if not name:
            QMessageBox.warning(self, "Проверка данных", "Поле «Имя» обязательно.")
            return

        query = QSqlQuery(self.db)
        query.prepare(
            f"INSERT INTO {TABLE_NAME} (name, email, phone) VALUES (:name, :email, :phone)"
        )
        query.bindValue(":name", name)
        query.bindValue(":email", email)
        query.bindValue(":phone", phone)

        if not query.exec():
            err = query.lastError().text()
            QMessageBox.critical(self, "Ошибка добавления", f"Не удалось сохранить запись:\n{err}")
            return

        self.clear_inputs()
        self.reload()
        self.status.showMessage("Контакт добавлен.", 3000)

    def reload(self):
        self.model.select()
        self.table.resizeColumnsToContents()
        self.status.showMessage(f"Загружено записей: {self.model.rowCount()}", 3000)

    def clear_inputs(self):
        self.name_edit.clear()
        self.email_edit.clear()
        self.phone_edit.clear()
        self.name_edit.setFocus()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
