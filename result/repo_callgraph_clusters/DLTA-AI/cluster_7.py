# Cluster 7

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

def toggleActions(self, value=True):
    """Enable/Disable widgets which depend on an opened image."""
    for z in self.actions.zoomActions:
        z.setEnabled(value)
    for action in self.actions.onLoadActive:
        action.setEnabled(value)

def canvasShapeEdgeSelected(self, selected, shape):
    self.actions.addPointToEdge.setEnabled(selected and shape and shape.canAddPoint())

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

def addZoom(self, increment=1.1):
    zoom_value = self.zoomWidget.value() * increment
    if increment > 1:
        zoom_value = math.ceil(zoom_value)
    else:
        zoom_value = math.floor(zoom_value)
    self.setZoom(zoom_value)

def onNewBrightnessContrast(self, qimage):
    self.canvas.loadPixmap(QtGui.QPixmap.fromImage(qimage), clear_shapes=False)

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

def track_assigned_objects_button_clicked(self):
    if len(self.labelList.selectedItems()) == 0:
        self.errorMessage('found No objects to track', 'you need to assign at least one object to track')
        return
    self.TRACK_ASSIGNED_OBJECTS_ONLY = True
    self.track_buttonClicked()
    self.TRACK_ASSIGNED_OBJECTS_ONLY = False

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

def draw_bb_on_image(self, image, shapes, image_qt_flag=True):
    return visualizations.draw_bb_on_image(self.CURRENT_ANNOATAION_TRAJECTORIES, self.INDEX_OF_CURRENT_FRAME, self.CURRENT_ANNOATAION_FLAGS, self.TOTAL_VIDEO_FRAMES, image, shapes, image_qt_flag)

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

def assert_labelfile_sanity(filename):
    assert osp.exists(filename)
    data = json.load(open(filename))
    assert 'imagePath' in data
    imageData = data.get('imageData', None)
    if imageData is None:
        parent_dir = osp.dirname(filename)
        img_file = osp.join(parent_dir, data['imagePath'])
        assert osp.exists(img_file)
        img = imgviz.io.imread(img_file)
    else:
        img = labelme.utils.img_b64_to_arr(imageData)
    H, W = img.shape[:2]
    assert H == data['imageHeight']
    assert W == data['imageWidth']
    assert 'shapes' in data
    for shape in data['shapes']:
        assert 'label' in shape
        assert 'points' in shape
        for x, y in shape['points']:
            assert 0 <= x <= W
            assert 0 <= y <= H

class IntelligenceWorker(QThread):
    sinOut = pyqtSignal(int, int)

    def __init__(self, parent, images, source, multi_model_flag=False):
        super(IntelligenceWorker, self).__init__(parent)
        self.parent = parent
        self.source = source
        self.images = images
        self.multi_model_flag = multi_model_flag
        self.notif = []

    def run(self):
        index = 0
        total = len(self.images)
        for filename in self.images:
            if self.parent.isVisible == False:
                return
            if self.source.operationCanceled == True:
                return
            index = index + 1
            json_name = osp.splitext(filename)[0] + '.json'
            if os.path.isdir(json_name):
                os.remove(json_name)
            try:
                print('Decoding ' + filename)
                if self.multi_model_flag:
                    s = self.source.get_shapes_of_one(filename, multi_model_flag=True)
                else:
                    s = self.source.get_shapes_of_one(filename)
                s = mathOps.convert_shapes_to_qt_shapes(s)
                self.source.saveLabelFile(filename, s)
            except Exception as e:
                print(e)
            self.sinOut.emit(index, total)

def run(self):
    index = 0
    total = len(self.images)
    for filename in self.images:
        if self.parent.isVisible == False:
            return
        if self.source.operationCanceled == True:
            return
        index = index + 1
        json_name = osp.splitext(filename)[0] + '.json'
        if os.path.isdir(json_name):
            os.remove(json_name)
        try:
            print('Decoding ' + filename)
            if self.multi_model_flag:
                s = self.source.get_shapes_of_one(filename, multi_model_flag=True)
            else:
                s = self.source.get_shapes_of_one(filename)
            s = mathOps.convert_shapes_to_qt_shapes(s)
            self.source.saveLabelFile(filename, s)
        except Exception as e:
            print(e)
        self.sinOut.emit(index, total)

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

class Shape(object):
    P_SQUARE = 0
    P_ROUND = 1
    MOVE_VERTEX = 0
    NEAR_VERTEX = 1
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 8
    scale = 1.0

    def __init__(self, label=None, line_color=None, shape_type=None, flags=None, group_id=None, content=None):
        self.label = label
        self.group_id = group_id
        self.points = []
        self.bbox = []
        self.fill = False
        self.selected = False
        self.shape_type = shape_type
        self.flags = flags
        self.content = content
        self.other_data = {}
        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {self.NEAR_VERTEX: (4, self.P_ROUND), self.MOVE_VERTEX: (1.5, self.P_SQUARE)}
        self._closed = False
        if line_color is not None:
            self.line_color = line_color
        self.shape_type = shape_type

    @property
    def shape_type(self):
        return self._shape_type

    @shape_type.setter
    def shape_type(self, value):
        if value is None:
            value = 'polygon'
        if value not in ['polygon', 'rectangle', 'point', 'line', 'circle', 'linestrip']:
            raise ValueError('Unexpected shape_type: {}'.format(value))
        self._shape_type = value

    def close(self):
        self._closed = True

    def addPoint(self, point):
        if self.points and point == self.points[0]:
            self.close()
        else:
            self.points.append(point)

    def canAddPoint(self):
        return self.shape_type in ['polygon', 'linestrip']

    def popPoint(self):
        if self.points:
            return self.points.pop()
        return None

    def insertPoint(self, i, point):
        self.points.insert(i, point)

    def removePoint(self, i):
        self.points.pop(i)

    def isClosed(self):
        return self._closed

    def setOpen(self):
        self._closed = False

    def getRectFromLine(self, pt1, pt2):
        x1, y1 = (pt1.x(), pt1.y())
        x2, y2 = (pt2.x(), pt2.y())
        return QtCore.QRectF(x1, y1, x2 - x1, y2 - y1)

    def paint(self, painter):
        if self.points:
            color = self.select_line_color if self.selected else self.line_color
            pen = QtGui.QPen(color)
            pen.setWidth(max(1, int(round(2.0 / self.scale))))
            painter.setPen(pen)
            line_path = QtGui.QPainterPath()
            vrtx_path = QtGui.QPainterPath()
            if self.shape_type == 'rectangle':
                assert len(self.points) in [1, 2]
                if len(self.points) == 2:
                    rectangle = self.getRectFromLine(*self.points)
                    line_path.addRect(rectangle)
                for i in range(len(self.points)):
                    self.drawVertex(vrtx_path, i)
            elif self.shape_type == 'circle':
                assert len(self.points) in [1, 2]
                if len(self.points) == 2:
                    rectangle = self.getCircleRectFromLine(self.points)
                    line_path.addEllipse(rectangle)
                for i in range(len(self.points)):
                    self.drawVertex(vrtx_path, i)
            elif self.shape_type == 'linestrip':
                line_path.moveTo(self.points[0])
                for i, p in enumerate(self.points):
                    line_path.lineTo(p)
                    self.drawVertex(vrtx_path, i)
            else:
                line_path.moveTo(self.points[0])
                for i, p in enumerate(self.points):
                    line_path.lineTo(p)
                    self.drawVertex(vrtx_path, i)
                if self.isClosed():
                    line_path.lineTo(self.points[0])
            painter.drawPath(line_path)
            painter.drawPath(vrtx_path)
            painter.fillPath(vrtx_path, self._vertex_fill_color)
            if self.fill:
                color = self.select_fill_color if self.selected else self.fill_color
                painter.fillPath(line_path, color)

    def drawVertex(self, path, i):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]
        if i == self._highlightIndex:
            size, shape = self._highlightSettings[self._highlightMode]
            d *= size
        if self._highlightIndex is not None:
            self._vertex_fill_color = self.hvertex_fill_color
        else:
            self._vertex_fill_color = self.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            assert False, 'unsupported vertex shape'

    def nearestVertex(self, point, epsilon):
        min_distance = float('inf')
        min_i = None
        for i, p in enumerate(self.points):
            dist = labelme.utils.distance(p - point)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                min_i = i
        return min_i

    def nearestEdge(self, point, epsilon):
        min_distance = float('inf')
        post_i = None
        for i in range(len(self.points)):
            line = [self.points[i - 1], self.points[i]]
            dist = labelme.utils.distancetoline(point, line)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                post_i = i
        return post_i

    def containsPoint(self, point):
        return self.makePath().contains(point)

    def getCircleRectFromLine(self, line):
        """Computes parameters to draw with `QPainterPath::addEllipse`"""
        if len(line) != 2:
            return None
        c, point = line
        r = line[0] - line[1]
        d = math.sqrt(math.pow(r.x(), 2) + math.pow(r.y(), 2))
        rectangle = QtCore.QRectF(c.x() - d, c.y() - d, 2 * d, 2 * d)
        return rectangle

    def makePath(self):
        if self.shape_type == 'rectangle':
            path = QtGui.QPainterPath()
            if len(self.points) == 2:
                rectangle = self.getRectFromLine(*self.points)
                path.addRect(rectangle)
        elif self.shape_type == 'circle':
            path = QtGui.QPainterPath()
            if len(self.points) == 2:
                rectangle = self.getCircleRectFromLine(self.points)
                path.addEllipse(rectangle)
        else:
            path = QtGui.QPainterPath(self.points[0])
            for p in self.points[1:]:
                path.lineTo(p)
        return path

    def boundingRect(self):
        return self.makePath().boundingRect()

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    def moveVertexBy(self, i, offset):
        self.points[i] = self.points[i] + offset

    def highlightVertex(self, i, action):
        """Highlight a vertex appropriately based on the current action

        Args:
            i (int): The vertex index
            action (int): The action
            (see Shape.NEAR_VERTEX and Shape.MOVE_VERTEX)
        """
        self._highlightIndex = i
        self._highlightMode = action

    def highlightClear(self):
        """Clear the highlighted point"""
        self._highlightIndex = None

    def copy(self):
        return copy.deepcopy(self)

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value

def copy(self):
    return copy.deepcopy(self)

class LabelFile(object):
    suffix = '.json'

    def __init__(self, filename=None):
        self.shapes = []
        self.imagePath = None
        self.imageData = None
        if filename is not None:
            self.load(filename)
        self.filename = filename

    @staticmethod
    def load_image_file(filename):
        try:
            image_pil = PIL.Image.open(filename)
        except IOError:
            logger.error('Failed opening image file: {}'.format(filename))
            return
        image_pil = utils.apply_exif_orientation(image_pil)
        with io.BytesIO() as f:
            ext = osp.splitext(filename)[1].lower()
            if PY2 and QT4:
                format = 'PNG'
            elif ext in ['.jpg', '.jpeg']:
                format = 'JPEG'
            else:
                format = 'PNG'
            image_pil.save(f, format=format)
            f.seek(0)
            return f.read()

    def load(self, filename):
        keys = ['version', 'imageData', 'imagePath', 'shapes', 'flags', 'imageHeight', 'imageWidth']
        shape_keys = ['label', 'points', 'bbox', 'group_id', 'shape_type', 'flags', 'content']
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            version = data.get('version')
            if version is None:
                logger.warn('Loading JSON file ({}) of unknown version'.format(filename))
            elif version.split('.')[0] != __version__.split('.')[0]:
                logger.warn('This JSON file ({}) may be incompatible with current labelme. version in file: {}, current version: {}'.format(filename, version, __version__))
            if data['imageData'] is not None:
                imageData = base64.b64decode(data['imageData'])
                if PY2 and QT4:
                    imageData = utils.img_data_to_png_data(imageData)
            else:
                imagePath = osp.join(osp.dirname(filename), data['imagePath'])
                imageData = self.load_image_file(imagePath)
            flags = data.get('flags') or {}
            imagePath = data['imagePath']
            self._check_image_height_and_width(base64.b64encode(imageData).decode('utf-8'), data.get('imageHeight'), data.get('imageWidth'))
            shapes = [dict(label=s['label'], points=s['points'], bbox=s['bbox'], shape_type=s.get('shape_type', 'polygon'), flags=s.get('flags', {}), content=s.get('content'), group_id=s.get('group_id'), other_data={k: v for k, v in s.items() if k not in shape_keys}) for s in data['shapes']]
        except Exception as e:
            raise LabelFileError(e)
        otherData = {}
        for key, value in data.items():
            if key not in keys:
                otherData[key] = value
        self.flags = flags
        self.shapes = shapes
        self.imagePath = imagePath
        self.imageData = imageData
        self.filename = filename
        self.otherData = otherData

    @staticmethod
    def _check_image_height_and_width(imageData, imageHeight, imageWidth):
        img_arr = utils.img_b64_to_arr(imageData)
        if imageHeight is not None and img_arr.shape[0] != imageHeight:
            logger.error('imageHeight does not match with imageData or imagePath, so getting imageHeight from actual image.')
            imageHeight = img_arr.shape[0]
        if imageWidth is not None and img_arr.shape[1] != imageWidth:
            logger.error('imageWidth does not match with imageData or imagePath, so getting imageWidth from actual image.')
            imageWidth = img_arr.shape[1]
        return (imageHeight, imageWidth)

    def save(self, filename, shapes, imagePath, imageHeight, imageWidth, imageData=None, otherData=None, flags=None):
        if imageData is not None:
            imageData = base64.b64encode(imageData).decode('utf-8')
            imageHeight, imageWidth = self._check_image_height_and_width(imageData, imageHeight, imageWidth)
        if otherData is None:
            otherData = {}
        if flags is None:
            flags = {}
        data = dict(version=__version__, flags=flags, shapes=shapes, imagePath=imagePath, imageData=imageData, imageHeight=imageHeight, imageWidth=imageWidth)
        for key, value in otherData.items():
            assert key not in data
            data[key] = value
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.filename = filename
        except Exception as e:
            raise LabelFileError(e)

    @staticmethod
    def is_label_file(filename):
        return osp.splitext(filename)[1].lower() == LabelFile.suffix

@staticmethod
def load_image_file(filename):
    try:
        image_pil = PIL.Image.open(filename)
    except IOError:
        logger.error('Failed opening image file: {}'.format(filename))
        return
    image_pil = utils.apply_exif_orientation(image_pil)
    with io.BytesIO() as f:
        ext = osp.splitext(filename)[1].lower()
        if PY2 and QT4:
            format = 'PNG'
        elif ext in ['.jpg', '.jpeg']:
            format = 'JPEG'
        else:
            format = 'PNG'
        image_pil.save(f, format=format)
        f.seek(0)
        return f.read()

@staticmethod
def _check_image_height_and_width(imageData, imageHeight, imageWidth):
    img_arr = utils.img_b64_to_arr(imageData)
    if imageHeight is not None and img_arr.shape[0] != imageHeight:
        logger.error('imageHeight does not match with imageData or imagePath, so getting imageHeight from actual image.')
        imageHeight = img_arr.shape[0]
    if imageWidth is not None and img_arr.shape[1] != imageWidth:
        logger.error('imageWidth does not match with imageData or imagePath, so getting imageWidth from actual image.')
        imageWidth = img_arr.shape[1]
    return (imageHeight, imageWidth)

@staticmethod
def is_label_file(filename):
    return osp.splitext(filename)[1].lower() == LabelFile.suffix

def labelme_on_docker(in_file, out_file):
    ip = get_ip()
    cmd = 'xhost + %s' % ip
    subprocess.check_output(shlex.split(cmd))
    if out_file:
        out_file = osp.abspath(out_file)
        if osp.exists(out_file):
            raise RuntimeError('File exists: %s' % out_file)
        else:
            open(osp.abspath(out_file), 'w')
    cmd = 'docker run -it --rm -e DISPLAY={0}:0 -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix -v {1}:{2} -w /home/developer'
    in_file_a = osp.abspath(in_file)
    in_file_b = osp.join('/home/developer', osp.basename(in_file))
    cmd = cmd.format(ip, in_file_a, in_file_b)
    if out_file:
        out_file_a = osp.abspath(out_file)
        out_file_b = osp.join('/home/developer', osp.basename(out_file))
        cmd += ' -v {0}:{1}'.format(out_file_a, out_file_b)
    cmd += ' wkentaro/labelme labelme {0}'.format(in_file_b)
    if out_file:
        cmd += ' -O {0}'.format(out_file_b)
    subprocess.call(shlex.split(cmd))
    if out_file:
        try:
            json.load(open(out_file))
            return out_file
        except Exception:
            if open(out_file).read() == '':
                os.remove(out_file)
            raise RuntimeError('Annotation is cancelled.')

def check_duplicates_editLabel(id_frames_rec, old_group_id, new_group_id, only_this_frame, idChanged, currFrame):
    """
    Summary:
        Check if there are id duplicates in any frame if the id is changed.
        
    Args:
        id_frames_rec: a dictionary of id frames records
        old_group_id: the old id
        new_group_id: the new id
        only_this_frame: a flag to indicate if the id is changed only in the current frame or in all frames
        idChanged: a flag to indicate if the id is changed or not (if False, the function returns False as there is no change)
        currFrame: the current frame index
        
    Returns:
        True if there will be duplicates, False otherwise
    """
    if not idChanged:
        return False
    old_id_frame_record = copy.deepcopy(id_frames_rec['id_' + str(old_group_id)])
    try:
        new_id_frame_record = copy.deepcopy(id_frames_rec['id_' + str(new_group_id)])
    except:
        new_id_frame_record = set()
        pass
    if only_this_frame:
        Intersection = new_id_frame_record.intersection({currFrame})
        if len(Intersection) != 0:
            OKmsgBox('Warning', f'Two shapes with the same ID exists.\nApparantly, a shape with ID ({new_group_id}) already exists with another shape with ID ({old_group_id}) in the CURRENT FRAME and the edit will result in two shapes with the same ID in the same frame.\n\n The edit is NOT performed.')
            return True
    else:
        Intersection = old_id_frame_record.intersection(new_id_frame_record)
        if len(Intersection) != 0:
            reduced_Intersection = reducing_Intersection(Intersection)
            OKmsgBox('ID already exists', f'Two shapes with the same ID exists in at least one frame.\nApparantly, a shape with ID ({new_group_id}) already exists with another shape with ID ({old_group_id}).\nLike in frames ({reduced_Intersection}) and the edit will result in two shapes with the same ID ({new_group_id}).\n\n The edit is NOT performed.')
            return True
    return False

class LabelQLineEdit(QtWidgets.QLineEdit):

    def setListWidget(self, list_widget):
        self.list_widget = list_widget

    def keyPressEvent(self, e):
        if e.key() in [QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down]:
            self.list_widget.keyPressEvent(e)
        else:
            super(LabelQLineEdit, self).keyPressEvent(e)

def keyPressEvent(self, e):
    if e.key() in [QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down]:
        self.list_widget.keyPressEvent(e)
    else:
        super(LabelQLineEdit, self).keyPressEvent(e)

def PopUp():
    """
    Open a file with the default application for the file type.

    Args:
        filename (str): The name of the file to open.

    Raises:
        OSError: If the file cannot be opened.

    Returns:
        None
    """
    filename = os.path.join(os.getcwd(), 'labelme/utils/custom_exports.py')
    print(filename)
    if platform.system() == 'Windows':
        os.startfile(filename)
    elif platform.system() == 'Darwin':
        os.system(f'open {filename}')
    else:
        try:
            opener = 'open' if platform.system() == 'Darwin' else 'xdg-open'
            subprocess.call([opener, filename])
        except OSError:
            print(f'Could not open file: {filename}')

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

def createItemFromLabel(self, label):
    item = QtWidgets.QListWidgetItem()
    item.setData(Qt.ItemDataRole.UserRole, label)
    return item

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

def setShape(self, shape):
    self.setData(shape, Qt.ItemDataRole.UserRole)

def shape(self):
    return self.data(Qt.ItemDataRole.UserRole)

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

def clear(self):
    self.model().clear()

class EscapableQListWidget(QtWidgets.QListWidget):

    def keyPressEvent(self, event):
        super(EscapableQListWidget, self).keyPressEvent(event)
        if event.key() == Qt.Key.Key_Escape:
            self.clearSelection()

def keyPressEvent(self, event):
    super(EscapableQListWidget, self).keyPressEvent(event)
    if event.key() == Qt.Key.Key_Escape:
        self.clearSelection()

def show_unshow_overwrite():
    if with_sam.isChecked():
        config.update({'interpolationDefMethod': 'SAM'})
        overwrite_checkBox.setEnabled(True)
    else:
        config.update({'interpolationDefMethod': 'Linear'})
        overwrite_checkBox.setEnabled(False)

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

def polygons_to_mask(img_shape, polygons, shape_type=None):
    logger.warning("The 'polygons_to_mask' function is deprecated, use 'shape_to_mask' instead.")
    return shape_to_mask(img_shape, points=polygons, shape_type=shape_type)

def shapes_to_label(img_shape, shapes, label_name_to_value):
    cls = np.zeros(img_shape[:2], dtype=np.int32)
    ins = np.zeros_like(cls)
    instances = []
    for shape in shapes:
        points = shape['points']
        label = shape['label']
        group_id = shape.get('group_id')
        if group_id is None:
            group_id = uuid.uuid1()
        shape_type = shape.get('shape_type', None)
        cls_name = label
        instance = (cls_name, group_id)
        if instance not in instances:
            instances.append(instance)
        ins_id = instances.index(instance) + 1
        cls_id = label_name_to_value[cls_name]
        mask = shape_to_mask(img_shape[:2], points, shape_type)
        cls[mask] = cls_id
        ins[mask] = ins_id
    return (cls, ins)

class Sam_Predictor:

    def __init__(self, model_type, checkpoint_path, device):
        self.model_type = model_type
        self.checkpoint_path = checkpoint_path
        self.device = device
        self.model = sam_model_registry[model_type](checkpoint=checkpoint_path)
        self.model.to(device=self.device)
        self.predictor = SamPredictor(self.model)
        self.image = None
        self.mask_logit = None

    def set_new_image(self, image):
        self.image = image
        self.predictor.set_image(image)

    def clear_logit(self):
        self.mask_logit = None

    def predict(self, point_coords=None, point_labels=None, box=None, multimask_output=True, image=None):
        if box is None:
            if self.mask_logit is None:
                masks, scores, logits = self.predictor.predict(point_coords=point_coords, point_labels=point_labels, multimask_output=multimask_output)
            else:
                masks, scores, logits = self.predictor.predict(point_coords=point_coords, point_labels=point_labels, mask_input=self.mask_logit[None, :, :], multimask_output=multimask_output)
        elif len(box) == 1:
            input_box = np.array(box[0])
            masks, scores, logits = self.predictor.predict(point_coords=point_coords, point_labels=point_labels, box=input_box[None, :], multimask_output=multimask_output)
        else:
            input_box = np.array(box[0])
            box_tensor = torch.tensor(box, device=self.predictor.device)
            box_transformed = self.predictor.transform.apply_boxes_torch(box_tensor, image.shape[:2])
            masks, scores, logits = self.predictor.predict_torch(point_coords=None, point_labels=None, boxes=box_transformed, multimask_output=False)
        if multimask_output:
            if box is not None and len(box) != 1:
                logits = torch.Tensor.cpu(logits).numpy().reshape(-1, logits.shape[-2], logits.shape[-1])
                masks = torch.Tensor.cpu(masks).numpy().reshape(-1, masks.shape[-2], masks.shape[-1])
                scores = torch.Tensor.cpu(scores).numpy().reshape(-1)
            self.mask_logit = logits[np.argmax(scores), :, :]
            mask = masks[np.argmax(scores), :, :]
            score = np.max(scores)
        return (mask, score)

    def predict_batch(self, boxes=None, image=None):
        boxes = np.array(boxes)
        input_boxes = torch.tensor(boxes, device=self.predictor.device)
        transformed_boxes = self.predictor.transform.apply_boxes_torch(input_boxes, image.shape[:2])
        masks, scores, logits = self.predictor.predict_torch(point_coords=None, point_labels=None, boxes=transformed_boxes, multimask_output=False)
        return (masks, scores)

    def check_image(self, new_image):
        if not np.array_equal(self.image, new_image):
            self.mask_logit = None
            self.image = new_image
            self.predictor.set_image(new_image)
            return False
        return True

    def get_all_shapes(self, image, iou_threshold):
        self.mask_generator = SamAutomaticMaskGenerator(model=self.model)
        sam_result = self.mask_generator.generate(image)
        shapes = mathOps.OURnms_areaBased_fromSAM(sam_result, iou_threshold=iou_threshold)
        return shapes

def set_new_image(self, image):
    self.image = image
    self.predictor.set_image(image)

def check_image(self, new_image):
    if not np.array_equal(self.image, new_image):
        self.mask_logit = None
        self.image = new_image
        self.predictor.set_image(new_image)
        return False
    return True

def match_detections_with_tracks(detections, tracks, iou_threshold=0.5):
    """
    Summary:
        Match detections with tracks based on their bounding boxes using IOU threshold.

    Args:
        detections (list): List of detections, each detection is a dictionary with keys (bbox, confidence, class_id)
        tracks (list): List of tracks, each track is a tuple of (bboxes, track_id, class, conf)
        iou_threshold (float): IOU threshold for matching detections with tracks.

    Returns:
        matched_detections (list): List of detections that are matched with tracks, each detection is a dictionary with keys (bbox, confidence, class_id)
        unmatched_detections (list): List of detections that are not matched with any tracks, each detection is a dictionary with keys (bbox, confidence, class_id)
    """
    matched_detections = []
    unmatched_detections = []
    for detection in detections:
        detection_bbox = detection['bbox']
        max_iou = 0
        matched_track = None
        for track in tracks:
            track_bbox = track[0:4]
            iou = compute_iou(detection_bbox, track_bbox)
            if iou > iou_threshold and iou > max_iou:
                matched_track = track
                max_iou = iou
        if matched_track is not None:
            detection['group_id'] = int(matched_track[4])
            matched_detections.append(detection)
            tracks.remove(matched_track)
        else:
            unmatched_detections.append(detection)
    return (matched_detections, unmatched_detections)

def convert_cv_to_qt(cv_img):
    """
    Summary:
        Convert cv image to QT image format.
        
    Args:
        cv_img: a cv image
        
    Returns:
        convert_to_Qt_format: a QT image format
    """
    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
    return convert_to_Qt_format

def scaleQTshape(self, originalshape, center, ratioX, ratioY):
    """
    Summary:
        Scale a QT shape live in the canvas. 
        according to a center point and two ratios.
        
    Args:
        self: the main window object to access the canvas
        originalshape: the original shape
        center: the center point
        ratioX: the ratio of the x axis
        ratioY: the ratio of the y axis
        
    Returns:
        None
    """
    ratioX = ratioX / 100
    ratioY = ratioY / 100
    shape = self.canvas.selectedShapes[0]
    self.canvas.shapes.remove(shape)
    self.canvas.selectedShapes.remove(shape)
    self.remLabels([shape])
    for i in range(len(shape.points)):
        shape.points[i].setX((originalshape.points[i].x() - center[0]) * ratioX + center[0])
        shape.points[i].setY((originalshape.points[i].y() - center[1]) * ratioY + center[1])
    self.canvas.shapes.append(shape)
    self.canvas.selectedShapes.append(shape)
    self.addLabel(shape)

def mask_to_polygons(mask, n_points=25, resize_factors=[1.0, 1.0]):
    mask = mask > 0.0
    contours = skimage.measure.find_contours(mask)
    if len(contours) == 0:
        return []
    contour = max(contours, key=get_contour_length)
    coords = skimage.measure.approximate_polygon(coords=contour, tolerance=np.ptp(contour, axis=0).max() / 100)
    coords = coords * resize_factors
    coords = np.fliplr(coords)
    segment_points = coords.astype(int)
    polygon = segment_points
    return polygon

def get_default_config():
    config_file = osp.join(here, 'default_config.yaml')
    with open(config_file) as f:
        config = yaml.safe_load(f)
    user_config_file = osp.join(osp.expanduser('~'), '.labelmerc')
    if not osp.exists(user_config_file):
        try:
            shutil.copy(config_file, user_config_file)
        except Exception:
            logger.warn('Failed to save config: {}'.format(user_config_file))
    return config

def make_cuda_ext(name, module, sources, sources_cuda=[]):
    define_macros = []
    extra_compile_args = {'cxx': []}
    if torch.cuda.is_available() or os.getenv('FORCE_CUDA', '0') == '1':
        define_macros += [('WITH_CUDA', None)]
        extension = CUDAExtension
        extra_compile_args['nvcc'] = ['-D__CUDA_NO_HALF_OPERATORS__', '-D__CUDA_NO_HALF_CONVERSIONS__', '-D__CUDA_NO_HALF2_OPERATORS__']
        sources += sources_cuda
    else:
        print(f'Compiling {name} without CUDA')
        extension = CppExtension
    return extension(name=f'{module}.{name}', sources=[os.path.join(*module.split('.'), p) for p in sources], define_macros=define_macros, extra_compile_args=extra_compile_args)

def parse_line(line):
    """Parse information from a line in a requirements text file."""
    if line.startswith('-r '):
        target = line.split(' ')[1]
        for info in parse_require_file(target):
            yield info
    else:
        info = {'line': line}
        if line.startswith('-e '):
            info['package'] = line.split('#egg=')[1]
        elif '@git+' in line:
            info['package'] = line
        else:
            pat = '(' + '|'.join(['>=', '==', '>']) + ')'
            parts = re.split(pat, line, maxsplit=1)
            parts = [p.strip() for p in parts]
            info['package'] = parts[0]
            if len(parts) > 1:
                op, rest = parts[1:]
                if ';' in rest:
                    version, platform_deps = map(str.strip, rest.split(';'))
                    info['platform_deps'] = platform_deps
                else:
                    version = rest
                info['version'] = (op, version)
        yield info

def gen_packages_items():
    if exists(require_fpath):
        for info in parse_require_file(require_fpath):
            parts = [info['package']]
            if with_version and 'version' in info:
                parts.extend(info['version'])
            if not sys.version.startswith('3.4'):
                platform_deps = info.get('platform_deps')
                if platform_deps is not None:
                    parts.append(';' + platform_deps)
            item = ''.join(parts)
            yield item

def add_mim_extension():
    """Add extra files that are required to support MIM into the package.

    These files will be added by creating a symlink to the originals if the
    package is installed in `editable` mode (e.g. pip install -e .), or by
    copying from the originals otherwise.
    """
    if 'develop' in sys.argv:
        if platform.system() == 'Windows':
            mode = 'copy'
        else:
            mode = 'symlink'
    elif 'sdist' in sys.argv or 'bdist_wheel' in sys.argv:
        mode = 'copy'
    else:
        return
    filenames = ['tools', 'configs', 'demo', 'model-index.yml']
    repo_path = osp.dirname(__file__)
    mim_path = osp.join(repo_path, 'mmdet', '.mim')
    os.makedirs(mim_path, exist_ok=True)
    for filename in filenames:
        if osp.exists(filename):
            src_path = osp.join(repo_path, filename)
            tar_path = osp.join(mim_path, filename)
            if osp.isfile(tar_path) or osp.islink(tar_path):
                os.remove(tar_path)
            elif osp.isdir(tar_path):
                shutil.rmtree(tar_path)
            if mode == 'symlink':
                src_relpath = osp.relpath(src_path, osp.dirname(tar_path))
                os.symlink(src_relpath, tar_path)
            elif mode == 'copy':
                if osp.isfile(src_path):
                    shutil.copyfile(src_path, tar_path)
                elif osp.isdir(src_path):
                    shutil.copytree(src_path, tar_path)
                else:
                    warnings.warn(f'Cannot copy file {src_path}.')
            else:
                raise ValueError(f'Invalid mode {mode}')

def check_path(match_tuple: MatchTuple) -> bool:
    """Check if a file in this repository exists."""
    relative_path = match_tuple.link.split('#')[0]
    full_path = os.path.join(os.path.dirname(str(match_tuple.source)), relative_path)
    return os.path.exists(full_path)

def main():
    args = parse_args()
    if args.out:
        out_suffix = args.out.split('.')[-1]
        assert args.out.endswith('.sh'), f'Expected out file path suffix is .sh, but get .{out_suffix}'
    assert args.out or args.run, 'Please specify at least one operation (save/run/ the script) with the argument "--out" or "--run"'
    partition = args.partition
    root_name = './tools'
    train_script_name = osp.join(root_name, 'slurm_train.sh')
    stdout_cfg = '>/dev/null'
    max_keep_ckpts = args.max_keep_ckpts
    commands = []
    with open(args.txt_path, 'r') as f:
        model_cfgs = f.readlines()
        for i, cfg in enumerate(model_cfgs):
            cfg = cfg.strip()
            if len(cfg) == 0:
                continue
            echo_info = f"echo '{cfg}' &"
            commands.append(echo_info)
            commands.append('\n')
            fname, _ = osp.splitext(osp.basename(cfg))
            out_fname = osp.join(root_name, 'work_dir', fname)
            if cfg.find('16x') >= 0:
                command_info = f'GPUS=16  GPUS_PER_NODE=8  CPUS_PER_TASK=2 {train_script_name} '
            elif cfg.find('gn-head_4x4_1x_coco.py') >= 0 or cfg.find('gn-head_4x4_2x_coco.py') >= 0:
                command_info = f'GPUS=4  GPUS_PER_NODE=4  CPUS_PER_TASK=2 {train_script_name} '
            else:
                command_info = f'GPUS=8  GPUS_PER_NODE=8  CPUS_PER_TASK=2 {train_script_name} '
            command_info += f'{partition} '
            command_info += f'{fname} '
            command_info += f'{cfg} '
            command_info += f'{out_fname} '
            if max_keep_ckpts:
                command_info += f'--cfg-options checkpoint_config.max_keep_ckpts={max_keep_ckpts}' + ' '
            command_info += f'{stdout_cfg} &'
            commands.append(command_info)
            if i < len(model_cfgs):
                commands.append('\n')
        command_str = ''.join(commands)
        if args.out:
            with open(args.out, 'w') as f:
                f.write(command_str)
        if args.run:
            os.system(command_str)

