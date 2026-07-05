import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox, 
                              QFileDialog, QTableWidgetItem, QTableWidget)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.uic import loadUi
from PIL import Image
import database


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
    
        # загружаем интерфейс
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_main.ui")
        loadUi(ui_path, self)
    
        self.setWindowTitle("Коллекция цитат")
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)
    
        self.current_image_path = ""
    
        # инициализация бд
        self.db = database.DatabaseManager()
        self.db.init_db()
    
        # настройки таблицы
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Цитата", "Автор", "Категория", "Дата", "Избранное"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # ИСПРАВЛЕНО
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # ИСПРАВЛЕНО
    
        # заполняем комбобоксы
        self.cb_category.addItems(["Философия", "Юмор", "Мотивация", "Литература", "Другое"])
        self.cb_author.addItems(["Сократ", "Марк Твен", "Оскар Уайльд", "Фридрих Ницше", "Лев Толстой"])
    
        # настройки для картинки
        self.lbl_portrait.setMinimumSize(250, 250)
        self.lbl_portrait.setMaximumSize(250, 250)
        self.lbl_portrait.setScaledContents(True)

        self.connect_signals()
        self.update_table()
    
    def connect_signals(self):
        # привязываем кнопки
        self.btn_add.clicked.connect(self.add_quote)
        self.btn_edit.clicked.connect(self.edit_quote)
        self.btn_delete.clicked.connect(self.delete_quote)
        self.btn_copy.clicked.connect(self.copy_quote)
        self.btn_load_image.clicked.connect(self.load_image)
        self.table.itemSelectionChanged.connect(self.select_row)
    
    def add_quote(self):
        # проверка текста
        text = self.te_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Ошибка", "Введите текст цитаты")
            return
        
        # проверка даты
        if self.de_date.date() > QDate.currentDate():
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
        QMessageBox.information(self, "Готово", "Скопировано в буфер")
    
    def select_row(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self.clear_form()
            return
        
        row = selected[0].row()
        self.te_text.setPlainText(self.table.item(row, 0).text())
        
        # устанавливаем автора
        author = self.table.item(row, 1).text()
        index = self.cb_author.findText(author)
        if index >= 0:
            self.cb_author.setCurrentIndex(index)
        
        # категорию
        category = self.table.item(row, 2).text()
        index = self.cb_category.findText(category)
        if index >= 0:
            self.cb_category.setCurrentIndex(index)
        
        # дату
        date_str = self.table.item(row, 3).text()
        if date_str:
            self.de_date.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
        
        # избранное
        self.chk_favorite.setChecked(self.table.item(row, 4).text() == "✓")
        
        # картинку
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
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize((250, 250), Image.LANCZOS)
            
            qt_img = QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qt_img)
            self.lbl_portrait.setPixmap(pixmap)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить: {e}")
    
    def update_table(self):
        self.table.setRowCount(0)
        records = self.db.get_all()
        for i, rec in enumerate(records):
            self.table.insertRow(i)
            
            # обрезаем длинный текст
            text = rec["text"]
            if len(text) > 50:
                text = text[:50] + "..."
            
            self.table.setItem(i, 0, QTableWidgetItem(text))
            self.table.setItem(i, 1, QTableWidgetItem(rec["author"] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(rec["category"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(rec["date"] or ""))
            
            fav = "✓" if rec["is_favorite"] else ""
            self.table.setItem(i, 4, QTableWidgetItem(fav))
            
            # сохраняем id
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
        reply = QMessageBox.question(self, "Выход", "Закрыть программу?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
        if reply != QMessageBox.StandardButton.Cancel:
            self.db.close()
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("QuotesCollection")
    app.setFont(QFont("Segoe UI", 10))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()