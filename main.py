import sys
import os
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox, 
                              QFileDialog, QTableWidgetItem, QTableWidget)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.uic import loadUi
from PIL import Image
import database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_main.ui")
        loadUi(ui_path, self)
        
        self.setWindowTitle("Коллекция цитат")
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)
        
        self.current_image_path = ""
        
        self.db = database.DatabaseManager()
        self.db.init_db()
        
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Цитата", "Автор", "Категория", "Дата", "Избранное"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.cb_category.addItems(["Философия", "Юмор", "Мотивация", "Литература", "Другое"])
        self.cb_author.addItems(["Сократ", "Марк Твен", "Оскар Уайльд", "Фридрих Ницше", "Лев Толстой"])
        
        self.lbl_portrait.setMinimumSize(250, 250)
        self.lbl_portrait.setMaximumSize(250, 250)
        self.lbl_portrait.setScaledContents(True)
        
        self.de_date.setDate(QDate.currentDate())
        
        self.connect_signals()
        self.apply_styles()
        self.update_table()
        
        logger.info("Приложение инициализировано")
    
    def connect_signals(self):
        self.btn_add.clicked.connect(self.add_quote)
        self.btn_edit.clicked.connect(self.edit_quote)
        self.btn_delete.clicked.connect(self.delete_quote)
        self.btn_copy.clicked.connect(self.copy_quote)
        self.btn_load_image.clicked.connect(self.load_image)
        self.btn_clear.clicked.connect(self.clear_form)
        self.table.itemSelectionChanged.connect(self.select_row)
    
    def add_quote(self):
        text = self.te_text.toPlainText().strip()
        if not text:
            logger.warning("Попытка добавить пустую цитату")
            QMessageBox.warning(self, "Ошибка", "Введите текст цитаты")
            return
        
        if self.de_date.date() > QDate.currentDate():
            logger.warning("Попытка установить будущую дату")
            QMessageBox.warning(self, "Ошибка", "Дата не может быть в будущем")
            return
        
        data = {
            "text": text,
            "author": self.cb_author.currentText(),
            "category": self.cb_category.currentText(),
            "date": self.de_date.date().toString("yyyy-MM-dd"),
            "is_favorite": self.chk_favorite.isChecked(),
            "image_path": self.current_image_path
        }
        
        self.db.insert_quote(data)
        logger.info(f"Добавлена цитата: {text[:30]}...")
        self.update_table()
        self.clear_form()
        QMessageBox.information(self, "Готово", "Цитата добавлена")
    
    def edit_quote(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите цитату")
            return
        
        if not self.te_text.toPlainText().strip():
            QMessageBox.warning(self, "Ошибка", "Текст пустой")
            return
        
        row = selected[0].row()
        quote_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        data = {
            "id": quote_id,
            "text": self.te_text.toPlainText().strip(),
            "author": self.cb_author.currentText(),
            "category": self.cb_category.currentText(),
            "date": self.de_date.date().toString("yyyy-MM-dd"),
            "is_favorite": self.chk_favorite.isChecked(),
            "image_path": self.current_image_path
        }
        
        self.db.update_quote(data)
        logger.info(f"Изменена цитата ID: {quote_id}")
        self.update_table()
        QMessageBox.information(self, "Готово", "Изменения сохранены")
    
    def delete_quote(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите цитату")
            return
        
        reply = QMessageBox.question(self, "Подтверждение", "Удалить?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            row = selected[0].row()
            quote_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.db.delete_quote(quote_id)
            logger.info(f"Удалена цитата ID: {quote_id}")
            self.update_table()
            self.clear_form()
    
    def copy_quote(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите цитату")
            return
        
        row = selected[0].row()
        text = self.table.item(row, 0).text()
        author = self.table.item(row, 1).text()
        
        clipboard = QApplication.clipboard()
        clipboard.setText(f'"{text}" — {author}')
        logger.info("Цитата скопирована в буфер обмена")
        QMessageBox.information(self, "Готово", "Скопировано в буфер")
    
    def select_row(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self.clear_form()
            return
        
        row = selected[0].row()
        self.te_text.setPlainText(self.table.item(row, 0).text())
        
        author = self.table.item(row, 1).text()
        index = self.cb_author.findText(author)
        if index >= 0:
            self.cb_author.setCurrentIndex(index)
        
        category = self.table.item(row, 2).text()
        index = self.cb_category.findText(category)
        if index >= 0:
            self.cb_category.setCurrentIndex(index)
        
        date_str = self.table.item(row, 3).text()
        if date_str:
            self.de_date.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
        
        self.chk_favorite.setChecked(self.table.item(row, 4).text() == "✓")
        
        image_path = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole + 1)
        if image_path:
            self.load_portrait(image_path)
    
    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите портрет", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        self.current_image_path = path
        self.load_portrait(path)
    
    def load_portrait(self, path):
        if not os.path.exists(path):
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            return
        
        try:
            img = Image.open(path).convert("RGBA")
            
            if img.size[0] < 50 or img.size[1] < 50:
                QMessageBox.warning(self, "Ошибка", "Изображение слишком маленькое")
                return
            
            img = img.resize((250, 250), Image.LANCZOS)
            
            qt_img = QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qt_img)
            self.lbl_portrait.setPixmap(pixmap)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить: {e}")
            logger.error(f"Ошибка загрузки изображения: {e}")
    
    def update_table(self):
        self.table.setRowCount(0)
        records = self.db.get_all()
        for i, rec in enumerate(records):
            self.table.insertRow(i)
            
            text = rec["text"]
            if len(text) > 50:
                text = text[:50] + "..."
            
            self.table.setItem(i, 0, QTableWidgetItem(text))
            self.table.setItem(i, 1, QTableWidgetItem(rec["author"] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(rec["category"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(rec["date"] or ""))
            
            fav = "✓" if rec["is_favorite"] else ""
            self.table.setItem(i, 4, QTableWidgetItem(fav))
            
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, rec["id"])
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole + 1, rec["image_path"])
    
    def clear_form(self):
        self.te_text.clear()
        self.cb_author.setCurrentIndex(0)
        self.cb_category.setCurrentIndex(0)
        self.de_date.setDate(QDate.currentDate())
        self.chk_favorite.setChecked(False)
        self.lbl_portrait.clear()
        self.current_image_path = ""
    
    def closeEvent(self, event):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Выход")
        msg_box.setText("Закрыть программу?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg_box.setStyleSheet("""
        QMessageBox {
            background-color: white;
            color: black;
        }
        QPushButton {
            background-color: #4a90e2;
            color: white;
            border: 1px solid #357abd;
            border-radius: 3px;
            padding: 5px 15px;
        }
        QPushButton:hover {
            background-color: #357abd;
        }
        """)
        reply = msg_box.exec()

        if reply != QMessageBox.StandardButton.Cancel:
            self.db.close()
            logger.info("Приложение закрыто")
            event.accept()
        else:
            event.ignore()

    def apply_styles(self):
        """QSS стилизация с исправлением кнопок даты и диалогов"""
        self.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QTextEdit, QComboBox, QDateEdit {
            background-color: white;
            border: 1px solid #aaa;
            border-radius: 3px;
            padding: 3px;
            color: black;
        }
        
        QComboBox QAbstractItemView {
            background-color: white;
            color: black;
            selection-background-color: #4a90e2;
            selection-color: white;
        }
        
        QPushButton {
            background-color: #4a90e2;
            color: white;
            border: 1px solid #357abd;
            border-radius: 3px;
        }
        
        QPushButton:hover {
            background-color: #357abd;
        }
        
        QTableWidget {
            background-color: white;
            border: 1px solid #aaa;
            gridline-color: #ddd;
            color: black;
        }
        
        QHeaderView::section {
            background-color: #4a5568;
            color: white;
            padding: 4px;
            border: none;
        }
        
        QCheckBox, QLabel {
            color: black;
        }
        
        /* Исправление кнопок даты - убираем transparent */
        QDateEdit::up-button, QDateEdit::down-button {
            width: 16px;
            background-color: white;
            border: 1px solid #aaa;
        }
        
        QDateEdit::up-button:hover, QDateEdit::down-button:hover {
            background-color: #e0e0e0;
        }
        
        /* Стили для диалогов */
        QMessageBox {
            background-color: white;
        }
        
        QMessageBox QLabel {
            color: black;
            background-color: white;
        }
        
        QMessageBox QPushButton {
            background-color: #4a90e2;
            color: white;
            border: 1px solid #357abd;
            border-radius: 3px;
            padding: 5px 15px;
        }
        
        QMessageBox QPushButton:hover {
            background-color: #357abd;
        }

        QDateEdit::up-button, QDateEdit::down-button {
            width: 0;
            height: 0;
        }

        QFileDialog {
            background-color: white;
            color: black;
        }
    """)


def main():
    app = QApplication(sys.argv)
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        logger.error("Необработанное исключение", exc_info=(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(None, "Ошибка", f"Произошла ошибка:\n{exc_value}")
    
    sys.excepthook = handle_exception
    
    app.setApplicationName("QuotesCollection")
    app.setFont(QFont("Segoe UI", 9))
    
    window = MainWindow()
    window.show()
    
    logger.info("Приложение запущено")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()