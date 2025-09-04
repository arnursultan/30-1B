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
        SELECT xp, level, current_coins, books_taken, achievements
        FROM students WHERE id=%s;
        """, (student_id, ))
        xp, level, current_coins, books_taken, achievements = self.cur.fetchone()
        xp += amount
        current_coins += coins
        books_taken += books
        new_achievements = achievements.split(",") if achievements else []

        levelup = False
        while xp > 100:
            xp -= 100
            level += 1
            levelup = True

        if xp < 0: xp = 0
        if current_coins < 0: current_coins = 0

        events = []
        if books_taken >= 1 and "Первая книга" not in new_achievements:
            new_achievements.append("Первая книга")
            events.append(("🏆 Ачивка: Первая книга!", "achievement.gif"))
        if books_taken >=10 and "Книжный червь" not in new_achievements:
            new_achievements.append("Книжный червь")
            events.append(("🏆 Ачивка: Книжный червь!", "achievement.gif"))
        if current_coins >-50 and "Богач" not in new_achievements:
            new_achievements.append("Богач")
            events.append(("🏆 Ачивка: Богач!", "achievement.gif"))
        if level >=5 and "Чтец" not in achievements:
            new_achievements.append("Чтец")
            events.append(("🏆 Ачивка: Чтец!", "achievement.gif"))
        if levelup:
            events.append(("⚡ Новый уровень!", "levelup.gif"))

        self.cur.execute("""
        UPDATE students
        SET xp=%s, level=%s, current_coins=%s, books_taken=%s, achievements=%s
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
        self.cur.execute("INSERT INTO books(title, author_id) VALUES(%s, %s);)",
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
        return "📖 Вы вернули книгу! +5XP, +2 монеты"