def process_model_info(model_info, work_dir):
    config = model_info['config'].strip()
    fname, _ = osp.splitext(osp.basename(config))
    job_name = fname
    work_dir = osp.join(work_dir, fname)
    checkpoint = model_info['checkpoint'].strip()
    if not isinstance(model_info['eval'], list):
        evals = [model_info['eval']]
    else:
        evals = model_info['eval']
    eval = ' '.join(evals)
    return dict(config=config, job_name=job_name, work_dir=work_dir, checkpoint=checkpoint, eval=eval)

def main():
    args = parse_args()
    if args.out:
        out_suffix = args.out.split('.')[-1]
        assert args.out.endswith('.sh'), f'Expected out file path suffix is .sh, but get .{out_suffix}'
    assert args.out or args.run, 'Please specify at least one operation (save/run/ the script) with the argument "--out" or "--run"'
    commands = []
    partition_name = 'PARTITION=$1 '
    commands.append(partition_name)
    commands.append('\n')
    checkpoint_root = 'CHECKPOINT_DIR=$2 '
    commands.append(checkpoint_root)
    commands.append('\n')
    script_name = osp.join('tools', 'slurm_test.sh')
    port = args.port
    work_dir = args.work_dir
    cfg = Config.fromfile(args.config)
    for model_key in cfg:
        model_infos = cfg[model_key]
        if not isinstance(model_infos, list):
            model_infos = [model_infos]
        for model_info in model_infos:
            print('processing: ', model_info['config'])
            model_test_dict = process_model_info(model_info, work_dir)
            create_test_bash_info(commands, model_test_dict, port, script_name, '$PARTITION')
            port += 1
    command_str = ''.join(commands)
    if args.out:
        with open(args.out, 'w') as f:
            f.write(command_str)
    if args.run:
        os.system(command_str)

def _get_config_directory():
    """Find the predefined detector config directory."""
    try:
        repo_dpath = dirname(dirname(__file__))
    except NameError:
        import mmdet
        repo_dpath = dirname(dirname(mmdet.__file__))
    config_dpath = join(repo_dpath, 'configs')
    if not exists(config_dpath):
        raise Exception('Cannot find config path')
    return config_dpath

def _get_config_module(fname):
    """Load a configuration as a python module."""
    from mmcv import Config
    config_dpath = _get_config_directory()
    config_fpath = join(config_dpath, fname)
    config_mod = Config.fromfile(config_fpath)
    return config_mod

def _get_detector_cfg(fname):
    """Grab configs necessary to create a detector.

    These are deep copied to allow for safe modification of parameters without
    influencing other tests.
    """
    config = _get_config_module(fname)
    model = copy.deepcopy(config.model)
    return model

def _traversed_config_file():
    """We traversed all potential config files under the `config` file. If you
    need to print details or debug code, you can use this function.

    If the `backbone.init_cfg` is None (do not use `Pretrained` init way), you
    need add the folder name in `ignores_folder` (if the config files in this
    folder all set backbone.init_cfg is None) or add config name in
    `ignores_file` (if the config file set backbone.init_cfg is None)
    """
    config_path = _get_config_directory()
    check_cfg_names = []
    ignores_folder = ['_base_', 'legacy_1.x', 'common']
    ignores_folder += ['ld']
    ignores_folder += ['selfsup_pretrain']
    ignores_folder += ['centripetalnet', 'cornernet', 'cityscapes', 'scratch']
    ignores_file = ['ssdlite_mobilenetv2_scratch_600e_coco.py']
    for config_file_name in os.listdir(config_path):
        if config_file_name not in ignores_folder:
            config_file = join(config_path, config_file_name)
            if os.path.isdir(config_file):
                for config_sub_file in os.listdir(config_file):
                    if config_sub_file.endswith('py') and config_sub_file not in ignores_file:
                        name = join(config_file, config_sub_file)
                        check_cfg_names.append(name)
    return check_cfg_names

def setup_multi_processes(cfg):
    """Setup multi-processing environment variables."""
    if platform.system() != 'Windows':
        mp_start_method = cfg.get('mp_start_method', 'fork')
        current_method = mp.get_start_method(allow_none=True)
        if current_method is not None and current_method != mp_start_method:
            warnings.warn(f'Multi-processing start method `{mp_start_method}` is different from the previous setting `{current_method}`.It will be force set to `{mp_start_method}`. You can change this behavior by changing `mp_start_method` in your config.')
        mp.set_start_method(mp_start_method, force=True)
    opencv_num_threads = cfg.get('opencv_num_threads', 0)
    cv2.setNumThreads(opencv_num_threads)
    workers_per_gpu = cfg.data.get('workers_per_gpu', 1)
    if 'train_dataloader' in cfg.data:
        workers_per_gpu = max(cfg.data.train_dataloader.get('workers_per_gpu', 1), workers_per_gpu)
    if 'OMP_NUM_THREADS' not in os.environ and workers_per_gpu > 1:
        omp_num_threads = 1
        warnings.warn(f'Setting OMP_NUM_THREADS environment variable for each process to be {omp_num_threads} in default, to avoid your system being overloaded, please further tune the variable for optimal performance in your application as needed.')
        os.environ['OMP_NUM_THREADS'] = str(omp_num_threads)
    if 'MKL_NUM_THREADS' not in os.environ and workers_per_gpu > 1:
        mkl_num_threads = 1
        warnings.warn(f'Setting MKL_NUM_THREADS environment variable for each process to be {mkl_num_threads} in default, to avoid your system being overloaded, please further tune the variable for optimal performance in your application as needed.')
        os.environ['MKL_NUM_THREADS'] = str(mkl_num_threads)

def find_latest_checkpoint(path, suffix='pth'):
    """Find the latest checkpoint from the working directory.

    Args:
        path(str): The path to find checkpoints.
        suffix(str): File extension.
            Defaults to pth.

    Returns:
        latest_path(str | None): File path of the latest checkpoint.
    References:
        .. [1] https://github.com/microsoft/SoftTeacher
                  /blob/main/ssod/utils/patch.py
    """
    if not osp.exists(path):
        warnings.warn('The path of checkpoints does not exist.')
        return None
    if osp.exists(osp.join(path, f'latest.{suffix}')):
        return osp.join(path, f'latest.{suffix}')
    checkpoints = glob.glob(osp.join(path, f'*.{suffix}'))
    if len(checkpoints) == 0:
        warnings.warn('There are no checkpoints in the path.')
        return None
    latest = -1
    latest_path = None
    for checkpoint in checkpoints:
        count = int(osp.basename(checkpoint).split('_')[-1].split('.')[0])
        if count > latest:
            latest = count
            latest_path = checkpoint
    return latest_path

def compat_imgs_per_gpu(cfg):
    cfg = copy.deepcopy(cfg)
    if 'imgs_per_gpu' in cfg.data:
        warnings.warn('"imgs_per_gpu" is deprecated in MMDet V2.0. Please use "samples_per_gpu" instead')
        if 'samples_per_gpu' in cfg.data:
            warnings.warn(f'Got "imgs_per_gpu"={cfg.data.imgs_per_gpu} and "samples_per_gpu"={cfg.data.samples_per_gpu}, "imgs_per_gpu"={cfg.data.imgs_per_gpu} is used in this experiments')
        else:
            warnings.warn(f'Automatically set "samples_per_gpu"="imgs_per_gpu"={cfg.data.imgs_per_gpu} in this experiments')
        cfg.data.samples_per_gpu = cfg.data.imgs_per_gpu
    return cfg

def build_prior_generator(cfg, default_args=None):
    return build_from_cfg(cfg, PRIOR_GENERATORS, default_args)

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

def build_assigner(cfg, **default_args):
    """Builder of box assigner."""
    return build_from_cfg(cfg, BBOX_ASSIGNERS, default_args)

def build_sampler(cfg, **default_args):
    """Builder of box sampler."""
    return build_from_cfg(cfg, BBOX_SAMPLERS, default_args)

def build_bbox_coder(cfg, **default_args):
    """Builder of box coder."""
    return build_from_cfg(cfg, BBOX_CODERS, default_args)

def build_match_cost(cfg, default_args=None):
    """Builder of IoU calculator."""
    return build_from_cfg(cfg, MATCH_COST, default_args)

def build_iou_calculator(cfg, default_args=None):
    """Builder of IoU calculator."""
    return build_from_cfg(cfg, IOU_CALCULATORS, default_args)

class GeneralData(NiceRepr):
    """A general data structure of OpenMMlab.

    A data structure that stores the meta information,
    the annotations of the images or the model predictions,
    which can be used in communication between components.

    The attributes in `GeneralData` are divided into two parts,
    the `meta_info_fields` and the `data_fields` respectively.

        - `meta_info_fields`: Usually contains the
          information about the image such as filename,
          image_shape, pad_shape, etc. All attributes in
          it are immutable once set,
          but the user can add new meta information with
          `set_meta_info` function, all information can be accessed
          with methods `meta_info_keys`, `meta_info_values`,
          `meta_info_items`.

        - `data_fields`: Annotations or model predictions are
          stored. The attributes can be accessed or modified by
          dict-like or object-like operations, such as
          `.` , `[]`, `in`, `del`, `pop(str)` `get(str)`, `keys()`,
          `values()`, `items()`. Users can also apply tensor-like methods
          to all obj:`torch.Tensor` in the `data_fileds`,
          such as `.cuda()`, `.cpu()`, `.numpy()`, `device`, `.to()`
          `.detach()`, `.numpy()`

    Args:
        meta_info (dict, optional): A dict contains the meta information
            of single image. such as `img_shape`, `scale_factor`, etc.
            Default: None.
        data (dict, optional): A dict contains annotations of single image or
            model predictions. Default: None.

    Examples:
        >>> from mmdet.core import GeneralData
        >>> img_meta = dict(img_shape=(800, 1196, 3), pad_shape=(800, 1216, 3))
        >>> instance_data = GeneralData(meta_info=img_meta)
        >>> img_shape in instance_data
        True
        >>> instance_data.det_labels = torch.LongTensor([0, 1, 2, 3])
        >>> instance_data["det_scores"] = torch.Tensor([0.01, 0.1, 0.2, 0.3])
        >>> print(results)
        <GeneralData(

          META INFORMATION
        img_shape: (800, 1196, 3)
        pad_shape: (800, 1216, 3)

          DATA FIELDS
        shape of det_labels: torch.Size([4])
        shape of det_scores: torch.Size([4])

        ) at 0x7f84acd10f90>
        >>> instance_data.det_scores
        tensor([0.0100, 0.1000, 0.2000, 0.3000])
        >>> instance_data.det_labels
        tensor([0, 1, 2, 3])
        >>> instance_data['det_labels']
        tensor([0, 1, 2, 3])
        >>> 'det_labels' in instance_data
        True
        >>> instance_data.img_shape
        (800, 1196, 3)
        >>> 'det_scores' in instance_data
        True
        >>> del instance_data.det_scores
        >>> 'det_scores' in instance_data
        False
        >>> det_labels = instance_data.pop('det_labels', None)
        >>> det_labels
        tensor([0, 1, 2, 3])
        >>> 'det_labels' in instance_data
        >>> False
    """

    def __init__(self, meta_info=None, data=None):
        self._meta_info_fields = set()
        self._data_fields = set()
        if meta_info is not None:
            self.set_meta_info(meta_info=meta_info)
        if data is not None:
            self.set_data(data)

    def set_meta_info(self, meta_info):
        """Add meta information.

        Args:
            meta_info (dict): A dict contains the meta information
                of image. such as `img_shape`, `scale_factor`, etc.
                Default: None.
        """
        assert isinstance(meta_info, dict), f'meta should be a `dict` but get {meta_info}'
        meta = copy.deepcopy(meta_info)
        for k, v in meta.items():
            if k in self._meta_info_fields:
                ori_value = getattr(self, k)
                if isinstance(ori_value, (torch.Tensor, np.ndarray)):
                    if (ori_value == v).all():
                        continue
                    else:
                        raise KeyError(f'img_meta_info {k} has been set as {getattr(self, k)} before, which is immutable ')
                elif ori_value == v:
                    continue
                else:
                    raise KeyError(f'img_meta_info {k} has been set as {getattr(self, k)} before, which is immutable ')
            else:
                self._meta_info_fields.add(k)
                self.__dict__[k] = v

    def set_data(self, data):
        """Update a dict to `data_fields`.

        Args:
            data (dict): A dict contains annotations of image or
                model predictions. Default: None.
        """
        assert isinstance(data, dict), f'meta should be a `dict` but get {data}'
        for k, v in data.items():
            self.__setattr__(k, v)

    def new(self, meta_info=None, data=None):
        """Return a new results with same image meta information.

        Args:
            meta_info (dict, optional): A dict contains the meta information
                of image. such as `img_shape`, `scale_factor`, etc.
                Default: None.
            data (dict, optional): A dict contains annotations of image or
                model predictions. Default: None.
        """
        new_data = self.__class__()
        new_data.set_meta_info(dict(self.meta_info_items()))
        if meta_info is not None:
            new_data.set_meta_info(meta_info)
        if data is not None:
            new_data.set_data(data)
        return new_data

    def keys(self):
        """
        Returns:
            list: Contains all keys in data_fields.
        """
        return [key for key in self._data_fields]

    def meta_info_keys(self):
        """
        Returns:
            list: Contains all keys in meta_info_fields.
        """
        return [key for key in self._meta_info_fields]

    def values(self):
        """
        Returns:
            list: Contains all values in data_fields.
        """
        return [getattr(self, k) for k in self.keys()]

    def meta_info_values(self):
        """
        Returns:
            list: Contains all values in meta_info_fields.
        """
        return [getattr(self, k) for k in self.meta_info_keys()]

    def items(self):
        for k in self.keys():
            yield (k, getattr(self, k))

    def meta_info_items(self):
        for k in self.meta_info_keys():
            yield (k, getattr(self, k))

    def __setattr__(self, name, val):
        if name in ('_meta_info_fields', '_data_fields'):
            if not hasattr(self, name):
                super().__setattr__(name, val)
            else:
                raise AttributeError(f'{name} has been used as a private attribute, which is immutable. ')
        else:
            if name in self._meta_info_fields:
                raise AttributeError(f'`{name}` is used in meta information,which is immutable')
            self._data_fields.add(name)
            super().__setattr__(name, val)

    def __delattr__(self, item):
        if item in ('_meta_info_fields', '_data_fields'):
            raise AttributeError(f'{item} has been used as a private attribute, which is immutable. ')
        if item in self._meta_info_fields:
            raise KeyError(f'{item} is used in meta information, which is immutable.')
        super().__delattr__(item)
        if item in self._data_fields:
            self._data_fields.remove(item)
    __setitem__ = __setattr__
    __delitem__ = __delattr__

    def __getitem__(self, name):
        return getattr(self, name)

    def get(self, *args):
        assert len(args) < 3, '`get` get more than 2 arguments'
        return self.__dict__.get(*args)

    def pop(self, *args):
        assert len(args) < 3, '`pop` get more than 2 arguments'
        name = args[0]
        if name in self._meta_info_fields:
            raise KeyError(f'{name} is a key in meta information, which is immutable')
        if args[0] in self._data_fields:
            self._data_fields.remove(args[0])
            return self.__dict__.pop(*args)
        elif len(args) == 2:
            return args[1]
        else:
            raise KeyError(f'{args[0]}')

    def __contains__(self, item):
        return item in self._data_fields or item in self._meta_info_fields

    def to(self, *args, **kwargs):
        """Apply same name function to all tensors in data_fields."""
        new_data = self.new()
        for k, v in self.items():
            if hasattr(v, 'to'):
                v = v.to(*args, **kwargs)
            new_data[k] = v
        return new_data

    def cpu(self):
        """Apply same name function to all tensors in data_fields."""
        new_data = self.new()
        for k, v in self.items():
            if isinstance(v, torch.Tensor):
                v = v.cpu()
            new_data[k] = v
        return new_data

    def npu(self):
        """Apply same name function to all tensors in data_fields."""
        new_data = self.new()
        for k, v in self.items():
            if isinstance(v, torch.Tensor):
                v = v.npu()
            new_data[k] = v
        return new_data

    def mlu(self):
        """Apply same name function to all tensors in data_fields."""
        new_data = self.new()
        for k, v in self.items():
            if isinstance(v, torch.Tensor):
                v = v.mlu()
            new_data[k] = v
        return new_data

    def cuda(self):
        """Apply same name function to all tensors in data_fields."""
        new_data = self.new()
        for k, v in self.items():
            if isinstance(v, torch.Tensor):
                v = v.cuda()
            new_data[k] = v
        return new_data

    def detach(self):
        """Apply same name function to all tensors in data_fields."""
        new_data = self.new()
        for k, v in self.items():
            if isinstance(v, torch.Tensor):
                v = v.detach()
            new_data[k] = v
        return new_data

    def numpy(self):
        """Apply same name function to all tensors in data_fields."""
        new_data = self.new()
        for k, v in self.items():
            if isinstance(v, torch.Tensor):
                v = v.detach().cpu().numpy()
            new_data[k] = v
        return new_data

    def __nice__(self):
        repr = '\n \n  META INFORMATION \n'
        for k, v in self.meta_info_items():
            repr += f'{k}: {v} \n'
        repr += '\n   DATA FIELDS \n'
        for k, v in self.items():
            if isinstance(v, (torch.Tensor, np.ndarray)):
                repr += f'shape of {k}: {v.shape} \n'
            else:
                repr += f'{k}: {v} \n'
        return repr + '\n'

def pop(self, *args):
    assert len(args) < 3, '`pop` get more than 2 arguments'
    name = args[0]
    if name in self._meta_info_fields:
        raise KeyError(f'{name} is a key in meta information, which is immutable')
    if args[0] in self._data_fields:
        self._data_fields.remove(args[0])
        return self.__dict__.pop(*args)
    elif len(args) == 2:
        return args[1]
    else:
        raise KeyError(f'{args[0]}')

def build_transformer(cfg, default_args=None):
    """Builder for Transformer."""
    return build_from_cfg(cfg, TRANSFORMER, default_args)

def collect_files(img_dir, gt_dir):
    suffix = 'leftImg8bit.png'
    files = []
    for img_file in glob.glob(osp.join(img_dir, '**/*.png')):
        assert img_file.endswith(suffix), img_file
        inst_file = gt_dir + img_file[len(img_dir):-len(suffix)] + 'gtFine_instanceIds.png'
        segm_file = gt_dir + img_file[len(img_dir):-len(suffix)] + 'gtFine_labelIds.png'
        files.append((img_file, inst_file, segm_file))
    assert len(files), f'No images found in {img_dir}'
    print(f'Loaded {len(files)} images from {img_dir}')
    return files

def load_img_info(files):
    img_file, inst_file, segm_file = files
    inst_img = mmcv.imread(inst_file, 'unchanged')
    unique_inst_ids = np.unique(inst_img[inst_img >= 24])
    anno_info = []
    for inst_id in unique_inst_ids:
        label_id = inst_id // 1000 if inst_id >= 1000 else inst_id
        label = CSLabels.id2label[label_id]
        if not label.hasInstances or label.ignoreInEval:
            continue
        category_id = label.id
        iscrowd = int(inst_id < 1000)
        mask = np.asarray(inst_img == inst_id, dtype=np.uint8, order='F')
        mask_rle = maskUtils.encode(mask[:, :, None])[0]
        area = maskUtils.area(mask_rle)
        bbox = maskUtils.toBbox(mask_rle)
        mask_rle['counts'] = mask_rle['counts'].decode()
        anno = dict(iscrowd=iscrowd, category_id=category_id, bbox=bbox.tolist(), area=area.tolist(), segmentation=mask_rle)
        anno_info.append(anno)
    video_name = osp.basename(osp.dirname(img_file))
    img_info = dict(file_name=osp.join(video_name, osp.basename(img_file)), height=inst_img.shape[0], width=inst_img.shape[1], anno_info=anno_info, segm_file=osp.join(video_name, osp.basename(segm_file)))
    return img_info

def collect_image_infos(path, exclude_extensions=None):
    img_infos = []
    images_generator = mmcv.scandir(path, recursive=True)
    for image_path in mmcv.track_iter_progress(list(images_generator)):
        if exclude_extensions is None or (exclude_extensions is not None and (not image_path.lower().endswith(exclude_extensions))):
            image_path = os.path.join(path, image_path)
            img_pillow = Image.open(image_path)
            img_info = {'filename': image_path, 'width': img_pillow.width, 'height': img_pillow.height}
            img_infos.append(img_info)
    return img_infos

def main():
    args = parse_args()
    assert args.out.endswith('json'), 'The output file name must be json suffix'
    img_infos = collect_image_infos(args.img_path, args.exclude_extensions)
    classes = mmcv.list_from_file(args.classes)
    coco_info = cvt_to_coco_json(img_infos, classes)
    save_dir = os.path.join(args.img_path, '..', 'annotations')
    mmcv.mkdir_or_exist(save_dir)
    save_path = os.path.join(save_dir, args.out)
    mmcv.dump(coco_info, save_path)
    print(f'save json file: {save_path}')

def cvt_annotations(devkit_path, years, split, out_file):
    if not isinstance(years, list):
        years = [years]
    annotations = []
    for year in years:
        filelist = osp.join(devkit_path, f'VOC{year}/ImageSets/Main/{split}.txt')
        if not osp.isfile(filelist):
            print(f'filelist does not exist: {filelist}, skip voc{year} {split}')
            return
        img_names = mmcv.list_from_file(filelist)
        xml_paths = [osp.join(devkit_path, f'VOC{year}/Annotations/{img_name}.xml') for img_name in img_names]
        img_paths = [f'VOC{year}/JPEGImages/{img_name}.jpg' for img_name in img_names]
        part_annotations = mmcv.track_progress(parse_xml, list(zip(xml_paths, img_paths)))
        annotations.extend(part_annotations)
    if out_file.endswith('json'):
        annotations = cvt_to_coco_json(annotations)
    mmcv.dump(annotations, out_file)
    return annotations

def analyze_individual_category(k, cocoDt, cocoGt, catId, iou_type, areas=None):
    nm = cocoGt.loadCats(catId)[0]
    print(f'--------------analyzing {k + 1}-{nm['name']}---------------')
    ps_ = {}
    dt = copy.deepcopy(cocoDt)
    nm = cocoGt.loadCats(catId)[0]
    imgIds = cocoGt.getImgIds()
    dt_anns = dt.dataset['annotations']
    select_dt_anns = []
    for ann in dt_anns:
        if ann['category_id'] == catId:
            select_dt_anns.append(ann)
    dt.dataset['annotations'] = select_dt_anns
    dt.createIndex()
    gt = copy.deepcopy(cocoGt)
    child_catIds = gt.getCatIds(supNms=[nm['supercategory']])
    for idx, ann in enumerate(gt.dataset['annotations']):
        if ann['category_id'] in child_catIds and ann['category_id'] != catId:
            gt.dataset['annotations'][idx]['ignore'] = 1
            gt.dataset['annotations'][idx]['iscrowd'] = 1
            gt.dataset['annotations'][idx]['category_id'] = catId
    cocoEval = COCOeval(gt, copy.deepcopy(dt), iou_type)
    cocoEval.params.imgIds = imgIds
    cocoEval.params.maxDets = [100]
    cocoEval.params.iouThrs = [0.1]
    cocoEval.params.useCats = 1
    if areas:
        cocoEval.params.areaRng = [[0 ** 2, areas[2]], [0 ** 2, areas[0]], [areas[0], areas[1]], [areas[1], areas[2]]]
    cocoEval.evaluate()
    cocoEval.accumulate()
    ps_supercategory = cocoEval.eval['precision'][0, :, k, :, :]
    ps_['ps_supercategory'] = ps_supercategory
    gt = copy.deepcopy(cocoGt)
    for idx, ann in enumerate(gt.dataset['annotations']):
        if ann['category_id'] != catId:
            gt.dataset['annotations'][idx]['ignore'] = 1
            gt.dataset['annotations'][idx]['iscrowd'] = 1
            gt.dataset['annotations'][idx]['category_id'] = catId
    cocoEval = COCOeval(gt, copy.deepcopy(dt), iou_type)
    cocoEval.params.imgIds = imgIds
    cocoEval.params.maxDets = [100]
    cocoEval.params.iouThrs = [0.1]
    cocoEval.params.useCats = 1
    if areas:
        cocoEval.params.areaRng = [[0 ** 2, areas[2]], [0 ** 2, areas[0]], [areas[0], areas[1]], [areas[1], areas[2]]]
    cocoEval.evaluate()
    cocoEval.accumulate()
    ps_allcategory = cocoEval.eval['precision'][0, :, k, :, :]
    ps_['ps_allcategory'] = ps_allcategory
    return (k, ps_)

def analyze_results(res_file, ann_file, res_types, out_dir, extraplots=None, areas=None):
    for res_type in res_types:
        assert res_type in ['bbox', 'segm']
    if areas:
        assert len(areas) == 3, '3 integers should be specified as areas,             representing 3 area regions'
    directory = os.path.dirname(out_dir + '/')
    if not os.path.exists(directory):
        print(f'-------------create {out_dir}-----------------')
        os.makedirs(directory)
    cocoGt = COCO(ann_file)
    cocoDt = cocoGt.loadRes(res_file)
    imgIds = cocoGt.getImgIds()
    for res_type in res_types:
        res_out_dir = out_dir + '/' + res_type + '/'
        res_directory = os.path.dirname(res_out_dir)
        if not os.path.exists(res_directory):
            print(f'-------------create {res_out_dir}-----------------')
            os.makedirs(res_directory)
        iou_type = res_type
        cocoEval = COCOeval(copy.deepcopy(cocoGt), copy.deepcopy(cocoDt), iou_type)
        cocoEval.params.imgIds = imgIds
        cocoEval.params.iouThrs = [0.75, 0.5, 0.1]
        cocoEval.params.maxDets = [100]
        if areas:
            cocoEval.params.areaRng = [[0 ** 2, areas[2]], [0 ** 2, areas[0]], [areas[0], areas[1]], [areas[1], areas[2]]]
        cocoEval.evaluate()
        cocoEval.accumulate()
        ps = cocoEval.eval['precision']
        ps = np.vstack([ps, np.zeros((4, *ps.shape[1:]))])
        catIds = cocoGt.getCatIds()
        recThrs = cocoEval.params.recThrs
        with Pool(processes=48) as pool:
            args = [(k, cocoDt, cocoGt, catId, iou_type, areas) for k, catId in enumerate(catIds)]
            analyze_results = pool.starmap(analyze_individual_category, args)
        for k, catId in enumerate(catIds):
            nm = cocoGt.loadCats(catId)[0]
            print(f'--------------saving {k + 1}-{nm['name']}---------------')
            analyze_result = analyze_results[k]
            assert k == analyze_result[0]
            ps_supercategory = analyze_result[1]['ps_supercategory']
            ps_allcategory = analyze_result[1]['ps_allcategory']
            ps[3, :, k, :, :] = ps_supercategory
            ps[4, :, k, :, :] = ps_allcategory
            ps[ps == -1] = 0
            ps[5, :, k, :, :] = ps[4, :, k, :, :] > 0
            ps[6, :, k, :, :] = 1.0
            makeplot(recThrs, ps[:, :, k], res_out_dir, nm['name'], iou_type)
            if extraplots:
                makebarplot(recThrs, ps[:, :, k], res_out_dir, nm['name'], iou_type)
        makeplot(recThrs, ps, res_out_dir, 'allclass', iou_type)
        if extraplots:
            makebarplot(recThrs, ps, res_out_dir, 'allclass', iou_type)
            make_gt_area_group_numbers_plot(cocoEval=cocoEval, outDir=res_out_dir, verbose=True)
            make_gt_area_histogram_plot(cocoEval=cocoEval, outDir=res_out_dir)

def coco_eval_with_return(result_files, result_types, coco, max_dets=(100, 300, 1000)):
    for res_type in result_types:
        assert res_type in ['proposal', 'bbox', 'segm', 'keypoints']
    if mmcv.is_str(coco):
        coco = COCO(coco)
    assert isinstance(coco, COCO)
    eval_results = {}
    for res_type in result_types:
        result_file = result_files[res_type]
        assert result_file.endswith('.json')
        coco_dets = coco.loadRes(result_file)
        img_ids = coco.getImgIds()
        iou_type = 'bbox' if res_type == 'proposal' else res_type
        cocoEval = COCOeval(coco, coco_dets, iou_type)
        cocoEval.params.imgIds = img_ids
        if res_type == 'proposal':
            cocoEval.params.useCats = 0
            cocoEval.params.maxDets = list(max_dets)
        cocoEval.evaluate()
        cocoEval.accumulate()
        cocoEval.summarize()
        if res_type == 'segm' or res_type == 'bbox':
            metric_names = ['AP', 'AP50', 'AP75', 'APs', 'APm', 'APl', 'AR1', 'AR10', 'AR100', 'ARs', 'ARm', 'ARl']
            eval_results[res_type] = {metric_names[i]: cocoEval.stats[i] for i in range(len(metric_names))}
        else:
            eval_results[res_type] = cocoEval.stats
    return eval_results

