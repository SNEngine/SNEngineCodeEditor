from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QLinearGradient

class IfShowVariantNodeRenderer:
    def draw_node(self, painter: QPainter, node, canvas):
        # Get the base color for conditional nodes, similar to standard renderer
        base_color = canvas.type_colors.get('condition', QColor(128, 64, 128))
        body_color = base_color.darker(220)

        # Draw the node body with rounded corners, similar to standard renderer
        painter.setPen(QPen(QColor(10, 10, 10), 1.5))
        painter.setBrush(body_color)
        painter.drawRoundedRect(node.get_rect(), 8.0, 8.0)

        # Draw the header, similar to standard renderer but with specific text
        hdr_rect = QRectF(node.x, node.y, node.width, node.hdr_h)
        painter.setPen(Qt.NoPen)
        painter.setBrush(base_color)
        painter.drawRoundedRect(hdr_rect, 8.0, 8.0)
        painter.drawRect(QRectF(node.x, node.y + node.hdr_h - 5.0, node.width, 5.0))

        # Draw the node type in the header
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(hdr_rect.adjusted(12, 0, -12, 0), Qt.AlignVCenter, "IF SHOW VARIANT")

        # Parse content to extract variants, true and false branches
        content_lines = node.content.split('\n')
        variants_section = []
        true_section = []
        false_section = []

        current_section = None
        for line in content_lines:
            line = line.strip()
            if 'true:' in line.lower():
                current_section = 'true'
            elif 'false:' in line.lower():
                current_section = 'false'
            elif 'variants:' in line.lower() or 'option' in line.lower():
                variants_section.append(line)
            elif current_section == 'true' and line and not line.lower().startswith('endif'):
                true_section.append(line)
            elif current_section == 'false' and line and not line.lower().startswith('endif'):
                false_section.append(line)

        # Draw the node content with branching visualization
        painter.setFont(QFont("Consolas", 10))
        flags = Qt.AlignLeft | Qt.TextWordWrap | Qt.TextWrapAnywhere

        # Create a custom content display that shows the branching
        content_parts = []
        if variants_section:
            content_parts.append("Variants:")
            for variant in [v for v in variants_section if v.lower() != 'variants:']:
                content_parts.append(f"  • {variant}")

        if true_section:
            content_parts.append("True:")
            for line in true_section:
                content_parts.append(f"  {line}")

        if false_section:
            content_parts.append("False:")
            for line in false_section:
                content_parts.append(f"  {line}")

        # Draw the combined content
        display_content = "\n".join(content_parts) if content_parts else node.content
        content_rect = node.get_rect().adjusted(15, node.hdr_h + 12, -15, -12)
        painter.drawText(content_rect, flags, display_content)

        # Draw the connection ports - standard input/output like other nodes
        painter.setBrush(canvas.color_link)
        painter.setPen(QPen(QColor(0, 0, 0, 100), 1.0))

        # Draw the main input port (left side)
        painter.drawEllipse(node.enter_port, 5.0, 5.0)

        # Draw the main output port (right side)
        painter.drawEllipse(node.exit_port, 5.0, 5.0)

        # Show True/False visual indicators inside the node for the branching logic
        # Position True output slightly higher on the right side
        true_exit_pos = node.get_true_port()
        # Position False output slightly lower on the right side
        false_exit_pos = node.get_false_port()

        # Draw visual indicators for True/False (not actual connection ports)
        painter.setBrush(QColor(100, 255, 100, 100))  # Semi-transparent green for True
        painter.setPen(QPen(QColor(100, 255, 100, 150), 1.0))
        painter.drawEllipse(true_exit_pos, 3.0, 3.0)

        painter.setBrush(QColor(255, 100, 100, 100))  # Semi-transparent red for False
        painter.setPen(QPen(QColor(255, 100, 100, 150), 1.0))
        painter.drawEllipse(false_exit_pos, 3.0, 3.0)

        # Draw port labels
        painter.setPen(QColor(200, 200, 200))  # Light gray for visual indicators
        painter.setFont(QFont("Segoe UI", 6))
        painter.drawText(QRectF(true_exit_pos.x() - 8, true_exit_pos.y() - 10, 16, 8), Qt.AlignCenter, "T")
        painter.drawText(QRectF(false_exit_pos.x() - 8, false_exit_pos.y() - 10, 16, 8), Qt.AlignCenter, "F")