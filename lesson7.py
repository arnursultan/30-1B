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
        self.cursor.execute(query, (email,))
        existing = self.cursor.fetchone()

        if existing and (user_id is None or existing[0] != user_id):
            QMessageBox.warning(self, "Ошибка", "Такой email уже существует.")
            return False

        return True

    def add_user(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        if name and email:
            if self.validate_inputs(name, email):
                try:
                    self.cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
                    self.conn.commit()
                    self.load_users()
                    self.name_input.clear()
                    self.email_input.clear()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка БД", str(e))
                    self.conn.rollback()
        else:
            QMessageBox.warning(self, "Ошибка", "Введите имя и email")

    def load_users(self):
        self.users_list.clear()
        self.cursor.execute("SELECT id, name, email FROM users ORDER BY id")
        users = self.cursor.fetchall()
        for user in users:
            self.users_list.addItem(f"{user[0]} | {user[1]} | {user[2]}")

        self.counter_label.setText(f"Записей: {len(users)}")

    def load_user(self, item):
        data = item.text().split(" | ")
        self.selected_id = int(data[0])
        self.name_input.setText(data[1])
        self.email_input.setText(data[2])

    def update_user(self):
        try:
            user_id = self.selected_id
        except AttributeError:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return

        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        if name and email:
            if self.validate_inputs(name, email, user_id):
                try:
                    self.cursor.execute(
                        "UPDATE users SET name=%s, email=%s WHERE id=%s",
                        (name, email, user_id)
                    )
                    self.conn.commit()
                    self.load_users()
                    self.name_input.clear()
                    self.email_input.clear()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка БД", str(e))
                    self.conn.rollback()
        else:
            QMessageBox.warning(self, "Ошибка", "Введите имя и email")

    def delete_user(self):
        try:
            user_id = self.selected_id
        except AttributeError:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return

        self.cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        self.conn.commit()
        self.load_users()
        self.name_input.clear()
        self.email_input.clear()

    def search_user(self):
        query = self.search_input.text()
        self.users_list.clear()
        self.cursor.execute(
            "SELECT id, name, email FROM users WHERE name ILIKE %s OR email ILIKE %s ORDER BY id",
            (f"%{query}%", f"%{query}%")
        )
        users = self.cursor.fetchall()
        for user in users:
            self.users_list.addItem(f"{user[0]} | {user[1]} | {user[2]}")

        self.counter_label.setText(f"Записей: {len(users)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CRUDApp()
    window.show()
    sys.exit(app.exec())