class ResultVisualizer:
    """Display and save evaluation results.

    Args:
        show (bool): Whether to show the image. Default: True.
        wait_time (float): Value of waitKey param. Default: 0.
        score_thr (float): Minimum score of bboxes to be shown.
           Default: 0.
        overlay_gt_pred (bool): Whether to plot gts and predictions on the
            same image. If False, predictions and gts will be plotted on two
            same image which will be concatenated in vertical direction.
            The image above is drawn with gt, and the image below is drawn
            with the prediction result. Default: False.
    """

    def __init__(self, show=False, wait_time=0, score_thr=0, overlay_gt_pred=False):
        self.show = show
        self.wait_time = wait_time
        self.score_thr = score_thr
        self.overlay_gt_pred = overlay_gt_pred

    def _save_image_gts_results(self, dataset, results, performances, out_dir=None):
        """Display or save image with groung truths and predictions from a
        model.

        Args:
            dataset (Dataset): A PyTorch dataset.
            results (list): Object detection or panoptic segmentation
                results from test results pkl file.
            performances (dict): A dict contains samples's indices
                in dataset and model's performance on them.
            out_dir (str, optional): The filename to write the image.
                Defaults: None.
        """
        mmcv.mkdir_or_exist(out_dir)
        for performance_info in performances:
            index, performance = performance_info
            data_info = dataset.prepare_train_img(index)
            filename = data_info['filename']
            if data_info['img_prefix'] is not None:
                filename = osp.join(data_info['img_prefix'], filename)
            else:
                filename = data_info['filename']
            fname, name = osp.splitext(osp.basename(filename))
            save_filename = fname + '_' + str(round(performance, 3)) + name
            out_file = osp.join(out_dir, save_filename)
            imshow_gt_det_bboxes(data_info['img'], data_info, results[index], dataset.CLASSES, gt_bbox_color=dataset.PALETTE, gt_text_color=(200, 200, 200), gt_mask_color=dataset.PALETTE, det_bbox_color=dataset.PALETTE, det_text_color=(200, 200, 200), det_mask_color=dataset.PALETTE, show=self.show, score_thr=self.score_thr, wait_time=self.wait_time, out_file=out_file, overlay_gt_pred=self.overlay_gt_pred)

    def evaluate_and_show(self, dataset, results, topk=20, show_dir='work_dir'):
        """Evaluate and show results.

        Args:
            dataset (Dataset): A PyTorch dataset.
            results (list): Object detection or panoptic segmentation
                results from test results pkl file.
            topk (int): Number of the highest topk and
                lowest topk after evaluation index sorting. Default: 20.
            show_dir (str, optional): The filename to write the image.
                Default: 'work_dir'
            eval_fn (callable, optional): Eval function, Default: None.
        """
        assert topk > 0
        if topk * 2 > len(dataset):
            topk = len(dataset) // 2
        if isinstance(results[0], dict):
            good_samples, bad_samples = self.panoptic_evaluate(dataset, results, topk=topk)
        elif isinstance(results[0], list):
            good_samples, bad_samples = self.detection_evaluate(dataset, results, topk=topk)
        elif isinstance(results[0], tuple):
            results_ = [result[0] for result in results]
            good_samples, bad_samples = self.detection_evaluate(dataset, results_, topk=topk)
        else:
            raise 'The format of result is not supported yet. Current dict for panoptic segmentation and list or tuple for object detection are supported.'
        good_dir = osp.abspath(osp.join(show_dir, 'good'))
        bad_dir = osp.abspath(osp.join(show_dir, 'bad'))
        self._save_image_gts_results(dataset, results, good_samples, good_dir)
        self._save_image_gts_results(dataset, results, bad_samples, bad_dir)

    def detection_evaluate(self, dataset, results, topk=20, eval_fn=None):
        """Evaluation for object detection.

        Args:
            dataset (Dataset): A PyTorch dataset.
            results (list): Object detection results from test
                results pkl file.
            topk (int): Number of the highest topk and
                lowest topk after evaluation index sorting. Default: 20.
            eval_fn (callable, optional): Eval function, Default: None.

        Returns:
            tuple: A tuple contains good samples and bad samples.
                good_mAPs (dict[int, float]): A dict contains good
                    samples's indices in dataset and model's
                    performance on them.
                bad_mAPs (dict[int, float]): A dict contains bad
                    samples's indices in dataset and model's
                    performance on them.
        """
        if eval_fn is None:
            eval_fn = bbox_map_eval
        else:
            assert callable(eval_fn)
        prog_bar = mmcv.ProgressBar(len(results))
        _mAPs = {}
        for i, (result,) in enumerate(zip(results)):
            data_info = dataset.prepare_train_img(i)
            mAP = eval_fn(result, data_info['ann_info'])
            _mAPs[i] = mAP
            prog_bar.update()
        _mAPs = list(sorted(_mAPs.items(), key=lambda kv: kv[1]))
        good_mAPs = _mAPs[-topk:]
        bad_mAPs = _mAPs[:topk]
        return (good_mAPs, bad_mAPs)

    def panoptic_evaluate(self, dataset, results, topk=20):
        """Evaluation for panoptic segmentation.

        Args:
            dataset (Dataset): A PyTorch dataset.
            results (list): Panoptic segmentation results from test
                results pkl file.
            topk (int): Number of the highest topk and
                lowest topk after evaluation index sorting. Default: 20.

        Returns:
            tuple: A tuple contains good samples and bad samples.
                good_pqs (dict[int, float]): A dict contains good
                    samples's indices in dataset and model's
                    performance on them.
                bad_pqs (dict[int, float]): A dict contains bad
                    samples's indices in dataset and model's
                    performance on them.
        """
        gt_json = dataset.coco.img_ann_map
        result_files, tmp_dir = dataset.format_results(results)
        pred_json = mmcv.load(result_files['panoptic'])['annotations']
        pred_folder = osp.join(tmp_dir.name, 'panoptic')
        gt_folder = dataset.seg_prefix
        pqs = {}
        prog_bar = mmcv.ProgressBar(len(results))
        for i in range(len(results)):
            data_info = dataset.prepare_train_img(i)
            image_id = data_info['img_info']['id']
            gt_ann = {'image_id': image_id, 'segments_info': gt_json[image_id], 'file_name': data_info['img_info']['segm_file']}
            pred_ann = pred_json[i]
            pq_stat = pq_compute_single_core(i, [(gt_ann, pred_ann)], gt_folder, pred_folder, dataset.categories, dataset.file_client, print_log=False)
            pq_results, classwise_results = pq_stat.pq_average(dataset.categories, isthing=None)
            pqs[i] = pq_results['pq']
            prog_bar.update()
        if tmp_dir is not None:
            tmp_dir.cleanup()
        pqs = list(sorted(pqs.items(), key=lambda kv: kv[1]))
        good_pqs = pqs[-topk:]
        bad_pqs = pqs[:topk]
        return (good_pqs, bad_pqs)

def _save_image_gts_results(self, dataset, results, performances, out_dir=None):
    """Display or save image with groung truths and predictions from a
        model.

        Args:
            dataset (Dataset): A PyTorch dataset.
            results (list): Object detection or panoptic segmentation
                results from test results pkl file.
            performances (dict): A dict contains samples's indices
                in dataset and model's performance on them.
            out_dir (str, optional): The filename to write the image.
                Defaults: None.
        """
    mmcv.mkdir_or_exist(out_dir)
    for performance_info in performances:
        index, performance = performance_info
        data_info = dataset.prepare_train_img(index)
        filename = data_info['filename']
        if data_info['img_prefix'] is not None:
            filename = osp.join(data_info['img_prefix'], filename)
        else:
            filename = data_info['filename']
        fname, name = osp.splitext(osp.basename(filename))
        save_filename = fname + '_' + str(round(performance, 3)) + name
        out_file = osp.join(out_dir, save_filename)
        imshow_gt_det_bboxes(data_info['img'], data_info, results[index], dataset.CLASSES, gt_bbox_color=dataset.PALETTE, gt_text_color=(200, 200, 200), gt_mask_color=dataset.PALETTE, det_bbox_color=dataset.PALETTE, det_text_color=(200, 200, 200), det_mask_color=dataset.PALETTE, show=self.show, score_thr=self.score_thr, wait_time=self.wait_time, out_file=out_file, overlay_gt_pred=self.overlay_gt_pred)

def _get_config_directory():
    """Find the predefined detector config directory."""
    try:
        repo_dpath = dirname(dirname(dirname(__file__)))
    except NameError:
        import mmdet
        repo_dpath = dirname(dirname(mmdet.__file__))
    config_dpath = join(repo_dpath, 'configs')
    if not exists(config_dpath):
        raise Exception('Cannot find config path')
    return config_dpath

def _get_config_module(fname):
    """Load a configuration as a python module."""
    from mmcv import Config
    config_dpath = _get_config_directory()
    config_fpath = join(config_dpath, fname)
    config_mod = Config.fromfile(config_fpath)
    return config_mod

def _get_detector_cfg(fname):
    """Grab configs necessary to create a detector.

    These are deep copied to allow for safe modification of parameters without
    influencing other tests.
    """
    config = _get_config_module(fname)
    model = copy.deepcopy(config.model)
    return model

def _get_config_directory():
    """Find the predefined detector config directory."""
    try:
        repo_dpath = dirname(dirname(dirname(__file__)))
    except NameError:
        import mmdet
        repo_dpath = dirname(dirname(mmdet.__file__))
    config_dpath = join(repo_dpath, 'configs')
    if not exists(config_dpath):
        raise Exception('Cannot find config path')
    return config_dpath

def _get_config_module(fname):
    """Load a configuration as a python module."""
    from mmcv import Config
    config_dpath = _get_config_directory()
    config_fpath = join(config_dpath, fname)
    config_mod = Config.fromfile(config_fpath)
    return config_mod

def _get_detector_cfg(fname):
    """Grab configs necessary to create a detector.

    These are deep copied to allow for safe modification of parameters without
    influencing other tests.
    """
    config = _get_config_module(fname)
    model = copy.deepcopy(config.model)
    return model

def _replace_r50_with_r18(model):
    """Replace ResNet50 with ResNet18 in config."""
    model = copy.deepcopy(model)
    if model.backbone.type == 'ResNet':
        model.backbone.depth = 18
        model.backbone.base_channels = 2
        model.neck.in_channels = [2, 4, 8, 16]
    return model

def test_imshow_det_bboxes():
    tmp_filename = osp.join(tempfile.gettempdir(), 'det_bboxes_image', 'image.jpg')
    image = np.ones((10, 10, 3), np.uint8)
    bbox = np.array([[2, 1, 3, 3], [3, 4, 6, 6]])
    label = np.array([0, 1])
    out_image = vis.imshow_det_bboxes(image, bbox, label, out_file=tmp_filename, show=False)
    assert osp.isfile(tmp_filename)
    assert image.shape == out_image.shape
    assert not np.allclose(image, out_image)
    os.remove(tmp_filename)
    image = np.ones((10, 10), np.uint8)
    bbox = np.array([[2, 1, 3, 3], [3, 4, 6, 6]])
    label = np.array([0, 1])
    out_image = vis.imshow_det_bboxes(image, bbox, label, out_file=tmp_filename, show=False)
    assert osp.isfile(tmp_filename)
    assert image.shape == out_image.shape[:2]
    os.remove(tmp_filename)
    image = np.ones((10, 10, 3), np.uint8)
    bbox = np.ones((0, 4))
    label = np.ones((0,))
    vis.imshow_det_bboxes(image, bbox, label, out_file=tmp_filename, show=False)
    assert osp.isfile(tmp_filename)
    os.remove(tmp_filename)
    image = np.ones((10, 10, 3), np.uint8)
    bbox = np.array([[2, 1, 3, 3], [3, 4, 6, 6]])
    label = np.array([0, 1])
    segms = np.random.random((2, 10, 10)) > 0.5
    segms = np.array(segms, np.int32)
    vis.imshow_det_bboxes(image, bbox, label, segms, out_file=tmp_filename, show=False)
    assert osp.isfile(tmp_filename)
    os.remove(tmp_filename)
    with pytest.raises(AttributeError):
        segms = torch.tensor(segms)
        vis.imshow_det_bboxes(image, bbox, label, segms, show=False)

def test_imshow_gt_det_bboxes():
    tmp_filename = osp.join(tempfile.gettempdir(), 'det_bboxes_image', 'image.jpg')
    image = np.ones((10, 10, 3), np.uint8)
    bbox = np.array([[2, 1, 3, 3], [3, 4, 6, 6]])
    label = np.array([0, 1])
    annotation = dict(gt_bboxes=bbox, gt_labels=label)
    det_result = np.array([[2, 1, 3, 3, 0], [3, 4, 6, 6, 1]])
    result = [det_result]
    out_image = vis.imshow_gt_det_bboxes(image, annotation, result, out_file=tmp_filename, show=False)
    assert osp.isfile(tmp_filename)
    assert image.shape == out_image.shape
    assert not np.allclose(image, out_image)
    os.remove(tmp_filename)
    image = np.ones((10, 10), np.uint8)
    bbox = np.array([[2, 1, 3, 3], [3, 4, 6, 6]])
    label = np.array([0, 1])
    annotation = dict(gt_bboxes=bbox, gt_labels=label)
    det_result = np.array([[2, 1, 3, 3, 0], [3, 4, 6, 6, 1]])
    result = [det_result]
    vis.imshow_gt_det_bboxes(image, annotation, result, out_file=tmp_filename, show=False)
    assert osp.isfile(tmp_filename)
    os.remove(tmp_filename)
    gt_mask = np.ones((2, 10, 10))
    annotation['gt_masks'] = gt_mask
    vis.imshow_gt_det_bboxes(image, annotation, result, out_file=tmp_filename, show=False)
    assert osp.isfile(tmp_filename)
    os.remove(tmp_filename)
    gt_mask = torch.ones((2, 10, 10))
    annotation['gt_masks'] = gt_mask
    vis.imshow_gt_det_bboxes(image, annotation, result, out_file=tmp_filename, show=False)
    assert osp.isfile(tmp_filename)
    os.remove(tmp_filename)
    annotation['gt_masks'] = []
    with pytest.raises(TypeError):
        vis.imshow_gt_det_bboxes(image, annotation, result, show=False)

def test_setup_multi_processes():
    sys_start_mehod = mp.get_start_method(allow_none=True)
    sys_cv_threads = cv2.getNumThreads()
    sys_omp_threads = os.environ.pop('OMP_NUM_THREADS', default=None)
    sys_mkl_threads = os.environ.pop('MKL_NUM_THREADS', default=None)
    config = dict(data=dict(workers_per_gpu=2))
    cfg = Config(config)
    setup_multi_processes(cfg)
    assert os.getenv('OMP_NUM_THREADS') == '1'
    assert os.getenv('MKL_NUM_THREADS') == '1'
    assert cv2.getNumThreads() == 1
    if platform.system() != 'Windows':
        assert mp.get_start_method() == 'fork'
    os.environ.pop('OMP_NUM_THREADS')
    os.environ.pop('MKL_NUM_THREADS')
    config = dict(data=dict(workers_per_gpu=0))
    cfg = Config(config)
    setup_multi_processes(cfg)
    assert 'OMP_NUM_THREADS' not in os.environ
    assert 'MKL_NUM_THREADS' not in os.environ
    os.environ['OMP_NUM_THREADS'] = '4'
    config = dict(data=dict(workers_per_gpu=2))
    cfg = Config(config)
    setup_multi_processes(cfg)
    assert os.getenv('OMP_NUM_THREADS') == '4'
    config = dict(data=dict(workers_per_gpu=2), opencv_num_threads=4, mp_start_method='spawn')
    cfg = Config(config)
    setup_multi_processes(cfg)
    assert cv2.getNumThreads() == 4
    assert mp.get_start_method() == 'spawn'
    if sys_start_mehod:
        mp.set_start_method(sys_start_mehod, force=True)
    cv2.setNumThreads(sys_cv_threads)
    if sys_omp_threads:
        os.environ['OMP_NUM_THREADS'] = sys_omp_threads
    else:
        os.environ.pop('OMP_NUM_THREADS')
    if sys_mkl_threads:
        os.environ['MKL_NUM_THREADS'] = sys_mkl_threads
    else:
        os.environ.pop('MKL_NUM_THREADS')

def test_split_batch():
    img_root = osp.join(osp.dirname(__file__), '../data/color.jpg')
    img = mmcv.imread(img_root, 'color')
    h, w, _ = img.shape
    gt_bboxes = np.array([[0.2 * w, 0.2 * h, 0.4 * w, 0.4 * h], [0.6 * w, 0.6 * h, 0.8 * w, 0.8 * h]], dtype=np.float32)
    gt_lables = np.ones(gt_bboxes.shape[0], dtype=np.int64)
    img = torch.tensor(img).permute(2, 0, 1)
    meta = dict()
    meta['filename'] = img_root
    meta['ori_shape'] = img.shape
    meta['img_shape'] = img.shape
    meta['img_norm_cfg'] = {'mean': np.array([103.53, 116.28, 123.675], dtype=np.float32), 'std': np.array([1.0, 1.0, 1.0], dtype=np.float32), 'to_rgb': False}
    meta['pad_shape'] = img.shape
    imgs = img.unsqueeze(0).repeat(9, 1, 1, 1)
    img_metas = []
    tags = ['sup', 'unsup_teacher', 'unsup_student', 'unsup_teacher', 'unsup_student', 'unsup_teacher', 'unsup_student', 'unsup_teacher', 'unsup_student']
    for tag in tags:
        img_meta = deepcopy(meta)
        if tag == 'sup':
            img_meta['scale_factor'] = [0.5, 0.5, 0.5, 0.5]
            img_meta['tag'] = 'sup'
        elif tag == 'unsup_teacher':
            img_meta['scale_factor'] = [1.0, 1.0, 1.0, 1.0]
            img_meta['tag'] = 'unsup_teacher'
        elif tag == 'unsup_student':
            img_meta['scale_factor'] = [2.0, 2.0, 2.0, 2.0]
            img_meta['tag'] = 'unsup_student'
        else:
            continue
        img_metas.append(img_meta)
    kwargs = dict()
    kwargs['gt_bboxes'] = [torch.tensor(gt_bboxes)] + [torch.zeros(0, 4)] * 8
    kwargs['gt_lables'] = [torch.tensor(gt_lables)] + [torch.zeros(0)] * 8
    data_groups = split_batch(imgs, img_metas, kwargs)
    assert set(data_groups.keys()) == set(tags)
    assert data_groups['sup']['img'].shape == (1, 3, h, w)
    assert data_groups['unsup_teacher']['img'].shape == (4, 3, h, w)
    assert data_groups['unsup_student']['img'].shape == (4, 3, h, w)
    assert data_groups['sup']['img_metas'][0]['scale_factor'] == [0.5, 0.5, 0.5, 0.5]
    assert data_groups['unsup_teacher']['img_metas'][0]['scale_factor'] == [1.0, 1.0, 1.0, 1.0]
    assert data_groups['unsup_teacher']['img_metas'][1]['scale_factor'] == [1.0, 1.0, 1.0, 1.0]
    assert data_groups['unsup_teacher']['img_metas'][2]['scale_factor'] == [1.0, 1.0, 1.0, 1.0]
    assert data_groups['unsup_teacher']['img_metas'][3]['scale_factor'] == [1.0, 1.0, 1.0, 1.0]
    assert data_groups['unsup_student']['img_metas'][0]['scale_factor'] == [2.0, 2.0, 2.0, 2.0]
    assert data_groups['unsup_student']['img_metas'][1]['scale_factor'] == [2.0, 2.0, 2.0, 2.0]
    assert data_groups['unsup_student']['img_metas'][2]['scale_factor'] == [2.0, 2.0, 2.0, 2.0]
    assert data_groups['unsup_student']['img_metas'][3]['scale_factor'] == [2.0, 2.0, 2.0, 2.0]

def test_replace_cfg_vals():
    temp_file = tempfile.NamedTemporaryFile()
    cfg_path = f'{temp_file.name}.py'
    with open(cfg_path, 'w') as f:
        f.write('configs')
    ori_cfg_dict = dict()
    ori_cfg_dict['cfg_name'] = osp.basename(temp_file.name)
    ori_cfg_dict['work_dir'] = 'work_dirs/${cfg_name}/${percent}/${fold}'
    ori_cfg_dict['percent'] = 5
    ori_cfg_dict['fold'] = 1
    ori_cfg_dict['model_wrapper'] = dict(type='SoftTeacher', detector='${model}')
    ori_cfg_dict['model'] = dict(type='FasterRCNN', backbone=dict(type='ResNet'), neck=dict(type='FPN'), rpn_head=dict(type='RPNHead'), roi_head=dict(type='StandardRoIHead'), train_cfg=dict(rpn=dict(assigner=dict(type='MaxIoUAssigner'), sampler=dict(type='RandomSampler')), rpn_proposal=dict(nms=dict(type='nms', iou_threshold=0.7)), rcnn=dict(assigner=dict(type='MaxIoUAssigner'), sampler=dict(type='RandomSampler'))), test_cfg=dict(rpn=dict(nms=dict(type='nms', iou_threshold=0.7)), rcnn=dict(nms=dict(type='nms', iou_threshold=0.5))))
    ori_cfg_dict['iou_threshold'] = dict(rpn_proposal_nms='${model.train_cfg.rpn_proposal.nms.iou_threshold}', test_rpn_nms='${model.test_cfg.rpn.nms.iou_threshold}', test_rcnn_nms='${model.test_cfg.rcnn.nms.iou_threshold}')
    ori_cfg_dict['str'] = 'Hello, world!'
    ori_cfg_dict['dict'] = {'Hello': 'world!'}
    ori_cfg_dict['list'] = ['Hello, world!']
    ori_cfg_dict['tuple'] = ('Hello, world!',)
    ori_cfg_dict['test_str'] = 'xxx${str}xxx'
    ori_cfg = Config(ori_cfg_dict, filename=cfg_path)
    updated_cfg = replace_cfg_vals(deepcopy(ori_cfg))
    assert updated_cfg.work_dir == f'work_dirs/{osp.basename(temp_file.name)}/5/1'
    assert updated_cfg.model.detector == ori_cfg.model
    assert updated_cfg.iou_threshold.rpn_proposal_nms == ori_cfg.model.train_cfg.rpn_proposal.nms.iou_threshold
    assert updated_cfg.test_str == 'xxxHello, world!xxx'
    ori_cfg_dict['test_dict'] = 'xxx${dict}xxx'
    ori_cfg_dict['test_list'] = 'xxx${list}xxx'
    ori_cfg_dict['test_tuple'] = 'xxx${tuple}xxx'
    with pytest.raises(AssertionError):
        cfg = deepcopy(ori_cfg)
        cfg['test_dict'] = 'xxx${dict}xxx'
        updated_cfg = replace_cfg_vals(cfg)
    with pytest.raises(AssertionError):
        cfg = deepcopy(ori_cfg)
        cfg['test_list'] = 'xxx${list}xxx'
        updated_cfg = replace_cfg_vals(cfg)
    with pytest.raises(AssertionError):
        cfg = deepcopy(ori_cfg)
        cfg['test_tuple'] = 'xxx${tuple}xxx'
        updated_cfg = replace_cfg_vals(cfg)

def test_init_detector():
    project_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    project_dir = os.path.join(project_dir, '..')
    config_file = os.path.join(project_dir, 'configs/mask_rcnn/mask_rcnn_r50_fpn_1x_coco.py')
    cfg_options = dict(model=dict(backbone=dict(depth=18, init_cfg=dict(type='Pretrained', checkpoint='torchvision://resnet18'))))
    model = init_detector(config_file, device='cpu', cfg_options=cfg_options)
    config_path_object = Path(config_file)
    model = init_detector(config_path_object, device='cpu')
    with pytest.raises(TypeError):
        config_list = [config_file]
        model = init_detector(config_list)

def _get_config_directory():
    """Find the predefined detector config directory."""
    try:
        repo_dpath = dirname(dirname(__file__))
        repo_dpath = join(repo_dpath, '..')
    except NameError:
        import mmdet
        repo_dpath = dirname(dirname(mmdet.__file__))
    config_dpath = join(repo_dpath, 'configs')
    if not exists(config_dpath):
        raise Exception('Cannot find config path')
    return config_dpath

def dummy_masks(h, w, num_obj=3, mode='bitmap'):
    assert mode in ('polygon', 'bitmap')
    if mode == 'bitmap':
        masks = np.random.randint(0, 2, (num_obj, h, w), dtype=np.uint8)
        masks = BitmapMasks(masks, h, w)
    else:
        masks = []
        for i in range(num_obj):
            masks.append([])
            masks[-1].append(np.random.uniform(0, min(h - 1, w - 1), (8 + 4 * i,)))
            masks[-1].append(np.random.uniform(0, min(h - 1, w - 1), (10 + 4 * i,)))
        masks = PolygonMasks(masks, h, w)
    return masks

@pytest.mark.parametrize('classes, expected_length', [(['bus'], 2), (['car'], 1), (['bus', 'car'], 2)])
def test_allow_empty_images(classes, expected_length):
    dataset_class = DATASETS.get('CocoDataset')
    filtered_dataset = dataset_class(ann_file='tests/data/coco_sample.json', img_prefix='tests/data', pipeline=[], classes=classes, filter_empty_gt=True)
    full_dataset = dataset_class(ann_file='tests/data/coco_sample.json', img_prefix='tests/data', pipeline=[], classes=classes, filter_empty_gt=False)
    assert len(filtered_dataset) == expected_length
    assert len(filtered_dataset.img_ids) == expected_length
    assert len(full_dataset) == 3
    assert len(full_dataset.img_ids) == 3
    assert filtered_dataset.CLASSES == classes
    assert full_dataset.CLASSES == classes

class CustomDatasetTests(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.data_dir = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))), 'data')
        self.dataset_class = DATASETS.get('XMLDataset')

    def test_data_infos__default_db_directories(self):
        """Test correct data read having a Pacal-VOC directory structure."""
        test_dataset_root = osp.join(self.data_dir, 'VOCdevkit', 'VOC2007')
        custom_ds = self.dataset_class(data_root=test_dataset_root, ann_file=osp.join(test_dataset_root, 'ImageSets', 'Main', 'trainval.txt'), pipeline=[], classes=('person', 'dog'), test_mode=True)
        self.assertListEqual([{'id': '000001', 'filename': osp.join('JPEGImages', '000001.jpg'), 'width': 353, 'height': 500}], custom_ds.data_infos)

    def test_data_infos__overridden_db_subdirectories(self):
        """Test correct data read having a customized directory structure."""
        test_dataset_root = osp.join(self.data_dir, 'custom_dataset')
        custom_ds = self.dataset_class(data_root=test_dataset_root, ann_file=osp.join(test_dataset_root, 'trainval.txt'), pipeline=[], classes=('person', 'dog'), test_mode=True, img_prefix='', img_subdir='images', ann_subdir='images')
        self.assertListEqual([{'id': '000001', 'filename': osp.join('images', '000001.jpg'), 'width': 353, 'height': 500}], custom_ds.data_infos)

def setUp(self):
    super().setUp()
    self.data_dir = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))), 'data')
    self.dataset_class = DATASETS.get('XMLDataset')

def test_data_infos__default_db_directories(self):
    """Test correct data read having a Pacal-VOC directory structure."""
    test_dataset_root = osp.join(self.data_dir, 'VOCdevkit', 'VOC2007')
    custom_ds = self.dataset_class(data_root=test_dataset_root, ann_file=osp.join(test_dataset_root, 'ImageSets', 'Main', 'trainval.txt'), pipeline=[], classes=('person', 'dog'), test_mode=True)
    self.assertListEqual([{'id': '000001', 'filename': osp.join('JPEGImages', '000001.jpg'), 'width': 353, 'height': 500}], custom_ds.data_infos)

def test_data_infos__overridden_db_subdirectories(self):
    """Test correct data read having a customized directory structure."""
    test_dataset_root = osp.join(self.data_dir, 'custom_dataset')
    custom_ds = self.dataset_class(data_root=test_dataset_root, ann_file=osp.join(test_dataset_root, 'trainval.txt'), pipeline=[], classes=('person', 'dog'), test_mode=True, img_prefix='', img_subdir='images', ann_subdir='images')
    self.assertListEqual([{'id': '000001', 'filename': osp.join('images', '000001.jpg'), 'width': 353, 'height': 500}], custom_ds.data_infos)

def _create_panoptic_gt_annotations(ann_file):
    categories = [{'id': 0, 'name': 'person', 'supercategory': 'person', 'isthing': 1}, {'id': 1, 'name': 'dog', 'supercategory': 'dog', 'isthing': 1}, {'id': 2, 'name': 'wall', 'supercategory': 'wall', 'isthing': 0}]
    images = [{'id': 0, 'width': 80, 'height': 60, 'file_name': 'fake_name1.jpg'}]
    annotations = [{'segments_info': [{'id': 1, 'category_id': 0, 'area': 400, 'bbox': [10, 10, 10, 40], 'iscrowd': 0}, {'id': 2, 'category_id': 0, 'area': 400, 'bbox': [30, 10, 10, 40], 'iscrowd': 0}, {'id': 3, 'category_id': 1, 'iscrowd': 0, 'bbox': [50, 10, 10, 5], 'area': 50}, {'id': 4, 'category_id': 2, 'iscrowd': 0, 'bbox': [0, 0, 80, 60], 'area': 3950}], 'file_name': 'fake_name1.png', 'image_id': 0}]
    gt_json = {'images': images, 'annotations': annotations, 'categories': categories}
    gt = np.zeros((60, 80), dtype=np.int64) + 4
    gt_bboxes = np.array([[10, 10, 10, 40], [30, 10, 10, 40], [50, 10, 10, 5]], dtype=np.int64)
    for i in range(3):
        x, y, w, h = gt_bboxes[i]
        gt[y:y + h, x:x + w] = i + 1
    gt = id2rgb(gt).astype(np.uint8)
    img_path = osp.join(osp.dirname(ann_file), 'fake_name1.png')
    mmcv.imwrite(gt[:, :, ::-1], img_path)
    mmcv.dump(gt_json, ann_file)
    return gt_json

class TestLoading:

    @classmethod
    def setup_class(cls):
        cls.data_prefix = osp.join(osp.dirname(__file__), '../../data')

    def test_load_img(self):
        results = dict(img_prefix=self.data_prefix, img_info=dict(filename='color.jpg'))
        transform = LoadImageFromFile()
        results = transform(copy.deepcopy(results))
        assert results['filename'] == osp.join(self.data_prefix, 'color.jpg')
        assert results['ori_filename'] == 'color.jpg'
        assert results['img'].shape == (288, 512, 3)
        assert results['img'].dtype == np.uint8
        assert results['img_shape'] == (288, 512, 3)
        assert results['ori_shape'] == (288, 512, 3)
        assert repr(transform) == transform.__class__.__name__ + "(to_float32=False, color_type='color', channel_order='bgr', " + "file_client_args={'backend': 'disk'})"
        results = dict(img_prefix=None, img_info=dict(filename='tests/data/color.jpg'))
        transform = LoadImageFromFile()
        results = transform(copy.deepcopy(results))
        assert results['filename'] == 'tests/data/color.jpg'
        assert results['ori_filename'] == 'tests/data/color.jpg'
        assert results['img'].shape == (288, 512, 3)
        transform = LoadImageFromFile(to_float32=True)
        results = transform(copy.deepcopy(results))
        assert results['img'].dtype == np.float32
        results = dict(img_prefix=self.data_prefix, img_info=dict(filename='gray.jpg'))
        transform = LoadImageFromFile()
        results = transform(copy.deepcopy(results))
        assert results['img'].shape == (288, 512, 3)
        assert results['img'].dtype == np.uint8
        transform = LoadImageFromFile(color_type='unchanged')
        results = transform(copy.deepcopy(results))
        assert results['img'].shape == (288, 512)
        assert results['img'].dtype == np.uint8

    def test_load_multi_channel_img(self):
        results = dict(img_prefix=self.data_prefix, img_info=dict(filename=['color.jpg', 'color.jpg']))
        transform = LoadMultiChannelImageFromFiles()
        results = transform(copy.deepcopy(results))
        assert results['filename'] == [osp.join(self.data_prefix, 'color.jpg'), osp.join(self.data_prefix, 'color.jpg')]
        assert results['ori_filename'] == ['color.jpg', 'color.jpg']
        assert results['img'].shape == (288, 512, 3, 2)
        assert results['img'].dtype == np.uint8
        assert results['img_shape'] == (288, 512, 3, 2)
        assert results['ori_shape'] == (288, 512, 3, 2)
        assert results['pad_shape'] == (288, 512, 3, 2)
        assert results['scale_factor'] == 1.0
        assert repr(transform) == transform.__class__.__name__ + "(to_float32=False, color_type='unchanged', " + "file_client_args={'backend': 'disk'})"

    def test_load_webcam_img(self):
        img = mmcv.imread(osp.join(self.data_prefix, 'color.jpg'))
        results = dict(img=img)
        transform = LoadImageFromWebcam()
        results = transform(copy.deepcopy(results))
        assert results['filename'] is None
        assert results['ori_filename'] is None
        assert results['img'].shape == (288, 512, 3)
        assert results['img'].dtype == np.uint8
        assert results['img_shape'] == (288, 512, 3)
        assert results['ori_shape'] == (288, 512, 3)

@classmethod
def setup_class(cls):
    cls.data_prefix = osp.join(osp.dirname(__file__), '../../data')

def test_load_img(self):
    results = dict(img_prefix=self.data_prefix, img_info=dict(filename='color.jpg'))
    transform = LoadImageFromFile()
    results = transform(copy.deepcopy(results))
    assert results['filename'] == osp.join(self.data_prefix, 'color.jpg')
    assert results['ori_filename'] == 'color.jpg'
    assert results['img'].shape == (288, 512, 3)
    assert results['img'].dtype == np.uint8
    assert results['img_shape'] == (288, 512, 3)
    assert results['ori_shape'] == (288, 512, 3)
    assert repr(transform) == transform.__class__.__name__ + "(to_float32=False, color_type='color', channel_order='bgr', " + "file_client_args={'backend': 'disk'})"
    results = dict(img_prefix=None, img_info=dict(filename='tests/data/color.jpg'))
    transform = LoadImageFromFile()
    results = transform(copy.deepcopy(results))
    assert results['filename'] == 'tests/data/color.jpg'
    assert results['ori_filename'] == 'tests/data/color.jpg'
    assert results['img'].shape == (288, 512, 3)
    transform = LoadImageFromFile(to_float32=True)
    results = transform(copy.deepcopy(results))
    assert results['img'].dtype == np.float32
    results = dict(img_prefix=self.data_prefix, img_info=dict(filename='gray.jpg'))
    transform = LoadImageFromFile()
    results = transform(copy.deepcopy(results))
    assert results['img'].shape == (288, 512, 3)
    assert results['img'].dtype == np.uint8
    transform = LoadImageFromFile(color_type='unchanged')
    results = transform(copy.deepcopy(results))
    assert results['img'].shape == (288, 512)
    assert results['img'].dtype == np.uint8

def test_load_multi_channel_img(self):
    results = dict(img_prefix=self.data_prefix, img_info=dict(filename=['color.jpg', 'color.jpg']))
    transform = LoadMultiChannelImageFromFiles()
    results = transform(copy.deepcopy(results))
    assert results['filename'] == [osp.join(self.data_prefix, 'color.jpg'), osp.join(self.data_prefix, 'color.jpg')]
    assert results['ori_filename'] == ['color.jpg', 'color.jpg']
    assert results['img'].shape == (288, 512, 3, 2)
    assert results['img'].dtype == np.uint8
    assert results['img_shape'] == (288, 512, 3, 2)
    assert results['ori_shape'] == (288, 512, 3, 2)
    assert results['pad_shape'] == (288, 512, 3, 2)
    assert results['scale_factor'] == 1.0
    assert repr(transform) == transform.__class__.__name__ + "(to_float32=False, color_type='unchanged', " + "file_client_args={'backend': 'disk'})"

