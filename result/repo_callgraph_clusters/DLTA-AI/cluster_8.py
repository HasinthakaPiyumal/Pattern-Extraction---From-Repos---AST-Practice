# Cluster 8

def main():
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)
    app.setApplicationName(__appname__)
    app.setWindowIcon(newIcon('icon'))
    splash_pix = QtGui.QPixmap('labelme/icons/splash_screen.png')
    splash = QtWidgets.QSplashScreen(splash_pix)
    try:
        from screeninfo import get_monitors
        original_width = get_monitors()[0].width
        original_heigth = get_monitors()[0].height
        slapsh_width = splash.width()
        splash_height = splash.height()
        splash.move(int((original_width - slapsh_width) / 2), int((original_heigth - splash_height) / 2))
    except Exception as e:
        pass
    splash.show()
    qss = '\n    QMenuBar::item {\n        padding: 10px;\n        margin: 0 5px\n    }\n    QMenu{\n        border-radius: 5px;\n    }\n    QMenu::item{\n        padding: 8px;\n        margin: 5px;\n        border-radius: 5px;\n    }\n    QToolTip {\n            color: #111111;\n            background-color: #EEEEEE;\n            }\n    QCheckBox{\n        margin: 0 7px;\n    }\n    QComboBox{\n        font-size: 10pt;\n        font-weight: bold;\n    }\n    '
    try:
        import yaml
        with open('labelme/config/default_config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        qdarktheme.setup_theme(theme=config['theme'], default_theme='dark', additional_qss=qss)
    except Exception as e:
        print(f'ERROR {e}')
    from labelme.app import MainWindow
    win = MainWindow()
    splash.finish(win)
    win.showMaximized()
    win.raise_()
    sys.exit(app.exec())

class MainWindow(QtWidgets.QMainWindow):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = (0, 1, 2)
    tracking_progress_bar_signal = pyqtSignal(int)

    def __init__(self, config=None, filename=None, output=None, output_file=None, output_dir=None):
        self.buttons_text_style_sheet = 'QPushButton {font-size: 10pt; margin: 2px 5px; padding: 2px 7px;font-weight: bold; background-color: #0d69f5; color: #FFFFFF;} QPushButton:hover {background-color: #4990ED;} QPushButton:disabled {background-color: #7A7A7A;}'
        if output is not None:
            logger.warning('argument output is deprecated, use output_file instead')
            if output_file is None:
                output_file = output
        if config is None:
            config = get_config()
        self._config = config
        self.decodingCanceled = False
        Shape.line_color = QtGui.QColor(*self._config['shape']['line_color'])
        Shape.fill_color = QtGui.QColor(*self._config['shape']['fill_color'])
        Shape.select_line_color = QtGui.QColor(*self._config['shape']['select_line_color'])
        Shape.select_fill_color = QtGui.QColor(*self._config['shape']['select_fill_color'])
        Shape.vertex_fill_color = QtGui.QColor(*self._config['shape']['vertex_fill_color'])
        Shape.hvertex_fill_color = QtGui.QColor(*self._config['shape']['hvertex_fill_color'])
        mathOps.update_saved_models_json(os.getcwd())
        self.segmentation_options_UI = SegmentationOptionsUI(self)
        self.merge_feature_UI = MergeFeatureUI(self)
        super(MainWindow, self).__init__()
        try:
            self.intelligenceHelper = Intelligence(self)
        except:
            print('it seems you have a problem with initializing model\ncheck you have at least one model')
            self.helper_first_time_flag = True
        else:
            self.helper_first_time_flag = False
        self.setWindowTitle(__appname__)
        self.dirty = False
        self._noSelectionSlot = False
        self.labelDialog = LabelDialog(parent=self, labels=self._config['labels'], sort_labels=self._config['sort_labels'], show_text_field=self._config['show_label_text_field'], completion=self._config['label_completion'], fit_to_content=self._config['fit_to_content'], flags=self._config['label_flags'])
        self.labelList = LabelListWidget()
        self.lastOpenDir = None
        self.flag_dock = self.flag_widget = None
        self.flag_dock = QtWidgets.QDockWidget(self.tr('Flags'), self)
        self.flag_dock.setObjectName('Flags')
        self.flag_widget = QtWidgets.QListWidget()
        if config['flags']:
            self.loadFlags({k: False for k in config['flags']})
        self.flag_widget.itemChanged.connect(self.setDirty)
        self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)
        self.labelList.itemDoubleClicked.connect(self.editLabel)
        self.labelList.itemChanged.connect(self.labelItemChanged)
        self.labelList.itemDropped.connect(self.labelOrderChanged)
        self.shape_dock = QtWidgets.QDockWidget(self.tr('Polygon Labels'), self)
        self.shape_dock.setObjectName('Labels')
        self.shape_dock.setWidget(self.labelList)
        self.uniqLabelList = UniqueLabelQListWidget()
        self.uniqLabelList.setToolTip(self.tr("Select label to start annotating for it. Press 'Esc' to deselect."))
        if self._config['labels']:
            for label in self._config['labels']:
                item = self.uniqLabelList.createItemFromLabel(label)
                self.uniqLabelList.addItem(item)
                rgb = self._get_rgb_by_label(label)
                self.uniqLabelList.setItemLabel(item, label, rgb)
        self.label_dock = QtWidgets.QDockWidget(self.tr(u'Label List'), self)
        self.label_dock.setObjectName(u'Label List')
        self.label_dock.setWidget(self.uniqLabelList)
        self.fileSearch = QtWidgets.QLineEdit()
        self.fileSearch.setPlaceholderText(self.tr('Search Filename'))
        self.fileSearch.textChanged.connect(self.fileSearchChanged)
        self.fileListWidget = QtWidgets.QListWidget()
        self.fileListWidget.itemSelectionChanged.connect(self.fileSelectionChanged)
        fileListLayout = QtWidgets.QVBoxLayout()
        fileListLayout.setContentsMargins(0, 0, 0, 0)
        fileListLayout.setSpacing(0)
        fileListLayout.addWidget(self.fileSearch)
        fileListLayout.addWidget(self.fileListWidget)
        self.file_dock = QtWidgets.QDockWidget(self.tr(u'File List'), self)
        self.file_dock.setObjectName(u'Files')
        fileListWidget = QtWidgets.QWidget()
        fileListWidget.setLayout(fileListLayout)
        self.file_dock.setWidget(fileListWidget)
        self.vis_dock = QtWidgets.QDockWidget(self.tr(u'Visualization Options'), self)
        self.vis_dock.setObjectName(u'Visualization Options')
        self.vis_widget = QtWidgets.QWidget()
        self.vis_dock.setWidget(self.vis_widget)
        self.zoomWidget = ZoomWidget()
        self.setAcceptDrops(True)
        self.canvas = self.labelList.canvas = Canvas(epsilon=self._config['epsilon'], double_click=self._config['canvas']['double_click'], num_backups=self._config['canvas']['num_backups'])
        self.canvas.zoomRequest.connect(self.zoomRequest)
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidget(self.canvas)
        scrollArea.setWidgetResizable(True)
        self.scrollBars = {Qt.Orientation.Vertical: scrollArea.verticalScrollBar(), Qt.Orientation.Horizontal: scrollArea.horizontalScrollBar(), Qt.Orientation.Horizontal.value: scrollArea.horizontalScrollBar(), Qt.Orientation.Vertical.value: scrollArea.verticalScrollBar()}
        self.canvas.scrollRequest.connect(self.scrollRequest)
        self.canvas.newShape.connect(self.newShape)
        self.canvas.shapeMoved.connect(self.setDirty)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)
        self.canvas.drawingPolygon.connect(self.toggleDrawingSensitive)
        self.canvas.edgeSelected.connect(self.canvasShapeEdgeSelected)
        self.canvas.APPrefresh.connect(self.refresh_image_MODE)
        self.addSamControls()
        self.canvas.pointAdded.connect(self.run_sam_model)
        self.canvas.samFinish.connect(self.sam_finish_annotation_button_clicked)
        self.sam_predictor = None
        self.current_sam_shape = None
        self.SAM_SHAPES_IN_IMAGE = []
        self.sam_last_mode = 'rectangle'
        self.setCentralWidget(scrollArea)
        self.target_directory = ''
        self.save_path = ''
        self.global_listObj = []
        self.multi_model_flag = False
        self.addVideoControls()
        self.frame_time = 0
        self.FRAMES_TO_SKIP = 30
        self.TRACK_ASSIGNED_OBJECTS_ONLY = False
        self.TrackingMode = False
        self.current_annotation_mode = ''
        self.CURRENT_ANNOATAION_FLAGS = {'traj': False, 'bbox': True, 'id': True, 'class': True, 'mask': True, 'polygons': True, 'conf': True}
        self.CURRENT_ANNOATAION_TRAJECTORIES = {'length': 30, 'alpha': 0.7}
        self.CURRENT_SHAPES_IN_IMG = []
        self.featuresOptions = {'deleteDefault': 'this frame only', 'interpolationDefMethod': 'linear', 'interpolationDefType': 'all', 'interpolationOverwrite': False, 'EditDefault': 'Edit only this frame'}
        self.key_frames = {}
        self.id_frames_rec = {}
        self.copiedShapes = []
        self.INDEX_OF_CURRENT_FRAME = 1
        self.interrupted = False
        self.minID = -2
        self.maxID = 0
        for dock in ['label_dock', 'shape_dock', 'file_dock', 'vis_dock']:
            if self._config[dock]['closable']:
                getattr(self, dock).setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable)
            if self._config[dock]['floatable']:
                getattr(self, dock).setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable)
            if self._config[dock]['movable']:
                getattr(self, dock).setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable)
            if self._config[dock]['show'] is False:
                getattr(self, dock).setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.label_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.shape_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.file_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.vis_dock)
        action = functools.partial(utils.newAction, self)
        shortcuts = self._config['shortcuts']
        quit = action(self.tr('&Quit'), self.close, shortcuts['quit'], 'quit', self.tr('Quit application'))
        open_ = action(self.tr('&Open Image'), self.openFile, shortcuts['open'], 'open', self.tr(f'Open image or label file ({str(shortcuts['open'])})'))
        opendir = action(self.tr('&Open Dir'), self.openDirDialog, shortcuts['open_dir'], 'opendir', self.tr(f'Open Dir ({str(shortcuts['open_dir'])})'))
        save = action(self.tr('&Save'), self.saveFile, shortcuts['save'], 'save', self.tr(f'Save labels to file ({str(shortcuts['save'])})'), enabled=False)
        export = action(self.tr('&Export'), self.exportData, shortcuts['export'], 'export', self.tr(f'Export annotations to COCO format ({str(shortcuts['export'])})'), enabled=False)
        modelExplorer = action(self.tr('&Model Explorer'), self.model_explorer, None, 'checklist', self.tr(u'Model Explorer'))
        saveAs = action(self.tr('&Save As'), self.saveFileAs, shortcuts['save_as'], 'save-as', self.tr('Save labels to a different file'), enabled=False)
        deleteFile = action(self.tr('&Delete File'), self.deleteFile, shortcuts['delete_file'], 'delete', self.tr('Delete current label file'), enabled=False)
        changeOutputDir = action(self.tr('&Change Output Dir'), slot=self.changeOutputDirDialog, shortcut=shortcuts['save_to'], icon='open', tip=self.tr(u'Change where annotations are loaded/saved'))
        saveAuto = action(text=self.tr('Save &Automatically'), slot=lambda x: self.actions.saveAuto.setChecked(x), icon='save', tip=self.tr('Save automatically'), checkable=True, enabled=True)
        saveAuto.setChecked(self._config['auto_save'])
        saveWithImageData = action(text='Save With Image Data', slot=self.enableSaveImageWithData, tip='Save image data in label file', checkable=True, checked=self._config['store_data'])
        close = action('&Close', self.closeFile, shortcuts['close'], 'close', 'Close current file')
        toggle_keep_prev_mode = action(self.tr('Keep Previous Annotation'), self.toggleKeepPrevMode, shortcuts['toggle_keep_prev_mode'], None, self.tr('Toggle "keep pevious annotation" mode'), checkable=True)
        toggle_keep_prev_mode.setChecked(self._config['keep_prev'])
        createMode = action(self.tr('Create Polygons'), self.setCreateMode, shortcuts['create_polygon'], 'objects', self.tr('Start drawing polygons'), enabled=False)
        editMode = action(self.tr('Edit Polygons'), self.setEditMode, shortcuts['edit_polygon'], 'edit', self.tr('Move and edit the selected polygons'), enabled=False)
        delete = action(self.tr('Delete Polygons'), self.deleteSelectedShape, shortcuts['delete_polygon'], 'close', self.tr('Delete the selected polygons'), enabled=False)
        copy = action(self.tr('Duplicate Polygons'), self.copySelectedShape, shortcuts['duplicate_polygon'], 'copy', self.tr('Create a duplicate of the selected polygons'), enabled=False)
        undoLastPoint = action(self.tr('Undo last point'), self.canvas.undoLastPoint, shortcuts['undo_last_point'], 'undo', self.tr('Undo last drawn point'), enabled=False)
        addPointToEdge = action(text=self.tr('Add Point to Edge'), slot=self.canvas.addPointToEdge, shortcut=shortcuts['add_point_to_edge'], icon='add_point', tip=self.tr('Add point to the nearest edge'), enabled=False)
        removePoint = action(text='Remove Selected Point', slot=self.removeSelectedPoint, icon='edit', tip='Remove selected point from polygon', enabled=False)
        undo = action(self.tr('Undo'), self.undoShapeEdit, shortcuts['undo'], 'undo', self.tr('Undo last add and edit of shape'), enabled=False)
        hideAll = action(self.tr('&Hide\nPolygons'), functools.partial(self.togglePolygons, False), icon='eye', tip=self.tr('Hide all polygons'), enabled=False)
        showAll = action(self.tr('&Show\nPolygons'), functools.partial(self.togglePolygons, True), icon='eye', tip=self.tr('Show all polygons'), enabled=False)
        zoom = QtWidgets.QWidgetAction(self)
        zoom.setDefaultWidget(self.zoomWidget)
        self.zoomWidget.setWhatsThis(self.tr('Zoom in or out of the image. Also accessible with {} and {} from the canvas.').format(utils.fmtShortcut('{},{}'.format(shortcuts['zoom_in'], shortcuts['zoom_out'])), utils.fmtShortcut(self.tr('Ctrl+Wheel'))))
        self.zoomWidget.setEnabled(False)
        zoomIn = action(self.tr('Zoom &In'), functools.partial(self.addZoom, 1.1), shortcuts['zoom_in'], 'zoom-in', self.tr('Increase zoom level'), enabled=False)
        zoomOut = action(self.tr('&Zoom Out'), functools.partial(self.addZoom, 0.9), shortcuts['zoom_out'], 'zoom-out', self.tr('Decrease zoom level'), enabled=False)
        zoomOrg = action(self.tr('&Original size'), functools.partial(self.setZoom, 100), shortcuts['zoom_to_original'], 'zoom', self.tr('Zoom to original size'), enabled=False)
        fitWindow = action(self.tr('&Fit Window'), self.setFitWindow, shortcuts['fit_window'], 'fit-window', self.tr('Zoom follows window size'), checkable=True, enabled=False)
        fitWidth = action(self.tr('Fit &Width'), self.setFitWidth, shortcuts['fit_width'], 'fit-width', self.tr('Zoom follows window width'), checkable=True, enabled=False)
        brightnessContrast = action('&Brightness Contrast', self.brightnessContrast, None, 'color', 'Adjust brightness and contrast', enabled=False)
        show_cross_line = action(self.tr('&Toggle Cross Line'), self.enable_show_cross_line, tip=self.tr('cross line for mouse position'), icon='cartesian', checkable=True, checked=self._config['show_cross_line'], enabled=True)
        zoomActions = (self.zoomWidget, zoomIn, zoomOut, zoomOrg, fitWindow, fitWidth)
        self.zoomMode = self.FIT_WINDOW
        fitWindow.setChecked(True)
        self.scalers = {self.FIT_WINDOW: self.scaleFitWindow, self.FIT_WIDTH: self.scaleFitWidth, self.MANUAL_ZOOM: lambda: 1}
        edit = action(self.tr('Edit &Label'), self.editLabel, shortcuts['edit_label'], 'label', self.tr('Modify the label of the selected polygon'), enabled=False)
        enhance = action(self.tr('&Enhace Polygons'), self.sam_enhance_annotation_button_clicked, shortcuts['SAM_enhance'], 'SAM', self.tr('Enhance the selected polygon with AI'), enabled=True)
        interpolate = action(self.tr('&Interpolation Tracking'), self.interpolateMENU, shortcuts['interpolate'], 'tracking', self.tr('Interpolate the selected polygon between to frames to Track it'), enabled=True)
        mark_as_key = action(self.tr('&Mark as key'), self.mark_as_key, shortcuts['mark_as_key'], 'mark', self.tr('Mark this frame as KEY for interpolation'), enabled=True)
        remove_all_keyframes = action(self.tr('&Remove all keyframes'), self.remove_all_keyframes, None, 'mark', self.tr('Remove all keyframes'), enabled=True)
        scale = action(self.tr('&Scale'), self.scaleMENU, shortcuts['scale'], 'resize', self.tr('Scale the selected polygon'), enabled=True)
        copyShapes = action(self.tr('&Copy'), self.ctrlCopy, shortcuts['copy'], 'copy', self.tr('Copy selected polygons'), enabled=True)
        pasteShapes = action(self.tr('&Paste'), self.ctrlPaste, shortcuts['paste'], 'paste', self.tr('paste copied polygons'), enabled=True)
        update_curr_frame = action(self.tr('&Update current frame'), self.update_current_frame_annotation_button_clicked, None, 'done', self.tr('Update frame'), enabled=True)
        ignore_changes = action(self.tr('&Ignore changes'), self.main_video_frames_slider_changed, shortcuts['ignore_updates'], 'delete', self.tr('Ignore unsaved changes'), enabled=True)
        fill_drawing = action(self.tr('Fill Drawing Polygon'), self.canvas.setFillDrawing, None, 'color', self.tr('Fill polygon while drawing'), checkable=True, enabled=True)
        fill_drawing.trigger()
        annotate_one_action = action(self.tr('Run Model on Current Image'), self.annotate_one, None, 'open', self.tr('Run Model on Current Image'))
        annotate_batch_action = action(self.tr('Run Model on All Images'), self.annotate_batch, None, 'file', self.tr('Run Model on All Images'))
        set_conf_threshold = action(self.tr('Confidence Threshold'), self.setConfThreshold, None, 'tune', self.tr('Confidence Threshold'))
        set_iou_threshold = action(self.tr('IOU Threshold (NMS)'), self.setIOUThreshold, None, 'iou', self.tr('IOU Threshold (Non Maximum Suppression)'))
        select_classes = action(self.tr('Select Classes'), self.selectClasses, None, 'checklist', self.tr('Select Classes to be Annotated'))
        merge_segmentation_models = action(self.tr('Merge Segmentation Models'), self.mergeSegModels, None, 'merge', self.tr('Merge Segmentation Models'))
        runtime_data = action(self.tr('Show Runtime Data'), runtime_data_UI.PopUp, None, 'runtime', self.tr('Show Runtime Data'))
        git_hub = action(self.tr('GitHub Repository'), links.open_git_hub, None, 'github', self.tr('GitHub Repository'))
        feedback = action(self.tr('Feedback'), feedback_UI.PopUp, None, 'feedback', self.tr('Feedback'))
        license = action(self.tr('license'), links.open_license, None, 'license', self.tr('license'))
        user_guide = action(self.tr('User Guide'), links.open_guide, None, 'guide', self.tr('User Guide'))
        check_updates = action(self.tr('Check for Updates'), check_updates_UI.PopUp, None, 'info', self.tr('Check for Updates'))
        preferences = action(self.tr('Preferences'), preferences_UI.PopUp, None, 'settings', self.tr('Preferences'))
        shortcut_selector = action(self.tr('Shortcuts'), shortcut_selector_UI.PopUp, None, 'shortcuts', self.tr('Shortcuts'))
        sam = action(self.tr('Toggle SAM Toolbar'), self.Segment_anything, None, 'SAM', self.tr('Toggle SAM Toolbar'))
        openVideo = action(self.tr('Open &Video'), self.openVideo, shortcuts['open_video'], 'video', self.tr(f'Open a video file ({shortcuts['open_video']})'))
        openVideoFrames = action(self.tr('Open Video as Frames'), self.openVideoFrames, shortcuts['open_video_frames'], 'frames', self.tr(f'Open Video as Frames ({shortcuts['open_video_frames']})'))
        labelmenu = QtWidgets.QMenu()
        utils.addActions(labelmenu, (edit, delete))
        self.labelList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.labelList.customContextMenuRequested.connect(self.popLabelListMenu)
        self.actions = utils.struct(saveAuto=saveAuto, saveWithImageData=saveWithImageData, changeOutputDir=changeOutputDir, save=save, saveAs=saveAs, open=open_, close=close, deleteFile=deleteFile, toggleKeepPrevMode=toggle_keep_prev_mode, delete=delete, edit=edit, copy=copy, undoLastPoint=undoLastPoint, undo=undo, addPointToEdge=addPointToEdge, removePoint=removePoint, createMode=createMode, editMode=editMode, zoom=zoom, zoomIn=zoomIn, zoomOut=zoomOut, zoomOrg=zoomOrg, fitWindow=fitWindow, fitWidth=fitWidth, brightnessContrast=brightnessContrast, show_cross_line=show_cross_line, zoomActions=zoomActions, export=export, openVideo=openVideo, openVideoFrames=openVideoFrames, fileMenuActions=(open_, opendir, save, saveAs, close, quit), modelExplorer=modelExplorer, runtime_data=runtime_data, tool=(), editMenu=(edit, copy, delete, None, undo, undoLastPoint, None, addPointToEdge), menu=(createMode, editMode, edit, enhance, interpolate, mark_as_key, remove_all_keyframes, scale, copyShapes, pasteShapes, copy, delete, undo, undoLastPoint, addPointToEdge, removePoint, update_curr_frame, ignore_changes), onLoadActive=(close, createMode, editMode, brightnessContrast), onShapesPresent=(saveAs, hideAll, showAll))
        self.canvas.vertexSelected.connect(self.actions.removePoint.setEnabled)
        self.menus = utils.struct(file=self.menu(self.tr('&File')), edit=self.menu(self.tr('&Edit')), view=self.menu(self.tr('&View')), intelligence=self.menu(self.tr('&Auto Annotation')), model_selection=self.menu(self.tr('&Model Selection')), options=self.menu(self.tr('&Options')), help=self.menu(self.tr('&Help')), recentFiles=QtWidgets.QMenu(self.tr('Open &Recent')), saved_models=QtWidgets.QMenu(self.tr('Select Segmentation model')), tracking_models=QtWidgets.QMenu(self.tr('Select Tracking model')), labelList=labelmenu, certain_area=QtWidgets.QMenu(self.tr('Select Certain Area')), ui_elements=QtWidgets.QMenu(self.tr('&Show UI Elements')), zoom_options=QtWidgets.QMenu(self.tr('&Zoom Options')))
        utils.addActions(self.menus.file, (open_, opendir, openVideo, openVideoFrames, None, save, saveAs, export, None, close, quit))
        utils.addActions(self.menus.intelligence, (annotate_one_action, annotate_batch_action))
        self.menus.ui_elements.setIcon(QtGui.QIcon('labelme/icons/UI.png'))
        utils.addActions(self.menus.ui_elements, (self.vis_dock.toggleViewAction(), self.label_dock.toggleViewAction(), self.shape_dock.toggleViewAction(), self.file_dock.toggleViewAction()))
        self.menus.zoom_options.setIcon(QtGui.QIcon('labelme/icons/zoom.png'))
        utils.addActions(self.menus.zoom_options, (zoomIn, zoomOut, zoomOrg, None, fitWindow, fitWidth))
        utils.addActions(self.menus.view, (sam, self.menus.ui_elements, None, hideAll, showAll, None, self.menus.zoom_options, None, show_cross_line))
        self.menus.saved_models.setIcon(QtGui.QIcon('labelme/icons/brain.png'))
        self.menus.tracking_models.setIcon(QtGui.QIcon('labelme/icons/tracking.png'))
        self.menus.certain_area.setIcon(QtGui.QIcon('labelme/icons/polygon.png'))
        utils.addActions(self.menus.model_selection, (self.menus.saved_models, merge_segmentation_models, None, self.menus.tracking_models, None, modelExplorer))
        utils.addActions(self.menus.options, (set_conf_threshold, set_iou_threshold, self.menus.certain_area, None, select_classes))
        utils.addActions(self.menus.help, (user_guide, preferences, shortcut_selector, None, git_hub, feedback, None, runtime_data, None, license, check_updates))
        self.menus.file.aboutToShow.connect(self.updateFileMenu)
        self.menus.file.aboutToShow.connect(self.update_models_menu)
        utils.addActions(self.canvas.menus[0], self.actions.menu)
        utils.addActions(self.canvas.menus[1], (action('&Copy here', self.copyShape), action('&Move here', self.moveShape)))
        self.tools = self.toolbar('Tools')
        self.actions.tool = (open_, opendir, openVideo, None, save, export, None, createMode, editMode, edit, None, delete, undo, None)
        self.statusBar().showMessage(self.tr('%s started.') % __appname__)
        self.statusBar().show()
        if output_file is not None and self._config['auto_save']:
            logger.warn('If `auto_save` argument is True, `output_file` argument is ignored and output filename is automatically set as IMAGE_BASENAME.json.')
        self.output_file = output_file
        self.output_dir = output_dir
        self.image = QtGui.QImage()
        self.imagePath = None
        self.recentFiles = []
        self.maxRecent = 7
        self.otherData = None
        self.zoom_level = 100
        self.fit_window = False
        self.zoom_values = {}
        self.brightnessContrast_values = {}
        self.scroll_values = {Qt.Orientation.Horizontal: {}, Qt.Orientation.Vertical: {}, Qt.Orientation.Horizontal.value: {}, Qt.Orientation.Vertical.value: {}}
        if filename is not None and osp.isdir(filename):
            self.importDirImages(filename, load=False)
        else:
            self.filename = filename
        if config['file_search']:
            self.fileSearch.setText(config['file_search'])
            self.fileSearchChanged()
        self.settings = QtCore.QSettings('labelme', 'labelme')
        self.recentFiles = self.settings.value('recentFiles', []) or []
        size = self.settings.value('window/size', QtCore.QSize(600, 500))
        position = self.settings.value('window/position', QtCore.QPoint(0, 0))
        self.resize(size)
        self.move(position)
        self.restoreState(self.settings.value('window/state', QtCore.QByteArray()))
        self.updateFileMenu()
        self.update_models_menu()
        if self.filename is not None:
            self.queueEvent(functools.partial(self.loadFile, self.filename))
        self.zoomWidget.valueChanged.connect(self.paintCanvas)
        self.populateModeActions()
        self.right_click_menu()
        QtGui.QShortcut(QtGui.QKeySequence(self._config['shortcuts']['stop']), self).activated.connect(self.Escape_clicked)

    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            utils.addActions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName('%sToolBar' % title)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        if actions:
            utils.addActions(toolbar, actions)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)
        return toolbar

    def noShapes(self):
        return not len(self.labelList)

    def populateModeActions(self):
        tool, menu = (self.actions.tool, self.actions.menu)
        self.tools.clear()
        utils.addActions(self.tools, tool)
        self.canvas.menus[0].clear()
        utils.addActions(self.canvas.menus[0], menu)
        self.menus.edit.clear()
        actions = (self.actions.editMode,)
        utils.addActions(self.menus.edit, actions + self.actions.editMenu)

    def setDirty(self):
        self.actions.undo.setEnabled(self.canvas.isShapeRestorable)
        if self._config['auto_save'] or self.actions.saveAuto.isChecked():
            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            if os.path.isdir(label_file):
                os.remove(label_file)
            self.saveLabels(label_file)
            return
        self.dirty = True
        self.actions.save.setEnabled(True)
        title = __appname__
        if self.filename is not None:
            title = '{} - {}*'.format(title, self.filename)
        self.setWindowTitle(title)

    def setClean(self):
        self.dirty = False
        self.actions.save.setEnabled(False)
        self.actions.createMode.setEnabled(True)
        title = __appname__
        if self.filename is not None:
            title = '{} - {}'.format(title, self.filename)
        self.setWindowTitle(title)
        if self.hasLabelFile():
            self.actions.deleteFile.setEnabled(True)
        else:
            self.actions.deleteFile.setEnabled(False)

    def toggleActions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            z.setEnabled(value)
        for action in self.actions.onLoadActive:
            action.setEnabled(value)

    def canvasShapeEdgeSelected(self, selected, shape):
        self.actions.addPointToEdge.setEnabled(selected and shape and shape.canAddPoint())

    def queueEvent(self, function):
        QtCore.QTimer.singleShot(0, function)

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def resetState(self):
        self.labelList.clear()
        self.filename = None
        self.imagePath = None
        self.imageData = None
        self.CURRENT_FRAME_IMAGE = None
        self.labelFile = None
        self.otherData = None
        self.canvas.resetState()

    def currentItem(self):
        items = self.labelList.selectedItems()
        if items:
            return items[0]
        return None

    def addRecentFile(self, filename):
        if filename in self.recentFiles:
            self.recentFiles.remove(filename)
        elif len(self.recentFiles) >= self.maxRecent:
            self.recentFiles.pop()
        self.recentFiles.insert(0, filename)

    def Escape_clicked(self):
        """
        Summary:
            This function is called when the user presses the escape key.
            It resets the SAM toolbar and the canvas.
            It also interrupts the current annotation process like (tracking, interpolation, etc.)
        """
        self.interrupted = True
        self.sam_reset_button_clicked()
        if self.canvas.tracking_area == 'drawing':
            self.certain_area_clicked(1)

    def undoShapeEdit(self):
        self.canvas.restoreShape()
        self.labelList.clear()
        self.loadShapes(self.canvas.shapes)
        self.actions.undo.setEnabled(self.canvas.isShapeRestorable)

    def toggleDrawingSensitive(self, drawing=True):
        """Toggle drawing sensitive.
        In the middle of drawing, toggling between modes should be disabled.
        """
        self.actions.editMode.setEnabled(not drawing)
        self.actions.undoLastPoint.setEnabled(drawing)
        self.actions.undo.setEnabled(not drawing)
        self.actions.delete.setEnabled(not drawing)

    def toggleDrawMode(self, edit=True, createMode='polygon'):
        self.canvas.setEditing(edit)
        self.canvas.createMode = createMode
        if edit:
            self.actions.createMode.setEnabled(True)
        elif createMode == 'polygon':
            self.actions.createMode.setEnabled(False)
        else:
            self.actions.createMode.setEnabled(True)
        self.actions.editMode.setEnabled(not edit)

    def setEditMode(self):
        self.turnOFF_SAM()
        try:
            x = self.CURRENT_VIDEO_PATH
        except:
            self.toggleDrawMode(True)
            return
        self.update_current_frame_annotation()
        self.toggleDrawMode(True)

    def updateFileMenu(self):
        current = self.filename

        def exists(filename):
            return osp.exists(str(filename))
        menu = self.menus.recentFiles
        menu.clear()
        files = [f for f in self.recentFiles if f != current and exists(f)]
        for i, f in enumerate(files):
            icon = utils.newIcon('brain')
            action = QtGui.QAction(icon, '&%d %s' % (i + 1, QtCore.QFileInfo(f).fileName()), self)
            action.triggered.connect(functools.partial(self.loadRecent, f))
            menu.addAction(action)

    def update_models_menu(self):
        menu = self.menus.saved_models
        menu.clear()
        with open('saved_models.json') as json_file:
            data = json.load(json_file)
            i = 0
            for model_name in list(data.keys()):
                if i >= 6:
                    break
                icon = utils.newIcon('brain')
                action = QtGui.QAction(icon, '&%d %s' % (i + 1, model_name), self)
                action.triggered.connect(functools.partial(self.change_curr_model, model_name))
                menu.addAction(action)
                i += 1
        self.add_tracking_models_menu()
        self.add_certain_area_menu()

    def add_tracking_models_menu(self):
        menu2 = self.menus.tracking_models
        menu2.clear()
        icon = utils.newIcon('tracking')
        action = QtGui.QAction(icon, '1 Byte track (DEFAULT)', self)
        action.triggered.connect(lambda: self.update_tracking_method('bytetrack'))
        menu2.addAction(action)
        icon = utils.newIcon('tracking')
        action = QtGui.QAction(icon, '2 Strong SORT  (lowest id switch)', self)
        action.triggered.connect(lambda: self.update_tracking_method('strongsort'))
        menu2.addAction(action)
        icon = utils.newIcon('tracking')
        action = QtGui.QAction(icon, '3 Deep SORT', self)
        action.triggered.connect(lambda: self.update_tracking_method('deepocsort'))
        menu2.addAction(action)
        icon = utils.newIcon('tracking')
        action = QtGui.QAction(icon, '4 OC SORT', self)
        action.triggered.connect(lambda: self.update_tracking_method('ocsort'))
        menu2.addAction(action)
        icon = utils.newIcon('tracking')
        action = QtGui.QAction(icon, '5 BoT SORT', self)
        action.triggered.connect(lambda: self.update_tracking_method('botsort'))
        menu2.addAction(action)

    def add_certain_area_menu(self):
        menu3 = self.menus.certain_area
        menu3.clear()
        icon = utils.newIcon('polygon')
        action = QtGui.QAction(icon, 'Select Certain Area', self)
        action.triggered.connect(lambda: self.certain_area_clicked(1))
        menu3.addAction(action)
        icon = utils.newIcon('rectangle')
        action = QtGui.QAction(icon, 'Cancel Area', self)
        action.triggered.connect(lambda: self.certain_area_clicked(0))
        menu3.addAction(action)

    def update_tracking_method(self, method='bytetrack'):
        self.waitWindow(visible=True, text=f'Please Wait.\n{method} is Loading...')
        self.tracking_method = method
        self.tracking_config = ROOT / 'trackers' / method / 'configs' / (method + '.yaml')
        with torch.no_grad():
            device = select_device('')
            print(f'tracking method {self.tracking_method} , config {self.tracking_config} , reid {reid_weights} , device {device} , half {False}')
            self.tracker = create_tracker(self.tracking_method, self.tracking_config, reid_weights, device, False)
            if hasattr(self.tracker, 'model'):
                if hasattr(self.tracker.model, 'warmup'):
                    self.tracker.model.warmup()
        self.waitWindow()
        print(f'Changed tracking method to {method}')

    def popLabelListMenu(self, point):
        self.menus.labelList.exec(self.labelList.mapToGlobal(point))

    def validateLabel(self, label):
        if self._config['validate_label'] is None:
            return True
        for i in range(self.uniqLabelList.count()):
            label_i = self.uniqLabelList.item(i).data(Qt.ItemDataRole.UserRole)
            if self._config['validate_label'] in ['exact']:
                if label_i == label:
                    return True
        return False

    def setCreateMode(self):
        self.turnON_SAM()
        self.toggleDrawMode(False, createMode='polygon')
        return

    def editLabel(self, item=None):
        if self.current_annotation_mode == 'video':
            self.update_current_frame_annotation()
        if item and (not isinstance(item, LabelListWidgetItem)):
            raise TypeError('item must be LabelListWidgetItem type')
        if not self.canvas.editing():
            return
        if not item:
            item = self.currentItem()
        if item is None:
            return
        shape = item.shape()
        if shape is None:
            return
        old_text, old_flags, old_group_id, old_content = self.labelDialog.popUp(text=shape.label, flags=shape.flags, group_id=shape.group_id, content=shape.content, skip_flag=True)
        text, flags, new_group_id, content = self.labelDialog.popUp(text=shape.label, flags=shape.flags, group_id=shape.group_id, content=shape.content)
        if text is None:
            return
        if not self.validateLabel(text):
            self.errorMessage(self.tr('Invalid label'), self.tr("Invalid label '{}' with validation type '{}'").format(text, self._config['validate_label']))
            return
        shape.label = text
        shape.flags = flags
        shape.group_id = new_group_id
        shape.content = str(content)
        if self.current_annotation_mode == 'img' or self.current_annotation_mode == 'dir':
            item.setText(f'{shape.label}')
            self.setDirty()
            if not self.uniqLabelList.findItemsByLabel(shape.label):
                item = QtWidgets.QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, shape.label)
                self.uniqLabelList.addItem(item)
            self.refresh_image_MODE()
            return
        if shape.group_id is None:
            item.setText(shape.label)
        else:
            idChanged = old_group_id != new_group_id
            result, self.featuresOptions, only_this_frame, duplicates = editLabel_idChanged_UI(self.featuresOptions, old_group_id, new_group_id, self.id_frames_rec, self.INDEX_OF_CURRENT_FRAME)
            if duplicates or result != QtWidgets.QDialog.DialogCode.Accepted:
                shape.label = old_text
                shape.flags = old_flags
                shape.content = old_content
                shape.group_id = old_group_id
                return
            self.minID = min(self.minID, new_group_id - 1)
            listObj = self.load_objects_from_json__orjson()
            self.id_frames_rec, self.CURRENT_ANNOATAION_TRAJECTORIES, listObj = editLabel_handle_data(currFrame=self.INDEX_OF_CURRENT_FRAME, listObj=listObj, trajectories=self.CURRENT_ANNOATAION_TRAJECTORIES, id_frames_rec=self.id_frames_rec, idChanged=idChanged, only_this_frame=only_this_frame, shape=shape, old_group_id=old_group_id, new_group_id=new_group_id)
            self.load_objects_to_json__orjson(listObj)
            self.main_video_frames_slider_changed()

    def mark_as_key(self):
        """
        Summary:
            This function is called when the user presses the "Mark as Key" button.
            It marks the selected shape as a key frame.
        """
        try:
            self.update_current_frame_annotation()
            id = self.canvas.selectedShapes[0].group_id
            try:
                if self.INDEX_OF_CURRENT_FRAME not in self.key_frames['id_' + str(id)]:
                    self.key_frames['id_' + str(id)].add(self.INDEX_OF_CURRENT_FRAME)
                else:
                    res = MsgBox.OKmsgBox('Caution', f'Frame {self.INDEX_OF_CURRENT_FRAME} is already a key frame for ID {id}.\nDo you want to remove it?', 'warning', turnResult=True)
                    if res == QtWidgets.QMessageBox.StandardButton.Ok:
                        self.key_frames['id_' + str(id)].remove(self.INDEX_OF_CURRENT_FRAME)
                    else:
                        return
            except:
                self.key_frames['id_' + str(id)] = set()
                self.key_frames['id_' + str(id)].add(self.INDEX_OF_CURRENT_FRAME)
            self.main_video_frames_slider_changed()
        except Exception as e:
            MsgBox.OKmsgBox('Error', f'Error: {e}', 'critical')

    def remove_all_keyframes(self):
        try:
            self.update_current_frame_annotation()
            id = self.canvas.selectedShapes[0].group_id
            self.key_frames['id_' + str(id)] = set()
        except:
            pass

    def rec_frame_for_id(self, id, frame, type_='add'):
        """
        Summary:
            To store the frames in which the object with the given id is present.

        Args:
            id (int): The id of the object.
            frame (int): The frame number.
            type_ (str, optional): 'add' or 'remove'. Defaults to 'add'.
                                    'add' to add the frame to the list of frames in which the object is present.
                                    'remove' to remove the frame from the list of frames in which the object is present.

        Returns:
            None
        """
        if type_ == 'add':
            try:
                self.id_frames_rec['id_' + str(id)].add(frame)
            except:
                self.id_frames_rec['id_' + str(id)] = set()
                self.id_frames_rec['id_' + str(id)].add(frame)
        else:
            try:
                self.id_frames_rec['id_' + str(id)].remove(frame)
            except:
                pass

    def interpolateMENU(self, item=None):
        try:
            if len(self.canvas.selectedShapes) == 0:
                mb = QtWidgets.QMessageBox
                msg = self.tr('Interpolate all IDs?\n')
                answer = mb.warning(self, self.tr('Attention'), msg, mb.StandardButton.Yes | mb.StandardButton.No)
                if answer != mb.StandardButton.Yes:
                    return
                else:
                    self.update_current_frame_annotation()
                    keys = list(self.id_frames_rec.keys())
                    idsORG = [int(keys[i][3:]) for i in range(len(keys))]
            else:
                self.update_current_frame_annotation()
                idsORG = [shape.group_id for shape in self.canvas.selectedShapes]
                id = self.canvas.selectedShapes[0].group_id
            result, self.featuresOptions = interpolation_UI.PopUp(self.featuresOptions)
            if result != QtWidgets.QDialog.DialogCode.Accepted:
                return
            with_linear = True if self.featuresOptions['interpolationDefMethod'] == 'linear' else False
            with_sam = True if self.featuresOptions['interpolationDefMethod'] == 'SAM' else False
            with_keyframes = True if self.featuresOptions['interpolationDefType'] == 'key' else False
            if with_keyframes:
                allAccepted, allRejected, ids = mathOps.checkKeyFrames(idsORG, self.key_frames)
                if not allAccepted:
                    if allRejected:
                        MsgBox.OKmsgBox('Key Frames Error', f'All of the selected IDs have no KEY frames.\n    ie. less than 2 key frames\n The interpolation is NOT performed.')
                        return
                    else:
                        resutl = MsgBox.OKmsgBox('Key Frames Error', f'Some of the selected IDs have no KEY frames.\n    ie. less than 2 key frames\n The interpolation is performed only for the IDs with KEY frames.\nIDs: {ids}.', 'info', turnResult=True)
                        if resutl != QtWidgets.QMessageBox.StandardButton.Ok:
                            return
            else:
                ids = idsORG
            self.interrupted = False
            if with_sam:
                self.interpolate_with_sam(ids, with_keyframes)
            else:
                for id in ids:
                    QtWidgets.QApplication.processEvents()
                    if self.interrupted:
                        self.interrupted = False
                        break
                    self.interpolate(id=id, only_edited=with_keyframes)
            self.waitWindow()
        except Exception as e:
            MsgBox.OKmsgBox('Error', f'Error: {e}', 'critical')

    def interpolate(self, id, only_edited=False):
        """
        Summary:
            This function is called when the user presses the "Interpolate" button.
            It interpolates the object with the given id.

        Args:
            id (int): The id of the object.
            only_edited (bool, optional): True to interpolate using only the key frames. Defaults to False.
        """
        self.waitWindow(visible=True, text=f'Please Wait.\nID {id} is being interpolated...')
        listObj = self.load_objects_from_json__orjson()
        if only_edited:
            try:
                FRAMES = list(self.key_frames['id_' + str(id)])
            except:
                return
        else:
            FRAMES = list(self.id_frames_rec['id_' + str(id)]) if len(self.id_frames_rec['id_' + str(id)]) > 1 else [-1]
        first_frame_idx = min(FRAMES)
        last_frame_idx = max(FRAMES)
        if first_frame_idx >= last_frame_idx:
            return
        records = [None for i in range(first_frame_idx - 1, last_frame_idx, 1)]
        for frame in range(first_frame_idx, last_frame_idx + 1, 1):
            listobjframe = listObj[frame - 1]['frame_idx']
            frameobjects = listObj[frame - 1]['frame_data']
            for object_ in frameobjects:
                if object_['tracker_id'] == id:
                    if not only_edited or listobjframe in FRAMES:
                        records[frame - first_frame_idx] = copy.deepcopy(object_)
                    break
        baseObject = None
        baseObjectFrame = None
        nextObject = None
        nextObjectFrame = None
        for frame in range(first_frame_idx, last_frame_idx, 1):
            QtWidgets.QApplication.processEvents()
            if self.interrupted:
                break
            listobjframe = listObj[frame - 1]['frame_idx']
            frameobjects = listObj[frame - 1]['frame_data']
            if records[frame - first_frame_idx] is not None:
                baseObject = copy.deepcopy(records[frame - first_frame_idx])
                baseObjectFrame = frame
                for j in range(frame + 1, last_frame_idx + 1, 1):
                    if records[j - first_frame_idx] != None:
                        nextObject = copy.deepcopy(records[j - first_frame_idx])
                        nextObjectFrame = j
                        break
                continue
            if only_edited and frame not in FRAMES:
                for object_ in frameobjects:
                    if object_['tracker_id'] == id:
                        listObj[frame - 1]['frame_data'].remove(object_)
                        break
            cur = mathOps.getInterpolated(baseObject=baseObject, baseObjectFrame=baseObjectFrame, nextObject=nextObject, nextObjectFrame=nextObjectFrame, curFrame=frame)
            listObj[frame - 1]['frame_data'].append(cur)
            self.rec_frame_for_id(id, frame)
        self.load_objects_to_json__orjson(listObj)
        frames = range(first_frame_idx - 1, last_frame_idx, 1)
        self.calculate_trajectories(frames)
        self.main_video_frames_slider_changed()

    def interpolate_with_sam(self, idsLISTX, only_edited=False):
        """
        Summary:
            This function is called when the user chooses the "Interpolate with SAM".
            It interpolates and inhance the objects with the given ids using SAM.

        Args:
            idsLISTX (list): The list of ids of the objects.
        """
        self.waitWindow(visible=True, text=f'Please Wait.\nIDs are being interpolated with SAM...')
        if self.sam_model_comboBox.currentText() == 'Select Model (SAM disabled)':
            MsgBox.OKmsgBox('SAM is disabled', f'SAM is disabled.\nPlease enable SAM.')
            return
        idsLIST = []
        first_frame_idxLIST = []
        last_frame_idxLIST = []
        for id in idsLISTX:
            try:
                if only_edited:
                    [minf, maxf] = [min(self.key_frames['id_' + str(id)]), max(self.key_frames['id_' + str(id)])]
                else:
                    [minf, maxf] = [min(self.id_frames_rec['id_' + str(id)]), max(self.id_frames_rec['id_' + str(id)])]
            except:
                continue
            if minf == maxf:
                continue
            first_frame_idxLIST.append(minf)
            last_frame_idxLIST.append(maxf)
            idsLIST.append(id)
        if len(idsLIST) == 0:
            return
        overwrite = self.featuresOptions['interpolationOverwrite']
        listObj = self.load_objects_from_json__orjson()
        listObjNEW = copy.deepcopy(listObj)
        recordsLIST = [[None for ii in range(first_frame_idxLIST[i], last_frame_idxLIST[i] + 1)] for i in range(len(idsLIST))]
        for i in range(min(first_frame_idxLIST) - 1, max(last_frame_idxLIST), 1):
            self.waitWindow(visible=True)
            listobjframe = listObj[i]['frame_idx']
            frameobjects = listObj[i]['frame_data'].copy()
            for object_ in frameobjects:
                if object_['tracker_id'] in idsLIST:
                    index = idsLIST.index(object_['tracker_id'])
                    recordsLIST[index][listobjframe - first_frame_idxLIST[index]] = copy.deepcopy(object_)
                    listObj[i]['frame_data'].remove(object_)
        for frameIDX in range(min(first_frame_idxLIST), max(last_frame_idxLIST) + 1):
            QtWidgets.QApplication.processEvents()
            if self.interrupted:
                self.interrupted = False
                break
            self.waitWindow(visible=True, text=f'Please Wait.\nIDs are being interpolated with SAM...\nFrame {frameIDX}')
            frameIMAGE = self.get_frame_by_idx(frameIDX)
            for ididx in range(len(idsLIST)):
                i = frameIDX - first_frame_idxLIST[ididx]
                self.waitWindow(visible=True)
                if frameIDX < first_frame_idxLIST[ididx] or frameIDX > last_frame_idxLIST[ididx]:
                    continue
                records = recordsLIST[ididx]
                if records[i] != None:
                    current = copy.deepcopy(records[i])
                    cur_bbox = current['bbox']
                    if not overwrite:
                        listObj[frameIDX - 1]['frame_data'].append(current)
                        continue
                else:
                    prev_idx = i - 1
                    current = copy.deepcopy(records[i - 1])
                    next_idx = i + 1
                    for j in range(i + 1, len(records)):
                        self.waitWindow(visible=True)
                        if records[j] != None:
                            next_idx = j
                            break
                    cur_bbox = (next_idx - i) / (next_idx - prev_idx) * np.array(records[prev_idx]['bbox']) + (i - prev_idx) / (next_idx - prev_idx) * np.array(records[next_idx]['bbox'])
                    cur_bbox = [int(cur_bbox[i]) for i in range(len(cur_bbox))]
                    current['bbox'] = copy.deepcopy(cur_bbox)
                    records[i] = current
                try:
                    same_image = self.sam_predictor.check_image(frameIMAGE)
                except:
                    return
                cur_bbox, cur_segment = self.sam_enhanced_bbox_segment(frameIMAGE, cur_bbox, 1.2, max_itr=5, forSHAPE=False)
                current['bbox'] = copy.deepcopy(cur_bbox)
                current['segment'] = copy.deepcopy(cur_segment)
                listObj[frameIDX - 1]['frame_data'].append(current)
                self.rec_frame_for_id(idsLIST[ididx], frameIDX)
            listObjNEW[frameIDX - 1] = copy.deepcopy(listObj[frameIDX - 1])
        self.load_objects_to_json__orjson(listObjNEW)
        self.calculate_trajectories(range(min(first_frame_idxLIST) - 1, max(last_frame_idxLIST), 1))
        self.main_video_frames_slider_changed()
        self._config = get_config()
        if not self._config['mute']:
            if not self.isActiveWindow():
                notification.PopUp('SAM Interpolation Completed')

    def get_frame_by_idx(self, frameIDX):
        self.CAP.set(cv2.CAP_PROP_POS_FRAMES, frameIDX - 1)
        success, img = self.CAP.read()
        return img

    def scaleMENU(self):
        """
        Summary:
            This function is called when the user presses the "Scale" button.
            It scales the selected shape.
        """
        if len(self.canvas.selectedShapes) != 1:
            MsgBox.OKmsgBox(f'Scale error', f'There is {len(self.canvas.selectedShapes)} selected shapes. Please select only one shape to scale.')
            return
        result = scaleObject_UI.PopUp(self)
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            self.update_current_frame_annotation_button_clicked()
            return
        else:
            self.main_video_frames_slider_changed()
            return

    def ctrlCopy(self):
        """
        Summary:
            This function is called when the user presses the "Copy" button.
            It copies the selected shape(s).
        """
        if len(self.canvas.selectedShapes) == 0:
            return
        self.copiedShapes = copy.deepcopy(self.canvas.selectedShapes)

    def ctrlPaste(self):
        """
        Summary:
            This function is called when the user presses the "Paste" button.
            It pastes the copied shape(s).
        """
        if len(self.copiedShapes) == 0:
            return
        ids = [shape.group_id for shape in self.canvas.shapes]
        flag = False
        for shape in self.copiedShapes:
            if shape.group_id in ids:
                flag = True
                continue
            self.canvas.shapes.append(shape)
            self.addLabel(shape)
            self.rec_frame_for_id(shape.group_id, self.INDEX_OF_CURRENT_FRAME)
        if flag:
            MsgBox.OKmsgBox('IDs already exist', 'A Shape(s) with the same ID(s) already exist(s) in this frame.\n\nShapes with no duplicate IDs are Copied Successfully.')
        if self.current_annotation_mode == 'video':
            self.update_current_frame_annotation_button_clicked()

    def fileSearchChanged(self):
        self.importDirImages(self.lastOpenDir, pattern=self.fileSearch.text(), load=False)

    def fileSelectionChanged(self):
        items = self.fileListWidget.selectedItems()
        if not items:
            return
        item = items[0]
        if not self.mayContinue():
            return
        currIndex = self.imageList.index(str(item.text()))
        if currIndex < len(self.imageList):
            filename = self.imageList[currIndex]
            if filename:
                self.loadFile(filename)
                self.refresh_image_MODE()

    def shapeSelectionChanged(self, selected_shapes):
        try:
            self._noSelectionSlot = True
            for shape in self.canvas.selectedShapes:
                shape.selected = False
            self.labelList.clearSelection()
            self.canvas.selectedShapes = selected_shapes
            for shape in self.canvas.selectedShapes:
                shape.selected = True
                item = self.labelList.findItemByShape(shape)
                self.labelList.selectItem(item)
                self.labelList.scrollToItem(item)
            self._noSelectionSlot = False
            n_selected = len(selected_shapes)
            self.actions.delete.setEnabled(n_selected)
            self.actions.copy.setEnabled(n_selected)
            self.actions.edit.setEnabled(n_selected == 1)
        except Exception as e:
            pass

    def addLabel(self, shape):
        if shape.group_id is None or self.current_annotation_mode != 'video':
            text = shape.label
        else:
            text = f' ID {shape.group_id}: {shape.label}'
        label_list_item = LabelListWidgetItem(text, shape)
        self.labelList.addItem(label_list_item)
        if not self.uniqLabelList.findItemsByLabel(shape.label):
            item = self.uniqLabelList.createItemFromLabel(shape.label)
            self.uniqLabelList.addItem(item)
            rgb = self._get_rgb_by_label(shape.label)
            self.uniqLabelList.setItemLabel(item, shape.label, rgb)
        self.labelDialog.addLabelHistory(shape.label)
        for action in self.actions.onShapesPresent:
            action.setEnabled(True)
        rgb = self._get_rgb_by_label(shape.label)
        r, g, b = rgb
        label_list_item.setText('{} <font color="#{:02x}{:02x}{:02x}">●</font>'.format(text, r, g, b))
        shape.line_color = QtGui.QColor(r, g, b)
        shape.vertex_fill_color = QtGui.QColor(r, g, b)
        shape.hvertex_fill_color = QtGui.QColor(255, 255, 255)
        shape.fill_color = QtGui.QColor(r, g, b, 128)
        shape.select_line_color = QtGui.QColor(255, 255, 255)
        shape.select_fill_color = QtGui.QColor(r, g, b, 155)

    def _get_rgb_by_label(self, label):
        if self._config['shape_color'] == 'auto':
            label_ascii = sum([ord(c) for c in label])
            idx = label_ascii % len(color_palette)
            color = color_palette[idx]
            return color[::-1]
        elif self._config['shape_color'] == 'manual' and self._config['label_colors'] and (label in self._config['label_colors']):
            return self._config['label_colors'][label]
        elif self._config['default_shape_color']:
            return self._config['default_shape_color']

    def remLabels(self, shapes):
        for shape in shapes:
            item = self.labelList.findItemByShape(shape)
            self.labelList.removeItem(item)

    def loadShapes(self, shapes, replace=True):
        self._noSelectionSlot = True
        shapes = sorted(shapes, key=lambda x: int(x.group_id) if x.group_id is not None else 0)
        for shape in shapes:
            self.addLabel(shape)
        self.labelList.clearSelection()
        self._noSelectionSlot = False
        self.canvas.loadShapes(shapes, replace=replace)
        for shape in self.canvas.shapes:
            self.canvas.setShapeVisible(shape, self.CURRENT_ANNOATAION_FLAGS['polygons'])

    def loadLabels(self, shapes, replace=True):
        s = []
        for shape in shapes:
            label = shape['label']
            points = shape['points']
            bbox = shape['bbox']
            shape_type = shape['shape_type']
            content = shape['content']
            group_id = shape['group_id']
            if not points:
                continue
            shape = Shape(label=label, shape_type=shape_type, group_id=group_id, content=content)
            for i in range(0, len(points), 2):
                shape.addPoint(QtCore.QPointF(points[i], points[i + 1]))
            shape.close()
            default_flags = {}
            if self._config['label_flags']:
                for pattern, keys in self._config['label_flags'].items():
                    if re.match(pattern, label):
                        for key in keys:
                            default_flags[key] = False
            shape.flags = default_flags
            s.append(shape)
        self.loadShapes(s, replace=replace)

    def loadFlags(self, flags):
        self.flag_widget.clear()
        for key, flag in flags.items():
            item = QtWidgets.QListWidgetItem(key)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if flag else Qt.CheckState.Unchecked)
            self.flag_widget.addItem(item)

    def saveLabels(self, filename):
        lf = LabelFile()

        def format_shape(s):
            data = s.other_data.copy()
            data.update(dict(label=s.label.encode('utf-8') if PY2 else s.label, points=mathOps.flattener(s.points), bbox=s.bbox, group_id=s.group_id, content=s.content, shape_type=s.shape_type, flags=s.flags))
            return data
        shapes = [format_shape(item.shape()) for item in self.labelList]
        flags = {}
        for i in range(self.flag_widget.count()):
            item = self.flag_widget.item(i)
            key = item.text()
            flag = item.checkState() == Qt.CheckState.Checked
            flags[key] = flag
        try:
            imagePath = osp.relpath(self.imagePath, osp.dirname(filename))
            imageData = self.imageData if self._config['store_data'] else None
            if osp.dirname(filename) and (not osp.exists(osp.dirname(filename))):
                os.makedirs(osp.dirname(filename))
            lf.save(filename=filename, shapes=shapes, imagePath=imagePath, imageData=imageData, imageHeight=self.image.height(), imageWidth=self.image.width(), otherData=self.otherData, flags=flags)
            self.labelFile = lf
            items = self.fileListWidget.findItems(self.imagePath, Qt.MatchFlag.MatchExactly)
            if len(items) > 0:
                if len(items) != 1:
                    raise RuntimeError('There are duplicate files.')
                items[0].setCheckState(Qt.CheckState.Checked)
            return True
        except LabelFileError as e:
            self.errorMessage(self.tr('Error saving label data'), self.tr('<b>%s</b>') % e)
            return False

    def copySelectedShape(self):
        added_shapes = self.canvas.copySelectedShapes()
        self.labelList.clearSelection()
        for shape in added_shapes:
            self.addLabel(shape)
        self.setDirty()

    def labelSelectionChanged(self):
        if self._noSelectionSlot:
            return
        if self.canvas.editing():
            selected_shapes = []
            for item in self.labelList.selectedItems():
                selected_shapes.append(item.shape())
            if selected_shapes:
                self.canvas.selectShapes(selected_shapes)
            else:
                self.canvas.deSelectShape()

    def labelItemChanged(self, item):
        shape = item.shape()
        self.canvas.setShapeVisible(shape, item.checkState() == Qt.CheckState.Checked)

    def labelOrderChanged(self):
        self.setDirty()
        self.canvas.loadShapes([item.shape() for item in self.labelList])

    def newShape(self):
        """Pop-up and give focus to the label editor.
        position MUST be in global coordinates.
        """
        items = self.uniqLabelList.selectedItems()
        text = None
        if items:
            text = items[0].data(Qt.ItemDataRole.UserRole)
        flags = {}
        group_id = None
        if self._config['display_label_popup'] or not text:
            previous_text = self.labelDialog.edit.text()
            text, flags, group_id, content = self.labelDialog.popUp(text)
            if not text:
                self.labelDialog.edit.setText(previous_text)
        if text and (not self.validateLabel(text)):
            self.errorMessage(self.tr('Invalid label'), self.tr("Invalid label '{}' with validation type '{}'").format(text, self._config['validate_label']))
            text = ''
        if text == 'SAM instance':
            text = 'SAM instance - confirmed'
        if self.current_annotation_mode == 'video':
            group_id, text = getIDfromUser_UI.PopUp(self, group_id, text)
        if text:
            if group_id is None:
                group_id = self.minID
                self.minID -= 1
            else:
                self.minID = min(self.minID, group_id - 1)
            if self.canvas.SAM_mode == 'finished':
                self.current_sam_shape['label'] = text
                self.current_sam_shape['group_id'] = group_id
            else:
                self.labelList.clearSelection()
                shape = self.canvas.setLastLabel(text, flags)
                shape.group_id = group_id
                shape.content = content
                self.addLabel(shape)
                self.rec_frame_for_id(group_id, self.INDEX_OF_CURRENT_FRAME)
            self.actions.editMode.setEnabled(True)
            self.actions.undoLastPoint.setEnabled(False)
            self.actions.undo.setEnabled(True)
            self.setDirty()
            self.refresh_image_MODE()
        elif self.canvas.SAM_mode == 'finished':
            self.current_sam_shape['label'] = text
            self.current_sam_shape['group_id'] = -1
            self.canvas.SAM_mode = ''
        else:
            self.canvas.undoLastLine()
            self.canvas.shapesBackups.pop()
        if self.current_annotation_mode == 'video':
            self.update_current_frame_annotation_button_clicked()
            self.update_current_frame_annotation_button_clicked()

    def scrollRequest(self, delta, orientation):
        units = -delta * 0.1
        bar = self.scrollBars[orientation]
        value = bar.value() + bar.singleStep() * units
        self.setScroll(orientation, value)

    def setScroll(self, orientation, value):
        self.scrollBars[orientation].setValue(value)
        self.scroll_values[orientation][self.filename] = value

    def setZoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.MANUAL_ZOOM
        self.zoomWidget.setValue(value)
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def addZoom(self, increment=1.1):
        zoom_value = self.zoomWidget.value() * increment
        if increment > 1:
            zoom_value = math.ceil(zoom_value)
        else:
            zoom_value = math.floor(zoom_value)
        self.setZoom(zoom_value)

    def zoomRequest(self, delta, pos):
        canvas_width_old = self.canvas.width()
        units = 1.1
        if delta < 0:
            units = 0.9
        self.addZoom(units)
        canvas_width_new = self.canvas.width()
        if canvas_width_old != canvas_width_new:
            canvas_scale_factor = canvas_width_new / canvas_width_old
            x_shift = round(pos.x() * canvas_scale_factor) - pos.x()
            y_shift = round(pos.y() * canvas_scale_factor) - pos.y()
            self.setScroll(Qt.Orientation.Horizontal, self.scrollBars[Qt.Orientation.Horizontal].value() + x_shift)
            self.setScroll(Qt.Orientation.Vertical, self.scrollBars[Qt.Orientation.Vertical].value() + y_shift)

    def setFitWindow(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjustScale()

    def setFitWidth(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjustScale()

    def onNewBrightnessContrast(self, qimage):
        self.canvas.loadPixmap(QtGui.QPixmap.fromImage(qimage), clear_shapes=False)

    def enable_show_cross_line(self, enabled):
        self._config['show_cross_line'] = enabled
        self.actions.show_cross_line.setChecked(enabled)
        self.canvas.set_show_cross_line(enabled)

    def brightnessContrast(self, value):
        dialog = BrightnessContrastDialog(utils.img_data_to_pil(self.imageData), self.onNewBrightnessContrast, parent=self)
        brightness, contrast = self.brightnessContrast_values.get(self.filename, (None, None))
        if brightness is not None:
            dialog.slider_brightness.setValue(brightness)
        if contrast is not None:
            dialog.slider_contrast.setValue(contrast)
        dialog.exec()
        brightness = dialog.slider_brightness.value()
        contrast = dialog.slider_contrast.value()
        self.brightnessContrast_values[self.filename] = (brightness, contrast)

    def togglePolygons(self, value):
        for item in self.labelList:
            item.setCheckState(Qt.CheckState.Checked if value else Qt.CheckState.Unchecked)

    def loadFile(self, filename=None):
        """Load the specified file, or the last opened file if None."""
        if filename in self.imageList and self.fileListWidget.currentRow() != self.imageList.index(filename):
            self.fileListWidget.setCurrentRow(self.imageList.index(filename))
            self.fileListWidget.repaint()
            return
        self.resetState()
        self.canvas.setEnabled(False)
        if filename is None:
            filename = self.settings.value('filename', '')
        filename = str(filename)
        if not QtCore.QFile.exists(filename):
            print(f'File {filename} does not exist')
            self.errorMessage(self.tr('Error opening file'), self.tr('No such file: <b>%s</b>') % filename)
            return False
        self.status(self.tr('Loading %s...') % osp.basename(str(filename)))
        label_file = osp.splitext(filename)[0] + '.json'
        if self.output_dir:
            label_file_without_path = osp.basename(label_file)
            label_file = osp.join(self.output_dir, label_file_without_path)
        if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(label_file):
            try:
                self.labelFile = LabelFile(label_file)
            except LabelFileError as e:
                self.errorMessage(self.tr('Error opening file'), self.tr('<p><b>%s</b></p><p>Make sure <i>%s</i> is a valid label file.') % (e, label_file))
                self.status(self.tr('Error reading %s') % label_file)
                return False
            self.imageData = self.labelFile.imageData
            self.imagePath = osp.join(osp.dirname(label_file), self.labelFile.imagePath)
            self.otherData = self.labelFile.otherData
        else:
            self.imageData = LabelFile.load_image_file(filename)
            if self.imageData:
                self.imagePath = filename
            self.labelFile = None
        image = QtGui.QImage.fromData(self.imageData)
        if image.isNull():
            formats = ['*.{}'.format(fmt.data().decode()) for fmt in QtGui.QImageReader.supportedImageFormats()]
            self.errorMessage(self.tr('Error opening file'), self.tr('<p>Make sure <i>{0}</i> is a valid image file.<br/>Supported image formats: {1}</p>').format(filename, ','.join(formats)))
            self.status(self.tr('Error reading %s') % filename)
            return False
        self.image = image
        self.CURRENT_FRAME_IMAGE = cv2.imread(filename)
        self.filename = filename
        if self._config['keep_prev']:
            prev_shapes = self.canvas.shapes
        self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
        flags = {k: False for k in self._config['flags'] or []}
        if self.labelFile:
            self.actions.export.setEnabled(True)
            self.CURRENT_SHAPES_IN_IMG = self.labelFile.shapes
            self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
            self.loadLabels(self.labelFile.shapes)
            if self.labelFile.flags is not None:
                flags.update(self.labelFile.flags)
        self.loadFlags(flags)
        if self._config['keep_prev'] and self.noShapes():
            self.loadShapes(prev_shapes, replace=False)
            self.setDirty()
        else:
            self.setClean()
        self.canvas.setEnabled(True)
        is_initial_load = not self.zoom_values
        if self.filename in self.zoom_values:
            self.zoomMode = self.zoom_values[self.filename][0]
            self.setZoom(self.zoom_values[self.filename][1])
        elif is_initial_load or not self._config['keep_prev_scale']:
            self.adjustScale(initial=True)
        for orientation in self.scroll_values:
            if self.filename in self.scroll_values[orientation]:
                self.setScroll(orientation, self.scroll_values[orientation][self.filename])
        if self.sam_predictor is not None:
            self.sam_predictor.clear_logit()
            self.canvas.SAM_coordinates = []
        dialog = BrightnessContrastDialog(utils.img_data_to_pil(self.imageData), self.onNewBrightnessContrast, parent=self)
        brightness, contrast = self.brightnessContrast_values.get(self.filename, (None, None))
        if self._config['keep_prev_brightness'] and self.recentFiles:
            brightness, _ = self.brightnessContrast_values.get(self.recentFiles[0], (None, None))
        if self._config['keep_prev_contrast'] and self.recentFiles:
            _, contrast = self.brightnessContrast_values.get(self.recentFiles[0], (None, None))
        if brightness is not None:
            dialog.slider_brightness.setValue(brightness)
        if contrast is not None:
            dialog.slider_contrast.setValue(contrast)
        self.brightnessContrast_values[self.filename] = (brightness, contrast)
        if brightness is not None or contrast is not None:
            dialog.onNewValue(None)
        self.paintCanvas()
        self.addRecentFile(self.filename)
        self.toggleActions(True)
        self.canvas.setFocus()
        self.status(self.tr('Loaded %s') % osp.basename(str(filename)))
        return True

    def resizeEvent(self, event):
        if self.canvas and (not self.image.isNull()) and (self.zoomMode != self.MANUAL_ZOOM):
            self.adjustScale()
        super(MainWindow, self).resizeEvent(event)

    def paintCanvas(self):
        assert not self.image.isNull(), 'cannot paint null image'
        self.canvas.scale = 0.01 * self.zoomWidget.value()
        self.canvas.adjustSize()
        self.canvas.update()

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        value = int(100 * value)
        self.zoomWidget.setValue(value)
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def scaleFitWindow(self):
        """Figure out the size of the pixmap to fit the main widget."""
        e = 2.0
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scaleFitWidth(self):
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def enableSaveImageWithData(self, enabled):
        self._config['store_data'] = enabled
        self.actions.saveWithImageData.setChecked(enabled)

    def closeEvent(self, event):
        if not self.mayContinue():
            event.ignore()
        else:
            self.Escape_clicked()
        self.settings.setValue('filename', self.filename if self.filename else '')
        self.settings.setValue('window/size', self.size())
        self.settings.setValue('window/position', self.pos())
        self.settings.setValue('window/state', self.saveState())
        self.settings.setValue('recentFiles', self.recentFiles)

    def dragEnterEvent(self, event):
        extensions = ['.%s' % fmt.data().decode().lower() for fmt in QtGui.QImageReader.supportedImageFormats()]
        if event.mimeData().hasUrls():
            items = [i.toLocalFile() for i in event.mimeData().urls()]
            if any([i.lower().endswith(tuple(extensions)) for i in items]):
                event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not self.mayContinue():
            event.ignore()
            return
        items = [i.toLocalFile() for i in event.mimeData().urls()]
        self.importDroppedImageFiles(items)

    def loadRecent(self, filename):
        if self.mayContinue():
            self.loadFile(filename)

    def change_curr_model(self, model_name):
        """
        Summary:
            Change current model to the model_name

        Args:
            model_name (str): name of the model to be changed to
        """
        self.multi_model_flag = False
        self.waitWindow(visible=True, text=f'Please Wait.\n{model_name} is being Loaded...')
        self.intelligenceHelper.current_model_name, self.intelligenceHelper.current_mm_model = self.intelligenceHelper.make_mm_model(model_name)
        self.waitWindow()

    def model_explorer(self):
        """
        Summary:
            Open model explorer dialog to select or download models
        """
        self._config = get_config()
        model_explorer_dialog = utils.ModelExplorerDialog(self, self._config['mute'], notification.PopUp)
        model_explorer_dialog.adjustSize()
        model_explorer_dialog.setMinimumWidth(model_explorer_dialog.table.width() * 1.5)
        model_explorer_dialog.setMinimumHeight(model_explorer_dialog.table.rowHeight(0) * 10)
        model_explorer_dialog.exec()
        if self.helper_first_time_flag:
            try:
                self.intelligenceHelper = Intelligence(self)
            except:
                print('it seems you have a problem with initializing model\ncheck you have at least one model')
                self.helper_first_time_flag = True
            else:
                self.helper_first_time_flag = False
        mathOps.update_saved_models_json(os.getcwd())
        selected_model_name, config, checkpoint = model_explorer_dialog.selected_model
        if selected_model_name != -1:
            self.intelligenceHelper.current_model_name, self.intelligenceHelper.current_mm_model = self.intelligenceHelper.make_mm_model_more(selected_model_name, config, checkpoint)
        self.updateSamControls()

    def openNextImg(self, _value=False, load=True):
        self.refresh_image_MODE()
        keep_prev = self._config['keep_prev']
        if not self.mayContinue():
            return
        if len(self.imageList) <= 0:
            return
        filename = None
        if self.filename is None:
            filename = self.imageList[0]
        else:
            currIndex = self.imageList.index(self.filename)
            if currIndex + 1 < len(self.imageList):
                filename = self.imageList[currIndex + 1]
            else:
                filename = self.imageList[-1]
        self.filename = filename
        if self.filename and load:
            self.loadFile(self.filename)
        self._config['keep_prev'] = keep_prev
        self.refresh_image_MODE()

    def openFile(self, _value=False):
        self.actions.export.setEnabled(False)
        try:
            cv2.destroyWindow('video processing')
        except:
            pass
        if not self.mayContinue():
            return
        path = osp.dirname(str(self.filename)) if self.filename else '.'
        formats = ['*.{}'.format(fmt.data().decode()) for fmt in QtGui.QImageReader.supportedImageFormats()]
        filters = self.tr('Image & Label files (%s)') % ' '.join(formats + ['*%s' % LabelFile.suffix])
        filename = QtWidgets.QFileDialog.getOpenFileName(self, self.tr('%s - Choose Image or Label file') % __appname__, path, filters)
        filename, _ = filename
        filename = str(filename)
        if filename:
            self.reset_for_new_mode('img')
            self.loadFile(filename)
            self.refresh_image_MODE()
            self.set_video_controls_visibility(False)
        self.filename = filename
        self.fileListWidget.clear()
        self.uniqLabelList.clear()
        for option in self.vis_options:
            if option in [self.id_checkBox, self.traj_checkBox, self.trajectory_length_lineEdit]:
                option.setEnabled(False)
            else:
                option.setEnabled(True)

    def changeOutputDirDialog(self, _value=False):
        default_output_dir = self.output_dir
        if default_output_dir is None and self.filename:
            default_output_dir = osp.dirname(self.filename)
        if default_output_dir is None:
            default_output_dir = self.currentPath()
        output_dir = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr('%s - Save/Load Annotations in Directory') % __appname__, default_output_dir, QtWidgets.QFileDialog.Option.ShowDirsOnly | QtWidgets.QFileDialog.Option.DontResolveSymlinks)
        output_dir = str(output_dir)
        if not output_dir:
            return
        self.output_dir = output_dir
        self.statusBar().showMessage(self.tr('%s . Annotations will be saved/loaded in %s') % ('Change Annotations Dir', self.output_dir))
        self.statusBar().show()
        current_filename = self.filename
        self.importDirImages(self.lastOpenDir, load=False)
        if current_filename in self.imageList:
            self.fileListWidget.setCurrentRow(self.imageList.index(current_filename))
            self.fileListWidget.repaint()

    def saveFile(self, _value=False):
        assert not self.image.isNull(), 'cannot save empty image'
        if self.labelFile:
            self.save_path = self.labelFile.filename
            self._saveFile(self.save_path)
        elif self.output_file:
            self.save_path = self.output_file
            self._saveFile(self.save_path)
            self.close()
        else:
            self.save_path = self.saveFileDialog()
            self._saveFile(self.save_path)
        if self.save_path is not None and self.save_path != '':
            self.actions.export.setEnabled(True)

    def exportData(self):
        """
        Export data to COCO, MOT, video, and custom exports, depending on the current annotation mode.

        If the current annotation mode is "video", the function prompts the user to select which types of exports to perform
        (COCO, MOT, video, and/or custom exports), and then prompts the user to select the output file path for each export type
        that was selected. The function then exports the data to the selected file paths.

        If the current annotation mode is "img" or "dir", the function prompts the user to select the output file path for a COCO
        export, and then exports the data to the selected file path.

        If an error occurs during the export process, the function displays an error message. Otherwise, the function displays
        a success message.
        """
        try:
            if self.current_annotation_mode == 'video':
                result, coco_radio, mot_radio, video_radio, custom_exports_radio_checked_list = exportData_UI.PopUp()
                if not result:
                    return
                json_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}_tracking_results.json'
                pth = ''
                if video_radio:
                    folderDialog = utils.FolderDialog('tracking_results.mp4', 'mp4')
                    if folderDialog.exec():
                        pth = self.export_as_video_button_clicked(folderDialog.selectedFiles()[0])
                    else:
                        return
                if coco_radio:
                    folderDialog = utils.FolderDialog('coco.json', 'json')
                    if folderDialog.exec():
                        pth = utils.exportCOCOvid(json_file_name, self.CURRENT_VIDEO_WIDTH, self.CURRENT_VIDEO_HEIGHT, folderDialog.selectedFiles()[0])
                    else:
                        return
                if mot_radio:
                    folderDialog = utils.FolderDialog('mot.txt', 'txt')
                    if folderDialog.exec():
                        pth = utils.exportMOT(json_file_name, folderDialog.selectedFiles()[0])
                    else:
                        return
                custom_exports_list_video = [custom_export for custom_export in custom_exports_list if custom_export.mode == 'video']
                if len(custom_exports_radio_checked_list) != 0:
                    for i in range(len(custom_exports_radio_checked_list)):
                        if custom_exports_radio_checked_list[i]:
                            folderDialog = utils.FolderDialog(f'{custom_exports_list_video[i].file_name}.{custom_exports_list_video[i].format}', custom_exports_list_video[i].format)
                            if folderDialog.exec():
                                try:
                                    pth = custom_exports_list_video[i](json_file_name, self.CURRENT_VIDEO_WIDTH, self.CURRENT_VIDEO_HEIGHT, folderDialog.selectedFiles()[0])
                                except Exception as e:
                                    MsgBox.OKmsgBox(f'Error', f'Error: with custom export {custom_exports_list_video[i].button_name}\n check the parameters matches the specified ones in custom_exports.py\n Error Message: {e}', 'critical')
                            else:
                                return
            elif self.current_annotation_mode == 'img' or self.current_annotation_mode == 'dir':
                result, coco_radio, custom_exports_radio_checked_list = exportData_UI.PopUp(mode='image')
                if not result:
                    return
                save_path = self.save_path if self.save_path else self.labelFile.filename
                json_paths = utils.parse_img_export(self.target_directory, save_path)
                if coco_radio:
                    folderDialog = utils.FolderDialog('coco.json', 'json')
                    if folderDialog.exec():
                        pth = utils.exportCOCO(json_paths, folderDialog.selectedFiles()[0])
                    else:
                        return
                custom_exports_list_image = [custom_export for custom_export in custom_exports_list if custom_export.mode == 'image']
                if len(custom_exports_radio_checked_list) != 0:
                    for i in range(len(custom_exports_radio_checked_list)):
                        if custom_exports_radio_checked_list[i]:
                            folderDialog = utils.FolderDialog(f'{custom_exports_list_image[i].file_name}.{custom_exports_list_image[i].format}', custom_exports_list_image[i].format)
                            if folderDialog.exec():
                                try:
                                    pth = custom_exports_list_image[i](json_paths, folderDialog.selectedFiles()[0])
                                except Exception as e:
                                    MsgBox.OKmsgBox(f'Error', f'Error: with custom export {custom_exports_list_image[i].button_name}\n check the parameters matches the specified ones in custom_exports.py\n Error Message: {e}', 'critical')
                            else:
                                return
        except Exception as e:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            msg.setText(f'Error\n {e}')
            msg.setWindowTitle('Export Error')
            print(e)
            msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.exec()
            return
        else:
            msg = QtWidgets.QMessageBox()
            try:
                if pth not in ['', None, False]:
                    msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
                    msg.setText(f'Annotations exported successfully to {pth}')
                    msg.setWindowTitle('Export Success')
                else:
                    msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
                    msg.setText(f'Export Failed')
                    msg.setWindowTitle('Export Failed')
            except:
                msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
                msg.setText(f'Export Failed')
                msg.setWindowTitle('Export Failed')
            msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.exec()

    def saveFileAs(self, _value=False):
        self.actions.export.setEnabled(True)
        assert not self.image.isNull(), 'cannot save empty image'
        self.save_path = self.saveFileDialog()
        self._saveFile(self.save_path)

    def saveFileDialog(self):
        caption = self.tr('%s - Choose File') % __appname__
        filters = self.tr('Label files (*%s)') % LabelFile.suffix
        if self.output_dir:
            dlg = QtWidgets.QFileDialog(self, caption, self.output_dir, filters)
        else:
            dlg = QtWidgets.QFileDialog(self, caption, self.currentPath(), filters)
        dlg.setDefaultSuffix(LabelFile.suffix[1:])
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        dlg.setOption(QtWidgets.QFileDialog.Option.DontConfirmOverwrite, False)
        dlg.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog, False)
        basename = osp.basename(osp.splitext(self.filename)[0])
        if self.output_dir:
            default_labelfile_name = osp.join(self.output_dir, basename + LabelFile.suffix)
        else:
            default_labelfile_name = osp.join(self.currentPath(), basename + LabelFile.suffix)
        filename = dlg.getSaveFileName(self, self.tr('Choose File'), default_labelfile_name, self.tr('Label files (*%s)') % LabelFile.suffix)
        if isinstance(filename, tuple):
            filename, _ = filename
        return filename

    def _saveFile(self, filename):
        if filename and self.saveLabels(filename):
            self.addRecentFile(filename)
            self.setClean()

    def closeFile(self, _value=False):
        if not self.mayContinue():
            return
        self.resetState()
        self.setClean()
        self.toggleActions(False)
        self.canvas.setEnabled(False)
        self.actions.saveAs.setEnabled(False)
        self.fileListWidget.clear()
        self.uniqLabelList.clear()
        self.current_annotation_mode = ''
        self.right_click_menu()
        for option in self.vis_options:
            option.setEnabled(False)

    def getLabelFile(self):
        if self.filename.lower().endswith('.json'):
            label_file = self.filename
        else:
            label_file = osp.splitext(self.filename)[0] + '.json'
        return label_file

    def deleteFile(self):
        mb = QtWidgets.QMessageBox
        msg = self.tr('You are about to permanently delete this label file, proceed anyway?')
        answer = mb.warning(self, self.tr('Attention'), msg, mb.StandardButton.Yes | mb.StandardButton.No)
        if answer != mb.StandardButton.Yes:
            return
        label_file = self.getLabelFile()
        if osp.exists(label_file):
            os.remove(label_file)
            logger.info('Label file is removed: {}'.format(label_file))
            item = self.fileListWidget.currentItem()
            item.setCheckState(Qt.CheckState.Unchecked)
            self.resetState()

    def hasLabels(self):
        if self.noShapes():
            self.errorMessage('No objects labeled', 'You must label at least one object to save the file.')
            return False
        return True

    def hasLabelFile(self):
        if self.filename is None:
            return False
        label_file = self.getLabelFile()
        return osp.exists(label_file)

    def mayContinue(self):
        if not self.dirty:
            return True
        mb = QtWidgets.QMessageBox
        msg = self.tr('Save annotations to "{}" before closing?').format(self.filename)
        answer = mb.question(self, self.tr('Save annotations?'), msg, mb.StandardButton.Save | mb.StandardButton.Discard | mb.StandardButton.Cancel, mb.StandardButton.Save)
        if answer == mb.StandardButton.Discard:
            return True
        elif answer == mb.StandardButton.Save:
            self.saveFile()
            return True
        else:
            return False

    def errorMessage(self, title, message):
        msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical, title, message)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        return msg_box

    def currentPath(self):
        return osp.dirname(str(self.filename)) if self.filename else '.'

    def toggleKeepPrevMode(self):
        self._config['keep_prev'] = not self._config['keep_prev']

    def removeSelectedPoint(self):
        self.canvas.removeSelectedPoint()
        if not self.canvas.hShape.points:
            self.canvas.deleteShape(self.canvas.hShape)
            self.remLabels([self.canvas.hShape])
            self.setDirty()
            if self.noShapes():
                for action in self.actions.onShapesPresent:
                    action.setEnabled(False)

    def deleteSelectedShape(self):
        try:
            if len(self.canvas.selectedShapes) == 0:
                return
            yes, no = (QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
            msg = self.tr('You are about to permanently delete {} polygons, proceed anyway?').format(len(self.canvas.selectedShapes))
            if yes == QtWidgets.QMessageBox.warning(self, self.tr('Attention'), msg, yes | no, yes):
                deleted_shapes = self.canvas.deleteSelected()
                deleted_ids = [shape.group_id for shape in deleted_shapes]
                self.remLabels(deleted_shapes)
                self.setDirty()
                if self.noShapes():
                    for action in self.actions.onShapesPresent:
                        action.setEnabled(False)
                if self.current_annotation_mode == 'img' or self.current_annotation_mode == 'dir':
                    self.refresh_image_MODE()
                    return
                result, self.featuresOptions, fromFrameVAL, toFrameVAL = deleteSelectedShape_UI.PopUp(self.TOTAL_VIDEO_FRAMES, self.INDEX_OF_CURRENT_FRAME, self.featuresOptions)
                if result == QtWidgets.QDialog.DialogCode.Accepted:
                    for deleted_id in deleted_ids:
                        self.delete_ids_from_all_frames([deleted_id], from_frame=fromFrameVAL, to_frame=toFrameVAL)
                self.main_video_frames_slider_changed()
        except Exception as e:
            MsgBox.OKmsgBox(f'Error', f'Error: {e}', 'critical')

    def delete_ids_from_all_frames(self, deleted_ids, from_frame, to_frame):
        """
        Summary:
            Delete ids from a range of frames

        Args:
            deleted_ids (list): list of ids to be deleted
            from_frame (int): starting frame
            to_frame (int): ending frame
        """
        from_frame, to_frame = (np.min([from_frame, to_frame]), np.max([from_frame, to_frame]))
        listObj = self.load_objects_from_json__orjson()
        for i in range(from_frame - 1, to_frame, 1):
            frame_idx = listObj[i]['frame_idx']
            for object_ in listObj[i]['frame_data']:
                id = object_['tracker_id']
                if id in deleted_ids:
                    listObj[i]['frame_data'].remove(object_)
                    self.CURRENT_ANNOATAION_TRAJECTORIES['id_' + str(id)][frame_idx - 1] = (-1, -1)
                    self.rec_frame_for_id(id, frame_idx, type_='remove')
        self.load_objects_to_json__orjson(listObj)

    def copyShape(self):
        """
        Summary:
            Copy selected shape in right click menu.
            is NOT saved in the clipboard
        """
        if len(self.canvas.selectedShapes) > 1 and self.current_annotation_mode == 'video':
            org = copy.deepcopy(self.canvas.shapes)
            self.canvas.endMove(copy=True)
            self.canvas.undoLastLine()
            self.canvas.shapesBackups.pop()
            self.canvas.shapes = org
            self.update_current_frame_annotation_button_clicked()
            return
        elif self.current_annotation_mode == 'video':
            self.canvas.endMove(copy=True)
            shape = self.canvas.selectedShapes[0]
            text = shape.label
            text, flags, group_id, content = self.labelDialog.popUp(text)
            shape.group_id = -1
            shape.content = content
            shape.label = text
            shape.flags = flags
            group_id, text = getIDfromUser_UI.PopUp(self, group_id, text)
            if text:
                self.labelList.clearSelection()
                shape = self.canvas.setLastLabel(text, flags)
                shape.group_id = group_id
                self.addLabel(shape)
                self.rec_frame_for_id(shape.group_id, self.INDEX_OF_CURRENT_FRAME)
                self.actions.editMode.setEnabled(True)
                self.actions.undoLastPoint.setEnabled(False)
                self.actions.undo.setEnabled(True)
                self.setDirty()
            else:
                self.canvas.undoLastLine()
                self.canvas.shapesBackups.pop()
            self.update_current_frame_annotation_button_clicked()
            return
        self.canvas.endMove(copy=True)
        for shape in self.canvas.selectedShapes:
            self.addLabel(shape)
        self.labelList.clearSelection()
        self.setDirty()

    def moveShape(self):
        self.canvas.endMove(copy=False)
        self.setDirty()
        if self.current_annotation_mode == 'video':
            self.update_current_frame_annotation_button_clicked()

    def openDirDialog(self, _value=False, dirpath=None):
        if not self.mayContinue():
            return
        defaultOpenDirPath = dirpath if dirpath else '.'
        if self.lastOpenDir and osp.exists(self.lastOpenDir):
            defaultOpenDirPath = self.lastOpenDir
        else:
            defaultOpenDirPath = osp.dirname(self.filename) if self.filename else '.'
        targetDirPath = str(QtWidgets.QFileDialog.getExistingDirectory(self, self.tr('%s - Open Directory') % __appname__, defaultOpenDirPath, QtWidgets.QFileDialog.Option.ShowDirsOnly | QtWidgets.QFileDialog.Option.DontResolveSymlinks))
        self.target_directory = targetDirPath
        self.importDirImages(targetDirPath)
        self.set_video_controls_visibility(False)
        for option in self.vis_options:
            if option in [self.id_checkBox, self.traj_checkBox, self.trajectory_length_lineEdit]:
                option.setEnabled(False)
            else:
                option.setEnabled(True)

    @property
    def imageList(self):
        lst = []
        for i in range(self.fileListWidget.count()):
            item = self.fileListWidget.item(i)
            lst.append(item.text())
        return lst

    def importDroppedImageFiles(self, imageFiles):
        extensions = ['.%s' % fmt.data().decode().lower() for fmt in QtGui.QImageReader.supportedImageFormats()]
        self.filename = None
        for file in imageFiles:
            if file in self.imageList or not file.lower().endswith(tuple(extensions)):
                continue
            label_file = osp.splitext(file)[0] + '.json'
            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            item = QtWidgets.QListWidgetItem(file)
            if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(label_file):
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.fileListWidget.addItem(item)
            self.openNextImg()

    def importDirImages(self, dirpath, pattern=None, load=True):
        self.actions.export.setEnabled(True)
        if not self.mayContinue() or not dirpath:
            return
        self.reset_for_new_mode('dir')
        self.lastOpenDir = dirpath
        self.filename = None
        self.fileListWidget.clear()
        self.uniqLabelList.clear()
        for filename in self.scanAllImages(dirpath):
            if pattern and pattern not in filename:
                continue
            label_file = osp.splitext(filename)[0] + '.json'
            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            item = QtWidgets.QListWidgetItem(filename)
            if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(label_file):
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.fileListWidget.addItem(item)
        self.openNextImg(load=load)
        self.fileListWidget.horizontalScrollBar().setValue(self.fileListWidget.horizontalScrollBar().maximum())

    def scanAllImages(self, folderPath):
        extensions = ['.%s' % fmt.data().decode().lower() for fmt in QtGui.QImageReader.supportedImageFormats()]
        images = []
        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relativePath = osp.join(root, file)
                    images.append(relativePath)
        images.sort(key=lambda x: x.lower())
        return images

    def refresh_image_MODE(self, fromSignal=False):
        try:
            if self.current_annotation_mode == 'video' and (not fromSignal):
                return
            self.CURRENT_SHAPES_IN_IMG = mathOps.convert_qt_shapes_to_shapes(self.canvas.shapes)
            imageX = visualizations.draw_bb_on_image_MODE(self.CURRENT_ANNOATAION_FLAGS, self.image, self.CURRENT_SHAPES_IN_IMG)
            self.labelList.clear()
            self.canvas.loadPixmap(QtGui.QPixmap.fromImage(imageX))
            self.loadLabels(self.CURRENT_SHAPES_IN_IMG)
        except:
            pass

    def annotate_one(self, called_from_tracking=False):
        areaFlag = len(self.canvas.tracking_area_polygon) > 2
        if areaFlag:
            dims = self.CURRENT_FRAME_IMAGE.shape
            area_points = self.canvas.tracking_area_polygon
            [x1, y1, x2, y2] = mathOps.track_area_adjustedBboex(area_points, dims, ratio=0.1)
            targetImage = self.CURRENT_FRAME_IMAGE[y1:y2, x1:x2]
        else:
            targetImage = self.CURRENT_FRAME_IMAGE
        try:
            if self.current_annotation_mode != 'video':
                if os.path.exists(self.filename):
                    self.labelList.clearSelection()
            if self.multi_model_flag:
                shapes = self.intelligenceHelper.get_shapes_of_one(targetImage, img_array_flag=True, multi_model_flag=True)
            else:
                shapes = self.intelligenceHelper.get_shapes_of_one(targetImage, img_array_flag=True)
            if areaFlag:
                shapes = mathOps.adjust_shapes_to_original_image(shapes, x1, y1, area_points)
            if self.current_annotation_mode == 'video' and called_from_tracking:
                return shapes
        except Exception as e:
            MsgBox.OKmsgBox('Error', f'{e}', 'critical')
            return
        imageX = visualizations.draw_bb_on_image_MODE(self.CURRENT_ANNOATAION_FLAGS, self.image, shapes)
        self.labelList.clear()
        self.CURRENT_SHAPES_IN_IMG = shapes
        self.canvas.loadPixmap(QtGui.QPixmap.fromImage(imageX))
        self.loadLabels(self.CURRENT_SHAPES_IN_IMG)
        self.actions.editMode.setEnabled(True)
        self.actions.undoLastPoint.setEnabled(False)
        self.actions.undo.setEnabled(True)
        self.setDirty()

    def annotate_batch(self):
        images = []
        self._config = get_config()
        notif = [self._config['mute'], self, notification.PopUp]
        for filename in self.imageList:
            images.append(filename)
        if self.multi_model_flag:
            self.intelligenceHelper.get_shapes_of_batch(images, multi_model_flag=True, notif=notif)
        else:
            self.intelligenceHelper.get_shapes_of_batch(images, notif=notif)

    def setConfThreshold(self):
        if self.intelligenceHelper.conf_threshold:
            self.intelligenceHelper.conf_threshold = self.segmentation_options_UI.setConfThreshold(self.intelligenceHelper.conf_threshold)
        else:
            self.intelligenceHelper.conf_threshold = self.segmentation_options_UI.setConfThreshold()

    def setIOUThreshold(self):
        if self.intelligenceHelper.iou_threshold:
            self.intelligenceHelper.iou_threshold = self.segmentation_options_UI.setIOUThreshold(self.intelligenceHelper.iou_threshold)
        else:
            self.intelligenceHelper.iou_threshold = self.segmentation_options_UI.setIOUThreshold()

    def selectClasses(self):
        print(' from intelligenceHelper:' + str(self.intelligenceHelper.selectedclasses))
        self.intelligenceHelper.selectedclasses = self.segmentation_options_UI.selectClasses()

    def mergeSegModels(self):
        print(' from intelligenceHelper:' + str(self.intelligenceHelper.selectedmodels))
        self.intelligenceHelper.selectedmodels = self.merge_feature_UI.mergeSegModels()
        if len(self.intelligenceHelper.selectedmodels) == 0:
            print('No models selected')
        else:
            self.multi_model_flag = True

    def Segment_anything(self):
        if self.sam_toolbar.isVisible():
            self.set_sam_toolbar_visibility(False)
        else:
            self.set_sam_toolbar_visibility(True)

    def calculate_trajectories(self, frames=None):
        """
        Summary:
            Calculate trajectories for all objects in the video

        Args:
            frames (list): list of frames to calculate trajectories for (default: None -> all frames)
        """
        listObj = self.load_objects_from_json__orjson()
        if len(listObj) == 0:
            return
        frames = frames if frames else range(len(listObj))
        for i in frames:
            listobjframe = listObj[i]['frame_idx']
            for object in listObj[i]['frame_data']:
                id = object['tracker_id']
                self.minID = min(self.minID, id - 1)
                self.rec_frame_for_id(id, listobjframe)
                label = object['class_name']
                label_ascii = sum([ord(c) for c in label])
                idx = label_ascii % len(color_palette)
                color = color_palette[idx]
                center = mathOps.centerOFmass(object['segment'])
                try:
                    centers_rec = self.CURRENT_ANNOATAION_TRAJECTORIES['id_' + str(id)]
                    try:
                        xp, yp = centers_rec[listobjframe - 2]
                        xn, yn = center
                        if xp == -1 or xn == -1:
                            c = 5 / 0
                        r = 0.5
                        x = r * xn + (1 - r) * xp
                        y = r * yn + (1 - r) * yp
                        center = (int(x), int(y))
                    except:
                        pass
                    centers_rec[listobjframe - 1] = center
                    self.CURRENT_ANNOATAION_TRAJECTORIES['id_' + str(id)] = centers_rec
                    self.CURRENT_ANNOATAION_TRAJECTORIES['id_color_' + str(id)] = color
                except:
                    centers_rec = [(-1, -1)] * int(self.TOTAL_VIDEO_FRAMES)
                    centers_rec[listobjframe - 1] = center
                    self.CURRENT_ANNOATAION_TRAJECTORIES['id_' + str(id)] = centers_rec
                    self.CURRENT_ANNOATAION_TRAJECTORIES['id_color_' + str(id)] = color

    def right_click_menu(self):
        """
        Summary:
            Set the right click menu according to the current annotation mode
        """
        self.set_sam_toolbar_enable(False)
        self.sam_model_comboBox.setCurrentIndex(0)
        self.sam_buttons_colors('x')
        mode = self.current_annotation_mode
        video_menu_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 14, 15, 16, 17]
        image_menu_list = [0, 1, 2, 3, 10, 11, 12, 13, 14, 15]
        if self.current_annotation_mode == 'video':
            self.canvas.menus[0].clear()
            utils.addActions(self.canvas.menus[0], (self.actions.menu[i] for i in video_menu_list))
            self.menus.edit.clear()
            utils.addActions(self.menus.edit, (self.actions.menu[i] for i in video_menu_list))
        else:
            self.canvas.menus[0].clear()
            utils.addActions(self.canvas.menus[0], (self.actions.menu[i] for i in image_menu_list))
            self.menus.edit.clear()
            utils.addActions(self.menus.edit, (self.actions.menu[i] for i in image_menu_list))

    def reset_for_new_mode(self, mode):
        self.CURRENT_ANNOATAION_TRAJECTORIES = {'length': 30, 'alpha': 0.7}
        self.key_frames.clear()
        self.id_frames_rec.clear()
        for shape in self.canvas.shapes:
            self.canvas.deleteShape(shape)
        self.resetState()
        self.CURRENT_SHAPES_IN_IMG = []
        self.image = QtGui.QImage()
        self.CURRENT_FRAME_IMAGE = None
        self.current_annotation_mode = mode
        self.canvas.current_annotation_mode = mode
        self.right_click_menu()
        self.global_listObj = []
        self.minID = -2
        self.maxID = 0

    def openVideo(self):
        try:
            cv2.destroyWindow('video processing')
        except:
            pass
        if not self.mayContinue():
            return
        videoFile = QtWidgets.QFileDialog.getOpenFileName(self, self.tr('%s - Open Video') % __appname__, '.', self.tr('Video files (*.mp4 *.avi *.mov)'))
        if videoFile[0]:
            self.fileListWidget.clear()
            self.uniqLabelList.clear()
            self.reset_for_new_mode('video')
            self.CURRENT_VIDEO_NAME = videoFile[0].split('.')[-2].split('/')[-1]
            self.CURRENT_VIDEO_PATH = '/'.join(videoFile[0].split('.')[-2].split('/')[:-1])
            json_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}_tracking_results.json'
            if os.path.exists(json_file_name):
                self.actions.export.setEnabled(True)
            else:
                self.actions.export.setEnabled(False)
            cap = cv2.VideoCapture(videoFile[0])
            self.CURRENT_VIDEO_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.CURRENT_VIDEO_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.CAP = cap
            self.TOTAL_VIDEO_FRAMES = int(self.CAP.get(cv2.CAP_PROP_FRAME_COUNT))
            self.CURRENT_VIDEO_FPS = self.CAP.get(cv2.CAP_PROP_FPS)
            self.main_video_frames_slider.setMaximum(self.TOTAL_VIDEO_FRAMES)
            self.frames_to_track_slider.setMaximum(self.TOTAL_VIDEO_FRAMES - self.INDEX_OF_CURRENT_FRAME)
            self.main_video_frames_slider.setValue(2)
            self.INDEX_OF_CURRENT_FRAME = 1
            self.main_video_frames_slider.setValue(self.INDEX_OF_CURRENT_FRAME)
            self.set_video_controls_visibility(True)
            self.update_tracking_method()
            self.calculate_trajectories()
            keys = list(self.id_frames_rec.keys())
            idsORG = [int(keys[i][3:]) for i in range(len(keys))]
            if len(idsORG) > 0:
                self.maxID = max(idsORG)
            for option in self.vis_options:
                option.setEnabled(True)
        self.actions.save.setEnabled(False)
        self.actions.saveAs.setEnabled(False)

    def openVideoFrames(self):
        try:
            video_frame_extractor_dialog = utils.VideoFrameExtractor(self._config['mute'], notification.PopUp)
            video_frame_extractor_dialog.exec()
            dir_path_name = video_frame_extractor_dialog.path_name
            if dir_path_name:
                self.target_directory = dir_path_name
                self.importDirImages(dir_path_name)
                self.set_video_controls_visibility(False)
                for option in self.vis_options:
                    if option in [self.id_checkBox, self.traj_checkBox, self.trajectory_length_lineEdit]:
                        option.setEnabled(False)
                    else:
                        option.setEnabled(True)
        except Exception as e:
            MsgBox.OKmsgBox('Error', f'Error: {e}', 'critical')

    def load_shapes_for_video_frame(self, json_file_name, index):
        target_frame_idx = index
        listObj = self.load_objects_from_json__orjson()
        listObj = np.array(listObj)
        shapes = []
        i = target_frame_idx - 1
        frame_objects = listObj[i]['frame_data']
        for object_ in frame_objects:
            shape = {}
            shape['label'] = object_['class_name']
            shape['group_id'] = object_['tracker_id']
            shape['content'] = object_['confidence']
            shape['bbox'] = object_['bbox']
            points = object_['segment']
            points = np.array(points, np.int16).flatten().tolist()
            shape['points'] = points
            shape['shape_type'] = 'polygon'
            shape['other_data'] = {}
            shape['flags'] = {}
            shapes.append(shape)
        self.CURRENT_SHAPES_IN_IMG = shapes

    def loadFramefromVideo(self, frame_array, index=1):
        self.resetState()
        self.canvas.setEnabled(False)
        self.imageData = frame_array.data
        self.CURRENT_FRAME_IMAGE = frame_array
        image = QtGui.QImage(self.imageData, self.imageData.shape[1], self.imageData.shape[0], QtGui.QImage.Format.Format_BGR888)
        self.image = image
        if self._config['keep_prev']:
            prev_shapes = self.canvas.shapes
        flags = {k: False for k in self._config['flags'] or []}
        self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
        if self.TrackingMode:
            image = self.draw_bb_on_image(image, self.CURRENT_SHAPES_IN_IMG)
            self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
            if len(self.CURRENT_SHAPES_IN_IMG) > 0:
                self.loadLabels(self.CURRENT_SHAPES_IN_IMG)
        elif self.labelFile:
            self.CURRENT_SHAPES_IN_IMG = self.labelFile.shapes
            image = self.draw_bb_on_image(image, self.CURRENT_SHAPES_IN_IMG)
            self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
            self.loadLabels(self.labelFile.shapes)
            if self.labelFile.flags is not None:
                flags.update(self.labelFile.flags)
        else:
            json_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}_tracking_results.json'
            if os.path.exists(json_file_name):
                self.load_shapes_for_video_frame(json_file_name, index)
                image = self.draw_bb_on_image(image, self.CURRENT_SHAPES_IN_IMG)
                self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
                if len(self.CURRENT_SHAPES_IN_IMG) > 0:
                    self.loadLabels(self.CURRENT_SHAPES_IN_IMG)
        self.loadFlags(flags)
        self.setClean()
        self.canvas.setEnabled(True)
        is_initial_load = not self.zoom_values
        if self.filename in self.zoom_values:
            self.zoomMode = self.zoom_values[self.filename][0]
            self.setZoom(self.zoom_values[self.filename][1])
        elif is_initial_load or not self._config['keep_prev_scale']:
            self.adjustScale(initial=True)
        self.paintCanvas()
        self.toggleActions(True)
        self.canvas.setFocus()
        self.status(self.tr(f'Loaded {self.CURRENT_VIDEO_NAME} frame {self.INDEX_OF_CURRENT_FRAME}'))

    def nextFrame_buttonClicked(self):
        self.update_current_frame_annotation_button_clicked()
        new_value = self.INDEX_OF_CURRENT_FRAME + self.FRAMES_TO_SKIP
        if new_value >= self.TOTAL_VIDEO_FRAMES:
            new_value = self.TOTAL_VIDEO_FRAMES
        self.main_video_frames_slider.setValue(new_value)

    def next_1_Frame_buttonClicked(self):
        self.update_current_frame_annotation_button_clicked()
        new_value = self.INDEX_OF_CURRENT_FRAME + 1
        if new_value >= self.TOTAL_VIDEO_FRAMES:
            new_value = self.TOTAL_VIDEO_FRAMES
        self.main_video_frames_slider.setValue(new_value)

    def previousFrame_buttonClicked(self):
        self.update_current_frame_annotation_button_clicked()
        new_value = self.INDEX_OF_CURRENT_FRAME - self.FRAMES_TO_SKIP
        if new_value <= 0:
            new_value = 0
        self.main_video_frames_slider.setValue(new_value)

    def previous_1_Frame_buttonclicked(self):
        self.update_current_frame_annotation_button_clicked()
        new_value = self.INDEX_OF_CURRENT_FRAME - 1
        if new_value <= 0:
            new_value = 0
        self.main_video_frames_slider.setValue(new_value)

    def frames_to_skip_slider_changed(self):
        self.FRAMES_TO_SKIP = self.frames_to_skip_slider.value()
        zeros = (2 - int(np.log10(self.FRAMES_TO_SKIP + 0.9))) * '0'
        self.frames_to_skip_label.setText('Jump forward/backward frames: ' + zeros + str(self.FRAMES_TO_SKIP))

    def playPauseButtonClicked(self):
        if self.playPauseButton_mode == 'Play':
            self.playPauseButton_mode = 'Pause'
            self.playPauseButton.setShortcut(self._config['shortcuts']['play'])
            self.playPauseButton.setToolTip(f'Play ({self._config['shortcuts']['play']})')
            self.playPauseButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPause))
            self.play_timer = QtCore.QTimer(self)
            self.play_timer.timeout.connect(self.move_frame_by_frame)
            self.play_timer.start(40)
        elif self.playPauseButton_mode == 'Pause':
            self.play_timer.stop()
            self.playPauseButton_mode = 'Play'
            self.playPauseButton.setShortcut(self._config['shortcuts']['play'])
            self.playPauseButton.setToolTip(f'Pause ({self._config['shortcuts']['play']})')
            self.playPauseButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))

    def move_frame_by_frame(self):
        QtWidgets.QApplication.processEvents()
        self.main_video_frames_slider.setValue(self.INDEX_OF_CURRENT_FRAME + 1)

    def main_video_frames_slider_changed(self):
        if self.current_annotation_mode != 'video':
            return
        if self.sam_model_comboBox.currentIndex() != 0 and self.canvas.SAM_mode != 'finished' and (not self.TrackingMode):
            self.sam_clear_annotation_button_clicked()
            self.sam_buttons_colors('X')
        try:
            x = self.CURRENT_VIDEO_PATH
        except:
            return
        frame_idx = self.main_video_frames_slider.value()
        self.INDEX_OF_CURRENT_FRAME = frame_idx
        self.CAP.set(cv2.CAP_PROP_POS_FRAMES, frame_idx - 1)
        fps = self.CAP.get(cv2.CAP_PROP_FPS)
        zeros = (int(np.log10(self.TOTAL_VIDEO_FRAMES + 0.9)) - int(np.log10(frame_idx + 0.9))) * '0'
        self.main_video_frames_label_1.setText(f'frame {zeros}{frame_idx} / {int(self.TOTAL_VIDEO_FRAMES)}')
        self.frame_time = mathOps.mapFrameToTime(frame_idx, fps)
        frame_text = '%02d:%02d:%02d:%03d' % (self.frame_time[0], self.frame_time[1], self.frame_time[2], self.frame_time[3])
        video_duration = mathOps.mapFrameToTime(self.TOTAL_VIDEO_FRAMES, fps)
        video_duration_text = '%02d:%02d:%02d:%03d' % (video_duration[0], video_duration[1], video_duration[2], video_duration[3])
        final_text = frame_text + ' / ' + video_duration_text
        self.main_video_frames_label_2.setText(f'time {final_text}')
        success, img = self.CAP.read()
        if success:
            frame_array = np.array(img)
            self.loadFramefromVideo(frame_array, frame_idx)
        else:
            pass
        self.frames_to_track_slider.setMaximum(self.TOTAL_VIDEO_FRAMES - self.INDEX_OF_CURRENT_FRAME)

    def frames_to_track_input_changed(self, text):
        try:
            value = int(text)
            if 2 <= value <= self.frames_to_track_slider.maximum():
                self.frames_to_track_slider.setValue(value)
            elif value > self.frames_to_track_slider.maximum():
                self.frames_to_track_slider.setValue(self.frames_to_track_slider.maximum())
            elif value < 2:
                self.frames_to_track_slider.setValue(1)
        except ValueError:
            pass

    def frames_to_track_slider_changed(self, value):
        self.frames_to_track_input.setText(str(value))
        self.FRAMES_TO_TRACK = self.frames_to_track_slider.value()

    def track_assigned_objects_button_clicked(self):
        if len(self.labelList.selectedItems()) == 0:
            self.errorMessage('found No objects to track', 'you need to assign at least one object to track')
            return
        self.TRACK_ASSIGNED_OBJECTS_ONLY = True
        self.track_buttonClicked()
        self.TRACK_ASSIGNED_OBJECTS_ONLY = False

    def update_gui_after_tracking(self, index):
        if index != self.FRAMES_TO_TRACK - 1:
            self.main_video_frames_slider.setValue(self.INDEX_OF_CURRENT_FRAME + 1)
        QtWidgets.QApplication.processEvents()

    def certain_area_clicked(self, index):
        self.canvas.cancelManualDrawing()
        self.setEditMode()
        self.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))
        if index == 0:
            self.canvas.tracking_area = ''
            self.canvas.tracking_area_polygon = []
        else:
            self.canvas.tracking_area = 'drawing'
            self.canvas.tracking_area_polygon = []

    def track_dropdown_changed(self, index):
        self.selected_option = index

    def start_tracking_button_clicked(self):
        try:
            try:
                if self.selected_option == 0:
                    self.track_buttonClicked()
                elif self.selected_option == 1:
                    self.track_assigned_objects_button_clicked()
                elif self.selected_option == 2:
                    self.track_full_video_button_clicked()
            except Exception as e:
                self.track_buttonClicked()
        except Exception as e:
            MsgBox.OKmsgBox('Error', f'Error: {e}', 'critical')

    def track_buttonClicked(self):
        self.actions.export.setEnabled(False)
        self.tracking_progress_bar.setVisible(True)
        listObj = self.load_objects_from_json__orjson()
        existing_annotation = False
        shapes = self.canvas.shapes
        tracks_to_follow = None
        if len(shapes) > 0:
            existing_annotation = True
            tracks_to_follow = []
            for shape in shapes:
                if shape.group_id != None:
                    tracks_to_follow.append(int(shape.group_id))
        self.TrackingMode = True
        curr_frame, prev_frame = (None, None)
        if self.FRAMES_TO_TRACK + self.INDEX_OF_CURRENT_FRAME <= self.TOTAL_VIDEO_FRAMES:
            number_of_frames_to_track = self.FRAMES_TO_TRACK
        else:
            number_of_frames_to_track = self.TOTAL_VIDEO_FRAMES - self.INDEX_OF_CURRENT_FRAME
        self.interrupted = False
        for i in range(number_of_frames_to_track):
            QtWidgets.QApplication.processEvents()
            if self.interrupted:
                self.interrupted = False
                break
            if i % 100 == 0:
                self.load_objects_to_json__orjson(listObj)
            self.tracking_progress_bar.setValue(int((i + 1) / number_of_frames_to_track * 100))
            if existing_annotation:
                existing_annotation = False
                shapes = self.canvas.shapes
                shapes = mathOps.convert_qt_shapes_to_shapes(shapes)
            else:
                with torch.no_grad():
                    shapes = self.annotate_one(called_from_tracking=True)
            curr_frame = self.CURRENT_FRAME_IMAGE
            if len(shapes) == 0:
                self.update_gui_after_tracking(i)
                continue
            for shape in shapes:
                if shape['content'] is None:
                    shape['content'] = 1.0
            boxes, confidences, class_ids, segments = mathOps.get_boxes_conf_classids_segments(shapes)
            boxes = np.array(boxes, dtype=int)
            confidences = np.array(confidences)
            class_ids = np.array(class_ids)
            detections = Detections(xyxy=boxes, confidence=confidences, class_id=class_ids)
            boxes = torch.from_numpy(detections.xyxy)
            confidences = torch.from_numpy(detections.confidence)
            class_ids = torch.from_numpy(detections.class_id)
            dets = torch.cat((boxes, confidences.unsqueeze(1), class_ids.unsqueeze(1)), dim=1)
            dets = dets.to(torch.float32)
            if hasattr(self.tracker, 'tracker') and hasattr(self.tracker.tracker, 'camera_update'):
                if prev_frame is not None and curr_frame is not None:
                    self.tracker.tracker.camera_update(prev_frame, curr_frame)
            prev_frame = curr_frame
            with torch.no_grad():
                org_tracks = self.tracker.update(dets.cpu(), self.CURRENT_FRAME_IMAGE)
            tracks = []
            for org_track in org_tracks:
                track = []
                for i in range(6):
                    track.append(int(org_track[i]))
                track[4] += int(self.maxID)
                track.append(org_track[6])
                tracks.append(track)
            matched_shapes, unmatched_shapes = mathOps.match_detections_with_tracks(shapes, tracks)
            shapes = matched_shapes
            self.CURRENT_SHAPES_IN_IMG = [shape_ for shape_ in shapes if shape_['group_id'] is not None]
            if self.TRACK_ASSIGNED_OBJECTS_ONLY and tracks_to_follow is not None:
                try:
                    if len(self.labelList.selectedItems()) != 0:
                        tracks_to_follow = []
                        for item in self.labelList.selectedItems():
                            x = item.text()
                            i1, i2 = (x.find('D'), x.find(':'))
                            tracks_to_follow.append(int(x[i1 + 2:i2]))
                    self.CURRENT_SHAPES_IN_IMG = [shape_ for shape_ in shapes if shape_['group_id'] in tracks_to_follow]
                except:
                    self.errorMessage('Error', 'Please use the tracker on the image first so that you can select labels with IDs to track')
                    return
            json_frame = {}
            json_frame.update({'frame_idx': self.INDEX_OF_CURRENT_FRAME})
            json_frame_object_list = []
            for shape in self.CURRENT_SHAPES_IN_IMG:
                self.rec_frame_for_id(int(shape['group_id']), self.INDEX_OF_CURRENT_FRAME, type_='add')
                json_tracked_object = {}
                json_tracked_object['tracker_id'] = int(shape['group_id'])
                json_tracked_object['bbox'] = [int(i) for i in shape['bbox']]
                json_tracked_object['confidence'] = shape['content']
                json_tracked_object['class_name'] = shape['label']
                json_tracked_object['class_id'] = coco_classes.index(shape['label']) if shape['label'] in coco_classes else -1
                points = shape['points']
                segment = [[int(points[z]), int(points[z + 1])] for z in range(0, len(points), 2)]
                json_tracked_object['segment'] = segment
                json_frame_object_list.append(json_tracked_object)
            json_frame.update({'frame_data': json_frame_object_list})
            listObj[self.INDEX_OF_CURRENT_FRAME - 1] = json_frame
            QtWidgets.QApplication.processEvents()
            self.update_gui_after_tracking(i)
            print('finished tracking for frame ', self.INDEX_OF_CURRENT_FRAME)
        self.load_objects_to_json__orjson(listObj)
        self._config = get_config()
        if not self._config['mute']:
            if not self.isActiveWindow():
                notification.PopUp('Tracking Completed')
        self.TrackingMode = False
        self.labelFile = None
        self.main_video_frames_slider.setValue(self.INDEX_OF_CURRENT_FRAME - 1)
        self.main_video_frames_slider.setValue(self.INDEX_OF_CURRENT_FRAME)
        self.tracking_progress_bar.hide()
        self.tracking_progress_bar.setValue(0)
        self.actions.export.setEnabled(True)

    def track_full_video_button_clicked(self):
        self.FRAMES_TO_TRACK = int(self.TOTAL_VIDEO_FRAMES - self.INDEX_OF_CURRENT_FRAME)
        self.track_buttonClicked()

    def set_video_controls_visibility(self, visible=False):
        self.videoControls.setVisible(visible)
        for widget in self.videoControls.children():
            try:
                widget.setVisible(visible)
            except:
                pass
        self.videoControls_2.setVisible(visible)
        for widget in self.videoControls_2.children():
            try:
                widget.setVisible(visible)
            except:
                pass

    def traj_checkBox_changed(self):
        try:
            self.CURRENT_ANNOATAION_FLAGS['traj'] = self.traj_checkBox.isChecked()
            self.update_current_frame_annotation()
            self.main_video_frames_slider_changed()
        except:
            pass

    def mask_checkBox_changed(self):
        try:
            self.CURRENT_ANNOATAION_FLAGS['mask'] = self.mask_checkBox.isChecked()
            self.update_current_frame_annotation()
            self.main_video_frames_slider_changed()
        except:
            pass
        self.refresh_image_MODE()

    def class_checkBox_changed(self):
        try:
            self.CURRENT_ANNOATAION_FLAGS['class'] = self.class_checkBox.isChecked()
            self.update_current_frame_annotation()
            self.main_video_frames_slider_changed()
        except:
            pass
        self.refresh_image_MODE()

    def conf_checkBox_changed(self):
        try:
            self.CURRENT_ANNOATAION_FLAGS['conf'] = self.conf_checkBox.isChecked()
            self.update_current_frame_annotation()
            self.main_video_frames_slider_changed()
        except:
            pass
        self.refresh_image_MODE()

    def id_checkBox_changed(self):
        try:
            self.CURRENT_ANNOATAION_FLAGS['id'] = self.id_checkBox.isChecked()
            self.update_current_frame_annotation()
            self.main_video_frames_slider_changed()
        except:
            pass

    def bbox_checkBox_changed(self):
        try:
            self.CURRENT_ANNOATAION_FLAGS['bbox'] = self.bbox_checkBox.isChecked()
            self.update_current_frame_annotation()
            self.main_video_frames_slider_changed()
        except:
            pass
        self.refresh_image_MODE()

    def polygons_visable_checkBox_changed(self):
        try:
            self.CURRENT_ANNOATAION_FLAGS['polygons'] = self.polygons_visable_checkBox.isChecked()
            self.update_current_frame_annotation()
            for shape in self.canvas.shapes:
                self.canvas.setShapeVisible(shape, self.CURRENT_ANNOATAION_FLAGS['polygons'])
        except:
            pass

    def export_as_video_button_clicked(self, output_filename=None):
        self.update_current_frame_annotation()
        input_video_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}.mp4'
        output_video_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}_tracking_results.mp4'
        if output_filename is not False:
            output_video_file_name = output_filename
        input_cap = cv2.VideoCapture(input_video_file_name)
        output_cap = cv2.VideoWriter(output_video_file_name, cv2.VideoWriter_fourcc(*'mp4v'), int(self.CURRENT_VIDEO_FPS), (int(self.CURRENT_VIDEO_WIDTH), int(self.CURRENT_VIDEO_HEIGHT)))
        listObj = self.load_objects_from_json__orjson()
        empty_frame = False
        empty_video = True
        for target_frame_idx in range(self.TOTAL_VIDEO_FRAMES):
            try:
                self.INDEX_OF_CURRENT_FRAME = target_frame_idx + 1
                ret, image = input_cap.read()
                shapes = []
                frame_objects = listObj[target_frame_idx]['frame_data']
                for object_ in frame_objects:
                    shape = {}
                    shape['label'] = object_['class_name']
                    shape['group_id'] = str(object_['tracker_id'])
                    shape['content'] = str(object_['confidence'])
                    shape['bbox'] = object_['bbox']
                    points = object_['segment']
                    points = np.array(points, np.int16).flatten().tolist()
                    shape['points'] = points
                    shape['shape_type'] = 'polygon'
                    shape['other_data'] = {}
                    shape['flags'] = {}
                    shapes.append(shape)
                if len(shapes) == 0:
                    if not empty_frame:
                        self.waitWindow(visible=True, text=f'Processing...')
                        empty_frame = True
                    continue
                self.waitWindow(visible=True, text=f'Please Wait.\nFrame {target_frame_idx} is being exported...')
                image = self.draw_bb_on_image(image, shapes, image_qt_flag=False)
                output_cap.write(image)
                empty_frame = False
                empty_video = False
            except:
                input_cap.release()
                output_cap.release()
        input_cap.release()
        output_cap.release()
        self.waitWindow()
        try:
            if empty_video:
                os.remove(output_video_file_name)
                return False
        except:
            pass
        self.INDEX_OF_CURRENT_FRAME = self.main_video_frames_slider.value()
        if output_filename is False:
            MsgBox.OKmsgBox('Export Video', 'Done Exporting Video')
        if output_filename is not False:
            return output_filename

    def clear_video_annotations_button_clicked(self):
        self.global_listObj = []
        self.CURRENT_ANNOATAION_TRAJECTORIES = {'length': 30, 'alpha': 0.7}
        self.key_frames.clear()
        self.id_frames_rec.clear()
        self.minID = -2
        self.maxID = 0
        for shape in self.canvas.shapes:
            self.canvas.deleteShape(shape)
        self.CURRENT_SHAPES_IN_IMG = []
        json_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}_tracking_results.json'
        if os.path.exists(json_file_name):
            os.remove(json_file_name)
        MsgBox.OKmsgBox('clear annotations', 'All video frames annotations are cleared')
        self.main_video_frames_slider.setValue(2)
        self.main_video_frames_slider.setValue(1)

    def update_current_frame_annotation_button_clicked(self):
        if self.sam_model_comboBox.currentIndex() != 0 and self.canvas.SAM_mode != 'finished' and (not self.TrackingMode):
            self.sam_clear_annotation_button_clicked()
        try:
            x = self.CURRENT_VIDEO_PATH
        except:
            return
        self.update_current_frame_annotation()
        self.main_video_frames_slider_changed()

    def update_current_frame_annotation(self):
        if self.current_annotation_mode != 'video':
            return
        listObj = self.load_objects_from_json__orjson()
        json_frame = {}
        json_frame.update({'frame_idx': self.INDEX_OF_CURRENT_FRAME})
        json_frame_object_list = []
        shapes = mathOps.convert_qt_shapes_to_shapes(self.canvas.shapes)
        for shape in shapes:
            json_tracked_object = {}
            if shape['group_id'] != None:
                json_tracked_object['tracker_id'] = int(shape['group_id'])
            else:
                json_tracked_object['tracker_id'] = self.minID
                self.minID -= 1
            bbox = shape['bbox']
            bbox = [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])]
            json_tracked_object['bbox'] = bbox
            json_tracked_object['confidence'] = str(shape['content'] if shape['content'] != None else 1)
            json_tracked_object['class_name'] = shape['label']
            json_tracked_object['class_id'] = coco_classes.index(shape['label']) if shape['label'] in coco_classes else -1
            points = shape['points']
            segment = [[int(points[z]), int(points[z + 1])] for z in range(0, len(points), 2)]
            json_tracked_object['segment'] = segment
            json_frame_object_list.append(json_tracked_object)
        json_frame.update({'frame_data': json_frame_object_list})
        listObj[self.INDEX_OF_CURRENT_FRAME - 1] = json_frame
        self.load_objects_to_json__orjson(listObj)
        print('saved frame annotation')

    def trajectory_length_lineEdit_changed(self):
        try:
            text = self.trajectory_length_lineEdit.text()
            self.CURRENT_ANNOATAION_TRAJECTORIES['length'] = int(text) if text != '' else 1
            self.main_video_frames_slider_changed()
        except:
            pass

    def addVideoControls(self):
        self.videoControls = QtWidgets.QToolBar()
        self.videoControls.setMovable(True)
        self.videoControls.setFloatable(True)
        self.videoControls.setObjectName('videoControls')
        self.videoControls.setStyleSheet('QToolBar#videoControls { border: 50px }')
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.videoControls)
        self.videoControls_2 = QtWidgets.QToolBar()
        self.videoControls_2.setMovable(True)
        self.videoControls_2.setFloatable(True)
        self.videoControls_2.setObjectName('videoControls_2')
        self.videoControls_2.setStyleSheet('QToolBar#videoControls_2 { border: 50px }')
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.videoControls_2)
        self.frames_to_skip_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.frames_to_skip_slider.setMinimum(1)
        self.frames_to_skip_slider.setMaximum(100)
        self.frames_to_skip_slider.setValue(3)
        self.frames_to_skip_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.frames_to_skip_slider.setTickInterval(1)
        self.frames_to_skip_slider.setMaximumWidth(250)
        self.frames_to_skip_slider.valueChanged.connect(self.frames_to_skip_slider_changed)
        self.frames_to_skip_label = QtWidgets.QLabel()
        self.frames_to_skip_label.setStyleSheet('QLabel { font-size: 10pt; font-weight: bold; }')
        self.frames_to_skip_slider.setValue(30)
        self.videoControls.addWidget(self.frames_to_skip_label)
        self.videoControls.addWidget(self.frames_to_skip_slider)
        self.previousFrame_button = QtWidgets.QPushButton()
        self.previousFrame_button.setText('<<')
        self.previousFrame_button.setShortcut(self._config['shortcuts']['prev_x'])
        self.previousFrame_button.setToolTip(f'Jump Backward ({self._config['shortcuts']['prev_x']})')
        self.previousFrame_button.clicked.connect(self.previousFrame_buttonClicked)
        self.previous_1_Frame_button = QtWidgets.QPushButton()
        self.previous_1_Frame_button.setText('<')
        self.previous_1_Frame_button.setShortcut(self._config['shortcuts']['prev_1'])
        self.previous_1_Frame_button.setToolTip(f'Previous Frame ({self._config['shortcuts']['prev_1']})')
        self.previous_1_Frame_button.clicked.connect(self.previous_1_Frame_buttonclicked)
        self.playPauseButton = QtWidgets.QPushButton()
        self.playPauseButton_mode = 'Play'
        self.playPauseButton.setShortcut(self._config['shortcuts']['play'])
        self.playPauseButton.setToolTip(f'Play ({self._config['shortcuts']['play']})')
        self.playPauseButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
        self.playPauseButton.setIconSize(QtCore.QSize(22, 22))
        self.playPauseButton.setStyleSheet('QPushButton { margin: 5px;}')
        self.playPauseButton.pressed.connect(self.playPauseButtonClicked)
        self.nextFrame_button = QtWidgets.QPushButton()
        self.nextFrame_button.setText('>>')
        self.nextFrame_button.setShortcut(self._config['shortcuts']['next_x'])
        self.nextFrame_button.setToolTip(f'Jump forward ({self._config['shortcuts']['next_x']})')
        self.nextFrame_button.clicked.connect(self.nextFrame_buttonClicked)
        self.next_1_Frame_button = QtWidgets.QPushButton()
        self.next_1_Frame_button.setText('>')
        self.next_1_Frame_button.setShortcut(self._config['shortcuts']['next_1'])
        self.next_1_Frame_button.setToolTip(f'Next Frame ({self._config['shortcuts']['next_1']})')
        self.next_1_Frame_button.clicked.connect(self.next_1_Frame_buttonClicked)
        self.videoControls.addWidget(self.previousFrame_button)
        self.videoControls.addWidget(self.previous_1_Frame_button)
        self.videoControls.addWidget(self.playPauseButton)
        self.videoControls.addWidget(self.next_1_Frame_button)
        self.videoControls.addWidget(self.nextFrame_button)
        self.main_video_frames_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.main_video_frames_slider.setMinimum(1)
        self.main_video_frames_slider.setMaximum(100)
        self.main_video_frames_slider.setValue(2)
        self.main_video_frames_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.main_video_frames_slider.setTickInterval(1)
        self.main_video_frames_slider.setMaximumWidth(1000)
        self.main_video_frames_slider.valueChanged.connect(self.main_video_frames_slider_changed)
        self.main_video_frames_label_1 = QtWidgets.QLabel()
        self.main_video_frames_label_2 = QtWidgets.QLabel()
        self.main_video_frames_label_1.setStyleSheet('QLabel { font-size: 12pt; font-weight: bold; }')
        self.main_video_frames_label_2.setStyleSheet('QLabel { font-size: 12pt; font-weight: bold; }')
        self.videoControls.addWidget(self.main_video_frames_label_1)
        self.videoControls.addWidget(self.main_video_frames_slider)
        self.videoControls.addWidget(self.main_video_frames_label_2)
        self.frames_to_track_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.frames_to_track_slider.setMinimum(1)
        self.frames_to_track_slider.setMaximum(100)
        self.frames_to_track_slider.setValue(4)
        self.frames_to_track_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.frames_to_track_slider.setTickInterval(1)
        self.frames_to_track_slider.setMaximumWidth(200)
        self.frames_to_track_slider.valueChanged.connect(self.frames_to_track_slider_changed)
        self.frames_to_track_input = QtWidgets.QLineEdit()
        self.frames_to_track_input.setText('4')
        self.frames_to_track_input.setStyleSheet('QLineEdit { font-size: 10pt; }')
        self.frames_to_track_input.setMaximumWidth(50)
        self.frames_to_track_input.textChanged.connect(self.frames_to_track_input_changed)
        self.frames_to_track_label_before = QtWidgets.QLabel('Track for')
        self.frames_to_track_label_before.setStyleSheet('QLabel { font-size: 10pt; font-weight: bold; }')
        self.frames_to_track_label_after = QtWidgets.QLabel('frames')
        self.frames_to_track_label_after.setStyleSheet('QLabel { font-size: 10pt; font-weight: bold; }')
        self.videoControls_2.addWidget(self.frames_to_track_label_before)
        self.videoControls_2.addWidget(self.frames_to_track_input)
        self.videoControls_2.addWidget(self.frames_to_track_label_after)
        self.videoControls_2.addWidget(self.frames_to_track_slider)
        self.frames_to_track_slider.setValue(10)
        self.track_dropdown = QtWidgets.QComboBox()
        self.track_dropdown.addItems([f'Track for selected frames', 'Track Only assigned objects', 'Track Full Video'])
        self.track_dropdown.setCurrentIndex(0)
        self.track_dropdown.currentIndexChanged.connect(self.track_dropdown_changed)
        self.videoControls_2.addWidget(self.track_dropdown)
        self.start_button = QtWidgets.QPushButton('Start Tracking')
        self.start_button.setIcon(QtGui.QIcon('labelme/icons/start.png'))
        self.start_button.setIconSize(QtCore.QSize(24, 24))
        self.start_button.setStyleSheet(self.buttons_text_style_sheet)
        self.start_button.clicked.connect(self.start_tracking_button_clicked)
        self.videoControls_2.addWidget(self.start_button)
        self.tracking_progress_bar_label = QtWidgets.QLabel()
        self.tracking_progress_bar_label.setStyleSheet('QLabel { font-size: 10pt; font-weight: bold; }')
        self.tracking_progress_bar_label.setText('Tracking Progress')
        self.videoControls_2.addWidget(self.tracking_progress_bar_label)
        self.tracking_progress_bar = QtWidgets.QProgressBar()
        self.tracking_progress_bar.setMaximumWidth(300)
        self.tracking_progress_bar.setMinimum(0)
        self.tracking_progress_bar.setMaximum(100)
        self.tracking_progress_bar.setValue(0)
        self.videoControls_2.addWidget(self.tracking_progress_bar)
        self.track_stop_button = QtWidgets.QPushButton()
        self.track_stop_button.setStyleSheet('QPushButton {font-size: 10pt; margin: 2px 5px; padding: 2px 7px;font-weight: bold; background-color: #FF9090; color: #FFFFFF;} QPushButton:hover {background-color: #FF0000;} QPushButton:disabled {background-color: #7A7A7A;}')
        self.track_stop_button.setStyleSheet('QPushButton {font-size: 10pt; margin: 2px 5px; padding: 2px 7px;font-weight: bold; background-color: #FF0000; color: #FFFFFF;} QPushButton:hover {background-color: #FE4242;} QPushButton:disabled {background-color: #7A7A7A;}')
        self.track_stop_button.setText('Stop Tracking')
        self.track_stop_button.setIcon(QtGui.QIcon('labelme/icons/stop.png'))
        self.track_stop_button.setIconSize(QtCore.QSize(24, 24))
        self.track_stop_button.setToolTip(f'Stop Tracking ({self._config['shortcuts']['stop']})')
        self.track_stop_button.pressed.connect(self.Escape_clicked)
        self.videoControls_2.addWidget(self.track_stop_button)
        self.bbox_checkBox = QtWidgets.QCheckBox()
        self.bbox_checkBox.setText('bbox')
        self.bbox_checkBox.setChecked(True)
        self.bbox_checkBox.stateChanged.connect(self.bbox_checkBox_changed)
        self.id_checkBox = QtWidgets.QCheckBox()
        self.id_checkBox.setText('id')
        self.id_checkBox.setChecked(True)
        self.id_checkBox.stateChanged.connect(self.id_checkBox_changed)
        self.class_checkBox = QtWidgets.QCheckBox()
        self.class_checkBox.setText('class')
        self.class_checkBox.setChecked(True)
        self.class_checkBox.stateChanged.connect(self.class_checkBox_changed)
        self.conf_checkBox = QtWidgets.QCheckBox()
        self.conf_checkBox.setText('confidence')
        self.conf_checkBox.setChecked(True)
        self.conf_checkBox.stateChanged.connect(self.conf_checkBox_changed)
        self.mask_checkBox = QtWidgets.QCheckBox()
        self.mask_checkBox.setText('mask')
        self.mask_checkBox.setChecked(True)
        self.mask_checkBox.stateChanged.connect(self.mask_checkBox_changed)
        self.traj_checkBox = QtWidgets.QCheckBox()
        self.traj_checkBox.setText('trajectories')
        self.traj_checkBox.setChecked(False)
        self.traj_checkBox.stateChanged.connect(self.traj_checkBox_changed)
        self.trajectory_length_lineEdit = QtWidgets.QLineEdit()
        self.trajectory_length_lineEdit.setText(str(30))
        self.trajectory_length_lineEdit.setMaximumWidth(50)
        self.trajectory_length_lineEdit.editingFinished.connect(self.trajectory_length_lineEdit_changed)
        self.polygons_visable_checkBox = QtWidgets.QCheckBox()
        self.polygons_visable_checkBox.setText('show polygons')
        self.polygons_visable_checkBox.setChecked(True)
        self.polygons_visable_checkBox.stateChanged.connect(self.polygons_visable_checkBox_changed)
        self.vis_options = [self.id_checkBox, self.class_checkBox, self.bbox_checkBox, self.mask_checkBox, self.polygons_visable_checkBox, self.traj_checkBox, self.trajectory_length_lineEdit, self.conf_checkBox]
        self.vis_widget.setLayout(QtWidgets.QGridLayout())
        self.vis_widget.layout().setContentsMargins(10, 10, 25, 10)
        self.vis_widget.layout().addWidget(self.id_checkBox, 0, 0)
        self.vis_widget.layout().addWidget(self.class_checkBox, 0, 1)
        self.vis_widget.layout().addWidget(self.bbox_checkBox, 1, 0)
        self.vis_widget.layout().addWidget(self.mask_checkBox, 1, 1)
        self.vis_widget.layout().addWidget(self.traj_checkBox, 2, 0)
        self.vis_widget.layout().addWidget(self.trajectory_length_lineEdit, 2, 1)
        self.vis_widget.layout().addWidget(self.polygons_visable_checkBox, 3, 0)
        self.vis_widget.layout().addWidget(self.conf_checkBox, 3, 1)
        for option in self.vis_options:
            option.setEnabled(False)
        self.update_current_frame_annotation_button = QtWidgets.QPushButton()
        self.update_current_frame_annotation_button.setStyleSheet(self.buttons_text_style_sheet)
        self.update_current_frame_annotation_button.setText('Apply Changes')
        self.update_current_frame_annotation_button.setIcon(QtGui.QIcon('labelme/icons/done.png'))
        self.update_current_frame_annotation_button.setIconSize(QtCore.QSize(24, 24))
        self.update_current_frame_annotation_button.setShortcut(self._config['shortcuts']['update_frame'])
        self.update_current_frame_annotation_button.setToolTip(f'Apply changes on current frame ({self._config['shortcuts']['update_frame']})')
        self.update_current_frame_annotation_button.clicked.connect(self.update_current_frame_annotation_button_clicked)
        self.videoControls_2.addWidget(self.update_current_frame_annotation_button)
        self.clear_video_annotations_button = QtWidgets.QPushButton()
        self.clear_video_annotations_button.setStyleSheet(self.buttons_text_style_sheet)
        self.clear_video_annotations_button.setText('Clear All')
        self.clear_video_annotations_button.setIcon(QtGui.QIcon('labelme/icons/clear.png'))
        self.clear_video_annotations_button.setIconSize(QtCore.QSize(24, 24))
        self.clear_video_annotations_button.setShortcut(self._config['shortcuts']['clear_annotations'])
        self.clear_video_annotations_button.setToolTip(f'Clears Annotations from all frames ({self._config['shortcuts']['clear_annotations']})')
        self.clear_video_annotations_button.clicked.connect(self.clear_video_annotations_button_clicked)
        self.videoControls_2.addWidget(self.clear_video_annotations_button)
        self.set_video_controls_visibility(False)

    def draw_bb_on_image(self, image, shapes, image_qt_flag=True):
        return visualizations.draw_bb_on_image(self.CURRENT_ANNOATAION_TRAJECTORIES, self.INDEX_OF_CURRENT_FRAME, self.CURRENT_ANNOATAION_FLAGS, self.TOTAL_VIDEO_FRAMES, image, shapes, image_qt_flag)

    def waitWindow(self, visible=False, text=None):
        if visible:
            self.canvas.is_loading = True
            if text is not None:
                self.canvas.loading_text = text
        else:
            self.canvas.is_loading = False
            self.canvas.loading_text = 'Loading...'
        self.canvas.repaint()
        QtWidgets.QApplication.processEvents()

    def set_sam_toolbar_enable(self, enable=False):
        for widget in self.sam_toolbar.children():
            try:
                widget.setEnabled(enable or widget.accessibleName() == 'sam_enhance_annotation_button' or widget.accessibleName() == 'sam_model_comboBox')
            except:
                pass

    def set_sam_toolbar_visibility(self, visible=False):
        if not visible:
            try:
                self.sam_clear_annotation_button_clicked()
                self.sam_buttons_colors('X')
            except:
                pass
        self.sam_toolbar.setVisible(visible)
        for widget in self.sam_toolbar.children():
            try:
                widget.setVisible(visible)
            except:
                pass

    def addSamControls(self):
        self.sam_toolbar = QtWidgets.QToolBar()
        self.sam_toolbar.setMovable(True)
        self.sam_toolbar.setFloatable(True)
        self.sam_toolbar.setObjectName('sam_toolbar')
        self.sam_toolbar.setStyleSheet('QToolBar#videoControls { border: 50px }')
        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.sam_toolbar)
        self.sam_model_label = QtWidgets.QLabel()
        self.sam_model_label.setText('SAM Model')
        self.sam_model_label.setStyleSheet('QLabel { font-size: 10pt; font-weight: bold; }')
        self.sam_toolbar.addWidget(self.sam_model_label)
        self.sam_model_comboBox = QtWidgets.QComboBox()
        self.sam_model_comboBox.setAccessibleName('sam_model_comboBox')
        self.sam_model_comboBox.addItem('Select Model (SAM disabled)')
        self.sam_model_comboBox.addItems(self.sam_models())
        self.sam_model_comboBox.currentIndexChanged.connect(self.sam_model_comboBox_changed)
        self.sam_toolbar.addWidget(self.sam_model_comboBox)
        self.sam_add_point_button = QtWidgets.QPushButton()
        self.sam_add_point_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
        self.sam_add_point_button.setText('Add')
        self.sam_add_point_button.setIcon(QtGui.QIcon('labelme/icons/add.png'))
        self.sam_add_point_button.setIconSize(QtCore.QSize(24, 24))
        self.sam_add_point_button.setToolTip(f'Add point ({self._config['shortcuts']['SAM_add_point']})')
        self.sam_add_point_button.setShortcut(self._config['shortcuts']['SAM_add_point'])
        self.sam_add_point_button.clicked.connect(self.sam_add_point_button_clicked)
        self.sam_toolbar.addWidget(self.sam_add_point_button)
        self.sam_remove_point_button = QtWidgets.QPushButton()
        self.sam_remove_point_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
        self.sam_remove_point_button.setText('Remove')
        self.sam_remove_point_button.setIcon(QtGui.QIcon('labelme/icons/remove.png'))
        self.sam_remove_point_button.setIconSize(QtCore.QSize(24, 24))
        self.sam_remove_point_button.setToolTip(f'Remove Point ({self._config['shortcuts']['SAM_remove_point']})')
        self.sam_remove_point_button.setShortcut(self._config['shortcuts']['SAM_remove_point'])
        self.sam_remove_point_button.clicked.connect(self.sam_remove_point_button_clicked)
        self.sam_toolbar.addWidget(self.sam_remove_point_button)
        self.sam_select_rect_button = QtWidgets.QPushButton()
        self.sam_select_rect_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
        self.sam_select_rect_button.setText('Box')
        self.sam_select_rect_button.setIcon(QtGui.QIcon('labelme/icons/bbox.png'))
        self.sam_select_rect_button.setIconSize(QtCore.QSize(24, 24))
        self.sam_select_rect_button.setToolTip(f'Add Box ({self._config['shortcuts']['SAM_select_rect']})')
        self.sam_select_rect_button.setShortcut(self._config['shortcuts']['SAM_select_rect'])
        self.sam_select_rect_button.clicked.connect(self.sam_select_rect_button_clicked)
        self.sam_toolbar.addWidget(self.sam_select_rect_button)
        self.sam_clear_annotation_button = QtWidgets.QPushButton()
        self.sam_clear_annotation_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
        self.sam_clear_annotation_button.setText('Clear')
        self.sam_clear_annotation_button.setIcon(QtGui.QIcon('labelme/icons/clear.png'))
        self.sam_clear_annotation_button.setIconSize(QtCore.QSize(24, 24))
        self.sam_clear_annotation_button.setShortcut(self._config['shortcuts']['SAM_clear'])
        self.sam_clear_annotation_button.setToolTip(f'Clear points and boxes ({self._config['shortcuts']['SAM_clear']})')
        self.sam_clear_annotation_button.clicked.connect(self.sam_clear_annotation_button_clicked)
        self.sam_toolbar.addWidget(self.sam_clear_annotation_button)
        self.sam_finish_annotation_button = QtWidgets.QPushButton()
        self.sam_finish_annotation_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
        self.sam_finish_annotation_button.setText('Finish')
        self.sam_finish_annotation_button.setIcon(QtGui.QIcon('labelme/icons/done.png'))
        self.sam_finish_annotation_button.setIconSize(QtCore.QSize(24, 24))
        self.sam_finish_annotation_button.clicked.connect(self.sam_finish_annotation_button_clicked)
        self.sam_finish_annotation_button.setToolTip(f'Finish Annotation ({self._config['shortcuts']['SAM_finish_annotation']} or ENTER)')
        self.sam_finish_annotation_button.setShortcut(self._config['shortcuts']['SAM_finish_annotation'])
        self.sam_toolbar.addWidget(self.sam_finish_annotation_button)
        self.sam_close_button = QtWidgets.QPushButton()
        self.sam_close_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
        self.sam_close_button.setText('Manual')
        self.sam_close_button.setIcon(QtGui.QIcon('labelme/icons/objects.png'))
        self.sam_close_button.setIconSize(QtCore.QSize(24, 24))
        self.sam_close_button.setShortcut(self._config['shortcuts']['SAM_RESET'])
        self.sam_close_button.setToolTip(f'Return to Manual Mode ({self._config['shortcuts']['SAM_RESET']} or ESC)')
        self.sam_close_button.clicked.connect(self.sam_reset_button_clicked)
        self.sam_toolbar.addWidget(self.sam_close_button)
        self.sam_enhance_annotation_button = QtWidgets.QPushButton()
        self.sam_enhance_annotation_button.setAccessibleName('sam_enhance_annotation_button')
        self.sam_enhance_annotation_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
        self.sam_enhance_annotation_button.setText('Enhance Polygons')
        self.sam_enhance_annotation_button.setIcon(QtGui.QIcon('labelme/icons/SAM.png'))
        self.sam_enhance_annotation_button.setIconSize(QtCore.QSize(24, 24))
        self.sam_enhance_annotation_button.setShortcut(self._config['shortcuts']['SAM_enhance'])
        self.sam_enhance_annotation_button.setToolTip(f'Enhance Selected Polygons with SAM ({self._config['shortcuts']['SAM_enhance']})')
        self.sam_enhance_annotation_button.clicked.connect(self.sam_enhance_annotation_button_clicked)
        self.sam_toolbar.addWidget(self.sam_enhance_annotation_button)
        self.set_sam_toolbar_enable(False)
        self.sam_buttons_colors('x')

    def updateSamControls(self):
        self.sam_model_comboBox.clear()
        self.sam_model_comboBox.addItem('Select Model (SAM disabled)')
        self.sam_model_comboBox.addItems(self.sam_models())

    def sam_reset_button_clicked(self):
        self.sam_clear_annotation_button_clicked()
        self.setCreateMode()

    def sam_enhance_annotation_button_clicked(self):
        if self.sam_model_comboBox.currentText() == 'Select Model (SAM disabled)':
            MsgBox.OKmsgBox('SAM is disabled', 'SAM is disabled.\nPlease enable SAM.')
            return
        try:
            same_image = self.sam_predictor.check_image(self.CURRENT_FRAME_IMAGE)
        except:
            return
        toBeEnhanced = self.canvas.selectedShapes if len(self.canvas.selectedShapes) > 0 else self.canvas.shapes
        for shape in toBeEnhanced:
            try:
                self.canvas.shapes.remove(shape)
                self.remLabels([shape])
            except:
                return
            shapeX = mathOps.convert_qt_shapes_to_shapes([shape])[0]
            x1, y1, x2, y2 = shapeX['bbox']
            cur_bbox, cur_segment = self.sam_enhanced_bbox_segment(self.CURRENT_FRAME_IMAGE, [x1, y1, x2, y2], 1.2, max_itr=5, forSHAPE=True)
            shapeX['points'] = cur_segment
            shapeX = mathOps.convert_shapes_to_qt_shapes([shapeX])[0]
            self.canvas.shapes.append(shapeX)
            self.addLabel(shapeX)
        if self.current_annotation_mode == 'video':
            self.update_current_frame_annotation_button_clicked()
        else:
            self.sam_clear_annotation_button_clicked()
            self.refresh_image_MODE()
        self.sam_buttons_colors('X')

    def sam_models(self):
        cwd = os.getcwd()
        with open(cwd + '/models_menu/sam_models.json') as f:
            data = json.load(f)
        files = os.listdir(cwd + '/mmdetection/checkpoints/')
        models = []
        for model in data:
            if model['checkpoint'].split('/')[-1] in files:
                models.append(model['name'])
        return models

    def sam_model_comboBox_changed(self):
        createFlag = self.canvas.mode == 0
        self.canvas.cancelManualDrawing()
        self.sam_clear_annotation_button_clicked()
        self.sam_buttons_colors('X')
        if self.sam_model_comboBox.currentText() == 'Select Model (SAM disabled)':
            self.set_sam_toolbar_enable(False)
            return
        model_type = self.sam_model_comboBox.currentText()
        self.waitWindow(visible=True, text=f'Please Wait.\n{model_type} is Loading...')
        with open('models_menu/sam_models.json') as f:
            data = json.load(f)
        checkpoint_path = ''
        for model in data:
            if model['name'] == model_type:
                checkpoint_path = model['checkpoint']
        if checkpoint_path != '':
            self.sam_predictor = Sam_Predictor(model_type, checkpoint_path, device)
        try:
            self.sam_predictor.set_new_image(self.CURRENT_FRAME_IMAGE)
        except:
            print('please open an image first')
            self.waitWindow()
            return
        self.waitWindow()
        print('done loading model')
        if createFlag:
            self.setCreateMode()
            if self.sam_last_mode == 'point':
                self.sam_add_point_button_clicked()
            elif self.sam_last_mode == 'rectangle':
                self.sam_select_rect_button_clicked()
        else:
            self.setEditMode()

    def sam_buttons_colors(self, mode):
        setEnabled = False if self.sam_model_comboBox.currentText() == 'Select Model (SAM disabled)' else True
        if not setEnabled:
            self.set_sam_toolbar_enable(setEnabled)
            self.set_sam_toolbar_colors('X')
            return
        self.set_sam_toolbar_colors(mode)

    def set_sam_toolbar_enable(self, setEnabled):
        self.sam_add_point_button.setEnabled(setEnabled)
        self.sam_remove_point_button.setEnabled(setEnabled)
        self.sam_select_rect_button.setEnabled(setEnabled)
        self.sam_clear_annotation_button.setEnabled(setEnabled)
        self.sam_finish_annotation_button.setEnabled(setEnabled)

    def set_sam_toolbar_colors(self, mode):
        red, green, blue, trans = ('#2D7CFA;', '#2D7CFA;', '#2D7CFA;', '#4B515A;')
        hover_const = 'QPushButton::hover { background-color : '
        disabled_const = 'QPushButton:disabled { color : #7A7A7A} '
        style_sheet_const = 'QPushButton { font-size: 10pt; font-weight: bold; color: #ffffff; background-color: '
        [add_style, add_hover] = [green, green] if mode == 'add' else [trans, green]
        [remove_style, remove_hover] = [red, red] if mode == 'remove' else [trans, red]
        [rect_style, rect_hover] = [green, green] if mode == 'rect' else [trans, green]
        [clear_style, clear_hover] = [red, red] if mode == 'clear' else [trans, red]
        [finish_style, finish_hover] = [blue, blue] if mode == 'finish' else [trans, blue]
        [replace_style, replace_hover] = [blue, blue] if mode == 'replace' else [trans, blue]
        self.sam_add_point_button.setStyleSheet(style_sheet_const + add_style + ';}' + hover_const + add_hover + ';}' + disabled_const)
        self.sam_remove_point_button.setStyleSheet(style_sheet_const + remove_style + ';}' + hover_const + remove_hover + ';}' + disabled_const)
        self.sam_select_rect_button.setStyleSheet(style_sheet_const + rect_style + ';}' + hover_const + rect_hover + ';}' + disabled_const)
        self.sam_clear_annotation_button.setStyleSheet(style_sheet_const + clear_style + ';}' + hover_const + clear_hover + ';}' + disabled_const)
        self.sam_finish_annotation_button.setStyleSheet(style_sheet_const + finish_style + ';}' + hover_const + finish_hover + ';}' + disabled_const)
        self.sam_enhance_annotation_button.setStyleSheet(style_sheet_const + replace_style + ';}' + hover_const + replace_hover + ';}' + disabled_const)

    def sam_add_point_button_clicked(self):
        self.canvas.cancelManualDrawing()
        self.sam_last_mode = 'point'
        self.sam_buttons_colors('add')
        try:
            same_image = self.sam_predictor.check_image(self.CURRENT_FRAME_IMAGE)
        except:
            self.sam_buttons_colors('x')
            return
        if not same_image:
            self.sam_clear_annotation_button_clicked()
            self.sam_buttons_colors('add')
        self.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))
        self.canvas.SAM_mode = 'add point'

    def sam_remove_point_button_clicked(self):
        self.canvas.cancelManualDrawing()
        self.sam_buttons_colors('remove')
        try:
            same_image = self.sam_predictor.check_image(self.CURRENT_FRAME_IMAGE)
        except:
            self.sam_buttons_colors('x')
            return
        if not same_image:
            self.sam_clear_annotation_button_clicked()
            self.sam_buttons_colors('remove')
        self.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))
        self.canvas.SAM_mode = 'remove point'

    def sam_select_rect_button_clicked(self):
        self.canvas.cancelManualDrawing()
        self.sam_last_mode = 'rectangle'
        self.sam_buttons_colors('rect')
        try:
            same_image = self.sam_predictor.check_image(self.CURRENT_FRAME_IMAGE)
        except:
            self.sam_buttons_colors('x')
            return
        if not same_image:
            self.sam_clear_annotation_button_clicked()
            self.sam_buttons_colors('rect')
        self.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))
        self.canvas.SAM_mode = 'select rect'

    def sam_clear_annotation_button_clicked(self):
        self.canvas.cancelManualDrawing()
        self.sam_buttons_colors('clear')
        self.canvas.SAM_coordinates = []
        self.canvas.SAM_mode = ''
        self.canvas.SAM_rect = []
        self.canvas.SAM_rects = []
        self.current_sam_shape = None
        try:
            self.sam_predictor.clear_logit()
        except:
            pass
        self.labelList.clear()
        self.CURRENT_SHAPES_IN_IMG = mathOps.convert_qt_shapes_to_shapes(self.canvas.shapes)
        self.CURRENT_SHAPES_IN_IMG = self.check_sam_instance_in_shapes(self.CURRENT_SHAPES_IN_IMG)
        self.loadLabels(self.CURRENT_SHAPES_IN_IMG)

    def sam_finish_annotation_button_clicked(self):
        self.canvas.cancelManualDrawing()
        self.sam_buttons_colors('finish')
        self.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        self.canvas.SAM_coordinates = []
        self.canvas.SAM_rect = []
        self.canvas.SAM_rects = []
        self.canvas.SAM_mode = 'finished'
        try:
            self.sam_predictor.clear_logit()
            if len(self.current_sam_shape) == 0:
                return
        except:
            if self.sam_last_mode == 'point':
                self.sam_add_point_button_clicked()
            elif self.sam_last_mode == 'rectangle':
                self.sam_select_rect_button_clicked()
            return
        self.labelList.clear()
        sam_qt_shape = mathOps.convert_shapes_to_qt_shapes([self.current_sam_shape])[0]
        self.canvas.SAM_current = sam_qt_shape
        self.canvas.finalise(SAM_SHAPE=True)
        self.CURRENT_SHAPES_IN_IMG = mathOps.convert_qt_shapes_to_shapes(self.canvas.shapes)
        self.CURRENT_SHAPES_IN_IMG = self.check_sam_instance_in_shapes(self.CURRENT_SHAPES_IN_IMG)
        try:
            if self.current_sam_shape['group_id'] != -1:
                self.CURRENT_SHAPES_IN_IMG.append(self.current_sam_shape)
            self.rec_frame_for_id(self.current_sam_shape['group_id'], self.INDEX_OF_CURRENT_FRAME)
        except:
            pass
        self.loadLabels(self.CURRENT_SHAPES_IN_IMG)
        self.sam_predictor.clear_logit()
        self.canvas.SAM_coordinates = []
        self.current_sam_shape = None
        self.canvas.SAM_current = None
        self.canvas.SAM_mode = ''
        if self.current_annotation_mode == 'video':
            self.update_current_frame_annotation_button_clicked()
        else:
            self.canvas.shapes = mathOps.convert_shapes_to_qt_shapes(self.CURRENT_SHAPES_IN_IMG)
            self.sam_clear_annotation_button_clicked()
            self.refresh_image_MODE()

    def check_sam_instance_in_shapes(self, shapes):
        if len(shapes) == 0:
            return []
        for shape in shapes:
            if shape['label'] == 'SAM instance':
                shapes.remove(shape)
        return shapes

    def run_sam_model(self):
        if self.sam_predictor is None or self.sam_model_comboBox.currentText() == 'Select Model (SAM disabled)':
            print('please select a model')
            return
        try:
            same_image = self.sam_predictor.check_image(self.CURRENT_FRAME_IMAGE)
        except:
            self.sam_buttons_colors('x')
            return
        input_points, input_labels = mathOps.SAM_points_and_labels_from_coordinates(self.canvas.SAM_coordinates)
        input_boxes = mathOps.SAM_rects_to_boxes(self.canvas.SAM_rects)
        mask, score = self.sam_predictor.predict(point_coords=input_points, point_labels=input_labels, box=input_boxes, image=self.CURRENT_FRAME_IMAGE)
        points = mathOps.mask_to_polygons(mask)
        shape = mathOps.polygon_to_shape(points, score)
        self.current_sam_shape = shape
        self.labelList.clear()
        self.CURRENT_SHAPES_IN_IMG = mathOps.convert_qt_shapes_to_shapes(self.canvas.shapes)
        self.CURRENT_SHAPES_IN_IMG = self.check_sam_instance_in_shapes(self.CURRENT_SHAPES_IN_IMG)
        self.CURRENT_SHAPES_IN_IMG.append(self.current_sam_shape)
        self.loadLabels(self.CURRENT_SHAPES_IN_IMG)

    def turnOFF_SAM(self):
        if self.sam_model_comboBox.currentText() != 'Select Model (SAM disabled)':
            self.sam_clear_annotation_button_clicked()
        self.sam_buttons_colors('x')
        self.set_sam_toolbar_enable(False)
        self.canvas.SAM_mode = ''
        self.canvas.SAM_coordinates = []
        self.canvas.SAM_rect = []
        self.canvas.SAM_rects = []
        self.canvas.SAM_current = None

    def turnON_SAM(self):
        if self.sam_model_comboBox.currentText() == 'Select Model (SAM disabled)':
            return
        self.sam_buttons_colors('X')
        self.set_sam_toolbar_enable(True)
        self.canvas.SAM_mode = ''
        self.canvas.SAM_coordinates = []
        self.canvas.SAM_rect = []
        self.canvas.SAM_rects = []
        self.canvas.SAM_current = None

    def sam_enhanced_bbox_segment(self, frameIMAGE, cur_bbox, thresh, max_itr=5, forSHAPE=False):
        oldAREA = abs(cur_bbox[2] - cur_bbox[0]) * abs(cur_bbox[3] - cur_bbox[1])
        [x1, y1, x2, y2] = [cur_bbox[0], cur_bbox[1], cur_bbox[2], cur_bbox[3]]
        listPOINTS = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
        listPOINTS = [int(round(x)) for x in listPOINTS]
        input_boxes = [listPOINTS]
        mask, score = self.sam_predictor.predict(point_coords=None, point_labels=None, box=input_boxes, image=frameIMAGE)
        points = mathOps.mask_to_polygons(mask)
        SAMshape = mathOps.polygon_to_shape(points, score)
        cur_segment = SAMshape['points']
        cur_segment = [[int(cur_segment[i]), int(cur_segment[i + 1])] for i in range(0, len(cur_segment), 2)]
        cur_bbox = [min(np.array(cur_segment)[:, 0]), min(np.array(cur_segment)[:, 1]), max(np.array(cur_segment)[:, 0]), max(np.array(cur_segment)[:, 1])]
        cur_bbox = [int(round(x)) for x in cur_bbox]
        newAREA = abs(cur_bbox[2] - cur_bbox[0]) * abs(cur_bbox[3] - cur_bbox[1])
        bigger, smaller = (max(oldAREA, newAREA), min(oldAREA, newAREA))
        if bigger / smaller < thresh or max_itr == 1:
            if forSHAPE:
                return (cur_bbox, SAMshape['points'])
            else:
                return (cur_bbox, cur_segment)
        else:
            return self.sam_enhanced_bbox_segment(frameIMAGE, cur_bbox, thresh, max_itr - 1, forSHAPE)

    def load_objects_from_json__json(self):
        if self.global_listObj != []:
            return self.global_listObj
        json_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}_tracking_results.json'
        return mathOps.load_objects_from_json__json(json_file_name, self.TOTAL_VIDEO_FRAMES)

    def load_objects_to_json__json(self, listObj):
        self.global_listObj = listObj
        json_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}_tracking_results.json'
        mathOps.load_objects_to_json__json(json_file_name, listObj)

    def load_objects_from_json__orjson(self):
        if self.global_listObj != []:
            return self.global_listObj
        json_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}_tracking_results.json'
        return mathOps.load_objects_from_json__orjson(json_file_name, self.TOTAL_VIDEO_FRAMES)

    def load_objects_to_json__orjson(self, listObj):
        self.global_listObj = listObj
        json_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}_tracking_results.json'
        mathOps.load_objects_to_json__orjson(json_file_name, listObj)

def __init__(self, config=None, filename=None, output=None, output_file=None, output_dir=None):
    self.buttons_text_style_sheet = 'QPushButton {font-size: 10pt; margin: 2px 5px; padding: 2px 7px;font-weight: bold; background-color: #0d69f5; color: #FFFFFF;} QPushButton:hover {background-color: #4990ED;} QPushButton:disabled {background-color: #7A7A7A;}'
    if output is not None:
        logger.warning('argument output is deprecated, use output_file instead')
        if output_file is None:
            output_file = output
    if config is None:
        config = get_config()
    self._config = config
    self.decodingCanceled = False
    Shape.line_color = QtGui.QColor(*self._config['shape']['line_color'])
    Shape.fill_color = QtGui.QColor(*self._config['shape']['fill_color'])
    Shape.select_line_color = QtGui.QColor(*self._config['shape']['select_line_color'])
    Shape.select_fill_color = QtGui.QColor(*self._config['shape']['select_fill_color'])
    Shape.vertex_fill_color = QtGui.QColor(*self._config['shape']['vertex_fill_color'])
    Shape.hvertex_fill_color = QtGui.QColor(*self._config['shape']['hvertex_fill_color'])
    mathOps.update_saved_models_json(os.getcwd())
    self.segmentation_options_UI = SegmentationOptionsUI(self)
    self.merge_feature_UI = MergeFeatureUI(self)
    super(MainWindow, self).__init__()
    try:
        self.intelligenceHelper = Intelligence(self)
    except:
        print('it seems you have a problem with initializing model\ncheck you have at least one model')
        self.helper_first_time_flag = True
    else:
        self.helper_first_time_flag = False
    self.setWindowTitle(__appname__)
    self.dirty = False
    self._noSelectionSlot = False
    self.labelDialog = LabelDialog(parent=self, labels=self._config['labels'], sort_labels=self._config['sort_labels'], show_text_field=self._config['show_label_text_field'], completion=self._config['label_completion'], fit_to_content=self._config['fit_to_content'], flags=self._config['label_flags'])
    self.labelList = LabelListWidget()
    self.lastOpenDir = None
    self.flag_dock = self.flag_widget = None
    self.flag_dock = QtWidgets.QDockWidget(self.tr('Flags'), self)
    self.flag_dock.setObjectName('Flags')
    self.flag_widget = QtWidgets.QListWidget()
    if config['flags']:
        self.loadFlags({k: False for k in config['flags']})
    self.flag_widget.itemChanged.connect(self.setDirty)
    self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)
    self.labelList.itemDoubleClicked.connect(self.editLabel)
    self.labelList.itemChanged.connect(self.labelItemChanged)
    self.labelList.itemDropped.connect(self.labelOrderChanged)
    self.shape_dock = QtWidgets.QDockWidget(self.tr('Polygon Labels'), self)
    self.shape_dock.setObjectName('Labels')
    self.shape_dock.setWidget(self.labelList)
    self.uniqLabelList = UniqueLabelQListWidget()
    self.uniqLabelList.setToolTip(self.tr("Select label to start annotating for it. Press 'Esc' to deselect."))
    if self._config['labels']:
        for label in self._config['labels']:
            item = self.uniqLabelList.createItemFromLabel(label)
            self.uniqLabelList.addItem(item)
            rgb = self._get_rgb_by_label(label)
            self.uniqLabelList.setItemLabel(item, label, rgb)
    self.label_dock = QtWidgets.QDockWidget(self.tr(u'Label List'), self)
    self.label_dock.setObjectName(u'Label List')
    self.label_dock.setWidget(self.uniqLabelList)
    self.fileSearch = QtWidgets.QLineEdit()
    self.fileSearch.setPlaceholderText(self.tr('Search Filename'))
    self.fileSearch.textChanged.connect(self.fileSearchChanged)
    self.fileListWidget = QtWidgets.QListWidget()
    self.fileListWidget.itemSelectionChanged.connect(self.fileSelectionChanged)
    fileListLayout = QtWidgets.QVBoxLayout()
    fileListLayout.setContentsMargins(0, 0, 0, 0)
    fileListLayout.setSpacing(0)
    fileListLayout.addWidget(self.fileSearch)
    fileListLayout.addWidget(self.fileListWidget)
    self.file_dock = QtWidgets.QDockWidget(self.tr(u'File List'), self)
    self.file_dock.setObjectName(u'Files')
    fileListWidget = QtWidgets.QWidget()
    fileListWidget.setLayout(fileListLayout)
    self.file_dock.setWidget(fileListWidget)
    self.vis_dock = QtWidgets.QDockWidget(self.tr(u'Visualization Options'), self)
    self.vis_dock.setObjectName(u'Visualization Options')
    self.vis_widget = QtWidgets.QWidget()
    self.vis_dock.setWidget(self.vis_widget)
    self.zoomWidget = ZoomWidget()
    self.setAcceptDrops(True)
    self.canvas = self.labelList.canvas = Canvas(epsilon=self._config['epsilon'], double_click=self._config['canvas']['double_click'], num_backups=self._config['canvas']['num_backups'])
    self.canvas.zoomRequest.connect(self.zoomRequest)
    scrollArea = QtWidgets.QScrollArea()
    scrollArea.setWidget(self.canvas)
    scrollArea.setWidgetResizable(True)
    self.scrollBars = {Qt.Orientation.Vertical: scrollArea.verticalScrollBar(), Qt.Orientation.Horizontal: scrollArea.horizontalScrollBar(), Qt.Orientation.Horizontal.value: scrollArea.horizontalScrollBar(), Qt.Orientation.Vertical.value: scrollArea.verticalScrollBar()}
    self.canvas.scrollRequest.connect(self.scrollRequest)
    self.canvas.newShape.connect(self.newShape)
    self.canvas.shapeMoved.connect(self.setDirty)
    self.canvas.selectionChanged.connect(self.shapeSelectionChanged)
    self.canvas.drawingPolygon.connect(self.toggleDrawingSensitive)
    self.canvas.edgeSelected.connect(self.canvasShapeEdgeSelected)
    self.canvas.APPrefresh.connect(self.refresh_image_MODE)
    self.addSamControls()
    self.canvas.pointAdded.connect(self.run_sam_model)
    self.canvas.samFinish.connect(self.sam_finish_annotation_button_clicked)
    self.sam_predictor = None
    self.current_sam_shape = None
    self.SAM_SHAPES_IN_IMAGE = []
    self.sam_last_mode = 'rectangle'
    self.setCentralWidget(scrollArea)
    self.target_directory = ''
    self.save_path = ''
    self.global_listObj = []
    self.multi_model_flag = False
    self.addVideoControls()
    self.frame_time = 0
    self.FRAMES_TO_SKIP = 30
    self.TRACK_ASSIGNED_OBJECTS_ONLY = False
    self.TrackingMode = False
    self.current_annotation_mode = ''
    self.CURRENT_ANNOATAION_FLAGS = {'traj': False, 'bbox': True, 'id': True, 'class': True, 'mask': True, 'polygons': True, 'conf': True}
    self.CURRENT_ANNOATAION_TRAJECTORIES = {'length': 30, 'alpha': 0.7}
    self.CURRENT_SHAPES_IN_IMG = []
    self.featuresOptions = {'deleteDefault': 'this frame only', 'interpolationDefMethod': 'linear', 'interpolationDefType': 'all', 'interpolationOverwrite': False, 'EditDefault': 'Edit only this frame'}
    self.key_frames = {}
    self.id_frames_rec = {}
    self.copiedShapes = []
    self.INDEX_OF_CURRENT_FRAME = 1
    self.interrupted = False
    self.minID = -2
    self.maxID = 0
    for dock in ['label_dock', 'shape_dock', 'file_dock', 'vis_dock']:
        if self._config[dock]['closable']:
            getattr(self, dock).setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable)
        if self._config[dock]['floatable']:
            getattr(self, dock).setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        if self._config[dock]['movable']:
            getattr(self, dock).setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable)
        if self._config[dock]['show'] is False:
            getattr(self, dock).setVisible(False)
    self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.label_dock)
    self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.shape_dock)
    self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.file_dock)
    self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.vis_dock)
    action = functools.partial(utils.newAction, self)
    shortcuts = self._config['shortcuts']
    quit = action(self.tr('&Quit'), self.close, shortcuts['quit'], 'quit', self.tr('Quit application'))
    open_ = action(self.tr('&Open Image'), self.openFile, shortcuts['open'], 'open', self.tr(f'Open image or label file ({str(shortcuts['open'])})'))
    opendir = action(self.tr('&Open Dir'), self.openDirDialog, shortcuts['open_dir'], 'opendir', self.tr(f'Open Dir ({str(shortcuts['open_dir'])})'))
    save = action(self.tr('&Save'), self.saveFile, shortcuts['save'], 'save', self.tr(f'Save labels to file ({str(shortcuts['save'])})'), enabled=False)
    export = action(self.tr('&Export'), self.exportData, shortcuts['export'], 'export', self.tr(f'Export annotations to COCO format ({str(shortcuts['export'])})'), enabled=False)
    modelExplorer = action(self.tr('&Model Explorer'), self.model_explorer, None, 'checklist', self.tr(u'Model Explorer'))
    saveAs = action(self.tr('&Save As'), self.saveFileAs, shortcuts['save_as'], 'save-as', self.tr('Save labels to a different file'), enabled=False)
    deleteFile = action(self.tr('&Delete File'), self.deleteFile, shortcuts['delete_file'], 'delete', self.tr('Delete current label file'), enabled=False)
    changeOutputDir = action(self.tr('&Change Output Dir'), slot=self.changeOutputDirDialog, shortcut=shortcuts['save_to'], icon='open', tip=self.tr(u'Change where annotations are loaded/saved'))
    saveAuto = action(text=self.tr('Save &Automatically'), slot=lambda x: self.actions.saveAuto.setChecked(x), icon='save', tip=self.tr('Save automatically'), checkable=True, enabled=True)
    saveAuto.setChecked(self._config['auto_save'])
    saveWithImageData = action(text='Save With Image Data', slot=self.enableSaveImageWithData, tip='Save image data in label file', checkable=True, checked=self._config['store_data'])
    close = action('&Close', self.closeFile, shortcuts['close'], 'close', 'Close current file')
    toggle_keep_prev_mode = action(self.tr('Keep Previous Annotation'), self.toggleKeepPrevMode, shortcuts['toggle_keep_prev_mode'], None, self.tr('Toggle "keep pevious annotation" mode'), checkable=True)
    toggle_keep_prev_mode.setChecked(self._config['keep_prev'])
    createMode = action(self.tr('Create Polygons'), self.setCreateMode, shortcuts['create_polygon'], 'objects', self.tr('Start drawing polygons'), enabled=False)
    editMode = action(self.tr('Edit Polygons'), self.setEditMode, shortcuts['edit_polygon'], 'edit', self.tr('Move and edit the selected polygons'), enabled=False)
    delete = action(self.tr('Delete Polygons'), self.deleteSelectedShape, shortcuts['delete_polygon'], 'close', self.tr('Delete the selected polygons'), enabled=False)
    copy = action(self.tr('Duplicate Polygons'), self.copySelectedShape, shortcuts['duplicate_polygon'], 'copy', self.tr('Create a duplicate of the selected polygons'), enabled=False)
    undoLastPoint = action(self.tr('Undo last point'), self.canvas.undoLastPoint, shortcuts['undo_last_point'], 'undo', self.tr('Undo last drawn point'), enabled=False)
    addPointToEdge = action(text=self.tr('Add Point to Edge'), slot=self.canvas.addPointToEdge, shortcut=shortcuts['add_point_to_edge'], icon='add_point', tip=self.tr('Add point to the nearest edge'), enabled=False)
    removePoint = action(text='Remove Selected Point', slot=self.removeSelectedPoint, icon='edit', tip='Remove selected point from polygon', enabled=False)
    undo = action(self.tr('Undo'), self.undoShapeEdit, shortcuts['undo'], 'undo', self.tr('Undo last add and edit of shape'), enabled=False)
    hideAll = action(self.tr('&Hide\nPolygons'), functools.partial(self.togglePolygons, False), icon='eye', tip=self.tr('Hide all polygons'), enabled=False)
    showAll = action(self.tr('&Show\nPolygons'), functools.partial(self.togglePolygons, True), icon='eye', tip=self.tr('Show all polygons'), enabled=False)
    zoom = QtWidgets.QWidgetAction(self)
    zoom.setDefaultWidget(self.zoomWidget)
    self.zoomWidget.setWhatsThis(self.tr('Zoom in or out of the image. Also accessible with {} and {} from the canvas.').format(utils.fmtShortcut('{},{}'.format(shortcuts['zoom_in'], shortcuts['zoom_out'])), utils.fmtShortcut(self.tr('Ctrl+Wheel'))))
    self.zoomWidget.setEnabled(False)
    zoomIn = action(self.tr('Zoom &In'), functools.partial(self.addZoom, 1.1), shortcuts['zoom_in'], 'zoom-in', self.tr('Increase zoom level'), enabled=False)
    zoomOut = action(self.tr('&Zoom Out'), functools.partial(self.addZoom, 0.9), shortcuts['zoom_out'], 'zoom-out', self.tr('Decrease zoom level'), enabled=False)
    zoomOrg = action(self.tr('&Original size'), functools.partial(self.setZoom, 100), shortcuts['zoom_to_original'], 'zoom', self.tr('Zoom to original size'), enabled=False)
    fitWindow = action(self.tr('&Fit Window'), self.setFitWindow, shortcuts['fit_window'], 'fit-window', self.tr('Zoom follows window size'), checkable=True, enabled=False)
    fitWidth = action(self.tr('Fit &Width'), self.setFitWidth, shortcuts['fit_width'], 'fit-width', self.tr('Zoom follows window width'), checkable=True, enabled=False)
    brightnessContrast = action('&Brightness Contrast', self.brightnessContrast, None, 'color', 'Adjust brightness and contrast', enabled=False)
    show_cross_line = action(self.tr('&Toggle Cross Line'), self.enable_show_cross_line, tip=self.tr('cross line for mouse position'), icon='cartesian', checkable=True, checked=self._config['show_cross_line'], enabled=True)
    zoomActions = (self.zoomWidget, zoomIn, zoomOut, zoomOrg, fitWindow, fitWidth)
    self.zoomMode = self.FIT_WINDOW
    fitWindow.setChecked(True)
    self.scalers = {self.FIT_WINDOW: self.scaleFitWindow, self.FIT_WIDTH: self.scaleFitWidth, self.MANUAL_ZOOM: lambda: 1}
    edit = action(self.tr('Edit &Label'), self.editLabel, shortcuts['edit_label'], 'label', self.tr('Modify the label of the selected polygon'), enabled=False)
    enhance = action(self.tr('&Enhace Polygons'), self.sam_enhance_annotation_button_clicked, shortcuts['SAM_enhance'], 'SAM', self.tr('Enhance the selected polygon with AI'), enabled=True)
    interpolate = action(self.tr('&Interpolation Tracking'), self.interpolateMENU, shortcuts['interpolate'], 'tracking', self.tr('Interpolate the selected polygon between to frames to Track it'), enabled=True)
    mark_as_key = action(self.tr('&Mark as key'), self.mark_as_key, shortcuts['mark_as_key'], 'mark', self.tr('Mark this frame as KEY for interpolation'), enabled=True)
    remove_all_keyframes = action(self.tr('&Remove all keyframes'), self.remove_all_keyframes, None, 'mark', self.tr('Remove all keyframes'), enabled=True)
    scale = action(self.tr('&Scale'), self.scaleMENU, shortcuts['scale'], 'resize', self.tr('Scale the selected polygon'), enabled=True)
    copyShapes = action(self.tr('&Copy'), self.ctrlCopy, shortcuts['copy'], 'copy', self.tr('Copy selected polygons'), enabled=True)
    pasteShapes = action(self.tr('&Paste'), self.ctrlPaste, shortcuts['paste'], 'paste', self.tr('paste copied polygons'), enabled=True)
    update_curr_frame = action(self.tr('&Update current frame'), self.update_current_frame_annotation_button_clicked, None, 'done', self.tr('Update frame'), enabled=True)
    ignore_changes = action(self.tr('&Ignore changes'), self.main_video_frames_slider_changed, shortcuts['ignore_updates'], 'delete', self.tr('Ignore unsaved changes'), enabled=True)
    fill_drawing = action(self.tr('Fill Drawing Polygon'), self.canvas.setFillDrawing, None, 'color', self.tr('Fill polygon while drawing'), checkable=True, enabled=True)
    fill_drawing.trigger()
    annotate_one_action = action(self.tr('Run Model on Current Image'), self.annotate_one, None, 'open', self.tr('Run Model on Current Image'))
    annotate_batch_action = action(self.tr('Run Model on All Images'), self.annotate_batch, None, 'file', self.tr('Run Model on All Images'))
    set_conf_threshold = action(self.tr('Confidence Threshold'), self.setConfThreshold, None, 'tune', self.tr('Confidence Threshold'))
    set_iou_threshold = action(self.tr('IOU Threshold (NMS)'), self.setIOUThreshold, None, 'iou', self.tr('IOU Threshold (Non Maximum Suppression)'))
    select_classes = action(self.tr('Select Classes'), self.selectClasses, None, 'checklist', self.tr('Select Classes to be Annotated'))
    merge_segmentation_models = action(self.tr('Merge Segmentation Models'), self.mergeSegModels, None, 'merge', self.tr('Merge Segmentation Models'))
    runtime_data = action(self.tr('Show Runtime Data'), runtime_data_UI.PopUp, None, 'runtime', self.tr('Show Runtime Data'))
    git_hub = action(self.tr('GitHub Repository'), links.open_git_hub, None, 'github', self.tr('GitHub Repository'))
    feedback = action(self.tr('Feedback'), feedback_UI.PopUp, None, 'feedback', self.tr('Feedback'))
    license = action(self.tr('license'), links.open_license, None, 'license', self.tr('license'))
    user_guide = action(self.tr('User Guide'), links.open_guide, None, 'guide', self.tr('User Guide'))
    check_updates = action(self.tr('Check for Updates'), check_updates_UI.PopUp, None, 'info', self.tr('Check for Updates'))
    preferences = action(self.tr('Preferences'), preferences_UI.PopUp, None, 'settings', self.tr('Preferences'))
    shortcut_selector = action(self.tr('Shortcuts'), shortcut_selector_UI.PopUp, None, 'shortcuts', self.tr('Shortcuts'))
    sam = action(self.tr('Toggle SAM Toolbar'), self.Segment_anything, None, 'SAM', self.tr('Toggle SAM Toolbar'))
    openVideo = action(self.tr('Open &Video'), self.openVideo, shortcuts['open_video'], 'video', self.tr(f'Open a video file ({shortcuts['open_video']})'))
    openVideoFrames = action(self.tr('Open Video as Frames'), self.openVideoFrames, shortcuts['open_video_frames'], 'frames', self.tr(f'Open Video as Frames ({shortcuts['open_video_frames']})'))
    labelmenu = QtWidgets.QMenu()
    utils.addActions(labelmenu, (edit, delete))
    self.labelList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    self.labelList.customContextMenuRequested.connect(self.popLabelListMenu)
    self.actions = utils.struct(saveAuto=saveAuto, saveWithImageData=saveWithImageData, changeOutputDir=changeOutputDir, save=save, saveAs=saveAs, open=open_, close=close, deleteFile=deleteFile, toggleKeepPrevMode=toggle_keep_prev_mode, delete=delete, edit=edit, copy=copy, undoLastPoint=undoLastPoint, undo=undo, addPointToEdge=addPointToEdge, removePoint=removePoint, createMode=createMode, editMode=editMode, zoom=zoom, zoomIn=zoomIn, zoomOut=zoomOut, zoomOrg=zoomOrg, fitWindow=fitWindow, fitWidth=fitWidth, brightnessContrast=brightnessContrast, show_cross_line=show_cross_line, zoomActions=zoomActions, export=export, openVideo=openVideo, openVideoFrames=openVideoFrames, fileMenuActions=(open_, opendir, save, saveAs, close, quit), modelExplorer=modelExplorer, runtime_data=runtime_data, tool=(), editMenu=(edit, copy, delete, None, undo, undoLastPoint, None, addPointToEdge), menu=(createMode, editMode, edit, enhance, interpolate, mark_as_key, remove_all_keyframes, scale, copyShapes, pasteShapes, copy, delete, undo, undoLastPoint, addPointToEdge, removePoint, update_curr_frame, ignore_changes), onLoadActive=(close, createMode, editMode, brightnessContrast), onShapesPresent=(saveAs, hideAll, showAll))
    self.canvas.vertexSelected.connect(self.actions.removePoint.setEnabled)
    self.menus = utils.struct(file=self.menu(self.tr('&File')), edit=self.menu(self.tr('&Edit')), view=self.menu(self.tr('&View')), intelligence=self.menu(self.tr('&Auto Annotation')), model_selection=self.menu(self.tr('&Model Selection')), options=self.menu(self.tr('&Options')), help=self.menu(self.tr('&Help')), recentFiles=QtWidgets.QMenu(self.tr('Open &Recent')), saved_models=QtWidgets.QMenu(self.tr('Select Segmentation model')), tracking_models=QtWidgets.QMenu(self.tr('Select Tracking model')), labelList=labelmenu, certain_area=QtWidgets.QMenu(self.tr('Select Certain Area')), ui_elements=QtWidgets.QMenu(self.tr('&Show UI Elements')), zoom_options=QtWidgets.QMenu(self.tr('&Zoom Options')))
    utils.addActions(self.menus.file, (open_, opendir, openVideo, openVideoFrames, None, save, saveAs, export, None, close, quit))
    utils.addActions(self.menus.intelligence, (annotate_one_action, annotate_batch_action))
    self.menus.ui_elements.setIcon(QtGui.QIcon('labelme/icons/UI.png'))
    utils.addActions(self.menus.ui_elements, (self.vis_dock.toggleViewAction(), self.label_dock.toggleViewAction(), self.shape_dock.toggleViewAction(), self.file_dock.toggleViewAction()))
    self.menus.zoom_options.setIcon(QtGui.QIcon('labelme/icons/zoom.png'))
    utils.addActions(self.menus.zoom_options, (zoomIn, zoomOut, zoomOrg, None, fitWindow, fitWidth))
    utils.addActions(self.menus.view, (sam, self.menus.ui_elements, None, hideAll, showAll, None, self.menus.zoom_options, None, show_cross_line))
    self.menus.saved_models.setIcon(QtGui.QIcon('labelme/icons/brain.png'))
    self.menus.tracking_models.setIcon(QtGui.QIcon('labelme/icons/tracking.png'))
    self.menus.certain_area.setIcon(QtGui.QIcon('labelme/icons/polygon.png'))
    utils.addActions(self.menus.model_selection, (self.menus.saved_models, merge_segmentation_models, None, self.menus.tracking_models, None, modelExplorer))
    utils.addActions(self.menus.options, (set_conf_threshold, set_iou_threshold, self.menus.certain_area, None, select_classes))
    utils.addActions(self.menus.help, (user_guide, preferences, shortcut_selector, None, git_hub, feedback, None, runtime_data, None, license, check_updates))
    self.menus.file.aboutToShow.connect(self.updateFileMenu)
    self.menus.file.aboutToShow.connect(self.update_models_menu)
    utils.addActions(self.canvas.menus[0], self.actions.menu)
    utils.addActions(self.canvas.menus[1], (action('&Copy here', self.copyShape), action('&Move here', self.moveShape)))
    self.tools = self.toolbar('Tools')
    self.actions.tool = (open_, opendir, openVideo, None, save, export, None, createMode, editMode, edit, None, delete, undo, None)
    self.statusBar().showMessage(self.tr('%s started.') % __appname__)
    self.statusBar().show()
    if output_file is not None and self._config['auto_save']:
        logger.warn('If `auto_save` argument is True, `output_file` argument is ignored and output filename is automatically set as IMAGE_BASENAME.json.')
    self.output_file = output_file
    self.output_dir = output_dir
    self.image = QtGui.QImage()
    self.imagePath = None
    self.recentFiles = []
    self.maxRecent = 7
    self.otherData = None
    self.zoom_level = 100
    self.fit_window = False
    self.zoom_values = {}
    self.brightnessContrast_values = {}
    self.scroll_values = {Qt.Orientation.Horizontal: {}, Qt.Orientation.Vertical: {}, Qt.Orientation.Horizontal.value: {}, Qt.Orientation.Vertical.value: {}}
    if filename is not None and osp.isdir(filename):
        self.importDirImages(filename, load=False)
    else:
        self.filename = filename
    if config['file_search']:
        self.fileSearch.setText(config['file_search'])
        self.fileSearchChanged()
    self.settings = QtCore.QSettings('labelme', 'labelme')
    self.recentFiles = self.settings.value('recentFiles', []) or []
    size = self.settings.value('window/size', QtCore.QSize(600, 500))
    position = self.settings.value('window/position', QtCore.QPoint(0, 0))
    self.resize(size)
    self.move(position)
    self.restoreState(self.settings.value('window/state', QtCore.QByteArray()))
    self.updateFileMenu()
    self.update_models_menu()
    if self.filename is not None:
        self.queueEvent(functools.partial(self.loadFile, self.filename))
    self.zoomWidget.valueChanged.connect(self.paintCanvas)
    self.populateModeActions()
    self.right_click_menu()
    QtGui.QShortcut(QtGui.QKeySequence(self._config['shortcuts']['stop']), self).activated.connect(self.Escape_clicked)

def menu(self, title, actions=None):
    menu = self.menuBar().addMenu(title)
    if actions:
        utils.addActions(menu, actions)
    return menu

def toolbar(self, title, actions=None):
    toolbar = ToolBar(title)
    toolbar.setObjectName('%sToolBar' % title)
    toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    if actions:
        utils.addActions(toolbar, actions)
    self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)
    return toolbar

def populateModeActions(self):
    tool, menu = (self.actions.tool, self.actions.menu)
    self.tools.clear()
    utils.addActions(self.tools, tool)
    self.canvas.menus[0].clear()
    utils.addActions(self.canvas.menus[0], menu)
    self.menus.edit.clear()
    actions = (self.actions.editMode,)
    utils.addActions(self.menus.edit, actions + self.actions.editMenu)

def status(self, message, delay=5000):
    self.statusBar().showMessage(message, delay)

def Escape_clicked(self):
    """
        Summary:
            This function is called when the user presses the escape key.
            It resets the SAM toolbar and the canvas.
            It also interrupts the current annotation process like (tracking, interpolation, etc.)
        """
    self.interrupted = True
    self.sam_reset_button_clicked()
    if self.canvas.tracking_area == 'drawing':
        self.certain_area_clicked(1)

def exists(filename):
    return osp.exists(str(filename))

def updateFileMenu(self):
    current = self.filename

    def exists(filename):
        return osp.exists(str(filename))
    menu = self.menus.recentFiles
    menu.clear()
    files = [f for f in self.recentFiles if f != current and exists(f)]
    for i, f in enumerate(files):
        icon = utils.newIcon('brain')
        action = QtGui.QAction(icon, '&%d %s' % (i + 1, QtCore.QFileInfo(f).fileName()), self)
        action.triggered.connect(functools.partial(self.loadRecent, f))
        menu.addAction(action)

def add_tracking_models_menu(self):
    menu2 = self.menus.tracking_models
    menu2.clear()
    icon = utils.newIcon('tracking')
    action = QtGui.QAction(icon, '1 Byte track (DEFAULT)', self)
    action.triggered.connect(lambda: self.update_tracking_method('bytetrack'))
    menu2.addAction(action)
    icon = utils.newIcon('tracking')
    action = QtGui.QAction(icon, '2 Strong SORT  (lowest id switch)', self)
    action.triggered.connect(lambda: self.update_tracking_method('strongsort'))
    menu2.addAction(action)
    icon = utils.newIcon('tracking')
    action = QtGui.QAction(icon, '3 Deep SORT', self)
    action.triggered.connect(lambda: self.update_tracking_method('deepocsort'))
    menu2.addAction(action)
    icon = utils.newIcon('tracking')
    action = QtGui.QAction(icon, '4 OC SORT', self)
    action.triggered.connect(lambda: self.update_tracking_method('ocsort'))
    menu2.addAction(action)
    icon = utils.newIcon('tracking')
    action = QtGui.QAction(icon, '5 BoT SORT', self)
    action.triggered.connect(lambda: self.update_tracking_method('botsort'))
    menu2.addAction(action)

def add_certain_area_menu(self):
    menu3 = self.menus.certain_area
    menu3.clear()
    icon = utils.newIcon('polygon')
    action = QtGui.QAction(icon, 'Select Certain Area', self)
    action.triggered.connect(lambda: self.certain_area_clicked(1))
    menu3.addAction(action)
    icon = utils.newIcon('rectangle')
    action = QtGui.QAction(icon, 'Cancel Area', self)
    action.triggered.connect(lambda: self.certain_area_clicked(0))
    menu3.addAction(action)

def validateLabel(self, label):
    if self._config['validate_label'] is None:
        return True
    for i in range(self.uniqLabelList.count()):
        label_i = self.uniqLabelList.item(i).data(Qt.ItemDataRole.UserRole)
        if self._config['validate_label'] in ['exact']:
            if label_i == label:
                return True
    return False

def addLabel(self, shape):
    if shape.group_id is None or self.current_annotation_mode != 'video':
        text = shape.label
    else:
        text = f' ID {shape.group_id}: {shape.label}'
    label_list_item = LabelListWidgetItem(text, shape)
    self.labelList.addItem(label_list_item)
    if not self.uniqLabelList.findItemsByLabel(shape.label):
        item = self.uniqLabelList.createItemFromLabel(shape.label)
        self.uniqLabelList.addItem(item)
        rgb = self._get_rgb_by_label(shape.label)
        self.uniqLabelList.setItemLabel(item, shape.label, rgb)
    self.labelDialog.addLabelHistory(shape.label)
    for action in self.actions.onShapesPresent:
        action.setEnabled(True)
    rgb = self._get_rgb_by_label(shape.label)
    r, g, b = rgb
    label_list_item.setText('{} <font color="#{:02x}{:02x}{:02x}">●</font>'.format(text, r, g, b))
    shape.line_color = QtGui.QColor(r, g, b)
    shape.vertex_fill_color = QtGui.QColor(r, g, b)
    shape.hvertex_fill_color = QtGui.QColor(255, 255, 255)
    shape.fill_color = QtGui.QColor(r, g, b, 128)
    shape.select_line_color = QtGui.QColor(255, 255, 255)
    shape.select_fill_color = QtGui.QColor(r, g, b, 155)

def setScroll(self, orientation, value):
    self.scrollBars[orientation].setValue(value)
    self.scroll_values[orientation][self.filename] = value

def setZoom(self, value):
    self.actions.fitWidth.setChecked(False)
    self.actions.fitWindow.setChecked(False)
    self.zoomMode = self.MANUAL_ZOOM
    self.zoomWidget.setValue(value)
    self.zoom_values[self.filename] = (self.zoomMode, value)

def setFitWindow(self, value=True):
    if value:
        self.actions.fitWidth.setChecked(False)
    self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
    self.adjustScale()

def setFitWidth(self, value=True):
    if value:
        self.actions.fitWindow.setChecked(False)
    self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
    self.adjustScale()

def enable_show_cross_line(self, enabled):
    self._config['show_cross_line'] = enabled
    self.actions.show_cross_line.setChecked(enabled)
    self.canvas.set_show_cross_line(enabled)

def brightnessContrast(self, value):
    dialog = BrightnessContrastDialog(utils.img_data_to_pil(self.imageData), self.onNewBrightnessContrast, parent=self)
    brightness, contrast = self.brightnessContrast_values.get(self.filename, (None, None))
    if brightness is not None:
        dialog.slider_brightness.setValue(brightness)
    if contrast is not None:
        dialog.slider_contrast.setValue(contrast)
    dialog.exec()
    brightness = dialog.slider_brightness.value()
    contrast = dialog.slider_contrast.value()
    self.brightnessContrast_values[self.filename] = (brightness, contrast)

def resizeEvent(self, event):
    if self.canvas and (not self.image.isNull()) and (self.zoomMode != self.MANUAL_ZOOM):
        self.adjustScale()
    super(MainWindow, self).resizeEvent(event)

def paintCanvas(self):
    assert not self.image.isNull(), 'cannot paint null image'
    self.canvas.scale = 0.01 * self.zoomWidget.value()
    self.canvas.adjustSize()
    self.canvas.update()

def adjustScale(self, initial=False):
    value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
    value = int(100 * value)
    self.zoomWidget.setValue(value)
    self.zoom_values[self.filename] = (self.zoomMode, value)

def enableSaveImageWithData(self, enabled):
    self._config['store_data'] = enabled
    self.actions.saveWithImageData.setChecked(enabled)

def closeEvent(self, event):
    if not self.mayContinue():
        event.ignore()
    else:
        self.Escape_clicked()
    self.settings.setValue('filename', self.filename if self.filename else '')
    self.settings.setValue('window/size', self.size())
    self.settings.setValue('window/position', self.pos())
    self.settings.setValue('window/state', self.saveState())
    self.settings.setValue('recentFiles', self.recentFiles)

def model_explorer(self):
    """
        Summary:
            Open model explorer dialog to select or download models
        """
    self._config = get_config()
    model_explorer_dialog = utils.ModelExplorerDialog(self, self._config['mute'], notification.PopUp)
    model_explorer_dialog.adjustSize()
    model_explorer_dialog.setMinimumWidth(model_explorer_dialog.table.width() * 1.5)
    model_explorer_dialog.setMinimumHeight(model_explorer_dialog.table.rowHeight(0) * 10)
    model_explorer_dialog.exec()
    if self.helper_first_time_flag:
        try:
            self.intelligenceHelper = Intelligence(self)
        except:
            print('it seems you have a problem with initializing model\ncheck you have at least one model')
            self.helper_first_time_flag = True
        else:
            self.helper_first_time_flag = False
    mathOps.update_saved_models_json(os.getcwd())
    selected_model_name, config, checkpoint = model_explorer_dialog.selected_model
    if selected_model_name != -1:
        self.intelligenceHelper.current_model_name, self.intelligenceHelper.current_mm_model = self.intelligenceHelper.make_mm_model_more(selected_model_name, config, checkpoint)
    self.updateSamControls()

def exportData(self):
    """
        Export data to COCO, MOT, video, and custom exports, depending on the current annotation mode.

        If the current annotation mode is "video", the function prompts the user to select which types of exports to perform
        (COCO, MOT, video, and/or custom exports), and then prompts the user to select the output file path for each export type
        that was selected. The function then exports the data to the selected file paths.

        If the current annotation mode is "img" or "dir", the function prompts the user to select the output file path for a COCO
        export, and then exports the data to the selected file path.

        If an error occurs during the export process, the function displays an error message. Otherwise, the function displays
        a success message.
        """
    try:
        if self.current_annotation_mode == 'video':
            result, coco_radio, mot_radio, video_radio, custom_exports_radio_checked_list = exportData_UI.PopUp()
            if not result:
                return
            json_file_name = f'{self.CURRENT_VIDEO_PATH}/{self.CURRENT_VIDEO_NAME}_tracking_results.json'
            pth = ''
            if video_radio:
                folderDialog = utils.FolderDialog('tracking_results.mp4', 'mp4')
                if folderDialog.exec():
                    pth = self.export_as_video_button_clicked(folderDialog.selectedFiles()[0])
                else:
                    return
            if coco_radio:
                folderDialog = utils.FolderDialog('coco.json', 'json')
                if folderDialog.exec():
                    pth = utils.exportCOCOvid(json_file_name, self.CURRENT_VIDEO_WIDTH, self.CURRENT_VIDEO_HEIGHT, folderDialog.selectedFiles()[0])
                else:
                    return
            if mot_radio:
                folderDialog = utils.FolderDialog('mot.txt', 'txt')
                if folderDialog.exec():
                    pth = utils.exportMOT(json_file_name, folderDialog.selectedFiles()[0])
                else:
                    return
            custom_exports_list_video = [custom_export for custom_export in custom_exports_list if custom_export.mode == 'video']
            if len(custom_exports_radio_checked_list) != 0:
                for i in range(len(custom_exports_radio_checked_list)):
                    if custom_exports_radio_checked_list[i]:
                        folderDialog = utils.FolderDialog(f'{custom_exports_list_video[i].file_name}.{custom_exports_list_video[i].format}', custom_exports_list_video[i].format)
                        if folderDialog.exec():
                            try:
                                pth = custom_exports_list_video[i](json_file_name, self.CURRENT_VIDEO_WIDTH, self.CURRENT_VIDEO_HEIGHT, folderDialog.selectedFiles()[0])
                            except Exception as e:
                                MsgBox.OKmsgBox(f'Error', f'Error: with custom export {custom_exports_list_video[i].button_name}\n check the parameters matches the specified ones in custom_exports.py\n Error Message: {e}', 'critical')
                        else:
                            return
        elif self.current_annotation_mode == 'img' or self.current_annotation_mode == 'dir':
            result, coco_radio, custom_exports_radio_checked_list = exportData_UI.PopUp(mode='image')
            if not result:
                return
            save_path = self.save_path if self.save_path else self.labelFile.filename
            json_paths = utils.parse_img_export(self.target_directory, save_path)
            if coco_radio:
                folderDialog = utils.FolderDialog('coco.json', 'json')
                if folderDialog.exec():
                    pth = utils.exportCOCO(json_paths, folderDialog.selectedFiles()[0])
                else:
                    return
            custom_exports_list_image = [custom_export for custom_export in custom_exports_list if custom_export.mode == 'image']
            if len(custom_exports_radio_checked_list) != 0:
                for i in range(len(custom_exports_radio_checked_list)):
                    if custom_exports_radio_checked_list[i]:
                        folderDialog = utils.FolderDialog(f'{custom_exports_list_image[i].file_name}.{custom_exports_list_image[i].format}', custom_exports_list_image[i].format)
                        if folderDialog.exec():
                            try:
                                pth = custom_exports_list_image[i](json_paths, folderDialog.selectedFiles()[0])
                            except Exception as e:
                                MsgBox.OKmsgBox(f'Error', f'Error: with custom export {custom_exports_list_image[i].button_name}\n check the parameters matches the specified ones in custom_exports.py\n Error Message: {e}', 'critical')
                        else:
                            return
    except Exception as e:
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        msg.setText(f'Error\n {e}')
        msg.setWindowTitle('Export Error')
        print(e)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg.exec()
        return
    else:
        msg = QtWidgets.QMessageBox()
        try:
            if pth not in ['', None, False]:
                msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
                msg.setText(f'Annotations exported successfully to {pth}')
                msg.setWindowTitle('Export Success')
            else:
                msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
                msg.setText(f'Export Failed')
                msg.setWindowTitle('Export Failed')
        except:
            msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            msg.setText(f'Export Failed')
            msg.setWindowTitle('Export Failed')
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg.exec()

def errorMessage(self, title, message):
    msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Critical, title, message)
    msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    return msg_box

def currentPath(self):
    return osp.dirname(str(self.filename)) if self.filename else '.'

def annotate_batch(self):
    images = []
    self._config = get_config()
    notif = [self._config['mute'], self, notification.PopUp]
    for filename in self.imageList:
        images.append(filename)
    if self.multi_model_flag:
        self.intelligenceHelper.get_shapes_of_batch(images, multi_model_flag=True, notif=notif)
    else:
        self.intelligenceHelper.get_shapes_of_batch(images, notif=notif)

def frames_to_skip_slider_changed(self):
    self.FRAMES_TO_SKIP = self.frames_to_skip_slider.value()
    zeros = (2 - int(np.log10(self.FRAMES_TO_SKIP + 0.9))) * '0'
    self.frames_to_skip_label.setText('Jump forward/backward frames: ' + zeros + str(self.FRAMES_TO_SKIP))

def playPauseButtonClicked(self):
    if self.playPauseButton_mode == 'Play':
        self.playPauseButton_mode = 'Pause'
        self.playPauseButton.setShortcut(self._config['shortcuts']['play'])
        self.playPauseButton.setToolTip(f'Play ({self._config['shortcuts']['play']})')
        self.playPauseButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPause))
        self.play_timer = QtCore.QTimer(self)
        self.play_timer.timeout.connect(self.move_frame_by_frame)
        self.play_timer.start(40)
    elif self.playPauseButton_mode == 'Pause':
        self.play_timer.stop()
        self.playPauseButton_mode = 'Play'
        self.playPauseButton.setShortcut(self._config['shortcuts']['play'])
        self.playPauseButton.setToolTip(f'Pause ({self._config['shortcuts']['play']})')
        self.playPauseButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))

def move_frame_by_frame(self):
    QtWidgets.QApplication.processEvents()
    self.main_video_frames_slider.setValue(self.INDEX_OF_CURRENT_FRAME + 1)

def main_video_frames_slider_changed(self):
    if self.current_annotation_mode != 'video':
        return
    if self.sam_model_comboBox.currentIndex() != 0 and self.canvas.SAM_mode != 'finished' and (not self.TrackingMode):
        self.sam_clear_annotation_button_clicked()
        self.sam_buttons_colors('X')
    try:
        x = self.CURRENT_VIDEO_PATH
    except:
        return
    frame_idx = self.main_video_frames_slider.value()
    self.INDEX_OF_CURRENT_FRAME = frame_idx
    self.CAP.set(cv2.CAP_PROP_POS_FRAMES, frame_idx - 1)
    fps = self.CAP.get(cv2.CAP_PROP_FPS)
    zeros = (int(np.log10(self.TOTAL_VIDEO_FRAMES + 0.9)) - int(np.log10(frame_idx + 0.9))) * '0'
    self.main_video_frames_label_1.setText(f'frame {zeros}{frame_idx} / {int(self.TOTAL_VIDEO_FRAMES)}')
    self.frame_time = mathOps.mapFrameToTime(frame_idx, fps)
    frame_text = '%02d:%02d:%02d:%03d' % (self.frame_time[0], self.frame_time[1], self.frame_time[2], self.frame_time[3])
    video_duration = mathOps.mapFrameToTime(self.TOTAL_VIDEO_FRAMES, fps)
    video_duration_text = '%02d:%02d:%02d:%03d' % (video_duration[0], video_duration[1], video_duration[2], video_duration[3])
    final_text = frame_text + ' / ' + video_duration_text
    self.main_video_frames_label_2.setText(f'time {final_text}')
    success, img = self.CAP.read()
    if success:
        frame_array = np.array(img)
        self.loadFramefromVideo(frame_array, frame_idx)
    else:
        pass
    self.frames_to_track_slider.setMaximum(self.TOTAL_VIDEO_FRAMES - self.INDEX_OF_CURRENT_FRAME)

def frames_to_track_slider_changed(self, value):
    self.frames_to_track_input.setText(str(value))
    self.FRAMES_TO_TRACK = self.frames_to_track_slider.value()

def update_gui_after_tracking(self, index):
    if index != self.FRAMES_TO_TRACK - 1:
        self.main_video_frames_slider.setValue(self.INDEX_OF_CURRENT_FRAME + 1)
    QtWidgets.QApplication.processEvents()

def set_video_controls_visibility(self, visible=False):
    self.videoControls.setVisible(visible)
    for widget in self.videoControls.children():
        try:
            widget.setVisible(visible)
        except:
            pass
    self.videoControls_2.setVisible(visible)
    for widget in self.videoControls_2.children():
        try:
            widget.setVisible(visible)
        except:
            pass

def trajectory_length_lineEdit_changed(self):
    try:
        text = self.trajectory_length_lineEdit.text()
        self.CURRENT_ANNOATAION_TRAJECTORIES['length'] = int(text) if text != '' else 1
        self.main_video_frames_slider_changed()
    except:
        pass

def addVideoControls(self):
    self.videoControls = QtWidgets.QToolBar()
    self.videoControls.setMovable(True)
    self.videoControls.setFloatable(True)
    self.videoControls.setObjectName('videoControls')
    self.videoControls.setStyleSheet('QToolBar#videoControls { border: 50px }')
    self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.videoControls)
    self.videoControls_2 = QtWidgets.QToolBar()
    self.videoControls_2.setMovable(True)
    self.videoControls_2.setFloatable(True)
    self.videoControls_2.setObjectName('videoControls_2')
    self.videoControls_2.setStyleSheet('QToolBar#videoControls_2 { border: 50px }')
    self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.videoControls_2)
    self.frames_to_skip_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    self.frames_to_skip_slider.setMinimum(1)
    self.frames_to_skip_slider.setMaximum(100)
    self.frames_to_skip_slider.setValue(3)
    self.frames_to_skip_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
    self.frames_to_skip_slider.setTickInterval(1)
    self.frames_to_skip_slider.setMaximumWidth(250)
    self.frames_to_skip_slider.valueChanged.connect(self.frames_to_skip_slider_changed)
    self.frames_to_skip_label = QtWidgets.QLabel()
    self.frames_to_skip_label.setStyleSheet('QLabel { font-size: 10pt; font-weight: bold; }')
    self.frames_to_skip_slider.setValue(30)
    self.videoControls.addWidget(self.frames_to_skip_label)
    self.videoControls.addWidget(self.frames_to_skip_slider)
    self.previousFrame_button = QtWidgets.QPushButton()
    self.previousFrame_button.setText('<<')
    self.previousFrame_button.setShortcut(self._config['shortcuts']['prev_x'])
    self.previousFrame_button.setToolTip(f'Jump Backward ({self._config['shortcuts']['prev_x']})')
    self.previousFrame_button.clicked.connect(self.previousFrame_buttonClicked)
    self.previous_1_Frame_button = QtWidgets.QPushButton()
    self.previous_1_Frame_button.setText('<')
    self.previous_1_Frame_button.setShortcut(self._config['shortcuts']['prev_1'])
    self.previous_1_Frame_button.setToolTip(f'Previous Frame ({self._config['shortcuts']['prev_1']})')
    self.previous_1_Frame_button.clicked.connect(self.previous_1_Frame_buttonclicked)
    self.playPauseButton = QtWidgets.QPushButton()
    self.playPauseButton_mode = 'Play'
    self.playPauseButton.setShortcut(self._config['shortcuts']['play'])
    self.playPauseButton.setToolTip(f'Play ({self._config['shortcuts']['play']})')
    self.playPauseButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
    self.playPauseButton.setIconSize(QtCore.QSize(22, 22))
    self.playPauseButton.setStyleSheet('QPushButton { margin: 5px;}')
    self.playPauseButton.pressed.connect(self.playPauseButtonClicked)
    self.nextFrame_button = QtWidgets.QPushButton()
    self.nextFrame_button.setText('>>')
    self.nextFrame_button.setShortcut(self._config['shortcuts']['next_x'])
    self.nextFrame_button.setToolTip(f'Jump forward ({self._config['shortcuts']['next_x']})')
    self.nextFrame_button.clicked.connect(self.nextFrame_buttonClicked)
    self.next_1_Frame_button = QtWidgets.QPushButton()
    self.next_1_Frame_button.setText('>')
    self.next_1_Frame_button.setShortcut(self._config['shortcuts']['next_1'])
    self.next_1_Frame_button.setToolTip(f'Next Frame ({self._config['shortcuts']['next_1']})')
    self.next_1_Frame_button.clicked.connect(self.next_1_Frame_buttonClicked)
    self.videoControls.addWidget(self.previousFrame_button)
    self.videoControls.addWidget(self.previous_1_Frame_button)
    self.videoControls.addWidget(self.playPauseButton)
    self.videoControls.addWidget(self.next_1_Frame_button)
    self.videoControls.addWidget(self.nextFrame_button)
    self.main_video_frames_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    self.main_video_frames_slider.setMinimum(1)
    self.main_video_frames_slider.setMaximum(100)
    self.main_video_frames_slider.setValue(2)
    self.main_video_frames_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
    self.main_video_frames_slider.setTickInterval(1)
    self.main_video_frames_slider.setMaximumWidth(1000)
    self.main_video_frames_slider.valueChanged.connect(self.main_video_frames_slider_changed)
    self.main_video_frames_label_1 = QtWidgets.QLabel()
    self.main_video_frames_label_2 = QtWidgets.QLabel()
    self.main_video_frames_label_1.setStyleSheet('QLabel { font-size: 12pt; font-weight: bold; }')
    self.main_video_frames_label_2.setStyleSheet('QLabel { font-size: 12pt; font-weight: bold; }')
    self.videoControls.addWidget(self.main_video_frames_label_1)
    self.videoControls.addWidget(self.main_video_frames_slider)
    self.videoControls.addWidget(self.main_video_frames_label_2)
    self.frames_to_track_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    self.frames_to_track_slider.setMinimum(1)
    self.frames_to_track_slider.setMaximum(100)
    self.frames_to_track_slider.setValue(4)
    self.frames_to_track_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
    self.frames_to_track_slider.setTickInterval(1)
    self.frames_to_track_slider.setMaximumWidth(200)
    self.frames_to_track_slider.valueChanged.connect(self.frames_to_track_slider_changed)
    self.frames_to_track_input = QtWidgets.QLineEdit()
    self.frames_to_track_input.setText('4')
    self.frames_to_track_input.setStyleSheet('QLineEdit { font-size: 10pt; }')
    self.frames_to_track_input.setMaximumWidth(50)
    self.frames_to_track_input.textChanged.connect(self.frames_to_track_input_changed)
    self.frames_to_track_label_before = QtWidgets.QLabel('Track for')
    self.frames_to_track_label_before.setStyleSheet('QLabel { font-size: 10pt; font-weight: bold; }')
    self.frames_to_track_label_after = QtWidgets.QLabel('frames')
    self.frames_to_track_label_after.setStyleSheet('QLabel { font-size: 10pt; font-weight: bold; }')
    self.videoControls_2.addWidget(self.frames_to_track_label_before)
    self.videoControls_2.addWidget(self.frames_to_track_input)
    self.videoControls_2.addWidget(self.frames_to_track_label_after)
    self.videoControls_2.addWidget(self.frames_to_track_slider)
    self.frames_to_track_slider.setValue(10)
    self.track_dropdown = QtWidgets.QComboBox()
    self.track_dropdown.addItems([f'Track for selected frames', 'Track Only assigned objects', 'Track Full Video'])
    self.track_dropdown.setCurrentIndex(0)
    self.track_dropdown.currentIndexChanged.connect(self.track_dropdown_changed)
    self.videoControls_2.addWidget(self.track_dropdown)
    self.start_button = QtWidgets.QPushButton('Start Tracking')
    self.start_button.setIcon(QtGui.QIcon('labelme/icons/start.png'))
    self.start_button.setIconSize(QtCore.QSize(24, 24))
    self.start_button.setStyleSheet(self.buttons_text_style_sheet)
    self.start_button.clicked.connect(self.start_tracking_button_clicked)
    self.videoControls_2.addWidget(self.start_button)
    self.tracking_progress_bar_label = QtWidgets.QLabel()
    self.tracking_progress_bar_label.setStyleSheet('QLabel { font-size: 10pt; font-weight: bold; }')
    self.tracking_progress_bar_label.setText('Tracking Progress')
    self.videoControls_2.addWidget(self.tracking_progress_bar_label)
    self.tracking_progress_bar = QtWidgets.QProgressBar()
    self.tracking_progress_bar.setMaximumWidth(300)
    self.tracking_progress_bar.setMinimum(0)
    self.tracking_progress_bar.setMaximum(100)
    self.tracking_progress_bar.setValue(0)
    self.videoControls_2.addWidget(self.tracking_progress_bar)
    self.track_stop_button = QtWidgets.QPushButton()
    self.track_stop_button.setStyleSheet('QPushButton {font-size: 10pt; margin: 2px 5px; padding: 2px 7px;font-weight: bold; background-color: #FF9090; color: #FFFFFF;} QPushButton:hover {background-color: #FF0000;} QPushButton:disabled {background-color: #7A7A7A;}')
    self.track_stop_button.setStyleSheet('QPushButton {font-size: 10pt; margin: 2px 5px; padding: 2px 7px;font-weight: bold; background-color: #FF0000; color: #FFFFFF;} QPushButton:hover {background-color: #FE4242;} QPushButton:disabled {background-color: #7A7A7A;}')
    self.track_stop_button.setText('Stop Tracking')
    self.track_stop_button.setIcon(QtGui.QIcon('labelme/icons/stop.png'))
    self.track_stop_button.setIconSize(QtCore.QSize(24, 24))
    self.track_stop_button.setToolTip(f'Stop Tracking ({self._config['shortcuts']['stop']})')
    self.track_stop_button.pressed.connect(self.Escape_clicked)
    self.videoControls_2.addWidget(self.track_stop_button)
    self.bbox_checkBox = QtWidgets.QCheckBox()
    self.bbox_checkBox.setText('bbox')
    self.bbox_checkBox.setChecked(True)
    self.bbox_checkBox.stateChanged.connect(self.bbox_checkBox_changed)
    self.id_checkBox = QtWidgets.QCheckBox()
    self.id_checkBox.setText('id')
    self.id_checkBox.setChecked(True)
    self.id_checkBox.stateChanged.connect(self.id_checkBox_changed)
    self.class_checkBox = QtWidgets.QCheckBox()
    self.class_checkBox.setText('class')
    self.class_checkBox.setChecked(True)
    self.class_checkBox.stateChanged.connect(self.class_checkBox_changed)
    self.conf_checkBox = QtWidgets.QCheckBox()
    self.conf_checkBox.setText('confidence')
    self.conf_checkBox.setChecked(True)
    self.conf_checkBox.stateChanged.connect(self.conf_checkBox_changed)
    self.mask_checkBox = QtWidgets.QCheckBox()
    self.mask_checkBox.setText('mask')
    self.mask_checkBox.setChecked(True)
    self.mask_checkBox.stateChanged.connect(self.mask_checkBox_changed)
    self.traj_checkBox = QtWidgets.QCheckBox()
    self.traj_checkBox.setText('trajectories')
    self.traj_checkBox.setChecked(False)
    self.traj_checkBox.stateChanged.connect(self.traj_checkBox_changed)
    self.trajectory_length_lineEdit = QtWidgets.QLineEdit()
    self.trajectory_length_lineEdit.setText(str(30))
    self.trajectory_length_lineEdit.setMaximumWidth(50)
    self.trajectory_length_lineEdit.editingFinished.connect(self.trajectory_length_lineEdit_changed)
    self.polygons_visable_checkBox = QtWidgets.QCheckBox()
    self.polygons_visable_checkBox.setText('show polygons')
    self.polygons_visable_checkBox.setChecked(True)
    self.polygons_visable_checkBox.stateChanged.connect(self.polygons_visable_checkBox_changed)
    self.vis_options = [self.id_checkBox, self.class_checkBox, self.bbox_checkBox, self.mask_checkBox, self.polygons_visable_checkBox, self.traj_checkBox, self.trajectory_length_lineEdit, self.conf_checkBox]
    self.vis_widget.setLayout(QtWidgets.QGridLayout())
    self.vis_widget.layout().setContentsMargins(10, 10, 25, 10)
    self.vis_widget.layout().addWidget(self.id_checkBox, 0, 0)
    self.vis_widget.layout().addWidget(self.class_checkBox, 0, 1)
    self.vis_widget.layout().addWidget(self.bbox_checkBox, 1, 0)
    self.vis_widget.layout().addWidget(self.mask_checkBox, 1, 1)
    self.vis_widget.layout().addWidget(self.traj_checkBox, 2, 0)
    self.vis_widget.layout().addWidget(self.trajectory_length_lineEdit, 2, 1)
    self.vis_widget.layout().addWidget(self.polygons_visable_checkBox, 3, 0)
    self.vis_widget.layout().addWidget(self.conf_checkBox, 3, 1)
    for option in self.vis_options:
        option.setEnabled(False)
    self.update_current_frame_annotation_button = QtWidgets.QPushButton()
    self.update_current_frame_annotation_button.setStyleSheet(self.buttons_text_style_sheet)
    self.update_current_frame_annotation_button.setText('Apply Changes')
    self.update_current_frame_annotation_button.setIcon(QtGui.QIcon('labelme/icons/done.png'))
    self.update_current_frame_annotation_button.setIconSize(QtCore.QSize(24, 24))
    self.update_current_frame_annotation_button.setShortcut(self._config['shortcuts']['update_frame'])
    self.update_current_frame_annotation_button.setToolTip(f'Apply changes on current frame ({self._config['shortcuts']['update_frame']})')
    self.update_current_frame_annotation_button.clicked.connect(self.update_current_frame_annotation_button_clicked)
    self.videoControls_2.addWidget(self.update_current_frame_annotation_button)
    self.clear_video_annotations_button = QtWidgets.QPushButton()
    self.clear_video_annotations_button.setStyleSheet(self.buttons_text_style_sheet)
    self.clear_video_annotations_button.setText('Clear All')
    self.clear_video_annotations_button.setIcon(QtGui.QIcon('labelme/icons/clear.png'))
    self.clear_video_annotations_button.setIconSize(QtCore.QSize(24, 24))
    self.clear_video_annotations_button.setShortcut(self._config['shortcuts']['clear_annotations'])
    self.clear_video_annotations_button.setToolTip(f'Clears Annotations from all frames ({self._config['shortcuts']['clear_annotations']})')
    self.clear_video_annotations_button.clicked.connect(self.clear_video_annotations_button_clicked)
    self.videoControls_2.addWidget(self.clear_video_annotations_button)
    self.set_video_controls_visibility(False)

def set_sam_toolbar_enable(self, setEnabled):
    self.sam_add_point_button.setEnabled(setEnabled)
    self.sam_remove_point_button.setEnabled(setEnabled)
    self.sam_select_rect_button.setEnabled(setEnabled)
    self.sam_clear_annotation_button.setEnabled(setEnabled)
    self.sam_finish_annotation_button.setEnabled(setEnabled)

def set_sam_toolbar_visibility(self, visible=False):
    if not visible:
        try:
            self.sam_clear_annotation_button_clicked()
            self.sam_buttons_colors('X')
        except:
            pass
    self.sam_toolbar.setVisible(visible)
    for widget in self.sam_toolbar.children():
        try:
            widget.setVisible(visible)
        except:
            pass

def addSamControls(self):
    self.sam_toolbar = QtWidgets.QToolBar()
    self.sam_toolbar.setMovable(True)
    self.sam_toolbar.setFloatable(True)
    self.sam_toolbar.setObjectName('sam_toolbar')
    self.sam_toolbar.setStyleSheet('QToolBar#videoControls { border: 50px }')
    self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.sam_toolbar)
    self.sam_model_label = QtWidgets.QLabel()
    self.sam_model_label.setText('SAM Model')
    self.sam_model_label.setStyleSheet('QLabel { font-size: 10pt; font-weight: bold; }')
    self.sam_toolbar.addWidget(self.sam_model_label)
    self.sam_model_comboBox = QtWidgets.QComboBox()
    self.sam_model_comboBox.setAccessibleName('sam_model_comboBox')
    self.sam_model_comboBox.addItem('Select Model (SAM disabled)')
    self.sam_model_comboBox.addItems(self.sam_models())
    self.sam_model_comboBox.currentIndexChanged.connect(self.sam_model_comboBox_changed)
    self.sam_toolbar.addWidget(self.sam_model_comboBox)
    self.sam_add_point_button = QtWidgets.QPushButton()
    self.sam_add_point_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
    self.sam_add_point_button.setText('Add')
    self.sam_add_point_button.setIcon(QtGui.QIcon('labelme/icons/add.png'))
    self.sam_add_point_button.setIconSize(QtCore.QSize(24, 24))
    self.sam_add_point_button.setToolTip(f'Add point ({self._config['shortcuts']['SAM_add_point']})')
    self.sam_add_point_button.setShortcut(self._config['shortcuts']['SAM_add_point'])
    self.sam_add_point_button.clicked.connect(self.sam_add_point_button_clicked)
    self.sam_toolbar.addWidget(self.sam_add_point_button)
    self.sam_remove_point_button = QtWidgets.QPushButton()
    self.sam_remove_point_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
    self.sam_remove_point_button.setText('Remove')
    self.sam_remove_point_button.setIcon(QtGui.QIcon('labelme/icons/remove.png'))
    self.sam_remove_point_button.setIconSize(QtCore.QSize(24, 24))
    self.sam_remove_point_button.setToolTip(f'Remove Point ({self._config['shortcuts']['SAM_remove_point']})')
    self.sam_remove_point_button.setShortcut(self._config['shortcuts']['SAM_remove_point'])
    self.sam_remove_point_button.clicked.connect(self.sam_remove_point_button_clicked)
    self.sam_toolbar.addWidget(self.sam_remove_point_button)
    self.sam_select_rect_button = QtWidgets.QPushButton()
    self.sam_select_rect_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
    self.sam_select_rect_button.setText('Box')
    self.sam_select_rect_button.setIcon(QtGui.QIcon('labelme/icons/bbox.png'))
    self.sam_select_rect_button.setIconSize(QtCore.QSize(24, 24))
    self.sam_select_rect_button.setToolTip(f'Add Box ({self._config['shortcuts']['SAM_select_rect']})')
    self.sam_select_rect_button.setShortcut(self._config['shortcuts']['SAM_select_rect'])
    self.sam_select_rect_button.clicked.connect(self.sam_select_rect_button_clicked)
    self.sam_toolbar.addWidget(self.sam_select_rect_button)
    self.sam_clear_annotation_button = QtWidgets.QPushButton()
    self.sam_clear_annotation_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
    self.sam_clear_annotation_button.setText('Clear')
    self.sam_clear_annotation_button.setIcon(QtGui.QIcon('labelme/icons/clear.png'))
    self.sam_clear_annotation_button.setIconSize(QtCore.QSize(24, 24))
    self.sam_clear_annotation_button.setShortcut(self._config['shortcuts']['SAM_clear'])
    self.sam_clear_annotation_button.setToolTip(f'Clear points and boxes ({self._config['shortcuts']['SAM_clear']})')
    self.sam_clear_annotation_button.clicked.connect(self.sam_clear_annotation_button_clicked)
    self.sam_toolbar.addWidget(self.sam_clear_annotation_button)
    self.sam_finish_annotation_button = QtWidgets.QPushButton()
    self.sam_finish_annotation_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
    self.sam_finish_annotation_button.setText('Finish')
    self.sam_finish_annotation_button.setIcon(QtGui.QIcon('labelme/icons/done.png'))
    self.sam_finish_annotation_button.setIconSize(QtCore.QSize(24, 24))
    self.sam_finish_annotation_button.clicked.connect(self.sam_finish_annotation_button_clicked)
    self.sam_finish_annotation_button.setToolTip(f'Finish Annotation ({self._config['shortcuts']['SAM_finish_annotation']} or ENTER)')
    self.sam_finish_annotation_button.setShortcut(self._config['shortcuts']['SAM_finish_annotation'])
    self.sam_toolbar.addWidget(self.sam_finish_annotation_button)
    self.sam_close_button = QtWidgets.QPushButton()
    self.sam_close_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
    self.sam_close_button.setText('Manual')
    self.sam_close_button.setIcon(QtGui.QIcon('labelme/icons/objects.png'))
    self.sam_close_button.setIconSize(QtCore.QSize(24, 24))
    self.sam_close_button.setShortcut(self._config['shortcuts']['SAM_RESET'])
    self.sam_close_button.setToolTip(f'Return to Manual Mode ({self._config['shortcuts']['SAM_RESET']} or ESC)')
    self.sam_close_button.clicked.connect(self.sam_reset_button_clicked)
    self.sam_toolbar.addWidget(self.sam_close_button)
    self.sam_enhance_annotation_button = QtWidgets.QPushButton()
    self.sam_enhance_annotation_button.setAccessibleName('sam_enhance_annotation_button')
    self.sam_enhance_annotation_button.setStyleSheet('QPushButton { font-size: 10pt; font-weight: bold; }')
    self.sam_enhance_annotation_button.setText('Enhance Polygons')
    self.sam_enhance_annotation_button.setIcon(QtGui.QIcon('labelme/icons/SAM.png'))
    self.sam_enhance_annotation_button.setIconSize(QtCore.QSize(24, 24))
    self.sam_enhance_annotation_button.setShortcut(self._config['shortcuts']['SAM_enhance'])
    self.sam_enhance_annotation_button.setToolTip(f'Enhance Selected Polygons with SAM ({self._config['shortcuts']['SAM_enhance']})')
    self.sam_enhance_annotation_button.clicked.connect(self.sam_enhance_annotation_button_clicked)
    self.sam_toolbar.addWidget(self.sam_enhance_annotation_button)
    self.set_sam_toolbar_enable(False)
    self.sam_buttons_colors('x')

def updateSamControls(self):
    self.sam_model_comboBox.clear()
    self.sam_model_comboBox.addItem('Select Model (SAM disabled)')
    self.sam_model_comboBox.addItems(self.sam_models())

def set_sam_toolbar_colors(self, mode):
    red, green, blue, trans = ('#2D7CFA;', '#2D7CFA;', '#2D7CFA;', '#4B515A;')
    hover_const = 'QPushButton::hover { background-color : '
    disabled_const = 'QPushButton:disabled { color : #7A7A7A} '
    style_sheet_const = 'QPushButton { font-size: 10pt; font-weight: bold; color: #ffffff; background-color: '
    [add_style, add_hover] = [green, green] if mode == 'add' else [trans, green]
    [remove_style, remove_hover] = [red, red] if mode == 'remove' else [trans, red]
    [rect_style, rect_hover] = [green, green] if mode == 'rect' else [trans, green]
    [clear_style, clear_hover] = [red, red] if mode == 'clear' else [trans, red]
    [finish_style, finish_hover] = [blue, blue] if mode == 'finish' else [trans, blue]
    [replace_style, replace_hover] = [blue, blue] if mode == 'replace' else [trans, blue]
    self.sam_add_point_button.setStyleSheet(style_sheet_const + add_style + ';}' + hover_const + add_hover + ';}' + disabled_const)
    self.sam_remove_point_button.setStyleSheet(style_sheet_const + remove_style + ';}' + hover_const + remove_hover + ';}' + disabled_const)
    self.sam_select_rect_button.setStyleSheet(style_sheet_const + rect_style + ';}' + hover_const + rect_hover + ';}' + disabled_const)
    self.sam_clear_annotation_button.setStyleSheet(style_sheet_const + clear_style + ';}' + hover_const + clear_hover + ';}' + disabled_const)
    self.sam_finish_annotation_button.setStyleSheet(style_sheet_const + finish_style + ';}' + hover_const + finish_hover + ';}' + disabled_const)
    self.sam_enhance_annotation_button.setStyleSheet(style_sheet_const + replace_style + ';}' + hover_const + replace_hover + ';}' + disabled_const)

class Intelligence:

    def __init__(self, parent):
        self.reader = models_inference()
        self.parent = parent
        self.conf_threshold = 0.3
        self.iou_threshold = 0.5
        with open('labelme/config/default_config.yaml') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        self.default_classes = self.config['default_classes']
        try:
            self.selectedclasses = {}
            for class_ in self.default_classes:
                if class_ in coco_classes:
                    index = coco_classes.index(class_)
                    self.selectedclasses[index] = class_
        except:
            self.selectedclasses = {i: class_ for i, class_ in enumerate(coco_classes)}
            print('error in loading the default classes from the config file, so we will use all the coco classes')
        self.selectedmodels = []
        self.current_model_name, self.current_mm_model = self.make_mm_model('')

    @torch.no_grad()
    def make_mm_model(self, selected_model_name):
        try:
            with open('saved_models.json') as json_file:
                data = json.load(json_file)
                if selected_model_name == '':
                    selected_model_name = list(data.keys())[0]
                    config = data[selected_model_name]['config']
                    checkpoint = data[selected_model_name]['checkpoint']
                else:
                    config = data[selected_model_name]['config']
                    checkpoint = data[selected_model_name]['checkpoint']
                print(f'selected model : {selected_model_name} \nconfig : {config}\ncheckpoint : {checkpoint} \n')
        except Exception as e:
            OKmsgBox('Error', f'Error in loading the model\n{e}', 'critical')
            return
        torch.cuda.empty_cache()
        if 'YOLOv8' in selected_model_name:
            model = YOLO(checkpoint)
            model.fuse()
            return (selected_model_name, model)
        try:
            print(f'From the working one: {config}')
            model = init_detector(config, checkpoint, device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
        except:
            print('Error in loading the model, please check if the config and checkpoint files do exist')
        return (selected_model_name, model)

    @torch.no_grad()
    def make_mm_model_more(self, selected_model_name, config, checkpoint):
        torch.cuda.empty_cache()
        print(f'Selected model is {selected_model_name}\n and config is {config}\n and checkpoint is {checkpoint}')
        if 'YOLOv8' in selected_model_name:
            try:
                model = YOLO(checkpoint)
                model.fuse()
                return (selected_model_name, model)
            except Exception as e:
                OKmsgBox('Error', f'Error in loading the model\n{e}', 'critical')
                return
        else:
            try:
                print(f'From the new one: {config}')
                model = init_detector(config, checkpoint, device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
            except Exception as e:
                OKmsgBox
                OKmsgBox('Error', f'Error in loading the model\n{e}', 'critical')
                return
            return (selected_model_name, model)

    def get_shapes_of_one(self, image, img_array_flag=False, multi_model_flag=False):
        start_time = time.time()
        if multi_model_flag:
            if len(self.selectedmodels) == 0:
                return []
            self.reader.annotating_models.clear()
            for model_name in self.selectedmodels:
                self.current_model_name, self.current_mm_model = self.make_mm_model(model_name)
                if img_array_flag:
                    results0, results1 = self.reader.decode_file(img=image, model=self.current_mm_model, classdict=self.selectedclasses, threshold=self.conf_threshold, img_array_flag=True)
                else:
                    results0, results1 = self.reader.decode_file(img=image, model=self.current_mm_model, classdict=self.selectedclasses, threshold=self.conf_threshold)
                self.reader.annotating_models[model_name] = [results0, results1]
                end_time = time.time()
                print(f'Time taken to annoatate img on {self.current_model_name}: {int((end_time - start_time) * 1000)} ms' + '\n')
            print('merging masks')
            results0, results1 = self.reader.merge_masks()
            results = self.reader.polegonise(results0, results1, classdict=self.selectedclasses, threshold=self.conf_threshold)['results']
        else:
            if img_array_flag:
                results = self.reader.decode_file(img=image, model=self.current_mm_model, classdict=self.selectedclasses, threshold=self.conf_threshold, img_array_flag=True)
                if isinstance(results, tuple):
                    results = self.reader.polegonise(results[0], results[1], classdict=self.selectedclasses, threshold=self.conf_threshold)['results']
                else:
                    results = results['results']
            else:
                results = self.reader.decode_file(img=image, model=self.current_mm_model, classdict=self.selectedclasses, threshold=self.conf_threshold)
                if isinstance(results, tuple):
                    results = self.reader.polegonise(results[0], results[1], classdict=self.selectedclasses, threshold=self.conf_threshold)['results']
                else:
                    results = results['results']
            end_time = time.time()
            print(f'Time taken to annoatate img on {self.current_model_name}: {int((end_time - start_time) * 1000)} ms')
        shapes = []
        for result in results:
            shape = {}
            shape['label'] = result['class']
            shape['content'] = result['confidence']
            shape['group_id'] = None
            shape['shape_type'] = 'polygon'
            shape['bbox'] = mathOps.get_bbox_xyxy(result['seg'])
            shape['flags'] = {}
            shape['other_data'] = {}
            shape['points'] = [item for sublist in result['seg'] for item in sublist]
            shapes.append(shape)
            shapes, boxes, confidences, class_ids, segments = mathOps.OURnms_confidenceBased(shapes, self.iou_threshold)
        return shapes

    def get_shapes_of_batch(self, images, multi_model_flag=False, notif=[]):
        self.pd = self.startOperationDialog()
        self.thread = IntelligenceWorker(self.parent, images, self, multi_model_flag)
        self.thread.sinOut.connect(self.updateDialog)
        self.thread.start()
        self.notif = notif

    def updateDialog(self, completed, total):
        progress = int(completed / total * 100)
        self.pd.setLabelText(str(completed) + '/' + str(total))
        self.pd.setValue(progress)
        if completed == total:
            self.onProgressDialogCanceledOrCompleted()

    def startOperationDialog(self):
        self.operationCanceled = False
        pd1 = QtWidgets.QProgressDialog('Progress', 'Cancel', 0, 100, self.parent)
        pd1.setLabelText('Progress')
        pd1.setCancelButtonText('Cancel')
        pd1.setRange(0, 100)
        pd1.setValue(0)
        pd1.setMinimumDuration(0)
        pd1.show()
        pd1.canceled.connect(self.onProgressDialogCanceledOrCompleted)
        return pd1

    def onProgressDialogCanceledOrCompleted(self):
        try:
            if not self.notif[0] and (not self.notif[1].isActiveWindow()):
                self.notif[2]('Batch Annotation Completed')
        except:
            print('Error in batch mode notification')
        self.operationCanceled = True
        if self.parent.lastOpenDir and osp.exists(self.parent.lastOpenDir):
            self.parent.importDirImages(self.parent.lastOpenDir)
        else:
            self.parent.loadFile(self.parent.filename)

    def clear_annotating_models(self):
        self.reader.annotating_models.clear()

    def saveLabelFile(self, filename, detectedShapes):
        lf = LabelFile()

        def format_shape(s):
            data = s.other_data.copy()
            data.update(dict(label=s.label.encode('utf-8') if PY2 else s.label, points=mathOps.flattener(s.points), bbox=s.bbox, group_id=s.group_id, content=s.content, shape_type=s.shape_type, flags=s.flags))
            return data
        shapes = [format_shape(item) for item in detectedShapes]
        imageData = LabelFile.load_image_file(filename)
        image = QtGui.QImage.fromData(imageData)
        if osp.dirname(filename) and (not osp.exists(osp.dirname(filename))):
            os.makedirs(osp.dirname(filename))
        json_name = osp.splitext(filename)[0] + '.json'
        imagePath = osp.relpath(filename, osp.dirname(json_name))
        lf.save(filename=json_name, shapes=shapes, imagePath=imagePath, imageData=imageData, imageHeight=image.height(), imageWidth=image.width(), otherData={}, flags={})

def get_shapes_of_batch(self, images, multi_model_flag=False, notif=[]):
    self.pd = self.startOperationDialog()
    self.thread = IntelligenceWorker(self.parent, images, self, multi_model_flag)
    self.thread.sinOut.connect(self.updateDialog)
    self.thread.start()
    self.notif = notif

def updateDialog(self, completed, total):
    progress = int(completed / total * 100)
    self.pd.setLabelText(str(completed) + '/' + str(total))
    self.pd.setValue(progress)
    if completed == total:
        self.onProgressDialogCanceledOrCompleted()

def startOperationDialog(self):
    self.operationCanceled = False
    pd1 = QtWidgets.QProgressDialog('Progress', 'Cancel', 0, 100, self.parent)
    pd1.setLabelText('Progress')
    pd1.setCancelButtonText('Cancel')
    pd1.setRange(0, 100)
    pd1.setValue(0)
    pd1.setMinimumDuration(0)
    pd1.show()
    pd1.canceled.connect(self.onProgressDialogCanceledOrCompleted)
    return pd1

def PopUp():
    """

    Description:
    This function displays a dialog box with information about the runtime data of the system, including GPU and RAM stats.

    Parameters:
    This function takes no parameters.

    Returns:
    This function does not return anything.

    Libraries:
    This function requires the following libraries to be installed:
    - PyQt6
    - psutil
    - torch
    """
    dialog = QDialog()
    dialog.setWindowTitle('Runtime data')
    dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)
    title_font = QFont()
    title_font.setPointSize(12)
    title_font.setBold(True)
    normal_font = QFont()
    normal_font.setPointSize(10)
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        gpu_title_label = QLabel('Device Stats')
        gpu_title_label.setFont(title_font)
        layout.addWidget(gpu_title_label)
        gpu_name_label = QLabel(f'GPU Name: {device_name}')
        gpu_name_label.setFont(normal_font)
        layout.addWidget(gpu_name_label)
        total_vram = round(torch.cuda.get_device_properties(0).total_memory / 1024 ** 3, 2)
        used_vram = round(torch.cuda.memory_allocated(0) / 1024 ** 3, 2)
        gpu_vram_label = QLabel(f'Total GPU VRAM: {total_vram} GB\nUsed: {used_vram} GB')
        gpu_vram_label.setFont(normal_font)
        layout.addWidget(gpu_vram_label)
    else:
        cpu_label = QLabel('DLTA-AI is Using CPU')
        cpu_label.setFont(title_font)
        layout.addWidget(cpu_label)
    ram_title_label = QLabel('RAM Stats')
    ram_title_label.setFont(title_font)
    layout.addWidget(ram_title_label)
    total_ram = round(psutil.virtual_memory().total / 1024 ** 3, 2)
    used_ram = round(psutil.virtual_memory().used / 1024 ** 3, 2)
    ram_label = QLabel(f'Total RAM: {total_ram} GB\nUsed: {used_ram} GB')
    ram_label.setFont(normal_font)
    layout.addWidget(ram_label)
    dialog.exec()

def OKmsgBox(title, text, type='info', turnResult=False):
    """
    Show a message box.

    Args:
        title (str): The title of the message box.
        text (str): The text of the message box.
        type (str, optional): The type of the message box. Can be "info", "warning", or "critical". Defaults to "info".

    Returns:
        int: The result of the message box. This will be the value of the button clicked by the user.
    """
    msgBox = QtWidgets.QMessageBox()
    if type == 'info':
        msgBox.setIcon(QtWidgets.QMessageBox.Icon.Information)
    elif type == 'warning':
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
    elif type == 'critical':
        msgBox.setIcon(QtWidgets.QMessageBox.Icon.Critical)
    msgBox.setText(text)
    msgBox.setWindowTitle(title)
    if turnResult:
        msgBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Ok)
    else:
        msgBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    msgBox.exec()
    return msgBox.result()

def PopUp():
    """
    Displays a dialog box for selecting and editing keyboard shortcuts for the application.

    Parameters:
    None

    Returns:
    None
    """
    shortcuts = {}
    with open('labelme/config/default_config.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        shortcuts = config.get('shortcuts', {})
    shortcuts_names_encode = {name: name.lower().capitalize().replace('_', ' ').replace('Sam', 'SAM').replace('sam', 'SAM') for name in shortcuts.keys()}
    shortcuts_names_decode = {value: key for key, value in shortcuts_names_encode.items()}
    shortcuts = {shortcuts_names_encode[key]: value for key, value in shortcuts.items()}
    shortcut_table = QtWidgets.QTableWidget()
    shortcut_table.setColumnCount(2)
    shortcut_table.setHorizontalHeaderLabels(['Function', 'Shortcut'])
    shortcut_table.setRowCount(len(shortcuts))
    shortcut_table.verticalHeader().setVisible(False)
    row = 0
    for name, key in shortcuts.items():
        name_item = QtWidgets.QTableWidgetItem(name)
        shortcut_item = QtWidgets.QTableWidgetItem(key)
        shortcut_table.setItem(row, 0, name_item)
        shortcut_table.setItem(row, 1, shortcut_item)
        row += 1

    def on_shortcut_table_clicked(item):
        row = item.row()
        name_item = shortcut_table.item(row, 0)
        name = name_item.text()
        current_key = shortcuts[name]
        key_edit = QtWidgets.QKeySequenceEdit(QtGui.QKeySequence(current_key))
        key_edit.setWindowTitle(f'Edit Shortcut for {name}')
        key_edit_label = QtWidgets.QLabel('Enter new shortcut for ' + name)
        dialog = QtWidgets.QDialog()
        dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        dialog.setWindowTitle('Shortcut Selector')
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(key_edit_label)
        layout.addWidget(key_edit)
        ok_button = QtWidgets.QPushButton('OK')
        ok_button.clicked.connect(dialog.accept)
        null_hint_label = QtWidgets.QLabel("to remove shortcut, press 'Ctrl' only then click 'OK")
        layout.addWidget(ok_button)
        layout.addWidget(null_hint_label)
        dialog.setLayout(layout)
        if dialog.exec():
            key = key_edit.keySequence().toString(QtGui.QKeySequence.SequenceFormat.NativeText)
            if key in shortcuts.values() and list(shortcuts.keys())[list(shortcuts.values()).index(key)] != name:
                conflicting_shortcut = list(shortcuts.keys())[list(shortcuts.values()).index(key)]
                QtWidgets.QMessageBox.warning(None, 'Error', f'{key} is already assigned to {conflicting_shortcut}.')
            else:
                if key == '':
                    key = None
                shortcuts[name] = key
                shortcut_table.item(row, 1).setText(key)

    def write_shortcuts_to_ui(config):
        shortcuts = config.get('shortcuts', {})
        shortcuts_names_encode = {name: name.lower().capitalize().replace('_', ' ').replace('Sam', 'SAM').replace('sam', 'SAM') for name in shortcuts.keys()}
        shortcuts = {shortcuts_names_encode[key]: value for key, value in shortcuts.items()}
        row = 0
        for name, key in shortcuts.items():
            name_item = QtWidgets.QTableWidgetItem(name)
            shortcut_item = QtWidgets.QTableWidgetItem(key)
            shortcut_table.setItem(row, 0, name_item)
            shortcut_table.setItem(row, 1, shortcut_item)
            row += 1

    def on_reset_button_clicked():
        with open('labelme/config/default_config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        write_shortcuts_to_ui(config)

    def on_restore_button_clicked():
        with open('labelme/config/default_config_base.yaml', 'r') as f:
            configBase = yaml.load(f, Loader=yaml.FullLoader)
        with open('labelme/config/default_config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        config['shortcuts'] = configBase['shortcuts']
        write_shortcuts_to_ui(config)
    shortcut_table.itemClicked.connect(on_shortcut_table_clicked)
    dialog = QtWidgets.QDialog()
    dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
    dialog.setWindowTitle('Shortcuts')
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(shortcut_table)
    ok_button = QtWidgets.QPushButton('OK')
    ok_button.clicked.connect(dialog.accept)
    layout.addWidget(ok_button)
    reset_button = QtWidgets.QPushButton('Reset')
    reset_button.clicked.connect(on_reset_button_clicked)
    layout.addWidget(reset_button)
    restore_button = QtWidgets.QPushButton('Restore Default Shortcuts')
    restore_button.clicked.connect(on_restore_button_clicked)
    layout.addWidget(restore_button)
    note_label = QtWidgets.QLabel('Shortcuts will be updated after restarting the app.')
    layout.addWidget(note_label)
    dialog.setLayout(layout)
    dialog.setMinimumWidth(shortcut_table.sizeHintForColumn(0) + shortcut_table.sizeHintForColumn(1) + 55)
    dialog.setMinimumHeight(shortcut_table.rowHeight(0) * 10 + 50)
    dialog.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
    dialog.exec()
    shortcuts = {}
    for row in range(shortcut_table.rowCount()):
        name_item = shortcut_table.item(row, 0)
        name = name_item.text()
        shortcut_item = shortcut_table.item(row, 1)
        shortcut = shortcut_item.text()
        shortcuts[name] = shortcut if shortcut != '' else None
    shortcuts = {shortcuts_names_decode[key]: value for key, value in shortcuts.items()}
    with open('labelme/config/default_config.yaml', 'w') as f:
        config['shortcuts'] = shortcuts
        yaml.dump(config, f)

def on_shortcut_table_clicked(item):
    row = item.row()
    name_item = shortcut_table.item(row, 0)
    name = name_item.text()
    current_key = shortcuts[name]
    key_edit = QtWidgets.QKeySequenceEdit(QtGui.QKeySequence(current_key))
    key_edit.setWindowTitle(f'Edit Shortcut for {name}')
    key_edit_label = QtWidgets.QLabel('Enter new shortcut for ' + name)
    dialog = QtWidgets.QDialog()
    dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
    dialog.setWindowTitle('Shortcut Selector')
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(key_edit_label)
    layout.addWidget(key_edit)
    ok_button = QtWidgets.QPushButton('OK')
    ok_button.clicked.connect(dialog.accept)
    null_hint_label = QtWidgets.QLabel("to remove shortcut, press 'Ctrl' only then click 'OK")
    layout.addWidget(ok_button)
    layout.addWidget(null_hint_label)
    dialog.setLayout(layout)
    if dialog.exec():
        key = key_edit.keySequence().toString(QtGui.QKeySequence.SequenceFormat.NativeText)
        if key in shortcuts.values() and list(shortcuts.keys())[list(shortcuts.values()).index(key)] != name:
            conflicting_shortcut = list(shortcuts.keys())[list(shortcuts.values()).index(key)]
            QtWidgets.QMessageBox.warning(None, 'Error', f'{key} is already assigned to {conflicting_shortcut}.')
        else:
            if key == '':
                key = None
            shortcuts[name] = key
            shortcut_table.item(row, 1).setText(key)

def PopUp(text):
    """
    Sends a desktop notification with the given text.

    Args:
        text (str): The text to display in the notification.

    Returns:
        None
    """
    try:
        from notifypy import Notify
        notification = Notify(default_notification_title='DLTA-AI')
        notification.message = text
        print(os.getcwd())
        notification.icon = 'labelme/icons/icon.ico'
        notification.send(block=False)
    except Exception as e:
        print(e)
        print('please install notifypy to get desktop notifications')

def editLabel_idChanged_UI(config, old_group_id, new_group_id, id_frames_rec, INDEX_OF_CURRENT_FRAME):
    idChanged = old_group_id != new_group_id
    if not idChanged:
        result = QtWidgets.QDialog.DialogCode.Accepted
        only_this_frame = False
        duplicates = False
        return (result, config, only_this_frame, duplicates)
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle('Choose Edit Options')
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.resize(250, 100)
    layout = QtWidgets.QVBoxLayout()
    label = QtWidgets.QLabel('Choose Edit Options')
    layout.addWidget(label)
    only = QtWidgets.QRadioButton('Edit only this frame')
    all = QtWidgets.QRadioButton('Edit all frames with this ID')
    if config['EditDefault'] == 'Edit only this frame':
        only.toggle()
    if config['EditDefault'] == 'Edit all frames with this ID':
        all.toggle()
    only.toggled.connect(lambda: config.update({'EditDefault': 'Edit only this frame'}))
    all.toggled.connect(lambda: config.update({'EditDefault': 'Edit all frames with this ID'}))
    layout.addWidget(only)
    layout.addWidget(all)
    buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
    buttonBox.accepted.connect(dialog.accept)
    layout.addWidget(buttonBox)
    dialog.setLayout(layout)
    result = dialog.exec()
    only_this_frame = config['EditDefault'] == 'Edit only this frame'
    duplicates = check_duplicates_editLabel(id_frames_rec, old_group_id, new_group_id, only_this_frame, idChanged, INDEX_OF_CURRENT_FRAME)
    return (result, config, only_this_frame, duplicates)

def editLabel_handle_data(currFrame, listObj, trajectories, id_frames_rec, idChanged, only_this_frame, shape, old_group_id, new_group_id=None):
    """
    Summary:
        Handle id change in edit label.
        Check if the id is changed or not.
        If the id is changed, transfer the frames from the old id to the new id.
            two cases:
                1- only_this_frame: transfer only the current frame
                2- not only_this_frame: transfer all the frames
        If the id is not changed, update the id in the current frame.
        
    Args:
        currFrame: the current frame index
        listObj: a list of objects (each object is a dictionary of a frame with keys (frame_idx, frame_data))
        trajectories: a dictionary of trajectories
        id_frames_rec: a dictionary of id frames records
        idChanged: a flag to indicate if the id is changed or not
        only_this_frame: a flag to indicate if the id is changed only in the current frame or in all frames
        shape: the shape to update
        old_group_id: the old id
        new_group_id: the new id, if None then the old id is used (no id change)
        
    Returns:
        id_frames_rec: a dictionary of id frames records
        trajectories: a dictionary of trajectories
        listObj: a list of objects (each object is a dictionary of a frame with keys (frame_idx, frame_data))
    """
    if new_group_id is None or not idChanged:
        new_group_id = old_group_id
    if not idChanged:
        old_frames = id_frames_rec['id_' + str(old_group_id)]
        listObj = update_id_in_listObjframes(listObj, old_frames, shape, old_group_id)
    elif idChanged and only_this_frame:
        transfer_rec_and_traj(old_group_id, id_frames_rec, trajectories, [currFrame], new_group_id)
        update_id_in_listObjframe(listObj, currFrame, shape, old_group_id, new_group_id)
        new_frames = id_frames_rec['id_' + str(new_group_id)]
        update_id_in_listObjframes(listObj, new_frames, shape, new_group_id)
    elif idChanged and (not only_this_frame):
        old_frames = id_frames_rec['id_' + str(old_group_id)]
        transfer_rec_and_traj(old_group_id, id_frames_rec, trajectories, old_frames, new_group_id)
        update_id_in_listObjframes(listObj, old_frames, shape, old_group_id, new_group_id)
        new_frames = id_frames_rec['id_' + str(new_group_id)]
        update_id_in_listObjframes(listObj, new_frames, shape, new_group_id)
    return (id_frames_rec, trajectories, listObj)

def update_id_in_listObjframes(listObj, frames, shape, old_id, new_id=None):
    """
    Summary:
        Update the id of a shape in a list of frames in listObj.
        
    Args:
        listObj: a list of objects (each object is a dictionary of a frame with keys (frame_idx, frame_data))
        frames: a list of frames to update
        shape: the shape to update
        old_id: the old id
        new_id: the new id, if None then the old id is used (no id change)
        
    Returns:
        listObj: a list of objects (each object is a dictionary of a frame with keys (frame_idx, frame_data))
    """
    for frame in frames:
        listObj = update_id_in_listObjframe(listObj, frame, shape, old_id, new_id)
    return listObj

def reducing_Intersection(Intersection):
    """
    Summary:
        Reduce the intersection of two sets to a string.
        Make all the consecutive numbers in the intersection as a range.
            example: [1, 2, 3, 4, 5, 7, 8, 9] -> "1 to 5, 7 to 9"
        
    Args:
        Intersection: the intersection of two sets
        
    Returns:
        reduced_Intersection: the reduced intersection as a string
    """
    Intersection = list(Intersection)
    Intersection.sort()
    reduced_Intersection = ''
    reduced_Intersection += str(Intersection[0])
    flag = False
    i = 1
    while i < len(Intersection):
        if Intersection[i] - Intersection[i - 1] == 1:
            reduced_Intersection += ' to ' if not flag else ''
            flag = True
            if i + 1 == len(Intersection):
                reduced_Intersection += str(Intersection[i])
        elif flag:
            reduced_Intersection += str(Intersection[i - 1])
            if i + 1 < len(Intersection):
                reduced_Intersection += ', ' + str(Intersection[i])
                i += 1
            flag = False
        else:
            reduced_Intersection += ', ' + str(Intersection[i])
        i += 1
    return reduced_Intersection

class ToolBar(QtWidgets.QToolBar):

    def __init__(self, title):
        super(ToolBar, self).__init__(title)
        layout = self.layout()
        m = (0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setContentsMargins(*m)
        self.setContentsMargins(*m)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.FramelessWindowHint)

    def addAction(self, action):
        if isinstance(action, QtWidgets.QWidgetAction):
            return super(ToolBar, self).addAction(action)
        btn = QtWidgets.QToolButton()
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(self.toolButtonStyle())
        self.addWidget(btn)
        for i in range(self.layout().count()):
            if isinstance(self.layout().itemAt(i).widget(), QtWidgets.QToolButton):
                self.layout().itemAt(i).setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

def __init__(self, title):
    super(ToolBar, self).__init__(title)
    layout = self.layout()
    m = (0, 0, 0, 0)
    layout.setSpacing(0)
    layout.setContentsMargins(*m)
    self.setContentsMargins(*m)
    self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.FramelessWindowHint)

def addAction(self, action):
    if isinstance(action, QtWidgets.QWidgetAction):
        return super(ToolBar, self).addAction(action)
    btn = QtWidgets.QToolButton()
    btn.setDefaultAction(action)
    btn.setToolButtonStyle(self.toolButtonStyle())
    self.addWidget(btn)
    for i in range(self.layout().count()):
        if isinstance(self.layout().itemAt(i).widget(), QtWidgets.QToolButton):
            self.layout().itemAt(i).setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

class LabelDialog(QtWidgets.QDialog):

    def __init__(self, text='Enter object label', parent=None, labels=None, sort_labels=True, show_text_field=True, completion='startswith', fit_to_content=None, flags=None):
        if fit_to_content is None:
            fit_to_content = {'row': False, 'column': True}
        self._fit_to_content = fit_to_content
        super(LabelDialog, self).__init__(parent)
        self.setWindowTitle('Edit Label')
        self.edit = LabelQLineEdit()
        self.edit.setPlaceholderText(text)
        self.edit.setValidator(labelme.utils.labelValidator())
        self.edit.editingFinished.connect(self.postProcess)
        if flags:
            self.edit.textChanged.connect(self.updateFlags)
        self.edit_group_id = QtWidgets.QLineEdit()
        self.edit_group_id.setPlaceholderText('Tracking ID')
        self.edit_group_id.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression('\\d*'), None))
        self.edit_group_id_label = QtWidgets.QLabel()
        self.edit_group_id_label.setText('Tracking ID')
        self.select_class_label = QtWidgets.QLabel()
        self.select_class_label.setText('Class Name')
        self.buttonBox = bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel, QtCore.Qt.Orientation.Horizontal, self)
        bb.button(bb.StandardButton.Ok).setIcon(labelme.utils.newIcon('done'))
        bb.button(bb.StandardButton.Cancel).setIcon(labelme.utils.newIcon('undo'))
        bb.setCenterButtons(True)
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        self.labelList = QtWidgets.QListWidget()
        if self._fit_to_content['row']:
            self.labelList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        if self._fit_to_content['column']:
            self.labelList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._sort_labels = sort_labels
        if labels:
            self.labelList.addItems(labels)
        if self._sort_labels:
            self.labelList.sortItems()
        else:
            self.labelList.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.labelList.currentItemChanged.connect(self.labelSelected)
        self.labelList.itemDoubleClicked.connect(self.labelDoubleClicked)
        self.edit.setListWidget(self.labelList)
        self.labelListLabel = QtWidgets.QLabel()
        self.labelListLabel.setText('Select From Class List')
        if flags is None:
            flags = {}
        self._flags = flags
        self.flagsLayout = QtWidgets.QVBoxLayout()
        self.resetFlags()
        self.edit.textChanged.connect(self.updateFlags)
        self.confidenceEdit = QtWidgets.QLineEdit()
        self.confidenceEdit.setPlaceholderText('Confidence')
        validator = QtGui.QDoubleValidator(0, 1, 2, self.confidenceEdit)
        self.confidenceEdit.setValidator(validator)
        self.confidenceEditLabel = QtWidgets.QLabel()
        self.confidenceEditLabel.setText('Confidence')
        layout = QtWidgets.QVBoxLayout()
        layout.addItem(self.flagsLayout)
        layout.addWidget(self.select_class_label)
        layout.addWidget(self.edit)
        edit_group_id_layout = QtWidgets.QVBoxLayout()
        edit_group_id_layout.addWidget(self.edit_group_id_label)
        edit_group_id_layout.addWidget(self.edit_group_id)
        confidence_layout = QtWidgets.QVBoxLayout()
        confidence_layout.addWidget(self.confidenceEditLabel)
        confidence_layout.addWidget(self.confidenceEdit)
        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.addItem(edit_group_id_layout)
        horizontal_layout.addSpacing(10)
        horizontal_layout.addItem(confidence_layout)
        layout.addItem(horizontal_layout)
        layout.addWidget(self.labelListLabel)
        layout.addWidget(self.labelList)
        layout.addWidget(bb)
        self.resize(300, 200)
        self.setLayout(layout)
        completer = QtWidgets.QCompleter()
        if not QT5 and completion != 'startswith':
            logger.warn("completion other than 'startswith' is only supported with Qt5. Using 'startswith'")
            completion = 'startswith'
        if completion == 'startswith':
            completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.InlineCompletion)
        elif completion == 'contains':
            completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        else:
            raise ValueError('Unsupported completion: {}'.format(completion))
        completer.setModel(self.labelList.model())
        self.edit.setCompleter(completer)

    def addLabelHistory(self, label):
        if self.labelList.findItems(label, QtCore.Qt.MatchFlag.MatchExactly):
            return
        self.labelList.addItem(label)
        if self._sort_labels:
            self.labelList.sortItems()

    def labelSelected(self, item):
        self.edit.setText(item.text())

    def validate(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        if text:
            self.accept()

    def labelDoubleClicked(self, item):
        self.validate()

    def postProcess(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        self.edit.setText(text)

    def updateFlags(self, label_new):
        flags_old = self.getFlags()
        flags_new = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label_new):
                for key in keys:
                    flags_new[key] = flags_old.get(key, False)
        self.setFlags(flags_new)

    def deleteFlags(self):
        for i in reversed(range(self.flagsLayout.count())):
            item = self.flagsLayout.itemAt(i).widget()
            self.flagsLayout.removeWidget(item)
            item.setParent(None)

    def resetFlags(self, label=''):
        flags = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label):
                for key in keys:
                    flags[key] = False
        self.setFlags(flags)

    def setFlags(self, flags):
        self.deleteFlags()
        for key in flags:
            item = QtWidgets.QCheckBox(key, self)
            item.setChecked(flags[key])
            self.flagsLayout.addWidget(item)
            item.show()

    def getFlags(self):
        flags = {}
        for i in range(self.flagsLayout.count()):
            item = self.flagsLayout.itemAt(i).widget()
            print(type(item))
            flags[item.text()] = item.isChecked()
        return flags

    def getGroupId(self):
        group_id = self.edit_group_id.text()
        if group_id:
            return int(group_id)
        return None

    def getContent(self):
        content = self.confidenceEdit.text()
        if content:
            return content
        return None

    def setContent(self, content):
        if type(content) != str:
            content = str(content)
        self.confidenceEdit.setText(content)

    def popUp(self, text=None, move=True, flags=None, group_id=None, content=None, skip_flag=False):
        if self._fit_to_content['row']:
            self.labelList.setMinimumHeight(self.labelList.sizeHintForRow(0) * self.labelList.count() + 2)
        if self._fit_to_content['column']:
            self.labelList.setMinimumWidth(self.labelList.sizeHintForColumn(0) + 2)
        if text is None:
            text = self.edit.text()
        if content is None:
            content = ''
        self.setContent(content)
        if flags:
            self.setFlags(flags)
        else:
            self.resetFlags(text)
        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        if group_id is None:
            self.edit_group_id.clear()
        else:
            self.edit_group_id.setText(str(group_id))
        items = self.labelList.findItems(text, QtCore.Qt.MatchFlag.MatchFixedString)
        if items:
            if len(items) != 1:
                logger.warning("Label list has duplicate '{}'".format(text))
            self.labelList.setCurrentItem(items[0])
            row = self.labelList.row(items[0])
            self.edit.completer().setCurrentRow(row)
        self.edit.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
        if move:
            self.move(QtGui.QCursor.pos())
        if skip_flag:
            return (self.edit.text(), self.getFlags(), self.getGroupId(), self.getContent())
        if self.exec():
            return (self.edit.text(), self.getFlags(), self.getGroupId(), self.getContent())
        else:
            return (None, None, None, None)

def __init__(self, text='Enter object label', parent=None, labels=None, sort_labels=True, show_text_field=True, completion='startswith', fit_to_content=None, flags=None):
    if fit_to_content is None:
        fit_to_content = {'row': False, 'column': True}
    self._fit_to_content = fit_to_content
    super(LabelDialog, self).__init__(parent)
    self.setWindowTitle('Edit Label')
    self.edit = LabelQLineEdit()
    self.edit.setPlaceholderText(text)
    self.edit.setValidator(labelme.utils.labelValidator())
    self.edit.editingFinished.connect(self.postProcess)
    if flags:
        self.edit.textChanged.connect(self.updateFlags)
    self.edit_group_id = QtWidgets.QLineEdit()
    self.edit_group_id.setPlaceholderText('Tracking ID')
    self.edit_group_id.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression('\\d*'), None))
    self.edit_group_id_label = QtWidgets.QLabel()
    self.edit_group_id_label.setText('Tracking ID')
    self.select_class_label = QtWidgets.QLabel()
    self.select_class_label.setText('Class Name')
    self.buttonBox = bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel, QtCore.Qt.Orientation.Horizontal, self)
    bb.button(bb.StandardButton.Ok).setIcon(labelme.utils.newIcon('done'))
    bb.button(bb.StandardButton.Cancel).setIcon(labelme.utils.newIcon('undo'))
    bb.setCenterButtons(True)
    bb.accepted.connect(self.validate)
    bb.rejected.connect(self.reject)
    self.labelList = QtWidgets.QListWidget()
    if self._fit_to_content['row']:
        self.labelList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    if self._fit_to_content['column']:
        self.labelList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    self._sort_labels = sort_labels
    if labels:
        self.labelList.addItems(labels)
    if self._sort_labels:
        self.labelList.sortItems()
    else:
        self.labelList.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
    self.labelList.currentItemChanged.connect(self.labelSelected)
    self.labelList.itemDoubleClicked.connect(self.labelDoubleClicked)
    self.edit.setListWidget(self.labelList)
    self.labelListLabel = QtWidgets.QLabel()
    self.labelListLabel.setText('Select From Class List')
    if flags is None:
        flags = {}
    self._flags = flags
    self.flagsLayout = QtWidgets.QVBoxLayout()
    self.resetFlags()
    self.edit.textChanged.connect(self.updateFlags)
    self.confidenceEdit = QtWidgets.QLineEdit()
    self.confidenceEdit.setPlaceholderText('Confidence')
    validator = QtGui.QDoubleValidator(0, 1, 2, self.confidenceEdit)
    self.confidenceEdit.setValidator(validator)
    self.confidenceEditLabel = QtWidgets.QLabel()
    self.confidenceEditLabel.setText('Confidence')
    layout = QtWidgets.QVBoxLayout()
    layout.addItem(self.flagsLayout)
    layout.addWidget(self.select_class_label)
    layout.addWidget(self.edit)
    edit_group_id_layout = QtWidgets.QVBoxLayout()
    edit_group_id_layout.addWidget(self.edit_group_id_label)
    edit_group_id_layout.addWidget(self.edit_group_id)
    confidence_layout = QtWidgets.QVBoxLayout()
    confidence_layout.addWidget(self.confidenceEditLabel)
    confidence_layout.addWidget(self.confidenceEdit)
    horizontal_layout = QtWidgets.QHBoxLayout()
    horizontal_layout.addItem(edit_group_id_layout)
    horizontal_layout.addSpacing(10)
    horizontal_layout.addItem(confidence_layout)
    layout.addItem(horizontal_layout)
    layout.addWidget(self.labelListLabel)
    layout.addWidget(self.labelList)
    layout.addWidget(bb)
    self.resize(300, 200)
    self.setLayout(layout)
    completer = QtWidgets.QCompleter()
    if not QT5 and completion != 'startswith':
        logger.warn("completion other than 'startswith' is only supported with Qt5. Using 'startswith'")
        completion = 'startswith'
    if completion == 'startswith':
        completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.InlineCompletion)
    elif completion == 'contains':
        completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
    else:
        raise ValueError('Unsupported completion: {}'.format(completion))
    completer.setModel(self.labelList.model())
    self.edit.setCompleter(completer)

def addLabelHistory(self, label):
    if self.labelList.findItems(label, QtCore.Qt.MatchFlag.MatchExactly):
        return
    self.labelList.addItem(label)
    if self._sort_labels:
        self.labelList.sortItems()

def labelSelected(self, item):
    self.edit.setText(item.text())

def deleteFlags(self):
    for i in reversed(range(self.flagsLayout.count())):
        item = self.flagsLayout.itemAt(i).widget()
        self.flagsLayout.removeWidget(item)
        item.setParent(None)

def setFlags(self, flags):
    self.deleteFlags()
    for key in flags:
        item = QtWidgets.QCheckBox(key, self)
        item.setChecked(flags[key])
        self.flagsLayout.addWidget(item)
        item.show()

def getFlags(self):
    flags = {}
    for i in range(self.flagsLayout.count()):
        item = self.flagsLayout.itemAt(i).widget()
        print(type(item))
        flags[item.text()] = item.isChecked()
    return flags

def getGroupId(self):
    group_id = self.edit_group_id.text()
    if group_id:
        return int(group_id)
    return None

def getContent(self):
    content = self.confidenceEdit.text()
    if content:
        return content
    return None

def setContent(self, content):
    if type(content) != str:
        content = str(content)
    self.confidenceEdit.setText(content)

def popUp(self, text=None, move=True, flags=None, group_id=None, content=None, skip_flag=False):
    if self._fit_to_content['row']:
        self.labelList.setMinimumHeight(self.labelList.sizeHintForRow(0) * self.labelList.count() + 2)
    if self._fit_to_content['column']:
        self.labelList.setMinimumWidth(self.labelList.sizeHintForColumn(0) + 2)
    if text is None:
        text = self.edit.text()
    if content is None:
        content = ''
    self.setContent(content)
    if flags:
        self.setFlags(flags)
    else:
        self.resetFlags(text)
    self.edit.setText(text)
    self.edit.setSelection(0, len(text))
    if group_id is None:
        self.edit_group_id.clear()
    else:
        self.edit_group_id.setText(str(group_id))
    items = self.labelList.findItems(text, QtCore.Qt.MatchFlag.MatchFixedString)
    if items:
        if len(items) != 1:
            logger.warning("Label list has duplicate '{}'".format(text))
        self.labelList.setCurrentItem(items[0])
        row = self.labelList.row(items[0])
        self.edit.completer().setCurrentRow(row)
    self.edit.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
    if move:
        self.move(QtGui.QCursor.pos())
    if skip_flag:
        return (self.edit.text(), self.getFlags(), self.getGroupId(), self.getContent())
    if self.exec():
        return (self.edit.text(), self.getFlags(), self.getGroupId(), self.getContent())
    else:
        return (None, None, None, None)

def PopUp(self, group_id, text):
    """
    Summary:
        Show a dialog to get a new id from the user.
        check if the id is repeated.
        
    Args:
        self: the main window object to access the canvas
        group_id: the group id
        text: Class name
        
    Returns:
        group_id: the new group id
        text: Class name (False if the user-input id is repeated)
    """
    mainTEXT = 'A Shape with that ID already exists in this frame.\n\n'
    repeated = 0
    while is_id_repeated(self, group_id):
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle('ID already exists')
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.resize(450, 100)
        if repeated == 0:
            label = QtWidgets.QLabel(mainTEXT + f'Please try a new ID: ')
        if repeated == 1:
            label = QtWidgets.QLabel(mainTEXT + f'OH GOD.. AGAIN? I hpoe you are not doing this on purpose..')
        if repeated == 2:
            label = QtWidgets.QLabel(mainTEXT + f'AGAIN? REALLY? LAST time for you..')
        if repeated == 3:
            text = False
            return (group_id, text)
        properID = QtWidgets.QSpinBox()
        properID.setRange(1, 1000)
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        buttonBox.accepted.connect(dialog.accept)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(properID)
        layout.addWidget(buttonBox)
        dialog.setLayout(layout)
        result = dialog.exec()
        if result != QtWidgets.QDialog.DialogCode.Accepted:
            text = False
            return (group_id, text)
        group_id = properID.value()
        repeated += 1
    if repeated > 1:
        OKmsgBox('Finally..!', 'OH, Finally..!')
    return (group_id, text)

class Classeswidget(QtWidgets.QDialog):

    def __init__(self):
        super(Classeswidget, self).__init__()
        self.setModal(True)
        self.setWindowTitle('Select Class')
        self.class_name = 'person'
        self.class_name = self._createQComboBox()

    def _createQComboBox(self):
        class_name = QtWidgets.QComboBox()
        class_name.addItems(['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'])
        class_name.currentIndexChanged.connect(self.onNewValue)
        return class_name

    def onNewValue(self, value):
        self.class_name = value

    def getValue(self):
        return self.class_name

    def setValue(self, value):
        self.class_name = value

    def exec(self):
        super(Classeswidget, self).exec()
        return self.class_name

def __init__(self):
    super(Classeswidget, self).__init__()
    self.setModal(True)
    self.setWindowTitle('Select Class')
    self.class_name = 'person'
    self.class_name = self._createQComboBox()

def _createQComboBox(self):
    class_name = QtWidgets.QComboBox()
    class_name.addItems(['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'])
    class_name.currentIndexChanged.connect(self.onNewValue)
    return class_name

def exec(self):
    super(Classeswidget, self).exec()
    return self.class_name

class ZoomWidget(QtWidgets.QSpinBox):

    def __init__(self, value=100):
        super(ZoomWidget, self).__init__()
        self.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setRange(1, 1000)
        self.setSuffix(' %')
        self.setValue(value)
        self.setToolTip('Zoom Level')
        self.setStatusTip(self.toolTip())
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    def minimumSizeHint(self):
        height = super(ZoomWidget, self).minimumSizeHint().height()
        fm = QtGui.QFontMetrics(self.font())
        width = fm.width(str(self.maximum()))
        return QtCore.QSize(width, height)

def __init__(self, value=100):
    super(ZoomWidget, self).__init__()
    self.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
    self.setRange(1, 1000)
    self.setSuffix(' %')
    self.setValue(value)
    self.setToolTip('Zoom Level')
    self.setStatusTip(self.toolTip())
    self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

class UniqueLabelQListWidget(EscapableQListWidget):

    def mousePressEvent(self, event):
        super(UniqueLabelQListWidget, self).mousePressEvent(event)
        if not self.indexAt(event.pos()).isValid():
            self.clearSelection()

    def findItemsByLabel(self, label):
        items = []
        for row in range(self.count()):
            item = self.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == label:
                items.append(item)
        return items

    def createItemFromLabel(self, label):
        item = QtWidgets.QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, label)
        return item

    def setItemLabel(self, item, label, color=None):
        qlabel = QtWidgets.QLabel()
        if color is None:
            qlabel.setText('{}'.format(label))
        else:
            qlabel.setText('{} <font color="#{:02x}{:02x}{:02x}">●</font>'.format(label, *color))
        qlabel.setAlignment(Qt.AlignmentFlag.AlignBottom)
        item.setSizeHint(qlabel.sizeHint())
        self.setItemWidget(item, qlabel)

def mousePressEvent(self, event):
    super(UniqueLabelQListWidget, self).mousePressEvent(event)
    if not self.indexAt(event.pos()).isValid():
        self.clearSelection()

def setItemLabel(self, item, label, color=None):
    qlabel = QtWidgets.QLabel()
    if color is None:
        qlabel.setText('{}'.format(label))
    else:
        qlabel.setText('{} <font color="#{:02x}{:02x}{:02x}">●</font>'.format(label, *color))
    qlabel.setAlignment(Qt.AlignmentFlag.AlignBottom)
    item.setSizeHint(qlabel.sizeHint())
    self.setItemWidget(item, qlabel)

class LabelListWidgetItem(QtGui.QStandardItem):

    def __init__(self, text=None, shape=None):
        super(LabelListWidgetItem, self).__init__()
        self.setText(text)
        self.setShape(shape)
        self.setCheckable(True)
        self.setCheckState(Qt.CheckState.Checked)
        self.setEditable(False)
        self.setTextAlignment(Qt.AlignmentFlag.AlignBottom)
        font = QtGui.QFont('Arial', 10)
        self.setFont(font)

    def clone(self):
        return LabelListWidgetItem(self.text(), self.shape())

    def setShape(self, shape):
        self.setData(shape, Qt.ItemDataRole.UserRole)

    def shape(self):
        return self.data(Qt.ItemDataRole.UserRole)

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return '{}("{}")'.format(self.__class__.__name__, self.text())

def __init__(self, text=None, shape=None):
    super(LabelListWidgetItem, self).__init__()
    self.setText(text)
    self.setShape(shape)
    self.setCheckable(True)
    self.setCheckState(Qt.CheckState.Checked)
    self.setEditable(False)
    self.setTextAlignment(Qt.AlignmentFlag.AlignBottom)
    font = QtGui.QFont('Arial', 10)
    self.setFont(font)

def clone(self):
    return LabelListWidgetItem(self.text(), self.shape())

def __hash__(self):
    return id(self)

def __repr__(self):
    return '{}("{}")'.format(self.__class__.__name__, self.text())

class LabelListWidget(QtWidgets.QListView):
    itemDoubleClicked = QtCore.pyqtSignal(LabelListWidgetItem)
    itemSelectionChanged = QtCore.pyqtSignal(list, list)

    def __init__(self):
        super(LabelListWidget, self).__init__()
        self._selectedItems = []
        self.setWindowFlags(Qt.WindowType.Window)
        self.setModel(StandardItemModel())
        self.model().setItemPrototype(LabelListWidgetItem())
        self.setItemDelegate(HTMLDelegate())
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.doubleClicked.connect(self.itemDoubleClickedEvent)
        self.selectionModel().selectionChanged.connect(self.itemSelectionChangedEvent)

    def __len__(self):
        return self.model().rowCount()

    def __getitem__(self, i):
        return self.model().item(i)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    @property
    def itemDropped(self):
        return self.model().itemDropped

    @property
    def itemChanged(self):
        return self.model().itemChanged

    def itemSelectionChangedEvent(self, selected, deselected):
        selected = [self.model().itemFromIndex(i) for i in selected.indexes()]
        deselected = [self.model().itemFromIndex(i) for i in deselected.indexes()]
        self.itemSelectionChanged.emit(selected, deselected)

    def itemDoubleClickedEvent(self, index):
        self.itemDoubleClicked.emit(self.model().itemFromIndex(index))

    def selectedItems(self):
        return [self.model().itemFromIndex(i) for i in self.selectedIndexes()]

    def scrollToItem(self, item):
        self.scrollTo(self.model().indexFromItem(item))

    def addItem(self, item):
        if not isinstance(item, LabelListWidgetItem):
            raise TypeError('item must be LabelListWidgetItem')
        self.model().setItem(self.model().rowCount(), 0, item)
        item.setSizeHint(self.itemDelegate().sizeHint(None, None))

    def removeItem(self, item):
        index = self.model().indexFromItem(item)
        self.model().removeRows(index.row(), 1)

    def selectItem(self, item):
        index = self.model().indexFromItem(item)
        self.selectionModel().select(index, QtCore.QItemSelectionModel.SelectionFlag.Select)

    def findItemByShape(self, shape):
        for row in range(self.model().rowCount()):
            item = self.model().item(row, 0)
            if item.shape() == shape:
                return item
        raise ValueError('cannot find shape: {}'.format(shape))

    def clear(self):
        self.model().clear()

def __init__(self):
    super(LabelListWidget, self).__init__()
    self._selectedItems = []
    self.setWindowFlags(Qt.WindowType.Window)
    self.setModel(StandardItemModel())
    self.model().setItemPrototype(LabelListWidgetItem())
    self.setItemDelegate(HTMLDelegate())
    self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
    self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
    self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
    self.doubleClicked.connect(self.itemDoubleClickedEvent)
    self.selectionModel().selectionChanged.connect(self.itemSelectionChangedEvent)

def scrollToItem(self, item):
    self.scrollTo(self.model().indexFromItem(item))

def addItem(self, item):
    if not isinstance(item, LabelListWidgetItem):
        raise TypeError('item must be LabelListWidgetItem')
    self.model().setItem(self.model().rowCount(), 0, item)
    item.setSizeHint(self.itemDelegate().sizeHint(None, None))

def removeItem(self, item):
    index = self.model().indexFromItem(item)
    self.model().removeRows(index.row(), 1)

def selectItem(self, item):
    index = self.model().indexFromItem(item)
    self.selectionModel().select(index, QtCore.QItemSelectionModel.SelectionFlag.Select)

class BrightnessContrastDialog(QtWidgets.QDialog):

    def __init__(self, img, callback, parent=None):
        super(BrightnessContrastDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowTitle('Brightness/Contrast')
        self.slider_brightness = self._create_slider()
        self.slider_contrast = self._create_slider()
        formLayout = QtWidgets.QFormLayout()
        formLayout.addRow(self.tr('Brightness'), self.slider_brightness)
        formLayout.addRow(self.tr('Contrast'), self.slider_contrast)
        self.setLayout(formLayout)
        assert isinstance(img, PIL.Image.Image)
        self.img = img
        self.callback = callback

    def onNewValue(self, value):
        brightness = self.slider_brightness.value() / 50.0
        contrast = self.slider_contrast.value() / 50.0
        img = self.img
        img = PIL.ImageEnhance.Brightness(img).enhance(brightness)
        img = PIL.ImageEnhance.Contrast(img).enhance(contrast)
        img_data = utils.img_pil_to_data(img)
        qimage = QtGui.QImage.fromData(img_data)
        self.callback(qimage)

    def _create_slider(self):
        slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 150)
        slider.setValue(50)
        slider.valueChanged.connect(self.onNewValue)
        return slider

def __init__(self, img, callback, parent=None):
    super(BrightnessContrastDialog, self).__init__(parent)
    self.setModal(True)
    self.setWindowTitle('Brightness/Contrast')
    self.slider_brightness = self._create_slider()
    self.slider_contrast = self._create_slider()
    formLayout = QtWidgets.QFormLayout()
    formLayout.addRow(self.tr('Brightness'), self.slider_brightness)
    formLayout.addRow(self.tr('Contrast'), self.slider_contrast)
    self.setLayout(formLayout)
    assert isinstance(img, PIL.Image.Image)
    self.img = img
    self.callback = callback

def _create_slider(self):
    slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 150)
    slider.setValue(50)
    slider.valueChanged.connect(self.onNewValue)
    return slider

def PopUp():
    """
    Displays a dialog box for providing feedback on the DLTA-AI project.

    Parameters:
    None

    Returns:
    None
    """
    text = 'Found a bug? 🐞\nWant to suggest a feature? 🌟\n'
    msgBox = QMessageBox()
    msgBox.setWindowTitle('Feedback')
    msgBox.setText(text)
    msgBox.addButton(QMessageBox.StandardButton.Yes)
    msgBox.button(QMessageBox.StandardButton.Yes).setText('Open an Issue')
    msgBox.button(QMessageBox.StandardButton.Yes).clicked.connect(open_issue)
    msgBox.addButton(QMessageBox.StandardButton.Close)
    msgBox.button(QMessageBox.StandardButton.Close).setText('Close')
    msgBox.exec()

def PopUp(mode='video'):
    """
    Displays a dialog box for choosing export options for annotations and videos.

    Args:
        mode (str): The mode of the export. Can be either "video" or "image". Defaults to "video".

    Returns:
        A tuple containing the result of the dialog box and the selected export options. If the dialog box is accepted, the first element of the tuple is `QtWidgets.QDialog.DialogCode.Accepted`. Otherwise, it is `QtWidgets.QDialog.Rejected`. The second element of the tuple is a boolean indicating whether to export annotations in COCO format. If `mode` is "video", the third element of the tuple is a boolean indicating whether to export annotations in MOT format, and the fourth element is a boolean indicating whether to export the video with the current visualization settings. If there are any custom export options available, the fifth element of the tuple is a list of booleans indicating whether to export using each custom export option.
    """
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle('Choose Export Options')
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.resize(250, 100)
    layout = QtWidgets.QVBoxLayout()
    font = QtGui.QFont()
    font.setBold(True)
    font.setPointSize(10)
    if mode == 'video':
        vid_label = QtWidgets.QLabel('Export Video')
        vid_label.setFont(font)
        vid_label.setMargin(7)
    std_label = QtWidgets.QLabel('Export Annotations (Standard Formats)')
    std_label.setFont(font)
    std_label.setMargin(7)
    custom_label = QtWidgets.QLabel('Export Annotations (Custom Formats)')
    custom_label.setFont(font)
    custom_label.setMargin(7)
    button_group = QtWidgets.QButtonGroup()
    coco_radio = QtWidgets.QRadioButton('COCO Format (Detection / Segmentation)')
    if mode == 'video':
        video_radio = QtWidgets.QRadioButton('Export Video with current visualization settings')
        mot_radio = QtWidgets.QRadioButton('MOT Format (Tracking)')
    custom_exports_radio_list = []
    if len(custom_exports_list) != 0:
        for custom_exp in custom_exports_list:
            if custom_exp.mode == 'video' and mode == 'video':
                custom_radio = QtWidgets.QRadioButton(custom_exp.button_name)
                button_group.addButton(custom_radio)
                custom_exports_radio_list.append(custom_radio)
            if custom_exp.mode == 'image' and mode == 'image':
                custom_radio = QtWidgets.QRadioButton(custom_exp.button_name)
                button_group.addButton(custom_radio)
                custom_exports_radio_list.append(custom_radio)
    button_group.addButton(coco_radio)
    if mode == 'video':
        button_group.addButton(video_radio)
        button_group.addButton(mot_radio)
    if len(custom_exports_list) != 0:
        for custom_radio in custom_exports_radio_list:
            button_group.addButton(custom_radio)
    if mode == 'video':
        layout.addWidget(vid_label)
        layout.addWidget(video_radio)
    layout.addWidget(std_label)
    layout.addWidget(coco_radio)
    if mode == 'video':
        layout.addWidget(mot_radio)
    layout.addWidget(custom_label)
    if len(custom_exports_radio_list) != 0:
        for custom_radio in custom_exports_radio_list:
            layout.addWidget(custom_radio)
    else:
        layout.addWidget(QtWidgets.QLabel('No Custom Exports Available, you can add them in utils.custom_exports.py'))
    custom_exports_button = QtWidgets.QPushButton('Open Custom Exports')
    custom_exports_button.clicked.connect(open_file.PopUp)
    layout.addWidget(custom_exports_button)
    buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    buttonBox.accepted.connect(dialog.accept)
    buttonBox.rejected.connect(dialog.reject)
    layout.addWidget(buttonBox)
    dialog.setLayout(layout)
    result = dialog.exec()
    custom_exports_radio_checked_list = []
    if len(custom_exports_list) != 0:
        for custom_radio in custom_exports_radio_list:
            custom_exports_radio_checked_list.append(custom_radio.isChecked())
    if mode == 'video':
        return (result, coco_radio.isChecked(), mot_radio.isChecked(), video_radio.isChecked(), custom_exports_radio_checked_list)
    else:
        return (result, coco_radio.isChecked(), custom_exports_radio_checked_list)

class ColorDialog(QtWidgets.QColorDialog):

    def __init__(self, parent=None):
        super(ColorDialog, self).__init__(parent)
        self.setOption(QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel)
        self.setOption(QtWidgets.QColorDialog.ColorDialogOption.DontUseNativeDialog)
        self.default = None
        self.bb = self.findChild(QtWidgets.QDialogButtonBox)
        self.bb.addButton(QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults)
        self.bb.clicked.connect(self.checkRestore)

    def getColor(self, value=None, title=None, default=None):
        self.default = default
        if title:
            self.setWindowTitle(title)
        if value:
            self.setCurrentColor(value)
        return self.currentColor() if self.exec() else None

    def checkRestore(self, button):
        if self.bb.buttonRole(button) & QtWidgets.QDialogButtonBox.ButtonRole.ResetRole and self.default:
            self.setCurrentColor(self.default)

def __init__(self, parent=None):
    super(ColorDialog, self).__init__(parent)
    self.setOption(QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel)
    self.setOption(QtWidgets.QColorDialog.ColorDialogOption.DontUseNativeDialog)
    self.default = None
    self.bb = self.findChild(QtWidgets.QDialogButtonBox)
    self.bb.addButton(QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults)
    self.bb.clicked.connect(self.checkRestore)

def getColor(self, value=None, title=None, default=None):
    self.default = default
    if title:
        self.setWindowTitle(title)
    if value:
        self.setCurrentColor(value)
    return self.currentColor() if self.exec() else None

def checkRestore(self, button):
    if self.bb.buttonRole(button) & QtWidgets.QDialogButtonBox.ButtonRole.ResetRole and self.default:
        self.setCurrentColor(self.default)

class SegmentationOptionsUI:

    def __init__(self, parent):
        self.parent = parent
        self.conf_threshold = 0.3
        self.iou_threshold = 0.5
        with open('labelme/config/default_config.yaml') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        self.default_classes = self.config['default_classes']
        try:
            self.selectedclasses = {}
            for class_ in self.default_classes:
                if class_ in coco_classes:
                    index = coco_classes.index(class_)
                    self.selectedclasses[index] = class_
        except:
            self.selectedclasses = {i: class_ for i, class_ in enumerate(coco_classes)}
            print('error in loading the default classes from the config file, so we will use all the coco classes')

    def setConfThreshold(self, prev_threshold=0.3):
        dialog = QtWidgets.QDialog(self.parent)
        dialog.setWindowTitle('Threshold Selector')
        dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        layout = QtWidgets.QVBoxLayout(dialog)
        label = QtWidgets.QLabel('Enter Confidence Threshold')
        layout.addWidget(label)
        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setMinimum(1)
        slider.setMaximum(100)
        slider.setValue(int(prev_threshold * 100))
        text_input = QtWidgets.QLineEdit(str(prev_threshold))

        def on_slider_change(value):
            text_input.setText(str(value / 100))

        def on_text_change(text):
            try:
                value = float(text)
                slider.setValue(int(value * 100))
            except ValueError:
                pass
        slider.valueChanged.connect(on_slider_change)
        text_input.textChanged.connect(on_text_change)
        layout.addWidget(slider)
        layout.addWidget(text_input)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)

        def on_ok():
            threshold = float(text_input.text())
            dialog.accept()
            return threshold

        def on_cancel():
            dialog.reject()
            return prev_threshold
        button_box.accepted.connect(on_ok)
        button_box.rejected.connect(on_cancel)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            return slider.value() / 100
        else:
            return prev_threshold

    def setIOUThreshold(self, prev_threshold=0.5):
        dialog = QtWidgets.QDialog(self.parent)
        dialog.setWindowTitle('Threshold Selector')
        dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        layout = QtWidgets.QVBoxLayout(dialog)
        label = QtWidgets.QLabel('Enter IOU Threshold')
        layout.addWidget(label)
        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setMinimum(1)
        slider.setMaximum(100)
        slider.setValue(int(prev_threshold * 100))
        text_input = QtWidgets.QLineEdit(str(prev_threshold))

        def on_slider_change(value):
            text_input.setText(str(value / 100))

        def on_text_change(text):
            try:
                value = float(text)
                slider.setValue(int(value * 100))
            except ValueError:
                pass
        slider.valueChanged.connect(on_slider_change)
        text_input.textChanged.connect(on_text_change)
        layout.addWidget(slider)
        layout.addWidget(text_input)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)

        def on_ok():
            threshold = float(text_input.text())
            dialog.accept()
            return threshold

        def on_cancel():
            dialog.reject()
            return prev_threshold
        button_box.accepted.connect(on_ok)
        button_box.rejected.connect(on_cancel)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            return slider.value() / 100
        else:
            return prev_threshold

    def selectClasses(self):
        """
        Display a dialog box that allows the user to select which classes to annotate.

        The function creates a QDialog object and adds various widgets to it, including a QScrollArea that contains QCheckBox
        widgets for each class. The function sets the state of each QCheckBox based on whether the class is in the
        self.selectedclasses dictionary. The function also adds "Select All", "Deselect All", "Select Classes", "Set as Default",
        and "Cancel" buttons to the dialog box. When the user clicks the "Select Classes" button, the function saves the selected
        classes to the self.selectedclasses dictionary and returns it.

        :return: A dictionary that maps class indices to class names for the selected classes.
        """
        dialog = QtWidgets.QDialog(self.parent)
        dialog.setWindowTitle('Select Classes')
        dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        dialog.resize(500, 500)
        dialog.setMinimumSize(QtCore.QSize(500, 500))
        dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        verticalLayout = QtWidgets.QVBoxLayout(dialog)
        verticalLayout.setObjectName('verticalLayout')
        horizontalLayout = QtWidgets.QHBoxLayout()
        selectAllButton = QtWidgets.QPushButton('Select All', dialog)
        deselectAllButton = QtWidgets.QPushButton('Deselect All', dialog)
        horizontalLayout.addWidget(selectAllButton)
        horizontalLayout.addWidget(deselectAllButton)
        verticalLayout.addLayout(horizontalLayout)
        scrollArea = QtWidgets.QScrollArea(dialog)
        scrollArea.setWidgetResizable(True)
        scrollArea.setObjectName('scrollArea')
        scrollAreaWidgetContents = QtWidgets.QWidget()
        scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 478, 478))
        scrollAreaWidgetContents.setObjectName('scrollAreaWidgetContents')
        gridLayout = QtWidgets.QGridLayout(scrollAreaWidgetContents)
        gridLayout.setObjectName('gridLayout')
        self.scrollAreaWidgetContents = scrollAreaWidgetContents
        scrollArea.setWidget(scrollAreaWidgetContents)
        verticalLayout.addWidget(scrollArea)
        buttonBox = QtWidgets.QDialogButtonBox(dialog)
        buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok)
        buttonBox.setObjectName('buttonBox')
        buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText('Select Classes')
        defaultButton = QtWidgets.QPushButton('Set as Default', dialog)
        buttonBox.addButton(defaultButton, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        buttonLayout.addWidget(defaultButton)
        buttonLayout.addWidget(buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel))
        verticalLayout.addLayout(buttonLayout)
        buttonBox.accepted.connect(lambda: self.saveClasses(dialog))
        buttonBox.rejected.connect(dialog.reject)
        defaultButton.clicked.connect(lambda: self.saveClasses(dialog, True))
        self.classes = []
        for i in range(len(coco_classes)):
            self.classes.append(QtWidgets.QCheckBox(coco_classes[i], dialog))
            row = i // 3
            col = i % 3
            gridLayout.addWidget(self.classes[i], row, col)
        for value in self.selectedclasses.values():
            if value != None:
                indx = coco_classes.index(value)
                self.classes[indx].setChecked(True)
        selectAllButton.clicked.connect(lambda: self.selectAll())
        deselectAllButton.clicked.connect(lambda: self.deselectAll())
        dialog.show()
        dialog.exec()
        self.selectedclasses.clear()
        for i in range(len(self.classes)):
            if self.classes[i].isChecked():
                indx = coco_classes.index(self.classes[i].text())
                self.selectedclasses[indx] = self.classes[i].text()
        return self.selectedclasses

    def saveClasses(self, dialog, is_default=False):
        """
        Save the selected classes to the self.selectedclasses dictionary.

        The function clears the self.selectedclasses dictionary and then iterates over the QCheckBox widgets for each class.
        If a QCheckBox is checked, the function adds the corresponding class name to the self.selectedclasses dictionary. If the
        is_default parameter is True, the function also updates the default_config.yaml file with the selected classes.

        :param dialog: The QDialog object that contains the class selection dialog.
        :param is_default: A boolean that indicates whether to update the default_config.yaml file with the selected classes.
        """
        self.selectedclasses.clear()
        for i in range(len(self.classes)):
            if self.classes[i].isChecked():
                indx = coco_classes.index(self.classes[i].text())
                self.selectedclasses[indx] = self.classes[i].text()
        if is_default:
            with open('labelme/config/default_config.yaml', 'r') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
            config['default_classes'] = list(self.selectedclasses.values())
            with open('labelme/config/default_config.yaml', 'w') as f:
                yaml.dump(config, f)
        dialog.accept()

    def selectAll(self):
        """
        Select all classes in the class selection dialog.

        The function iterates over the QCheckBox widgets for each class and sets their checked state to True.
        """
        for checkbox in self.classes:
            checkbox.setChecked(True)

    def deselectAll(self):
        """
        Deselect all classes in the class selection dialog.

        The function iterates over the QCheckBox widgets for each class and sets their checked state to False.
        """
        for checkbox in self.classes:
            checkbox.setChecked(False)

def setConfThreshold(self, prev_threshold=0.3):
    dialog = QtWidgets.QDialog(self.parent)
    dialog.setWindowTitle('Threshold Selector')
    dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
    layout = QtWidgets.QVBoxLayout(dialog)
    label = QtWidgets.QLabel('Enter Confidence Threshold')
    layout.addWidget(label)
    slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    slider.setMinimum(1)
    slider.setMaximum(100)
    slider.setValue(int(prev_threshold * 100))
    text_input = QtWidgets.QLineEdit(str(prev_threshold))

    def on_slider_change(value):
        text_input.setText(str(value / 100))

    def on_text_change(text):
        try:
            value = float(text)
            slider.setValue(int(value * 100))
        except ValueError:
            pass
    slider.valueChanged.connect(on_slider_change)
    text_input.textChanged.connect(on_text_change)
    layout.addWidget(slider)
    layout.addWidget(text_input)
    button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    layout.addWidget(button_box)

    def on_ok():
        threshold = float(text_input.text())
        dialog.accept()
        return threshold

    def on_cancel():
        dialog.reject()
        return prev_threshold
    button_box.accepted.connect(on_ok)
    button_box.rejected.connect(on_cancel)
    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return slider.value() / 100
    else:
        return prev_threshold

def on_slider_change(value):
    text_input.setText(str(value / 100))

def setIOUThreshold(self, prev_threshold=0.5):
    dialog = QtWidgets.QDialog(self.parent)
    dialog.setWindowTitle('Threshold Selector')
    dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
    layout = QtWidgets.QVBoxLayout(dialog)
    label = QtWidgets.QLabel('Enter IOU Threshold')
    layout.addWidget(label)
    slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    slider.setMinimum(1)
    slider.setMaximum(100)
    slider.setValue(int(prev_threshold * 100))
    text_input = QtWidgets.QLineEdit(str(prev_threshold))

    def on_slider_change(value):
        text_input.setText(str(value / 100))

    def on_text_change(text):
        try:
            value = float(text)
            slider.setValue(int(value * 100))
        except ValueError:
            pass
    slider.valueChanged.connect(on_slider_change)
    text_input.textChanged.connect(on_text_change)
    layout.addWidget(slider)
    layout.addWidget(text_input)
    button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    layout.addWidget(button_box)

    def on_ok():
        threshold = float(text_input.text())
        dialog.accept()
        return threshold

    def on_cancel():
        dialog.reject()
        return prev_threshold
    button_box.accepted.connect(on_ok)
    button_box.rejected.connect(on_cancel)
    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return slider.value() / 100
    else:
        return prev_threshold

def selectClasses(self):
    """
        Display a dialog box that allows the user to select which classes to annotate.

        The function creates a QDialog object and adds various widgets to it, including a QScrollArea that contains QCheckBox
        widgets for each class. The function sets the state of each QCheckBox based on whether the class is in the
        self.selectedclasses dictionary. The function also adds "Select All", "Deselect All", "Select Classes", "Set as Default",
        and "Cancel" buttons to the dialog box. When the user clicks the "Select Classes" button, the function saves the selected
        classes to the self.selectedclasses dictionary and returns it.

        :return: A dictionary that maps class indices to class names for the selected classes.
        """
    dialog = QtWidgets.QDialog(self.parent)
    dialog.setWindowTitle('Select Classes')
    dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
    dialog.resize(500, 500)
    dialog.setMinimumSize(QtCore.QSize(500, 500))
    dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
    verticalLayout = QtWidgets.QVBoxLayout(dialog)
    verticalLayout.setObjectName('verticalLayout')
    horizontalLayout = QtWidgets.QHBoxLayout()
    selectAllButton = QtWidgets.QPushButton('Select All', dialog)
    deselectAllButton = QtWidgets.QPushButton('Deselect All', dialog)
    horizontalLayout.addWidget(selectAllButton)
    horizontalLayout.addWidget(deselectAllButton)
    verticalLayout.addLayout(horizontalLayout)
    scrollArea = QtWidgets.QScrollArea(dialog)
    scrollArea.setWidgetResizable(True)
    scrollArea.setObjectName('scrollArea')
    scrollAreaWidgetContents = QtWidgets.QWidget()
    scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 478, 478))
    scrollAreaWidgetContents.setObjectName('scrollAreaWidgetContents')
    gridLayout = QtWidgets.QGridLayout(scrollAreaWidgetContents)
    gridLayout.setObjectName('gridLayout')
    self.scrollAreaWidgetContents = scrollAreaWidgetContents
    scrollArea.setWidget(scrollAreaWidgetContents)
    verticalLayout.addWidget(scrollArea)
    buttonBox = QtWidgets.QDialogButtonBox(dialog)
    buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
    buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok)
    buttonBox.setObjectName('buttonBox')
    buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText('Select Classes')
    defaultButton = QtWidgets.QPushButton('Set as Default', dialog)
    buttonBox.addButton(defaultButton, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
    buttonLayout = QtWidgets.QHBoxLayout()
    buttonLayout.addWidget(buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    buttonLayout.addWidget(defaultButton)
    buttonLayout.addWidget(buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel))
    verticalLayout.addLayout(buttonLayout)
    buttonBox.accepted.connect(lambda: self.saveClasses(dialog))
    buttonBox.rejected.connect(dialog.reject)
    defaultButton.clicked.connect(lambda: self.saveClasses(dialog, True))
    self.classes = []
    for i in range(len(coco_classes)):
        self.classes.append(QtWidgets.QCheckBox(coco_classes[i], dialog))
        row = i // 3
        col = i % 3
        gridLayout.addWidget(self.classes[i], row, col)
    for value in self.selectedclasses.values():
        if value != None:
            indx = coco_classes.index(value)
            self.classes[indx].setChecked(True)
    selectAllButton.clicked.connect(lambda: self.selectAll())
    deselectAllButton.clicked.connect(lambda: self.deselectAll())
    dialog.show()
    dialog.exec()
    self.selectedclasses.clear()
    for i in range(len(self.classes)):
        if self.classes[i].isChecked():
            indx = coco_classes.index(self.classes[i].text())
            self.selectedclasses[indx] = self.classes[i].text()
    return self.selectedclasses

def selectAll(self):
    """
        Select all classes in the class selection dialog.

        The function iterates over the QCheckBox widgets for each class and sets their checked state to True.
        """
    for checkbox in self.classes:
        checkbox.setChecked(True)

def deselectAll(self):
    """
        Deselect all classes in the class selection dialog.

        The function iterates over the QCheckBox widgets for each class and sets their checked state to False.
        """
    for checkbox in self.classes:
        checkbox.setChecked(False)

def PopUp(self):
    """
    Summary:
        Show a dialog to scale a shape.
        
    Args:
        self: the main window object to access the canvas
        
    Returns:
        result: the result of the dialog
    """
    originalshape = self.canvas.selectedShapes[0].copy()
    xx = [originalshape.points[i].x() for i in range(len(originalshape.points))]
    yy = [originalshape.points[i].y() for i in range(len(originalshape.points))]
    center = [sum(xx) / len(xx), sum(yy) / len(yy)]
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle('Scaling')
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.resize(400, 400)
    layout = QtWidgets.QVBoxLayout()
    label = QtWidgets.QLabel('Scaling object with ID: ' + str(originalshape.group_id) + '\n ')
    label.setStyleSheet('QLabel { font-weight: bold; }')
    layout.addWidget(label)
    xLabel = QtWidgets.QLabel()
    xLabel.setText('Width(x) factor is: ' + '100' + '%')
    yLabel = QtWidgets.QLabel()
    yLabel.setText('Hight(y) factor is: ' + '100' + '%')
    xSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    xSlider.setMinimum(50)
    xSlider.setMaximum(150)
    xSlider.setValue(100)
    xSlider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
    xSlider.setTickInterval(1)
    xSlider.setMaximumWidth(750)
    xSlider.valueChanged.connect(lambda: xLabel.setText('Width(x) factor is: ' + str(xSlider.value()) + '%'))
    xSlider.valueChanged.connect(lambda: scaleQTshape(self, originalshape, center, xSlider.value(), ySlider.value()))
    ySlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)
    ySlider.setMinimum(50)
    ySlider.setMaximum(150)
    ySlider.setValue(100)
    ySlider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
    ySlider.setTickInterval(1)
    ySlider.setMaximumWidth(750)
    ySlider.valueChanged.connect(lambda: yLabel.setText('Hight(y) factor is: ' + str(ySlider.value()) + '%'))
    ySlider.valueChanged.connect(lambda: scaleQTshape(self, originalshape, center, xSlider.value(), ySlider.value()))
    layout.addWidget(xLabel)
    layout.addWidget(yLabel)
    layout.addWidget(xSlider)
    layout.addWidget(ySlider)
    buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
    buttonBox.accepted.connect(dialog.accept)
    layout.addWidget(buttonBox)
    dialog.setLayout(layout)
    result = dialog.exec()
    return result

def PopUp(TOTAL_VIDEO_FRAMES, INDEX_OF_CURRENT_FRAME, config):
    """
    Summary:
        Show a dialog to choose the deletion options.
        (   This Frame and All Previous Frames,
            This Frame and All Next Frames,
            All Frames,
            This Frame Only,
            Specific Range of Frames           )
            
    Args:
        TOTAL_VIDEO_FRAMES: the total number of frames
        config: a dictionary of configurations
        
    Returns:
        result: the result of the dialog
        config: the updated dictionary of configurations
        fromFrameVAL: the start frame of the deletion range
        toFrameVAL: the end frame of the deletion range
    """
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle('Choose Deletion Options')
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.resize(500, 100)
    dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
    layout = QtWidgets.QVBoxLayout()
    label = QtWidgets.QLabel('Choose Deletion Options')
    layout.addWidget(label)
    prev = QtWidgets.QRadioButton('This Frame and All Previous Frames')
    next = QtWidgets.QRadioButton('This Frame and All Next Frames')
    all = QtWidgets.QRadioButton('All Frames')
    only = QtWidgets.QRadioButton('This Frame Only')
    from_to = QtWidgets.QRadioButton('Specific Range of Frames')
    from_frame = QtWidgets.QSpinBox()
    to_frame = QtWidgets.QSpinBox()
    from_frame.setRange(1, TOTAL_VIDEO_FRAMES)
    to_frame.setRange(1, TOTAL_VIDEO_FRAMES)
    from_frame.valueChanged.connect(lambda: from_to.toggle())
    to_frame.valueChanged.connect(lambda: from_to.toggle())
    from_label = QtWidgets.QLabel('From:')
    to_label = QtWidgets.QLabel('To:')
    if config['deleteDefault'] == 'This Frame and All Previous Frames':
        prev.toggle()
    if config['deleteDefault'] == 'This Frame and All Next Frames':
        next.toggle()
    if config['deleteDefault'] == 'All Frames':
        all.toggle()
    if config['deleteDefault'] == 'This Frame Only':
        only.toggle()
    if config['deleteDefault'] == 'Specific Range of Frames':
        from_to.toggle()
    prev.toggled.connect(lambda: config.update({'deleteDefault': 'This Frame and All Previous Frames'}))
    next.toggled.connect(lambda: config.update({'deleteDefault': 'This Frame and All Next Frames'}))
    all.toggled.connect(lambda: config.update({'deleteDefault': 'All Frames'}))
    only.toggled.connect(lambda: config.update({'deleteDefault': 'This Frame Only'}))
    from_to.toggled.connect(lambda: config.update({'deleteDefault': 'Specific Range of Frames'}))
    button_layout = QtWidgets.QHBoxLayout()
    button_layout.addWidget(only)
    button_layout.addWidget(all)
    layout.addLayout(button_layout)
    button_layout = QtWidgets.QHBoxLayout()
    button_layout.addWidget(prev)
    button_layout.addWidget(next)
    layout.addLayout(button_layout)
    layout.addWidget(from_to)
    button_layout = QtWidgets.QHBoxLayout()
    button_layout.addWidget(from_label)
    button_layout.addWidget(from_frame)
    button_layout.addWidget(to_label)
    button_layout.addWidget(to_frame)
    layout.addLayout(button_layout)
    buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
    buttonBox.accepted.connect(dialog.accept)
    buttonBox.rejected.connect(dialog.reject)
    layout.addWidget(buttonBox)
    dialog.setLayout(layout)
    result = dialog.exec()
    mode = config['deleteDefault']
    fromFrameVAL = from_frame.value()
    toFrameVAL = to_frame.value()
    if mode == 'This Frame and All Previous Frames':
        toFrameVAL = INDEX_OF_CURRENT_FRAME
        fromFrameVAL = 1
    elif mode == 'This Frame and All Next Frames':
        toFrameVAL = TOTAL_VIDEO_FRAMES
        fromFrameVAL = INDEX_OF_CURRENT_FRAME
    elif mode == 'This Frame Only':
        toFrameVAL = INDEX_OF_CURRENT_FRAME
        fromFrameVAL = INDEX_OF_CURRENT_FRAME
    elif mode == 'All Frames':
        toFrameVAL = TOTAL_VIDEO_FRAMES
        fromFrameVAL = 1
    return (result, config, fromFrameVAL, toFrameVAL)

class Canvas(QtWidgets.QWidget):
    zoomRequest = QtCore.pyqtSignal(int, QtCore.QPoint)
    scrollRequest = QtCore.pyqtSignal(int, int)
    newShape = QtCore.pyqtSignal()
    selectionChanged = QtCore.pyqtSignal(list)
    shapeMoved = QtCore.pyqtSignal()
    drawingPolygon = QtCore.pyqtSignal(bool)
    edgeSelected = QtCore.pyqtSignal(bool, object)
    vertexSelected = QtCore.pyqtSignal(bool)
    pointAdded = QtCore.pyqtSignal()
    samFinish = QtCore.pyqtSignal()
    APPrefresh = QtCore.pyqtSignal(bool)
    CREATE, EDIT = (0, 1)
    CREATE, EDIT = (0, 1)
    _createMode = 'polygon'
    _fill_drawing = False

    def __init__(self, *args, **kwargs):
        self.epsilon = kwargs.pop('epsilon', 10.0)
        self.double_click = kwargs.pop('double_click', 'close')
        if self.double_click not in [None, 'close']:
            raise ValueError('Unexpected value for double_click event: {}'.format(self.double_click))
        self.num_backups = kwargs.pop('num_backups', 10)
        super(Canvas, self).__init__(*args, **kwargs)
        self.mode = self.EDIT
        self.shapes = []
        self.SAM_mode = ''
        self.SAM_coordinates = []
        self.SAM_rect = []
        self.SAM_rects = []
        self.SAM_painter = QtGui.QPainter()
        self.SAM_current = None
        self.show_cross_line = True
        self.is_loading = False
        self.loading_angle = 0
        self.loading_text = 'Loading...'
        self.tracking_area = ''
        self.tracking_area_polygon = []
        self.current_annotation_mode = ''
        self.shapesBackups = []
        self.current = None
        self.selectedShapes = []
        self.selectedShapesCopy = []
        self.line = Shape()
        self.prevPoint = QtCore.QPoint()
        self.prevMovePoint = QtCore.QPoint()
        self.offsets = (QtCore.QPoint(), QtCore.QPoint())
        self.scale = 1.0
        self.pixmap = QtGui.QPixmap()
        self.visible = {}
        self._hideBackround = False
        self.hideBackround = False
        self.hShape = None
        self.prevhShape = None
        self.hVertex = None
        self.prevhVertex = None
        self.hEdge = None
        self.prevhEdge = None
        self.movingShape = False
        self._painter = QtGui.QPainter()
        self._cursor = CURSOR_DEFAULT
        self.menus = (QtWidgets.QMenu(), QtWidgets.QMenu())
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.WheelFocus)

    def fillDrawing(self):
        return self._fill_drawing

    def setFillDrawing(self, value):
        self._fill_drawing = value

    @property
    def createMode(self):
        return self._createMode

    @createMode.setter
    def createMode(self, value):
        if value not in ['polygon']:
            raise ValueError('Unsupported createMode: %s' % value)
        self._createMode = value

    def storeShapes(self):
        shapesBackup = []
        for shape in self.shapes:
            shapesBackup.append(shape.copy())
        if len(self.shapesBackups) > self.num_backups:
            self.shapesBackups = self.shapesBackups[-self.num_backups - 1:]
        self.shapesBackups.append(shapesBackup)

    @property
    def isShapeRestorable(self):
        if len(self.shapesBackups) < 2:
            return False
        return True

    def restoreShape(self):
        if not self.isShapeRestorable:
            return
        self.shapesBackups.pop()
        shapesBackup = self.shapesBackups.pop()
        self.shapes = shapesBackup
        self.selectedShapes = []
        for shape in self.shapes:
            shape.selected = False
        self.update()

    def enterEvent(self, ev):
        self.overrideCursor(self._cursor)

    def leaveEvent(self, ev):
        self.unHighlight()
        self.restoreCursor()

    def focusOutEvent(self, ev):
        self.restoreCursor()

    def isVisible(self, shape):
        return self.visible.get(shape, True)

    def drawing(self):
        return self.mode == self.CREATE

    def editing(self):
        return self.mode == self.EDIT

    def setEditing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE
        if not value:
            self.unHighlight()
            self.deSelectShape()

    def unHighlight(self):
        if self.hShape:
            self.hShape.highlightClear()
            self.update()
        self.prevhShape = self.hShape
        self.prevhVertex = self.hVertex
        self.prevhEdge = self.hEdge
        self.hShape = self.hVertex = self.hEdge = None

    def selectedVertex(self):
        return self.hVertex is not None

    def set_show_cross_line(self, enabled):
        """Set cross line visibility"""
        self.show_cross_line = enabled
        self.update()

    def mouseMoveEvent(self, ev):
        """Update line with last point and current coordinates."""
        try:
            pos = self.transformPos(ev.position())
        except AttributeError:
            return
        self.prevMovePoint = pos
        self.repaint()
        self.restoreCursor()
        if self.drawing():
            self.line.shape_type = self.createMode
            self.overrideCursor(CURSOR_DRAW)
            if not self.current:
                return
            if self.outOfPixmap(pos):
                pos = self.intersectionPoint(self.current[-1], pos)
            elif len(self.current) > 1 and self.createMode == 'polygon' and self.closeEnough(pos, self.current[0]):
                pos = self.current[0]
                self.overrideCursor(CURSOR_POINT)
                self.current.highlightVertex(0, Shape.NEAR_VERTEX)
            if self.createMode in ['polygon']:
                self.line[0] = self.current[-1]
                self.line[1] = pos
            self.repaint()
            self.current.highlightClear()
            return
        if QtCore.Qt.MouseButton.RightButton & ev.buttons():
            if self.selectedShapesCopy and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShapes(self.selectedShapesCopy, pos)
                self.repaint()
            elif self.selectedShapes:
                self.selectedShapesCopy = [s.copy() for s in self.selectedShapes]
                self.repaint()
            return
        if QtCore.Qt.MouseButton.LeftButton & ev.buttons():
            if self.selectedVertex():
                self.boundedMoveVertex(pos)
                self.repaint()
                self.movingShape = True
            elif self.selectedShapes and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShapes(self.selectedShapes, pos)
                self.repaint()
                self.movingShape = True
            return
        self.setToolTip(self.tr('Image'))
        for shape in reversed([s for s in self.shapes if self.isVisible(s)]):
            index = shape.nearestVertex(pos, self.epsilon / self.scale)
            index_edge = shape.nearestEdge(pos, self.epsilon / self.scale)
            if index is not None:
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.prevhVertex = self.hVertex = index
                self.prevhShape = self.hShape = shape
                self.prevhEdge = self.hEdge = index_edge
                shape.highlightVertex(index, shape.MOVE_VERTEX)
                self.overrideCursor(CURSOR_POINT)
                self.setToolTip(self.tr('Click & drag to move point'))
                self.setStatusTip(self.toolTip())
                self.update()
                break
            elif shape.containsPoint(pos):
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.prevhVertex = self.hVertex
                self.hVertex = None
                self.prevhShape = self.hShape = shape
                self.prevhEdge = self.hEdge = index_edge
                self.setToolTip(self.tr("Click & drag to move shape '%s'") % shape.label)
                if shape.group_id != None and self.current_annotation_mode == 'video':
                    self.setToolTip(self.tr(f'ID {str(shape.group_id)} {shape.label} {shape.content}'))
                else:
                    self.setToolTip(self.tr(f'{shape.label} {shape.content}'))
                self.setStatusTip(self.toolTip())
                self.overrideCursor(CURSOR_GRAB)
                self.update()
                break
        else:
            self.unHighlight()
        self.edgeSelected.emit(self.hEdge is not None, self.hShape)
        self.vertexSelected.emit(self.hVertex is not None)

    def addPointToEdge(self):
        shape = self.prevhShape
        index = self.prevhEdge
        point = self.prevMovePoint
        if shape is None or index is None or point is None:
            return
        shape.insertPoint(index, point)
        shape.highlightVertex(index, shape.MOVE_VERTEX)
        self.hShape = shape
        self.hVertex = index
        self.hEdge = None
        self.movingShape = True

    def removeSelectedPoint(self):
        shape = self.prevhShape
        point = self.prevMovePoint
        if shape is None or point is None:
            return
        index = shape.nearestVertex(point, self.epsilon)
        shape.removePoint(index)
        self.hShape = shape
        self.hVertex = None
        self.hEdge = None
        self.movingShape = True

    def corrected_pos_into_pixmap(self, pos):
        x = pos.x()
        y = pos.y()
        x = min(self.pixmap.width(), max(0, x))
        y = min(self.pixmap.height(), max(0, y))
        res = QtCore.QPointF(x, y)
        return res

    def mousePressEvent(self, ev):
        pos = self.transformPos(ev.position())
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.drawing() and self.SAM_mode == '':
                if self.current:
                    if self.createMode == 'polygon':
                        self.current.addPoint(self.line[1])
                        self.line[0] = self.current[-1]
                        if self.current.isClosed():
                            self.finalise()
                elif not self.outOfPixmap(pos):
                    self.current = Shape(shape_type=self.createMode)
                    self.current.addPoint(pos)
                    self.line.points = [pos, pos]
                    self.setHiding()
                    self.drawingPolygon.emit(True)
                    self.update()
            elif self.SAM_mode == 'add point':
                if not self.outOfPixmap(pos):
                    self.SAM_coordinates.append([pos.x(), pos.y(), 1])
                    self.pointAdded.emit()
            elif self.SAM_mode == 'remove point':
                if not self.outOfPixmap(pos):
                    self.SAM_coordinates.append([pos.x(), pos.y(), 0])
                    self.pointAdded.emit()
            elif self.SAM_mode == 'select rect':
                self.SAM_rect.append(self.corrected_pos_into_pixmap(pos))
                if len(self.SAM_rect) == 2:
                    self.SAM_rects = [self.SAM_rect]
                    self.pointAdded.emit()
                    self.SAM_rect = []
            elif self.tracking_area == 'drawing':
                corrected_pos = self.corrected_pos_into_pixmap(pos)
                self.tracking_area_polygon.append([corrected_pos.x(), corrected_pos.y()])
            else:
                group_mode = ev.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
                self.selectShapePoint(pos, multiple_selection_mode=group_mode)
                self.prevPoint = pos
                self.repaint()
        elif ev.button() == QtCore.Qt.MouseButton.RightButton and self.editing():
            group_mode = ev.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
            self.selectShapePoint(pos, multiple_selection_mode=group_mode)
            self.prevPoint = pos
            self.repaint()

    def handle_right_click(self, menu):
        try:
            setEnabledd = menu.actions()[7].text() == 'Edit &Label' and menu.actions()[7].isEnabled()
            if menu.actions()[10].text() == '&Mark as key':
                menu.actions()[10].setEnabled(setEnabledd)
            if menu.actions()[11].text() == '&Scale':
                menu.actions()[11].setEnabled(setEnabledd)
        except:
            pass
        return menu

    def mouseReleaseEvent(self, ev):
        pos = self.transformPos(ev.position())
        if ev.button() == QtCore.Qt.MouseButton.RightButton:
            menu = self.menus[len(self.selectedShapesCopy) > 0]
            menu = self.handle_right_click(menu)
            self.restoreCursor()
            if not menu.exec(self.mapToGlobal(ev.pos())) and self.selectedShapesCopy:
                self.selectedShapesCopy = []
                self.repaint()
        elif ev.button() == QtCore.Qt.MouseButton.LeftButton and self.selectedShapes:
            self.overrideCursor(CURSOR_GRAB)
            if self.editing() and ev.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier:
                self.addPointToEdge()
        elif ev.button() == QtCore.Qt.MouseButton.LeftButton and self.selectedVertex():
            if self.editing() and ev.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier:
                self.removeSelectedPoint()
        elif ev.button() == QtCore.Qt.MouseButton.LeftButton and len(self.SAM_rect) == 1:
            if abs(pos.x() - self.SAM_rect[0].x()) + abs(pos.y() - self.SAM_rect[0].y()) > 50:
                self.SAM_rect.append(self.corrected_pos_into_pixmap(pos))
                self.SAM_rects = [self.SAM_rect]
                self.pointAdded.emit()
                self.SAM_rect = []
        if self.movingShape and self.hShape:
            index = self.shapes.index(self.hShape)
            if self.shapesBackups[-1][index].points != self.shapes[index].points:
                self.storeShapes()
                self.shapeMoved.emit()
            self.movingShape = False
            self.APPrefresh.emit(True)

    def endMove(self, copy):
        assert self.selectedShapes and self.selectedShapesCopy
        assert len(self.selectedShapesCopy) == len(self.selectedShapes)
        if copy:
            for i, shape in enumerate(self.selectedShapesCopy):
                self.shapes.append(shape)
                self.selectedShapes[i].selected = False
                self.selectedShapes[i] = shape
        else:
            for i, shape in enumerate(self.selectedShapesCopy):
                self.selectedShapes[i].points = shape.points
        self.selectedShapesCopy = []
        self.repaint()
        self.storeShapes()
        return True

    def hideBackroundShapes(self, value):
        self.hideBackround = value
        if self.selectedShapes:
            self.setHiding(True)
            self.update()

    def setHiding(self, enable=True):
        self._hideBackround = self.hideBackround if enable else False

    def canCloseShape(self):
        return self.drawing() and self.current and (len(self.current) > 2)

    def mouseDoubleClickEvent(self, ev):
        if self.double_click == 'close' and self.canCloseShape() and (len(self.current) > 3):
            self.current.popPoint()
            self.finalise()
        if self.tracking_area == 'drawing':
            self.tracking_area = 'drawn'
            self.update()

    def selectShapes(self, shapes):
        self.setHiding()
        self.selectionChanged.emit(shapes)
        self.update()

    def selectShapePoint(self, point, multiple_selection_mode):
        """Select the first shape created which contains this point."""
        if self.selectedVertex():
            index, shape = (self.hVertex, self.hShape)
            shape.highlightVertex(index, shape.MOVE_VERTEX)
        else:
            for shape in reversed(self.shapes):
                if self.isVisible(shape) and shape.containsPoint(point):
                    self.calculateOffsets(shape, point)
                    self.setHiding()
                    if multiple_selection_mode:
                        if shape not in self.selectedShapes:
                            self.selectionChanged.emit(self.selectedShapes + [shape])
                    else:
                        self.selectionChanged.emit([shape])
                    return
        self.deSelectShape()

    def calculateOffsets(self, shape, point):
        rect = shape.boundingRect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = rect.x() + rect.width() - 1 - point.x()
        y2 = rect.y() + rect.height() - 1 - point.y()
        self.offsets = (QtCore.QPoint(x1, y1), QtCore.QPoint(x2, y2))

    def boundedMoveVertex(self, pos):
        index, shape = (self.hVertex, self.hShape)
        point = shape[index]
        if self.outOfPixmap(pos):
            pos = self.intersectionPoint(point, pos)
        pos = QtCore.QPointF(pos)
        shape.moveVertexBy(index, pos - point)

    def boundedMoveShapes(self, shapes, pos):
        if self.outOfPixmap(pos):
            return False
        o1 = pos + QtCore.QPointF(self.offsets[0])
        if self.outOfPixmap(o1):
            pos -= QtCore.QPoint(min(0, o1.x()), min(0, o1.y()))
        o2 = pos + QtCore.QPointF(self.offsets[1])
        if self.outOfPixmap(o2):
            pos += QtCore.QPoint(min(0, self.pixmap.width() - o2.x()), min(0, self.pixmap.height() - o2.y()))
        dp = pos - self.prevPoint
        if dp:
            for shape in shapes:
                shape.moveBy(dp)
            self.prevPoint = pos
            return True
        return False

    def deSelectShape(self):
        if self.selectedShapes:
            self.setHiding(False)
            self.selectionChanged.emit([])
            self.update()

    def deleteSelected(self):
        deleted_shapes = []
        if self.selectedShapes:
            for shape in self.selectedShapes:
                self.shapes.remove(shape)
                deleted_shapes.append(shape)
            self.storeShapes()
            self.selectedShapes = []
            self.update()
        return deleted_shapes

    def deleteShape(self, shape):
        if shape in self.selectedShapes:
            self.selectedShapes.remove(shape)
        if shape in self.shapes:
            self.shapes.remove(shape)
        self.storeShapes()
        self.update()

    def copySelectedShapes(self):
        if self.selectedShapes:
            self.selectedShapesCopy = [s.copy() for s in self.selectedShapes]
            self.boundedShiftShapes(self.selectedShapesCopy)
            self.endMove(copy=True)
        return self.selectedShapes

    def boundedShiftShapes(self, shapes):
        point = shapes[0][0]
        offset = QtCore.QPoint(2.0, 2.0)
        self.offsets = (QtCore.QPoint(), QtCore.QPoint())
        self.prevPoint = point
        if not self.boundedMoveShapes(shapes, point - offset):
            self.boundedMoveShapes(shapes, point + offset)

    def paintEvent(self, event):
        if not self.pixmap and (not self.is_loading):
            return super(Canvas, self).paintEvent(event)
        p = self._painter
        p.begin(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())
        p.drawPixmap(0, 0, self.pixmap)
        Shape.scale = self.scale
        if self.is_loading:
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(QtGui.QColor(0, 0, 0, 100))
            p.drawRect(self.pixmap.rect())
            p.setPen(QtGui.QColor(255, 255, 255))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.save()
            p.translate(self.pixmap.width() / 2, self.pixmap.height() / 2 - 50)
            p.rotate(self.loading_angle)
            p.drawEllipse(-20, -20, 40, 40)
            p.drawLine(0, 0, 0, -20)
            p.restore()
            self.loading_angle += 5
            if self.loading_angle >= 360:
                self.loading_angle = 0
            p.setPen(QtGui.QColor(255, 255, 255))
            try:
                fontsize = self.pixmap.width() / 50
                p.setFont(QtGui.QFont('Arial', fontsize))
            except:
                p.setFont(QtGui.QFont('Arial', 20))
            p.drawText(self.pixmap.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, self.loading_text)
            p.end()
            self.update()
            return
        for shape in self.shapes:
            if (shape.selected or not self._hideBackround) and self.isVisible(shape):
                shape.fill = shape.selected or shape == self.hShape
                shape.paint(p)
        if self.current:
            self.current.paint(p)
            self.line.paint(p)
        if self.selectedShapesCopy:
            for s in self.selectedShapesCopy:
                s.paint(p)
        if self.fillDrawing() and self.createMode == 'polygon' and (self.current is not None) and (len(self.current.points) >= 2):
            drawing_shape = self.current.copy()
            drawing_shape.addPoint(self.line[1])
            drawing_shape.fill = True
            drawing_shape.paint(p)
        if self.show_cross_line:
            pen = QtGui.QPen(QtGui.QColor('#00FF00'), max(1, int(round(2.0 / Shape.scale))), QtCore.Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.setOpacity(0.5)
            mouseX = min(self.pixmap.width(), max(0, self.prevMovePoint.x()))
            mouseY = min(self.pixmap.height(), max(0, self.prevMovePoint.y()))
            p.drawLine(QtCore.QPointF(mouseX, 0), QtCore.QPointF(mouseX, self.pixmap.height()))
            p.drawLine(QtCore.QPointF(0, mouseY), QtCore.QPointF(self.pixmap.width(), mouseY))
        if len(self.SAM_rect) == 1:
            pen = QtGui.QPen(QtGui.QColor('#FF0000'), 2 * max(1, int(round(2.0 / Shape.scale))), QtCore.Qt.PenStyle.SolidLine)
            p.setPen(pen)
            p.setOpacity(0.8)
            point1 = [self.SAM_rect[0].x(), self.SAM_rect[0].y()]
            corrected = self.corrected_pos_into_pixmap(self.prevMovePoint)
            point2 = [corrected.x(), corrected.y()]
            x1 = min(point1[0], point2[0])
            y1 = min(point1[1], point2[1])
            w = abs(point1[0] - point2[0])
            h = abs(point1[1] - point2[1])
            p.drawRect(x1, y1, w, h)
        if len(self.SAM_coordinates) != 0:
            for point in self.SAM_coordinates:
                color = '#FF0000' if point[2] == 0 else '#19EB25'
                pen = QtGui.QPen(QtGui.QColor(color), 5 * max(1, int(round(2.0 / Shape.scale))), QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap)
                p.setPen(pen)
                p.setOpacity(0.8)
                p.drawPoint(point[0], point[1])
        if len(self.SAM_rects) != 0:
            box = self.SAM_rects[-1]
            pen = QtGui.QPen(QtGui.QColor('#2D7CFA'), 2 * max(1, int(round(2.0 / Shape.scale))), QtCore.Qt.PenStyle.SolidLine)
            p.setPen(pen)
            p.setOpacity(0.8)
            point1 = [box[0].x(), box[0].y()]
            point2 = [box[1].x(), box[1].y()]
            x1 = min(point1[0], point2[0])
            y1 = min(point1[1], point2[1])
            w = abs(point1[0] - point2[0])
            h = abs(point1[1] - point2[1])
            p.drawRect(x1, y1, w, h)
        if self.tracking_area != '':
            pen = QtGui.QPen(QtGui.QColor('#FF0000'), 2 * max(1, int(round(2.0 / Shape.scale))), QtCore.Qt.PenStyle.SolidLine)
            p.setPen(pen)
            p.setOpacity(0.1)
            p.setBrush(QtGui.QColor('#FF0000'))
            if len(self.tracking_area_polygon) > 0:
                corrected = self.corrected_pos_into_pixmap(self.prevMovePoint)
                point2 = [corrected.x(), corrected.y()]
                total = copy.deepcopy(self.tracking_area_polygon)
                if self.tracking_area == 'drawing':
                    total.append(point2)
                total = [QtCore.QPoint(p[0], p[1]) for p in total]
                p.drawPolygon(total)
                p.setOpacity(0.7)
                if self.tracking_area == 'drawing':
                    p.drawPolyline(total)
                else:
                    total.append(total[0])
                    p.drawPolyline(total)
        p.end()

    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical ones."""
        return point / self.scale - QtCore.QPointF(self.offsetToCenter())

    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = (self.pixmap.width() * s, self.pixmap.height() * s)
        aw, ah = (area.width(), area.height())
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QtCore.QPoint(x, y)

    def outOfPixmap(self, p):
        w, h = (self.pixmap.width(), self.pixmap.height())
        return not (0 <= p.x() <= w - 1 and 0 <= p.y() <= h - 1)

    def finalise(self, SAM_SHAPE=False):
        if SAM_SHAPE:
            assert self.SAM_current
            self.SAM_current.close()
            self.storeShapes()
            self.SAM_current = None
            self.setHiding(False)
            self.newShape.emit()
            self.update()
        else:
            assert self.current
            self.current.close()
            self.shapes.append(self.current)
            self.storeShapes()
            self.current = None
            self.setHiding(False)
            self.newShape.emit()
            self.update()

    def closeEnough(self, p1, p2):
        return labelme.utils.distance(p1 - p2) < self.epsilon / self.scale

    def intersectionPoint(self, p1, p2):
        size = self.pixmap.size()
        points = [(0, 0), (size.width() - 1, 0), (size.width() - 1, size.height() - 1), (0, size.height() - 1)]
        x1 = min(max(p1.x(), 0), size.width() - 1)
        y1 = min(max(p1.y(), 0), size.height() - 1)
        x2, y2 = (p2.x(), p2.y())
        d, i, (x, y) = min(self.intersectingEdges((x1, y1), (x2, y2), points))
        x3, y3 = points[i]
        x4, y4 = points[(i + 1) % 4]
        if (x, y) == (x1, y1):
            if x3 == x4:
                return QtCore.QPoint(x3, min(max(0, y2), max(y3, y4)))
            else:
                return QtCore.QPoint(min(max(0, x2), max(x3, x4)), y3)
        return QtCore.QPoint(x, y)

    def intersectingEdges(self, point1, point2, points):
        """Find intersecting edges.

        For each edge formed by `points', yield the intersection
        with the line segment `(x1,y1) - (x2,y2)`, if it exists.
        Also return the distance of `(x2,y2)' to the middle of the
        edge along with its index, so that the one closest can be chosen.
        """
        x1, y1 = point1
        x2, y2 = point2
        for i in range(4):
            x3, y3 = points[i]
            x4, y4 = points[(i + 1) % 4]
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
            nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
            if denom == 0:
                continue
            ua, ub = (nua / denom, nub / denom)
            if 0 <= ua <= 1 and 0 <= ub <= 1:
                x = x1 + ua * (x2 - x1)
                y = y1 + ua * (y2 - y1)
                m = QtCore.QPoint((x3 + x4) / 2, (y3 + y4) / 2)
                d = labelme.utils.distance(m - QtCore.QPoint(x2, y2))
                yield (d, i, (x, y))

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    def wheelEvent(self, ev):
        mods = ev.modifiers()
        delta = ev.angleDelta()
        if mods.value:
            self.zoomRequest.emit(delta.y(), ev.position().toPoint())
        else:
            self.scrollRequest.emit(delta.x(), QtCore.Qt.Orientation.Horizontal.value)
            self.scrollRequest.emit(delta.y(), QtCore.Qt.Orientation.Vertical.value)
        ev.accept()

    def keyPressEvent(self, ev):
        key = ev.key()
        if key == QtCore.Qt.Key.Key_Return:
            if self.SAM_mode != '':
                self.samFinish.emit()
            elif self.tracking_area:
                self.tracking_area = 'drawn'
                self.update()
            elif self.canCloseShape():
                self.finalise()

    def cancelManualDrawing(self):
        self.current = None
        self.drawingPolygon.emit(False)
        self.update()

    def setLastLabel(self, text, flags):
        assert text
        self.shapes[-1].label = text
        self.shapes[-1].flags = flags
        self.shapesBackups.pop()
        self.storeShapes()
        return self.shapes[-1]

    def undoLastLine(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        if self.createMode in ['polygon']:
            self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)

    def undoLastPoint(self):
        if not self.current or self.current.isClosed():
            return
        self.current.popPoint()
        if len(self.current) > 0:
            self.line[0] = self.current[-1]
        else:
            self.current = None
            self.drawingPolygon.emit(False)
        self.update()

    def loadPixmap(self, pixmap, clear_shapes=True):
        self.pixmap = pixmap
        if clear_shapes:
            self.shapes = []
        self.update()

    def loadShapes(self, shapes, replace=True):
        if replace:
            self.shapes = list(shapes)
        else:
            self.shapes.extend(shapes)
        self.storeShapes()
        self.current = None
        self.hShape = None
        self.hVertex = None
        self.hEdge = None
        self.update()

    def setShapeVisible(self, shape, value):
        self.visible[shape] = value
        self.update()

    def overrideCursor(self, cursor):
        self.restoreCursor()
        self._cursor = cursor
        QtWidgets.QApplication.setOverrideCursor(cursor)

    def restoreCursor(self):
        QtWidgets.QApplication.restoreOverrideCursor()

    def resetState(self):
        self.restoreCursor()
        self.pixmap = None
        self.shapesBackups = []
        self.update()

def __init__(self, *args, **kwargs):
    self.epsilon = kwargs.pop('epsilon', 10.0)
    self.double_click = kwargs.pop('double_click', 'close')
    if self.double_click not in [None, 'close']:
        raise ValueError('Unexpected value for double_click event: {}'.format(self.double_click))
    self.num_backups = kwargs.pop('num_backups', 10)
    super(Canvas, self).__init__(*args, **kwargs)
    self.mode = self.EDIT
    self.shapes = []
    self.SAM_mode = ''
    self.SAM_coordinates = []
    self.SAM_rect = []
    self.SAM_rects = []
    self.SAM_painter = QtGui.QPainter()
    self.SAM_current = None
    self.show_cross_line = True
    self.is_loading = False
    self.loading_angle = 0
    self.loading_text = 'Loading...'
    self.tracking_area = ''
    self.tracking_area_polygon = []
    self.current_annotation_mode = ''
    self.shapesBackups = []
    self.current = None
    self.selectedShapes = []
    self.selectedShapesCopy = []
    self.line = Shape()
    self.prevPoint = QtCore.QPoint()
    self.prevMovePoint = QtCore.QPoint()
    self.offsets = (QtCore.QPoint(), QtCore.QPoint())
    self.scale = 1.0
    self.pixmap = QtGui.QPixmap()
    self.visible = {}
    self._hideBackround = False
    self.hideBackround = False
    self.hShape = None
    self.prevhShape = None
    self.hVertex = None
    self.prevhVertex = None
    self.hEdge = None
    self.prevhEdge = None
    self.movingShape = False
    self._painter = QtGui.QPainter()
    self._cursor = CURSOR_DEFAULT
    self.menus = (QtWidgets.QMenu(), QtWidgets.QMenu())
    self.setMouseTracking(True)
    self.setFocusPolicy(QtCore.Qt.FocusPolicy.WheelFocus)

def handle_right_click(self, menu):
    try:
        setEnabledd = menu.actions()[7].text() == 'Edit &Label' and menu.actions()[7].isEnabled()
        if menu.actions()[10].text() == '&Mark as key':
            menu.actions()[10].setEnabled(setEnabledd)
        if menu.actions()[11].text() == '&Scale':
            menu.actions()[11].setEnabled(setEnabledd)
    except:
        pass
    return menu

class MergeFeatureUI:

    def __init__(self, parent):
        self.parent = parent
        self.selectedmodels = []

    def mergeSegModels(self):
        models = []
        with open('saved_models.json') as json_file:
            data = json.load(json_file)
            for model in data.keys():
                if 'YOLOv8' not in model:
                    models.append(model)
        dialog = QtWidgets.QDialog(self.parent)
        dialog.setWindowTitle('Select Models')
        dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        dialog.resize(200, 250)
        dialog.setMinimumSize(QtCore.QSize(200, 200))
        verticalLayout = QtWidgets.QVBoxLayout(dialog)
        verticalLayout.setObjectName('verticalLayout')
        scrollArea = QtWidgets.QScrollArea(dialog)
        scrollArea.setWidgetResizable(True)
        scrollArea.setObjectName('scrollArea')
        scrollAreaWidgetContents = QtWidgets.QWidget()
        scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 478, 478))
        scrollAreaWidgetContents.setObjectName('scrollAreaWidgetContents')
        verticalLayout_2 = QtWidgets.QVBoxLayout(scrollAreaWidgetContents)
        verticalLayout_2.setObjectName('verticalLayout_2')
        self.scrollAreaWidgetContents = scrollAreaWidgetContents
        scrollArea.setWidget(scrollAreaWidgetContents)
        verticalLayout.addWidget(scrollArea)
        buttonBox = QtWidgets.QDialogButtonBox(dialog)
        buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok)
        buttonBox.setObjectName('buttonBox')
        verticalLayout.addWidget(buttonBox)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        self.models = []
        for i in range(len(models)):
            self.models.append(QtWidgets.QCheckBox(models[i], dialog))
            verticalLayout_2.addWidget(self.models[i])
        dialog.show()
        dialog.exec()
        self.selectedmodels.clear()
        for i in range(len(self.models)):
            if self.models[i].isChecked():
                self.selectedmodels.append(self.models[i].text())
        print(self.selectedmodels)
        return self.selectedmodels

def mergeSegModels(self):
    models = []
    with open('saved_models.json') as json_file:
        data = json.load(json_file)
        for model in data.keys():
            if 'YOLOv8' not in model:
                models.append(model)
    dialog = QtWidgets.QDialog(self.parent)
    dialog.setWindowTitle('Select Models')
    dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
    dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
    dialog.resize(200, 250)
    dialog.setMinimumSize(QtCore.QSize(200, 200))
    verticalLayout = QtWidgets.QVBoxLayout(dialog)
    verticalLayout.setObjectName('verticalLayout')
    scrollArea = QtWidgets.QScrollArea(dialog)
    scrollArea.setWidgetResizable(True)
    scrollArea.setObjectName('scrollArea')
    scrollAreaWidgetContents = QtWidgets.QWidget()
    scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 478, 478))
    scrollAreaWidgetContents.setObjectName('scrollAreaWidgetContents')
    verticalLayout_2 = QtWidgets.QVBoxLayout(scrollAreaWidgetContents)
    verticalLayout_2.setObjectName('verticalLayout_2')
    self.scrollAreaWidgetContents = scrollAreaWidgetContents
    scrollArea.setWidget(scrollAreaWidgetContents)
    verticalLayout.addWidget(scrollArea)
    buttonBox = QtWidgets.QDialogButtonBox(dialog)
    buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
    buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok)
    buttonBox.setObjectName('buttonBox')
    verticalLayout.addWidget(buttonBox)
    buttonBox.accepted.connect(dialog.accept)
    buttonBox.rejected.connect(dialog.reject)
    self.models = []
    for i in range(len(models)):
        self.models.append(QtWidgets.QCheckBox(models[i], dialog))
        verticalLayout_2.addWidget(self.models[i])
    dialog.show()
    dialog.exec()
    self.selectedmodels.clear()
    for i in range(len(self.models)):
        if self.models[i].isChecked():
            self.selectedmodels.append(self.models[i].text())
    print(self.selectedmodels)
    return self.selectedmodels

class ThresholdWidget(QtWidgets.QDialog):

    def __init__(self):
        super(ThresholdWidget, self).__init__()
        self.setModal(True)
        self.setWindowTitle('Enter Threshold')
        self.threshold = 0.5
        self.threshold = self._createQLineEdit()

    def _createQLineEdit(self):
        threshold = QtWidgets.QLineEdit()
        threshold.setRange(0, 1)
        threshold.setValue(0.5)
        threshold.valueChanged.connect(self.onNewValue)
        return threshold

def _createQLineEdit(self):
    threshold = QtWidgets.QLineEdit()
    threshold.setRange(0, 1)
    threshold.setValue(0.5)
    threshold.valueChanged.connect(self.onNewValue)
    return threshold

def PopUp(config):
    """
    Summary:
        Show a dialog to choose the interpolation options.
        (   interpolate only missed frames between detected frames, 
            interpolate all frames between your KEY frames, 
            interpolate ALL frames with SAM (more precision, more time) )
            
    Args:
        config: a dictionary of configurations
        
    Returns:
        result: the result of the dialog
        config: the updated dictionary of configurations
    """

    def show_unshow_overwrite():
        if with_sam.isChecked():
            config.update({'interpolationDefMethod': 'SAM'})
            overwrite_checkBox.setEnabled(True)
        else:
            config.update({'interpolationDefMethod': 'Linear'})
            overwrite_checkBox.setEnabled(False)
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle('Choose Interpolation Options')
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.resize(250, 100)
    dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
    layout = QtWidgets.QVBoxLayout()
    label = QtWidgets.QLabel('Choose Interpolation Options')
    label.setFont(QtGui.QFont('Arial', 10))
    method_label = QtWidgets.QLabel('Interpolation Method')
    between_label = QtWidgets.QLabel('Interpolation Between')
    layout.addWidget(label)
    method_group = QtWidgets.QButtonGroup()
    with_linear = QtWidgets.QRadioButton('Linear Interpolation')
    with_sam = QtWidgets.QRadioButton('SAM Interpolation')
    method_group.addButton(with_linear)
    method_group.addButton(with_sam)
    with_linear.toggled.connect(show_unshow_overwrite)
    with_sam.toggled.connect(show_unshow_overwrite)
    layout.addWidget(method_label)
    method_layout = QtWidgets.QHBoxLayout()
    method_layout.addWidget(with_linear)
    method_layout.addWidget(with_sam)
    layout.addLayout(method_layout)
    between_group = QtWidgets.QButtonGroup()
    with_keyframes = QtWidgets.QRadioButton('Selected Keyframes')
    without_keyframes = QtWidgets.QRadioButton('Detected Frames')
    between_group.addButton(with_keyframes)
    between_group.addButton(without_keyframes)
    with_keyframes.toggled.connect(lambda: config.update({'interpolationDefType': 'key' * with_keyframes.isChecked()}))
    without_keyframes.toggled.connect(lambda: config.update({'interpolationDefType': 'all' * without_keyframes.isChecked()}))
    layout.addWidget(between_label)
    keyframes_layout = QtWidgets.QHBoxLayout()
    keyframes_layout.addWidget(with_keyframes)
    keyframes_layout.addWidget(without_keyframes)
    layout.addLayout(keyframes_layout)
    overwrite_checkBox = QtWidgets.QCheckBox('Overwrite used frames with SAM')
    overwrite_checkBox.setChecked(config['interpolationOverwrite'])
    overwrite_checkBox.toggled.connect(lambda: config.update({'interpolationOverwrite': overwrite_checkBox.isChecked()}))
    layout.addWidget(overwrite_checkBox)
    show_unshow_overwrite()
    with_linear.setChecked(True)
    buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
    buttonBox.accepted.connect(dialog.accept)
    layout.addWidget(buttonBox)
    dialog.setLayout(layout)
    result = dialog.exec()
    return (result, config)

def PopUp():
    """

    Description:
    This function displays a dialog box with preferences for the LabelMe application, including theme and notification settings.

    Parameters:
    This function takes no parameters.

    Returns:
    If the user clicks the OK button, this function writes the new theme and notification settings to the config file and returns `QtWidgets.QDialog.DialogCode.Accepted`. If the user clicks the Cancel button, this function does not write any changes to the config file and returns `QtWidgets.QDialog.Rejected`.

    Libraries:
    This function requires the following libraries to be installed:
    - yaml
    - PyQt6.QtWidgets
    - PyQt6.QtGui
    - PyQt6.QtCore
    """
    with open('labelme/config/default_config.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle('Preferences')
    dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
    themeLabel = QtWidgets.QLabel('Theme Settings 🌓')
    themeLabel.setFont(QtGui.QFont('Arial', 10, QtGui.QFont.Weight.Bold))
    theme_note_label = QtWidgets.QLabel('Requires app restart to take effect')
    notificationLabel = QtWidgets.QLabel('Notifications Settings 🔔')
    notificationLabel.setFont(QtGui.QFont('Arial', 10, QtGui.QFont.Weight.Bold))
    notification_note_label = QtWidgets.QLabel("Notifications works only for long tasks and if the app isn't focused")
    current_theme = config['theme']
    current_mute = config['mute']
    autoButton = QtWidgets.QRadioButton('OS Default')
    lightButton = QtWidgets.QRadioButton('Light')
    darkButton = QtWidgets.QRadioButton('Dark')
    if current_theme == 'auto':
        autoButton.setChecked(True)
    elif current_theme == 'light':
        lightButton.setChecked(True)
    elif current_theme == 'dark':
        darkButton.setChecked(True)
    autoImage = QtGui.QPixmap('labelme/icons/auto-img.png').scaledToWidth(128)
    lightImage = QtGui.QPixmap('labelme/icons/light-img.png').scaledToWidth(128)
    darkImage = QtGui.QPixmap('labelme/icons/dark-img.png').scaledToWidth(128)
    autoLabel = QtWidgets.QLabel()
    autoLabel.setPixmap(autoImage)
    lightLabel = QtWidgets.QLabel()
    lightLabel.setPixmap(lightImage)
    darkLabel = QtWidgets.QLabel()
    darkLabel.setPixmap(darkImage)
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(themeLabel)
    layout.addWidget(theme_note_label)
    buttonLayout = QtWidgets.QHBoxLayout()
    buttonLayout.addWidget(autoButton)
    buttonLayout.addWidget(lightButton)
    buttonLayout.addWidget(darkButton)
    layout.addLayout(buttonLayout)
    imageLayout = QtWidgets.QHBoxLayout()
    imageLayout.addWidget(autoLabel)
    imageLayout.addWidget(lightLabel)
    imageLayout.addWidget(darkLabel)
    layout.addLayout(imageLayout)
    notificationCheckbox = QtWidgets.QCheckBox('Mute Notifications')
    notificationCheckbox.setChecked(current_mute)
    layout.addWidget(notificationLabel)
    layout.addWidget(notification_note_label)
    layout.addWidget(notificationCheckbox)
    dialog.setLayout(layout)
    okButton = QtWidgets.QPushButton('OK')
    cancelButton = QtWidgets.QPushButton('Cancel')
    buttonLayout = QtWidgets.QHBoxLayout()
    buttonLayout.addWidget(okButton)
    buttonLayout.addWidget(cancelButton)
    layout.addLayout(buttonLayout)
    okButton.clicked.connect(dialog.accept)
    cancelButton.clicked.connect(dialog.reject)
    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        if autoButton.isChecked():
            theme = 'auto'
        elif lightButton.isChecked():
            theme = 'light'
        elif darkButton.isChecked():
            theme = 'dark'
        mute = notificationCheckbox.isChecked()
        with open('labelme/config/default_config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        config['theme'] = theme
        config['mute'] = mute
        with open('labelme/config/default_config.yaml', 'w') as f:
            yaml.dump(config, f)

def PopUp():
    """
    Check for updates of DLTA-AI and display a message box with the result.

    The function checks the latest release of DLTA-AI on GitHub and compares it with the current version.
    If the latest release is newer than the current version, a message box is displayed with a button to
    download the latest version. Otherwise, a message box is displayed indicating that the user is using
    the latest version.

    Args:
        None

    Returns:
        None
    """
    from labelme import __version__
    updates = False
    tag = {}
    tag['href'] = None
    try:
        url = 'https://github.com/0ssamaak0/DLTA-AI/releases'
        html = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('a', class_='Link--primary')
        lastest_version = tag.text.lower().split('v')[1]
        if lastest_version != __version__:
            text = f'New version of DLTA-AI (v{lastest_version}) is available.\n You are currently using (v{__version__})\n'
            updates = True
        else:
            text = f'you are using the latest version of DLTA-AI (v{__version__})\n'
    except:
        text = f'You are using DLTA-AI (v{__version__})\n There was an error checking for updates.\n'
    msgBox = QMessageBox()
    msgBox.setWindowTitle('Check for Updates')
    msgBox.setFont(QFont('Arial', 10))
    msgBox.setText(text)
    if updates:
        msgBox.addButton(QMessageBox.StandardButton.Yes)
        msgBox.button(QMessageBox.StandardButton.Yes).setText('Get the Latest Version')
        msgBox.button(QMessageBox.StandardButton.Yes).clicked.connect(lambda: open_release(tag['href']))
    msgBox.addButton(QMessageBox.StandardButton.Close)
    msgBox.button(QMessageBox.StandardButton.Close).setText('Close')
    msgBox.exec()

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

class VideoFrameExtractor(QDialog):

    def __init__(self, mute=None, notification=None):
        super().__init__()
        self.mute = mute
        self.notification = notification
        self.setMinimumSize(500, 300)
        self.setWindowTitle('Open Video as Frames')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.sampling_max = 100
        self.vid_path = None
        self.sampling_rate = 1
        self.start_frame = 1
        self.end_frame = None
        self.fps = None
        self.stop = False
        self.path_name = None
        font = QFont()
        font.setBold(True)
        self.file_label = QLabel('Select a video file:')
        self.file_button = QPushButton('Open Video')
        self.file_button.clicked.connect(self.select_file)
        self.sampling_label = QLabel('Sampling rate:')
        self.sampling_slider = QSlider()
        self.sampling_slider.setOrientation(Qt.Orientation.Horizontal)
        self.sampling_slider.setRange(1, self.sampling_max)
        self.sampling_slider.setValue(1)
        self.sampling_slider.setEnabled(False)
        self.sampling_slider.valueChanged.connect(self.update_sampling_rate)
        self.sampling_edit = QLineEdit(str(self.sampling_slider.value()))
        self.sampling_edit.setFont(QFont('Arial', 10))
        self.sampling_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sampling_edit.setEnabled(False)
        self.sampling_edit.textChanged.connect(self.update_sampling_slider)
        self.sampling_time_label = QLabel('hh:mm:ss')
        self.sampling_time_label.setFont(font)
        self.sampling_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.start_label = QLabel('Start frame:')
        self.start_slider = QSlider()
        self.start_slider.setOrientation(Qt.Orientation.Horizontal)
        self.start_slider.setRange(0, 1000)
        self.start_slider.setValue(0)
        self.start_slider.setEnabled(False)
        self.start_slider.valueChanged.connect(self.update_start_frame)
        self.start_edit = QLineEdit(str(self.start_slider.value()))
        self.start_edit.setFont(QFont('Arial', 10))
        self.start_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_edit.setEnabled(False)
        self.start_edit.textChanged.connect(self.update_start_slider)
        self.start_time_label = QLabel('hh:mm:ss')
        self.start_time_label.setFont(font)
        self.start_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.end_label = QLabel('End frame:')
        self.end_slider = QSlider()
        self.end_slider.setOrientation(Qt.Orientation.Horizontal)
        self.end_slider.setRange(0, 1)
        self.end_slider.setValue(1)
        self.end_slider.setEnabled(False)
        self.end_slider.valueChanged.connect(self.update_end_frame)
        self.end_edit = QLineEdit(str(self.end_slider.value()))
        self.end_edit.setFont(QFont('Arial', 10))
        self.end_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.end_edit.setEnabled(False)
        self.end_edit.textChanged.connect(self.update_end_slider)
        self.end_time_label = QLabel('hh:mm:ss')
        self.end_time_label.setFont(font)
        self.end_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.extract_button = QPushButton('Extract Frames')
        self.extract_button.clicked.connect(self.extract_frames)
        self.extract_button.setEnabled(False)
        self.stop_button = QPushButton('Stop')
        self.stop_button.pressed.connect(self.stop_extraction)
        self.stop_button.setEnabled(False)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 150, 300, 20)
        self.progress_bar.setFormat('Waiting for extraction...')
        self.progress_bar.setValue(0)
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_button)
        sampling_layout = QHBoxLayout()
        inner_sampling_layout = QVBoxLayout()
        inner_sampling_layout.addWidget(self.sampling_label)
        inner_sampling_layout.addWidget(self.sampling_time_label)
        sampling_layout.addLayout(inner_sampling_layout)
        inner_sampling_layout = QVBoxLayout()
        inner_sampling_layout.addWidget(self.sampling_edit)
        inner_sampling_layout.addWidget(self.sampling_slider)
        sampling_layout.addLayout(inner_sampling_layout)
        range_layout = QHBoxLayout()
        start_layout = QHBoxLayout()
        inner_start_layout = QVBoxLayout()
        inner_start_layout.addWidget(self.start_label, alignment=Qt.AlignmentFlag.AlignLeft)
        inner_start_layout.addWidget(self.start_time_label, alignment=Qt.AlignmentFlag.AlignLeft)
        start_layout.addLayout(inner_start_layout)
        inner_start_layout = QVBoxLayout()
        inner_start_layout.addWidget(self.start_edit)
        inner_start_layout.addWidget(self.start_slider)
        start_layout.addLayout(inner_start_layout)
        end_layout = QHBoxLayout()
        inner_end_layout = QVBoxLayout()
        inner_end_layout.addWidget(self.end_label)
        inner_end_layout.addWidget(self.end_time_label)
        end_layout.addLayout(inner_end_layout)
        inner_end_layout = QVBoxLayout()
        inner_end_layout.addWidget(self.end_edit)
        inner_end_layout.addWidget(self.end_slider)
        end_layout.addLayout(inner_end_layout)
        range_layout.addLayout(start_layout)
        end_layout.setContentsMargins(20, 0, 0, 0)
        range_layout.addLayout(end_layout)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.extract_button)
        button_layout.addWidget(self.stop_button)
        main_layout = QVBoxLayout()
        main_layout.addLayout(file_layout)
        range_layout.setContentsMargins(0, 20, 0, 0)
        main_layout.addLayout(range_layout)
        main_layout.addLayout(sampling_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.progress_bar)
        self.setLayout(main_layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Video to Frames', '', 'Video Files (*.mp4 *.avi *.mov)')
        if file_path:
            self.vid_path = file_path
            self.file_label.setText(f'Selected video file: {self.vid_path}')
            self.sampling_slider.setEnabled(True)
            self.sampling_edit.setEnabled(True)
            self.start_slider.setEnabled(True)
            self.start_edit.setEnabled(True)
            self.end_slider.setEnabled(True)
            self.end_edit.setEnabled(True)
            self.extract_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet('background-color: red; color: white;')
            vidcap = cv2.VideoCapture(self.vid_path)
            self.fps = vidcap.get(cv2.CAP_PROP_FPS)
            self.max_frame = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.start_slider.setMaximum(self.max_frame)
            self.start_time_label.setText(self.get_time_string(0))
            self.end_slider.setMaximum(self.max_frame)
            self.end_slider.setValue(self.max_frame)
            self.end_edit.setText(str(self.end_slider.value()))
            self.end_time_label.setText(self.get_time_string(self.max_frame / self.fps))
            self.sampling_time_label.setText(self.get_time_string(1 / self.fps))
            self.sampling_slider.setMaximum(self.max_frame // 10)
            self.sampling_slider.setValue(self.max_frame // 100)
            self.sampling_max = self.max_frame // 10
        else:
            self.file_label.setText('No video is selected')
            self.sampling_slider.setEnabled(False)
            self.sampling_edit.setEnabled(False)
            self.start_slider.setEnabled(False)
            self.start_edit.setEnabled(False)
            self.end_slider.setEnabled(False)
            self.end_edit.setEnabled(False)

    def update_sampling_rate(self, value):
        self.sampling_rate = value
        self.sampling_edit.setText(str(value))

    def update_sampling_slider(self, text):
        try:
            value = int(text)
            if value < 1:
                value = 1
            elif value > self.sampling_max:
                value = self.sampling_max
            self.sampling_rate = value
            self.sampling_slider.setValue(value)
            if self.fps:
                self.sampling_time_label.setText(self.get_time_string(value / self.fps))
                if self.end_frame is not None:
                    self.progress_bar.setFormat(f'Will Extract {(self.end_frame - self.start_frame) // self.sampling_rate} Frames')
        except ValueError:
            pass

    def update_start_frame(self, value):
        self.start_frame = value
        self.start_edit.setText(str(value))

    def update_start_slider(self, text):
        try:
            value = int(text)
            if value < 0:
                value = 0
            elif self.end_frame is not None and value > self.end_frame:
                self.start_slider.setValue(self.end_frame)
                value = self.end_frame
            self.start_frame = value
            self.start_slider.setValue(value)
            if self.fps:
                self.start_time_label.setText(self.get_time_string(value / self.fps))
                if self.end_frame is not None:
                    self.progress_bar.setFormat(f'Will Extract {(self.end_frame - self.start_frame) // self.sampling_rate} Frames')
        except ValueError:
            pass

    def update_end_frame(self, value):
        self.end_frame = value
        self.end_edit.setText(str(value))

    def update_end_slider(self, text):
        try:
            value = int(text)
            if self.start_frame is not None and value < self.start_frame:
                value = self.start_frame
            self.end_frame = value
            self.end_slider.setValue(value)
            if self.fps:
                self.end_time_label.setText(self.get_time_string(value / self.fps))
                if self.end_frame is not None:
                    self.progress_bar.setFormat(f'Will Extract {(self.end_frame - self.start_frame) // self.sampling_rate} Frames')
        except ValueError:
            pass

    def extract_frames(self):
        try:
            self.path_name = self.vid_to_frames(self.vid_path, self.sampling_rate, self.start_frame, self.end_frame)
        except ValueError as e:
            self.progress_bar.setFormat(str(e))
            return
        self.close()
        return self.path_name

    def stop_extraction(self):
        self.stop = True

    def get_time_string(self, seconds, separator=':'):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f'{int(h):02d}{separator}{int(m):02d}{separator}{int(s):02d}'

    def vid_to_frames(self, vid_path, sampling_rate, start_frame, end_frame):
        """
        Extracts frames from a video file and saves them as JPEG images.

        Args:
            vid_path (str): Path to the video file.
            sampling_rate (int): How often to save a frame. For example, if sampling_rate = 2, every other frame will be saved.
            start_frame (int): Starting frame number.
            end_frame (int): Ending frame number.
        """
        if not os.path.exists(vid_path):
            raise ValueError('Video path does not exist')
        frames_path = ''.join([vid_path.split('.')[0], '_frames'])
        if not os.path.exists(frames_path):
            os.mkdir(frames_path)
        else:
            for file in os.listdir(frames_path):
                os.remove(os.path.join(frames_path, file))
        vidcap = cv2.VideoCapture(vid_path)
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        n_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f'Total number of frames: {n_frames}')
        count = start_frame
        success = True
        while success:
            success, image = vidcap.read()
            if count % sampling_rate == 0:
                time_in_sec = count / self.fps
                time_str = self.get_time_string(time_in_sec, separator='_')
                indented_count = str(count).zfill(len(str(n_frames)))
                cv2.imwrite(f'{frames_path}/frame_{indented_count}_time_{time_str}.jpg', image)
            self.progress_bar.setValue(int((count - start_frame) / (end_frame - start_frame) * 100))
            self.progress_bar.setFormat(f'{int((count - start_frame) / (end_frame - start_frame) * 100)}%')
            count += 1
            if count >= end_frame:
                self.progress_bar.setValue(100)
                break
            QtWidgets.QApplication.processEvents()
            if self.stop:
                self.stop = False
                self.progress_bar.setFormat('Extraction stopped')
                self.progress_bar.setValue(0)
                break
        try:
            if not self.mute:
                if not self.isActiveWindow():
                    self.notification(f'Video Extraction Completed')
        except:
            pass
        return frames_path

def __init__(self, mute=None, notification=None):
    super().__init__()
    self.mute = mute
    self.notification = notification
    self.setMinimumSize(500, 300)
    self.setWindowTitle('Open Video as Frames')
    self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
    self.sampling_max = 100
    self.vid_path = None
    self.sampling_rate = 1
    self.start_frame = 1
    self.end_frame = None
    self.fps = None
    self.stop = False
    self.path_name = None
    font = QFont()
    font.setBold(True)
    self.file_label = QLabel('Select a video file:')
    self.file_button = QPushButton('Open Video')
    self.file_button.clicked.connect(self.select_file)
    self.sampling_label = QLabel('Sampling rate:')
    self.sampling_slider = QSlider()
    self.sampling_slider.setOrientation(Qt.Orientation.Horizontal)
    self.sampling_slider.setRange(1, self.sampling_max)
    self.sampling_slider.setValue(1)
    self.sampling_slider.setEnabled(False)
    self.sampling_slider.valueChanged.connect(self.update_sampling_rate)
    self.sampling_edit = QLineEdit(str(self.sampling_slider.value()))
    self.sampling_edit.setFont(QFont('Arial', 10))
    self.sampling_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.sampling_edit.setEnabled(False)
    self.sampling_edit.textChanged.connect(self.update_sampling_slider)
    self.sampling_time_label = QLabel('hh:mm:ss')
    self.sampling_time_label.setFont(font)
    self.sampling_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
    self.start_label = QLabel('Start frame:')
    self.start_slider = QSlider()
    self.start_slider.setOrientation(Qt.Orientation.Horizontal)
    self.start_slider.setRange(0, 1000)
    self.start_slider.setValue(0)
    self.start_slider.setEnabled(False)
    self.start_slider.valueChanged.connect(self.update_start_frame)
    self.start_edit = QLineEdit(str(self.start_slider.value()))
    self.start_edit.setFont(QFont('Arial', 10))
    self.start_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.start_edit.setEnabled(False)
    self.start_edit.textChanged.connect(self.update_start_slider)
    self.start_time_label = QLabel('hh:mm:ss')
    self.start_time_label.setFont(font)
    self.start_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
    self.end_label = QLabel('End frame:')
    self.end_slider = QSlider()
    self.end_slider.setOrientation(Qt.Orientation.Horizontal)
    self.end_slider.setRange(0, 1)
    self.end_slider.setValue(1)
    self.end_slider.setEnabled(False)
    self.end_slider.valueChanged.connect(self.update_end_frame)
    self.end_edit = QLineEdit(str(self.end_slider.value()))
    self.end_edit.setFont(QFont('Arial', 10))
    self.end_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.end_edit.setEnabled(False)
    self.end_edit.textChanged.connect(self.update_end_slider)
    self.end_time_label = QLabel('hh:mm:ss')
    self.end_time_label.setFont(font)
    self.end_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
    self.extract_button = QPushButton('Extract Frames')
    self.extract_button.clicked.connect(self.extract_frames)
    self.extract_button.setEnabled(False)
    self.stop_button = QPushButton('Stop')
    self.stop_button.pressed.connect(self.stop_extraction)
    self.stop_button.setEnabled(False)
    self.progress_bar = QProgressBar(self)
    self.progress_bar.setGeometry(50, 150, 300, 20)
    self.progress_bar.setFormat('Waiting for extraction...')
    self.progress_bar.setValue(0)
    file_layout = QHBoxLayout()
    file_layout.addWidget(self.file_label)
    file_layout.addWidget(self.file_button)
    sampling_layout = QHBoxLayout()
    inner_sampling_layout = QVBoxLayout()
    inner_sampling_layout.addWidget(self.sampling_label)
    inner_sampling_layout.addWidget(self.sampling_time_label)
    sampling_layout.addLayout(inner_sampling_layout)
    inner_sampling_layout = QVBoxLayout()
    inner_sampling_layout.addWidget(self.sampling_edit)
    inner_sampling_layout.addWidget(self.sampling_slider)
    sampling_layout.addLayout(inner_sampling_layout)
    range_layout = QHBoxLayout()
    start_layout = QHBoxLayout()
    inner_start_layout = QVBoxLayout()
    inner_start_layout.addWidget(self.start_label, alignment=Qt.AlignmentFlag.AlignLeft)
    inner_start_layout.addWidget(self.start_time_label, alignment=Qt.AlignmentFlag.AlignLeft)
    start_layout.addLayout(inner_start_layout)
    inner_start_layout = QVBoxLayout()
    inner_start_layout.addWidget(self.start_edit)
    inner_start_layout.addWidget(self.start_slider)
    start_layout.addLayout(inner_start_layout)
    end_layout = QHBoxLayout()
    inner_end_layout = QVBoxLayout()
    inner_end_layout.addWidget(self.end_label)
    inner_end_layout.addWidget(self.end_time_label)
    end_layout.addLayout(inner_end_layout)
    inner_end_layout = QVBoxLayout()
    inner_end_layout.addWidget(self.end_edit)
    inner_end_layout.addWidget(self.end_slider)
    end_layout.addLayout(inner_end_layout)
    range_layout.addLayout(start_layout)
    end_layout.setContentsMargins(20, 0, 0, 0)
    range_layout.addLayout(end_layout)
    button_layout = QHBoxLayout()
    button_layout.addWidget(self.extract_button)
    button_layout.addWidget(self.stop_button)
    main_layout = QVBoxLayout()
    main_layout.addLayout(file_layout)
    range_layout.setContentsMargins(0, 20, 0, 0)
    main_layout.addLayout(range_layout)
    main_layout.addLayout(sampling_layout)
    main_layout.addLayout(button_layout)
    main_layout.addWidget(self.progress_bar)
    self.setLayout(main_layout)

def select_file(self):
    file_path, _ = QFileDialog.getOpenFileName(self, 'Video to Frames', '', 'Video Files (*.mp4 *.avi *.mov)')
    if file_path:
        self.vid_path = file_path
        self.file_label.setText(f'Selected video file: {self.vid_path}')
        self.sampling_slider.setEnabled(True)
        self.sampling_edit.setEnabled(True)
        self.start_slider.setEnabled(True)
        self.start_edit.setEnabled(True)
        self.end_slider.setEnabled(True)
        self.end_edit.setEnabled(True)
        self.extract_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.stop_button.setStyleSheet('background-color: red; color: white;')
        vidcap = cv2.VideoCapture(self.vid_path)
        self.fps = vidcap.get(cv2.CAP_PROP_FPS)
        self.max_frame = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.start_slider.setMaximum(self.max_frame)
        self.start_time_label.setText(self.get_time_string(0))
        self.end_slider.setMaximum(self.max_frame)
        self.end_slider.setValue(self.max_frame)
        self.end_edit.setText(str(self.end_slider.value()))
        self.end_time_label.setText(self.get_time_string(self.max_frame / self.fps))
        self.sampling_time_label.setText(self.get_time_string(1 / self.fps))
        self.sampling_slider.setMaximum(self.max_frame // 10)
        self.sampling_slider.setValue(self.max_frame // 100)
        self.sampling_max = self.max_frame // 10
    else:
        self.file_label.setText('No video is selected')
        self.sampling_slider.setEnabled(False)
        self.sampling_edit.setEnabled(False)
        self.start_slider.setEnabled(False)
        self.start_edit.setEnabled(False)
        self.end_slider.setEnabled(False)
        self.end_edit.setEnabled(False)

def update_sampling_rate(self, value):
    self.sampling_rate = value
    self.sampling_edit.setText(str(value))

def update_sampling_slider(self, text):
    try:
        value = int(text)
        if value < 1:
            value = 1
        elif value > self.sampling_max:
            value = self.sampling_max
        self.sampling_rate = value
        self.sampling_slider.setValue(value)
        if self.fps:
            self.sampling_time_label.setText(self.get_time_string(value / self.fps))
            if self.end_frame is not None:
                self.progress_bar.setFormat(f'Will Extract {(self.end_frame - self.start_frame) // self.sampling_rate} Frames')
    except ValueError:
        pass

def update_start_frame(self, value):
    self.start_frame = value
    self.start_edit.setText(str(value))

def update_start_slider(self, text):
    try:
        value = int(text)
        if value < 0:
            value = 0
        elif self.end_frame is not None and value > self.end_frame:
            self.start_slider.setValue(self.end_frame)
            value = self.end_frame
        self.start_frame = value
        self.start_slider.setValue(value)
        if self.fps:
            self.start_time_label.setText(self.get_time_string(value / self.fps))
            if self.end_frame is not None:
                self.progress_bar.setFormat(f'Will Extract {(self.end_frame - self.start_frame) // self.sampling_rate} Frames')
    except ValueError:
        pass

def update_end_frame(self, value):
    self.end_frame = value
    self.end_edit.setText(str(value))

def update_end_slider(self, text):
    try:
        value = int(text)
        if self.start_frame is not None and value < self.start_frame:
            value = self.start_frame
        self.end_frame = value
        self.end_slider.setValue(value)
        if self.fps:
            self.end_time_label.setText(self.get_time_string(value / self.fps))
            if self.end_frame is not None:
                self.progress_bar.setFormat(f'Will Extract {(self.end_frame - self.start_frame) // self.sampling_rate} Frames')
    except ValueError:
        pass

def extract_frames(self):
    try:
        self.path_name = self.vid_to_frames(self.vid_path, self.sampling_rate, self.start_frame, self.end_frame)
    except ValueError as e:
        self.progress_bar.setFormat(str(e))
        return
    self.close()
    return self.path_name

def vid_to_frames(self, vid_path, sampling_rate, start_frame, end_frame):
    """
        Extracts frames from a video file and saves them as JPEG images.

        Args:
            vid_path (str): Path to the video file.
            sampling_rate (int): How often to save a frame. For example, if sampling_rate = 2, every other frame will be saved.
            start_frame (int): Starting frame number.
            end_frame (int): Ending frame number.
        """
    if not os.path.exists(vid_path):
        raise ValueError('Video path does not exist')
    frames_path = ''.join([vid_path.split('.')[0], '_frames'])
    if not os.path.exists(frames_path):
        os.mkdir(frames_path)
    else:
        for file in os.listdir(frames_path):
            os.remove(os.path.join(frames_path, file))
    vidcap = cv2.VideoCapture(vid_path)
    vidcap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    n_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f'Total number of frames: {n_frames}')
    count = start_frame
    success = True
    while success:
        success, image = vidcap.read()
        if count % sampling_rate == 0:
            time_in_sec = count / self.fps
            time_str = self.get_time_string(time_in_sec, separator='_')
            indented_count = str(count).zfill(len(str(n_frames)))
            cv2.imwrite(f'{frames_path}/frame_{indented_count}_time_{time_str}.jpg', image)
        self.progress_bar.setValue(int((count - start_frame) / (end_frame - start_frame) * 100))
        self.progress_bar.setFormat(f'{int((count - start_frame) / (end_frame - start_frame) * 100)}%')
        count += 1
        if count >= end_frame:
            self.progress_bar.setValue(100)
            break
        QtWidgets.QApplication.processEvents()
        if self.stop:
            self.stop = False
            self.progress_bar.setFormat('Extraction stopped')
            self.progress_bar.setValue(0)
            break
    try:
        if not self.mute:
            if not self.isActiveWindow():
                self.notification(f'Video Extraction Completed')
    except:
        pass
    return frames_path

def newIcon(icon):
    icons_dir = osp.join(here, '../icons')
    return QtGui.QIcon(osp.join(':/', icons_dir, '%s.png' % icon))

def newButton(text, icon=None, slot=None):
    b = QtWidgets.QPushButton(text)
    if icon is not None:
        b.setIcon(newIcon(icon))
    if slot is not None:
        b.clicked.connect(slot)
    return b

def newAction(parent, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False, enabled=True, checked=False):
    """Create a new action and assign callbacks, shortcuts, etc."""
    a = QtGui.QAction(text, parent)
    if icon is not None:
        a.setIconText(text.replace(' ', '\n'))
        a.setIcon(newIcon(icon))
    if shortcut is not None:
        if isinstance(shortcut, (list, tuple)):
            a.setShortcuts(shortcut)
        else:
            a.setShortcut(shortcut)
    if tip is not None:
        a.setToolTip(tip)
        a.setStatusTip(tip)
    if slot is not None:
        a.triggered.connect(slot)
    if checkable:
        a.setCheckable(True)
    a.setEnabled(enabled)
    a.setChecked(checked)
    return a

def addActions(widget, actions):
    for action in actions:
        if action is None:
            widget.addSeparator()
        elif isinstance(action, QtWidgets.QMenu):
            widget.addMenu(action)
        else:
            widget.addAction(action)

def labelValidator():
    return QtGui.QRegularExpressionValidator(QtCore.QRegularExpression('^[^ \\t].+'))

def checkKeyFrames(ids, keyFrames):
    """
    Summary:
        Check if all the ids have at least two key frames.
        
    Args:
        ids: a list of ids
        keyFrames: a dictionary of key frames
        
    Returns:
        allAccepted: True if all the ids have at least two key frames, False otherwise
        idsToTrack: a list of ids that have at least two key frames
    """
    idsToTrack = []
    allAccepted = True
    for id in ids:
        try:
            if len(keyFrames['id_' + str(id)]) == 1:
                allAccepted = False
            else:
                idsToTrack.append(id)
        except:
            allAccepted = False
    allRejected = len(idsToTrack) == 0
    return (allAccepted, allRejected, idsToTrack)

def setup(app):
    app.connect('builder-inited', builder_inited_handler)

def setup(app):
    app.connect('builder-inited', builder_inited_handler)

@contextmanager
def _ignore_torch_cuda_oom():
    """A context which ignores CUDA OOM exception from pytorch.

    Code is modified from
    <https://github.com/facebookresearch/detectron2/blob/main/detectron2/utils/memory.py>  # noqa: E501
    """
    try:
        yield
    except RuntimeError as e:
        if 'CUDA out of memory. ' in str(e):
            pass
        else:
            raise

class NiceRepr:
    """Inherit from this class and define ``__nice__`` to "nicely" print your
    objects.

    Defines ``__str__`` and ``__repr__`` in terms of ``__nice__`` function
    Classes that inherit from :class:`NiceRepr` should redefine ``__nice__``.
    If the inheriting class has a ``__len__``, method then the default
    ``__nice__`` method will return its length.

    Example:
        >>> class Foo(NiceRepr):
        ...    def __nice__(self):
        ...        return 'info'
        >>> foo = Foo()
        >>> assert str(foo) == '<Foo(info)>'
        >>> assert repr(foo).startswith('<Foo(info) at ')

    Example:
        >>> class Bar(NiceRepr):
        ...    pass
        >>> bar = Bar()
        >>> import pytest
        >>> with pytest.warns(None) as record:
        >>>     assert 'object at' in str(bar)
        >>>     assert 'object at' in repr(bar)

    Example:
        >>> class Baz(NiceRepr):
        ...    def __len__(self):
        ...        return 5
        >>> baz = Baz()
        >>> assert str(baz) == '<Baz(5)>'
    """

    def __nice__(self):
        """str: a "nice" summary string describing this module"""
        if hasattr(self, '__len__'):
            return str(len(self))
        else:
            raise NotImplementedError(f'Define the __nice__ method for {self.__class__!r}')

    def __repr__(self):
        """str: the string of the module"""
        try:
            nice = self.__nice__()
            classname = self.__class__.__name__
            return f'<{classname}({nice}) at {hex(id(self))}>'
        except NotImplementedError as ex:
            warnings.warn(str(ex), category=RuntimeWarning)
            return object.__repr__(self)

    def __str__(self):
        """str: the string of the module"""
        try:
            classname = self.__class__.__name__
            nice = self.__nice__()
            return f'<{classname}({nice})>'
        except NotImplementedError as ex:
            warnings.warn(str(ex), category=RuntimeWarning)
            return object.__repr__(self)

def __repr__(self):
    """str: the string of the module"""
    try:
        nice = self.__nice__()
        classname = self.__class__.__name__
        return f'<{classname}({nice}) at {hex(id(self))}>'
    except NotImplementedError as ex:
        warnings.warn(str(ex), category=RuntimeWarning)
        return object.__repr__(self)

def __str__(self):
    """str: the string of the module"""
    try:
        classname = self.__class__.__name__
        nice = self.__nice__()
        return f'<{classname}({nice})>'
    except NotImplementedError as ex:
        warnings.warn(str(ex), category=RuntimeWarning)
        return object.__repr__(self)

def draw_labels(ax, labels, positions, scores=None, class_names=None, color='w', font_size=8, scales=None, horizontal_alignment='left'):
    """Draw labels on the axes.

    Args:
        ax (matplotlib.Axes): The input axes.
        labels (ndarray): The labels with the shape of (n, ).
        positions (ndarray): The positions to draw each labels.
        scores (ndarray): The scores for each labels.
        class_names (list[str]): The class names.
        color (list[tuple] | matplotlib.color): The colors for labels.
        font_size (int): Font size of texts. Default: 8.
        scales (list[float]): Scales of texts. Default: None.
        horizontal_alignment (str): The horizontal alignment method of
            texts. Default: 'left'.

    Returns:
        matplotlib.Axes: The result axes.
    """
    for i, (pos, label) in enumerate(zip(positions, labels)):
        label_text = class_names[label] if class_names is not None else f'class {label}'
        if scores is not None:
            label_text += f'|{scores[i]:.02f}'
        text_color = color[i] if isinstance(color, list) else color
        font_size_mask = font_size if scales is None else font_size * scales[i]
        ax.text(pos[0], pos[1], f'{label_text}', bbox={'facecolor': 'black', 'alpha': 0.8, 'pad': 0.7, 'edgecolor': 'none'}, color=text_color, fontsize=font_size_mask, verticalalignment='top', horizontalalignment=horizontal_alignment)
    return ax

@HOOKS.register_module()
class MMDetWandbHook(WandbLoggerHook):
    """Enhanced Wandb logger hook for MMDetection.

    Comparing with the :cls:`mmcv.runner.WandbLoggerHook`, this hook can not
    only automatically log all the metrics but also log the following extra
    information - saves model checkpoints as W&B Artifact, and
    logs model prediction as interactive W&B Tables.

    - Metrics: The MMDetWandbHook will automatically log training
        and validation metrics along with system metrics (CPU/GPU).

    - Checkpointing: If `log_checkpoint` is True, the checkpoint saved at
        every checkpoint interval will be saved as W&B Artifacts.
        This depends on the : class:`mmcv.runner.CheckpointHook` whose priority
        is higher than this hook. Please refer to
        https://docs.wandb.ai/guides/artifacts/model-versioning
        to learn more about model versioning with W&B Artifacts.

    - Checkpoint Metadata: If evaluation results are available for a given
        checkpoint artifact, it will have a metadata associated with it.
        The metadata contains the evaluation metrics computed on validation
        data with that checkpoint along with the current epoch. It depends
        on `EvalHook` whose priority is more than MMDetWandbHook.

    - Evaluation: At every evaluation interval, the `MMDetWandbHook` logs the
        model prediction as interactive W&B Tables. The number of samples
        logged is given by `num_eval_images`. Currently, the `MMDetWandbHook`
        logs the predicted bounding boxes along with the ground truth at every
        evaluation interval. This depends on the `EvalHook` whose priority is
        more than `MMDetWandbHook`. Also note that the data is just logged once
        and subsequent evaluation tables uses reference to the logged data
        to save memory usage. Please refer to
        https://docs.wandb.ai/guides/data-vis to learn more about W&B Tables.

    For more details check out W&B's MMDetection docs:
    https://docs.wandb.ai/guides/integrations/mmdetection

    ```
    Example:
        log_config = dict(
            ...
            hooks=[
                ...,
                dict(type='MMDetWandbHook',
                     init_kwargs={
                         'entity': "YOUR_ENTITY",
                         'project': "YOUR_PROJECT_NAME"
                     },
                     interval=50,
                     log_checkpoint=True,
                     log_checkpoint_metadata=True,
                     num_eval_images=100,
                     bbox_score_thr=0.3)
            ])
    ```

    Args:
        init_kwargs (dict): A dict passed to wandb.init to initialize
            a W&B run. Please refer to https://docs.wandb.ai/ref/python/init
            for possible key-value pairs.
        interval (int): Logging interval (every k iterations). Defaults to 50.
        log_checkpoint (bool): Save the checkpoint at every checkpoint interval
            as W&B Artifacts. Use this for model versioning where each version
            is a checkpoint. Defaults to False.
        log_checkpoint_metadata (bool): Log the evaluation metrics computed
            on the validation data with the checkpoint, along with current
            epoch as a metadata to that checkpoint.
            Defaults to True.
        num_eval_images (int): The number of validation images to be logged.
            If zero, the evaluation won't be logged. Defaults to 100.
        bbox_score_thr (float): Threshold for bounding box scores.
            Defaults to 0.3.
    """

    def __init__(self, init_kwargs=None, interval=50, log_checkpoint=False, log_checkpoint_metadata=False, num_eval_images=100, bbox_score_thr=0.3, **kwargs):
        super(MMDetWandbHook, self).__init__(init_kwargs, interval, **kwargs)
        self.log_checkpoint = log_checkpoint
        self.log_checkpoint_metadata = log_checkpoint and log_checkpoint_metadata
        self.num_eval_images = num_eval_images
        self.bbox_score_thr = bbox_score_thr
        self.log_evaluation = num_eval_images > 0
        self.ckpt_hook: CheckpointHook = None
        self.eval_hook: EvalHook = None

    def import_wandb(self):
        try:
            import wandb
            from wandb import init
            if digit_version(wandb.__version__) < digit_version('0.12.10'):
                warnings.warn(f'The current wandb {wandb.__version__} is lower than v0.12.10 will cause ResourceWarning when calling wandb.log, Please run "pip install --upgrade wandb"')
        except ImportError:
            raise ImportError('Please run "pip install "wandb>=0.12.10"" to install wandb')
        self.wandb = wandb

    @master_only
    def before_run(self, runner):
        super(MMDetWandbHook, self).before_run(runner)
        if runner.meta is not None and runner.meta.get('exp_name', None) is not None:
            src_cfg_path = osp.join(runner.work_dir, runner.meta.get('exp_name', None))
            if osp.exists(src_cfg_path):
                self.wandb.save(src_cfg_path, base_path=runner.work_dir)
                self._update_wandb_config(runner)
        else:
            runner.logger.warning('No meta information found in the runner. ')
        for hook in runner.hooks:
            if isinstance(hook, CheckpointHook):
                self.ckpt_hook = hook
            if isinstance(hook, (EvalHook, DistEvalHook)):
                self.eval_hook = hook
        if self.log_checkpoint:
            if self.ckpt_hook is None:
                self.log_checkpoint = False
                self.log_checkpoint_metadata = False
                runner.logger.warning('To log checkpoint in MMDetWandbHook, `CheckpointHook` isrequired, please check hooks in the runner.')
            else:
                self.ckpt_interval = self.ckpt_hook.interval
        if self.log_evaluation or self.log_checkpoint_metadata:
            if self.eval_hook is None:
                self.log_evaluation = False
                self.log_checkpoint_metadata = False
                runner.logger.warning('To log evaluation or checkpoint metadata in MMDetWandbHook, `EvalHook` or `DistEvalHook` in mmdet is required, please check whether the validation is enabled.')
            else:
                self.eval_interval = self.eval_hook.interval
                self.val_dataset = self.eval_hook.dataloader.dataset
                if self.num_eval_images > len(self.val_dataset):
                    self.num_eval_images = len(self.val_dataset)
                    runner.logger.warning(f'The num_eval_images ({self.num_eval_images}) is greater than the total number of validation samples ({len(self.val_dataset)}). The complete validation dataset will be logged.')
        if self.log_checkpoint_metadata:
            assert self.ckpt_interval % self.eval_interval == 0, f'To log checkpoint metadata in MMDetWandbHook, the interval of checkpoint saving ({self.ckpt_interval}) should be divisible by the interval of evaluation ({self.eval_interval}).'
        if self.log_evaluation:
            self._init_data_table()
            self._add_ground_truth(runner)
            self._log_data_table()

    @master_only
    def after_train_epoch(self, runner):
        super(MMDetWandbHook, self).after_train_epoch(runner)
        if not self.by_epoch:
            return
        if self.log_checkpoint and self.every_n_epochs(runner, self.ckpt_interval) or (self.ckpt_hook.save_last and self.is_last_epoch(runner)):
            if self.log_checkpoint_metadata and self.eval_hook:
                metadata = {'epoch': runner.epoch + 1, **self._get_eval_results()}
            else:
                metadata = None
            aliases = [f'epoch_{runner.epoch + 1}', 'latest']
            model_path = osp.join(self.ckpt_hook.out_dir, f'epoch_{runner.epoch + 1}.pth')
            self._log_ckpt_as_artifact(model_path, aliases, metadata)
        if self.log_evaluation and self.eval_hook._should_evaluate(runner):
            results = self.eval_hook.latest_results
            self._init_pred_table()
            self._log_predictions(results)
            self._log_eval_table(runner.epoch + 1)

    @master_only
    def after_train_iter(self, runner):
        if self.get_mode(runner) == 'train':
            return super(MMDetWandbHook, self).after_train_iter(runner)
        else:
            super(MMDetWandbHook, self).after_train_iter(runner)
        if self.by_epoch:
            return
        if self.log_checkpoint and self.every_n_iters(runner, self.ckpt_interval) or (self.ckpt_hook.save_last and self.is_last_iter(runner)):
            if self.log_checkpoint_metadata and self.eval_hook:
                metadata = {'iter': runner.iter + 1, **self._get_eval_results()}
            else:
                metadata = None
            aliases = [f'iter_{runner.iter + 1}', 'latest']
            model_path = osp.join(self.ckpt_hook.out_dir, f'iter_{runner.iter + 1}.pth')
            self._log_ckpt_as_artifact(model_path, aliases, metadata)
        if self.log_evaluation and self.eval_hook._should_evaluate(runner):
            results = self.eval_hook.latest_results
            self._init_pred_table()
            self._log_predictions(results)
            self._log_eval_table(runner.iter + 1)

    @master_only
    def after_run(self, runner):
        self.wandb.finish()

    def _update_wandb_config(self, runner):
        """Update wandb config."""
        sys.path.append(runner.work_dir)
        config_filename = runner.meta['exp_name'][:-3]
        configs = importlib.import_module(config_filename)
        config_keys = [key for key in dir(configs) if not key.startswith('__')]
        config_dict = {key: getattr(configs, key) for key in config_keys}
        self.wandb.config.update(config_dict)

    def _log_ckpt_as_artifact(self, model_path, aliases, metadata=None):
        """Log model checkpoint as  W&B Artifact.

        Args:
            model_path (str): Path of the checkpoint to log.
            aliases (list): List of the aliases associated with this artifact.
            metadata (dict, optional): Metadata associated with this artifact.
        """
        model_artifact = self.wandb.Artifact(f'run_{self.wandb.run.id}_model', type='model', metadata=metadata)
        model_artifact.add_file(model_path)
        self.wandb.log_artifact(model_artifact, aliases=aliases)

    def _get_eval_results(self):
        """Get model evaluation results."""
        results = self.eval_hook.latest_results
        eval_results = self.val_dataset.evaluate(results, logger='silent', **self.eval_hook.eval_kwargs)
        return eval_results

    def _init_data_table(self):
        """Initialize the W&B Tables for validation data."""
        columns = ['image_name', 'image']
        self.data_table = self.wandb.Table(columns=columns)

    def _init_pred_table(self):
        """Initialize the W&B Tables for model evaluation."""
        columns = ['image_name', 'ground_truth', 'prediction']
        self.eval_table = self.wandb.Table(columns=columns)

    def _add_ground_truth(self, runner):
        from mmdet.datasets.pipelines import LoadImageFromFile
        img_loader = None
        for t in self.val_dataset.pipeline.transforms:
            if isinstance(t, LoadImageFromFile):
                img_loader = t
        if img_loader is None:
            self.log_evaluation = False
            runner.logger.warning('LoadImageFromFile is required to add images to W&B Tables.')
            return
        self.eval_image_indexs = np.arange(len(self.val_dataset))
        np.random.seed(42)
        np.random.shuffle(self.eval_image_indexs)
        self.eval_image_indexs = self.eval_image_indexs[:self.num_eval_images]
        CLASSES = self.val_dataset.CLASSES
        self.class_id_to_label = {id + 1: name for id, name in enumerate(CLASSES)}
        self.class_set = self.wandb.Classes([{'id': id, 'name': name} for id, name in self.class_id_to_label.items()])
        img_prefix = self.val_dataset.img_prefix
        for idx in self.eval_image_indexs:
            img_info = self.val_dataset.data_infos[idx]
            image_name = img_info.get('filename', f'img_{idx}')
            img_height, img_width = (img_info['height'], img_info['width'])
            img_meta = img_loader(dict(img_info=img_info, img_prefix=img_prefix))
            image = mmcv.bgr2rgb(img_meta['img'])
            data_ann = self.val_dataset.get_ann_info(idx)
            bboxes = data_ann['bboxes']
            labels = data_ann['labels']
            masks = data_ann.get('masks', None)
            assert len(bboxes) == len(labels)
            wandb_boxes = self._get_wandb_bboxes(bboxes, labels)
            if masks is not None:
                wandb_masks = self._get_wandb_masks(masks, labels, is_poly_mask=True, height=img_height, width=img_width)
            else:
                wandb_masks = None
            self.data_table.add_data(image_name, self.wandb.Image(image, boxes=wandb_boxes, masks=wandb_masks, classes=self.class_set))

    def _log_predictions(self, results):
        table_idxs = self.data_table_ref.get_index()
        assert len(table_idxs) == len(self.eval_image_indexs)
        for ndx, eval_image_index in enumerate(self.eval_image_indexs):
            result = results[eval_image_index]
            if isinstance(result, tuple):
                bbox_result, segm_result = result
                if isinstance(segm_result, tuple):
                    segm_result = segm_result[0]
            else:
                bbox_result, segm_result = (result, None)
            assert len(bbox_result) == len(self.class_id_to_label)
            bboxes = np.vstack(bbox_result)
            labels = [np.full(bbox.shape[0], i, dtype=np.int32) for i, bbox in enumerate(bbox_result)]
            labels = np.concatenate(labels)
            segms = None
            if segm_result is not None and len(labels) > 0:
                segms = mmcv.concat_list(segm_result)
                segms = mask_util.decode(segms)
                segms = segms.transpose(2, 0, 1)
                assert len(segms) == len(labels)
            if self.bbox_score_thr > 0:
                assert bboxes is not None and bboxes.shape[1] == 5
                scores = bboxes[:, -1]
                inds = scores > self.bbox_score_thr
                bboxes = bboxes[inds, :]
                labels = labels[inds]
                if segms is not None:
                    segms = segms[inds, ...]
            wandb_boxes = self._get_wandb_bboxes(bboxes, labels, log_gt=False)
            if segms is not None:
                wandb_masks = self._get_wandb_masks(segms, labels)
            else:
                wandb_masks = None
            self.eval_table.add_data(self.data_table_ref.data[ndx][0], self.data_table_ref.data[ndx][1], self.wandb.Image(self.data_table_ref.data[ndx][1], boxes=wandb_boxes, masks=wandb_masks, classes=self.class_set))

    def _get_wandb_bboxes(self, bboxes, labels, log_gt=True):
        """Get list of structured dict for logging bounding boxes to W&B.

        Args:
            bboxes (list): List of bounding box coordinates in
                        (minX, minY, maxX, maxY) format.
            labels (int): List of label ids.
            log_gt (bool): Whether to log ground truth or prediction boxes.

        Returns:
            Dictionary of bounding boxes to be logged.
        """
        wandb_boxes = {}
        box_data = []
        for bbox, label in zip(bboxes, labels):
            if not isinstance(label, int):
                label = int(label)
            label = label + 1
            if len(bbox) == 5:
                confidence = float(bbox[4])
                class_name = self.class_id_to_label[label]
                box_caption = f'{class_name} {confidence:.2f}'
            else:
                box_caption = str(self.class_id_to_label[label])
            position = dict(minX=int(bbox[0]), minY=int(bbox[1]), maxX=int(bbox[2]), maxY=int(bbox[3]))
            box_data.append({'position': position, 'class_id': label, 'box_caption': box_caption, 'domain': 'pixel'})
        wandb_bbox_dict = {'box_data': box_data, 'class_labels': self.class_id_to_label}
        if log_gt:
            wandb_boxes['ground_truth'] = wandb_bbox_dict
        else:
            wandb_boxes['predictions'] = wandb_bbox_dict
        return wandb_boxes

    def _get_wandb_masks(self, masks, labels, is_poly_mask=False, height=None, width=None):
        """Get list of structured dict for logging masks to W&B.

        Args:
            masks (list): List of masks.
            labels (int): List of label ids.
            is_poly_mask (bool): Whether the mask is polygonal or not.
                This is true for CocoDataset.
            height (int): Height of the image.
            width (int): Width of the image.

        Returns:
            Dictionary of masks to be logged.
        """
        mask_label_dict = dict()
        for mask, label in zip(masks, labels):
            label = label + 1
            if is_poly_mask:
                if height is not None and width is not None:
                    mask = polygon_to_bitmap(mask, height, width)
            if label not in mask_label_dict.keys():
                mask_label_dict[label] = mask
            else:
                mask_label_dict[label] = np.logical_or(mask_label_dict[label], mask)
        wandb_masks = dict()
        for key, value in mask_label_dict.items():
            value = value.astype(np.uint8)
            value[value > 0] = key
            class_name = self.class_id_to_label[key]
            wandb_masks[class_name] = {'mask_data': value, 'class_labels': self.class_id_to_label}
        return wandb_masks

    def _log_data_table(self):
        """Log the W&B Tables for validation data as artifact and calls
        `use_artifact` on it so that the evaluation table can use the reference
        of already uploaded images.

        This allows the data to be uploaded just once.
        """
        data_artifact = self.wandb.Artifact('val', type='dataset')
        data_artifact.add(self.data_table, 'val_data')
        if not self.wandb.run.offline:
            self.wandb.run.use_artifact(data_artifact)
            data_artifact.wait()
            self.data_table_ref = data_artifact.get('val_data')
        else:
            self.data_table_ref = self.data_table

    def _log_eval_table(self, idx):
        """Log the W&B Tables for model evaluation.

        The table will be logged multiple times creating new version. Use this
        to compare models at different intervals interactively.
        """
        pred_artifact = self.wandb.Artifact(f'run_{self.wandb.run.id}_pred', type='evaluation')
        pred_artifact.add(self.eval_table, 'eval_data')
        if self.by_epoch:
            aliases = ['latest', f'epoch_{idx}']
        else:
            aliases = ['latest', f'iter_{idx}']
        self.wandb.run.log_artifact(pred_artifact, aliases=aliases)

@master_only
def after_run(self, runner):
    self.wandb.finish()

def get_gt_area_group_numbers(cocoEval):
    areaRng = cocoEval.params.areaRng
    areaRngStr = [str(aRng) for aRng in areaRng]
    areaRngLbl = cocoEval.params.areaRngLbl
    areaRngStr2areaRngLbl = dict(zip(areaRngStr, areaRngLbl))
    areaRngLbl2Number = dict.fromkeys(areaRngLbl, 0)
    for evalImg in cocoEval.evalImgs:
        if evalImg:
            for gtIgnore in evalImg['gtIgnore']:
                if not gtIgnore:
                    aRngLbl = areaRngStr2areaRngLbl[str(evalImg['aRng'])]
                    areaRngLbl2Number[aRngLbl] += 1
    return areaRngLbl2Number

