# src/particles.py
import random
from typing import List
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QPainterPath
from PyQt5.QtCore import QTimer, QRect, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve
from PyQt5.QtCore import Qt, QPoint


class Particle:
    """Класс для представления одной частицы."""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.size = random.randint(2, 5)
        self.color = QColor(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255), 200)
        self.speed_x = random.uniform(-2, 2)
        self.speed_y = random.uniform(-2, 2)
        self.life = 1.0  # Прозрачность от 0 до 1
        self.decay = random.uniform(0.01, 0.03)  # Скорость уменьшения жизни
        self.gravity = 0.1  # Гравитация

    def update(self) -> bool:
        """Обновляет позицию частицы. Возвращает True, если частица всё ещё жива."""
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += self.gravity  # Применяем гравитацию
        self.life -= self.decay
        
        return self.life > 0

    def draw(self, painter: QPainter):
        """Рисует частицу."""
        if self.life <= 0:
            return
            
        alpha = int(self.life * 255)
        color = QColor(self.color.red(), self.color.green(), self.color.blue(), alpha)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawEllipse(int(self.x), int(self.y), self.size, self.size)


class TypingParticlesEffect(QWidget):
    """Виджет для отображения частиц при печатании."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.particles: List[Particle] = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(16)  # ~60 FPS
        
        self.hide()  # Изначально скрыт

    def add_particles_at_position(self, x: int, y: int, count: int = 5):
        """Добавляет новые частицы в указанную позицию."""
        for _ in range(count):
            particle = Particle(x, y)
            self.particles.append(particle)
        
        # Показываем виджет, когда появляются частицы
        if not self.isVisible():
            self.show()
        
        # Устанавливаем размеры, чтобы покрыть весь экран
        self.resize(QApplication.desktop().screenGeometry().size())
        self.move(0, 0)

    def update_particles(self):
        """Обновляет все частицы и удаляет мертвые."""
        # Обновляем каждую частицу
        alive_particles = []
        for particle in self.particles:
            if particle.update():
                alive_particles.append(particle)
        
        self.particles = alive_particles
        
        # Если нет живых частиц, скрываем виджет
        if not self.particles:
            self.hide()
        else:
            self.update()

    def paintEvent(self, event):
        """Отрисовывает все частицы."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for particle in self.particles:
            particle.draw(painter)

    def clear_particles(self):
        """Очищает все частицы."""
        self.particles.clear()
        self.hide()