def test_load_webcam_img(self):
    img = mmcv.imread(osp.join(self.data_prefix, 'color.jpg'))
    results = dict(img=img)
    transform = LoadImageFromWebcam()
    results = transform(copy.deepcopy(results))
    assert results['filename'] is None
    assert results['ori_filename'] is None
    assert results['img'].shape == (288, 512, 3)
    assert results['img'].dtype == np.uint8
    assert results['img_shape'] == (288, 512, 3)
    assert results['ori_shape'] == (288, 512, 3)

def test_default_format_bundle():
    results = dict(img_prefix=osp.join(osp.dirname(__file__), '../../data'), img_info=dict(filename='color.jpg'))
    load = dict(type='LoadImageFromFile')
    load = build_from_cfg(load, PIPELINES)
    bundle = dict(type='DefaultFormatBundle')
    bundle = build_from_cfg(bundle, PIPELINES)
    results = load(results)
    assert 'pad_shape' not in results
    assert 'scale_factor' not in results
    assert 'img_norm_cfg' not in results
    results = bundle(results)
    assert 'pad_shape' in results
    assert 'scale_factor' in results
    assert 'img_norm_cfg' in results

def test_aug_test_size():
    results = dict(img_prefix=osp.join(osp.dirname(__file__), '../../../data'), img_info=dict(filename='color.jpg'))
    load = dict(type='LoadImageFromFile')
    load = build_from_cfg(load, PIPELINES)
    transform = dict(type='MultiScaleFlipAug', transforms=[], img_scale=[(1333, 800), (800, 600), (640, 480)], flip=True, flip_direction=['horizontal', 'vertical', 'diagonal'])
    multi_aug_test_module = build_from_cfg(transform, PIPELINES)
    results = load(results)
    results = multi_aug_test_module(load(results))
    assert len(results['img']) == 12

def check_result_same(results, pipeline_results):
    """Check whether the `pipeline_results` is the same with the predefined
    `results`.

    Args:
        results (dict): Predefined results which should be the standard output
            of the transform pipeline.
        pipeline_results (dict): Results processed by the transform pipeline.
    """
    _check_fields(results, pipeline_results, results.get('img_fields', ['img']))
    _check_fields(results, pipeline_results, results.get('bbox_fields', []))
    _check_fields(results, pipeline_results, results.get('mask_fields', []))
    _check_fields(results, pipeline_results, results.get('seg_fields', []))
    if 'gt_labels' in results:
        assert np.equal(results['gt_labels'], pipeline_results['gt_labels']).all()

def _construct_img(results):
    h, w = (results['img_info']['height'], results['img_info']['width'])
    img = np.random.uniform(0, 1, (h, w, 3)) * 255
    img = img.astype(np.uint8)
    results['img'] = img
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['img_fields'] = ['img']

def _construct_semantic_seg(results):
    h, w = (results['img_info']['height'], results['img_info']['width'])
    seg_toy = (np.random.uniform(0, 1, (h, w)) * 255).astype(np.uint8)
    results['gt_semantic_seg'] = seg_toy
    results['seg_fields'] = ['gt_semantic_seg']

def test_translate():
    with pytest.raises(AssertionError):
        transform = dict(type='Translate', level=-1)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Translate', level=[1])
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Translate', level=1, prob=-0.5)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Translate', level=1, img_fill_val=(128, 128, 128, 128))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(ValueError):
        transform = dict(type='Translate', level=1, img_fill_val=[128, 128, 128])
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Translate', level=1, img_fill_val=(128, -1, 256))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Translate', level=1, img_fill_val=128, direction='diagonal')
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Translate', level=1, img_fill_val=128, max_translate_offset=(250.0,))
        build_from_cfg(transform, PIPELINES)
    results = construct_toy_data()

    def _check_bbox_mask(results, results_translated, offset, direction, min_size=0.0):
        bbox2label = {'gt_bboxes': 'gt_labels', 'gt_bboxes_ignore': 'gt_labels_ignore'}
        bbox2mask = {'gt_bboxes': 'gt_masks', 'gt_bboxes_ignore': 'gt_masks_ignore'}

        def _translate_bbox(bboxes, offset, direction, max_h, max_w):
            if direction == 'horizontal':
                bboxes[:, 0::2] = bboxes[:, 0::2] + offset
            elif direction == 'vertical':
                bboxes[:, 1::2] = bboxes[:, 1::2] + offset
            else:
                raise ValueError
            bboxes[:, 0::2] = np.clip(bboxes[:, 0::2], 0, max_w)
            bboxes[:, 1::2] = np.clip(bboxes[:, 1::2], 0, max_h)
            return bboxes
        h, w, c = results_translated['img'].shape
        for key in results_translated.get('bbox_fields', []):
            label_key, mask_key = (bbox2label[key], bbox2mask[key])
            if label_key in results:
                assert len(results_translated[key]) == len(results_translated[label_key])
            if mask_key in results:
                assert len(results_translated[key]) == len(results_translated[mask_key])
            gt_bboxes = _translate_bbox(copy.deepcopy(results[key]), offset, direction, h, w)
            valid_inds = (gt_bboxes[:, 2] - gt_bboxes[:, 0] > min_size) & (gt_bboxes[:, 3] - gt_bboxes[:, 1] > min_size)
            gt_bboxes = gt_bboxes[valid_inds]
            assert np.equal(gt_bboxes, results_translated[key]).all()
            if mask_key not in results:
                continue
            masks, masks_translated = (results[mask_key].to_ndarray(), results_translated[mask_key].to_ndarray())
            assert masks.dtype == masks_translated.dtype
            if direction == 'horizontal':
                masks_pad = _pad(h, abs(offset), masks.shape[0], 0, axis=0, dtype=masks.dtype)
                if offset <= 0:
                    gt_masks = np.concatenate((masks[:, :, -offset:], masks_pad), axis=-1)
                else:
                    gt_masks = np.concatenate((masks_pad, masks[:, :, :-offset]), axis=-1)
            else:
                masks_pad = _pad(abs(offset), w, masks.shape[0], 0, axis=0, dtype=masks.dtype)
                if offset <= 0:
                    gt_masks = np.concatenate((masks[:, -offset:, :], masks_pad), axis=1)
                else:
                    gt_masks = np.concatenate((masks_pad, masks[:, :-offset, :]), axis=1)
            gt_masks = gt_masks[valid_inds]
            assert np.equal(gt_masks, masks_translated).all()

    def _check_img_seg(results, results_translated, keys, offset, fill_val, direction):
        for key in keys:
            assert isinstance(results_translated[key], type(results[key]))
            data, data_translated = (results[key], results_translated[key])
            if 'mask' in key:
                data, data_translated = (data.to_ndarray(), data_translated.to_ndarray())
            assert data.dtype == data_translated.dtype
            if 'img' in key:
                data, data_translated = (data.transpose((2, 0, 1)), data_translated.transpose((2, 0, 1)))
            elif 'seg' in key:
                data, data_translated = (data[None, :, :], data_translated[None, :, :])
            c, h, w = data.shape
            if direction == 'horizontal':
                data_pad = _pad(h, abs(offset), c, fill_val, axis=0, dtype=data.dtype)
                if offset <= 0:
                    data_gt = np.concatenate((data[:, :, -offset:], data_pad), axis=-1)
                else:
                    data_gt = np.concatenate((data_pad, data[:, :, :-offset]), axis=-1)
            else:
                data_pad = _pad(abs(offset), w, c, fill_val, axis=0, dtype=data.dtype)
                if offset <= 0:
                    data_gt = np.concatenate((data[:, -offset:, :], data_pad), axis=1)
                else:
                    data_gt = np.concatenate((data_pad, data[:, :-offset, :]), axis=1)
            if 'mask' in key:
                pass
            else:
                assert np.equal(data_gt, data_translated).all()

    def check_translate(results, results_translated, offset, img_fill_val, seg_ignore_label, direction, min_size=0):
        _check_keys(results, results_translated)
        _check_img_seg(results, results_translated, results.get('img_fields', ['img']), offset, img_fill_val, direction)
        _check_img_seg(results, results_translated, results.get('seg_fields', []), offset, seg_ignore_label, direction)
        _check_bbox_mask(results, results_translated, offset, direction, min_size)
    img_fill_val = (104, 116, 124)
    seg_ignore_label = 255
    transform = dict(type='Translate', level=0, prob=1.0, img_fill_val=img_fill_val, seg_ignore_label=seg_ignore_label)
    translate_module = build_from_cfg(transform, PIPELINES)
    results_wo_translate = translate_module(copy.deepcopy(results))
    check_translate(copy.deepcopy(results), results_wo_translate, 0, img_fill_val, seg_ignore_label, 'horizontal')
    transform = dict(type='Translate', level=8, prob=1.0, img_fill_val=img_fill_val, random_negative_prob=1.0, seg_ignore_label=seg_ignore_label)
    translate_module = build_from_cfg(transform, PIPELINES)
    offset = translate_module.offset
    results_translated = translate_module(copy.deepcopy(results))
    check_translate(copy.deepcopy(results), results_translated, -offset, img_fill_val, seg_ignore_label, 'horizontal')
    translate_module.random_negative_prob = 0.0
    results_translated = translate_module(copy.deepcopy(results))
    check_translate(copy.deepcopy(results), results_translated, offset, img_fill_val, seg_ignore_label, 'horizontal')
    transform = dict(type='Translate', level=10, prob=1.0, img_fill_val=img_fill_val, seg_ignore_label=seg_ignore_label, random_negative_prob=1.0, direction='vertical')
    translate_module = build_from_cfg(transform, PIPELINES)
    offset = translate_module.offset
    results_translated = translate_module(copy.deepcopy(results))
    check_translate(copy.deepcopy(results), results_translated, -offset, img_fill_val, seg_ignore_label, 'vertical')
    translate_module.random_negative_prob = 0.0
    results_translated = translate_module(copy.deepcopy(results))
    check_translate(copy.deepcopy(results), results_translated, offset, img_fill_val, seg_ignore_label, 'vertical')
    transform = dict(type='Translate', level=8, prob=0.0, img_fill_val=img_fill_val, random_negative_prob=0.0, seg_ignore_label=seg_ignore_label)
    translate_module = build_from_cfg(transform, PIPELINES)
    results_translated = translate_module(copy.deepcopy(results))
    results = construct_toy_data(False)
    transform = dict(type='Translate', level=10, prob=1.0, img_fill_val=img_fill_val, seg_ignore_label=seg_ignore_label, direction='vertical')
    translate_module = build_from_cfg(transform, PIPELINES)
    offset = translate_module.offset
    translate_module.random_negative_prob = 1.0
    results_translated = translate_module(copy.deepcopy(results))

    def _translated_gt(masks, direction, offset, out_shape):
        translated_masks = []
        for poly_per_obj in masks:
            translated_poly_per_obj = []
            for p in poly_per_obj:
                p = p.copy()
                if direction == 'horizontal':
                    p[0::2] = np.clip(p[0::2] + offset, 0, out_shape[1])
                elif direction == 'vertical':
                    p[1::2] = np.clip(p[1::2] + offset, 0, out_shape[0])
                if PolygonMasks([[p]], *out_shape).areas[0] > 0:
                    translated_poly_per_obj.append(p)
            if len(translated_poly_per_obj):
                translated_masks.append(translated_poly_per_obj)
        translated_masks = PolygonMasks(translated_masks, *out_shape)
        return translated_masks
    h, w = results['img_shape'][:2]
    for key in results.get('mask_fields', []):
        masks = results[key]
        translated_gt = _translated_gt(masks, 'vertical', -offset, (h, w))
        assert np.equal(results_translated[key].to_ndarray(), translated_gt.to_ndarray()).all()
    results = construct_toy_data(False)
    transform = dict(type='Translate', level=8, prob=1.0, img_fill_val=img_fill_val, random_negative_prob=0.0, seg_ignore_label=seg_ignore_label)
    translate_module = build_from_cfg(transform, PIPELINES)
    offset = translate_module.offset
    results_translated = translate_module(copy.deepcopy(results))
    h, w = results['img_shape'][:2]
    for key in results.get('mask_fields', []):
        masks = results[key]
        translated_gt = _translated_gt(masks, 'horizontal', offset, (h, w))
        assert np.equal(results_translated[key].to_ndarray(), translated_gt.to_ndarray()).all()
    policies = [[dict(type='Translate', level=10, prob=1.0)]]
    autoaug = dict(type='AutoAugment', policies=policies)
    autoaug_module = build_from_cfg(autoaug, PIPELINES)
    autoaug_module(copy.deepcopy(results))
    policies = [[dict(type='Translate', level=10, prob=1.0), dict(type='Translate', level=8, img_fill_val=img_fill_val, direction='vertical')]]
    autoaug = dict(type='AutoAugment', policies=policies)
    autoaug_module = build_from_cfg(autoaug, PIPELINES)
    autoaug_module(copy.deepcopy(results))

def test_shear():
    with pytest.raises(AssertionError):
        transform = dict(type='Shear', level=1, max_shear_magnitude=(0.5,))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Shear', level=2, max_shear_magnitude=1.2)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(ValueError):
        transform = dict(type='Shear', level=2, img_fill_val=[128])
        build_from_cfg(transform, PIPELINES)
    results = construct_toy_data()
    img_fill_val = (104, 116, 124)
    seg_ignore_label = 255
    transform = dict(type='Shear', level=0, prob=1.0, img_fill_val=img_fill_val, seg_ignore_label=seg_ignore_label, direction='horizontal')
    shear_module = build_from_cfg(transform, PIPELINES)
    results_wo_shear = shear_module(copy.deepcopy(results))
    check_result_same(results, results_wo_shear)
    transform = dict(type='Shear', level=0, prob=1.0, img_fill_val=img_fill_val, seg_ignore_label=seg_ignore_label, direction='vertical')
    shear_module = build_from_cfg(transform, PIPELINES)
    results_wo_shear = shear_module(copy.deepcopy(results))
    check_result_same(results, results_wo_shear)
    transform = dict(type='Shear', level=10, prob=0.0, img_fill_val=img_fill_val, direction='vertical')
    shear_module = build_from_cfg(transform, PIPELINES)
    results_wo_shear = shear_module(copy.deepcopy(results))
    check_result_same(results, results_wo_shear)
    transform = dict(type='Shear', level=10, prob=1.0, img_fill_val=img_fill_val, direction='horizontal', max_shear_magnitude=1.0, random_negative_prob=0.0)
    shear_module = build_from_cfg(transform, PIPELINES)
    results_sheared = shear_module(copy.deepcopy(results))
    results_gt = copy.deepcopy(results)
    img_s = np.array([[1, 2, 3, 4], [0, 5, 6, 7]], dtype=np.uint8)
    img_s = np.stack([img_s, img_s, img_s], axis=-1)
    img_s[1, 0, :] = np.array(img_fill_val)
    results_gt['img'] = img_s
    results_gt['gt_bboxes'] = np.array([[0.0, 0.0, 3.0, 1.0]], dtype=np.float32)
    results_gt['gt_bboxes_ignore'] = np.array([[2.0, 0.0, 4.0, 1.0]], dtype=np.float32)
    gt_masks = np.array([[0, 1, 1, 0], [0, 0, 1, 0]], dtype=np.uint8)[None, :, :]
    results_gt['gt_masks'] = BitmapMasks(gt_masks, 2, 4)
    results_gt['gt_semantic_seg'] = np.array([[1, 2, 3, 4], [255, 5, 6, 7]], dtype=results['gt_semantic_seg'].dtype)
    check_result_same(results_gt, results_sheared)
    results = construct_toy_data(poly2mask=False)
    results_sheared = shear_module(copy.deepcopy(results))
    print(results_sheared['gt_masks'])
    gt_masks = [[np.array([0, 0, 2, 0, 3, 1, 1, 1], dtype=np.float)]]
    results_gt['gt_masks'] = PolygonMasks(gt_masks, 2, 4)
    check_result_same(results_gt, results_sheared)
    img_fill_val = 128
    results = construct_toy_data()
    transform = dict(type='Shear', level=10, prob=1.0, img_fill_val=img_fill_val, direction='vertical', max_shear_magnitude=1.0, random_negative_prob=1.0)
    shear_module = build_from_cfg(transform, PIPELINES)
    results_sheared = shear_module(copy.deepcopy(results))
    results_gt = copy.deepcopy(results)
    img_s = np.array([[1, 6, img_fill_val, img_fill_val], [5, img_fill_val, img_fill_val, img_fill_val]], dtype=np.uint8)
    img_s = np.stack([img_s, img_s, img_s], axis=-1)
    results_gt['img'] = img_s
    results_gt['gt_bboxes'] = np.empty((0, 4), dtype=np.float32)
    results_gt['gt_labels'] = np.empty((0,), dtype=np.int64)
    results_gt['gt_bboxes_ignore'] = np.empty((0, 4), dtype=np.float32)
    gt_masks = np.array([[0, 1, 0, 0], [0, 0, 0, 0]], dtype=np.uint8)[None, :, :]
    results_gt['gt_masks'] = BitmapMasks(gt_masks, 2, 4)
    results_gt['gt_semantic_seg'] = np.array([[1, 6, 255, 255], [5, 255, 255, 255]], dtype=results['gt_semantic_seg'].dtype)
    check_result_same(results_gt, results_sheared)
    results = construct_toy_data(poly2mask=False)
    results_sheared = shear_module(copy.deepcopy(results))
    gt_masks = [[np.array([0, 0, 2, 0, 2, 0, 0, 1], dtype=np.float)]]
    results_gt['gt_masks'] = PolygonMasks(gt_masks, 2, 4)
    check_result_same(results_gt, results_sheared)
    results = construct_toy_data()
    results['gt_masks'] = BitmapMasks(np.array([[0, 1, 1, 0], [0, 1, 1, 0]], dtype=np.uint8)[None, :, :], 2, 4)
    results['gt_bboxes'] = np.array([[1.0, 0.0, 2.0, 1.0]], dtype=np.float32)
    results_sheared_bitmap = shear_module(copy.deepcopy(results))
    check_result_same(results_sheared_bitmap, results_sheared)
    policies = [[dict(type='Shear', level=10, prob=1.0)]]
    autoaug = dict(type='AutoAugment', policies=policies)
    autoaug_module = build_from_cfg(autoaug, PIPELINES)
    autoaug_module(copy.deepcopy(results))
    policies = [[dict(type='Shear', level=10, prob=1.0), dict(type='Shear', level=8, img_fill_val=img_fill_val, direction='vertical', max_shear_magnitude=1.0)]]
    autoaug = dict(type='AutoAugment', policies=policies)
    autoaug_module = build_from_cfg(autoaug, PIPELINES)
    autoaug_module(copy.deepcopy(results))

def test_imequalize(nb_rand_test=100):

    def _imequalize(img):
        from PIL import Image, ImageOps
        img = Image.fromarray(img)
        equalized_img = np.asarray(ImageOps.equalize(img))
        return equalized_img
    results = construct_toy_data()
    transform = dict(type='EqualizeTransform', prob=0)
    transform_module = build_from_cfg(transform, PIPELINES)
    results_transformed = transform_module(copy.deepcopy(results))
    assert_array_equal(results_transformed['img'], results['img'])
    transform = dict(type='EqualizeTransform', prob=1.0)
    transform_module = build_from_cfg(transform, PIPELINES)
    img = np.array([[0, 0, 0], [120, 120, 120], [255, 255, 255]], dtype=np.uint8)
    img = np.stack([img, img, img], axis=-1)
    results['img'] = img
    results_transformed = transform_module(copy.deepcopy(results))
    assert_array_equal(results_transformed['img'], img)
    for _ in range(nb_rand_test):
        img = np.clip(np.random.uniform(0, 1, (1000, 1200, 3)) * 260, 0, 255).astype(np.uint8)
        results['img'] = img
        results_transformed = transform_module(copy.deepcopy(results))
        assert_array_equal(results_transformed['img'], _imequalize(img))

def test_adjust_brightness(nb_rand_test=100):

    def _adjust_brightness(img, factor):
        from PIL import Image
        from PIL.ImageEnhance import Brightness
        img = Image.fromarray(img)
        brightened_img = Brightness(img).enhance(factor)
        return np.asarray(brightened_img)
    results = construct_toy_data()
    transform = dict(type='BrightnessTransform', level=10, prob=0)
    transform_module = build_from_cfg(transform, PIPELINES)
    results_transformed = transform_module(copy.deepcopy(results))
    assert_array_equal(results_transformed['img'], results['img'])
    transform = dict(type='BrightnessTransform', level=10, prob=1.0)
    transform_module = build_from_cfg(transform, PIPELINES)
    transform_module.factor = 1.0
    results_transformed = transform_module(copy.deepcopy(results))
    assert_array_equal(results_transformed['img'], results['img'])
    transform_module.factor = 0.0
    results_transformed = transform_module(copy.deepcopy(results))
    assert_array_equal(results_transformed['img'], np.zeros_like(results['img']))
    for _ in range(nb_rand_test):
        img = np.clip(np.random.uniform(0, 1, (1000, 1200, 3)) * 260, 0, 255).astype(np.uint8)
        factor = np.random.uniform()
        transform_module.factor = factor
        results['img'] = img
        np.testing.assert_allclose(transform_module(copy.deepcopy(results))['img'].astype(np.int32), _adjust_brightness(img, factor).astype(np.int32), rtol=0, atol=1)

def test_adjust_contrast(nb_rand_test=100):

    def _adjust_contrast(img, factor):
        from PIL import Image
        from PIL.ImageEnhance import Contrast
        img = Image.fromarray(img[..., ::-1], mode='RGB')
        contrasted_img = Contrast(img).enhance(factor)
        return np.asarray(contrasted_img)[..., ::-1]
    results = construct_toy_data()
    transform = dict(type='ContrastTransform', level=10, prob=0)
    transform_module = build_from_cfg(transform, PIPELINES)
    results_transformed = transform_module(copy.deepcopy(results))
    assert_array_equal(results_transformed['img'], results['img'])
    transform = dict(type='ContrastTransform', level=10, prob=1.0)
    transform_module = build_from_cfg(transform, PIPELINES)
    transform_module.factor = 1.0
    results_transformed = transform_module(copy.deepcopy(results))
    assert_array_equal(results_transformed['img'], results['img'])
    transform_module.factor = 0.0
    results_transformed = transform_module(copy.deepcopy(results))
    np.testing.assert_allclose(results_transformed['img'], _adjust_contrast(results['img'], 0.0), rtol=0, atol=1)
    for _ in range(nb_rand_test):
        img = np.clip(np.random.uniform(0, 1, (1200, 1000, 3)) * 260, 0, 255).astype(np.uint8)
        factor = np.random.uniform()
        transform_module.factor = factor
        results['img'] = img
        results_transformed = transform_module(copy.deepcopy(results))
        np.testing.assert_allclose(transform_module(copy.deepcopy(results))['img'].astype(np.int32), _adjust_contrast(results['img'], factor).astype(np.int32), rtol=0, atol=1)

def test_resize():
    with pytest.raises(AssertionError):
        transform = dict(type='Resize', img_scale=[1333, 800], keep_ratio=True)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Resize', img_scale=[(1333, 800), (1333, 600)], ratio_range=(0.9, 1.1), keep_ratio=True)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Resize', img_scale=[(1333, 800), (1333, 600)], keep_ratio=True, multiscale_mode='2333')
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        results = dict(img_prefix=osp.join(osp.dirname(__file__), '../../../data'), img_info=dict(filename='color.jpg'))
        load = dict(type='LoadImageFromFile')
        load = build_from_cfg(load, PIPELINES)
        transform = dict(type='Resize', img_scale=(1333, 800), keep_ratio=True)
        transform = build_from_cfg(transform, PIPELINES)
        results = load(results)
        results['scale'] = (1333, 800)
        results['scale_factor'] = 1.0
        results = transform(results)
    transform = dict(type='Resize', img_scale=(1333, 800), keep_ratio=True)
    resize_module = build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    results['img'] = img
    results['img2'] = copy.deepcopy(img)
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['pad_shape'] = img.shape
    results['img_fields'] = ['img', 'img2']
    results = resize_module(results)
    assert np.equal(results['img'], results['img2']).all()
    results.pop('scale')
    results.pop('scale_factor')
    transform = dict(type='Resize', img_scale=(1280, 800), multiscale_mode='value', keep_ratio=False)
    resize_module = build_from_cfg(transform, PIPELINES)
    results = resize_module(results)
    assert np.equal(results['img'], results['img2']).all()
    assert results['img_shape'] == (800, 1280, 3)
    assert results['img'].dtype == results['img'].dtype == np.uint8
    results_seg = {'img': img, 'img_shape': img.shape, 'ori_shape': img.shape, 'gt_semantic_seg': copy.deepcopy(img), 'gt_seg': copy.deepcopy(img), 'seg_fields': ['gt_semantic_seg', 'gt_seg']}
    transform = dict(type='Resize', img_scale=(640, 400), multiscale_mode='value', keep_ratio=False)
    resize_module = build_from_cfg(transform, PIPELINES)
    results_seg = resize_module(results_seg)
    assert results_seg['gt_semantic_seg'].shape == results_seg['gt_seg'].shape
    assert results_seg['img_shape'] == (400, 640, 3)
    assert results_seg['img_shape'] != results_seg['ori_shape']
    assert results_seg['gt_semantic_seg'].shape == results_seg['img_shape']
    assert np.equal(results_seg['gt_semantic_seg'], results_seg['gt_seg']).all()

def test_flip():
    with pytest.raises(AssertionError):
        transform = dict(type='RandomFlip', flip_ratio=1.5)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomFlip', flip_ratio=[0.7, 0.8], direction=['horizontal', 'vertical'])
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomFlip', flip_ratio=[0.4, 0.5])
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomFlip', flip_ratio=1.0, direction='horizonta')
        build_from_cfg(transform, PIPELINES)
    transform = dict(type='RandomFlip', flip_ratio=1.0)
    flip_module = build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    original_img = copy.deepcopy(img)
    results['img'] = img
    results['img2'] = copy.deepcopy(img)
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['pad_shape'] = img.shape
    results['scale_factor'] = 1.0
    results['img_fields'] = ['img', 'img2']
    results = flip_module(results)
    assert np.equal(results['img'], results['img2']).all()
    flip_module = build_from_cfg(transform, PIPELINES)
    results = flip_module(results)
    assert np.equal(results['img'], results['img2']).all()
    assert np.equal(original_img, results['img']).all()
    transform = dict(type='RandomFlip', flip_ratio=0.9, direction=['horizontal', 'vertical', 'diagonal'])
    flip_module = build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    original_img = copy.deepcopy(img)
    results['img'] = img
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['pad_shape'] = img.shape
    results['scale_factor'] = 1.0
    results['img_fields'] = ['img']
    results = flip_module(results)
    if results['flip']:
        assert np.array_equal(mmcv.imflip(original_img, results['flip_direction']), results['img'])
    else:
        assert np.array_equal(original_img, results['img'])
    transform = dict(type='RandomFlip', flip_ratio=[0.3, 0.3, 0.2], direction=['horizontal', 'vertical', 'diagonal'])
    flip_module = build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    original_img = copy.deepcopy(img)
    results['img'] = img
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['pad_shape'] = img.shape
    results['scale_factor'] = 1.0
    results['img_fields'] = ['img']
    results = flip_module(results)
    if results['flip']:
        assert np.array_equal(mmcv.imflip(original_img, results['flip_direction']), results['img'])
    else:
        assert np.array_equal(original_img, results['img'])

def test_random_crop():
    with pytest.raises(AssertionError):
        transform = dict(type='RandomCrop', crop_size=(-1, 0))
        build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    results['img'] = img
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['bbox_fields'] = ['gt_bboxes', 'gt_bboxes_ignore']
    results['pad_shape'] = img.shape
    results['scale_factor'] = 1.0
    h, w, _ = img.shape
    gt_bboxes = create_random_bboxes(8, w, h)
    gt_bboxes_ignore = create_random_bboxes(2, w, h)
    results['gt_labels'] = np.ones(gt_bboxes.shape[0], dtype=np.int64)
    results['gt_bboxes'] = gt_bboxes
    results['gt_bboxes_ignore'] = gt_bboxes_ignore
    transform = dict(type='RandomCrop', crop_size=(h - 20, w - 20))
    crop_module = build_from_cfg(transform, PIPELINES)
    results = crop_module(results)
    assert results['img'].shape[:2] == (h - 20, w - 20)
    assert results['img_shape'][:2] == (h - 20, w - 20)
    assert results['gt_labels'].shape[0] == results['gt_bboxes'].shape[0]
    assert results['gt_labels'].dtype == np.int64
    assert results['gt_bboxes'].dtype == np.float32
    assert results['gt_bboxes'].shape[0] == 8
    assert results['gt_bboxes_ignore'].shape[0] == 2

    def area(bboxes):
        return np.prod(bboxes[:, 2:4] - bboxes[:, 0:2], axis=1)
    assert (area(results['gt_bboxes']) <= area(gt_bboxes)).all()
    assert (area(results['gt_bboxes_ignore']) <= area(gt_bboxes_ignore)).all()
    assert results['gt_bboxes'].dtype == np.float32
    assert results['gt_bboxes_ignore'].dtype == np.float32
    with pytest.raises(ValueError):
        transform = dict(type='RandomCrop', crop_size=(1, 1), crop_type='unknown')
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomCrop', crop_type='relative', crop_size=(0, 0))
        build_from_cfg(transform, PIPELINES)

    def _construct_toy_data():
        img = np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.uint8)
        img = np.stack([img, img, img], axis=-1)
        results = dict()
        results['img'] = img
        results['img_shape'] = img.shape
        results['img_fields'] = ['img']
        results['bbox_fields'] = ['gt_bboxes', 'gt_bboxes_ignore']
        results['gt_bboxes'] = np.array([[0.0, 0.0, 2.0, 1.0]], dtype=np.float32)
        results['gt_bboxes_ignore'] = np.array([[2.0, 0.0, 3.0, 1.0]], dtype=np.float32)
        results['gt_labels'] = np.array([1], dtype=np.int64)
        return results
    results = _construct_toy_data()
    transform = dict(type='RandomCrop', crop_type='relative_range', crop_size=(0.3, 0.7), allow_negative_crop=True)
    transform_module = build_from_cfg(transform, PIPELINES)
    results_transformed = transform_module(copy.deepcopy(results))
    h, w = results_transformed['img_shape'][:2]
    assert int(2 * 0.3 + 0.5) <= h <= int(2 * 1 + 0.5)
    assert int(4 * 0.7 + 0.5) <= w <= int(4 * 1 + 0.5)
    assert results_transformed['gt_bboxes'].dtype == np.float32
    assert results_transformed['gt_bboxes_ignore'].dtype == np.float32
    transform = dict(type='RandomCrop', crop_type='relative', crop_size=(0.3, 0.7), allow_negative_crop=True)
    transform_module = build_from_cfg(transform, PIPELINES)
    results_transformed = transform_module(copy.deepcopy(results))
    h, w = results_transformed['img_shape'][:2]
    assert h == int(2 * 0.3 + 0.5) and w == int(4 * 0.7 + 0.5)
    assert results_transformed['gt_bboxes'].dtype == np.float32
    assert results_transformed['gt_bboxes_ignore'].dtype == np.float32
    transform = dict(type='RandomCrop', crop_type='absolute', crop_size=(1, 2), allow_negative_crop=True)
    transform_module = build_from_cfg(transform, PIPELINES)
    results_transformed = transform_module(copy.deepcopy(results))
    h, w = results_transformed['img_shape'][:2]
    assert h == 1 and w == 2
    assert results_transformed['gt_bboxes'].dtype == np.float32
    assert results_transformed['gt_bboxes_ignore'].dtype == np.float32
    transform = dict(type='RandomCrop', crop_type='absolute_range', crop_size=(1, 20), allow_negative_crop=True)
    transform_module = build_from_cfg(transform, PIPELINES)
    results_transformed = transform_module(copy.deepcopy(results))
    h, w = results_transformed['img_shape'][:2]
    assert 1 <= h <= 2 and 1 <= w <= 4
    assert results_transformed['gt_bboxes'].dtype == np.float32
    assert results_transformed['gt_bboxes_ignore'].dtype == np.float32

def test_min_iou_random_crop():
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    results['img'] = img
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['bbox_fields'] = ['gt_bboxes', 'gt_bboxes_ignore']
    results['pad_shape'] = img.shape
    results['scale_factor'] = 1.0
    h, w, _ = img.shape
    gt_bboxes = create_random_bboxes(1, w, h)
    gt_bboxes_ignore = create_random_bboxes(1, w, h)
    results['gt_labels'] = np.ones(gt_bboxes.shape[0], dtype=np.int64)
    results['gt_bboxes'] = gt_bboxes
    results['gt_bboxes_ignore'] = gt_bboxes_ignore
    transform = dict(type='MinIoURandomCrop')
    crop_module = build_from_cfg(transform, PIPELINES)
    results_test = copy.deepcopy(results)
    results_test['img1'] = results_test['img']
    results_test['img_fields'] = ['img', 'img1']
    with pytest.raises(AssertionError):
        crop_module(results_test)
    results = crop_module(results)
    assert results['gt_labels'].shape[0] == results['gt_bboxes'].shape[0]
    assert results['gt_labels'].dtype == np.int64
    assert results['gt_bboxes'].dtype == np.float32
    assert results['gt_bboxes_ignore'].dtype == np.float32
    patch = np.array([0, 0, results['img_shape'][1], results['img_shape'][0]])
    ious = bbox_overlaps(patch.reshape(-1, 4), results['gt_bboxes']).reshape(-1)
    ious_ignore = bbox_overlaps(patch.reshape(-1, 4), results['gt_bboxes_ignore']).reshape(-1)
    mode = crop_module.mode
    if mode == 1:
        assert np.equal(results['gt_bboxes'], gt_bboxes).all()
        assert np.equal(results['gt_bboxes_ignore'], gt_bboxes_ignore).all()
    else:
        assert (ious >= mode).all()
        assert (ious_ignore >= mode).all()

