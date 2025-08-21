# import sqlite3
#
# conn = sqlite3.connect('library.db')
# cursor = conn.cursor()
#
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS users (
#     id    I   NTEGER PRIMARY KEY AUTOINCREMENT,
#     name      TEXT NOT NULL,
#     age       INTEGER
# )
# ''')
#
# cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Emily", 18))
# conn.commit()
#
# cursor.execute("SELECT * FROM users")
# for row in cursor.fetchall():
#     print(row)
#
# conn.close()

import sqlite3
from contextlib import closing

DB_PATH = "prolibrary.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

DDL = """
CREATE TABLE IF NOT EXISTS authors (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS books (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT NOT NULL,
    year      INTEGER,
    author_id INTEGER NOT NULL,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
);
"""

def init_db():
    with closing(get_conn()) as conn, conn:
        conn.executescript(DDL)
        conn.execute("INSERT OR IGNORE INTO authors (name) VALUES (?)", ("Рене Декарт",))
        conn.execute("INSERT OR IGNORE INTO authors (name) VALUES (?)", ("Джордж Оруэлл",))
        conn.execute("INSERT OR IGNORE INTO authors (name) VALUES (?)", ("Адам Смит",))

        def ensure_book(title, year, author_name):
            a = conn.execute("SELECT id FROM authors WHERE name=?", (author_name,)).fetchone()
            if not a:
                return
            author_id = a["id"]
            exists = conn.execute(
                "SELECT 1 FROM books WHERE title=? AND author_id=?",
                (title, author_id)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO books(title, year, author_id) VALUES (?, ?, ?)",
                    (title, year, author_id)
                )

        ensure_book("Правила для руководства ума", "2025", "Рене Декарт")
        ensure_book("Глотнуть воздуха", "2023", "Джордж Оруэлл")
        ensure_book("Исследование о природе и причинах богатства народов", "2023", "Адам Смит")


def create_author(name: str) -> int:
    with closing(get_conn()) as conn, conn:
        cur = conn.execute("INSERT INTO authors(name) VALUES (?)", (name,))
        return cur.lastrowid

def create_book(title: str, year: int | None, author_name: str) -> int:
    with closing(get_conn()) as conn, conn:
        a = conn.execute("SELECT id FROM authors WHERE name=?", (author_name,)).fetchone()
        author_id = a["id"] if a else conn.execute(
            "INSERT INTO authors(name) VALUES (?)", (author_name,)
        ).lastrowid
        cur = conn.execute(
            "INSERT INTO books(title, year, author_id) VALUES (?, ?, ?)",
            (title, year, author_id)
        )
        return cur.lastrowid

def list_authors() -> list[dict]:
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT id, name FROM authors ORDER BY name").fetchall()
        return [dict(r) for r in rows]

def list_books() -> list[dict]:
    sql = """
    SELECT b.id, b.title, b.year, a.name AS author
    FROM books b JOIN authors a ON a.id=b.author_id
    ORDER BY b.year, b.title
    """
    with closing(get_conn()) as conn:
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]

def find_books(query: str) -> list[dict]:
    sql = """
    SELECT b.id, b.title, b.year, a.name AS author
    FROM books b JOIN authors a ON a.id=b.author_id
    WHERE b.title LIKE ? OR a.name LIKE ?
    ORDER BY b.year, b.title
    """
    like = f"%{query}%"
    with closing(get_conn()) as conn:
        rows = conn.execute(sql, (like, like)).fetchall()
        return [dict(r) for r in rows]

def update_book(book_id: int, new_title: str | None = None, new_year: int | None = None) -> int:
    if new_title is None and new_year is None:
        return 0
    parts, params = [], []
    if new_title is not None:
        parts.append("title=?")
        params.append(new_title)
    if new_year is not None:
        parts.append("year=?")
        params.append(new_year)
    params.append(book_id)
    sql = f"UPDATE books SET {', '.join(parts)} WHERE id=?"
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(sql, params)
        return cur.rowcount

def delete_book(book_id: int) -> int:
    with closing(get_conn()) as conn, conn:
        cur = conn.execute("DELETE FROM books WHERE id=?", (book_id,))
        return cur.rowcount

def delete_author(author_id: int) -> int:
    with closing(get_conn()) as conn, conn:
        cur = conn.execute("DELETE FROM authors WHERE id=?", (author_id,))
        return cur.rowcount

def demo():
    init_db()
    print("== Авторы ==")
    for a in list_authors():
        print(a)

    print("\n== Книги ==")
    for b in list_books():
        print(b)

    print("\nДобавим книгу:")
    new_id = create_book("Грозовой перевал", 1847, "Эмили Бронте")
    print("Создано book_id", new_id)

    print("\nПоиск 'Декарт'")
    for b in find_books("Декарт"):
        print(b)

    print("\nОбновим добавленную книгу (год = 2004):")
    print("изменено строк:", update_book(new_id, new_year=2004))

    print("\nУдалим книгу:")
    print("удалено строк:", delete_book(new_id))

if __name__ == "__main__":
    demo()
