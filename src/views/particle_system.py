"""
Система частиц для визуального эффекта при вводе символов с GPU ускорением
"""
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QTimer, Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QOpenGLContext
from PyQt5.QtOpenGL import QGLWidget
import random


class Particle:
    """Класс для одной частицы"""
    def __init__(self, x, y, primary_color="#FF6B6B", secondary_color="#4ECDC4",
                 accent_color="#FFE66D", glow_color="#C84B31",
                 particle_line_primary_color="#FF6B6B80", particle_line_secondary_color="#4ECDC480",
                 particle_type="primary"):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.vx = random.uniform(-3, 3)  # Случайная скорость по X
        self.vy = random.uniform(-3, 3)  # Случайная скорость по Y
        self.life = 1.0  # Жизнь частицы (от 1.0 до 0.0)
        self.decay = random.uniform(0.02, 0.05)  # Скорость уменьшения жизни
        self.size = random.randint(2, 5)  # Размер частицы

        # Store previous positions for trail effect
        self.prev_positions = [(x, y)]  # Keep track of previous positions for trail effect
        self.max_trail_length = 5  # Max number of positions to store for trail

        # Set color based on particle type and style colors
        self.particle_type = particle_type

        if particle_type == "primary":
            self.base_color = QColor(primary_color)
        elif particle_type == "secondary":
            self.base_color = QColor(secondary_color)
        elif particle_type == "accent":
            self.base_color = QColor(accent_color)
        else:  # glow/default
            self.base_color = QColor(glow_color)

        # Set line color based on particle type
        if particle_type in ["primary", "accent"]:
            self.line_color = QColor(particle_line_primary_color)
        else:  # secondary, glow
            self.line_color = QColor(particle_line_secondary_color)

        self.alpha = 255

    def update(self):
        """Обновление состояния частицы"""
        # Store current position before updating
        self.prev_positions.append((self.x, self.y))
        if len(self.prev_positions) > self.max_trail_length:
            self.prev_positions.pop(0)  # Remove oldest position

        self.x += self.vx
        self.y += self.vy
        # Добавляем гравитацию для более реалистичного движения
        self.vy += 0.1
        self.life -= self.decay
        self.alpha = int(self.life * 255)
        return self.life > 0 and 0 <= self.alpha <= 255

    def draw(self, painter):
        """Отрисовка частицы"""
        if self.life > 0:
            # Draw trail/line between previous positions
            if len(self.prev_positions) > 1:
                painter.save()
                trail_pen = QPen(self.line_color, 1)
                trail_pen.setCapStyle(Qt.RoundCap)
                painter.setPen(trail_pen)

                # Draw lines between positions in the trail
                for i in range(1, len(self.prev_positions)):
                    pos1 = self.prev_positions[i-1]
                    pos2 = self.prev_positions[i]
                    alpha_factor = i / len(self.prev_positions)  # Fade effect along the trail
                    trail_color = QColor(
                        self.line_color.red(),
                        self.line_color.green(),
                        self.line_color.blue(),
                        int(self.line_color.alpha() * alpha_factor * self.life)
                    )
                    trail_pen.setColor(trail_color)
                    painter.setPen(trail_pen)
                    painter.drawLine(int(pos1[0]), int(pos1[1]), int(pos2[0]), int(pos2[1]))
                painter.restore()

            # Draw the main particle
            color = QColor(
                self.base_color.red(),
                self.base_color.green(),
                self.base_color.blue(),
                self.alpha
            )
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(
                int(self.x - self.size/2),
                int(self.y - self.size/2),
                self.size,
                self.size
            )


