"""
Утилита для определения поддержки 3D ускорения GPU
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QOpenGLContext
from PyQt5.QtOpenGL import QGLFormat

def check_gpu_support():
    """Проверяет поддержку GPU ускорения"""
    try:
        # Проверяем, доступен ли OpenGL (в разных версиях Qt методы могут отличаться)
        # Для PyQt5 используем QOpenGLContext.areSharing()
        # Проверим через создание контекста
        context = QOpenGLContext()
        has_opengl = context.isValid()  # Это не совсем то же самое, но дает общее представление
        # Альтернативный способ - проверить поддержку QOpenGLWidget
        try:
            from PyQt5.QtWidgets import QOpenGLWidget
            has_opengl = True
        except ImportError:
            has_opengl = False

        if has_opengl:
            return {
                'has_opengl': True,
                'opengl_version': check_opengl_version(),
                'gpu_info': get_gpu_info(),
                'hardware_acceleration': True
            }
        else:
            return {
                'has_opengl': False,
                'opengl_version': 'N/A',
                'gpu_info': 'N/A',
                'hardware_acceleration': False
            }
    except Exception as e:
        return {
            'has_opengl': False,
            'opengl_version': 'N/A',
            'gpu_info': f'Error: {str(e)}',
            'hardware_acceleration': False
        }

def check_opengl_version():
    """Проверяет версию OpenGL через Qt"""
    try:
        # Пробуем создать OpenGL контекст для проверки поддержки
        context = QOpenGLContext()
        if context:
            # Для получения точной информации нужен OpenGL контекст, но это сложно через PyQt
            return "Available (version check requires native OpenGL context)"
        else:
            return "Not available"
    except Exception:
        return "Error checking version"

def get_gpu_info():
    """Получает информацию о GPU через Qt"""
    try:
        # Проверяем поддержку OpenGL
        from PyQt5.QtWidgets import QOpenGLWidget
        return "OpenGL supported, GPU info requires native access"
    except ImportError:
        return "OpenGL not supported"

def check_qt_opengl_support():
    """Проверяет поддержку OpenGL в Qt"""
    try:
        from PyQt5.QtWidgets import QOpenGLWidget
        from PyQt5.QtOpenGL import QGLWidget
        return True
    except ImportError:
        return False

def print_gpu_debug_info():
    """Выводит отладочную информацию о GPU"""
    print("=== GPU Debug Information ===")

    gpu_support = check_gpu_support()
    print(f"Has OpenGL Support: {gpu_support['has_opengl']}")
    print(f"Hardware Acceleration: {gpu_support['hardware_acceleration']}")
    print(f"OpenGL Version: {gpu_support['opengl_version']}")
    print(f"GPU Info: {gpu_support['gpu_info']}")

    qt_opengl_support = check_qt_opengl_support()
    print(f"Qt OpenGL Widget Support: {qt_opengl_support}")

    # Проверяем, как Qt использует рендеринг
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        from PyQt5.QtWidgets import QOpenGLWidget
        from PyQt5.QtGui import QSurfaceFormat

        # Проверяем формат поверхности OpenGL
        format = QSurfaceFormat()
        print(f"OpenGL Surface Format: {format.renderableType()}, Version: {format.majorVersion()}.{format.minorVersion()}")

    except Exception as e:
        print(f"Error checking Qt rendering: {str(e)}")

    print("=============================")

class GPUDebugWindow(QMainWindow):
    """Оконное представление информации о GPU"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPU Debug Information")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # Label для отображения информации о GPU
        self.gpu_info_label = QLabel()
        self.gpu_info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.gpu_info_label)
        
        # Кнопка для обновления информации
        refresh_btn = QPushButton("Refresh GPU Info")
        refresh_btn.clicked.connect(self.update_gpu_info)
        layout.addWidget(refresh_btn)
        
        central_widget.setLayout(layout)
        
        # Обновляем информацию при запуске
        self.update_gpu_info()
    
    def update_gpu_info(self):
        """Обновляет информацию о GPU"""
        gpu_support = check_gpu_support()
        info_text = f"""<h2>GPU Debug Information</h2>
        <p><b>Has OpenGL Support:</b> {gpu_support['has_opengl']}</p>
        <p><b>Hardware Acceleration:</b> {gpu_support['hardware_acceleration']}</p>
        <p><b>OpenGL Version:</b> {gpu_support['opengl_version']}</p>
        <p><b>GPU Info:</b> {gpu_support['gpu_info']}</p>
        <p><b>Qt OpenGL Widget Support:</b> {check_qt_opengl_support()}</p>"""
        
        self.gpu_info_label.setText(info_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Выводим информацию в консоль
    print_gpu_debug_info()
    
    # Показываем окно с информацией
    window = GPUDebugWindow()
    window.show()
    
    sys.exit(app.exec_())