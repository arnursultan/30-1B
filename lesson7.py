import sys
import re
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QMessageBox, QLabel
)

class CRUDApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CRUD PyQt6 + PostgreSQL")
        self.setGeometry(200, 200, 600, 500)

        try:
            self.conn = psycopg2.connect(
                host="localhost",
                port=5432,
                dbname="testdb",
                user="postgres",
                password="123456"
            )
            self.cursor = self.conn.cursor()
            self.create_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка подключения", str(e))
            sys.exit(1)

        layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Имя")
        layout.addWidget(self.name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_user)
        btn_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("Изменить")
        self.update_btn.clicked.connect(self.update_user)
        btn_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_user)
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по имени/email")
        self.search_input.textChanged.connect(self.search_user)
        layout.addWidget(self.search_input)

        self.users_list = QListWidget()
