# Cluster 11

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

class ColoredFormatter(logging.Formatter):

    def __init__(self, fmt, use_color=True):
        logging.Formatter.__init__(self, fmt)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:

            def colored(text):
                return termcolor.colored(text, color=COLORS[levelname], attrs={'bold': True})
            record.levelname2 = colored('{:<7}'.format(record.levelname))
            record.message2 = colored(record.msg)
            asctime2 = datetime.datetime.fromtimestamp(record.created)
            record.asctime2 = termcolor.colored(asctime2, color='green')
            record.module2 = termcolor.colored(record.module, color='cyan')
            record.funcName2 = termcolor.colored(record.funcName, color='cyan')
            record.lineno2 = termcolor.colored(record.lineno, color='cyan')
        return logging.Formatter.format(self, record)

def colored(text):
    return termcolor.colored(text, color=COLORS[levelname], attrs={'bold': True})

def format(self, record):
    levelname = record.levelname
    if self.use_color and levelname in COLORS:

        def colored(text):
            return termcolor.colored(text, color=COLORS[levelname], attrs={'bold': True})
        record.levelname2 = colored('{:<7}'.format(record.levelname))
        record.message2 = colored(record.msg)
        asctime2 = datetime.datetime.fromtimestamp(record.created)
        record.asctime2 = termcolor.colored(asctime2, color='green')
        record.module2 = termcolor.colored(record.module, color='cyan')
        record.funcName2 = termcolor.colored(record.funcName, color='cyan')
        record.lineno2 = termcolor.colored(record.lineno, color='cyan')
    return logging.Formatter.format(self, record)

def update_dict(target_dict, new_dict, validate_item=None):
    for key, value in new_dict.items():
        if validate_item:
            validate_item(key, value)
        if key not in target_dict:
            logger.warn('Skipping unexpected key in config: {}'.format(key))
            continue
        if isinstance(target_dict[key], dict) and isinstance(value, dict):
            update_dict(target_dict[key], value, validate_item=validate_item)
        else:
            target_dict[key] = value

def get_config(config_file_or_yaml=None, config_from_args=None):
    config = get_default_config()
    if config_file_or_yaml is not None:
        config_from_yaml = yaml.safe_load(config_file_or_yaml)
        if not isinstance(config_from_yaml, dict):
            with open(config_from_yaml) as f:
                logger.info('Loading config file from: {}'.format(config_from_yaml))
                config_from_yaml = yaml.safe_load(f)
        update_dict(config, config_from_yaml, validate_item=validate_config_item)
    if config_from_args is not None:
        update_dict(config, config_from_args, validate_item=validate_config_item)
    return config

def convert_model_info_to_pwc(model_infos):
    pwc_files = {}
    for model in model_infos:
        cfg_folder_name = osp.split(model['config'])[-2]
        pwc_model_info = OrderedDict()
        pwc_model_info['Name'] = osp.split(model['config'])[-1].split('.')[0]
        pwc_model_info['In Collection'] = 'Please fill in Collection name'
        pwc_model_info['Config'] = osp.join('configs', model['config'])
        memory = round(model['results']['memory'] / 1024, 1)
        meta_data = OrderedDict()
        meta_data['Training Memory (GB)'] = memory
        if 'epochs' in model:
            meta_data['Epochs'] = get_real_epoch_or_iter(model['config'])
        else:
            meta_data['Iterations'] = get_real_epoch_or_iter(model['config'])
        pwc_model_info['Metadata'] = meta_data
        dataset_name = get_dataset_name(model['config'])
        results = []
        if 'bbox_mAP' in model['results']:
            metric = round(model['results']['bbox_mAP'] * 100, 1)
            results.append(OrderedDict(Task='Object Detection', Dataset=dataset_name, Metrics={'box AP': metric}))
        if 'segm_mAP' in model['results']:
            metric = round(model['results']['segm_mAP'] * 100, 1)
            results.append(OrderedDict(Task='Instance Segmentation', Dataset=dataset_name, Metrics={'mask AP': metric}))
        if 'PQ' in model['results']:
            metric = round(model['results']['PQ'], 1)
            results.append(OrderedDict(Task='Panoptic Segmentation', Dataset=dataset_name, Metrics={'PQ': metric}))
        pwc_model_info['Results'] = results
        link_string = 'https://download.openmmlab.com/mmdetection/v2.0/'
        link_string += '{}/{}'.format(model['config'].rstrip('.py'), osp.split(model['model_path'])[-1])
        pwc_model_info['Weights'] = link_string
        if cfg_folder_name in pwc_files:
            pwc_files[cfg_folder_name].append(pwc_model_info)
        else:
            pwc_files[cfg_folder_name] = [pwc_model_info]
    return pwc_files

@functools.wraps(loss_func)
def wrapper(pred, target, weight=None, reduction='mean', avg_factor=None, **kwargs):
    loss = loss_func(pred, target, **kwargs)
    loss = weight_reduce_loss(loss, weight, reduction, avg_factor)
    return loss