def test_pad():
    with pytest.raises(AssertionError):
        transform = dict(type='Pad')
        build_from_cfg(transform, PIPELINES)
    transform = dict(type='Pad', size_divisor=32)
    transform = build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    original_img = copy.deepcopy(img)
    results['img'] = img
    results['img2'] = copy.deepcopy(img)
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['pad_shape'] = img.shape
    results['scale_factor'] = 1.0
    results['img_fields'] = ['img', 'img2']
    results = transform(results)
    assert np.equal(results['img'], results['img2']).all()
    assert np.equal(results['img'], original_img).all()
    img_shape = results['img'].shape
    assert img_shape[0] % 32 == 0
    assert img_shape[1] % 32 == 0
    resize_transform = dict(type='Resize', img_scale=(1333, 800), keep_ratio=True)
    resize_module = build_from_cfg(resize_transform, PIPELINES)
    results = resize_module(results)
    results = transform(results)
    img_shape = results['img'].shape
    assert np.equal(results['img'], results['img2']).all()
    assert img_shape[0] % 32 == 0
    assert img_shape[1] % 32 == 0
    with pytest.raises(AssertionError):
        transform = dict(type='Pad', size_divisor=32, pad_to_square=True)
        build_from_cfg(transform, PIPELINES)
    transform = dict(type='Pad', pad_to_square=True)
    transform = build_from_cfg(transform, PIPELINES)
    results['img'] = img
    results = transform(results)
    assert results['img'].shape[0] == results['img'].shape[1]
    transform = dict(type='Pad', size_divisor=32, pad_val=0)
    with pytest.deprecated_call():
        transform = build_from_cfg(transform, PIPELINES)
    assert isinstance(transform.pad_val, dict)
    results = transform(results)
    img_shape = results['img'].shape
    assert img_shape[0] % 32 == 0
    assert img_shape[1] % 32 == 0

def test_normalize():
    img_norm_cfg = dict(mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)
    transform = dict(type='Normalize', **img_norm_cfg)
    transform = build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    original_img = copy.deepcopy(img)
    results['img'] = img
    results['img2'] = copy.deepcopy(img)
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['pad_shape'] = img.shape
    results['scale_factor'] = 1.0
    results['img_fields'] = ['img', 'img2']
    results = transform(results)
    assert np.equal(results['img'], results['img2']).all()
    mean = np.array(img_norm_cfg['mean'])
    std = np.array(img_norm_cfg['std'])
    converted_img = (original_img[..., ::-1] - mean) / std
    assert np.allclose(results['img'], converted_img)

def test_albu_transform():
    results = dict(img_prefix=osp.join(osp.dirname(__file__), '../../../data'), img_info=dict(filename='color.jpg'))
    load = dict(type='LoadImageFromFile')
    load = build_from_cfg(load, PIPELINES)
    albu_transform = dict(type='Albu', transforms=[dict(type='ChannelShuffle', p=1)])
    albu_transform = build_from_cfg(albu_transform, PIPELINES)
    normalize = dict(type='Normalize', mean=[0] * 3, std=[0] * 3, to_rgb=True)
    normalize = build_from_cfg(normalize, PIPELINES)
    results = load(results)
    results = albu_transform(results)
    results = normalize(results)
    assert results['img'].dtype == np.float32

def test_random_center_crop_pad():
    with pytest.raises(AssertionError):
        transform = dict(type='RandomCenterCropPad', crop_size=(-1, 0), test_mode=False, test_pad_mode=None)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomCenterCropPad', crop_size=(511, 511), ratios=1.0, test_mode=False, test_pad_mode=None)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomCenterCropPad', crop_size=(511, 511), mean=None, std=None, to_rgb=None, test_mode=False, test_pad_mode=None)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomCenterCropPad', crop_size=(511, 511), ratios=None, border=None, mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True, test_mode=True, test_pad_mode=('logical_or', 127))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomCenterCropPad', crop_size=None, ratios=(0.9, 1.0, 1.1), border=None, mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True, test_mode=True, test_pad_mode=('logical_or', 127))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomCenterCropPad', crop_size=None, ratios=None, border=128, mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True, test_mode=True, test_pad_mode=('logical_or', 127))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomCenterCropPad', crop_size=None, ratios=None, border=None, mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True, test_mode=True, test_pad_mode=('do_nothing', 100))
        build_from_cfg(transform, PIPELINES)
    results = dict(img_prefix=osp.join(osp.dirname(__file__), '../../../data'), img_info=dict(filename='color.jpg'))
    load = dict(type='LoadImageFromFile', to_float32=True)
    load = build_from_cfg(load, PIPELINES)
    results = load(results)
    test_results = copy.deepcopy(results)
    h, w, _ = results['img_shape']
    gt_bboxes = create_random_bboxes(8, w, h)
    gt_bboxes_ignore = create_random_bboxes(2, w, h)
    results['gt_bboxes'] = gt_bboxes
    results['gt_bboxes_ignore'] = gt_bboxes_ignore
    train_transform = dict(type='RandomCenterCropPad', crop_size=(h - 20, w - 20), ratios=(1.0,), border=128, mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True, test_mode=False, test_pad_mode=None)
    crop_module = build_from_cfg(train_transform, PIPELINES)
    train_results = crop_module(results)
    assert train_results['img'].shape[:2] == (h - 20, w - 20)
    assert train_results['pad_shape'][:2] == (h - 20, w - 20)
    assert train_results['gt_bboxes'].shape[0] == 8
    assert train_results['gt_bboxes_ignore'].shape[0] == 2
    assert train_results['gt_bboxes'].dtype == np.float32
    assert train_results['gt_bboxes_ignore'].dtype == np.float32
    test_transform = dict(type='RandomCenterCropPad', crop_size=None, ratios=None, border=None, mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True, test_mode=True, test_pad_mode=('logical_or', 127))
    crop_module = build_from_cfg(test_transform, PIPELINES)
    test_results = crop_module(test_results)
    assert test_results['img'].shape[:2] == (h | 127, w | 127)
    assert test_results['pad_shape'][:2] == (h | 127, w | 127)
    assert 'border' in test_results

def test_multi_scale_flip_aug():
    with pytest.raises(AssertionError):
        transform = dict(type='MultiScaleFlipAug', scale_factor=1.0, img_scale=[(1333, 800)], transforms=[dict(type='Resize')])
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='MultiScaleFlipAug', scale_factor=None, img_scale=None, transforms=[dict(type='Resize')])
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='MultiScaleFlipAug', img_scale=[1333, 800], transforms=[dict(type='Resize')])
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='MultiScaleFlipAug', img_scale=[(1333, 800)], flip_direction=1, transforms=[dict(type='Resize')])
        build_from_cfg(transform, PIPELINES)
    scale_transform = dict(type='MultiScaleFlipAug', img_scale=[(1333, 800), (1333, 640)], transforms=[dict(type='Resize', keep_ratio=True)])
    transform = build_from_cfg(scale_transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    results['img'] = img
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['pad_shape'] = img.shape
    results['img_fields'] = ['img']
    scale_results = transform(copy.deepcopy(results))
    assert len(scale_results['img']) == 2
    assert scale_results['img'][0].shape == (750, 1333, 3)
    assert scale_results['img_shape'][0] == (750, 1333, 3)
    assert scale_results['img'][1].shape == (640, 1138, 3)
    assert scale_results['img_shape'][1] == (640, 1138, 3)
    scale_factor_transform = dict(type='MultiScaleFlipAug', scale_factor=[0.8, 1.0, 1.2], transforms=[dict(type='Resize', keep_ratio=False)])
    transform = build_from_cfg(scale_factor_transform, PIPELINES)
    scale_factor_results = transform(copy.deepcopy(results))
    assert len(scale_factor_results['img']) == 3
    assert scale_factor_results['img'][0].shape == (230, 409, 3)
    assert scale_factor_results['img_shape'][0] == (230, 409, 3)
    assert scale_factor_results['img'][1].shape == (288, 512, 3)
    assert scale_factor_results['img_shape'][1] == (288, 512, 3)
    assert scale_factor_results['img'][2].shape == (345, 614, 3)
    assert scale_factor_results['img_shape'][2] == (345, 614, 3)
    results = dict(img_prefix=osp.join(osp.dirname(__file__), '../../../data'), img_info=dict(filename='color.jpg'))
    load_cfg, multi_scale_cfg = mmcv.Config.fromfile('configs/_base_/datasets/coco_detection.py').test_pipeline
    load = build_from_cfg(load_cfg, PIPELINES)
    transform = build_from_cfg(multi_scale_cfg, PIPELINES)
    results = transform(load(results))
    assert len(results['img']) == 1
    assert len(results['img_metas']) == 1
    assert isinstance(results['img'][0], torch.Tensor)
    assert isinstance(results['img_metas'][0], mmcv.parallel.DataContainer)
    assert results['img_metas'][0].data['ori_shape'] == (288, 512, 3)
    assert results['img_metas'][0].data['img_shape'] == (750, 1333, 3)
    assert results['img_metas'][0].data['pad_shape'] == (768, 1344, 3)
    assert results['img_metas'][0].data['scale_factor'].tolist() == [2.603515625, 2.6041667461395264, 2.603515625, 2.6041667461395264]

def test_cutout():
    with pytest.raises(AssertionError):
        transform = dict(type='CutOut', n_holes=(5, 3), cutout_shape=(8, 8))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='CutOut', n_holes=(3, 4, 5), cutout_shape=(8, 8))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='CutOut', n_holes=1, cutout_shape=8)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='CutOut', n_holes=1, cutout_ratio=0.2)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='CutOut', n_holes=1)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='CutOut', n_holes=1, cutout_shape=(2, 2), cutout_ratio=(0.4, 0.4))
        build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    results['img'] = img
    results['img_shape'] = img.shape
    results['ori_shape'] = img.shape
    results['pad_shape'] = img.shape
    results['img_fields'] = ['img']
    transform = dict(type='CutOut', n_holes=1, cutout_shape=(10, 10))
    cutout_module = build_from_cfg(transform, PIPELINES)
    cutout_result = cutout_module(copy.deepcopy(results))
    assert cutout_result['img'].sum() < img.sum()
    transform = dict(type='CutOut', n_holes=1, cutout_ratio=(0.8, 0.8))
    cutout_module = build_from_cfg(transform, PIPELINES)
    cutout_result = cutout_module(copy.deepcopy(results))
    assert cutout_result['img'].sum() < img.sum()
    transform = dict(type='CutOut', n_holes=(2, 4), cutout_shape=[(10, 10), (15, 15)], fill_in=(255, 255, 255))
    cutout_module = build_from_cfg(transform, PIPELINES)
    cutout_result = cutout_module(copy.deepcopy(results))
    assert cutout_result['img'].sum() > img.sum()
    transform = dict(type='CutOut', n_holes=1, cutout_ratio=(0.8, 0.8), fill_in=(255, 255, 255))
    cutout_module = build_from_cfg(transform, PIPELINES)
    cutout_result = cutout_module(copy.deepcopy(results))
    assert cutout_result['img'].sum() > img.sum()

def test_random_shift():
    with pytest.raises(AssertionError):
        transform = dict(type='RandomShift', shift_ratio=1.5)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomShift', max_shift_px=-1)
        build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    results['img'] = img
    results['bbox_fields'] = ['gt_bboxes', 'gt_bboxes_ignore']
    h, w, _ = img.shape
    gt_bboxes = create_random_bboxes(8, w, h)
    gt_bboxes_ignore = create_random_bboxes(2, w, h)
    results['gt_labels'] = np.ones(gt_bboxes.shape[0], dtype=np.int64)
    results['gt_bboxes'] = gt_bboxes
    results['gt_bboxes_ignore'] = gt_bboxes_ignore
    transform = dict(type='RandomShift', shift_ratio=1.0)
    random_shift_module = build_from_cfg(transform, PIPELINES)
    results = random_shift_module(results)
    assert results['img'].shape[:2] == (h, w)
    assert results['gt_labels'].shape[0] == results['gt_bboxes'].shape[0]
    assert results['gt_labels'].dtype == np.int64
    assert results['gt_bboxes'].dtype == np.float32
    assert results['gt_bboxes_ignore'].dtype == np.float32

def test_random_affine():
    with pytest.raises(AssertionError):
        transform = dict(type='RandomAffine', max_translate_ratio=1.5)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomAffine', scaling_ratio_range=(1.5, 0.5))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='RandomAffine', scaling_ratio_range=(0, 0.5))
        build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    results['img'] = img
    results['bbox_fields'] = ['gt_bboxes', 'gt_bboxes_ignore']
    h, w, _ = img.shape
    gt_bboxes = create_random_bboxes(8, w, h)
    gt_bboxes_ignore = create_random_bboxes(2, w, h)
    results['gt_labels'] = np.ones(gt_bboxes.shape[0], dtype=np.int64)
    results['gt_bboxes'] = gt_bboxes
    results['gt_bboxes_ignore'] = gt_bboxes_ignore
    transform = dict(type='RandomAffine')
    random_affine_module = build_from_cfg(transform, PIPELINES)
    results = random_affine_module(results)
    assert results['img'].shape[:2] == (h, w)
    assert results['gt_labels'].shape[0] == results['gt_bboxes'].shape[0]
    assert results['gt_labels'].dtype == np.int64
    assert results['gt_bboxes'].dtype == np.float32
    assert results['gt_bboxes_ignore'].dtype == np.float32
    gt_bboxes = np.array([[0, 0, 1, 1], [0, 0, 3, 100]], dtype=np.float32)
    results['gt_labels'] = np.ones(gt_bboxes.shape[0], dtype=np.int64)
    results['gt_bboxes'] = gt_bboxes
    transform = dict(type='RandomAffine', max_rotate_degree=0.0, max_translate_ratio=0.0, scaling_ratio_range=(1.0, 1.0), max_shear_degree=0.0, border=(0, 0), min_bbox_size=2, max_aspect_ratio=20, skip_filter=False)
    random_affine_module = build_from_cfg(transform, PIPELINES)
    results = random_affine_module(results)
    assert results['gt_bboxes'].shape[0] == 0
    assert results['gt_labels'].shape[0] == 0
    assert results['gt_labels'].shape[0] == results['gt_bboxes'].shape[0]
    assert results['gt_labels'].dtype == np.int64
    assert results['gt_bboxes'].dtype == np.float32
    assert results['gt_bboxes_ignore'].dtype == np.float32

def test_mosaic():
    with pytest.raises(AssertionError):
        transform = dict(type='Mosaic', img_scale=640)
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Mosaic', prob=1.5)
        build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    results['img'] = img
    results['bbox_fields'] = ['gt_bboxes', 'gt_bboxes_ignore']
    h, w, _ = img.shape
    gt_bboxes = create_random_bboxes(8, w, h)
    gt_bboxes_ignore = create_random_bboxes(2, w, h)
    results['gt_labels'] = np.ones(gt_bboxes.shape[0], dtype=np.int64)
    results['gt_bboxes'] = gt_bboxes
    results['gt_bboxes_ignore'] = gt_bboxes_ignore
    transform = dict(type='Mosaic', img_scale=(10, 12))
    mosaic_module = build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        mosaic_module(results)
    results['mix_results'] = [copy.deepcopy(results)] * 3
    results = mosaic_module(results)
    assert results['img'].shape[:2] == (20, 24)
    assert results['gt_labels'].shape[0] == results['gt_bboxes'].shape[0]
    assert results['gt_labels'].dtype == np.int64
    assert results['gt_bboxes'].dtype == np.float32
    assert results['gt_bboxes_ignore'].dtype == np.float32

def test_mixup():
    with pytest.raises(AssertionError):
        transform = dict(type='MixUp', img_scale=640)
        build_from_cfg(transform, PIPELINES)
    results = dict()
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    results['img'] = img
    results['bbox_fields'] = ['gt_bboxes', 'gt_bboxes_ignore']
    h, w, _ = img.shape
    gt_bboxes = create_random_bboxes(8, w, h)
    gt_bboxes_ignore = create_random_bboxes(2, w, h)
    results['gt_labels'] = np.ones(gt_bboxes.shape[0], dtype=np.int64)
    results['gt_bboxes'] = gt_bboxes
    results['gt_bboxes_ignore'] = gt_bboxes_ignore
    transform = dict(type='MixUp', img_scale=(10, 12))
    mixup_module = build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        mixup_module(results)
    with pytest.raises(AssertionError):
        results['mix_results'] = [copy.deepcopy(results)] * 2
        mixup_module(results)
    results['mix_results'] = [copy.deepcopy(results)]
    results = mixup_module(results)
    assert results['img'].shape[:2] == (288, 512)
    assert results['gt_labels'].shape[0] == results['gt_bboxes'].shape[0]
    assert results['gt_labels'].dtype == np.int64
    assert results['gt_bboxes'].dtype == np.float32
    assert results['gt_bboxes_ignore'].dtype == np.float32
    gt_bboxes = np.array([[0, 0, 1, 1], [0, 0, 3, 3]], dtype=np.float32)
    results['gt_labels'] = np.ones(gt_bboxes.shape[0], dtype=np.int64)
    results['gt_bboxes'] = gt_bboxes
    results['gt_bboxes_ignore'] = np.array([], dtype=np.float32)
    mixresults = results['mix_results'][0]
    mixresults['gt_labels'] = copy.deepcopy(results['gt_labels'])
    mixresults['gt_bboxes'] = copy.deepcopy(results['gt_bboxes'])
    mixresults['gt_bboxes_ignore'] = copy.deepcopy(results['gt_bboxes_ignore'])
    transform = dict(type='MixUp', img_scale=(10, 12), ratio_range=(1.5, 1.5), min_bbox_size=5, skip_filter=False)
    mixup_module = build_from_cfg(transform, PIPELINES)
    results = mixup_module(results)
    assert results['gt_bboxes'].shape[0] == 2
    assert results['gt_labels'].shape[0] == 2
    assert results['gt_labels'].shape[0] == results['gt_bboxes'].shape[0]
    assert results['gt_labels'].dtype == np.int64
    assert results['gt_bboxes'].dtype == np.float32
    assert results['gt_bboxes_ignore'].dtype == np.float32

def test_photo_metric_distortion():
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    transform = dict(type='PhotoMetricDistortion')
    distortion_module = build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        results = dict()
        results['img'] = img
        results['img2'] = img
        results['img_fields'] = ['img', 'img2']
        distortion_module(results)
    results = dict()
    results['img'] = img
    results = distortion_module(results)
    assert results['img'].dtype == np.float32
    results = dict()
    results['img'] = img.astype(np.float32)
    results = distortion_module(results)
    assert results['img'].dtype == np.float32

def test_copypaste():
    dst_results, src_results = (dict(), dict())
    img = mmcv.imread(osp.join(osp.dirname(__file__), '../../../data/color.jpg'), 'color')
    dst_results['img'] = img.copy()
    src_results['img'] = img.copy()
    h, w, _ = img.shape
    dst_bboxes = np.array([[0.2 * w, 0.2 * h, 0.4 * w, 0.4 * h], [0.5 * w, 0.5 * h, 0.6 * w, 0.6 * h]], dtype=np.float32)
    src_bboxes = np.array([[0.1 * w, 0.1 * h, 0.3 * w, 0.5 * h], [0.4 * w, 0.4 * h, 0.7 * w, 0.7 * h], [0.8 * w, 0.8 * h, 0.9 * w, 0.9 * h]], dtype=np.float32)
    dst_labels = np.ones(dst_bboxes.shape[0], dtype=np.int64)
    src_labels = np.ones(src_bboxes.shape[0], dtype=np.int64) * 2
    dst_masks = create_full_masks(dst_bboxes, w, h)
    src_masks = create_full_masks(src_bboxes, w, h)
    dst_results['gt_bboxes'] = dst_bboxes.copy()
    src_results['gt_bboxes'] = src_bboxes.copy()
    dst_results['gt_labels'] = dst_labels.copy()
    src_results['gt_labels'] = src_labels.copy()
    dst_results['gt_masks'] = copy.deepcopy(dst_masks)
    src_results['gt_masks'] = copy.deepcopy(src_masks)
    results = copy.deepcopy(dst_results)
    transform = dict(type='CopyPaste', selected=False)
    copypaste_module = build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        copypaste_module(results)
    results['mix_results'] = [copy.deepcopy(src_results)]
    results = copypaste_module(results)
    assert results['img'].shape[:2] == (h, w)
    assert results['gt_bboxes'].shape[0] == dst_bboxes.shape[0] + src_bboxes.shape[0] - 1
    assert results['gt_labels'].shape[0] == dst_labels.shape[0] + src_labels.shape[0] - 1
    assert results['gt_masks'].masks.shape[0] == dst_masks.masks.shape[0] + src_masks.masks.shape[0] - 1
    assert results['gt_labels'].dtype == np.int64
    assert results['gt_bboxes'].dtype == np.float32
    ori_bbox = dst_bboxes[0]
    occ_bbox = results['gt_bboxes'][0]
    ori_mask = dst_masks.masks[0]
    occ_mask = results['gt_masks'].masks[0]
    assert ori_mask.sum() > occ_mask.sum()
    assert np.all(np.abs(occ_bbox - ori_bbox) <= copypaste_module.bbox_occluded_thr) or occ_mask.sum() > copypaste_module.mask_occluded_thr
    transform = dict(type='CopyPaste')
    copypaste_module = build_from_cfg(transform, PIPELINES)
    results = copy.deepcopy(dst_results)
    results['mix_results'] = [copy.deepcopy(src_results)]
    copypaste_module(results)
    results = copy.deepcopy(dst_results)
    valid_inds = [False] * src_bboxes.shape[0]
    src_results['gt_bboxes'] = src_bboxes[valid_inds]
    src_results['gt_labels'] = src_labels[valid_inds]
    src_results['gt_masks'] = src_masks[valid_inds]
    results['mix_results'] = [copy.deepcopy(src_results)]
    copypaste_module(results)
    dst_results.pop('gt_masks')
    src_results.pop('gt_masks')
    dst_bboxes = dst_results['gt_bboxes']
    src_bboxes = src_results['gt_bboxes']
    dst_masks = create_full_masks(dst_bboxes, w, h)
    src_masks = create_full_masks(src_bboxes, w, h)
    results = copy.deepcopy(dst_results)
    results['mix_results'] = [copy.deepcopy(src_results)]
    results = copypaste_module(results)
    result_masks = create_full_masks(results['gt_bboxes'], w, h)
    result_masks_np = np.where(result_masks.to_ndarray().sum(0) > 0, 1, 0)
    masks_np = np.where(src_masks.to_ndarray().sum(0) + dst_masks.to_ndarray().sum(0) > 0, 1, 0)
    assert np.all(result_masks_np == masks_np)
    assert 'gt_masks' not in results

def test_rotate():
    with pytest.raises(AssertionError):
        transform = dict(type='Rotate', level=1, max_rotate_angle=(30,))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Rotate', level=2, scale=(1.2,))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(ValueError):
        transform = dict(type='Rotate', level=2, img_fill_val=[128])
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Rotate', level=2, center=(0.5,))
        build_from_cfg(transform, PIPELINES)
    with pytest.raises(AssertionError):
        transform = dict(type='Rotate', level=2, center=[0, 0])
        build_from_cfg(transform, PIPELINES)
    results = construct_toy_data()
    img_fill_val = (104, 116, 124)
    seg_ignore_label = 255
    transform = dict(type='Rotate', level=0, prob=1.0, img_fill_val=img_fill_val, seg_ignore_label=seg_ignore_label)
    rotate_module = build_from_cfg(transform, PIPELINES)
    results_wo_rotate = rotate_module(copy.deepcopy(results))
    check_result_same(results, results_wo_rotate)
    transform = dict(type='Rotate', level=10, prob=0.0, img_fill_val=img_fill_val, scale=0.6)
    rotate_module = build_from_cfg(transform, PIPELINES)
    results_wo_rotate = rotate_module(copy.deepcopy(results))
    check_result_same(results, results_wo_rotate)
    results = construct_toy_data()
    img_fill_val = 128
    transform = dict(type='Rotate', level=10, max_rotate_angle=90, img_fill_val=img_fill_val, random_negative_prob=0.0, prob=1.0)
    rotate_module = build_from_cfg(transform, PIPELINES)
    results_rotated = rotate_module(copy.deepcopy(results))
    img_r = np.array([[img_fill_val, 6, 2, img_fill_val], [img_fill_val, 7, 3, img_fill_val]]).astype(np.uint8)
    img_r = np.stack([img_r, img_r, img_r], axis=-1)
    results_gt = copy.deepcopy(results)
    results_gt['img'] = img_r
    results_gt['gt_bboxes'] = np.array([[1.0, 0.0, 2.0, 1.0]], dtype=np.float32)
    results_gt['gt_bboxes_ignore'] = np.empty((0, 4), dtype=np.float32)
    gt_masks = np.array([[0, 1, 1, 0], [0, 0, 1, 0]], dtype=np.uint8)[None, :, :]
    results_gt['gt_masks'] = BitmapMasks(gt_masks, 2, 4)
    results_gt['gt_semantic_seg'] = np.array([[255, 6, 2, 255], [255, 7, 3, 255]]).astype(results['gt_semantic_seg'].dtype)
    check_result_same(results_gt, results_rotated)
    results = construct_toy_data(poly2mask=False)
    results_rotated = rotate_module(copy.deepcopy(results))
    gt_masks = [[np.array([2, 0, 2, 1, 1, 1, 1, 0], dtype=np.float)]]
    results_gt['gt_masks'] = PolygonMasks(gt_masks, 2, 4)
    check_result_same(results_gt, results_rotated)
    img_fill_val = (104, 116, 124)
    transform = dict(type='Rotate', level=10, max_rotate_angle=90, center=(0, 0), img_fill_val=img_fill_val, random_negative_prob=1.0, prob=1.0)
    results = construct_toy_data()
    rotate_module = build_from_cfg(transform, PIPELINES)
    results_rotated = rotate_module(copy.deepcopy(results))
    results_gt = copy.deepcopy(results)
    h, w = results['img'].shape[:2]
    img_r = np.stack([np.ones((h, w)) * img_fill_val[0], np.ones((h, w)) * img_fill_val[1], np.ones((h, w)) * img_fill_val[2]], axis=-1).astype(np.uint8)
    img_r[0, 0, :] = 1
    img_r[0, 1, :] = 5
    results_gt['img'] = img_r
    results_gt['gt_bboxes'] = np.empty((0, 4), dtype=np.float32)
    results_gt['gt_bboxes_ignore'] = np.empty((0, 4), dtype=np.float32)
    results_gt['gt_labels'] = np.empty((0,), dtype=np.int64)
    gt_masks = np.empty((0, h, w), dtype=np.uint8)
    results_gt['gt_masks'] = BitmapMasks(gt_masks, h, w)
    gt_seg = (np.ones((h, w)) * 255).astype(results['gt_semantic_seg'].dtype)
    gt_seg[0, 0], gt_seg[0, 1] = (1, 5)
    results_gt['gt_semantic_seg'] = gt_seg
    check_result_same(results_gt, results_rotated)
    transform = dict(type='Rotate', level=10, max_rotate_angle=90, center=0, img_fill_val=img_fill_val, random_negative_prob=1.0, prob=1.0)
    rotate_module = build_from_cfg(transform, PIPELINES)
    results_rotated = rotate_module(copy.deepcopy(results))
    check_result_same(results_gt, results_rotated)
    results = construct_toy_data(poly2mask=False)
    results_rotated = rotate_module(copy.deepcopy(results))
    gt_masks = [[np.array([0, 0, 0, 0, 1, 0, 1, 0], dtype=np.float)]]
    results_gt['gt_masks'] = PolygonMasks(gt_masks, 2, 4)
    check_result_same(results_gt, results_rotated)
    policies = [[dict(type='Rotate', level=10, prob=1.0)]]
    autoaug = dict(type='AutoAugment', policies=policies)
    autoaug_module = build_from_cfg(autoaug, PIPELINES)
    autoaug_module(copy.deepcopy(results))
    policies = [[dict(type='Rotate', level=10, prob=1.0), dict(type='Rotate', level=8, max_rotate_angle=90, center=0, img_fill_val=img_fill_val)]]
    autoaug = dict(type='AutoAugment', policies=policies)
    autoaug_module = build_from_cfg(autoaug, PIPELINES)
    autoaug_module(copy.deepcopy(results))

def check_suffix(file='yolov5s.pt', suffix=('.pt',), msg=''):
    if file and suffix:
        if isinstance(suffix, str):
            suffix = [suffix]
        for f in file if isinstance(file, (list, tuple)) else [file]:
            s = Path(f).suffix.lower()
            if len(s):
                assert s in suffix, f'{msg}{f} acceptable suffix is {suffix}'

class Tracker:
    """
    This is the multi-target tracker.
    Parameters
    ----------
    metric : nn_matching.NearestNeighborDistanceMetric
        A distance metric for measurement-to-track association.
    max_age : int
        Maximum number of missed misses before a track is deleted.
    n_init : int
        Number of consecutive detections before the track is confirmed. The
        track state is set to `Deleted` if a miss occurs within the first
        `n_init` frames.
    Attributes
    ----------
    metric : nn_matching.NearestNeighborDistanceMetric
        The distance metric used for measurement to track association.
    max_age : int
        Maximum number of missed misses before a track is deleted.
    n_init : int
        Number of frames that a track remains in initialization phase.
    kf : kalman_filter.KalmanFilter
        A Kalman filter to filter target trajectories in image space.
    tracks : List[Track]
        The list of active tracks at the current time step.
    """
    GATING_THRESHOLD = np.sqrt(kalman_filter.chi2inv95[4])

    def __init__(self, metric, max_iou_dist=0.9, max_age=30, max_unmatched_preds=7, n_init=3, _lambda=0, ema_alpha=0.9, mc_lambda=0.995):
        self.metric = metric
        self.max_iou_dist = max_iou_dist
        self.max_age = max_age
        self.n_init = n_init
        self._lambda = _lambda
        self.ema_alpha = ema_alpha
        self.mc_lambda = mc_lambda
        self.max_unmatched_preds = max_unmatched_preds
        self.kf = kalman_filter.KalmanFilter()
        self.tracks = []
        self._next_id = 1

    def predict(self):
        """Propagate track state distributions one time step forward.

        This function should be called once every time step, before `update`.
        """
        for track in self.tracks:
            track.predict(self.kf)

    def increment_ages(self):
        for track in self.tracks:
            track.increment_age()
            track.mark_missed()

    def camera_update(self, previous_img, current_img):
        for track in self.tracks:
            track.camera_update(previous_img, current_img)

    def pred_n_update_all_tracks(self):
        """Perform predictions and updates for all tracks by its own predicted state.

        """
        self.predict()
        for t in self.tracks:
            if self.max_unmatched_preds != 0 and t.updates_wo_assignment < t.max_num_updates_wo_assignment:
                bbox = t.to_tlwh()
                t.update_kf(detection.to_xyah_ext(bbox))

    def update(self, detections, classes, confidences):
        """Perform measurement update and track management.

        Parameters
        ----------
        detections : List[deep_sort.detection.Detection]
            A list of detections at the current time step.

        """
        matches, unmatched_tracks, unmatched_detections = self._match(detections)
        for track_idx, detection_idx in matches:
            self.tracks[track_idx].update(detections[detection_idx], classes[detection_idx], confidences[detection_idx])
        for track_idx in unmatched_tracks:
            self.tracks[track_idx].mark_missed()
            if self.max_unmatched_preds != 0 and self.tracks[track_idx].updates_wo_assignment < self.tracks[track_idx].max_num_updates_wo_assignment:
                bbox = self.tracks[track_idx].to_tlwh()
                self.tracks[track_idx].update_kf(detection.to_xyah_ext(bbox))
        for detection_idx in unmatched_detections:
            self._initiate_track(detections[detection_idx], classes[detection_idx].item(), confidences[detection_idx].item())
        self.tracks = [t for t in self.tracks if not t.is_deleted()]
        active_targets = [t.track_id for t in self.tracks if t.is_confirmed()]
        features, targets = ([], [])
        for track in self.tracks:
            if not track.is_confirmed():
                continue
            features += track.features
            targets += [track.track_id for _ in track.features]
        self.metric.partial_fit(np.asarray(features), np.asarray(targets), active_targets)

    def _full_cost_metric(self, tracks, dets, track_indices, detection_indices):
        """
        This implements the full lambda-based cost-metric. However, in doing so, it disregards
        the possibility to gate the position only which is provided by
        linear_assignment.gate_cost_matrix(). Instead, I gate by everything.
        Note that the Mahalanobis distance is itself an unnormalised metric. Given the cosine
        distance being normalised, we employ a quick and dirty normalisation based on the
        threshold: that is, we divide the positional-cost by the gating threshold, thus ensuring
        that the valid values range 0-1.
        Note also that the authors work with the squared distance. I also sqrt this, so that it
        is more intuitive in terms of values.
        """
        pos_cost = np.empty([len(track_indices), len(detection_indices)])
        msrs = np.asarray([dets[i].to_xyah() for i in detection_indices])
        for row, track_idx in enumerate(track_indices):
            pos_cost[row, :] = np.sqrt(self.kf.gating_distance(tracks[track_idx].mean, tracks[track_idx].covariance, msrs, False)) / self.GATING_THRESHOLD
        pos_gate = pos_cost > 1.0
        app_cost = self.metric.distance(np.array([dets[i].feature for i in detection_indices]), np.array([tracks[i].track_id for i in track_indices]))
        app_gate = app_cost > self.metric.matching_threshold
        cost_matrix = self._lambda * pos_cost + (1 - self._lambda) * app_cost
        cost_matrix[np.logical_or(pos_gate, app_gate)] = linear_assignment.INFTY_COST
        return cost_matrix

    def _match(self, detections):

        def gated_metric(tracks, dets, track_indices, detection_indices):
            features = np.array([dets[i].feature for i in detection_indices])
            targets = np.array([tracks[i].track_id for i in track_indices])
            cost_matrix = self.metric.distance(features, targets)
            cost_matrix = linear_assignment.gate_cost_matrix(cost_matrix, tracks, dets, track_indices, detection_indices, self.mc_lambda)
            return cost_matrix
        confirmed_tracks = [i for i, t in enumerate(self.tracks) if t.is_confirmed()]
        unconfirmed_tracks = [i for i, t in enumerate(self.tracks) if not t.is_confirmed()]
        matches_a, unmatched_tracks_a, unmatched_detections = linear_assignment.matching_cascade(gated_metric, self.metric.matching_threshold, self.max_age, self.tracks, detections, confirmed_tracks)
        iou_track_candidates = unconfirmed_tracks + [k for k in unmatched_tracks_a if self.tracks[k].time_since_update == 1]
        unmatched_tracks_a = [k for k in unmatched_tracks_a if self.tracks[k].time_since_update != 1]
        matches_b, unmatched_tracks_b, unmatched_detections = linear_assignment.min_cost_matching(iou_matching.iou_cost, self.max_iou_dist, self.tracks, detections, iou_track_candidates, unmatched_detections)
        matches = matches_a + matches_b
        unmatched_tracks = list(set(unmatched_tracks_a + unmatched_tracks_b))
        return (matches, unmatched_tracks, unmatched_detections)

    def _initiate_track(self, detection, class_id, conf):
        self.tracks.append(Track(detection.to_xyah(), self._next_id, class_id, conf, self.n_init, self.max_age, self.ema_alpha, detection.feature))
        self._next_id += 1

