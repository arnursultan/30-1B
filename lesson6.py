# import sqlite3
#
# conn = sqlite3.connect("crud.sqlite")
# cursor = conn.cursor()
#
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS users (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT,
#     age INTEGER
# )
# """)
#
# cursor.executemany("INSERT INTO users (name, age) VALUES (?, ?)", [
#     ("Даниил", 20),
#     ("Эмили", 17),
#     ("Артём", 25)
# ])
# conn.commit()
#
# print("Все пользователи старше 18 лет:")
# cursor.execute("SELECT * FROM users WHERE age > 18")
# for row in cursor.fetchall():
#     print(row)
#
# cursor.execute("DELETE FROM users WHERE name = ?", ("Эмили",))
# conn.commit()
#
# print("После удаления Эмили:")
# cursor.execute("SELECT * FROM users")
# for row in cursor.fetchall():
#     print(row)
#
# conn.close()

import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QMessageBox, QLabel
)

DB_NAME = "mydb.sqlite"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER
    )
    """)
    conn.commit()
    conn.close()

class UserApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CRUD - PyQt6 + SQLite")
        self.resize(400, 400)

        self.layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Имя")

        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Возраст")

        self.add_button = QPushButton("Добавить пользователя")

        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Имя:"))
        add_layout.addWidget(self.name_input)
        add_layout.addWidget(QLabel("Возраст:"))
        add_layout.addWidget(self.age_input)
        add_layout.addWidget(self.add_button)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите имя для поиска")
        self.search_button = QPushButton("Поиск")

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        self.list_widget = QListWidget()

        self.delete_button = QPushButton("Удалить выбранного")

        self.layout.addLayout(add_layout)
        self.layout.addLayout(search_layout)
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.delete_button)
        self.setLayout(self.layout)

        self.add_button.clicked.connect(self.add_user)
        self.search_button.clicked.connect(self.search_user)
        self.delete_button.clicked.connect(self.delete_user)

        self.load_all_users()

    def db_connect(self):
        return sqlite3.connect(DB_NAME)

    def load_all_users(self):
        self.list_widget.clear()
        conn = self.db_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, age FROM users")
        for row in cursor.fetchall():
            self.list_widget.addItem(f"{row[0]}: {row[1]} ({row[2]} лет)")
        conn.close()

    def add_user(self):
        name = self.name_input.text().strip()
        age_text = self.age_input.text().strip()

        if not name or not age_text.isdigit():
            QMessageBox.warning(self, "Ошибка", "Введите корректные данные")
            return

        age = int(age_text)
        conn = self.db_connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", (name, age))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Успех", f"Пользователь {name} добавлен")
        self.name_input.clear()
        self.age_input.clear()
        self.load_all_users()

    def search_user(self):
        name = self.search_input.text().strip()
        self.list_widget.clear()
        conn = self.db_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, age FROM users WHERE name LIKE ?", (f"%{name}%",))
        row = cursor.fetchall()
        for row in row:
            self.list_widget.addItem(f"{row[0]}: {row[1]} ({row[2]} лет)")
        conn.close()

    def delete_user(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return

        user_id = int(item.text().split(":")[0])

        conn = self.db_connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Успех", "Пользователь удалён")
        self.load_all_users()

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = UserApp()
    window.show()
    sys.exit(app.exec())
