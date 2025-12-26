"""
Custom QPlainTextEdit with line numbers and particle effects
Based on PyQt5 example for creating a text editor with line numbers
"""
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QFrame, QLabel, QScrollBar
from PyQt5.QtCore import Qt, QRect, pyqtProperty
import re
from PyQt5.QtGui import QPainter, QColor, QTextFormat, QFontMetrics, QTextCursor
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
from .particle_system import ParticleEffect


class LineNumberArea(QFrame):
    """Widget to display line numbers"""

    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor
        self.setFrameShape(QFrame.NoFrame)  # Remove any frame
        # Устанавливаем стиль фона из темы
        secondary_bg = editor.styles.get('DarkTheme', {}).get('SecondaryBackground', '#2A2A2A')
        self.setStyleSheet(f"background-color: {secondary_bg};")

    def sizeHint(self):
        from PyQt5.QtCore import QSize
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_paint_event(event)

    def mousePressEvent(self, event):
        # Determine which block was clicked and forward to editor to toggle folding
        y = event.y()
        block = self.code_editor.firstVisibleBlock()
        top = self.code_editor.blockBoundingGeometry(block).translated(self.code_editor.contentOffset()).top()
        while block.isValid():
            bottom = top + self.code_editor.blockBoundingRect(block).height()
            if y >= top and y <= bottom:
                self.code_editor.toggle_fold_at_line(block.blockNumber())
                return
            block = block.next()
            top = bottom