def camera_update(self, previous_img, current_img):
    for track in self.tracks:
        track.camera_update(previous_img, current_img)

def is_video(ext: str):
    """
    Returns true if ext exists in
    allowed_exts for video files.

    Args:
        ext:

    Returns:

    """
    allowed_exts = ('.mp4', '.webm', '.ogg', '.avi', '.wmv', '.mkv', '.3gp')
    return any((ext.endswith(x) for x in allowed_exts))

class Evaluator(object):

    def __init__(self, data_root, seq_name, data_type):
        self.data_root = data_root
        self.seq_name = seq_name
        self.data_type = data_type
        self.load_annotations()
        self.reset_accumulator()

    def load_annotations(self):
        assert self.data_type == 'mot'
        gt_filename = os.path.join(self.data_root, self.seq_name, 'gt', 'gt.txt')
        self.gt_frame_dict = read_results(gt_filename, self.data_type, is_gt=True)
        self.gt_ignore_frame_dict = read_results(gt_filename, self.data_type, is_ignore=True)

    def reset_accumulator(self):
        self.acc = mm.MOTAccumulator(auto_id=True)

    def eval_frame(self, frame_id, trk_tlwhs, trk_ids, rtn_events=False):
        trk_tlwhs = np.copy(trk_tlwhs)
        trk_ids = np.copy(trk_ids)
        gt_objs = self.gt_frame_dict.get(frame_id, [])
        gt_tlwhs, gt_ids = unzip_objs(gt_objs)[:2]
        ignore_objs = self.gt_ignore_frame_dict.get(frame_id, [])
        ignore_tlwhs = unzip_objs(ignore_objs)[0]
        keep = np.ones(len(trk_tlwhs), dtype=bool)
        iou_distance = mm.distances.iou_matrix(ignore_tlwhs, trk_tlwhs, max_iou=0.5)
        if len(iou_distance) > 0:
            match_is, match_js = mm.lap.linear_sum_assignment(iou_distance)
            match_is, match_js = map(lambda a: np.asarray(a, dtype=int), [match_is, match_js])
            match_ious = iou_distance[match_is, match_js]
            match_js = np.asarray(match_js, dtype=int)
            match_js = match_js[np.logical_not(np.isnan(match_ious))]
            keep[match_js] = False
            trk_tlwhs = trk_tlwhs[keep]
            trk_ids = trk_ids[keep]
        iou_distance = mm.distances.iou_matrix(gt_tlwhs, trk_tlwhs, max_iou=0.5)
        self.acc.update(gt_ids, trk_ids, iou_distance)
        if rtn_events and iou_distance.size > 0 and hasattr(self.acc, 'last_mot_events'):
            events = self.acc.last_mot_events
        else:
            events = None
        return events

    def eval_file(self, filename):
        self.reset_accumulator()
        result_frame_dict = read_results(filename, self.data_type, is_gt=False)
        frames = sorted(list(set(self.gt_frame_dict.keys()) | set(result_frame_dict.keys())))
        for frame_id in frames:
            trk_objs = result_frame_dict.get(frame_id, [])
            trk_tlwhs, trk_ids = unzip_objs(trk_objs)[:2]
            self.eval_frame(frame_id, trk_tlwhs, trk_ids, rtn_events=False)
        return self.acc

    @staticmethod
    def get_summary(accs, names, metrics=('mota', 'num_switches', 'idp', 'idr', 'idf1', 'precision', 'recall')):
        names = copy.deepcopy(names)
        if metrics is None:
            metrics = mm.metrics.motchallenge_metrics
        metrics = copy.deepcopy(metrics)
        mh = mm.metrics.create()
        summary = mh.compute_many(accs, metrics=metrics, names=names, generate_overall=True)
        return summary

    @staticmethod
    def save_summary(summary, filename):
        import pandas as pd
        writer = pd.ExcelWriter(filename)
        summary.to_excel(writer)
        writer.save()

@staticmethod
def get_summary(accs, names, metrics=('mota', 'num_switches', 'idp', 'idr', 'idf1', 'precision', 'recall')):
    names = copy.deepcopy(names)
    if metrics is None:
        metrics = mm.metrics.motchallenge_metrics
    metrics = copy.deepcopy(metrics)
    mh = mm.metrics.create()
    summary = mh.compute_many(accs, metrics=metrics, names=names, generate_overall=True)
    return summary

class BboxToJsonLogger(BaseJsonLogger):
    """
    ُ This module is designed to automate the task of logging jsons. An example json is used
    to show the contents of json file shortly
    Example:
          {
          "video_details": {
            "frame_width": 1920,
            "frame_height": 1080,
            "frame_rate": 20,
            "video_name": "/home/gpu/codes/MSD/pedestrian_2/project/public/camera1.avi"
          },
          "frames": [
            {
              "frame_id": 329,
              "timestamp": 3365.1254
              "bboxes": [
                {
                  "labels": [
                    {
                      "category": "pedestrian",
                      "confidence": 0.9
                    }
                  ],
                  "bbox_id": 0,
                  "top": 1257,
                  "left": 138,
                  "width": 68,
                  "height": 109
                }
              ]
            }],

    Attributes:
        frames (dict): It's a dictionary that maps each frame_id to json attributes.
        video_details (dict): information about video file.
        top_k_labels (int): shows the allowed number of labels
        start_time (datetime object): we use it to automate the json output by time.

    Args:
        top_k_labels (int): shows the allowed number of labels

    """

    def __init__(self, top_k_labels: int=1):
        self.frames = {}
        self.video_details = self.video_details = dict(frame_width=None, frame_height=None, frame_rate=None, video_name=None)
        self.top_k_labels = top_k_labels
        self.start_time = datetime.now()

    def set_top_k(self, value):
        self.top_k_labels = value

    def frame_exists(self, frame_id: int) -> bool:
        """
        Args:
            frame_id (int):

        Returns:
            bool: true if frame_id is recognized
        """
        return frame_id in self.frames.keys()

    def add_frame(self, frame_id: int, timestamp: float=None) -> None:
        """
        Args:
            frame_id (int):
            timestamp (float): opencv captured frame time property

        Raises:
             ValueError: if frame_id would not exist in class frames attribute

        Returns:
            None

        """
        if not self.frame_exists(frame_id):
            self.frames[frame_id] = Frame(frame_id, timestamp)
        else:
            raise ValueError('Frame id: {} already exists'.format(frame_id))

    def bbox_exists(self, frame_id: int, bbox_id: int) -> bool:
        """
        Args:
            frame_id:
            bbox_id:

        Returns:
            bool: if bbox exists in frame bboxes list
        """
        bboxes = []
        if self.frame_exists(frame_id=frame_id):
            bboxes = [bbox.bbox_id for bbox in self.frames[frame_id].bboxes]
        return bbox_id in bboxes

    def find_bbox(self, frame_id: int, bbox_id: int):
        """

        Args:
            frame_id:
            bbox_id:

        Returns:
            bbox_id (int):

        Raises:
            ValueError: if bbox_id does not exist in the bbox list of specific frame.
        """
        if not self.bbox_exists(frame_id, bbox_id):
            raise ValueError('frame with id: {} does not contain bbox with id: {}'.format(frame_id, bbox_id))
        bboxes = {bbox.bbox_id: bbox for bbox in self.frames[frame_id].bboxes}
        return bboxes.get(bbox_id)

    def add_bbox_to_frame(self, frame_id: int, bbox_id: int, top: int, left: int, width: int, height: int) -> None:
        """

        Args:
            frame_id (int):
            bbox_id (int):
            top (int):
            left (int):
            width (int):
            height (int):

        Returns:
            None

        Raises:
            ValueError: if bbox_id already exist in frame information with frame_id
            ValueError: if frame_id does not exist in frames attribute
        """
        if self.frame_exists(frame_id):
            frame = self.frames[frame_id]
            if not self.bbox_exists(frame_id, bbox_id):
                frame.add_bbox(bbox_id, top, left, width, height)
            else:
                raise ValueError('frame with frame_id: {} already contains the bbox with id: {} '.format(frame_id, bbox_id))
        else:
            raise ValueError('frame with frame_id: {} does not exist'.format(frame_id))

    def add_label_to_bbox(self, frame_id: int, bbox_id: int, category: str, confidence: float):
        """
        Args:
            frame_id:
            bbox_id:
            category:
            confidence: the confidence value returned from yolo detection

        Returns:
            None

        Raises:
            ValueError: if labels quota (top_k_labels) exceeds.
        """
        bbox = self.find_bbox(frame_id, bbox_id)
        if not bbox.labels_full(self.top_k_labels):
            bbox.add_label(category, confidence)
        else:
            raise ValueError('labels in frame_id: {}, bbox_id: {} is fulled'.format(frame_id, bbox_id))

    def add_video_details(self, frame_width: int=None, frame_height: int=None, frame_rate: int=None, video_name: str=None):
        self.video_details['frame_width'] = frame_width
        self.video_details['frame_height'] = frame_height
        self.video_details['frame_rate'] = frame_rate
        self.video_details['video_name'] = video_name

    def output(self):
        output = {'video_details': self.video_details}
        result = list(self.frames.values())
        output['frames'] = [item.dic() for item in result]
        return output

    def json_output(self, output_name):
        """
        Args:
            output_name:

        Returns:
            None

        Notes:
            It creates the json output with `output_name` name.
        """
        if not output_name.endswith('.json'):
            output_name += '.json'
        with open(output_name, 'w') as file:
            json.dump(self.output(), file)
        file.close()

    def set_start(self):
        self.start_time = datetime.now()

    def schedule_output_by_time(self, output_dir=JsonMeta.PATH_TO_SAVE, hours: int=0, minutes: int=0, seconds: int=60) -> None:
        """
        Notes:
            Creates folder and then periodically stores the jsons on that address.

        Args:
            output_dir (str): the directory where output files will be stored
            hours (int):
            minutes (int):
            seconds (int):

        Returns:
            None

        """
        end = datetime.now()
        interval = 0
        interval += abs(min([hours, JsonMeta.HOURS]) * 3600)
        interval += abs(min([minutes, JsonMeta.MINUTES]) * 60)
        interval += abs(min([seconds, JsonMeta.SECONDS]))
        diff = (end - self.start_time).seconds
        if diff > interval:
            output_name = self.start_time.strftime('%Y-%m-%d %H-%M-%S') + '.json'
            if not exists(output_dir):
                makedirs(output_dir)
            output = join(output_dir, output_name)
            self.json_output(output_name=output)
            self.frames = {}
            self.start_time = datetime.now()

    def schedule_output_by_frames(self, frames_quota, frame_counter, output_dir=JsonMeta.PATH_TO_SAVE):
        """
        saves as the number of frames quota increases higher.
        :param frames_quota:
        :param frame_counter:
        :param output_dir:
        :return:
        """
        pass

    def flush(self, output_dir):
        """
        Notes:
            We use this function to output jsons whenever possible.
            like the time that we exit the while loop of opencv.

        Args:
            output_dir:

        Returns:
            None

        """
        filename = self.start_time.strftime('%Y-%m-%d %H-%M-%S') + '-remaining.json'
        output = join(output_dir, filename)
        self.json_output(output_name=output)

def schedule_output_by_time(self, output_dir=JsonMeta.PATH_TO_SAVE, hours: int=0, minutes: int=0, seconds: int=60) -> None:
    """
        Notes:
            Creates folder and then periodically stores the jsons on that address.

        Args:
            output_dir (str): the directory where output files will be stored
            hours (int):
            minutes (int):
            seconds (int):

        Returns:
            None

        """
    end = datetime.now()
    interval = 0
    interval += abs(min([hours, JsonMeta.HOURS]) * 3600)
    interval += abs(min([minutes, JsonMeta.MINUTES]) * 60)
    interval += abs(min([seconds, JsonMeta.SECONDS]))
    diff = (end - self.start_time).seconds
    if diff > interval:
        output_name = self.start_time.strftime('%Y-%m-%d %H-%M-%S') + '.json'
        if not exists(output_dir):
            makedirs(output_dir)
        output = join(output_dir, output_name)
        self.json_output(output_name=output)
        self.frames = {}
        self.start_time = datetime.now()

def flush(self, output_dir):
    """
        Notes:
            We use this function to output jsons whenever possible.
            like the time that we exit the while loop of opencv.

        Args:
            output_dir:

        Returns:
            None

        """
    filename = self.start_time.strftime('%Y-%m-%d %H-%M-%S') + '-remaining.json'
    output = join(output_dir, filename)
    self.json_output(output_name=output)

def _get_torch_home():
    ENV_TORCH_HOME = 'TORCH_HOME'
    ENV_XDG_CACHE_HOME = 'XDG_CACHE_HOME'
    DEFAULT_CACHE_DIR = '~/.cache'
    torch_home = os.path.expanduser(os.getenv(ENV_TORCH_HOME, os.path.join(os.getenv(ENV_XDG_CACHE_HOME, DEFAULT_CACHE_DIR), 'torch')))
    return torch_home

def _get_torch_home():
    ENV_TORCH_HOME = 'TORCH_HOME'
    ENV_XDG_CACHE_HOME = 'XDG_CACHE_HOME'
    DEFAULT_CACHE_DIR = '~/.cache'
    torch_home = os.path.expanduser(os.getenv(ENV_TORCH_HOME, os.path.join(os.getenv(ENV_XDG_CACHE_HOME, DEFAULT_CACHE_DIR), 'torch')))
    return torch_home