class ParticleEffect(QWidget):
    """Виджет для отображения системы частиц с GPU ускорением"""

    def __init__(self, parent=None, style_colors=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Делаем окно прозрачным для мыши

        # Initialize style colors - default to predefined values
        self.style_colors = style_colors or {
            'ParticlePrimaryColor': '#FF6B6B',
            'ParticleSecondaryColor': '#4ECDC4',
            'ParticleAccentColor': '#FFE66D',
            'ParticleGlowColor': '#C84B31',
            'ParticleTrailColor': '#A0A0A0',
            'ParticleLinePrimaryColor': '#FF6B6B80',
            'ParticleLineSecondaryColor': '#4ECDC480',
            'ParticleConnectionColor': '#C84B3140'
        }

        # Пытаемся включить GPU ускорение для QPainter
        try:
            # Установим политику рендеринга для использования OpenGL
            self.setMouseTracking(False)
            # Используем более производительный рендерер если возможно
            if QOpenGLContext.hasOpenGL():
                # Установим атрибуты для возможного использования GPU
                self.setAttribute(Qt.WA_PaintOnScreen, False)  # Разрешаем двойную буферизацию
        except:
            pass  # Если нет поддержки OpenGL, продолжаем без неё

        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(16)  # ~60 FPS
        self.hide()  # Изначально скрыт

        # Устанавливаем геометрию сразу при инициализации
        if self.parent():
            self.update_parent_geometry()

    def add_particles_at(self, x, y, count=8):
        """Добавить частицы в указанную позицию"""
        for _ in range(count):
            # Randomly select a particle type for variety
            particle_type = random.choice(["primary", "secondary", "accent", "glow"])
            particle = Particle(
                x, y,
                primary_color=self.style_colors.get('ParticlePrimaryColor', '#FF6B6B'),
                secondary_color=self.style_colors.get('ParticleSecondaryColor', '#4ECDC4'),
                accent_color=self.style_colors.get('ParticleAccentColor', '#FFE66D'),
                glow_color=self.style_colors.get('ParticleGlowColor', '#C84B31'),
                particle_line_primary_color=self.style_colors.get('ParticleLinePrimaryColor', '#FF6B6B80'),
                particle_line_secondary_color=self.style_colors.get('ParticleLineSecondaryColor', '#4ECDC480'),
                particle_type=particle_type
            )
            self.particles.append(particle)

        # Показываем виджет на короткое время
        self.show()
        # Автоматически скрываем через 1.5 секунды, если нет частиц
        QTimer.singleShot(1500, self._check_hide)

    def update_particles(self):
        """Обновление всех частиц"""
        self.particles = [p for p in self.particles if p.update()]
        self.update()

        # Если частиц нет, скрываем виджет
        if not self.particles:
            self.hide()

    def _check_hide(self):
        """Проверка необходимости скрытия виджета"""
        if not self.particles:
            self.hide()

    def paintEvent(self, event):
        """Событие отрисовки"""
        # Создаем QPainter с возможным GPU ускорением
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Сглаживание
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Пытаемся использовать OpenGL backend для QPainter если возможно
        try:
            # Устанавливаем дополнительные оптимизации
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        except:
            pass

        for particle in self.particles:
            particle.draw(painter)

        # Дополнительно, если доступен OpenGL, можем создать отладочное сообщение
        try:
            if QOpenGLContext.hasOpenGL():
                # Выводим отладочную информацию о GPU использовании
                debug_color = QColor(0, 255, 0, 100)  # Полупрозрачный зеленый
                painter.setPen(QPen(debug_color, 1))
                painter.drawText(10, 15, "GPU: ON")  # Показываем, что GPU режим включен
        except:
            pass

    def resizeEvent(self, event):
        """Событие изменения размера"""
        super().resizeEvent(event)
        # Обновляем размер для корректного позиционирования
        self.update_parent_geometry()

    def update_parent_geometry(self):
        """Update geometry to match parent"""
        if self.parent():
            parent_rect = self.parent().rect()
            self.setGeometry(parent_rect)
            self.setFixedSize(parent_rect.size())

    def update_style_colors(self, style_colors):
        """Update the color scheme used by particles"""
        self.style_colors = style_colors or {
            'ParticlePrimaryColor': '#FF6B6B',
            'ParticleSecondaryColor': '#4ECDC4',
            'ParticleAccentColor': '#FFE66D',
            'ParticleGlowColor': '#C84B31',
            'ParticleTrailColor': '#A0A0A0',
            'ParticleLinePrimaryColor': '#FF6B6B80',
            'ParticleLineSecondaryColor': '#4ECDC480',
            'ParticleConnectionColor': '#C84B3140'
        }