class CodeEditor(QPlainTextEdit):
    """Custom text editor with line numbers"""

    def __init__(self, styles=None, settings_manager=None):
        super().__init__()

        self.styles = styles or {}
        self.settings_manager = settings_manager

        # Create line number area
        self.line_numbers = LineNumberArea(self)

        # Create particle effect system
        try:
            from .particle_system import ParticleEffect
            # Get particle colors from styles, with defaults
            particle_colors = {
                'ParticlePrimaryColor': self.styles.get('DarkTheme', {}).get('ParticlePrimaryColor', '#FF6B6B'),
                'ParticleSecondaryColor': self.styles.get('DarkTheme', {}).get('ParticleSecondaryColor', '#4ECDC4'),
                'ParticleAccentColor': self.styles.get('DarkTheme', {}).get('ParticleAccentColor', '#FFE66D'),
                'ParticleGlowColor': self.styles.get('DarkTheme', {}).get('ParticleGlowColor', '#C84B31'),
                'ParticleTrailColor': self.styles.get('DarkTheme', {}).get('ParticleTrailColor', '#A0A0A0'),
                'ParticleLinePrimaryColor': self.styles.get('DarkTheme', {}).get('ParticleLinePrimaryColor', '#FF6B6B80'),
                'ParticleLineSecondaryColor': self.styles.get('DarkTheme', {}).get('ParticleLineSecondaryColor', '#4ECDC480'),
                'ParticleConnectionColor': self.styles.get('DarkTheme', {}).get('ParticleConnectionColor', '#C84B3140')
            }
            self.particle_effect = ParticleEffect(self, style_colors=particle_colors)
            self.particle_effect.hide()  # Изначально скрыт

            # Initialize the particle effect geometry to match the editor
            self.particle_effect.update_parent_geometry()
        except ImportError:
            self.particle_effect = None  # Disable particles if import fails

        # Initialize line number area width
        self.update_line_number_area_width(0)

        # Set font for line numbers area to match editor
        self.line_numbers.setFont(self.font())

        # Get highlight color from styles for current line number
        self.current_line_color = self.styles.get('DarkTheme', {}).get('ActiveLineNumberColor', '#C84B31')  # Default to highlight color

        # Animation for current line highlighting
        self._current_line_opacity = 0.0  # Initial opacity for animation
        self.current_line_animation = QPropertyAnimation(self, b"current_line_opacity")
        self.current_line_animation.setDuration(150)  # Animation duration in ms
        self.current_line_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Timer for pulsing animation when highlighting is enabled
        from PyQt5.QtCore import QTimer
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_value = 0.0  # Current pulse value (0.0 to 1.0)
        self._pulse_direction = 0.02  # Pulse increment/decrement value

        # Connect signals - correct PyQt5 signals (after initialization)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)  # Highlight current line when cursor moves
        self.verticalScrollBar().valueChanged.connect(self.update_line_numbers_scroll)

        # Connect text input event to particle effect
        self.textChanged.connect(self.on_text_changed)

        # Folding support: compute fold ranges for functions and 'name:' branches and track folded state
        self._fold_ranges = {}  # start_block_number -> end_block_number
        self._folded = set()    # set of start_block_numbers that are currently folded
        # Recompute fold ranges when text changes or blocks change
        self.textChanged.connect(self.compute_fold_ranges)
        self.blockCountChanged.connect(self.compute_fold_ranges)

        # Expose a click handler on the gutter (handled by LineNumberArea.mousePressEvent)
        # LineNumberArea will call editor.toggle_fold_at_line(block_number) when clicked

    def resizeEvent(self, event):
        """Handle resize events to ensure particle effect is properly sized"""
        # Call the original resize event
        super().resizeEvent(event)

        # Update particle effect geometry to match new editor size
        if hasattr(self, 'particle_effect'):
            self.particle_effect.update_parent_geometry()

    def line_number_area_width(self):
        """Calculate the width needed for line numbers"""
        digits = len(str(max(1, self.blockCount())))
        # Увеличиваем базовый отступ для большего расстояния между номерами строк и текстом
        space = 25 + self.fontMetrics().width('9') * digits
        return space

    def update_line_number_area_width(self, new_block_count):
        """Update the width of the line number area"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Update the line number area"""
        if dy:
            self.line_numbers.scroll(0, dy)
        else:
            # Update only the changed region
            self.line_numbers.update(0, rect.y(), self.line_numbers.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def highlight_current_line(self):
        """Highlight the current line in the line number area with animation"""
        # Check if line highlighting is enabled in settings
        if (self.settings_manager and
            hasattr(self.settings_manager, 'highlight_current_line') and
            not self.settings_manager.highlight_current_line):
            # If highlighting is disabled, stop the pulse timer and clear the highlight
            self.pulse_timer.stop()
            self.current_line_animation.stop()
            self.current_line_animation.setStartValue(self._current_line_opacity)
            self.current_line_animation.setEndValue(0.0)
            self.current_line_animation.start()
            return

        # If highlighting is enabled, start the pulsing animation
        self.current_line_animation.stop()
        self._pulse_value = 1.0  # Start with full opacity
        self._pulse_direction = -0.02  # Start decreasing
        if not self.pulse_timer.isActive():
            self.pulse_timer.start(30)  # Update every 30ms for smooth pulsing

    def resizeEvent(self, event):
        """Handle resize events to update line number area"""
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.line_numbers.setGeometry(QRect(cr.left(), cr.top(),
                                          self.line_number_area_width(), cr.height()))

    def line_number_paint_event(self, event):
        """Paint the line numbers"""
        painter = QPainter(self.line_numbers)

        # Fill the background
        background_color = self.styles.get('DarkTheme', {}).get('SecondaryBackground', '#2A2A2A')
        painter.fillRect(event.rect(), QColor(background_color))

        # Get the current line number (cursor position)
        current_line = self.textCursor().blockNumber() + 1

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                # Check if this is the current line (where cursor is located)
                is_current_line = (block_number + 1 == current_line)

                # Check if line highlighting is enabled in settings
                highlight_enabled = True
                if (self.settings_manager and
                    hasattr(self.settings_manager, 'highlight_current_line')):
                    highlight_enabled = self.settings_manager.highlight_current_line

                # Draw background for the current line if it's the active line AND highlighting is enabled
                if is_current_line and highlight_enabled:
                    # Highlight the current line with the highlight color and animated opacity
                    highlight_color = QColor(self.current_line_color)
                    # Use the animated opacity (convert from 0.0-1.0 to 0-255 alpha)
                    alpha = int(self.current_line_opacity * 100)  # Use the animated opacity value
                    highlight_color.setAlpha(alpha)
                    painter.fillRect(0, int(top), int(self.line_numbers.width()),
                                   int(self.fontMetrics().height()), highlight_color)
                elif is_current_line and not highlight_enabled:
                    # If current line highlighting is disabled, draw the same as other lines
                    # Calculate alternating background color based on line number for current line when highlighting is disabled
                    if (block_number + 1) % 2 == 0:
                        # Even line numbers get a slightly different background
                        alt_bg_color = QColor(self.styles.get('DarkTheme', {}).get('Background', '#1A1A1A'))
                        alt_bg_color.setAlpha(100)  # Make it semi-transparent
                        painter.fillRect(0, int(top), int(self.line_numbers.width()),
                                       int(self.fontMetrics().height()), alt_bg_color)
                else:
                    # Calculate alternating background color based on line number for non-current lines
                    if (block_number + 1) % 2 == 0:
                        # Even line numbers get a slightly different background
                        alt_bg_color = QColor(self.styles.get('DarkTheme', {}).get('Background', '#1A1A1A'))
                        alt_bg_color.setAlpha(100)  # Make it semi-transparent
                        painter.fillRect(0, int(top), int(self.line_numbers.width()),
                                       int(self.fontMetrics().height()), alt_bg_color)

                # Check if line highlighting is enabled in settings
                highlight_enabled = True
                if (self.settings_manager and
                    hasattr(self.settings_manager, 'highlight_current_line')):
                    highlight_enabled = self.settings_manager.highlight_current_line

                # Set text color based on whether this is the current line
                if is_current_line and highlight_enabled:
                    # Use the current line highlight color for the text when highlighting is enabled
                    text_color = QColor(self.current_line_color)
                elif is_current_line and not highlight_enabled:
                    # Use the default line number color when highlighting is disabled
                    # (per user request: the background should be normal, so should be the text)
                    text_color = QColor(self.styles.get('DarkTheme', {}).get('StatusDefault', '#999999'))
                else:
                    # Use foreground color from styles for other line numbers
                    text_color = QColor(self.styles.get('DarkTheme', {}).get('StatusDefault', '#999999'))

                painter.setPen(text_color)  # Color for line numbers

                font = self.font()
                font.setPointSize(font.pointSize() - 1)  # Slightly smaller font for line numbers
                painter.setFont(font)

                # Draw the line number with padding
                painter.drawText(3, int(top), int(self.line_numbers.width()) - 6,
                               int(self.fontMetrics().height()),
                               Qt.AlignRight | Qt.AlignVCenter, number)

                # Draw fold markers (triangle) for foldable block starts
                block_num = block_number
                if block_num in self._fold_ranges:
                    folded = (block_num in self._folded)
                    icon_char = '►' if folded else '▼'
                    painter.setPen(QColor(self.styles.get('DarkTheme', {}).get('StatusDefault', '#999999')))
                    painter.drawText(4, int(top), 12, int(self.fontMetrics().height()), Qt.AlignLeft | Qt.AlignVCenter, icon_char)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    @pyqtProperty(float)
    def current_line_opacity(self):
        # Return the base opacity with pulse effect when highlighting is enabled
        if (self.settings_manager and
            hasattr(self.settings_manager, 'highlight_current_line') and
            self.settings_manager.highlight_current_line):
            # When pulsing, use the pulse value (with safety check for initialization)
            if hasattr(self, '_pulse_value'):
                return self._pulse_value
            else:
                # If _pulse_value is not yet initialized, return full opacity
                return 1.0
        else:
            # When not highlighting, return the set opacity value
            return self._current_line_opacity

    @current_line_opacity.setter
    def current_line_opacity(self, value):
        # Only set the base opacity when not using the pulse animation
        self._current_line_opacity = value
        self.line_numbers.update()  # Trigger repaint when opacity changes

    def _update_pulse(self):
        """Update the pulse animation"""
        # Update pulse value
        self._pulse_value += self._pulse_direction

        # Reverse direction when reaching limits
        if self._pulse_value >= 1.0:
            self._pulse_value = 1.0
            self._pulse_direction = -0.02  # Start decreasing
        elif self._pulse_value <= 0.3:  # Minimum opacity for pulsing
            self._pulse_value = 0.3
            self._pulse_direction = 0.02  # Start increasing

        # Trigger repaint to update the highlight
        self.line_numbers.update()

    def update_line_numbers_scroll(self, value):
        """Sync line number area with editor scrolling"""
        self.line_numbers.update()

    def setPlainText(self, text):
        """Override setPlainText to ensure line numbers are updated"""
        super().setPlainText(text)
        self.update_line_number_area_width(0)

    def insertFromMimeData(self, source):
        """Override to make sure line numbers are updated after paste operations"""
        super().insertFromMimeData(source)
        self.update_line_number_area_width(0)

    def setFont(self, font):
        """Override setFont to update line numbers font as well"""
        super().setFont(font)
        self.line_numbers.setFont(font)
        self.update_line_number_area_width(0)

    def on_text_changed(self):
        """Событие изменения текста - запускает эффект частиц если включено в настройках"""
        # Проверяем, включены ли частицы в настройках
        if (self.settings_manager and
            hasattr(self.settings_manager, 'typing_particles_enabled') and
            not self.settings_manager.typing_particles_enabled):
            return  # Не создаем частицы, если опция отключена

        # Проверяем, что particle_effect доступен
        if not self.particle_effect:
            return

        # Получаем текущую позицию курсора
        cursor = self.textCursor()
        current_pos = cursor.position()

        # Проверяем, есть ли предыдущий символ (чтобы не создавать частицы при удалении)
        if current_pos > 0 and len(self.toPlainText()) > 0:
            # Создаем новый курсор и устанавливаем его на позицию предыдущего символа
            prev_cursor = QTextCursor(cursor)
            prev_cursor.setPosition(current_pos - 1, QTextCursor.MoveAnchor)

            # Получаем прямоугольник для позиции предыдущего символа
            cursor_rect = self.cursorRect(prev_cursor)

            # Преобразуем координаты в координаты виджета
            pos = self.mapToGlobal(cursor_rect.topLeft())
            local_pos = self.mapFromGlobal(pos)

            # Calculate the absolute position within the document, considering horizontal scroll
            # The particle effect is a child widget that covers the entire editor area,
            # so we need to position particles relative to the editor's visible area
            content_offset = self.contentOffset()
            x_pos = local_pos.x() + cursor_rect.width() - content_offset.x()
            y_pos = local_pos.y() - content_offset.y()

            # Ensure the particle position is within the editor bounds (but allow positions beyond width
            # for long lines that extend beyond visible area)
            x_pos = max(0, x_pos)
            y_pos = max(0, y_pos)

            # Добавляем частицы в позицию последнего символа
            self.particle_effect.add_particles_at(x_pos, y_pos)

            # Обновляем геометрию эффекта частиц, чтобы она соответствовала родительскому элементу
            self.particle_effect.update_parent_geometry()

    def update_font_from_settings(self):
        """Update the editor font based on settings manager"""
        if self.settings_manager:
            font_family = self.settings_manager.font_family
            font_size = self.settings_manager.font_size

            # Create a new font and apply it to the editor
            current_font = self.font()
            current_font.setFamily(font_family)
            current_font.setPointSize(font_size)
            self.setFont(current_font)

            # Also update the line numbers font if line numbers are enabled
            show_line_numbers = getattr(self.settings_manager, 'show_line_numbers', True)
            if show_line_numbers:
                self.line_numbers.setFont(current_font)
                # Update the viewport margins to accommodate the new font size for line numbers
                self._update_line_numbers_layout()
            else:
                # If line numbers are disabled, make sure the editor has no left margin
                self.setViewportMargins(0, 0, 0, 0)
                # Still update the font for line numbers area so it's ready if enabled later
                self.line_numbers.setFont(current_font)

    def _update_line_numbers_layout(self):
        """Helper method to update line numbers layout after font changes"""
        # Recalculate and update the line number area width
        self.update_line_number_area_width(0)

        # Update the line numbers area geometry to match new font metrics
        if self.isVisible():
            cr = self.contentsRect()
            self.line_numbers.setGeometry(QRect(cr.left(), cr.top(),
                                              self.line_number_area_width(), cr.height()))

    def update_line_numbers_visibility(self):
        """Update the visibility of line numbers based on settings"""
        if self.settings_manager:
            show_line_numbers = self.settings_manager.show_line_numbers
            if show_line_numbers:
                self.line_numbers.show()
                # Update the viewport margins to make space for line numbers
                self._update_line_numbers_layout()
            else:
                self.line_numbers.hide()
                # Remove the margin for line numbers
                self.setViewportMargins(0, 0, 0, 0)

    def compute_fold_ranges(self):
        """Compute fold ranges for functions (function..end) and 'name:' YAML branches"""
        doc = self.document()
        block = doc.firstBlock()
        fold_ranges = {}
        # Simple stack for function blocks
        func_stack = []
        # Simple stack for If Show Variant blocks
        if_stack = []
        line_no = 0
        while block.isValid():
            text = block.text()
            stripped = text.strip()
            # Function start
            if re.match(r'^\s*(function|call)\b', text, re.IGNORECASE):
                func_stack.append((line_no, text))
            # Function end
            if re.match(r'^\s*end\b', text, re.IGNORECASE) and func_stack:
                start, _ = func_stack.pop()
                fold_ranges[start] = line_no

            # If Show Variant start -> push to stack until 'endif'
            if re.match(r'^\s*If\s+Show\s+Variant\b', text, re.IGNORECASE):
                if_stack.append((line_no, text))
            if re.match(r'^\s*endif\b', text, re.IGNORECASE) and if_stack:
                start, _ = if_stack.pop()
                fold_ranges[start] = line_no

            # name: (YAML dialog header) -> fold until next '---' separator, next name:, or EOF
            m = re.match(r'^(\s*)name\s*:\s*.*', text, re.IGNORECASE)
            if m:
                # Find end by looking for separator '---' or next 'name:' header or EOF
                search_block = block.next()
                end_line = line_no
                i = line_no + 1
                while search_block.isValid():
                    next_text = search_block.text()
                    # If we encounter separator or another name:, stop
                    if re.match(r'^\s*---\s*$', next_text) or re.match(r'^(\s*)name\s*:\s*.*', next_text, re.IGNORECASE):
                        break
                    end_line = i
                    search_block = search_block.next()
                    i += 1
                # Only create fold range if there is at least one line to fold
                if end_line > line_no:
                    fold_ranges[line_no] = end_line
            block = block.next()
            line_no += 1
        self._fold_ranges = fold_ranges
        # Remove folded states that are no longer valid
        self._folded = set(s for s in self._folded if s in self._fold_ranges)
        # Redraw gutter
        self.line_numbers.update()

    def toggle_fold_at_line(self, block_number: int):
        """Toggle fold at a given block number if a fold range exists"""
        if block_number not in self._fold_ranges:
            return
        if block_number in self._folded:
            # Unfold
            self._apply_fold(block_number, unfold=True)
            self._folded.remove(block_number)
        else:
            # Fold
            self._apply_fold(block_number, unfold=False)
            self._folded.add(block_number)
        # Repaint gutter and layout
        self.line_numbers.update()
        self.update()

    def _apply_fold(self, start: int, unfold: bool = False):
        """Apply folding or unfolding by changing block visibility"""
        end = self._fold_ranges.get(start)
        if end is None or end <= start:
            return
        doc = self.document()
        for n in range(start + 1, end + 1):
            block = doc.findBlockByNumber(n)
            if not block.isValid():
                continue
            block.setVisible(unfold)
            # Mark contents dirty to force layout (length of block text is sufficient)
            doc.markContentsDirty(block.position(), len(block.text()))
        # Force layout update
        self.updateGeometry()
        self.viewport().update()

    def update_highlight_current_line_setting(self):
        """Update the line highlighting based on settings change"""
        if self.settings_manager:
            highlight_enabled = self.settings_manager.highlight_current_line
            if highlight_enabled:
                # If highlighting is enabled, start the pulsing animation
                self._pulse_value = 1.0  # Start with full opacity
                self._pulse_direction = -0.02  # Start decreasing
                if not self.pulse_timer.isActive():
                    self.pulse_timer.start(30)  # Update every 30ms for smooth pulsing
            else:
                # If highlighting is disabled, stop the pulse timer
                self.pulse_timer.stop()
                # Clear the highlight with animation
                self.current_line_animation.stop()
                self.current_line_animation.setStartValue(self._current_line_opacity)
                self.current_line_animation.setEndValue(0.0)
                self.current_line_animation.start()

    def update_line_number_styles(self):
        """Update styles for the line number area"""
        secondary_bg = self.styles.get('DarkTheme', {}).get('SecondaryBackground', '#2A2A2A')
        self.current_line_color = self.styles.get('DarkTheme', {}).get('ActiveLineNumberColor', '#C84B31')  # Update the highlight color
        self.line_numbers.setStyleSheet(f"background-color: {secondary_bg};")

    def __del__(self):
        """Cleanup when the CodeEditor is destroyed"""
        if self.pulse_timer:
            self.pulse_timer.stop()

    def update_particle_colors(self, styles):
        """Update particle colors from new styles"""
        self.styles = styles
        # Update the current line highlight color from the new styles
        self.current_line_color = styles.get('DarkTheme', {}).get('ActiveLineNumberColor', '#C84B31')
        if self.particle_effect:
            particle_colors = {
                'ParticlePrimaryColor': styles.get('DarkTheme', {}).get('ParticlePrimaryColor', '#FF6B6B'),
                'ParticleSecondaryColor': styles.get('DarkTheme', {}).get('ParticleSecondaryColor', '#4ECDC4'),
                'ParticleAccentColor': styles.get('DarkTheme', {}).get('ParticleAccentColor', '#FFE66D'),
                'ParticleGlowColor': styles.get('DarkTheme', {}).get('ParticleGlowColor', '#C84B31'),
                'ParticleTrailColor': styles.get('DarkTheme', {}).get('ParticleTrailColor', '#A0A0A0'),
                'ParticleLinePrimaryColor': styles.get('DarkTheme', {}).get('ParticleLinePrimaryColor', '#FF6B6B80'),
                'ParticleLineSecondaryColor': styles.get('DarkTheme', {}).get('ParticleLineSecondaryColor', '#4ECDC480'),
                'ParticleConnectionColor': styles.get('DarkTheme', {}).get('ParticleConnectionColor', '#C84B3140')
            }
            self.particle_effect.update_style_colors(particle_colors)