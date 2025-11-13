# Cluster 3

class MainWindow(QMainWindow):

    def __init__(self, store, anthropic_client):
        super().__init__()
        self.store = store
        self.anthropic_client = anthropic_client
        self.prompt_manager = PromptManager()
        self.settings = QSettings('Grunty', 'Preferences')
        self.dark_mode = self.settings.value('dark_mode', True, type=bool)
        self.voice_controller = VoiceController()
        self.voice_controller.voice_input_signal.connect(self.handle_voice_input)
        self.voice_controller.status_signal.connect(self.update_status)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Voice control ready')
        if self.store.error and 'ANTHROPIC_API_KEY not found' in self.store.error:
            self.show_api_key_dialog()
        self.setWindowTitle('Grunty 👨💻')
        self.setGeometry(100, 100, 400, 600)
        self.setMinimumSize(400, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui()
        self.setup_tray()
        self.setup_shortcuts()

    def show_api_key_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('API Key Required')
        dialog.setFixedWidth(400)
        layout = QVBoxLayout()
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('fa5s.key', color='#4CAF50').pixmap(32, 32))
        title_layout.addWidget(icon_label)
        title_label = QLabel('Anthropic API Key Required')
        title_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #4CAF50;')
        title_layout.addWidget(title_label)
        layout.addLayout(title_layout)
        desc_label = QLabel('Please enter your Anthropic API key to continue. You can find this in your Anthropic dashboard.')
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet('color: #666; margin: 10px 0;')
        layout.addWidget(desc_label)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText('sk-ant-...')
        self.api_key_input.setStyleSheet('\n            QLineEdit {\n                padding: 10px;\n                border: 2px solid #4CAF50;\n                border-radius: 5px;\n                font-size: 14px;\n            }\n        ')
        layout.addWidget(self.api_key_input)
        save_btn = QPushButton('Save API Key')
        save_btn.setStyleSheet('\n            QPushButton {\n                background-color: #4CAF50;\n                color: white;\n                border: none;\n                padding: 10px;\n                border-radius: 5px;\n                font-size: 14px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #45a049;\n            }\n        ')
        save_btn.clicked.connect(lambda: self.save_api_key(dialog))
        layout.addWidget(save_btn)
        dialog.setLayout(layout)
        dialog.exec()

    def save_api_key(self, dialog):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            return
        with open('.env', 'w') as f:
            f.write(f'ANTHROPIC_API_KEY={api_key}')
        self.store = Store()
        self.anthropic_client = AnthropicClient()
        dialog.accept()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        central_widget.setLayout(main_layout)
        self.container = QWidget()
        self.container.setObjectName('container')
        container_layout = QVBoxLayout()
        container_layout.setSpacing(0)
        self.container.setLayout(container_layout)
        title_bar = QWidget()
        title_bar.setObjectName('titleBar')
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 5, 10, 5)
        title_label = QLabel('Grunty 🤖')
        title_label.setObjectName('titleLabel')
        title_bar_layout.addWidget(title_label)
        file_menu = QMenu('File')
        new_task_action = QAction('New Task', self)
        new_task_action.setShortcut('Ctrl+N')
        edit_prompt_action = QAction('Edit System Prompt', self)
        edit_prompt_action.setShortcut('Ctrl+E')
        edit_prompt_action.triggered.connect(self.show_prompt_dialog)
        quit_action = QAction('Quit', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.quit_application)
        file_menu.addAction(new_task_action)
        file_menu.addAction(edit_prompt_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)
        file_button = QPushButton('File')
        file_button.setObjectName('menuButton')
        file_button.clicked.connect(lambda: file_menu.exec(file_button.mapToGlobal(QPoint(0, file_button.height()))))
        title_bar_layout.addWidget(file_button)
        title_bar_layout.addStretch()
        self.theme_button = QPushButton()
        self.theme_button.setObjectName('titleBarButton')
        self.theme_button.clicked.connect(self.toggle_theme)
        self.update_theme_button()
        title_bar_layout.addWidget(self.theme_button)
        minimize_button = QPushButton('−')
        minimize_button.setObjectName('titleBarButton')
        minimize_button.clicked.connect(self.showMinimized)
        title_bar_layout.addWidget(minimize_button)
        close_button = QPushButton('×')
        close_button.setObjectName('titleBarButton')
        close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(close_button)
        container_layout.addWidget(title_bar)
        self.action_log = QTextEdit()
        self.action_log.setReadOnly(True)
        self.action_log.setStyleSheet('\n            QTextEdit {\n                background-color: #262626;\n                border: none;\n                border-radius: 0;\n                color: #ffffff;\n                padding: 16px;\n                font-family: Inter;\n                font-size: 13px;\n            }\n        ')
        container_layout.addWidget(self.action_log, stretch=1)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet('\n            QProgressBar {\n                border: none;\n                background-color: #262626;\n                height: 2px;\n                margin: 0;\n            }\n            QProgressBar::chunk {\n                background-color: #4CAF50;\n            }\n        ')
        self.progress_bar.hide()
        container_layout.addWidget(self.progress_bar)
        input_section = QWidget()
        input_section.setObjectName('input_section')
        input_section.setStyleSheet('\n            QWidget {\n                background-color: #1e1e1e;\n                border-top: 1px solid #333333;\n            }\n        ')
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(12)
        input_section.setLayout(input_layout)
        self.input_area = QTextEdit()
        self.input_area.setPlaceholderText('What can I do for you today?')
        self.input_area.setFixedHeight(100)
        self.input_area.setStyleSheet('\n            QTextEdit {\n                background-color: #262626;\n                border: 1px solid #333333;\n                border-radius: 8px;\n                color: #ffffff;\n                padding: 12px;\n                font-family: Inter;\n                font-size: 14px;\n                selection-background-color: #4CAF50;\n            }\n            QTextEdit:focus {\n                border: 1px solid #4CAF50;\n            }\n        ')
        self.input_area.textChanged.connect(self.update_run_button)
        input_layout.addWidget(self.input_area)
        control_layout = QHBoxLayout()
        self.run_button = QPushButton(qta.icon('fa5s.play', color='white'), 'Start')
        self.stop_button = QPushButton(qta.icon('fa5s.stop', color='white'), 'Stop')
        self.run_button.clicked.connect(self.run_agent)
        self.stop_button.clicked.connect(self.stop_agent)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        for button in (self.run_button, self.stop_button):
            button.setFixedHeight(40)
            if button == self.run_button:
                button.setStyleSheet('\n                    QPushButton {\n                        background-color: #4CAF50;\n                        color: white;\n                        border: none;\n                        border-radius: 8px;\n                        padding: 0 24px;\n                        font-family: Inter;\n                        font-size: 14px;\n                        font-weight: bold;\n                    }\n                    QPushButton:hover {\n                        background-color: #45a049;\n                    }\n                    QPushButton:disabled {\n                        background-color: #333333;\n                        color: #666666;\n                    }\n                ')
            else:
                button.setStyleSheet('\n                    QPushButton {\n                        background-color: #ff4444;\n                        color: white;\n                        border: none;\n                        border-radius: 8px;\n                        padding: 0 24px;\n                        font-family: Inter;\n                        font-size: 14px;\n                        font-weight: bold;\n                    }\n                    QPushButton:hover {\n                        background-color: #ff3333;\n                    }\n                    QPushButton:disabled {\n                        background-color: #333333;\n                        color: #666666;\n                    }\n                ')
            control_layout.addWidget(button)
        self.voice_button = QPushButton(qta.icon('fa5s.microphone', color='white'), 'Voice')
        self.voice_button.setFixedHeight(40)
        self.voice_button.setStyleSheet('\n            QPushButton {\n                background-color: #4CAF50;\n                color: white;\n                border: none;\n                border-radius: 8px;\n                padding: 0 24px;\n                font-family: Inter;\n                font-size: 14px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #45a049;\n            }\n            QPushButton:checked {\n                background-color: #ff4444;\n            }\n        ')
        self.voice_button.setCheckable(True)
        self.voice_button.clicked.connect(self.toggle_voice_control)
        control_layout.addWidget(self.voice_button)
        input_layout.addLayout(control_layout)
        container_layout.addWidget(input_section)
        main_layout.addWidget(self.container)
        self.apply_theme()

    def update_theme_button(self):
        if self.dark_mode:
            self.theme_button.setIcon(qta.icon('fa5s.sun', color='white'))
            self.theme_button.setToolTip('Switch to Light Mode')
        else:
            self.theme_button.setIcon(qta.icon('fa5s.moon', color='black'))
            self.theme_button.setToolTip('Switch to Dark Mode')

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.settings.setValue('dark_mode', self.dark_mode)
        self.update_theme_button()
        self.apply_theme()

    def apply_theme(self):
        colors = {'bg': '#1a1a1a' if self.dark_mode else '#ffffff', 'text': '#ffffff' if self.dark_mode else '#000000', 'button_bg': '#333333' if self.dark_mode else '#f0f0f0', 'button_text': '#ffffff' if self.dark_mode else '#000000', 'button_hover': '#4CAF50' if self.dark_mode else '#e0e0e0', 'border': '#333333' if self.dark_mode else '#e0e0e0'}
        container_style = f'\n            QWidget#container {{\n                background-color: {colors['bg']};\n                border-radius: 12px;\n                border: 1px solid {colors['border']};\n            }}\n        '
        self.container.setStyleSheet(container_style)
        self.findChild(QLabel, 'titleLabel').setStyleSheet(f'color: {colors['text']}; padding: 5px;')
        self.action_log.setStyleSheet(f'\n            QTextEdit {{\n                background-color: {colors['bg']};\n                border: none;\n                border-radius: 0;\n                color: {colors['text']};\n                padding: 16px;\n                font-family: Inter;\n                font-size: 13px;\n            }}\n        ')
        self.input_area.setStyleSheet(f'\n            QTextEdit {{\n                background-color: {colors['bg']};\n                border: 1px solid {colors['border']};\n                border-radius: 8px;\n                color: {colors['text']};\n                padding: 12px;\n                font-family: Inter;\n                font-size: 14px;\n                selection-background-color: {colors['button_hover']};\n            }}\n            QTextEdit:focus {{\n                border: 1px solid {colors['button_hover']};\n            }}\n        ')
        self.progress_bar.setStyleSheet(f'\n            QProgressBar {{\n                border: none;\n                background-color: {colors['bg']};\n                height: 2px;\n                margin: 0;\n            }}\n            QProgressBar::chunk {{\n                background-color: {colors['button_hover']};\n            }}\n        ')
        input_section_style = f'\n            QWidget {{\n                background-color: {colors['button_bg']};\n                border-top: 1px solid {colors['border']};\n            }}\n        '
        self.findChild(QWidget, 'input_section').setStyleSheet(input_section_style)
        window_control_style = f'\n            QPushButton {{\n                color: {colors['button_text']};\n                background-color: transparent;\n                border-radius: 8px;\n                padding: 4px 12px;\n                font-weight: bold;\n            }}\n            QPushButton:hover {{\n                background-color: {colors['button_hover']};\n            }}\n        '
        for button in [self.theme_button, self.findChild(QPushButton, 'menuButton'), self.findChild(QPushButton, 'titleBarButton')]:
            if button:
                button.setStyleSheet(window_control_style)
        if self.dark_mode:
            self.theme_button.setIcon(qta.icon('fa5s.sun', color=colors['button_text']))
        else:
            self.theme_button.setIcon(qta.icon('fa5s.moon', color=colors['button_text']))
        if hasattr(self, 'tray_icon') and self.tray_icon.contextMenu():
            self.tray_icon.contextMenu().setStyleSheet(f'\n                QMenu {{\n                    background-color: {colors['bg']};\n                    color: {colors['text']};\n                    border: 1px solid {colors['border']};\n                    border-radius: 6px;\n                    padding: 5px;\n                }}\n                QMenu::item {{\n                    padding: 8px 25px 8px 8px;\n                    border-radius: 4px;\n                }}\n                QMenu::item:selected {{\n                    background-color: {colors['button_hover']};\n                    color: white;\n                }}\n                QMenu::separator {{\n                    height: 1px;\n                    background: {colors['border']};\n                    margin: 5px 0px;\n                }}\n            ')

    def update_run_button(self):
        self.run_button.setEnabled(bool(self.input_area.toPlainText().strip()))

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = qta.icon('fa5s.robot', scale_factor=1.5, color='white')
        self.tray_icon.setIcon(icon)
        tray_menu = QMenu()
        title_action = tray_menu.addAction('Grunty 👨🏽\u200d💻')
        title_action.setEnabled(False)
        tray_menu.addSeparator()
        new_task = tray_menu.addAction(qta.icon('fa5s.plus', color='white'), 'New Task')
        new_task.triggered.connect(self.show)
        toggle_action = tray_menu.addAction(qta.icon('fa5s.eye', color='white'), 'Show/Hide')
        toggle_action.triggered.connect(self.toggle_window)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction(qta.icon('fa5s.power-off', color='white'), 'Quit')
        quit_action.triggered.connect(self.quit_application)
        tray_menu.setStyleSheet('\n            QMenu {\n                background-color: #333333;\n                color: white;\n                border: 1px solid #444444;\n                border-radius: 6px;\n                padding: 5px;\n            }\n            QMenu::item {\n                padding: 8px 25px 8px 8px;\n                border-radius: 4px;\n            }\n            QMenu::item:selected {\n                background-color: #4CAF50;\n            }\n            QMenu::separator {\n                height: 1px;\n                background: #444444;\n                margin: 5px 0px;\n            }\n        ')
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.showMessage('Grunty is running', 'Click the robot icon in the menu bar to get started!', QSystemTrayIcon.MessageIcon.Information, 3000)
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window()

    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def run_agent(self):
        instructions = self.input_area.toPlainText()
        if not instructions:
            self.update_log('Please enter instructions before running the agent.')
            return
        self.store.set_instructions(instructions)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.show()
        self.action_log.clear()
        self.input_area.clear()
        self.agent_thread = AgentThread(self.store)
        self.agent_thread.update_signal.connect(self.update_log)
        self.agent_thread.finished_signal.connect(self.agent_finished)
        self.agent_thread.start()

    def stop_agent(self):
        self.store.stop_run()
        self.stop_button.setEnabled(False)

    def agent_finished(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.hide()
        completion_message = '\n            <div style="margin: 6px 0;">\n                <span style="\n                    display: inline-flex;\n                    align-items: center;\n                    background-color: rgba(45, 45, 45, 0.95);\n                    border: 1px solid rgba(255, 255, 255, 0.1);\n                    border-radius: 100px;\n                    padding: 4px 12px;\n                    color: #FFD700;\n                    font-family: Inter, -apple-system, system-ui, sans-serif;\n                    font-size: 13px;\n                    line-height: 1.4;\n                    white-space: nowrap;\n                ">✨ Agent run completed</span>\n            </div>\n        '
        self.action_log.append(completion_message)
        if hasattr(self, 'voice_controller'):
            self.voice_controller.finish_processing()

    def update_log(self, message):
        if message.startswith('Performed action:'):
            action_text = message.replace('Performed action:', '').strip()
            button_style = '\n                <div style="margin: 6px 0;">\n                    <span style="\n                        display: inline-flex;\n                        align-items: center;\n                        background-color: rgba(45, 45, 45, 0.95);\n                        border: 1px solid rgba(255, 255, 255, 0.1);\n                        border-radius: 100px;\n                        padding: 4px 12px;\n                        color: #4CAF50;\n                        font-family: Inter, -apple-system, system-ui, sans-serif;\n                        font-size: 13px;\n                        line-height: 1.4;\n                        white-space: nowrap;\n                    ">{}</span>\n                </div>\n            '
            try:
                import json
                action_data = json.loads(action_text)
                action_type = action_data.get('type', '').lower()
                if action_type == 'type':
                    text = action_data.get('text', '')
                    msg = f'⌨️ <span style="margin: 0 4px; color: #4CAF50;">Typed</span> <span style="color: #4CAF50">"{text}"</span>'
                    self.action_log.append(button_style.format(msg))
                elif action_type == 'key':
                    key = action_data.get('text', '')
                    msg = f'⌨️ <span style="margin: 0 4px; color: #4CAF50;">Pressed</span> <span style="color: #4CAF50">{key}</span>'
                    self.action_log.append(button_style.format(msg))
                elif action_type == 'mouse_move':
                    x = action_data.get('x', 0)
                    y = action_data.get('y', 0)
                    msg = f'🖱️ <span style="margin: 0 4px; color: #4CAF50;">Moved to</span> <span style="color: #4CAF50">({x}, {y})</span>'
                    self.action_log.append(button_style.format(msg))
                elif action_type == 'screenshot':
                    msg = '📸 <span style="margin: 0 4px; color: #4CAF50;">Captured Screenshot</span>'
                    self.action_log.append(button_style.format(msg))
                elif 'click' in action_type:
                    x = action_data.get('x', 0)
                    y = action_data.get('y', 0)
                    click_map = {'left_click': 'Left Click', 'right_click': 'Right Click', 'middle_click': 'Middle Click', 'double_click': 'Double Click'}
                    click_type = click_map.get(action_type, 'Click')
                    msg = f'👆 <span style="margin: 0 4px; color: #4CAF50;">{click_type}</span> <span style="color: #4CAF50">({x}, {y})</span>'
                    self.action_log.append(button_style.format(msg))
            except json.JSONDecodeError:
                self.action_log.append(button_style.format(action_text))
        elif message.startswith('Assistant:'):
            message_style = '\n                <div style="\n                    border-left: 2px solid #666;\n                    padding: 8px 16px;\n                    margin: 8px 0;\n                    font-family: Inter, -apple-system, system-ui, sans-serif;\n                    font-size: 13px;\n                    line-height: 1.5;\n                    color: #e0e0e0;\n                ">{}</div>\n            '
            clean_message = message.replace('Assistant:', '').strip()
            self.action_log.append(message_style.format(f'💬 {clean_message}'))
        elif message.startswith('Assistant action:'):
            action_style = '\n                <div style="\n                    color: #666;\n                    font-style: italic;\n                    padding: 4px 0;\n                    font-size: 12px;\n                    font-family: Inter, -apple-system, system-ui, sans-serif;\n                    line-height: 1.4;\n                ">🤖 {}</div>\n            '
            clean_message = message.replace('Assistant action:', '').strip()
            self.action_log.append(action_style.format(clean_message))
        else:
            regular_style = '\n                <div style="\n                    padding: 4px 0;\n                    color: #e0e0e0;\n                    font-family: Inter, -apple-system, system-ui, sans-serif;\n                    font-size: 13px;\n                    line-height: 1.4;\n                ">{}</div>\n            '
            self.action_log.append(regular_style.format(message))
        self.action_log.verticalScrollBar().setValue(self.action_log.verticalScrollBar().maximum())

    def handle_voice_input(self, text):
        """Handle voice input by setting it in the input area and running the agent"""
        self.input_area.setText(text)
        if text.strip():
            self.run_agent()

    def update_status(self, message):
        """Update status bar with voice control status"""
        self.status_bar.showMessage(message)

    def update_voice_status(self, status):
        """Update the action log with voice control status"""
        status_style = '\n            <div style="margin: 6px 0;">\n                <span style="\n                    display: inline-flex;\n                    align-items: center;\n                    background-color: rgba(45, 45, 45, 0.95);\n                    border: 1px solid rgba(255, 255, 255, 0.1);\n                    border-radius: 100px;\n                    padding: 4px 12px;\n                    color: #4CAF50;\n                    font-family: Inter, -apple-system, system-ui, sans-serif;\n                    font-size: 13px;\n                    line-height: 1.4;\n                    white-space: nowrap;\n                ">🎤 {}</span>\n            </div>\n        '
        self.action_log.append(status_style.format(status))

    def toggle_voice_control(self):
        """Toggle voice control on/off"""
        if self.voice_button.isChecked():
            self.voice_controller.toggle_voice_control()
        else:
            self.voice_controller.toggle_voice_control()

    def setup_shortcuts(self):
        close_window = QShortcut(QKeySequence('Ctrl+W'), self)
        close_window.activated.connect(self.close)
        stop_agent = QShortcut(QKeySequence('Ctrl+C'), self)
        stop_agent.activated.connect(self.stop_agent)
        send_message = QShortcut(QKeySequence('Ctrl+Return'), self)
        send_message.activated.connect(self.run_agent)
        voice_shortcut = QShortcut(QKeySequence('Alt+V'), self)
        voice_shortcut.activated.connect(lambda: self.voice_button.click())
        self.input_area.setTabChangesFocus(False)
        self.input_area.keyPressEvent = self.handle_input_keypress

    def handle_input_keypress(self, event):
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.input_area.textCursor()
            cursor.insertText('    ')
            return
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.run_agent()
            return
        QTextEdit.keyPressEvent(self.input_area, event)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

    def closeEvent(self, event):
        """Handle window close event - properly quit the application"""
        self.quit_application()
        event.accept()

    def quit_application(self):
        """Clean up resources and quit the application"""
        self.store.stop_run()
        if hasattr(self, 'voice_controller'):
            self.voice_controller.cleanup()
        self.settings.sync()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()

    def show_prompt_dialog(self):
        dialog = SystemPromptDialog(self, self.prompt_manager)
        dialog.exec()

def update_theme_button(self):
    if self.dark_mode:
        self.theme_button.setIcon(qta.icon('fa5s.sun', color='white'))
        self.theme_button.setToolTip('Switch to Light Mode')
    else:
        self.theme_button.setIcon(qta.icon('fa5s.moon', color='black'))
        self.theme_button.setToolTip('Switch to Dark Mode')

def apply_theme(self):
    colors = {'bg': '#1a1a1a' if self.dark_mode else '#ffffff', 'text': '#ffffff' if self.dark_mode else '#000000', 'button_bg': '#333333' if self.dark_mode else '#f0f0f0', 'button_text': '#ffffff' if self.dark_mode else '#000000', 'button_hover': '#4CAF50' if self.dark_mode else '#e0e0e0', 'border': '#333333' if self.dark_mode else '#e0e0e0'}
    container_style = f'\n            QWidget#container {{\n                background-color: {colors['bg']};\n                border-radius: 12px;\n                border: 1px solid {colors['border']};\n            }}\n        '
    self.container.setStyleSheet(container_style)
    self.findChild(QLabel, 'titleLabel').setStyleSheet(f'color: {colors['text']}; padding: 5px;')
    self.action_log.setStyleSheet(f'\n            QTextEdit {{\n                background-color: {colors['bg']};\n                border: none;\n                border-radius: 0;\n                color: {colors['text']};\n                padding: 16px;\n                font-family: Inter;\n                font-size: 13px;\n            }}\n        ')
    self.input_area.setStyleSheet(f'\n            QTextEdit {{\n                background-color: {colors['bg']};\n                border: 1px solid {colors['border']};\n                border-radius: 8px;\n                color: {colors['text']};\n                padding: 12px;\n                font-family: Inter;\n                font-size: 14px;\n                selection-background-color: {colors['button_hover']};\n            }}\n            QTextEdit:focus {{\n                border: 1px solid {colors['button_hover']};\n            }}\n        ')
    self.progress_bar.setStyleSheet(f'\n            QProgressBar {{\n                border: none;\n                background-color: {colors['bg']};\n                height: 2px;\n                margin: 0;\n            }}\n            QProgressBar::chunk {{\n                background-color: {colors['button_hover']};\n            }}\n        ')
    input_section_style = f'\n            QWidget {{\n                background-color: {colors['button_bg']};\n                border-top: 1px solid {colors['border']};\n            }}\n        '
    self.findChild(QWidget, 'input_section').setStyleSheet(input_section_style)
    window_control_style = f'\n            QPushButton {{\n                color: {colors['button_text']};\n                background-color: transparent;\n                border-radius: 8px;\n                padding: 4px 12px;\n                font-weight: bold;\n            }}\n            QPushButton:hover {{\n                background-color: {colors['button_hover']};\n            }}\n        '
    for button in [self.theme_button, self.findChild(QPushButton, 'menuButton'), self.findChild(QPushButton, 'titleBarButton')]:
        if button:
            button.setStyleSheet(window_control_style)
    if self.dark_mode:
        self.theme_button.setIcon(qta.icon('fa5s.sun', color=colors['button_text']))
    else:
        self.theme_button.setIcon(qta.icon('fa5s.moon', color=colors['button_text']))
    if hasattr(self, 'tray_icon') and self.tray_icon.contextMenu():
        self.tray_icon.contextMenu().setStyleSheet(f'\n                QMenu {{\n                    background-color: {colors['bg']};\n                    color: {colors['text']};\n                    border: 1px solid {colors['border']};\n                    border-radius: 6px;\n                    padding: 5px;\n                }}\n                QMenu::item {{\n                    padding: 8px 25px 8px 8px;\n                    border-radius: 4px;\n                }}\n                QMenu::item:selected {{\n                    background-color: {colors['button_hover']};\n                    color: white;\n                }}\n                QMenu::separator {{\n                    height: 1px;\n                    background: {colors['border']};\n                    margin: 5px 0px;\n                }}\n            ')

def setup_tray(self):
    self.tray_icon = QSystemTrayIcon(self)
    icon = qta.icon('fa5s.robot', scale_factor=1.5, color='white')
    self.tray_icon.setIcon(icon)
    tray_menu = QMenu()
    title_action = tray_menu.addAction('Grunty 👨🏽\u200d💻')
    title_action.setEnabled(False)
    tray_menu.addSeparator()
    new_task = tray_menu.addAction(qta.icon('fa5s.plus', color='white'), 'New Task')
    new_task.triggered.connect(self.show)
    toggle_action = tray_menu.addAction(qta.icon('fa5s.eye', color='white'), 'Show/Hide')
    toggle_action.triggered.connect(self.toggle_window)
    tray_menu.addSeparator()
    quit_action = tray_menu.addAction(qta.icon('fa5s.power-off', color='white'), 'Quit')
    quit_action.triggered.connect(self.quit_application)
    tray_menu.setStyleSheet('\n            QMenu {\n                background-color: #333333;\n                color: white;\n                border: 1px solid #444444;\n                border-radius: 6px;\n                padding: 5px;\n            }\n            QMenu::item {\n                padding: 8px 25px 8px 8px;\n                border-radius: 4px;\n            }\n            QMenu::item:selected {\n                background-color: #4CAF50;\n            }\n            QMenu::separator {\n                height: 1px;\n                background: #444444;\n                margin: 5px 0px;\n            }\n        ')
    self.tray_icon.setContextMenu(tray_menu)
    self.tray_icon.show()
    self.tray_icon.showMessage('Grunty is running', 'Click the robot icon in the menu bar to get started!', QSystemTrayIcon.MessageIcon.Information, 3000)
    self.tray_icon.activated.connect(self.tray_icon_activated)

def update_status(self, message):
    """Update status bar with voice control status"""
    self.status_bar.showMessage(message)

