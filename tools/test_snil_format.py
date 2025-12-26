import sys
sys.path.insert(0, 'src')
from PyQt5.QtGui import QTextDocument
from snil_highlighter import SNILHighlighter

# Create a document with two lines
text = "Nagatoro says You'll have to wait and see!\nWait 2 seconds\n"

doc = QTextDocument()
doc.setPlainText(text)

h = SNILHighlighter(doc)

# Force rehighlight
h.rehighlight()

# Inspect blocks
for i in range(doc.blockCount()):
    block = doc.findBlockByNumber(i)
    print('Line', i, repr(block.text()))
    layout = block.layout()
    formats = layout.formats()
    for f in formats:
        start = f.start
        length = f.length
        fmt = f.format
        color = fmt.foreground().color().name()
        bold = fmt.fontWeight()
        print(f'  span {start}:{start+length} -> color={color} bold={bold} text={block.text()[start:start+length]!r}')
