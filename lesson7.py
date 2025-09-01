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
        self.users_list.itemClicked.connect(self.load_user)
        layout.addWidget(self.users_list)

        self.counter_label = QLabel("Записей: 0")
        layout.addWidget(self.counter_label)

        self.setLayout(layout)
        self.load_users()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE
            )
        """)
        self.conn.commit()

    def validate_inputs(self, name, email, user_id=None):
        if not re.match(r"^[A-Za-zА-Яа-яЁё\s\-]+$", name):
            QMessageBox.warning(self, "Ошибка", "Имя может содержать только буквы, пробелы и дефисы.")
            return False

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            QMessageBox.warning(self, "Ошибка", "Введите корректный email.")
            return False

        query = "SELECT id FROM users WHERE email = %s"
        self.cursor.execute(query, (email, ))
        existing = self.cursor.fetchone()

        if existing and (user_id is None or existing[0] != user_id):
            QMessageBox.warning(self, "Ошибка", "Такой email уеж существует.")
            return False

        return True

    def add_user(self):
        name = self.name_input.text().strip()