@HEADS.register_module()
class SABLHead(BaseModule):
    """Side-Aware Boundary Localization (SABL) for RoI-Head.

    Side-Aware features are extracted by conv layers
    with an attention mechanism.
    Boundary Localization with Bucketing and Bucketing Guided Rescoring
    are implemented in BucketingBBoxCoder.

    Please refer to https://arxiv.org/abs/1912.04260 for more details.

    Args:
        cls_in_channels (int): Input channels of cls RoI feature.             Defaults to 256.
        reg_in_channels (int): Input channels of reg RoI feature.             Defaults to 256.
        roi_feat_size (int): Size of RoI features. Defaults to 7.
        reg_feat_up_ratio (int): Upsample ratio of reg features.             Defaults to 2.
        reg_pre_kernel (int): Kernel of 2D conv layers before             attention pooling. Defaults to 3.
        reg_post_kernel (int): Kernel of 1D conv layers after             attention pooling. Defaults to 3.
        reg_pre_num (int): Number of pre convs. Defaults to 2.
        reg_post_num (int): Number of post convs. Defaults to 1.
        num_classes (int): Number of classes in dataset. Defaults to 80.
        cls_out_channels (int): Hidden channels in cls fcs. Defaults to 1024.
        reg_offset_out_channels (int): Hidden and output channel             of reg offset branch. Defaults to 256.
        reg_cls_out_channels (int): Hidden and output channel             of reg cls branch. Defaults to 256.
        num_cls_fcs (int): Number of fcs for cls branch. Defaults to 1.
        num_reg_fcs (int): Number of fcs for reg branch.. Defaults to 0.
        reg_class_agnostic (bool): Class agnostic regression or not.             Defaults to True.
        norm_cfg (dict): Config of norm layers. Defaults to None.
        bbox_coder (dict): Config of bbox coder. Defaults 'BucketingBBoxCoder'.
        loss_cls (dict): Config of classification loss.
        loss_bbox_cls (dict): Config of classification loss for bbox branch.
        loss_bbox_reg (dict): Config of regression loss for bbox branch.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """

    def __init__(self, num_classes, cls_in_channels=256, reg_in_channels=256, roi_feat_size=7, reg_feat_up_ratio=2, reg_pre_kernel=3, reg_post_kernel=3, reg_pre_num=2, reg_post_num=1, cls_out_channels=1024, reg_offset_out_channels=256, reg_cls_out_channels=256, num_cls_fcs=1, num_reg_fcs=0, reg_class_agnostic=True, norm_cfg=None, bbox_coder=dict(type='BucketingBBoxCoder', num_buckets=14, scale_factor=1.7), loss_cls=dict(type='CrossEntropyLoss', use_sigmoid=False, loss_weight=1.0), loss_bbox_cls=dict(type='CrossEntropyLoss', use_sigmoid=True, loss_weight=1.0), loss_bbox_reg=dict(type='SmoothL1Loss', beta=0.1, loss_weight=1.0), init_cfg=None):
        super(SABLHead, self).__init__(init_cfg)
        self.cls_in_channels = cls_in_channels
        self.reg_in_channels = reg_in_channels
        self.roi_feat_size = roi_feat_size
        self.reg_feat_up_ratio = int(reg_feat_up_ratio)
        self.num_buckets = bbox_coder['num_buckets']
        assert self.reg_feat_up_ratio // 2 >= 1
        self.up_reg_feat_size = roi_feat_size * self.reg_feat_up_ratio
        assert self.up_reg_feat_size == bbox_coder['num_buckets']
        self.reg_pre_kernel = reg_pre_kernel
        self.reg_post_kernel = reg_post_kernel
        self.reg_pre_num = reg_pre_num
        self.reg_post_num = reg_post_num
        self.num_classes = num_classes
        self.cls_out_channels = cls_out_channels
        self.reg_offset_out_channels = reg_offset_out_channels
        self.reg_cls_out_channels = reg_cls_out_channels
        self.num_cls_fcs = num_cls_fcs
        self.num_reg_fcs = num_reg_fcs
        self.reg_class_agnostic = reg_class_agnostic
        assert self.reg_class_agnostic
        self.norm_cfg = norm_cfg
        self.bbox_coder = build_bbox_coder(bbox_coder)
        self.loss_cls = build_loss(loss_cls)
        self.loss_bbox_cls = build_loss(loss_bbox_cls)
        self.loss_bbox_reg = build_loss(loss_bbox_reg)
        self.cls_fcs = self._add_fc_branch(self.num_cls_fcs, self.cls_in_channels, self.roi_feat_size, self.cls_out_channels)
        self.side_num = int(np.ceil(self.num_buckets / 2))
        if self.reg_feat_up_ratio > 1:
            self.upsample_x = nn.ConvTranspose1d(reg_in_channels, reg_in_channels, self.reg_feat_up_ratio, stride=self.reg_feat_up_ratio)
            self.upsample_y = nn.ConvTranspose1d(reg_in_channels, reg_in_channels, self.reg_feat_up_ratio, stride=self.reg_feat_up_ratio)
        self.reg_pre_convs = nn.ModuleList()
        for i in range(self.reg_pre_num):
            reg_pre_conv = ConvModule(reg_in_channels, reg_in_channels, kernel_size=reg_pre_kernel, padding=reg_pre_kernel // 2, norm_cfg=norm_cfg, act_cfg=dict(type='ReLU'))
            self.reg_pre_convs.append(reg_pre_conv)
        self.reg_post_conv_xs = nn.ModuleList()
        for i in range(self.reg_post_num):
            reg_post_conv_x = ConvModule(reg_in_channels, reg_in_channels, kernel_size=(1, reg_post_kernel), padding=(0, reg_post_kernel // 2), norm_cfg=norm_cfg, act_cfg=dict(type='ReLU'))
            self.reg_post_conv_xs.append(reg_post_conv_x)
        self.reg_post_conv_ys = nn.ModuleList()
        for i in range(self.reg_post_num):
            reg_post_conv_y = ConvModule(reg_in_channels, reg_in_channels, kernel_size=(reg_post_kernel, 1), padding=(reg_post_kernel // 2, 0), norm_cfg=norm_cfg, act_cfg=dict(type='ReLU'))
            self.reg_post_conv_ys.append(reg_post_conv_y)
        self.reg_conv_att_x = nn.Conv2d(reg_in_channels, 1, 1)
        self.reg_conv_att_y = nn.Conv2d(reg_in_channels, 1, 1)
        self.fc_cls = nn.Linear(self.cls_out_channels, self.num_classes + 1)
        self.relu = nn.ReLU(inplace=True)
        self.reg_cls_fcs = self._add_fc_branch(self.num_reg_fcs, self.reg_in_channels, 1, self.reg_cls_out_channels)
        self.reg_offset_fcs = self._add_fc_branch(self.num_reg_fcs, self.reg_in_channels, 1, self.reg_offset_out_channels)
        self.fc_reg_cls = nn.Linear(self.reg_cls_out_channels, 1)
        self.fc_reg_offset = nn.Linear(self.reg_offset_out_channels, 1)
        if init_cfg is None:
            self.init_cfg = [dict(type='Xavier', layer='Linear', distribution='uniform', override=[dict(type='Normal', name='reg_conv_att_x', std=0.01), dict(type='Normal', name='reg_conv_att_y', std=0.01), dict(type='Normal', name='fc_reg_cls', std=0.01), dict(type='Normal', name='fc_cls', std=0.01), dict(type='Normal', name='fc_reg_offset', std=0.001)])]
            if self.reg_feat_up_ratio > 1:
                self.init_cfg += [dict(type='Kaiming', distribution='normal', override=[dict(name='upsample_x'), dict(name='upsample_y')])]

    @property
    def custom_cls_channels(self):
        return getattr(self.loss_cls, 'custom_cls_channels', False)

    @property
    def custom_activation(self):
        return getattr(self.loss_cls, 'custom_activation', False)

    @property
    def custom_accuracy(self):
        return getattr(self.loss_cls, 'custom_accuracy', False)

    def _add_fc_branch(self, num_branch_fcs, in_channels, roi_feat_size, fc_out_channels):
        in_channels = in_channels * roi_feat_size * roi_feat_size
        branch_fcs = nn.ModuleList()
        for i in range(num_branch_fcs):
            fc_in_channels = in_channels if i == 0 else fc_out_channels
            branch_fcs.append(nn.Linear(fc_in_channels, fc_out_channels))
        return branch_fcs

    def cls_forward(self, cls_x):
        cls_x = cls_x.view(cls_x.size(0), -1)
        for fc in self.cls_fcs:
            cls_x = self.relu(fc(cls_x))
        cls_score = self.fc_cls(cls_x)
        return cls_score

    def attention_pool(self, reg_x):
        """Extract direction-specific features fx and fy with attention
        methanism."""
        reg_fx = reg_x
        reg_fy = reg_x
        reg_fx_att = self.reg_conv_att_x(reg_fx).sigmoid()
        reg_fy_att = self.reg_conv_att_y(reg_fy).sigmoid()
        reg_fx_att = reg_fx_att / reg_fx_att.sum(dim=2).unsqueeze(2)
        reg_fy_att = reg_fy_att / reg_fy_att.sum(dim=3).unsqueeze(3)
        reg_fx = (reg_fx * reg_fx_att).sum(dim=2)
        reg_fy = (reg_fy * reg_fy_att).sum(dim=3)
        return (reg_fx, reg_fy)

    def side_aware_feature_extractor(self, reg_x):
        """Refine and extract side-aware features without split them."""
        for reg_pre_conv in self.reg_pre_convs:
            reg_x = reg_pre_conv(reg_x)
        reg_fx, reg_fy = self.attention_pool(reg_x)
        if self.reg_post_num > 0:
            reg_fx = reg_fx.unsqueeze(2)
            reg_fy = reg_fy.unsqueeze(3)
            for i in range(self.reg_post_num):
                reg_fx = self.reg_post_conv_xs[i](reg_fx)
                reg_fy = self.reg_post_conv_ys[i](reg_fy)
            reg_fx = reg_fx.squeeze(2)
            reg_fy = reg_fy.squeeze(3)
        if self.reg_feat_up_ratio > 1:
            reg_fx = self.relu(self.upsample_x(reg_fx))
            reg_fy = self.relu(self.upsample_y(reg_fy))
        reg_fx = torch.transpose(reg_fx, 1, 2)
        reg_fy = torch.transpose(reg_fy, 1, 2)
        return (reg_fx.contiguous(), reg_fy.contiguous())

    def reg_pred(self, x, offset_fcs, cls_fcs):
        """Predict bucketing estimation (cls_pred) and fine regression (offset
        pred) with side-aware features."""
        x_offset = x.view(-1, self.reg_in_channels)
        x_cls = x.view(-1, self.reg_in_channels)
        for fc in offset_fcs:
            x_offset = self.relu(fc(x_offset))
        for fc in cls_fcs:
            x_cls = self.relu(fc(x_cls))
        offset_pred = self.fc_reg_offset(x_offset)
        cls_pred = self.fc_reg_cls(x_cls)
        offset_pred = offset_pred.view(x.size(0), -1)
        cls_pred = cls_pred.view(x.size(0), -1)
        return (offset_pred, cls_pred)

    def side_aware_split(self, feat):
        """Split side-aware features aligned with orders of bucketing
        targets."""
        l_end = int(np.ceil(self.up_reg_feat_size / 2))
        r_start = int(np.floor(self.up_reg_feat_size / 2))
        feat_fl = feat[:, :l_end]
        feat_fr = feat[:, r_start:].flip(dims=(1,))
        feat_fl = feat_fl.contiguous()
        feat_fr = feat_fr.contiguous()
        feat = torch.cat([feat_fl, feat_fr], dim=-1)
        return feat

    def bbox_pred_split(self, bbox_pred, num_proposals_per_img):
        """Split batch bbox prediction back to each image."""
        bucket_cls_preds, bucket_offset_preds = bbox_pred
        bucket_cls_preds = bucket_cls_preds.split(num_proposals_per_img, 0)
        bucket_offset_preds = bucket_offset_preds.split(num_proposals_per_img, 0)
        bbox_pred = tuple(zip(bucket_cls_preds, bucket_offset_preds))
        return bbox_pred

    def reg_forward(self, reg_x):
        outs = self.side_aware_feature_extractor(reg_x)
        edge_offset_preds = []
        edge_cls_preds = []
        reg_fx = outs[0]
        reg_fy = outs[1]
        offset_pred_x, cls_pred_x = self.reg_pred(reg_fx, self.reg_offset_fcs, self.reg_cls_fcs)
        offset_pred_y, cls_pred_y = self.reg_pred(reg_fy, self.reg_offset_fcs, self.reg_cls_fcs)
        offset_pred_x = self.side_aware_split(offset_pred_x)
        offset_pred_y = self.side_aware_split(offset_pred_y)
        cls_pred_x = self.side_aware_split(cls_pred_x)
        cls_pred_y = self.side_aware_split(cls_pred_y)
        edge_offset_preds = torch.cat([offset_pred_x, offset_pred_y], dim=-1)
        edge_cls_preds = torch.cat([cls_pred_x, cls_pred_y], dim=-1)
        return (edge_cls_preds, edge_offset_preds)

    def forward(self, x):
        bbox_pred = self.reg_forward(x)
        cls_score = self.cls_forward(x)
        return (cls_score, bbox_pred)

    def get_targets(self, sampling_results, gt_bboxes, gt_labels, rcnn_train_cfg):
        pos_proposals = [res.pos_bboxes for res in sampling_results]
        neg_proposals = [res.neg_bboxes for res in sampling_results]
        pos_gt_bboxes = [res.pos_gt_bboxes for res in sampling_results]
        pos_gt_labels = [res.pos_gt_labels for res in sampling_results]
        cls_reg_targets = self.bucket_target(pos_proposals, neg_proposals, pos_gt_bboxes, pos_gt_labels, rcnn_train_cfg)
        labels, label_weights, bucket_cls_targets, bucket_cls_weights, bucket_offset_targets, bucket_offset_weights = cls_reg_targets
        return (labels, label_weights, (bucket_cls_targets, bucket_offset_targets), (bucket_cls_weights, bucket_offset_weights))

    def bucket_target(self, pos_proposals_list, neg_proposals_list, pos_gt_bboxes_list, pos_gt_labels_list, rcnn_train_cfg, concat=True):
        labels, label_weights, bucket_cls_targets, bucket_cls_weights, bucket_offset_targets, bucket_offset_weights = multi_apply(self._bucket_target_single, pos_proposals_list, neg_proposals_list, pos_gt_bboxes_list, pos_gt_labels_list, cfg=rcnn_train_cfg)
        if concat:
            labels = torch.cat(labels, 0)
            label_weights = torch.cat(label_weights, 0)
            bucket_cls_targets = torch.cat(bucket_cls_targets, 0)
            bucket_cls_weights = torch.cat(bucket_cls_weights, 0)
            bucket_offset_targets = torch.cat(bucket_offset_targets, 0)
            bucket_offset_weights = torch.cat(bucket_offset_weights, 0)
        return (labels, label_weights, bucket_cls_targets, bucket_cls_weights, bucket_offset_targets, bucket_offset_weights)

    def _bucket_target_single(self, pos_proposals, neg_proposals, pos_gt_bboxes, pos_gt_labels, cfg):
        """Compute bucketing estimation targets and fine regression targets for
        a single image.

        Args:
            pos_proposals (Tensor): positive proposals of a single image,
                 Shape (n_pos, 4)
            neg_proposals (Tensor): negative proposals of a single image,
                 Shape (n_neg, 4).
            pos_gt_bboxes (Tensor): gt bboxes assigned to positive proposals
                 of a single image, Shape (n_pos, 4).
            pos_gt_labels (Tensor): gt labels assigned to positive proposals
                 of a single image, Shape (n_pos, ).
            cfg (dict): Config of calculating targets

        Returns:
            tuple:

                - labels (Tensor): Labels in a single image.                     Shape (n,).
                - label_weights (Tensor): Label weights in a single image.                    Shape (n,)
                - bucket_cls_targets (Tensor): Bucket cls targets in                     a single image. Shape (n, num_buckets*2).
                - bucket_cls_weights (Tensor): Bucket cls weights in                     a single image. Shape (n, num_buckets*2).
                - bucket_offset_targets (Tensor): Bucket offset targets                     in a single image. Shape (n, num_buckets*2).
                - bucket_offset_targets (Tensor): Bucket offset weights                     in a single image. Shape (n, num_buckets*2).
        """
        num_pos = pos_proposals.size(0)
        num_neg = neg_proposals.size(0)
        num_samples = num_pos + num_neg
        labels = pos_gt_bboxes.new_full((num_samples,), self.num_classes, dtype=torch.long)
        label_weights = pos_proposals.new_zeros(num_samples)
        bucket_cls_targets = pos_proposals.new_zeros(num_samples, 4 * self.side_num)
        bucket_cls_weights = pos_proposals.new_zeros(num_samples, 4 * self.side_num)
        bucket_offset_targets = pos_proposals.new_zeros(num_samples, 4 * self.side_num)
        bucket_offset_weights = pos_proposals.new_zeros(num_samples, 4 * self.side_num)
        if num_pos > 0:
            labels[:num_pos] = pos_gt_labels
            label_weights[:num_pos] = 1.0
            pos_bucket_offset_targets, pos_bucket_offset_weights, pos_bucket_cls_targets, pos_bucket_cls_weights = self.bbox_coder.encode(pos_proposals, pos_gt_bboxes)
            bucket_cls_targets[:num_pos, :] = pos_bucket_cls_targets
            bucket_cls_weights[:num_pos, :] = pos_bucket_cls_weights
            bucket_offset_targets[:num_pos, :] = pos_bucket_offset_targets
            bucket_offset_weights[:num_pos, :] = pos_bucket_offset_weights
        if num_neg > 0:
            label_weights[-num_neg:] = 1.0
        return (labels, label_weights, bucket_cls_targets, bucket_cls_weights, bucket_offset_targets, bucket_offset_weights)

    def loss(self, cls_score, bbox_pred, rois, labels, label_weights, bbox_targets, bbox_weights, reduction_override=None):
        losses = dict()
        if cls_score is not None:
            avg_factor = max(torch.sum(label_weights > 0).float().item(), 1.0)
            losses['loss_cls'] = self.loss_cls(cls_score, labels, label_weights, avg_factor=avg_factor, reduction_override=reduction_override)
            losses['acc'] = accuracy(cls_score, labels)
        if bbox_pred is not None:
            bucket_cls_preds, bucket_offset_preds = bbox_pred
            bucket_cls_targets, bucket_offset_targets = bbox_targets
            bucket_cls_weights, bucket_offset_weights = bbox_weights
            bucket_cls_preds = bucket_cls_preds.view(-1, self.side_num)
            bucket_cls_targets = bucket_cls_targets.view(-1, self.side_num)
            bucket_cls_weights = bucket_cls_weights.view(-1, self.side_num)
            losses['loss_bbox_cls'] = self.loss_bbox_cls(bucket_cls_preds, bucket_cls_targets, bucket_cls_weights, avg_factor=bucket_cls_targets.size(0), reduction_override=reduction_override)
            losses['loss_bbox_reg'] = self.loss_bbox_reg(bucket_offset_preds, bucket_offset_targets, bucket_offset_weights, avg_factor=bucket_offset_targets.size(0), reduction_override=reduction_override)
        return losses

    @force_fp32(apply_to=('cls_score', 'bbox_pred'))
    def get_bboxes(self, rois, cls_score, bbox_pred, img_shape, scale_factor, rescale=False, cfg=None):
        if isinstance(cls_score, list):
            cls_score = sum(cls_score) / float(len(cls_score))
        scores = F.softmax(cls_score, dim=1) if cls_score is not None else None
        if bbox_pred is not None:
            bboxes, confidences = self.bbox_coder.decode(rois[:, 1:], bbox_pred, img_shape)
        else:
            bboxes = rois[:, 1:].clone()
            confidences = None
            if img_shape is not None:
                bboxes[:, [0, 2]].clamp_(min=0, max=img_shape[1] - 1)
                bboxes[:, [1, 3]].clamp_(min=0, max=img_shape[0] - 1)
        if rescale and bboxes.size(0) > 0:
            if isinstance(scale_factor, float):
                bboxes /= scale_factor
            else:
                bboxes /= torch.from_numpy(scale_factor).to(bboxes.device)
        if cfg is None:
            return (bboxes, scores)
        else:
            det_bboxes, det_labels = multiclass_nms(bboxes, scores, cfg.score_thr, cfg.nms, cfg.max_per_img, score_factors=confidences)
            return (det_bboxes, det_labels)

    @force_fp32(apply_to=('bbox_preds',))
    def refine_bboxes(self, rois, labels, bbox_preds, pos_is_gts, img_metas):
        """Refine bboxes during training.

        Args:
            rois (Tensor): Shape (n*bs, 5), where n is image number per GPU,
                and bs is the sampled RoIs per image.
            labels (Tensor): Shape (n*bs, ).
            bbox_preds (list[Tensor]): Shape [(n*bs, num_buckets*2),                 (n*bs, num_buckets*2)].
            pos_is_gts (list[Tensor]): Flags indicating if each positive bbox
                is a gt bbox.
            img_metas (list[dict]): Meta info of each image.

        Returns:
            list[Tensor]: Refined bboxes of each image in a mini-batch.
        """
        img_ids = rois[:, 0].long().unique(sorted=True)
        assert img_ids.numel() == len(img_metas)
        bboxes_list = []
        for i in range(len(img_metas)):
            inds = torch.nonzero(rois[:, 0] == i, as_tuple=False).squeeze(dim=1)
            num_rois = inds.numel()
            bboxes_ = rois[inds, 1:]
            label_ = labels[inds]
            edge_cls_preds, edge_offset_preds = bbox_preds
            edge_cls_preds_ = edge_cls_preds[inds]
            edge_offset_preds_ = edge_offset_preds[inds]
            bbox_pred_ = [edge_cls_preds_, edge_offset_preds_]
            img_meta_ = img_metas[i]
            pos_is_gts_ = pos_is_gts[i]
            bboxes = self.regress_by_class(bboxes_, label_, bbox_pred_, img_meta_)
            pos_keep = 1 - pos_is_gts_
            keep_inds = pos_is_gts_.new_ones(num_rois)
            keep_inds[:len(pos_is_gts_)] = pos_keep
            bboxes_list.append(bboxes[keep_inds.type(torch.bool)])
        return bboxes_list

    @force_fp32(apply_to=('bbox_pred',))
    def regress_by_class(self, rois, label, bbox_pred, img_meta):
        """Regress the bbox for the predicted class. Used in Cascade R-CNN.

        Args:
            rois (Tensor): shape (n, 4) or (n, 5)
            label (Tensor): shape (n, )
            bbox_pred (list[Tensor]): shape [(n, num_buckets *2),                 (n, num_buckets *2)]
            img_meta (dict): Image meta info.

        Returns:
            Tensor: Regressed bboxes, the same shape as input rois.
        """
        assert rois.size(1) == 4 or rois.size(1) == 5
        if rois.size(1) == 4:
            new_rois, _ = self.bbox_coder.decode(rois, bbox_pred, img_meta['img_shape'])
        else:
            bboxes, _ = self.bbox_coder.decode(rois[:, 1:], bbox_pred, img_meta['img_shape'])
            new_rois = torch.cat((rois[:, [0]], bboxes), dim=1)
        return new_rois

def reg_pred(self, x, offset_fcs, cls_fcs):
    """Predict bucketing estimation (cls_pred) and fine regression (offset
        pred) with side-aware features."""
    x_offset = x.view(-1, self.reg_in_channels)
    x_cls = x.view(-1, self.reg_in_channels)
    for fc in offset_fcs:
        x_offset = self.relu(fc(x_offset))
    for fc in cls_fcs:
        x_cls = self.relu(fc(x_cls))
    offset_pred = self.fc_reg_offset(x_offset)
    cls_pred = self.fc_reg_cls(x_cls)
    offset_pred = offset_pred.view(x.size(0), -1)
    cls_pred = cls_pred.view(x.size(0), -1)
    return (offset_pred, cls_pred)

@HEADS.register_module()
class MaskPointHead(BaseModule):
    """A mask point head use in PointRend.

    ``MaskPointHead`` use shared multi-layer perceptron (equivalent to
    nn.Conv1d) to predict the logit of input points. The fine-grained feature
    and coarse feature will be concatenate together for predication.

    Args:
        num_fcs (int): Number of fc layers in the head. Default: 3.
        in_channels (int): Number of input channels. Default: 256.
        fc_channels (int): Number of fc channels. Default: 256.
        num_classes (int): Number of classes for logits. Default: 80.
        class_agnostic (bool): Whether use class agnostic classification.
            If so, the output channels of logits will be 1. Default: False.
        coarse_pred_each_layer (bool): Whether concatenate coarse feature with
            the output of each fc layer. Default: True.
        conv_cfg (dict | None): Dictionary to construct and config conv layer.
            Default: dict(type='Conv1d'))
        norm_cfg (dict | None): Dictionary to construct and config norm layer.
            Default: None.
        loss_point (dict): Dictionary to construct and config loss layer of
            point head. Default: dict(type='CrossEntropyLoss', use_mask=True,
            loss_weight=1.0).
        init_cfg (dict or list[dict], optional): Initialization config dict.
    """

    def __init__(self, num_classes, num_fcs=3, in_channels=256, fc_channels=256, class_agnostic=False, coarse_pred_each_layer=True, conv_cfg=dict(type='Conv1d'), norm_cfg=None, act_cfg=dict(type='ReLU'), loss_point=dict(type='CrossEntropyLoss', use_mask=True, loss_weight=1.0), init_cfg=dict(type='Normal', std=0.001, override=dict(name='fc_logits'))):
        super().__init__(init_cfg)
        self.num_fcs = num_fcs
        self.in_channels = in_channels
        self.fc_channels = fc_channels
        self.num_classes = num_classes
        self.class_agnostic = class_agnostic
        self.coarse_pred_each_layer = coarse_pred_each_layer
        self.conv_cfg = conv_cfg
        self.norm_cfg = norm_cfg
        self.loss_point = build_loss(loss_point)
        fc_in_channels = in_channels + num_classes
        self.fcs = nn.ModuleList()
        for _ in range(num_fcs):
            fc = ConvModule(fc_in_channels, fc_channels, kernel_size=1, stride=1, padding=0, conv_cfg=conv_cfg, norm_cfg=norm_cfg, act_cfg=act_cfg)
            self.fcs.append(fc)
            fc_in_channels = fc_channels
            fc_in_channels += num_classes if self.coarse_pred_each_layer else 0
        out_channels = 1 if self.class_agnostic else self.num_classes
        self.fc_logits = nn.Conv1d(fc_in_channels, out_channels, kernel_size=1, stride=1, padding=0)

    def forward(self, fine_grained_feats, coarse_feats):
        """Classify each point base on fine grained and coarse feats.

        Args:
            fine_grained_feats (Tensor): Fine grained feature sampled from FPN,
                shape (num_rois, in_channels, num_points).
            coarse_feats (Tensor): Coarse feature sampled from CoarseMaskHead,
                shape (num_rois, num_classes, num_points).

        Returns:
            Tensor: Point classification results,
                shape (num_rois, num_class, num_points).
        """
        x = torch.cat([fine_grained_feats, coarse_feats], dim=1)
        for fc in self.fcs:
            x = fc(x)
            if self.coarse_pred_each_layer:
                x = torch.cat((x, coarse_feats), dim=1)
        return self.fc_logits(x)

    def get_targets(self, rois, rel_roi_points, sampling_results, gt_masks, cfg):
        """Get training targets of MaskPointHead for all images.

        Args:
            rois (Tensor): Region of Interest, shape (num_rois, 5).
            rel_roi_points: Points coordinates relative to RoI, shape
                (num_rois, num_points, 2).
            sampling_results (:obj:`SamplingResult`): Sampling result after
                sampling and assignment.
            gt_masks (Tensor) : Ground truth segmentation masks of
                corresponding boxes, shape (num_rois, height, width).
            cfg (dict): Training cfg.

        Returns:
            Tensor: Point target, shape (num_rois, num_points).
        """
        num_imgs = len(sampling_results)
        rois_list = []
        rel_roi_points_list = []
        for batch_ind in range(num_imgs):
            inds = rois[:, 0] == batch_ind
            rois_list.append(rois[inds])
            rel_roi_points_list.append(rel_roi_points[inds])
        pos_assigned_gt_inds_list = [res.pos_assigned_gt_inds for res in sampling_results]
        cfg_list = [cfg for _ in range(num_imgs)]
        point_targets = map(self._get_target_single, rois_list, rel_roi_points_list, pos_assigned_gt_inds_list, gt_masks, cfg_list)
        point_targets = list(point_targets)
        if len(point_targets) > 0:
            point_targets = torch.cat(point_targets)
        return point_targets

    def _get_target_single(self, rois, rel_roi_points, pos_assigned_gt_inds, gt_masks, cfg):
        """Get training target of MaskPointHead for each image."""
        num_pos = rois.size(0)
        num_points = cfg.num_points
        if num_pos > 0:
            gt_masks_th = gt_masks.to_tensor(rois.dtype, rois.device).index_select(0, pos_assigned_gt_inds)
            gt_masks_th = gt_masks_th.unsqueeze(1)
            rel_img_points = rel_roi_point_to_rel_img_point(rois, rel_roi_points, gt_masks_th)
            point_targets = point_sample(gt_masks_th, rel_img_points).squeeze(1)
        else:
            point_targets = rois.new_zeros((0, num_points))
        return point_targets

    def loss(self, point_pred, point_targets, labels):
        """Calculate loss for MaskPointHead.

        Args:
            point_pred (Tensor): Point predication result, shape
                (num_rois, num_classes, num_points).
            point_targets (Tensor): Point targets, shape (num_roi, num_points).
            labels (Tensor): Class label of corresponding boxes,
                shape (num_rois, )

        Returns:
            dict[str, Tensor]: a dictionary of point loss components
        """
        loss = dict()
        if self.class_agnostic:
            loss_point = self.loss_point(point_pred, point_targets, torch.zeros_like(labels))
        else:
            loss_point = self.loss_point(point_pred, point_targets, labels)
        loss['loss_point'] = loss_point
        return loss

    def get_roi_rel_points_train(self, mask_pred, labels, cfg):
        """Get ``num_points`` most uncertain points with random points during
        train.

        Sample points in [0, 1] x [0, 1] coordinate space based on their
        uncertainty. The uncertainties are calculated for each point using
        '_get_uncertainty()' function that takes point's logit prediction as
        input.

        Args:
            mask_pred (Tensor): A tensor of shape (num_rois, num_classes,
                mask_height, mask_width) for class-specific or class-agnostic
                prediction.
            labels (list): The ground truth class for each instance.
            cfg (dict): Training config of point head.

        Returns:
            point_coords (Tensor): A tensor of shape (num_rois, num_points, 2)
                that contains the coordinates sampled points.
        """
        point_coords = get_uncertain_point_coords_with_randomness(mask_pred, labels, cfg.num_points, cfg.oversample_ratio, cfg.importance_sample_ratio)
        return point_coords

    def get_roi_rel_points_test(self, mask_pred, pred_label, cfg):
        """Get ``num_points`` most uncertain points during test.

        Args:
            mask_pred (Tensor): A tensor of shape (num_rois, num_classes,
                mask_height, mask_width) for class-specific or class-agnostic
                prediction.
            pred_label (list): The predication class for each instance.
            cfg (dict): Testing config of point head.

        Returns:
            point_indices (Tensor): A tensor of shape (num_rois, num_points)
                that contains indices from [0, mask_height x mask_width) of the
                most uncertain points.
            point_coords (Tensor): A tensor of shape (num_rois, num_points, 2)
                that contains [0, 1] x [0, 1] normalized coordinates of the
                most uncertain points from the [mask_height, mask_width] grid .
        """
        num_points = cfg.subdivision_num_points
        uncertainty_map = get_uncertainty(mask_pred, pred_label)
        num_rois, _, mask_height, mask_width = uncertainty_map.shape
        if isinstance(mask_height, torch.Tensor):
            h_step = 1.0 / mask_height.float()
            w_step = 1.0 / mask_width.float()
        else:
            h_step = 1.0 / mask_height
            w_step = 1.0 / mask_width
        mask_size = int(mask_height * mask_width)
        uncertainty_map = uncertainty_map.view(num_rois, mask_size)
        num_points = min(mask_size, num_points)
        point_indices = uncertainty_map.topk(num_points, dim=1)[1]
        xs = w_step / 2.0 + (point_indices % mask_width).float() * w_step
        ys = h_step / 2.0 + (point_indices // mask_width).float() * h_step
        point_coords = torch.stack([xs, ys], dim=2)
        return (point_indices, point_coords)

def forward(self, fine_grained_feats, coarse_feats):
    """Classify each point base on fine grained and coarse feats.

        Args:
            fine_grained_feats (Tensor): Fine grained feature sampled from FPN,
                shape (num_rois, in_channels, num_points).
            coarse_feats (Tensor): Coarse feature sampled from CoarseMaskHead,
                shape (num_rois, num_classes, num_points).

        Returns:
            Tensor: Point classification results,
                shape (num_rois, num_class, num_points).
        """
    x = torch.cat([fine_grained_feats, coarse_feats], dim=1)
    for fc in self.fcs:
        x = fc(x)
        if self.coarse_pred_each_layer:
            x = torch.cat((x, coarse_feats), dim=1)
    return self.fc_logits(x)

def autolabel(ax, rects):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        if height > 0 and height <= 1:
            text_label = '{:2.0f}'.format(height * 100)
        else:
            text_label = '{:2.0f}'.format(height)
        ax.annotate(text_label, xy=(rect.get_x() + rect.get_width() / 2, height), xytext=(0, 3), textcoords='offset points', ha='center', va='bottom', fontsize='x-small')

@wraps(func)
def _time_it(*args, **kwargs):
    start = time()
    try:
        return func(*args, **kwargs)
    finally:
        end_ = time()
        print('time: {:.03f}s, fps: {:.03f}'.format(end_ - start, 1 / (end_ - start)))

def read_results(filename, data_type: str, is_gt=False, is_ignore=False):
    if data_type in ('mot', 'lab'):
        read_fun = read_mot_results
    else:
        raise ValueError('Unknown data type: {}'.format(data_type))
    return read_fun(filename, is_gt, is_ignore)

class Frame(BaseJsonLogger):
    """
    This module stores the information for each frame and use them in JsonParser
    Attributes:
        timestamp (float): The elapsed time of captured frame
        frame_id (int): The frame number of the captured video
        bboxes (list of Bbox objects): Stores the list of bbox objects.

    References:
        Check Bbox class for better information

    Args:
        timestamp (float):
        frame_id (int):

    """

    def __init__(self, frame_id: int, timestamp: float=None):
        self.frame_id = frame_id
        self.timestamp = timestamp
        self.bboxes = []

    def add_bbox(self, bbox_id: int, top: int, left: int, width: int, height: int):
        bboxes_ids = [bbox.bbox_id for bbox in self.bboxes]
        if bbox_id not in bboxes_ids:
            self.bboxes.append(Bbox(bbox_id, top, left, width, height))
        else:
            raise ValueError('Frame with id: {} already has a Bbox with id: {}'.format(self.frame_id, bbox_id))

    def add_label_to_bbox(self, bbox_id: int, category: str, confidence: float):
        bboxes = {bbox.id: bbox for bbox in self.bboxes}
        if bbox_id in bboxes.keys():
            res = bboxes.get(bbox_id)
            res.add_label(category, confidence)
        else:
            raise ValueError('the bbox with id: {} does not exists!'.format(bbox_id))

def add_bbox(self, bbox_id: int, top: int, left: int, width: int, height: int):
    bboxes_ids = [bbox.bbox_id for bbox in self.bboxes]
    if bbox_id not in bboxes_ids:
        self.bboxes.append(Bbox(bbox_id, top, left, width, height))
    else:
        raise ValueError('Frame with id: {} already has a Bbox with id: {}'.format(self.frame_id, bbox_id))

def add_label_to_bbox(self, bbox_id: int, category: str, confidence: float):
    bboxes = {bbox.id: bbox for bbox in self.bboxes}
    if bbox_id in bboxes.keys():
        res = bboxes.get(bbox_id)
        res.add_label(category, confidence)
    else:
        raise ValueError('the bbox with id: {} does not exists!'.format(bbox_id))

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

def download_url(url, dst):
    """Downloads file from a url to a destination.

    Args:
        url (str): url to download file.
        dst (str): destination path.
    """
    from six.moves import urllib
    print('* url="{}"'.format(url))
    print('* destination="{}"'.format(dst))

    def _reporthook(count, block_size, total_size):
        global start_time
        if count == 0:
            start_time = time.time()
            return
        duration = time.time() - start_time
        progress_size = int(count * block_size)
        speed = int(progress_size / (1024 * duration))
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write('\r...%d%%, %d MB, %d KB/s, %d seconds passed' % (percent, progress_size / (1024 * 1024), speed, duration))
        sys.stdout.flush()
    urllib.request.urlretrieve(url, dst, _reporthook)
    sys.stdout.write('\n')

def _reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write('\r...%d%%, %d MB, %d KB/s, %d seconds passed' % (percent, progress_size / (1024 * 1024), speed, duration))
    sys.stdout.flush()

class HACNN(nn.Module):
    """Harmonious Attention Convolutional Neural Network.

    Reference:
        Li et al. Harmonious Attention Network for Person Re-identification. CVPR 2018.

    Public keys:
        - ``hacnn``: HACNN.
    """

    def __init__(self, num_classes, loss='softmax', nchannels=[128, 256, 384], feat_dim=512, learn_region=True, use_gpu=True, **kwargs):
        super(HACNN, self).__init__()
        self.loss = loss
        self.learn_region = learn_region
        self.use_gpu = use_gpu
        self.conv = ConvBlock(3, 32, 3, s=2, p=1)
        self.inception1 = nn.Sequential(InceptionA(32, nchannels[0]), InceptionB(nchannels[0], nchannels[0]))
        self.ha1 = HarmAttn(nchannels[0])
        self.inception2 = nn.Sequential(InceptionA(nchannels[0], nchannels[1]), InceptionB(nchannels[1], nchannels[1]))
        self.ha2 = HarmAttn(nchannels[1])
        self.inception3 = nn.Sequential(InceptionA(nchannels[1], nchannels[2]), InceptionB(nchannels[2], nchannels[2]))
        self.ha3 = HarmAttn(nchannels[2])
        self.fc_global = nn.Sequential(nn.Linear(nchannels[2], feat_dim), nn.BatchNorm1d(feat_dim), nn.ReLU())
        self.classifier_global = nn.Linear(feat_dim, num_classes)
        if self.learn_region:
            self.init_scale_factors()
            self.local_conv1 = InceptionB(32, nchannels[0])
            self.local_conv2 = InceptionB(nchannels[0], nchannels[1])
            self.local_conv3 = InceptionB(nchannels[1], nchannels[2])
            self.fc_local = nn.Sequential(nn.Linear(nchannels[2] * 4, feat_dim), nn.BatchNorm1d(feat_dim), nn.ReLU())
            self.classifier_local = nn.Linear(feat_dim, num_classes)
            self.feat_dim = feat_dim * 2
        else:
            self.feat_dim = feat_dim

    def init_scale_factors(self):
        self.scale_factors = []
        self.scale_factors.append(torch.tensor([[1, 0], [0, 0.25]], dtype=torch.float))
        self.scale_factors.append(torch.tensor([[1, 0], [0, 0.25]], dtype=torch.float))
        self.scale_factors.append(torch.tensor([[1, 0], [0, 0.25]], dtype=torch.float))
        self.scale_factors.append(torch.tensor([[1, 0], [0, 0.25]], dtype=torch.float))

    def stn(self, x, theta):
        """Performs spatial transform
        
        x: (batch, channel, height, width)
        theta: (batch, 2, 3)
        """
        grid = F.affine_grid(theta, x.size())
        x = F.grid_sample(x, grid)
        return x

    def transform_theta(self, theta_i, region_idx):
        """Transforms theta to include (s_w, s_h), resulting in (batch, 2, 3)"""
        scale_factors = self.scale_factors[region_idx]
        theta = torch.zeros(theta_i.size(0), 2, 3)
        theta[:, :, :2] = scale_factors
        theta[:, :, -1] = theta_i
        if self.use_gpu:
            theta = theta.cuda()
        return theta

    def forward(self, x):
        assert x.size(2) == 160 and x.size(3) == 64, 'Input size does not match, expected (160, 64) but got ({}, {})'.format(x.size(2), x.size(3))
        x = self.conv(x)
        x1 = self.inception1(x)
        x1_attn, x1_theta = self.ha1(x1)
        x1_out = x1 * x1_attn
        if self.learn_region:
            x1_local_list = []
            for region_idx in range(4):
                x1_theta_i = x1_theta[:, region_idx, :]
                x1_theta_i = self.transform_theta(x1_theta_i, region_idx)
                x1_trans_i = self.stn(x, x1_theta_i)
                x1_trans_i = F.upsample(x1_trans_i, (24, 28), mode='bilinear', align_corners=True)
                x1_local_i = self.local_conv1(x1_trans_i)
                x1_local_list.append(x1_local_i)
        x2 = self.inception2(x1_out)
        x2_attn, x2_theta = self.ha2(x2)
        x2_out = x2 * x2_attn
        if self.learn_region:
            x2_local_list = []
            for region_idx in range(4):
                x2_theta_i = x2_theta[:, region_idx, :]
                x2_theta_i = self.transform_theta(x2_theta_i, region_idx)
                x2_trans_i = self.stn(x1_out, x2_theta_i)
                x2_trans_i = F.upsample(x2_trans_i, (12, 14), mode='bilinear', align_corners=True)
                x2_local_i = x2_trans_i + x1_local_list[region_idx]
                x2_local_i = self.local_conv2(x2_local_i)
                x2_local_list.append(x2_local_i)
        x3 = self.inception3(x2_out)
        x3_attn, x3_theta = self.ha3(x3)
        x3_out = x3 * x3_attn
        if self.learn_region:
            x3_local_list = []
            for region_idx in range(4):
                x3_theta_i = x3_theta[:, region_idx, :]
                x3_theta_i = self.transform_theta(x3_theta_i, region_idx)
                x3_trans_i = self.stn(x2_out, x3_theta_i)
                x3_trans_i = F.upsample(x3_trans_i, (6, 7), mode='bilinear', align_corners=True)
                x3_local_i = x3_trans_i + x2_local_list[region_idx]
                x3_local_i = self.local_conv3(x3_local_i)
                x3_local_list.append(x3_local_i)
        x_global = F.avg_pool2d(x3_out, x3_out.size()[2:]).view(x3_out.size(0), x3_out.size(1))
        x_global = self.fc_global(x_global)
        if self.learn_region:
            x_local_list = []
            for region_idx in range(4):
                x_local_i = x3_local_list[region_idx]
                x_local_i = F.avg_pool2d(x_local_i, x_local_i.size()[2:]).view(x_local_i.size(0), -1)
                x_local_list.append(x_local_i)
            x_local = torch.cat(x_local_list, 1)
            x_local = self.fc_local(x_local)
        if not self.training:
            if self.learn_region:
                x_global = x_global / x_global.norm(p=2, dim=1, keepdim=True)
                x_local = x_local / x_local.norm(p=2, dim=1, keepdim=True)
                return torch.cat([x_global, x_local], 1)
            else:
                return x_global
        prelogits_global = self.classifier_global(x_global)
        if self.learn_region:
            prelogits_local = self.classifier_local(x_local)
        if self.loss == 'softmax':
            if self.learn_region:
                return (prelogits_global, prelogits_local)
            else:
                return prelogits_global
        elif self.loss == 'triplet':
            if self.learn_region:
                return ((prelogits_global, prelogits_local), (x_global, x_local))
            else:
                return (prelogits_global, x_global)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    assert x.size(2) == 160 and x.size(3) == 64, 'Input size does not match, expected (160, 64) but got ({}, {})'.format(x.size(2), x.size(3))
    x = self.conv(x)
    x1 = self.inception1(x)
    x1_attn, x1_theta = self.ha1(x1)
    x1_out = x1 * x1_attn
    if self.learn_region:
        x1_local_list = []
        for region_idx in range(4):
            x1_theta_i = x1_theta[:, region_idx, :]
            x1_theta_i = self.transform_theta(x1_theta_i, region_idx)
            x1_trans_i = self.stn(x, x1_theta_i)
            x1_trans_i = F.upsample(x1_trans_i, (24, 28), mode='bilinear', align_corners=True)
            x1_local_i = self.local_conv1(x1_trans_i)
            x1_local_list.append(x1_local_i)
    x2 = self.inception2(x1_out)
    x2_attn, x2_theta = self.ha2(x2)
    x2_out = x2 * x2_attn
    if self.learn_region:
        x2_local_list = []
        for region_idx in range(4):
            x2_theta_i = x2_theta[:, region_idx, :]
            x2_theta_i = self.transform_theta(x2_theta_i, region_idx)
            x2_trans_i = self.stn(x1_out, x2_theta_i)
            x2_trans_i = F.upsample(x2_trans_i, (12, 14), mode='bilinear', align_corners=True)
            x2_local_i = x2_trans_i + x1_local_list[region_idx]
            x2_local_i = self.local_conv2(x2_local_i)
            x2_local_list.append(x2_local_i)
    x3 = self.inception3(x2_out)
    x3_attn, x3_theta = self.ha3(x3)
    x3_out = x3 * x3_attn
    if self.learn_region:
        x3_local_list = []
        for region_idx in range(4):
            x3_theta_i = x3_theta[:, region_idx, :]
            x3_theta_i = self.transform_theta(x3_theta_i, region_idx)
            x3_trans_i = self.stn(x2_out, x3_theta_i)
            x3_trans_i = F.upsample(x3_trans_i, (6, 7), mode='bilinear', align_corners=True)
            x3_local_i = x3_trans_i + x2_local_list[region_idx]
            x3_local_i = self.local_conv3(x3_local_i)
            x3_local_list.append(x3_local_i)
    x_global = F.avg_pool2d(x3_out, x3_out.size()[2:]).view(x3_out.size(0), x3_out.size(1))
    x_global = self.fc_global(x_global)
    if self.learn_region:
        x_local_list = []
        for region_idx in range(4):
            x_local_i = x3_local_list[region_idx]
            x_local_i = F.avg_pool2d(x_local_i, x_local_i.size()[2:]).view(x_local_i.size(0), -1)
            x_local_list.append(x_local_i)
        x_local = torch.cat(x_local_list, 1)
        x_local = self.fc_local(x_local)
    if not self.training:
        if self.learn_region:
            x_global = x_global / x_global.norm(p=2, dim=1, keepdim=True)
            x_local = x_local / x_local.norm(p=2, dim=1, keepdim=True)
            return torch.cat([x_global, x_local], 1)
        else:
            return x_global
    prelogits_global = self.classifier_global(x_global)
    if self.learn_region:
        prelogits_local = self.classifier_local(x_local)
    if self.loss == 'softmax':
        if self.learn_region:
            return (prelogits_global, prelogits_local)
        else:
            return prelogits_global
    elif self.loss == 'triplet':
        if self.learn_region:
            return ((prelogits_global, prelogits_local), (x_global, x_local))
        else:
            return (prelogits_global, x_global)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class MuDeep(nn.Module):
    """Multiscale deep neural network.

    Reference:
        Qian et al. Multi-scale Deep Learning Architectures
        for Person Re-identification. ICCV 2017.

    Public keys:
        - ``mudeep``: Multiscale deep neural network.
    """

    def __init__(self, num_classes, loss='softmax', **kwargs):
        super(MuDeep, self).__init__()
        self.loss = loss
        self.block1 = ConvLayers()
        self.block2 = MultiScaleA()
        self.block3 = Reduction()
        self.block4 = MultiScaleB()
        self.block5 = Fusion()
        self.fc = nn.Sequential(nn.Linear(256 * 16 * 8, 4096), nn.BatchNorm1d(4096), nn.ReLU())
        self.classifier = nn.Linear(4096, num_classes)
        self.feat_dim = 4096

    def featuremaps(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.block5(*x)
        return x

    def forward(self, x):
        x = self.featuremaps(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        y = self.classifier(x)
        if not self.training:
            return x
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, x)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    x = self.featuremaps(x)
    x = x.view(x.size(0), -1)
    x = self.fc(x)
    y = self.classifier(x)
    if not self.training:
        return x
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, x)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class InceptionResNetV2(nn.Module):
    """Inception-ResNet-V2.

    Reference:
        Szegedy et al. Inception-v4, Inception-ResNet and the Impact of Residual
        Connections on Learning. AAAI 2017.

    Public keys:
        - ``inceptionresnetv2``: Inception-ResNet-V2.
    """

    def __init__(self, num_classes, loss='softmax', **kwargs):
        super(InceptionResNetV2, self).__init__()
        self.loss = loss
        self.conv2d_1a = BasicConv2d(3, 32, kernel_size=3, stride=2)
        self.conv2d_2a = BasicConv2d(32, 32, kernel_size=3, stride=1)
        self.conv2d_2b = BasicConv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.maxpool_3a = nn.MaxPool2d(3, stride=2)
        self.conv2d_3b = BasicConv2d(64, 80, kernel_size=1, stride=1)
        self.conv2d_4a = BasicConv2d(80, 192, kernel_size=3, stride=1)
        self.maxpool_5a = nn.MaxPool2d(3, stride=2)
        self.mixed_5b = Mixed_5b()
        self.repeat = nn.Sequential(Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17), Block35(scale=0.17))
        self.mixed_6a = Mixed_6a()
        self.repeat_1 = nn.Sequential(Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1), Block17(scale=0.1))
        self.mixed_7a = Mixed_7a()
        self.repeat_2 = nn.Sequential(Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2), Block8(scale=0.2))
        self.block8 = Block8(noReLU=True)
        self.conv2d_7b = BasicConv2d(2080, 1536, kernel_size=1, stride=1)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(1536, num_classes)

    def load_imagenet_weights(self):
        settings = pretrained_settings['inceptionresnetv2']['imagenet']
        pretrain_dict = model_zoo.load_url(settings['url'])
        model_dict = self.state_dict()
        pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
        model_dict.update(pretrain_dict)
        self.load_state_dict(model_dict)

    def featuremaps(self, x):
        x = self.conv2d_1a(x)
        x = self.conv2d_2a(x)
        x = self.conv2d_2b(x)
        x = self.maxpool_3a(x)
        x = self.conv2d_3b(x)
        x = self.conv2d_4a(x)
        x = self.maxpool_5a(x)
        x = self.mixed_5b(x)
        x = self.repeat(x)
        x = self.mixed_6a(x)
        x = self.repeat_1(x)
        x = self.mixed_7a(x)
        x = self.repeat_2(x)
        x = self.block8(x)
        x = self.conv2d_7b(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.featuremaps(x)
    v = self.global_avgpool(f)
    v = v.view(v.size(0), -1)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class ResNet(nn.Module):
    """Residual network + IBN layer.
    
    Reference:
        - He et al. Deep Residual Learning for Image Recognition. CVPR 2016.
        - Pan et al. Two at Once: Enhancing Learning and Generalization
          Capacities via IBN-Net. ECCV 2018.
    """

    def __init__(self, block, layers, num_classes=1000, loss='softmax', fc_dims=None, dropout_p=None, **kwargs):
        scale = 64
        self.inplanes = scale
        super(ResNet, self).__init__()
        self.loss = loss
        self.feature_dim = scale * 8 * block.expansion
        self.conv1 = nn.Conv2d(3, scale, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.InstanceNorm2d(scale, affine=True)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, scale, layers[0], stride=1, IN=True)
        self.layer2 = self._make_layer(block, scale * 2, layers[1], stride=2, IN=True)
        self.layer3 = self._make_layer(block, scale * 4, layers[2], stride=2)
        self.layer4 = self._make_layer(block, scale * 8, layers[3], stride=2)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = self._construct_fc_layer(fc_dims, scale * 8 * block.expansion, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2.0 / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.InstanceNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1, IN=False):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), nn.BatchNorm2d(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks - 1):
            layers.append(block(self.inplanes, planes))
        layers.append(block(self.inplanes, planes, IN=IN))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.featuremaps(x)
    v = self.avgpool(f)
    v = v.view(v.size(0), -1)
    if self.fc is not None:
        v = self.fc(v)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class NASNetAMobile(nn.Module):
    """Neural Architecture Search (NAS).

    Reference:
        Zoph et al. Learning Transferable Architectures
        for Scalable Image Recognition. CVPR 2018.

    Public keys:
        - ``nasnetamobile``: NASNet-A Mobile.
    """

    def __init__(self, num_classes, loss, stem_filters=32, penultimate_filters=1056, filters_multiplier=2, **kwargs):
        super(NASNetAMobile, self).__init__()
        self.stem_filters = stem_filters
        self.penultimate_filters = penultimate_filters
        self.filters_multiplier = filters_multiplier
        self.loss = loss
        filters = self.penultimate_filters // 24
        self.conv0 = nn.Sequential()
        self.conv0.add_module('conv', nn.Conv2d(in_channels=3, out_channels=self.stem_filters, kernel_size=3, padding=0, stride=2, bias=False))
        self.conv0.add_module('bn', nn.BatchNorm2d(self.stem_filters, eps=0.001, momentum=0.1, affine=True))
        self.cell_stem_0 = CellStem0(self.stem_filters, num_filters=filters // filters_multiplier ** 2)
        self.cell_stem_1 = CellStem1(self.stem_filters, num_filters=filters // filters_multiplier)
        self.cell_0 = FirstCell(in_channels_left=filters, out_channels_left=filters // 2, in_channels_right=2 * filters, out_channels_right=filters)
        self.cell_1 = NormalCell(in_channels_left=2 * filters, out_channels_left=filters, in_channels_right=6 * filters, out_channels_right=filters)
        self.cell_2 = NormalCell(in_channels_left=6 * filters, out_channels_left=filters, in_channels_right=6 * filters, out_channels_right=filters)
        self.cell_3 = NormalCell(in_channels_left=6 * filters, out_channels_left=filters, in_channels_right=6 * filters, out_channels_right=filters)
        self.reduction_cell_0 = ReductionCell0(in_channels_left=6 * filters, out_channels_left=2 * filters, in_channels_right=6 * filters, out_channels_right=2 * filters)
        self.cell_6 = FirstCell(in_channels_left=6 * filters, out_channels_left=filters, in_channels_right=8 * filters, out_channels_right=2 * filters)
        self.cell_7 = NormalCell(in_channels_left=8 * filters, out_channels_left=2 * filters, in_channels_right=12 * filters, out_channels_right=2 * filters)
        self.cell_8 = NormalCell(in_channels_left=12 * filters, out_channels_left=2 * filters, in_channels_right=12 * filters, out_channels_right=2 * filters)
        self.cell_9 = NormalCell(in_channels_left=12 * filters, out_channels_left=2 * filters, in_channels_right=12 * filters, out_channels_right=2 * filters)
        self.reduction_cell_1 = ReductionCell1(in_channels_left=12 * filters, out_channels_left=4 * filters, in_channels_right=12 * filters, out_channels_right=4 * filters)
        self.cell_12 = FirstCell(in_channels_left=12 * filters, out_channels_left=2 * filters, in_channels_right=16 * filters, out_channels_right=4 * filters)
        self.cell_13 = NormalCell(in_channels_left=16 * filters, out_channels_left=4 * filters, in_channels_right=24 * filters, out_channels_right=4 * filters)
        self.cell_14 = NormalCell(in_channels_left=24 * filters, out_channels_left=4 * filters, in_channels_right=24 * filters, out_channels_right=4 * filters)
        self.cell_15 = NormalCell(in_channels_left=24 * filters, out_channels_left=4 * filters, in_channels_right=24 * filters, out_channels_right=4 * filters)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout()
        self.classifier = nn.Linear(24 * filters, num_classes)
        self._init_params()

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def features(self, input):
        x_conv0 = self.conv0(input)
        x_stem_0 = self.cell_stem_0(x_conv0)
        x_stem_1 = self.cell_stem_1(x_conv0, x_stem_0)
        x_cell_0 = self.cell_0(x_stem_1, x_stem_0)
        x_cell_1 = self.cell_1(x_cell_0, x_stem_1)
        x_cell_2 = self.cell_2(x_cell_1, x_cell_0)
        x_cell_3 = self.cell_3(x_cell_2, x_cell_1)
        x_reduction_cell_0 = self.reduction_cell_0(x_cell_3, x_cell_2)
        x_cell_6 = self.cell_6(x_reduction_cell_0, x_cell_3)
        x_cell_7 = self.cell_7(x_cell_6, x_reduction_cell_0)
        x_cell_8 = self.cell_8(x_cell_7, x_cell_6)
        x_cell_9 = self.cell_9(x_cell_8, x_cell_7)
        x_reduction_cell_1 = self.reduction_cell_1(x_cell_9, x_cell_8)
        x_cell_12 = self.cell_12(x_reduction_cell_1, x_cell_9)
        x_cell_13 = self.cell_13(x_cell_12, x_reduction_cell_1)
        x_cell_14 = self.cell_14(x_cell_13, x_cell_12)
        x_cell_15 = self.cell_15(x_cell_14, x_cell_13)
        x_cell_15 = self.relu(x_cell_15)
        x_cell_15 = F.avg_pool2d(x_cell_15, x_cell_15.size()[2:])
        x_cell_15 = x_cell_15.view(x_cell_15.size(0), -1)
        x_cell_15 = self.dropout(x_cell_15)
        return x_cell_15

    def forward(self, input):
        v = self.features(input)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, input):
    v = self.features(input)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class DenseNet(nn.Module):
    """Densely connected network.
    
    Reference:
        Huang et al. Densely Connected Convolutional Networks. CVPR 2017.

    Public keys:
        - ``densenet121``: DenseNet121.
        - ``densenet169``: DenseNet169.
        - ``densenet201``: DenseNet201.
        - ``densenet161``: DenseNet161.
        - ``densenet121_fc512``: DenseNet121 + FC.
    """

    def __init__(self, num_classes, loss, growth_rate=32, block_config=(6, 12, 24, 16), num_init_features=64, bn_size=4, drop_rate=0, fc_dims=None, dropout_p=None, **kwargs):
        super(DenseNet, self).__init__()
        self.loss = loss
        self.features = nn.Sequential(OrderedDict([('conv0', nn.Conv2d(3, num_init_features, kernel_size=7, stride=2, padding=3, bias=False)), ('norm0', nn.BatchNorm2d(num_init_features)), ('relu0', nn.ReLU(inplace=True)), ('pool0', nn.MaxPool2d(kernel_size=3, stride=2, padding=1))]))
        num_features = num_init_features
        for i, num_layers in enumerate(block_config):
            block = _DenseBlock(num_layers=num_layers, num_input_features=num_features, bn_size=bn_size, growth_rate=growth_rate, drop_rate=drop_rate)
            self.features.add_module('denseblock%d' % (i + 1), block)
            num_features = num_features + num_layers * growth_rate
            if i != len(block_config) - 1:
                trans = _Transition(num_input_features=num_features, num_output_features=num_features // 2)
                self.features.add_module('transition%d' % (i + 1), trans)
                num_features = num_features // 2
        self.features.add_module('norm5', nn.BatchNorm2d(num_features))
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.feature_dim = num_features
        self.fc = self._construct_fc_layer(fc_dims, num_features, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer.

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        f = self.features(x)
        f = F.relu(f, inplace=True)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.features(x)
    f = F.relu(f, inplace=True)
    v = self.global_avgpool(f)
    v = v.view(v.size(0), -1)
    if self.fc is not None:
        v = self.fc(v)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

def shufflenet(num_classes, loss='softmax', pretrained=True, **kwargs):
    model = ShuffleNet(num_classes, loss, **kwargs)
    if pretrained:
        import warnings
        warnings.warn('The imagenet pretrained weights need to be manually downloaded from {}'.format(model_urls['imagenet']))
    return model

class SENet(nn.Module):
    """Squeeze-and-excitation network.
    
    Reference:
        Hu et al. Squeeze-and-Excitation Networks. CVPR 2018.

    Public keys:
        - ``senet154``: SENet154.
        - ``se_resnet50``: ResNet50 + SE.
        - ``se_resnet101``: ResNet101 + SE.
        - ``se_resnet152``: ResNet152 + SE.
        - ``se_resnext50_32x4d``: ResNeXt50 (groups=32, width=4) + SE.
        - ``se_resnext101_32x4d``: ResNeXt101 (groups=32, width=4) + SE.
        - ``se_resnet50_fc512``: (ResNet50 + SE) + FC.
    """

    def __init__(self, num_classes, loss, block, layers, groups, reduction, dropout_p=0.2, inplanes=128, input_3x3=True, downsample_kernel_size=3, downsample_padding=1, last_stride=2, fc_dims=None, **kwargs):
        """
        Parameters
        ----------
        block (nn.Module): Bottleneck class.
            - For SENet154: SEBottleneck
            - For SE-ResNet models: SEResNetBottleneck
            - For SE-ResNeXt models:  SEResNeXtBottleneck
        layers (list of ints): Number of residual blocks for 4 layers of the
            network (layer1...layer4).
        groups (int): Number of groups for the 3x3 convolution in each
            bottleneck block.
            - For SENet154: 64
            - For SE-ResNet models: 1
            - For SE-ResNeXt models:  32
        reduction (int): Reduction ratio for Squeeze-and-Excitation modules.
            - For all models: 16
        dropout_p (float or None): Drop probability for the Dropout layer.
            If `None` the Dropout layer is not used.
            - For SENet154: 0.2
            - For SE-ResNet models: None
            - For SE-ResNeXt models: None
        inplanes (int):  Number of input channels for layer1.
            - For SENet154: 128
            - For SE-ResNet models: 64
            - For SE-ResNeXt models: 64
        input_3x3 (bool): If `True`, use three 3x3 convolutions instead of
            a single 7x7 convolution in layer0.
            - For SENet154: True
            - For SE-ResNet models: False
            - For SE-ResNeXt models: False
        downsample_kernel_size (int): Kernel size for downsampling convolutions
            in layer2, layer3 and layer4.
            - For SENet154: 3
            - For SE-ResNet models: 1
            - For SE-ResNeXt models: 1
        downsample_padding (int): Padding for downsampling convolutions in
            layer2, layer3 and layer4.
            - For SENet154: 1
            - For SE-ResNet models: 0
            - For SE-ResNeXt models: 0
        num_classes (int): Number of outputs in `classifier` layer.
        """
        super(SENet, self).__init__()
        self.inplanes = inplanes
        self.loss = loss
        if input_3x3:
            layer0_modules = [('conv1', nn.Conv2d(3, 64, 3, stride=2, padding=1, bias=False)), ('bn1', nn.BatchNorm2d(64)), ('relu1', nn.ReLU(inplace=True)), ('conv2', nn.Conv2d(64, 64, 3, stride=1, padding=1, bias=False)), ('bn2', nn.BatchNorm2d(64)), ('relu2', nn.ReLU(inplace=True)), ('conv3', nn.Conv2d(64, inplanes, 3, stride=1, padding=1, bias=False)), ('bn3', nn.BatchNorm2d(inplanes)), ('relu3', nn.ReLU(inplace=True))]
        else:
            layer0_modules = [('conv1', nn.Conv2d(3, inplanes, kernel_size=7, stride=2, padding=3, bias=False)), ('bn1', nn.BatchNorm2d(inplanes)), ('relu1', nn.ReLU(inplace=True))]
        layer0_modules.append(('pool', nn.MaxPool2d(3, stride=2, ceil_mode=True)))
        self.layer0 = nn.Sequential(OrderedDict(layer0_modules))
        self.layer1 = self._make_layer(block, planes=64, blocks=layers[0], groups=groups, reduction=reduction, downsample_kernel_size=1, downsample_padding=0)
        self.layer2 = self._make_layer(block, planes=128, blocks=layers[1], stride=2, groups=groups, reduction=reduction, downsample_kernel_size=downsample_kernel_size, downsample_padding=downsample_padding)
        self.layer3 = self._make_layer(block, planes=256, blocks=layers[2], stride=2, groups=groups, reduction=reduction, downsample_kernel_size=downsample_kernel_size, downsample_padding=downsample_padding)
        self.layer4 = self._make_layer(block, planes=512, blocks=layers[3], stride=last_stride, groups=groups, reduction=reduction, downsample_kernel_size=downsample_kernel_size, downsample_padding=downsample_padding)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = self._construct_fc_layer(fc_dims, 512 * block.expansion, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)

    def _make_layer(self, block, planes, blocks, groups, reduction, stride=1, downsample_kernel_size=1, downsample_padding=0):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=downsample_kernel_size, stride=stride, padding=downsample_padding, bias=False), nn.BatchNorm2d(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, groups, reduction, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes, groups, reduction))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """
        Construct fully connected layer

        - fc_dims (list or tuple): dimensions of fc layers, if None,
                                   no fc layers are constructed
        - input_dim (int): input dimension
        - dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def featuremaps(self, x):
        x = self.layer0(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.featuremaps(x)
    v = self.global_avgpool(f)
    v = v.view(v.size(0), -1)
    if self.fc is not None:
        v = self.fc(v)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class SqueezeNet(nn.Module):
    """SqueezeNet.

    Reference:
        Iandola et al. SqueezeNet: AlexNet-level accuracy with 50x fewer parameters
        and< 0.5 MB model size. arXiv:1602.07360.

    Public keys:
        - ``squeezenet1_0``: SqueezeNet (version=1.0).
        - ``squeezenet1_1``: SqueezeNet (version=1.1).
        - ``squeezenet1_0_fc512``: SqueezeNet (version=1.0) + FC.
    """

    def __init__(self, num_classes, loss, version=1.0, fc_dims=None, dropout_p=None, **kwargs):
        super(SqueezeNet, self).__init__()
        self.loss = loss
        self.feature_dim = 512
        if version not in [1.0, 1.1]:
            raise ValueError('Unsupported SqueezeNet version {version}:1.0 or 1.1 expected'.format(version=version))
        if version == 1.0:
            self.features = nn.Sequential(nn.Conv2d(3, 96, kernel_size=7, stride=2), nn.ReLU(inplace=True), nn.MaxPool2d(kernel_size=3, stride=2, ceil_mode=True), Fire(96, 16, 64, 64), Fire(128, 16, 64, 64), Fire(128, 32, 128, 128), nn.MaxPool2d(kernel_size=3, stride=2, ceil_mode=True), Fire(256, 32, 128, 128), Fire(256, 48, 192, 192), Fire(384, 48, 192, 192), Fire(384, 64, 256, 256), nn.MaxPool2d(kernel_size=3, stride=2, ceil_mode=True), Fire(512, 64, 256, 256))
        else:
            self.features = nn.Sequential(nn.Conv2d(3, 64, kernel_size=3, stride=2), nn.ReLU(inplace=True), nn.MaxPool2d(kernel_size=3, stride=2, ceil_mode=True), Fire(64, 16, 64, 64), Fire(128, 16, 64, 64), nn.MaxPool2d(kernel_size=3, stride=2, ceil_mode=True), Fire(128, 32, 128, 128), Fire(256, 32, 128, 128), nn.MaxPool2d(kernel_size=3, stride=2, ceil_mode=True), Fire(256, 48, 192, 192), Fire(384, 48, 192, 192), Fire(384, 64, 256, 256), Fire(512, 64, 256, 256))
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = self._construct_fc_layer(fc_dims, 512, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        f = self.features(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.features(x)
    v = self.global_avgpool(f)
    v = v.view(v.size(0), -1)
    if self.fc is not None:
        v = self.fc(v)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

def build_model(name, num_classes, loss='softmax', pretrained=True, use_gpu=True):
    """A function wrapper for building a model.

    Args:
        name (str): model name.
        num_classes (int): number of training identities.
        loss (str, optional): loss function to optimize the model. Currently
            supports "softmax" and "triplet". Default is "softmax".
        pretrained (bool, optional): whether to load ImageNet-pretrained weights.
            Default is True.
        use_gpu (bool, optional): whether to use gpu. Default is True.

    Returns:
        nn.Module

    Examples::
        >>> from torchreid import models
        >>> model = models.build_model('resnet50', 751, loss='softmax')
    """
    avai_models = list(__model_factory.keys())
    if name not in avai_models:
        raise KeyError('Unknown model: {}. Must be one of {}'.format(name, avai_models))
    return __model_factory[name](num_classes=num_classes, loss=loss, pretrained=pretrained, use_gpu=use_gpu)

class MobileNetV2(nn.Module):
    """MobileNetV2.

    Reference:
        Sandler et al. MobileNetV2: Inverted Residuals and
        Linear Bottlenecks. CVPR 2018.

    Public keys:
        - ``mobilenetv2_x1_0``: MobileNetV2 x1.0.
        - ``mobilenetv2_x1_4``: MobileNetV2 x1.4.
    """

    def __init__(self, num_classes, width_mult=1, loss='softmax', fc_dims=None, dropout_p=None, **kwargs):
        super(MobileNetV2, self).__init__()
        self.loss = loss
        self.in_channels = int(32 * width_mult)
        self.feature_dim = int(1280 * width_mult) if width_mult > 1 else 1280
        self.conv1 = ConvBlock(3, self.in_channels, 3, s=2, p=1)
        self.conv2 = self._make_layer(Bottleneck, 1, int(16 * width_mult), 1, 1)
        self.conv3 = self._make_layer(Bottleneck, 6, int(24 * width_mult), 2, 2)
        self.conv4 = self._make_layer(Bottleneck, 6, int(32 * width_mult), 3, 2)
        self.conv5 = self._make_layer(Bottleneck, 6, int(64 * width_mult), 4, 2)
        self.conv6 = self._make_layer(Bottleneck, 6, int(96 * width_mult), 3, 1)
        self.conv7 = self._make_layer(Bottleneck, 6, int(160 * width_mult), 3, 2)
        self.conv8 = self._make_layer(Bottleneck, 6, int(320 * width_mult), 1, 1)
        self.conv9 = ConvBlock(self.in_channels, self.feature_dim, 1)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = self._construct_fc_layer(fc_dims, self.feature_dim, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _make_layer(self, block, t, c, n, s):
        layers = []
        layers.append(block(self.in_channels, c, t, s))
        self.in_channels = c
        for i in range(1, n):
            layers.append(block(self.in_channels, c, t))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer.

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        x = self.conv6(x)
        x = self.conv7(x)
        x = self.conv8(x)
        x = self.conv9(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.featuremaps(x)
    v = self.global_avgpool(f)
    v = v.view(v.size(0), -1)
    if self.fc is not None:
        v = self.fc(v)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

def mobilenetv2_x1_0(num_classes, loss, pretrained=True, **kwargs):
    model = MobileNetV2(num_classes, loss=loss, width_mult=1, fc_dims=None, dropout_p=None, **kwargs)
    if pretrained:
        import warnings
        warnings.warn('The imagenet pretrained weights need to be manually downloaded from {}'.format(model_urls['mobilenetv2_x1_0']))
    return model

def mobilenetv2_x1_4(num_classes, loss, pretrained=True, **kwargs):
    model = MobileNetV2(num_classes, loss=loss, width_mult=1.4, fc_dims=None, dropout_p=None, **kwargs)
    if pretrained:
        import warnings
        warnings.warn('The imagenet pretrained weights need to be manually downloaded from {}'.format(model_urls['mobilenetv2_x1_4']))
    return model

class ResNet(nn.Module):
    """Residual network.
    
    Reference:
        - He et al. Deep Residual Learning for Image Recognition. CVPR 2016.
        - Xie et al. Aggregated Residual Transformations for Deep Neural Networks. CVPR 2017.

    Public keys:
        - ``resnet18``: ResNet18.
        - ``resnet34``: ResNet34.
        - ``resnet50``: ResNet50.
        - ``resnet101``: ResNet101.
        - ``resnet152``: ResNet152.
        - ``resnext50_32x4d``: ResNeXt50.
        - ``resnext101_32x8d``: ResNeXt101.
        - ``resnet50_fc512``: ResNet50 + FC.
    """

    def __init__(self, num_classes, loss, block, layers, zero_init_residual=False, groups=1, width_per_group=64, replace_stride_with_dilation=None, norm_layer=None, last_stride=2, fc_dims=None, dropout_p=None, **kwargs):
        super(ResNet, self).__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d
        self._norm_layer = norm_layer
        self.loss = loss
        self.feature_dim = 512 * block.expansion
        self.inplanes = 64
        self.dilation = 1
        if replace_stride_with_dilation is None:
            replace_stride_with_dilation = [False, False, False]
        if len(replace_stride_with_dilation) != 3:
            raise ValueError('replace_stride_with_dilation should be None or a 3-element tuple, got {}'.format(replace_stride_with_dilation))
        self.groups = groups
        self.base_width = width_per_group
        self.conv1 = nn.Conv2d(3, self.inplanes, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = norm_layer(self.inplanes)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2, dilate=replace_stride_with_dilation[0])
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2, dilate=replace_stride_with_dilation[1])
        self.layer4 = self._make_layer(block, 512, layers[3], stride=last_stride, dilate=replace_stride_with_dilation[2])
        self.global_avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = self._construct_fc_layer(fc_dims, 512 * block.expansion, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()
        if zero_init_residual:
            for m in self.modules():
                if isinstance(m, Bottleneck):
                    nn.init.constant_(m.bn3.weight, 0)
                elif isinstance(m, BasicBlock):
                    nn.init.constant_(m.bn2.weight, 0)

    def _make_layer(self, block, planes, blocks, stride=1, dilate=False):
        norm_layer = self._norm_layer
        downsample = None
        previous_dilation = self.dilation
        if dilate:
            self.dilation *= stride
            stride = 1
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(conv1x1(self.inplanes, planes * block.expansion, stride), norm_layer(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample, self.groups, self.base_width, previous_dilation, norm_layer))
        self.inplanes = planes * block.expansion
        for _ in range(1, blocks):
            layers.append(block(self.inplanes, planes, groups=self.groups, base_width=self.base_width, dilation=self.dilation, norm_layer=norm_layer))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.featuremaps(x)
    v = self.global_avgpool(f)
    v = v.view(v.size(0), -1)
    if self.fc is not None:
        v = self.fc(v)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class OSNet(nn.Module):
    """Omni-Scale Network.
    
    Reference:
        - Zhou et al. Omni-Scale Feature Learning for Person Re-Identification. ICCV, 2019.
        - Zhou et al. Learning Generalisable Omni-Scale Representations
          for Person Re-Identification. TPAMI, 2021.
    """

    def __init__(self, num_classes, blocks, layers, channels, feature_dim=512, loss='softmax', IN=False, **kwargs):
        super(OSNet, self).__init__()
        num_blocks = len(blocks)
        assert num_blocks == len(layers)
        assert num_blocks == len(channels) - 1
        self.loss = loss
        self.feature_dim = feature_dim
        self.conv1 = ConvLayer(3, channels[0], 7, stride=2, padding=3, IN=IN)
        self.maxpool = nn.MaxPool2d(3, stride=2, padding=1)
        self.conv2 = self._make_layer(blocks[0], layers[0], channels[0], channels[1], reduce_spatial_size=True, IN=IN)
        self.conv3 = self._make_layer(blocks[1], layers[1], channels[1], channels[2], reduce_spatial_size=True)
        self.conv4 = self._make_layer(blocks[2], layers[2], channels[2], channels[3], reduce_spatial_size=False)
        self.conv5 = Conv1x1(channels[3], channels[3])
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = self._construct_fc_layer(self.feature_dim, channels[3], dropout_p=None)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _make_layer(self, block, layer, in_channels, out_channels, reduce_spatial_size, IN=False):
        layers = []
        layers.append(block(in_channels, out_channels, IN=IN))
        for i in range(1, layer):
            layers.append(block(out_channels, out_channels, IN=IN))
        if reduce_spatial_size:
            layers.append(nn.Sequential(Conv1x1(out_channels, out_channels), nn.AvgPool2d(2, stride=2)))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        if fc_dims is None or fc_dims < 0:
            self.feature_dim = input_dim
            return None
        if isinstance(fc_dims, int):
            fc_dims = [fc_dims]
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.maxpool(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        return x

    def forward(self, x, return_featuremaps=False):
        x = self.featuremaps(x)
        if return_featuremaps:
            return x
        v = self.global_avgpool(x)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x, return_featuremaps=False):
    x = self.featuremaps(x)
    if return_featuremaps:
        return x
    v = self.global_avgpool(x)
    v = v.view(v.size(0), -1)
    if self.fc is not None:
        v = self.fc(v)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class ResNet(nn.Module):
    """Residual network + IBN layer.
    
    Reference:
        - He et al. Deep Residual Learning for Image Recognition. CVPR 2016.
        - Pan et al. Two at Once: Enhancing Learning and Generalization
          Capacities via IBN-Net. ECCV 2018.
    """

    def __init__(self, block, layers, num_classes=1000, loss='softmax', fc_dims=None, dropout_p=None, **kwargs):
        scale = 64
        self.inplanes = scale
        super(ResNet, self).__init__()
        self.loss = loss
        self.feature_dim = scale * 8 * block.expansion
        self.conv1 = nn.Conv2d(3, scale, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(scale)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, scale, layers[0])
        self.layer2 = self._make_layer(block, scale * 2, layers[1], stride=2)
        self.layer3 = self._make_layer(block, scale * 4, layers[2], stride=2)
        self.layer4 = self._make_layer(block, scale * 8, layers[3], stride=2)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = self._construct_fc_layer(fc_dims, scale * 8 * block.expansion, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2.0 / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.InstanceNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), nn.BatchNorm2d(planes * block.expansion))
        layers = []
        ibn = True
        if planes == 512:
            ibn = False
        layers.append(block(self.inplanes, planes, ibn, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes, ibn))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.featuremaps(x)
    v = self.avgpool(f)
    v = v.view(v.size(0), -1)
    if self.fc is not None:
        v = self.fc(v)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class ShuffleNetV2(nn.Module):
    """ShuffleNetV2.
    
    Reference:
        Ma et al. ShuffleNet V2: Practical Guidelines for Efficient CNN Architecture Design. ECCV 2018.

    Public keys:
        - ``shufflenet_v2_x0_5``: ShuffleNetV2 x0.5.
        - ``shufflenet_v2_x1_0``: ShuffleNetV2 x1.0.
        - ``shufflenet_v2_x1_5``: ShuffleNetV2 x1.5.
        - ``shufflenet_v2_x2_0``: ShuffleNetV2 x2.0.
    """

    def __init__(self, num_classes, loss, stages_repeats, stages_out_channels, **kwargs):
        super(ShuffleNetV2, self).__init__()
        self.loss = loss
        if len(stages_repeats) != 3:
            raise ValueError('expected stages_repeats as list of 3 positive ints')
        if len(stages_out_channels) != 5:
            raise ValueError('expected stages_out_channels as list of 5 positive ints')
        self._stage_out_channels = stages_out_channels
        input_channels = 3
        output_channels = self._stage_out_channels[0]
        self.conv1 = nn.Sequential(nn.Conv2d(input_channels, output_channels, 3, 2, 1, bias=False), nn.BatchNorm2d(output_channels), nn.ReLU(inplace=True))
        input_channels = output_channels
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        stage_names = ['stage{}'.format(i) for i in [2, 3, 4]]
        for name, repeats, output_channels in zip(stage_names, stages_repeats, self._stage_out_channels[1:]):
            seq = [InvertedResidual(input_channels, output_channels, 2)]
            for i in range(repeats - 1):
                seq.append(InvertedResidual(output_channels, output_channels, 1))
            setattr(self, name, nn.Sequential(*seq))
            input_channels = output_channels
        output_channels = self._stage_out_channels[-1]
        self.conv5 = nn.Sequential(nn.Conv2d(input_channels, output_channels, 1, 1, 0, bias=False), nn.BatchNorm2d(output_channels), nn.ReLU(inplace=True))
        self.global_avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Linear(output_channels, num_classes)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.maxpool(x)
        x = self.stage2(x)
        x = self.stage3(x)
        x = self.stage4(x)
        x = self.conv5(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.featuremaps(x)
    v = self.global_avgpool(f)
    v = v.view(v.size(0), -1)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class ResNetMid(nn.Module):
    """Residual network + mid-level features.
    
    Reference:
        Yu et al. The Devil is in the Middle: Exploiting Mid-level Representations for
        Cross-Domain Instance Matching. arXiv:1711.08106.

    Public keys:
        - ``resnet50mid``: ResNet50 + mid-level feature fusion.
    """

    def __init__(self, num_classes, loss, block, layers, last_stride=2, fc_dims=None, **kwargs):
        self.inplanes = 64
        super(ResNetMid, self).__init__()
        self.loss = loss
        self.feature_dim = 512 * block.expansion
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=last_stride)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        assert fc_dims is not None
        self.fc_fusion = self._construct_fc_layer(fc_dims, 512 * block.expansion * 2)
        self.feature_dim += 512 * block.expansion
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), nn.BatchNorm2d(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x4a = self.layer4[0](x)
        x4b = self.layer4[1](x4a)
        x4c = self.layer4[2](x4b)
        return (x4a, x4b, x4c)

    def forward(self, x):
        x4a, x4b, x4c = self.featuremaps(x)
        v4a = self.global_avgpool(x4a)
        v4b = self.global_avgpool(x4b)
        v4c = self.global_avgpool(x4c)
        v4ab = torch.cat([v4a, v4b], 1)
        v4ab = v4ab.view(v4ab.size(0), -1)
        v4ab = self.fc_fusion(v4ab)
        v4c = v4c.view(v4c.size(0), -1)
        v = torch.cat([v4ab, v4c], 1)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    x4a, x4b, x4c = self.featuremaps(x)
    v4a = self.global_avgpool(x4a)
    v4b = self.global_avgpool(x4b)
    v4c = self.global_avgpool(x4c)
    v4ab = torch.cat([v4a, v4b], 1)
    v4ab = v4ab.view(v4ab.size(0), -1)
    v4ab = self.fc_fusion(v4ab)
    v4c = v4c.view(v4c.size(0), -1)
    v = torch.cat([v4ab, v4c], 1)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class InceptionV4(nn.Module):
    """Inception-v4.

    Reference:
        Szegedy et al. Inception-v4, Inception-ResNet and the Impact of Residual
        Connections on Learning. AAAI 2017.

    Public keys:
        - ``inceptionv4``: InceptionV4.
    """

    def __init__(self, num_classes, loss, **kwargs):
        super(InceptionV4, self).__init__()
        self.loss = loss
        self.features = nn.Sequential(BasicConv2d(3, 32, kernel_size=3, stride=2), BasicConv2d(32, 32, kernel_size=3, stride=1), BasicConv2d(32, 64, kernel_size=3, stride=1, padding=1), Mixed_3a(), Mixed_4a(), Mixed_5a(), Inception_A(), Inception_A(), Inception_A(), Inception_A(), Reduction_A(), Inception_B(), Inception_B(), Inception_B(), Inception_B(), Inception_B(), Inception_B(), Inception_B(), Reduction_B(), Inception_C(), Inception_C(), Inception_C())
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(1536, num_classes)

    def forward(self, x):
        f = self.features(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.features(x)
    v = self.global_avgpool(f)
    v = v.view(v.size(0), -1)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class Xception(nn.Module):
    """Xception.
    
    Reference:
        Chollet. Xception: Deep Learning with Depthwise
        Separable Convolutions. CVPR 2017.

    Public keys:
        - ``xception``: Xception.
    """

    def __init__(self, num_classes, loss, fc_dims=None, dropout_p=None, **kwargs):
        super(Xception, self).__init__()
        self.loss = loss
        self.conv1 = nn.Conv2d(3, 32, 3, 2, 0, bias=False)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, 3, bias=False)
        self.bn2 = nn.BatchNorm2d(64)
        self.block1 = Block(64, 128, 2, 2, start_with_relu=False, grow_first=True)
        self.block2 = Block(128, 256, 2, 2, start_with_relu=True, grow_first=True)
        self.block3 = Block(256, 728, 2, 2, start_with_relu=True, grow_first=True)
        self.block4 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block5 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block6 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block7 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block8 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block9 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block10 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block11 = Block(728, 728, 3, 1, start_with_relu=True, grow_first=True)
        self.block12 = Block(728, 1024, 2, 2, start_with_relu=True, grow_first=False)
        self.conv3 = SeparableConv2d(1024, 1536, 3, 1, 1)
        self.bn3 = nn.BatchNorm2d(1536)
        self.conv4 = SeparableConv2d(1536, 2048, 3, 1, 1)
        self.bn4 = nn.BatchNorm2d(2048)
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.feature_dim = 2048
        self.fc = self._construct_fc_layer(fc_dims, 2048, dropout_p)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        """Constructs fully connected layer.

        Args:
            fc_dims (list or tuple): dimensions of fc layers, if None, no fc layers are constructed
            input_dim (int): input dimension
            dropout_p (float): dropout probability, if None, dropout is unused
        """
        if fc_dims is None:
            self.feature_dim = input_dim
            return None
        assert isinstance(fc_dims, (list, tuple)), 'fc_dims must be either list or tuple, but got {}'.format(type(fc_dims))
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU(inplace=True))
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, input):
        x = self.conv1(input)
        x = self.bn1(x)
        x = F.relu(x, inplace=True)
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x, inplace=True)
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.block5(x)
        x = self.block6(x)
        x = self.block7(x)
        x = self.block8(x)
        x = self.block9(x)
        x = self.block10(x)
        x = self.block11(x)
        x = self.block12(x)
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x, inplace=True)
        x = self.conv4(x)
        x = self.bn4(x)
        x = F.relu(x, inplace=True)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v = self.global_avgpool(f)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.featuremaps(x)
    v = self.global_avgpool(f)
    v = v.view(v.size(0), -1)
    if self.fc is not None:
        v = self.fc(v)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class PCB(nn.Module):
    """Part-based Convolutional Baseline.

    Reference:
        Sun et al. Beyond Part Models: Person Retrieval with Refined
        Part Pooling (and A Strong Convolutional Baseline). ECCV 2018.

    Public keys:
        - ``pcb_p4``: PCB with 4-part strips.
        - ``pcb_p6``: PCB with 6-part strips.
    """

    def __init__(self, num_classes, loss, block, layers, parts=6, reduced_dim=256, nonlinear='relu', **kwargs):
        self.inplanes = 64
        super(PCB, self).__init__()
        self.loss = loss
        self.parts = parts
        self.feature_dim = 512 * block.expansion
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=1)
        self.parts_avgpool = nn.AdaptiveAvgPool2d((self.parts, 1))
        self.dropout = nn.Dropout(p=0.5)
        self.conv5 = DimReduceLayer(512 * block.expansion, reduced_dim, nonlinear=nonlinear)
        self.feature_dim = reduced_dim
        self.classifier = nn.ModuleList([nn.Linear(self.feature_dim, num_classes) for _ in range(self.parts)])
        self._init_params()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False), nn.BatchNorm2d(planes * block.expansion))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def forward(self, x):
        f = self.featuremaps(x)
        v_g = self.parts_avgpool(f)
        if not self.training:
            v_g = F.normalize(v_g, p=2, dim=1)
            return v_g.view(v_g.size(0), -1)
        v_g = self.dropout(v_g)
        v_h = self.conv5(v_g)
        y = []
        for i in range(self.parts):
            v_h_i = v_h[:, :, i, :]
            v_h_i = v_h_i.view(v_h_i.size(0), -1)
            y_i = self.classifier[i](v_h_i)
            y.append(y_i)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            v_g = F.normalize(v_g, p=2, dim=1)
            return (y, v_g.view(v_g.size(0), -1))
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    f = self.featuremaps(x)
    v_g = self.parts_avgpool(f)
    if not self.training:
        v_g = F.normalize(v_g, p=2, dim=1)
        return v_g.view(v_g.size(0), -1)
    v_g = self.dropout(v_g)
    v_h = self.conv5(v_g)
    y = []
    for i in range(self.parts):
        v_h_i = v_h[:, :, i, :]
        v_h_i = v_h_i.view(v_h_i.size(0), -1)
        y_i = self.classifier[i](v_h_i)
        y.append(y_i)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        v_g = F.normalize(v_g, p=2, dim=1)
        return (y, v_g.view(v_g.size(0), -1))
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class OSNet(nn.Module):
    """Omni-Scale Network.
    
    Reference:
        - Zhou et al. Omni-Scale Feature Learning for Person Re-Identification. ICCV, 2019.
        - Zhou et al. Learning Generalisable Omni-Scale Representations
          for Person Re-Identification. TPAMI, 2021.
    """

    def __init__(self, num_classes, blocks, layers, channels, feature_dim=512, loss='softmax', conv1_IN=False, **kwargs):
        super(OSNet, self).__init__()
        num_blocks = len(blocks)
        assert num_blocks == len(layers)
        assert num_blocks == len(channels) - 1
        self.loss = loss
        self.feature_dim = feature_dim
        self.conv1 = ConvLayer(3, channels[0], 7, stride=2, padding=3, IN=conv1_IN)
        self.maxpool = nn.MaxPool2d(3, stride=2, padding=1)
        self.conv2 = self._make_layer(blocks[0], layers[0], channels[0], channels[1])
        self.pool2 = nn.Sequential(Conv1x1(channels[1], channels[1]), nn.AvgPool2d(2, stride=2))
        self.conv3 = self._make_layer(blocks[1], layers[1], channels[1], channels[2])
        self.pool3 = nn.Sequential(Conv1x1(channels[2], channels[2]), nn.AvgPool2d(2, stride=2))
        self.conv4 = self._make_layer(blocks[2], layers[2], channels[2], channels[3])
        self.conv5 = Conv1x1(channels[3], channels[3])
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc = self._construct_fc_layer(self.feature_dim, channels[3], dropout_p=None)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self._init_params()

    def _make_layer(self, blocks, layer, in_channels, out_channels):
        layers = []
        layers += [blocks[0](in_channels, out_channels)]
        for i in range(1, len(blocks)):
            layers += [blocks[i](out_channels, out_channels)]
        return nn.Sequential(*layers)

    def _construct_fc_layer(self, fc_dims, input_dim, dropout_p=None):
        if fc_dims is None or fc_dims < 0:
            self.feature_dim = input_dim
            return None
        if isinstance(fc_dims, int):
            fc_dims = [fc_dims]
        layers = []
        for dim in fc_dims:
            layers.append(nn.Linear(input_dim, dim))
            layers.append(nn.BatchNorm1d(dim))
            layers.append(nn.ReLU())
            if dropout_p is not None:
                layers.append(nn.Dropout(p=dropout_p))
            input_dim = dim
        self.feature_dim = fc_dims[-1]
        return nn.Sequential(*layers)

    def _init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.InstanceNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def featuremaps(self, x):
        x = self.conv1(x)
        x = self.maxpool(x)
        x = self.conv2(x)
        x = self.pool2(x)
        x = self.conv3(x)
        x = self.pool3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        return x

    def forward(self, x, return_featuremaps=False):
        x = self.featuremaps(x)
        if return_featuremaps:
            return x
        v = self.global_avgpool(x)
        v = v.view(v.size(0), -1)
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x, return_featuremaps=False):
    x = self.featuremaps(x)
    if return_featuremaps:
        return x
    v = self.global_avgpool(x)
    v = v.view(v.size(0), -1)
    if self.fc is not None:
        v = self.fc(v)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

class MLFN(nn.Module):
    """Multi-Level Factorisation Net.

    Reference:
        Chang et al. Multi-Level Factorisation Net for
        Person Re-Identification. CVPR 2018.

    Public keys:
        - ``mlfn``: MLFN (Multi-Level Factorisation Net).
    """

    def __init__(self, num_classes, loss='softmax', groups=32, channels=[64, 256, 512, 1024, 2048], embed_dim=1024, **kwargs):
        super(MLFN, self).__init__()
        self.loss = loss
        self.groups = groups
        self.conv1 = nn.Conv2d(3, channels[0], 7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm2d(channels[0])
        self.maxpool = nn.MaxPool2d(3, stride=2, padding=1)
        self.feature = nn.ModuleList([MLFNBlock(channels[0], channels[1], 1, [128, 64], self.groups), MLFNBlock(channels[1], channels[1], 1, [128, 64], self.groups), MLFNBlock(channels[1], channels[1], 1, [128, 64], self.groups), MLFNBlock(channels[1], channels[2], 2, [256, 128], self.groups), MLFNBlock(channels[2], channels[2], 1, [256, 128], self.groups), MLFNBlock(channels[2], channels[2], 1, [256, 128], self.groups), MLFNBlock(channels[2], channels[2], 1, [256, 128], self.groups), MLFNBlock(channels[2], channels[3], 2, [512, 128], self.groups), MLFNBlock(channels[3], channels[3], 1, [512, 128], self.groups), MLFNBlock(channels[3], channels[3], 1, [512, 128], self.groups), MLFNBlock(channels[3], channels[3], 1, [512, 128], self.groups), MLFNBlock(channels[3], channels[3], 1, [512, 128], self.groups), MLFNBlock(channels[3], channels[3], 1, [512, 128], self.groups), MLFNBlock(channels[3], channels[4], 2, [512, 128], self.groups), MLFNBlock(channels[4], channels[4], 1, [512, 128], self.groups), MLFNBlock(channels[4], channels[4], 1, [512, 128], self.groups)])
        self.global_avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc_x = nn.Sequential(nn.Conv2d(channels[4], embed_dim, 1, bias=False), nn.BatchNorm2d(embed_dim), nn.ReLU(inplace=True))
        self.fc_s = nn.Sequential(nn.Conv2d(self.groups * 16, embed_dim, 1, bias=False), nn.BatchNorm2d(embed_dim), nn.ReLU(inplace=True))
        self.classifier = nn.Linear(embed_dim, num_classes)
        self.init_params()

    def init_params(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x, inplace=True)
        x = self.maxpool(x)
        s_hat = []
        for block in self.feature:
            x, s = block(x)
            s_hat.append(s)
        s_hat = torch.cat(s_hat, 1)
        x = self.global_avgpool(x)
        x = self.fc_x(x)
        s_hat = self.fc_s(s_hat)
        v = (x + s_hat) * 0.5
        v = v.view(v.size(0), -1)
        if not self.training:
            return v
        y = self.classifier(v)
        if self.loss == 'softmax':
            return y
        elif self.loss == 'triplet':
            return (y, v)
        else:
            raise KeyError('Unsupported loss: {}'.format(self.loss))

def forward(self, x):
    x = self.conv1(x)
    x = self.bn1(x)
    x = F.relu(x, inplace=True)
    x = self.maxpool(x)
    s_hat = []
    for block in self.feature:
        x, s = block(x)
        s_hat.append(s)
    s_hat = torch.cat(s_hat, 1)
    x = self.global_avgpool(x)
    x = self.fc_x(x)
    s_hat = self.fc_s(s_hat)
    v = (x + s_hat) * 0.5
    v = v.view(v.size(0), -1)
    if not self.training:
        return v
    y = self.classifier(v)
    if self.loss == 'softmax':
        return y
    elif self.loss == 'triplet':
        return (y, v)
    else:
        raise KeyError('Unsupported loss: {}'.format(self.loss))

def mlfn(num_classes, loss='softmax', pretrained=True, **kwargs):
    model = MLFN(num_classes, loss, **kwargs)
    if pretrained:
        import warnings
        warnings.warn('The imagenet pretrained weights need to be manually downloaded from {}'.format(model_urls['imagenet']))
    return model

class STrack(BaseTrack):
    shared_kalman = KalmanFilter()

    def __init__(self, tlwh, score, cls):
        self._tlwh = np.asarray(tlwh, dtype=np.float32)
        self.kalman_filter = None
        self.mean, self.covariance = (None, None)
        self.is_activated = False
        self.score = score
        self.tracklet_len = 0
        self.cls = cls

    def predict(self):
        mean_state = self.mean.copy()
        if self.state != TrackState.Tracked:
            mean_state[7] = 0
        self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)

    @staticmethod
    def multi_predict(stracks):
        if len(stracks) > 0:
            multi_mean = np.asarray([st.mean.copy() for st in stracks])
            multi_covariance = np.asarray([st.covariance for st in stracks])
            for i, st in enumerate(stracks):
                if st.state != TrackState.Tracked:
                    multi_mean[i][7] = 0
            multi_mean, multi_covariance = STrack.shared_kalman.multi_predict(multi_mean, multi_covariance)
            for i, (mean, cov) in enumerate(zip(multi_mean, multi_covariance)):
                stracks[i].mean = mean
                stracks[i].covariance = cov

    def activate(self, kalman_filter, frame_id):
        """Start a new tracklet"""
        self.kalman_filter = kalman_filter
        self.track_id = self.next_id()
        self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xyah(self._tlwh))
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        if frame_id == 1:
            self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id

    def re_activate(self, new_track, frame_id, new_id=False):
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyah(new_track.tlwh))
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        if new_id:
            self.track_id = self.next_id()
        self.score = new_track.score
        self.cls = new_track.cls

    def update(self, new_track, frame_id):
        """
        Update a matched track
        :type new_track: STrack
        :type frame_id: int
        :type update_feature: bool
        :return:
        """
        self.frame_id = frame_id
        self.tracklet_len += 1
        new_tlwh = new_track.tlwh
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xyah(new_tlwh))
        self.state = TrackState.Tracked
        self.is_activated = True
        self.score = new_track.score

    @property
    def tlwh(self):
        """Get current position in bounding box format `(top left x, top left y,
                width, height)`.
        """
        if self.mean is None:
            return self._tlwh.copy()
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    def tlbr(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    @staticmethod
    def tlwh_to_xyah(tlwh):
        """Convert bounding box to format `(center x, center y, aspect ratio,
        height)`, where the aspect ratio is `width / height`.
        """
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    def to_xyah(self):
        return self.tlwh_to_xyah(self.tlwh)

    @staticmethod
    def tlbr_to_tlwh(tlbr):
        ret = np.asarray(tlbr).copy()
        ret[2:] -= ret[:2]
        return ret

    @staticmethod
    def tlwh_to_tlbr(tlwh):
        ret = np.asarray(tlwh).copy()
        ret[2:] += ret[:2]
        return ret

    def __repr__(self):
        return 'OT_{}_({}-{})'.format(self.track_id, self.start_frame, self.end_frame)

def __repr__(self):
    return 'OT_{}_({}-{})'.format(self.track_id, self.start_frame, self.end_frame)

class STrack(BaseTrack):
    shared_kalman = KalmanFilter()

    def __init__(self, tlwh, score, cls, feat=None, feat_history=50):
        self._tlwh = np.asarray(tlwh, dtype=np.float32)
        self.kalman_filter = None
        self.mean, self.covariance = (None, None)
        self.is_activated = False
        self.cls = -1
        self.cls_hist = []
        self.update_cls(cls, score)
        self.score = score
        self.tracklet_len = 0
        self.smooth_feat = None
        self.curr_feat = None
        if feat is not None:
            self.update_features(feat)
        self.features = deque([], maxlen=feat_history)
        self.alpha = 0.9

    def update_features(self, feat):
        feat /= np.linalg.norm(feat)
        self.curr_feat = feat
        if self.smooth_feat is None:
            self.smooth_feat = feat
        else:
            self.smooth_feat = self.alpha * self.smooth_feat + (1 - self.alpha) * feat
        self.features.append(feat)
        self.smooth_feat /= np.linalg.norm(self.smooth_feat)

    def update_cls(self, cls, score):
        if len(self.cls_hist) > 0:
            max_freq = 0
            found = False
            for c in self.cls_hist:
                if cls == c[0]:
                    c[1] += score
                    found = True
                if c[1] > max_freq:
                    max_freq = c[1]
                    self.cls = c[0]
            if not found:
                self.cls_hist.append([cls, score])
                self.cls = cls
        else:
            self.cls_hist.append([cls, score])
            self.cls = cls

    def predict(self):
        mean_state = self.mean.copy()
        if self.state != TrackState.Tracked:
            mean_state[6] = 0
            mean_state[7] = 0
        self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)

    @staticmethod
    def multi_predict(stracks):
        if len(stracks) > 0:
            multi_mean = np.asarray([st.mean.copy() for st in stracks])
            multi_covariance = np.asarray([st.covariance for st in stracks])
            for i, st in enumerate(stracks):
                if st.state != TrackState.Tracked:
                    multi_mean[i][6] = 0
                    multi_mean[i][7] = 0
            multi_mean, multi_covariance = STrack.shared_kalman.multi_predict(multi_mean, multi_covariance)
            for i, (mean, cov) in enumerate(zip(multi_mean, multi_covariance)):
                stracks[i].mean = mean
                stracks[i].covariance = cov

    @staticmethod
    def multi_gmc(stracks, H=np.eye(2, 3)):
        if len(stracks) > 0:
            multi_mean = np.asarray([st.mean.copy() for st in stracks])
            multi_covariance = np.asarray([st.covariance for st in stracks])
            R = H[:2, :2]
            R8x8 = np.kron(np.eye(4, dtype=float), R)
            t = H[:2, 2]
            for i, (mean, cov) in enumerate(zip(multi_mean, multi_covariance)):
                mean = R8x8.dot(mean)
                mean[:2] += t
                cov = R8x8.dot(cov).dot(R8x8.transpose())
                stracks[i].mean = mean
                stracks[i].covariance = cov

    def activate(self, kalman_filter, frame_id):
        """Start a new tracklet"""
        self.kalman_filter = kalman_filter
        self.track_id = self.next_id()
        self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xywh(self._tlwh))
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        if frame_id == 1:
            self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id

    def re_activate(self, new_track, frame_id, new_id=False):
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xywh(new_track.tlwh))
        if new_track.curr_feat is not None:
            self.update_features(new_track.curr_feat)
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        if new_id:
            self.track_id = self.next_id()
        self.score = new_track.score
        self.update_cls(new_track.cls, new_track.score)

    def update(self, new_track, frame_id):
        """
        Update a matched track
        :type new_track: STrack
        :type frame_id: int
        :type update_feature: bool
        :return:
        """
        self.frame_id = frame_id
        self.tracklet_len += 1
        new_tlwh = new_track.tlwh
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, self.tlwh_to_xywh(new_tlwh))
        if new_track.curr_feat is not None:
            self.update_features(new_track.curr_feat)
        self.state = TrackState.Tracked
        self.is_activated = True
        self.score = new_track.score
        self.update_cls(new_track.cls, new_track.score)

    @property
    def tlwh(self):
        """Get current position in bounding box format `(top left x, top left y,
                width, height)`.
        """
        if self.mean is None:
            return self._tlwh.copy()
        ret = self.mean[:4].copy()
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    def tlbr(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    @property
    def xywh(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[:2] += ret[2:] / 2.0
        return ret

    @staticmethod
    def tlwh_to_xyah(tlwh):
        """Convert bounding box to format `(center x, center y, aspect ratio,
        height)`, where the aspect ratio is `width / height`.
        """
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    @staticmethod
    def tlwh_to_xywh(tlwh):
        """Convert bounding box to format `(center x, center y, width,
        height)`.
        """
        ret = np.asarray(tlwh).copy()
        ret[:2] += ret[2:] / 2
        return ret

    def to_xywh(self):
        return self.tlwh_to_xywh(self.tlwh)

    @staticmethod
    def tlbr_to_tlwh(tlbr):
        ret = np.asarray(tlbr).copy()
        ret[2:] -= ret[:2]
        return ret

    @staticmethod
    def tlwh_to_tlbr(tlwh):
        ret = np.asarray(tlwh).copy()
        ret[2:] += ret[:2]
        return ret

    def __repr__(self):
        return 'OT_{}_({}-{})'.format(self.track_id, self.start_frame, self.end_frame)

def __repr__(self):
    return 'OT_{}_({}-{})'.format(self.track_id, self.start_frame, self.end_frame)

