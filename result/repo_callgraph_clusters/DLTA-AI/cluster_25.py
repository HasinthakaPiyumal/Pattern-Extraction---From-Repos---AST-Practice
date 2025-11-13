# Cluster 25

class ModelExplorerDialog(QDialog):
    """
    A dialog window for exploring available models and downloading them.

    Attributes:
        main_window (QMainWindow): The main window of the application.
        mute (bool): Whether to mute notifications or not.
        notification (function): A function for displaying notifications.
    """

    def __init__(self, main_window=None, mute=None, notification=None):
        """
        Initializes the ModelExplorerDialog.

        Args:
            main_window (QMainWindow): The main window of the application.
            mute (bool): Whether to mute notifications.
            notification (function): A function for displaying notifications.
        """
        super().__init__()
        self.main_window = main_window
        self.mute = mute
        self.notification = notification
        self.setWindowTitle('Model Explorer')
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        self.cols_labels = ['id', 'Model Name', 'Backbone', 'Lr schd', 'Memory (GB)', 'Inference Time (fps)', 'box AP', 'mask AP', 'Checkpoint Size (MB)']
        self.model_keys = sorted(list(set([model['Model'] for model in models_json])))
        layout = QVBoxLayout()
        self.setLayout(layout)
        toolbar = QToolBar()
        layout.addWidget(toolbar)
        self.model_type_dropdown = QComboBox()
        self.model_type_dropdown.addItems(['All'] + self.model_keys)
        self.model_type_dropdown.currentIndexChanged.connect(self.search)
        toolbar.addWidget(self.model_type_dropdown)
        self.available_checkbox = QCheckBox('Downloaded')
        self.available_checkbox.clicked.connect(self.search)
        toolbar.addWidget(self.available_checkbox)
        self.not_available_checkbox = QCheckBox('Not Downloaded')
        self.not_available_checkbox.clicked.connect(self.search)
        toolbar.addWidget(self.not_available_checkbox)
        open_checkpoints_dir_button = QPushButton('Open Checkpoints Dir')
        open_checkpoints_dir_button.setIcon(QtGui.QIcon(cwd + '/labelme/icons/downloads.png'))
        open_checkpoints_dir_button.setIconSize(QtCore.QSize(20, 20))
        open_checkpoints_dir_button.clicked.connect(self.open_checkpoints_dir)
        toolbar.addWidget(open_checkpoints_dir_button)
        layout.setSpacing(10)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.num_rows = len(models_json)
        self.num_cols = 9
        self.check_availability()
        self.populate_table()
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        close_button = QPushButton('Ok')
        close_button.clicked.connect(self.close)
        close_button.setFixedWidth(100)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.setSpacing(10)

    def populate_table(self):
        """
        Populates the table with data from models_json.

        Returns:
            None
        """
        self.table.clearContents()
        self.table.setRowCount(self.num_rows)
        self.table.setColumnCount(self.num_cols + 2)
        header = self.table.horizontalHeader()
        self.table.setHorizontalHeaderLabels(self.cols_labels + ['Status', 'Select Model'])
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        row_count = 0
        for model in models_json:
            col_count = 0
            for key in self.cols_labels:
                item = QTableWidgetItem(f'{model[key]}')
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_count, col_count, item)
                col_count += 1
            self.selected_model = (-1, -1, -1)
            select_row_button = QPushButton('Select Model')
            select_row_button.clicked.connect(self.select_model)
            self.table.setContentsMargins(10, 10, 10, 10)
            self.table.setCellWidget(row_count, 10, select_row_button)
            if model['Downloaded']:
                available_item = QTableWidgetItem('Downloaded')
                available_item.setForeground(QtCore.Qt.GlobalColor.darkGreen)
                self.table.setItem(row_count, 9, available_item)
                available_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            else:
                available_item = QPushButton('Requires Download')
                available_item.clicked.connect(self.create_download_callback(model['id']))
                available_item.setContentsMargins(10, 10, 10, 10)
                available_item.setStyleSheet('color: red')
                self.table.setCellWidget(row_count, 9, available_item)
                select_row_button.setEnabled(False)
            if model['Model'] == 'SAM':
                select_row_button.setEnabled(False)
                select_row_button.setText('Select from SAM Toolbar')
            row_count += 1

    def search(self):
        """
        Filters the table based on the selected model type and availability.

        Returns:
            None
        """
        model_type = self.model_type_dropdown.currentText()
        available = self.available_checkbox.isChecked()
        not_available = self.not_available_checkbox.isChecked()
        for row in range(self.num_rows):
            show_row = True
            if model_type != 'All':
                id = int(self.table.item(row, 0).text())
                if models_json[id]['Model'] != model_type:
                    show_row = False
            if available or not_available:
                available_text = self.table.item(row, 9)
                try:
                    available_text = available_text.text()
                except AttributeError:
                    pass
                if available and available_text != 'Downloaded':
                    show_row = False
                if not_available and available_text == 'Downloaded':
                    show_row = False
            self.table.setRowHidden(row, not show_row)

    def select_model(self):
        """
        Gets the selected model from the table and sets it as the selected model.

        Returns:
            None
        """
        sender = self.sender()
        index = self.table.indexAt(sender.pos())
        row = index.row()
        model_id = int(self.table.item(row, 0).text())
        self.selected_model = (models_json[model_id]['Model Name'], models_json[model_id]['Config'], models_json[model_id]['Checkpoint'])
        self.accept()

    def download_model(self, id):
        """
        Downloads the model with the given id and updates the progress dialog.

        Args:
            id (int): The id of the model to download.

        Returns:
            None
        """
        checkpoint_link = models_json[id]['Checkpoint_link']
        model_name = models_json[id]['Model Name']
        self.progress_dialog = QProgressDialog(f'Downloading {model_name}...', 'Cancel', 0, 100, self)
        self.progress_dialog.setWindowTitle('Downloading Model')
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.progress_dialog.canceled.connect(self.cancel_download)
        self.progress_dialog.show()
        self.start_time = time.time()
        self.last_time = self.start_time
        self.last_downloaded = 0
        self.download_canceled = False

        def handle_progress(block_num, block_size, total_size):
            """
            Updates the progress dialog with the current download progress.

            Args:
                block_num (int): The number of blocks downloaded.
                block_size (int): The size of each block.
                total_size (int): The total size of the file being downloaded.

            Returns:
                None
            """
            read_data = block_num * block_size
            if total_size > 0:
                download_percentage = read_data * 100 / total_size
                self.progress_dialog.setValue(download_percentage)
                self.progress_dialog.setLabelText(f'Downloading {model_name}... ')
                QApplication.processEvents()
        failed = False
        try:
            response = requests.get(checkpoint_link, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            block_num = 0
            file_path = f'{cwd}/mmdetection/checkpoints/{checkpoint_link.split('/')[-1]}'
            with open(file_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    if self.download_canceled:
                        break
                    f.write(data)
                    block_num += 1
                    handle_progress(block_num, block_size, total_size)
            if self.download_canceled:
                os.remove(file_path)
                print('Download canceled by user')
                failed = True
        except Exception as e:
            os.remove(file_path)
            print(f'Download error: {e}')
            failed = True
        self.progress_dialog.close()
        self.check_availability()
        self.populate_table()
        print('Download finished')
        try:
            if not self.mute:
                if not self.isActiveWindow():
                    if not failed:
                        self.notification(f'{model_name} has been downloaded successfully')
                    else:
                        self.notification(f'Failed to download {model_name}')
        except:
            pass

    def cancel_download(self):
        """
        Sets the download_canceled flag to True to cancel the download.

        Returns:
            None
        """
        self.download_canceled = True

    def create_download_callback(self, model_id):
        """
        Returns a lambda function that downloads the model with the given id.

        Args:
            model_id (int): The id of the model to download.

        Returns:
            function: A lambda function that downloads the model with the given id.
        """
        return lambda: self.download_model(model_id)

    def check_availability(self):
        """
        Checks the availability of each model in the table and updates the "Downloaded" column.

        Returns:
            None
        """
        checkpoints_dir = cwd + '/mmdetection/checkpoints/'
        for model in models_json:
            if model['Checkpoint'].split('/')[-1] in os.listdir(checkpoints_dir):
                model['Downloaded'] = True
            else:
                model['Downloaded'] = False

    def open_checkpoints_dir(self):
        """
        Opens the directory containing the downloaded checkpoints in the file explorer.

        Returns:
            None
        """
        url = QtCore.QUrl.fromLocalFile(cwd + '/mmdetection/checkpoints/')
        if not QtGui.QDesktopServices.openUrl(url):
            print('Failed to open checkpoints directory')

def create_download_callback(self, model_id):
    """
        Returns a lambda function that downloads the model with the given id.

        Args:
            model_id (int): The id of the model to download.

        Returns:
            function: A lambda function that downloads the model with the given id.
        """
    return lambda: self.download_model(model_id)

