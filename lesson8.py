import sys
import os
import json
import random
import psycopg2

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QMessageBox, QInputDialog, QProgressBar, QDialog
)
from PyQt6.QtGui import QPixmap, QMovie
from PyQt6.QtCore import Qt

CONFIG_FILE = "config.json"

DB_SETTINGS = {
    "dbname": "LibraryGame",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_SETTINGS)
        self.cur = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            xp INT DEFAULT 0,
            level INT DEFAULT 1,
            coins INT DEFAULT 0,
            books_taken INT DEFAULT 0,
            achievements TEXT DEFAULT ''
        );
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS authors (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL
        );
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            author_id INT REFERENCES authors(id) ON DELETE SET NULL,
            is_taken BOOLEAN DEFAULT FALSE
        );
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS students_books (
            student_id INT REFERENCES students(id) ON DELETE CASCADE,
            book_id INT REFERENCES books(id) ON DELETE CASCADE,
            PRIMARY KEY (student_id, book_id)
        );
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price INT NOT NULL,
            effect TEXT NOT NULL
        );
        """)
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS student_items (
            student_id INT REFERENCES students(id) ON DELETE CASCADE,
            item_id INT REFERENCES items(id) ON DELETE CASCADE,
            qty INT DEFAULT 1,
            PRIMARY KEY (student_id, item_id)
        );
        """)
        self.conn.commit()

        self.cur.execute("SELECT COUNT(*) FROM items;")
        if self.cur.fetchone()[0] == 0:
            self.cur.executemany("INSERT INTO items(name, price, effect) VALUES (%s,%s,%s);", [
                ("Зелье опыта", 10, "xp+20"),
                ("Мешочек монет", 15, "coins+20"),
                ("Редкая книга", 20, "xp+50"),
            ])
            self.conn.commit()

    def init_student(self, name):
        self.cur.execute("SELECT id FROM students WHERE name=%s;", (name,))
        row = self.cur.fetchone()
        if row:
            return row[0]
        else:
            self.cur.execute(
                "INSERT INTO students(name) VALUES(%s) RETURNING id;", (name,)
            )
            student_id = self.cur.fetchone()[0]
            self.conn.commit()
            return student_id

    def get_student_stats(self, student_id):
        self.cur.execute("""
        SELECT xp, level, coins, books_taken, achievements 
        FROM students WHERE id=%s;
        """, (student_id,))
        return self.cur.fetchone()

    def update_xp(self, student_id, amount, coins=0, books=0):
        self.cur.execute("""
        SELECT xp, level, coins, books_taken, achievements 
        FROM students WHERE id=%s;
        """, (student_id,))
        xp, level, current_coins, books_taken, achievements = self.cur.fetchone()
        xp += amount
        current_coins += coins
        books_taken += books
        new_achievements = achievements.split(",") if achievements else []

        levelup = False
        while xp >= 100:
            xp -= 100
            level += 1
            levelup = True

        if xp < 0: xp = 0
        if current_coins < 0: current_coins = 0

        events = []
        if books_taken >= 1 and "Первая книга" not in new_achievements:
            new_achievements.append("Первая книга")
            events.append(("🏆 Ачивка: Первая книга!", "achievement.gif"))
        if books_taken >= 10 and "Книжный червь" not in new_achievements:
            new_achievements.append("Книжный червь")
            events.append(("🏆 Ачивка: Книжный червь!", "achievement.gif"))
        if current_coins >= 50 and "Богач" not in new_achievements:
            new_achievements.append("Богач")
            events.append(("🏆 Ачивка: Богач!", "achievement.gif"))
        if level >= 5 and "Чтец" not in new_achievements:
            new_achievements.append("Чтец")
            events.append(("🏆 Ачивка: Чтец!", "achievement.gif"))
        if levelup:
            events.append(("⚡ Новый уровень!", "levelup.gif"))

        self.cur.execute("""
        UPDATE students 
        SET xp=%s, level=%s, coins=%s, books_taken=%s, achievements=%s 
        WHERE id=%s;
        """, (xp, level, current_coins, books_taken, ",".join(new_achievements), student_id))
        self.conn.commit()
        return xp, level, current_coins, events

    def get_all_books(self):
        self.cur.execute("""
        SELECT b.id, b.title, COALESCE(a.name, 'Неизвестен'), b.is_taken
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.id
        ORDER BY b.id;
        """)
        return self.cur.fetchall()

    def get_my_books(self, student_id):
        self.cur.execute("""
        SELECT b.id, b.title FROM books b
        JOIN students_books sb ON sb.book_id = b.id
        WHERE sb.student_id = %s;
        """, (student_id,))
        return self.cur.fetchall()

    def get_authors(self):
        self.cur.execute("SELECT id, name FROM authors ORDER BY id;")
        return self.cur.fetchall()

    def add_author(self, name):
        self.cur.execute("INSERT INTO authors(name) VALUES(%s);", (name,))
        self.conn.commit()

    def add_book(self, title, author_id):
        self.cur.execute("INSERT INTO books(title, author_id) VALUES(%s, %s);",
                         (title, author_id))
        self.conn.commit()

    def take_book(self, student_id, book_id):
        self.cur.execute("SELECT is_taken FROM books WHERE id=%s;", (book_id,))
        row = self.cur.fetchone()
        if not row:
            return "❌ Нет такой книги!"
        if row[0]:
            return "❌ Книга уже занята!"
        self.cur.execute("UPDATE books SET is_taken=TRUE WHERE id=%s;", (book_id,))
        self.cur.execute("INSERT INTO students_books(student_id, book_id) VALUES(%s, %s);",
                         (student_id, book_id))
        self.conn.commit()
        return "✅ Вы взяли книгу! +10 XP, +1 монета"

    def return_book(self, student_id, book_id):
        self.cur.execute("DELETE FROM students_books WHERE student_id=%s AND book_id=%s;",
                         (student_id, book_id))
        self.cur.execute("UPDATE books SET is_taken=FALSE WHERE id=%s;", (book_id,))
        self.conn.commit()
        return "📖 Вы вернули книгу! +5 XP, +2 монеты"

    def get_items(self):
        self.cur.execute("SELECT id, name, price, effect FROM items ORDER BY id;")
        return self.cur.fetchall()

    def buy_item(self, student_id, item_id):
        self.cur.execute("SELECT price, effect FROM items WHERE id=%s;", (item_id,))
        row = self.cur.fetchone()
        if not row:
            return "❌ Нет такого товара!"
        price, effect = row
        xp, lvl, coins, books_taken, ach = self.get_student_stats(student_id)
        if coins < price:
            return "❌ Недостаточно монет!"
        self.cur.execute("UPDATE students SET coins=coins-%s WHERE id=%s;", (price, student_id))
        self.cur.execute("SELECT qty FROM student_items WHERE student_id=%s AND item_id=%s;",
                         (student_id, item_id))
        row = self.cur.fetchone()
        if row:
            self.cur.execute("UPDATE student_items SET qty=qty+1 WHERE student_id=%s AND item_id=%s;",
                             (student_id, item_id))
        else:
            self.cur.execute("INSERT INTO student_items(student_id, item_id, qty) VALUES(%s, %s, 1);",
                             (student_id, item_id))
        self.conn.commit()
        return f"🛒 Куплен товар за {price} монет!"

    def get_inventory(self, student_id):
        self.cur.execute("""
        SELECT i.id, i.name, i.effect, si.qty 
        FROM student_items si
        JOIN items i ON i.id = si.item_id
        WHERE si.student_id=%s;
        """, (student_id,))
        return self.cur.fetchall()

    def use_item(self, student_id, item_id):
        self.cur.execute("SELECT effect FROM items WHERE id=%s;", (item_id,))
        row = self.cur.fetchone()
        if not row:
            return "❌ Нет такого предмета!"
        effect = row[0]
        self.cur.execute("UPDATE student_items SET qty=qty-1 WHERE student_id=%s AND item_id=%s;", (student_id, item_id))
        self.cur.execute("DELETE FROM student_items WHERE qty<=0;")
        self.conn.commit()
        if effect.startswith("xp+"):
            val = int(effect.split("+")[1])
            self.update_xp(student_id, val)
            return f"⚡ Получено {val} XP!"
        elif effect.startswith("coins+"):
            val = int(effect.split("+")[1])
            self.update_xp(student_id, 0, val)
            return f"💰 Получено {val} монет!"
        return "❌ Эффект неизвестен"

