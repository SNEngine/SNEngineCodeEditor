"""
Тестовый скрипт для проверки функциональности нумерации строк
"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer

# Добавим путь к исходникам
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.code_editor import CodeEditor

def main():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Тест нумерации строк")
    window.setGeometry(100, 100, 800, 600)
    
    layout = QVBoxLayout()
    
    # Создаем редактор с нумерацией строк
    test_styles = {
        'DarkTheme': {
            'SecondaryBackground': '#2A2A2A',
            'Background': '#1A1A1A',
            'StatusDefault': '#999999',
            'ActiveLineNumberColor': '#C84B31'  # Add the highlight color for current line
        }
    }
    editor = CodeEditor(styles=test_styles)
    
    # Добавляем тестовый YAML-контент
    test_content = """# YAML файл для тестирования
test:
  key1: value1
  key2: value2
  nested:
    - item1
    - item2
    - item3
  another_key: true
  null_value: null

# Еще один блок
section2:
  list:
    - element1
    - element2
    - element3
"""
    
    editor.setPlainText(test_content)
    
    layout.addWidget(editor)
    window.setLayout(layout)
    
    window.show()
    
    # Закрыть приложение через 5 секунд для демонстрации
    # QTimer.singleShot(5000, app.quit)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()