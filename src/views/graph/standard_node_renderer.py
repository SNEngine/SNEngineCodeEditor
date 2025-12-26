"""
Renderer for standard nodes that appear horizontally in the graph.
This handles the basic node rendering with header, body, and ports.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen


class StandardNodeRenderer:
    """
    Renderer for standard nodes that appear horizontally in the graph.
    This handles the basic node rendering with header, body, and ports.
    """
    
    def draw_node(self, painter: QPainter, node, canvas):
        """
        Draw a standard node with header, body, and connection ports.
        
        Args:
            painter: QPainter instance to draw with
            node: The node object to draw
            canvas: The canvas that contains the node
        """
        # Get the base color based on node type
        base_color = canvas.type_colors.get(node.type, QColor(60, 60, 60))
        body_color = base_color.darker(220)

        # Draw the node body with rounded corners
        painter.setPen(QPen(QColor(10, 10, 10), 1.5))
        painter.setBrush(body_color)
        painter.drawRoundedRect(node.get_rect(), 8.0, 8.0)

        # Draw the header
        hdr_rect = QRectF(node.x, node.y, node.width, node.hdr_h)
        painter.setPen(Qt.NoPen)
        painter.setBrush(base_color)
        painter.drawRoundedRect(hdr_rect, 8.0, 8.0)
        painter.drawRect(QRectF(node.x, node.y + node.hdr_h - 5.0, node.width, 5.0))

        # Draw the node type in the header
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(hdr_rect.adjusted(12, 0, -12, 0), Qt.AlignVCenter, node.type.upper())

        # Draw the node content
        painter.setFont(QFont("Consolas", 10))
        flags = Qt.AlignLeft | Qt.TextWordWrap | Qt.TextWrapAnywhere
        content_rect = node.get_rect().adjusted(15, node.hdr_h + 12, -15, -12)
        painter.drawText(content_rect, flags, node.content)

        # Draw the connection ports
        painter.setBrush(canvas.color_link)
        painter.setPen(QPen(QColor(0, 0, 0, 100), 1.0))
        painter.drawEllipse(node.enter_port, 5.0, 5.0)
        painter.drawEllipse(node.exit_port, 5.0, 5.0)