class CMCComputer:

    def __init__(self, minimum_features=10, method='sparse'):
        assert method in ['file', 'sparse', 'sift']
        os.makedirs('./cache', exist_ok=True)
        self.cache_path = './cache/affine_ocsort.pkl'
        self.cache = {}
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'rb') as fp:
                self.cache = pickle.load(fp)
        self.minimum_features = minimum_features
        self.prev_img = None
        self.prev_desc = None
        self.sparse_flow_param = dict(maxCorners=3000, qualityLevel=0.01, minDistance=1, blockSize=3, useHarrisDetector=False, k=0.04)
        self.file_computed = {}
        self.comp_function = None
        if method == 'sparse':
            self.comp_function = self._affine_sparse_flow
        elif method == 'sift':
            self.comp_function = self._affine_sift
        elif method == 'file':
            self.comp_function = self._affine_file
            self.file_affines = {}
            self.file_names = {}
            for f_name in os.listdir('./cache/cmc_files/MOT17_ablation/'):
                tag = f_name.replace('GMC-', '').replace('.txt', '') + '-FRCNN'
                f_name = os.path.join('./cache/cmc_files/MOT17_ablation/', f_name)
                self.file_names[tag] = f_name
            for f_name in os.listdir('./cache/cmc_files/MOT20_ablation/'):
                tag = f_name.replace('GMC-', '').replace('.txt', '')
                f_name = os.path.join('./cache/cmc_files/MOT20_ablation/', f_name)
                self.file_names[tag] = f_name
            for f_name in os.listdir('./cache/cmc_files/MOTChallenge/'):
                tag = f_name.replace('GMC-', '').replace('.txt', '')
                if 'MOT17' in tag:
                    tag = tag + '-FRCNN'
                if tag in self.file_names:
                    continue
                f_name = os.path.join('./cache/cmc_files/MOTChallenge/', f_name)
                self.file_names[tag] = f_name

    def compute_affine(self, img, bbox, tag):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if tag in self.cache:
            A = self.cache[tag]
            return A
        mask = np.ones_like(img, dtype=np.uint8)
        if bbox.shape[0] > 0:
            bbox = np.round(bbox).astype(np.int32)
            bbox[bbox < 0] = 0
            for bb in bbox:
                mask[bb[1]:bb[3], bb[0]:bb[2]] = 0
        A = self.comp_function(img, mask, tag)
        self.cache[tag] = A
        return A

    def _load_file(self, name):
        affines = []
        with open(self.file_names[name], 'r') as fp:
            for line in fp:
                tokens = [float(f) for f in line.split('\t')[1:7]]
                A = np.eye(2, 3)
                A[0, 0] = tokens[0]
                A[0, 1] = tokens[1]
                A[0, 2] = tokens[2]
                A[1, 0] = tokens[3]
                A[1, 1] = tokens[4]
                A[1, 2] = tokens[5]
                affines.append(A)
        self.file_affines[name] = affines

    def _affine_file(self, frame, mask, tag):
        name, num = tag.split(':')
        if name not in self.file_affines:
            self._load_file(name)
        if name not in self.file_affines:
            raise RuntimeError('Error loading file affines for CMC.')
        return self.file_affines[name][int(num) - 1]

    def _affine_sift(self, frame, mask, tag):
        A = np.eye(2, 3)
        detector = cv2.SIFT_create()
        kp, desc = detector.detectAndCompute(frame, mask)
        if self.prev_desc is None:
            self.prev_desc = [kp, desc]
            return A
        if desc.shape[0] < self.minimum_features or self.prev_desc[1].shape[0] < self.minimum_features:
            return A
        bf = cv2.BFMatcher(cv2.NORM_L2)
        matches = bf.knnMatch(self.prev_desc[1], desc, k=2)
        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)
        if len(good) > self.minimum_features:
            src_pts = np.float32([self.prev_desc[0][m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            A, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC)
        else:
            print('Warning: not enough matching points')
        if A is None:
            A = np.eye(2, 3)
        self.prev_desc = [kp, desc]
        return A

    def _affine_sparse_flow(self, frame, mask, tag):
        A = np.eye(2, 3)
        keypoints = cv2.goodFeaturesToTrack(frame, mask=mask, **self.sparse_flow_param)
        if self.prev_img is None:
            self.prev_img = frame
            self.prev_desc = keypoints
            return A
        matched_kp, status, err = cv2.calcOpticalFlowPyrLK(self.prev_img, frame, self.prev_desc, None)
        matched_kp = matched_kp.reshape(-1, 2)
        status = status.reshape(-1)
        prev_points = self.prev_desc.reshape(-1, 2)
        prev_points = prev_points[status]
        curr_points = matched_kp[status]
        if prev_points.shape[0] > self.minimum_features:
            A, _ = cv2.estimateAffinePartial2D(prev_points, curr_points, method=cv2.RANSAC)
        else:
            print('Warning: not enough matching points')
        if A is None:
            A = np.eye(2, 3)
        self.prev_img = frame
        self.prev_desc = keypoints
        return A

    def dump_cache(self):
        with open(self.cache_path, 'wb') as fp:
            pickle.dump(self.cache, fp)

def __init__(self, minimum_features=10, method='sparse'):
    assert method in ['file', 'sparse', 'sift']
    os.makedirs('./cache', exist_ok=True)
    self.cache_path = './cache/affine_ocsort.pkl'
    self.cache = {}
    if os.path.exists(self.cache_path):
        with open(self.cache_path, 'rb') as fp:
            self.cache = pickle.load(fp)
    self.minimum_features = minimum_features
    self.prev_img = None
    self.prev_desc = None
    self.sparse_flow_param = dict(maxCorners=3000, qualityLevel=0.01, minDistance=1, blockSize=3, useHarrisDetector=False, k=0.04)
    self.file_computed = {}
    self.comp_function = None
    if method == 'sparse':
        self.comp_function = self._affine_sparse_flow
    elif method == 'sift':
        self.comp_function = self._affine_sift
    elif method == 'file':
        self.comp_function = self._affine_file
        self.file_affines = {}
        self.file_names = {}
        for f_name in os.listdir('./cache/cmc_files/MOT17_ablation/'):
            tag = f_name.replace('GMC-', '').replace('.txt', '') + '-FRCNN'
            f_name = os.path.join('./cache/cmc_files/MOT17_ablation/', f_name)
            self.file_names[tag] = f_name
        for f_name in os.listdir('./cache/cmc_files/MOT20_ablation/'):
            tag = f_name.replace('GMC-', '').replace('.txt', '')
            f_name = os.path.join('./cache/cmc_files/MOT20_ablation/', f_name)
            self.file_names[tag] = f_name
        for f_name in os.listdir('./cache/cmc_files/MOTChallenge/'):
            tag = f_name.replace('GMC-', '').replace('.txt', '')
            if 'MOT17' in tag:
                tag = tag + '-FRCNN'
            if tag in self.file_names:
                continue
            f_name = os.path.join('./cache/cmc_files/MOTChallenge/', f_name)
            self.file_names[tag] = f_name

class EmbeddingComputer:

    def __init__(self, dataset):
        self.model = None
        self.dataset = dataset
        self.crop_size = (128, 384)
        os.makedirs('./cache/embeddings/', exist_ok=True)
        self.cache_path = './cache/embeddings/{}_embedding.pkl'
        self.cache = {}
        self.cache_name = ''

    def load_cache(self, path):
        self.cache_name = path
        cache_path = self.cache_path.format(path)
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as fp:
                self.cache = pickle.load(fp)

    def compute_embedding(self, img, bbox, tag, is_numpy=True):
        if self.cache_name != tag.split(':')[0]:
            self.load_cache(tag.split(':')[0])
        if tag in self.cache:
            embs = self.cache[tag]
            if embs.shape[0] != bbox.shape[0]:
                raise RuntimeError("ERROR: The number of cached embeddings don't match the number of detections.\nWas the detector model changed? Delete cache if so.")
            return embs
        if self.model is None:
            self.initialize_model()
        if is_numpy:
            h, w = img.shape[:2]
        else:
            h, w = img.shape[2:]
        results = np.round(bbox).astype(np.int32)
        results[:, 0] = results[:, 0].clip(0, w)
        results[:, 1] = results[:, 1].clip(0, h)
        results[:, 2] = results[:, 2].clip(0, w)
        results[:, 3] = results[:, 3].clip(0, h)
        crops = []
        for p in results:
            if is_numpy:
                crop = img[p[1]:p[3], p[0]:p[2]]
                crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                crop = cv2.resize(crop, self.crop_size, interpolation=cv2.INTER_LINEAR)
                crop = torch.as_tensor(crop.astype('float32').transpose(2, 0, 1))
                crop = crop.unsqueeze(0)
            else:
                crop = img[:, :, p[1]:p[3], p[0]:p[2]]
                crop = torchvision.transforms.functional.resize(crop, self.crop_size)
            crops.append(crop)
        crops = torch.cat(crops, dim=0)
        with torch.no_grad():
            crops = crops.cuda()
            crops = crops.half()
            embs = self.model(crops)
        embs = torch.nn.functional.normalize(embs)
        embs = embs.cpu().numpy()
        self.cache[tag] = embs
        return embs

    def initialize_model(self):
        """
        model = torchreid.models.build_model(name="osnet_ain_x1_0", num_classes=2510, loss="softmax", pretrained=False)
        sd = torch.load("external/weights/osnet_ain_ms_d_c.pth.tar")["state_dict"]
        new_state_dict = OrderedDict()
        for k, v in sd.items():
            name = k[7:]  # remove `module.`
            new_state_dict[name] = v
        # load params
        model.load_state_dict(new_state_dict)
        model.eval()
        model.cuda()
        """
        if self.dataset == 'mot17':
            path = 'external/weights/mot17_sbs_S50.pth'
        elif self.dataset == 'mot20':
            path = 'external/weights/mot20_sbs_S50.pth'
        elif self.dataset == 'dance':
            path = None
        else:
            raise RuntimeError('Need the path for a new ReID model.')
        model = FastReID(path)
        model.eval()
        model.cuda()
        model.half()
        self.model = model

    def dump_cache(self):
        if self.cache_name:
            with open(self.cache_path.format(self.cache_name), 'wb') as fp:
                pickle.dump(self.cache, fp)

def __init__(self, dataset):
    self.model = None
    self.dataset = dataset
    self.crop_size = (128, 384)
    os.makedirs('./cache/embeddings/', exist_ok=True)
    self.cache_path = './cache/embeddings/{}_embedding.pkl'
    self.cache = {}
    self.cache_name = ''

def check_suffix(file='yolov5s.pt', suffix=('.pt',), msg=''):
    if file and suffix:
        if isinstance(suffix, str):
            suffix = [suffix]
        for f in file if isinstance(file, (list, tuple)) else [file]:
            s = Path(f).suffix.lower()
            if len(s):
                assert s in suffix, f'{msg}{f} acceptable suffix is {suffix}'

class KalmanFilterNew(object):
    """Implements a Kalman filter. You are responsible for setting the
    various state variables to reasonable values; the defaults  will
    not give you a functional filter.
    For now the best documentation is my free book Kalman and Bayesian
    Filters in Python [2]_. The test files in this directory also give you a
    basic idea of use, albeit without much description.
    In brief, you will first construct this object, specifying the size of
    the state vector with dim_x and the size of the measurement vector that
    you will be using with dim_z. These are mostly used to perform size checks
    when you assign values to the various matrices. For example, if you
    specified dim_z=2 and then try to assign a 3x3 matrix to R (the
    measurement noise matrix you will get an assert exception because R
    should be 2x2. (If for whatever reason you need to alter the size of
    things midstream just use the underscore version of the matrices to
    assign directly: your_filter._R = a_3x3_matrix.)
    After construction the filter will have default matrices created for you,
    but you must specify the values for each. It’s usually easiest to just
    overwrite them rather than assign to each element yourself. This will be
    clearer in the example below. All are of type numpy.array.
    Examples
    --------
    Here is a filter that tracks position and velocity using a sensor that only
    reads position.
    First construct the object with the required dimensionality. Here the state
    (`dim_x`) has 2 coefficients (position and velocity), and the measurement
    (`dim_z`) has one. In FilterPy `x` is the state, `z` is the measurement.
    .. code::
        from filterpy.kalman import KalmanFilter
        f = KalmanFilter (dim_x=2, dim_z=1)
    Assign the initial value for the state (position and velocity). You can do this
    with a two dimensional array like so:
        .. code::
            f.x = np.array([[2.],    # position
                            [0.]])   # velocity
    or just use a one dimensional array, which I prefer doing.
    .. code::
        f.x = np.array([2., 0.])
    Define the state transition matrix:
        .. code::
            f.F = np.array([[1.,1.],
                            [0.,1.]])
    Define the measurement function. Here we need to convert a position-velocity
    vector into just a position vector, so we use:
        .. code::
        f.H = np.array([[1., 0.]])
    Define the state's covariance matrix P.
    .. code::
        f.P = np.array([[1000.,    0.],
                        [   0., 1000.] ])
    Now assign the measurement noise. Here the dimension is 1x1, so I can
    use a scalar
    .. code::
        f.R = 5
    I could have done this instead:
    .. code::
        f.R = np.array([[5.]])
    Note that this must be a 2 dimensional array.
    Finally, I will assign the process noise. Here I will take advantage of
    another FilterPy library function:
    .. code::
        from filterpy.common import Q_discrete_white_noise
        f.Q = Q_discrete_white_noise(dim=2, dt=0.1, var=0.13)
    Now just perform the standard predict/update loop:
    .. code::
        while some_condition_is_true:
            z = get_sensor_reading()
            f.predict()
            f.update(z)
            do_something_with_estimate (f.x)
    **Procedural Form**
    This module also contains stand alone functions to perform Kalman filtering.
    Use these if you are not a fan of objects.
    **Example**
    .. code::
        while True:
            z, R = read_sensor()
            x, P = predict(x, P, F, Q)
            x, P = update(x, P, z, R, H)
    See my book Kalman and Bayesian Filters in Python [2]_.
    You will have to set the following attributes after constructing this
    object for the filter to perform properly. Please note that there are
    various checks in place to ensure that you have made everything the
    'correct' size. However, it is possible to provide incorrectly sized
    arrays such that the linear algebra can not perform an operation.
    It can also fail silently - you can end up with matrices of a size that
    allows the linear algebra to work, but are the wrong shape for the problem
    you are trying to solve.
    Parameters
    ----------
    dim_x : int
        Number of state variables for the Kalman filter. For example, if
        you are tracking the position and velocity of an object in two
        dimensions, dim_x would be 4.
        This is used to set the default size of P, Q, and u
    dim_z : int
        Number of of measurement inputs. For example, if the sensor
        provides you with position in (x,y), dim_z would be 2.
    dim_u : int (optional)
        size of the control input, if it is being used.
        Default value of 0 indicates it is not used.
    compute_log_likelihood : bool (default = True)
        Computes log likelihood by default, but this can be a slow
        computation, so if you never use it you can turn this computation
        off.
    Attributes
    ----------
    x : numpy.array(dim_x, 1)
        Current state estimate. Any call to update() or predict() updates
        this variable.
    P : numpy.array(dim_x, dim_x)
        Current state covariance matrix. Any call to update() or predict()
        updates this variable.
    x_prior : numpy.array(dim_x, 1)
        Prior (predicted) state estimate. The *_prior and *_post attributes
        are for convenience; they store the  prior and posterior of the
        current epoch. Read Only.
    P_prior : numpy.array(dim_x, dim_x)
        Prior (predicted) state covariance matrix. Read Only.
    x_post : numpy.array(dim_x, 1)
        Posterior (updated) state estimate. Read Only.
    P_post : numpy.array(dim_x, dim_x)
        Posterior (updated) state covariance matrix. Read Only.
    z : numpy.array
        Last measurement used in update(). Read only.
    R : numpy.array(dim_z, dim_z)
        Measurement noise covariance matrix. Also known as the
        observation covariance.
    Q : numpy.array(dim_x, dim_x)
        Process noise covariance matrix. Also known as the transition
        covariance.
    F : numpy.array()
        State Transition matrix. Also known as `A` in some formulation.
    H : numpy.array(dim_z, dim_x)
        Measurement function. Also known as the observation matrix, or as `C`.
    y : numpy.array
        Residual of the update step. Read only.
    K : numpy.array(dim_x, dim_z)
        Kalman gain of the update step. Read only.
    S :  numpy.array
        System uncertainty (P projected to measurement space). Read only.
    SI :  numpy.array
        Inverse system uncertainty. Read only.
    log_likelihood : float
        log-likelihood of the last measurement. Read only.
    likelihood : float
        likelihood of last measurement. Read only.
        Computed from the log-likelihood. The log-likelihood can be very
        small,  meaning a large negative value such as -28000. Taking the
        exp() of that results in 0.0, which can break typical algorithms
        which multiply by this value, so by default we always return a
        number >= sys.float_info.min.
    mahalanobis : float
        mahalanobis distance of the innovation. Read only.
    inv : function, default numpy.linalg.inv
        If you prefer another inverse function, such as the Moore-Penrose
        pseudo inverse, set it to that instead: kf.inv = np.linalg.pinv
        This is only used to invert self.S. If you know it is diagonal, you
        might choose to set it to filterpy.common.inv_diagonal, which is
        several times faster than numpy.linalg.inv for diagonal matrices.
    alpha : float
        Fading memory setting. 1.0 gives the normal Kalman filter, and
        values slightly larger than 1.0 (such as 1.02) give a fading
        memory effect - previous measurements have less influence on the
        filter's estimates. This formulation of the Fading memory filter
        (there are many) is due to Dan Simon [1]_.
    References
    ----------
    .. [1] Dan Simon. "Optimal State Estimation." John Wiley & Sons.
       p. 208-212. (2006)
    .. [2] Roger Labbe. "Kalman and Bayesian Filters in Python"
       https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python
    """

    def __init__(self, dim_x, dim_z, dim_u=0):
        if dim_x < 1:
            raise ValueError('dim_x must be 1 or greater')
        if dim_z < 1:
            raise ValueError('dim_z must be 1 or greater')
        if dim_u < 0:
            raise ValueError('dim_u must be 0 or greater')
        self.dim_x = dim_x
        self.dim_z = dim_z
        self.dim_u = dim_u
        self.x = zeros((dim_x, 1))
        self.P = eye(dim_x)
        self.Q = eye(dim_x)
        self.B = None
        self.F = eye(dim_x)
        self.H = zeros((dim_z, dim_x))
        self.R = eye(dim_z)
        self._alpha_sq = 1.0
        self.M = np.zeros((dim_x, dim_z))
        self.z = np.array([[None] * self.dim_z]).T
        self.K = np.zeros((dim_x, dim_z))
        self.y = zeros((dim_z, 1))
        self.S = np.zeros((dim_z, dim_z))
        self.SI = np.zeros((dim_z, dim_z))
        self._I = np.eye(dim_x)
        self.x_prior = self.x.copy()
        self.P_prior = self.P.copy()
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()
        self._log_likelihood = log(sys.float_info.min)
        self._likelihood = sys.float_info.min
        self._mahalanobis = None
        self.history_obs = []
        self.inv = np.linalg.inv
        self.attr_saved = None
        self.observed = False
        self.last_measurement = None

    def predict(self, u=None, B=None, F=None, Q=None):
        """
        Predict next state (prior) using the Kalman filter state propagation
        equations.
        Parameters
        ----------
        u : np.array, default 0
            Optional control vector.
        B : np.array(dim_x, dim_u), or None
            Optional control transition matrix; a value of None
            will cause the filter to use `self.B`.
        F : np.array(dim_x, dim_x), or None
            Optional state transition matrix; a value of None
            will cause the filter to use `self.F`.
        Q : np.array(dim_x, dim_x), scalar, or None
            Optional process noise matrix; a value of None will cause the
            filter to use `self.Q`.
        """
        if B is None:
            B = self.B
        if F is None:
            F = self.F
        if Q is None:
            Q = self.Q
        elif isscalar(Q):
            Q = eye(self.dim_x) * Q
        if B is not None and u is not None:
            self.x = dot(F, self.x) + dot(B, u)
        else:
            self.x = dot(F, self.x)
        self.P = self._alpha_sq * dot(dot(F, self.P), F.T) + Q
        self.x_prior = self.x.copy()
        self.P_prior = self.P.copy()

    def freeze(self):
        """
        Save the parameters before non-observation forward
        """
        self.attr_saved = deepcopy(self.__dict__)

    def apply_affine_correction(self, m, t, new_kf):
        """
        Apply to both last state and last observation for OOS smoothing.

        Messy due to internal logic for kalman filter being messy.
        """
        if new_kf:
            big_m = np.kron(np.eye(4, dtype=float), m)
            self.x = big_m @ self.x
            self.x[:2] += t
            self.P = big_m @ self.P @ big_m.T
            if not self.observed and self.attr_saved is not None:
                self.attr_saved['x'] = big_m @ self.attr_saved['x']
                self.attr_saved['x'][:2] += t
                self.attr_saved['P'] = big_m @ self.attr_saved['P'] @ big_m.T
                self.attr_saved['last_measurement'][:2] = m @ self.attr_saved['last_measurement'][:2] + t
                self.attr_saved['last_measurement'][2:] = m @ self.attr_saved['last_measurement'][2:]
        else:
            scale = np.linalg.norm(m[:, 0])
            self.x[:2] = m @ self.x[:2] + t
            self.x[4:6] = m @ self.x[4:6]
            self.P[:2, :2] = m @ self.P[:2, :2] @ m.T
            self.P[4:6, 4:6] = m @ self.P[4:6, 4:6] @ m.T
            if not self.observed and self.attr_saved is not None:
                self.attr_saved['x'][:2] = m @ self.attr_saved['x'][:2] + t
                self.attr_saved['x'][4:6] = m @ self.attr_saved['x'][4:6]
                self.attr_saved['P'][:2, :2] = m @ self.attr_saved['P'][:2, :2] @ m.T
                self.attr_saved['P'][4:6, 4:6] = m @ self.attr_saved['P'][4:6, 4:6] @ m.T
                self.attr_saved['last_measurement'][:2] = m @ self.attr_saved['last_measurement'][:2] + t

    def unfreeze(self):
        if self.attr_saved is not None:
            new_history = deepcopy(self.history_obs)
            self.__dict__ = self.attr_saved
            self.history_obs = self.history_obs[:-1]
            occur = [int(d is None) for d in new_history]
            indices = np.where(np.array(occur) == 0)[0]
            index1 = indices[-2]
            index2 = indices[-1]
            box1 = self.last_measurement
            x1, y1, s1, r1 = box1
            w1 = np.sqrt(s1 * r1)
            h1 = np.sqrt(s1 / r1)
            box2 = new_history[index2]
            x2, y2, s2, r2 = box2
            w2 = np.sqrt(s2 * r2)
            h2 = np.sqrt(s2 / r2)
            time_gap = index2 - index1
            dx = (x2 - x1) / time_gap
            dy = (y2 - y1) / time_gap
            dw = (w2 - w1) / time_gap
            dh = (h2 - h1) / time_gap
            for i in range(index2 - index1):
                '\n                The default virtual trajectory generation is by linear\n                motion (constant speed hypothesis), you could modify this\n                part to implement your own.\n                '
                x = x1 + (i + 1) * dx
                y = y1 + (i + 1) * dy
                w = w1 + (i + 1) * dw
                h = h1 + (i + 1) * dh
                s = w * h
                r = w / float(h)
                new_box = np.array([x, y, s, r]).reshape((4, 1))
                '\n                    I still use predict-update loop here to refresh the parameters,\n                    but this can be faster by directly modifying the internal parameters\n                    as suggested in the paper. I keep this naive but slow way for \n                    easy read and understanding\n                '
                self.update(new_box)
                if not i == index2 - index1 - 1:
                    self.predict()

    def update(self, z, R=None, H=None):
        """
        Add a new measurement (z) to the Kalman filter.
        If z is None, nothing is computed. However, x_post and P_post are
        updated with the prior (x_prior, P_prior), and self.z is set to None.
        Parameters
        ----------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.
            If you pass in a value of H, z must be a column vector the
            of the correct size.
        R : np.array, scalar, or None
            Optionally provide R to override the measurement noise for this
            one call, otherwise  self.R will be used.
        H : np.array, or None
            Optionally provide H to override the measurement function for this
            one call, otherwise self.H will be used.
        """
        self._log_likelihood = None
        self._likelihood = None
        self._mahalanobis = None
        self.history_obs.append(z)
        if z is None:
            if self.observed:
                '\n                Got no observation so freeze the current parameters for future\n                potential online smoothing.\n                '
                self.last_measurement = self.history_obs[-2]
                self.freeze()
            self.observed = False
            self.z = np.array([[None] * self.dim_z]).T
            self.x_post = self.x.copy()
            self.P_post = self.P.copy()
            self.y = zeros((self.dim_z, 1))
            return
        if not self.observed:
            '\n            Get observation, use online smoothing to re-update parameters\n            '
            self.unfreeze()
        self.observed = True
        if R is None:
            R = self.R
        elif isscalar(R):
            R = eye(self.dim_z) * R
        if H is None:
            z = reshape_z(z, self.dim_z, self.x.ndim)
            H = self.H
        self.y = z - dot(H, self.x)
        PHT = dot(self.P, H.T)
        self.S = dot(H, PHT) + R
        self.SI = self.inv(self.S)
        self.K = dot(PHT, self.SI)
        self.x = self.x + dot(self.K, self.y)
        I_KH = self._I - dot(self.K, H)
        self.P = dot(dot(I_KH, self.P), I_KH.T) + dot(dot(self.K, R), self.K.T)
        self.z = deepcopy(z)
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()

    def md_for_measurement(self, z):
        """Mahalanobis distance for any measurement.

        Should be run after a prediction() call.
        """
        z = reshape_z(z, self.dim_z, self.x.ndim)
        H = self.H
        y = z - dot(H, self.x)
        md = sqrt(float(dot(dot(y.T, self.SI), y)))
        return md

    def predict_steadystate(self, u=0, B=None):
        """
        Predict state (prior) using the Kalman filter state propagation
        equations. Only x is updated, P is left unchanged. See
        update_steadstate() for a longer explanation of when to use this
        method.
        Parameters
        ----------
        u : np.array
            Optional control vector. If non-zero, it is multiplied by B
            to create the control input into the system.
        B : np.array(dim_x, dim_u), or None
            Optional control transition matrix; a value of None
            will cause the filter to use `self.B`.
        """
        if B is None:
            B = self.B
        if B is not None:
            self.x = dot(self.F, self.x) + dot(B, u)
        else:
            self.x = dot(self.F, self.x)
        self.x_prior = self.x.copy()
        self.P_prior = self.P.copy()

    def update_steadystate(self, z):
        """
        Add a new measurement (z) to the Kalman filter without recomputing
        the Kalman gain K, the state covariance P, or the system
        uncertainty S.
        You can use this for LTI systems since the Kalman gain and covariance
        converge to a fixed value. Precompute these and assign them explicitly,
        or run the Kalman filter using the normal predict()/update(0 cycle
        until they converge.
        The main advantage of this call is speed. We do significantly less
        computation, notably avoiding a costly matrix inversion.
        Use in conjunction with predict_steadystate(), otherwise P will grow
        without bound.
        Parameters
        ----------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.
        Examples
        --------
        >>> cv = kinematic_kf(dim=3, order=2) # 3D const velocity filter
        >>> # let filter converge on representative data, then save k and P
        >>> for i in range(100):
        >>>     cv.predict()
        >>>     cv.update([i, i, i])
        >>> saved_k = np.copy(cv.K)
        >>> saved_P = np.copy(cv.P)
        later on:
        >>> cv = kinematic_kf(dim=3, order=2) # 3D const velocity filter
        >>> cv.K = np.copy(saved_K)
        >>> cv.P = np.copy(saved_P)
        >>> for i in range(100):
        >>>     cv.predict_steadystate()
        >>>     cv.update_steadystate([i, i, i])
        """
        self._log_likelihood = None
        self._likelihood = None
        self._mahalanobis = None
        if z is None:
            self.z = np.array([[None] * self.dim_z]).T
            self.x_post = self.x.copy()
            self.P_post = self.P.copy()
            self.y = zeros((self.dim_z, 1))
            return
        z = reshape_z(z, self.dim_z, self.x.ndim)
        self.y = z - dot(self.H, self.x)
        self.x = self.x + dot(self.K, self.y)
        self.z = deepcopy(z)
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()
        self._log_likelihood = None
        self._likelihood = None
        self._mahalanobis = None

    def update_correlated(self, z, R=None, H=None):
        """Add a new measurement (z) to the Kalman filter assuming that
        process noise and measurement noise are correlated as defined in
        the `self.M` matrix.
        A partial derivation can be found in [1]
        If z is None, nothing is changed.
        Parameters
        ----------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.
        R : np.array, scalar, or None
            Optionally provide R to override the measurement noise for this
            one call, otherwise  self.R will be used.
        H : np.array,  or None
            Optionally provide H to override the measurement function for this
            one call, otherwise  self.H will be used.
        References
        ----------
        .. [1] Bulut, Y. (2011). Applied Kalman filter theory (Doctoral dissertation, Northeastern University).
               http://people.duke.edu/~hpgavin/SystemID/References/Balut-KalmanFilter-PhD-NEU-2011.pdf
        """
        self._log_likelihood = None
        self._likelihood = None
        self._mahalanobis = None
        if z is None:
            self.z = np.array([[None] * self.dim_z]).T
            self.x_post = self.x.copy()
            self.P_post = self.P.copy()
            self.y = zeros((self.dim_z, 1))
            return
        if R is None:
            R = self.R
        elif isscalar(R):
            R = eye(self.dim_z) * R
        if H is None:
            z = reshape_z(z, self.dim_z, self.x.ndim)
            H = self.H
        if self.x.ndim == 1 and shape(z) == (1, 1):
            z = z[0]
        if shape(z) == ():
            z = np.asarray([z])
        self.y = z - dot(H, self.x)
        PHT = dot(self.P, H.T)
        self.S = dot(H, PHT) + dot(H, self.M) + dot(self.M.T, H.T) + R
        self.SI = self.inv(self.S)
        self.K = dot(PHT + self.M, self.SI)
        self.x = self.x + dot(self.K, self.y)
        self.P = self.P - dot(self.K, dot(H, self.P) + self.M.T)
        self.z = deepcopy(z)
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()

    def batch_filter(self, zs, Fs=None, Qs=None, Hs=None, Rs=None, Bs=None, us=None, update_first=False, saver=None):
        """Batch processes a sequences of measurements.
         Parameters
         ----------
         zs : list-like
             list of measurements at each time step `self.dt`. Missing
             measurements must be represented by `None`.
         Fs : None, list-like, default=None
             optional value or list of values to use for the state transition
             matrix F.
             If Fs is None then self.F is used for all epochs.
             Otherwise it must contain a list-like list of F's, one for
             each epoch.  This allows you to have varying F per epoch.
         Qs : None, np.array or list-like, default=None
             optional value or list of values to use for the process error
             covariance Q.
             If Qs is None then self.Q is used for all epochs.
             Otherwise it must contain a list-like list of Q's, one for
             each epoch.  This allows you to have varying Q per epoch.
         Hs : None, np.array or list-like, default=None
             optional list of values to use for the measurement matrix H.
             If Hs is None then self.H is used for all epochs.
             If Hs contains a single matrix, then it is used as H for all
             epochs.
             Otherwise it must contain a list-like list of H's, one for
             each epoch.  This allows you to have varying H per epoch.
         Rs : None, np.array or list-like, default=None
             optional list of values to use for the measurement error
             covariance R.
             If Rs is None then self.R is used for all epochs.
             Otherwise it must contain a list-like list of R's, one for
             each epoch.  This allows you to have varying R per epoch.
         Bs : None, np.array or list-like, default=None
             optional list of values to use for the control transition matrix B.
             If Bs is None then self.B is used for all epochs.
             Otherwise it must contain a list-like list of B's, one for
             each epoch.  This allows you to have varying B per epoch.
         us : None, np.array or list-like, default=None
             optional list of values to use for the control input vector;
             If us is None then None is used for all epochs (equivalent to 0,
             or no control input).
             Otherwise it must contain a list-like list of u's, one for
             each epoch.
        update_first : bool, optional, default=False
             controls whether the order of operations is update followed by
             predict, or predict followed by update. Default is predict->update.
         saver : filterpy.common.Saver, optional
             filterpy.common.Saver object. If provided, saver.save() will be
             called after every epoch
         Returns
         -------
         means : np.array((n,dim_x,1))
             array of the state for each time step after the update. Each entry
             is an np.array. In other words `means[k,:]` is the state at step
             `k`.
         covariance : np.array((n,dim_x,dim_x))
             array of the covariances for each time step after the update.
             In other words `covariance[k,:,:]` is the covariance at step `k`.
         means_predictions : np.array((n,dim_x,1))
             array of the state for each time step after the predictions. Each
             entry is an np.array. In other words `means[k,:]` is the state at
             step `k`.
         covariance_predictions : np.array((n,dim_x,dim_x))
             array of the covariances for each time step after the prediction.
             In other words `covariance[k,:,:]` is the covariance at step `k`.
         Examples
         --------
         .. code-block:: Python
             # this example demonstrates tracking a measurement where the time
             # between measurement varies, as stored in dts. This requires
             # that F be recomputed for each epoch. The output is then smoothed
             # with an RTS smoother.
             zs = [t + random.randn()*4 for t in range (40)]
             Fs = [np.array([[1., dt], [0, 1]] for dt in dts]
             (mu, cov, _, _) = kf.batch_filter(zs, Fs=Fs)
             (xs, Ps, Ks, Pps) = kf.rts_smoother(mu, cov, Fs=Fs)
        """
        n = np.size(zs, 0)
        if Fs is None:
            Fs = [self.F] * n
        if Qs is None:
            Qs = [self.Q] * n
        if Hs is None:
            Hs = [self.H] * n
        if Rs is None:
            Rs = [self.R] * n
        if Bs is None:
            Bs = [self.B] * n
        if us is None:
            us = [0] * n
        if self.x.ndim == 1:
            means = zeros((n, self.dim_x))
            means_p = zeros((n, self.dim_x))
        else:
            means = zeros((n, self.dim_x, 1))
            means_p = zeros((n, self.dim_x, 1))
        covariances = zeros((n, self.dim_x, self.dim_x))
        covariances_p = zeros((n, self.dim_x, self.dim_x))
        if update_first:
            for i, (z, F, Q, H, R, B, u) in enumerate(zip(zs, Fs, Qs, Hs, Rs, Bs, us)):
                self.update(z, R=R, H=H)
                means[i, :] = self.x
                covariances[i, :, :] = self.P
                self.predict(u=u, B=B, F=F, Q=Q)
                means_p[i, :] = self.x
                covariances_p[i, :, :] = self.P
                if saver is not None:
                    saver.save()
        else:
            for i, (z, F, Q, H, R, B, u) in enumerate(zip(zs, Fs, Qs, Hs, Rs, Bs, us)):
                self.predict(u=u, B=B, F=F, Q=Q)
                means_p[i, :] = self.x
                covariances_p[i, :, :] = self.P
                self.update(z, R=R, H=H)
                means[i, :] = self.x
                covariances[i, :, :] = self.P
                if saver is not None:
                    saver.save()
        return (means, covariances, means_p, covariances_p)

    def rts_smoother(self, Xs, Ps, Fs=None, Qs=None, inv=np.linalg.inv):
        """
        Runs the Rauch-Tung-Striebel Kalman smoother on a set of
        means and covariances computed by a Kalman filter. The usual input
        would come from the output of `KalmanFilter.batch_filter()`.
        Parameters
        ----------
        Xs : numpy.array
           array of the means (state variable x) of the output of a Kalman
           filter.
        Ps : numpy.array
            array of the covariances of the output of a kalman filter.
        Fs : list-like collection of numpy.array, optional
            State transition matrix of the Kalman filter at each time step.
            Optional, if not provided the filter's self.F will be used
        Qs : list-like collection of numpy.array, optional
            Process noise of the Kalman filter at each time step. Optional,
            if not provided the filter's self.Q will be used
        inv : function, default numpy.linalg.inv
            If you prefer another inverse function, such as the Moore-Penrose
            pseudo inverse, set it to that instead: kf.inv = np.linalg.pinv
        Returns
        -------
        x : numpy.ndarray
           smoothed means
        P : numpy.ndarray
           smoothed state covariances
        K : numpy.ndarray
            smoother gain at each step
        Pp : numpy.ndarray
           Predicted state covariances
        Examples
        --------
        .. code-block:: Python
            zs = [t + random.randn()*4 for t in range (40)]
            (mu, cov, _, _) = kalman.batch_filter(zs)
            (x, P, K, Pp) = rts_smoother(mu, cov, kf.F, kf.Q)
        """
        if len(Xs) != len(Ps):
            raise ValueError('length of Xs and Ps must be the same')
        n = Xs.shape[0]
        dim_x = Xs.shape[1]
        if Fs is None:
            Fs = [self.F] * n
        if Qs is None:
            Qs = [self.Q] * n
        K = zeros((n, dim_x, dim_x))
        x, P, Pp = (Xs.copy(), Ps.copy(), Ps.copy())
        for k in range(n - 2, -1, -1):
            Pp[k] = dot(dot(Fs[k + 1], P[k]), Fs[k + 1].T) + Qs[k + 1]
            K[k] = dot(dot(P[k], Fs[k + 1].T), inv(Pp[k]))
            x[k] += dot(K[k], x[k + 1] - dot(Fs[k + 1], x[k]))
            P[k] += dot(dot(K[k], P[k + 1] - Pp[k]), K[k].T)
        return (x, P, K, Pp)

    def get_prediction(self, u=None, B=None, F=None, Q=None):
        """
        Predict next state (prior) using the Kalman filter state propagation
        equations and returns it without modifying the object.
        Parameters
        ----------
        u : np.array, default 0
            Optional control vector.
        B : np.array(dim_x, dim_u), or None
            Optional control transition matrix; a value of None
            will cause the filter to use `self.B`.
        F : np.array(dim_x, dim_x), or None
            Optional state transition matrix; a value of None
            will cause the filter to use `self.F`.
        Q : np.array(dim_x, dim_x), scalar, or None
            Optional process noise matrix; a value of None will cause the
            filter to use `self.Q`.
        Returns
        -------
        (x, P) : tuple
            State vector and covariance array of the prediction.
        """
        if B is None:
            B = self.B
        if F is None:
            F = self.F
        if Q is None:
            Q = self.Q
        elif isscalar(Q):
            Q = eye(self.dim_x) * Q
        if B is not None and u is not None:
            x = dot(F, self.x) + dot(B, u)
        else:
            x = dot(F, self.x)
        P = self._alpha_sq * dot(dot(F, self.P), F.T) + Q
        return (x, P)

    def get_update(self, z=None):
        """
        Computes the new estimate based on measurement `z` and returns it
        without altering the state of the filter.
        Parameters
        ----------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.
        Returns
        -------
        (x, P) : tuple
            State vector and covariance array of the update.
        """
        if z is None:
            return (self.x, self.P)
        z = reshape_z(z, self.dim_z, self.x.ndim)
        R = self.R
        H = self.H
        P = self.P
        x = self.x
        y = z - dot(H, x)
        PHT = dot(P, H.T)
        S = dot(H, PHT) + R
        K = dot(PHT, self.inv(S))
        x = x + dot(K, y)
        I_KH = self._I - dot(K, H)
        P = dot(dot(I_KH, P), I_KH.T) + dot(dot(K, R), K.T)
        return (x, P)

    def residual_of(self, z):
        """
        Returns the residual for the given measurement (z). Does not alter
        the state of the filter.
        """
        z = reshape_z(z, self.dim_z, self.x.ndim)
        return z - dot(self.H, self.x_prior)

    def measurement_of_state(self, x):
        """
        Helper function that converts a state into a measurement.
        Parameters
        ----------
        x : np.array
            kalman state vector
        Returns
        -------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.
        """
        return dot(self.H, x)

    @property
    def log_likelihood(self):
        """
        log-likelihood of the last measurement.
        """
        if self._log_likelihood is None:
            self._log_likelihood = logpdf(x=self.y, cov=self.S)
        return self._log_likelihood

    @property
    def likelihood(self):
        """
        Computed from the log-likelihood. The log-likelihood can be very
        small,  meaning a large negative value such as -28000. Taking the
        exp() of that results in 0.0, which can break typical algorithms
        which multiply by this value, so by default we always return a
        number >= sys.float_info.min.
        """
        if self._likelihood is None:
            self._likelihood = exp(self.log_likelihood)
            if self._likelihood == 0:
                self._likelihood = sys.float_info.min
        return self._likelihood

    @property
    def mahalanobis(self):
        """ "
        Mahalanobis distance of measurement. E.g. 3 means measurement
        was 3 standard deviations away from the predicted value.
        Returns
        -------
        mahalanobis : float
        """
        if self._mahalanobis is None:
            self._mahalanobis = sqrt(float(dot(dot(self.y.T, self.SI), self.y)))
        return self._mahalanobis

    @property
    def alpha(self):
        """
        Fading memory setting. 1.0 gives the normal Kalman filter, and
        values slightly larger than 1.0 (such as 1.02) give a fading
        memory effect - previous measurements have less influence on the
        filter's estimates. This formulation of the Fading memory filter
        (there are many) is due to Dan Simon [1]_.
        """
        return self._alpha_sq ** 0.5

    def log_likelihood_of(self, z):
        """
        log likelihood of the measurement `z`. This should only be called
        after a call to update(). Calling after predict() will yield an
        incorrect result."""
        if z is None:
            return log(sys.float_info.min)
        return logpdf(z, dot(self.H, self.x), self.S)

    @alpha.setter
    def alpha(self, value):
        if not np.isscalar(value) or value < 1:
            raise ValueError('alpha must be a float greater than 1')
        self._alpha_sq = value ** 2

    def __repr__(self):
        return '\n'.join(['KalmanFilter object', pretty_str('dim_x', self.dim_x), pretty_str('dim_z', self.dim_z), pretty_str('dim_u', self.dim_u), pretty_str('x', self.x), pretty_str('P', self.P), pretty_str('x_prior', self.x_prior), pretty_str('P_prior', self.P_prior), pretty_str('x_post', self.x_post), pretty_str('P_post', self.P_post), pretty_str('F', self.F), pretty_str('Q', self.Q), pretty_str('R', self.R), pretty_str('H', self.H), pretty_str('K', self.K), pretty_str('y', self.y), pretty_str('S', self.S), pretty_str('SI', self.SI), pretty_str('M', self.M), pretty_str('B', self.B), pretty_str('z', self.z), pretty_str('log-likelihood', self.log_likelihood), pretty_str('likelihood', self.likelihood), pretty_str('mahalanobis', self.mahalanobis), pretty_str('alpha', self.alpha), pretty_str('inv', self.inv)])

    def test_matrix_dimensions(self, z=None, H=None, R=None, F=None, Q=None):
        """
        Performs a series of asserts to check that the size of everything
        is what it should be. This can help you debug problems in your design.
        If you pass in H, R, F, Q those will be used instead of this object's
        value for those matrices.
        Testing `z` (the measurement) is problamatic. x is a vector, and can be
        implemented as either a 1D array or as a nx1 column vector. Thus Hx
        can be of different shapes. Then, if Hx is a single value, it can
        be either a 1D array or 2D vector. If either is true, z can reasonably
        be a scalar (either '3' or np.array('3') are scalars under this
        definition), a 1D, 1 element array, or a 2D, 1 element array. You are
        allowed to pass in any combination that works.
        """
        if H is None:
            H = self.H
        if R is None:
            R = self.R
        if F is None:
            F = self.F
        if Q is None:
            Q = self.Q
        x = self.x
        P = self.P
        assert x.ndim == 1 or x.ndim == 2, 'x must have one or two dimensions, but has {}'.format(x.ndim)
        if x.ndim == 1:
            assert x.shape[0] == self.dim_x, 'Shape of x must be ({},{}), but is {}'.format(self.dim_x, 1, x.shape)
        else:
            assert x.shape == (self.dim_x, 1), 'Shape of x must be ({},{}), but is {}'.format(self.dim_x, 1, x.shape)
        assert P.shape == (self.dim_x, self.dim_x), 'Shape of P must be ({},{}), but is {}'.format(self.dim_x, self.dim_x, P.shape)
        assert Q.shape == (self.dim_x, self.dim_x), 'Shape of Q must be ({},{}), but is {}'.format(self.dim_x, self.dim_x, P.shape)
        assert F.shape == (self.dim_x, self.dim_x), 'Shape of F must be ({},{}), but is {}'.format(self.dim_x, self.dim_x, F.shape)
        assert np.ndim(H) == 2, 'Shape of H must be (dim_z, {}), but is {}'.format(P.shape[0], shape(H))
        assert H.shape[1] == P.shape[0], 'Shape of H must be (dim_z, {}), but is {}'.format(P.shape[0], H.shape)
        hph_shape = (H.shape[0], H.shape[0])
        r_shape = shape(R)
        if H.shape[0] == 1:
            assert r_shape in [(), (1,), (1, 1)], 'R must be scalar or one element array, but is shaped {}'.format(r_shape)
        else:
            assert r_shape == hph_shape, 'shape of R should be {} but it is {}'.format(hph_shape, r_shape)
        if z is not None:
            z_shape = shape(z)
        else:
            z_shape = (self.dim_z, 1)
        Hx = dot(H, x)
        if z_shape == ():
            assert Hx.ndim == 1 or shape(Hx) == (1, 1), 'shape of z should be {}, not {} for the given H'.format(shape(Hx), z_shape)
        elif shape(Hx) == (1,):
            assert z_shape[0] == 1, 'Shape of z must be {} for the given H'.format(shape(Hx))
        else:
            assert z_shape == shape(Hx) or (len(z_shape) == 1 and shape(Hx) == (z_shape[0], 1)), 'shape of z should be {}, not {} for the given H'.format(shape(Hx), z_shape)
        if np.ndim(Hx) > 1 and shape(Hx) != (1, 1):
            assert shape(Hx) == z_shape, 'shape of z should be {} for the given H, but it is {}'.format(shape(Hx), z_shape)

def freeze(self):
    """
        Save the parameters before non-observation forward
        """
    self.attr_saved = deepcopy(self.__dict__)

def __repr__(self):
    return '\n'.join(['KalmanFilter object', pretty_str('dim_x', self.dim_x), pretty_str('dim_z', self.dim_z), pretty_str('dim_u', self.dim_u), pretty_str('x', self.x), pretty_str('P', self.P), pretty_str('x_prior', self.x_prior), pretty_str('P_prior', self.P_prior), pretty_str('x_post', self.x_post), pretty_str('P_post', self.P_post), pretty_str('F', self.F), pretty_str('Q', self.Q), pretty_str('R', self.R), pretty_str('H', self.H), pretty_str('K', self.K), pretty_str('y', self.y), pretty_str('S', self.S), pretty_str('SI', self.SI), pretty_str('M', self.M), pretty_str('B', self.B), pretty_str('z', self.z), pretty_str('log-likelihood', self.log_likelihood), pretty_str('likelihood', self.likelihood), pretty_str('mahalanobis', self.mahalanobis), pretty_str('alpha', self.alpha), pretty_str('inv', self.inv)])

class KalmanFilterNew(object):
    """ Implements a Kalman filter. You are responsible for setting the
    various state variables to reasonable values; the defaults  will
    not give you a functional filter.
    For now the best documentation is my free book Kalman and Bayesian
    Filters in Python [2]_. The test files in this directory also give you a
    basic idea of use, albeit without much description.
    In brief, you will first construct this object, specifying the size of
    the state vector with dim_x and the size of the measurement vector that
    you will be using with dim_z. These are mostly used to perform size checks
    when you assign values to the various matrices. For example, if you
    specified dim_z=2 and then try to assign a 3x3 matrix to R (the
    measurement noise matrix you will get an assert exception because R
    should be 2x2. (If for whatever reason you need to alter the size of
    things midstream just use the underscore version of the matrices to
    assign directly: your_filter._R = a_3x3_matrix.)
    After construction the filter will have default matrices created for you,
    but you must specify the values for each. It’s usually easiest to just
    overwrite them rather than assign to each element yourself. This will be
    clearer in the example below. All are of type numpy.array.
    Examples
    --------
    Here is a filter that tracks position and velocity using a sensor that only
    reads position.
    First construct the object with the required dimensionality. Here the state
    (`dim_x`) has 2 coefficients (position and velocity), and the measurement
    (`dim_z`) has one. In FilterPy `x` is the state, `z` is the measurement.
    .. code::
        from filterpy.kalman import KalmanFilter
        f = KalmanFilter (dim_x=2, dim_z=1)
    Assign the initial value for the state (position and velocity). You can do this
    with a two dimensional array like so:
        .. code::
            f.x = np.array([[2.],    # position
                            [0.]])   # velocity
    or just use a one dimensional array, which I prefer doing.
    .. code::
        f.x = np.array([2., 0.])
    Define the state transition matrix:
        .. code::
            f.F = np.array([[1.,1.],
                            [0.,1.]])
    Define the measurement function. Here we need to convert a position-velocity
    vector into just a position vector, so we use:
        .. code::
        f.H = np.array([[1., 0.]])
    Define the state's covariance matrix P. 
    .. code::
        f.P = np.array([[1000.,    0.],
                        [   0., 1000.] ])
    Now assign the measurement noise. Here the dimension is 1x1, so I can
    use a scalar
    .. code::
        f.R = 5
    I could have done this instead:
    .. code::
        f.R = np.array([[5.]])
    Note that this must be a 2 dimensional array.
    Finally, I will assign the process noise. Here I will take advantage of
    another FilterPy library function:
    .. code::
        from filterpy.common import Q_discrete_white_noise
        f.Q = Q_discrete_white_noise(dim=2, dt=0.1, var=0.13)
    Now just perform the standard predict/update loop:
    .. code::
        while some_condition_is_true:
            z = get_sensor_reading()
            f.predict()
            f.update(z)
            do_something_with_estimate (f.x)
    **Procedural Form**
    This module also contains stand alone functions to perform Kalman filtering.
    Use these if you are not a fan of objects.
    **Example**
    .. code::
        while True:
            z, R = read_sensor()
            x, P = predict(x, P, F, Q)
            x, P = update(x, P, z, R, H)
    See my book Kalman and Bayesian Filters in Python [2]_.
    You will have to set the following attributes after constructing this
    object for the filter to perform properly. Please note that there are
    various checks in place to ensure that you have made everything the
    'correct' size. However, it is possible to provide incorrectly sized
    arrays such that the linear algebra can not perform an operation.
    It can also fail silently - you can end up with matrices of a size that
    allows the linear algebra to work, but are the wrong shape for the problem
    you are trying to solve.
    Parameters
    ----------
    dim_x : int
        Number of state variables for the Kalman filter. For example, if
        you are tracking the position and velocity of an object in two
        dimensions, dim_x would be 4.
        This is used to set the default size of P, Q, and u
    dim_z : int
        Number of of measurement inputs. For example, if the sensor
        provides you with position in (x,y), dim_z would be 2.
    dim_u : int (optional)
        size of the control input, if it is being used.
        Default value of 0 indicates it is not used.
    compute_log_likelihood : bool (default = True)
        Computes log likelihood by default, but this can be a slow
        computation, so if you never use it you can turn this computation
        off.
    Attributes
    ----------
    x : numpy.array(dim_x, 1)
        Current state estimate. Any call to update() or predict() updates
        this variable.
    P : numpy.array(dim_x, dim_x)
        Current state covariance matrix. Any call to update() or predict()
        updates this variable.
    x_prior : numpy.array(dim_x, 1)
        Prior (predicted) state estimate. The *_prior and *_post attributes
        are for convenience; they store the  prior and posterior of the
        current epoch. Read Only.
    P_prior : numpy.array(dim_x, dim_x)
        Prior (predicted) state covariance matrix. Read Only.
    x_post : numpy.array(dim_x, 1)
        Posterior (updated) state estimate. Read Only.
    P_post : numpy.array(dim_x, dim_x)
        Posterior (updated) state covariance matrix. Read Only.
    z : numpy.array
        Last measurement used in update(). Read only.
    R : numpy.array(dim_z, dim_z)
        Measurement noise covariance matrix. Also known as the
        observation covariance.
    Q : numpy.array(dim_x, dim_x)
        Process noise covariance matrix. Also known as the transition
        covariance.
    F : numpy.array()
        State Transition matrix. Also known as `A` in some formulation.
    H : numpy.array(dim_z, dim_x)
        Measurement function. Also known as the observation matrix, or as `C`.
    y : numpy.array
        Residual of the update step. Read only.
    K : numpy.array(dim_x, dim_z)
        Kalman gain of the update step. Read only.
    S :  numpy.array
        System uncertainty (P projected to measurement space). Read only.
    SI :  numpy.array
        Inverse system uncertainty. Read only.
    log_likelihood : float
        log-likelihood of the last measurement. Read only.
    likelihood : float
        likelihood of last measurement. Read only.
        Computed from the log-likelihood. The log-likelihood can be very
        small,  meaning a large negative value such as -28000. Taking the
        exp() of that results in 0.0, which can break typical algorithms
        which multiply by this value, so by default we always return a
        number >= sys.float_info.min.
    mahalanobis : float
        mahalanobis distance of the innovation. Read only.
    inv : function, default numpy.linalg.inv
        If you prefer another inverse function, such as the Moore-Penrose
        pseudo inverse, set it to that instead: kf.inv = np.linalg.pinv
        This is only used to invert self.S. If you know it is diagonal, you
        might choose to set it to filterpy.common.inv_diagonal, which is
        several times faster than numpy.linalg.inv for diagonal matrices.
    alpha : float
        Fading memory setting. 1.0 gives the normal Kalman filter, and
        values slightly larger than 1.0 (such as 1.02) give a fading
        memory effect - previous measurements have less influence on the
        filter's estimates. This formulation of the Fading memory filter
        (there are many) is due to Dan Simon [1]_.
    References
    ----------
    .. [1] Dan Simon. "Optimal State Estimation." John Wiley & Sons.
       p. 208-212. (2006)
    .. [2] Roger Labbe. "Kalman and Bayesian Filters in Python"
       https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python
    """

    def __init__(self, dim_x, dim_z, dim_u=0):
        if dim_x < 1:
            raise ValueError('dim_x must be 1 or greater')
        if dim_z < 1:
            raise ValueError('dim_z must be 1 or greater')
        if dim_u < 0:
            raise ValueError('dim_u must be 0 or greater')
        self.dim_x = dim_x
        self.dim_z = dim_z
        self.dim_u = dim_u
        self.x = zeros((dim_x, 1))
        self.P = eye(dim_x)
        self.Q = eye(dim_x)
        self.B = None
        self.F = eye(dim_x)
        self.H = zeros((dim_z, dim_x))
        self.R = eye(dim_z)
        self._alpha_sq = 1.0
        self.M = np.zeros((dim_x, dim_z))
        self.z = np.array([[None] * self.dim_z]).T
        self.K = np.zeros((dim_x, dim_z))
        self.y = zeros((dim_z, 1))
        self.S = np.zeros((dim_z, dim_z))
        self.SI = np.zeros((dim_z, dim_z))
        self._I = np.eye(dim_x)
        self.x_prior = self.x.copy()
        self.P_prior = self.P.copy()
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()
        self._log_likelihood = log(sys.float_info.min)
        self._likelihood = sys.float_info.min
        self._mahalanobis = None
        self.history_obs = []
        self.inv = np.linalg.inv
        self.attr_saved = None
        self.observed = False

    def predict(self, u=None, B=None, F=None, Q=None):
        """
        Predict next state (prior) using the Kalman filter state propagation
        equations.
        Parameters
        ----------
        u : np.array, default 0
            Optional control vector.
        B : np.array(dim_x, dim_u), or None
            Optional control transition matrix; a value of None
            will cause the filter to use `self.B`.
        F : np.array(dim_x, dim_x), or None
            Optional state transition matrix; a value of None
            will cause the filter to use `self.F`.
        Q : np.array(dim_x, dim_x), scalar, or None
            Optional process noise matrix; a value of None will cause the
            filter to use `self.Q`.
        """
        if B is None:
            B = self.B
        if F is None:
            F = self.F
        if Q is None:
            Q = self.Q
        elif isscalar(Q):
            Q = eye(self.dim_x) * Q
        if B is not None and u is not None:
            self.x = dot(F, self.x) + dot(B, u)
        else:
            self.x = dot(F, self.x)
        self.P = self._alpha_sq * dot(dot(F, self.P), F.T) + Q
        self.x_prior = self.x.copy()
        self.P_prior = self.P.copy()

    def freeze(self):
        """
            Save the parameters before non-observation forward
        """
        self.attr_saved = deepcopy(self.__dict__)

    def unfreeze(self):
        if self.attr_saved is not None:
            new_history = deepcopy(self.history_obs)
            self.__dict__ = self.attr_saved
            self.history_obs = self.history_obs[:-1]
            occur = [int(d is None) for d in new_history]
            indices = np.where(np.array(occur) == 0)[0]
            index1 = indices[-2]
            index2 = indices[-1]
            box1 = new_history[index1]
            x1, y1, s1, r1 = box1
            w1 = np.sqrt(s1 * r1)
            h1 = np.sqrt(s1 / r1)
            box2 = new_history[index2]
            x2, y2, s2, r2 = box2
            w2 = np.sqrt(s2 * r2)
            h2 = np.sqrt(s2 / r2)
            time_gap = index2 - index1
            dx = (x2 - x1) / time_gap
            dy = (y2 - y1) / time_gap
            dw = (w2 - w1) / time_gap
            dh = (h2 - h1) / time_gap
            for i in range(index2 - index1):
                '\n                    The default virtual trajectory generation is by linear\n                    motion (constant speed hypothesis), you could modify this \n                    part to implement your own. \n                '
                x = x1 + (i + 1) * dx
                y = y1 + (i + 1) * dy
                w = w1 + (i + 1) * dw
                h = h1 + (i + 1) * dh
                s = w * h
                r = w / float(h)
                new_box = np.array([x, y, s, r]).reshape((4, 1))
                '\n                    I still use predict-update loop here to refresh the parameters,\n                    but this can be faster by directly modifying the internal parameters\n                    as suggested in the paper. I keep this naive but slow way for \n                    easy read and understanding\n                '
                self.update(new_box)
                if not i == index2 - index1 - 1:
                    self.predict()

    def update(self, z, R=None, H=None):
        """
        Add a new measurement (z) to the Kalman filter.
        If z is None, nothing is computed. However, x_post and P_post are
        updated with the prior (x_prior, P_prior), and self.z is set to None.
        Parameters
        ----------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.
            If you pass in a value of H, z must be a column vector the
            of the correct size.
        R : np.array, scalar, or None
            Optionally provide R to override the measurement noise for this
            one call, otherwise  self.R will be used.
        H : np.array, or None
            Optionally provide H to override the measurement function for this
            one call, otherwise self.H will be used.
        """
        self._log_likelihood = None
        self._likelihood = None
        self._mahalanobis = None
        self.history_obs.append(z)
        if z is None:
            if self.observed:
                '\n                    Got no observation so freeze the current parameters for future\n                    potential online smoothing.\n                '
                self.freeze()
            self.observed = False
            self.z = np.array([[None] * self.dim_z]).T
            self.x_post = self.x.copy()
            self.P_post = self.P.copy()
            self.y = zeros((self.dim_z, 1))
            return
        if not self.observed:
            '\n                Get observation, use online smoothing to re-update parameters\n            '
            self.unfreeze()
        self.observed = True
        if R is None:
            R = self.R
        elif isscalar(R):
            R = eye(self.dim_z) * R
        if H is None:
            z = reshape_z(z, self.dim_z, self.x.ndim)
            H = self.H
        self.y = z - dot(H, self.x)
        PHT = dot(self.P, H.T)
        self.S = dot(H, PHT) + R
        self.SI = self.inv(self.S)
        self.K = dot(PHT, self.SI)
        self.x = self.x + dot(self.K, self.y)
        I_KH = self._I - dot(self.K, H)
        self.P = dot(dot(I_KH, self.P), I_KH.T) + dot(dot(self.K, R), self.K.T)
        self.z = deepcopy(z)
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()

    def predict_steadystate(self, u=0, B=None):
        """
        Predict state (prior) using the Kalman filter state propagation
        equations. Only x is updated, P is left unchanged. See
        update_steadstate() for a longer explanation of when to use this
        method.
        Parameters
        ----------
        u : np.array
            Optional control vector. If non-zero, it is multiplied by B
            to create the control input into the system.
        B : np.array(dim_x, dim_u), or None
            Optional control transition matrix; a value of None
            will cause the filter to use `self.B`.
        """
        if B is None:
            B = self.B
        if B is not None:
            self.x = dot(self.F, self.x) + dot(B, u)
        else:
            self.x = dot(self.F, self.x)
        self.x_prior = self.x.copy()
        self.P_prior = self.P.copy()

    def update_steadystate(self, z):
        """
        Add a new measurement (z) to the Kalman filter without recomputing
        the Kalman gain K, the state covariance P, or the system
        uncertainty S.
        You can use this for LTI systems since the Kalman gain and covariance
        converge to a fixed value. Precompute these and assign them explicitly,
        or run the Kalman filter using the normal predict()/update(0 cycle
        until they converge.
        The main advantage of this call is speed. We do significantly less
        computation, notably avoiding a costly matrix inversion.
        Use in conjunction with predict_steadystate(), otherwise P will grow
        without bound.
        Parameters
        ----------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.
        Examples
        --------
        >>> cv = kinematic_kf(dim=3, order=2) # 3D const velocity filter
        >>> # let filter converge on representative data, then save k and P
        >>> for i in range(100):
        >>>     cv.predict()
        >>>     cv.update([i, i, i])
        >>> saved_k = np.copy(cv.K)
        >>> saved_P = np.copy(cv.P)
        later on:
        >>> cv = kinematic_kf(dim=3, order=2) # 3D const velocity filter
        >>> cv.K = np.copy(saved_K)
        >>> cv.P = np.copy(saved_P)
        >>> for i in range(100):
        >>>     cv.predict_steadystate()
        >>>     cv.update_steadystate([i, i, i])
        """
        self._log_likelihood = None
        self._likelihood = None
        self._mahalanobis = None
        if z is None:
            self.z = np.array([[None] * self.dim_z]).T
            self.x_post = self.x.copy()
            self.P_post = self.P.copy()
            self.y = zeros((self.dim_z, 1))
            return
        z = reshape_z(z, self.dim_z, self.x.ndim)
        self.y = z - dot(self.H, self.x)
        self.x = self.x + dot(self.K, self.y)
        self.z = deepcopy(z)
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()
        self._log_likelihood = None
        self._likelihood = None
        self._mahalanobis = None

    def update_correlated(self, z, R=None, H=None):
        """ Add a new measurement (z) to the Kalman filter assuming that
        process noise and measurement noise are correlated as defined in
        the `self.M` matrix.
        A partial derivation can be found in [1]
        If z is None, nothing is changed.
        Parameters
        ----------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.
        R : np.array, scalar, or None
            Optionally provide R to override the measurement noise for this
            one call, otherwise  self.R will be used.
        H : np.array,  or None
            Optionally provide H to override the measurement function for this
            one call, otherwise  self.H will be used.
        References
        ----------
        .. [1] Bulut, Y. (2011). Applied Kalman filter theory (Doctoral dissertation, Northeastern University).
               http://people.duke.edu/~hpgavin/SystemID/References/Balut-KalmanFilter-PhD-NEU-2011.pdf
        """
        self._log_likelihood = None
        self._likelihood = None
        self._mahalanobis = None
        if z is None:
            self.z = np.array([[None] * self.dim_z]).T
            self.x_post = self.x.copy()
            self.P_post = self.P.copy()
            self.y = zeros((self.dim_z, 1))
            return
        if R is None:
            R = self.R
        elif isscalar(R):
            R = eye(self.dim_z) * R
        if H is None:
            z = reshape_z(z, self.dim_z, self.x.ndim)
            H = self.H
        if self.x.ndim == 1 and shape(z) == (1, 1):
            z = z[0]
        if shape(z) == ():
            z = np.asarray([z])
        self.y = z - dot(H, self.x)
        PHT = dot(self.P, H.T)
        self.S = dot(H, PHT) + dot(H, self.M) + dot(self.M.T, H.T) + R
        self.SI = self.inv(self.S)
        self.K = dot(PHT + self.M, self.SI)
        self.x = self.x + dot(self.K, self.y)
        self.P = self.P - dot(self.K, dot(H, self.P) + self.M.T)
        self.z = deepcopy(z)
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()

    def batch_filter(self, zs, Fs=None, Qs=None, Hs=None, Rs=None, Bs=None, us=None, update_first=False, saver=None):
        """ Batch processes a sequences of measurements.
        Parameters
        ----------
        zs : list-like
            list of measurements at each time step `self.dt`. Missing
            measurements must be represented by `None`.
        Fs : None, list-like, default=None
            optional value or list of values to use for the state transition
            matrix F.
            If Fs is None then self.F is used for all epochs.
            Otherwise it must contain a list-like list of F's, one for
            each epoch.  This allows you to have varying F per epoch.
        Qs : None, np.array or list-like, default=None
            optional value or list of values to use for the process error
            covariance Q.
            If Qs is None then self.Q is used for all epochs.
            Otherwise it must contain a list-like list of Q's, one for
            each epoch.  This allows you to have varying Q per epoch.
        Hs : None, np.array or list-like, default=None
            optional list of values to use for the measurement matrix H.
            If Hs is None then self.H is used for all epochs.
            If Hs contains a single matrix, then it is used as H for all
            epochs.
            Otherwise it must contain a list-like list of H's, one for
            each epoch.  This allows you to have varying H per epoch.
        Rs : None, np.array or list-like, default=None
            optional list of values to use for the measurement error
            covariance R.
            If Rs is None then self.R is used for all epochs.
            Otherwise it must contain a list-like list of R's, one for
            each epoch.  This allows you to have varying R per epoch.
        Bs : None, np.array or list-like, default=None
            optional list of values to use for the control transition matrix B.
            If Bs is None then self.B is used for all epochs.
            Otherwise it must contain a list-like list of B's, one for
            each epoch.  This allows you to have varying B per epoch.
        us : None, np.array or list-like, default=None
            optional list of values to use for the control input vector;
            If us is None then None is used for all epochs (equivalent to 0,
            or no control input).
            Otherwise it must contain a list-like list of u's, one for
            each epoch.
       update_first : bool, optional, default=False
            controls whether the order of operations is update followed by
            predict, or predict followed by update. Default is predict->update.
        saver : filterpy.common.Saver, optional
            filterpy.common.Saver object. If provided, saver.save() will be
            called after every epoch
        Returns
        -------
        means : np.array((n,dim_x,1))
            array of the state for each time step after the update. Each entry
            is an np.array. In other words `means[k,:]` is the state at step
            `k`.
        covariance : np.array((n,dim_x,dim_x))
            array of the covariances for each time step after the update.
            In other words `covariance[k,:,:]` is the covariance at step `k`.
        means_predictions : np.array((n,dim_x,1))
            array of the state for each time step after the predictions. Each
            entry is an np.array. In other words `means[k,:]` is the state at
            step `k`.
        covariance_predictions : np.array((n,dim_x,dim_x))
            array of the covariances for each time step after the prediction.
            In other words `covariance[k,:,:]` is the covariance at step `k`.
        Examples
        --------
        .. code-block:: Python
            # this example demonstrates tracking a measurement where the time
            # between measurement varies, as stored in dts. This requires
            # that F be recomputed for each epoch. The output is then smoothed
            # with an RTS smoother.
            zs = [t + random.randn()*4 for t in range (40)]
            Fs = [np.array([[1., dt], [0, 1]] for dt in dts]
            (mu, cov, _, _) = kf.batch_filter(zs, Fs=Fs)
            (xs, Ps, Ks, Pps) = kf.rts_smoother(mu, cov, Fs=Fs)
        """
        n = np.size(zs, 0)
        if Fs is None:
            Fs = [self.F] * n
        if Qs is None:
            Qs = [self.Q] * n
        if Hs is None:
            Hs = [self.H] * n
        if Rs is None:
            Rs = [self.R] * n
        if Bs is None:
            Bs = [self.B] * n
        if us is None:
            us = [0] * n
        if self.x.ndim == 1:
            means = zeros((n, self.dim_x))
            means_p = zeros((n, self.dim_x))
        else:
            means = zeros((n, self.dim_x, 1))
            means_p = zeros((n, self.dim_x, 1))
        covariances = zeros((n, self.dim_x, self.dim_x))
        covariances_p = zeros((n, self.dim_x, self.dim_x))
        if update_first:
            for i, (z, F, Q, H, R, B, u) in enumerate(zip(zs, Fs, Qs, Hs, Rs, Bs, us)):
                self.update(z, R=R, H=H)
                means[i, :] = self.x
                covariances[i, :, :] = self.P
                self.predict(u=u, B=B, F=F, Q=Q)
                means_p[i, :] = self.x
                covariances_p[i, :, :] = self.P
                if saver is not None:
                    saver.save()
        else:
            for i, (z, F, Q, H, R, B, u) in enumerate(zip(zs, Fs, Qs, Hs, Rs, Bs, us)):
                self.predict(u=u, B=B, F=F, Q=Q)
                means_p[i, :] = self.x
                covariances_p[i, :, :] = self.P
                self.update(z, R=R, H=H)
                means[i, :] = self.x
                covariances[i, :, :] = self.P
                if saver is not None:
                    saver.save()
        return (means, covariances, means_p, covariances_p)

    def rts_smoother(self, Xs, Ps, Fs=None, Qs=None, inv=np.linalg.inv):
        """
        Runs the Rauch-Tung-Striebel Kalman smoother on a set of
        means and covariances computed by a Kalman filter. The usual input
        would come from the output of `KalmanFilter.batch_filter()`.
        Parameters
        ----------
        Xs : numpy.array
           array of the means (state variable x) of the output of a Kalman
           filter.
        Ps : numpy.array
            array of the covariances of the output of a kalman filter.
        Fs : list-like collection of numpy.array, optional
            State transition matrix of the Kalman filter at each time step.
            Optional, if not provided the filter's self.F will be used
        Qs : list-like collection of numpy.array, optional
            Process noise of the Kalman filter at each time step. Optional,
            if not provided the filter's self.Q will be used
        inv : function, default numpy.linalg.inv
            If you prefer another inverse function, such as the Moore-Penrose
            pseudo inverse, set it to that instead: kf.inv = np.linalg.pinv
        Returns
        -------
        x : numpy.ndarray
           smoothed means
        P : numpy.ndarray
           smoothed state covariances
        K : numpy.ndarray
            smoother gain at each step
        Pp : numpy.ndarray
           Predicted state covariances
        Examples
        --------
        .. code-block:: Python
            zs = [t + random.randn()*4 for t in range (40)]
            (mu, cov, _, _) = kalman.batch_filter(zs)
            (x, P, K, Pp) = rts_smoother(mu, cov, kf.F, kf.Q)
        """
        if len(Xs) != len(Ps):
            raise ValueError('length of Xs and Ps must be the same')
        n = Xs.shape[0]
        dim_x = Xs.shape[1]
        if Fs is None:
            Fs = [self.F] * n
        if Qs is None:
            Qs = [self.Q] * n
        K = zeros((n, dim_x, dim_x))
        x, P, Pp = (Xs.copy(), Ps.copy(), Ps.copy())
        for k in range(n - 2, -1, -1):
            Pp[k] = dot(dot(Fs[k + 1], P[k]), Fs[k + 1].T) + Qs[k + 1]
            K[k] = dot(dot(P[k], Fs[k + 1].T), inv(Pp[k]))
            x[k] += dot(K[k], x[k + 1] - dot(Fs[k + 1], x[k]))
            P[k] += dot(dot(K[k], P[k + 1] - Pp[k]), K[k].T)
        return (x, P, K, Pp)

    def get_prediction(self, u=None, B=None, F=None, Q=None):
        """
        Predict next state (prior) using the Kalman filter state propagation
        equations and returns it without modifying the object.
        Parameters
        ----------
        u : np.array, default 0
            Optional control vector.
        B : np.array(dim_x, dim_u), or None
            Optional control transition matrix; a value of None
            will cause the filter to use `self.B`.
        F : np.array(dim_x, dim_x), or None
            Optional state transition matrix; a value of None
            will cause the filter to use `self.F`.
        Q : np.array(dim_x, dim_x), scalar, or None
            Optional process noise matrix; a value of None will cause the
            filter to use `self.Q`.
        Returns
        -------
        (x, P) : tuple
            State vector and covariance array of the prediction.
        """
        if B is None:
            B = self.B
        if F is None:
            F = self.F
        if Q is None:
            Q = self.Q
        elif isscalar(Q):
            Q = eye(self.dim_x) * Q
        if B is not None and u is not None:
            x = dot(F, self.x) + dot(B, u)
        else:
            x = dot(F, self.x)
        P = self._alpha_sq * dot(dot(F, self.P), F.T) + Q
        return (x, P)

    def get_update(self, z=None):
        """
        Computes the new estimate based on measurement `z` and returns it
        without altering the state of the filter.
        Parameters
        ----------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.
        Returns
        -------
        (x, P) : tuple
            State vector and covariance array of the update.
       """
        if z is None:
            return (self.x, self.P)
        z = reshape_z(z, self.dim_z, self.x.ndim)
        R = self.R
        H = self.H
        P = self.P
        x = self.x
        y = z - dot(H, x)
        PHT = dot(P, H.T)
        S = dot(H, PHT) + R
        K = dot(PHT, self.inv(S))
        x = x + dot(K, y)
        I_KH = self._I - dot(K, H)
        P = dot(dot(I_KH, P), I_KH.T) + dot(dot(K, R), K.T)
        return (x, P)

    def residual_of(self, z):
        """
        Returns the residual for the given measurement (z). Does not alter
        the state of the filter.
        """
        z = reshape_z(z, self.dim_z, self.x.ndim)
        return z - dot(self.H, self.x_prior)

    def measurement_of_state(self, x):
        """
        Helper function that converts a state into a measurement.
        Parameters
        ----------
        x : np.array
            kalman state vector
        Returns
        -------
        z : (dim_z, 1): array_like
            measurement for this update. z can be a scalar if dim_z is 1,
            otherwise it must be convertible to a column vector.
        """
        return dot(self.H, x)

    @property
    def log_likelihood(self):
        """
        log-likelihood of the last measurement.
        """
        if self._log_likelihood is None:
            self._log_likelihood = logpdf(x=self.y, cov=self.S)
        return self._log_likelihood

    @property
    def likelihood(self):
        """
        Computed from the log-likelihood. The log-likelihood can be very
        small,  meaning a large negative value such as -28000. Taking the
        exp() of that results in 0.0, which can break typical algorithms
        which multiply by this value, so by default we always return a
        number >= sys.float_info.min.
        """
        if self._likelihood is None:
            self._likelihood = exp(self.log_likelihood)
            if self._likelihood == 0:
                self._likelihood = sys.float_info.min
        return self._likelihood

    @property
    def mahalanobis(self):
        """"
        Mahalanobis distance of measurement. E.g. 3 means measurement
        was 3 standard deviations away from the predicted value.
        Returns
        -------
        mahalanobis : float
        """
        if self._mahalanobis is None:
            self._mahalanobis = sqrt(float(dot(dot(self.y.T, self.SI), self.y)))
        return self._mahalanobis

    @property
    def alpha(self):
        """
        Fading memory setting. 1.0 gives the normal Kalman filter, and
        values slightly larger than 1.0 (such as 1.02) give a fading
        memory effect - previous measurements have less influence on the
        filter's estimates. This formulation of the Fading memory filter
        (there are many) is due to Dan Simon [1]_.
        """
        return self._alpha_sq ** 0.5

    def log_likelihood_of(self, z):
        """
        log likelihood of the measurement `z`. This should only be called
        after a call to update(). Calling after predict() will yield an
        incorrect result."""
        if z is None:
            return log(sys.float_info.min)
        return logpdf(z, dot(self.H, self.x), self.S)

    @alpha.setter
    def alpha(self, value):
        if not np.isscalar(value) or value < 1:
            raise ValueError('alpha must be a float greater than 1')
        self._alpha_sq = value ** 2

    def __repr__(self):
        return '\n'.join(['KalmanFilter object', pretty_str('dim_x', self.dim_x), pretty_str('dim_z', self.dim_z), pretty_str('dim_u', self.dim_u), pretty_str('x', self.x), pretty_str('P', self.P), pretty_str('x_prior', self.x_prior), pretty_str('P_prior', self.P_prior), pretty_str('x_post', self.x_post), pretty_str('P_post', self.P_post), pretty_str('F', self.F), pretty_str('Q', self.Q), pretty_str('R', self.R), pretty_str('H', self.H), pretty_str('K', self.K), pretty_str('y', self.y), pretty_str('S', self.S), pretty_str('SI', self.SI), pretty_str('M', self.M), pretty_str('B', self.B), pretty_str('z', self.z), pretty_str('log-likelihood', self.log_likelihood), pretty_str('likelihood', self.likelihood), pretty_str('mahalanobis', self.mahalanobis), pretty_str('alpha', self.alpha), pretty_str('inv', self.inv)])

    def test_matrix_dimensions(self, z=None, H=None, R=None, F=None, Q=None):
        """
        Performs a series of asserts to check that the size of everything
        is what it should be. This can help you debug problems in your design.
        If you pass in H, R, F, Q those will be used instead of this object's
        value for those matrices.
        Testing `z` (the measurement) is problamatic. x is a vector, and can be
        implemented as either a 1D array or as a nx1 column vector. Thus Hx
        can be of different shapes. Then, if Hx is a single value, it can
        be either a 1D array or 2D vector. If either is true, z can reasonably
        be a scalar (either '3' or np.array('3') are scalars under this
        definition), a 1D, 1 element array, or a 2D, 1 element array. You are
        allowed to pass in any combination that works.
        """
        if H is None:
            H = self.H
        if R is None:
            R = self.R
        if F is None:
            F = self.F
        if Q is None:
            Q = self.Q
        x = self.x
        P = self.P
        assert x.ndim == 1 or x.ndim == 2, 'x must have one or two dimensions, but has {}'.format(x.ndim)
        if x.ndim == 1:
            assert x.shape[0] == self.dim_x, 'Shape of x must be ({},{}), but is {}'.format(self.dim_x, 1, x.shape)
        else:
            assert x.shape == (self.dim_x, 1), 'Shape of x must be ({},{}), but is {}'.format(self.dim_x, 1, x.shape)
        assert P.shape == (self.dim_x, self.dim_x), 'Shape of P must be ({},{}), but is {}'.format(self.dim_x, self.dim_x, P.shape)
        assert Q.shape == (self.dim_x, self.dim_x), 'Shape of Q must be ({},{}), but is {}'.format(self.dim_x, self.dim_x, P.shape)
        assert F.shape == (self.dim_x, self.dim_x), 'Shape of F must be ({},{}), but is {}'.format(self.dim_x, self.dim_x, F.shape)
        assert np.ndim(H) == 2, 'Shape of H must be (dim_z, {}), but is {}'.format(P.shape[0], shape(H))
        assert H.shape[1] == P.shape[0], 'Shape of H must be (dim_z, {}), but is {}'.format(P.shape[0], H.shape)
        hph_shape = (H.shape[0], H.shape[0])
        r_shape = shape(R)
        if H.shape[0] == 1:
            assert r_shape in [(), (1,), (1, 1)], 'R must be scalar or one element array, but is shaped {}'.format(r_shape)
        else:
            assert r_shape == hph_shape, 'shape of R should be {} but it is {}'.format(hph_shape, r_shape)
        if z is not None:
            z_shape = shape(z)
        else:
            z_shape = (self.dim_z, 1)
        Hx = dot(H, x)
        if z_shape == ():
            assert Hx.ndim == 1 or shape(Hx) == (1, 1), 'shape of z should be {}, not {} for the given H'.format(shape(Hx), z_shape)
        elif shape(Hx) == (1,):
            assert z_shape[0] == 1, 'Shape of z must be {} for the given H'.format(shape(Hx))
        else:
            assert z_shape == shape(Hx) or (len(z_shape) == 1 and shape(Hx) == (z_shape[0], 1)), 'shape of z should be {}, not {} for the given H'.format(shape(Hx), z_shape)
        if np.ndim(Hx) > 1 and shape(Hx) != (1, 1):
            assert shape(Hx) == z_shape, 'shape of z should be {} for the given H, but it is {}'.format(shape(Hx), z_shape)

def freeze(self):
    """
            Save the parameters before non-observation forward
        """
    self.attr_saved = deepcopy(self.__dict__)

def __repr__(self):
    return '\n'.join(['KalmanFilter object', pretty_str('dim_x', self.dim_x), pretty_str('dim_z', self.dim_z), pretty_str('dim_u', self.dim_u), pretty_str('x', self.x), pretty_str('P', self.P), pretty_str('x_prior', self.x_prior), pretty_str('P_prior', self.P_prior), pretty_str('x_post', self.x_post), pretty_str('P_post', self.P_post), pretty_str('F', self.F), pretty_str('Q', self.Q), pretty_str('R', self.R), pretty_str('H', self.H), pretty_str('K', self.K), pretty_str('y', self.y), pretty_str('S', self.S), pretty_str('SI', self.SI), pretty_str('M', self.M), pretty_str('B', self.B), pretty_str('z', self.z), pretty_str('log-likelihood', self.log_likelihood), pretty_str('likelihood', self.likelihood), pretty_str('mahalanobis', self.mahalanobis), pretty_str('alpha', self.alpha), pretty_str('inv', self.inv)])

def check_suffix(file='yolov5s.pt', suffix=('.pt',), msg=''):
    if file and suffix:
        if isinstance(suffix, str):
            suffix = [suffix]
        for f in file if isinstance(file, (list, tuple)) else [file]:
            s = Path(f).suffix.lower()
            if len(s):
                assert s in suffix, f'{msg}{f} acceptable suffix is {suffix}'

def evaluate_coco(gt_file: str, pred_file: str, task: str='bbox', evaluation_type: str='full') -> None:
    """
    Evaluates the performance of a COCO object detection model.

    Args:
        gt_file (str): Path to the ground truth file.
        pred_file (str): Path to the prediction file.
        task (str, optional): The type of task to evaluate (bbox or segm). Defaults to "bbox".
        evaluation_type (str, optional): The type of evaluation to perform (full or mAP). Defaults to "full".
    """
    with HiddenPrints():
        coco_gt = COCO(gt_file)
        with open(pred_file, 'r') as f:
            pred_file = json.load(f)
            pred_file = pred_file[0]['annotations']
        coco_dt = coco_gt.loadRes(pred_file)
        coco_eval = COCOeval(coco_gt, coco_dt, task)
        coco_eval.evaluate()
        coco_eval.accumulate()
        coco_eval.summarize()
    if evaluation_type == 'full':
        coco_eval.summarize()
    elif evaluation_type == 'mAP':
        print(f'{task} mAP: {coco_eval.stats[0]:.3f}')

