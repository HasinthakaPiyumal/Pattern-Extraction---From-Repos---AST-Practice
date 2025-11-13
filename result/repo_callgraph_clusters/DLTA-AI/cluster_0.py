# Cluster 0

def get_long_description():
    with open('README.md') as f:
        long_description = f.read()
    try:
        import github2pypi
        return github2pypi.replace_url(slug='wkentaro/labelme', content=long_description)
    except Exception:
        return long_description

def count_instances(annotating_models):
    counts = {}
    for model in annotating_models.keys():
        counts[model] = 0
        for classno in range(len(annotating_models[model][1])):
            counts[model] += len(annotating_models[model][1][classno])
    return counts

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

def popLabelListMenu(self, point):
    self.menus.labelList.exec(self.labelList.mapToGlobal(point))

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

def get_frame_by_idx(self, frameIDX):
    self.CAP.set(cv2.CAP_PROP_POS_FRAMES, frameIDX - 1)
    success, img = self.CAP.read()
    return img

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

def addPoint(self, point):
    if self.points and point == self.points[0]:
        self.close()
    else:
        self.points.append(point)

@contextlib.contextmanager
def open(name, mode):
    assert mode in ['r', 'w']
    if PY2:
        mode += 'b'
        encoding = None
    else:
        encoding = 'utf-8'
    yield io.open(name, mode, encoding=encoding)
    return

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

def __init__(self, filename=None):
    self.shapes = []
    self.imagePath = None
    self.imageData = None
    if filename is not None:
        self.load(filename)
    self.filename = filename

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

def get_ip():
    dist = platform.platform().split('-')[0]
    if dist == 'Linux':
        return ''
    elif dist == 'Darwin':
        cmd = 'ifconfig en0'
        output = subprocess.check_output(shlex.split(cmd))
        if str != bytes:
            output = output.decode('utf-8')
        for row in output.splitlines():
            cols = row.strip().split(' ')
            if cols[0] == 'inet':
                ip = cols[1]
                return ip
        else:
            raise RuntimeError('No ip is found.')
    else:
        raise RuntimeError('Unsupported platform.')

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

def update_id_in_listObjframe(listObj, frame, shape, old_id, new_id=None):
    """
        Summary:
            Update the id of a shape in a frame in listObj.
            
        Args:
            listObj: a list of objects (each object is a dictionary of a frame with keys (frame_idx, frame_data))
            frame: the frame to update
            shape: the shape to update
            old_id: the old id
            new_id: the new id, if None then the old id is used (no id change)
            
        Returns:
            listObj: a list of objects (each object is a dictionary of a frame with keys (frame_idx, frame_data))
        """
    new_id = old_id if new_id is None else new_id
    for object_ in listObj[frame - 1]['frame_data']:
        if object_['tracker_id'] == old_id:
            object_['tracker_id'] = new_id
            object_['class_name'] = shape.label
            object_['confidence'] = str(1.0)
            object_['class_id'] = coco_classes.index(shape.label) if shape.label in coco_classes else -1
            break
    return listObj

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

def updateFlags(self, label_new):
    flags_old = self.getFlags()
    flags_new = {}
    for pattern, keys in self._flags.items():
        if re.match(pattern, label_new):
            for key in keys:
                flags_new[key] = flags_old.get(key, False)
    self.setFlags(flags_new)

def resetFlags(self, label=''):
    flags = {}
    for pattern, keys in self._flags.items():
        if re.match(pattern, label):
            for key in keys:
                flags[key] = False
    self.setFlags(flags)

def open_git_hub():
    """
    Opens the GitHub repository for the DLTA-AI project in the default web browser.

    Parameters:
    None

    Returns:
    None
    """
    webbrowser.open('https://github.com/0ssamaak0/DLTA-AI')

def open_issue():
    """
    Opens the GitHub issues page for the DLTA-AI project in the default web browser.

    Parameters:
    None

    Returns:
    None
    """
    webbrowser.open('https://github.com/0ssamaak0/DLTA-AI/issues')

def open_license():
    """
    Opens the license file for the DLTA-AI project in the default web browser.

    Parameters:
    None

    Returns:
    None
    """
    webbrowser.open('https://github.com/0ssamaak0/DLTA-AI/blob/master/LICENSE')

def open_guide():
    """
    Opens the guide for the DLTA-AI project in the default web browser.

    Parameters:
    None

    Returns:
    None
    """
    webbrowser.open('https://0ssamaak0.github.io/DLTA-AI/')

def open_release(link=None):
    """
    Opens the release page for the DLTA-AI project in the default web browser.

    Parameters:
    link (str): The link to the release page. If None, the default link will be used.

    Returns:
    None
    """
    import webbrowser
    if link is None:
        link = 'https://github.com/0ssamaak0/DLTA-AI/releases'
    else:
        link = 'https://github.com/' + link
    webbrowser.open(link)

class StandardItemModel(QtGui.QStandardItemModel):
    itemDropped = QtCore.pyqtSignal()

    def removeRows(self, *args, **kwargs):
        ret = super().removeRows(*args, **kwargs)
        self.itemDropped.emit()
        return ret

def removeRows(self, *args, **kwargs):
    ret = super().removeRows(*args, **kwargs)
    self.itemDropped.emit()
    return ret

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

def on_ok():
    threshold = float(text_input.text())
    dialog.accept()
    return threshold

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

def enterEvent(self, ev):
    self.overrideCursor(self._cursor)

def leaveEvent(self, ev):
    self.unHighlight()
    self.restoreCursor()

def focusOutEvent(self, ev):
    self.restoreCursor()

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

def boundedMoveVertex(self, pos):
    index, shape = (self.hVertex, self.hShape)
    point = shape[index]
    if self.outOfPixmap(pos):
        pos = self.intersectionPoint(point, pos)
    pos = QtCore.QPointF(pos)
    shape.moveVertexBy(index, pos - point)

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

def boundedShiftShapes(self, shapes):
    point = shapes[0][0]
    offset = QtCore.QPoint(2.0, 2.0)
    self.offsets = (QtCore.QPoint(), QtCore.QPoint())
    self.prevPoint = point
    if not self.boundedMoveShapes(shapes, point - offset):
        self.boundedMoveShapes(shapes, point + offset)

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

def resetState(self):
    self.restoreCursor()
    self.pixmap = None
    self.shapesBackups = []
    self.update()

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

def img_data_to_pil(img_data):
    f = io.BytesIO()
    f.write(img_data)
    img_pil = PIL.Image.open(f)
    return img_pil

def img_pil_to_data(img_pil):
    f = io.BytesIO()
    img_pil.save(f, format='PNG')
    img_data = f.getvalue()
    return img_data

def img_arr_to_b64(img_arr):
    img_pil = PIL.Image.fromarray(img_arr)
    f = io.BytesIO()
    img_pil.save(f, format='PNG')
    img_bin = f.getvalue()
    if hasattr(base64, 'encodebytes'):
        img_b64 = base64.encodebytes(img_bin)
    else:
        img_b64 = base64.encodestring(img_bin)
    return img_b64

def img_data_to_png_data(img_data):
    with io.BytesIO() as f:
        f.write(img_data)
        img = PIL.Image.open(f)
        with io.BytesIO() as f:
            img.save(f, 'PNG')
            f.seek(0)
            return f.read()

def apply_exif_orientation(image):
    try:
        exif = image._getexif()
    except AttributeError:
        exif = None
    if exif is None:
        return image
    exif = {PIL.ExifTags.TAGS[k]: v for k, v in exif.items() if k in PIL.ExifTags.TAGS}
    orientation = exif.get('Orientation', None)
    if orientation == 1:
        return image
    elif orientation == 2:
        return PIL.ImageOps.mirror(image)
    elif orientation == 3:
        return image.transpose(PIL.Image.ROTATE_180)
    elif orientation == 4:
        return PIL.ImageOps.flip(image)
    elif orientation == 5:
        return PIL.ImageOps.mirror(image.transpose(PIL.Image.ROTATE_270))
    elif orientation == 6:
        return image.transpose(PIL.Image.ROTATE_270)
    elif orientation == 7:
        return PIL.ImageOps.mirror(image.transpose(PIL.Image.ROTATE_90))
    elif orientation == 8:
        return image.transpose(PIL.Image.ROTATE_90)
    else:
        return image

def exportCOCO(json_paths, annotation_path):
    """
    Export annotations in COCO format from a directory of JSON files for image and dir modes

    Args:
        target_directory (str): The directory containing the JSON files (dir)
        save_path (str): The path to save the output file (image mode)
        annotation_path (str): The path to the output file.

    Returns:
        str: The path to the output file.

    Raises:
        ValueError: If no JSON files are found in the directory.

    """
    file = {}
    file['info'] = {'description': 'Exported from DLTA-AI', 'year': datetime.datetime.now().year, 'date_created': datetime.date.today().strftime('%Y/%m/%d')}
    used_classes = set()
    annotations = []
    images = []
    for i in range(len(json_paths)):
        try:
            with open(json_paths[i]) as f:
                data = json.load(f)
                images.append({'id': i, 'width': data['imageWidth'], 'height': data['imageHeight'], 'file_name': json_paths[i].split('/')[-1].replace('.json', '.jpg')})
                for j in range(len(data['shapes'])):
                    if len(data['shapes'][j]['points']) == 0:
                        continue
                    if data['shapes'][j]['label'].lower() not in coco_classes:
                        print(f'{data['shapes'][j]['label']} is not a valid COCO class.. Adding it to the list.')
                        coco_classes.append(data['shapes'][j]['label'].lower())
                    annotations.append({'id': len(annotations), 'image_id': i, 'category_id': coco_classes.index(data['shapes'][j]['label'].lower()) + 1, 'bbox': get_bbox(data['shapes'][j]['points']), 'iscrowd': 0})
                    try:
                        annotations[-1]['segmentation'] = [data['shapes'][j]['points']]
                        annotations[-1]['area'] = get_area_from_polygon(annotations[-1]['segmentation'][0], mode='segmentation')
                    except:
                        annotations[-1]['area'] = get_area_from_polygon(annotations[-1]['bbox'], mode='bbox')
                    try:
                        annotations[-1]['score'] = float(data['shapes'][j]['content'])
                    except:
                        pass
                    used_classes.add(coco_classes.index(data['shapes'][j]['label'].lower()) + 1)
        except Exception as e:
            print(f'Error with {json_paths[i]}')
            print(e)
            continue
    used_classes = sorted(used_classes)
    file['categories'] = [{'id': i, 'name': coco_classes[i - 1]} for i in used_classes]
    file['images'] = images
    file['annotations'] = annotations
    with open(annotation_path, 'w') as outfile:
        json.dump(file, outfile, indent=4)
    return annotation_path

def exportCOCOvid(results_file, vid_width, vid_height, annotation_path):
    """
    Export object detection results in COCO format for a video.

    Args:
        results_file (str): Path to the JSON file containing the object detection results.
        vid_width (int): Width of the video frames.
        vid_height (int): Height of the video frames.
        annotation_path (str): Path to the output COCO annotation file.

    Returns:
        str: Path to the output COCO annotation file.

    Raises:
        ValueError: If no object detection results are found in the JSON file.

    """
    file = {}
    file['info'] = {'description': 'Exported from DLTA-AI', 'year': datetime.datetime.now().year, 'date_created': datetime.date.today().strftime('%Y/%m/%d')}
    annotations = []
    images = []
    used_classes = set()
    with open(results_file) as f:
        data = json.load(f)
        for frame in data:
            if len(frame['frame_data']) == 0:
                continue
            images.append({'id': frame['frame_idx'], 'width': vid_width, 'height': vid_height, 'file_name': f'frame {frame['frame_idx']}'})
            for object in frame['frame_data']:
                annotations.append({'id': len(annotations), 'image_id': frame['frame_idx'], 'category_id': object['class_id'] + 1, 'iscrowd': 0})
                if annotations[-1]['category_id'] == 0:
                    coco_classes.append(object['class_name'].lower())
                    annotations[-1]['category_id'] = coco_classes.index(object['class_name'].lower()) + 1
                try:
                    annotations[-1]['bbox'] = get_bbox(object['segment'])
                    annotations[-1]['segmentation'] = [[val for sublist in object['segment'] for val in sublist]]
                    annotations[-1]['area'] = get_area_from_polygon(annotations[-1]['segmentation'][0], mode='segmentation')
                except:
                    annotations[-1]['bbox'] = object['bbox']
                    annotations[-1]['area'] = get_area_from_polygon(annotations[-1]['bbox'], mode='bbox')
                try:
                    annotations[-1]['score'] = float(object['confidence'])
                except:
                    pass
                used_classes.add(annotations[-1]['category_id'])
    used_classes = sorted(list(used_classes))
    file['categories'] = [{'id': i, 'name': coco_classes[i - 1]} for i in used_classes]
    file['images'] = images
    file['annotations'] = annotations
    with open(annotation_path, 'w') as outfile:
        json.dump(file, outfile, indent=4)
    return annotation_path

def exportMOT(results_file, annotation_path):
    """
    Export object tracking results in MOT format.

    Args:
        results_file (str): Path to the JSON file containing the object tracking results.
        annotation_path (str): Path to the output MOT annotation file.

    Returns:
        str: Path to the output MOT annotation file.

    """
    with open(results_file) as f, open(annotation_path, 'w') as outfile:
        for frame in json.load(f):
            for object in frame['frame_data']:
                outfile.write(f'{frame['frame_idx']}, {object['tracker_id']},  {object['bbox'][0]},  {object['bbox'][1]},  {object['bbox'][2]},  {object['bbox'][3]},  {object['confidence']}, {object['class_id'] + 1}, 1\n')
    return annotation_path

class struct(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def __init__(self, **kwargs):
    self.__dict__.update(kwargs)

def foo():
    print('foo')

def bar(results_file, vid_width, vid_height, annotation_path):
    foo()
    print('bar')
    print(f'Export Function Check: results_file: {results_file} | vid_width: {vid_width} | vid_height: {vid_height} | annotation_path: {annotation_path}')
    return annotation_path

def baz(json_paths, annotation_path):
    foo()
    print('baz')
    print(f'Export Function Check: json_paths {json_paths} | annotation_path: {annotation_path}')
    return annotation_path

def class_name_to_id(class_name):
    """
    Summary:
        Map a class name to its id in the coco dataset.
        
    Args:
        class_name: the class name
        
    Returns:
        class_id: the id of the class
    """
    try:
        return coco_classes.index(class_name)
    except:
        return -1

def load_objects_from_json__json(json_file_name, nTotalFrames):
    """
    Summary:
        Load objects from a json file using json library.
        
    Args:
        json_file_name: the name of the json file
        nTotalFrames: the total number of frames
        
    Returns:
        listObj: a list of objects (each object is a dictionary of a frame with keys (frame_idx, frame_data))
    """
    listObj = [{'frame_idx': i + 1, 'frame_data': []} for i in range(nTotalFrames)]
    if not os.path.exists(json_file_name):
        with open(json_file_name, 'w') as jf:
            json.dump(listObj, jf, indent=4, separators=(',', ': '))
        jf.close()
    with open(json_file_name, 'r') as jf:
        listObj = json.load(jf)
    jf.close()
    return listObj

def load_objects_to_json__json(json_file_name, listObj):
    """
    Summary:
        Load objects to a json file using json library.
        
    Args:
        json_file_name: the name of the json file
        listObj: a list of objects (each object is a dictionary of a frame with keys (frame_idx, frame_data))
        
    Returns:
        None
    """
    with open(json_file_name, 'w') as json_file:
        json.dump(listObj, json_file, indent=4, separators=(',', ': '))
    json_file.close()

def load_objects_from_json__orjson(json_file_name, nTotalFrames):
    """
    Summary:
        Load objects from a json file using orjson library.
        
    Args:
        json_file_name: the name of the json file
        nTotalFrames: the total number of frames
        
    Returns:
        listObj: a list of objects (each object is a dictionary of a frame with keys (frame_idx, frame_data))
    """
    listObj = [{'frame_idx': i + 1, 'frame_data': []} for i in range(nTotalFrames)]
    if not os.path.exists(json_file_name):
        with open(json_file_name, 'wb') as jf:
            jf.write(orjson.dumps(listObj))
        jf.close()
    with open(json_file_name, 'rb') as jf:
        listObj = orjson.loads(jf.read())
    jf.close()
    return listObj

def load_objects_to_json__orjson(json_file_name, listObj):
    """
    Summary:
        Load objects to a json file using orjson library.
        
    Args:
        json_file_name: the name of the json file
        listObj: a list of objects (each object is a dictionary of a frame with keys (frame_idx, frame_data))
        
    Returns:
        None
    """
    with open(json_file_name, 'wb') as jf:
        jf.write(orjson.dumps(listObj, option=orjson.OPT_INDENT_2))
    jf.close()

def update_saved_models_json(cwd):
    """
    Summary:
        Update the saved models json file.
    """
    checkpoints_dir = cwd + '/mmdetection/checkpoints/'
    try:
        files = os.listdir(checkpoints_dir)
    except:
        os.mkdir(checkpoints_dir)
    with open(cwd + '/models_menu/models_json.json') as f:
        models_json = json.load(f)
    saved_models = {}
    for model in models_json:
        if model['Model'] != 'SAM':
            if model['Checkpoint'].split('/')[-1] in os.listdir(checkpoints_dir):
                saved_models[model['Model Name']] = {'id': model['id'], 'checkpoint': model['Checkpoint'], 'config': model['Config']}
    with open(cwd + '/saved_models.json', 'w') as f:
        json.dump(saved_models, f, indent=4)

def delete_id_from_rec_and_traj(id, id_frames_rec, trajectories, frames):
    """
    Summary:
        Delete an id from id_frames_rec and trajectories.
        
    Args:
        id: the id to delete
        id_frames_rec: a dictionary of id frames records
        
    Returns:
    """
    id_frames_rec['id_' + str(id)] = id_frames_rec['id_' + str(id)] - set(frames)
    for frame in frames:
        trajectories['id_' + str(id)][frame - 1] = (-1, -1)
    return (id_frames_rec, trajectories)

def OURnms_areaBased_fromSAM(self, sam_result, iou_threshold=0.5):
    iou_threshold = float(iou_threshold)
    sortedResult = sorted(sam_result, key=lambda x: x['area'], reverse=True)
    masks = [mask['segmentation'] for mask in sortedResult]
    scores = [mask['stability_score'] for mask in sortedResult]
    polygons = [mask_to_polygons(mask) for mask in masks]
    toBeRemoved = []
    if iou_threshold > 0.99:
        for i in range(len(polygons)):
            shape1 = polygons[i]
            for j in range(i + 1, len(sortedResult)):
                shape2 = polygons[j]
                iou = compute_iou_exact(shape1, shape2)
                if iou > iou_threshold:
                    toBeRemoved.append(j)
    shapes = []
    for i in range(len(polygons)):
        if i in toBeRemoved:
            continue
        shapes.append(self.polygon_to_shape(polygons[i], scores[i], f'X{i}'))
    return shapes

def validate_config_item(key, value):
    if key == 'validate_label' and value not in [None, 'exact']:
        raise ValueError("Unexpected value for config key 'validate_label': {}".format(value))
    if key == 'shape_color' and value not in [None, 'auto', 'manual']:
        raise ValueError("Unexpected value for config key 'shape_color': {}".format(value))
    if key == 'labels' and value is not None and (len(value) != len(set(value))):
        raise ValueError("Duplicates are detected for config key 'labels': {}".format(value))

def readme():
    with open('README.md', encoding='utf-8') as f:
        content = f.read()
    return content

def get_version():
    with open(version_file, 'r') as f:
        exec(compile(f.read(), version_file, 'exec'))
    return locals()['__version__']

def parse_require_file(fpath):
    with open(fpath, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if line and (not line.startswith('#')):
                for info in parse_line(line):
                    yield info

def parse_requirements(fname='requirements.txt', with_version=True):
    """Parse the package dependencies listed in a requirements file but strips
    specific versioning information.

    Args:
        fname (str): path to requirements file
        with_version (bool, default=False): if True include version specs

    Returns:
        List[str]: list of requirements items

    CommandLine:
        python -c "import setup; print(setup.parse_requirements())"
    """
    import re
    import sys
    from os.path import exists
    require_fpath = fname

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

    def parse_require_file(fpath):
        with open(fpath, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and (not line.startswith('#')):
                    for info in parse_line(line):
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
    packages = list(gen_packages_items())
    return packages

def results2markdown(result_dict):
    table_data = []
    is_multiple_results = False
    for cfg_name, value in result_dict.items():
        name = cfg_name.replace('configs/', '')
        fps = value['fps']
        ms_times_pre_image = value['ms_times_pre_image']
        if isinstance(fps, list):
            is_multiple_results = True
            mean_fps = value['mean_fps']
            mean_times_pre_image = value['mean_times_pre_image']
            fps_str = ','.join([str(s) for s in fps])
            ms_times_pre_image_str = ','.join([str(s) for s in ms_times_pre_image])
            table_data.append([name, fps_str, mean_fps, ms_times_pre_image_str, mean_times_pre_image])
        else:
            table_data.append([name, fps, ms_times_pre_image])
    if is_multiple_results:
        table_data.insert(0, ['model', 'fps', 'mean_fps', 'times_pre_image(ms)', 'mean_times_pre_image(ms)'])
    else:
        table_data.insert(0, ['model', 'fps', 'times_pre_image(ms)'])
    table = GithubFlavoredMarkdownTable(table_data)
    print(table.table, flush=True)

def check_link(match_tuple: MatchTuple, http_session: requests.Session, logger: logging=None) -> Tuple[MatchTuple, bool, Optional[str]]:
    reason: Optional[str] = None
    if match_tuple.link.startswith('http'):
        result_ok, reason = check_url(match_tuple, http_session)
    else:
        result_ok = check_path(match_tuple)
    if logger is None:
        print(f'  {('✓' if result_ok else '✗')} {match_tuple.link}')
    else:
        logger.info(f'  {('✓' if result_ok else '✗')} {match_tuple.link}')
    return (match_tuple, result_ok, reason)

def main():
    args = parse_args()
    logger = get_logger(name='mmdet', log_file=args.out)
    if args.https_proxy:
        os.environ['https_proxy'] = args.https_proxy
    http_session = requests.Session()
    for resource_prefix in ('http://', 'https://'):
        http_session.mount(resource_prefix, requests.adapters.HTTPAdapter(max_retries=5, pool_connections=20, pool_maxsize=args.num_threads))
    logger.info('Finding all markdown files in the current directory...')
    project_root = (pathlib.Path(__file__).parent / '..').resolve()
    markdown_files = project_root.glob('**/*.md')
    all_matches = set()
    url_regex = re.compile('\\[([^!][^\\]]+)\\]\\(([^)(]+)\\)')
    for markdown_file in markdown_files:
        with open(markdown_file) as handle:
            for line in handle.readlines():
                matches = url_regex.findall(line)
                for name, link in matches:
                    if 'localhost' not in link:
                        all_matches.add(MatchTuple(source=str(markdown_file), name=name, link=link))
    logger.info(f'  {len(all_matches)} markdown files found')
    logger.info('Checking to make sure we can retrieve each link...')
    with Pool(processes=args.num_threads) as pool:
        results = pool.starmap(check_link, [(match, http_session, logger) for match in list(all_matches)])
    unreachable_results = [(match_tuple, reason) for match_tuple, success, reason in results if not success]
    if unreachable_results:
        logger.info('================================================')
        logger.info(f'Unreachable links ({len(unreachable_results)}):')
        for match_tuple, reason in unreachable_results:
            logger.info('  > Source: ' + match_tuple.source)
            logger.info('    Name: ' + match_tuple.name)
            logger.info('    Link: ' + match_tuple.link)
            if reason is not None:
                logger.info('    Reason: ' + reason)
        sys.exit(1)
    logger.info('No Unreachable link found.')

def main():
    args = parse_args()
    benchmark_type = []
    if args.basic_arch:
        benchmark_type += basic_arch_root
    if args.datasets:
        benchmark_type += datasets_root
    if args.data_pipeline:
        benchmark_type += data_pipeline_root
    if args.nn_module:
        benchmark_type += nn_module_root
    special_model = args.model_options
    if special_model is not None:
        benchmark_type += special_model
    config_dpath = 'configs/'
    benchmark_configs = []
    for cfg_root in benchmark_type:
        cfg_dir = osp.join(config_dpath, cfg_root)
        configs = os.scandir(cfg_dir)
        for cfg in configs:
            config_path = osp.join(cfg_dir, cfg.name)
            if config_path in benchmark_pool and config_path not in benchmark_configs:
                benchmark_configs.append(config_path)
    print(f'Totally found {len(benchmark_configs)} configs to benchmark')
    with open(args.out, 'w') as f:
        for config in benchmark_configs:
            f.write(config + '\n')

def inference_model(config_name, checkpoint, args, logger=None):
    cfg = Config.fromfile(config_name)
    if args.aug:
        if 'flip' in cfg.data.test.pipeline[1]:
            cfg.data.test.pipeline[1].flip = True
        elif logger is not None:
            logger.error(f'{config_name}: unable to start aug test')
        else:
            print(f'{config_name}: unable to start aug test', flush=True)
    model = init_detector(cfg, checkpoint, device=args.device)
    result = inference_detector(model, args.img)
    if args.show:
        show_result_pyplot(model, args.img, result, score_thr=args.score_thr, wait_time=args.wait_time)
    return result

def _check_backbone(config, print_cfg=True):
    """Check out backbone whether successfully load pretrained model, by using
    `backbone.init_cfg`.

    First, using `mmcv._load_checkpoint` to load the checkpoint without
        loading models.
    Then, using `build_detector` to build models, and using
        `model.init_weights()` to initialize the parameters.
    Finally, assert weights and bias of each layer loaded from pretrained
        checkpoint are equal to the weights and bias of original checkpoint.
        For the convenience of comparison, we sum up weights and bias of
        each loaded layer separately.

    Args:
        config (str): Config file path.
        print_cfg (bool): Whether print logger and return the result.

    Returns:
        results (str or None): If backbone successfully load pretrained
            checkpoint, return None; else, return config file path.
    """
    if print_cfg:
        print('-' * 15 + 'loading ', config)
    cfg = Config.fromfile(config)
    init_cfg = None
    try:
        init_cfg = cfg.model.backbone.init_cfg
        init_flag = True
    except AttributeError:
        init_flag = False
    if init_cfg is None or init_cfg.get('type') != 'Pretrained':
        init_flag = False
    if init_flag:
        checkpoint = _load_checkpoint(init_cfg.checkpoint)
        if 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        else:
            state_dict = checkpoint
        model = build_detector(cfg.model, train_cfg=cfg.get('train_cfg'), test_cfg=cfg.get('test_cfg'))
        model.init_weights()
        checkpoint_layers = state_dict.keys()
        for name, value in model.backbone.state_dict().items():
            if name in checkpoint_layers:
                assert value.equal(state_dict[name])
        if print_cfg:
            print('-' * 10 + 'Successfully load checkpoint' + '-' * 10 + '\n')
            return None
    elif print_cfg:
        print(config + '\n' + '-' * 10 + 'config file do not have init_cfg' + '-' * 10 + '\n')
        return config

@pytest.mark.parametrize('config', _traversed_config_file())
def test_load_pretrained(config):
    """Check out backbone whether successfully load pretrained model by using
    `backbone.init_cfg`.

    Details please refer to `_check_backbone`
    """
    _check_backbone(config, print_cfg=False)

def _test_load_pretrained():
    """We traversed all potential config files under the `config` file. If you
    need to print details or debug code, you can use this function.

    Returns:
        check_cfg_names (list[str]): Config files that backbone initialized
        from pretrained checkpoint might be problematic. Need to recheck
        the config file. The output including the config files that the
        backbone.init_cfg is None
    """
    check_cfg_names = _traversed_config_file()
    need_check_cfg = []
    prog_bar = ProgressBar(len(check_cfg_names))
    for config in check_cfg_names:
        init_cfg_name = _check_backbone(config)
        if init_cfg_name is not None:
            need_check_cfg.append(init_cfg_name)
        prog_bar.update()
    print('These config files need to be checked again')
    print(need_check_cfg)

def _dict_representer(dumper, data):
    return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())

def ordered_yaml_dump(data, stream=None, Dumper=yaml.SafeDumper, **kwds):

    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())
    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)

def process_checkpoint(in_file, out_file):
    checkpoint = torch.load(in_file, map_location='cpu')
    if 'optimizer' in checkpoint:
        del checkpoint['optimizer']
    for key in list(checkpoint['state_dict']):
        if key.startswith('ema_'):
            checkpoint['state_dict'].pop(key)
    if torch.__version__ >= '1.6':
        torch.save(checkpoint, out_file, _use_new_zipfile_serialization=False)
    else:
        torch.save(checkpoint, out_file)
    sha = subprocess.check_output(['sha256sum', out_file]).decode()
    final_file = out_file.rstrip('.pth') + '-{}.pth'.format(sha[:8])
    subprocess.Popen(['mv', out_file, final_file])
    return final_file

def get_best_epoch_or_iter(exp_dir):
    best_epoch_iter_full_path = list(sorted(glob.glob(osp.join(exp_dir, 'best_*.pth'))))[-1]
    best_epoch_or_iter_model_path = best_epoch_iter_full_path.split('/')[-1]
    best_epoch_or_iter = best_epoch_or_iter_model_path.split('_')[-1].split('.')[0]
    return (best_epoch_or_iter_model_path, int(best_epoch_or_iter))

def get_final_results(log_json_path, epoch_or_iter, results_lut, by_epoch=True):
    result_dict = dict()
    last_val_line = None
    last_train_line = None
    last_val_line_idx = -1
    last_train_line_idx = -1
    with open(log_json_path, 'r') as f:
        for i, line in enumerate(f.readlines()):
            log_line = json.loads(line)
            if 'mode' not in log_line.keys():
                continue
            if by_epoch:
                if log_line['mode'] == 'train' and log_line['epoch'] == epoch_or_iter:
                    result_dict['memory'] = log_line['memory']
                if log_line['mode'] == 'val' and log_line['epoch'] == epoch_or_iter:
                    result_dict.update({key: log_line[key] for key in results_lut if key in log_line})
                    return result_dict
            else:
                if log_line['mode'] == 'train':
                    last_train_line_idx = i
                    last_train_line = log_line
                if log_line and log_line['mode'] == 'val':
                    last_val_line_idx = i
                    last_val_line = log_line
    assert last_val_line_idx == last_train_line_idx + 1, 'Log file is incomplete'
    result_dict['memory'] = last_train_line['memory']
    result_dict.update({key: last_val_line[key] for key in results_lut if key in last_val_line})
    return result_dict

def main():
    args = parse_args()
    models_root = args.root
    models_out = args.out
    mmcv.mkdir_or_exist(models_out)
    raw_configs = list(mmcv.scandir('./configs', '.py', recursive=True))
    used_configs = []
    for raw_config in raw_configs:
        if osp.exists(osp.join(models_root, raw_config)):
            used_configs.append(raw_config)
    print(f'Find {len(used_configs)} models to be gathered')
    model_infos = []
    for used_config in used_configs:
        exp_dir = osp.join(models_root, used_config)
        by_epoch = is_by_epoch(used_config)
        if args.best is True:
            final_model, final_epoch_or_iter = get_best_epoch_or_iter(exp_dir)
        else:
            final_epoch_or_iter = get_final_epoch_or_iter(used_config)
            final_model = '{}_{}.pth'.format('epoch' if by_epoch else 'iter', final_epoch_or_iter)
        model_path = osp.join(exp_dir, final_model)
        if not osp.exists(model_path):
            continue
        log_json_path = list(sorted(glob.glob(osp.join(exp_dir, '*.log.json'))))[-1]
        log_txt_path = list(sorted(glob.glob(osp.join(exp_dir, '*.log'))))[-1]
        cfg = mmcv.Config.fromfile('./configs/' + used_config)
        results_lut = cfg.evaluation.metric
        if not isinstance(results_lut, list):
            results_lut = [results_lut]
        for i, key in enumerate(results_lut):
            if 'mAP' not in key and 'PQ' not in key:
                results_lut[i] = key + '_mAP'
        model_performance = get_final_results(log_json_path, final_epoch_or_iter, results_lut, by_epoch)
        if model_performance is None:
            continue
        model_time = osp.split(log_txt_path)[-1].split('.')[0]
        model_info = dict(config=used_config, results=model_performance, model_time=model_time, final_model=final_model, log_json_path=osp.split(log_json_path)[-1])
        model_info['epochs' if by_epoch else 'iterations'] = final_epoch_or_iter
        model_infos.append(model_info)
    publish_model_infos = []
    for model in model_infos:
        model_publish_dir = osp.join(models_out, model['config'].rstrip('.py'))
        mmcv.mkdir_or_exist(model_publish_dir)
        model_name = osp.split(model['config'])[-1].split('.')[0]
        model_name += '_' + model['model_time']
        publish_model_path = osp.join(model_publish_dir, model_name)
        trained_model_path = osp.join(models_root, model['config'], model['final_model'])
        final_model_path = process_checkpoint(trained_model_path, publish_model_path)
        shutil.copy(osp.join(models_root, model['config'], model['log_json_path']), osp.join(model_publish_dir, f'{model_name}.log.json'))
        shutil.copy(osp.join(models_root, model['config'], model['log_json_path'].rstrip('.json')), osp.join(model_publish_dir, f'{model_name}.log'))
        config_path = model['config']
        config_path = osp.join('configs', config_path) if 'configs' not in config_path else config_path
        target_config_path = osp.split(config_path)[-1]
        shutil.copy(config_path, osp.join(model_publish_dir, target_config_path))
        model['model_path'] = final_model_path
        publish_model_infos.append(model)
    models = dict(models=publish_model_infos)
    print(f'Totally gathered {len(publish_model_infos)} models')
    mmcv.dump(models, osp.join(models_out, 'model_info.json'))
    pwc_files = convert_model_info_to_pwc(publish_model_infos)
    for name in pwc_files:
        with open(osp.join(models_out, name + '_metafile.yml'), 'w') as f:
            ordered_yaml_dump(pwc_files[name], f, encoding='utf-8')

def get_version():
    with open(version_file, 'r') as f:
        exec(compile(f.read(), version_file, 'exec'))
    return locals()['__version__']

def builder_inited_handler(app):
    subprocess.run(['./stat.py'])

def get_version():
    with open(version_file, 'r') as f:
        exec(compile(f.read(), version_file, 'exec'))
    return locals()['__version__']

def builder_inited_handler(app):
    subprocess.run(['./stat.py'])

def replace_value(cfg):
    if isinstance(cfg, dict):
        return {key: replace_value(value) for key, value in cfg.items()}
    elif isinstance(cfg, list):
        return [replace_value(item) for item in cfg]
    elif isinstance(cfg, tuple):
        return tuple([replace_value(item) for item in cfg])
    elif isinstance(cfg, str):
        keys = pattern_key.findall(cfg)
        values = [get_value(ori_cfg, key[2:-1]) for key in keys]
        if len(keys) == 1 and keys[0] == cfg:
            cfg = values[0]
        else:
            for key, value in zip(keys, values):
                assert not isinstance(value, (dict, list, tuple)), f"for the format of string cfg is 'xxxxx${key}xxxxx' or 'xxx${key}xxx${key}xxx', the type of the value of '${key}' can not be dict, list, or tuplebut you input {type(value)} in {cfg}"
                cfg = cfg.replace(key, str(value))
        return cfg
    else:
        return cfg

def update(cfg, src_str, dst_str):
    for k, v in cfg.items():
        if isinstance(v, mmcv.ConfigDict):
            update(cfg[k], src_str, dst_str)
        if isinstance(v, str) and src_str in v:
            cfg[k] = v.replace(src_str, dst_str)

@contextlib.contextmanager
def profile_time(trace_name, name, enabled=True, stream=None, end_stream=None):
    """Print time spent by CPU and GPU.

        Useful as a temporary context manager to find sweet spots of code
        suitable for async implementation.
        """
    if not enabled or not torch.cuda.is_available():
        yield
        return
    stream = stream if stream else torch.cuda.current_stream()
    end_stream = end_stream if end_stream else stream
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    stream.record_event(start)
    try:
        cpu_start = time.monotonic()
        yield
    finally:
        cpu_end = time.monotonic()
        end_stream.record_event(end)
        end.synchronize()
        cpu_time = (cpu_end - cpu_start) * 1000
        gpu_time = start.elapsed_time(end)
        msg = f'{trace_name} {name} cpu_time {cpu_time:.2f} ms '
        msg += f'gpu_time {gpu_time:.2f} ms stream {stream}'
        print(msg, end_stream)

def select_group(data_batch, current_tag):
    group_flag = [tag == current_tag for tag in data_batch['tag']]
    return {k: fuse_list([vv for vv, gf in zip(v, group_flag) if gf], v) for k, v in data_batch.items()}

def split_batch(img, img_metas, kwargs):
    """Split data_batch by tags.

    Code is modified from
    <https://github.com/microsoft/SoftTeacher/blob/main/ssod/utils/structure_utils.py> # noqa: E501

    Args:
        img (Tensor): of shape (N, C, H, W) encoding input images.
            Typically these should be mean centered and std scaled.
        img_metas (list[dict]): List of image info dict where each dict
            has: 'img_shape', 'scale_factor', 'flip', and may also contain
            'filename', 'ori_shape', 'pad_shape', and 'img_norm_cfg'.
            For details on the values of these keys, see
            :class:`mmdet.datasets.pipelines.Collect`.
        kwargs (dict): Specific to concrete implementation.

    Returns:
        data_groups (dict): a dict that data_batch splited by tags,
            such as 'sup', 'unsup_teacher', and 'unsup_student'.
    """

    def fuse_list(obj_list, obj):
        return torch.stack(obj_list) if isinstance(obj, torch.Tensor) else obj_list

    def select_group(data_batch, current_tag):
        group_flag = [tag == current_tag for tag in data_batch['tag']]
        return {k: fuse_list([vv for vv, gf in zip(v, group_flag) if gf], v) for k, v in data_batch.items()}
    kwargs.update({'img': img, 'img_metas': img_metas})
    kwargs.update({'tag': [meta['tag'] for meta in img_metas]})
    tags = list(set(kwargs['tag']))
    data_groups = {tag: select_group(kwargs, tag) for tag in tags}
    for tag, group in data_groups.items():
        group.pop('tag')
    return data_groups

def log_img_scale(img_scale, shape_order='hw', skip_square=False):
    """Log image size.

    Args:
        img_scale (tuple): Image size to be logged.
        shape_order (str, optional): The order of image shape.
            'hw' for (height, width) and 'wh' for (width, height).
            Defaults to 'hw'.
        skip_square (bool, optional): Whether to skip logging for square
            img_scale. Defaults to False.

    Returns:
        bool: Whether to have done logging.
    """
    if shape_order == 'hw':
        height, width = img_scale
    elif shape_order == 'wh':
        width, height = img_scale
    else:
        raise ValueError(f'Invalid shape_order {shape_order}.')
    if skip_square and height == width:
        return False
    logger = get_root_logger()
    caller = get_caller_name()
    logger.info(f'image shape: height={height}, width={width} in {caller}')
    return True

class BitmapMasks(BaseInstanceMasks):
    """This class represents masks in the form of bitmaps.

    Args:
        masks (ndarray): ndarray of masks in shape (N, H, W), where N is
            the number of objects.
        height (int): height of masks
        width (int): width of masks

    Example:
        >>> from mmdet.core.mask.structures import *  # NOQA
        >>> num_masks, H, W = 3, 32, 32
        >>> rng = np.random.RandomState(0)
        >>> masks = (rng.rand(num_masks, H, W) > 0.1).astype(np.int)
        >>> self = BitmapMasks(masks, height=H, width=W)

        >>> # demo crop_and_resize
        >>> num_boxes = 5
        >>> bboxes = np.array([[0, 0, 30, 10.0]] * num_boxes)
        >>> out_shape = (14, 14)
        >>> inds = torch.randint(0, len(self), size=(num_boxes,))
        >>> device = 'cpu'
        >>> interpolation = 'bilinear'
        >>> new = self.crop_and_resize(
        ...     bboxes, out_shape, inds, device, interpolation)
        >>> assert len(new) == num_boxes
        >>> assert new.height, new.width == out_shape
    """

    def __init__(self, masks, height, width):
        self.height = height
        self.width = width
        if len(masks) == 0:
            self.masks = np.empty((0, self.height, self.width), dtype=np.uint8)
        else:
            assert isinstance(masks, (list, np.ndarray))
            if isinstance(masks, list):
                assert isinstance(masks[0], np.ndarray)
                assert masks[0].ndim == 2
            else:
                assert masks.ndim == 3
            self.masks = np.stack(masks).reshape(-1, height, width)
            assert self.masks.shape[1] == self.height
            assert self.masks.shape[2] == self.width

    def __getitem__(self, index):
        """Index the BitmapMask.

        Args:
            index (int | ndarray): Indices in the format of integer or ndarray.

        Returns:
            :obj:`BitmapMasks`: Indexed bitmap masks.
        """
        masks = self.masks[index].reshape(-1, self.height, self.width)
        return BitmapMasks(masks, self.height, self.width)

    def __iter__(self):
        return iter(self.masks)

    def __repr__(self):
        s = self.__class__.__name__ + '('
        s += f'num_masks={len(self.masks)}, '
        s += f'height={self.height}, '
        s += f'width={self.width})'
        return s

    def __len__(self):
        """Number of masks."""
        return len(self.masks)

    def rescale(self, scale, interpolation='nearest'):
        """See :func:`BaseInstanceMasks.rescale`."""
        if len(self.masks) == 0:
            new_w, new_h = mmcv.rescale_size((self.width, self.height), scale)
            rescaled_masks = np.empty((0, new_h, new_w), dtype=np.uint8)
        else:
            rescaled_masks = np.stack([mmcv.imrescale(mask, scale, interpolation=interpolation) for mask in self.masks])
        height, width = rescaled_masks.shape[1:]
        return BitmapMasks(rescaled_masks, height, width)

    def resize(self, out_shape, interpolation='nearest'):
        """See :func:`BaseInstanceMasks.resize`."""
        if len(self.masks) == 0:
            resized_masks = np.empty((0, *out_shape), dtype=np.uint8)
        else:
            resized_masks = np.stack([mmcv.imresize(mask, out_shape[::-1], interpolation=interpolation) for mask in self.masks])
        return BitmapMasks(resized_masks, *out_shape)

    def flip(self, flip_direction='horizontal'):
        """See :func:`BaseInstanceMasks.flip`."""
        assert flip_direction in ('horizontal', 'vertical', 'diagonal')
        if len(self.masks) == 0:
            flipped_masks = self.masks
        else:
            flipped_masks = np.stack([mmcv.imflip(mask, direction=flip_direction) for mask in self.masks])
        return BitmapMasks(flipped_masks, self.height, self.width)

    def pad(self, out_shape, pad_val=0):
        """See :func:`BaseInstanceMasks.pad`."""
        if len(self.masks) == 0:
            padded_masks = np.empty((0, *out_shape), dtype=np.uint8)
        else:
            padded_masks = np.stack([mmcv.impad(mask, shape=out_shape, pad_val=pad_val) for mask in self.masks])
        return BitmapMasks(padded_masks, *out_shape)

    def crop(self, bbox):
        """See :func:`BaseInstanceMasks.crop`."""
        assert isinstance(bbox, np.ndarray)
        assert bbox.ndim == 1
        bbox = bbox.copy()
        bbox[0::2] = np.clip(bbox[0::2], 0, self.width)
        bbox[1::2] = np.clip(bbox[1::2], 0, self.height)
        x1, y1, x2, y2 = bbox
        w = np.maximum(x2 - x1, 1)
        h = np.maximum(y2 - y1, 1)
        if len(self.masks) == 0:
            cropped_masks = np.empty((0, h, w), dtype=np.uint8)
        else:
            cropped_masks = self.masks[:, y1:y1 + h, x1:x1 + w]
        return BitmapMasks(cropped_masks, h, w)

    def crop_and_resize(self, bboxes, out_shape, inds, device='cpu', interpolation='bilinear', binarize=True):
        """See :func:`BaseInstanceMasks.crop_and_resize`."""
        if len(self.masks) == 0:
            empty_masks = np.empty((0, *out_shape), dtype=np.uint8)
            return BitmapMasks(empty_masks, *out_shape)
        if isinstance(bboxes, np.ndarray):
            bboxes = torch.from_numpy(bboxes).to(device=device)
        if isinstance(inds, np.ndarray):
            inds = torch.from_numpy(inds).to(device=device)
        num_bbox = bboxes.shape[0]
        fake_inds = torch.arange(num_bbox, device=device).to(dtype=bboxes.dtype)[:, None]
        rois = torch.cat([fake_inds, bboxes], dim=1)
        rois = rois.to(device=device)
        if num_bbox > 0:
            gt_masks_th = torch.from_numpy(self.masks).to(device).index_select(0, inds).to(dtype=rois.dtype)
            targets = roi_align(gt_masks_th[:, None, :, :], rois, out_shape, 1.0, 0, 'avg', True).squeeze(1)
            if binarize:
                resized_masks = (targets >= 0.5).cpu().numpy()
            else:
                resized_masks = targets.cpu().numpy()
        else:
            resized_masks = []
        return BitmapMasks(resized_masks, *out_shape)

    def expand(self, expanded_h, expanded_w, top, left):
        """See :func:`BaseInstanceMasks.expand`."""
        if len(self.masks) == 0:
            expanded_mask = np.empty((0, expanded_h, expanded_w), dtype=np.uint8)
        else:
            expanded_mask = np.zeros((len(self), expanded_h, expanded_w), dtype=np.uint8)
            expanded_mask[:, top:top + self.height, left:left + self.width] = self.masks
        return BitmapMasks(expanded_mask, expanded_h, expanded_w)

    def translate(self, out_shape, offset, direction='horizontal', fill_val=0, interpolation='bilinear'):
        """Translate the BitmapMasks.

        Args:
            out_shape (tuple[int]): Shape for output mask, format (h, w).
            offset (int | float): The offset for translate.
            direction (str): The translate direction, either "horizontal"
                or "vertical".
            fill_val (int | float): Border value. Default 0 for masks.
            interpolation (str): Same as :func:`mmcv.imtranslate`.

        Returns:
            BitmapMasks: Translated BitmapMasks.

        Example:
            >>> from mmdet.core.mask.structures import BitmapMasks
            >>> self = BitmapMasks.random(dtype=np.uint8)
            >>> out_shape = (32, 32)
            >>> offset = 4
            >>> direction = 'horizontal'
            >>> fill_val = 0
            >>> interpolation = 'bilinear'
            >>> # Note, There seem to be issues when:
            >>> # * out_shape is different than self's shape
            >>> # * the mask dtype is not supported by cv2.AffineWarp
            >>> new = self.translate(out_shape, offset, direction, fill_val,
            >>>                      interpolation)
            >>> assert len(new) == len(self)
            >>> assert new.height, new.width == out_shape
        """
        if len(self.masks) == 0:
            translated_masks = np.empty((0, *out_shape), dtype=np.uint8)
        else:
            translated_masks = mmcv.imtranslate(self.masks.transpose((1, 2, 0)), offset, direction, border_value=fill_val, interpolation=interpolation)
            if translated_masks.ndim == 2:
                translated_masks = translated_masks[:, :, None]
            translated_masks = translated_masks.transpose((2, 0, 1)).astype(self.masks.dtype)
        return BitmapMasks(translated_masks, *out_shape)

    def shear(self, out_shape, magnitude, direction='horizontal', border_value=0, interpolation='bilinear'):
        """Shear the BitmapMasks.

        Args:
            out_shape (tuple[int]): Shape for output mask, format (h, w).
            magnitude (int | float): The magnitude used for shear.
            direction (str): The shear direction, either "horizontal"
                or "vertical".
            border_value (int | tuple[int]): Value used in case of a
                constant border.
            interpolation (str): Same as in :func:`mmcv.imshear`.

        Returns:
            BitmapMasks: The sheared masks.
        """
        if len(self.masks) == 0:
            sheared_masks = np.empty((0, *out_shape), dtype=np.uint8)
        else:
            sheared_masks = mmcv.imshear(self.masks.transpose((1, 2, 0)), magnitude, direction, border_value=border_value, interpolation=interpolation)
            if sheared_masks.ndim == 2:
                sheared_masks = sheared_masks[:, :, None]
            sheared_masks = sheared_masks.transpose((2, 0, 1)).astype(self.masks.dtype)
        return BitmapMasks(sheared_masks, *out_shape)

    def rotate(self, out_shape, angle, center=None, scale=1.0, fill_val=0):
        """Rotate the BitmapMasks.

        Args:
            out_shape (tuple[int]): Shape for output mask, format (h, w).
            angle (int | float): Rotation angle in degrees. Positive values
                mean counter-clockwise rotation.
            center (tuple[float], optional): Center point (w, h) of the
                rotation in source image. If not specified, the center of
                the image will be used.
            scale (int | float): Isotropic scale factor.
            fill_val (int | float): Border value. Default 0 for masks.

        Returns:
            BitmapMasks: Rotated BitmapMasks.
        """
        if len(self.masks) == 0:
            rotated_masks = np.empty((0, *out_shape), dtype=self.masks.dtype)
        else:
            rotated_masks = mmcv.imrotate(self.masks.transpose((1, 2, 0)), angle, center=center, scale=scale, border_value=fill_val)
            if rotated_masks.ndim == 2:
                rotated_masks = rotated_masks[:, :, None]
            rotated_masks = rotated_masks.transpose((2, 0, 1)).astype(self.masks.dtype)
        return BitmapMasks(rotated_masks, *out_shape)

    @property
    def areas(self):
        """See :py:attr:`BaseInstanceMasks.areas`."""
        return self.masks.sum((1, 2))

    def to_ndarray(self):
        """See :func:`BaseInstanceMasks.to_ndarray`."""
        return self.masks

    def to_tensor(self, dtype, device):
        """See :func:`BaseInstanceMasks.to_tensor`."""
        return torch.tensor(self.masks, dtype=dtype, device=device)

    @classmethod
    def random(cls, num_masks=3, height=32, width=32, dtype=np.uint8, rng=None):
        """Generate random bitmap masks for demo / testing purposes.

        Example:
            >>> from mmdet.core.mask.structures import BitmapMasks
            >>> self = BitmapMasks.random()
            >>> print('self = {}'.format(self))
            self = BitmapMasks(num_masks=3, height=32, width=32)
        """
        from mmdet.utils.util_random import ensure_rng
        rng = ensure_rng(rng)
        masks = (rng.rand(num_masks, height, width) > 0.1).astype(dtype)
        self = cls(masks, height=height, width=width)
        return self

    def get_bboxes(self):
        num_masks = len(self)
        boxes = np.zeros((num_masks, 4), dtype=np.float32)
        x_any = self.masks.any(axis=1)
        y_any = self.masks.any(axis=2)
        for idx in range(num_masks):
            x = np.where(x_any[idx, :])[0]
            y = np.where(y_any[idx, :])[0]
            if len(x) > 0 and len(y) > 0:
                boxes[idx, :] = np.array([x[0], y[0], x[-1] + 1, y[-1] + 1], dtype=np.float32)
        return boxes

def __iter__(self):
    return iter(self.masks)

class PolygonMasks(BaseInstanceMasks):
    """This class represents masks in the form of polygons.

    Polygons is a list of three levels. The first level of the list
    corresponds to objects, the second level to the polys that compose the
    object, the third level to the poly coordinates

    Args:
        masks (list[list[ndarray]]): The first level of the list
            corresponds to objects, the second level to the polys that
            compose the object, the third level to the poly coordinates
        height (int): height of masks
        width (int): width of masks

    Example:
        >>> from mmdet.core.mask.structures import *  # NOQA
        >>> masks = [
        >>>     [ np.array([0, 0, 10, 0, 10, 10., 0, 10, 0, 0]) ]
        >>> ]
        >>> height, width = 16, 16
        >>> self = PolygonMasks(masks, height, width)

        >>> # demo translate
        >>> new = self.translate((16, 16), 4., direction='horizontal')
        >>> assert np.all(new.masks[0][0][1::2] == masks[0][0][1::2])
        >>> assert np.all(new.masks[0][0][0::2] == masks[0][0][0::2] + 4)

        >>> # demo crop_and_resize
        >>> num_boxes = 3
        >>> bboxes = np.array([[0, 0, 30, 10.0]] * num_boxes)
        >>> out_shape = (16, 16)
        >>> inds = torch.randint(0, len(self), size=(num_boxes,))
        >>> device = 'cpu'
        >>> interpolation = 'bilinear'
        >>> new = self.crop_and_resize(
        ...     bboxes, out_shape, inds, device, interpolation)
        >>> assert len(new) == num_boxes
        >>> assert new.height, new.width == out_shape
    """

    def __init__(self, masks, height, width):
        assert isinstance(masks, list)
        if len(masks) > 0:
            assert isinstance(masks[0], list)
            assert isinstance(masks[0][0], np.ndarray)
        self.height = height
        self.width = width
        self.masks = masks

    def __getitem__(self, index):
        """Index the polygon masks.

        Args:
            index (ndarray | List): The indices.

        Returns:
            :obj:`PolygonMasks`: The indexed polygon masks.
        """
        if isinstance(index, np.ndarray):
            index = index.tolist()
        if isinstance(index, list):
            masks = [self.masks[i] for i in index]
        else:
            try:
                masks = self.masks[index]
            except Exception:
                raise ValueError(f'Unsupported input of type {type(index)} for indexing!')
        if len(masks) and isinstance(masks[0], np.ndarray):
            masks = [masks]
        return PolygonMasks(masks, self.height, self.width)

    def __iter__(self):
        return iter(self.masks)

    def __repr__(self):
        s = self.__class__.__name__ + '('
        s += f'num_masks={len(self.masks)}, '
        s += f'height={self.height}, '
        s += f'width={self.width})'
        return s

    def __len__(self):
        """Number of masks."""
        return len(self.masks)

    def rescale(self, scale, interpolation=None):
        """see :func:`BaseInstanceMasks.rescale`"""
        new_w, new_h = mmcv.rescale_size((self.width, self.height), scale)
        if len(self.masks) == 0:
            rescaled_masks = PolygonMasks([], new_h, new_w)
        else:
            rescaled_masks = self.resize((new_h, new_w))
        return rescaled_masks

    def resize(self, out_shape, interpolation=None):
        """see :func:`BaseInstanceMasks.resize`"""
        if len(self.masks) == 0:
            resized_masks = PolygonMasks([], *out_shape)
        else:
            h_scale = out_shape[0] / self.height
            w_scale = out_shape[1] / self.width
            resized_masks = []
            for poly_per_obj in self.masks:
                resized_poly = []
                for p in poly_per_obj:
                    p = p.copy()
                    p[0::2] = p[0::2] * w_scale
                    p[1::2] = p[1::2] * h_scale
                    resized_poly.append(p)
                resized_masks.append(resized_poly)
            resized_masks = PolygonMasks(resized_masks, *out_shape)
        return resized_masks

    def flip(self, flip_direction='horizontal'):
        """see :func:`BaseInstanceMasks.flip`"""
        assert flip_direction in ('horizontal', 'vertical', 'diagonal')
        if len(self.masks) == 0:
            flipped_masks = PolygonMasks([], self.height, self.width)
        else:
            flipped_masks = []
            for poly_per_obj in self.masks:
                flipped_poly_per_obj = []
                for p in poly_per_obj:
                    p = p.copy()
                    if flip_direction == 'horizontal':
                        p[0::2] = self.width - p[0::2]
                    elif flip_direction == 'vertical':
                        p[1::2] = self.height - p[1::2]
                    else:
                        p[0::2] = self.width - p[0::2]
                        p[1::2] = self.height - p[1::2]
                    flipped_poly_per_obj.append(p)
                flipped_masks.append(flipped_poly_per_obj)
            flipped_masks = PolygonMasks(flipped_masks, self.height, self.width)
        return flipped_masks

    def crop(self, bbox):
        """see :func:`BaseInstanceMasks.crop`"""
        assert isinstance(bbox, np.ndarray)
        assert bbox.ndim == 1
        bbox = bbox.copy()
        bbox[0::2] = np.clip(bbox[0::2], 0, self.width)
        bbox[1::2] = np.clip(bbox[1::2], 0, self.height)
        x1, y1, x2, y2 = bbox
        w = np.maximum(x2 - x1, 1)
        h = np.maximum(y2 - y1, 1)
        if len(self.masks) == 0:
            cropped_masks = PolygonMasks([], h, w)
        else:
            cropped_masks = []
            for poly_per_obj in self.masks:
                cropped_poly_per_obj = []
                for p in poly_per_obj:
                    p = p.copy()
                    p[0::2] = p[0::2] - bbox[0]
                    p[1::2] = p[1::2] - bbox[1]
                    cropped_poly_per_obj.append(p)
                cropped_masks.append(cropped_poly_per_obj)
            cropped_masks = PolygonMasks(cropped_masks, h, w)
        return cropped_masks

    def pad(self, out_shape, pad_val=0):
        """padding has no effect on polygons`"""
        return PolygonMasks(self.masks, *out_shape)

    def expand(self, *args, **kwargs):
        """TODO: Add expand for polygon"""
        raise NotImplementedError

    def crop_and_resize(self, bboxes, out_shape, inds, device='cpu', interpolation='bilinear', binarize=True):
        """see :func:`BaseInstanceMasks.crop_and_resize`"""
        out_h, out_w = out_shape
        if len(self.masks) == 0:
            return PolygonMasks([], out_h, out_w)
        if not binarize:
            raise ValueError('Polygons are always binary, setting binarize=False is unsupported')
        resized_masks = []
        for i in range(len(bboxes)):
            mask = self.masks[inds[i]]
            bbox = bboxes[i, :]
            x1, y1, x2, y2 = bbox
            w = np.maximum(x2 - x1, 1)
            h = np.maximum(y2 - y1, 1)
            h_scale = out_h / max(h, 0.1)
            w_scale = out_w / max(w, 0.1)
            resized_mask = []
            for p in mask:
                p = p.copy()
                p[0::2] = p[0::2] - bbox[0]
                p[1::2] = p[1::2] - bbox[1]
                p[0::2] = p[0::2] * w_scale
                p[1::2] = p[1::2] * h_scale
                resized_mask.append(p)
            resized_masks.append(resized_mask)
        return PolygonMasks(resized_masks, *out_shape)

    def translate(self, out_shape, offset, direction='horizontal', fill_val=None, interpolation=None):
        """Translate the PolygonMasks.

        Example:
            >>> self = PolygonMasks.random(dtype=np.int)
            >>> out_shape = (self.height, self.width)
            >>> new = self.translate(out_shape, 4., direction='horizontal')
            >>> assert np.all(new.masks[0][0][1::2] == self.masks[0][0][1::2])
            >>> assert np.all(new.masks[0][0][0::2] == self.masks[0][0][0::2] + 4)  # noqa: E501
        """
        assert fill_val is None or fill_val == 0, f'Here fill_val is not used, and defaultly should be None or 0. got {fill_val}.'
        if len(self.masks) == 0:
            translated_masks = PolygonMasks([], *out_shape)
        else:
            translated_masks = []
            for poly_per_obj in self.masks:
                translated_poly_per_obj = []
                for p in poly_per_obj:
                    p = p.copy()
                    if direction == 'horizontal':
                        p[0::2] = np.clip(p[0::2] + offset, 0, out_shape[1])
                    elif direction == 'vertical':
                        p[1::2] = np.clip(p[1::2] + offset, 0, out_shape[0])
                    translated_poly_per_obj.append(p)
                translated_masks.append(translated_poly_per_obj)
            translated_masks = PolygonMasks(translated_masks, *out_shape)
        return translated_masks

    def shear(self, out_shape, magnitude, direction='horizontal', border_value=0, interpolation='bilinear'):
        """See :func:`BaseInstanceMasks.shear`."""
        if len(self.masks) == 0:
            sheared_masks = PolygonMasks([], *out_shape)
        else:
            sheared_masks = []
            if direction == 'horizontal':
                shear_matrix = np.stack([[1, magnitude], [0, 1]]).astype(np.float32)
            elif direction == 'vertical':
                shear_matrix = np.stack([[1, 0], [magnitude, 1]]).astype(np.float32)
            for poly_per_obj in self.masks:
                sheared_poly = []
                for p in poly_per_obj:
                    p = np.stack([p[0::2], p[1::2]], axis=0)
                    new_coords = np.matmul(shear_matrix, p)
                    new_coords[0, :] = np.clip(new_coords[0, :], 0, out_shape[1])
                    new_coords[1, :] = np.clip(new_coords[1, :], 0, out_shape[0])
                    sheared_poly.append(new_coords.transpose((1, 0)).reshape(-1))
                sheared_masks.append(sheared_poly)
            sheared_masks = PolygonMasks(sheared_masks, *out_shape)
        return sheared_masks

    def rotate(self, out_shape, angle, center=None, scale=1.0, fill_val=0):
        """See :func:`BaseInstanceMasks.rotate`."""
        if len(self.masks) == 0:
            rotated_masks = PolygonMasks([], *out_shape)
        else:
            rotated_masks = []
            rotate_matrix = cv2.getRotationMatrix2D(center, -angle, scale)
            for poly_per_obj in self.masks:
                rotated_poly = []
                for p in poly_per_obj:
                    p = p.copy()
                    coords = np.stack([p[0::2], p[1::2]], axis=1)
                    coords = np.concatenate((coords, np.ones((coords.shape[0], 1), coords.dtype)), axis=1)
                    rotated_coords = np.matmul(rotate_matrix[None, :, :], coords[:, :, None])[..., 0]
                    rotated_coords[:, 0] = np.clip(rotated_coords[:, 0], 0, out_shape[1])
                    rotated_coords[:, 1] = np.clip(rotated_coords[:, 1], 0, out_shape[0])
                    rotated_poly.append(rotated_coords.reshape(-1))
                rotated_masks.append(rotated_poly)
            rotated_masks = PolygonMasks(rotated_masks, *out_shape)
        return rotated_masks

    def to_bitmap(self):
        """convert polygon masks to bitmap masks."""
        bitmap_masks = self.to_ndarray()
        return BitmapMasks(bitmap_masks, self.height, self.width)

    @property
    def areas(self):
        """Compute areas of masks.

        This func is modified from `detectron2
        <https://github.com/facebookresearch/detectron2/blob/ffff8acc35ea88ad1cb1806ab0f00b4c1c5dbfd9/detectron2/structures/masks.py#L387>`_.
        The function only works with Polygons using the shoelace formula.

        Return:
            ndarray: areas of each instance
        """
        area = []
        for polygons_per_obj in self.masks:
            area_per_obj = 0
            for p in polygons_per_obj:
                area_per_obj += self._polygon_area(p[0::2], p[1::2])
            area.append(area_per_obj)
        return np.asarray(area)

    def _polygon_area(self, x, y):
        """Compute the area of a component of a polygon.

        Using the shoelace formula:
        https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates

        Args:
            x (ndarray): x coordinates of the component
            y (ndarray): y coordinates of the component

        Return:
            float: the are of the component
        """
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    def to_ndarray(self):
        """Convert masks to the format of ndarray."""
        if len(self.masks) == 0:
            return np.empty((0, self.height, self.width), dtype=np.uint8)
        bitmap_masks = []
        for poly_per_obj in self.masks:
            bitmap_masks.append(polygon_to_bitmap(poly_per_obj, self.height, self.width))
        return np.stack(bitmap_masks)

    def to_tensor(self, dtype, device):
        """See :func:`BaseInstanceMasks.to_tensor`."""
        if len(self.masks) == 0:
            return torch.empty((0, self.height, self.width), dtype=dtype, device=device)
        ndarray_masks = self.to_ndarray()
        return torch.tensor(ndarray_masks, dtype=dtype, device=device)

    @classmethod
    def random(cls, num_masks=3, height=32, width=32, n_verts=5, dtype=np.float32, rng=None):
        """Generate random polygon masks for demo / testing purposes.

        Adapted from [1]_

        References:
            .. [1] https://gitlab.kitware.com/computer-vision/kwimage/-/blob/928cae35ca8/kwimage/structs/polygon.py#L379  # noqa: E501

        Example:
            >>> from mmdet.core.mask.structures import PolygonMasks
            >>> self = PolygonMasks.random()
            >>> print('self = {}'.format(self))
        """
        from mmdet.utils.util_random import ensure_rng
        rng = ensure_rng(rng)

        def _gen_polygon(n, irregularity, spikeyness):
            """Creates the polygon by sampling points on a circle around the
            centre.  Random noise is added by varying the angular spacing
            between sequential points, and by varying the radial distance of
            each point from the centre.

            Based on original code by Mike Ounsworth

            Args:
                n (int): number of vertices
                irregularity (float): [0,1] indicating how much variance there
                    is in the angular spacing of vertices. [0,1] will map to
                    [0, 2pi/numberOfVerts]
                spikeyness (float): [0,1] indicating how much variance there is
                    in each vertex from the circle of radius aveRadius. [0,1]
                    will map to [0, aveRadius]

            Returns:
                a list of vertices, in CCW order.
            """
            from scipy.stats import truncnorm
            cx, cy = (0.0, 0.0)
            radius = 1
            tau = np.pi * 2
            irregularity = np.clip(irregularity, 0, 1) * 2 * np.pi / n
            spikeyness = np.clip(spikeyness, 1e-09, 1)
            lower = tau / n - irregularity
            upper = tau / n + irregularity
            angle_steps = rng.uniform(lower, upper, n)
            k = angle_steps.sum() / (2 * np.pi)
            angles = (angle_steps / k).cumsum() + rng.uniform(0, tau)
            low = 0
            high = 2 * radius
            mean = radius
            std = spikeyness
            a = (low - mean) / std
            b = (high - mean) / std
            tnorm = truncnorm(a=a, b=b, loc=mean, scale=std)
            radii = tnorm.rvs(n, random_state=rng)
            x_pts = cx + radii * np.cos(angles)
            y_pts = cy + radii * np.sin(angles)
            points = np.hstack([x_pts[:, None], y_pts[:, None]])
            points = points - points.min(axis=0)
            points = points / points.max(axis=0)
            points = points * (rng.rand() * 0.8 + 0.2)
            min_pt = points.min(axis=0)
            max_pt = points.max(axis=0)
            high = 1 - max_pt
            low = 0 - min_pt
            offset = rng.rand(2) * (high - low) + low
            points = points + offset
            return points

        def _order_vertices(verts):
            """
            References:
                https://stackoverflow.com/questions/1709283/how-can-i-sort-a-coordinate-list-for-a-rectangle-counterclockwise
            """
            mlat = verts.T[0].sum() / len(verts)
            mlng = verts.T[1].sum() / len(verts)
            tau = np.pi * 2
            angle = (np.arctan2(mlat - verts.T[0], verts.T[1] - mlng) + tau) % tau
            sortx = angle.argsort()
            verts = verts.take(sortx, axis=0)
            return verts
        masks = []
        for _ in range(num_masks):
            exterior = _order_vertices(_gen_polygon(n_verts, 0.9, 0.9))
            exterior = (exterior * [(width, height)]).astype(dtype)
            masks.append([exterior.ravel()])
        self = cls(masks, height, width)
        return self

    def get_bboxes(self):
        num_masks = len(self)
        boxes = np.zeros((num_masks, 4), dtype=np.float32)
        for idx, poly_per_obj in enumerate(self.masks):
            xy_min = np.array([self.width * 2, self.height * 2], dtype=np.float32)
            xy_max = np.zeros(2, dtype=np.float32)
            for p in poly_per_obj:
                xy = np.array(p).reshape(-1, 2).astype(np.float32)
                xy_min = np.minimum(xy_min, np.min(xy, axis=0))
                xy_max = np.maximum(xy_max, np.max(xy, axis=0))
            boxes[idx, :2] = xy_min
            boxes[idx, 2:] = xy_max
        return boxes

def __iter__(self):
    return iter(self.masks)

def filter_scores_and_topk(scores, score_thr, topk, results=None):
    """Filter results using score threshold and topk candidates.

    Args:
        scores (Tensor): The scores, shape (num_bboxes, K).
        score_thr (float): The score filter threshold.
        topk (int): The number of topk candidates.
        results (dict or list or Tensor, Optional): The results to
           which the filtering rule is to be applied. The shape
           of each item is (num_bboxes, N).

    Returns:
        tuple: Filtered results

            - scores (Tensor): The scores after being filtered,                 shape (num_bboxes_filtered, ).
            - labels (Tensor): The class labels, shape                 (num_bboxes_filtered, ).
            - anchor_idxs (Tensor): The anchor indexes, shape                 (num_bboxes_filtered, ).
            - filtered_results (dict or list or Tensor, Optional):                 The filtered results. The shape of each item is                 (num_bboxes_filtered, N).
    """
    valid_mask = scores > score_thr
    scores = scores[valid_mask]
    valid_idxs = torch.nonzero(valid_mask)
    num_topk = min(topk, valid_idxs.size(0))
    scores, idxs = scores.sort(descending=True)
    scores = scores[:num_topk]
    topk_idxs = valid_idxs[idxs[:num_topk]]
    keep_idxs, labels = topk_idxs.unbind(dim=1)
    filtered_results = None
    if results is not None:
        if isinstance(results, dict):
            filtered_results = {k: v[keep_idxs] for k, v in results.items()}
        elif isinstance(results, list):
            filtered_results = [result[keep_idxs] for result in results]
        elif isinstance(results, torch.Tensor):
            filtered_results = results[keep_idxs]
        else:
            raise NotImplementedError(f'Only supports dict or list or Tensor, but get {type(results)}.')
    return (scores, labels, keep_idxs, filtered_results)

def obj2tensor(pyobj, device='cuda'):
    """Serialize picklable python object to tensor."""
    storage = torch.ByteStorage.from_buffer(pickle.dumps(pyobj))
    return torch.ByteTensor(storage).to(device=device)

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

class BaseEMAHook(Hook):
    """Exponential Moving Average Hook.

    Use Exponential Moving Average on all parameters of model in training
    process. All parameters have a ema backup, which update by the formula
    as below. EMAHook takes priority over EvalHook and CheckpointHook. Note,
    the original model parameters are actually saved in ema field after train.

    Args:
        momentum (float): The momentum used for updating ema parameter.
            Ema's parameter are updated with the formula:
           `ema_param = (1-momentum) * ema_param + momentum * cur_param`.
            Defaults to 0.0002.
        skip_buffers (bool): Whether to skip the model buffers, such as
            batchnorm running stats (running_mean, running_var), it does not
            perform the ema operation. Default to False.
        interval (int): Update ema parameter every interval iteration.
            Defaults to 1.
        resume_from (str, optional): The checkpoint path. Defaults to None.
        momentum_fun (func, optional): The function to change momentum
            during early iteration (also warmup) to help early training.
            It uses `momentum` as a constant. Defaults to None.
    """

    def __init__(self, momentum=0.0002, interval=1, skip_buffers=False, resume_from=None, momentum_fun=None):
        assert 0 < momentum < 1
        self.momentum = momentum
        self.skip_buffers = skip_buffers
        self.interval = interval
        self.checkpoint = resume_from
        self.momentum_fun = momentum_fun

    def before_run(self, runner):
        """To resume model with it's ema parameters more friendly.

        Register ema parameter as ``named_buffer`` to model.
        """
        model = runner.model
        if is_module_wrapper(model):
            model = model.module
        self.param_ema_buffer = {}
        if self.skip_buffers:
            self.model_parameters = dict(model.named_parameters())
        else:
            self.model_parameters = model.state_dict()
        for name, value in self.model_parameters.items():
            buffer_name = f'ema_{name.replace('.', '_')}'
            self.param_ema_buffer[name] = buffer_name
            model.register_buffer(buffer_name, value.data.clone())
        self.model_buffers = dict(model.named_buffers())
        if self.checkpoint is not None:
            runner.resume(self.checkpoint)

    def get_momentum(self, runner):
        return self.momentum_fun(runner.iter) if self.momentum_fun else self.momentum

    def after_train_iter(self, runner):
        """Update ema parameter every self.interval iterations."""
        if (runner.iter + 1) % self.interval != 0:
            return
        momentum = self.get_momentum(runner)
        for name, parameter in self.model_parameters.items():
            if parameter.dtype.is_floating_point:
                buffer_name = self.param_ema_buffer[name]
                buffer_parameter = self.model_buffers[buffer_name]
                buffer_parameter.mul_(1 - momentum).add_(parameter.data, alpha=momentum)

    def after_train_epoch(self, runner):
        """We load parameter values from ema backup to model before the
        EvalHook."""
        self._swap_ema_parameters()

    def before_train_epoch(self, runner):
        """We recover model's parameter from ema backup after last epoch's
        EvalHook."""
        self._swap_ema_parameters()

    def _swap_ema_parameters(self):
        """Swap the parameter of model with parameter in ema_buffer."""
        for name, value in self.model_parameters.items():
            temp = value.data.clone()
            ema_buffer = self.model_buffers[self.param_ema_buffer[name]]
            value.data.copy_(ema_buffer.data)
            ema_buffer.data.copy_(temp)

def before_run(self, runner):
    """To resume model with it's ema parameters more friendly.

        Register ema parameter as ``named_buffer`` to model.
        """
    model = runner.model
    if is_module_wrapper(model):
        model = model.module
    self.param_ema_buffer = {}
    if self.skip_buffers:
        self.model_parameters = dict(model.named_parameters())
    else:
        self.model_parameters = model.state_dict()
    for name, value in self.model_parameters.items():
        buffer_name = f'ema_{name.replace('.', '_')}'
        self.param_ema_buffer[name] = buffer_name
        model.register_buffer(buffer_name, value.data.clone())
    self.model_buffers = dict(model.named_buffers())
    if self.checkpoint is not None:
        runner.resume(self.checkpoint)

def after_train_iter(self, runner):
    """Update ema parameter every self.interval iterations."""
    if (runner.iter + 1) % self.interval != 0:
        return
    momentum = self.get_momentum(runner)
    for name, parameter in self.model_parameters.items():
        if parameter.dtype.is_floating_point:
            buffer_name = self.param_ema_buffer[name]
            buffer_parameter = self.model_buffers[buffer_name]
            buffer_parameter.mul_(1 - momentum).add_(parameter.data, alpha=momentum)

def get_norm_states(module):
    async_norm_states = OrderedDict()
    for name, child in module.named_modules():
        if isinstance(child, nn.modules.batchnorm._NormBase):
            for k, v in child.state_dict().items():
                async_norm_states['.'.join([name, k])] = v
    return async_norm_states

@HOOKS.register_module()
class SyncNormHook(Hook):
    """Synchronize Norm states after training epoch, currently used in YOLOX.

    Args:
        num_last_epochs (int): The number of latter epochs in the end of the
            training to switch to synchronizing norm interval. Default: 15.
        interval (int): Synchronizing norm interval. Default: 1.
    """

    def __init__(self, num_last_epochs=15, interval=1):
        self.interval = interval
        self.num_last_epochs = num_last_epochs

    def before_train_epoch(self, runner):
        epoch = runner.epoch
        if epoch + 1 == runner.max_epochs - self.num_last_epochs:
            self.interval = 1

    def after_train_epoch(self, runner):
        """Synchronizing norm."""
        epoch = runner.epoch
        module = runner.model
        if (epoch + 1) % self.interval == 0:
            _, world_size = get_dist_info()
            if world_size == 1:
                return
            norm_states = get_norm_states(module)
            if len(norm_states) == 0:
                return
            norm_states = all_reduce_dict(norm_states, op='mean')
            module.load_state_dict(norm_states, strict=False)

def after_train_epoch(self, runner):
    """Synchronizing norm."""
    epoch = runner.epoch
    module = runner.model
    if (epoch + 1) % self.interval == 0:
        _, world_size = get_dist_info()
        if world_size == 1:
            return
        norm_states = get_norm_states(module)
        if len(norm_states) == 0:
            return
        norm_states = all_reduce_dict(norm_states, op='mean')
        module.load_state_dict(norm_states, strict=False)

@HOOKS.register_module()
class YOLOXModeSwitchHook(Hook):
    """Switch the mode of YOLOX during training.

    This hook turns off the mosaic and mixup data augmentation and switches
    to use L1 loss in bbox_head.

    Args:
        num_last_epochs (int): The number of latter epochs in the end of the
            training to close the data augmentation and switch to L1 loss.
            Default: 15.
       skip_type_keys (list[str], optional): Sequence of type string to be
            skip pipeline. Default: ('Mosaic', 'RandomAffine', 'MixUp')
    """

    def __init__(self, num_last_epochs=15, skip_type_keys=('Mosaic', 'RandomAffine', 'MixUp')):
        self.num_last_epochs = num_last_epochs
        self.skip_type_keys = skip_type_keys
        self._restart_dataloader = False

    def before_train_epoch(self, runner):
        """Close mosaic and mixup augmentation and switches to use L1 loss."""
        epoch = runner.epoch
        train_loader = runner.data_loader
        model = runner.model
        if is_module_wrapper(model):
            model = model.module
        if epoch + 1 == runner.max_epochs - self.num_last_epochs:
            runner.logger.info('No mosaic and mixup aug now!')
            train_loader.dataset.update_skip_type_keys(self.skip_type_keys)
            if hasattr(train_loader, 'persistent_workers') and train_loader.persistent_workers is True:
                train_loader._DataLoader__initialized = False
                train_loader._iterator = None
                self._restart_dataloader = True
            runner.logger.info('Add additional L1 loss now!')
            model.bbox_head.use_l1 = True
        elif self._restart_dataloader:
            train_loader._DataLoader__initialized = True

def before_train_epoch(self, runner):
    """Close mosaic and mixup augmentation and switches to use L1 loss."""
    epoch = runner.epoch
    train_loader = runner.data_loader
    model = runner.model
    if is_module_wrapper(model):
        model = model.module
    if epoch + 1 == runner.max_epochs - self.num_last_epochs:
        runner.logger.info('No mosaic and mixup aug now!')
        train_loader.dataset.update_skip_type_keys(self.skip_type_keys)
        if hasattr(train_loader, 'persistent_workers') and train_loader.persistent_workers is True:
            train_loader._DataLoader__initialized = False
            train_loader._iterator = None
            self._restart_dataloader = True
        runner.logger.info('Add additional L1 loss now!')
        model.bbox_head.use_l1 = True
    elif self._restart_dataloader:
        train_loader._DataLoader__initialized = True

@HOOKS.register_module()
class SetEpochInfoHook(Hook):
    """Set runner's epoch information to the model."""

    def before_train_epoch(self, runner):
        epoch = runner.epoch
        model = runner.model
        if is_module_wrapper(model):
            model = model.module
        model.set_epoch(epoch)

def before_train_epoch(self, runner):
    epoch = runner.epoch
    model = runner.model
    if is_module_wrapper(model):
        model = model.module
    model.set_epoch(epoch)

@HOOKS.register_module()
class YOLOXLrUpdaterHook(CosineAnnealingLrUpdaterHook):
    """YOLOX learning rate scheme.

    There are two main differences between YOLOXLrUpdaterHook
    and CosineAnnealingLrUpdaterHook.

       1. When the current running epoch is greater than
           `max_epoch-last_epoch`, a fixed learning rate will be used
       2. The exp warmup scheme is different with LrUpdaterHook in MMCV

    Args:
        num_last_epochs (int): The number of epochs with a fixed learning rate
           before the end of the training.
    """

    def __init__(self, num_last_epochs, **kwargs):
        self.num_last_epochs = num_last_epochs
        super(YOLOXLrUpdaterHook, self).__init__(**kwargs)

    def get_warmup_lr(self, cur_iters):

        def _get_warmup_lr(cur_iters, regular_lr):
            k = self.warmup_ratio * pow((cur_iters + 1) / float(self.warmup_iters), 2)
            warmup_lr = [_lr * k for _lr in regular_lr]
            return warmup_lr
        if isinstance(self.base_lr, dict):
            lr_groups = {}
            for key, base_lr in self.base_lr.items():
                lr_groups[key] = _get_warmup_lr(cur_iters, base_lr)
            return lr_groups
        else:
            return _get_warmup_lr(cur_iters, self.base_lr)

    def get_lr(self, runner, base_lr):
        last_iter = len(runner.data_loader) * self.num_last_epochs
        if self.by_epoch:
            progress = runner.epoch
            max_progress = runner.max_epochs
        else:
            progress = runner.iter
            max_progress = runner.max_iters
        progress += 1
        if self.min_lr_ratio is not None:
            target_lr = base_lr * self.min_lr_ratio
        else:
            target_lr = self.min_lr
        if progress >= max_progress - last_iter:
            return target_lr
        else:
            return annealing_cos(base_lr, target_lr, (progress - self.warmup_iters) / (max_progress - self.warmup_iters - last_iter))

def get_warmup_lr(self, cur_iters):

    def _get_warmup_lr(cur_iters, regular_lr):
        k = self.warmup_ratio * pow((cur_iters + 1) / float(self.warmup_iters), 2)
        warmup_lr = [_lr * k for _lr in regular_lr]
        return warmup_lr
    if isinstance(self.base_lr, dict):
        lr_groups = {}
        for key, base_lr in self.base_lr.items():
            lr_groups[key] = _get_warmup_lr(cur_iters, base_lr)
        return lr_groups
    else:
        return _get_warmup_lr(cur_iters, self.base_lr)

class MaskSamplingResult(SamplingResult):
    """Mask sampling result."""

    def __init__(self, pos_inds, neg_inds, masks, gt_masks, assign_result, gt_flags):
        self.pos_inds = pos_inds
        self.neg_inds = neg_inds
        self.pos_masks = masks[pos_inds]
        self.neg_masks = masks[neg_inds]
        self.pos_is_gt = gt_flags[pos_inds]
        self.num_gts = gt_masks.shape[0]
        self.pos_assigned_gt_inds = assign_result.gt_inds[pos_inds] - 1
        if gt_masks.numel() == 0:
            assert self.pos_assigned_gt_inds.numel() == 0
            self.pos_gt_masks = torch.empty_like(gt_masks)
        else:
            self.pos_gt_masks = gt_masks[self.pos_assigned_gt_inds, :]
        if assign_result.labels is not None:
            self.pos_gt_labels = assign_result.labels[pos_inds]
        else:
            self.pos_gt_labels = None

    @property
    def masks(self):
        """torch.Tensor: concatenated positive and negative boxes"""
        return torch.cat([self.pos_masks, self.neg_masks])

    def __nice__(self):
        data = self.info.copy()
        data['pos_masks'] = data.pop('pos_masks').shape
        data['neg_masks'] = data.pop('neg_masks').shape
        parts = [f"'{k}': {v!r}" for k, v in sorted(data.items())]
        body = '    ' + ',\n    '.join(parts)
        return '{\n' + body + '\n}'

    @property
    def info(self):
        """Returns a dictionary of info about the object."""
        return {'pos_inds': self.pos_inds, 'neg_inds': self.neg_inds, 'pos_masks': self.pos_masks, 'neg_masks': self.neg_masks, 'pos_is_gt': self.pos_is_gt, 'num_gts': self.num_gts, 'pos_assigned_gt_inds': self.pos_assigned_gt_inds}

def __nice__(self):
    data = self.info.copy()
    data['pos_masks'] = data.pop('pos_masks').shape
    data['neg_masks'] = data.pop('neg_masks').shape
    parts = [f"'{k}': {v!r}" for k, v in sorted(data.items())]
    body = '    ' + ',\n    '.join(parts)
    return '{\n' + body + '\n}'

class SamplingResult(util_mixins.NiceRepr):
    """Bbox sampling result.

    Example:
        >>> # xdoctest: +IGNORE_WANT
        >>> from mmdet.core.bbox.samplers.sampling_result import *  # NOQA
        >>> self = SamplingResult.random(rng=10)
        >>> print(f'self = {self}')
        self = <SamplingResult({
            'neg_bboxes': torch.Size([12, 4]),
            'neg_inds': tensor([ 0,  1,  2,  4,  5,  6,  7,  8,  9, 10, 11, 12]),
            'num_gts': 4,
            'pos_assigned_gt_inds': tensor([], dtype=torch.int64),
            'pos_bboxes': torch.Size([0, 4]),
            'pos_inds': tensor([], dtype=torch.int64),
            'pos_is_gt': tensor([], dtype=torch.uint8)
        })>
    """

    def __init__(self, pos_inds, neg_inds, bboxes, gt_bboxes, assign_result, gt_flags):
        self.pos_inds = pos_inds
        self.neg_inds = neg_inds
        self.pos_bboxes = bboxes[pos_inds]
        self.neg_bboxes = bboxes[neg_inds]
        self.pos_is_gt = gt_flags[pos_inds]
        self.num_gts = gt_bboxes.shape[0]
        self.pos_assigned_gt_inds = assign_result.gt_inds[pos_inds] - 1
        if gt_bboxes.numel() == 0:
            assert self.pos_assigned_gt_inds.numel() == 0
            self.pos_gt_bboxes = torch.empty_like(gt_bboxes).view(-1, 4)
        else:
            if len(gt_bboxes.shape) < 2:
                gt_bboxes = gt_bboxes.view(-1, 4)
            self.pos_gt_bboxes = gt_bboxes[self.pos_assigned_gt_inds.long(), :]
        if assign_result.labels is not None:
            self.pos_gt_labels = assign_result.labels[pos_inds]
        else:
            self.pos_gt_labels = None

    @property
    def bboxes(self):
        """torch.Tensor: concatenated positive and negative boxes"""
        return torch.cat([self.pos_bboxes, self.neg_bboxes])

    def to(self, device):
        """Change the device of the data inplace.

        Example:
            >>> self = SamplingResult.random()
            >>> print(f'self = {self.to(None)}')
            >>> # xdoctest: +REQUIRES(--gpu)
            >>> print(f'self = {self.to(0)}')
        """
        _dict = self.__dict__
        for key, value in _dict.items():
            if isinstance(value, torch.Tensor):
                _dict[key] = value.to(device)
        return self

    def __nice__(self):
        data = self.info.copy()
        data['pos_bboxes'] = data.pop('pos_bboxes').shape
        data['neg_bboxes'] = data.pop('neg_bboxes').shape
        parts = [f"'{k}': {v!r}" for k, v in sorted(data.items())]
        body = '    ' + ',\n    '.join(parts)
        return '{\n' + body + '\n}'

    @property
    def info(self):
        """Returns a dictionary of info about the object."""
        return {'pos_inds': self.pos_inds, 'neg_inds': self.neg_inds, 'pos_bboxes': self.pos_bboxes, 'neg_bboxes': self.neg_bboxes, 'pos_is_gt': self.pos_is_gt, 'num_gts': self.num_gts, 'pos_assigned_gt_inds': self.pos_assigned_gt_inds}

    @classmethod
    def random(cls, rng=None, **kwargs):
        """
        Args:
            rng (None | int | numpy.random.RandomState): seed or state.
            kwargs (keyword arguments):
                - num_preds: number of predicted boxes
                - num_gts: number of true boxes
                - p_ignore (float): probability of a predicted box assigned to                     an ignored truth.
                - p_assigned (float): probability of a predicted box not being                     assigned.
                - p_use_label (float | bool): with labels or not.

        Returns:
            :obj:`SamplingResult`: Randomly generated sampling result.

        Example:
            >>> from mmdet.core.bbox.samplers.sampling_result import *  # NOQA
            >>> self = SamplingResult.random()
            >>> print(self.__dict__)
        """
        from mmdet.core.bbox import demodata
        from mmdet.core.bbox.assigners.assign_result import AssignResult
        from mmdet.core.bbox.samplers.random_sampler import RandomSampler
        rng = demodata.ensure_rng(rng)
        num = 32
        pos_fraction = 0.5
        neg_pos_ub = -1
        assign_result = AssignResult.random(rng=rng, **kwargs)
        bboxes = demodata.random_boxes(assign_result.num_preds, rng=rng)
        gt_bboxes = demodata.random_boxes(assign_result.num_gts, rng=rng)
        if rng.rand() > 0.2:
            gt_bboxes = gt_bboxes.squeeze()
            bboxes = bboxes.squeeze()
        if assign_result.labels is None:
            gt_labels = None
        else:
            gt_labels = None
        if gt_labels is None:
            add_gt_as_proposals = False
        else:
            add_gt_as_proposals = True
        sampler = RandomSampler(num, pos_fraction, neg_pos_ub=neg_pos_ub, add_gt_as_proposals=add_gt_as_proposals, rng=rng)
        self = sampler.sample(assign_result, bboxes, gt_bboxes, gt_labels)
        return self

def to(self, device):
    """Change the device of the data inplace.

        Example:
            >>> self = SamplingResult.random()
            >>> print(f'self = {self.to(None)}')
            >>> # xdoctest: +REQUIRES(--gpu)
            >>> print(f'self = {self.to(0)}')
        """
    _dict = self.__dict__
    for key, value in _dict.items():
        if isinstance(value, torch.Tensor):
            _dict[key] = value.to(device)
    return self

def __nice__(self):
    data = self.info.copy()
    data['pos_bboxes'] = data.pop('pos_bboxes').shape
    data['neg_bboxes'] = data.pop('neg_bboxes').shape
    parts = [f"'{k}': {v!r}" for k, v in sorted(data.items())]
    body = '    ' + ',\n    '.join(parts)
    return '{\n' + body + '\n}'

class AssignResult(util_mixins.NiceRepr):
    """Stores assignments between predicted and truth boxes.

    Attributes:
        num_gts (int): the number of truth boxes considered when computing this
            assignment

        gt_inds (LongTensor): for each predicted box indicates the 1-based
            index of the assigned truth box. 0 means unassigned and -1 means
            ignore.

        max_overlaps (FloatTensor): the iou between the predicted box and its
            assigned truth box.

        labels (None | LongTensor): If specified, for each predicted box
            indicates the category label of the assigned truth box.

    Example:
        >>> # An assign result between 4 predicted boxes and 9 true boxes
        >>> # where only two boxes were assigned.
        >>> num_gts = 9
        >>> max_overlaps = torch.LongTensor([0, .5, .9, 0])
        >>> gt_inds = torch.LongTensor([-1, 1, 2, 0])
        >>> labels = torch.LongTensor([0, 3, 4, 0])
        >>> self = AssignResult(num_gts, gt_inds, max_overlaps, labels)
        >>> print(str(self))  # xdoctest: +IGNORE_WANT
        <AssignResult(num_gts=9, gt_inds.shape=(4,), max_overlaps.shape=(4,),
                      labels.shape=(4,))>
        >>> # Force addition of gt labels (when adding gt as proposals)
        >>> new_labels = torch.LongTensor([3, 4, 5])
        >>> self.add_gt_(new_labels)
        >>> print(str(self))  # xdoctest: +IGNORE_WANT
        <AssignResult(num_gts=9, gt_inds.shape=(7,), max_overlaps.shape=(7,),
                      labels.shape=(7,))>
    """

    def __init__(self, num_gts, gt_inds, max_overlaps, labels=None):
        self.num_gts = num_gts
        self.gt_inds = gt_inds
        self.max_overlaps = max_overlaps
        self.labels = labels
        self._extra_properties = {}

    @property
    def num_preds(self):
        """int: the number of predictions in this assignment"""
        return len(self.gt_inds)

    def set_extra_property(self, key, value):
        """Set user-defined new property."""
        assert key not in self.info
        self._extra_properties[key] = value

    def get_extra_property(self, key):
        """Get user-defined property."""
        return self._extra_properties.get(key, None)

    @property
    def info(self):
        """dict: a dictionary of info about the object"""
        basic_info = {'num_gts': self.num_gts, 'num_preds': self.num_preds, 'gt_inds': self.gt_inds, 'max_overlaps': self.max_overlaps, 'labels': self.labels}
        basic_info.update(self._extra_properties)
        return basic_info

    def __nice__(self):
        """str: a "nice" summary string describing this assign result"""
        parts = []
        parts.append(f'num_gts={self.num_gts!r}')
        if self.gt_inds is None:
            parts.append(f'gt_inds={self.gt_inds!r}')
        else:
            parts.append(f'gt_inds.shape={tuple(self.gt_inds.shape)!r}')
        if self.max_overlaps is None:
            parts.append(f'max_overlaps={self.max_overlaps!r}')
        else:
            parts.append(f'max_overlaps.shape={tuple(self.max_overlaps.shape)!r}')
        if self.labels is None:
            parts.append(f'labels={self.labels!r}')
        else:
            parts.append(f'labels.shape={tuple(self.labels.shape)!r}')
        return ', '.join(parts)

    @classmethod
    def random(cls, **kwargs):
        """Create random AssignResult for tests or debugging.

        Args:
            num_preds: number of predicted boxes
            num_gts: number of true boxes
            p_ignore (float): probability of a predicted box assigned to an
                ignored truth
            p_assigned (float): probability of a predicted box not being
                assigned
            p_use_label (float | bool): with labels or not
            rng (None | int | numpy.random.RandomState): seed or state

        Returns:
            :obj:`AssignResult`: Randomly generated assign results.

        Example:
            >>> from mmdet.core.bbox.assigners.assign_result import *  # NOQA
            >>> self = AssignResult.random()
            >>> print(self.info)
        """
        from mmdet.core.bbox import demodata
        rng = demodata.ensure_rng(kwargs.get('rng', None))
        num_gts = kwargs.get('num_gts', None)
        num_preds = kwargs.get('num_preds', None)
        p_ignore = kwargs.get('p_ignore', 0.3)
        p_assigned = kwargs.get('p_assigned', 0.7)
        p_use_label = kwargs.get('p_use_label', 0.5)
        num_classes = kwargs.get('p_use_label', 3)
        if num_gts is None:
            num_gts = rng.randint(0, 8)
        if num_preds is None:
            num_preds = rng.randint(0, 16)
        if num_gts == 0:
            max_overlaps = torch.zeros(num_preds, dtype=torch.float32)
            gt_inds = torch.zeros(num_preds, dtype=torch.int64)
            if p_use_label is True or p_use_label < rng.rand():
                labels = torch.zeros(num_preds, dtype=torch.int64)
            else:
                labels = None
        else:
            import numpy as np
            max_overlaps = torch.from_numpy(rng.rand(num_preds))
            is_assigned = torch.from_numpy(rng.rand(num_preds) < p_assigned)
            n_assigned = min(num_preds, min(num_gts, is_assigned.sum()))
            assigned_idxs = np.where(is_assigned)[0]
            rng.shuffle(assigned_idxs)
            assigned_idxs = assigned_idxs[0:n_assigned]
            assigned_idxs.sort()
            is_assigned[:] = 0
            is_assigned[assigned_idxs] = True
            is_ignore = torch.from_numpy(rng.rand(num_preds) < p_ignore) & is_assigned
            gt_inds = torch.zeros(num_preds, dtype=torch.int64)
            true_idxs = np.arange(num_gts)
            rng.shuffle(true_idxs)
            true_idxs = torch.from_numpy(true_idxs)
            gt_inds[is_assigned] = true_idxs[:n_assigned].long()
            gt_inds = torch.from_numpy(rng.randint(1, num_gts + 1, size=num_preds))
            gt_inds[is_ignore] = -1
            gt_inds[~is_assigned] = 0
            max_overlaps[~is_assigned] = 0
            if p_use_label is True or p_use_label < rng.rand():
                if num_classes == 0:
                    labels = torch.zeros(num_preds, dtype=torch.int64)
                else:
                    labels = torch.from_numpy(rng.randint(0, num_classes, size=num_preds))
                    labels[~is_assigned] = 0
            else:
                labels = None
        self = cls(num_gts, gt_inds, max_overlaps, labels)
        return self

    def add_gt_(self, gt_labels):
        """Add ground truth as assigned results.

        Args:
            gt_labels (torch.Tensor): Labels of gt boxes
        """
        self_inds = torch.arange(1, len(gt_labels) + 1, dtype=torch.long, device=gt_labels.device)
        self.gt_inds = torch.cat([self_inds, self.gt_inds])
        self.max_overlaps = torch.cat([self.max_overlaps.new_ones(len(gt_labels)), self.max_overlaps])
        if self.labels is not None:
            self.labels = torch.cat([gt_labels, self.labels])

@property
def info(self):
    """dict: a dictionary of info about the object"""
    basic_info = {'num_gts': self.num_gts, 'num_preds': self.num_preds, 'gt_inds': self.gt_inds, 'max_overlaps': self.max_overlaps, 'labels': self.labels}
    basic_info.update(self._extra_properties)
    return basic_info

def cast_tensor_type(x, scale=1.0, dtype=None):
    if dtype == 'fp16':
        x = (x / scale).half()
    return x

class ONNXRuntimeDetector(DeployBaseDetector):
    """Wrapper for detector's inference with ONNXRuntime."""

    def __init__(self, onnx_file, class_names, device_id):
        super(ONNXRuntimeDetector, self).__init__(class_names, device_id)
        import onnxruntime as ort
        ort_custom_op_path = ''
        try:
            from mmcv.ops import get_onnxruntime_op_path
            ort_custom_op_path = get_onnxruntime_op_path()
        except (ImportError, ModuleNotFoundError):
            warnings.warn('If input model has custom op from mmcv,                 you may have to build mmcv with ONNXRuntime from source.')
        session_options = ort.SessionOptions()
        if osp.exists(ort_custom_op_path):
            session_options.register_custom_ops_library(ort_custom_op_path)
        sess = ort.InferenceSession(onnx_file, session_options)
        providers = ['CPUExecutionProvider']
        options = [{}]
        is_cuda_available = ort.get_device() == 'GPU'
        if is_cuda_available:
            providers.insert(0, 'CUDAExecutionProvider')
            options.insert(0, {'device_id': device_id})
        sess.set_providers(providers, options)
        self.sess = sess
        self.io_binding = sess.io_binding()
        self.output_names = [_.name for _ in sess.get_outputs()]
        self.is_cuda_available = is_cuda_available

    def forward_test(self, imgs, img_metas, **kwargs):
        input_data = imgs[0]
        device_type = 'cuda' if self.is_cuda_available else 'cpu'
        if not self.is_cuda_available:
            input_data = input_data.cpu()
        self.io_binding.bind_input(name='input', device_type=device_type, device_id=self.device_id, element_type=np.float32, shape=input_data.shape, buffer_ptr=input_data.data_ptr())
        for name in self.output_names:
            self.io_binding.bind_output(name)
        self.sess.run_with_iobinding(self.io_binding)
        ort_outputs = self.io_binding.copy_outputs_to_cpu()
        return ort_outputs

def __init__(self, onnx_file, class_names, device_id):
    super(ONNXRuntimeDetector, self).__init__(class_names, device_id)
    import onnxruntime as ort
    ort_custom_op_path = ''
    try:
        from mmcv.ops import get_onnxruntime_op_path
        ort_custom_op_path = get_onnxruntime_op_path()
    except (ImportError, ModuleNotFoundError):
        warnings.warn('If input model has custom op from mmcv,                 you may have to build mmcv with ONNXRuntime from source.')
    session_options = ort.SessionOptions()
    if osp.exists(ort_custom_op_path):
        session_options.register_custom_ops_library(ort_custom_op_path)
    sess = ort.InferenceSession(onnx_file, session_options)
    providers = ['CPUExecutionProvider']
    options = [{}]
    is_cuda_available = ort.get_device() == 'GPU'
    if is_cuda_available:
        providers.insert(0, 'CUDAExecutionProvider')
        options.insert(0, {'device_id': device_id})
    sess.set_providers(providers, options)
    self.sess = sess
    self.io_binding = sess.io_binding()
    self.output_names = [_.name for _ in sess.get_outputs()]
    self.is_cuda_available = is_cuda_available

def forward_test(self, imgs, img_metas, **kwargs):
    input_data = imgs[0]
    device_type = 'cuda' if self.is_cuda_available else 'cpu'
    if not self.is_cuda_available:
        input_data = input_data.cpu()
    self.io_binding.bind_input(name='input', device_type=device_type, device_id=self.device_id, element_type=np.float32, shape=input_data.shape, buffer_ptr=input_data.data_ptr())
    for name in self.output_names:
        self.io_binding.bind_output(name)
    self.sess.run_with_iobinding(self.io_binding)
    ort_outputs = self.io_binding.copy_outputs_to_cpu()
    return ort_outputs

def generate_inputs_and_wrap_model(config_path, checkpoint_path, input_config, cfg_options=None):
    """Prepare sample input and wrap model for ONNX export.

    The ONNX export API only accept args, and all inputs should be
    torch.Tensor or corresponding types (such as tuple of tensor).
    So we should call this function before exporting. This function will:

    1. generate corresponding inputs which are used to execute the model.
    2. Wrap the model's forward function.

    For example, the MMDet models' forward function has a parameter
    ``return_loss:bool``. As we want to set it as False while export API
    supports neither bool type or kwargs. So we have to replace the forward
    method like ``model.forward = partial(model.forward, return_loss=False)``.

    Args:
        config_path (str): the OpenMMLab config for the model we want to
            export to ONNX
        checkpoint_path (str): Path to the corresponding checkpoint
        input_config (dict): the exactly data in this dict depends on the
            framework. For MMSeg, we can just declare the input shape,
            and generate the dummy data accordingly. However, for MMDet,
            we may pass the real img path, or the NMS will return None
            as there is no legal bbox.

    Returns:
        tuple: (model, tensor_data) wrapped model which can be called by
            ``model(*tensor_data)`` and a list of inputs which are used to
            execute the model while exporting.
    """
    model = build_model_from_cfg(config_path, checkpoint_path, cfg_options=cfg_options)
    one_img, one_meta = preprocess_example_input(input_config)
    tensor_data = [one_img]
    model.forward = partial(model.forward, img_metas=[[one_meta]], return_loss=False)
    opset_version = 11
    try:
        from mmcv.onnx.symbolic import register_extra_symbolics
    except ModuleNotFoundError:
        raise NotImplementedError('please update mmcv to version>=v1.0.4')
    register_extra_symbolics(opset_version)
    return (model, tensor_data)

class InstanceData(GeneralData):
    """Data structure for instance-level annnotations or predictions.

    Subclass of :class:`GeneralData`. All value in `data_fields`
    should have the same length. This design refer to
    https://github.com/facebookresearch/detectron2/blob/master/detectron2/structures/instances.py # noqa E501

    Examples:
        >>> from mmdet.core import InstanceData
        >>> import numpy as np
        >>> img_meta = dict(img_shape=(800, 1196, 3), pad_shape=(800, 1216, 3))
        >>> results = InstanceData(img_meta)
        >>> img_shape in results
        True
        >>> results.det_labels = torch.LongTensor([0, 1, 2, 3])
        >>> results["det_scores"] = torch.Tensor([0.01, 0.7, 0.6, 0.3])
        >>> results["det_masks"] = np.ndarray(4, 2, 2)
        >>> len(results)
        4
        >>> print(resutls)
        <InstanceData(

            META INFORMATION
        pad_shape: (800, 1216, 3)
        img_shape: (800, 1196, 3)

            PREDICTIONS
        shape of det_labels: torch.Size([4])
        shape of det_masks: (4, 2, 2)
        shape of det_scores: torch.Size([4])

        ) at 0x7fe26b5ca990>
        >>> sorted_results = results[results.det_scores.sort().indices]
        >>> sorted_results.det_scores
        tensor([0.0100, 0.3000, 0.6000, 0.7000])
        >>> sorted_results.det_labels
        tensor([0, 3, 2, 1])
        >>> print(results[results.scores > 0.5])
        <InstanceData(

            META INFORMATION
        pad_shape: (800, 1216, 3)
        img_shape: (800, 1196, 3)

            PREDICTIONS
        shape of det_labels: torch.Size([2])
        shape of det_masks: (2, 2, 2)
        shape of det_scores: torch.Size([2])

        ) at 0x7fe26b6d7790>
        >>> results[results.det_scores > 0.5].det_labels
        tensor([1, 2])
        >>> results[results.det_scores > 0.5].det_scores
        tensor([0.7000, 0.6000])
    """

    def __setattr__(self, name, value):
        if name in ('_meta_info_fields', '_data_fields'):
            if not hasattr(self, name):
                super().__setattr__(name, value)
            else:
                raise AttributeError(f'{name} has been used as a private attribute, which is immutable. ')
        else:
            assert isinstance(value, (torch.Tensor, np.ndarray, list)), f'Can set {type(value)}, only support {(torch.Tensor, np.ndarray, list)}'
            if self._data_fields:
                assert len(value) == len(self), f'the length of values {len(value)} is not consistent with the length of this :obj:`InstanceData` {len(self)} '
            super().__setattr__(name, value)

    def __getitem__(self, item):
        """
        Args:
            item (str, obj:`slice`,
                obj`torch.LongTensor`, obj:`torch.BoolTensor`):
                get the corresponding values according to item.

        Returns:
            obj:`InstanceData`: Corresponding values.
        """
        assert len(self), ' This is a empty instance'
        assert isinstance(item, (str, slice, int, torch.LongTensor, torch.BoolTensor))
        if isinstance(item, str):
            return getattr(self, item)
        if type(item) == int:
            if item >= len(self) or item < -len(self):
                raise IndexError(f'Index {item} out of range!')
            else:
                item = slice(item, None, len(self))
        new_data = self.new()
        if isinstance(item, torch.Tensor):
            assert item.dim() == 1, 'Only support to get the values along the first dimension.'
            if isinstance(item, torch.BoolTensor):
                assert len(item) == len(self), f'The shape of the input(BoolTensor)) {len(item)}  does not match the shape of the indexed tensor in results_filed {len(self)} at first dimension. '
            for k, v in self.items():
                if isinstance(v, torch.Tensor):
                    new_data[k] = v[item]
                elif isinstance(v, np.ndarray):
                    new_data[k] = v[item.cpu().numpy()]
                elif isinstance(v, list):
                    r_list = []
                    if isinstance(item, torch.BoolTensor):
                        indexes = torch.nonzero(item).view(-1)
                    else:
                        indexes = item
                    for index in indexes:
                        r_list.append(v[index])
                    new_data[k] = r_list
        else:
            for k, v in self.items():
                new_data[k] = v[item]
        return new_data

    @staticmethod
    def cat(instances_list):
        """Concat the predictions of all :obj:`InstanceData` in the list.

        Args:
            instances_list (list[:obj:`InstanceData`]): A list
                of :obj:`InstanceData`.

        Returns:
            obj:`InstanceData`
        """
        assert all((isinstance(results, InstanceData) for results in instances_list))
        assert len(instances_list) > 0
        if len(instances_list) == 1:
            return instances_list[0]
        new_data = instances_list[0].new()
        for k in instances_list[0]._data_fields:
            values = [results[k] for results in instances_list]
            v0 = values[0]
            if isinstance(v0, torch.Tensor):
                values = torch.cat(values, dim=0)
            elif isinstance(v0, np.ndarray):
                values = np.concatenate(values, axis=0)
            elif isinstance(v0, list):
                values = list(itertools.chain(*values))
            else:
                raise ValueError(f'Can not concat the {k} which is a {type(v0)}')
            new_data[k] = values
        return new_data

    def __len__(self):
        if len(self._data_fields):
            for v in self.values():
                return len(v)
        else:
            raise AssertionError('This is an empty `InstanceData`.')

def __len__(self):
    if len(self._data_fields):
        for v in self.values():
            return len(v)
    else:
        raise AssertionError('This is an empty `InstanceData`.')

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

def pvt_convert(ckpt):
    new_ckpt = OrderedDict()
    use_abs_pos_embed = False
    use_conv_ffn = False
    for k in ckpt.keys():
        if k.startswith('pos_embed'):
            use_abs_pos_embed = True
        if k.find('dwconv') >= 0:
            use_conv_ffn = True
    for k, v in ckpt.items():
        if k.startswith('head'):
            continue
        if k.startswith('norm.'):
            continue
        if k.startswith('cls_token'):
            continue
        if k.startswith('pos_embed'):
            stage_i = int(k.replace('pos_embed', ''))
            new_k = k.replace(f'pos_embed{stage_i}', f'layers.{stage_i - 1}.1.0.pos_embed')
            if stage_i == 4 and v.size(1) == 50:
                new_v = v[:, 1:, :]
            else:
                new_v = v
        elif k.startswith('patch_embed'):
            stage_i = int(k.split('.')[0].replace('patch_embed', ''))
            new_k = k.replace(f'patch_embed{stage_i}', f'layers.{stage_i - 1}.0')
            new_v = v
            if 'proj.' in new_k:
                new_k = new_k.replace('proj.', 'projection.')
        elif k.startswith('block'):
            stage_i = int(k.split('.')[0].replace('block', ''))
            layer_i = int(k.split('.')[1])
            new_layer_i = layer_i + use_abs_pos_embed
            new_k = k.replace(f'block{stage_i}.{layer_i}', f'layers.{stage_i - 1}.1.{new_layer_i}')
            new_v = v
            if 'attn.q.' in new_k:
                sub_item_k = k.replace('q.', 'kv.')
                new_k = new_k.replace('q.', 'attn.in_proj_')
                new_v = torch.cat([v, ckpt[sub_item_k]], dim=0)
            elif 'attn.kv.' in new_k:
                continue
            elif 'attn.proj.' in new_k:
                new_k = new_k.replace('proj.', 'attn.out_proj.')
            elif 'attn.sr.' in new_k:
                new_k = new_k.replace('sr.', 'sr.')
            elif 'mlp.' in new_k:
                string = f'{new_k}-'
                new_k = new_k.replace('mlp.', 'ffn.layers.')
                if 'fc1.weight' in new_k or 'fc2.weight' in new_k:
                    new_v = v.reshape((*v.shape, 1, 1))
                new_k = new_k.replace('fc1.', '0.')
                new_k = new_k.replace('dwconv.dwconv.', '1.')
                if use_conv_ffn:
                    new_k = new_k.replace('fc2.', '4.')
                else:
                    new_k = new_k.replace('fc2.', '3.')
                string += f'{new_k} {v.shape}-{new_v.shape}'
        elif k.startswith('norm'):
            stage_i = int(k[4])
            new_k = k.replace(f'norm{stage_i}', f'layers.{stage_i - 1}.2')
            new_v = v
        else:
            new_k = k
            new_v = v
        new_ckpt[new_k] = new_v
    return new_ckpt

def swin_converter(ckpt):
    new_ckpt = OrderedDict()

    def correct_unfold_reduction_order(x):
        out_channel, in_channel = x.shape
        x = x.reshape(out_channel, 4, in_channel // 4)
        x = x[:, [0, 2, 1, 3], :].transpose(1, 2).reshape(out_channel, in_channel)
        return x

    def correct_unfold_norm_order(x):
        in_channel = x.shape[0]
        x = x.reshape(4, in_channel // 4)
        x = x[[0, 2, 1, 3], :].transpose(0, 1).reshape(in_channel)
        return x
    for k, v in ckpt.items():
        if k.startswith('head'):
            continue
        elif k.startswith('layers'):
            new_v = v
            if 'attn.' in k:
                new_k = k.replace('attn.', 'attn.w_msa.')
            elif 'mlp.' in k:
                if 'mlp.fc1.' in k:
                    new_k = k.replace('mlp.fc1.', 'ffn.layers.0.0.')
                elif 'mlp.fc2.' in k:
                    new_k = k.replace('mlp.fc2.', 'ffn.layers.1.')
                else:
                    new_k = k.replace('mlp.', 'ffn.')
            elif 'downsample' in k:
                new_k = k
                if 'reduction.' in k:
                    new_v = correct_unfold_reduction_order(v)
                elif 'norm.' in k:
                    new_v = correct_unfold_norm_order(v)
            else:
                new_k = k
            new_k = new_k.replace('layers', 'stages', 1)
        elif k.startswith('patch_embed'):
            new_v = v
            if 'proj' in k:
                new_k = k.replace('proj', 'projection')
            else:
                new_k = k
        else:
            new_v = v
            new_k = k
        new_ckpt['backbone.' + new_k] = new_v
    return new_ckpt

class WindowMSA(BaseModule):
    """Window based multi-head self-attention (W-MSA) module with relative
    position bias.

    Args:
        embed_dims (int): Number of input channels.
        num_heads (int): Number of attention heads.
        window_size (tuple[int]): The height and width of the window.
        qkv_bias (bool, optional):  If True, add a learnable bias to q, k, v.
            Default: True.
        qk_scale (float | None, optional): Override default qk scale of
            head_dim ** -0.5 if set. Default: None.
        attn_drop_rate (float, optional): Dropout ratio of attention weight.
            Default: 0.0
        proj_drop_rate (float, optional): Dropout ratio of output. Default: 0.
        init_cfg (dict | None, optional): The Config for initialization.
            Default: None.
    """

    def __init__(self, embed_dims, num_heads, window_size, qkv_bias=True, qk_scale=None, attn_drop_rate=0.0, proj_drop_rate=0.0, init_cfg=None):
        super().__init__()
        self.embed_dims = embed_dims
        self.window_size = window_size
        self.num_heads = num_heads
        head_embed_dims = embed_dims // num_heads
        self.scale = qk_scale or head_embed_dims ** (-0.5)
        self.init_cfg = init_cfg
        self.relative_position_bias_table = nn.Parameter(torch.zeros((2 * window_size[0] - 1) * (2 * window_size[1] - 1), num_heads))
        Wh, Ww = self.window_size
        rel_index_coords = self.double_step_seq(2 * Ww - 1, Wh, 1, Ww)
        rel_position_index = rel_index_coords + rel_index_coords.T
        rel_position_index = rel_position_index.flip(1).contiguous()
        self.register_buffer('relative_position_index', rel_position_index)
        self.qkv = nn.Linear(embed_dims, embed_dims * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop_rate)
        self.proj = nn.Linear(embed_dims, embed_dims)
        self.proj_drop = nn.Dropout(proj_drop_rate)
        self.softmax = nn.Softmax(dim=-1)

    def init_weights(self):
        trunc_normal_(self.relative_position_bias_table, std=0.02)

    def forward(self, x, mask=None):
        """
        Args:

            x (tensor): input features with shape of (num_windows*B, N, C)
            mask (tensor | None, Optional): mask with shape of (num_windows,
                Wh*Ww, Wh*Ww), value should be between (-inf, 0].
        """
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = (qkv[0], qkv[1], qkv[2])
        q = q * self.scale
        attn = q @ k.transpose(-2, -1)
        relative_position_bias = self.relative_position_bias_table[self.relative_position_index.view(-1)].view(self.window_size[0] * self.window_size[1], self.window_size[0] * self.window_size[1], -1)
        relative_position_bias = relative_position_bias.permute(2, 0, 1).contiguous()
        attn = attn + relative_position_bias.unsqueeze(0)
        if mask is not None:
            nW = mask.shape[0]
            attn = attn.view(B // nW, nW, self.num_heads, N, N) + mask.unsqueeze(1).unsqueeze(0)
            attn = attn.view(-1, self.num_heads, N, N)
        attn = self.softmax(attn)
        attn = self.attn_drop(attn)
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x

    @staticmethod
    def double_step_seq(step1, len1, step2, len2):
        seq1 = torch.arange(0, step1 * len1, step1)
        seq2 = torch.arange(0, step2 * len2, step2)
        return (seq1[:, None] + seq2[None, :]).reshape(1, -1)

def init_weights(self):
    trunc_normal_(self.relative_position_bias_table, std=0.02)

@BACKBONES.register_module()
class SwinTransformer(BaseModule):
    """ Swin Transformer
    A PyTorch implement of : `Swin Transformer:
    Hierarchical Vision Transformer using Shifted Windows`  -
        https://arxiv.org/abs/2103.14030

    Inspiration from
    https://github.com/microsoft/Swin-Transformer

    Args:
        pretrain_img_size (int | tuple[int]): The size of input image when
            pretrain. Defaults: 224.
        in_channels (int): The num of input channels.
            Defaults: 3.
        embed_dims (int): The feature dimension. Default: 96.
        patch_size (int | tuple[int]): Patch size. Default: 4.
        window_size (int): Window size. Default: 7.
        mlp_ratio (int): Ratio of mlp hidden dim to embedding dim.
            Default: 4.
        depths (tuple[int]): Depths of each Swin Transformer stage.
            Default: (2, 2, 6, 2).
        num_heads (tuple[int]): Parallel attention heads of each Swin
            Transformer stage. Default: (3, 6, 12, 24).
        strides (tuple[int]): The patch merging or patch embedding stride of
            each Swin Transformer stage. (In swin, we set kernel size equal to
            stride.) Default: (4, 2, 2, 2).
        out_indices (tuple[int]): Output from which stages.
            Default: (0, 1, 2, 3).
        qkv_bias (bool, optional): If True, add a learnable bias to query, key,
            value. Default: True
        qk_scale (float | None, optional): Override default qk scale of
            head_dim ** -0.5 if set. Default: None.
        patch_norm (bool): If add a norm layer for patch embed and patch
            merging. Default: True.
        drop_rate (float): Dropout rate. Defaults: 0.
        attn_drop_rate (float): Attention dropout rate. Default: 0.
        drop_path_rate (float): Stochastic depth rate. Defaults: 0.1.
        use_abs_pos_embed (bool): If True, add absolute position embedding to
            the patch embedding. Defaults: False.
        act_cfg (dict): Config dict for activation layer.
            Default: dict(type='GELU').
        norm_cfg (dict): Config dict for normalization layer at
            output of backone. Defaults: dict(type='LN').
        with_cp (bool, optional): Use checkpoint or not. Using checkpoint
            will save some memory while slowing down the training speed.
            Default: False.
        pretrained (str, optional): model pretrained path. Default: None.
        convert_weights (bool): The flag indicates whether the
            pre-trained model is from the original repo. We may need
            to convert some keys to make it compatible.
            Default: False.
        frozen_stages (int): Stages to be frozen (stop grad and set eval mode).
            Default: -1 (-1 means not freezing any parameters).
        init_cfg (dict, optional): The Config for initialization.
            Defaults to None.
    """

    def __init__(self, pretrain_img_size=224, in_channels=3, embed_dims=96, patch_size=4, window_size=7, mlp_ratio=4, depths=(2, 2, 6, 2), num_heads=(3, 6, 12, 24), strides=(4, 2, 2, 2), out_indices=(0, 1, 2, 3), qkv_bias=True, qk_scale=None, patch_norm=True, drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.1, use_abs_pos_embed=False, act_cfg=dict(type='GELU'), norm_cfg=dict(type='LN'), with_cp=False, pretrained=None, convert_weights=False, frozen_stages=-1, init_cfg=None):
        self.convert_weights = convert_weights
        self.frozen_stages = frozen_stages
        if isinstance(pretrain_img_size, int):
            pretrain_img_size = to_2tuple(pretrain_img_size)
        elif isinstance(pretrain_img_size, tuple):
            if len(pretrain_img_size) == 1:
                pretrain_img_size = to_2tuple(pretrain_img_size[0])
            assert len(pretrain_img_size) == 2, f'The size of image should have length 1 or 2, but got {len(pretrain_img_size)}'
        assert not (init_cfg and pretrained), 'init_cfg and pretrained cannot be specified at the same time'
        if isinstance(pretrained, str):
            warnings.warn('DeprecationWarning: pretrained is deprecated, please use "init_cfg" instead')
            self.init_cfg = dict(type='Pretrained', checkpoint=pretrained)
        elif pretrained is None:
            self.init_cfg = init_cfg
        else:
            raise TypeError('pretrained must be a str or None')
        super(SwinTransformer, self).__init__(init_cfg=init_cfg)
        num_layers = len(depths)
        self.out_indices = out_indices
        self.use_abs_pos_embed = use_abs_pos_embed
        assert strides[0] == patch_size, 'Use non-overlapping patch embed.'
        self.patch_embed = PatchEmbed(in_channels=in_channels, embed_dims=embed_dims, conv_type='Conv2d', kernel_size=patch_size, stride=strides[0], norm_cfg=norm_cfg if patch_norm else None, init_cfg=None)
        if self.use_abs_pos_embed:
            patch_row = pretrain_img_size[0] // patch_size
            patch_col = pretrain_img_size[1] // patch_size
            self.absolute_pos_embed = nn.Parameter(torch.zeros((1, embed_dims, patch_row, patch_col)))
        self.drop_after_pos = nn.Dropout(p=drop_rate)
        total_depth = sum(depths)
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, total_depth)]
        self.stages = ModuleList()
        in_channels = embed_dims
        for i in range(num_layers):
            if i < num_layers - 1:
                downsample = PatchMerging(in_channels=in_channels, out_channels=2 * in_channels, stride=strides[i + 1], norm_cfg=norm_cfg if patch_norm else None, init_cfg=None)
            else:
                downsample = None
            stage = SwinBlockSequence(embed_dims=in_channels, num_heads=num_heads[i], feedforward_channels=mlp_ratio * in_channels, depth=depths[i], window_size=window_size, qkv_bias=qkv_bias, qk_scale=qk_scale, drop_rate=drop_rate, attn_drop_rate=attn_drop_rate, drop_path_rate=dpr[sum(depths[:i]):sum(depths[:i + 1])], downsample=downsample, act_cfg=act_cfg, norm_cfg=norm_cfg, with_cp=with_cp, init_cfg=None)
            self.stages.append(stage)
            if downsample:
                in_channels = downsample.out_channels
        self.num_features = [int(embed_dims * 2 ** i) for i in range(num_layers)]
        for i in out_indices:
            layer = build_norm_layer(norm_cfg, self.num_features[i])[1]
            layer_name = f'norm{i}'
            self.add_module(layer_name, layer)

    def train(self, mode=True):
        """Convert the model into training mode while keep layers freezed."""
        super(SwinTransformer, self).train(mode)
        self._freeze_stages()

    def _freeze_stages(self):
        if self.frozen_stages >= 0:
            self.patch_embed.eval()
            for param in self.patch_embed.parameters():
                param.requires_grad = False
            if self.use_abs_pos_embed:
                self.absolute_pos_embed.requires_grad = False
            self.drop_after_pos.eval()
        for i in range(1, self.frozen_stages + 1):
            if i - 1 in self.out_indices:
                norm_layer = getattr(self, f'norm{i - 1}')
                norm_layer.eval()
                for param in norm_layer.parameters():
                    param.requires_grad = False
            m = self.stages[i - 1]
            m.eval()
            for param in m.parameters():
                param.requires_grad = False

    def init_weights(self):
        logger = get_root_logger()
        if self.init_cfg is None:
            logger.warn(f'No pre-trained weights for {self.__class__.__name__}, training start from scratch')
            if self.use_abs_pos_embed:
                trunc_normal_(self.absolute_pos_embed, std=0.02)
            for m in self.modules():
                if isinstance(m, nn.Linear):
                    trunc_normal_init(m, std=0.02, bias=0.0)
                elif isinstance(m, nn.LayerNorm):
                    constant_init(m, 1.0)
        else:
            assert 'checkpoint' in self.init_cfg, f'Only support specify `Pretrained` in `init_cfg` in {self.__class__.__name__} '
            ckpt = _load_checkpoint(self.init_cfg.checkpoint, logger=logger, map_location='cpu')
            if 'state_dict' in ckpt:
                _state_dict = ckpt['state_dict']
            elif 'model' in ckpt:
                _state_dict = ckpt['model']
            else:
                _state_dict = ckpt
            if self.convert_weights:
                _state_dict = swin_converter(_state_dict)
            state_dict = OrderedDict()
            for k, v in _state_dict.items():
                if k.startswith('backbone.'):
                    state_dict[k[9:]] = v
            if list(state_dict.keys())[0].startswith('module.'):
                state_dict = {k[7:]: v for k, v in state_dict.items()}
            if state_dict.get('absolute_pos_embed') is not None:
                absolute_pos_embed = state_dict['absolute_pos_embed']
                N1, L, C1 = absolute_pos_embed.size()
                N2, C2, H, W = self.absolute_pos_embed.size()
                if N1 != N2 or C1 != C2 or L != H * W:
                    logger.warning('Error in loading absolute_pos_embed, pass')
                else:
                    state_dict['absolute_pos_embed'] = absolute_pos_embed.view(N2, H, W, C2).permute(0, 3, 1, 2).contiguous()
            relative_position_bias_table_keys = [k for k in state_dict.keys() if 'relative_position_bias_table' in k]
            for table_key in relative_position_bias_table_keys:
                table_pretrained = state_dict[table_key]
                table_current = self.state_dict()[table_key]
                L1, nH1 = table_pretrained.size()
                L2, nH2 = table_current.size()
                if nH1 != nH2:
                    logger.warning(f'Error in loading {table_key}, pass')
                elif L1 != L2:
                    S1 = int(L1 ** 0.5)
                    S2 = int(L2 ** 0.5)
                    table_pretrained_resized = F.interpolate(table_pretrained.permute(1, 0).reshape(1, nH1, S1, S1), size=(S2, S2), mode='bicubic')
                    state_dict[table_key] = table_pretrained_resized.view(nH2, L2).permute(1, 0).contiguous()
            self.load_state_dict(state_dict, False)

    def forward(self, x):
        x, hw_shape = self.patch_embed(x)
        if self.use_abs_pos_embed:
            h, w = self.absolute_pos_embed.shape[1:3]
            if hw_shape[0] != h or hw_shape[1] != w:
                absolute_pos_embed = F.interpolate(self.absolute_pos_embed, size=hw_shape, mode='bicubic', align_corners=False).flatten(2).transpose(1, 2)
            else:
                absolute_pos_embed = self.absolute_pos_embed.flatten(2).transpose(1, 2)
            x = x + absolute_pos_embed
        x = self.drop_after_pos(x)
        outs = []
        for i, stage in enumerate(self.stages):
            x, hw_shape, out, out_hw_shape = stage(x, hw_shape)
            if i in self.out_indices:
                norm_layer = getattr(self, f'norm{i}')
                out = norm_layer(out)
                out = out.view(-1, *out_hw_shape, self.num_features[i]).permute(0, 3, 1, 2).contiguous()
                outs.append(out)
        return outs

def init_weights(self):
    logger = get_root_logger()
    if self.init_cfg is None:
        logger.warn(f'No pre-trained weights for {self.__class__.__name__}, training start from scratch')
        if self.use_abs_pos_embed:
            trunc_normal_(self.absolute_pos_embed, std=0.02)
        for m in self.modules():
            if isinstance(m, nn.Linear):
                trunc_normal_init(m, std=0.02, bias=0.0)
            elif isinstance(m, nn.LayerNorm):
                constant_init(m, 1.0)
    else:
        assert 'checkpoint' in self.init_cfg, f'Only support specify `Pretrained` in `init_cfg` in {self.__class__.__name__} '
        ckpt = _load_checkpoint(self.init_cfg.checkpoint, logger=logger, map_location='cpu')
        if 'state_dict' in ckpt:
            _state_dict = ckpt['state_dict']
        elif 'model' in ckpt:
            _state_dict = ckpt['model']
        else:
            _state_dict = ckpt
        if self.convert_weights:
            _state_dict = swin_converter(_state_dict)
        state_dict = OrderedDict()
        for k, v in _state_dict.items():
            if k.startswith('backbone.'):
                state_dict[k[9:]] = v
        if list(state_dict.keys())[0].startswith('module.'):
            state_dict = {k[7:]: v for k, v in state_dict.items()}
        if state_dict.get('absolute_pos_embed') is not None:
            absolute_pos_embed = state_dict['absolute_pos_embed']
            N1, L, C1 = absolute_pos_embed.size()
            N2, C2, H, W = self.absolute_pos_embed.size()
            if N1 != N2 or C1 != C2 or L != H * W:
                logger.warning('Error in loading absolute_pos_embed, pass')
            else:
                state_dict['absolute_pos_embed'] = absolute_pos_embed.view(N2, H, W, C2).permute(0, 3, 1, 2).contiguous()
        relative_position_bias_table_keys = [k for k in state_dict.keys() if 'relative_position_bias_table' in k]
        for table_key in relative_position_bias_table_keys:
            table_pretrained = state_dict[table_key]
            table_current = self.state_dict()[table_key]
            L1, nH1 = table_pretrained.size()
            L2, nH2 = table_current.size()
            if nH1 != nH2:
                logger.warning(f'Error in loading {table_key}, pass')
            elif L1 != L2:
                S1 = int(L1 ** 0.5)
                S2 = int(L2 ** 0.5)
                table_pretrained_resized = F.interpolate(table_pretrained.permute(1, 0).reshape(1, nH1, S1, S1), size=(S2, S2), mode='bicubic')
                state_dict[table_key] = table_pretrained_resized.view(nH2, L2).permute(1, 0).contiguous()
        self.load_state_dict(state_dict, False)

class AbsolutePositionEmbedding(BaseModule):
    """An implementation of the absolute position embedding in PVT.

    Args:
        pos_shape (int): The shape of the absolute position embedding.
        pos_dim (int): The dimension of the absolute position embedding.
        drop_rate (float): Probability of an element to be zeroed.
            Default: 0.0.
    """

    def __init__(self, pos_shape, pos_dim, drop_rate=0.0, init_cfg=None):
        super().__init__(init_cfg=init_cfg)
        if isinstance(pos_shape, int):
            pos_shape = to_2tuple(pos_shape)
        elif isinstance(pos_shape, tuple):
            if len(pos_shape) == 1:
                pos_shape = to_2tuple(pos_shape[0])
            assert len(pos_shape) == 2, f'The size of image should have length 1 or 2, but got {len(pos_shape)}'
        self.pos_shape = pos_shape
        self.pos_dim = pos_dim
        self.pos_embed = nn.Parameter(torch.zeros(1, pos_shape[0] * pos_shape[1], pos_dim))
        self.drop = nn.Dropout(p=drop_rate)

    def init_weights(self):
        trunc_normal_(self.pos_embed, std=0.02)

    def resize_pos_embed(self, pos_embed, input_shape, mode='bilinear'):
        """Resize pos_embed weights.

        Resize pos_embed using bilinear interpolate method.

        Args:
            pos_embed (torch.Tensor): Position embedding weights.
            input_shape (tuple): Tuple for (downsampled input image height,
                downsampled input image width).
            mode (str): Algorithm used for upsampling:
                ``'nearest'`` | ``'linear'`` | ``'bilinear'`` | ``'bicubic'`` |
                ``'trilinear'``. Default: ``'bilinear'``.

        Return:
            torch.Tensor: The resized pos_embed of shape [B, L_new, C].
        """
        assert pos_embed.ndim == 3, 'shape of pos_embed must be [B, L, C]'
        pos_h, pos_w = self.pos_shape
        pos_embed_weight = pos_embed[:, -1 * pos_h * pos_w:]
        pos_embed_weight = pos_embed_weight.reshape(1, pos_h, pos_w, self.pos_dim).permute(0, 3, 1, 2).contiguous()
        pos_embed_weight = F.interpolate(pos_embed_weight, size=input_shape, mode=mode)
        pos_embed_weight = torch.flatten(pos_embed_weight, 2).transpose(1, 2).contiguous()
        pos_embed = pos_embed_weight
        return pos_embed

    def forward(self, x, hw_shape, mode='bilinear'):
        pos_embed = self.resize_pos_embed(self.pos_embed, hw_shape, mode)
        return self.drop(x + pos_embed)

def init_weights(self):
    trunc_normal_(self.pos_embed, std=0.02)

@HEADS.register_module()
class AnchorFreeHead(BaseDenseHead, BBoxTestMixin):
    """Anchor-free head (FCOS, Fovea, RepPoints, etc.).

    Args:
        num_classes (int): Number of categories excluding the background
            category.
        in_channels (int): Number of channels in the input feature map.
        feat_channels (int): Number of hidden channels. Used in child classes.
        stacked_convs (int): Number of stacking convs of the head.
        strides (tuple): Downsample factor of each feature map.
        dcn_on_last_conv (bool): If true, use dcn in the last layer of
            towers. Default: False.
        conv_bias (bool | str): If specified as `auto`, it will be decided by
            the norm_cfg. Bias of conv will be set as True if `norm_cfg` is
            None, otherwise False. Default: "auto".
        loss_cls (dict): Config of classification loss.
        loss_bbox (dict): Config of localization loss.
        bbox_coder (dict): Config of bbox coder. Defaults
            'DistancePointBBoxCoder'.
        conv_cfg (dict): Config dict for convolution layer. Default: None.
        norm_cfg (dict): Config dict for normalization layer. Default: None.
        train_cfg (dict): Training config of anchor head.
        test_cfg (dict): Testing config of anchor head.
        init_cfg (dict or list[dict], optional): Initialization config dict.
    """
    _version = 1

    def __init__(self, num_classes, in_channels, feat_channels=256, stacked_convs=4, strides=(4, 8, 16, 32, 64), dcn_on_last_conv=False, conv_bias='auto', loss_cls=dict(type='FocalLoss', use_sigmoid=True, gamma=2.0, alpha=0.25, loss_weight=1.0), loss_bbox=dict(type='IoULoss', loss_weight=1.0), bbox_coder=dict(type='DistancePointBBoxCoder'), conv_cfg=None, norm_cfg=None, train_cfg=None, test_cfg=None, init_cfg=dict(type='Normal', layer='Conv2d', std=0.01, override=dict(type='Normal', name='conv_cls', std=0.01, bias_prob=0.01))):
        super(AnchorFreeHead, self).__init__(init_cfg)
        self.num_classes = num_classes
        self.use_sigmoid_cls = loss_cls.get('use_sigmoid', False)
        if self.use_sigmoid_cls:
            self.cls_out_channels = num_classes
        else:
            self.cls_out_channels = num_classes + 1
        self.in_channels = in_channels
        self.feat_channels = feat_channels
        self.stacked_convs = stacked_convs
        self.strides = strides
        self.dcn_on_last_conv = dcn_on_last_conv
        assert conv_bias == 'auto' or isinstance(conv_bias, bool)
        self.conv_bias = conv_bias
        self.loss_cls = build_loss(loss_cls)
        self.loss_bbox = build_loss(loss_bbox)
        self.bbox_coder = build_bbox_coder(bbox_coder)
        self.prior_generator = MlvlPointGenerator(strides)
        self.num_base_priors = self.prior_generator.num_base_priors[0]
        self.train_cfg = train_cfg
        self.test_cfg = test_cfg
        self.conv_cfg = conv_cfg
        self.norm_cfg = norm_cfg
        self.fp16_enabled = False
        self._init_layers()

    def _init_layers(self):
        """Initialize layers of the head."""
        self._init_cls_convs()
        self._init_reg_convs()
        self._init_predictor()

    def _init_cls_convs(self):
        """Initialize classification conv layers of the head."""
        self.cls_convs = nn.ModuleList()
        for i in range(self.stacked_convs):
            chn = self.in_channels if i == 0 else self.feat_channels
            if self.dcn_on_last_conv and i == self.stacked_convs - 1:
                conv_cfg = dict(type='DCNv2')
            else:
                conv_cfg = self.conv_cfg
            self.cls_convs.append(ConvModule(chn, self.feat_channels, 3, stride=1, padding=1, conv_cfg=conv_cfg, norm_cfg=self.norm_cfg, bias=self.conv_bias))

    def _init_reg_convs(self):
        """Initialize bbox regression conv layers of the head."""
        self.reg_convs = nn.ModuleList()
        for i in range(self.stacked_convs):
            chn = self.in_channels if i == 0 else self.feat_channels
            if self.dcn_on_last_conv and i == self.stacked_convs - 1:
                conv_cfg = dict(type='DCNv2')
            else:
                conv_cfg = self.conv_cfg
            self.reg_convs.append(ConvModule(chn, self.feat_channels, 3, stride=1, padding=1, conv_cfg=conv_cfg, norm_cfg=self.norm_cfg, bias=self.conv_bias))

    def _init_predictor(self):
        """Initialize predictor layers of the head."""
        self.conv_cls = nn.Conv2d(self.feat_channels, self.cls_out_channels, 3, padding=1)
        self.conv_reg = nn.Conv2d(self.feat_channels, 4, 3, padding=1)

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        """Hack some keys of the model state dict so that can load checkpoints
        of previous version."""
        version = local_metadata.get('version', None)
        if version is None:
            bbox_head_keys = [k for k in state_dict.keys() if k.startswith(prefix)]
            ori_predictor_keys = []
            new_predictor_keys = []
            for key in bbox_head_keys:
                ori_predictor_keys.append(key)
                key = key.split('.')
                conv_name = None
                if key[1].endswith('cls'):
                    conv_name = 'conv_cls'
                elif key[1].endswith('reg'):
                    conv_name = 'conv_reg'
                elif key[1].endswith('centerness'):
                    conv_name = 'conv_centerness'
                else:
                    assert NotImplementedError
                if conv_name is not None:
                    key[1] = conv_name
                    new_predictor_keys.append('.'.join(key))
                else:
                    ori_predictor_keys.pop(-1)
            for i in range(len(new_predictor_keys)):
                state_dict[new_predictor_keys[i]] = state_dict.pop(ori_predictor_keys[i])
        super()._load_from_state_dict(state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs)

    def forward(self, feats):
        """Forward features from the upstream network.

        Args:
            feats (tuple[Tensor]): Features from the upstream network, each is
                a 4D-tensor.

        Returns:
            tuple: Usually contain classification scores and bbox predictions.
                cls_scores (list[Tensor]): Box scores for each scale level,
                    each is a 4D-tensor, the channel number is
                    num_points * num_classes.
                bbox_preds (list[Tensor]): Box energies / deltas for each scale
                    level, each is a 4D-tensor, the channel number is
                    num_points * 4.
        """
        return multi_apply(self.forward_single, feats)[:2]

    def forward_single(self, x):
        """Forward features of a single scale level.

        Args:
            x (Tensor): FPN feature maps of the specified stride.

        Returns:
            tuple: Scores for each class, bbox predictions, features
                after classification and regression conv layers, some
                models needs these features like FCOS.
        """
        cls_feat = x
        reg_feat = x
        for cls_layer in self.cls_convs:
            cls_feat = cls_layer(cls_feat)
        cls_score = self.conv_cls(cls_feat)
        for reg_layer in self.reg_convs:
            reg_feat = reg_layer(reg_feat)
        bbox_pred = self.conv_reg(reg_feat)
        return (cls_score, bbox_pred, cls_feat, reg_feat)

    @abstractmethod
    @force_fp32(apply_to=('cls_scores', 'bbox_preds'))
    def loss(self, cls_scores, bbox_preds, gt_bboxes, gt_labels, img_metas, gt_bboxes_ignore=None):
        """Compute loss of the head.

        Args:
            cls_scores (list[Tensor]): Box scores for each scale level,
                each is a 4D-tensor, the channel number is
                num_points * num_classes.
            bbox_preds (list[Tensor]): Box energies / deltas for each scale
                level, each is a 4D-tensor, the channel number is
                num_points * 4.
            gt_bboxes (list[Tensor]): Ground truth bboxes for each image with
                shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            gt_labels (list[Tensor]): class indices corresponding to each box
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            gt_bboxes_ignore (None | list[Tensor]): specify which bounding
                boxes can be ignored when computing the loss.
        """
        raise NotImplementedError

    @abstractmethod
    def get_targets(self, points, gt_bboxes_list, gt_labels_list):
        """Compute regression, classification and centerness targets for points
        in multiple images.

        Args:
            points (list[Tensor]): Points of each fpn level, each has shape
                (num_points, 2).
            gt_bboxes_list (list[Tensor]): Ground truth bboxes of each image,
                each has shape (num_gt, 4).
            gt_labels_list (list[Tensor]): Ground truth labels of each box,
                each has shape (num_gt,).
        """
        raise NotImplementedError

    def _get_points_single(self, featmap_size, stride, dtype, device, flatten=False):
        """Get points of a single scale level.

        This function will be deprecated soon.
        """
        warnings.warn('`_get_points_single` in `AnchorFreeHead` will be deprecated soon, we support a multi level point generator nowyou can get points of a single level feature map with `self.prior_generator.single_level_grid_priors` ')
        h, w = featmap_size
        x_range = torch.arange(w, device=device).to(dtype)
        y_range = torch.arange(h, device=device).to(dtype)
        y, x = torch.meshgrid(y_range, x_range)
        if flatten:
            y = y.flatten()
            x = x.flatten()
        return (y, x)

    def get_points(self, featmap_sizes, dtype, device, flatten=False):
        """Get points according to feature map sizes.

        Args:
            featmap_sizes (list[tuple]): Multi-level feature map sizes.
            dtype (torch.dtype): Type of points.
            device (torch.device): Device of points.

        Returns:
            tuple: points of each image.
        """
        warnings.warn('`get_points` in `AnchorFreeHead` will be deprecated soon, we support a multi level point generator nowyou can get points of all levels with `self.prior_generator.grid_priors` ')
        mlvl_points = []
        for i in range(len(featmap_sizes)):
            mlvl_points.append(self._get_points_single(featmap_sizes[i], self.strides[i], dtype, device, flatten))
        return mlvl_points

    def aug_test(self, feats, img_metas, rescale=False):
        """Test function with test time augmentation.

        Args:
            feats (list[Tensor]): the outer list indicates test-time
                augmentations and inner Tensor should have a shape NxCxHxW,
                which contains features for all images in the batch.
            img_metas (list[list[dict]]): the outer list indicates test-time
                augs (multiscale, flip, etc.) and the inner list indicates
                images in a batch. each dict has image information.
            rescale (bool, optional): Whether to rescale the results.
                Defaults to False.

        Returns:
            list[ndarray]: bbox results of each class
        """
        return self.aug_test_bboxes(feats, img_metas, rescale=rescale)

def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
    """Hack some keys of the model state dict so that can load checkpoints
        of previous version."""
    version = local_metadata.get('version', None)
    if version is None:
        bbox_head_keys = [k for k in state_dict.keys() if k.startswith(prefix)]
        ori_predictor_keys = []
        new_predictor_keys = []
        for key in bbox_head_keys:
            ori_predictor_keys.append(key)
            key = key.split('.')
            conv_name = None
            if key[1].endswith('cls'):
                conv_name = 'conv_cls'
            elif key[1].endswith('reg'):
                conv_name = 'conv_reg'
            elif key[1].endswith('centerness'):
                conv_name = 'conv_centerness'
            else:
                assert NotImplementedError
            if conv_name is not None:
                key[1] = conv_name
                new_predictor_keys.append('.'.join(key))
            else:
                ori_predictor_keys.pop(-1)
        for i in range(len(new_predictor_keys)):
            state_dict[new_predictor_keys[i]] = state_dict.pop(ori_predictor_keys[i])
    super()._load_from_state_dict(state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs)

@HEADS.register_module()
class DETRHead(AnchorFreeHead):
    """Implements the DETR transformer head.

    See `paper: End-to-End Object Detection with Transformers
    <https://arxiv.org/pdf/2005.12872>`_ for details.

    Args:
        num_classes (int): Number of categories excluding the background.
        in_channels (int): Number of channels in the input feature map.
        num_query (int): Number of query in Transformer.
        num_reg_fcs (int, optional): Number of fully-connected layers used in
            `FFN`, which is then used for the regression head. Default 2.
        transformer (obj:`mmcv.ConfigDict`|dict): Config for transformer.
            Default: None.
        sync_cls_avg_factor (bool): Whether to sync the avg_factor of
            all ranks. Default to False.
        positional_encoding (obj:`mmcv.ConfigDict`|dict):
            Config for position encoding.
        loss_cls (obj:`mmcv.ConfigDict`|dict): Config of the
            classification loss. Default `CrossEntropyLoss`.
        loss_bbox (obj:`mmcv.ConfigDict`|dict): Config of the
            regression loss. Default `L1Loss`.
        loss_iou (obj:`mmcv.ConfigDict`|dict): Config of the
            regression iou loss. Default `GIoULoss`.
        tran_cfg (obj:`mmcv.ConfigDict`|dict): Training config of
            transformer head.
        test_cfg (obj:`mmcv.ConfigDict`|dict): Testing config of
            transformer head.
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None
    """
    _version = 2

    def __init__(self, num_classes, in_channels, num_query=100, num_reg_fcs=2, transformer=None, sync_cls_avg_factor=False, positional_encoding=dict(type='SinePositionalEncoding', num_feats=128, normalize=True), loss_cls=dict(type='CrossEntropyLoss', bg_cls_weight=0.1, use_sigmoid=False, loss_weight=1.0, class_weight=1.0), loss_bbox=dict(type='L1Loss', loss_weight=5.0), loss_iou=dict(type='GIoULoss', loss_weight=2.0), train_cfg=dict(assigner=dict(type='HungarianAssigner', cls_cost=dict(type='ClassificationCost', weight=1.0), reg_cost=dict(type='BBoxL1Cost', weight=5.0), iou_cost=dict(type='IoUCost', iou_mode='giou', weight=2.0))), test_cfg=dict(max_per_img=100), init_cfg=None, **kwargs):
        super(AnchorFreeHead, self).__init__(init_cfg)
        self.bg_cls_weight = 0
        self.sync_cls_avg_factor = sync_cls_avg_factor
        class_weight = loss_cls.get('class_weight', None)
        if class_weight is not None and self.__class__ is DETRHead:
            assert isinstance(class_weight, float), f'Expected class_weight to have type float. Found {type(class_weight)}.'
            bg_cls_weight = loss_cls.get('bg_cls_weight', class_weight)
            assert isinstance(bg_cls_weight, float), f'Expected bg_cls_weight to have type float. Found {type(bg_cls_weight)}.'
            class_weight = torch.ones(num_classes + 1) * class_weight
            class_weight[num_classes] = bg_cls_weight
            loss_cls.update({'class_weight': class_weight})
            if 'bg_cls_weight' in loss_cls:
                loss_cls.pop('bg_cls_weight')
            self.bg_cls_weight = bg_cls_weight
        if train_cfg:
            assert 'assigner' in train_cfg, 'assigner should be provided when train_cfg is set.'
            assigner = train_cfg['assigner']
            assert loss_cls['loss_weight'] == assigner['cls_cost']['weight'], 'The classification weight for loss and matcher should beexactly the same.'
            assert loss_bbox['loss_weight'] == assigner['reg_cost']['weight'], 'The regression L1 weight for loss and matcher should be exactly the same.'
            assert loss_iou['loss_weight'] == assigner['iou_cost']['weight'], 'The regression iou weight for loss and matcher should beexactly the same.'
            self.assigner = build_assigner(assigner)
            sampler_cfg = dict(type='PseudoSampler')
            self.sampler = build_sampler(sampler_cfg, context=self)
        self.num_query = num_query
        self.num_classes = num_classes
        self.in_channels = in_channels
        self.num_reg_fcs = num_reg_fcs
        self.train_cfg = train_cfg
        self.test_cfg = test_cfg
        self.fp16_enabled = False
        self.loss_cls = build_loss(loss_cls)
        self.loss_bbox = build_loss(loss_bbox)
        self.loss_iou = build_loss(loss_iou)
        if self.loss_cls.use_sigmoid:
            self.cls_out_channels = num_classes
        else:
            self.cls_out_channels = num_classes + 1
        self.act_cfg = transformer.get('act_cfg', dict(type='ReLU', inplace=True))
        self.activate = build_activation_layer(self.act_cfg)
        self.positional_encoding = build_positional_encoding(positional_encoding)
        self.transformer = build_transformer(transformer)
        self.embed_dims = self.transformer.embed_dims
        assert 'num_feats' in positional_encoding
        num_feats = positional_encoding['num_feats']
        assert num_feats * 2 == self.embed_dims, f'embed_dims should be exactly 2 times of num_feats. Found {self.embed_dims} and {num_feats}.'
        self._init_layers()

    def _init_layers(self):
        """Initialize layers of the transformer head."""
        self.input_proj = Conv2d(self.in_channels, self.embed_dims, kernel_size=1)
        self.fc_cls = Linear(self.embed_dims, self.cls_out_channels)
        self.reg_ffn = FFN(self.embed_dims, self.embed_dims, self.num_reg_fcs, self.act_cfg, dropout=0.0, add_residual=False)
        self.fc_reg = Linear(self.embed_dims, 4)
        self.query_embedding = nn.Embedding(self.num_query, self.embed_dims)

    def init_weights(self):
        """Initialize weights of the transformer head."""
        self.transformer.init_weights()

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
        """load checkpoints."""
        version = local_metadata.get('version', None)
        if (version is None or version < 2) and self.__class__ is DETRHead:
            convert_dict = {'.self_attn.': '.attentions.0.', '.ffn.': '.ffns.0.', '.multihead_attn.': '.attentions.1.', '.decoder.norm.': '.decoder.post_norm.'}
            state_dict_keys = list(state_dict.keys())
            for k in state_dict_keys:
                for ori_key, convert_key in convert_dict.items():
                    if ori_key in k:
                        convert_key = k.replace(ori_key, convert_key)
                        state_dict[convert_key] = state_dict[k]
                        del state_dict[k]
        super(AnchorFreeHead, self)._load_from_state_dict(state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs)

    def forward(self, feats, img_metas):
        """Forward function.

        Args:
            feats (tuple[Tensor]): Features from the upstream network, each is
                a 4D-tensor.
            img_metas (list[dict]): List of image information.

        Returns:
            tuple[list[Tensor], list[Tensor]]: Outputs for all scale levels.

                - all_cls_scores_list (list[Tensor]): Classification scores                     for each scale level. Each is a 4D-tensor with shape                     [nb_dec, bs, num_query, cls_out_channels]. Note                     `cls_out_channels` should includes background.
                - all_bbox_preds_list (list[Tensor]): Sigmoid regression                     outputs for each scale level. Each is a 4D-tensor with                     normalized coordinate format (cx, cy, w, h) and shape                     [nb_dec, bs, num_query, 4].
        """
        num_levels = len(feats)
        img_metas_list = [img_metas for _ in range(num_levels)]
        return multi_apply(self.forward_single, feats, img_metas_list)

    def forward_single(self, x, img_metas):
        """"Forward function for a single feature level.

        Args:
            x (Tensor): Input feature from backbone's single stage, shape
                [bs, c, h, w].
            img_metas (list[dict]): List of image information.

        Returns:
            all_cls_scores (Tensor): Outputs from the classification head,
                shape [nb_dec, bs, num_query, cls_out_channels]. Note
                cls_out_channels should includes background.
            all_bbox_preds (Tensor): Sigmoid outputs from the regression
                head with normalized coordinate format (cx, cy, w, h).
                Shape [nb_dec, bs, num_query, 4].
        """
        batch_size = x.size(0)
        input_img_h, input_img_w = img_metas[0]['batch_input_shape']
        masks = x.new_ones((batch_size, input_img_h, input_img_w))
        for img_id in range(batch_size):
            img_h, img_w, _ = img_metas[img_id]['img_shape']
            masks[img_id, :img_h, :img_w] = 0
        x = self.input_proj(x)
        masks = F.interpolate(masks.unsqueeze(1), size=x.shape[-2:]).to(torch.bool).squeeze(1)
        pos_embed = self.positional_encoding(masks)
        outs_dec, _ = self.transformer(x, masks, self.query_embedding.weight, pos_embed)
        all_cls_scores = self.fc_cls(outs_dec)
        all_bbox_preds = self.fc_reg(self.activate(self.reg_ffn(outs_dec))).sigmoid()
        return (all_cls_scores, all_bbox_preds)

    @force_fp32(apply_to=('all_cls_scores_list', 'all_bbox_preds_list'))
    def loss(self, all_cls_scores_list, all_bbox_preds_list, gt_bboxes_list, gt_labels_list, img_metas, gt_bboxes_ignore=None):
        """"Loss function.

        Only outputs from the last feature level are used for computing
        losses by default.

        Args:
            all_cls_scores_list (list[Tensor]): Classification outputs
                for each feature level. Each is a 4D-tensor with shape
                [nb_dec, bs, num_query, cls_out_channels].
            all_bbox_preds_list (list[Tensor]): Sigmoid regression
                outputs for each feature level. Each is a 4D-tensor with
                normalized coordinate format (cx, cy, w, h) and shape
                [nb_dec, bs, num_query, 4].
            gt_bboxes_list (list[Tensor]): Ground truth bboxes for each image
                with shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            gt_labels_list (list[Tensor]): Ground truth class indices for each
                image with shape (num_gts, ).
            img_metas (list[dict]): List of image meta information.
            gt_bboxes_ignore (list[Tensor], optional): Bounding boxes
                which can be ignored for each image. Default None.

        Returns:
            dict[str, Tensor]: A dictionary of loss components.
        """
        all_cls_scores = all_cls_scores_list[-1]
        all_bbox_preds = all_bbox_preds_list[-1]
        assert gt_bboxes_ignore is None, 'Only supports for gt_bboxes_ignore setting to None.'
        num_dec_layers = len(all_cls_scores)
        all_gt_bboxes_list = [gt_bboxes_list for _ in range(num_dec_layers)]
        all_gt_labels_list = [gt_labels_list for _ in range(num_dec_layers)]
        all_gt_bboxes_ignore_list = [gt_bboxes_ignore for _ in range(num_dec_layers)]
        img_metas_list = [img_metas for _ in range(num_dec_layers)]
        losses_cls, losses_bbox, losses_iou = multi_apply(self.loss_single, all_cls_scores, all_bbox_preds, all_gt_bboxes_list, all_gt_labels_list, img_metas_list, all_gt_bboxes_ignore_list)
        loss_dict = dict()
        loss_dict['loss_cls'] = losses_cls[-1]
        loss_dict['loss_bbox'] = losses_bbox[-1]
        loss_dict['loss_iou'] = losses_iou[-1]
        num_dec_layer = 0
        for loss_cls_i, loss_bbox_i, loss_iou_i in zip(losses_cls[:-1], losses_bbox[:-1], losses_iou[:-1]):
            loss_dict[f'd{num_dec_layer}.loss_cls'] = loss_cls_i
            loss_dict[f'd{num_dec_layer}.loss_bbox'] = loss_bbox_i
            loss_dict[f'd{num_dec_layer}.loss_iou'] = loss_iou_i
            num_dec_layer += 1
        return loss_dict

    def loss_single(self, cls_scores, bbox_preds, gt_bboxes_list, gt_labels_list, img_metas, gt_bboxes_ignore_list=None):
        """"Loss function for outputs from a single decoder layer of a single
        feature level.

        Args:
            cls_scores (Tensor): Box score logits from a single decoder layer
                for all images. Shape [bs, num_query, cls_out_channels].
            bbox_preds (Tensor): Sigmoid outputs from a single decoder layer
                for all images, with normalized coordinate (cx, cy, w, h) and
                shape [bs, num_query, 4].
            gt_bboxes_list (list[Tensor]): Ground truth bboxes for each image
                with shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            gt_labels_list (list[Tensor]): Ground truth class indices for each
                image with shape (num_gts, ).
            img_metas (list[dict]): List of image meta information.
            gt_bboxes_ignore_list (list[Tensor], optional): Bounding
                boxes which can be ignored for each image. Default None.

        Returns:
            dict[str, Tensor]: A dictionary of loss components for outputs from
                a single decoder layer.
        """
        num_imgs = cls_scores.size(0)
        cls_scores_list = [cls_scores[i] for i in range(num_imgs)]
        bbox_preds_list = [bbox_preds[i] for i in range(num_imgs)]
        cls_reg_targets = self.get_targets(cls_scores_list, bbox_preds_list, gt_bboxes_list, gt_labels_list, img_metas, gt_bboxes_ignore_list)
        labels_list, label_weights_list, bbox_targets_list, bbox_weights_list, num_total_pos, num_total_neg = cls_reg_targets
        labels = torch.cat(labels_list, 0)
        label_weights = torch.cat(label_weights_list, 0)
        bbox_targets = torch.cat(bbox_targets_list, 0)
        bbox_weights = torch.cat(bbox_weights_list, 0)
        cls_scores = cls_scores.reshape(-1, self.cls_out_channels)
        cls_avg_factor = num_total_pos * 1.0 + num_total_neg * self.bg_cls_weight
        if self.sync_cls_avg_factor:
            cls_avg_factor = reduce_mean(cls_scores.new_tensor([cls_avg_factor]))
        cls_avg_factor = max(cls_avg_factor, 1)
        loss_cls = self.loss_cls(cls_scores, labels, label_weights, avg_factor=cls_avg_factor)
        num_total_pos = loss_cls.new_tensor([num_total_pos])
        num_total_pos = torch.clamp(reduce_mean(num_total_pos), min=1).item()
        factors = []
        for img_meta, bbox_pred in zip(img_metas, bbox_preds):
            img_h, img_w, _ = img_meta['img_shape']
            factor = bbox_pred.new_tensor([img_w, img_h, img_w, img_h]).unsqueeze(0).repeat(bbox_pred.size(0), 1)
            factors.append(factor)
        factors = torch.cat(factors, 0)
        bbox_preds = bbox_preds.reshape(-1, 4)
        bboxes = bbox_cxcywh_to_xyxy(bbox_preds) * factors
        bboxes_gt = bbox_cxcywh_to_xyxy(bbox_targets) * factors
        loss_iou = self.loss_iou(bboxes, bboxes_gt, bbox_weights, avg_factor=num_total_pos)
        loss_bbox = self.loss_bbox(bbox_preds, bbox_targets, bbox_weights, avg_factor=num_total_pos)
        return (loss_cls, loss_bbox, loss_iou)

    def get_targets(self, cls_scores_list, bbox_preds_list, gt_bboxes_list, gt_labels_list, img_metas, gt_bboxes_ignore_list=None):
        """"Compute regression and classification targets for a batch image.

        Outputs from a single decoder layer of a single feature level are used.

        Args:
            cls_scores_list (list[Tensor]): Box score logits from a single
                decoder layer for each image with shape [num_query,
                cls_out_channels].
            bbox_preds_list (list[Tensor]): Sigmoid outputs from a single
                decoder layer for each image, with normalized coordinate
                (cx, cy, w, h) and shape [num_query, 4].
            gt_bboxes_list (list[Tensor]): Ground truth bboxes for each image
                with shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            gt_labels_list (list[Tensor]): Ground truth class indices for each
                image with shape (num_gts, ).
            img_metas (list[dict]): List of image meta information.
            gt_bboxes_ignore_list (list[Tensor], optional): Bounding
                boxes which can be ignored for each image. Default None.

        Returns:
            tuple: a tuple containing the following targets.

                - labels_list (list[Tensor]): Labels for all images.
                - label_weights_list (list[Tensor]): Label weights for all                     images.
                - bbox_targets_list (list[Tensor]): BBox targets for all                     images.
                - bbox_weights_list (list[Tensor]): BBox weights for all                     images.
                - num_total_pos (int): Number of positive samples in all                     images.
                - num_total_neg (int): Number of negative samples in all                     images.
        """
        assert gt_bboxes_ignore_list is None, 'Only supports for gt_bboxes_ignore setting to None.'
        num_imgs = len(cls_scores_list)
        gt_bboxes_ignore_list = [gt_bboxes_ignore_list for _ in range(num_imgs)]
        labels_list, label_weights_list, bbox_targets_list, bbox_weights_list, pos_inds_list, neg_inds_list = multi_apply(self._get_target_single, cls_scores_list, bbox_preds_list, gt_bboxes_list, gt_labels_list, img_metas, gt_bboxes_ignore_list)
        num_total_pos = sum((inds.numel() for inds in pos_inds_list))
        num_total_neg = sum((inds.numel() for inds in neg_inds_list))
        return (labels_list, label_weights_list, bbox_targets_list, bbox_weights_list, num_total_pos, num_total_neg)

    def _get_target_single(self, cls_score, bbox_pred, gt_bboxes, gt_labels, img_meta, gt_bboxes_ignore=None):
        """"Compute regression and classification targets for one image.

        Outputs from a single decoder layer of a single feature level are used.

        Args:
            cls_score (Tensor): Box score logits from a single decoder layer
                for one image. Shape [num_query, cls_out_channels].
            bbox_pred (Tensor): Sigmoid outputs from a single decoder layer
                for one image, with normalized coordinate (cx, cy, w, h) and
                shape [num_query, 4].
            gt_bboxes (Tensor): Ground truth bboxes for one image with
                shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.
            gt_labels (Tensor): Ground truth class indices for one image
                with shape (num_gts, ).
            img_meta (dict): Meta information for one image.
            gt_bboxes_ignore (Tensor, optional): Bounding boxes
                which can be ignored. Default None.

        Returns:
            tuple[Tensor]: a tuple containing the following for one image.

                - labels (Tensor): Labels of each image.
                - label_weights (Tensor]): Label weights of each image.
                - bbox_targets (Tensor): BBox targets of each image.
                - bbox_weights (Tensor): BBox weights of each image.
                - pos_inds (Tensor): Sampled positive indices for each image.
                - neg_inds (Tensor): Sampled negative indices for each image.
        """
        num_bboxes = bbox_pred.size(0)
        assign_result = self.assigner.assign(bbox_pred, cls_score, gt_bboxes, gt_labels, img_meta, gt_bboxes_ignore)
        sampling_result = self.sampler.sample(assign_result, bbox_pred, gt_bboxes)
        pos_inds = sampling_result.pos_inds
        neg_inds = sampling_result.neg_inds
        labels = gt_bboxes.new_full((num_bboxes,), self.num_classes, dtype=torch.long)
        labels[pos_inds] = gt_labels[sampling_result.pos_assigned_gt_inds]
        label_weights = gt_bboxes.new_ones(num_bboxes)
        bbox_targets = torch.zeros_like(bbox_pred)
        bbox_weights = torch.zeros_like(bbox_pred)
        bbox_weights[pos_inds] = 1.0
        img_h, img_w, _ = img_meta['img_shape']
        factor = bbox_pred.new_tensor([img_w, img_h, img_w, img_h]).unsqueeze(0)
        pos_gt_bboxes_normalized = sampling_result.pos_gt_bboxes / factor
        pos_gt_bboxes_targets = bbox_xyxy_to_cxcywh(pos_gt_bboxes_normalized)
        bbox_targets[pos_inds] = pos_gt_bboxes_targets
        return (labels, label_weights, bbox_targets, bbox_weights, pos_inds, neg_inds)

    def forward_train(self, x, img_metas, gt_bboxes, gt_labels=None, gt_bboxes_ignore=None, proposal_cfg=None, **kwargs):
        """Forward function for training mode.

        Args:
            x (list[Tensor]): Features from backbone.
            img_metas (list[dict]): Meta information of each image, e.g.,
                image size, scaling factor, etc.
            gt_bboxes (Tensor): Ground truth bboxes of the image,
                shape (num_gts, 4).
            gt_labels (Tensor): Ground truth labels of each box,
                shape (num_gts,).
            gt_bboxes_ignore (Tensor): Ground truth bboxes to be
                ignored, shape (num_ignored_gts, 4).
            proposal_cfg (mmcv.Config): Test / postprocessing configuration,
                if None, test_cfg would be used.

        Returns:
            dict[str, Tensor]: A dictionary of loss components.
        """
        assert proposal_cfg is None, '"proposal_cfg" must be None'
        outs = self(x, img_metas)
        if gt_labels is None:
            loss_inputs = outs + (gt_bboxes, img_metas)
        else:
            loss_inputs = outs + (gt_bboxes, gt_labels, img_metas)
        losses = self.loss(*loss_inputs, gt_bboxes_ignore=gt_bboxes_ignore)
        return losses

    @force_fp32(apply_to=('all_cls_scores_list', 'all_bbox_preds_list'))
    def get_bboxes(self, all_cls_scores_list, all_bbox_preds_list, img_metas, rescale=False):
        """Transform network outputs for a batch into bbox predictions.

        Args:
            all_cls_scores_list (list[Tensor]): Classification outputs
                for each feature level. Each is a 4D-tensor with shape
                [nb_dec, bs, num_query, cls_out_channels].
            all_bbox_preds_list (list[Tensor]): Sigmoid regression
                outputs for each feature level. Each is a 4D-tensor with
                normalized coordinate format (cx, cy, w, h) and shape
                [nb_dec, bs, num_query, 4].
            img_metas (list[dict]): Meta information of each image.
            rescale (bool, optional): If True, return boxes in original
                image space. Default False.

        Returns:
            list[list[Tensor, Tensor]]: Each item in result_list is 2-tuple.                 The first item is an (n, 5) tensor, where the first 4 columns                 are bounding box positions (tl_x, tl_y, br_x, br_y) and the                 5-th column is a score between 0 and 1. The second item is a                 (n,) tensor where each item is the predicted class label of                 the corresponding box.
        """
        cls_scores = all_cls_scores_list[-1][-1]
        bbox_preds = all_bbox_preds_list[-1][-1]
        result_list = []
        for img_id in range(len(img_metas)):
            cls_score = cls_scores[img_id]
            bbox_pred = bbox_preds[img_id]
            img_shape = img_metas[img_id]['img_shape']
            scale_factor = img_metas[img_id]['scale_factor']
            proposals = self._get_bboxes_single(cls_score, bbox_pred, img_shape, scale_factor, rescale)
            result_list.append(proposals)
        return result_list

    def _get_bboxes_single(self, cls_score, bbox_pred, img_shape, scale_factor, rescale=False):
        """Transform outputs from the last decoder layer into bbox predictions
        for each image.

        Args:
            cls_score (Tensor): Box score logits from the last decoder layer
                for each image. Shape [num_query, cls_out_channels].
            bbox_pred (Tensor): Sigmoid outputs from the last decoder layer
                for each image, with coordinate format (cx, cy, w, h) and
                shape [num_query, 4].
            img_shape (tuple[int]): Shape of input image, (height, width, 3).
            scale_factor (ndarray, optional): Scale factor of the image arange
                as (w_scale, h_scale, w_scale, h_scale).
            rescale (bool, optional): If True, return boxes in original image
                space. Default False.

        Returns:
            tuple[Tensor]: Results of detected bboxes and labels.

                - det_bboxes: Predicted bboxes with shape [num_query, 5],                     where the first 4 columns are bounding box positions                     (tl_x, tl_y, br_x, br_y) and the 5-th column are scores                     between 0 and 1.
                - det_labels: Predicted labels of the corresponding box with                     shape [num_query].
        """
        assert len(cls_score) == len(bbox_pred)
        max_per_img = self.test_cfg.get('max_per_img', self.num_query)
        if self.loss_cls.use_sigmoid:
            cls_score = cls_score.sigmoid()
            scores, indexes = cls_score.view(-1).topk(max_per_img)
            det_labels = indexes % self.num_classes
            bbox_index = indexes // self.num_classes
            bbox_pred = bbox_pred[bbox_index]
        else:
            scores, det_labels = F.softmax(cls_score, dim=-1)[..., :-1].max(-1)
            scores, bbox_index = scores.topk(max_per_img)
            bbox_pred = bbox_pred[bbox_index]
            det_labels = det_labels[bbox_index]
        det_bboxes = bbox_cxcywh_to_xyxy(bbox_pred)
        det_bboxes[:, 0::2] = det_bboxes[:, 0::2] * img_shape[1]
        det_bboxes[:, 1::2] = det_bboxes[:, 1::2] * img_shape[0]
        det_bboxes[:, 0::2].clamp_(min=0, max=img_shape[1])
        det_bboxes[:, 1::2].clamp_(min=0, max=img_shape[0])
        if rescale:
            det_bboxes /= det_bboxes.new_tensor(scale_factor)
        det_bboxes = torch.cat((det_bboxes, scores.unsqueeze(1)), -1)
        return (det_bboxes, det_labels)

    def simple_test_bboxes(self, feats, img_metas, rescale=False):
        """Test det bboxes without test-time augmentation.

        Args:
            feats (tuple[torch.Tensor]): Multi-level features from the
                upstream network, each is a 4D-tensor.
            img_metas (list[dict]): List of image information.
            rescale (bool, optional): Whether to rescale the results.
                Defaults to False.

        Returns:
            list[tuple[Tensor, Tensor]]: Each item in result_list is 2-tuple.
                The first item is ``bboxes`` with shape (n, 5),
                where 5 represent (tl_x, tl_y, br_x, br_y, score).
                The shape of the second tensor in the tuple is ``labels``
                with shape (n,)
        """
        outs = self.forward(feats, img_metas)
        results_list = self.get_bboxes(*outs, img_metas, rescale=rescale)
        return results_list

    def forward_onnx(self, feats, img_metas):
        """Forward function for exporting to ONNX.

        Over-write `forward` because: `masks` is directly created with
        zero (valid position tag) and has the same spatial size as `x`.
        Thus the construction of `masks` is different from that in `forward`.

        Args:
            feats (tuple[Tensor]): Features from the upstream network, each is
                a 4D-tensor.
            img_metas (list[dict]): List of image information.

        Returns:
            tuple[list[Tensor], list[Tensor]]: Outputs for all scale levels.

                - all_cls_scores_list (list[Tensor]): Classification scores                     for each scale level. Each is a 4D-tensor with shape                     [nb_dec, bs, num_query, cls_out_channels]. Note                     `cls_out_channels` should includes background.
                - all_bbox_preds_list (list[Tensor]): Sigmoid regression                     outputs for each scale level. Each is a 4D-tensor with                     normalized coordinate format (cx, cy, w, h) and shape                     [nb_dec, bs, num_query, 4].
        """
        num_levels = len(feats)
        img_metas_list = [img_metas for _ in range(num_levels)]
        return multi_apply(self.forward_single_onnx, feats, img_metas_list)

    def forward_single_onnx(self, x, img_metas):
        """"Forward function for a single feature level with ONNX exportation.

        Args:
            x (Tensor): Input feature from backbone's single stage, shape
                [bs, c, h, w].
            img_metas (list[dict]): List of image information.

        Returns:
            all_cls_scores (Tensor): Outputs from the classification head,
                shape [nb_dec, bs, num_query, cls_out_channels]. Note
                cls_out_channels should includes background.
            all_bbox_preds (Tensor): Sigmoid outputs from the regression
                head with normalized coordinate format (cx, cy, w, h).
                Shape [nb_dec, bs, num_query, 4].
        """
        batch_size = x.size(0)
        h, w = x.size()[-2:]
        masks = x.new_zeros((batch_size, h, w))
        x = self.input_proj(x)
        masks = F.interpolate(masks.unsqueeze(1), size=x.shape[-2:]).to(torch.bool).squeeze(1)
        pos_embed = self.positional_encoding(masks)
        outs_dec, _ = self.transformer(x, masks, self.query_embedding.weight, pos_embed)
        all_cls_scores = self.fc_cls(outs_dec)
        all_bbox_preds = self.fc_reg(self.activate(self.reg_ffn(outs_dec))).sigmoid()
        return (all_cls_scores, all_bbox_preds)

    def onnx_export(self, all_cls_scores_list, all_bbox_preds_list, img_metas):
        """Transform network outputs into bbox predictions, with ONNX
        exportation.

        Args:
            all_cls_scores_list (list[Tensor]): Classification outputs
                for each feature level. Each is a 4D-tensor with shape
                [nb_dec, bs, num_query, cls_out_channels].
            all_bbox_preds_list (list[Tensor]): Sigmoid regression
                outputs for each feature level. Each is a 4D-tensor with
                normalized coordinate format (cx, cy, w, h) and shape
                [nb_dec, bs, num_query, 4].
            img_metas (list[dict]): Meta information of each image.

        Returns:
            tuple[Tensor, Tensor]: dets of shape [N, num_det, 5]
                and class labels of shape [N, num_det].
        """
        assert len(img_metas) == 1, 'Only support one input image while in exporting to ONNX'
        cls_scores = all_cls_scores_list[-1][-1]
        bbox_preds = all_bbox_preds_list[-1][-1]
        img_shape = img_metas[0]['img_shape_for_onnx']
        max_per_img = self.test_cfg.get('max_per_img', self.num_query)
        batch_size = cls_scores.size(0)
        batch_index_offset = torch.arange(batch_size).to(cls_scores.device) * max_per_img
        batch_index_offset = batch_index_offset.unsqueeze(1).expand(batch_size, max_per_img)
        if self.loss_cls.use_sigmoid:
            cls_scores = cls_scores.sigmoid()
            scores, indexes = cls_scores.view(batch_size, -1).topk(max_per_img, dim=1)
            det_labels = indexes % self.num_classes
            bbox_index = indexes // self.num_classes
            bbox_index = (bbox_index + batch_index_offset).view(-1)
            bbox_preds = bbox_preds.view(-1, 4)[bbox_index]
            bbox_preds = bbox_preds.view(batch_size, -1, 4)
        else:
            scores, det_labels = F.softmax(cls_scores, dim=-1)[..., :-1].max(-1)
            scores, bbox_index = scores.topk(max_per_img, dim=1)
            bbox_index = (bbox_index + batch_index_offset).view(-1)
            bbox_preds = bbox_preds.view(-1, 4)[bbox_index]
            det_labels = det_labels.view(-1)[bbox_index]
            bbox_preds = bbox_preds.view(batch_size, -1, 4)
            det_labels = det_labels.view(batch_size, -1)
        det_bboxes = bbox_cxcywh_to_xyxy(bbox_preds)
        img_shape_tensor = img_shape.flip(0).repeat(2)
        img_shape_tensor = img_shape_tensor.unsqueeze(0).unsqueeze(0).expand(batch_size, det_bboxes.size(1), 4)
        det_bboxes = det_bboxes * img_shape_tensor
        x1, y1, x2, y2 = det_bboxes.split((1, 1, 1, 1), dim=-1)
        from mmdet.core.export import dynamic_clip_for_onnx
        x1, y1, x2, y2 = dynamic_clip_for_onnx(x1, y1, x2, y2, img_shape)
        det_bboxes = torch.cat([x1, y1, x2, y2], dim=-1)
        det_bboxes = torch.cat((det_bboxes, scores.unsqueeze(-1)), -1)
        return (det_bboxes, det_labels)

def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs):
    """load checkpoints."""
    version = local_metadata.get('version', None)
    if (version is None or version < 2) and self.__class__ is DETRHead:
        convert_dict = {'.self_attn.': '.attentions.0.', '.ffn.': '.ffns.0.', '.multihead_attn.': '.attentions.1.', '.decoder.norm.': '.decoder.post_norm.'}
        state_dict_keys = list(state_dict.keys())
        for k in state_dict_keys:
            for ori_key, convert_key in convert_dict.items():
                if ori_key in k:
                    convert_key = k.replace(ori_key, convert_key)
                    state_dict[convert_key] = state_dict[k]
                    del state_dict[k]
    super(AnchorFreeHead, self)._load_from_state_dict(state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs)

@DETECTORS.register_module()
class RPN(BaseDetector):
    """Implementation of Region Proposal Network."""

    def __init__(self, backbone, neck, rpn_head, train_cfg, test_cfg, pretrained=None, init_cfg=None):
        super(RPN, self).__init__(init_cfg)
        if pretrained:
            warnings.warn('DeprecationWarning: pretrained is deprecated, please use "init_cfg" instead')
            backbone.pretrained = pretrained
        self.backbone = build_backbone(backbone)
        self.neck = build_neck(neck) if neck is not None else None
        rpn_train_cfg = train_cfg.rpn if train_cfg is not None else None
        rpn_head.update(train_cfg=rpn_train_cfg)
        rpn_head.update(test_cfg=test_cfg.rpn)
        self.rpn_head = build_head(rpn_head)
        self.train_cfg = train_cfg
        self.test_cfg = test_cfg

    def extract_feat(self, img):
        """Extract features.

        Args:
            img (torch.Tensor): Image tensor with shape (n, c, h ,w).

        Returns:
            list[torch.Tensor]: Multi-level features that may have
                different resolutions.
        """
        x = self.backbone(img)
        if self.with_neck:
            x = self.neck(x)
        return x

    def forward_dummy(self, img):
        """Dummy forward function."""
        x = self.extract_feat(img)
        rpn_outs = self.rpn_head(x)
        return rpn_outs

    def forward_train(self, img, img_metas, gt_bboxes=None, gt_bboxes_ignore=None):
        """
        Args:
            img (Tensor): Input images of shape (N, C, H, W).
                Typically these should be mean centered and std scaled.
            img_metas (list[dict]): A List of image info dict where each dict
                has: 'img_shape', 'scale_factor', 'flip', and may also contain
                'filename', 'ori_shape', 'pad_shape', and 'img_norm_cfg'.
                For details on the values of these keys see
                :class:`mmdet.datasets.pipelines.Collect`.
            gt_bboxes (list[Tensor]): Each item are the truth boxes for each
                image in [tl_x, tl_y, br_x, br_y] format.
            gt_bboxes_ignore (None | list[Tensor]): Specify which bounding
                boxes can be ignored when computing the loss.

        Returns:
            dict[str, Tensor]: A dictionary of loss components.
        """
        if isinstance(self.train_cfg.rpn, dict) and self.train_cfg.rpn.get('debug', False):
            self.rpn_head.debug_imgs = tensor2imgs(img)
        x = self.extract_feat(img)
        losses = self.rpn_head.forward_train(x, img_metas, gt_bboxes, None, gt_bboxes_ignore)
        return losses

    def simple_test(self, img, img_metas, rescale=False):
        """Test function without test time augmentation.

        Args:
            imgs (list[torch.Tensor]): List of multiple images
            img_metas (list[dict]): List of image information.
            rescale (bool, optional): Whether to rescale the results.
                Defaults to False.

        Returns:
            list[np.ndarray]: proposals
        """
        x = self.extract_feat(img)
        if torch.onnx.is_in_onnx_export():
            img_shape = torch._shape_as_tensor(img)[2:]
            img_metas[0]['img_shape_for_onnx'] = img_shape
        proposal_list = self.rpn_head.simple_test_rpn(x, img_metas)
        if rescale:
            for proposals, meta in zip(proposal_list, img_metas):
                proposals[:, :4] /= proposals.new_tensor(meta['scale_factor'])
        if torch.onnx.is_in_onnx_export():
            return proposal_list
        return [proposal.cpu().numpy() for proposal in proposal_list]

    def aug_test(self, imgs, img_metas, rescale=False):
        """Test function with test time augmentation.

        Args:
            imgs (list[torch.Tensor]): List of multiple images
            img_metas (list[dict]): List of image information.
            rescale (bool, optional): Whether to rescale the results.
                Defaults to False.

        Returns:
            list[np.ndarray]: proposals
        """
        proposal_list = self.rpn_head.aug_test_rpn(self.extract_feats(imgs), img_metas)
        if not rescale:
            for proposals, img_meta in zip(proposal_list, img_metas[0]):
                img_shape = img_meta['img_shape']
                scale_factor = img_meta['scale_factor']
                flip = img_meta['flip']
                flip_direction = img_meta['flip_direction']
                proposals[:, :4] = bbox_mapping(proposals[:, :4], img_shape, scale_factor, flip, flip_direction)
        return [proposal.cpu().numpy() for proposal in proposal_list]

    def show_result(self, data, result, top_k=20, **kwargs):
        """Show RPN proposals on the image.

        Args:
            data (str or np.ndarray): Image filename or loaded image.
            result (Tensor or tuple): The results to draw over `img`
                bbox_result or (bbox_result, segm_result).
            top_k (int): Plot the first k bboxes only
               if set positive. Default: 20

        Returns:
            np.ndarray: The image with bboxes drawn on it.
        """
        if kwargs is not None:
            kwargs['colors'] = 'green'
            sig = signature(mmcv.imshow_bboxes)
            for k in list(kwargs.keys()):
                if k not in sig.parameters:
                    kwargs.pop(k)
        mmcv.imshow_bboxes(data, result, top_k=top_k, **kwargs)

def show_result(self, data, result, top_k=20, **kwargs):
    """Show RPN proposals on the image.

        Args:
            data (str or np.ndarray): Image filename or loaded image.
            result (Tensor or tuple): The results to draw over `img`
                bbox_result or (bbox_result, segm_result).
            top_k (int): Plot the first k bboxes only
               if set positive. Default: 20

        Returns:
            np.ndarray: The image with bboxes drawn on it.
        """
    if kwargs is not None:
        kwargs['colors'] = 'green'
        sig = signature(mmcv.imshow_bboxes)
        for k in list(kwargs.keys()):
            if k not in sig.parameters:
                kwargs.pop(k)
    mmcv.imshow_bboxes(data, result, top_k=top_k, **kwargs)

@HEADS.register_module()
class PointRendRoIHead(StandardRoIHead):
    """`PointRend <https://arxiv.org/abs/1912.08193>`_."""

    def __init__(self, point_head, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.with_bbox and self.with_mask
        self.init_point_head(point_head)

    def init_point_head(self, point_head):
        """Initialize ``point_head``"""
        self.point_head = builder.build_head(point_head)

    def _mask_forward_train(self, x, sampling_results, bbox_feats, gt_masks, img_metas):
        """Run forward function and calculate loss for mask head and point head
        in training."""
        mask_results = super()._mask_forward_train(x, sampling_results, bbox_feats, gt_masks, img_metas)
        if mask_results['loss_mask'] is not None:
            loss_point = self._mask_point_forward_train(x, sampling_results, mask_results['mask_pred'], gt_masks, img_metas)
            mask_results['loss_mask'].update(loss_point)
        return mask_results

    def _mask_point_forward_train(self, x, sampling_results, mask_pred, gt_masks, img_metas):
        """Run forward function and calculate loss for point head in
        training."""
        pos_labels = torch.cat([res.pos_gt_labels for res in sampling_results])
        rel_roi_points = self.point_head.get_roi_rel_points_train(mask_pred, pos_labels, cfg=self.train_cfg)
        rois = bbox2roi([res.pos_bboxes for res in sampling_results])
        fine_grained_point_feats = self._get_fine_grained_point_feats(x, rois, rel_roi_points, img_metas)
        coarse_point_feats = point_sample(mask_pred, rel_roi_points)
        mask_point_pred = self.point_head(fine_grained_point_feats, coarse_point_feats)
        mask_point_target = self.point_head.get_targets(rois, rel_roi_points, sampling_results, gt_masks, self.train_cfg)
        loss_mask_point = self.point_head.loss(mask_point_pred, mask_point_target, pos_labels)
        return loss_mask_point

    def _get_fine_grained_point_feats(self, x, rois, rel_roi_points, img_metas):
        """Sample fine grained feats from each level feature map and
        concatenate them together.

        Args:
            x (tuple[Tensor]): Feature maps of all scale level.
            rois (Tensor): shape (num_rois, 5).
            rel_roi_points (Tensor): A tensor of shape (num_rois, num_points,
                2) that contains [0, 1] x [0, 1] normalized coordinates of the
                most uncertain points from the [mask_height, mask_width] grid.
            img_metas (list[dict]): Image meta info.

        Returns:
            Tensor: The fine grained features for each points,
                has shape (num_rois, feats_channels, num_points).
        """
        num_imgs = len(img_metas)
        fine_grained_feats = []
        for idx in range(self.mask_roi_extractor.num_inputs):
            feats = x[idx]
            spatial_scale = 1.0 / float(self.mask_roi_extractor.featmap_strides[idx])
            point_feats = []
            for batch_ind in range(num_imgs):
                feat = feats[batch_ind].unsqueeze(0)
                inds = rois[:, 0].long() == batch_ind
                if inds.any():
                    rel_img_points = rel_roi_point_to_rel_img_point(rois[inds], rel_roi_points[inds], feat.shape[2:], spatial_scale).unsqueeze(0)
                    point_feat = point_sample(feat, rel_img_points)
                    point_feat = point_feat.squeeze(0).transpose(0, 1)
                    point_feats.append(point_feat)
            fine_grained_feats.append(torch.cat(point_feats, dim=0))
        return torch.cat(fine_grained_feats, dim=1)

    def _mask_point_forward_test(self, x, rois, label_pred, mask_pred, img_metas):
        """Mask refining process with point head in testing.

        Args:
            x (tuple[Tensor]): Feature maps of all scale level.
            rois (Tensor): shape (num_rois, 5).
            label_pred (Tensor): The predication class for each rois.
            mask_pred (Tensor): The predication coarse masks of
                shape (num_rois, num_classes, small_size, small_size).
            img_metas (list[dict]): Image meta info.

        Returns:
            Tensor: The refined masks of shape (num_rois, num_classes,
                large_size, large_size).
        """
        refined_mask_pred = mask_pred.clone()
        for subdivision_step in range(self.test_cfg.subdivision_steps):
            refined_mask_pred = F.interpolate(refined_mask_pred, scale_factor=self.test_cfg.scale_factor, mode='bilinear', align_corners=False)
            num_rois, channels, mask_height, mask_width = refined_mask_pred.shape
            if self.test_cfg.subdivision_num_points >= self.test_cfg.scale_factor ** 2 * mask_height * mask_width and subdivision_step < self.test_cfg.subdivision_steps - 1:
                continue
            point_indices, rel_roi_points = self.point_head.get_roi_rel_points_test(refined_mask_pred, label_pred, cfg=self.test_cfg)
            fine_grained_point_feats = self._get_fine_grained_point_feats(x, rois, rel_roi_points, img_metas)
            coarse_point_feats = point_sample(mask_pred, rel_roi_points)
            mask_point_pred = self.point_head(fine_grained_point_feats, coarse_point_feats)
            point_indices = point_indices.unsqueeze(1).expand(-1, channels, -1)
            refined_mask_pred = refined_mask_pred.reshape(num_rois, channels, mask_height * mask_width)
            refined_mask_pred = refined_mask_pred.scatter_(2, point_indices, mask_point_pred)
            refined_mask_pred = refined_mask_pred.view(num_rois, channels, mask_height, mask_width)
        return refined_mask_pred

    def simple_test_mask(self, x, img_metas, det_bboxes, det_labels, rescale=False):
        """Obtain mask prediction without augmentation."""
        ori_shapes = tuple((meta['ori_shape'] for meta in img_metas))
        scale_factors = tuple((meta['scale_factor'] for meta in img_metas))
        if isinstance(scale_factors[0], float):
            warnings.warn('Scale factor in img_metas should be a ndarray with shape (4,) arrange as (factor_w, factor_h, factor_w, factor_h), The scale_factor with float type has been deprecated. ')
            scale_factors = np.array([scale_factors] * 4, dtype=np.float32)
        num_imgs = len(det_bboxes)
        if all((det_bbox.shape[0] == 0 for det_bbox in det_bboxes)):
            segm_results = [[[] for _ in range(self.mask_head.num_classes)] for _ in range(num_imgs)]
        else:
            _bboxes = [det_bboxes[i][:, :4] for i in range(len(det_bboxes))]
            if rescale:
                scale_factors = [torch.from_numpy(scale_factor).to(det_bboxes[0].device) for scale_factor in scale_factors]
                _bboxes = [_bboxes[i] * scale_factors[i] for i in range(len(_bboxes))]
            mask_rois = bbox2roi(_bboxes)
            mask_results = self._mask_forward(x, mask_rois)
            mask_pred = mask_results['mask_pred']
            num_mask_roi_per_img = [len(det_bbox) for det_bbox in det_bboxes]
            mask_preds = mask_pred.split(num_mask_roi_per_img, 0)
            mask_rois = mask_rois.split(num_mask_roi_per_img, 0)
            segm_results = []
            for i in range(num_imgs):
                if det_bboxes[i].shape[0] == 0:
                    segm_results.append([[] for _ in range(self.mask_head.num_classes)])
                else:
                    x_i = [xx[[i]] for xx in x]
                    mask_rois_i = mask_rois[i]
                    mask_rois_i[:, 0] = 0
                    mask_pred_i = self._mask_point_forward_test(x_i, mask_rois_i, det_labels[i], mask_preds[i], [img_metas])
                    segm_result = self.mask_head.get_seg_masks(mask_pred_i, _bboxes[i], det_labels[i], self.test_cfg, ori_shapes[i], scale_factors[i], rescale)
                    segm_results.append(segm_result)
        return segm_results

    def aug_test_mask(self, feats, img_metas, det_bboxes, det_labels):
        """Test for mask head with test time augmentation."""
        if det_bboxes.shape[0] == 0:
            segm_result = [[] for _ in range(self.mask_head.num_classes)]
        else:
            aug_masks = []
            for x, img_meta in zip(feats, img_metas):
                img_shape = img_meta[0]['img_shape']
                scale_factor = img_meta[0]['scale_factor']
                flip = img_meta[0]['flip']
                _bboxes = bbox_mapping(det_bboxes[:, :4], img_shape, scale_factor, flip)
                mask_rois = bbox2roi([_bboxes])
                mask_results = self._mask_forward(x, mask_rois)
                mask_results['mask_pred'] = self._mask_point_forward_test(x, mask_rois, det_labels, mask_results['mask_pred'], img_meta)
                aug_masks.append(mask_results['mask_pred'].sigmoid().cpu().numpy())
            merged_masks = merge_aug_masks(aug_masks, img_metas, self.test_cfg)
            ori_shape = img_metas[0][0]['ori_shape']
            segm_result = self.mask_head.get_seg_masks(merged_masks, det_bboxes, det_labels, self.test_cfg, ori_shape, scale_factor=1.0, rescale=False)
        return segm_result

    def _onnx_get_fine_grained_point_feats(self, x, rois, rel_roi_points):
        """Export the process of sampling fine grained feats to onnx.

        Args:
            x (tuple[Tensor]): Feature maps of all scale level.
            rois (Tensor): shape (num_rois, 5).
            rel_roi_points (Tensor): A tensor of shape (num_rois, num_points,
                2) that contains [0, 1] x [0, 1] normalized coordinates of the
                most uncertain points from the [mask_height, mask_width] grid.

        Returns:
            Tensor: The fine grained features for each points,
                has shape (num_rois, feats_channels, num_points).
        """
        batch_size = x[0].shape[0]
        num_rois = rois.shape[0]
        fine_grained_feats = []
        for idx in range(self.mask_roi_extractor.num_inputs):
            feats = x[idx]
            spatial_scale = 1.0 / float(self.mask_roi_extractor.featmap_strides[idx])
            rel_img_points = rel_roi_point_to_rel_img_point(rois, rel_roi_points, feats, spatial_scale)
            channels = feats.shape[1]
            num_points = rel_img_points.shape[1]
            rel_img_points = rel_img_points.reshape(batch_size, -1, num_points, 2)
            point_feats = point_sample(feats, rel_img_points)
            point_feats = point_feats.transpose(1, 2).reshape(num_rois, channels, num_points)
            fine_grained_feats.append(point_feats)
        return torch.cat(fine_grained_feats, dim=1)

    def _mask_point_onnx_export(self, x, rois, label_pred, mask_pred):
        """Export mask refining process with point head to onnx.

        Args:
            x (tuple[Tensor]): Feature maps of all scale level.
            rois (Tensor): shape (num_rois, 5).
            label_pred (Tensor): The predication class for each rois.
            mask_pred (Tensor): The predication coarse masks of
                shape (num_rois, num_classes, small_size, small_size).

        Returns:
            Tensor: The refined masks of shape (num_rois, num_classes,
                large_size, large_size).
        """
        refined_mask_pred = mask_pred.clone()
        for subdivision_step in range(self.test_cfg.subdivision_steps):
            refined_mask_pred = F.interpolate(refined_mask_pred, scale_factor=self.test_cfg.scale_factor, mode='bilinear', align_corners=False)
            num_rois, channels, mask_height, mask_width = refined_mask_pred.shape
            if self.test_cfg.subdivision_num_points >= self.test_cfg.scale_factor ** 2 * mask_height * mask_width and subdivision_step < self.test_cfg.subdivision_steps - 1:
                continue
            point_indices, rel_roi_points = self.point_head.get_roi_rel_points_test(refined_mask_pred, label_pred, cfg=self.test_cfg)
            fine_grained_point_feats = self._onnx_get_fine_grained_point_feats(x, rois, rel_roi_points)
            coarse_point_feats = point_sample(mask_pred, rel_roi_points)
            mask_point_pred = self.point_head(fine_grained_point_feats, coarse_point_feats)
            point_indices = point_indices.unsqueeze(1).expand(-1, channels, -1)
            refined_mask_pred = refined_mask_pred.reshape(num_rois, channels, mask_height * mask_width)
            is_trt_backend = os.environ.get('ONNX_BACKEND') == 'MMCVTensorRT'
            if is_trt_backend:
                mask_shape = refined_mask_pred.shape
                point_shape = point_indices.shape
                inds_dim0 = torch.arange(point_shape[0]).reshape(point_shape[0], 1, 1).expand_as(point_indices)
                inds_dim1 = torch.arange(point_shape[1]).reshape(1, point_shape[1], 1).expand_as(point_indices)
                inds_1d = inds_dim0.reshape(-1) * mask_shape[1] * mask_shape[2] + inds_dim1.reshape(-1) * mask_shape[2] + point_indices.reshape(-1)
                refined_mask_pred = refined_mask_pred.reshape(-1)
                refined_mask_pred[inds_1d] = mask_point_pred.reshape(-1)
                refined_mask_pred = refined_mask_pred.reshape(*mask_shape)
            else:
                refined_mask_pred = refined_mask_pred.scatter_(2, point_indices, mask_point_pred)
            refined_mask_pred = refined_mask_pred.view(num_rois, channels, mask_height, mask_width)
        return refined_mask_pred

    def mask_onnx_export(self, x, img_metas, det_bboxes, det_labels, **kwargs):
        """Export mask branch to onnx which supports batch inference.

        Args:
            x (tuple[Tensor]): Feature maps of all scale level.
            img_metas (list[dict]): Image meta info.
            det_bboxes (Tensor): Bboxes and corresponding scores.
                has shape [N, num_bboxes, 5].
            det_labels (Tensor): class labels of
                shape [N, num_bboxes].

        Returns:
            Tensor: The segmentation results of shape [N, num_bboxes,
                image_height, image_width].
        """
        if all((det_bbox.shape[0] == 0 for det_bbox in det_bboxes)):
            raise RuntimeError('[ONNX Error] Can not record MaskHead as it has not been executed this time')
        batch_size = det_bboxes.size(0)
        det_bboxes = det_bboxes[..., :4]
        batch_index = torch.arange(det_bboxes.size(0), device=det_bboxes.device).float().view(-1, 1, 1).expand(det_bboxes.size(0), det_bboxes.size(1), 1)
        mask_rois = torch.cat([batch_index, det_bboxes], dim=-1)
        mask_rois = mask_rois.view(-1, 5)
        mask_results = self._mask_forward(x, mask_rois)
        mask_pred = mask_results['mask_pred']
        max_shape = img_metas[0]['img_shape_for_onnx']
        num_det = det_bboxes.shape[1]
        det_bboxes = det_bboxes.reshape(-1, 4)
        det_labels = det_labels.reshape(-1)
        mask_pred = self._mask_point_onnx_export(x, mask_rois, det_labels, mask_pred)
        segm_results = self.mask_head.onnx_export(mask_pred, det_bboxes, det_labels, self.test_cfg, max_shape)
        segm_results = segm_results.reshape(batch_size, num_det, max_shape[0], max_shape[1])
        return segm_results

def _mask_forward_train(self, x, sampling_results, bbox_feats, gt_masks, img_metas):
    """Run forward function and calculate loss for mask head and point head
        in training."""
    mask_results = super()._mask_forward_train(x, sampling_results, bbox_feats, gt_masks, img_metas)
    if mask_results['loss_mask'] is not None:
        loss_point = self._mask_point_forward_train(x, sampling_results, mask_results['mask_pred'], gt_masks, img_metas)
        mask_results['loss_mask'].update(loss_point)
    return mask_results

@NECKS.register_module()
class FPG(BaseModule):
    """FPG.

    Implementation of `Feature Pyramid Grids (FPG)
    <https://arxiv.org/abs/2004.03580>`_.
    This implementation only gives the basic structure stated in the paper.
    But users can implement different type of transitions to fully explore the
    the potential power of the structure of FPG.

    Args:
        in_channels (int): Number of input channels (feature maps of all levels
            should have the same channels).
        out_channels (int): Number of output channels (used at each scale)
        num_outs (int): Number of output scales.
        stack_times (int): The number of times the pyramid architecture will
            be stacked.
        paths (list[str]): Specify the path order of each stack level.
            Each element in the list should be either 'bu' (bottom-up) or
            'td' (top-down).
        inter_channels (int): Number of inter channels.
        same_up_trans (dict): Transition that goes down at the same stage.
        same_down_trans (dict): Transition that goes up at the same stage.
        across_lateral_trans (dict): Across-pathway same-stage
        across_down_trans (dict): Across-pathway bottom-up connection.
        across_up_trans (dict): Across-pathway top-down connection.
        across_skip_trans (dict): Across-pathway skip connection.
        output_trans (dict): Transition that trans the output of the
            last stage.
        start_level (int): Index of the start input backbone level used to
            build the feature pyramid. Default: 0.
        end_level (int): Index of the end input backbone level (exclusive) to
            build the feature pyramid. Default: -1, which means the last level.
        add_extra_convs (bool): It decides whether to add conv
            layers on top of the original feature maps. Default to False.
            If True, its actual mode is specified by `extra_convs_on_inputs`.
        norm_cfg (dict): Config dict for normalization layer. Default: None.
        init_cfg (dict or list[dict], optional): Initialization config dict.
    """
    transition_types = {'conv': ConvModule, 'interpolation_conv': UpInterpolationConv, 'last_conv': LastConv}

    def __init__(self, in_channels, out_channels, num_outs, stack_times, paths, inter_channels=None, same_down_trans=None, same_up_trans=dict(type='conv', kernel_size=3, stride=2, padding=1), across_lateral_trans=dict(type='conv', kernel_size=1), across_down_trans=dict(type='conv', kernel_size=3), across_up_trans=None, across_skip_trans=dict(type='identity'), output_trans=dict(type='last_conv', kernel_size=3), start_level=0, end_level=-1, add_extra_convs=False, norm_cfg=None, skip_inds=None, init_cfg=[dict(type='Caffe2Xavier', layer='Conv2d'), dict(type='Constant', layer=['_BatchNorm', '_InstanceNorm', 'GroupNorm', 'LayerNorm'], val=1.0)]):
        super(FPG, self).__init__(init_cfg)
        assert isinstance(in_channels, list)
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_ins = len(in_channels)
        self.num_outs = num_outs
        if inter_channels is None:
            self.inter_channels = [out_channels for _ in range(num_outs)]
        elif isinstance(inter_channels, int):
            self.inter_channels = [inter_channels for _ in range(num_outs)]
        else:
            assert isinstance(inter_channels, list)
            assert len(inter_channels) == num_outs
            self.inter_channels = inter_channels
        self.stack_times = stack_times
        self.paths = paths
        assert isinstance(paths, list) and len(paths) == stack_times
        for d in paths:
            assert d in ('bu', 'td')
        self.same_down_trans = same_down_trans
        self.same_up_trans = same_up_trans
        self.across_lateral_trans = across_lateral_trans
        self.across_down_trans = across_down_trans
        self.across_up_trans = across_up_trans
        self.output_trans = output_trans
        self.across_skip_trans = across_skip_trans
        self.with_bias = norm_cfg is None
        if self.across_skip_trans is not None:
            skip_inds is not None
        self.skip_inds = skip_inds
        assert len(self.skip_inds[0]) <= self.stack_times
        if end_level == -1 or end_level == self.num_ins - 1:
            self.backbone_end_level = self.num_ins
            assert num_outs >= self.num_ins - start_level
        else:
            self.backbone_end_level = end_level + 1
            assert end_level < self.num_ins
            assert num_outs == end_level - start_level + 1
        self.start_level = start_level
        self.end_level = end_level
        self.add_extra_convs = add_extra_convs
        self.lateral_convs = nn.ModuleList()
        for i in range(self.start_level, self.backbone_end_level):
            l_conv = nn.Conv2d(self.in_channels[i], self.inter_channels[i - self.start_level], 1)
            self.lateral_convs.append(l_conv)
        extra_levels = num_outs - self.backbone_end_level + self.start_level
        self.extra_downsamples = nn.ModuleList()
        for i in range(extra_levels):
            if self.add_extra_convs:
                fpn_idx = self.backbone_end_level - self.start_level + i
                extra_conv = nn.Conv2d(self.inter_channels[fpn_idx - 1], self.inter_channels[fpn_idx], 3, stride=2, padding=1)
                self.extra_downsamples.append(extra_conv)
            else:
                self.extra_downsamples.append(nn.MaxPool2d(1, stride=2))
        self.fpn_transitions = nn.ModuleList()
        for s in range(self.stack_times):
            stage_trans = nn.ModuleList()
            for i in range(self.num_outs):
                trans = nn.ModuleDict()
                if s in self.skip_inds[i]:
                    stage_trans.append(trans)
                    continue
                if i == 0 or self.same_up_trans is None:
                    same_up_trans = None
                else:
                    same_up_trans = self.build_trans(self.same_up_trans, self.inter_channels[i - 1], self.inter_channels[i])
                trans['same_up'] = same_up_trans
                if i == self.num_outs - 1 or self.same_down_trans is None:
                    same_down_trans = None
                else:
                    same_down_trans = self.build_trans(self.same_down_trans, self.inter_channels[i + 1], self.inter_channels[i])
                trans['same_down'] = same_down_trans
                across_lateral_trans = self.build_trans(self.across_lateral_trans, self.inter_channels[i], self.inter_channels[i])
                trans['across_lateral'] = across_lateral_trans
                if i == self.num_outs - 1 or self.across_down_trans is None:
                    across_down_trans = None
                else:
                    across_down_trans = self.build_trans(self.across_down_trans, self.inter_channels[i + 1], self.inter_channels[i])
                trans['across_down'] = across_down_trans
                if i == 0 or self.across_up_trans is None:
                    across_up_trans = None
                else:
                    across_up_trans = self.build_trans(self.across_up_trans, self.inter_channels[i - 1], self.inter_channels[i])
                trans['across_up'] = across_up_trans
                if self.across_skip_trans is None:
                    across_skip_trans = None
                else:
                    across_skip_trans = self.build_trans(self.across_skip_trans, self.inter_channels[i - 1], self.inter_channels[i])
                trans['across_skip'] = across_skip_trans
                stage_trans.append(trans)
            self.fpn_transitions.append(stage_trans)
        self.output_transition = nn.ModuleList()
        for i in range(self.num_outs):
            trans = self.build_trans(self.output_trans, self.inter_channels[i], self.out_channels, num_inputs=self.stack_times + 1)
            self.output_transition.append(trans)
        self.relu = nn.ReLU(inplace=True)

    def build_trans(self, cfg, in_channels, out_channels, **extra_args):
        cfg_ = cfg.copy()
        trans_type = cfg_.pop('type')
        trans_cls = self.transition_types[trans_type]
        return trans_cls(in_channels, out_channels, **cfg_, **extra_args)

    def fuse(self, fuse_dict):
        out = None
        for item in fuse_dict.values():
            if item is not None:
                if out is None:
                    out = item
                else:
                    out = out + item
        return out

    def forward(self, inputs):
        assert len(inputs) == len(self.in_channels)
        feats = [lateral_conv(inputs[i + self.start_level]) for i, lateral_conv in enumerate(self.lateral_convs)]
        for downsample in self.extra_downsamples:
            feats.append(downsample(feats[-1]))
        outs = [feats]
        for i in range(self.stack_times):
            current_outs = outs[-1]
            next_outs = []
            direction = self.paths[i]
            for j in range(self.num_outs):
                if i in self.skip_inds[j]:
                    next_outs.append(outs[-1][j])
                    continue
                if direction == 'td':
                    lvl = self.num_outs - j - 1
                else:
                    lvl = j
                if direction == 'td':
                    same_trans = self.fpn_transitions[i][lvl]['same_down']
                else:
                    same_trans = self.fpn_transitions[i][lvl]['same_up']
                across_lateral_trans = self.fpn_transitions[i][lvl]['across_lateral']
                across_down_trans = self.fpn_transitions[i][lvl]['across_down']
                across_up_trans = self.fpn_transitions[i][lvl]['across_up']
                across_skip_trans = self.fpn_transitions[i][lvl]['across_skip']
                to_fuse = dict(same=None, lateral=None, across_up=None, across_down=None)
                if same_trans is not None:
                    to_fuse['same'] = same_trans(next_outs[-1])
                if across_lateral_trans is not None:
                    to_fuse['lateral'] = across_lateral_trans(current_outs[lvl])
                if lvl > 0 and across_up_trans is not None:
                    to_fuse['across_up'] = across_up_trans(current_outs[lvl - 1])
                if lvl < self.num_outs - 1 and across_down_trans is not None:
                    to_fuse['across_down'] = across_down_trans(current_outs[lvl + 1])
                if across_skip_trans is not None:
                    to_fuse['across_skip'] = across_skip_trans(outs[0][lvl])
                x = self.fuse(to_fuse)
                next_outs.append(x)
            if direction == 'td':
                outs.append(next_outs[::-1])
            else:
                outs.append(next_outs)
        final_outs = []
        for i in range(self.num_outs):
            lvl_out_list = []
            for s in range(len(outs)):
                lvl_out_list.append(outs[s][i])
            lvl_out = self.output_transition[i](lvl_out_list)
            final_outs.append(lvl_out)
        return final_outs

def fuse(self, fuse_dict):
    out = None
    for item in fuse_dict.values():
        if item is not None:
            if out is None:
                out = item
            else:
                out = out + item
    return out

class MMdetHandler(BaseHandler):
    threshold = 0.5

    def initialize(self, context):
        properties = context.system_properties
        self.map_location = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = torch.device(self.map_location + ':' + str(properties.get('gpu_id')) if torch.cuda.is_available() else self.map_location)
        self.manifest = context.manifest
        model_dir = properties.get('model_dir')
        serialized_file = self.manifest['model']['serializedFile']
        checkpoint = os.path.join(model_dir, serialized_file)
        self.config_file = os.path.join(model_dir, 'config.py')
        self.model = init_detector(self.config_file, checkpoint, self.device)
        self.initialized = True

    def preprocess(self, data):
        images = []
        for row in data:
            image = row.get('data') or row.get('body')
            if isinstance(image, str):
                image = base64.b64decode(image)
            image = mmcv.imfrombytes(image)
            images.append(image)
        return images

    def inference(self, data, *args, **kwargs):
        results = inference_detector(self.model, data)
        return results

    def postprocess(self, data):
        output = []
        for image_index, image_result in enumerate(data):
            output.append([])
            if isinstance(image_result, tuple):
                bbox_result, segm_result = image_result
                if isinstance(segm_result, tuple):
                    segm_result = segm_result[0]
            else:
                bbox_result, segm_result = (image_result, None)
            for class_index, class_result in enumerate(bbox_result):
                class_name = self.model.CLASSES[class_index]
                for bbox in class_result:
                    bbox_coords = bbox[:-1].tolist()
                    score = float(bbox[-1])
                    if score >= self.threshold:
                        output[image_index].append({'class_name': class_name, 'bbox': bbox_coords, 'score': score})
        return output

def initialize(self, context):
    properties = context.system_properties
    self.map_location = 'cuda' if torch.cuda.is_available() else 'cpu'
    self.device = torch.device(self.map_location + ':' + str(properties.get('gpu_id')) if torch.cuda.is_available() else self.map_location)
    self.manifest = context.manifest
    model_dir = properties.get('model_dir')
    serialized_file = self.manifest['model']['serializedFile']
    checkpoint = os.path.join(model_dir, serialized_file)
    self.config_file = os.path.join(model_dir, 'config.py')
    self.model = init_detector(self.config_file, checkpoint, self.device)
    self.initialized = True

def inference(self, data, *args, **kwargs):
    results = inference_detector(self.model, data)
    return results

def pytorch2onnx(model, input_img, input_shape, normalize_cfg, opset_version=11, show=False, output_file='tmp.onnx', verify=False, test_img=None, do_simplify=False, dynamic_export=None, skip_postprocess=False):
    input_config = {'input_shape': input_shape, 'input_path': input_img, 'normalize_cfg': normalize_cfg}
    one_img, one_meta = preprocess_example_input(input_config)
    img_list, img_meta_list = ([one_img], [[one_meta]])
    if skip_postprocess:
        warnings.warn('Not all models support export onnx without post process, especially two stage detectors!')
        model.forward = model.forward_dummy
        torch.onnx.export(model, one_img, output_file, input_names=['input'], export_params=True, keep_initializers_as_inputs=True, do_constant_folding=True, verbose=show, opset_version=opset_version)
        print(f'Successfully exported ONNX model without post process: {output_file}')
        return
    origin_forward = model.forward
    model.forward = partial(model.forward, img_metas=img_meta_list, return_loss=False, rescale=False)
    output_names = ['dets', 'labels']
    if model.with_mask:
        output_names.append('masks')
    input_name = 'input'
    dynamic_axes = None
    if dynamic_export:
        dynamic_axes = {input_name: {0: 'batch', 2: 'height', 3: 'width'}, 'dets': {0: 'batch', 1: 'num_dets'}, 'labels': {0: 'batch', 1: 'num_dets'}}
        if model.with_mask:
            dynamic_axes['masks'] = {0: 'batch', 1: 'num_dets'}
    torch.onnx.export(model, img_list, output_file, input_names=[input_name], output_names=output_names, export_params=True, keep_initializers_as_inputs=True, do_constant_folding=True, verbose=show, opset_version=opset_version, dynamic_axes=dynamic_axes)
    model.forward = origin_forward
    if do_simplify:
        import onnxsim
        from mmdet import digit_version
        min_required_version = '0.4.0'
        assert digit_version(onnxsim.__version__) >= digit_version(min_required_version), f'Requires to install onnxsim>={min_required_version}'
        model_opt, check_ok = onnxsim.simplify(output_file)
        if check_ok:
            onnx.save(model_opt, output_file)
            print(f'Successfully simplified ONNX model: {output_file}')
        else:
            warnings.warn('Failed to simplify ONNX model.')
    print(f'Successfully exported ONNX model: {output_file}')
    if verify:
        onnx_model = onnx.load(output_file)
        onnx.checker.check_model(onnx_model)
        onnx_model = ONNXRuntimeDetector(output_file, model.CLASSES, 0)
        if dynamic_export:
            h, w = [int(_ * 1.5 // 32 * 32) for _ in input_shape[2:]]
            h, w = (min(1344, h), min(1344, w))
            input_config['input_shape'] = (1, 3, h, w)
        if test_img is None:
            input_config['input_path'] = input_img
        one_img, one_meta = preprocess_example_input(input_config)
        img_list, img_meta_list = ([one_img], [[one_meta]])
        with torch.no_grad():
            pytorch_results = model(img_list, img_metas=img_meta_list, return_loss=False, rescale=True)[0]
        img_list = [_.cuda().contiguous() for _ in img_list]
        if dynamic_export:
            img_list = img_list + [_.flip(-1).contiguous() for _ in img_list]
            img_meta_list = img_meta_list * 2
        onnx_results = onnx_model(img_list, img_metas=img_meta_list, return_loss=False)[0]
        score_thr = 0.3
        if show:
            out_file_ort, out_file_pt = (None, None)
        else:
            out_file_ort, out_file_pt = ('show-ort.png', 'show-pt.png')
        show_img = one_meta['show_img']
        model.show_result(show_img, pytorch_results, score_thr=score_thr, show=True, win_name='PyTorch', out_file=out_file_pt)
        onnx_model.show_result(show_img, onnx_results, score_thr=score_thr, show=True, win_name='ONNXRuntime', out_file=out_file_ort)
        if model.with_mask:
            compare_pairs = list(zip(onnx_results, pytorch_results))
        else:
            compare_pairs = [(onnx_results, pytorch_results)]
        err_msg = 'The numerical values are different between Pytorch' + ' and ONNX, but it does not necessarily mean the' + ' exported ONNX model is problematic.'
        for onnx_res, pytorch_res in compare_pairs:
            for o_res, p_res in zip(onnx_res, pytorch_res):
                np.testing.assert_allclose(o_res, p_res, rtol=0.001, atol=1e-05, err_msg=err_msg)
        print('The numerical values are the same between Pytorch and ONNX')

def parse_result(input, model_class):
    bbox = []
    label = []
    score = []
    for anchor in input:
        bbox.append(anchor['bbox'])
        label.append(model_class.index(anchor['class_name']))
        score.append([anchor['score']])
    bboxes = np.append(bbox, score, axis=1)
    labels = np.array(label)
    result = bbox2result(bboxes, labels, len(model_class))
    return result

def main(args):
    model = init_detector(args.config, args.checkpoint, device=args.device)
    model_result = inference_detector(model, args.img)
    for i, anchor_set in enumerate(model_result):
        anchor_set = anchor_set[anchor_set[:, 4] >= 0.5]
        model_result[i] = anchor_set
    show_result_pyplot(model, args.img, model_result, score_thr=args.score_thr, title='pytorch_result')
    url = 'http://' + args.inference_addr + '/predictions/' + args.model_name
    with open(args.img, 'rb') as image:
        response = requests.post(url, image)
    server_result = parse_result(response.json(), model.CLASSES)
    show_result_pyplot(model, args.img, server_result, score_thr=args.score_thr, title='server_result')
    for i in range(len(model.CLASSES)):
        assert np.allclose(model_result[i], server_result[i])

def onnx2tensorrt(onnx_file, trt_file, input_config, verify=False, show=False, workspace_size=1, verbose=False):
    import tensorrt as trt
    onnx_model = onnx.load(onnx_file)
    max_shape = input_config['max_shape']
    min_shape = input_config['min_shape']
    opt_shape = input_config['opt_shape']
    fp16_mode = False
    opt_shape_dict = {'input': [min_shape, opt_shape, max_shape]}
    max_workspace_size = get_GiB(workspace_size)
    trt_engine = onnx2trt(onnx_model, opt_shape_dict, log_level=trt.Logger.VERBOSE if verbose else trt.Logger.ERROR, fp16_mode=fp16_mode, max_workspace_size=max_workspace_size)
    save_dir, _ = osp.split(trt_file)
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    save_trt_engine(trt_engine, trt_file)
    print(f'Successfully created TensorRT engine: {trt_file}')
    if verify:
        one_img, one_meta = preprocess_example_input(input_config)
        img_list, img_meta_list = ([one_img], [[one_meta]])
        img_list = [_.cuda().contiguous() for _ in img_list]
        onnx_model = ONNXRuntimeDetector(onnx_file, CLASSES, device_id=0)
        trt_model = TensorRTDetector(trt_file, CLASSES, device_id=0)
        with torch.no_grad():
            onnx_results = onnx_model(img_list, img_metas=img_meta_list, return_loss=False)[0]
            trt_results = trt_model(img_list, img_metas=img_meta_list, return_loss=False)[0]
        if show:
            out_file_ort, out_file_trt = (None, None)
        else:
            out_file_ort, out_file_trt = ('show-ort.png', 'show-trt.png')
        show_img = one_meta['show_img']
        score_thr = 0.3
        onnx_model.show_result(show_img, onnx_results, score_thr=score_thr, show=True, win_name='ONNXRuntime', out_file=out_file_ort)
        trt_model.show_result(show_img, trt_results, score_thr=score_thr, show=True, win_name='TensorRT', out_file=out_file_trt)
        with_mask = trt_model.with_masks
        if with_mask:
            compare_pairs = list(zip(onnx_results, trt_results))
        else:
            compare_pairs = [(onnx_results, trt_results)]
        err_msg = 'The numerical values are different between Pytorch' + ' and ONNX, but it does not necessarily mean the' + ' exported ONNX model is problematic.'
        for onnx_res, pytorch_res in compare_pairs:
            for o_res, p_res in zip(onnx_res, pytorch_res):
                np.testing.assert_allclose(o_res, p_res, rtol=0.001, atol=1e-05, err_msg=err_msg)
        print('The numerical values are the same between Pytorch and ONNX')

def collect_annotations(files, nproc=1):
    print('Loading annotation images')
    if nproc > 1:
        images = mmcv.track_parallel_progress(load_img_info, files, nproc=nproc)
    else:
        images = mmcv.track_progress(load_img_info, files)
    return images

def main():
    args = parse_args()
    cityscapes_path = args.cityscapes_path
    out_dir = args.out_dir if args.out_dir else cityscapes_path
    mmcv.mkdir_or_exist(out_dir)
    img_dir = osp.join(cityscapes_path, args.img_dir)
    gt_dir = osp.join(cityscapes_path, args.gt_dir)
    set_name = dict(train='instancesonly_filtered_gtFine_train.json', val='instancesonly_filtered_gtFine_val.json', test='instancesonly_filtered_gtFine_test.json')
    for split, json_name in set_name.items():
        print(f'Converting {split} into {json_name}')
        with mmcv.Timer(print_tmpl='It took {}s to convert Cityscapes annotation'):
            files = collect_files(osp.join(img_dir, split), osp.join(gt_dir, split))
            image_infos = collect_annotations(files, nproc=args.nproc)
            cvt_annotations(image_infos, osp.join(out_dir, json_name))

def parse_xml(args):
    xml_path, img_path = args
    tree = ET.parse(xml_path)
    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)
    bboxes = []
    labels = []
    bboxes_ignore = []
    labels_ignore = []
    for obj in root.findall('object'):
        name = obj.find('name').text
        label = label_ids[name]
        difficult = int(obj.find('difficult').text)
        bnd_box = obj.find('bndbox')
        bbox = [int(bnd_box.find('xmin').text), int(bnd_box.find('ymin').text), int(bnd_box.find('xmax').text), int(bnd_box.find('ymax').text)]
        if difficult:
            bboxes_ignore.append(bbox)
            labels_ignore.append(label)
        else:
            bboxes.append(bbox)
            labels.append(label)
    if not bboxes:
        bboxes = np.zeros((0, 4))
        labels = np.zeros((0,))
    else:
        bboxes = np.array(bboxes, ndmin=2) - 1
        labels = np.array(labels)
    if not bboxes_ignore:
        bboxes_ignore = np.zeros((0, 4))
        labels_ignore = np.zeros((0,))
    else:
        bboxes_ignore = np.array(bboxes_ignore, ndmin=2) - 1
        labels_ignore = np.array(labels_ignore)
    annotation = {'filename': img_path, 'width': w, 'height': h, 'ann': {'bboxes': bboxes.astype(np.float32), 'labels': labels.astype(np.int64), 'bboxes_ignore': bboxes_ignore.astype(np.float32), 'labels_ignore': labels_ignore.astype(np.int64)}}
    return annotation

def cvt_to_coco_json(annotations):
    image_id = 0
    annotation_id = 0
    coco = dict()
    coco['images'] = []
    coco['type'] = 'instance'
    coco['categories'] = []
    coco['annotations'] = []
    image_set = set()

    def addAnnItem(annotation_id, image_id, category_id, bbox, difficult_flag):
        annotation_item = dict()
        annotation_item['segmentation'] = []
        seg = []
        seg.append(int(bbox[0]))
        seg.append(int(bbox[1]))
        seg.append(int(bbox[0]))
        seg.append(int(bbox[3]))
        seg.append(int(bbox[2]))
        seg.append(int(bbox[3]))
        seg.append(int(bbox[2]))
        seg.append(int(bbox[1]))
        annotation_item['segmentation'].append(seg)
        xywh = np.array([bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]])
        annotation_item['area'] = int(xywh[2] * xywh[3])
        if difficult_flag == 1:
            annotation_item['ignore'] = 0
            annotation_item['iscrowd'] = 1
        else:
            annotation_item['ignore'] = 0
            annotation_item['iscrowd'] = 0
        annotation_item['image_id'] = int(image_id)
        annotation_item['bbox'] = xywh.astype(int).tolist()
        annotation_item['category_id'] = int(category_id)
        annotation_item['id'] = int(annotation_id)
        coco['annotations'].append(annotation_item)
        return annotation_id + 1
    for category_id, name in enumerate(voc_classes()):
        category_item = dict()
        category_item['supercategory'] = str('none')
        category_item['id'] = int(category_id)
        category_item['name'] = str(name)
        coco['categories'].append(category_item)
    for ann_dict in annotations:
        file_name = ann_dict['filename']
        ann = ann_dict['ann']
        assert file_name not in image_set
        image_item = dict()
        image_item['id'] = int(image_id)
        image_item['file_name'] = str(file_name)
        image_item['height'] = int(ann_dict['height'])
        image_item['width'] = int(ann_dict['width'])
        coco['images'].append(image_item)
        image_set.add(file_name)
        bboxes = ann['bboxes'][:, :4]
        labels = ann['labels']
        for bbox_id in range(len(bboxes)):
            bbox = bboxes[bbox_id]
            label = labels[bbox_id]
            annotation_id = addAnnItem(annotation_id, image_id, label, bbox, difficult_flag=0)
        bboxes_ignore = ann['bboxes_ignore'][:, :4]
        labels_ignore = ann['labels_ignore']
        for bbox_id in range(len(bboxes_ignore)):
            bbox = bboxes_ignore[bbox_id]
            label = labels_ignore[bbox_id]
            annotation_id = addAnnItem(annotation_id, image_id, label, bbox, difficult_flag=1)
        image_id += 1
    return coco

def main():
    args = parse_args()
    devkit_path = args.devkit_path
    out_dir = args.out_dir if args.out_dir else devkit_path
    mmcv.mkdir_or_exist(out_dir)
    years = []
    if osp.isdir(osp.join(devkit_path, 'VOC2007')):
        years.append('2007')
    if osp.isdir(osp.join(devkit_path, 'VOC2012')):
        years.append('2012')
    if '2007' in years and '2012' in years:
        years.append(['2007', '2012'])
    if not years:
        raise IOError(f'The devkit path {devkit_path} contains neither "VOC2007" nor "VOC2012" subfolder')
    out_fmt = f'.{args.out_format}'
    if args.out_format == 'coco':
        out_fmt = '.json'
    for year in years:
        if year == '2007':
            prefix = 'voc07'
        elif year == '2012':
            prefix = 'voc12'
        elif year == ['2007', '2012']:
            prefix = 'voc0712'
        for split in ['train', 'val', 'trainval']:
            dataset_name = prefix + '_' + split
            print(f'processing {dataset_name} ...')
            cvt_annotations(devkit_path, year, split, osp.join(out_dir, dataset_name + out_fmt))
        if not isinstance(year, list):
            dataset_name = prefix + '_test'
            print(f'processing {dataset_name} ...')
            cvt_annotations(devkit_path, year, 'test', osp.join(out_dir, dataset_name + out_fmt))
    print('Done!')

def convert_conv_fc(blobs, state_dict, caffe_name, torch_name, converted_names):
    state_dict[torch_name + '.weight'] = torch.from_numpy(blobs[caffe_name + '_w'])
    converted_names.add(caffe_name + '_w')
    if caffe_name + '_b' in blobs:
        state_dict[torch_name + '.bias'] = torch.from_numpy(blobs[caffe_name + '_b'])
        converted_names.add(caffe_name + '_b')

def convert(src, dst, depth):
    """Convert keys in detectron pretrained ResNet models to pytorch style."""
    if depth not in arch_settings:
        raise ValueError('Only support ResNet-50 and ResNet-101 currently')
    block_nums = arch_settings[depth]
    caffe_model = mmcv.load(src, encoding='latin1')
    blobs = caffe_model['blobs'] if 'blobs' in caffe_model else caffe_model
    state_dict = OrderedDict()
    converted_names = set()
    convert_conv_fc(blobs, state_dict, 'conv1', 'conv1', converted_names)
    convert_bn(blobs, state_dict, 'res_conv1_bn', 'bn1', converted_names)
    for i in range(1, len(block_nums) + 1):
        for j in range(block_nums[i - 1]):
            if j == 0:
                convert_conv_fc(blobs, state_dict, f'res{i + 1}_{j}_branch1', f'layer{i}.{j}.downsample.0', converted_names)
                convert_bn(blobs, state_dict, f'res{i + 1}_{j}_branch1_bn', f'layer{i}.{j}.downsample.1', converted_names)
            for k, letter in enumerate(['a', 'b', 'c']):
                convert_conv_fc(blobs, state_dict, f'res{i + 1}_{j}_branch2{letter}', f'layer{i}.{j}.conv{k + 1}', converted_names)
                convert_bn(blobs, state_dict, f'res{i + 1}_{j}_branch2{letter}_bn', f'layer{i}.{j}.bn{k + 1}', converted_names)
    for key in blobs:
        if key not in converted_names:
            print(f'Not Convert: {key}')
    checkpoint = dict()
    checkpoint['state_dict'] = state_dict
    torch.save(checkpoint, dst)

def parse_config(config_strings):
    temp_file = tempfile.NamedTemporaryFile()
    config_path = f'{temp_file.name}.py'
    with open(config_path, 'w') as f:
        f.write(config_strings)
    config = Config.fromfile(config_path)
    is_two_stage = True
    is_ssd = False
    is_retina = False
    reg_cls_agnostic = False
    if 'rpn_head' not in config.model:
        is_two_stage = False
        if config.model.bbox_head.type == 'SSDHead':
            is_ssd = True
        elif config.model.bbox_head.type == 'RetinaHead':
            is_retina = True
    elif isinstance(config.model['bbox_head'], list):
        reg_cls_agnostic = True
    elif 'reg_class_agnostic' in config.model.bbox_head:
        reg_cls_agnostic = config.model.bbox_head.reg_class_agnostic
    temp_file.close()
    return (is_two_stage, is_ssd, is_retina, reg_cls_agnostic)

def convert(in_file, out_file, num_classes):
    """Convert keys in checkpoints.

    There can be some breaking changes during the development of mmdetection,
    and this tool is used for upgrading checkpoints trained with old versions
    to the latest one.
    """
    checkpoint = torch.load(in_file)
    in_state_dict = checkpoint.pop('state_dict')
    out_state_dict = OrderedDict()
    meta_info = checkpoint['meta']
    is_two_stage, is_ssd, is_retina, reg_cls_agnostic = parse_config('#' + meta_info['config'])
    if meta_info['mmdet_version'] <= '0.5.3' and is_retina:
        upgrade_retina = True
    else:
        upgrade_retina = False
    if meta_info['mmdet_version'] < '2.5.0':
        upgrade_rpn = True
    else:
        upgrade_rpn = False
    for key, val in in_state_dict.items():
        new_key = key
        new_val = val
        if is_two_stage and is_head(key):
            new_key = 'roi_head.{}'.format(key)
        if upgrade_rpn:
            m = re.search('(conv_cls|retina_cls|rpn_cls|fc_cls|fcos_cls|fovea_cls).(weight|bias)', new_key)
        else:
            m = re.search('(conv_cls|retina_cls|fc_cls|fcos_cls|fovea_cls).(weight|bias)', new_key)
        if m is not None:
            print(f'reorder cls channels of {new_key}')
            new_val = reorder_cls_channel(val, num_classes)
        if upgrade_rpn:
            m = re.search('(fc_reg).(weight|bias)', new_key)
        else:
            m = re.search('(fc_reg|rpn_reg).(weight|bias)', new_key)
        if m is not None and (not reg_cls_agnostic):
            print(f'truncate regression channels of {new_key}')
            new_val = truncate_reg_channel(val, num_classes)
        m = re.search('(conv_logits).(weight|bias)', new_key)
        if m is not None:
            print(f'truncate mask prediction channels of {new_key}')
            new_val = truncate_cls_channel(val, num_classes)
        m = re.search('(cls_convs|reg_convs).\\d.(weight|bias)', key)
        if m is not None and upgrade_retina:
            param = m.groups()[1]
            new_key = key.replace(param, f'conv.{param}')
            out_state_dict[new_key] = val
            print(f'rename the name of {key} to {new_key}')
            continue
        m = re.search('(cls_convs).\\d.(weight|bias)', key)
        if m is not None and is_ssd:
            print(f'reorder cls channels of {new_key}')
            new_val = reorder_cls_channel(val, num_classes)
        out_state_dict[new_key] = new_val
    checkpoint['state_dict'] = out_state_dict
    torch.save(checkpoint, out_file)

def process_checkpoint(in_file, out_file):
    checkpoint = torch.load(in_file, map_location='cpu')
    if 'optimizer' in checkpoint:
        del checkpoint['optimizer']
    if torch.__version__ >= '1.6':
        torch.save(checkpoint, out_file, _use_new_zipfile_serialization=False)
    else:
        torch.save(checkpoint, out_file)
    sha = subprocess.check_output(['sha256sum', out_file]).decode()
    if out_file.endswith('.pth'):
        out_file_name = out_file[:-4]
    else:
        out_file_name = out_file
    final_file = out_file_name + f'-{sha[:8]}.pth'
    subprocess.Popen(['mv', out_file, final_file])

def parse_config(config_strings):
    temp_file = tempfile.NamedTemporaryFile()
    config_path = f'{temp_file.name}.py'
    with open(config_path, 'w') as f:
        f.write(config_strings)
    config = Config.fromfile(config_path)
    if config.model.bbox_head.type != 'SSDHead':
        raise AssertionError('This is not a SSD model.')

def convert(in_file, out_file):
    checkpoint = torch.load(in_file)
    in_state_dict = checkpoint.pop('state_dict')
    out_state_dict = OrderedDict()
    meta_info = checkpoint['meta']
    parse_config('#' + meta_info['config'])
    for key, value in in_state_dict.items():
        if 'extra' in key:
            layer_idx = int(key.split('.')[2])
            new_key = 'neck.extra_layers.{}.{}.conv.'.format(layer_idx // 2, layer_idx % 2) + key.split('.')[-1]
        elif 'l2_norm' in key:
            new_key = 'neck.l2_norm.weight'
        elif 'bbox_head' in key:
            new_key = key[:21] + '.0' + key[21:]
        else:
            new_key = key
        out_state_dict[new_key] = value
    checkpoint['state_dict'] = out_state_dict
    if torch.__version__ >= '1.6':
        torch.save(checkpoint, out_file, _use_new_zipfile_serialization=False)
    else:
        torch.save(checkpoint, out_file)

def moco_convert(src, dst):
    """Convert keys in pycls pretrained moco models to mmdet style."""
    moco_model = torch.load(src)
    blobs = moco_model['state_dict']
    state_dict = OrderedDict()
    for k, v in blobs.items():
        if not k.startswith('module.encoder_q.'):
            continue
        old_k = k
        k = k.replace('module.encoder_q.', '')
        state_dict[k] = v
        print(old_k, '->', k)
    checkpoint = dict()
    checkpoint['state_dict'] = state_dict
    torch.save(checkpoint, dst)

def convert_stem(model_key, model_weight, state_dict, converted_names):
    new_key = model_key.replace('stem.conv', 'conv1')
    new_key = new_key.replace('stem.bn', 'bn1')
    state_dict[new_key] = model_weight
    converted_names.add(model_key)
    print(f'Convert {model_key} to {new_key}')

def convert_head(model_key, model_weight, state_dict, converted_names):
    new_key = model_key.replace('head.fc', 'fc')
    state_dict[new_key] = model_weight
    converted_names.add(model_key)
    print(f'Convert {model_key} to {new_key}')

def convert_reslayer(model_key, model_weight, state_dict, converted_names):
    split_keys = model_key.split('.')
    layer, block, module = split_keys[:3]
    block_id = int(block[1:])
    layer_name = f'layer{int(layer[1:])}'
    block_name = f'{block_id - 1}'
    if block_id == 1 and module == 'bn':
        new_key = f'{layer_name}.{block_name}.downsample.1.{split_keys[-1]}'
    elif block_id == 1 and module == 'proj':
        new_key = f'{layer_name}.{block_name}.downsample.0.{split_keys[-1]}'
    elif module == 'f':
        if split_keys[3] == 'a_bn':
            module_name = 'bn1'
        elif split_keys[3] == 'b_bn':
            module_name = 'bn2'
        elif split_keys[3] == 'c_bn':
            module_name = 'bn3'
        elif split_keys[3] == 'a':
            module_name = 'conv1'
        elif split_keys[3] == 'b':
            module_name = 'conv2'
        elif split_keys[3] == 'c':
            module_name = 'conv3'
        new_key = f'{layer_name}.{block_name}.{module_name}.{split_keys[-1]}'
    else:
        raise ValueError(f'Unsupported conversion of key {model_key}')
    print(f'Convert {model_key} to {new_key}')
    state_dict[new_key] = model_weight
    converted_names.add(model_key)

def convert(src, dst):
    """Convert keys in pycls pretrained RegNet models to mmdet style."""
    regnet_model = torch.load(src)
    blobs = regnet_model['model_state']
    state_dict = OrderedDict()
    converted_names = set()
    for key, weight in blobs.items():
        if 'stem' in key:
            convert_stem(key, weight, state_dict, converted_names)
        elif 'head' in key:
            convert_head(key, weight, state_dict, converted_names)
        elif key.startswith('s'):
            convert_reslayer(key, weight, state_dict, converted_names)
    for key in blobs:
        if key not in converted_names:
            print(f'not converted: {key}')
    checkpoint = dict()
    checkpoint['state_dict'] = state_dict
    torch.save(checkpoint, dst)

def main():
    args = parse_args()
    data_root = args.data_root
    val_info = mmcv.load(osp.join(data_root, 'panoptic_val2017.json'))
    test_old_info = mmcv.load(osp.join(data_root, 'image_info_test-dev2017.json'))
    test_info = test_old_info
    test_info.update({'categories': val_info['categories']})
    mmcv.dump(test_info, osp.join(data_root, 'panoptic_image_info_test-dev2017.json'))

def get_metas_from_txt_style_ann_file(ann_file):
    with open(ann_file) as f:
        lines = f.readlines()
    i = 0
    data_infos = []
    while i < len(lines):
        filename = lines[i].rstrip()
        data_infos.append(dict(filename=filename))
        skip_lines = int(lines[i + 2]) + 3
        i += skip_lines
    return data_infos

def main():
    args = parse_args()
    assert args.out.endswith('pkl'), 'The output file name must be pkl suffix'
    cfg = Config.fromfile(args.config)
    ann_file = cfg.data.test.ann_file
    img_prefix = cfg.data.test.img_prefix
    print(f'{'-' * 5} Start Processing {'-' * 5}')
    if ann_file.endswith('csv'):
        data_infos = get_metas_from_csv_style_ann_file(ann_file)
    elif ann_file.endswith('txt'):
        data_infos = get_metas_from_txt_style_ann_file(ann_file)
    else:
        shuffix = ann_file.split('.')[-1]
        raise NotImplementedError(f'File name must be csv or txt suffix but get {shuffix}')
    print(f'Successfully load annotation file from {ann_file}')
    print(f'Processing {len(data_infos)} images...')
    pool = Pool(args.nproc)
    image_metas = pool.starmap(get_image_metas, zip(data_infos, [img_prefix for _ in range(len(data_infos))]))
    pool.close()
    root_path = cfg.data.test.ann_file.rsplit('/', 1)[0]
    save_path = osp.join(root_path, args.out)
    mmcv.dump(image_metas, save_path)
    print(f'Image meta file save to: {save_path}')

def download_one(url, dir):
    f = dir / Path(url).name
    if Path(url).is_file():
        Path(url).rename(f)
    elif not f.exists():
        print('Downloading {} to {}'.format(url, f))
        torch.hub.download_url_to_file(url, f, progress=True)
    if unzip and f.suffix in ('.zip', '.tar'):
        print('Unzipping {}'.format(f.name))
        if f.suffix == '.zip':
            ZipFile(f).extractall(path=dir)
        elif f.suffix == '.tar':
            TarFile(f).extractall(path=dir)
        if delete:
            f.unlink()
            print('Delete {}'.format(f))

def download(url, dir, unzip=True, delete=False, threads=1):

    def download_one(url, dir):
        f = dir / Path(url).name
        if Path(url).is_file():
            Path(url).rename(f)
        elif not f.exists():
            print('Downloading {} to {}'.format(url, f))
            torch.hub.download_url_to_file(url, f, progress=True)
        if unzip and f.suffix in ('.zip', '.tar'):
            print('Unzipping {}'.format(f.name))
            if f.suffix == '.zip':
                ZipFile(f).extractall(path=dir)
            elif f.suffix == '.tar':
                TarFile(f).extractall(path=dir)
            if delete:
                f.unlink()
                print('Delete {}'.format(f))
    dir = Path(dir)
    if threads > 1:
        pool = ThreadPool(threads)
        pool.imap(lambda x: download_one(*x), zip(url, repeat(dir)))
        pool.close()
        pool.join()
    else:
        for u in [url] if isinstance(url, (str, Path)) else url:
            download_one(u, dir)

def main():
    args = parse_args()
    path = Path(args.save_dir)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    data2url = dict(coco2017=['http://images.cocodataset.org/zips/train2017.zip', 'http://images.cocodataset.org/zips/val2017.zip', 'http://images.cocodataset.org/zips/test2017.zip', 'http://images.cocodataset.org/annotations/' + 'annotations_trainval2017.zip'], lvis=['https://s3-us-west-2.amazonaws.com/dl.fbaipublicfiles.com/LVIS/lvis_v1_train.json.zip', 'https://s3-us-west-2.amazonaws.com/dl.fbaipublicfiles.com/LVIS/lvis_v1_train.json.zip'], voc2007=['http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCtrainval_06-Nov-2007.tar', 'http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCtest_06-Nov-2007.tar', 'http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCdevkit_08-Jun-2007.tar'])
    url = data2url.get(args.dataset_name, None)
    if url is None:
        print('Only support COCO, VOC, and LVIS now!')
        return
    download(url, dir=path, unzip=args.unzip, delete=args.delete, threads=args.threads)

def save_anns(name, images, annotations):
    sub_anns = dict()
    sub_anns['images'] = images
    sub_anns['annotations'] = annotations
    sub_anns['licenses'] = anns['licenses']
    sub_anns['categories'] = anns['categories']
    sub_anns['info'] = anns['info']
    mmcv.mkdir_or_exist(out_dir)
    mmcv.dump(sub_anns, f'{out_dir}/{name}.json')

def split_coco(data_root, out_dir, percent, fold):
    """Split COCO data for Semi-supervised object detection.

    Args:
        data_root (str): The data root of coco dataset.
        out_dir (str): The output directory of coco semi-supervised
            annotations.
        percent (float): The percentage of labeled data in the training set.
        fold (int): The fold of dataset and set as random seed for data split.
    """

    def save_anns(name, images, annotations):
        sub_anns = dict()
        sub_anns['images'] = images
        sub_anns['annotations'] = annotations
        sub_anns['licenses'] = anns['licenses']
        sub_anns['categories'] = anns['categories']
        sub_anns['info'] = anns['info']
        mmcv.mkdir_or_exist(out_dir)
        mmcv.dump(sub_anns, f'{out_dir}/{name}.json')
    np.random.seed(fold)
    ann_file = osp.join(data_root, 'annotations/instances_train2017.json')
    anns = mmcv.load(ann_file)
    image_list = anns['images']
    labeled_total = int(percent / 100.0 * len(image_list))
    labeled_inds = set(np.random.choice(range(len(image_list)), size=labeled_total))
    labeled_ids, labeled_images, unlabeled_images = ([], [], [])
    for i in range(len(image_list)):
        if i in labeled_inds:
            labeled_images.append(image_list[i])
            labeled_ids.append(image_list[i]['id'])
        else:
            unlabeled_images.append(image_list[i])
    labeled_ids = set(labeled_ids)
    labeled_annotations, unlabeled_annotations = ([], [])
    for ann in anns['annotations']:
        if ann['image_id'] in labeled_ids:
            labeled_annotations.append(ann)
        else:
            unlabeled_annotations.append(ann)
    labeled_name = f'instances_train2017.{fold}@{percent}'
    unlabeled_name = f'instances_train2017.{fold}@{percent}-unlabeled'
    save_anns(labeled_name, labeled_images, labeled_annotations)
    save_anns(unlabeled_name, unlabeled_images, unlabeled_annotations)

def _print(result, ap=1, iouThr=None, areaRng='all', maxDets=100):
    titleStr = 'Average Precision' if ap == 1 else 'Average Recall'
    typeStr = '(AP)' if ap == 1 else '(AR)'
    iouStr = '0.50:0.95' if iouThr is None else f'{iouThr:0.2f}'
    iStr = f' {titleStr:<18} {typeStr} @[ IoU={iouStr:<9} | '
    iStr += f'area={areaRng:>6s} | maxDets={maxDets:>3d} ] = {result:0.3f}'
    print(iStr)

def get_coco_style_results(filename, task='bbox', metric=None, prints='mPC', aggregate='benchmark'):
    assert aggregate in ['benchmark', 'all']
    if prints == 'all':
        prints = ['P', 'mPC', 'rPC']
    elif isinstance(prints, str):
        prints = [prints]
    for p in prints:
        assert p in ['P', 'mPC', 'rPC']
    if metric is None:
        metrics = ['AP', 'AP50', 'AP75', 'APs', 'APm', 'APl', 'AR1', 'AR10', 'AR100', 'ARs', 'ARm', 'ARl']
    elif isinstance(metric, list):
        metrics = metric
    else:
        metrics = [metric]
    for metric_name in metrics:
        assert metric_name in ['AP', 'AP50', 'AP75', 'APs', 'APm', 'APl', 'AR1', 'AR10', 'AR100', 'ARs', 'ARm', 'ARl']
    eval_output = mmcv.load(filename)
    num_distortions = len(list(eval_output.keys()))
    results = np.zeros((num_distortions, 6, len(metrics)), dtype='float32')
    for corr_i, distortion in enumerate(eval_output):
        for severity in eval_output[distortion]:
            for metric_j, metric_name in enumerate(metrics):
                mAP = eval_output[distortion][severity][task][metric_name]
                results[corr_i, severity, metric_j] = mAP
    P = results[0, 0, :]
    if aggregate == 'benchmark':
        mPC = np.mean(results[:15, 1:, :], axis=(0, 1))
    else:
        mPC = np.mean(results[:, 1:, :], axis=(0, 1))
    rPC = mPC / P
    print(f'\nmodel: {osp.basename(filename)}')
    if metric is None:
        if 'P' in prints:
            print(f'Performance on Clean Data [P] ({task})')
            print_coco_results(P)
        if 'mPC' in prints:
            print(f'Mean Performance under Corruption [mPC] ({task})')
            print_coco_results(mPC)
        if 'rPC' in prints:
            print(f'Relative Performance under Corruption [rPC] ({task})')
            print_coco_results(rPC)
    else:
        if 'P' in prints:
            print(f'Performance on Clean Data [P] ({task})')
            for metric_i, metric_name in enumerate(metrics):
                print(f'{metric_name:5} =  {P[metric_i]:0.3f}')
        if 'mPC' in prints:
            print(f'Mean Performance under Corruption [mPC] ({task})')
            for metric_i, metric_name in enumerate(metrics):
                print(f'{metric_name:5} =  {mPC[metric_i]:0.3f}')
        if 'rPC' in prints:
            print(f'Relative Performance under Corruption [rPC] ({task})')
            for metric_i, metric_name in enumerate(metrics):
                print(f'{metric_name:5} => {rPC[metric_i] * 100:0.1f} %')
    return results

def get_voc_style_results(filename, prints='mPC', aggregate='benchmark'):
    assert aggregate in ['benchmark', 'all']
    if prints == 'all':
        prints = ['P', 'mPC', 'rPC']
    elif isinstance(prints, str):
        prints = [prints]
    for p in prints:
        assert p in ['P', 'mPC', 'rPC']
    eval_output = mmcv.load(filename)
    num_distortions = len(list(eval_output.keys()))
    results = np.zeros((num_distortions, 6, 20), dtype='float32')
    for i, distortion in enumerate(eval_output):
        for severity in eval_output[distortion]:
            mAP = [eval_output[distortion][severity][j]['ap'] for j in range(len(eval_output[distortion][severity]))]
            results[i, severity, :] = mAP
    P = results[0, 0, :]
    if aggregate == 'benchmark':
        mPC = np.mean(results[:15, 1:, :], axis=(0, 1))
    else:
        mPC = np.mean(results[:, 1:, :], axis=(0, 1))
    rPC = mPC / P
    print(f'\nmodel: {osp.basename(filename)}')
    if 'P' in prints:
        print(f'Performance on Clean Data [P] in AP50 = {np.mean(P):0.3f}')
    if 'mPC' in prints:
        print(f'Mean Performance under Corruption [mPC] in AP50 = {np.mean(mPC):0.3f}')
    if 'rPC' in prints:
        print(f'Relative Performance under Corruption [rPC] in % = {np.mean(rPC) * 100:0.1f}')
    return np.mean(results, axis=2, keepdims=True)

def get_results(filename, dataset='coco', task='bbox', metric=None, prints='mPC', aggregate='benchmark'):
    assert dataset in ['coco', 'voc', 'cityscapes']
    if dataset in ['coco', 'cityscapes']:
        results = get_coco_style_results(filename, task=task, metric=metric, prints=prints, aggregate=aggregate)
    elif dataset == 'voc':
        if task != 'bbox':
            print('Only bbox analysis is supported for Pascal VOC')
            print('Will report bbox results\n')
        if metric not in [None, ['AP'], ['AP50']]:
            print('Only the AP50 metric is supported for Pascal VOC')
            print('Will report AP50 metric\n')
        results = get_voc_style_results(filename, prints=prints, aggregate=aggregate)
    return results

def get_distortions_from_file(filename):
    eval_output = mmcv.load(filename)
    return get_distortions_from_results(eval_output)

def get_distortions_from_results(eval_output):
    distortions = []
    for i, distortion in enumerate(eval_output):
        distortions.append(distortion.replace('_', ' '))
    return distortions

def calculate_confusion_matrix(dataset, results, score_thr=0, nms_iou_thr=None, tp_iou_thr=0.5):
    """Calculate the confusion matrix.

    Args:
        dataset (Dataset): Test or val dataset.
        results (list[ndarray]): A list of detection results in each image.
        score_thr (float|optional): Score threshold to filter bboxes.
            Default: 0.
        nms_iou_thr (float|optional): nms IoU threshold, the detection results
            have done nms in the detector, only applied when users want to
            change the nms IoU threshold. Default: None.
        tp_iou_thr (float|optional): IoU threshold to be considered as matched.
            Default: 0.5.
    """
    num_classes = len(dataset.CLASSES)
    confusion_matrix = np.zeros(shape=[num_classes + 1, num_classes + 1])
    assert len(dataset) == len(results)
    prog_bar = mmcv.ProgressBar(len(results))
    for idx, per_img_res in enumerate(results):
        if isinstance(per_img_res, tuple):
            res_bboxes, _ = per_img_res
        else:
            res_bboxes = per_img_res
        ann = dataset.get_ann_info(idx)
        gt_bboxes = ann['bboxes']
        labels = ann['labels']
        analyze_per_img_dets(confusion_matrix, gt_bboxes, labels, res_bboxes, score_thr, tp_iou_thr, nms_iou_thr)
        prog_bar.update()
    return confusion_matrix

def voc_eval_with_return(result_file, dataset, iou_thr=0.5, logger='print', only_ap=True):
    det_results = mmcv.load(result_file)
    annotations = [dataset.get_ann_info(i) for i in range(len(dataset))]
    if hasattr(dataset, 'year') and dataset.year == 2007:
        dataset_name = 'voc07'
    else:
        dataset_name = dataset.CLASSES
    mean_ap, eval_results = eval_map(det_results, annotations, scale_ranges=None, iou_thr=iou_thr, dataset=dataset_name, logger=logger)
    if only_ap:
        eval_results = [{'ap': eval_results[i]['ap']} for i in range(len(eval_results))]
    return (mean_ap, eval_results)

def bbox_map_eval(det_result, annotation, nproc=4):
    """Evaluate mAP of single image det result.

    Args:
        det_result (list[list]): [[cls1_det, cls2_det, ...], ...].
            The outer list indicates images, and the inner list indicates
            per-class detected bboxes.
        annotation (dict): Ground truth annotations where keys of
             annotations are:

            - bboxes: numpy array of shape (n, 4)
            - labels: numpy array of shape (n, )
            - bboxes_ignore (optional): numpy array of shape (k, 4)
            - labels_ignore (optional): numpy array of shape (k, )

        nproc (int): Processes used for computing mAP.
            Default: 4.

    Returns:
        float: mAP
    """
    if isinstance(det_result, tuple):
        bbox_det_result = [det_result[0]]
    else:
        bbox_det_result = [det_result]
    iou_thrs = np.linspace(0.5, 0.95, int(np.round((0.95 - 0.5) / 0.05)) + 1, endpoint=True)
    processes = []
    workers = Pool(processes=nproc)
    for thr in iou_thrs:
        p = workers.apply_async(eval_map, (bbox_det_result, [annotation]), {'iou_thr': thr, 'logger': 'silent', 'nproc': 1})
        processes.append(p)
    workers.close()
    workers.join()
    mean_aps = []
    for p in processes:
        mean_aps.append(p.get()[0])
    return sum(mean_aps) / len(mean_aps)

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

class BaseAnchorOptimizer:
    """Base class for anchor optimizer.

    Args:
        dataset (obj:`Dataset`): Dataset object.
        input_shape (list[int]): Input image shape of the model.
            Format in [width, height].
        logger (obj:`logging.Logger`): The logger for logging.
        device (str, optional): Device used for calculating.
            Default: 'cuda:0'
        out_dir (str, optional): Path to save anchor optimize result.
            Default: None
    """

    def __init__(self, dataset, input_shape, logger, device='cuda:0', out_dir=None):
        self.dataset = dataset
        self.input_shape = input_shape
        self.logger = logger
        self.device = device
        self.out_dir = out_dir
        bbox_whs, img_shapes = self.get_whs_and_shapes()
        ratios = img_shapes.max(1, keepdims=True) / np.array([input_shape])
        self.bbox_whs = bbox_whs / ratios

    def get_whs_and_shapes(self):
        """Get widths and heights of bboxes and shapes of images.

        Returns:
            tuple[np.ndarray]: Array of bbox shapes and array of image
            shapes with shape (num_bboxes, 2) in [width, height] format.
        """
        self.logger.info('Collecting bboxes from annotation...')
        bbox_whs = []
        img_shapes = []
        prog_bar = mmcv.ProgressBar(len(self.dataset))
        for idx in range(len(self.dataset)):
            ann = self.dataset.get_ann_info(idx)
            data_info = self.dataset.data_infos[idx]
            img_shape = np.array([data_info['width'], data_info['height']])
            gt_bboxes = ann['bboxes']
            for bbox in gt_bboxes:
                wh = bbox[2:4] - bbox[0:2]
                img_shapes.append(img_shape)
                bbox_whs.append(wh)
            prog_bar.update()
        print('\n')
        bbox_whs = np.array(bbox_whs)
        img_shapes = np.array(img_shapes)
        self.logger.info(f'Collected {bbox_whs.shape[0]} bboxes.')
        return (bbox_whs, img_shapes)

    def get_zero_center_bbox_tensor(self):
        """Get a tensor of bboxes centered at (0, 0).

        Returns:
            Tensor: Tensor of bboxes with shape (num_bboxes, 4)
            in [xmin, ymin, xmax, ymax] format.
        """
        whs = torch.from_numpy(self.bbox_whs).to(self.device, dtype=torch.float32)
        bboxes = bbox_cxcywh_to_xyxy(torch.cat([torch.zeros_like(whs), whs], dim=1))
        return bboxes

    def optimize(self):
        raise NotImplementedError

    def save_result(self, anchors, path=None):
        anchor_results = []
        for w, h in anchors:
            anchor_results.append([round(w), round(h)])
        self.logger.info(f'Anchor optimize result:{anchor_results}')
        if path:
            json_path = osp.join(path, 'anchor_optimize_result.json')
            mmcv.dump(anchor_results, json_path)
            self.logger.info(f'Result saved in {json_path}')

def get_whs_and_shapes(self):
    """Get widths and heights of bboxes and shapes of images.

        Returns:
            tuple[np.ndarray]: Array of bbox shapes and array of image
            shapes with shape (num_bboxes, 2) in [width, height] format.
        """
    self.logger.info('Collecting bboxes from annotation...')
    bbox_whs = []
    img_shapes = []
    prog_bar = mmcv.ProgressBar(len(self.dataset))
    for idx in range(len(self.dataset)):
        ann = self.dataset.get_ann_info(idx)
        data_info = self.dataset.data_infos[idx]
        img_shape = np.array([data_info['width'], data_info['height']])
        gt_bboxes = ann['bboxes']
        for bbox in gt_bboxes:
            wh = bbox[2:4] - bbox[0:2]
            img_shapes.append(img_shape)
            bbox_whs.append(wh)
        prog_bar.update()
    print('\n')
    bbox_whs = np.array(bbox_whs)
    img_shapes = np.array(img_shapes)
    self.logger.info(f'Collected {bbox_whs.shape[0]} bboxes.')
    return (bbox_whs, img_shapes)

def save_result(self, anchors, path=None):
    anchor_results = []
    for w, h in anchors:
        anchor_results.append([round(w), round(h)])
    self.logger.info(f'Anchor optimize result:{anchor_results}')
    if path:
        json_path = osp.join(path, 'anchor_optimize_result.json')
        mmcv.dump(anchor_results, json_path)
        self.logger.info(f'Result saved in {json_path}')

class YOLOKMeansAnchorOptimizer(BaseAnchorOptimizer):
    """YOLO anchor optimizer using k-means. Code refer to `AlexeyAB/darknet.
    <https://github.com/AlexeyAB/darknet/blob/master/src/detector.c>`_.

    Args:
        num_anchors (int) : Number of anchors.
        iters (int): Maximum iterations for k-means.
    """

    def __init__(self, num_anchors, iters, **kwargs):
        super(YOLOKMeansAnchorOptimizer, self).__init__(**kwargs)
        self.num_anchors = num_anchors
        self.iters = iters

    def optimize(self):
        anchors = self.kmeans_anchors()
        self.save_result(anchors, self.out_dir)

    def kmeans_anchors(self):
        self.logger.info(f'Start cluster {self.num_anchors} YOLO anchors with K-means...')
        bboxes = self.get_zero_center_bbox_tensor()
        cluster_center_idx = torch.randint(0, bboxes.shape[0], (self.num_anchors,)).to(self.device)
        assignments = torch.zeros((bboxes.shape[0],)).to(self.device)
        cluster_centers = bboxes[cluster_center_idx]
        if self.num_anchors == 1:
            cluster_centers = self.kmeans_maximization(bboxes, assignments, cluster_centers)
            anchors = bbox_xyxy_to_cxcywh(cluster_centers)[:, 2:].cpu().numpy()
            anchors = sorted(anchors, key=lambda x: x[0] * x[1])
            return anchors
        prog_bar = mmcv.ProgressBar(self.iters)
        for i in range(self.iters):
            converged, assignments = self.kmeans_expectation(bboxes, assignments, cluster_centers)
            if converged:
                self.logger.info(f'K-means process has converged at iter {i}.')
                break
            cluster_centers = self.kmeans_maximization(bboxes, assignments, cluster_centers)
            prog_bar.update()
        print('\n')
        avg_iou = bbox_overlaps(bboxes, cluster_centers).max(1)[0].mean().item()
        anchors = bbox_xyxy_to_cxcywh(cluster_centers)[:, 2:].cpu().numpy()
        anchors = sorted(anchors, key=lambda x: x[0] * x[1])
        self.logger.info(f'Anchor cluster finish. Average IOU: {avg_iou}')
        return anchors

    def kmeans_maximization(self, bboxes, assignments, centers):
        """Maximization part of EM algorithm(Expectation-Maximization)"""
        new_centers = torch.zeros_like(centers)
        for i in range(centers.shape[0]):
            mask = assignments == i
            if mask.sum():
                new_centers[i, :] = bboxes[mask].mean(0)
        return new_centers

    def kmeans_expectation(self, bboxes, assignments, centers):
        """Expectation part of EM algorithm(Expectation-Maximization)"""
        ious = bbox_overlaps(bboxes, centers)
        closest = ious.argmax(1)
        converged = (closest == assignments).all()
        return (converged, closest)

def optimize(self):
    anchors = self.kmeans_anchors()
    self.save_result(anchors, self.out_dir)

class YOLODEAnchorOptimizer(BaseAnchorOptimizer):
    """YOLO anchor optimizer using differential evolution algorithm.

    Args:
        num_anchors (int) : Number of anchors.
        iters (int): Maximum iterations for k-means.
        strategy (str): The differential evolution strategy to use.
            Should be one of:

                - 'best1bin'
                - 'best1exp'
                - 'rand1exp'
                - 'randtobest1exp'
                - 'currenttobest1exp'
                - 'best2exp'
                - 'rand2exp'
                - 'randtobest1bin'
                - 'currenttobest1bin'
                - 'best2bin'
                - 'rand2bin'
                - 'rand1bin'

            Default: 'best1bin'.
        population_size (int): Total population size of evolution algorithm.
            Default: 15.
        convergence_thr (float): Tolerance for convergence, the
            optimizing stops when ``np.std(pop) <= abs(convergence_thr)
            + convergence_thr * np.abs(np.mean(population_energies))``,
            respectively. Default: 0.0001.
        mutation (tuple[float]): Range of dithering randomly changes the
            mutation constant. Default: (0.5, 1).
        recombination (float): Recombination constant of crossover probability.
            Default: 0.7.
    """

    def __init__(self, num_anchors, iters, strategy='best1bin', population_size=15, convergence_thr=0.0001, mutation=(0.5, 1), recombination=0.7, **kwargs):
        super(YOLODEAnchorOptimizer, self).__init__(**kwargs)
        self.num_anchors = num_anchors
        self.iters = iters
        self.strategy = strategy
        self.population_size = population_size
        self.convergence_thr = convergence_thr
        self.mutation = mutation
        self.recombination = recombination

    def optimize(self):
        anchors = self.differential_evolution()
        self.save_result(anchors, self.out_dir)

    def differential_evolution(self):
        bboxes = self.get_zero_center_bbox_tensor()
        bounds = []
        for i in range(self.num_anchors):
            bounds.extend([(0, self.input_shape[0]), (0, self.input_shape[1])])
        result = differential_evolution(func=self.avg_iou_cost, bounds=bounds, args=(bboxes,), strategy=self.strategy, maxiter=self.iters, popsize=self.population_size, tol=self.convergence_thr, mutation=self.mutation, recombination=self.recombination, updating='immediate', disp=True)
        self.logger.info(f'Anchor evolution finish. Average IOU: {1 - result.fun}')
        anchors = [(w, h) for w, h in zip(result.x[::2], result.x[1::2])]
        anchors = sorted(anchors, key=lambda x: x[0] * x[1])
        return anchors

    @staticmethod
    def avg_iou_cost(anchor_params, bboxes):
        assert len(anchor_params) % 2 == 0
        anchor_whs = torch.tensor([[w, h] for w, h in zip(anchor_params[::2], anchor_params[1::2])]).to(bboxes.device, dtype=bboxes.dtype)
        anchor_boxes = bbox_cxcywh_to_xyxy(torch.cat([torch.zeros_like(anchor_whs), anchor_whs], dim=1))
        ious = bbox_overlaps(bboxes, anchor_boxes)
        max_ious, _ = ious.max(1)
        cost = 1 - max_ious.mean().item()
        return cost

def optimize(self):
    anchors = self.differential_evolution()
    self.save_result(anchors, self.out_dir)

def differential_evolution(self):
    bboxes = self.get_zero_center_bbox_tensor()
    bounds = []
    for i in range(self.num_anchors):
        bounds.extend([(0, self.input_shape[0]), (0, self.input_shape[1])])
    result = differential_evolution(func=self.avg_iou_cost, bounds=bounds, args=(bboxes,), strategy=self.strategy, maxiter=self.iters, popsize=self.population_size, tol=self.convergence_thr, mutation=self.mutation, recombination=self.recombination, updating='immediate', disp=True)
    self.logger.info(f'Anchor evolution finish. Average IOU: {1 - result.fun}')
    anchors = [(w, h) for w, h in zip(result.x[::2], result.x[1::2])]
    anchors = sorted(anchors, key=lambda x: x[0] * x[1])
    return anchors

def test_dense_heads_test_attr():
    """Tests inference methods such as simple_test and aug_test."""
    exceptions = ['FeatureAdaption']
    all_dense_heads = [m for m in dense_heads.__all__ if m not in exceptions]
    check_attributes = ['simple_test', 'aug_test', 'simple_test_bboxes', 'simple_test_rpn', 'aug_test_rpn']
    table_header = ['head name'] + check_attributes
    table_data = [table_header]
    not_found = {k: [] for k in check_attributes}
    for target_head_name in all_dense_heads:
        target_head = globals()[target_head_name]
        target_head_attributes = dir(target_head)
        check_results = [target_head_name]
        for check_attribute in check_attributes:
            found = check_attribute in target_head_attributes
            check_results.append(found)
            if not found:
                not_found[check_attribute].append(target_head_name)
        table_data.append(check_results)
    table = AsciiTable(table_data)
    print()
    print(table.table)
    assert len(not_found['simple_test']) == 0, f'simple_test not found in {not_found['simple_test']}'
    if len(not_found['aug_test']) != 0:
        warnings.warn(f'aug_test not found in {not_found['aug_test']}. Please implement it or raise NotImplementedError.')

def test_eval_map():
    det_results = [[det_bboxes, det_bboxes], [det_bboxes, det_bboxes]]
    labels = np.array([0, 1, 1])
    labels_ignore = np.array([0, 1])
    gt_info = {'bboxes': gt_bboxes, 'bboxes_ignore': gt_ignore, 'labels': labels, 'labels_ignore': labels_ignore}
    annotations = [gt_info, gt_info]
    mean_ap, eval_results = eval_map(det_results, annotations, use_legacy_coordinate=True)
    assert 0.291 < mean_ap < 0.293
    mean_ap, eval_results = eval_map(det_results, annotations, use_legacy_coordinate=False)
    assert 0.291 < mean_ap < 0.293
    det_results = [[det_bboxes, det_bboxes]]
    labels = np.array([0, 1, 1])
    labels_ignore = np.array([0, 1])
    gt_info = {'bboxes': gt_bboxes, 'bboxes_ignore': gt_ignore, 'labels': labels, 'labels_ignore': labels_ignore}
    annotations = [gt_info]
    mean_ap, eval_results = eval_map(det_results, annotations, use_legacy_coordinate=True)
    assert 0.291 < mean_ap < 0.293
    mean_ap, eval_results = eval_map(det_results, annotations, use_legacy_coordinate=False)
    assert 0.291 < mean_ap < 0.293

def test_ema_hook():
    """xdoctest -m tests/test_hooks.py test_ema_hook."""

    class DemoModel(nn.Module):

        def __init__(self):
            super().__init__()
            self.conv = nn.Conv2d(in_channels=1, out_channels=2, kernel_size=1, padding=1, bias=True)
            self.bn = nn.BatchNorm2d(2)
            self._init_weight()

        def _init_weight(self):
            constant_(self.conv.weight, 0)
            constant_(self.conv.bias, 0)
            constant_(self.bn.weight, 0)
            constant_(self.bn.bias, 0)

        def forward(self, x):
            return self.bn(self.conv(x)).sum()

        def train_step(self, x, optimizer, **kwargs):
            return dict(loss=self(x))

        def val_step(self, x, optimizer, **kwargs):
            return dict(loss=self(x))
    loader = DataLoader(torch.ones((1, 1, 1, 1)))
    runner = _build_demo_runner()
    demo_model = DemoModel()
    runner.model = demo_model
    ema_hook = ExpMomentumEMAHook(momentum=0.0002, total_iter=1, skip_buffers=True, interval=2, resume_from=None)
    checkpointhook = CheckpointHook(interval=1, by_epoch=True)
    runner.register_hook(ema_hook, priority='HIGHEST')
    runner.register_hook(checkpointhook)
    runner.run([loader, loader], [('train', 1), ('val', 1)])
    checkpoint = torch.load(f'{runner.work_dir}/epoch_1.pth')
    num_eam_params = 0
    for name, value in checkpoint['state_dict'].items():
        if 'ema' in name:
            num_eam_params += 1
            value.fill_(1)
    assert num_eam_params == 4
    torch.save(checkpoint, f'{runner.work_dir}/epoch_1.pth')
    work_dir = runner.work_dir
    resume_ema_hook = ExpMomentumEMAHook(momentum=0.5, total_iter=10, skip_buffers=True, interval=1, resume_from=f'{work_dir}/epoch_1.pth')
    runner = _build_demo_runner(max_epochs=2)
    runner.model = demo_model
    runner.register_hook(resume_ema_hook, priority='HIGHEST')
    checkpointhook = CheckpointHook(interval=1, by_epoch=True)
    runner.register_hook(checkpointhook)
    runner.run([loader, loader], [('train', 1), ('val', 1)])
    checkpoint = torch.load(f'{runner.work_dir}/epoch_2.pth')
    num_eam_params = 0
    desired_output = [0.9094, 0.9094]
    for name, value in checkpoint['state_dict'].items():
        if 'ema' in name:
            num_eam_params += 1
            assert value.sum() == 2
        elif 'weight' in name or 'bias' in name:
            np.allclose(value.data.cpu().numpy().reshape(-1), desired_output, 0.0001)
    assert num_eam_params == 4
    shutil.rmtree(runner.work_dir)
    shutil.rmtree(work_dir)

def _mock_virtual_memory():
    virtual_memory_type = namedtuple('virtual_memory', ['total', 'available', 'percent', 'used'])
    return virtual_memory_type(total=270109085696, available=250416816128, percent=7.3, used=17840881664)

def _mock_swap_memory():
    swap_memory_type = namedtuple('swap_memory', ['total', 'used', 'percent'])
    return swap_memory_type(total=8589930496, used=0, percent=0.0)

def callee_func():
    caller_name = get_caller_name()
    return caller_name

def check_optimizer_lr_wd(optimizer, gt_lr_wd):
    assert isinstance(optimizer, torch.optim.AdamW)
    assert optimizer.defaults['lr'] == base_lr
    assert optimizer.defaults['weight_decay'] == base_wd
    param_groups = optimizer.param_groups
    print(param_groups)
    assert len(param_groups) == len(gt_lr_wd)
    for i, param_dict in enumerate(param_groups):
        assert param_dict['weight_decay'] == gt_lr_wd[i]['weight_decay']
        assert param_dict['lr_scale'] == gt_lr_wd[i]['lr_scale']
        assert param_dict['lr_scale'] == param_dict['lr']

def get_ort_model_output(feat, onnx_io='tmp.onnx'):
    """Run the model in onnxruntime env.

    Args:
        feat (list[Tensor]): A list of tensors from torch.rand,
            each is a 4D-tensor.

    Returns:
        list[np.array]: onnxruntime infer result, each is a np.array
    """
    onnx_model = onnx.load(onnx_io)
    onnx.checker.check_model(onnx_model)
    session_options = ort.SessionOptions()
    if osp.exists(ort_custom_op_path):
        session_options.register_custom_ops_library(ort_custom_op_path)
    sess = ort.InferenceSession(onnx_io, session_options)
    if isinstance(feat, torch.Tensor):
        onnx_outputs = sess.run(None, {sess.get_inputs()[0].name: feat.numpy()})
    else:
        onnx_outputs = sess.run(None, {sess.get_inputs()[i].name: feat[i].numpy() for i in range(len(feat))})
    return onnx_outputs

def yolo_neck_config(test_step_name):
    """Config yolov3 Neck."""
    in_channels = [16, 8, 4]
    out_channels = [8, 4, 2]
    yolov3_neck_data = 'yolov3_neck.pkl'
    feats = mmcv.load(osp.join(data_path, yolov3_neck_data))
    if yolo_test_step_names[test_step_name] == 0:
        yolo_model = YOLOV3Neck(in_channels=in_channels, out_channels=out_channels, num_scales=3)
    return (yolo_model, feats)

class MaskRCNNDetector:

    def __init__(self, model_config, checkpoint=None, streamqueue_size=3, device='cuda:0'):
        self.streamqueue_size = streamqueue_size
        self.device = device
        self.model = init_detector(model_config, checkpoint=None, device=self.device)
        self.streamqueue = None

    async def init(self):
        self.streamqueue = asyncio.Queue()
        for _ in range(self.streamqueue_size):
            stream = torch.cuda.Stream(device=self.device)
            self.streamqueue.put_nowait(stream)
    if sys.version_info >= (3, 7):

        async def apredict(self, img):
            if isinstance(img, str):
                img = mmcv.imread(img)
            async with concurrent(self.streamqueue):
                result = await async_inference_detector(self.model, img)
            return result

def __init__(self, model_config, checkpoint=None, streamqueue_size=3, device='cuda:0'):
    self.streamqueue_size = streamqueue_size
    self.device = device
    self.model = init_detector(model_config, checkpoint=None, device=self.device)
    self.streamqueue = None

class EvalDataset(ExampleDataset):

    def evaluate(self, results, logger=None):
        mean_ap = self.eval_result[self.index]
        output = OrderedDict(mAP=mean_ap, index=self.index, score=mean_ap)
        self.index += 1
        return output

def evaluate(self, results, logger=None):
    mean_ap = self.eval_result[self.index]
    output = OrderedDict(mAP=mean_ap, index=self.index, score=mean_ap)
    self.index += 1
    return output

def _create_dummy_coco_json(json_name):
    image = {'id': 0, 'width': 640, 'height': 640, 'file_name': 'fake_name.jpg'}
    annotation_1 = {'id': 1, 'image_id': 0, 'category_id': 0, 'area': 400, 'bbox': [50, 60, 20, 20], 'iscrowd': 0}
    annotation_2 = {'id': 2, 'image_id': 0, 'category_id': 0, 'area': 900, 'bbox': [100, 120, 30, 30], 'iscrowd': 0}
    annotation_3 = {'id': 3, 'image_id': 0, 'category_id': 0, 'area': 1600, 'bbox': [150, 160, 40, 40], 'iscrowd': 0}
    annotation_4 = {'id': 4, 'image_id': 0, 'category_id': 0, 'area': 10000, 'bbox': [250, 260, 100, 100], 'iscrowd': 0}
    categories = [{'id': 0, 'name': 'car', 'supercategory': 'car'}]
    fake_json = {'images': [image], 'annotations': [annotation_1, annotation_2, annotation_3, annotation_4], 'categories': categories}
    mmcv.dump(fake_json, json_name)

def _create_dummy_custom_pkl(pkl_name):
    fake_pkl = [{'filename': 'fake_name.jpg', 'width': 640, 'height': 640, 'ann': {'bboxes': np.array([[50, 60, 70, 80], [100, 120, 130, 150], [150, 160, 190, 200], [250, 260, 350, 360]]), 'labels': np.array([0, 0, 0, 0])}}]
    mmcv.dump(fake_pkl, pkl_name)

def _create_ids_error_coco_json(json_name):
    image = {'id': 0, 'width': 640, 'height': 640, 'file_name': 'fake_name.jpg'}
    annotation_1 = {'id': 1, 'image_id': 0, 'category_id': 0, 'area': 400, 'bbox': [50, 60, 20, 20], 'iscrowd': 0}
    annotation_2 = {'id': 1, 'image_id': 0, 'category_id': 0, 'area': 900, 'bbox': [100, 120, 30, 30], 'iscrowd': 0}
    categories = [{'id': 0, 'name': 'car', 'supercategory': 'car'}]
    fake_json = {'images': [image], 'annotations': [annotation_1, annotation_2], 'categories': categories}
    mmcv.dump(fake_json, json_name)

def _create_panoptic_style_json(json_name):
    image1 = {'id': 0, 'width': 640, 'height': 640, 'file_name': 'fake_name1.jpg'}
    image2 = {'id': 1, 'width': 640, 'height': 800, 'file_name': 'fake_name2.jpg'}
    images = [image1, image2]
    annotations = [{'segments_info': [{'id': 1, 'category_id': 0, 'area': 400, 'bbox': [50, 60, 20, 20], 'iscrowd': 0}, {'id': 2, 'category_id': 1, 'area': 900, 'bbox': [100, 120, 30, 30], 'iscrowd': 0}, {'id': 3, 'category_id': 2, 'iscrowd': 0, 'bbox': [1, 189, 612, 285], 'area': 70036}], 'file_name': 'fake_name1.jpg', 'image_id': 0}, {'segments_info': [{'id': 1, 'category_id': 0, 'area': 400, 'bbox': [50, 60, 20, 20], 'iscrowd': 0}, {'id': 4, 'category_id': 1, 'area': 900, 'bbox': [100, 120, 30, 30], 'iscrowd': 1}, {'id': 5, 'category_id': 2, 'iscrowd': 0, 'bbox': [100, 200, 200, 300], 'area': 66666}, {'id': 6, 'category_id': 0, 'iscrowd': 0, 'bbox': [1, 189, -10, 285], 'area': 70036}], 'file_name': 'fake_name2.jpg', 'image_id': 1}]
    categories = [{'id': 0, 'name': 'car', 'supercategory': 'car', 'isthing': 1}, {'id': 1, 'name': 'person', 'supercategory': 'person', 'isthing': 1}, {'id': 2, 'name': 'wall', 'supercategory': 'wall', 'isthing': 0}]
    fake_json = {'images': images, 'annotations': annotations, 'categories': categories}
    mmcv.dump(fake_json, json_name)
    return fake_json

def _create_instance_segmentation_gt_annotations(ann_file):
    categories = [{'id': 0, 'name': 'person', 'supercategory': 'person', 'isthing': 1}, {'id': 1, 'name': 'dog', 'supercategory': 'dog', 'isthing': 1}, {'id': 2, 'name': 'wall', 'supercategory': 'wall', 'isthing': 0}]
    images = [{'id': 0, 'width': 80, 'height': 60, 'file_name': 'fake_name1.jpg'}]
    person1_polygon = [10, 10, 20, 10, 20, 50, 10, 50, 10, 10]
    person2_polygon = [30, 10, 40, 10, 40, 50, 30, 50, 30, 10]
    dog_polygon = [50, 10, 60, 10, 60, 15, 50, 15, 50, 10]
    annotations = [{'id': 0, 'image_id': 0, 'category_id': 0, 'segmentation': [person1_polygon], 'area': 400, 'bbox': [10, 10, 10, 40], 'iscrowd': 0}, {'id': 1, 'image_id': 0, 'category_id': 0, 'segmentation': [person2_polygon], 'area': 400, 'bbox': [30, 10, 10, 40], 'iscrowd': 0}, {'id': 2, 'image_id': 0, 'category_id': 1, 'segmentation': [dog_polygon], 'area': 50, 'bbox': [50, 10, 10, 5], 'iscrowd': 0}]
    gt_json = {'images': images, 'annotations': annotations, 'categories': categories}
    mmcv.dump(gt_json, ann_file)

def _create_ids_error_oid_csv(label_file, fake_csv_file):
    label_description = ['/m/000002', 'Football']
    with open(label_file, 'w', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(label_description)
    header = ['ImageID', 'Source', 'LabelName', 'Confidence', 'XMin', 'XMax', 'YMin', 'YMax', 'IsOccluded', 'IsTruncated', 'IsGroupOf', 'IsDepiction', 'IsInside']
    annotations = [['color', 'xclick', '/m/000002', '1', '0.022673031', '0.9642005', '0.07103825', '0.80054647', '0', '0', '0', '0', '0'], ['000595fe6fee6369', 'xclick', '/m/000000', '1', '0', '1', '0', '1', '0', '0', '1', '0', '0']]
    with open(fake_csv_file, 'w', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(header)
        f_csv.writerows(annotations)

def _create_oid_style_ann(label_file, csv_file, label_level_file):
    label_description = [['/m/000000', 'Sports equipment'], ['/m/000001', 'Ball'], ['/m/000002', 'Football'], ['/m/000004', 'Bicycle']]
    with open(label_file, 'w', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerows(label_description)
    header = ['ImageID', 'Source', 'LabelName', 'Confidence', 'XMin', 'XMax', 'YMin', 'YMax', 'IsOccluded', 'IsTruncated', 'IsGroupOf', 'IsDepiction', 'IsInside']
    annotations = [['color', 'xclick', '/m/000002', 1, 0.0333333, 0.1, 0.0333333, 0.1, 0, 0, 1, 0, 0], ['color', 'xclick', '/m/000002', 1, 0.1, 0.166667, 0.1, 0.166667, 0, 0, 0, 0, 0]]
    with open(csv_file, 'w', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(header)
        f_csv.writerows(annotations)
    header = ['ImageID', 'Source', 'LabelName', 'Confidence']
    annotations = [['color', 'xclick', '/m/000002', '1'], ['color', 'xclick', '/m/000004', '0']]
    with open(label_level_file, 'w', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(header)
        f_csv.writerows(annotations)

def _create_hierarchy_json(hierarchy_name):
    fake_hierarchy = {'LabelName': '/m/0bl9f', 'Subcategory': [{'LabelName': '/m/000000', 'Subcategory': [{'LabelName': '/m/000001', 'Subcategory': [{'LabelName': '/m/000002'}]}, {'LabelName': '/m/000004'}]}]}
    mmcv.dump(fake_hierarchy, hierarchy_name)

def _create_hierarchy_np(hierarchy_name):
    fake_hierarchy = np.array([[0, 1, 0, 0, 0], [0, 1, 1, 0, 0], [0, 1, 1, 1, 0], [0, 1, 0, 0, 1], [0, 0, 0, 0, 0]])
    with open(hierarchy_name, 'wb') as f:
        np.save(f, fake_hierarchy)

def _creat_oid_challenge_style_ann(txt_file, label_file, label_level_file):
    bboxes = ['validation/color.jpg\n', '4 29\n', '2\n', '1 0.0333333 0.1 0.0333333 0.1 1\n', '1 0.1 0.166667 0.1 0.166667 0\n']
    with open(txt_file, 'w', newline='') as f:
        f.writelines(bboxes)
        f.close()
    label_description = [['/m/000000', 'Sports equipment', 1], ['/m/000001', 'Ball', 2], ['/m/000002', 'Football', 3], ['/m/000004', 'Bicycle', 4]]
    with open(label_file, 'w', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerows(label_description)
    header = ['ImageID', 'LabelName', 'Confidence']
    annotations = [['color', '/m/000001', '1'], ['color', '/m/000000', '0']]
    with open(label_level_file, 'w', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(header)
        f_csv.writerows(annotations)

def _create_metas(meta_file):
    fake_meta = [{'filename': 'data/OpenImages/OpenImages/validation/color.jpg', 'ori_shape': (300, 300, 3)}]
    mmcv.dump(fake_meta, meta_file)

def test_dataset_wrapper():
    CustomDataset.load_annotations = MagicMock()
    CustomDataset.__getitem__ = MagicMock(side_effect=lambda idx: idx)
    dataset_a = CustomDataset(ann_file=MagicMock(), pipeline=[], test_mode=True, img_prefix='')
    len_a = 10
    cat_ids_list_a = [np.random.randint(0, 80, num).tolist() for num in np.random.randint(1, 20, len_a)]
    ann_info_list_a = []
    for _ in range(len_a):
        height = np.random.randint(10, 30)
        weight = np.random.randint(10, 30)
        img = np.ones((height, weight, 3))
        gt_bbox = np.concatenate([np.random.randint(1, 5, (2, 2)), np.random.randint(1, 5, (2, 2)) + 5], axis=1)
        gt_labels = np.random.randint(0, 80, 2)
        ann_info_list_a.append(dict(gt_bboxes=gt_bbox, gt_labels=gt_labels, img=img))
    dataset_a.data_infos = MagicMock()
    dataset_a.data_infos.__len__.return_value = len_a
    dataset_a.get_cat_ids = MagicMock(side_effect=lambda idx: cat_ids_list_a[idx])
    dataset_a.get_ann_info = MagicMock(side_effect=lambda idx: ann_info_list_a[idx])
    dataset_b = CustomDataset(ann_file=MagicMock(), pipeline=[], test_mode=True, img_prefix='')
    len_b = 20
    cat_ids_list_b = [np.random.randint(0, 80, num).tolist() for num in np.random.randint(1, 20, len_b)]
    ann_info_list_b = []
    for _ in range(len_b):
        height = np.random.randint(10, 30)
        weight = np.random.randint(10, 30)
        img = np.ones((height, weight, 3))
        gt_bbox = np.concatenate([np.random.randint(1, 5, (2, 2)), np.random.randint(1, 5, (2, 2)) + 5], axis=1)
        gt_labels = np.random.randint(0, 80, 2)
        ann_info_list_b.append(dict(gt_bboxes=gt_bbox, gt_labels=gt_labels, img=img))
    dataset_b.data_infos = MagicMock()
    dataset_b.data_infos.__len__.return_value = len_b
    dataset_b.get_cat_ids = MagicMock(side_effect=lambda idx: cat_ids_list_b[idx])
    dataset_b.get_ann_info = MagicMock(side_effect=lambda idx: ann_info_list_b[idx])
    concat_dataset = ConcatDataset([dataset_a, dataset_b])
    assert concat_dataset[5] == 5
    assert concat_dataset[25] == 15
    assert concat_dataset.get_cat_ids(5) == cat_ids_list_a[5]
    assert concat_dataset.get_cat_ids(25) == cat_ids_list_b[15]
    assert concat_dataset.get_ann_info(5) == ann_info_list_a[5]
    assert concat_dataset.get_ann_info(25) == ann_info_list_b[15]
    assert len(concat_dataset) == len(dataset_a) + len(dataset_b)
    palette_backup = CustomDataset.PALETTE
    delattr(CustomDataset, 'PALETTE')
    concat_dataset = ConcatDataset([dataset_a, dataset_b])
    assert concat_dataset.PALETTE is None
    CustomDataset.PALETTE = palette_backup
    repeat_dataset = RepeatDataset(dataset_a, 10)
    assert repeat_dataset[5] == 5
    assert repeat_dataset[15] == 5
    assert repeat_dataset[27] == 7
    assert repeat_dataset.get_cat_ids(5) == cat_ids_list_a[5]
    assert repeat_dataset.get_cat_ids(15) == cat_ids_list_a[5]
    assert repeat_dataset.get_cat_ids(27) == cat_ids_list_a[7]
    assert repeat_dataset.get_ann_info(5) == ann_info_list_a[5]
    assert repeat_dataset.get_ann_info(15) == ann_info_list_a[5]
    assert repeat_dataset.get_ann_info(27) == ann_info_list_a[7]
    assert len(repeat_dataset) == 10 * len(dataset_a)
    delattr(CustomDataset, 'PALETTE')
    repeat_dataset = RepeatDataset(dataset_a, 10)
    assert repeat_dataset.PALETTE is None
    CustomDataset.PALETTE = palette_backup
    category_freq = defaultdict(int)
    for cat_ids in cat_ids_list_a:
        cat_ids = set(cat_ids)
        for cat_id in cat_ids:
            category_freq[cat_id] += 1
    for k, v in category_freq.items():
        category_freq[k] = v / len(cat_ids_list_a)
    mean_freq = np.mean(list(category_freq.values()))
    repeat_thr = mean_freq
    category_repeat = {cat_id: max(1.0, math.sqrt(repeat_thr / cat_freq)) for cat_id, cat_freq in category_freq.items()}
    repeat_factors = []
    for cat_ids in cat_ids_list_a:
        cat_ids = set(cat_ids)
        repeat_factor = max({category_repeat[cat_id] for cat_id in cat_ids})
        repeat_factors.append(math.ceil(repeat_factor))
    repeat_factors_cumsum = np.cumsum(repeat_factors)
    repeat_factor_dataset = ClassBalancedDataset(dataset_a, repeat_thr)
    assert len(repeat_factor_dataset) == repeat_factors_cumsum[-1]
    for idx in np.random.randint(0, len(repeat_factor_dataset), 3):
        assert repeat_factor_dataset[idx] == bisect.bisect_right(repeat_factors_cumsum, idx)
        assert repeat_factor_dataset.get_ann_info(idx) == ann_info_list_a[bisect.bisect_right(repeat_factors_cumsum, idx)]
    delattr(CustomDataset, 'PALETTE')
    repeat_factor_dataset = ClassBalancedDataset(dataset_a, repeat_thr)
    assert repeat_factor_dataset.PALETTE is None
    CustomDataset.PALETTE = palette_backup
    img_scale = (60, 60)
    pipeline = [dict(type='Mosaic', img_scale=img_scale, pad_val=114.0), dict(type='RandomAffine', scaling_ratio_range=(0.1, 2), border=(-img_scale[0] // 2, -img_scale[1] // 2)), dict(type='MixUp', img_scale=img_scale, ratio_range=(0.8, 1.6), pad_val=114.0), dict(type='RandomFlip', flip_ratio=0.5), dict(type='Resize', img_scale=img_scale, keep_ratio=True), dict(type='Pad', pad_to_square=True, pad_val=114.0)]
    CustomDataset.load_annotations = MagicMock()
    results = []
    for _ in range(2):
        height = np.random.randint(10, 30)
        weight = np.random.randint(10, 30)
        img = np.ones((height, weight, 3))
        gt_bbox = np.concatenate([np.random.randint(1, 5, (2, 2)), np.random.randint(1, 5, (2, 2)) + 5], axis=1)
        gt_labels = np.random.randint(0, 80, 2)
        results.append(dict(gt_bboxes=gt_bbox, gt_labels=gt_labels, img=img))
    CustomDataset.__getitem__ = MagicMock(side_effect=lambda idx: results[idx])
    dataset_a = CustomDataset(ann_file=MagicMock(), pipeline=[], test_mode=True, img_prefix='')
    len_a = 2
    cat_ids_list_a = [np.random.randint(0, 80, num).tolist() for num in np.random.randint(1, 20, len_a)]
    dataset_a.data_infos = MagicMock()
    dataset_a.data_infos.__len__.return_value = len_a
    dataset_a.get_cat_ids = MagicMock(side_effect=lambda idx: cat_ids_list_a[idx])
    with pytest.raises(RuntimeError):
        MultiImageMixDataset(dataset_a, pipeline, (80, 80))
    multi_image_mix_dataset = MultiImageMixDataset(dataset_a, pipeline)
    for idx in range(len_a):
        results_ = multi_image_mix_dataset[idx]
        assert results_['img'].shape == (img_scale[0], img_scale[1], 3)
    multi_image_mix_dataset = MultiImageMixDataset(dataset_a, pipeline, skip_type_keys=('MixUp', 'RandomFlip', 'Resize', 'Pad'))
    for idx in range(len_a):
        results_ = multi_image_mix_dataset[idx]
        assert results_['img'].shape == (img_scale[0], img_scale[1], 3)
    delattr(CustomDataset, 'PALETTE')
    multi_image_mix_dataset = MultiImageMixDataset(dataset_a, pipeline)
    assert multi_image_mix_dataset.PALETTE is None
    CustomDataset.PALETTE = palette_backup

def _build_filter_annotations_args():
    kwargs = (dict(min_gt_bbox_wh=(100, 100)), dict(min_gt_bbox_wh=(100, 100), keep_empty=False), dict(min_gt_bbox_wh=(1, 1)), dict(min_gt_bbox_wh=(0.01, 0.01)), dict(min_gt_bbox_wh=(0.01, 0.01), by_mask=True), dict(by_mask=True), dict(by_box=False, by_mask=True))
    targets = (None, 0, 1, 2, 1, 1, 1)
    return list(zip(targets, kwargs))

def _check_keys(results, results_translated):
    assert len(set(results.keys()).difference(set(results_translated.keys()))) == 0
    assert len(set(results_translated.keys()).difference(set(results.keys()))) == 0

def file_size(path):
    path = Path(path)
    if path.is_file():
        return path.stat().st_size / 1000000.0
    elif path.is_dir():
        return sum((f.stat().st_size for f in path.glob('**/*') if f.is_file())) / 1000000.0
    else:
        return 0.0

def export_torchscript(model, im, file, optimize, prefix=colorstr('TorchScript:')):
    try:
        LOGGER.info(f'\n{prefix} starting export with torch {torch.__version__}...')
        f = file.with_suffix('.torchscript')
        ts = torch.jit.trace(model, im, strict=False)
        if optimize:
            optimize_for_mobile(ts)._save_for_lite_interpreter(str(f))
        else:
            ts.save(str(f))
        LOGGER.info(f'{prefix} export success, saved as {f} ({file_size(f):.1f} MB)')
        return f
    except Exception as e:
        LOGGER.info(f'{prefix} export failure: {e}')

def export_onnx(model, im, file, opset, dynamic, fp16, simplify, prefix=colorstr('ONNX:')):
    try:
        check_requirements(('onnx',))
        import onnx
        f = file.with_suffix('.onnx')
        LOGGER.info(f'\n{prefix} starting export with onnx {onnx.__version__}...')
        if dynamic:
            dynamic = {'images': {0: 'batch'}, 'output': {0: 'batch'}}
        torch.onnx.export(model.half() if fp16 else model.cpu(), im.half() if fp16 else im.cpu(), f, verbose=False, opset_version=opset, do_constant_folding=True, input_names=['images'], output_names=['output'], dynamic_axes=dynamic or None)
        model_onnx = onnx.load(f)
        onnx.checker.check_model(model_onnx)
        onnx.save(model_onnx, f)
        if simplify:
            try:
                cuda = torch.cuda.is_available()
                check_requirements(('onnxruntime-gpu' if cuda else 'onnxruntime', 'onnx-simplifier>=0.4.1'))
                import onnxsim
                LOGGER.info(f'simplifying with onnx-simplifier {onnxsim.__version__}...')
                model_onnx, check = onnxsim.simplify(model_onnx)
                assert check, 'assert check failed'
                onnx.save(model_onnx, f)
            except Exception as e:
                LOGGER.info(f'simplifier failure: {e}')
        LOGGER.info(f'{prefix} export success, saved as {f} ({file_size(f):.1f} MB)')
        return f
    except Exception as e:
        LOGGER.info(f'export failure: {e}')

def export_openvino(file, half, prefix=colorstr('OpenVINO:')):
    check_requirements(('openvino-dev',))
    import openvino.inference_engine as ie
    try:
        LOGGER.info(f'\n{prefix} starting export with openvino {ie.__version__}...')
        f = str(file).replace('.pt', f'_openvino_model{os.sep}')
        cmd = f'mo --input_model {file.with_suffix('.onnx')} --output_dir {f} --data_type {('FP16' if half else 'FP32')}'
        subprocess.check_output(cmd.split())
    except Exception as e:
        LOGGER.info(f'export failure: {e}')
    LOGGER.info(f'{prefix} export success, saved as {f} ({file_size(f):.1f} MB)')
    return f

def export_tflite(file, half, prefix=colorstr('TFLite:')):
    try:
        check_requirements(('openvino2tensorflow', 'tensorflow', 'tensorflow_datasets'))
        import openvino.inference_engine as ie
        LOGGER.info(f'\n{prefix} starting export with openvino {ie.__version__}...')
        output = Path(str(file).replace(f'_openvino_model{os.sep}', f'_tflite_model{os.sep}'))
        modelxml = list(Path(file).glob('*.xml'))[0]
        cmd = f'openvino2tensorflow             --model_path {modelxml}             --model_output_path {output}             --output_pb             --output_saved_model             --output_no_quant_float32_tflite             --output_dynamic_range_quant_tflite'
        subprocess.check_output(cmd.split())
        LOGGER.info(f'{prefix} export success, results saved in {output} ({file_size(f):.1f} MB)')
        return f
    except Exception as e:
        LOGGER.info(f'\n{prefix} export failure: {e}')

def export_engine(model, im, file, half, dynamic, simplify, workspace=4, verbose=False, prefix=colorstr('TensorRT:')):
    try:
        assert im.device.type != 'cpu', 'export running on CPU but must be on GPU, i.e. `python export.py --device 0`'
        try:
            import tensorrt as trt
        except Exception:
            if platform.system() == 'Linux':
                check_requirements(('nvidia-tensorrt',), cmds=('-U --index-url https://pypi.ngc.nvidia.com',))
            import tensorrt as trt
        if trt.__version__[0] == '7':
            grid = model.model[-1].anchor_grid
            model.model[-1].anchor_grid = [a[..., :1, :1, :] for a in grid]
            export_onnx(model, im, file, 12, dynamic, half, simplify)
            model.model[-1].anchor_grid = grid
        else:
            check_version(trt.__version__, '8.0.0', hard=True)
            export_onnx(model, im, file, 12, dynamic, half, simplify)
        onnx = file.with_suffix('.onnx')
        LOGGER.info(f'\n{prefix} starting export with TensorRT {trt.__version__}...')
        assert onnx.exists(), f'failed to export ONNX file: {onnx}'
        f = file.with_suffix('.engine')
        logger = trt.Logger(trt.Logger.INFO)
        if verbose:
            logger.min_severity = trt.Logger.Severity.VERBOSE
        builder = trt.Builder(logger)
        config = builder.create_builder_config()
        config.max_workspace_size = workspace * 1 << 30
        flag = 1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
        network = builder.create_network(flag)
        parser = trt.OnnxParser(network, logger)
        if not parser.parse_from_file(str(onnx)):
            raise RuntimeError(f'failed to load ONNX file: {onnx}')
        inputs = [network.get_input(i) for i in range(network.num_inputs)]
        outputs = [network.get_output(i) for i in range(network.num_outputs)]
        LOGGER.info(f'{prefix} Network Description:')
        for inp in inputs:
            LOGGER.info(f'{prefix}\tinput "{inp.name}" with shape {inp.shape} and dtype {inp.dtype}')
        for out in outputs:
            LOGGER.info(f'{prefix}\toutput "{out.name}" with shape {out.shape} and dtype {out.dtype}')
        if dynamic:
            if im.shape[0] <= 1:
                LOGGER.warning(f'{prefix}WARNING: --dynamic model requires maximum --batch-size argument')
            profile = builder.create_optimization_profile()
            for inp in inputs:
                if half:
                    inp.dtype = trt.float16
                profile.set_shape(inp.name, (1, *im.shape[1:]), (max(1, im.shape[0] // 2), *im.shape[1:]), im.shape)
            config.add_optimization_profile(profile)
        LOGGER.info(f'{prefix} building FP{(16 if builder.platform_has_fast_fp16 and half else 32)} engine in {f}')
        if builder.platform_has_fast_fp16 and half:
            config.set_flag(trt.BuilderFlag.FP16)
            config.default_device_type = trt.DeviceType.GPU
        with builder.build_engine(network, config) as engine, open(f, 'wb') as t:
            t.write(engine.serialize())
        LOGGER.info(f'{prefix} export success, saved as {f} ({file_size(f):.1f} MB)')
        return f
    except Exception as e:
        LOGGER.info(f'\n{prefix} export failure: {e}')

def create_tracker(tracker_type, tracker_config, reid_weights, device, half):
    cfg = get_config()
    cfg.merge_from_file(tracker_config)
    if tracker_type == 'strongsort':
        from trackers.strongsort.strong_sort import StrongSORT
        strongsort = StrongSORT(reid_weights, device, half, max_dist=cfg.strongsort.max_dist, max_iou_dist=cfg.strongsort.max_iou_dist, max_age=cfg.strongsort.max_age, max_unmatched_preds=cfg.strongsort.max_unmatched_preds, n_init=cfg.strongsort.n_init, nn_budget=cfg.strongsort.nn_budget, mc_lambda=cfg.strongsort.mc_lambda, ema_alpha=cfg.strongsort.ema_alpha)
        return strongsort
    elif tracker_type == 'ocsort':
        from trackers.ocsort.ocsort import OCSort
        ocsort = OCSort(det_thresh=cfg.ocsort.det_thresh, max_age=cfg.ocsort.max_age, min_hits=cfg.ocsort.min_hits, iou_threshold=cfg.ocsort.iou_thresh, delta_t=cfg.ocsort.delta_t, asso_func=cfg.ocsort.asso_func, inertia=cfg.ocsort.inertia, use_byte=cfg.ocsort.use_byte)
        return ocsort
    elif tracker_type == 'bytetrack':
        from trackers.bytetrack.byte_tracker import BYTETracker
        bytetracker = BYTETracker(track_thresh=cfg.bytetrack.track_thresh, match_thresh=cfg.bytetrack.match_thresh, track_buffer=cfg.bytetrack.track_buffer, frame_rate=cfg.bytetrack.frame_rate)
        return bytetracker
    elif tracker_type == 'botsort':
        from trackers.botsort.bot_sort import BoTSORT
        botsort = BoTSORT(reid_weights, device, half, track_high_thresh=cfg.botsort.track_high_thresh, new_track_thresh=cfg.botsort.new_track_thresh, track_buffer=cfg.botsort.track_buffer, match_thresh=cfg.botsort.match_thresh, proximity_thresh=cfg.botsort.proximity_thresh, appearance_thresh=cfg.botsort.appearance_thresh, cmc_method=cfg.botsort.cmc_method, frame_rate=cfg.botsort.frame_rate, lambda_=cfg.botsort.lambda_)
        return botsort
    elif tracker_type == 'deepocsort':
        from trackers.deepocsort.ocsort import OCSort
        botsort = OCSort(reid_weights, device, half, det_thresh=cfg.deepocsort.det_thresh, max_age=cfg.deepocsort.max_age, min_hits=cfg.deepocsort.min_hits, iou_threshold=cfg.deepocsort.iou_thresh, delta_t=cfg.deepocsort.delta_t, asso_func=cfg.deepocsort.asso_func, inertia=cfg.deepocsort.inertia)
        return botsort
    else:
        print('No such tracker')
        exit()

class ReIDDetectMultiBackend(nn.Module):

    def __init__(self, weights='osnet_x0_25_msmt17.pt', device=torch.device('cpu'), fp16=False):
        super().__init__()
        w = weights[0] if isinstance(weights, list) else weights
        self.pt, self.jit, self.onnx, self.xml, self.engine, self.tflite = self.model_type(w)
        self.fp16 = fp16
        self.fp16 &= self.pt or self.jit or self.engine
        self.device = device
        self.image_size = (256, 128)
        self.pixel_mean = [0.485, 0.456, 0.406]
        self.pixel_std = [0.229, 0.224, 0.225]
        self.transforms = []
        self.transforms += [T.Resize(self.image_size)]
        self.transforms += [T.ToTensor()]
        self.transforms += [T.Normalize(mean=self.pixel_mean, std=self.pixel_std)]
        self.preprocess = T.Compose(self.transforms)
        self.to_pil = T.ToPILImage()
        model_name = get_model_name(w)
        if w.suffix == '.pt':
            model_url = get_model_url(w)
            if not file_exists(w) and model_url is not None:
                gdown.download(model_url, str(w), quiet=False)
            elif file_exists(w):
                pass
            else:
                print(f'No URL associated to the chosen StrongSORT weights ({w}). Choose between:')
                show_downloadeable_models()
                exit()
        self.model = build_model(model_name, num_classes=1, pretrained=not (w and w.is_file()), use_gpu=device)
        if self.pt:
            if w and w.is_file() and (w.suffix == '.pt'):
                load_pretrained_weights(self.model, w)
            self.model.to(device).eval()
            self.model.half() if self.fp16 else self.model.float()
        elif self.jit:
            LOGGER.info(f'Loading {w} for TorchScript inference...')
            self.model = torch.jit.load(w)
            self.model.half() if self.fp16 else self.model.float()
        elif self.onnx:
            LOGGER.info(f'Loading {w} for ONNX Runtime inference...')
            cuda = torch.cuda.is_available() and device.type != 'cpu'
            import onnxruntime
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
            self.session = onnxruntime.InferenceSession(str(w), providers=providers)
        elif self.engine:
            LOGGER.info(f'Loading {w} for TensorRT inference...')
            import tensorrt as trt
            check_version(trt.__version__, '7.0.0', hard=True)
            if device.type == 'cpu':
                device = torch.device('cuda:0')
            Binding = namedtuple('Binding', ('name', 'dtype', 'shape', 'data', 'ptr'))
            logger = trt.Logger(trt.Logger.INFO)
            with open(w, 'rb') as f, trt.Runtime(logger) as runtime:
                self.model_ = runtime.deserialize_cuda_engine(f.read())
            self.context = self.model_.create_execution_context()
            self.bindings = OrderedDict()
            self.fp16 = False
            dynamic = False
            for index in range(self.model_.num_bindings):
                name = self.model_.get_binding_name(index)
                dtype = trt.nptype(self.model_.get_binding_dtype(index))
                if self.model_.binding_is_input(index):
                    if -1 in tuple(self.model_.get_binding_shape(index)):
                        dynamic = True
                        self.context.set_binding_shape(index, tuple(self.model_.get_profile_shape(0, index)[2]))
                    if dtype == np.float16:
                        self.fp16 = True
                shape = tuple(self.context.get_binding_shape(index))
                im = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
                self.bindings[name] = Binding(name, dtype, shape, im, int(im.data_ptr()))
            self.binding_addrs = OrderedDict(((n, d.ptr) for n, d in self.bindings.items()))
            batch_size = self.bindings['images'].shape[0]
        elif self.xml:
            LOGGER.info(f'Loading {w} for OpenVINO inference...')
            check_requirements(('openvino',))
            from openvino.runtime import Core, Layout, get_batch
            ie = Core()
            if not Path(w).is_file():
                w = next(Path(w).glob('*.xml'))
            network = ie.read_model(model=w, weights=Path(w).with_suffix('.bin'))
            if network.get_parameters()[0].get_layout().empty:
                network.get_parameters()[0].set_layout(Layout('NCWH'))
            batch_dim = get_batch(network)
            if batch_dim.is_static:
                batch_size = batch_dim.get_length()
            self.executable_network = ie.compile_model(network, device_name='CPU')
            self.output_layer = next(iter(self.executable_network.outputs))
        elif self.tflite:
            LOGGER.info(f'Loading {w} for TensorFlow Lite inference...')
            try:
                from tflite_runtime.interpreter import Interpreter, load_delegate
            except ImportError:
                import tensorflow as tf
                Interpreter, load_delegate = (tf.lite.Interpreter, tf.lite.experimental.load_delegate)
            self.interpreter = tf.lite.Interpreter(model_path=w)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            input_data = np.array(np.random.random_sample((1, 256, 128, 3)), dtype=np.float32)
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        else:
            print('This model framework is not supported yet!')
            exit()

    @staticmethod
    def model_type(p='path/to/model.pt'):
        from trackers.reid_export import export_formats
        sf = list(export_formats().Suffix)
        check_suffix(p, sf)
        types = [s in Path(p).name for s in sf]
        return types

    def _preprocess(self, im_batch):
        images = []
        for element in im_batch:
            image = self.to_pil(element)
            image = self.preprocess(image)
            images.append(image)
        images = torch.stack(images, dim=0)
        images = images.to(self.device)
        return images

    def forward(self, im_batch):
        im_batch = self._preprocess(im_batch)
        if self.fp16 and im_batch.dtype != torch.float16:
            im_batch = im_batch.half()
        features = []
        if self.pt:
            features = self.model(im_batch)
        elif self.jit:
            features = self.model(im_batch)
        elif self.onnx:
            im_batch = im_batch.cpu().numpy()
            features = self.session.run([self.session.get_outputs()[0].name], {self.session.get_inputs()[0].name: im_batch})[0]
        elif self.engine:
            if True and im_batch.shape != self.bindings['images'].shape:
                i_in, i_out = (self.model_.get_binding_index(x) for x in ('images', 'output'))
                self.context.set_binding_shape(i_in, im_batch.shape)
                self.bindings['images'] = self.bindings['images']._replace(shape=im_batch.shape)
                self.bindings['output'].data.resize_(tuple(self.context.get_binding_shape(i_out)))
            s = self.bindings['images'].shape
            assert im_batch.shape == s, f'input size {im_batch.shape} {('>' if self.dynamic else 'not equal to')} max model size {s}'
            self.binding_addrs['images'] = int(im_batch.data_ptr())
            self.context.execute_v2(list(self.binding_addrs.values()))
            features = self.bindings['output'].data
        elif self.xml:
            im_batch = im_batch.cpu().numpy()
            features = self.executable_network([im_batch])[self.output_layer]
        else:
            print('Framework not supported at the moment, we are working on it...')
            exit()
        if isinstance(features, (list, tuple)):
            return self.from_numpy(features[0]) if len(features) == 1 else [self.from_numpy(x) for x in features]
        else:
            return self.from_numpy(features)

    def from_numpy(self, x):
        return torch.from_numpy(x).to(self.device) if isinstance(x, np.ndarray) else x

    def warmup(self, imgsz=[(256, 128, 3)]):
        warmup_types = (self.pt, self.jit, self.onnx, self.engine, self.tflite)
        if any(warmup_types) and self.device.type != 'cpu':
            im = [np.empty(*imgsz).astype(np.uint8)]
            for _ in range(2 if self.jit else 1):
                self.forward(im)

def __init__(self, weights='osnet_x0_25_msmt17.pt', device=torch.device('cpu'), fp16=False):
    super().__init__()
    w = weights[0] if isinstance(weights, list) else weights
    self.pt, self.jit, self.onnx, self.xml, self.engine, self.tflite = self.model_type(w)
    self.fp16 = fp16
    self.fp16 &= self.pt or self.jit or self.engine
    self.device = device
    self.image_size = (256, 128)
    self.pixel_mean = [0.485, 0.456, 0.406]
    self.pixel_std = [0.229, 0.224, 0.225]
    self.transforms = []
    self.transforms += [T.Resize(self.image_size)]
    self.transforms += [T.ToTensor()]
    self.transforms += [T.Normalize(mean=self.pixel_mean, std=self.pixel_std)]
    self.preprocess = T.Compose(self.transforms)
    self.to_pil = T.ToPILImage()
    model_name = get_model_name(w)
    if w.suffix == '.pt':
        model_url = get_model_url(w)
        if not file_exists(w) and model_url is not None:
            gdown.download(model_url, str(w), quiet=False)
        elif file_exists(w):
            pass
        else:
            print(f'No URL associated to the chosen StrongSORT weights ({w}). Choose between:')
            show_downloadeable_models()
            exit()
    self.model = build_model(model_name, num_classes=1, pretrained=not (w and w.is_file()), use_gpu=device)
    if self.pt:
        if w and w.is_file() and (w.suffix == '.pt'):
            load_pretrained_weights(self.model, w)
        self.model.to(device).eval()
        self.model.half() if self.fp16 else self.model.float()
    elif self.jit:
        LOGGER.info(f'Loading {w} for TorchScript inference...')
        self.model = torch.jit.load(w)
        self.model.half() if self.fp16 else self.model.float()
    elif self.onnx:
        LOGGER.info(f'Loading {w} for ONNX Runtime inference...')
        cuda = torch.cuda.is_available() and device.type != 'cpu'
        import onnxruntime
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
        self.session = onnxruntime.InferenceSession(str(w), providers=providers)
    elif self.engine:
        LOGGER.info(f'Loading {w} for TensorRT inference...')
        import tensorrt as trt
        check_version(trt.__version__, '7.0.0', hard=True)
        if device.type == 'cpu':
            device = torch.device('cuda:0')
        Binding = namedtuple('Binding', ('name', 'dtype', 'shape', 'data', 'ptr'))
        logger = trt.Logger(trt.Logger.INFO)
        with open(w, 'rb') as f, trt.Runtime(logger) as runtime:
            self.model_ = runtime.deserialize_cuda_engine(f.read())
        self.context = self.model_.create_execution_context()
        self.bindings = OrderedDict()
        self.fp16 = False
        dynamic = False
        for index in range(self.model_.num_bindings):
            name = self.model_.get_binding_name(index)
            dtype = trt.nptype(self.model_.get_binding_dtype(index))
            if self.model_.binding_is_input(index):
                if -1 in tuple(self.model_.get_binding_shape(index)):
                    dynamic = True
                    self.context.set_binding_shape(index, tuple(self.model_.get_profile_shape(0, index)[2]))
                if dtype == np.float16:
                    self.fp16 = True
            shape = tuple(self.context.get_binding_shape(index))
            im = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
            self.bindings[name] = Binding(name, dtype, shape, im, int(im.data_ptr()))
        self.binding_addrs = OrderedDict(((n, d.ptr) for n, d in self.bindings.items()))
        batch_size = self.bindings['images'].shape[0]
    elif self.xml:
        LOGGER.info(f'Loading {w} for OpenVINO inference...')
        check_requirements(('openvino',))
        from openvino.runtime import Core, Layout, get_batch
        ie = Core()
        if not Path(w).is_file():
            w = next(Path(w).glob('*.xml'))
        network = ie.read_model(model=w, weights=Path(w).with_suffix('.bin'))
        if network.get_parameters()[0].get_layout().empty:
            network.get_parameters()[0].set_layout(Layout('NCWH'))
        batch_dim = get_batch(network)
        if batch_dim.is_static:
            batch_size = batch_dim.get_length()
        self.executable_network = ie.compile_model(network, device_name='CPU')
        self.output_layer = next(iter(self.executable_network.outputs))
    elif self.tflite:
        LOGGER.info(f'Loading {w} for TensorFlow Lite inference...')
        try:
            from tflite_runtime.interpreter import Interpreter, load_delegate
        except ImportError:
            import tensorflow as tf
            Interpreter, load_delegate = (tf.lite.Interpreter, tf.lite.experimental.load_delegate)
        self.interpreter = tf.lite.Interpreter(model_path=w)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        input_data = np.array(np.random.random_sample((1, 256, 128, 3)), dtype=np.float32)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
    else:
        print('This model framework is not supported yet!')
        exit()

@staticmethod
def model_type(p='path/to/model.pt'):
    from trackers.reid_export import export_formats
    sf = list(export_formats().Suffix)
    check_suffix(p, sf)
    types = [s in Path(p).name for s in sf]
    return types

def forward(self, im_batch):
    im_batch = self._preprocess(im_batch)
    if self.fp16 and im_batch.dtype != torch.float16:
        im_batch = im_batch.half()
    features = []
    if self.pt:
        features = self.model(im_batch)
    elif self.jit:
        features = self.model(im_batch)
    elif self.onnx:
        im_batch = im_batch.cpu().numpy()
        features = self.session.run([self.session.get_outputs()[0].name], {self.session.get_inputs()[0].name: im_batch})[0]
    elif self.engine:
        if True and im_batch.shape != self.bindings['images'].shape:
            i_in, i_out = (self.model_.get_binding_index(x) for x in ('images', 'output'))
            self.context.set_binding_shape(i_in, im_batch.shape)
            self.bindings['images'] = self.bindings['images']._replace(shape=im_batch.shape)
            self.bindings['output'].data.resize_(tuple(self.context.get_binding_shape(i_out)))
        s = self.bindings['images'].shape
        assert im_batch.shape == s, f'input size {im_batch.shape} {('>' if self.dynamic else 'not equal to')} max model size {s}'
        self.binding_addrs['images'] = int(im_batch.data_ptr())
        self.context.execute_v2(list(self.binding_addrs.values()))
        features = self.bindings['output'].data
    elif self.xml:
        im_batch = im_batch.cpu().numpy()
        features = self.executable_network([im_batch])[self.output_layer]
    else:
        print('Framework not supported at the moment, we are working on it...')
        exit()
    if isinstance(features, (list, tuple)):
        return self.from_numpy(features[0]) if len(features) == 1 else [self.from_numpy(x) for x in features]
    else:
        return self.from_numpy(features)

class StrongSORT(object):

    def __init__(self, model_weights, device, fp16, max_dist=0.2, max_iou_dist=0.7, max_age=70, max_unmatched_preds=7, n_init=3, nn_budget=100, mc_lambda=0.995, ema_alpha=0.9):
        self.model = ReIDDetectMultiBackend(weights=model_weights, device=device, fp16=fp16)
        self.max_dist = max_dist
        metric = NearestNeighborDistanceMetric('cosine', self.max_dist, nn_budget)
        self.tracker = Tracker(metric, max_iou_dist=max_iou_dist, max_age=max_age, n_init=n_init, max_unmatched_preds=max_unmatched_preds, mc_lambda=mc_lambda, ema_alpha=ema_alpha)

    def update(self, dets, ori_img):
        xyxys = dets[:, 0:4]
        confs = dets[:, 4]
        clss = dets[:, 5]
        classes = clss.numpy()
        xywhs = xyxy2xywh(xyxys.numpy())
        confs = confs.numpy()
        self.height, self.width = ori_img.shape[:2]
        features = self._get_features(xywhs, ori_img)
        bbox_tlwh = self._xywh_to_tlwh(xywhs)
        detections = [Detection(bbox_tlwh[i], conf, features[i]) for i, conf in enumerate(confs)]
        boxes = np.array([d.tlwh for d in detections])
        scores = np.array([d.confidence for d in detections])
        self.tracker.predict()
        self.tracker.update(detections, clss, confs)
        outputs = []
        for track in self.tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            box = track.to_tlwh()
            x1, y1, x2, y2 = self._tlwh_to_xyxy(box)
            track_id = track.track_id
            class_id = track.class_id
            conf = track.conf
            queue = track.q
            outputs.append(np.array([x1, y1, x2, y2, track_id, class_id, conf, queue], dtype=object))
        if len(outputs) > 0:
            outputs = np.stack(outputs, axis=0)
        return outputs
    '\n    TODO:\n        Convert bbox from xc_yc_w_h to xtl_ytl_w_h\n    Thanks JieChen91@github.com for reporting this bug!\n    '

    @staticmethod
    def _xywh_to_tlwh(bbox_xywh):
        if isinstance(bbox_xywh, np.ndarray):
            bbox_tlwh = bbox_xywh.copy()
        elif isinstance(bbox_xywh, torch.Tensor):
            bbox_tlwh = bbox_xywh.clone()
        bbox_tlwh[:, 0] = bbox_xywh[:, 0] - bbox_xywh[:, 2] / 2.0
        bbox_tlwh[:, 1] = bbox_xywh[:, 1] - bbox_xywh[:, 3] / 2.0
        return bbox_tlwh

    def _xywh_to_xyxy(self, bbox_xywh):
        x, y, w, h = bbox_xywh
        x1 = max(int(x - w / 2), 0)
        x2 = min(int(x + w / 2), self.width - 1)
        y1 = max(int(y - h / 2), 0)
        y2 = min(int(y + h / 2), self.height - 1)
        return (x1, y1, x2, y2)

    def _tlwh_to_xyxy(self, bbox_tlwh):
        """
        TODO:
            Convert bbox from xtl_ytl_w_h to xc_yc_w_h
        Thanks JieChen91@github.com for reporting this bug!
        """
        x, y, w, h = bbox_tlwh
        x1 = max(int(x), 0)
        x2 = min(int(x + w), self.width - 1)
        y1 = max(int(y), 0)
        y2 = min(int(y + h), self.height - 1)
        return (x1, y1, x2, y2)

    def increment_ages(self):
        self.tracker.increment_ages()

    def _xyxy_to_tlwh(self, bbox_xyxy):
        x1, y1, x2, y2 = bbox_xyxy
        t = x1
        l = y1
        w = int(x2 - x1)
        h = int(y2 - y1)
        return (t, l, w, h)

    def _get_features(self, bbox_xywh, ori_img):
        im_crops = []
        for box in bbox_xywh:
            x1, y1, x2, y2 = self._xywh_to_xyxy(box)
            im = ori_img[y1:y2, x1:x2]
            im_crops.append(im)
        if im_crops:
            features = self.model(im_crops)
        else:
            features = np.array([])
        return features

    def trajectory(self, im0, q, color):
        for i, p in enumerate(q):
            thickness = int(np.sqrt(float(i + 1)) * 1.5)
            if p[0] == 'observationupdate':
                cv2.circle(im0, p[1], 2, color=color, thickness=thickness)
            else:
                cv2.circle(im0, p[1], 2, color=(255, 255, 255), thickness=thickness)

def update(self, dets, ori_img):
    xyxys = dets[:, 0:4]
    confs = dets[:, 4]
    clss = dets[:, 5]
    classes = clss.numpy()
    xywhs = xyxy2xywh(xyxys.numpy())
    confs = confs.numpy()
    self.height, self.width = ori_img.shape[:2]
    features = self._get_features(xywhs, ori_img)
    bbox_tlwh = self._xywh_to_tlwh(xywhs)
    detections = [Detection(bbox_tlwh[i], conf, features[i]) for i, conf in enumerate(confs)]
    boxes = np.array([d.tlwh for d in detections])
    scores = np.array([d.confidence for d in detections])
    self.tracker.predict()
    self.tracker.update(detections, clss, confs)
    outputs = []
    for track in self.tracker.tracks:
        if not track.is_confirmed() or track.time_since_update > 1:
            continue
        box = track.to_tlwh()
        x1, y1, x2, y2 = self._tlwh_to_xyxy(box)
        track_id = track.track_id
        class_id = track.class_id
        conf = track.conf
        queue = track.q
        outputs.append(np.array([x1, y1, x2, y2, track_id, class_id, conf, queue], dtype=object))
    if len(outputs) > 0:
        outputs = np.stack(outputs, axis=0)
    return outputs

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

def matching_cascade(distance_metric, max_distance, cascade_depth, tracks, detections, track_indices=None, detection_indices=None):
    """Run matching cascade.
    Parameters
    ----------
    distance_metric : Callable[List[Track], List[Detection], List[int], List[int]) -> ndarray
        The distance metric is given a list of tracks and detections as well as
        a list of N track indices and M detection indices. The metric should
        return the NxM dimensional cost matrix, where element (i, j) is the
        association cost between the i-th track in the given track indices and
        the j-th detection in the given detection indices.
    max_distance : float
        Gating threshold. Associations with cost larger than this value are
        disregarded.
    cascade_depth: int
        The cascade depth, should be se to the maximum track age.
    tracks : List[track.Track]
        A list of predicted tracks at the current time step.
    detections : List[detection.Detection]
        A list of detections at the current time step.
    track_indices : Optional[List[int]]
        List of track indices that maps rows in `cost_matrix` to tracks in
        `tracks` (see description above). Defaults to all tracks.
    detection_indices : Optional[List[int]]
        List of detection indices that maps columns in `cost_matrix` to
        detections in `detections` (see description above). Defaults to all
        detections.
    Returns
    -------
    (List[(int, int)], List[int], List[int])
        Returns a tuple with the following three entries:
        * A list of matched track and detection indices.
        * A list of unmatched track indices.
        * A list of unmatched detection indices.
    """
    if track_indices is None:
        track_indices = list(range(len(tracks)))
    if detection_indices is None:
        detection_indices = list(range(len(detections)))
    unmatched_detections = detection_indices
    matches = []
    track_indices_l = [k for k in track_indices]
    matches_l, _, unmatched_detections = min_cost_matching(distance_metric, max_distance, tracks, detections, track_indices_l, unmatched_detections)
    matches += matches_l
    unmatched_tracks = list(set(track_indices) - set((k for k, _ in matches)))
    return (matches, unmatched_tracks, unmatched_detections)

class NearestNeighborDistanceMetric(object):
    """
    A nearest neighbor distance metric that, for each target, returns
    the closest distance to any sample that has been observed so far.
    Parameters
    ----------
    metric : str
        Either "euclidean" or "cosine".
    matching_threshold: float
        The matching threshold. Samples with larger distance are considered an
        invalid match.
    budget : Optional[int]
        If not None, fix samples per class to at most this number. Removes
        the oldest samples when the budget is reached.
    Attributes
    ----------
    samples : Dict[int -> List[ndarray]]
        A dictionary that maps from target identities to the list of samples
        that have been observed so far.
    """

    def __init__(self, metric, matching_threshold, budget=None):
        if metric == 'euclidean':
            self._metric = _nn_euclidean_distance
        elif metric == 'cosine':
            self._metric = _nn_cosine_distance
        else:
            raise ValueError("Invalid metric; must be either 'euclidean' or 'cosine'")
        self.matching_threshold = matching_threshold
        self.budget = budget
        self.samples = {}

    def partial_fit(self, features, targets, active_targets):
        """Update the distance metric with new data.
        Parameters
        ----------
        features : ndarray
            An NxM matrix of N features of dimensionality M.
        targets : ndarray
            An integer array of associated target identities.
        active_targets : List[int]
            A list of targets that are currently present in the scene.
        """
        for feature, target in zip(features, targets):
            self.samples.setdefault(target, []).append(feature)
            if self.budget is not None:
                self.samples[target] = self.samples[target][-self.budget:]
        self.samples = {k: self.samples[k] for k in active_targets}

    def distance(self, features, targets):
        """Compute distance between features and targets.
        Parameters
        ----------
        features : ndarray
            An NxM matrix of N features of dimensionality M.
        targets : List[int]
            A list of targets to match the given `features` against.
        Returns
        -------
        ndarray
            Returns a cost matrix of shape len(targets), len(features), where
            element (i, j) contains the closest squared distance between
            `targets[i]` and `features[j]`.
        """
        cost_matrix = np.zeros((len(targets), len(features)))
        for i, target in enumerate(targets):
            cost_matrix[i, :] = self._metric(self.samples[target], features)
        return cost_matrix

def partial_fit(self, features, targets, active_targets):
    """Update the distance metric with new data.
        Parameters
        ----------
        features : ndarray
            An NxM matrix of N features of dimensionality M.
        targets : ndarray
            An integer array of associated target identities.
        active_targets : List[int]
            A list of targets that are currently present in the scene.
        """
    for feature, target in zip(features, targets):
        self.samples.setdefault(target, []).append(feature)
        if self.budget is not None:
            self.samples[target] = self.samples[target][-self.budget:]
    self.samples = {k: self.samples[k] for k in active_targets}

class Track:
    """
    A single target track with state space `(x, y, a, h)` and associated
    velocities, where `(x, y)` is the center of the bounding box, `a` is the
    aspect ratio and `h` is the height.

    Parameters
    ----------
    mean : ndarray
        Mean vector of the initial state distribution.
    covariance : ndarray
        Covariance matrix of the initial state distribution.
    track_id : int
        A unique track identifier.
    n_init : int
        Number of consecutive detections before the track is confirmed. The
        track state is set to `Deleted` if a miss occurs within the first
        `n_init` frames.
    max_age : int
        The maximum number of consecutive misses before the track state is
        set to `Deleted`.
    feature : Optional[ndarray]
        Feature vector of the detection this track originates from. If not None,
        this feature is added to the `features` cache.

    Attributes
    ----------
    mean : ndarray
        Mean vector of the initial state distribution.
    covariance : ndarray
        Covariance matrix of the initial state distribution.
    track_id : int
        A unique track identifier.
    hits : int
        Total number of measurement updates.
    age : int
        Total number of frames since first occurance.
    time_since_update : int
        Total number of frames since last measurement update.
    state : TrackState
        The current track state.
    features : List[ndarray]
        A cache of features. On each measurement update, the associated feature
        vector is added to this list.

    """

    def __init__(self, detection, track_id, class_id, conf, n_init, max_age, ema_alpha, feature=None):
        self.track_id = track_id
        self.class_id = int(class_id)
        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.max_num_updates_wo_assignment = 7
        self.updates_wo_assignment = 0
        self.ema_alpha = ema_alpha
        self.state = TrackState.Tentative
        self.features = []
        if feature is not None:
            feature /= np.linalg.norm(feature)
            self.features.append(feature)
        self.conf = conf
        self._n_init = n_init
        self._max_age = max_age
        self.kf = KalmanFilter()
        self.mean, self.covariance = self.kf.initiate(detection)
        self.q = deque(maxlen=25)

    def to_tlwh(self):
        """Get current position in bounding box format `(top left x, top left y,
        width, height)`.

        Returns
        -------
        ndarray
            The bounding box.

        """
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[:2] -= ret[2:] / 2
        return ret

    def to_tlbr(self):
        """Get kf estimated current position in bounding box format `(min x, miny, max x,
        max y)`.

        Returns
        -------
        ndarray
            The predicted kf bounding box.

        """
        ret = self.to_tlwh()
        ret[2:] = ret[:2] + ret[2:]
        return ret

    def ECC(self, src, dst, warp_mode=cv2.MOTION_EUCLIDEAN, eps=1e-05, max_iter=100, scale=0.1, align=False):
        """Compute the warp matrix from src to dst.
        Parameters
        ----------
        src : ndarray 
            An NxM matrix of source img(BGR or Gray), it must be the same format as dst.
        dst : ndarray
            An NxM matrix of target img(BGR or Gray).
        warp_mode: flags of opencv
            translation: cv2.MOTION_TRANSLATION
            rotated and shifted: cv2.MOTION_EUCLIDEAN
            affine(shift,rotated,shear): cv2.MOTION_AFFINE
            homography(3d): cv2.MOTION_HOMOGRAPHY
        eps: float
            the threshold of the increment in the correlation coefficient between two iterations
        max_iter: int
            the number of iterations.
        scale: float or [int, int]
            scale_ratio: float
            scale_size: [W, H]
        align: bool
            whether to warp affine or perspective transforms to the source image
        Returns
        -------
        warp matrix : ndarray
            Returns the warp matrix from src to dst.
            if motion models is homography, the warp matrix will be 3x3, otherwise 2x3
        src_aligned: ndarray
            aligned source image of gray
        """
        if src.ndim == 3:
            src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
            dst = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)
        if scale is not None:
            if isinstance(scale, float) or isinstance(scale, int):
                if scale != 1:
                    src_r = cv2.resize(src, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                    dst_r = cv2.resize(dst, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                    scale = [scale, scale]
                else:
                    src_r, dst_r = (src, dst)
                    scale = None
            elif scale[0] != src.shape[1] and scale[1] != src.shape[0]:
                src_r = cv2.resize(src, (scale[0], scale[1]), interpolation=cv2.INTER_LINEAR)
                dst_r = cv2.resize(dst, (scale[0], scale[1]), interpolation=cv2.INTER_LINEAR)
                scale = [scale[0] / src.shape[1], scale[1] / src.shape[0]]
            else:
                src_r, dst_r = (src, dst)
                scale = None
        else:
            src_r, dst_r = (src, dst)
        if warp_mode == cv2.MOTION_HOMOGRAPHY:
            warp_matrix = np.eye(3, 3, dtype=np.float32)
        else:
            warp_matrix = np.eye(2, 3, dtype=np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, max_iter, eps)
        try:
            cc, warp_matrix = cv2.findTransformECC(src_r, dst_r, warp_matrix, warp_mode, criteria, None, 1)
        except cv2.error as e:
            print('ecc transform failed')
            return (None, None)
        if scale is not None:
            warp_matrix[0, 2] = warp_matrix[0, 2] / scale[0]
            warp_matrix[1, 2] = warp_matrix[1, 2] / scale[1]
        if align:
            sz = src.shape
            if warp_mode == cv2.MOTION_HOMOGRAPHY:
                src_aligned = cv2.warpPerspective(src, warp_matrix, (sz[1], sz[0]), flags=cv2.INTER_LINEAR)
            else:
                src_aligned = cv2.warpAffine(src, warp_matrix, (sz[1], sz[0]), flags=cv2.INTER_LINEAR)
            return (warp_matrix, src_aligned)
        else:
            return (warp_matrix, None)

    def get_matrix(self, matrix):
        eye = np.eye(3)
        dist = np.linalg.norm(eye - matrix)
        if dist < 100:
            return matrix
        else:
            return eye

    def camera_update(self, previous_frame, next_frame):
        warp_matrix, src_aligned = self.ECC(previous_frame, next_frame)
        if warp_matrix is None and src_aligned is None:
            return
        [a, b] = warp_matrix
        warp_matrix = np.array([a, b, [0, 0, 1]])
        warp_matrix = warp_matrix.tolist()
        matrix = self.get_matrix(warp_matrix)
        x1, y1, x2, y2 = self.to_tlbr()
        x1_, y1_, _ = matrix @ np.array([x1, y1, 1]).T
        x2_, y2_, _ = matrix @ np.array([x2, y2, 1]).T
        w, h = (x2_ - x1_, y2_ - y1_)
        cx, cy = (x1_ + w / 2, y1_ + h / 2)
        self.mean[:4] = [cx, cy, w / h, h]

    def increment_age(self):
        self.age += 1
        self.time_since_update += 1

    def predict(self, kf):
        """Propagate the state distribution to the current time step using a
        Kalman filter prediction step.

        Parameters
        ----------
        kf : kalman_filter.KalmanFilter
            The Kalman filter.

        """
        self.mean, self.covariance = self.kf.predict(self.mean, self.covariance)
        self.age += 1
        self.time_since_update += 1

    def update_kf(self, bbox, confidence=0.5):
        self.updates_wo_assignment = self.updates_wo_assignment + 1
        self.mean, self.covariance = self.kf.update(self.mean, self.covariance, bbox, confidence)
        tlbr = self.to_tlbr()
        x_c = int((tlbr[0] + tlbr[2]) / 2)
        y_c = int((tlbr[1] + tlbr[3]) / 2)
        self.q.append(('predupdate', (x_c, y_c)))

    def update(self, detection, class_id, conf):
        """Perform Kalman filter measurement update step and update the feature
        cache.
        Parameters
        ----------
        detection : Detection
            The associated detection.
        """
        self.conf = conf
        self.class_id = class_id.int()
        self.mean, self.covariance = self.kf.update(self.mean, self.covariance, detection.to_xyah(), detection.confidence)
        feature = detection.feature / np.linalg.norm(detection.feature)
        smooth_feat = self.ema_alpha * self.features[-1] + (1 - self.ema_alpha) * feature
        smooth_feat /= np.linalg.norm(smooth_feat)
        self.features = [smooth_feat]
        self.hits += 1
        self.time_since_update = 0
        if self.state == TrackState.Tentative and self.hits >= self._n_init:
            self.state = TrackState.Confirmed
        tlbr = self.to_tlbr()
        x_c = int((tlbr[0] + tlbr[2]) / 2)
        y_c = int((tlbr[1] + tlbr[3]) / 2)
        self.q.append(('observationupdate', (x_c, y_c)))

    def mark_missed(self):
        """Mark this track as missed (no association at the current time step).
        """
        if self.state == TrackState.Tentative:
            self.state = TrackState.Deleted
        elif self.time_since_update > self._max_age:
            self.state = TrackState.Deleted

    def is_tentative(self):
        """Returns True if this track is tentative (unconfirmed).
        """
        return self.state == TrackState.Tentative

    def is_confirmed(self):
        """Returns True if this track is confirmed."""
        return self.state == TrackState.Confirmed

    def is_deleted(self):
        """Returns True if this track is dead and should be deleted."""
        return self.state == TrackState.Deleted

def to_tlbr(self):
    """Get kf estimated current position in bounding box format `(min x, miny, max x,
        max y)`.

        Returns
        -------
        ndarray
            The predicted kf bounding box.

        """
    ret = self.to_tlwh()
    ret[2:] = ret[:2] + ret[2:]
    return ret

def predict(self, kf):
    """Propagate the state distribution to the current time step using a
        Kalman filter prediction step.

        Parameters
        ----------
        kf : kalman_filter.KalmanFilter
            The Kalman filter.

        """
    self.mean, self.covariance = self.kf.predict(self.mean, self.covariance)
    self.age += 1
    self.time_since_update += 1

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
def save_summary(summary, filename):
    import pandas as pd
    writer = pd.ExcelWriter(filename)
    summary.to_excel(writer)
    writer.save()

def assert_in(file, files_to_check):
    if file not in files_to_check:
        raise AssertionError('{} does not exist in the list'.format(str(file)))
    return True

def assert_in_env(check_list: list):
    for item in check_list:
        assert_in(item, environ.keys())
    return True

def write_results(filename, results, data_type):
    if data_type == 'mot':
        save_format = '{frame},{id},{x1},{y1},{w},{h},-1,-1,-1,-1\n'
    elif data_type == 'kitti':
        save_format = '{frame} {id} pedestrian 0 0 -10 {x1} {y1} {x2} {y2} -10 -10 -10 -1000 -1000 -1000 -10\n'
    else:
        raise ValueError(data_type)
    with open(filename, 'w') as f:
        for frame_id, tlwhs, track_ids in results:
            if data_type == 'kitti':
                frame_id -= 1
            for tlwh, track_id in zip(tlwhs, track_ids):
                if track_id < 0:
                    continue
                x1, y1, w, h = tlwh
                x2, y2 = (x1 + w, y1 + h)
                line = save_format.format(frame=frame_id, id=track_id, x1=x1, y1=y1, x2=x2, y2=y2, w=w, h=h)
                f.write(line)

def read_mot_results(filename, is_gt, is_ignore):
    valid_labels = {1}
    ignore_labels = {2, 7, 8, 12}
    results_dict = dict()
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            for line in f.readlines():
                linelist = line.split(',')
                if len(linelist) < 7:
                    continue
                fid = int(linelist[0])
                if fid < 1:
                    continue
                results_dict.setdefault(fid, list())
                if is_gt:
                    if 'MOT16-' in filename or 'MOT17-' in filename:
                        label = int(float(linelist[7]))
                        mark = int(float(linelist[6]))
                        if mark == 0 or label not in valid_labels:
                            continue
                    score = 1
                elif is_ignore:
                    if 'MOT16-' in filename or 'MOT17-' in filename:
                        label = int(float(linelist[7]))
                        vis_ratio = float(linelist[8])
                        if label not in ignore_labels and vis_ratio >= 0:
                            continue
                    else:
                        continue
                    score = 1
                else:
                    score = float(linelist[6])
                tlwh = tuple(map(float, linelist[2:6]))
                target_id = int(linelist[1])
                results_dict[fid].append((tlwh, target_id, score))
    return results_dict

class BaseJsonLogger(object):
    """
    This is the base class that returns __dict__ of its own
    it also returns the dicts of objects in the attributes that are list instances

    """

    def dic(self):
        out = {}
        for k, v in self.__dict__.items():
            if hasattr(v, 'dic'):
                out[k] = v.dic()
            elif isinstance(v, list):
                out[k] = self.list(v)
            else:
                out[k] = v
        return out

    @staticmethod
    def list(values):
        return [v.dic() if hasattr(v, 'dic') else v for v in values]

def dic(self):
    out = {}
    for k, v in self.__dict__.items():
        if hasattr(v, 'dic'):
            out[k] = v.dic()
        elif isinstance(v, list):
            out[k] = self.list(v)
        else:
            out[k] = v
    return out

@staticmethod
def list(values):
    return [v.dic() if hasattr(v, 'dic') else v for v in values]

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

def __init__(self, top_k_labels: int=1):
    self.frames = {}
    self.video_details = self.video_details = dict(frame_width=None, frame_height=None, frame_rate=None, video_name=None)
    self.top_k_labels = top_k_labels
    self.start_time = datetime.now()

def frame_exists(self, frame_id: int) -> bool:
    """
        Args:
            frame_id (int):

        Returns:
            bool: true if frame_id is recognized
        """
    return frame_id in self.frames.keys()

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

class YamlParser(edict):
    """
    This is yaml parser based on EasyDict.
    """

    def __init__(self, cfg_dict=None, config_file=None):
        if cfg_dict is None:
            cfg_dict = {}
        if config_file is not None:
            assert os.path.isfile(config_file)
            with open(config_file, 'r') as fo:
                yaml_ = yaml.load(fo.read(), Loader=yaml.FullLoader)
                cfg_dict.update(yaml_)
        super(YamlParser, self).__init__(cfg_dict)

    def merge_from_file(self, config_file):
        with open(config_file, 'r') as fo:
            yaml_ = yaml.load(fo.read(), Loader=yaml.FullLoader)
            self.update(yaml_)

    def merge_from_dict(self, config_dict):
        self.update(config_dict)

def __init__(self, cfg_dict=None, config_file=None):
    if cfg_dict is None:
        cfg_dict = {}
    if config_file is not None:
        assert os.path.isfile(config_file)
        with open(config_file, 'r') as fo:
            yaml_ = yaml.load(fo.read(), Loader=yaml.FullLoader)
            cfg_dict.update(yaml_)
    super(YamlParser, self).__init__(cfg_dict)

def merge_from_file(self, config_file):
    with open(config_file, 'r') as fo:
        yaml_ = yaml.load(fo.read(), Loader=yaml.FullLoader)
        self.update(yaml_)

def merge_from_dict(self, config_dict):
    self.update(config_dict)

def show_downloadeable_models():
    print('\nAvailable .pt ReID models for automatic download')
    print(list(__trained_urls.keys()))

def load_pretrained_weights(model, weight_path):
    """Loads pretrianed weights to model.

    Features::
        - Incompatible layers (unmatched in name or size) will be ignored.
        - Can automatically deal with keys containing "module.".

    Args:
        model (nn.Module): network model.
        weight_path (str): path to pretrained weights.

    Examples::
        >>> from torchreid.utils import load_pretrained_weights
        >>> weight_path = 'log/my_model/model-best.pth.tar'
        >>> load_pretrained_weights(model, weight_path)
    """
    checkpoint = torch.load(weight_path)
    if 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    else:
        state_dict = checkpoint
    model_dict = model.state_dict()
    new_state_dict = OrderedDict()
    matched_layers, discarded_layers = ([], [])
    for k, v in state_dict.items():
        if k.startswith('module.'):
            k = k[7:]
        if k in model_dict and model_dict[k].size() == v.size():
            new_state_dict[k] = v
            matched_layers.append(k)
        else:
            discarded_layers.append(k)
    model_dict.update(new_state_dict)
    model.load_state_dict(model_dict)
    if len(matched_layers) == 0:
        warnings.warn('The pretrained weights "{}" cannot be loaded, please check the key names manually (** ignored and continue **)'.format(weight_path))
    else:
        print('Successfully loaded pretrained weights from "{}"'.format(weight_path))
        if len(discarded_layers) > 0:
            print('** The following layers are discarded due to unmatched keys or layer size: {}'.format(discarded_layers))

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

def load_imagenet_weights(self):
    settings = pretrained_settings['inceptionresnetv2']['imagenet']
    pretrain_dict = model_zoo.load_url(settings['url'])
    model_dict = self.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    self.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    pattern = re.compile('^(.*denselayer\\d+\\.(?:norm|relu|conv))\\.((?:[12])\\.(?:weight|bias|running_mean|running_var))$')
    for key in list(pretrain_dict.keys()):
        res = pattern.match(key)
        if res:
            new_key = res.group(1) + res.group(2)
            pretrain_dict[new_key] = pretrain_dict[key]
            del pretrain_dict[key]
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url, map_location=None)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def show_avai_models():
    """Displays available models.

    Examples::
        >>> from torchreid import models
        >>> models.show_avai_models()
    """
    print(list(__model_factory.keys()))

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, key=''):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    import os
    import errno
    import gdown
    from collections import OrderedDict

    def _get_torch_home():
        ENV_TORCH_HOME = 'TORCH_HOME'
        ENV_XDG_CACHE_HOME = 'XDG_CACHE_HOME'
        DEFAULT_CACHE_DIR = '~/.cache'
        torch_home = os.path.expanduser(os.getenv(ENV_TORCH_HOME, os.path.join(os.getenv(ENV_XDG_CACHE_HOME, DEFAULT_CACHE_DIR), 'torch')))
        return torch_home
    torch_home = _get_torch_home()
    model_dir = os.path.join(torch_home, 'checkpoints')
    try:
        os.makedirs(model_dir)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    filename = key + '_imagenet.pth'
    cached_file = os.path.join(model_dir, filename)
    if not os.path.exists(cached_file):
        gdown.download(pretrained_urls[key], cached_file, quiet=False)
    state_dict = torch.load(cached_file)
    model_dict = model.state_dict()
    new_state_dict = OrderedDict()
    matched_layers, discarded_layers = ([], [])
    for k, v in state_dict.items():
        if k.startswith('module.'):
            k = k[7:]
        if k in model_dict and model_dict[k].size() == v.size():
            new_state_dict[k] = v
            matched_layers.append(k)
        else:
            discarded_layers.append(k)
    model_dict.update(new_state_dict)
    model.load_state_dict(model_dict)
    if len(matched_layers) == 0:
        warnings.warn('The pretrained weights from "{}" cannot be loaded, please check the key names manually (** ignored and continue **)'.format(cached_file))
    else:
        print('Successfully loaded imagenet pretrained weights from "{}"'.format(cached_file))
        if len(discarded_layers) > 0:
            print('** The following layers are discarded due to unmatched keys or layer size: {}'.format(discarded_layers))

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    if model_url is None:
        import warnings
        warnings.warn('ImageNet pretrained weights are unavailable for this model')
        return
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initialize models with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

def init_pretrained_weights(model, key=''):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    import os
    import errno
    import gdown
    from collections import OrderedDict

    def _get_torch_home():
        ENV_TORCH_HOME = 'TORCH_HOME'
        ENV_XDG_CACHE_HOME = 'XDG_CACHE_HOME'
        DEFAULT_CACHE_DIR = '~/.cache'
        torch_home = os.path.expanduser(os.getenv(ENV_TORCH_HOME, os.path.join(os.getenv(ENV_XDG_CACHE_HOME, DEFAULT_CACHE_DIR), 'torch')))
        return torch_home
    torch_home = _get_torch_home()
    model_dir = os.path.join(torch_home, 'checkpoints')
    try:
        os.makedirs(model_dir)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    filename = key + '_imagenet.pth'
    cached_file = os.path.join(model_dir, filename)
    if not os.path.exists(cached_file):
        gdown.download(pretrained_urls[key], cached_file, quiet=False)
    state_dict = torch.load(cached_file)
    model_dict = model.state_dict()
    new_state_dict = OrderedDict()
    matched_layers, discarded_layers = ([], [])
    for k, v in state_dict.items():
        if k.startswith('module.'):
            k = k[7:]
        if k in model_dict and model_dict[k].size() == v.size():
            new_state_dict[k] = v
            matched_layers.append(k)
        else:
            discarded_layers.append(k)
    model_dict.update(new_state_dict)
    model.load_state_dict(model_dict)
    if len(matched_layers) == 0:
        warnings.warn('The pretrained weights from "{}" cannot be loaded, please check the key names manually (** ignored and continue **)'.format(cached_file))
    else:
        print('Successfully loaded imagenet pretrained weights from "{}"'.format(cached_file))
        if len(discarded_layers) > 0:
            print('** The following layers are discarded due to unmatched keys or layer size: {}'.format(discarded_layers))

def init_pretrained_weights(model, model_url):
    """Initializes model with pretrained weights.
    
    Layers that don't match with pretrained layers in name or size are kept unchanged.
    """
    pretrain_dict = model_zoo.load_url(model_url)
    model_dict = model.state_dict()
    pretrain_dict = {k: v for k, v in pretrain_dict.items() if k in model_dict and model_dict[k].size() == v.size()}
    model_dict.update(pretrain_dict)
    model.load_state_dict(model_dict)

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

def dump_cache(self):
    with open(self.cache_path, 'wb') as fp:
        pickle.dump(self.cache, fp)

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

def load_cache(self, path):
    self.cache_name = path
    cache_path = self.cache_path.format(path)
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as fp:
            self.cache = pickle.load(fp)

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

class ReIDDetectMultiBackend(nn.Module):

    def __init__(self, weights='osnet_x0_25_msmt17.pt', device=torch.device('cpu'), fp16=False):
        super().__init__()
        w = weights[0] if isinstance(weights, list) else weights
        self.pt, self.jit, self.onnx, self.xml, self.engine, self.tflite = self.model_type(w)
        self.fp16 = fp16
        self.fp16 &= self.pt or self.jit or self.engine
        self.device = device
        self.image_size = (256, 128)
        self.pixel_mean = [0.485, 0.456, 0.406]
        self.pixel_std = [0.229, 0.224, 0.225]
        self.transforms = []
        self.transforms += [T.Resize(self.image_size)]
        self.transforms += [T.ToTensor()]
        self.transforms += [T.Normalize(mean=self.pixel_mean, std=self.pixel_std)]
        self.preprocess = T.Compose(self.transforms)
        self.to_pil = T.ToPILImage()
        model_name = get_model_name(w)
        if w.suffix == '.pt':
            model_url = get_model_url(w)
            if not file_exists(w) and model_url is not None:
                gdown.download(model_url, str(w), quiet=False)
            elif file_exists(w):
                pass
            else:
                print(f'No URL associated to the chosen StrongSORT weights ({w}). Choose between:')
                show_downloadeable_models()
                exit()
        self.model = build_model(model_name, num_classes=1, pretrained=not (w and w.is_file()), use_gpu=device)
        if self.pt:
            if w and w.is_file() and (w.suffix == '.pt'):
                load_pretrained_weights(self.model, w)
            self.model.to(device).eval()
            self.model.half() if self.fp16 else self.model.float()
        elif self.jit:
            LOGGER.info(f'Loading {w} for TorchScript inference...')
            self.model = torch.jit.load(w)
            self.model.half() if self.fp16 else self.model.float()
        elif self.onnx:
            LOGGER.info(f'Loading {w} for ONNX Runtime inference...')
            cuda = torch.cuda.is_available() and device.type != 'cpu'
            import onnxruntime
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
            self.session = onnxruntime.InferenceSession(str(w), providers=providers)
        elif self.engine:
            LOGGER.info(f'Loading {w} for TensorRT inference...')
            import tensorrt as trt
            check_version(trt.__version__, '7.0.0', hard=True)
            if device.type == 'cpu':
                device = torch.device('cuda:0')
            Binding = namedtuple('Binding', ('name', 'dtype', 'shape', 'data', 'ptr'))
            logger = trt.Logger(trt.Logger.INFO)
            with open(w, 'rb') as f, trt.Runtime(logger) as runtime:
                self.model_ = runtime.deserialize_cuda_engine(f.read())
            self.context = self.model_.create_execution_context()
            self.bindings = OrderedDict()
            self.fp16 = False
            dynamic = False
            for index in range(self.model_.num_bindings):
                name = self.model_.get_binding_name(index)
                dtype = trt.nptype(self.model_.get_binding_dtype(index))
                if self.model_.binding_is_input(index):
                    if -1 in tuple(self.model_.get_binding_shape(index)):
                        dynamic = True
                        self.context.set_binding_shape(index, tuple(self.model_.get_profile_shape(0, index)[2]))
                    if dtype == np.float16:
                        self.fp16 = True
                shape = tuple(self.context.get_binding_shape(index))
                im = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
                self.bindings[name] = Binding(name, dtype, shape, im, int(im.data_ptr()))
            self.binding_addrs = OrderedDict(((n, d.ptr) for n, d in self.bindings.items()))
            batch_size = self.bindings['images'].shape[0]
        elif self.xml:
            LOGGER.info(f'Loading {w} for OpenVINO inference...')
            check_requirements(('openvino',))
            from openvino.runtime import Core, Layout, get_batch
            ie = Core()
            if not Path(w).is_file():
                w = next(Path(w).glob('*.xml'))
            network = ie.read_model(model=w, weights=Path(w).with_suffix('.bin'))
            if network.get_parameters()[0].get_layout().empty:
                network.get_parameters()[0].set_layout(Layout('NCWH'))
            batch_dim = get_batch(network)
            if batch_dim.is_static:
                batch_size = batch_dim.get_length()
            self.executable_network = ie.compile_model(network, device_name='CPU')
            self.output_layer = next(iter(self.executable_network.outputs))
        elif self.tflite:
            LOGGER.info(f'Loading {w} for TensorFlow Lite inference...')
            try:
                from tflite_runtime.interpreter import Interpreter, load_delegate
            except ImportError:
                import tensorflow as tf
                Interpreter, load_delegate = (tf.lite.Interpreter, tf.lite.experimental.load_delegate)
            self.interpreter = tf.lite.Interpreter(model_path=w)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            input_data = np.array(np.random.random_sample((1, 256, 128, 3)), dtype=np.float32)
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        else:
            print('This model framework is not supported yet!')
            exit()

    @staticmethod
    def model_type(p='path/to/model.pt'):
        from trackers.reid_export import export_formats
        sf = list(export_formats().Suffix)
        check_suffix(p, sf)
        types = [s in Path(p).name for s in sf]
        return types

    def _preprocess(self, im_batch):
        images = []
        for element in im_batch:
            image = self.to_pil(element)
            image = self.preprocess(image)
            images.append(image)
        images = torch.stack(images, dim=0)
        images = images.to(self.device)
        return images

    def forward(self, im_batch):
        im_batch = self._preprocess(im_batch)
        if self.fp16 and im_batch.dtype != torch.float16:
            im_batch = im_batch.half()
        features = []
        if self.pt:
            features = self.model(im_batch)
        elif self.jit:
            features = self.model(im_batch)
        elif self.onnx:
            im_batch = im_batch.cpu().numpy()
            features = self.session.run([self.session.get_outputs()[0].name], {self.session.get_inputs()[0].name: im_batch})[0]
        elif self.engine:
            if True and im_batch.shape != self.bindings['images'].shape:
                i_in, i_out = (self.model_.get_binding_index(x) for x in ('images', 'output'))
                self.context.set_binding_shape(i_in, im_batch.shape)
                self.bindings['images'] = self.bindings['images']._replace(shape=im_batch.shape)
                self.bindings['output'].data.resize_(tuple(self.context.get_binding_shape(i_out)))
            s = self.bindings['images'].shape
            assert im_batch.shape == s, f'input size {im_batch.shape} {('>' if self.dynamic else 'not equal to')} max model size {s}'
            self.binding_addrs['images'] = int(im_batch.data_ptr())
            self.context.execute_v2(list(self.binding_addrs.values()))
            features = self.bindings['output'].data
        elif self.xml:
            im_batch = im_batch.cpu().numpy()
            features = self.executable_network([im_batch])[self.output_layer]
        else:
            print('Framework not supported at the moment, we are working on it...')
            exit()
        if isinstance(features, (list, tuple)):
            return self.from_numpy(features[0]) if len(features) == 1 else [self.from_numpy(x) for x in features]
        else:
            return self.from_numpy(features)

    def from_numpy(self, x):
        return torch.from_numpy(x).to(self.device) if isinstance(x, np.ndarray) else x

    def warmup(self, imgsz=[(256, 128, 3)]):
        warmup_types = (self.pt, self.jit, self.onnx, self.engine, self.tflite)
        if any(warmup_types) and self.device.type != 'cpu':
            im = [np.empty(*imgsz).astype(np.uint8)]
            for _ in range(2 if self.jit else 1):
                self.forward(im)

def __init__(self, weights='osnet_x0_25_msmt17.pt', device=torch.device('cpu'), fp16=False):
    super().__init__()
    w = weights[0] if isinstance(weights, list) else weights
    self.pt, self.jit, self.onnx, self.xml, self.engine, self.tflite = self.model_type(w)
    self.fp16 = fp16
    self.fp16 &= self.pt or self.jit or self.engine
    self.device = device
    self.image_size = (256, 128)
    self.pixel_mean = [0.485, 0.456, 0.406]
    self.pixel_std = [0.229, 0.224, 0.225]
    self.transforms = []
    self.transforms += [T.Resize(self.image_size)]
    self.transforms += [T.ToTensor()]
    self.transforms += [T.Normalize(mean=self.pixel_mean, std=self.pixel_std)]
    self.preprocess = T.Compose(self.transforms)
    self.to_pil = T.ToPILImage()
    model_name = get_model_name(w)
    if w.suffix == '.pt':
        model_url = get_model_url(w)
        if not file_exists(w) and model_url is not None:
            gdown.download(model_url, str(w), quiet=False)
        elif file_exists(w):
            pass
        else:
            print(f'No URL associated to the chosen StrongSORT weights ({w}). Choose between:')
            show_downloadeable_models()
            exit()
    self.model = build_model(model_name, num_classes=1, pretrained=not (w and w.is_file()), use_gpu=device)
    if self.pt:
        if w and w.is_file() and (w.suffix == '.pt'):
            load_pretrained_weights(self.model, w)
        self.model.to(device).eval()
        self.model.half() if self.fp16 else self.model.float()
    elif self.jit:
        LOGGER.info(f'Loading {w} for TorchScript inference...')
        self.model = torch.jit.load(w)
        self.model.half() if self.fp16 else self.model.float()
    elif self.onnx:
        LOGGER.info(f'Loading {w} for ONNX Runtime inference...')
        cuda = torch.cuda.is_available() and device.type != 'cpu'
        import onnxruntime
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
        self.session = onnxruntime.InferenceSession(str(w), providers=providers)
    elif self.engine:
        LOGGER.info(f'Loading {w} for TensorRT inference...')
        import tensorrt as trt
        check_version(trt.__version__, '7.0.0', hard=True)
        if device.type == 'cpu':
            device = torch.device('cuda:0')
        Binding = namedtuple('Binding', ('name', 'dtype', 'shape', 'data', 'ptr'))
        logger = trt.Logger(trt.Logger.INFO)
        with open(w, 'rb') as f, trt.Runtime(logger) as runtime:
            self.model_ = runtime.deserialize_cuda_engine(f.read())
        self.context = self.model_.create_execution_context()
        self.bindings = OrderedDict()
        self.fp16 = False
        dynamic = False
        for index in range(self.model_.num_bindings):
            name = self.model_.get_binding_name(index)
            dtype = trt.nptype(self.model_.get_binding_dtype(index))
            if self.model_.binding_is_input(index):
                if -1 in tuple(self.model_.get_binding_shape(index)):
                    dynamic = True
                    self.context.set_binding_shape(index, tuple(self.model_.get_profile_shape(0, index)[2]))
                if dtype == np.float16:
                    self.fp16 = True
            shape = tuple(self.context.get_binding_shape(index))
            im = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
            self.bindings[name] = Binding(name, dtype, shape, im, int(im.data_ptr()))
        self.binding_addrs = OrderedDict(((n, d.ptr) for n, d in self.bindings.items()))
        batch_size = self.bindings['images'].shape[0]
    elif self.xml:
        LOGGER.info(f'Loading {w} for OpenVINO inference...')
        check_requirements(('openvino',))
        from openvino.runtime import Core, Layout, get_batch
        ie = Core()
        if not Path(w).is_file():
            w = next(Path(w).glob('*.xml'))
        network = ie.read_model(model=w, weights=Path(w).with_suffix('.bin'))
        if network.get_parameters()[0].get_layout().empty:
            network.get_parameters()[0].set_layout(Layout('NCWH'))
        batch_dim = get_batch(network)
        if batch_dim.is_static:
            batch_size = batch_dim.get_length()
        self.executable_network = ie.compile_model(network, device_name='CPU')
        self.output_layer = next(iter(self.executable_network.outputs))
    elif self.tflite:
        LOGGER.info(f'Loading {w} for TensorFlow Lite inference...')
        try:
            from tflite_runtime.interpreter import Interpreter, load_delegate
        except ImportError:
            import tensorflow as tf
            Interpreter, load_delegate = (tf.lite.Interpreter, tf.lite.experimental.load_delegate)
        self.interpreter = tf.lite.Interpreter(model_path=w)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        input_data = np.array(np.random.random_sample((1, 256, 128, 3)), dtype=np.float32)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
    else:
        print('This model framework is not supported yet!')
        exit()

@staticmethod
def model_type(p='path/to/model.pt'):
    from trackers.reid_export import export_formats
    sf = list(export_formats().Suffix)
    check_suffix(p, sf)
    types = [s in Path(p).name for s in sf]
    return types

def forward(self, im_batch):
    im_batch = self._preprocess(im_batch)
    if self.fp16 and im_batch.dtype != torch.float16:
        im_batch = im_batch.half()
    features = []
    if self.pt:
        features = self.model(im_batch)
    elif self.jit:
        features = self.model(im_batch)
    elif self.onnx:
        im_batch = im_batch.cpu().numpy()
        features = self.session.run([self.session.get_outputs()[0].name], {self.session.get_inputs()[0].name: im_batch})[0]
    elif self.engine:
        if True and im_batch.shape != self.bindings['images'].shape:
            i_in, i_out = (self.model_.get_binding_index(x) for x in ('images', 'output'))
            self.context.set_binding_shape(i_in, im_batch.shape)
            self.bindings['images'] = self.bindings['images']._replace(shape=im_batch.shape)
            self.bindings['output'].data.resize_(tuple(self.context.get_binding_shape(i_out)))
        s = self.bindings['images'].shape
        assert im_batch.shape == s, f'input size {im_batch.shape} {('>' if self.dynamic else 'not equal to')} max model size {s}'
        self.binding_addrs['images'] = int(im_batch.data_ptr())
        self.context.execute_v2(list(self.binding_addrs.values()))
        features = self.bindings['output'].data
    elif self.xml:
        im_batch = im_batch.cpu().numpy()
        features = self.executable_network([im_batch])[self.output_layer]
    else:
        print('Framework not supported at the moment, we are working on it...')
        exit()
    if isinstance(features, (list, tuple)):
        return self.from_numpy(features[0]) if len(features) == 1 else [self.from_numpy(x) for x in features]
    else:
        return self.from_numpy(features)

def k_previous_obs(observations, cur_age, k):
    if len(observations) == 0:
        return [-1, -1, -1, -1, -1]
    for i in range(k):
        dt = k - i
        if cur_age - dt in observations:
            return observations[cur_age - dt]
    max_age = max(observations.keys())
    return observations[max_age]

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

def batch_filter(x, P, zs, Fs, Qs, Hs, Rs, Bs=None, us=None, update_first=False, saver=None):
    """
    Batch processes a sequences of measurements.
    Parameters
    ----------
    zs : list-like
        list of measurements at each time step. Missing measurements must be
        represented by None.
    Fs : list-like
        list of values to use for the state transition matrix matrix.
    Qs : list-like
        list of values to use for the process error
        covariance.
    Hs : list-like
        list of values to use for the measurement matrix.
    Rs : list-like
        list of values to use for the measurement error
        covariance.
    Bs : list-like, optional
        list of values to use for the control transition matrix;
        a value of None in any position will cause the filter
        to use `self.B` for that time step.
    us : list-like, optional
        list of values to use for the control input vector;
        a value of None in any position will cause the filter to use
        0 for that time step.
    update_first : bool, optional
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
        zs = [t + random.randn()*4 for t in range (40)]
        Fs = [kf.F for t in range (40)]
        Hs = [kf.H for t in range (40)]
        (mu, cov, _, _) = kf.batch_filter(zs, Rs=R_list, Fs=Fs, Hs=Hs, Qs=None,
                                          Bs=None, us=None, update_first=False)
        (xs, Ps, Ks, Pps) = kf.rts_smoother(mu, cov, Fs=Fs, Qs=None)
    """
    n = np.size(zs, 0)
    dim_x = x.shape[0]
    if x.ndim == 1:
        means = zeros((n, dim_x))
        means_p = zeros((n, dim_x))
    else:
        means = zeros((n, dim_x, 1))
        means_p = zeros((n, dim_x, 1))
    covariances = zeros((n, dim_x, dim_x))
    covariances_p = zeros((n, dim_x, dim_x))
    if us is None:
        us = [0.0] * n
        Bs = [0.0] * n
    if update_first:
        for i, (z, F, Q, H, R, B, u) in enumerate(zip(zs, Fs, Qs, Hs, Rs, Bs, us)):
            x, P = update(x, P, z, R=R, H=H)
            means[i, :] = x
            covariances[i, :, :] = P
            x, P = predict(x, P, u=u, B=B, F=F, Q=Q)
            means_p[i, :] = x
            covariances_p[i, :, :] = P
            if saver is not None:
                saver.save()
    else:
        for i, (z, F, Q, H, R, B, u) in enumerate(zip(zs, Fs, Qs, Hs, Rs, Bs, us)):
            x, P = predict(x, P, u=u, B=B, F=F, Q=Q)
            means_p[i, :] = x
            covariances_p[i, :, :] = P
            x, P = update(x, P, z, R=R, H=H)
            means[i, :] = x
            covariances[i, :, :] = P
            if saver is not None:
                saver.save()
    return (means, covariances, means_p, covariances_p)

def k_previous_obs(observations, cur_age, k):
    if len(observations) == 0:
        return [-1, -1, -1, -1, -1]
    for i in range(k):
        dt = k - i
        if cur_age - dt in observations:
            return observations[cur_age - dt]
    max_age = max(observations.keys())
    return observations[max_age]

class KalmanBoxTracker(object):
    """
    This class represents the internal state of individual tracked objects observed as bbox.
    """
    count = 0

    def __init__(self, bbox, cls, delta_t=3, orig=False):
        """
        Initialises a tracker using initial bounding box.

        """
        if not orig:
            from .kalmanfilter import KalmanFilterNew as KalmanFilter
            self.kf = KalmanFilter(dim_x=7, dim_z=4)
        else:
            from filterpy.kalman import KalmanFilter
            self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0], [0, 1, 0, 0, 0, 1, 0], [0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 1]])
        self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0]])
        self.kf.R[2:, 2:] *= 10.0
        self.kf.P[4:, 4:] *= 1000.0
        self.kf.P *= 10.0
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        self.kf.x[:4] = convert_bbox_to_z(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
        self.conf = bbox[-1]
        self.cls = cls
        "\n        NOTE: [-1,-1,-1,-1,-1] is a compromising placeholder for non-observation status, the same for the return of \n        function k_previous_obs. It is ugly and I do not like it. But to support generate observation array in a \n        fast and unified way, which you would see below k_observations = np.array([k_previous_obs(...]]), let's bear it for now.\n        "
        self.last_observation = np.array([-1, -1, -1, -1, -1])
        self.observations = dict()
        self.history_observations = []
        self.velocity = None
        self.delta_t = delta_t

    def update(self, bbox, cls):
        """
        Updates the state vector with observed bbox.
        """
        if bbox is not None:
            self.conf = bbox[-1]
            self.cls = cls
            if self.last_observation.sum() >= 0:
                previous_box = None
                for i in range(self.delta_t):
                    dt = self.delta_t - i
                    if self.age - dt in self.observations:
                        previous_box = self.observations[self.age - dt]
                        break
                if previous_box is None:
                    previous_box = self.last_observation
                '\n                  Estimate the track speed direction with observations \\Delta t steps away\n                '
                self.velocity = speed_direction(previous_box, bbox)
            '\n              Insert new observations. This is a ugly way to maintain both self.observations\n              and self.history_observations. Bear it for the moment.\n            '
            self.last_observation = bbox
            self.observations[self.age] = bbox
            self.history_observations.append(bbox)
            self.time_since_update = 0
            self.history = []
            self.hits += 1
            self.hit_streak += 1
            self.kf.update(convert_bbox_to_z(bbox))
        else:
            self.kf.update(bbox)

    def predict(self):
        """
        Advances the state vector and returns the predicted bounding box estimate.
        """
        if self.kf.x[6] + self.kf.x[2] <= 0:
            self.kf.x[6] *= 0.0
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(convert_x_to_bbox(self.kf.x))
        return self.history[-1]

    def get_state(self):
        """
        Returns the current bounding box estimate.
        """
        return convert_x_to_bbox(self.kf.x)

def predict(self):
    """
        Advances the state vector and returns the predicted bounding box estimate.
        """
    if self.kf.x[6] + self.kf.x[2] <= 0:
        self.kf.x[6] *= 0.0
    self.kf.predict()
    self.age += 1
    if self.time_since_update > 0:
        self.hit_streak = 0
    self.time_since_update += 1
    self.history.append(convert_x_to_bbox(self.kf.x))
    return self.history[-1]

def get_state(self):
    """
        Returns the current bounding box estimate.
        """
    return convert_x_to_bbox(self.kf.x)

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

def batch_filter(x, P, zs, Fs, Qs, Hs, Rs, Bs=None, us=None, update_first=False, saver=None):
    """
    Batch processes a sequences of measurements.
    Parameters
    ----------
    zs : list-like
        list of measurements at each time step. Missing measurements must be
        represented by None.
    Fs : list-like
        list of values to use for the state transition matrix matrix.
    Qs : list-like
        list of values to use for the process error
        covariance.
    Hs : list-like
        list of values to use for the measurement matrix.
    Rs : list-like
        list of values to use for the measurement error
        covariance.
    Bs : list-like, optional
        list of values to use for the control transition matrix;
        a value of None in any position will cause the filter
        to use `self.B` for that time step.
    us : list-like, optional
        list of values to use for the control input vector;
        a value of None in any position will cause the filter to use
        0 for that time step.
    update_first : bool, optional
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
        zs = [t + random.randn()*4 for t in range (40)]
        Fs = [kf.F for t in range (40)]
        Hs = [kf.H for t in range (40)]
        (mu, cov, _, _) = kf.batch_filter(zs, Rs=R_list, Fs=Fs, Hs=Hs, Qs=None,
                                          Bs=None, us=None, update_first=False)
        (xs, Ps, Ks, Pps) = kf.rts_smoother(mu, cov, Fs=Fs, Qs=None)
    """
    n = np.size(zs, 0)
    dim_x = x.shape[0]
    if x.ndim == 1:
        means = zeros((n, dim_x))
        means_p = zeros((n, dim_x))
    else:
        means = zeros((n, dim_x, 1))
        means_p = zeros((n, dim_x, 1))
    covariances = zeros((n, dim_x, dim_x))
    covariances_p = zeros((n, dim_x, dim_x))
    if us is None:
        us = [0.0] * n
        Bs = [0.0] * n
    if update_first:
        for i, (z, F, Q, H, R, B, u) in enumerate(zip(zs, Fs, Qs, Hs, Rs, Bs, us)):
            x, P = update(x, P, z, R=R, H=H)
            means[i, :] = x
            covariances[i, :, :] = P
            x, P = predict(x, P, u=u, B=B, F=F, Q=Q)
            means_p[i, :] = x
            covariances_p[i, :, :] = P
            if saver is not None:
                saver.save()
    else:
        for i, (z, F, Q, H, R, B, u) in enumerate(zip(zs, Fs, Qs, Hs, Rs, Bs, us)):
            x, P = predict(x, P, u=u, B=B, F=F, Q=Q)
            means_p[i, :] = x
            covariances_p[i, :, :] = P
            x, P = update(x, P, z, R=R, H=H)
            means[i, :] = x
            covariances[i, :, :] = P
            if saver is not None:
                saver.save()
    return (means, covariances, means_p, covariances_p)

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

def predict(self):
    mean_state = self.mean.copy()
    if self.state != TrackState.Tracked:
        mean_state[7] = 0
    self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)

def sub_stracks(tlista, tlistb):
    stracks = {}
    for t in tlista:
        stracks[t.track_id] = t
    for t in tlistb:
        tid = t.track_id
        if stracks.get(tid, 0):
            del stracks[tid]
    return list(stracks.values())

def _indices_to_matches(cost_matrix, indices, thresh):
    matched_cost = cost_matrix[tuple(zip(*indices))]
    matched_mask = matched_cost <= thresh
    matches = indices[matched_mask]
    unmatched_a = tuple(set(range(cost_matrix.shape[0])) - set(matches[:, 0]))
    unmatched_b = tuple(set(range(cost_matrix.shape[1])) - set(matches[:, 1]))
    return (matches, unmatched_a, unmatched_b)

class ReIDDetectMultiBackend(nn.Module):

    def __init__(self, weights='osnet_x0_25_msmt17.pt', device=torch.device('cpu'), fp16=False):
        super().__init__()
        w = weights[0] if isinstance(weights, list) else weights
        self.pt, self.jit, self.onnx, self.xml, self.engine, self.tflite = self.model_type(w)
        self.fp16 = fp16
        self.fp16 &= self.pt or self.jit or self.engine
        self.device = device
        self.image_size = (256, 128)
        self.pixel_mean = [0.485, 0.456, 0.406]
        self.pixel_std = [0.229, 0.224, 0.225]
        self.transforms = []
        self.transforms += [T.Resize(self.image_size)]
        self.transforms += [T.ToTensor()]
        self.transforms += [T.Normalize(mean=self.pixel_mean, std=self.pixel_std)]
        self.preprocess = T.Compose(self.transforms)
        self.to_pil = T.ToPILImage()
        model_name = get_model_name(w)
        if w.suffix == '.pt':
            model_url = get_model_url(w)
            if not file_exists(w) and model_url is not None:
                gdown.download(model_url, str(w), quiet=False)
            elif file_exists(w):
                pass
            else:
                print(f'No URL associated to the chosen StrongSORT weights ({w}). Choose between:')
                show_downloadeable_models()
                exit()
        self.model = build_model(model_name, num_classes=1, pretrained=not (w and w.is_file()), use_gpu=device)
        if self.pt:
            if w and w.is_file() and (w.suffix == '.pt'):
                load_pretrained_weights(self.model, w)
            self.model.to(device).eval()
            self.model.half() if self.fp16 else self.model.float()
        elif self.jit:
            LOGGER.info(f'Loading {w} for TorchScript inference...')
            self.model = torch.jit.load(w)
            self.model.half() if self.fp16 else self.model.float()
        elif self.onnx:
            LOGGER.info(f'Loading {w} for ONNX Runtime inference...')
            cuda = torch.cuda.is_available() and device.type != 'cpu'
            import onnxruntime
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
            self.session = onnxruntime.InferenceSession(str(w), providers=providers)
        elif self.engine:
            LOGGER.info(f'Loading {w} for TensorRT inference...')
            import tensorrt as trt
            check_version(trt.__version__, '7.0.0', hard=True)
            if device.type == 'cpu':
                device = torch.device('cuda:0')
            Binding = namedtuple('Binding', ('name', 'dtype', 'shape', 'data', 'ptr'))
            logger = trt.Logger(trt.Logger.INFO)
            with open(w, 'rb') as f, trt.Runtime(logger) as runtime:
                self.model_ = runtime.deserialize_cuda_engine(f.read())
            self.context = self.model_.create_execution_context()
            self.bindings = OrderedDict()
            self.fp16 = False
            dynamic = False
            for index in range(self.model_.num_bindings):
                name = self.model_.get_binding_name(index)
                dtype = trt.nptype(self.model_.get_binding_dtype(index))
                if self.model_.binding_is_input(index):
                    if -1 in tuple(self.model_.get_binding_shape(index)):
                        dynamic = True
                        self.context.set_binding_shape(index, tuple(self.model_.get_profile_shape(0, index)[2]))
                    if dtype == np.float16:
                        self.fp16 = True
                shape = tuple(self.context.get_binding_shape(index))
                im = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
                self.bindings[name] = Binding(name, dtype, shape, im, int(im.data_ptr()))
            self.binding_addrs = OrderedDict(((n, d.ptr) for n, d in self.bindings.items()))
            batch_size = self.bindings['images'].shape[0]
        elif self.xml:
            LOGGER.info(f'Loading {w} for OpenVINO inference...')
            check_requirements(('openvino',))
            from openvino.runtime import Core, Layout, get_batch
            ie = Core()
            if not Path(w).is_file():
                w = next(Path(w).glob('*.xml'))
            network = ie.read_model(model=w, weights=Path(w).with_suffix('.bin'))
            if network.get_parameters()[0].get_layout().empty:
                network.get_parameters()[0].set_layout(Layout('NCWH'))
            batch_dim = get_batch(network)
            if batch_dim.is_static:
                batch_size = batch_dim.get_length()
            self.executable_network = ie.compile_model(network, device_name='CPU')
            self.output_layer = next(iter(self.executable_network.outputs))
        elif self.tflite:
            LOGGER.info(f'Loading {w} for TensorFlow Lite inference...')
            try:
                from tflite_runtime.interpreter import Interpreter, load_delegate
            except ImportError:
                import tensorflow as tf
                Interpreter, load_delegate = (tf.lite.Interpreter, tf.lite.experimental.load_delegate)
            self.interpreter = tf.lite.Interpreter(model_path=w)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            input_data = np.array(np.random.random_sample((1, 256, 128, 3)), dtype=np.float32)
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        else:
            print('This model framework is not supported yet!')
            exit()

    @staticmethod
    def model_type(p='path/to/model.pt'):
        from trackers.reid_export import export_formats
        sf = list(export_formats().Suffix)
        check_suffix(p, sf)
        types = [s in Path(p).name for s in sf]
        return types

    def _preprocess(self, im_batch):
        images = []
        for element in im_batch:
            image = self.to_pil(element)
            image = self.preprocess(image)
            images.append(image)
        images = torch.stack(images, dim=0)
        images = images.to(self.device)
        return images

    def forward(self, im_batch):
        im_batch = self._preprocess(im_batch)
        if self.fp16 and im_batch.dtype != torch.float16:
            im_batch = im_batch.half()
        features = []
        if self.pt:
            features = self.model(im_batch)
        elif self.jit:
            features = self.model(im_batch)
        elif self.onnx:
            im_batch = im_batch.cpu().numpy()
            features = self.session.run([self.session.get_outputs()[0].name], {self.session.get_inputs()[0].name: im_batch})[0]
        elif self.engine:
            if True and im_batch.shape != self.bindings['images'].shape:
                i_in, i_out = (self.model_.get_binding_index(x) for x in ('images', 'output'))
                self.context.set_binding_shape(i_in, im_batch.shape)
                self.bindings['images'] = self.bindings['images']._replace(shape=im_batch.shape)
                self.bindings['output'].data.resize_(tuple(self.context.get_binding_shape(i_out)))
            s = self.bindings['images'].shape
            assert im_batch.shape == s, f'input size {im_batch.shape} {('>' if self.dynamic else 'not equal to')} max model size {s}'
            self.binding_addrs['images'] = int(im_batch.data_ptr())
            self.context.execute_v2(list(self.binding_addrs.values()))
            features = self.bindings['output'].data
        elif self.xml:
            im_batch = im_batch.cpu().numpy()
            features = self.executable_network([im_batch])[self.output_layer]
        else:
            print('Framework not supported at the moment, we are working on it...')
            exit()
        if isinstance(features, (list, tuple)):
            return self.from_numpy(features[0]) if len(features) == 1 else [self.from_numpy(x) for x in features]
        else:
            return self.from_numpy(features)

    def from_numpy(self, x):
        return torch.from_numpy(x).to(self.device) if isinstance(x, np.ndarray) else x

    def warmup(self, imgsz=[(256, 128, 3)]):
        warmup_types = (self.pt, self.jit, self.onnx, self.engine, self.tflite)
        if any(warmup_types) and self.device.type != 'cpu':
            im = [np.empty(*imgsz).astype(np.uint8)]
            for _ in range(2 if self.jit else 1):
                self.forward(im)

def __init__(self, weights='osnet_x0_25_msmt17.pt', device=torch.device('cpu'), fp16=False):
    super().__init__()
    w = weights[0] if isinstance(weights, list) else weights
    self.pt, self.jit, self.onnx, self.xml, self.engine, self.tflite = self.model_type(w)
    self.fp16 = fp16
    self.fp16 &= self.pt or self.jit or self.engine
    self.device = device
    self.image_size = (256, 128)
    self.pixel_mean = [0.485, 0.456, 0.406]
    self.pixel_std = [0.229, 0.224, 0.225]
    self.transforms = []
    self.transforms += [T.Resize(self.image_size)]
    self.transforms += [T.ToTensor()]
    self.transforms += [T.Normalize(mean=self.pixel_mean, std=self.pixel_std)]
    self.preprocess = T.Compose(self.transforms)
    self.to_pil = T.ToPILImage()
    model_name = get_model_name(w)
    if w.suffix == '.pt':
        model_url = get_model_url(w)
        if not file_exists(w) and model_url is not None:
            gdown.download(model_url, str(w), quiet=False)
        elif file_exists(w):
            pass
        else:
            print(f'No URL associated to the chosen StrongSORT weights ({w}). Choose between:')
            show_downloadeable_models()
            exit()
    self.model = build_model(model_name, num_classes=1, pretrained=not (w and w.is_file()), use_gpu=device)
    if self.pt:
        if w and w.is_file() and (w.suffix == '.pt'):
            load_pretrained_weights(self.model, w)
        self.model.to(device).eval()
        self.model.half() if self.fp16 else self.model.float()
    elif self.jit:
        LOGGER.info(f'Loading {w} for TorchScript inference...')
        self.model = torch.jit.load(w)
        self.model.half() if self.fp16 else self.model.float()
    elif self.onnx:
        LOGGER.info(f'Loading {w} for ONNX Runtime inference...')
        cuda = torch.cuda.is_available() and device.type != 'cpu'
        import onnxruntime
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
        self.session = onnxruntime.InferenceSession(str(w), providers=providers)
    elif self.engine:
        LOGGER.info(f'Loading {w} for TensorRT inference...')
        import tensorrt as trt
        check_version(trt.__version__, '7.0.0', hard=True)
        if device.type == 'cpu':
            device = torch.device('cuda:0')
        Binding = namedtuple('Binding', ('name', 'dtype', 'shape', 'data', 'ptr'))
        logger = trt.Logger(trt.Logger.INFO)
        with open(w, 'rb') as f, trt.Runtime(logger) as runtime:
            self.model_ = runtime.deserialize_cuda_engine(f.read())
        self.context = self.model_.create_execution_context()
        self.bindings = OrderedDict()
        self.fp16 = False
        dynamic = False
        for index in range(self.model_.num_bindings):
            name = self.model_.get_binding_name(index)
            dtype = trt.nptype(self.model_.get_binding_dtype(index))
            if self.model_.binding_is_input(index):
                if -1 in tuple(self.model_.get_binding_shape(index)):
                    dynamic = True
                    self.context.set_binding_shape(index, tuple(self.model_.get_profile_shape(0, index)[2]))
                if dtype == np.float16:
                    self.fp16 = True
            shape = tuple(self.context.get_binding_shape(index))
            im = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
            self.bindings[name] = Binding(name, dtype, shape, im, int(im.data_ptr()))
        self.binding_addrs = OrderedDict(((n, d.ptr) for n, d in self.bindings.items()))
        batch_size = self.bindings['images'].shape[0]
    elif self.xml:
        LOGGER.info(f'Loading {w} for OpenVINO inference...')
        check_requirements(('openvino',))
        from openvino.runtime import Core, Layout, get_batch
        ie = Core()
        if not Path(w).is_file():
            w = next(Path(w).glob('*.xml'))
        network = ie.read_model(model=w, weights=Path(w).with_suffix('.bin'))
        if network.get_parameters()[0].get_layout().empty:
            network.get_parameters()[0].set_layout(Layout('NCWH'))
        batch_dim = get_batch(network)
        if batch_dim.is_static:
            batch_size = batch_dim.get_length()
        self.executable_network = ie.compile_model(network, device_name='CPU')
        self.output_layer = next(iter(self.executable_network.outputs))
    elif self.tflite:
        LOGGER.info(f'Loading {w} for TensorFlow Lite inference...')
        try:
            from tflite_runtime.interpreter import Interpreter, load_delegate
        except ImportError:
            import tensorflow as tf
            Interpreter, load_delegate = (tf.lite.Interpreter, tf.lite.experimental.load_delegate)
        self.interpreter = tf.lite.Interpreter(model_path=w)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        input_data = np.array(np.random.random_sample((1, 256, 128, 3)), dtype=np.float32)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
    else:
        print('This model framework is not supported yet!')
        exit()

@staticmethod
def model_type(p='path/to/model.pt'):
    from trackers.reid_export import export_formats
    sf = list(export_formats().Suffix)
    check_suffix(p, sf)
    types = [s in Path(p).name for s in sf]
    return types

def forward(self, im_batch):
    im_batch = self._preprocess(im_batch)
    if self.fp16 and im_batch.dtype != torch.float16:
        im_batch = im_batch.half()
    features = []
    if self.pt:
        features = self.model(im_batch)
    elif self.jit:
        features = self.model(im_batch)
    elif self.onnx:
        im_batch = im_batch.cpu().numpy()
        features = self.session.run([self.session.get_outputs()[0].name], {self.session.get_inputs()[0].name: im_batch})[0]
    elif self.engine:
        if True and im_batch.shape != self.bindings['images'].shape:
            i_in, i_out = (self.model_.get_binding_index(x) for x in ('images', 'output'))
            self.context.set_binding_shape(i_in, im_batch.shape)
            self.bindings['images'] = self.bindings['images']._replace(shape=im_batch.shape)
            self.bindings['output'].data.resize_(tuple(self.context.get_binding_shape(i_out)))
        s = self.bindings['images'].shape
        assert im_batch.shape == s, f'input size {im_batch.shape} {('>' if self.dynamic else 'not equal to')} max model size {s}'
        self.binding_addrs['images'] = int(im_batch.data_ptr())
        self.context.execute_v2(list(self.binding_addrs.values()))
        features = self.bindings['output'].data
    elif self.xml:
        im_batch = im_batch.cpu().numpy()
        features = self.executable_network([im_batch])[self.output_layer]
    else:
        print('Framework not supported at the moment, we are working on it...')
        exit()
    if isinstance(features, (list, tuple)):
        return self.from_numpy(features[0]) if len(features) == 1 else [self.from_numpy(x) for x in features]
    else:
        return self.from_numpy(features)

def _indices_to_matches(cost_matrix, indices, thresh):
    matched_cost = cost_matrix[tuple(zip(*indices))]
    matched_mask = matched_cost <= thresh
    matches = indices[matched_mask]
    unmatched_a = tuple(set(range(cost_matrix.shape[0])) - set(matches[:, 0]))
    unmatched_b = tuple(set(range(cost_matrix.shape[1])) - set(matches[:, 1]))
    return (matches, unmatched_a, unmatched_b)

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

def predict(self):
    mean_state = self.mean.copy()
    if self.state != TrackState.Tracked:
        mean_state[6] = 0
        mean_state[7] = 0
    self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)

def sub_stracks(tlista, tlistb):
    stracks = {}
    for t in tlista:
        stracks[t.track_id] = t
    for t in tlistb:
        tid = t.track_id
        if stracks.get(tid, 0):
            del stracks[tid]
    return list(stracks.values())

class HiddenPrints:
    """
    A context manager to suppress print statements.
    """

    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

def __enter__(self):
    self._original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

def __exit__(self, exc_type, exc_val, exc_tb):
    sys.stdout.close()
    sys.stdout = self._original_stdout