class EventDialog(QDialog):
    def __init__(self, text, gif_path):
        super().__init__()
        self.setWindowTitle("🎬 Событие")
        self.setGeometry(300, 300, 400, 300)
        layout = QVBoxLayout()
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        anim = QLabel()
        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            anim.setMovie(movie)
            movie.start()
        else:
            anim.setText("⚠️ Нет анимации")
        layout.addWidget(anim, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

class LibraryGame(QWidget):
    def __init__(self, db, student_id, student_name):
        super().__init__()
        self.db = db
        self.student_id = student_id
        self.student_name = student_name
        self.setWindowTitle(f"📚 Library Quest RPG 4.0 — {self.student_name}")
        self.setGeometry(200, 200, 1200, 650)

        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.char_label = QLabel()
        pixmap = QPixmap(resource_path("hero.png"))
        self.char_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
        right_layout.addWidget(self.char_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.level_label = QLabel()
        right_layout.addWidget(self.level_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.xp_bar = QProgressBar()
        self.xp_bar.setMaximum(100)
        right_layout.addWidget(self.xp_bar)

        self.coins_label = QLabel()
        right_layout.addWidget(self.coins_label, alignment=Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(QLabel("📚 Все книги:"))
        self.list_all = QListWidget()
        left_layout.addWidget(self.list_all)

        left_layout.addWidget(QLabel("📖 Мои книги:"))
        self.list_my = QListWidget()
        left_layout.addWidget(self.list_my)

        btn_layout1 = QHBoxLayout()
        self.btn_take = QPushButton("➕ Взять книгу")
        self.btn_return = QPushButton("❌ Вернуть книгу")
        self.btn_event = QPushButton("🎲 Событие")
        btn_layout1.addWidget(self.btn_take)
        btn_layout1.addWidget(self.btn_return)
        btn_layout1.addWidget(self.btn_event)

        btn_layout2 = QHBoxLayout()
        self.btn_add_author = QPushButton("👤 Добавить автора")
        self.btn_add_book = QPushButton("📕 Добавить книгу")
        btn_layout2.addWidget(self.btn_add_author)
        btn_layout2.addWidget(self.btn_add_book)

        btn_layout3 = QHBoxLayout()
        self.btn_shop = QPushButton("🛒 Магазин")
        self.btn_inv = QPushButton("🎒 Инвентарь")
        btn_layout3.addWidget(self.btn_shop)
        btn_layout3.addWidget(self.btn_inv)

        left_layout.addLayout(btn_layout1)
        left_layout.addLayout(btn_layout2)
        left_layout.addLayout(btn_layout3)

        main_layout.addLayout(left_layout, 70)
        main_layout.addLayout(right_layout, 30)
        self.setLayout(main_layout)

        self.btn_take.clicked.connect(self.take_book)
        self.btn_return.clicked.connect(self.return_book)
        self.btn_event.clicked.connect(self.random_event)
        self.btn_add_author.clicked.connect(self.add_author)
        self.btn_add_book.clicked.connect(self.add_book)
        self.btn_shop.clicked.connect(self.open_shop)
        self.btn_inv.clicked.connect(self.open_inventory)

        self.refresh()

    def refresh(self):
        self.list_all.clear()
        for book_id, title, author, taken in self.db.get_all_books():
            status = "занята" if taken else "свободна"
            self.list_all.addItem(f"{book_id}. {title} — {author} ({status})")

        self.list_my.clear()
        for book_id, title in self.db.get_my_books(self.student_id):
            self.list_my.addItem(f"{book_id}. {title}")

        xp, level, coins, books_taken, achievements = self.db.get_student_stats(self.student_id)
        self.level_label.setText(f"Игрок: {self.student_name} | Уровень: {level}")
        self.xp_bar.setValue(xp)
        self.coins_label.setText(f"💰 Монеты: {coins}")

    def show_event(self, text, gif_file):
        dlg = EventDialog(text, resource_path(gif_file))
        dlg.exec()

    def take_book(self):
        item = self.list_all.currentItem()
        if not item: return
        book_id = int(item.text().split(".")[0])
        msg = self.db.take_book(self.student_id, book_id)
        xp, lvl, coins, events = self.db.update_xp(self.student_id, 10, 1, 1)
        self.show_event(msg, "take.gif")
        for e in events:
            self.show_event(e[0], e[1])
        self.refresh()

    def return_book(self):
        item = self.list_my.currentItem()
        if not item: return
        book_id = int(item.text().split(".")[0])
        msg = self.db.return_book(self.student_id, book_id)
        xp, lvl, coins, events = self.db.update_xp(self.student_id, 5, 2)
        self.show_event(msg, "return.gif")
        for e in events:
            self.show_event(e[0], e[1])
        self.refresh()

    def random_event(self):
        events_list = [
            ("Вы нашли редкую книгу! +20 XP 🎉", 20, 5, "event_good.gif"),
            ("Книга утеряна! -10 XP 😱", -10, -3, "event_bad.gif"),
            ("Библиотекарь похвалил вас! +15 XP 😊", 15, 2, "event_good.gif"),
            ("Вас наказали за шум. -5 XP 🙃", -5, -1, "event_bad.gif"),
        ]
        msg, xp_add, coins_add, gif = random.choice(events_list)
        xp, lvl, coins, events = self.db.update_xp(self.student_id, xp_add, coins_add)
        self.show_event(msg, gif)
        for e in events:
            self.show_event(e[0], e[1])
        self.refresh()

    def add_author(self):
        name, ok = QInputDialog.getText(self, "Добавить автора", "Имя автора:")
        if ok and name:
            self.db.add_author(name)
            QMessageBox.information(self, "Успех", f"Автор '{name}' добавлен!")

    def add_book(self):
        title, ok = QInputDialog.getText(self, "Добавить книгу", "Название книги:")
        if not ok or not title: return
        authors = self.db.get_authors()
        if not authors:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте автора!")
            return
        items = [f"{a[0]}. {a[1]}" for a in authors]
        item, ok = QInputDialog.getItem(self, "Выбор автора", "Автор:", items, 0, False)
        if not ok or not item: return
        author_id = int(item.split(".")[0])
        self.db.add_book(title, author_id)
        QMessageBox.information(self, "Успех", f"Книга '{title}' добавлена!")
        self.refresh()

    def open_shop(self):
        items = self.db.get_items()
        choices = [f"{i[0]}. {i[1]} — {i[2]} монет" for i in items]
        choice, ok = QInputDialog.getItem(self, "🛒 Магазин", "Выберите товар:", choices, 0, False)
        if not ok or not choice: return
        item_id = int(choice.split(".")[0])
        msg = self.db.buy_item(self.student_id, item_id)
        QMessageBox.information(self, "Магазин", msg)
        self.refresh()

    def open_inventory(self):
        inv = self.db.get_inventory(self.student_id)
        if not inv:
            QMessageBox.information(self, "Инвентарь", "🎒 Пусто")
            return
        choices = [f"{i[0]}. {i[1]} (x{i[3]})" for i in inv]
        choice, ok = QInputDialog.getItem(self, "🎒 Инвентарь", "Выберите предмет:", choices, 0, False)
        if not ok or not choice: return
        item_id = int(choice.split(".")[0])
        msg = self.db.use_item(self.student_id, item_id)
        QMessageBox.information(self, "Инвентарь", msg)
        self.refresh()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database()

    student_name = None
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            student_name = json.load(f).get("student_name")

    if not student_name:
        name, ok = QInputDialog.getText(None, "Вход", "Введите своё имя:")
        if not ok or not name:
            sys.exit()
        student_name = name
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"student_name": student_name}, f, ensure_ascii=False)

    student_id = db.init_student(student_name)

    game = LibraryGame(db, student_id, student_name)
    game.show()

    sys.exit(app.exec())






