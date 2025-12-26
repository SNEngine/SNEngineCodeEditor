"""
Renderer for conditional nodes, particularly for 'if show variant' logic.
This creates a visual representation that clearly shows the branching logic.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen


class ConditionalNodeRenderer:
    """
    Renderer for conditional nodes, particularly for 'if show variant' logic.
    This creates a visual representation that clearly shows the branching logic.
    """
    
    def draw_node(self, painter: QPainter, node, canvas):
        """
        Draw a conditional node with special styling to indicate branching logic.
        
        Args:
            painter: QPainter instance to draw with
            node: The node object to draw
            canvas: The canvas that contains the node
        """
        # Get the base color for conditional nodes
        base_color = canvas.type_colors.get('condition', QColor(128, 64, 128))
        body_color = base_color.darker(220)

        # Draw the node body with special styling for conditional nodes
        painter.setPen(QPen(QColor(10, 10, 10), 1.5))
        painter.setBrush(body_color)
        painter.drawRoundedRect(node.get_rect(), 8.0, 8.0)

        # Draw the header with special styling
        hdr_rect = QRectF(node.x, node.y, node.width, node.hdr_h)
        painter.setPen(Qt.NoPen)
        painter.setBrush(base_color)
        painter.drawRoundedRect(hdr_rect, 8.0, 8.0)
        painter.drawRect(QRectF(node.x, node.y + node.hdr_h - 5.0, node.width, 5.0))

        # Draw the node type in the header
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(hdr_rect.adjusted(12, 0, -12, 0), Qt.AlignVCenter, "CONDITION")

        # Draw the condition content with special formatting
        painter.setFont(QFont("Consolas", 10))
        flags = Qt.AlignLeft | Qt.TextWordWrap | Qt.TextWrapAnywhere
        content_rect = node.get_rect().adjusted(15, node.hdr_h + 12, -15, -12)
        
        # Highlight 'if' and 'show' keywords if present
        content = node.content
        painter.drawText(content_rect, flags, content)

        # Draw special branching indicators
        # Draw a small icon or symbol to indicate this is a conditional node
        branch_indicator_rect = QRectF(node.x + node.width - 20, node.y + 5, 15, 15)
        painter.setBrush(QColor(255, 255, 0))  # Yellow for branching
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))
        painter.drawEllipse(branch_indicator_rect)
        
        # Draw the connection ports
        painter.setBrush(canvas.color_link)
        painter.setPen(QPen(QColor(0, 0, 0, 100), 1.0))
        painter.drawEllipse(node.enter_port, 5.0, 5.0)
        painter.drawEllipse(node.exit_port, 5.0, 5.0)