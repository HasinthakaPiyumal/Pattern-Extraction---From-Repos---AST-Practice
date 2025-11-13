# Cluster 147

class DragBar(QWidget):
    """Custom drag bar for frameless window"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.dragging = False
        self.drag_position = QPoint()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        self.title_label = QLabel('⚓ FINCEPT MARITIME MAP')
        self.title_label.setStyleSheet('color: #ff8c00; font-weight: bold; font-size: 11px;')
        layout.addWidget(self.title_label)
        layout.addStretch()
        min_btn = QPushButton('_')
        min_btn.setFixedSize(25, 20)
        min_btn.clicked.connect(parent.showMinimized)
        min_btn.setStyleSheet('\n            QPushButton { background: #333; color: #fff; border: none; font-weight: bold; }\n            QPushButton:hover { background: #555; }\n        ')
        layout.addWidget(min_btn)
        max_btn = QPushButton('□')
        max_btn.setFixedSize(25, 20)
        max_btn.clicked.connect(self.toggle_maximize)
        max_btn.setStyleSheet('\n            QPushButton { background: #333; color: #fff; border: none; font-weight: bold; }\n            QPushButton:hover { background: #555; }\n        ')
        layout.addWidget(max_btn)
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(25, 20)
        close_btn.clicked.connect(parent.close_application)
        close_btn.setStyleSheet('\n            QPushButton { background: #d32f2f; color: #fff; border: none; font-weight: bold; }\n            QPushButton:hover { background: #f44336; }\n        ')
        layout.addWidget(close_btn)
        self.setStyleSheet('background: #1a1a1a; border-bottom: 1px solid #ff8c00;')
        self.setFixedHeight(24)

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.parent.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False
        event.accept()

def toggle_maximize(self):
    if self.parent.isMaximized():
        self.parent.showNormal()
    else:
        self.parent.showMaximized()

