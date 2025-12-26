import sys
sys.path.insert(0, 'src')
from snil_highlighter import SNILHighlighter
from PyQt5.QtGui import QTextDocument
h = SNILHighlighter(QTextDocument())
patterns = []
for p,f in h.highlighting_rules:
    try:
        patterns.append(p.pattern())
    except Exception:
        patterns.append(str(p))
print('\n'.join(patterns[:40]))
