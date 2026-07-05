import sqlite3

DB_FILE = "quotes.db"


class DatabaseManager:
    def __init__(self):
        self.conn = None
        
    def init_db(self):
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
    
    def get_all(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM quotes ORDER BY date DESC")
        return cursor.fetchall()
    
    def insert_quote(self, data):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO quotes(text, author, category, date, is_favorite, image_path) 
            VALUES(?, ?, ?, ?, ?, ?)
        """, (data["text"], data["author"], data["category"], 
              data["date"], 1 if data["is_favorite"] else 0, data["image_path"]))
        self.conn.commit()
    
    def update_quote(self, data):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE quotes SET text=?, author=?, category=?, date=?, is_favorite=?, image_path=? 
            WHERE id=?
        """, (data["text"], data["author"], data["category"], 
              data["date"], 1 if data["is_favorite"] else 0, data["image_path"], data["id"]))
        self.conn.commit()
    
    def delete_quote(self, quote_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM quotes WHERE id=?", (quote_id,))
        self.conn.commit()
    
    def close(self):
        if self.conn:
            self.conn.close()