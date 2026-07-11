import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_FILE = "quotes.db"


class DatabaseManager:
    """Менеджер базы данных для работы с цитатами (SQLite)."""
    
    def __init__(self):
        """Инициализация менеджера БД. Соединение создаётся в init_db()."""
        self.conn = None
        
    def init_db(self):
        """Создание таблицы quotes при первом запуске."""
        try:
            self.conn = sqlite3.connect(DB_FILE)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quotes(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    author TEXT,
                    category TEXT,
                    date TEXT,
                    is_favorite INTEGER DEFAULT 0,
                    image_path TEXT
                )
            """)
            self.conn.commit()
            logger.info(f"База данных инициализирована: {DB_FILE}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    def get_all(self):
        """Получение всех цитат из базы, отсортированных по дате (новые сверху)."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM quotes ORDER BY date DESC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения записей: {e}")
            return []
    
    def insert_quote(self, data):
        """Добавление новой цитаты в базу данных."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO quotes(text, author, category, date, is_favorite, image_path) 
                VALUES(?, ?, ?, ?, ?, ?)
            """, (data["text"], data["author"], data["category"], 
                  data["date"], 1 if data["is_favorite"] else 0, data["image_path"]))
            self.conn.commit()
            logger.info(f"Добавлена цитата ID: {cursor.lastrowid}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка вставки записи: {e}")
            raise
    
    def update_quote(self, data):
        """Обновление существующей цитаты по ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE quotes SET text=?, author=?, category=?, date=?, is_favorite=?, image_path=? 
                WHERE id=?
            """, (data["text"], data["author"], data["category"], 
                  data["date"], 1 if data["is_favorite"] else 0, data["image_path"], data["id"]))
            self.conn.commit()
            logger.info(f"Обновлена цитата ID: {data['id']}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления записи: {e}")
            raise
    
    def delete_quote(self, quote_id):
        """Удаление цитаты по ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM quotes WHERE id=?", (quote_id,))
            self.conn.commit()
            logger.info(f"Удалена цитата ID: {quote_id}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления записи: {e}")
            raise
    
    def close(self):
        """Закрытие соединения с базой данных."""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с БД закрыто")