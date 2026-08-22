import sqlite3


DB_NAME = "site.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT UNIQUE,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def add_deal(title, description, url, category):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO deals
            (title, description, url, category)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, url, category)
        )

        conn.commit()
        added = True

    except sqlite3.IntegrityError:
        added = False

    conn.close()

    return added


def get_deals(category=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if category and category != "すべて":
        cursor.execute(
            """
            SELECT id, title, description, url, created_at, category
            FROM deals
            WHERE category = ?
            ORDER BY id DESC
            """,
            (category,)
        )

    else:
        cursor.execute("""
            SELECT id, title, description, url, created_at, category
            FROM deals
            ORDER BY id DESC
        """)

    deals = cursor.fetchall()

    conn.close()

    return deals


def delete_old_deals(days=7):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM deals
        WHERE created_at < datetime('now', ?)
        """,
        (f"-{days} days",)
    )

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted