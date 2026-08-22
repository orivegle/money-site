import os
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():

    # RenderではPostgreSQL
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)

    # 自分のPCではSQLite
    return sqlite3.connect("site.db")


def is_postgres():
    return bool(DATABASE_URL)


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    if is_postgres():

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT UNIQUE,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    else:

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

    cursor.close()
    conn.close()


def add_deal(title, description, url, category):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        if is_postgres():

            cursor.execute("""
                INSERT INTO deals
                (title, description, url, category)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                title,
                description,
                url,
                category
            ))

        else:

            cursor.execute("""
                INSERT OR IGNORE INTO deals
                (title, description, url, category)
                VALUES (?, ?, ?, ?)
            """, (
                title,
                description,
                url,
                category
            ))

        added = cursor.rowcount > 0

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        cursor.close()
        conn.close()

    return added


def get_deals(category=None):

    conn = get_connection()
    cursor = conn.cursor()

    if category and category != "すべて":

        if is_postgres():

            cursor.execute("""
                SELECT
                    id,
                    title,
                    description,
                    url,
                    created_at,
                    category
                FROM deals
                WHERE category = %s
                ORDER BY id DESC
            """, (category,))

        else:

            cursor.execute("""
                SELECT
                    id,
                    title,
                    description,
                    url,
                    created_at,
                    category
                FROM deals
                WHERE category = ?
                ORDER BY id DESC
            """, (category,))

    else:

        cursor.execute("""
            SELECT
                id,
                title,
                description,
                url,
                created_at,
                category
            FROM deals
            ORDER BY id DESC
        """)

    deals = cursor.fetchall()

    cursor.close()
    conn.close()

    return deals


def delete_old_deals(days=7):

    conn = get_connection()
    cursor = conn.cursor()

    if is_postgres():

        cursor.execute("""
            DELETE FROM deals
            WHERE created_at <
            CURRENT_TIMESTAMP - (%s * INTERVAL '1 day')
        """, (days,))

    else:

        cursor.execute("""
            DELETE FROM deals
            WHERE created_at < datetime('now', ?)
        """, (f"-{days} days",))

    deleted = cursor.rowcount

    conn.commit()

    cursor.close()
    conn.close()

    return deleted