# Cluster 4

class models_inference:

    def __init__(self):
        self.annotating_models = {}

    def full_points(bbox):
        return np.array([[bbox[0], bbox[1]], [bbox[0], bbox[3]], [bbox[2], bbox[3]], [bbox[2], bbox[1]]])

    @torch.no_grad()
    def decode_file(self, img, model, classdict, threshold=0.3, img_array_flag=False):
        if model.__class__.__name__ == 'YOLO':
            if isinstance(img, str):
                img = cv2.imread(img)
            img_resized = cv2.resize(img, (640, 640))
            results = model(img_resized, conf=0.25, iou=0.45, verbose=False)
            results = results[0]
            if results.masks is None:
                return {'results': {}}
            masks = results.masks.cpu().numpy().masks
            masks = masks > 0.0
            org_size = img.shape[:2]
            out_size = masks.shape[1:]
            boxes = results.boxes.xyxy.cpu().numpy()
            boxes = boxes * np.array([org_size[1] / out_size[1], org_size[0] / out_size[0], org_size[1] / out_size[1], org_size[0] / out_size[0]])
            detections = Detections(xyxy=boxes, confidence=results.boxes.conf.cpu().numpy(), class_id=results.boxes.cls.cpu().numpy().astype(int))
            polygons = []
            result_dict = {}
            resize_factors = [org_size[0] / out_size[0], org_size[1] / out_size[1]]
            if len(masks) == 0:
                return {'results': {}}
            for mask in masks:
                polygon = mathOps.mask_to_polygons(mask, resize_factors=resize_factors)
                polygons.append(polygon)
            ind = 0
            res_list = []
            for detection in detections:
                if round(detection[1], 2) < float(threshold):
                    continue
                result = {}
                result['class'] = classdict.get(int(detection[2]))
                result['confidence'] = str(round(detection[1], 2))
                result['bbox'] = detection[0].astype(int)
                result['seg'] = polygons[ind]
                ind += 1
                if result['class'] == None:
                    continue
                if len(result['seg']) < 3:
                    continue
                res_list.append(result)
            result_dict['results'] = res_list
            return result_dict
        if img_array_flag:
            results = inference_detector(model, img)
        else:
            results = inference_detector(model, plt.imread(img))
        torch.cuda.empty_cache()
        results0 = []
        results1 = []
        for i in classdict.keys():
            mask = results[0][i][:, 4] >= float(threshold)
            results0.append(results[0][i][mask])
            results1.append(list(np.array(results[1][i])[mask]))
        return (results0, results1)

    def polegonise(self, results0, results1, classdict, threshold=0.3, show_bbox_flag=False):
        result_dict = {}
        res_list = []
        self.classes_numbering = [keyno for keyno in classdict.keys()]
        for classno in range(len(results0)):
            for instance in range(len(results0[classno])):
                if float(results0[classno][instance][-1]) < float(threshold):
                    continue
                result = {}
                result['class'] = classdict.get(self.classes_numbering[classno])
                result['confidence'] = str(round(results0[classno][instance][-1], 2))
                if classno == 0:
                    result['seg'] = mathOps.mask_to_polygons(results1[classno][instance].astype(np.uint8), 10)
                else:
                    result['seg'] = mathOps.mask_to_polygons(results1[classno][instance].astype(np.uint8), 25)
                if show_bbox_flag:
                    pass
                if result['class'] == None:
                    continue
                if len(result['seg']) < 3:
                    continue
                res_list.append(result)
        result_dict['results'] = res_list
        return result_dict

    def merge_masks(self):
        tic = time()
        result0 = []
        result1 = []
        counts = count_instances(self.annotating_models)
        for model in counts.keys():
            print('model {} has {} instances'.format(model, counts[model]))
        classnos = len(self.annotating_models[list(self.annotating_models.keys())[0]][1])
        merged_counts = 0
        for i in range(classnos):
            result1.append([])
            result0.append([])
        annotating_models_copy = copy.deepcopy(self.annotating_models)
        for idx1, model in enumerate(self.annotating_models.keys()):
            for classno in range(len(self.annotating_models[model][1])):
                if len(self.annotating_models[model][1][classno]) > 0:
                    for instance in range(len(self.annotating_models[model][1][classno])):
                        for idx2, model2 in enumerate(self.annotating_models.keys()):
                            if model != model2 and idx2 > idx1:
                                if classno in range(len(self.annotating_models[model2][1])):
                                    if len(self.annotating_models[model2][1][classno]) > 0:
                                        for instance2 in range(len(self.annotating_models[model2][1][classno])):
                                            dirty = False
                                            intersection = np.logical_and(self.annotating_models[model][1][classno][instance], self.annotating_models[model2][1][classno][instance2])
                                            intersection = np.sum(intersection)
                                            union = np.logical_or(self.annotating_models[model][1][classno][instance], self.annotating_models[model2][1][classno][instance2])
                                            union = np.sum(union)
                                            iou = intersection / union
                                            if iou > 0.5:
                                                if annotating_models_copy[model][1][classno][instance] is None or annotating_models_copy[model2][1][classno][instance2] is None:
                                                    dirty = True
                                                if dirty == False:
                                                    bbox1 = self.annotating_models[model][0][classno][instance]
                                                    bbox2 = self.annotating_models[model2][0][classno][instance2]
                                                    bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]), max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3]), max(bbox1[4], bbox2[4])]
                                                    result0[classno].append(bbox)
                                                    result1[classno].append(np.logical_or(self.annotating_models[model][1][classno][instance], self.annotating_models[model2][1][classno][instance2]))
                                                    merged_counts += 1
                                                annotating_models_copy[model][1][classno][instance] = None
                                                annotating_models_copy[model2][1][classno][instance2] = None
                                                annotating_models_copy[model][0][classno][instance] = None
                                                annotating_models_copy[model2][0][classno][instance2] = None
                                                break
        counts_here = {}
        for model in annotating_models_copy.keys():
            counts_here[model] = 0
            for classno in range(len(annotating_models_copy[model][1])):
                for instance in range(len(annotating_models_copy[model][1][classno])):
                    if annotating_models_copy[model][1][classno][instance] is not None:
                        counts_here[model] += 1
                        result1[classno].append(annotating_models_copy[model][1][classno][instance])
                        result0[classno].append(annotating_models_copy[model][0][classno][instance])
        self.annotating_models = {}
        for model in counts_here.keys():
            print('model {} has {} instances'.format(model, counts_here[model]))
        print('merged {} instances'.format(merged_counts))
        tac = time()
        print('merging took {} ms'.format((tac - tic) * 1000))
        return (result0, result1)

def full_points(bbox):
    return np.array([[bbox[0], bbox[1]], [bbox[0], bbox[3]], [bbox[2], bbox[3]], [bbox[2], bbox[1]]])

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

def format_shape(s):
    data = s.other_data.copy()
    data.update(dict(label=s.label.encode('utf-8') if PY2 else s.label, points=mathOps.flattener(s.points), bbox=s.bbox, group_id=s.group_id, content=s.content, shape_type=s.shape_type, flags=s.flags))
    return data

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

def format_shape(s):
    data = s.other_data.copy()
    data.update(dict(label=s.label.encode('utf-8') if PY2 else s.label, points=mathOps.flattener(s.points), bbox=s.bbox, group_id=s.group_id, content=s.content, shape_type=s.shape_type, flags=s.flags))
    return data

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

@shape_type.setter
def shape_type(self, value):
    if value is None:
        value = 'polygon'
    if value not in ['polygon', 'rectangle', 'point', 'line', 'circle', 'linestrip']:
        raise ValueError('Unexpected shape_type: {}'.format(value))
    self._shape_type = value

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

def __len__(self):
    return self.model().rowCount()

def findItemByShape(self, shape):
    for row in range(self.model().rowCount()):
        item = self.model().item(row, 0)
        if item.shape() == shape:
            return item
    raise ValueError('cannot find shape: {}'.format(shape))

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

def onNewValue(self, value):
    brightness = self.slider_brightness.value() / 50.0
    contrast = self.slider_contrast.value() / 50.0
    img = self.img
    img = PIL.ImageEnhance.Brightness(img).enhance(brightness)
    img = PIL.ImageEnhance.Contrast(img).enhance(contrast)
    img_data = utils.img_pil_to_data(img)
    qimage = QtGui.QImage.fromData(img_data)
    self.callback(qimage)

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

def copySelectedShapes(self):
    if self.selectedShapes:
        self.selectedShapesCopy = [s.copy() for s in self.selectedShapes]
        self.boundedShiftShapes(self.selectedShapesCopy)
        self.endMove(copy=True)
    return self.selectedShapes

def closeEnough(self, p1, p2):
    return labelme.utils.distance(p1 - p2) < self.epsilon / self.scale

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

def shape_to_mask(img_shape, points, shape_type=None, line_width=10, point_size=5):
    mask = np.zeros(img_shape[:2], dtype=np.uint8)
    mask = PIL.Image.fromarray(mask)
    draw = PIL.ImageDraw.Draw(mask)
    xy = [tuple(point) for point in points]
    if shape_type == 'circle':
        assert len(xy) == 2, 'Shape of shape_type=circle must have 2 points'
        (cx, cy), (px, py) = xy
        d = math.sqrt((cx - px) ** 2 + (cy - py) ** 2)
        draw.ellipse([cx - d, cy - d, cx + d, cy + d], outline=1, fill=1)
    elif shape_type == 'rectangle':
        assert len(xy) == 2, 'Shape of shape_type=rectangle must have 2 points'
        draw.rectangle(xy, outline=1, fill=1)
    elif shape_type == 'line':
        assert len(xy) == 2, 'Shape of shape_type=line must have 2 points'
        draw.line(xy=xy, fill=1, width=line_width)
    elif shape_type == 'linestrip':
        draw.line(xy=xy, fill=1, width=line_width)
    elif shape_type == 'point':
        assert len(xy) == 1, 'Shape of shape_type=point must have 1 points'
        cx, cy = xy[0]
        r = point_size
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=1, fill=1)
    else:
        assert len(xy) > 2, 'Polygon must have points more than 2'
        draw.polygon(xy=xy, outline=1, fill=1)
    mask = np.array(mask, dtype=bool)
    return mask

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

def predict_batch(self, boxes=None, image=None):
    boxes = np.array(boxes)
    input_boxes = torch.tensor(boxes, device=self.predictor.device)
    transformed_boxes = self.predictor.transform.apply_boxes_torch(input_boxes, image.shape[:2])
    masks, scores, logits = self.predictor.predict_torch(point_coords=None, point_labels=None, boxes=transformed_boxes, multimask_output=False)
    return (masks, scores)

def img_data_to_arr(img_data):
    img_pil = img_data_to_pil(img_data)
    img_arr = np.array(img_pil)
    return img_arr

def get_area_from_polygon(polygon, mode='segmentation'):
    """
    Calculates the area of a polygon defined by a list of consecutive pairs of x-y coordinates.

    Args:
        polygon (list): A list of consecutive pairs of x-y coordinates that define a polygon.
        mode (str): The mode to use for calculating the area. Can be "segmentation" (default) or "bbox".

    Returns:
        float: The area of the polygon.
    """
    if mode == 'segmentation':
        polygon = np.array(polygon).reshape(-1, 2)
        area = 0.5 * np.abs(np.dot(polygon[:, 0], np.roll(polygon[:, 1], 1)) - np.dot(polygon[:, 1], np.roll(polygon[:, 0], 1)))
        return area
    elif mode == 'bbox':
        x_min, y_min, width, height = polygon
        area = width * height
        return area
    else:
        raise ValueError("mode must be either 'segmentation' or 'bbox'")

def parse_img_export(target_directory, save_path):
    import json
    import glob
    try:
        if target_directory == '':
            image_mode = True
        else:
            image_mode = False
        json_paths = glob.glob(f'{target_directory}/*.json')
        if image_mode:
            json_paths = [save_path]
        if len(json_paths) == 0:
            raise ValueError('No json files found in the directory')
    except Exception as e:
        print(f'Error parsing image export: {e}')
        return None
    return json_paths

def distancetoline(point, line):
    p1, p2 = line
    p1 = np.array([p1.x(), p1.y()])
    p2 = np.array([p2.x(), p2.y()])
    p3 = np.array([point.x(), point.y()])
    if np.dot(p3 - p1, p2 - p1) < 0:
        return np.linalg.norm(p3 - p1)
    if np.dot(p3 - p2, p1 - p2) < 0:
        return np.linalg.norm(p3 - p2)
    if np.linalg.norm(p2 - p1) == 0:
        return 0
    return np.linalg.norm(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1)

def draw_bb_id(flags, image, x, y, w, h, id, conf, label, color=(0, 0, 255), thickness=1):
    if image is None:
        print('Image is None')
        return
    '\n    Summary:\n        Draw bounding box and id on an image (Single id).\n        \n    Args:\n        flags: a dictionary of flags (bbox, id, class)\n        image: a cv2 image\n        x: x coordinate of the bounding box\n        y: y coordinate of the bounding box\n        w: width of the bounding box\n        h: height of the bounding box\n        id: id of the shape\n        label: label of the shape (class name)\n        color: color of the bounding box\n        thickness: thickness of the bounding box\n        \n    Returns:\n        image: a cv2 image\n    '
    if flags['bbox']:
        image = cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness + 1)
    if flags['id'] or flags['class'] or flags['conf']:
        text = ''
        if flags['id'] and flags['class']:
            text = f'#{id} [{label}]'
        if flags['id'] and (not flags['class']):
            text = f'#{id}'
        if not flags['id'] and flags['class']:
            text = f'[{label}]'
        if flags['conf']:
            text = f'{text} {conf}' if len(text) > 0 else f'{conf}'
        fontscale = image.shape[0] / 2000
        if fontscale < 0.3:
            fontscale = 0.3
        elif fontscale > 5:
            fontscale = 5
        text_width, text_height = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontscale, thickness)[0]
        text_x = x + 10
        text_y = y - 10
        text_background_x1 = x
        text_background_y1 = y - 2 * 10 - text_height
        text_background_x2 = x + 2 * 10 + text_width
        text_background_y2 = y
        cv2.rectangle(img=image, pt1=(text_background_x1, text_background_y1), pt2=(text_background_x2, text_background_y2), color=color, thickness=cv2.FILLED)
        cv2.putText(img=image, text=text, org=(text_x, text_y), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=fontscale, color=(0, 0, 0), thickness=thickness, lineType=cv2.LINE_AA)
    if not flags['bbox'] and (flags['id'] or flags['class'] or flags['conf']):
        image = cv2.line(image, (x + int(w / 2), y + int(h / 2)), (x + 50, y - 5), color, thickness + 1)
    return image

def draw_trajectories(trajectories, CurrentFrameIndex, flags, img, shapes):
    """
    Summary:
        Draw trajectories on an image.
        
    Args:
        trajectories: a dictionary of trajectories
        CurrentFrameIndex: the current frame index
        flags: a dictionary of flags (traj, mask)
        img: a cv2 image
        shapes: a list of shapes
        
    Returns:
        img: a cv2 image
    """
    x = trajectories['length']
    for shape in shapes:
        id = shape['group_id']
        pts_traj = trajectories['id_' + str(id)][max(CurrentFrameIndex - x, 0):CurrentFrameIndex]
        pts_poly = np.array([[x, y] for x, y in zip(shape['points'][0::2], shape['points'][1::2])])
        color_poly = trajectories['id_color_' + str(id)]
        if flags['mask']:
            original_img = img.copy()
            if pts_poly is not None:
                cv2.fillPoly(img, pts=[pts_poly], color=color_poly)
            alpha = trajectories['alpha']
            img = cv2.addWeighted(original_img, alpha, img, 1 - alpha, 0)
        for i in range(len(pts_traj) - 1, 0, -1):
            thickness = (len(pts_traj) - i <= 10) * 1 + (len(pts_traj) - i <= 20) * 1 + (len(pts_traj) - i <= 30) * 1 + 3
            if pts_traj[i - 1] is None or pts_traj[i] is None:
                continue
            if pts_traj[i] == (-1, -1) or pts_traj[i - 1] == (-1, -1):
                break
            color_traj = color_poly
            if flags['traj']:
                cv2.line(img, pts_traj[i - 1], pts_traj[i], color_traj, thickness)
                if (len(pts_traj) - 1 - i) % 10 == 0:
                    cv2.circle(img, pts_traj[i], 3, (0, 0, 0), -1)
    return img

def draw_bb_on_image(trajectories, CurrentFrameIndex, flags, nTotalFrames, image, shapes, image_qt_flag=True):
    """
    Summary:
        Draw bounding boxes and trajectories on an image (multiple ids).
        
    Args:
        trajectories: a dictionary of trajectories.
        CurrentFrameIndex: the current frame index.
        nTotalFrames: the total number of frames.
        image: a QT image or a cv2 image.
        shapes: a list of shapes.
        image_qt_flag: a flag to indicate if the image is a QT image or a cv2 image.
        
    Returns:
        img: a QT image or a cv2 image.
    """
    img = image
    if image_qt_flag:
        img = convert_QT_to_cv(image)
    for shape in shapes:
        id = shape['group_id']
        label = shape['label']
        conf = shape['content']
        label_ascii = sum([ord(c) for c in label])
        idx = label_ascii % len(color_palette)
        color = color_palette[idx]
        x1, y1, x2, y2 = shape['bbox']
        x, y, w, h = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
        img = draw_bb_id(flags, img, x, y, w, h, id, conf, label, color, thickness=1)
        center = (int((x1 + x2) / 2), int((y1 + y2) / 2))
        try:
            centers_rec = trajectories['id_' + str(id)]
            try:
                xp, yp = centers_rec[CurrentFrameIndex - 2]
                xn, yn = center
                if xp == -1 or xn == -1:
                    c = 5 / 0
                r = 0.5
                x = r * xn + (1 - r) * xp
                y = r * yn + (1 - r) * yp
                center = (int(x), int(y))
            except:
                pass
            centers_rec[CurrentFrameIndex - 1] = center
            trajectories['id_' + str(id)] = centers_rec
            trajectories['id_color_' + str(id)] = color
        except:
            centers_rec = [(-1, -1)] * int(nTotalFrames)
            centers_rec[CurrentFrameIndex - 1] = center
            trajectories['id_' + str(id)] = centers_rec
            trajectories['id_color_' + str(id)] = color
    img = draw_trajectories(trajectories, CurrentFrameIndex, flags, img, shapes)
    if image_qt_flag:
        img = convert_cv_to_qt(img)
    return img

def draw_bb_on_image_MODE(flags, image, shapes):
    """
    Summary:
        Draw bounding boxes on an QT image (multiple ids) in MODE image.
        
    Args:
        flags: a dictionary of flags.
        image: a QT image.
        shapes: a list of shapes.
        
    Returns:
        img: a QT image.
    """
    img = convert_QT_to_cv(image)
    for shape in shapes:
        label = shape['label']
        if label == 'SAM instance':
            continue
        conf = shape['content']
        pts_poly = np.array([[x, y] for x, y in zip(shape['points'][0::2], shape['points'][1::2])])
        label_ascii = sum([ord(c) for c in label])
        idx = label_ascii % len(color_palette)
        color = color_palette[idx]
        x1, y1, x2, y2 = shape['bbox']
        x, y, w, h = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
        img = draw_bb_label_on_image_MODE(flags, img, x, y, w, h, label, conf, color, thickness=1)
        if flags['mask']:
            original_img = img.copy()
            if pts_poly is not None:
                cv2.fillPoly(img, pts=[pts_poly], color=color)
            alpha = 0.7
            img = cv2.addWeighted(original_img, alpha, img, 1 - alpha, 0)
    img = convert_cv_to_qt(img)
    return img

def draw_bb_label_on_image_MODE(flags, image, x, y, w, h, label, conf, color=(0, 0, 255), thickness=1):
    if image is None:
        print('Image is None')
        return
    '\n    Summary:\n        Draw bounding box and id on an image (Single id).\n        \n    Args:\n        flags: a dictionary of flags (bbox, id, class)\n        image: a cv2 image\n        x: x coordinate of the bounding box\n        y: y coordinate of the bounding box\n        w: width of the bounding box\n        h: height of the bounding box\n        label: label of the shape (class name)\n        color: color of the bounding box\n        thickness: thickness of the bounding box\n        \n    Returns:\n        image: a cv2 image\n    '
    if flags['bbox']:
        image = cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness + 1)
    if flags['conf'] or flags['class']:
        if flags['conf'] and flags['class']:
            text = f'[{label}] {conf}'
        if flags['conf'] and (not flags['class']):
            text = f'{conf}'
        if not flags['conf'] and flags['class']:
            text = f'[{label}]'
        fontscale = image.shape[0] / 2000
        if fontscale < 0.3:
            fontscale = 0.3
        elif fontscale > 5:
            fontscale = 5
        text_width, text_height = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontscale, thickness)[0]
        text_x = x + 10
        text_y = y - 10
        text_background_x1 = x
        text_background_y1 = y - 2 * 10 - text_height
        text_background_x2 = x + 2 * 10 + text_width
        text_background_y2 = y
        cv2.rectangle(img=image, pt1=(text_background_x1, text_background_y1), pt2=(text_background_x2, text_background_y2), color=color, thickness=cv2.FILLED)
        cv2.putText(img=image, text=text, org=(text_x, text_y), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=fontscale, color=(0, 0, 0), thickness=thickness, lineType=cv2.LINE_AA)
    if not flags['bbox'] and (flags['conf'] or flags['class']):
        image = cv2.line(image, (x + int(w / 2), y + int(h / 2)), (x + 50, y - 5), color, thickness + 1)
    return image

def getInterpolated(baseObject, baseObjectFrame, nextObject, nextObjectFrame, curFrame):
    """
    Summary:
        Interpolate a shape between two frames using linear interpolation.
        
    Args:
        baseObject: the base object
        baseObjectFrame: the base object frame
        nextObject: the next object
        nextObjectFrame: the next object frame
        curFrame: the frame to interpolate
        
    Returns:
        cur: the interpolated shape
    """
    prvR = (nextObjectFrame - curFrame) / (nextObjectFrame - baseObjectFrame)
    nxtR = (curFrame - baseObjectFrame) / (nextObjectFrame - baseObjectFrame)
    cur_bbox = prvR * np.array(baseObject['bbox']) + nxtR * np.array(nextObject['bbox'])
    cur_bbox = [int(cur_bbox[i]) for i in range(len(cur_bbox))]
    baseObject['segment'], nextObject['segment'] = handleTwoSegments(baseObject['segment'], nextObject['segment'])
    cur_segment = prvR * np.array(baseObject['segment']) + nxtR * np.array(nextObject['segment'])
    cur_segment = [[int(sublist[0]), int(sublist[1])] for sublist in cur_segment]
    cur = copy.deepcopy(baseObject)
    cur['bbox'] = cur_bbox
    cur['segment'] = cur_segment
    return cur

def get_contour_length(contour):
    contour_start = contour
    contour_end = np.r_[contour[1:], contour[0:1]]
    return np.linalg.norm(contour_end - contour_start, axis=1).sum()

@PRIOR_GENERATORS.register_module()
class AnchorGenerator:
    """Standard anchor generator for 2D anchor-based detectors.

    Args:
        strides (list[int] | list[tuple[int, int]]): Strides of anchors
            in multiple feature levels in order (w, h).
        ratios (list[float]): The list of ratios between the height and width
            of anchors in a single level.
        scales (list[int] | None): Anchor scales for anchors in a single level.
            It cannot be set at the same time if `octave_base_scale` and
            `scales_per_octave` are set.
        base_sizes (list[int] | None): The basic sizes
            of anchors in multiple levels.
            If None is given, strides will be used as base_sizes.
            (If strides are non square, the shortest stride is taken.)
        scale_major (bool): Whether to multiply scales first when generating
            base anchors. If true, the anchors in the same row will have the
            same scales. By default it is True in V2.0
        octave_base_scale (int): The base scale of octave.
        scales_per_octave (int): Number of scales for each octave.
            `octave_base_scale` and `scales_per_octave` are usually used in
            retinanet and the `scales` should be None when they are set.
        centers (list[tuple[float, float]] | None): The centers of the anchor
            relative to the feature grid center in multiple feature levels.
            By default it is set to be None and not used. If a list of tuple of
            float is given, they will be used to shift the centers of anchors.
        center_offset (float): The offset of center in proportion to anchors'
            width and height. By default it is 0 in V2.0.

    Examples:
        >>> from mmdet.core import AnchorGenerator
        >>> self = AnchorGenerator([16], [1.], [1.], [9])
        >>> all_anchors = self.grid_priors([(2, 2)], device='cpu')
        >>> print(all_anchors)
        [tensor([[-4.5000, -4.5000,  4.5000,  4.5000],
                [11.5000, -4.5000, 20.5000,  4.5000],
                [-4.5000, 11.5000,  4.5000, 20.5000],
                [11.5000, 11.5000, 20.5000, 20.5000]])]
        >>> self = AnchorGenerator([16, 32], [1.], [1.], [9, 18])
        >>> all_anchors = self.grid_priors([(2, 2), (1, 1)], device='cpu')
        >>> print(all_anchors)
        [tensor([[-4.5000, -4.5000,  4.5000,  4.5000],
                [11.5000, -4.5000, 20.5000,  4.5000],
                [-4.5000, 11.5000,  4.5000, 20.5000],
                [11.5000, 11.5000, 20.5000, 20.5000]]),         tensor([[-9., -9., 9., 9.]])]
    """

    def __init__(self, strides, ratios, scales=None, base_sizes=None, scale_major=True, octave_base_scale=None, scales_per_octave=None, centers=None, center_offset=0.0):
        if center_offset != 0:
            assert centers is None, f'center cannot be set when center_offset!=0, {centers} is given.'
        if not 0 <= center_offset <= 1:
            raise ValueError(f'center_offset should be in range [0, 1], {center_offset} is given.')
        if centers is not None:
            assert len(centers) == len(strides), f'The number of strides should be the same as centers, got {strides} and {centers}'
        self.strides = [_pair(stride) for stride in strides]
        self.base_sizes = [min(stride) for stride in self.strides] if base_sizes is None else base_sizes
        assert len(self.base_sizes) == len(self.strides), f'The number of strides should be the same as base sizes, got {self.strides} and {self.base_sizes}'
        assert (octave_base_scale is not None and scales_per_octave is not None) ^ (scales is not None), 'scales and octave_base_scale with scales_per_octave cannot be set at the same time'
        if scales is not None:
            self.scales = torch.Tensor(scales)
        elif octave_base_scale is not None and scales_per_octave is not None:
            octave_scales = np.array([2 ** (i / scales_per_octave) for i in range(scales_per_octave)])
            scales = octave_scales * octave_base_scale
            self.scales = torch.Tensor(scales)
        else:
            raise ValueError('Either scales or octave_base_scale with scales_per_octave should be set')
        self.octave_base_scale = octave_base_scale
        self.scales_per_octave = scales_per_octave
        self.ratios = torch.Tensor(ratios)
        self.scale_major = scale_major
        self.centers = centers
        self.center_offset = center_offset
        self.base_anchors = self.gen_base_anchors()

    @property
    def num_base_anchors(self):
        """list[int]: total number of base anchors in a feature grid"""
        return self.num_base_priors

    @property
    def num_base_priors(self):
        """list[int]: The number of priors (anchors) at a point
        on the feature grid"""
        return [base_anchors.size(0) for base_anchors in self.base_anchors]

    @property
    def num_levels(self):
        """int: number of feature levels that the generator will be applied"""
        return len(self.strides)

    def gen_base_anchors(self):
        """Generate base anchors.

        Returns:
            list(torch.Tensor): Base anchors of a feature grid in multiple                 feature levels.
        """
        multi_level_base_anchors = []
        for i, base_size in enumerate(self.base_sizes):
            center = None
            if self.centers is not None:
                center = self.centers[i]
            multi_level_base_anchors.append(self.gen_single_level_base_anchors(base_size, scales=self.scales, ratios=self.ratios, center=center))
        return multi_level_base_anchors

    def gen_single_level_base_anchors(self, base_size, scales, ratios, center=None):
        """Generate base anchors of a single level.

        Args:
            base_size (int | float): Basic size of an anchor.
            scales (torch.Tensor): Scales of the anchor.
            ratios (torch.Tensor): The ratio between between the height
                and width of anchors in a single level.
            center (tuple[float], optional): The center of the base anchor
                related to a single feature grid. Defaults to None.

        Returns:
            torch.Tensor: Anchors in a single-level feature maps.
        """
        w = base_size
        h = base_size
        if center is None:
            x_center = self.center_offset * w
            y_center = self.center_offset * h
        else:
            x_center, y_center = center
        h_ratios = torch.sqrt(ratios)
        w_ratios = 1 / h_ratios
        if self.scale_major:
            ws = (w * w_ratios[:, None] * scales[None, :]).view(-1)
            hs = (h * h_ratios[:, None] * scales[None, :]).view(-1)
        else:
            ws = (w * scales[:, None] * w_ratios[None, :]).view(-1)
            hs = (h * scales[:, None] * h_ratios[None, :]).view(-1)
        base_anchors = [x_center - 0.5 * ws, y_center - 0.5 * hs, x_center + 0.5 * ws, y_center + 0.5 * hs]
        base_anchors = torch.stack(base_anchors, dim=-1)
        return base_anchors

    def _meshgrid(self, x, y, row_major=True):
        """Generate mesh grid of x and y.

        Args:
            x (torch.Tensor): Grids of x dimension.
            y (torch.Tensor): Grids of y dimension.
            row_major (bool, optional): Whether to return y grids first.
                Defaults to True.

        Returns:
            tuple[torch.Tensor]: The mesh grids of x and y.
        """
        xx = x.repeat(y.shape[0])
        yy = y.view(-1, 1).repeat(1, x.shape[0]).view(-1)
        if row_major:
            return (xx, yy)
        else:
            return (yy, xx)

    def grid_priors(self, featmap_sizes, dtype=torch.float32, device='cuda'):
        """Generate grid anchors in multiple feature levels.

        Args:
            featmap_sizes (list[tuple]): List of feature map sizes in
                multiple feature levels.
            dtype (:obj:`torch.dtype`): Dtype of priors.
                Default: torch.float32.
            device (str): The device where the anchors will be put on.

        Return:
            list[torch.Tensor]: Anchors in multiple feature levels.                 The sizes of each tensor should be [N, 4], where                 N = width * height * num_base_anchors, width and height                 are the sizes of the corresponding feature level,                 num_base_anchors is the number of anchors for that level.
        """
        assert self.num_levels == len(featmap_sizes)
        multi_level_anchors = []
        for i in range(self.num_levels):
            anchors = self.single_level_grid_priors(featmap_sizes[i], level_idx=i, dtype=dtype, device=device)
            multi_level_anchors.append(anchors)
        return multi_level_anchors

    def single_level_grid_priors(self, featmap_size, level_idx, dtype=torch.float32, device='cuda'):
        """Generate grid anchors of a single level.

        Note:
            This function is usually called by method ``self.grid_priors``.

        Args:
            featmap_size (tuple[int]): Size of the feature maps.
            level_idx (int): The index of corresponding feature map level.
            dtype (obj:`torch.dtype`): Date type of points.Defaults to
                ``torch.float32``.
            device (str, optional): The device the tensor will be put on.
                Defaults to 'cuda'.

        Returns:
            torch.Tensor: Anchors in the overall feature maps.
        """
        base_anchors = self.base_anchors[level_idx].to(device).to(dtype)
        feat_h, feat_w = featmap_size
        stride_w, stride_h = self.strides[level_idx]
        shift_x = torch.arange(0, feat_w, device=device).to(dtype) * stride_w
        shift_y = torch.arange(0, feat_h, device=device).to(dtype) * stride_h
        shift_xx, shift_yy = self._meshgrid(shift_x, shift_y)
        shifts = torch.stack([shift_xx, shift_yy, shift_xx, shift_yy], dim=-1)
        all_anchors = base_anchors[None, :, :] + shifts[:, None, :]
        all_anchors = all_anchors.view(-1, 4)
        return all_anchors

    def sparse_priors(self, prior_idxs, featmap_size, level_idx, dtype=torch.float32, device='cuda'):
        """Generate sparse anchors according to the ``prior_idxs``.

        Args:
            prior_idxs (Tensor): The index of corresponding anchors
                in the feature map.
            featmap_size (tuple[int]): feature map size arrange as (h, w).
            level_idx (int): The level index of corresponding feature
                map.
            dtype (obj:`torch.dtype`): Date type of points.Defaults to
                ``torch.float32``.
            device (obj:`torch.device`): The device where the points is
                located.
        Returns:
            Tensor: Anchor with shape (N, 4), N should be equal to
                the length of ``prior_idxs``.
        """
        height, width = featmap_size
        num_base_anchors = self.num_base_anchors[level_idx]
        base_anchor_id = prior_idxs % num_base_anchors
        x = prior_idxs // num_base_anchors % width * self.strides[level_idx][0]
        y = prior_idxs // width // num_base_anchors % height * self.strides[level_idx][1]
        priors = torch.stack([x, y, x, y], 1).to(dtype).to(device) + self.base_anchors[level_idx][base_anchor_id, :].to(device)
        return priors

    def grid_anchors(self, featmap_sizes, device='cuda'):
        """Generate grid anchors in multiple feature levels.

        Args:
            featmap_sizes (list[tuple]): List of feature map sizes in
                multiple feature levels.
            device (str): Device where the anchors will be put on.

        Return:
            list[torch.Tensor]: Anchors in multiple feature levels.                 The sizes of each tensor should be [N, 4], where                 N = width * height * num_base_anchors, width and height                 are the sizes of the corresponding feature level,                 num_base_anchors is the number of anchors for that level.
        """
        warnings.warn('``grid_anchors`` would be deprecated soon. Please use ``grid_priors`` ')
        assert self.num_levels == len(featmap_sizes)
        multi_level_anchors = []
        for i in range(self.num_levels):
            anchors = self.single_level_grid_anchors(self.base_anchors[i].to(device), featmap_sizes[i], self.strides[i], device=device)
            multi_level_anchors.append(anchors)
        return multi_level_anchors

    def single_level_grid_anchors(self, base_anchors, featmap_size, stride=(16, 16), device='cuda'):
        """Generate grid anchors of a single level.

        Note:
            This function is usually called by method ``self.grid_anchors``.

        Args:
            base_anchors (torch.Tensor): The base anchors of a feature grid.
            featmap_size (tuple[int]): Size of the feature maps.
            stride (tuple[int], optional): Stride of the feature map in order
                (w, h). Defaults to (16, 16).
            device (str, optional): Device the tensor will be put on.
                Defaults to 'cuda'.

        Returns:
            torch.Tensor: Anchors in the overall feature maps.
        """
        warnings.warn('``single_level_grid_anchors`` would be deprecated soon. Please use ``single_level_grid_priors`` ')
        feat_h, feat_w = featmap_size
        shift_x = torch.arange(0, feat_w, device=device) * stride[0]
        shift_y = torch.arange(0, feat_h, device=device) * stride[1]
        shift_xx, shift_yy = self._meshgrid(shift_x, shift_y)
        shifts = torch.stack([shift_xx, shift_yy, shift_xx, shift_yy], dim=-1)
        shifts = shifts.type_as(base_anchors)
        all_anchors = base_anchors[None, :, :] + shifts[:, None, :]
        all_anchors = all_anchors.view(-1, 4)
        return all_anchors

    def valid_flags(self, featmap_sizes, pad_shape, device='cuda'):
        """Generate valid flags of anchors in multiple feature levels.

        Args:
            featmap_sizes (list(tuple)): List of feature map sizes in
                multiple feature levels.
            pad_shape (tuple): The padded shape of the image.
            device (str): Device where the anchors will be put on.

        Return:
            list(torch.Tensor): Valid flags of anchors in multiple levels.
        """
        assert self.num_levels == len(featmap_sizes)
        multi_level_flags = []
        for i in range(self.num_levels):
            anchor_stride = self.strides[i]
            feat_h, feat_w = featmap_sizes[i]
            h, w = pad_shape[:2]
            valid_feat_h = min(int(np.ceil(h / anchor_stride[1])), feat_h)
            valid_feat_w = min(int(np.ceil(w / anchor_stride[0])), feat_w)
            flags = self.single_level_valid_flags((feat_h, feat_w), (valid_feat_h, valid_feat_w), self.num_base_anchors[i], device=device)
            multi_level_flags.append(flags)
        return multi_level_flags

    def single_level_valid_flags(self, featmap_size, valid_size, num_base_anchors, device='cuda'):
        """Generate the valid flags of anchor in a single feature map.

        Args:
            featmap_size (tuple[int]): The size of feature maps, arrange
                as (h, w).
            valid_size (tuple[int]): The valid size of the feature maps.
            num_base_anchors (int): The number of base anchors.
            device (str, optional): Device where the flags will be put on.
                Defaults to 'cuda'.

        Returns:
            torch.Tensor: The valid flags of each anchor in a single level                 feature map.
        """
        feat_h, feat_w = featmap_size
        valid_h, valid_w = valid_size
        assert valid_h <= feat_h and valid_w <= feat_w
        valid_x = torch.zeros(feat_w, dtype=torch.bool, device=device)
        valid_y = torch.zeros(feat_h, dtype=torch.bool, device=device)
        valid_x[:valid_w] = 1
        valid_y[:valid_h] = 1
        valid_xx, valid_yy = self._meshgrid(valid_x, valid_y)
        valid = valid_xx & valid_yy
        valid = valid[:, None].expand(valid.size(0), num_base_anchors).contiguous().view(-1)
        return valid

    def __repr__(self):
        """str: a string that describes the module"""
        indent_str = '    '
        repr_str = self.__class__.__name__ + '(\n'
        repr_str += f'{indent_str}strides={self.strides},\n'
        repr_str += f'{indent_str}ratios={self.ratios},\n'
        repr_str += f'{indent_str}scales={self.scales},\n'
        repr_str += f'{indent_str}base_sizes={self.base_sizes},\n'
        repr_str += f'{indent_str}scale_major={self.scale_major},\n'
        repr_str += f'{indent_str}octave_base_scale='
        repr_str += f'{self.octave_base_scale},\n'
        repr_str += f'{indent_str}scales_per_octave='
        repr_str += f'{self.scales_per_octave},\n'
        repr_str += f'{indent_str}num_levels={self.num_levels}\n'
        repr_str += f'{indent_str}centers={self.centers},\n'
        repr_str += f'{indent_str}center_offset={self.center_offset})'
        return repr_str

def gen_single_level_base_anchors(self, base_size, scales, ratios, center=None):
    """Generate base anchors of a single level.

        Args:
            base_size (int | float): Basic size of an anchor.
            scales (torch.Tensor): Scales of the anchor.
            ratios (torch.Tensor): The ratio between between the height
                and width of anchors in a single level.
            center (tuple[float], optional): The center of the base anchor
                related to a single feature grid. Defaults to None.

        Returns:
            torch.Tensor: Anchors in a single-level feature maps.
        """
    w = base_size
    h = base_size
    if center is None:
        x_center = self.center_offset * w
        y_center = self.center_offset * h
    else:
        x_center, y_center = center
    h_ratios = torch.sqrt(ratios)
    w_ratios = 1 / h_ratios
    if self.scale_major:
        ws = (w * w_ratios[:, None] * scales[None, :]).view(-1)
        hs = (h * h_ratios[:, None] * scales[None, :]).view(-1)
    else:
        ws = (w * scales[:, None] * w_ratios[None, :]).view(-1)
        hs = (h * scales[:, None] * h_ratios[None, :]).view(-1)
    base_anchors = [x_center - 0.5 * ws, y_center - 0.5 * hs, x_center + 0.5 * ws, y_center + 0.5 * hs]
    base_anchors = torch.stack(base_anchors, dim=-1)
    return base_anchors

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

def merge_aug_masks(aug_masks, img_metas, rcnn_test_cfg, weights=None):
    """Merge augmented mask prediction.

    Args:
        aug_masks (list[ndarray]): shape (n, #class, h, w)
        img_shapes (list[ndarray]): shape (3, ).
        rcnn_test_cfg (dict): rcnn test config.

    Returns:
        tuple: (bboxes, scores)
    """
    recovered_masks = []
    for mask, img_info in zip(aug_masks, img_metas):
        flip = img_info[0]['flip']
        if flip:
            flip_direction = img_info[0]['flip_direction']
            if flip_direction == 'horizontal':
                mask = mask[:, :, :, ::-1]
            elif flip_direction == 'vertical':
                mask = mask[:, :, ::-1, :]
            elif flip_direction == 'diagonal':
                mask = mask[:, :, :, ::-1]
                mask = mask[:, :, ::-1, :]
            else:
                raise ValueError(f"Invalid flipping direction '{flip_direction}'")
        recovered_masks.append(mask)
    if weights is None:
        merged_masks = np.mean(recovered_masks, axis=0)
    else:
        merged_masks = np.average(np.array(recovered_masks), axis=0, weights=np.array(weights))
    return merged_masks

def _calc_dynamic_intervals(start_interval, dynamic_interval_list):
    assert mmcv.is_list_of(dynamic_interval_list, tuple)
    dynamic_milestones = [0]
    dynamic_milestones.extend([dynamic_interval[0] for dynamic_interval in dynamic_interval_list])
    dynamic_intervals = [start_interval]
    dynamic_intervals.extend([dynamic_interval[1] for dynamic_interval in dynamic_interval_list])
    return (dynamic_milestones, dynamic_intervals)

def set_recall_param(proposal_nums, iou_thrs):
    """Check proposal_nums and iou_thrs and set correct format."""
    if isinstance(proposal_nums, Sequence):
        _proposal_nums = np.array(proposal_nums)
    elif isinstance(proposal_nums, int):
        _proposal_nums = np.array([proposal_nums])
    else:
        _proposal_nums = proposal_nums
    if iou_thrs is None:
        _iou_thrs = np.array([0.5])
    elif isinstance(iou_thrs, Sequence):
        _iou_thrs = np.array(iou_thrs)
    elif isinstance(iou_thrs, float):
        _iou_thrs = np.array([iou_thrs])
    else:
        _iou_thrs = iou_thrs
    return (_proposal_nums, _iou_thrs)

def eval_recalls(gts, proposals, proposal_nums=None, iou_thrs=0.5, logger=None, use_legacy_coordinate=False):
    """Calculate recalls.

    Args:
        gts (list[ndarray]): a list of arrays of shape (n, 4)
        proposals (list[ndarray]): a list of arrays of shape (k, 4) or (k, 5)
        proposal_nums (int | Sequence[int]): Top N proposals to be evaluated.
        iou_thrs (float | Sequence[float]): IoU thresholds. Default: 0.5.
        logger (logging.Logger | str | None): The way to print the recall
            summary. See `mmcv.utils.print_log()` for details. Default: None.
        use_legacy_coordinate (bool): Whether use coordinate system
            in mmdet v1.x. "1" was added to both height and width
            which means w, h should be
            computed as 'x2 - x1 + 1` and 'y2 - y1 + 1'. Default: False.


    Returns:
        ndarray: recalls of different ious and proposal nums
    """
    img_num = len(gts)
    assert img_num == len(proposals)
    proposal_nums, iou_thrs = set_recall_param(proposal_nums, iou_thrs)
    all_ious = []
    for i in range(img_num):
        if proposals[i].ndim == 2 and proposals[i].shape[1] == 5:
            scores = proposals[i][:, 4]
            sort_idx = np.argsort(scores)[::-1]
            img_proposal = proposals[i][sort_idx, :]
        else:
            img_proposal = proposals[i]
        prop_num = min(img_proposal.shape[0], proposal_nums[-1])
        if gts[i] is None or gts[i].shape[0] == 0:
            ious = np.zeros((0, img_proposal.shape[0]), dtype=np.float32)
        else:
            ious = bbox_overlaps(gts[i], img_proposal[:prop_num, :4], use_legacy_coordinate=use_legacy_coordinate)
        all_ious.append(ious)
    all_ious = np.array(all_ious)
    recalls = _recalls(all_ious, proposal_nums, iou_thrs)
    print_recall_summary(recalls, proposal_nums, iou_thrs, logger=logger)
    return recalls

def bbox_overlaps(bboxes1, bboxes2, mode='iou', eps=1e-06, use_legacy_coordinate=False):
    """Calculate the ious between each bbox of bboxes1 and bboxes2.

    Args:
        bboxes1 (ndarray): Shape (n, 4)
        bboxes2 (ndarray): Shape (k, 4)
        mode (str): IOU (intersection over union) or IOF (intersection
            over foreground)
        use_legacy_coordinate (bool): Whether to use coordinate system in
            mmdet v1.x. which means width, height should be
            calculated as 'x2 - x1 + 1` and 'y2 - y1 + 1' respectively.
            Note when function is used in `VOCDataset`, it should be
            True to align with the official implementation
            `http://host.robots.ox.ac.uk/pascal/VOC/voc2012/VOCdevkit_18-May-2011.tar`
            Default: False.

    Returns:
        ious (ndarray): Shape (n, k)
    """
    assert mode in ['iou', 'iof']
    if not use_legacy_coordinate:
        extra_length = 0.0
    else:
        extra_length = 1.0
    bboxes1 = bboxes1.astype(np.float32)
    bboxes2 = bboxes2.astype(np.float32)
    rows = bboxes1.shape[0]
    cols = bboxes2.shape[0]
    ious = np.zeros((rows, cols), dtype=np.float32)
    if rows * cols == 0:
        return ious
    exchange = False
    if bboxes1.shape[0] > bboxes2.shape[0]:
        bboxes1, bboxes2 = (bboxes2, bboxes1)
        ious = np.zeros((cols, rows), dtype=np.float32)
        exchange = True
    area1 = (bboxes1[:, 2] - bboxes1[:, 0] + extra_length) * (bboxes1[:, 3] - bboxes1[:, 1] + extra_length)
    area2 = (bboxes2[:, 2] - bboxes2[:, 0] + extra_length) * (bboxes2[:, 3] - bboxes2[:, 1] + extra_length)
    for i in range(bboxes1.shape[0]):
        x_start = np.maximum(bboxes1[i, 0], bboxes2[:, 0])
        y_start = np.maximum(bboxes1[i, 1], bboxes2[:, 1])
        x_end = np.minimum(bboxes1[i, 2], bboxes2[:, 2])
        y_end = np.minimum(bboxes1[i, 3], bboxes2[:, 3])
        overlap = np.maximum(x_end - x_start + extra_length, 0) * np.maximum(y_end - y_start + extra_length, 0)
        if mode == 'iou':
            union = area1[i] + area2 - overlap
        else:
            union = area1[i] if not exchange else area2
        union = np.maximum(union, eps)
        ious[i, :] = overlap / union
    if exchange:
        ious = ious.T
    return ious

@TRANSFORMER.register_module()
class DynamicConv(BaseModule):
    """Implements Dynamic Convolution.

    This module generate parameters for each sample and
    use bmm to implement 1*1 convolution. Code is modified
    from the `official github repo <https://github.com/PeizeSun/
    SparseR-CNN/blob/main/projects/SparseRCNN/sparsercnn/head.py#L258>`_ .

    Args:
        in_channels (int): The input feature channel.
            Defaults to 256.
        feat_channels (int): The inner feature channel.
            Defaults to 64.
        out_channels (int, optional): The output feature channel.
            When not specified, it will be set to `in_channels`
            by default
        input_feat_shape (int): The shape of input feature.
            Defaults to 7.
        with_proj (bool): Project two-dimentional feature to
            one-dimentional feature. Default to True.
        act_cfg (dict): The activation config for DynamicConv.
        norm_cfg (dict): Config dict for normalization layer. Default
            layer normalization.
        init_cfg (obj:`mmcv.ConfigDict`): The Config for initialization.
            Default: None.
    """

    def __init__(self, in_channels=256, feat_channels=64, out_channels=None, input_feat_shape=7, with_proj=True, act_cfg=dict(type='ReLU', inplace=True), norm_cfg=dict(type='LN'), init_cfg=None):
        super(DynamicConv, self).__init__(init_cfg)
        self.in_channels = in_channels
        self.feat_channels = feat_channels
        self.out_channels_raw = out_channels
        self.input_feat_shape = input_feat_shape
        self.with_proj = with_proj
        self.act_cfg = act_cfg
        self.norm_cfg = norm_cfg
        self.out_channels = out_channels if out_channels else in_channels
        self.num_params_in = self.in_channels * self.feat_channels
        self.num_params_out = self.out_channels * self.feat_channels
        self.dynamic_layer = nn.Linear(self.in_channels, self.num_params_in + self.num_params_out)
        self.norm_in = build_norm_layer(norm_cfg, self.feat_channels)[1]
        self.norm_out = build_norm_layer(norm_cfg, self.out_channels)[1]
        self.activation = build_activation_layer(act_cfg)
        num_output = self.out_channels * input_feat_shape ** 2
        if self.with_proj:
            self.fc_layer = nn.Linear(num_output, self.out_channels)
            self.fc_norm = build_norm_layer(norm_cfg, self.out_channels)[1]

    def forward(self, param_feature, input_feature):
        """Forward function for `DynamicConv`.

        Args:
            param_feature (Tensor): The feature can be used
                to generate the parameter, has shape
                (num_all_proposals, in_channels).
            input_feature (Tensor): Feature that
                interact with parameters, has shape
                (num_all_proposals, in_channels, H, W).

        Returns:
            Tensor: The output feature has shape
            (num_all_proposals, out_channels).
        """
        input_feature = input_feature.flatten(2).permute(2, 0, 1)
        input_feature = input_feature.permute(1, 0, 2)
        parameters = self.dynamic_layer(param_feature)
        param_in = parameters[:, :self.num_params_in].view(-1, self.in_channels, self.feat_channels)
        param_out = parameters[:, -self.num_params_out:].view(-1, self.feat_channels, self.out_channels)
        features = torch.bmm(input_feature, param_in)
        features = self.norm_in(features)
        features = self.activation(features)
        features = torch.bmm(features, param_out)
        features = self.norm_out(features)
        features = self.activation(features)
        if self.with_proj:
            features = features.flatten(1)
            features = self.fc_layer(features)
            features = self.fc_norm(features)
            features = self.activation(features)
        return features

def forward(self, param_feature, input_feature):
    """Forward function for `DynamicConv`.

        Args:
            param_feature (Tensor): The feature can be used
                to generate the parameter, has shape
                (num_all_proposals, in_channels).
            input_feature (Tensor): Feature that
                interact with parameters, has shape
                (num_all_proposals, in_channels, H, W).

        Returns:
            Tensor: The output feature has shape
            (num_all_proposals, out_channels).
        """
    input_feature = input_feature.flatten(2).permute(2, 0, 1)
    input_feature = input_feature.permute(1, 0, 2)
    parameters = self.dynamic_layer(param_feature)
    param_in = parameters[:, :self.num_params_in].view(-1, self.in_channels, self.feat_channels)
    param_out = parameters[:, -self.num_params_out:].view(-1, self.feat_channels, self.out_channels)
    features = torch.bmm(input_feature, param_in)
    features = self.norm_in(features)
    features = self.activation(features)
    features = torch.bmm(features, param_out)
    features = self.norm_out(features)
    features = self.activation(features)
    if self.with_proj:
        features = features.flatten(1)
        features = self.fc_layer(features)
        features = self.fc_norm(features)
        features = self.activation(features)
    return features

def gaussian_radius(det_size, min_overlap):
    """Generate 2D gaussian radius.

    This function is modified from the `official github repo
    <https://github.com/princeton-vl/CornerNet-Lite/blob/master/core/sample/
    utils.py#L65>`_.

    Given ``min_overlap``, radius could computed by a quadratic equation
    according to Vieta's formulas.

    There are 3 cases for computing gaussian radius, details are following:

    - Explanation of figure: ``lt`` and ``br`` indicates the left-top and
      bottom-right corner of ground truth box. ``x`` indicates the
      generated corner at the limited position when ``radius=r``.

    - Case1: one corner is inside the gt box and the other is outside.

    .. code:: text

        |<   width   >|

        lt-+----------+         -
        |  |          |         ^
        +--x----------+--+
        |  |          |  |
        |  |          |  |    height
        |  | overlap  |  |
        |  |          |  |
        |  |          |  |      v
        +--+---------br--+      -
           |          |  |
           +----------+--x

    To ensure IoU of generated box and gt box is larger than ``min_overlap``:

    .. math::
        \\cfrac{(w-r)*(h-r)}{w*h+(w+h)r-r^2} \\ge {iou} \\quad\\Rightarrow\\quad
        {r^2-(w+h)r+\\cfrac{1-iou}{1+iou}*w*h} \\ge 0 \\\\
        {a} = 1,\\quad{b} = {-(w+h)},\\quad{c} = {\\cfrac{1-iou}{1+iou}*w*h} \\\\
        {r} \\le \\cfrac{-b-\\sqrt{b^2-4*a*c}}{2*a}

    - Case2: both two corners are inside the gt box.

    .. code:: text

        |<   width   >|

        lt-+----------+         -
        |  |          |         ^
        +--x-------+  |
        |  |       |  |
        |  |overlap|  |       height
        |  |       |  |
        |  +-------x--+
        |          |  |         v
        +----------+-br         -

    To ensure IoU of generated box and gt box is larger than ``min_overlap``:

    .. math::
        \\cfrac{(w-2*r)*(h-2*r)}{w*h} \\ge {iou} \\quad\\Rightarrow\\quad
        {4r^2-2(w+h)r+(1-iou)*w*h} \\ge 0 \\\\
        {a} = 4,\\quad {b} = {-2(w+h)},\\quad {c} = {(1-iou)*w*h} \\\\
        {r} \\le \\cfrac{-b-\\sqrt{b^2-4*a*c}}{2*a}

    - Case3: both two corners are outside the gt box.

    .. code:: text

           |<   width   >|

        x--+----------------+
        |  |                |
        +-lt-------------+  |   -
        |  |             |  |   ^
        |  |             |  |
        |  |   overlap   |  | height
        |  |             |  |
        |  |             |  |   v
        |  +------------br--+   -
        |                |  |
        +----------------+--x

    To ensure IoU of generated box and gt box is larger than ``min_overlap``:

    .. math::
        \\cfrac{w*h}{(w+2*r)*(h+2*r)} \\ge {iou} \\quad\\Rightarrow\\quad
        {4*iou*r^2+2*iou*(w+h)r+(iou-1)*w*h} \\le 0 \\\\
        {a} = {4*iou},\\quad {b} = {2*iou*(w+h)},\\quad {c} = {(iou-1)*w*h} \\\\
        {r} \\le \\cfrac{-b+\\sqrt{b^2-4*a*c}}{2*a}

    Args:
        det_size (list[int]): Shape of object.
        min_overlap (float): Min IoU with ground truth for boxes generated by
            keypoints inside the gaussian kernel.

    Returns:
        radius (int): Radius of gaussian kernel.
    """
    height, width = det_size
    a1 = 1
    b1 = height + width
    c1 = width * height * (1 - min_overlap) / (1 + min_overlap)
    sq1 = sqrt(b1 ** 2 - 4 * a1 * c1)
    r1 = (b1 - sq1) / (2 * a1)
    a2 = 4
    b2 = 2 * (height + width)
    c2 = (1 - min_overlap) * width * height
    sq2 = sqrt(b2 ** 2 - 4 * a2 * c2)
    r2 = (b2 - sq2) / (2 * a2)
    a3 = 4 * min_overlap
    b3 = -2 * min_overlap * (height + width)
    c3 = (min_overlap - 1) * width * height
    sq3 = sqrt(b3 ** 2 - 4 * a3 * c3)
    r3 = (b3 + sq3) / (2 * a3)
    return min(r1, r2, r3)

class SigmoidGeometricMean(Function):
    """Forward and backward function of geometric mean of two sigmoid
    functions.

    This implementation with analytical gradient function substitutes
    the autograd function of (x.sigmoid() * y.sigmoid()).sqrt(). The
    original implementation incurs none during gradient backprapagation
    if both x and y are very small values.
    """

    @staticmethod
    def forward(ctx, x, y):
        x_sigmoid = x.sigmoid()
        y_sigmoid = y.sigmoid()
        z = (x_sigmoid * y_sigmoid).sqrt()
        ctx.save_for_backward(x_sigmoid, y_sigmoid, z)
        return z

    @staticmethod
    def backward(ctx, grad_output):
        x_sigmoid, y_sigmoid, z = ctx.saved_tensors
        grad_x = grad_output * z * (1 - x_sigmoid) / 2
        grad_y = grad_output * z * (1 - y_sigmoid) / 2
        return (grad_x, grad_y)

@staticmethod
def forward(ctx, x, y):
    x_sigmoid = x.sigmoid()
    y_sigmoid = y.sigmoid()
    z = (x_sigmoid * y_sigmoid).sqrt()
    ctx.save_for_backward(x_sigmoid, y_sigmoid, z)
    return z

@BACKBONES.register_module()
class ResNet(BaseModule):
    """ResNet backbone.

    Args:
        depth (int): Depth of resnet, from {18, 34, 50, 101, 152}.
        stem_channels (int | None): Number of stem channels. If not specified,
            it will be the same as `base_channels`. Default: None.
        base_channels (int): Number of base channels of res layer. Default: 64.
        in_channels (int): Number of input image channels. Default: 3.
        num_stages (int): Resnet stages. Default: 4.
        strides (Sequence[int]): Strides of the first block of each stage.
        dilations (Sequence[int]): Dilation of each stage.
        out_indices (Sequence[int]): Output from which stages.
        style (str): `pytorch` or `caffe`. If set to "pytorch", the stride-two
            layer is the 3x3 conv layer, otherwise the stride-two layer is
            the first 1x1 conv layer.
        deep_stem (bool): Replace 7x7 conv in input stem with 3 3x3 conv
        avg_down (bool): Use AvgPool instead of stride conv when
            downsampling in the bottleneck.
        frozen_stages (int): Stages to be frozen (stop grad and set eval mode).
            -1 means not freezing any parameters.
        norm_cfg (dict): Dictionary to construct and config norm layer.
        norm_eval (bool): Whether to set norm layers to eval mode, namely,
            freeze running stats (mean and var). Note: Effect on Batch Norm
            and its variants only.
        plugins (list[dict]): List of plugins for stages, each dict contains:

            - cfg (dict, required): Cfg dict to build plugin.
            - position (str, required): Position inside block to insert
              plugin, options are 'after_conv1', 'after_conv2', 'after_conv3'.
            - stages (tuple[bool], optional): Stages to apply plugin, length
              should be same as 'num_stages'.
        with_cp (bool): Use checkpoint or not. Using checkpoint will save some
            memory while slowing down the training speed.
        zero_init_residual (bool): Whether to use zero init for last norm layer
            in resblocks to let them behave as identity.
        pretrained (str, optional): model pretrained path. Default: None
        init_cfg (dict or list[dict], optional): Initialization config dict.
            Default: None

    Example:
        >>> from mmdet.models import ResNet
        >>> import torch
        >>> self = ResNet(depth=18)
        >>> self.eval()
        >>> inputs = torch.rand(1, 3, 32, 32)
        >>> level_outputs = self.forward(inputs)
        >>> for level_out in level_outputs:
        ...     print(tuple(level_out.shape))
        (1, 64, 8, 8)
        (1, 128, 4, 4)
        (1, 256, 2, 2)
        (1, 512, 1, 1)
    """
    arch_settings = {18: (BasicBlock, (2, 2, 2, 2)), 34: (BasicBlock, (3, 4, 6, 3)), 50: (Bottleneck, (3, 4, 6, 3)), 101: (Bottleneck, (3, 4, 23, 3)), 152: (Bottleneck, (3, 8, 36, 3))}

    def __init__(self, depth, in_channels=3, stem_channels=None, base_channels=64, num_stages=4, strides=(1, 2, 2, 2), dilations=(1, 1, 1, 1), out_indices=(0, 1, 2, 3), style='pytorch', deep_stem=False, avg_down=False, frozen_stages=-1, conv_cfg=None, norm_cfg=dict(type='BN', requires_grad=True), norm_eval=True, dcn=None, stage_with_dcn=(False, False, False, False), plugins=None, with_cp=False, zero_init_residual=True, pretrained=None, init_cfg=None):
        super(ResNet, self).__init__(init_cfg)
        self.zero_init_residual = zero_init_residual
        if depth not in self.arch_settings:
            raise KeyError(f'invalid depth {depth} for resnet')
        block_init_cfg = None
        assert not (init_cfg and pretrained), 'init_cfg and pretrained cannot be specified at the same time'
        if isinstance(pretrained, str):
            warnings.warn('DeprecationWarning: pretrained is deprecated, please use "init_cfg" instead')
            self.init_cfg = dict(type='Pretrained', checkpoint=pretrained)
        elif pretrained is None:
            if init_cfg is None:
                self.init_cfg = [dict(type='Kaiming', layer='Conv2d'), dict(type='Constant', val=1, layer=['_BatchNorm', 'GroupNorm'])]
                block = self.arch_settings[depth][0]
                if self.zero_init_residual:
                    if block is BasicBlock:
                        block_init_cfg = dict(type='Constant', val=0, override=dict(name='norm2'))
                    elif block is Bottleneck:
                        block_init_cfg = dict(type='Constant', val=0, override=dict(name='norm3'))
        else:
            raise TypeError('pretrained must be a str or None')
        self.depth = depth
        if stem_channels is None:
            stem_channels = base_channels
        self.stem_channels = stem_channels
        self.base_channels = base_channels
        self.num_stages = num_stages
        assert num_stages >= 1 and num_stages <= 4
        self.strides = strides
        self.dilations = dilations
        assert len(strides) == len(dilations) == num_stages
        self.out_indices = out_indices
        assert max(out_indices) < num_stages
        self.style = style
        self.deep_stem = deep_stem
        self.avg_down = avg_down
        self.frozen_stages = frozen_stages
        self.conv_cfg = conv_cfg
        self.norm_cfg = norm_cfg
        self.with_cp = with_cp
        self.norm_eval = norm_eval
        self.dcn = dcn
        self.stage_with_dcn = stage_with_dcn
        if dcn is not None:
            assert len(stage_with_dcn) == num_stages
        self.plugins = plugins
        self.block, stage_blocks = self.arch_settings[depth]
        self.stage_blocks = stage_blocks[:num_stages]
        self.inplanes = stem_channels
        self._make_stem_layer(in_channels, stem_channels)
        self.res_layers = []
        for i, num_blocks in enumerate(self.stage_blocks):
            stride = strides[i]
            dilation = dilations[i]
            dcn = self.dcn if self.stage_with_dcn[i] else None
            if plugins is not None:
                stage_plugins = self.make_stage_plugins(plugins, i)
            else:
                stage_plugins = None
            planes = base_channels * 2 ** i
            res_layer = self.make_res_layer(block=self.block, inplanes=self.inplanes, planes=planes, num_blocks=num_blocks, stride=stride, dilation=dilation, style=self.style, avg_down=self.avg_down, with_cp=with_cp, conv_cfg=conv_cfg, norm_cfg=norm_cfg, dcn=dcn, plugins=stage_plugins, init_cfg=block_init_cfg)
            self.inplanes = planes * self.block.expansion
            layer_name = f'layer{i + 1}'
            self.add_module(layer_name, res_layer)
            self.res_layers.append(layer_name)
        self._freeze_stages()
        self.feat_dim = self.block.expansion * base_channels * 2 ** (len(self.stage_blocks) - 1)

    def make_stage_plugins(self, plugins, stage_idx):
        """Make plugins for ResNet ``stage_idx`` th stage.

        Currently we support to insert ``context_block``,
        ``empirical_attention_block``, ``nonlocal_block`` into the backbone
        like ResNet/ResNeXt. They could be inserted after conv1/conv2/conv3 of
        Bottleneck.

        An example of plugins format could be:

        Examples:
            >>> plugins=[
            ...     dict(cfg=dict(type='xxx', arg1='xxx'),
            ...          stages=(False, True, True, True),
            ...          position='after_conv2'),
            ...     dict(cfg=dict(type='yyy'),
            ...          stages=(True, True, True, True),
            ...          position='after_conv3'),
            ...     dict(cfg=dict(type='zzz', postfix='1'),
            ...          stages=(True, True, True, True),
            ...          position='after_conv3'),
            ...     dict(cfg=dict(type='zzz', postfix='2'),
            ...          stages=(True, True, True, True),
            ...          position='after_conv3')
            ... ]
            >>> self = ResNet(depth=18)
            >>> stage_plugins = self.make_stage_plugins(plugins, 0)
            >>> assert len(stage_plugins) == 3

        Suppose ``stage_idx=0``, the structure of blocks in the stage would be:

        .. code-block:: none

            conv1-> conv2->conv3->yyy->zzz1->zzz2

        Suppose 'stage_idx=1', the structure of blocks in the stage would be:

        .. code-block:: none

            conv1-> conv2->xxx->conv3->yyy->zzz1->zzz2

        If stages is missing, the plugin would be applied to all stages.

        Args:
            plugins (list[dict]): List of plugins cfg to build. The postfix is
                required if multiple same type plugins are inserted.
            stage_idx (int): Index of stage to build

        Returns:
            list[dict]: Plugins for current stage
        """
        stage_plugins = []
        for plugin in plugins:
            plugin = plugin.copy()
            stages = plugin.pop('stages', None)
            assert stages is None or len(stages) == self.num_stages
            if stages is None or stages[stage_idx]:
                stage_plugins.append(plugin)
        return stage_plugins

    def make_res_layer(self, **kwargs):
        """Pack all blocks in a stage into a ``ResLayer``."""
        return ResLayer(**kwargs)

    @property
    def norm1(self):
        """nn.Module: the normalization layer named "norm1" """
        return getattr(self, self.norm1_name)

    def _make_stem_layer(self, in_channels, stem_channels):
        if self.deep_stem:
            self.stem = nn.Sequential(build_conv_layer(self.conv_cfg, in_channels, stem_channels // 2, kernel_size=3, stride=2, padding=1, bias=False), build_norm_layer(self.norm_cfg, stem_channels // 2)[1], nn.ReLU(inplace=True), build_conv_layer(self.conv_cfg, stem_channels // 2, stem_channels // 2, kernel_size=3, stride=1, padding=1, bias=False), build_norm_layer(self.norm_cfg, stem_channels // 2)[1], nn.ReLU(inplace=True), build_conv_layer(self.conv_cfg, stem_channels // 2, stem_channels, kernel_size=3, stride=1, padding=1, bias=False), build_norm_layer(self.norm_cfg, stem_channels)[1], nn.ReLU(inplace=True))
        else:
            self.conv1 = build_conv_layer(self.conv_cfg, in_channels, stem_channels, kernel_size=7, stride=2, padding=3, bias=False)
            self.norm1_name, norm1 = build_norm_layer(self.norm_cfg, stem_channels, postfix=1)
            self.add_module(self.norm1_name, norm1)
            self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

    def _freeze_stages(self):
        if self.frozen_stages >= 0:
            if self.deep_stem:
                self.stem.eval()
                for param in self.stem.parameters():
                    param.requires_grad = False
            else:
                self.norm1.eval()
                for m in [self.conv1, self.norm1]:
                    for param in m.parameters():
                        param.requires_grad = False
        for i in range(1, self.frozen_stages + 1):
            m = getattr(self, f'layer{i}')
            m.eval()
            for param in m.parameters():
                param.requires_grad = False

    def forward(self, x):
        """Forward function."""
        if self.deep_stem:
            x = self.stem(x)
        else:
            x = self.conv1(x)
            x = self.norm1(x)
            x = self.relu(x)
        x = self.maxpool(x)
        outs = []
        for i, layer_name in enumerate(self.res_layers):
            res_layer = getattr(self, layer_name)
            x = res_layer(x)
            if i in self.out_indices:
                outs.append(x)
        return tuple(outs)

    def train(self, mode=True):
        """Convert the model into training mode while keep normalization layer
        freezed."""
        super(ResNet, self).train(mode)
        self._freeze_stages()
        if mode and self.norm_eval:
            for m in self.modules():
                if isinstance(m, _BatchNorm):
                    m.eval()

def make_stage_plugins(self, plugins, stage_idx):
    """Make plugins for ResNet ``stage_idx`` th stage.

        Currently we support to insert ``context_block``,
        ``empirical_attention_block``, ``nonlocal_block`` into the backbone
        like ResNet/ResNeXt. They could be inserted after conv1/conv2/conv3 of
        Bottleneck.

        An example of plugins format could be:

        Examples:
            >>> plugins=[
            ...     dict(cfg=dict(type='xxx', arg1='xxx'),
            ...          stages=(False, True, True, True),
            ...          position='after_conv2'),
            ...     dict(cfg=dict(type='yyy'),
            ...          stages=(True, True, True, True),
            ...          position='after_conv3'),
            ...     dict(cfg=dict(type='zzz', postfix='1'),
            ...          stages=(True, True, True, True),
            ...          position='after_conv3'),
            ...     dict(cfg=dict(type='zzz', postfix='2'),
            ...          stages=(True, True, True, True),
            ...          position='after_conv3')
            ... ]
            >>> self = ResNet(depth=18)
            >>> stage_plugins = self.make_stage_plugins(plugins, 0)
            >>> assert len(stage_plugins) == 3

        Suppose ``stage_idx=0``, the structure of blocks in the stage would be:

        .. code-block:: none

            conv1-> conv2->conv3->yyy->zzz1->zzz2

        Suppose 'stage_idx=1', the structure of blocks in the stage would be:

        .. code-block:: none

            conv1-> conv2->xxx->conv3->yyy->zzz1->zzz2

        If stages is missing, the plugin would be applied to all stages.

        Args:
            plugins (list[dict]): List of plugins cfg to build. The postfix is
                required if multiple same type plugins are inserted.
            stage_idx (int): Index of stage to build

        Returns:
            list[dict]: Plugins for current stage
        """
    stage_plugins = []
    for plugin in plugins:
        plugin = plugin.copy()
        stages = plugin.pop('stages', None)
        assert stages is None or len(stages) == self.num_stages
        if stages is None or stages[stage_idx]:
            stage_plugins.append(plugin)
    return stage_plugins

class HRModule(BaseModule):
    """High-Resolution Module for HRNet.

    In this module, every branch has 4 BasicBlocks/Bottlenecks. Fusion/Exchange
    is in this module.
    """

    def __init__(self, num_branches, blocks, num_blocks, in_channels, num_channels, multiscale_output=True, with_cp=False, conv_cfg=None, norm_cfg=dict(type='BN'), block_init_cfg=None, init_cfg=None):
        super(HRModule, self).__init__(init_cfg)
        self.block_init_cfg = block_init_cfg
        self._check_branches(num_branches, num_blocks, in_channels, num_channels)
        self.in_channels = in_channels
        self.num_branches = num_branches
        self.multiscale_output = multiscale_output
        self.norm_cfg = norm_cfg
        self.conv_cfg = conv_cfg
        self.with_cp = with_cp
        self.branches = self._make_branches(num_branches, blocks, num_blocks, num_channels)
        self.fuse_layers = self._make_fuse_layers()
        self.relu = nn.ReLU(inplace=False)

    def _check_branches(self, num_branches, num_blocks, in_channels, num_channels):
        if num_branches != len(num_blocks):
            error_msg = f'NUM_BRANCHES({num_branches}) != NUM_BLOCKS({len(num_blocks)})'
            raise ValueError(error_msg)
        if num_branches != len(num_channels):
            error_msg = f'NUM_BRANCHES({num_branches}) != NUM_CHANNELS({len(num_channels)})'
            raise ValueError(error_msg)
        if num_branches != len(in_channels):
            error_msg = f'NUM_BRANCHES({num_branches}) != NUM_INCHANNELS({len(in_channels)})'
            raise ValueError(error_msg)

    def _make_one_branch(self, branch_index, block, num_blocks, num_channels, stride=1):
        downsample = None
        if stride != 1 or self.in_channels[branch_index] != num_channels[branch_index] * block.expansion:
            downsample = nn.Sequential(build_conv_layer(self.conv_cfg, self.in_channels[branch_index], num_channels[branch_index] * block.expansion, kernel_size=1, stride=stride, bias=False), build_norm_layer(self.norm_cfg, num_channels[branch_index] * block.expansion)[1])
        layers = []
        layers.append(block(self.in_channels[branch_index], num_channels[branch_index], stride, downsample=downsample, with_cp=self.with_cp, norm_cfg=self.norm_cfg, conv_cfg=self.conv_cfg, init_cfg=self.block_init_cfg))
        self.in_channels[branch_index] = num_channels[branch_index] * block.expansion
        for i in range(1, num_blocks[branch_index]):
            layers.append(block(self.in_channels[branch_index], num_channels[branch_index], with_cp=self.with_cp, norm_cfg=self.norm_cfg, conv_cfg=self.conv_cfg, init_cfg=self.block_init_cfg))
        return Sequential(*layers)

    def _make_branches(self, num_branches, block, num_blocks, num_channels):
        branches = []
        for i in range(num_branches):
            branches.append(self._make_one_branch(i, block, num_blocks, num_channels))
        return ModuleList(branches)

    def _make_fuse_layers(self):
        if self.num_branches == 1:
            return None
        num_branches = self.num_branches
        in_channels = self.in_channels
        fuse_layers = []
        num_out_branches = num_branches if self.multiscale_output else 1
        for i in range(num_out_branches):
            fuse_layer = []
            for j in range(num_branches):
                if j > i:
                    fuse_layer.append(nn.Sequential(build_conv_layer(self.conv_cfg, in_channels[j], in_channels[i], kernel_size=1, stride=1, padding=0, bias=False), build_norm_layer(self.norm_cfg, in_channels[i])[1], nn.Upsample(scale_factor=2 ** (j - i), mode='nearest')))
                elif j == i:
                    fuse_layer.append(None)
                else:
                    conv_downsamples = []
                    for k in range(i - j):
                        if k == i - j - 1:
                            conv_downsamples.append(nn.Sequential(build_conv_layer(self.conv_cfg, in_channels[j], in_channels[i], kernel_size=3, stride=2, padding=1, bias=False), build_norm_layer(self.norm_cfg, in_channels[i])[1]))
                        else:
                            conv_downsamples.append(nn.Sequential(build_conv_layer(self.conv_cfg, in_channels[j], in_channels[j], kernel_size=3, stride=2, padding=1, bias=False), build_norm_layer(self.norm_cfg, in_channels[j])[1], nn.ReLU(inplace=False)))
                    fuse_layer.append(nn.Sequential(*conv_downsamples))
            fuse_layers.append(nn.ModuleList(fuse_layer))
        return nn.ModuleList(fuse_layers)

    def forward(self, x):
        """Forward function."""
        if self.num_branches == 1:
            return [self.branches[0](x[0])]
        for i in range(self.num_branches):
            x[i] = self.branches[i](x[i])
        x_fuse = []
        for i in range(len(self.fuse_layers)):
            y = 0
            for j in range(self.num_branches):
                if i == j:
                    y += x[j]
                else:
                    y += self.fuse_layers[i][j](x[j])
            x_fuse.append(self.relu(y))
        return x_fuse

def _check_branches(self, num_branches, num_blocks, in_channels, num_channels):
    if num_branches != len(num_blocks):
        error_msg = f'NUM_BRANCHES({num_branches}) != NUM_BLOCKS({len(num_blocks)})'
        raise ValueError(error_msg)
    if num_branches != len(num_channels):
        error_msg = f'NUM_BRANCHES({num_branches}) != NUM_CHANNELS({len(num_channels)})'
        raise ValueError(error_msg)
    if num_branches != len(in_channels):
        error_msg = f'NUM_BRANCHES({num_branches}) != NUM_INCHANNELS({len(in_channels)})'
        raise ValueError(error_msg)

class TaskDecomposition(nn.Module):
    """Task decomposition module in task-aligned predictor of TOOD.

    Args:
        feat_channels (int): Number of feature channels in TOOD head.
        stacked_convs (int): Number of conv layers in TOOD head.
        la_down_rate (int): Downsample rate of layer attention.
        conv_cfg (dict): Config dict for convolution layer.
        norm_cfg (dict): Config dict for normalization layer.
    """

    def __init__(self, feat_channels, stacked_convs, la_down_rate=8, conv_cfg=None, norm_cfg=None):
        super(TaskDecomposition, self).__init__()
        self.feat_channels = feat_channels
        self.stacked_convs = stacked_convs
        self.in_channels = self.feat_channels * self.stacked_convs
        self.norm_cfg = norm_cfg
        self.layer_attention = nn.Sequential(nn.Conv2d(self.in_channels, self.in_channels // la_down_rate, 1), nn.ReLU(inplace=True), nn.Conv2d(self.in_channels // la_down_rate, self.stacked_convs, 1, padding=0), nn.Sigmoid())
        self.reduction_conv = ConvModule(self.in_channels, self.feat_channels, 1, stride=1, padding=0, conv_cfg=conv_cfg, norm_cfg=norm_cfg, bias=norm_cfg is None)

    def init_weights(self):
        for m in self.layer_attention.modules():
            if isinstance(m, nn.Conv2d):
                normal_init(m, std=0.001)
        normal_init(self.reduction_conv.conv, std=0.01)

    def forward(self, feat, avg_feat=None):
        b, c, h, w = feat.shape
        if avg_feat is None:
            avg_feat = F.adaptive_avg_pool2d(feat, (1, 1))
        weight = self.layer_attention(avg_feat)
        conv_weight = weight.reshape(b, 1, self.stacked_convs, 1) * self.reduction_conv.conv.weight.reshape(1, self.feat_channels, self.stacked_convs, self.feat_channels)
        conv_weight = conv_weight.reshape(b, self.feat_channels, self.in_channels)
        feat = feat.reshape(b, self.in_channels, h * w)
        feat = torch.bmm(conv_weight, feat).reshape(b, self.feat_channels, h, w)
        if self.norm_cfg is not None:
            feat = self.reduction_conv.norm(feat)
        feat = self.reduction_conv.activate(feat)
        return feat

def forward(self, feat, avg_feat=None):
    b, c, h, w = feat.shape
    if avg_feat is None:
        avg_feat = F.adaptive_avg_pool2d(feat, (1, 1))
    weight = self.layer_attention(avg_feat)
    conv_weight = weight.reshape(b, 1, self.stacked_convs, 1) * self.reduction_conv.conv.weight.reshape(1, self.feat_channels, self.stacked_convs, self.feat_channels)
    conv_weight = conv_weight.reshape(b, self.feat_channels, self.in_channels)
    feat = feat.reshape(b, self.in_channels, h * w)
    feat = torch.bmm(conv_weight, feat).reshape(b, self.feat_channels, h, w)
    if self.norm_cfg is not None:
        feat = self.reduction_conv.norm(feat)
    feat = self.reduction_conv.activate(feat)
    return feat

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

def build_trans(self, cfg, in_channels, out_channels, **extra_args):
    cfg_ = cfg.copy()
    trans_type = cfg_.pop('type')
    trans_cls = self.transition_types[trans_type]
    return trans_cls(in_channels, out_channels, **cfg_, **extra_args)

class DyDCNv2(nn.Module):
    """ModulatedDeformConv2d with normalization layer used in DyHead.

    This module cannot be configured with `conv_cfg=dict(type='DCNv2')`
    because DyHead calculates offset and mask from middle-level feature.

    Args:
        in_channels (int): Number of input channels.
        out_channels (int): Number of output channels.
        stride (int | tuple[int], optional): Stride of the convolution.
            Default: 1.
        norm_cfg (dict, optional): Config dict for normalization layer.
            Default: dict(type='GN', num_groups=16, requires_grad=True).
    """

    def __init__(self, in_channels, out_channels, stride=1, norm_cfg=dict(type='GN', num_groups=16, requires_grad=True)):
        super().__init__()
        self.with_norm = norm_cfg is not None
        bias = not self.with_norm
        self.conv = ModulatedDeformConv2d(in_channels, out_channels, 3, stride=stride, padding=1, bias=bias)
        if self.with_norm:
            self.norm = build_norm_layer(norm_cfg, out_channels)[1]

    def forward(self, x, offset, mask):
        """Forward function."""
        x = self.conv(x.contiguous(), offset.contiguous(), mask)
        if self.with_norm:
            x = self.norm(x)
        return x

def forward(self, x, offset, mask):
    """Forward function."""
    x = self.conv(x.contiguous(), offset.contiguous(), mask)
    if self.with_norm:
        x = self.norm(x)
    return x

def parse_shape(shape):
    if len(shape) == 1:
        shape = (1, 3, shape[0], shape[0])
    elif len(args.shape) == 2:
        shape = (1, 3) + tuple(shape)
    else:
        raise ValueError('invalid input shape')
    return shape

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

def __init__(self, dataset, input_shape, logger, device='cuda:0', out_dir=None):
    self.dataset = dataset
    self.input_shape = input_shape
    self.logger = logger
    self.device = device
    self.out_dir = out_dir
    bbox_whs, img_shapes = self.get_whs_and_shapes()
    ratios = img_shapes.max(1, keepdims=True) / np.array([input_shape])
    self.bbox_whs = bbox_whs / ratios

def test_tpfp_imagenet():
    result = tpfp_imagenet(det_bboxes, gt_bboxes, gt_bboxes_ignore=gt_ignore, use_legacy_coordinate=True)
    tp = result[0]
    fp = result[1]
    assert tp.shape == (1, 3)
    assert fp.shape == (1, 3)
    assert (tp == np.array([[1, 1, 0]])).all()
    assert (fp == np.array([[0, 0, 1]])).all()
    result = tpfp_imagenet(det_bboxes, gt_bboxes, gt_bboxes_ignore=gt_ignore, use_legacy_coordinate=False)
    tp = result[0]
    fp = result[1]
    assert tp.shape == (1, 3)
    assert fp.shape == (1, 3)
    assert (tp == np.array([[1, 1, 0]])).all()
    assert (fp == np.array([[0, 0, 1]])).all()

def test_tpfp_default():
    result = tpfp_default(det_bboxes, gt_bboxes, gt_bboxes_ignore=gt_ignore, use_legacy_coordinate=True)
    tp = result[0]
    fp = result[1]
    assert tp.shape == (1, 3)
    assert fp.shape == (1, 3)
    assert (tp == np.array([[1, 1, 0]])).all()
    assert (fp == np.array([[0, 0, 1]])).all()
    result = tpfp_default(det_bboxes, gt_bboxes, gt_bboxes_ignore=gt_ignore, use_legacy_coordinate=False)
    tp = result[0]
    fp = result[1]
    assert tp.shape == (1, 3)
    assert fp.shape == (1, 3)
    assert (tp == np.array([[1, 1, 0]])).all()
    assert (fp == np.array([[0, 0, 1]])).all()

def _create_dummy_results():
    boxes = [np.array([[50, 60, 70, 80, 1.0], [100, 120, 130, 150, 0.98], [150, 160, 190, 200, 0.96], [250, 260, 350, 360, 0.95]])]
    return [boxes]

def _create_dummy_results():
    boxes = [np.zeros((0, 5)), np.zeros((0, 5)), np.array([[10, 10, 15, 15, 1.0], [15, 15, 30, 30, 0.98], [10, 10, 25, 25, 0.98], [28, 28, 35, 35, 0.97], [30, 30, 51, 51, 0.96], [100, 110, 120, 130, 0.15]]), np.array([[30, 30, 50, 50, 0.51]])]
    return [boxes]

def _construct_ann_info(h=427, w=640, c=3):
    bboxes = np.array([[222.62, 217.82, 241.81, 238.93], [50.5, 329.7, 130.23, 384.96], [175.47, 331.97, 254.8, 389.26]], dtype=np.float32)
    labels = np.array([9, 2, 2], dtype=np.int64)
    bboxes_ignore = np.array([[59.0, 253.0, 311.0, 337.0]], dtype=np.float32)
    masks = [[[222.62, 217.82, 222.62, 238.93, 241.81, 238.93, 240.85, 218.78]], [[69.19, 332.17, 82.39, 330.25, 97.24, 329.7, 114.01, 331.35, 116.76, 337.39, 119.78, 343.17, 128.03, 344.54, 128.86, 347.84, 124.18, 350.59, 129.96, 358.01, 130.23, 366.54, 129.13, 377.81, 125.28, 382.48, 119.78, 381.93, 117.31, 377.54, 116.21, 379.46, 114.83, 382.21, 107.14, 383.31, 105.49, 378.36, 77.99, 377.54, 75.79, 381.11, 69.74, 381.93, 66.72, 378.91, 65.07, 377.81, 63.15, 379.19, 62.32, 383.31, 52.7, 384.96, 50.5, 379.46, 51.32, 375.61, 51.6, 370.11, 51.6, 364.06, 53.52, 354.99, 56.27, 344.54, 59.57, 336.29, 66.45, 332.72]], [[175.47, 386.86, 175.87, 376.44, 177.08, 351.2, 189.1, 332.77, 194.31, 331.97, 236.37, 332.77, 244.79, 342.39, 246.79, 346.79, 248.39, 345.99, 251.6, 345.59, 254.8, 348.0, 254.8, 351.6, 250.0, 352.0, 250.0, 354.81, 251.6, 358.41, 251.6, 364.42, 251.6, 370.03, 252.8, 378.04, 252.8, 384.05, 250.8, 387.26, 246.39, 387.66, 245.19, 386.46, 242.38, 388.86, 233.97, 389.26, 232.77, 388.06, 232.77, 383.65, 195.91, 381.25, 195.91, 384.86, 191.1, 384.86, 187.49, 385.26, 186.69, 382.85, 184.29, 382.45, 183.09, 387.26, 178.68, 388.46, 176.28, 387.66]]]
    return dict(bboxes=bboxes, labels=labels, bboxes_ignore=bboxes_ignore, masks=masks)

def _load_bboxes(results):
    ann_info = results['ann_info']
    results['gt_bboxes'] = ann_info['bboxes'].copy()
    results['bbox_fields'] = ['gt_bboxes']
    gt_bboxes_ignore = ann_info.get('bboxes_ignore', None)
    if gt_bboxes_ignore is not None:
        results['gt_bboxes_ignore'] = gt_bboxes_ignore.copy()
        results['bbox_fields'].append('gt_bboxes_ignore')

def _load_labels(results):
    results['gt_labels'] = results['ann_info']['labels'].copy()

def _process_polygons(polygons):
    polygons = [np.array(p) for p in polygons]
    valid_polygons = []
    for polygon in polygons:
        if len(polygon) % 2 == 0 and len(polygon) >= 6:
            valid_polygons.append(polygon)
    return valid_polygons

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

def _imequalize(img):
    from PIL import Image, ImageOps
    img = Image.fromarray(img)
    equalized_img = np.asarray(ImageOps.equalize(img))
    return equalized_img

def _adjust_brightness(img, factor):
    from PIL import Image
    from PIL.ImageEnhance import Brightness
    img = Image.fromarray(img)
    brightened_img = Brightness(img).enhance(factor)
    return np.asarray(brightened_img)

def _adjust_contrast(img, factor):
    from PIL import Image
    from PIL.ImageEnhance import Contrast
    img = Image.fromarray(img[..., ::-1], mode='RGB')
    contrasted_img = Contrast(img).enhance(factor)
    return np.asarray(contrasted_img)[..., ::-1]

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

@staticmethod
def _xywh_to_tlwh(bbox_xywh):
    if isinstance(bbox_xywh, np.ndarray):
        bbox_tlwh = bbox_xywh.copy()
    elif isinstance(bbox_xywh, torch.Tensor):
        bbox_tlwh = bbox_xywh.clone()
    bbox_tlwh[:, 0] = bbox_xywh[:, 0] - bbox_xywh[:, 2] / 2.0
    bbox_tlwh[:, 1] = bbox_xywh[:, 1] - bbox_xywh[:, 3] / 2.0
    return bbox_tlwh

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

class Detection(object):
    """
    This class represents a bounding box detection in a single image.

    Parameters
    ----------
    tlwh : array_like
        Bounding box in format `(x, y, w, h)`.
    confidence : float
        Detector confidence score.
    feature : array_like
        A feature vector that describes the object contained in this image.

    Attributes
    ----------
    tlwh : ndarray
        Bounding box in format `(top left x, top left y, width, height)`.
    confidence : ndarray
        Detector confidence score.
    feature : ndarray | NoneType
        A feature vector that describes the object contained in this image.

    """

    def __init__(self, tlwh, confidence, feature):
        self.tlwh = np.asarray(tlwh, dtype=np.float32)
        self.confidence = float(confidence)
        self.feature = np.asarray(feature.cpu(), dtype=np.float32)

    def to_tlbr(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    def to_xyah(self):
        """Convert bounding box to format `(center x, center y, aspect ratio,
        height)`, where the aspect ratio is `width / height`.
        """
        ret = self.tlwh.copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

def to_tlbr(self):
    """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
    ret = self.tlwh.copy()
    ret[2:] += ret[:2]
    return ret

def to_xyah(self):
    """Convert bounding box to format `(center x, center y, aspect ratio,
        height)`, where the aspect ratio is `width / height`.
        """
    ret = self.tlwh.copy()
    ret[:2] += ret[2:] / 2
    ret[2] /= ret[3]
    return ret

def to_xyah_ext(bbox):
    """Convert bounding box to format `(center x, center y, aspect ratio,
    height)`, where the aspect ratio is `width / height`.
    """
    ret = bbox.copy()
    ret[:2] += ret[2:] / 2
    ret[2] /= ret[3]
    return ret

class KalmanFilter(object):
    """
    A simple Kalman filter for tracking bounding boxes in image space.
    The 8-dimensional state space
        x, y, a, h, vx, vy, va, vh
    contains the bounding box center position (x, y), aspect ratio a, height h,
    and their respective velocities.
    Object motion follows a constant velocity model. The bounding box location
    (x, y, a, h) is taken as direct observation of the state space (linear
    observation model).
    """

    def __init__(self):
        ndim, dt = (4, 1.0)
        self._motion_mat = np.eye(2 * ndim, 2 * ndim)
        for i in range(ndim):
            self._motion_mat[i, ndim + i] = dt
        self._update_mat = np.eye(ndim, 2 * ndim)
        self._std_weight_position = 1.0 / 20
        self._std_weight_velocity = 1.0 / 160

    def initiate(self, measurement):
        """Create track from unassociated measurement.
        Parameters
        ----------
        measurement : ndarray
            Bounding box coordinates (x, y, a, h) with center position (x, y),
            aspect ratio a, and height h.
        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector (8 dimensional) and covariance matrix (8x8
            dimensional) of the new track. Unobserved velocities are initialized
            to 0 mean.
        """
        mean_pos = measurement
        mean_vel = np.zeros_like(mean_pos)
        mean = np.r_[mean_pos, mean_vel]
        std = [2 * self._std_weight_position * measurement[0], 2 * self._std_weight_position * measurement[1], 1 * measurement[2], 2 * self._std_weight_position * measurement[3], 10 * self._std_weight_velocity * measurement[0], 10 * self._std_weight_velocity * measurement[1], 0.1 * measurement[2], 10 * self._std_weight_velocity * measurement[3]]
        covariance = np.diag(np.square(std))
        return (mean, covariance)

    def predict(self, mean, covariance):
        """Run Kalman filter prediction step.
        Parameters
        ----------
        mean : ndarray
            The 8 dimensional mean vector of the object state at the previous
            time step.
        covariance : ndarray
            The 8x8 dimensional covariance matrix of the object state at the
            previous time step.
        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector and covariance matrix of the predicted
            state. Unobserved velocities are initialized to 0 mean.
        """
        std_pos = [self._std_weight_position * mean[0], self._std_weight_position * mean[1], 1 * mean[2], self._std_weight_position * mean[3]]
        std_vel = [self._std_weight_velocity * mean[0], self._std_weight_velocity * mean[1], 0.1 * mean[2], self._std_weight_velocity * mean[3]]
        motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))
        mean = np.dot(self._motion_mat, mean)
        covariance = np.linalg.multi_dot((self._motion_mat, covariance, self._motion_mat.T)) + motion_cov
        return (mean, covariance)

    def project(self, mean, covariance, confidence=0.0):
        """Project state distribution to measurement space.
        Parameters
        ----------
        mean : ndarray
            The state's mean vector (8 dimensional array).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).
        confidence: (dyh) 检测框置信度
        Returns
        -------
        (ndarray, ndarray)
            Returns the projected mean and covariance matrix of the given state
            estimate.
        """
        std = [self._std_weight_position * mean[3], self._std_weight_position * mean[3], 0.1, self._std_weight_position * mean[3]]
        std = [(1 - confidence) * x for x in std]
        innovation_cov = np.diag(np.square(std))
        mean = np.dot(self._update_mat, mean)
        covariance = np.linalg.multi_dot((self._update_mat, covariance, self._update_mat.T))
        return (mean, covariance + innovation_cov)

    def update(self, mean, covariance, measurement, confidence=0.0):
        """Run Kalman filter correction step.
        Parameters
        ----------
        mean : ndarray
            The predicted state's mean vector (8 dimensional).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).
        measurement : ndarray
            The 4 dimensional measurement vector (x, y, a, h), where (x, y)
            is the center position, a the aspect ratio, and h the height of the
            bounding box.
        confidence: (dyh)检测框置信度
        Returns
        -------
        (ndarray, ndarray)
            Returns the measurement-corrected state distribution.
        """
        projected_mean, projected_cov = self.project(mean, covariance, confidence)
        chol_factor, lower = scipy.linalg.cho_factor(projected_cov, lower=True, check_finite=False)
        kalman_gain = scipy.linalg.cho_solve((chol_factor, lower), np.dot(covariance, self._update_mat.T).T, check_finite=False).T
        innovation = measurement - projected_mean
        new_mean = mean + np.dot(innovation, kalman_gain.T)
        new_covariance = covariance - np.linalg.multi_dot((kalman_gain, projected_cov, kalman_gain.T))
        return (new_mean, new_covariance)

    def gating_distance(self, mean, covariance, measurements, only_position=False):
        """Compute gating distance between state distribution and measurements.
        A suitable distance threshold can be obtained from `chi2inv95`. If
        `only_position` is False, the chi-square distribution has 4 degrees of
        freedom, otherwise 2.
        Parameters
        ----------
        mean : ndarray
            Mean vector over the state distribution (8 dimensional).
        covariance : ndarray
            Covariance of the state distribution (8x8 dimensional).
        measurements : ndarray
            An Nx4 dimensional matrix of N measurements, each in
            format (x, y, a, h) where (x, y) is the bounding box center
            position, a the aspect ratio, and h the height.
        only_position : Optional[bool]
            If True, distance computation is done with respect to the bounding
            box center position only.
        Returns
        -------
        ndarray
            Returns an array of length N, where the i-th element contains the
            squared Mahalanobis distance between (mean, covariance) and
            `measurements[i]`.
        """
        mean, covariance = self.project(mean, covariance)
        if only_position:
            mean, covariance = (mean[:2], covariance[:2, :2])
            measurements = measurements[:, :2]
        cholesky_factor = np.linalg.cholesky(covariance)
        d = measurements - mean
        z = scipy.linalg.solve_triangular(cholesky_factor, d.T, lower=True, check_finite=False, overwrite_b=True)
        squared_maha = np.sum(z * z, axis=0)
        return squared_maha

def __init__(self):
    ndim, dt = (4, 1.0)
    self._motion_mat = np.eye(2 * ndim, 2 * ndim)
    for i in range(ndim):
        self._motion_mat[i, ndim + i] = dt
    self._update_mat = np.eye(ndim, 2 * ndim)
    self._std_weight_position = 1.0 / 20
    self._std_weight_velocity = 1.0 / 160

def initiate(self, measurement):
    """Create track from unassociated measurement.
        Parameters
        ----------
        measurement : ndarray
            Bounding box coordinates (x, y, a, h) with center position (x, y),
            aspect ratio a, and height h.
        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector (8 dimensional) and covariance matrix (8x8
            dimensional) of the new track. Unobserved velocities are initialized
            to 0 mean.
        """
    mean_pos = measurement
    mean_vel = np.zeros_like(mean_pos)
    mean = np.r_[mean_pos, mean_vel]
    std = [2 * self._std_weight_position * measurement[0], 2 * self._std_weight_position * measurement[1], 1 * measurement[2], 2 * self._std_weight_position * measurement[3], 10 * self._std_weight_velocity * measurement[0], 10 * self._std_weight_velocity * measurement[1], 0.1 * measurement[2], 10 * self._std_weight_velocity * measurement[3]]
    covariance = np.diag(np.square(std))
    return (mean, covariance)

def predict(self, mean, covariance):
    """Run Kalman filter prediction step.
        Parameters
        ----------
        mean : ndarray
            The 8 dimensional mean vector of the object state at the previous
            time step.
        covariance : ndarray
            The 8x8 dimensional covariance matrix of the object state at the
            previous time step.
        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector and covariance matrix of the predicted
            state. Unobserved velocities are initialized to 0 mean.
        """
    std_pos = [self._std_weight_position * mean[0], self._std_weight_position * mean[1], 1 * mean[2], self._std_weight_position * mean[3]]
    std_vel = [self._std_weight_velocity * mean[0], self._std_weight_velocity * mean[1], 0.1 * mean[2], self._std_weight_velocity * mean[3]]
    motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))
    mean = np.dot(self._motion_mat, mean)
    covariance = np.linalg.multi_dot((self._motion_mat, covariance, self._motion_mat.T)) + motion_cov
    return (mean, covariance)

def project(self, mean, covariance, confidence=0.0):
    """Project state distribution to measurement space.
        Parameters
        ----------
        mean : ndarray
            The state's mean vector (8 dimensional array).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).
        confidence: (dyh) 检测框置信度
        Returns
        -------
        (ndarray, ndarray)
            Returns the projected mean and covariance matrix of the given state
            estimate.
        """
    std = [self._std_weight_position * mean[3], self._std_weight_position * mean[3], 0.1, self._std_weight_position * mean[3]]
    std = [(1 - confidence) * x for x in std]
    innovation_cov = np.diag(np.square(std))
    mean = np.dot(self._update_mat, mean)
    covariance = np.linalg.multi_dot((self._update_mat, covariance, self._update_mat.T))
    return (mean, covariance + innovation_cov)

def update(self, mean, covariance, measurement, confidence=0.0):
    """Run Kalman filter correction step.
        Parameters
        ----------
        mean : ndarray
            The predicted state's mean vector (8 dimensional).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).
        measurement : ndarray
            The 4 dimensional measurement vector (x, y, a, h), where (x, y)
            is the center position, a the aspect ratio, and h the height of the
            bounding box.
        confidence: (dyh)检测框置信度
        Returns
        -------
        (ndarray, ndarray)
            Returns the measurement-corrected state distribution.
        """
    projected_mean, projected_cov = self.project(mean, covariance, confidence)
    chol_factor, lower = scipy.linalg.cho_factor(projected_cov, lower=True, check_finite=False)
    kalman_gain = scipy.linalg.cho_solve((chol_factor, lower), np.dot(covariance, self._update_mat.T).T, check_finite=False).T
    innovation = measurement - projected_mean
    new_mean = mean + np.dot(innovation, kalman_gain.T)
    new_covariance = covariance - np.linalg.multi_dot((kalman_gain, projected_cov, kalman_gain.T))
    return (new_mean, new_covariance)

def gating_distance(self, mean, covariance, measurements, only_position=False):
    """Compute gating distance between state distribution and measurements.
        A suitable distance threshold can be obtained from `chi2inv95`. If
        `only_position` is False, the chi-square distribution has 4 degrees of
        freedom, otherwise 2.
        Parameters
        ----------
        mean : ndarray
            Mean vector over the state distribution (8 dimensional).
        covariance : ndarray
            Covariance of the state distribution (8x8 dimensional).
        measurements : ndarray
            An Nx4 dimensional matrix of N measurements, each in
            format (x, y, a, h) where (x, y) is the bounding box center
            position, a the aspect ratio, and h the height.
        only_position : Optional[bool]
            If True, distance computation is done with respect to the bounding
            box center position only.
        Returns
        -------
        ndarray
            Returns an array of length N, where the i-th element contains the
            squared Mahalanobis distance between (mean, covariance) and
            `measurements[i]`.
        """
    mean, covariance = self.project(mean, covariance)
    if only_position:
        mean, covariance = (mean[:2], covariance[:2, :2])
        measurements = measurements[:, :2]
    cholesky_factor = np.linalg.cholesky(covariance)
    d = measurements - mean
    z = scipy.linalg.solve_triangular(cholesky_factor, d.T, lower=True, check_finite=False, overwrite_b=True)
    squared_maha = np.sum(z * z, axis=0)
    return squared_maha

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

def gated_metric(tracks, dets, track_indices, detection_indices):
    features = np.array([dets[i].feature for i in detection_indices])
    targets = np.array([tracks[i].track_id for i in track_indices])
    cost_matrix = self.metric.distance(features, targets)
    cost_matrix = linear_assignment.gate_cost_matrix(cost_matrix, tracks, dets, track_indices, detection_indices, self.mc_lambda)
    return cost_matrix

def _initiate_track(self, detection, class_id, conf):
    self.tracks.append(Track(detection.to_xyah(), self._next_id, class_id, conf, self.n_init, self.max_age, self.ema_alpha, detection.feature))
    self._next_id += 1

def gate_cost_matrix(cost_matrix, tracks, detections, track_indices, detection_indices, mc_lambda, gated_cost=INFTY_COST, only_position=False):
    """Invalidate infeasible entries in cost matrix based on the state
    distributions obtained by Kalman filtering.
    Parameters
    ----------
    kf : The Kalman filter.
    cost_matrix : ndarray
        The NxM dimensional cost matrix, where N is the number of track indices
        and M is the number of detection indices, such that entry (i, j) is the
        association cost between `tracks[track_indices[i]]` and
        `detections[detection_indices[j]]`.
    tracks : List[track.Track]
        A list of predicted tracks at the current time step.
    detections : List[detection.Detection]
        A list of detections at the current time step.
    track_indices : List[int]
        List of track indices that maps rows in `cost_matrix` to tracks in
        `tracks` (see description above).
    detection_indices : List[int]
        List of detection indices that maps columns in `cost_matrix` to
        detections in `detections` (see description above).
    gated_cost : Optional[float]
        Entries in the cost matrix corresponding to infeasible associations are
        set this value. Defaults to a very large value.
    only_position : Optional[bool]
        If True, only the x, y position of the state distribution is considered
        during gating. Defaults to False.
    Returns
    -------
    ndarray
        Returns the modified cost matrix.
    """
    gating_dim = 2 if only_position else 4
    gating_threshold = kalman_filter.chi2inv95[gating_dim]
    measurements = np.asarray([detections[i].to_xyah() for i in detection_indices])
    for row, track_idx in enumerate(track_indices):
        track = tracks[track_idx]
        gating_distance = track.kf.gating_distance(track.mean, track.covariance, measurements, only_position)
        cost_matrix[row, gating_distance > gating_threshold] = gated_cost
        cost_matrix[row] = mc_lambda * cost_matrix[row] + (1 - mc_lambda) * gating_distance
    return cost_matrix

def iou(bbox, candidates):
    """Computer intersection over union.

    Parameters
    ----------
    bbox : ndarray
        A bounding box in format `(top left x, top left y, width, height)`.
    candidates : ndarray
        A matrix of candidate bounding boxes (one per row) in the same format
        as `bbox`.

    Returns
    -------
    ndarray
        The intersection over union in [0, 1] between the `bbox` and each
        candidate. A higher score means a larger fraction of the `bbox` is
        occluded by the candidate.

    """
    bbox_tl, bbox_br = (bbox[:2], bbox[:2] + bbox[2:])
    candidates_tl = candidates[:, :2]
    candidates_br = candidates[:, :2] + candidates[:, 2:]
    tl = np.c_[np.maximum(bbox_tl[0], candidates_tl[:, 0])[:, np.newaxis], np.maximum(bbox_tl[1], candidates_tl[:, 1])[:, np.newaxis]]
    br = np.c_[np.minimum(bbox_br[0], candidates_br[:, 0])[:, np.newaxis], np.minimum(bbox_br[1], candidates_br[:, 1])[:, np.newaxis]]
    wh = np.maximum(0.0, br - tl)
    area_intersection = wh.prod(axis=1)
    area_bbox = bbox[2:].prod()
    area_candidates = candidates[:, 2:].prod(axis=1)
    return area_intersection / (area_bbox + area_candidates - area_intersection)

def _cosine_distance(a, b, data_is_normalized=False):
    """Compute pair-wise cosine distance between points in `a` and `b`.
    Parameters
    ----------
    a : array_like
        An NxM matrix of N samples of dimensionality M.
    b : array_like
        An LxM matrix of L samples of dimensionality M.
    data_is_normalized : Optional[bool]
        If True, assumes rows in a and b are unit length vectors.
        Otherwise, a and b are explicitly normalized to lenght 1.
    Returns
    -------
    ndarray
        Returns a matrix of size len(a), len(b) such that eleement (i, j)
        contains the squared distance between `a[i]` and `b[j]`.
    """
    if not data_is_normalized:
        a = np.asarray(a) / np.linalg.norm(a, axis=1, keepdims=True)
        b = np.asarray(b) / np.linalg.norm(b, axis=1, keepdims=True)
    return 1.0 - np.dot(a, b.T)

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

def draw_boxes(img, bbox, identities=None, offset=(0, 0)):
    for i, box in enumerate(bbox):
        x1, y1, x2, y2 = [int(i) for i in box]
        x1 += offset[0]
        x2 += offset[0]
        y1 += offset[1]
        y2 += offset[1]
        id = int(identities[i]) if identities is not None else 0
        color = compute_color_for_labels(id)
        label = '{}{:d}'.format('', id)
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 2, 2)[0]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        cv2.rectangle(img, (x1, y1), (x1 + t_size[0] + 3, y1 + t_size[1] + 4), color, -1)
        cv2.putText(img, label, (x1, y1 + t_size[1] + 4), cv2.FONT_HERSHEY_PLAIN, 2, [255, 255, 255], 2)
    return img

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

def iou_batch(bboxes1, bboxes2):
    """
    From SORT: Computes IOU between two bboxes in the form [x1,y1,x2,y2]
    """
    bboxes2 = np.expand_dims(bboxes2, 0)
    bboxes1 = np.expand_dims(bboxes1, 1)
    xx1 = np.maximum(bboxes1[..., 0], bboxes2[..., 0])
    yy1 = np.maximum(bboxes1[..., 1], bboxes2[..., 1])
    xx2 = np.minimum(bboxes1[..., 2], bboxes2[..., 2])
    yy2 = np.minimum(bboxes1[..., 3], bboxes2[..., 3])
    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    wh = w * h
    o = wh / ((bboxes1[..., 2] - bboxes1[..., 0]) * (bboxes1[..., 3] - bboxes1[..., 1]) + (bboxes2[..., 2] - bboxes2[..., 0]) * (bboxes2[..., 3] - bboxes2[..., 1]) - wh)
    return o

def giou_batch(bboxes1, bboxes2):
    """
    :param bbox_p: predict of bbox(N,4)(x1,y1,x2,y2)
    :param bbox_g: groundtruth of bbox(N,4)(x1,y1,x2,y2)
    :return:
    """
    bboxes2 = np.expand_dims(bboxes2, 0)
    bboxes1 = np.expand_dims(bboxes1, 1)
    xx1 = np.maximum(bboxes1[..., 0], bboxes2[..., 0])
    yy1 = np.maximum(bboxes1[..., 1], bboxes2[..., 1])
    xx2 = np.minimum(bboxes1[..., 2], bboxes2[..., 2])
    yy2 = np.minimum(bboxes1[..., 3], bboxes2[..., 3])
    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    wh = w * h
    iou = wh / ((bboxes1[..., 2] - bboxes1[..., 0]) * (bboxes1[..., 3] - bboxes1[..., 1]) + (bboxes2[..., 2] - bboxes2[..., 0]) * (bboxes2[..., 3] - bboxes2[..., 1]) - wh)
    xxc1 = np.minimum(bboxes1[..., 0], bboxes2[..., 0])
    yyc1 = np.minimum(bboxes1[..., 1], bboxes2[..., 1])
    xxc2 = np.maximum(bboxes1[..., 2], bboxes2[..., 2])
    yyc2 = np.maximum(bboxes1[..., 3], bboxes2[..., 3])
    wc = xxc2 - xxc1
    hc = yyc2 - yyc1
    assert (wc > 0).all() and (hc > 0).all()
    area_enclose = wc * hc
    giou = iou - (area_enclose - wh) / area_enclose
    giou = (giou + 1.0) / 2.0
    return giou

def diou_batch(bboxes1, bboxes2):
    """
    :param bbox_p: predict of bbox(N,4)(x1,y1,x2,y2)
    :param bbox_g: groundtruth of bbox(N,4)(x1,y1,x2,y2)
    :return:
    """
    bboxes2 = np.expand_dims(bboxes2, 0)
    bboxes1 = np.expand_dims(bboxes1, 1)
    xx1 = np.maximum(bboxes1[..., 0], bboxes2[..., 0])
    yy1 = np.maximum(bboxes1[..., 1], bboxes2[..., 1])
    xx2 = np.minimum(bboxes1[..., 2], bboxes2[..., 2])
    yy2 = np.minimum(bboxes1[..., 3], bboxes2[..., 3])
    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    wh = w * h
    iou = wh / ((bboxes1[..., 2] - bboxes1[..., 0]) * (bboxes1[..., 3] - bboxes1[..., 1]) + (bboxes2[..., 2] - bboxes2[..., 0]) * (bboxes2[..., 3] - bboxes2[..., 1]) - wh)
    centerx1 = (bboxes1[..., 0] + bboxes1[..., 2]) / 2.0
    centery1 = (bboxes1[..., 1] + bboxes1[..., 3]) / 2.0
    centerx2 = (bboxes2[..., 0] + bboxes2[..., 2]) / 2.0
    centery2 = (bboxes2[..., 1] + bboxes2[..., 3]) / 2.0
    inner_diag = (centerx1 - centerx2) ** 2 + (centery1 - centery2) ** 2
    xxc1 = np.minimum(bboxes1[..., 0], bboxes2[..., 0])
    yyc1 = np.minimum(bboxes1[..., 1], bboxes2[..., 1])
    xxc2 = np.maximum(bboxes1[..., 2], bboxes2[..., 2])
    yyc2 = np.maximum(bboxes1[..., 3], bboxes2[..., 3])
    outer_diag = (xxc2 - xxc1) ** 2 + (yyc2 - yyc1) ** 2
    diou = iou - inner_diag / outer_diag
    return (diou + 1) / 2.0

def ciou_batch(bboxes1, bboxes2):
    """
    :param bbox_p: predict of bbox(N,4)(x1,y1,x2,y2)
    :param bbox_g: groundtruth of bbox(N,4)(x1,y1,x2,y2)
    :return:
    """
    bboxes2 = np.expand_dims(bboxes2, 0)
    bboxes1 = np.expand_dims(bboxes1, 1)
    xx1 = np.maximum(bboxes1[..., 0], bboxes2[..., 0])
    yy1 = np.maximum(bboxes1[..., 1], bboxes2[..., 1])
    xx2 = np.minimum(bboxes1[..., 2], bboxes2[..., 2])
    yy2 = np.minimum(bboxes1[..., 3], bboxes2[..., 3])
    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    wh = w * h
    iou = wh / ((bboxes1[..., 2] - bboxes1[..., 0]) * (bboxes1[..., 3] - bboxes1[..., 1]) + (bboxes2[..., 2] - bboxes2[..., 0]) * (bboxes2[..., 3] - bboxes2[..., 1]) - wh)
    centerx1 = (bboxes1[..., 0] + bboxes1[..., 2]) / 2.0
    centery1 = (bboxes1[..., 1] + bboxes1[..., 3]) / 2.0
    centerx2 = (bboxes2[..., 0] + bboxes2[..., 2]) / 2.0
    centery2 = (bboxes2[..., 1] + bboxes2[..., 3]) / 2.0
    inner_diag = (centerx1 - centerx2) ** 2 + (centery1 - centery2) ** 2
    xxc1 = np.minimum(bboxes1[..., 0], bboxes2[..., 0])
    yyc1 = np.minimum(bboxes1[..., 1], bboxes2[..., 1])
    xxc2 = np.maximum(bboxes1[..., 2], bboxes2[..., 2])
    yyc2 = np.maximum(bboxes1[..., 3], bboxes2[..., 3])
    outer_diag = (xxc2 - xxc1) ** 2 + (yyc2 - yyc1) ** 2
    w1 = bboxes1[..., 2] - bboxes1[..., 0]
    h1 = bboxes1[..., 3] - bboxes1[..., 1]
    w2 = bboxes2[..., 2] - bboxes2[..., 0]
    h2 = bboxes2[..., 3] - bboxes2[..., 1]
    h2 = h2 + 1.0
    h1 = h1 + 1.0
    arctan = np.arctan(w2 / h2) - np.arctan(w1 / h1)
    v = 4 / np.pi ** 2 * arctan ** 2
    S = 1 - iou
    alpha = v / (S + v)
    ciou = iou - inner_diag / outer_diag - alpha * v
    return (ciou + 1) / 2.0

def ct_dist(bboxes1, bboxes2):
    """
    Measure the center distance between two sets of bounding boxes,
    this is a coarse implementation, we don't recommend using it only
    for association, which can be unstable and sensitive to frame rate
    and object speed.
    """
    bboxes2 = np.expand_dims(bboxes2, 0)
    bboxes1 = np.expand_dims(bboxes1, 1)
    centerx1 = (bboxes1[..., 0] + bboxes1[..., 2]) / 2.0
    centery1 = (bboxes1[..., 1] + bboxes1[..., 3]) / 2.0
    centerx2 = (bboxes2[..., 0] + bboxes2[..., 2]) / 2.0
    centery2 = (bboxes2[..., 1] + bboxes2[..., 3]) / 2.0
    ct_dist2 = (centerx1 - centerx2) ** 2 + (centery1 - centery2) ** 2
    ct_dist = np.sqrt(ct_dist2)
    ct_dist = ct_dist / ct_dist.max()
    return ct_dist.max() - ct_dist

def speed_direction_batch(dets, tracks):
    tracks = tracks[..., np.newaxis]
    CX1, CY1 = ((dets[:, 0] + dets[:, 2]) / 2.0, (dets[:, 1] + dets[:, 3]) / 2.0)
    CX2, CY2 = ((tracks[:, 0] + tracks[:, 2]) / 2.0, (tracks[:, 1] + tracks[:, 3]) / 2.0)
    dx = CX1 - CX2
    dy = CY1 - CY2
    norm = np.sqrt(dx ** 2 + dy ** 2) + 1e-06
    dx = dx / norm
    dy = dy / norm
    return (dy, dx)

def linear_assignment(cost_matrix):
    try:
        import lap
        _, x, y = lap.lapjv(cost_matrix, extend_cost=True)
        return np.array([[y[i], i] for i in x if i >= 0])
    except ImportError:
        from scipy.optimize import linear_sum_assignment
        x, y = linear_sum_assignment(cost_matrix)
        return np.array(list(zip(x, y)))

def convert_bbox_to_z(bbox):
    """
    Takes a bounding box in the form [x1,y1,x2,y2] and returns z in the form
      [x,y,s,r] where x,y is the centre of the box and s is the scale/area and r is
      the aspect ratio
    """
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = bbox[0] + w / 2.0
    y = bbox[1] + h / 2.0
    s = w * h
    r = w / float(h + 1e-06)
    return np.array([x, y, s, r]).reshape((4, 1))

def convert_bbox_to_z_new(bbox):
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = bbox[0] + w / 2.0
    y = bbox[1] + h / 2.0
    return np.array([x, y, w, h]).reshape((4, 1))

def convert_x_to_bbox_new(x):
    x, y, w, h = x.reshape(-1)[:4]
    return np.array([x - w / 2, y - h / 2, x + w / 2, y + h / 2]).reshape(1, 4)

def convert_x_to_bbox(x, score=None):
    """
    Takes a bounding box in the centre form [x,y,s,r] and returns it in the form
      [x1,y1,x2,y2] where x1,y1 is the top left and x2,y2 is the bottom right
    """
    w = np.sqrt(x[2] * x[3])
    h = x[2] / w
    if score == None:
        return np.array([x[0] - w / 2.0, x[1] - h / 2.0, x[0] + w / 2.0, x[1] + h / 2.0]).reshape((1, 4))
    else:
        return np.array([x[0] - w / 2.0, x[1] - h / 2.0, x[0] + w / 2.0, x[1] + h / 2.0, score]).reshape((1, 5))

def speed_direction(bbox1, bbox2):
    cx1, cy1 = ((bbox1[0] + bbox1[2]) / 2.0, (bbox1[1] + bbox1[3]) / 2.0)
    cx2, cy2 = ((bbox2[0] + bbox2[2]) / 2.0, (bbox2[1] + bbox2[3]) / 2.0)
    speed = np.array([cy2 - cy1, cx2 - cx1])
    norm = np.sqrt((cy2 - cy1) ** 2 + (cx2 - cx1) ** 2) + 1e-06
    return speed / norm

def new_kf_process_noise(w, h, p=1 / 20, v=1 / 160):
    Q = np.diag(((p * w) ** 2, (p * h) ** 2, (p * w) ** 2, (p * h) ** 2, (v * w) ** 2, (v * h) ** 2, (v * w) ** 2, (v * h) ** 2))
    return Q

def new_kf_measurement_noise(w, h, m=1 / 20):
    w_var = (m * w) ** 2
    h_var = (m * h) ** 2
    R = np.diag((w_var, h_var, w_var, h_var))
    return R

class KalmanBoxTracker(object):
    """
    This class represents the internal state of individual tracked objects observed as bbox.
    """
    count = 0

    def __init__(self, bbox, cls, delta_t=3, orig=False, emb=None, alpha=0, new_kf=False):
        """
        Initialises a tracker using initial bounding box.

        """
        if not orig:
            from .kalmanfilter import KalmanFilterNew as KalmanFilter
        else:
            from filterpy.kalman import KalmanFilter
        self.cls = cls
        self.conf = bbox[-1]
        self.new_kf = new_kf
        if new_kf:
            self.kf = KalmanFilter(dim_x=8, dim_z=4)
            self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0, 0], [0, 1, 0, 0, 0, 1, 0, 0], [0, 0, 1, 0, 0, 0, 1, 0], [0, 0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 0, 1]])
            self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0, 0]])
            _, _, w, h = convert_bbox_to_z_new(bbox).reshape(-1)
            self.kf.P = new_kf_process_noise(w, h)
            self.kf.P[:4, :4] *= 4
            self.kf.P[4:, 4:] *= 100
            self.bbox_to_z_func = convert_bbox_to_z_new
            self.x_to_bbox_func = convert_x_to_bbox_new
        else:
            self.kf = KalmanFilter(dim_x=7, dim_z=4)
            self.kf.F = np.array([[1, 0, 0, 0, 1, 0, 0], [0, 1, 0, 0, 0, 1, 0], [0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 1]])
            self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0]])
            self.kf.R[2:, 2:] *= 10.0
            self.kf.P[4:, 4:] *= 1000.0
            self.kf.P *= 10.0
            self.kf.Q[-1, -1] *= 0.01
            self.kf.Q[4:, 4:] *= 0.01
            self.bbox_to_z_func = convert_bbox_to_z
            self.x_to_bbox_func = convert_x_to_bbox
        self.kf.x[:4] = self.bbox_to_z_func(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
        "\n        NOTE: [-1,-1,-1,-1,-1] is a compromising placeholder for non-observation status, the same for the return of \n        function k_previous_obs. It is ugly and I do not like it. But to support generate observation array in a \n        fast and unified way, which you would see below k_observations = np.array([k_previous_obs(...]]), let's bear it for now.\n        "
        self.last_observation = np.array([-1, -1, -1, -1, -1])
        self.history_observations = []
        self.observations = dict()
        self.velocity = None
        self.delta_t = delta_t
        self.emb = emb
        self.frozen = False

    def update(self, bbox, cls):
        """
        Updates the state vector with observed bbox.
        """
        if bbox is not None:
            self.frozen = False
            self.cls = cls
            if self.last_observation.sum() >= 0:
                previous_box = None
                for dt in range(self.delta_t, 0, -1):
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
            if self.new_kf:
                R = new_kf_measurement_noise(self.kf.x[2, 0], self.kf.x[3, 0])
                self.kf.update(self.bbox_to_z_func(bbox), R=R)
            else:
                self.kf.update(self.bbox_to_z_func(bbox))
        else:
            self.kf.update(bbox)
            self.frozen = True

    def update_emb(self, emb, alpha=0.9):
        self.emb = alpha * self.emb + (1 - alpha) * emb
        self.emb /= np.linalg.norm(self.emb)

    def get_emb(self):
        return self.emb.cpu()

    def apply_affine_correction(self, affine):
        m = affine[:, :2]
        t = affine[:, 2].reshape(2, 1)
        if self.last_observation.sum() > 0:
            ps = self.last_observation[:4].reshape(2, 2).T
            ps = m @ ps + t
            self.last_observation[:4] = ps.T.reshape(-1)
        for dt in range(self.delta_t, -1, -1):
            if self.age - dt in self.observations:
                ps = self.observations[self.age - dt][:4].reshape(2, 2).T
                ps = m @ ps + t
                self.observations[self.age - dt][:4] = ps.T.reshape(-1)
        self.kf.apply_affine_correction(m, t, self.new_kf)

    def predict(self):
        """
        Advances the state vector and returns the predicted bounding box estimate.
        """
        if self.new_kf:
            if self.kf.x[2] + self.kf.x[6] <= 0:
                self.kf.x[6] = 0
            if self.kf.x[3] + self.kf.x[7] <= 0:
                self.kf.x[7] = 0
            if self.frozen:
                self.kf.x[6] = self.kf.x[7] = 0
            Q = new_kf_process_noise(self.kf.x[2, 0], self.kf.x[3, 0])
        else:
            if self.kf.x[6] + self.kf.x[2] <= 0:
                self.kf.x[6] *= 0.0
            Q = None
        self.kf.predict(Q=Q)
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(self.x_to_bbox_func(self.kf.x))
        return self.history[-1]

    def get_state(self):
        """
        Returns the current bounding box estimate.
        """
        return self.x_to_bbox_func(self.kf.x)

    def mahalanobis(self, bbox):
        """Should be run after a predict() call for accuracy."""
        return self.kf.md_for_measurement(self.bbox_to_z_func(bbox))

def update_emb(self, emb, alpha=0.9):
    self.emb = alpha * self.emb + (1 - alpha) * emb
    self.emb /= np.linalg.norm(self.emb)

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

def update(x, P, z, R, H=None, return_all=False):
    """
    Add a new measurement (z) to the Kalman filter. If z is None, nothing
    is changed.
    This can handle either the multidimensional or unidimensional case. If
    all parameters are floats instead of arrays the filter will still work,
    and return floats for x, P as the result.
    update(1, 2, 1, 1, 1)  # univariate
    update(x, P, 1
    Parameters
    ----------
    x : numpy.array(dim_x, 1), or float
        State estimate vector
    P : numpy.array(dim_x, dim_x), or float
        Covariance matrix
    z : (dim_z, 1): array_like
        measurement for this update. z can be a scalar if dim_z is 1,
        otherwise it must be convertible to a column vector.
    R : numpy.array(dim_z, dim_z), or float
        Measurement noise matrix
    H : numpy.array(dim_x, dim_x), or float, optional
        Measurement function. If not provided, a value of 1 is assumed.
    return_all : bool, default False
        If true, y, K, S, and log_likelihood are returned, otherwise
        only x and P are returned.
    Returns
    -------
    x : numpy.array
        Posterior state estimate vector
    P : numpy.array
        Posterior covariance matrix
    y : numpy.array or scalar
        Residua. Difference between measurement and state in measurement space
    K : numpy.array
        Kalman gain
    S : numpy.array
        System uncertainty in measurement space
    log_likelihood : float
        log likelihood of the measurement
    """
    if z is None:
        if return_all:
            return (x, P, None, None, None, None)
        return (x, P)
    if H is None:
        H = np.array([1])
    if np.isscalar(H):
        H = np.array([H])
    Hx = np.atleast_1d(dot(H, x))
    z = reshape_z(z, Hx.shape[0], x.ndim)
    y = z - Hx
    S = dot(dot(H, P), H.T) + R
    try:
        K = dot(dot(P, H.T), linalg.inv(S))
    except:
        K = dot(dot(P, H.T), 1.0 / S)
    x = x + dot(K, y)
    KH = dot(K, H)
    try:
        I_KH = np.eye(KH.shape[0]) - KH
    except:
        I_KH = np.array([1 - KH])
    P = dot(dot(I_KH, P), I_KH.T) + dot(dot(K, R), K.T)
    if return_all:
        log_likelihood = logpdf(z, dot(H, x), S)
        return (x, P, y, K, S, log_likelihood)
    return (x, P)

def update_steadystate(x, z, K, H=None):
    """
    Add a new measurement (z) to the Kalman filter. If z is None, nothing
    is changed.
    Parameters
    ----------
    x : numpy.array(dim_x, 1), or float
        State estimate vector
    z : (dim_z, 1): array_like
        measurement for this update. z can be a scalar if dim_z is 1,
        otherwise it must be convertible to a column vector.
    K : numpy.array, or float
        Kalman gain matrix
    H : numpy.array(dim_x, dim_x), or float, optional
        Measurement function. If not provided, a value of 1 is assumed.
    Returns
    -------
    x : numpy.array
        Posterior state estimate vector
    Examples
    --------
    This can handle either the multidimensional or unidimensional case. If
    all parameters are floats instead of arrays the filter will still work,
    and return floats for x, P as the result.
    >>> update_steadystate(1, 2, 1)  # univariate
    >>> update_steadystate(x, P, z, H)
    """
    if z is None:
        return x
    if H is None:
        H = np.array([1])
    if np.isscalar(H):
        H = np.array([H])
    Hx = np.atleast_1d(dot(H, x))
    z = reshape_z(z, Hx.shape[0], x.ndim)
    y = z - Hx
    return x + dot(K, y)

def predict(x, P, F=1, Q=0, u=0, B=1, alpha=1.0):
    """
    Predict next state (prior) using the Kalman filter state propagation
    equations.
    Parameters
    ----------
    x : numpy.array
        State estimate vector
    P : numpy.array
        Covariance matrix
    F : numpy.array()
        State Transition matrix
    Q : numpy.array, Optional
        Process noise matrix
    u : numpy.array, Optional, default 0.
        Control vector. If non-zero, it is multiplied by B
        to create the control input into the system.
    B : numpy.array, optional, default 0.
        Control transition matrix.
    alpha : float, Optional, default=1.0
        Fading memory setting. 1.0 gives the normal Kalman filter, and
        values slightly larger than 1.0 (such as 1.02) give a fading
        memory effect - previous measurements have less influence on the
        filter's estimates. This formulation of the Fading memory filter
        (there are many) is due to Dan Simon
    Returns
    -------
    x : numpy.array
        Prior state estimate vector
    P : numpy.array
        Prior covariance matrix
    """
    if np.isscalar(F):
        F = np.array(F)
    x = dot(F, x) + dot(B, u)
    P = alpha * alpha * dot(dot(F, P), F.T) + Q
    return (x, P)

def predict_steadystate(x, F=1, u=0, B=1):
    """
    Predict next state (prior) using the Kalman filter state propagation
    equations. This steady state form only computes x, assuming that the
    covariance is constant.
    Parameters
    ----------
    x : numpy.array
        State estimate vector
    P : numpy.array
        Covariance matrix
    F : numpy.array()
        State Transition matrix
    u : numpy.array, Optional, default 0.
        Control vector. If non-zero, it is multiplied by B
        to create the control input into the system.
    B : numpy.array, optional, default 0.
        Control transition matrix.
    Returns
    -------
    x : numpy.array
        Prior state estimate vector
    """
    if np.isscalar(F):
        F = np.array(F)
    x = dot(F, x) + dot(B, u)
    return x

def rts_smoother(Xs, Ps, Fs, Qs):
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
    Fs : list-like collection of numpy.array
        State transition matrix of the Kalman filter at each time step.
    Qs : list-like collection of numpy.array, optional
        Process noise of the Kalman filter at each time step.
    Returns
    -------
    x : numpy.ndarray
       smoothed means
    P : numpy.ndarray
       smoothed state covariances
    K : numpy.ndarray
        smoother gain at each step
    pP : numpy.ndarray
       predicted state covariances
    Examples
    --------
    .. code-block:: Python
        zs = [t + random.randn()*4 for t in range (40)]
        (mu, cov, _, _) = kalman.batch_filter(zs)
        (x, P, K, pP) = rts_smoother(mu, cov, kf.F, kf.Q)
    """
    if len(Xs) != len(Ps):
        raise ValueError('length of Xs and Ps must be the same')
    n = Xs.shape[0]
    dim_x = Xs.shape[1]
    K = zeros((n, dim_x, dim_x))
    x, P, pP = (Xs.copy(), Ps.copy(), Ps.copy())
    for k in range(n - 2, -1, -1):
        pP[k] = dot(dot(Fs[k], P[k]), Fs[k].T) + Qs[k]
        K[k] = dot(dot(P[k], Fs[k].T), linalg.inv(pP[k]))
        x[k] += dot(K[k], x[k + 1] - dot(Fs[k], x[k]))
        P[k] += dot(dot(K[k], P[k + 1] - pP[k]), K[k].T)
    return (x, P, K, pP)

def iou_batch(bboxes1, bboxes2):
    """
    From SORT: Computes IOU between two bboxes in the form [x1,y1,x2,y2]
    """
    bboxes2 = np.expand_dims(bboxes2, 0)
    bboxes1 = np.expand_dims(bboxes1, 1)
    xx1 = np.maximum(bboxes1[..., 0], bboxes2[..., 0])
    yy1 = np.maximum(bboxes1[..., 1], bboxes2[..., 1])
    xx2 = np.minimum(bboxes1[..., 2], bboxes2[..., 2])
    yy2 = np.minimum(bboxes1[..., 3], bboxes2[..., 3])
    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    wh = w * h
    o = wh / ((bboxes1[..., 2] - bboxes1[..., 0]) * (bboxes1[..., 3] - bboxes1[..., 1]) + (bboxes2[..., 2] - bboxes2[..., 0]) * (bboxes2[..., 3] - bboxes2[..., 1]) - wh)
    return o

def giou_batch(bboxes1, bboxes2):
    """
    :param bbox_p: predict of bbox(N,4)(x1,y1,x2,y2)
    :param bbox_g: groundtruth of bbox(N,4)(x1,y1,x2,y2)
    :return:
    """
    bboxes2 = np.expand_dims(bboxes2, 0)
    bboxes1 = np.expand_dims(bboxes1, 1)
    xx1 = np.maximum(bboxes1[..., 0], bboxes2[..., 0])
    yy1 = np.maximum(bboxes1[..., 1], bboxes2[..., 1])
    xx2 = np.minimum(bboxes1[..., 2], bboxes2[..., 2])
    yy2 = np.minimum(bboxes1[..., 3], bboxes2[..., 3])
    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    wh = w * h
    iou = wh / ((bboxes1[..., 2] - bboxes1[..., 0]) * (bboxes1[..., 3] - bboxes1[..., 1]) + (bboxes2[..., 2] - bboxes2[..., 0]) * (bboxes2[..., 3] - bboxes2[..., 1]) - wh)
    xxc1 = np.minimum(bboxes1[..., 0], bboxes2[..., 0])
    yyc1 = np.minimum(bboxes1[..., 1], bboxes2[..., 1])
    xxc2 = np.maximum(bboxes1[..., 2], bboxes2[..., 2])
    yyc2 = np.maximum(bboxes1[..., 3], bboxes2[..., 3])
    wc = xxc2 - xxc1
    hc = yyc2 - yyc1
    assert (wc > 0).all() and (hc > 0).all()
    area_enclose = wc * hc
    giou = iou - (area_enclose - wh) / area_enclose
    giou = (giou + 1.0) / 2.0
    return giou

def diou_batch(bboxes1, bboxes2):
    """
    :param bbox_p: predict of bbox(N,4)(x1,y1,x2,y2)
    :param bbox_g: groundtruth of bbox(N,4)(x1,y1,x2,y2)
    :return:
    """
    bboxes2 = np.expand_dims(bboxes2, 0)
    bboxes1 = np.expand_dims(bboxes1, 1)
    xx1 = np.maximum(bboxes1[..., 0], bboxes2[..., 0])
    yy1 = np.maximum(bboxes1[..., 1], bboxes2[..., 1])
    xx2 = np.minimum(bboxes1[..., 2], bboxes2[..., 2])
    yy2 = np.minimum(bboxes1[..., 3], bboxes2[..., 3])
    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    wh = w * h
    iou = wh / ((bboxes1[..., 2] - bboxes1[..., 0]) * (bboxes1[..., 3] - bboxes1[..., 1]) + (bboxes2[..., 2] - bboxes2[..., 0]) * (bboxes2[..., 3] - bboxes2[..., 1]) - wh)
    centerx1 = (bboxes1[..., 0] + bboxes1[..., 2]) / 2.0
    centery1 = (bboxes1[..., 1] + bboxes1[..., 3]) / 2.0
    centerx2 = (bboxes2[..., 0] + bboxes2[..., 2]) / 2.0
    centery2 = (bboxes2[..., 1] + bboxes2[..., 3]) / 2.0
    inner_diag = (centerx1 - centerx2) ** 2 + (centery1 - centery2) ** 2
    xxc1 = np.minimum(bboxes1[..., 0], bboxes2[..., 0])
    yyc1 = np.minimum(bboxes1[..., 1], bboxes2[..., 1])
    xxc2 = np.maximum(bboxes1[..., 2], bboxes2[..., 2])
    yyc2 = np.maximum(bboxes1[..., 3], bboxes2[..., 3])
    outer_diag = (xxc2 - xxc1) ** 2 + (yyc2 - yyc1) ** 2
    diou = iou - inner_diag / outer_diag
    return (diou + 1) / 2.0

def ciou_batch(bboxes1, bboxes2):
    """
    :param bbox_p: predict of bbox(N,4)(x1,y1,x2,y2)
    :param bbox_g: groundtruth of bbox(N,4)(x1,y1,x2,y2)
    :return:
    """
    bboxes2 = np.expand_dims(bboxes2, 0)
    bboxes1 = np.expand_dims(bboxes1, 1)
    xx1 = np.maximum(bboxes1[..., 0], bboxes2[..., 0])
    yy1 = np.maximum(bboxes1[..., 1], bboxes2[..., 1])
    xx2 = np.minimum(bboxes1[..., 2], bboxes2[..., 2])
    yy2 = np.minimum(bboxes1[..., 3], bboxes2[..., 3])
    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    wh = w * h
    iou = wh / ((bboxes1[..., 2] - bboxes1[..., 0]) * (bboxes1[..., 3] - bboxes1[..., 1]) + (bboxes2[..., 2] - bboxes2[..., 0]) * (bboxes2[..., 3] - bboxes2[..., 1]) - wh)
    centerx1 = (bboxes1[..., 0] + bboxes1[..., 2]) / 2.0
    centery1 = (bboxes1[..., 1] + bboxes1[..., 3]) / 2.0
    centerx2 = (bboxes2[..., 0] + bboxes2[..., 2]) / 2.0
    centery2 = (bboxes2[..., 1] + bboxes2[..., 3]) / 2.0
    inner_diag = (centerx1 - centerx2) ** 2 + (centery1 - centery2) ** 2
    xxc1 = np.minimum(bboxes1[..., 0], bboxes2[..., 0])
    yyc1 = np.minimum(bboxes1[..., 1], bboxes2[..., 1])
    xxc2 = np.maximum(bboxes1[..., 2], bboxes2[..., 2])
    yyc2 = np.maximum(bboxes1[..., 3], bboxes2[..., 3])
    outer_diag = (xxc2 - xxc1) ** 2 + (yyc2 - yyc1) ** 2
    w1 = bboxes1[..., 2] - bboxes1[..., 0]
    h1 = bboxes1[..., 3] - bboxes1[..., 1]
    w2 = bboxes2[..., 2] - bboxes2[..., 0]
    h2 = bboxes2[..., 3] - bboxes2[..., 1]
    h2 = h2 + 1.0
    h1 = h1 + 1.0
    arctan = np.arctan(w2 / h2) - np.arctan(w1 / h1)
    v = 4 / np.pi ** 2 * arctan ** 2
    S = 1 - iou
    alpha = v / (S + v)
    ciou = iou - inner_diag / outer_diag - alpha * v
    return (ciou + 1) / 2.0

def ct_dist(bboxes1, bboxes2):
    """
        Measure the center distance between two sets of bounding boxes,
        this is a coarse implementation, we don't recommend using it only
        for association, which can be unstable and sensitive to frame rate
        and object speed.
    """
    bboxes2 = np.expand_dims(bboxes2, 0)
    bboxes1 = np.expand_dims(bboxes1, 1)
    centerx1 = (bboxes1[..., 0] + bboxes1[..., 2]) / 2.0
    centery1 = (bboxes1[..., 1] + bboxes1[..., 3]) / 2.0
    centerx2 = (bboxes2[..., 0] + bboxes2[..., 2]) / 2.0
    centery2 = (bboxes2[..., 1] + bboxes2[..., 3]) / 2.0
    ct_dist2 = (centerx1 - centerx2) ** 2 + (centery1 - centery2) ** 2
    ct_dist = np.sqrt(ct_dist2)
    ct_dist = ct_dist / ct_dist.max()
    return ct_dist.max() - ct_dist

def speed_direction_batch(dets, tracks):
    tracks = tracks[..., np.newaxis]
    CX1, CY1 = ((dets[:, 0] + dets[:, 2]) / 2.0, (dets[:, 1] + dets[:, 3]) / 2.0)
    CX2, CY2 = ((tracks[:, 0] + tracks[:, 2]) / 2.0, (tracks[:, 1] + tracks[:, 3]) / 2.0)
    dx = CX1 - CX2
    dy = CY1 - CY2
    norm = np.sqrt(dx ** 2 + dy ** 2) + 1e-06
    dx = dx / norm
    dy = dy / norm
    return (dy, dx)

def linear_assignment(cost_matrix):
    try:
        import lap
        _, x, y = lap.lapjv(cost_matrix, extend_cost=True)
        return np.array([[y[i], i] for i in x if i >= 0])
    except ImportError:
        from scipy.optimize import linear_sum_assignment
        x, y = linear_sum_assignment(cost_matrix)
        return np.array(list(zip(x, y)))

def convert_bbox_to_z(bbox):
    """
    Takes a bounding box in the form [x1,y1,x2,y2] and returns z in the form
      [x,y,s,r] where x,y is the centre of the box and s is the scale/area and r is
      the aspect ratio
    """
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = bbox[0] + w / 2.0
    y = bbox[1] + h / 2.0
    s = w * h
    r = w / float(h + 1e-06)
    return np.array([x, y, s, r]).reshape((4, 1))

def convert_x_to_bbox(x, score=None):
    """
    Takes a bounding box in the centre form [x,y,s,r] and returns it in the form
      [x1,y1,x2,y2] where x1,y1 is the top left and x2,y2 is the bottom right
    """
    w = np.sqrt(x[2] * x[3])
    h = x[2] / w
    if score == None:
        return np.array([x[0] - w / 2.0, x[1] - h / 2.0, x[0] + w / 2.0, x[1] + h / 2.0]).reshape((1, 4))
    else:
        return np.array([x[0] - w / 2.0, x[1] - h / 2.0, x[0] + w / 2.0, x[1] + h / 2.0, score]).reshape((1, 5))

def speed_direction(bbox1, bbox2):
    cx1, cy1 = ((bbox1[0] + bbox1[2]) / 2.0, (bbox1[1] + bbox1[3]) / 2.0)
    cx2, cy2 = ((bbox2[0] + bbox2[2]) / 2.0, (bbox2[1] + bbox2[3]) / 2.0)
    speed = np.array([cy2 - cy1, cx2 - cx1])
    norm = np.sqrt((cy2 - cy1) ** 2 + (cx2 - cx1) ** 2) + 1e-06
    return speed / norm

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

def update(x, P, z, R, H=None, return_all=False):
    """
    Add a new measurement (z) to the Kalman filter. If z is None, nothing
    is changed.
    This can handle either the multidimensional or unidimensional case. If
    all parameters are floats instead of arrays the filter will still work,
    and return floats for x, P as the result.
    update(1, 2, 1, 1, 1)  # univariate
    update(x, P, 1
    Parameters
    ----------
    x : numpy.array(dim_x, 1), or float
        State estimate vector
    P : numpy.array(dim_x, dim_x), or float
        Covariance matrix
    z : (dim_z, 1): array_like
        measurement for this update. z can be a scalar if dim_z is 1,
        otherwise it must be convertible to a column vector.
    R : numpy.array(dim_z, dim_z), or float
        Measurement noise matrix
    H : numpy.array(dim_x, dim_x), or float, optional
        Measurement function. If not provided, a value of 1 is assumed.
    return_all : bool, default False
        If true, y, K, S, and log_likelihood are returned, otherwise
        only x and P are returned.
    Returns
    -------
    x : numpy.array
        Posterior state estimate vector
    P : numpy.array
        Posterior covariance matrix
    y : numpy.array or scalar
        Residua. Difference between measurement and state in measurement space
    K : numpy.array
        Kalman gain
    S : numpy.array
        System uncertainty in measurement space
    log_likelihood : float
        log likelihood of the measurement
    """
    if z is None:
        if return_all:
            return (x, P, None, None, None, None)
        return (x, P)
    if H is None:
        H = np.array([1])
    if np.isscalar(H):
        H = np.array([H])
    Hx = np.atleast_1d(dot(H, x))
    z = reshape_z(z, Hx.shape[0], x.ndim)
    y = z - Hx
    S = dot(dot(H, P), H.T) + R
    try:
        K = dot(dot(P, H.T), linalg.inv(S))
    except:
        K = dot(dot(P, H.T), 1.0 / S)
    x = x + dot(K, y)
    KH = dot(K, H)
    try:
        I_KH = np.eye(KH.shape[0]) - KH
    except:
        I_KH = np.array([1 - KH])
    P = dot(dot(I_KH, P), I_KH.T) + dot(dot(K, R), K.T)
    if return_all:
        log_likelihood = logpdf(z, dot(H, x), S)
        return (x, P, y, K, S, log_likelihood)
    return (x, P)

def update_steadystate(x, z, K, H=None):
    """
    Add a new measurement (z) to the Kalman filter. If z is None, nothing
    is changed.
    Parameters
    ----------
    x : numpy.array(dim_x, 1), or float
        State estimate vector
    z : (dim_z, 1): array_like
        measurement for this update. z can be a scalar if dim_z is 1,
        otherwise it must be convertible to a column vector.
    K : numpy.array, or float
        Kalman gain matrix
    H : numpy.array(dim_x, dim_x), or float, optional
        Measurement function. If not provided, a value of 1 is assumed.
    Returns
    -------
    x : numpy.array
        Posterior state estimate vector
    Examples
    --------
    This can handle either the multidimensional or unidimensional case. If
    all parameters are floats instead of arrays the filter will still work,
    and return floats for x, P as the result.
    >>> update_steadystate(1, 2, 1)  # univariate
    >>> update_steadystate(x, P, z, H)
    """
    if z is None:
        return x
    if H is None:
        H = np.array([1])
    if np.isscalar(H):
        H = np.array([H])
    Hx = np.atleast_1d(dot(H, x))
    z = reshape_z(z, Hx.shape[0], x.ndim)
    y = z - Hx
    return x + dot(K, y)

def predict(x, P, F=1, Q=0, u=0, B=1, alpha=1.0):
    """
    Predict next state (prior) using the Kalman filter state propagation
    equations.
    Parameters
    ----------
    x : numpy.array
        State estimate vector
    P : numpy.array
        Covariance matrix
    F : numpy.array()
        State Transition matrix
    Q : numpy.array, Optional
        Process noise matrix
    u : numpy.array, Optional, default 0.
        Control vector. If non-zero, it is multiplied by B
        to create the control input into the system.
    B : numpy.array, optional, default 0.
        Control transition matrix.
    alpha : float, Optional, default=1.0
        Fading memory setting. 1.0 gives the normal Kalman filter, and
        values slightly larger than 1.0 (such as 1.02) give a fading
        memory effect - previous measurements have less influence on the
        filter's estimates. This formulation of the Fading memory filter
        (there are many) is due to Dan Simon
    Returns
    -------
    x : numpy.array
        Prior state estimate vector
    P : numpy.array
        Prior covariance matrix
    """
    if np.isscalar(F):
        F = np.array(F)
    x = dot(F, x) + dot(B, u)
    P = alpha * alpha * dot(dot(F, P), F.T) + Q
    return (x, P)

def predict_steadystate(x, F=1, u=0, B=1):
    """
    Predict next state (prior) using the Kalman filter state propagation
    equations. This steady state form only computes x, assuming that the
    covariance is constant.
    Parameters
    ----------
    x : numpy.array
        State estimate vector
    P : numpy.array
        Covariance matrix
    F : numpy.array()
        State Transition matrix
    u : numpy.array, Optional, default 0.
        Control vector. If non-zero, it is multiplied by B
        to create the control input into the system.
    B : numpy.array, optional, default 0.
        Control transition matrix.
    Returns
    -------
    x : numpy.array
        Prior state estimate vector
    """
    if np.isscalar(F):
        F = np.array(F)
    x = dot(F, x) + dot(B, u)
    return x

def rts_smoother(Xs, Ps, Fs, Qs):
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
    Fs : list-like collection of numpy.array
        State transition matrix of the Kalman filter at each time step.
    Qs : list-like collection of numpy.array, optional
        Process noise of the Kalman filter at each time step.
    Returns
    -------
    x : numpy.ndarray
       smoothed means
    P : numpy.ndarray
       smoothed state covariances
    K : numpy.ndarray
        smoother gain at each step
    pP : numpy.ndarray
       predicted state covariances
    Examples
    --------
    .. code-block:: Python
        zs = [t + random.randn()*4 for t in range (40)]
        (mu, cov, _, _) = kalman.batch_filter(zs)
        (x, P, K, pP) = rts_smoother(mu, cov, kf.F, kf.Q)
    """
    if len(Xs) != len(Ps):
        raise ValueError('length of Xs and Ps must be the same')
    n = Xs.shape[0]
    dim_x = Xs.shape[1]
    K = zeros((n, dim_x, dim_x))
    x, P, pP = (Xs.copy(), Ps.copy(), Ps.copy())
    for k in range(n - 2, -1, -1):
        pP[k] = dot(dot(Fs[k], P[k]), Fs[k].T) + Qs[k]
        K[k] = dot(dot(P[k], Fs[k].T), linalg.inv(pP[k]))
        x[k] += dot(K[k], x[k + 1] - dot(Fs[k], x[k]))
        P[k] += dot(dot(K[k], P[k + 1] - pP[k]), K[k].T)
    return (x, P, K, pP)

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

def __init__(self, tlwh, score, cls):
    self._tlwh = np.asarray(tlwh, dtype=np.float32)
    self.kalman_filter = None
    self.mean, self.covariance = (None, None)
    self.is_activated = False
    self.score = score
    self.tracklet_len = 0
    self.cls = cls

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

class BYTETracker(object):

    def __init__(self, track_thresh=0.45, match_thresh=0.8, track_buffer=25, frame_rate=30):
        self.tracked_stracks = []
        self.lost_stracks = []
        self.removed_stracks = []
        self.frame_id = 0
        self.track_buffer = track_buffer
        self.track_thresh = track_thresh
        self.match_thresh = match_thresh
        self.det_thresh = track_thresh + 0.1
        self.buffer_size = int(frame_rate / 30.0 * track_buffer)
        self.max_time_lost = self.buffer_size
        self.kalman_filter = KalmanFilter()

    def update(self, dets, _):
        self.frame_id += 1
        activated_starcks = []
        refind_stracks = []
        lost_stracks = []
        removed_stracks = []
        xyxys = dets[:, 0:4]
        xywh = xyxy2xywh(xyxys.numpy())
        confs = dets[:, 4]
        clss = dets[:, 5]
        classes = clss.numpy()
        xyxys = xyxys.numpy()
        confs = confs.numpy()
        remain_inds = confs > self.track_thresh
        inds_low = confs > 0.1
        inds_high = confs < self.track_thresh
        inds_second = np.logical_and(inds_low, inds_high)
        dets_second = xywh[inds_second]
        dets = xywh[remain_inds]
        scores_keep = confs[remain_inds]
        scores_second = confs[inds_second]
        clss_keep = classes[remain_inds]
        clss_second = classes[inds_second]
        if len(dets) > 0:
            'Detections'
            detections = [STrack(xyxy, s, c) for xyxy, s, c in zip(dets, scores_keep, clss_keep)]
        else:
            detections = []
        ' Add newly detected tracklets to tracked_stracks'
        unconfirmed = []
        tracked_stracks = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)
        ' Step 2: First association, with high score detection boxes'
        strack_pool = joint_stracks(tracked_stracks, self.lost_stracks)
        STrack.multi_predict(strack_pool)
        dists = matching.iou_distance(strack_pool, detections)
        dists = matching.fuse_score(dists, detections)
        matches, u_track, u_detection = matching.linear_assignment(dists, thresh=self.match_thresh)
        for itracked, idet in matches:
            track = strack_pool[itracked]
            det = detections[idet]
            if track.state == TrackState.Tracked:
                track.update(detections[idet], self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)
        ' Step 3: Second association, with low score detection boxes'
        if len(dets_second) > 0:
            'Detections'
            detections_second = [STrack(xywh, s, c) for xywh, s, c in zip(dets_second, scores_second, clss_second)]
        else:
            detections_second = []
        r_tracked_stracks = [strack_pool[i] for i in u_track if strack_pool[i].state == TrackState.Tracked]
        dists = matching.iou_distance(r_tracked_stracks, detections_second)
        matches, u_track, u_detection_second = matching.linear_assignment(dists, thresh=0.5)
        for itracked, idet in matches:
            track = r_tracked_stracks[itracked]
            det = detections_second[idet]
            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)
        for it in u_track:
            track = r_tracked_stracks[it]
            if not track.state == TrackState.Lost:
                track.mark_lost()
                lost_stracks.append(track)
        'Deal with unconfirmed tracks, usually tracks with only one beginning frame'
        detections = [detections[i] for i in u_detection]
        dists = matching.iou_distance(unconfirmed, detections)
        dists = matching.fuse_score(dists, detections)
        matches, u_unconfirmed, u_detection = matching.linear_assignment(dists, thresh=0.7)
        for itracked, idet in matches:
            unconfirmed[itracked].update(detections[idet], self.frame_id)
            activated_starcks.append(unconfirmed[itracked])
        for it in u_unconfirmed:
            track = unconfirmed[it]
            track.mark_removed()
            removed_stracks.append(track)
        ' Step 4: Init new stracks'
        for inew in u_detection:
            track = detections[inew]
            if track.score < self.det_thresh:
                continue
            track.activate(self.kalman_filter, self.frame_id)
            activated_starcks.append(track)
        ' Step 5: Update state'
        for track in self.lost_stracks:
            if self.frame_id - track.end_frame > self.max_time_lost:
                track.mark_removed()
                removed_stracks.append(track)
        self.tracked_stracks = [t for t in self.tracked_stracks if t.state == TrackState.Tracked]
        self.tracked_stracks = joint_stracks(self.tracked_stracks, activated_starcks)
        self.tracked_stracks = joint_stracks(self.tracked_stracks, refind_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.tracked_stracks)
        self.lost_stracks.extend(lost_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.removed_stracks)
        self.removed_stracks.extend(removed_stracks)
        self.tracked_stracks, self.lost_stracks = remove_duplicate_stracks(self.tracked_stracks, self.lost_stracks)
        output_stracks = [track for track in self.tracked_stracks if track.is_activated]
        outputs = []
        for t in output_stracks:
            output = []
            tlwh = t.tlwh
            tid = t.track_id
            tlwh = np.expand_dims(tlwh, axis=0)
            xyxy = xywh2xyxy(tlwh)
            xyxy = np.squeeze(xyxy, axis=0)
            output.extend(xyxy)
            output.append(tid)
            output.append(t.cls)
            output.append(t.score)
            outputs.append(output)
        return outputs

def update(self, dets, _):
    self.frame_id += 1
    activated_starcks = []
    refind_stracks = []
    lost_stracks = []
    removed_stracks = []
    xyxys = dets[:, 0:4]
    xywh = xyxy2xywh(xyxys.numpy())
    confs = dets[:, 4]
    clss = dets[:, 5]
    classes = clss.numpy()
    xyxys = xyxys.numpy()
    confs = confs.numpy()
    remain_inds = confs > self.track_thresh
    inds_low = confs > 0.1
    inds_high = confs < self.track_thresh
    inds_second = np.logical_and(inds_low, inds_high)
    dets_second = xywh[inds_second]
    dets = xywh[remain_inds]
    scores_keep = confs[remain_inds]
    scores_second = confs[inds_second]
    clss_keep = classes[remain_inds]
    clss_second = classes[inds_second]
    if len(dets) > 0:
        'Detections'
        detections = [STrack(xyxy, s, c) for xyxy, s, c in zip(dets, scores_keep, clss_keep)]
    else:
        detections = []
    ' Add newly detected tracklets to tracked_stracks'
    unconfirmed = []
    tracked_stracks = []
    for track in self.tracked_stracks:
        if not track.is_activated:
            unconfirmed.append(track)
        else:
            tracked_stracks.append(track)
    ' Step 2: First association, with high score detection boxes'
    strack_pool = joint_stracks(tracked_stracks, self.lost_stracks)
    STrack.multi_predict(strack_pool)
    dists = matching.iou_distance(strack_pool, detections)
    dists = matching.fuse_score(dists, detections)
    matches, u_track, u_detection = matching.linear_assignment(dists, thresh=self.match_thresh)
    for itracked, idet in matches:
        track = strack_pool[itracked]
        det = detections[idet]
        if track.state == TrackState.Tracked:
            track.update(detections[idet], self.frame_id)
            activated_starcks.append(track)
        else:
            track.re_activate(det, self.frame_id, new_id=False)
            refind_stracks.append(track)
    ' Step 3: Second association, with low score detection boxes'
    if len(dets_second) > 0:
        'Detections'
        detections_second = [STrack(xywh, s, c) for xywh, s, c in zip(dets_second, scores_second, clss_second)]
    else:
        detections_second = []
    r_tracked_stracks = [strack_pool[i] for i in u_track if strack_pool[i].state == TrackState.Tracked]
    dists = matching.iou_distance(r_tracked_stracks, detections_second)
    matches, u_track, u_detection_second = matching.linear_assignment(dists, thresh=0.5)
    for itracked, idet in matches:
        track = r_tracked_stracks[itracked]
        det = detections_second[idet]
        if track.state == TrackState.Tracked:
            track.update(det, self.frame_id)
            activated_starcks.append(track)
        else:
            track.re_activate(det, self.frame_id, new_id=False)
            refind_stracks.append(track)
    for it in u_track:
        track = r_tracked_stracks[it]
        if not track.state == TrackState.Lost:
            track.mark_lost()
            lost_stracks.append(track)
    'Deal with unconfirmed tracks, usually tracks with only one beginning frame'
    detections = [detections[i] for i in u_detection]
    dists = matching.iou_distance(unconfirmed, detections)
    dists = matching.fuse_score(dists, detections)
    matches, u_unconfirmed, u_detection = matching.linear_assignment(dists, thresh=0.7)
    for itracked, idet in matches:
        unconfirmed[itracked].update(detections[idet], self.frame_id)
        activated_starcks.append(unconfirmed[itracked])
    for it in u_unconfirmed:
        track = unconfirmed[it]
        track.mark_removed()
        removed_stracks.append(track)
    ' Step 4: Init new stracks'
    for inew in u_detection:
        track = detections[inew]
        if track.score < self.det_thresh:
            continue
        track.activate(self.kalman_filter, self.frame_id)
        activated_starcks.append(track)
    ' Step 5: Update state'
    for track in self.lost_stracks:
        if self.frame_id - track.end_frame > self.max_time_lost:
            track.mark_removed()
            removed_stracks.append(track)
    self.tracked_stracks = [t for t in self.tracked_stracks if t.state == TrackState.Tracked]
    self.tracked_stracks = joint_stracks(self.tracked_stracks, activated_starcks)
    self.tracked_stracks = joint_stracks(self.tracked_stracks, refind_stracks)
    self.lost_stracks = sub_stracks(self.lost_stracks, self.tracked_stracks)
    self.lost_stracks.extend(lost_stracks)
    self.lost_stracks = sub_stracks(self.lost_stracks, self.removed_stracks)
    self.removed_stracks.extend(removed_stracks)
    self.tracked_stracks, self.lost_stracks = remove_duplicate_stracks(self.tracked_stracks, self.lost_stracks)
    output_stracks = [track for track in self.tracked_stracks if track.is_activated]
    outputs = []
    for t in output_stracks:
        output = []
        tlwh = t.tlwh
        tid = t.track_id
        tlwh = np.expand_dims(tlwh, axis=0)
        xyxy = xywh2xyxy(tlwh)
        xyxy = np.squeeze(xyxy, axis=0)
        output.extend(xyxy)
        output.append(tid)
        output.append(t.cls)
        output.append(t.score)
        outputs.append(output)
    return outputs

class KalmanFilter(object):
    """
    A simple Kalman filter for tracking bounding boxes in image space.

    The 8-dimensional state space

        x, y, a, h, vx, vy, va, vh

    contains the bounding box center position (x, y), aspect ratio a, height h,
    and their respective velocities.

    Object motion follows a constant velocity model. The bounding box location
    (x, y, a, h) is taken as direct observation of the state space (linear
    observation model).

    """

    def __init__(self):
        ndim, dt = (4, 1.0)
        self._motion_mat = np.eye(2 * ndim, 2 * ndim)
        for i in range(ndim):
            self._motion_mat[i, ndim + i] = dt
        self._update_mat = np.eye(ndim, 2 * ndim)
        self._std_weight_position = 1.0 / 20
        self._std_weight_velocity = 1.0 / 160

    def initiate(self, measurement):
        """Create track from unassociated measurement.

        Parameters
        ----------
        measurement : ndarray
            Bounding box coordinates (x, y, a, h) with center position (x, y),
            aspect ratio a, and height h.

        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector (8 dimensional) and covariance matrix (8x8
            dimensional) of the new track. Unobserved velocities are initialized
            to 0 mean.

        """
        mean_pos = measurement
        mean_vel = np.zeros_like(mean_pos)
        mean = np.r_[mean_pos, mean_vel]
        std = [2 * self._std_weight_position * measurement[3], 2 * self._std_weight_position * measurement[3], 0.01, 2 * self._std_weight_position * measurement[3], 10 * self._std_weight_velocity * measurement[3], 10 * self._std_weight_velocity * measurement[3], 1e-05, 10 * self._std_weight_velocity * measurement[3]]
        covariance = np.diag(np.square(std))
        return (mean, covariance)

    def predict(self, mean, covariance):
        """Run Kalman filter prediction step.

        Parameters
        ----------
        mean : ndarray
            The 8 dimensional mean vector of the object state at the previous
            time step.
        covariance : ndarray
            The 8x8 dimensional covariance matrix of the object state at the
            previous time step.

        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector and covariance matrix of the predicted
            state. Unobserved velocities are initialized to 0 mean.

        """
        std_pos = [self._std_weight_position * mean[3], self._std_weight_position * mean[3], 0.01, self._std_weight_position * mean[3]]
        std_vel = [self._std_weight_velocity * mean[3], self._std_weight_velocity * mean[3], 1e-05, self._std_weight_velocity * mean[3]]
        motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))
        mean = np.dot(mean, self._motion_mat.T)
        covariance = np.linalg.multi_dot((self._motion_mat, covariance, self._motion_mat.T)) + motion_cov
        return (mean, covariance)

    def project(self, mean, covariance):
        """Project state distribution to measurement space.

        Parameters
        ----------
        mean : ndarray
            The state's mean vector (8 dimensional array).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).

        Returns
        -------
        (ndarray, ndarray)
            Returns the projected mean and covariance matrix of the given state
            estimate.

        """
        std = [self._std_weight_position * mean[3], self._std_weight_position * mean[3], 0.1, self._std_weight_position * mean[3]]
        innovation_cov = np.diag(np.square(std))
        mean = np.dot(self._update_mat, mean)
        covariance = np.linalg.multi_dot((self._update_mat, covariance, self._update_mat.T))
        return (mean, covariance + innovation_cov)

    def multi_predict(self, mean, covariance):
        """Run Kalman filter prediction step (Vectorized version).
        Parameters
        ----------
        mean : ndarray
            The Nx8 dimensional mean matrix of the object states at the previous
            time step.
        covariance : ndarray
            The Nx8x8 dimensional covariance matrics of the object states at the
            previous time step.
        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector and covariance matrix of the predicted
            state. Unobserved velocities are initialized to 0 mean.
        """
        std_pos = [self._std_weight_position * mean[:, 3], self._std_weight_position * mean[:, 3], 0.01 * np.ones_like(mean[:, 3]), self._std_weight_position * mean[:, 3]]
        std_vel = [self._std_weight_velocity * mean[:, 3], self._std_weight_velocity * mean[:, 3], 1e-05 * np.ones_like(mean[:, 3]), self._std_weight_velocity * mean[:, 3]]
        sqr = np.square(np.r_[std_pos, std_vel]).T
        motion_cov = []
        for i in range(len(mean)):
            motion_cov.append(np.diag(sqr[i]))
        motion_cov = np.asarray(motion_cov)
        mean = np.dot(mean, self._motion_mat.T)
        left = np.dot(self._motion_mat, covariance).transpose((1, 0, 2))
        covariance = np.dot(left, self._motion_mat.T) + motion_cov
        return (mean, covariance)

    def update(self, mean, covariance, measurement):
        """Run Kalman filter correction step.

        Parameters
        ----------
        mean : ndarray
            The predicted state's mean vector (8 dimensional).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).
        measurement : ndarray
            The 4 dimensional measurement vector (x, y, a, h), where (x, y)
            is the center position, a the aspect ratio, and h the height of the
            bounding box.

        Returns
        -------
        (ndarray, ndarray)
            Returns the measurement-corrected state distribution.

        """
        projected_mean, projected_cov = self.project(mean, covariance)
        chol_factor, lower = scipy.linalg.cho_factor(projected_cov, lower=True, check_finite=False)
        kalman_gain = scipy.linalg.cho_solve((chol_factor, lower), np.dot(covariance, self._update_mat.T).T, check_finite=False).T
        innovation = measurement - projected_mean
        new_mean = mean + np.dot(innovation, kalman_gain.T)
        new_covariance = covariance - np.linalg.multi_dot((kalman_gain, projected_cov, kalman_gain.T))
        return (new_mean, new_covariance)

    def gating_distance(self, mean, covariance, measurements, only_position=False, metric='maha'):
        """Compute gating distance between state distribution and measurements.
        A suitable distance threshold can be obtained from `chi2inv95`. If
        `only_position` is False, the chi-square distribution has 4 degrees of
        freedom, otherwise 2.
        Parameters
        ----------
        mean : ndarray
            Mean vector over the state distribution (8 dimensional).
        covariance : ndarray
            Covariance of the state distribution (8x8 dimensional).
        measurements : ndarray
            An Nx4 dimensional matrix of N measurements, each in
            format (x, y, a, h) where (x, y) is the bounding box center
            position, a the aspect ratio, and h the height.
        only_position : Optional[bool]
            If True, distance computation is done with respect to the bounding
            box center position only.
        Returns
        -------
        ndarray
            Returns an array of length N, where the i-th element contains the
            squared Mahalanobis distance between (mean, covariance) and
            `measurements[i]`.
        """
        mean, covariance = self.project(mean, covariance)
        if only_position:
            mean, covariance = (mean[:2], covariance[:2, :2])
            measurements = measurements[:, :2]
        d = measurements - mean
        if metric == 'gaussian':
            return np.sum(d * d, axis=1)
        elif metric == 'maha':
            cholesky_factor = np.linalg.cholesky(covariance)
            z = scipy.linalg.solve_triangular(cholesky_factor, d.T, lower=True, check_finite=False, overwrite_b=True)
            squared_maha = np.sum(z * z, axis=0)
            return squared_maha
        else:
            raise ValueError('invalid distance metric')

def __init__(self):
    ndim, dt = (4, 1.0)
    self._motion_mat = np.eye(2 * ndim, 2 * ndim)
    for i in range(ndim):
        self._motion_mat[i, ndim + i] = dt
    self._update_mat = np.eye(ndim, 2 * ndim)
    self._std_weight_position = 1.0 / 20
    self._std_weight_velocity = 1.0 / 160

def initiate(self, measurement):
    """Create track from unassociated measurement.

        Parameters
        ----------
        measurement : ndarray
            Bounding box coordinates (x, y, a, h) with center position (x, y),
            aspect ratio a, and height h.

        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector (8 dimensional) and covariance matrix (8x8
            dimensional) of the new track. Unobserved velocities are initialized
            to 0 mean.

        """
    mean_pos = measurement
    mean_vel = np.zeros_like(mean_pos)
    mean = np.r_[mean_pos, mean_vel]
    std = [2 * self._std_weight_position * measurement[3], 2 * self._std_weight_position * measurement[3], 0.01, 2 * self._std_weight_position * measurement[3], 10 * self._std_weight_velocity * measurement[3], 10 * self._std_weight_velocity * measurement[3], 1e-05, 10 * self._std_weight_velocity * measurement[3]]
    covariance = np.diag(np.square(std))
    return (mean, covariance)

def predict(self, mean, covariance):
    """Run Kalman filter prediction step.

        Parameters
        ----------
        mean : ndarray
            The 8 dimensional mean vector of the object state at the previous
            time step.
        covariance : ndarray
            The 8x8 dimensional covariance matrix of the object state at the
            previous time step.

        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector and covariance matrix of the predicted
            state. Unobserved velocities are initialized to 0 mean.

        """
    std_pos = [self._std_weight_position * mean[3], self._std_weight_position * mean[3], 0.01, self._std_weight_position * mean[3]]
    std_vel = [self._std_weight_velocity * mean[3], self._std_weight_velocity * mean[3], 1e-05, self._std_weight_velocity * mean[3]]
    motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))
    mean = np.dot(mean, self._motion_mat.T)
    covariance = np.linalg.multi_dot((self._motion_mat, covariance, self._motion_mat.T)) + motion_cov
    return (mean, covariance)

def project(self, mean, covariance):
    """Project state distribution to measurement space.

        Parameters
        ----------
        mean : ndarray
            The state's mean vector (8 dimensional array).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).

        Returns
        -------
        (ndarray, ndarray)
            Returns the projected mean and covariance matrix of the given state
            estimate.

        """
    std = [self._std_weight_position * mean[3], self._std_weight_position * mean[3], 0.1, self._std_weight_position * mean[3]]
    innovation_cov = np.diag(np.square(std))
    mean = np.dot(self._update_mat, mean)
    covariance = np.linalg.multi_dot((self._update_mat, covariance, self._update_mat.T))
    return (mean, covariance + innovation_cov)

def multi_predict(self, mean, covariance):
    """Run Kalman filter prediction step (Vectorized version).
        Parameters
        ----------
        mean : ndarray
            The Nx8 dimensional mean matrix of the object states at the previous
            time step.
        covariance : ndarray
            The Nx8x8 dimensional covariance matrics of the object states at the
            previous time step.
        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector and covariance matrix of the predicted
            state. Unobserved velocities are initialized to 0 mean.
        """
    std_pos = [self._std_weight_position * mean[:, 3], self._std_weight_position * mean[:, 3], 0.01 * np.ones_like(mean[:, 3]), self._std_weight_position * mean[:, 3]]
    std_vel = [self._std_weight_velocity * mean[:, 3], self._std_weight_velocity * mean[:, 3], 1e-05 * np.ones_like(mean[:, 3]), self._std_weight_velocity * mean[:, 3]]
    sqr = np.square(np.r_[std_pos, std_vel]).T
    motion_cov = []
    for i in range(len(mean)):
        motion_cov.append(np.diag(sqr[i]))
    motion_cov = np.asarray(motion_cov)
    mean = np.dot(mean, self._motion_mat.T)
    left = np.dot(self._motion_mat, covariance).transpose((1, 0, 2))
    covariance = np.dot(left, self._motion_mat.T) + motion_cov
    return (mean, covariance)

def update(self, mean, covariance, measurement):
    """Run Kalman filter correction step.

        Parameters
        ----------
        mean : ndarray
            The predicted state's mean vector (8 dimensional).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).
        measurement : ndarray
            The 4 dimensional measurement vector (x, y, a, h), where (x, y)
            is the center position, a the aspect ratio, and h the height of the
            bounding box.

        Returns
        -------
        (ndarray, ndarray)
            Returns the measurement-corrected state distribution.

        """
    projected_mean, projected_cov = self.project(mean, covariance)
    chol_factor, lower = scipy.linalg.cho_factor(projected_cov, lower=True, check_finite=False)
    kalman_gain = scipy.linalg.cho_solve((chol_factor, lower), np.dot(covariance, self._update_mat.T).T, check_finite=False).T
    innovation = measurement - projected_mean
    new_mean = mean + np.dot(innovation, kalman_gain.T)
    new_covariance = covariance - np.linalg.multi_dot((kalman_gain, projected_cov, kalman_gain.T))
    return (new_mean, new_covariance)

def gating_distance(self, mean, covariance, measurements, only_position=False, metric='maha'):
    """Compute gating distance between state distribution and measurements.
        A suitable distance threshold can be obtained from `chi2inv95`. If
        `only_position` is False, the chi-square distribution has 4 degrees of
        freedom, otherwise 2.
        Parameters
        ----------
        mean : ndarray
            Mean vector over the state distribution (8 dimensional).
        covariance : ndarray
            Covariance of the state distribution (8x8 dimensional).
        measurements : ndarray
            An Nx4 dimensional matrix of N measurements, each in
            format (x, y, a, h) where (x, y) is the bounding box center
            position, a the aspect ratio, and h the height.
        only_position : Optional[bool]
            If True, distance computation is done with respect to the bounding
            box center position only.
        Returns
        -------
        ndarray
            Returns an array of length N, where the i-th element contains the
            squared Mahalanobis distance between (mean, covariance) and
            `measurements[i]`.
        """
    mean, covariance = self.project(mean, covariance)
    if only_position:
        mean, covariance = (mean[:2], covariance[:2, :2])
        measurements = measurements[:, :2]
    d = measurements - mean
    if metric == 'gaussian':
        return np.sum(d * d, axis=1)
    elif metric == 'maha':
        cholesky_factor = np.linalg.cholesky(covariance)
        z = scipy.linalg.solve_triangular(cholesky_factor, d.T, lower=True, check_finite=False, overwrite_b=True)
        squared_maha = np.sum(z * z, axis=0)
        return squared_maha
    else:
        raise ValueError('invalid distance metric')

def embedding_distance(tracks, detections, metric='cosine'):
    """
    :param tracks: list[STrack]
    :param detections: list[BaseTrack]
    :param metric:
    :return: cost_matrix np.ndarray
    """
    cost_matrix = np.zeros((len(tracks), len(detections)), dtype=np.float32)
    if cost_matrix.size == 0:
        return cost_matrix
    det_features = np.asarray([track.curr_feat for track in detections], dtype=np.float32)
    track_features = np.asarray([track.smooth_feat for track in tracks], dtype=np.float32)
    cost_matrix = np.maximum(0.0, cdist(track_features, det_features, metric))
    return cost_matrix

def gate_cost_matrix(kf, cost_matrix, tracks, detections, only_position=False):
    if cost_matrix.size == 0:
        return cost_matrix
    gating_dim = 2 if only_position else 4
    gating_threshold = kalman_filter.chi2inv95[gating_dim]
    measurements = np.asarray([det.to_xyah() for det in detections])
    for row, track in enumerate(tracks):
        gating_distance = kf.gating_distance(track.mean, track.covariance, measurements, only_position)
        cost_matrix[row, gating_distance > gating_threshold] = np.inf
    return cost_matrix

def fuse_motion(kf, cost_matrix, tracks, detections, only_position=False, lambda_=0.98):
    if cost_matrix.size == 0:
        return cost_matrix
    gating_dim = 2 if only_position else 4
    gating_threshold = kalman_filter.chi2inv95[gating_dim]
    measurements = np.asarray([det.to_xyah() for det in detections])
    for row, track in enumerate(tracks):
        gating_distance = kf.gating_distance(track.mean, track.covariance, measurements, only_position, metric='maha')
        cost_matrix[row, gating_distance > gating_threshold] = np.inf
        cost_matrix[row] = lambda_ * cost_matrix[row] + (1 - lambda_) * gating_distance
    return cost_matrix

def fuse_iou(cost_matrix, tracks, detections):
    if cost_matrix.size == 0:
        return cost_matrix
    reid_sim = 1 - cost_matrix
    iou_dist = iou_distance(tracks, detections)
    iou_sim = 1 - iou_dist
    fuse_sim = reid_sim * (1 + iou_sim) / 2
    det_scores = np.array([det.score for det in detections])
    det_scores = np.expand_dims(det_scores, axis=0).repeat(cost_matrix.shape[0], axis=0)
    fuse_cost = 1 - fuse_sim
    return fuse_cost

def fuse_score(cost_matrix, detections):
    if cost_matrix.size == 0:
        return cost_matrix
    iou_sim = 1 - cost_matrix
    det_scores = np.array([det.score for det in detections])
    det_scores = np.expand_dims(det_scores, axis=0).repeat(cost_matrix.shape[0], axis=0)
    fuse_sim = iou_sim * det_scores
    fuse_cost = 1 - fuse_sim
    return fuse_cost

class KalmanFilter(object):
    """
    A simple Kalman filter for tracking bounding boxes in image space.

    The 8-dimensional state space

        x, y, w, h, vx, vy, vw, vh

    contains the bounding box center position (x, y), width w, height h,
    and their respective velocities.

    Object motion follows a constant velocity model. The bounding box location
    (x, y, w, h) is taken as direct observation of the state space (linear
    observation model).

    """

    def __init__(self):
        ndim, dt = (4, 1.0)
        self._motion_mat = np.eye(2 * ndim, 2 * ndim)
        for i in range(ndim):
            self._motion_mat[i, ndim + i] = dt
        self._update_mat = np.eye(ndim, 2 * ndim)
        self._std_weight_position = 1.0 / 20
        self._std_weight_velocity = 1.0 / 160

    def initiate(self, measurement):
        """Create track from unassociated measurement.

        Parameters
        ----------
        measurement : ndarray
            Bounding box coordinates (x, y, w, h) with center position (x, y),
            width w, and height h.

        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector (8 dimensional) and covariance matrix (8x8
            dimensional) of the new track. Unobserved velocities are initialized
            to 0 mean.

        """
        mean_pos = measurement
        mean_vel = np.zeros_like(mean_pos)
        mean = np.r_[mean_pos, mean_vel]
        std = [2 * self._std_weight_position * measurement[2], 2 * self._std_weight_position * measurement[3], 2 * self._std_weight_position * measurement[2], 2 * self._std_weight_position * measurement[3], 10 * self._std_weight_velocity * measurement[2], 10 * self._std_weight_velocity * measurement[3], 10 * self._std_weight_velocity * measurement[2], 10 * self._std_weight_velocity * measurement[3]]
        covariance = np.diag(np.square(std))
        return (mean, covariance)

    def predict(self, mean, covariance):
        """Run Kalman filter prediction step.

        Parameters
        ----------
        mean : ndarray
            The 8 dimensional mean vector of the object state at the previous
            time step.
        covariance : ndarray
            The 8x8 dimensional covariance matrix of the object state at the
            previous time step.

        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector and covariance matrix of the predicted
            state. Unobserved velocities are initialized to 0 mean.

        """
        std_pos = [self._std_weight_position * mean[2], self._std_weight_position * mean[3], self._std_weight_position * mean[2], self._std_weight_position * mean[3]]
        std_vel = [self._std_weight_velocity * mean[2], self._std_weight_velocity * mean[3], self._std_weight_velocity * mean[2], self._std_weight_velocity * mean[3]]
        motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))
        mean = np.dot(mean, self._motion_mat.T)
        covariance = np.linalg.multi_dot((self._motion_mat, covariance, self._motion_mat.T)) + motion_cov
        return (mean, covariance)

    def project(self, mean, covariance):
        """Project state distribution to measurement space.

        Parameters
        ----------
        mean : ndarray
            The state's mean vector (8 dimensional array).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).

        Returns
        -------
        (ndarray, ndarray)
            Returns the projected mean and covariance matrix of the given state
            estimate.

        """
        std = [self._std_weight_position * mean[2], self._std_weight_position * mean[3], self._std_weight_position * mean[2], self._std_weight_position * mean[3]]
        innovation_cov = np.diag(np.square(std))
        mean = np.dot(self._update_mat, mean)
        covariance = np.linalg.multi_dot((self._update_mat, covariance, self._update_mat.T))
        return (mean, covariance + innovation_cov)

    def multi_predict(self, mean, covariance):
        """Run Kalman filter prediction step (Vectorized version).
        Parameters
        ----------
        mean : ndarray
            The Nx8 dimensional mean matrix of the object states at the previous
            time step.
        covariance : ndarray
            The Nx8x8 dimensional covariance matrics of the object states at the
            previous time step.
        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector and covariance matrix of the predicted
            state. Unobserved velocities are initialized to 0 mean.
        """
        std_pos = [self._std_weight_position * mean[:, 2], self._std_weight_position * mean[:, 3], self._std_weight_position * mean[:, 2], self._std_weight_position * mean[:, 3]]
        std_vel = [self._std_weight_velocity * mean[:, 2], self._std_weight_velocity * mean[:, 3], self._std_weight_velocity * mean[:, 2], self._std_weight_velocity * mean[:, 3]]
        sqr = np.square(np.r_[std_pos, std_vel]).T
        motion_cov = []
        for i in range(len(mean)):
            motion_cov.append(np.diag(sqr[i]))
        motion_cov = np.asarray(motion_cov)
        mean = np.dot(mean, self._motion_mat.T)
        left = np.dot(self._motion_mat, covariance).transpose((1, 0, 2))
        covariance = np.dot(left, self._motion_mat.T) + motion_cov
        return (mean, covariance)

    def update(self, mean, covariance, measurement):
        """Run Kalman filter correction step.

        Parameters
        ----------
        mean : ndarray
            The predicted state's mean vector (8 dimensional).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).
        measurement : ndarray
            The 4 dimensional measurement vector (x, y, w, h), where (x, y)
            is the center position, w the width, and h the height of the
            bounding box.

        Returns
        -------
        (ndarray, ndarray)
            Returns the measurement-corrected state distribution.

        """
        projected_mean, projected_cov = self.project(mean, covariance)
        chol_factor, lower = scipy.linalg.cho_factor(projected_cov, lower=True, check_finite=False)
        kalman_gain = scipy.linalg.cho_solve((chol_factor, lower), np.dot(covariance, self._update_mat.T).T, check_finite=False).T
        innovation = measurement - projected_mean
        new_mean = mean + np.dot(innovation, kalman_gain.T)
        new_covariance = covariance - np.linalg.multi_dot((kalman_gain, projected_cov, kalman_gain.T))
        return (new_mean, new_covariance)

    def gating_distance(self, mean, covariance, measurements, only_position=False, metric='maha'):
        """Compute gating distance between state distribution and measurements.
        A suitable distance threshold can be obtained from `chi2inv95`. If
        `only_position` is False, the chi-square distribution has 4 degrees of
        freedom, otherwise 2.
        Parameters
        ----------
        mean : ndarray
            Mean vector over the state distribution (8 dimensional).
        covariance : ndarray
            Covariance of the state distribution (8x8 dimensional).
        measurements : ndarray
            An Nx4 dimensional matrix of N measurements, each in
            format (x, y, a, h) where (x, y) is the bounding box center
            position, a the aspect ratio, and h the height.
        only_position : Optional[bool]
            If True, distance computation is done with respect to the bounding
            box center position only.
        Returns
        -------
        ndarray
            Returns an array of length N, where the i-th element contains the
            squared Mahalanobis distance between (mean, covariance) and
            `measurements[i]`.
        """
        mean, covariance = self.project(mean, covariance)
        if only_position:
            mean, covariance = (mean[:2], covariance[:2, :2])
            measurements = measurements[:, :2]
        d = measurements - mean
        if metric == 'gaussian':
            return np.sum(d * d, axis=1)
        elif metric == 'maha':
            cholesky_factor = np.linalg.cholesky(covariance)
            z = scipy.linalg.solve_triangular(cholesky_factor, d.T, lower=True, check_finite=False, overwrite_b=True)
            squared_maha = np.sum(z * z, axis=0)
            return squared_maha
        else:
            raise ValueError('invalid distance metric')

def __init__(self):
    ndim, dt = (4, 1.0)
    self._motion_mat = np.eye(2 * ndim, 2 * ndim)
    for i in range(ndim):
        self._motion_mat[i, ndim + i] = dt
    self._update_mat = np.eye(ndim, 2 * ndim)
    self._std_weight_position = 1.0 / 20
    self._std_weight_velocity = 1.0 / 160

def initiate(self, measurement):
    """Create track from unassociated measurement.

        Parameters
        ----------
        measurement : ndarray
            Bounding box coordinates (x, y, w, h) with center position (x, y),
            width w, and height h.

        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector (8 dimensional) and covariance matrix (8x8
            dimensional) of the new track. Unobserved velocities are initialized
            to 0 mean.

        """
    mean_pos = measurement
    mean_vel = np.zeros_like(mean_pos)
    mean = np.r_[mean_pos, mean_vel]
    std = [2 * self._std_weight_position * measurement[2], 2 * self._std_weight_position * measurement[3], 2 * self._std_weight_position * measurement[2], 2 * self._std_weight_position * measurement[3], 10 * self._std_weight_velocity * measurement[2], 10 * self._std_weight_velocity * measurement[3], 10 * self._std_weight_velocity * measurement[2], 10 * self._std_weight_velocity * measurement[3]]
    covariance = np.diag(np.square(std))
    return (mean, covariance)

def predict(self, mean, covariance):
    """Run Kalman filter prediction step.

        Parameters
        ----------
        mean : ndarray
            The 8 dimensional mean vector of the object state at the previous
            time step.
        covariance : ndarray
            The 8x8 dimensional covariance matrix of the object state at the
            previous time step.

        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector and covariance matrix of the predicted
            state. Unobserved velocities are initialized to 0 mean.

        """
    std_pos = [self._std_weight_position * mean[2], self._std_weight_position * mean[3], self._std_weight_position * mean[2], self._std_weight_position * mean[3]]
    std_vel = [self._std_weight_velocity * mean[2], self._std_weight_velocity * mean[3], self._std_weight_velocity * mean[2], self._std_weight_velocity * mean[3]]
    motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))
    mean = np.dot(mean, self._motion_mat.T)
    covariance = np.linalg.multi_dot((self._motion_mat, covariance, self._motion_mat.T)) + motion_cov
    return (mean, covariance)

def project(self, mean, covariance):
    """Project state distribution to measurement space.

        Parameters
        ----------
        mean : ndarray
            The state's mean vector (8 dimensional array).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).

        Returns
        -------
        (ndarray, ndarray)
            Returns the projected mean and covariance matrix of the given state
            estimate.

        """
    std = [self._std_weight_position * mean[2], self._std_weight_position * mean[3], self._std_weight_position * mean[2], self._std_weight_position * mean[3]]
    innovation_cov = np.diag(np.square(std))
    mean = np.dot(self._update_mat, mean)
    covariance = np.linalg.multi_dot((self._update_mat, covariance, self._update_mat.T))
    return (mean, covariance + innovation_cov)

def multi_predict(self, mean, covariance):
    """Run Kalman filter prediction step (Vectorized version).
        Parameters
        ----------
        mean : ndarray
            The Nx8 dimensional mean matrix of the object states at the previous
            time step.
        covariance : ndarray
            The Nx8x8 dimensional covariance matrics of the object states at the
            previous time step.
        Returns
        -------
        (ndarray, ndarray)
            Returns the mean vector and covariance matrix of the predicted
            state. Unobserved velocities are initialized to 0 mean.
        """
    std_pos = [self._std_weight_position * mean[:, 2], self._std_weight_position * mean[:, 3], self._std_weight_position * mean[:, 2], self._std_weight_position * mean[:, 3]]
    std_vel = [self._std_weight_velocity * mean[:, 2], self._std_weight_velocity * mean[:, 3], self._std_weight_velocity * mean[:, 2], self._std_weight_velocity * mean[:, 3]]
    sqr = np.square(np.r_[std_pos, std_vel]).T
    motion_cov = []
    for i in range(len(mean)):
        motion_cov.append(np.diag(sqr[i]))
    motion_cov = np.asarray(motion_cov)
    mean = np.dot(mean, self._motion_mat.T)
    left = np.dot(self._motion_mat, covariance).transpose((1, 0, 2))
    covariance = np.dot(left, self._motion_mat.T) + motion_cov
    return (mean, covariance)

def update(self, mean, covariance, measurement):
    """Run Kalman filter correction step.

        Parameters
        ----------
        mean : ndarray
            The predicted state's mean vector (8 dimensional).
        covariance : ndarray
            The state's covariance matrix (8x8 dimensional).
        measurement : ndarray
            The 4 dimensional measurement vector (x, y, w, h), where (x, y)
            is the center position, w the width, and h the height of the
            bounding box.

        Returns
        -------
        (ndarray, ndarray)
            Returns the measurement-corrected state distribution.

        """
    projected_mean, projected_cov = self.project(mean, covariance)
    chol_factor, lower = scipy.linalg.cho_factor(projected_cov, lower=True, check_finite=False)
    kalman_gain = scipy.linalg.cho_solve((chol_factor, lower), np.dot(covariance, self._update_mat.T).T, check_finite=False).T
    innovation = measurement - projected_mean
    new_mean = mean + np.dot(innovation, kalman_gain.T)
    new_covariance = covariance - np.linalg.multi_dot((kalman_gain, projected_cov, kalman_gain.T))
    return (new_mean, new_covariance)

def gating_distance(self, mean, covariance, measurements, only_position=False, metric='maha'):
    """Compute gating distance between state distribution and measurements.
        A suitable distance threshold can be obtained from `chi2inv95`. If
        `only_position` is False, the chi-square distribution has 4 degrees of
        freedom, otherwise 2.
        Parameters
        ----------
        mean : ndarray
            Mean vector over the state distribution (8 dimensional).
        covariance : ndarray
            Covariance of the state distribution (8x8 dimensional).
        measurements : ndarray
            An Nx4 dimensional matrix of N measurements, each in
            format (x, y, a, h) where (x, y) is the bounding box center
            position, a the aspect ratio, and h the height.
        only_position : Optional[bool]
            If True, distance computation is done with respect to the bounding
            box center position only.
        Returns
        -------
        ndarray
            Returns an array of length N, where the i-th element contains the
            squared Mahalanobis distance between (mean, covariance) and
            `measurements[i]`.
        """
    mean, covariance = self.project(mean, covariance)
    if only_position:
        mean, covariance = (mean[:2], covariance[:2, :2])
        measurements = measurements[:, :2]
    d = measurements - mean
    if metric == 'gaussian':
        return np.sum(d * d, axis=1)
    elif metric == 'maha':
        cholesky_factor = np.linalg.cholesky(covariance)
        z = scipy.linalg.solve_triangular(cholesky_factor, d.T, lower=True, check_finite=False, overwrite_b=True)
        squared_maha = np.sum(z * z, axis=0)
        return squared_maha
    else:
        raise ValueError('invalid distance metric')

def embedding_distance(tracks, detections, metric='cosine'):
    """
    :param tracks: list[STrack]
    :param detections: list[BaseTrack]
    :param metric:
    :return: cost_matrix np.ndarray
    """
    cost_matrix = np.zeros((len(tracks), len(detections)), dtype=np.float32)
    if cost_matrix.size == 0:
        return cost_matrix
    det_features = np.asarray([track.curr_feat for track in detections], dtype=np.float32)
    track_features = np.asarray([track.smooth_feat for track in tracks], dtype=np.float32)
    cost_matrix = np.maximum(0.0, cdist(track_features, det_features, metric))
    return cost_matrix

def gate_cost_matrix(kf, cost_matrix, tracks, detections, only_position=False):
    if cost_matrix.size == 0:
        return cost_matrix
    gating_dim = 2 if only_position else 4
    gating_threshold = kalman_filter.chi2inv95[gating_dim]
    measurements = np.asarray([det.to_xywh() for det in detections])
    for row, track in enumerate(tracks):
        gating_distance = kf.gating_distance(track.mean, track.covariance, measurements, only_position)
        cost_matrix[row, gating_distance > gating_threshold] = np.inf
    return cost_matrix

def fuse_motion(kf, cost_matrix, tracks, detections, only_position=False, lambda_=0.98):
    if cost_matrix.size == 0:
        return cost_matrix
    gating_dim = 2 if only_position else 4
    gating_threshold = kalman_filter.chi2inv95[gating_dim]
    measurements = np.asarray([det.to_xywh() for det in detections])
    for row, track in enumerate(tracks):
        gating_distance = kf.gating_distance(track.mean, track.covariance, measurements, only_position, metric='maha')
        cost_matrix[row, gating_distance > gating_threshold] = np.inf
        cost_matrix[row] = lambda_ * cost_matrix[row] + (1 - lambda_) * gating_distance
    return cost_matrix

def fuse_iou(cost_matrix, tracks, detections):
    if cost_matrix.size == 0:
        return cost_matrix
    reid_sim = 1 - cost_matrix
    iou_dist = iou_distance(tracks, detections)
    iou_sim = 1 - iou_dist
    fuse_sim = reid_sim * (1 + iou_sim) / 2
    det_scores = np.array([det.score for det in detections])
    det_scores = np.expand_dims(det_scores, axis=0).repeat(cost_matrix.shape[0], axis=0)
    fuse_cost = 1 - fuse_sim
    return fuse_cost

def fuse_score(cost_matrix, detections):
    if cost_matrix.size == 0:
        return cost_matrix
    iou_sim = 1 - cost_matrix
    det_scores = np.array([det.score for det in detections])
    det_scores = np.expand_dims(det_scores, axis=0).repeat(cost_matrix.shape[0], axis=0)
    fuse_sim = iou_sim * det_scores
    fuse_cost = 1 - fuse_sim
    return fuse_cost

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

def update_features(self, feat):
    feat /= np.linalg.norm(feat)
    self.curr_feat = feat
    if self.smooth_feat is None:
        self.smooth_feat = feat
    else:
        self.smooth_feat = self.alpha * self.smooth_feat + (1 - self.alpha) * feat
    self.features.append(feat)
    self.smooth_feat /= np.linalg.norm(self.smooth_feat)

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

class BoTSORT(object):

    def __init__(self, model_weights, device, fp16, track_high_thresh: float=0.45, new_track_thresh: float=0.6, track_buffer: int=30, match_thresh: float=0.8, proximity_thresh: float=0.5, appearance_thresh: float=0.25, cmc_method: str='sparseOptFlow', frame_rate=30, lambda_=0.985):
        self.tracked_stracks = []
        self.lost_stracks = []
        self.removed_stracks = []
        BaseTrack.clear_count()
        self.frame_id = 0
        self.lambda_ = lambda_
        self.track_high_thresh = track_high_thresh
        self.new_track_thresh = new_track_thresh
        self.buffer_size = int(frame_rate / 30.0 * track_buffer)
        self.max_time_lost = self.buffer_size
        self.kalman_filter = KalmanFilter()
        self.proximity_thresh = proximity_thresh
        self.appearance_thresh = appearance_thresh
        self.match_thresh = match_thresh
        self.model = ReIDDetectMultiBackend(weights=model_weights, device=device, fp16=fp16)
        self.gmc = GMC(method=cmc_method, verbose=[None, False])

    def update(self, output_results, img):
        self.frame_id += 1
        activated_starcks = []
        refind_stracks = []
        lost_stracks = []
        removed_stracks = []
        xyxys = output_results[:, 0:4]
        xywh = xyxy2xywh(xyxys.numpy())
        confs = output_results[:, 4]
        clss = output_results[:, 5]
        classes = clss.numpy()
        xyxys = xyxys.numpy()
        confs = confs.numpy()
        remain_inds = confs > self.track_high_thresh
        inds_low = confs > 0.1
        inds_high = confs < self.track_high_thresh
        inds_second = np.logical_and(inds_low, inds_high)
        dets_second = xywh[inds_second]
        dets = xywh[remain_inds]
        scores_keep = confs[remain_inds]
        scores_second = confs[inds_second]
        classes_keep = classes[remain_inds]
        clss_second = classes[inds_second]
        self.height, self.width = img.shape[:2]
        'Extract embeddings '
        features_keep = self._get_features(dets, img)
        if len(dets) > 0:
            'Detections'
            detections = [STrack(xyxy, s, c, f.cpu().numpy()) for xyxy, s, c, f in zip(dets, scores_keep, classes_keep, features_keep)]
        else:
            detections = []
        ' Add newly detected tracklets to tracked_stracks'
        unconfirmed = []
        tracked_stracks = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)
        ' Step 2: First association, with high score detection boxes'
        strack_pool = joint_stracks(tracked_stracks, self.lost_stracks)
        STrack.multi_predict(strack_pool)
        warp = self.gmc.apply(img, dets)
        STrack.multi_gmc(strack_pool, warp)
        STrack.multi_gmc(unconfirmed, warp)
        raw_emb_dists = matching.embedding_distance(strack_pool, detections)
        dists = matching.fuse_motion(self.kalman_filter, raw_emb_dists, strack_pool, detections, only_position=False, lambda_=self.lambda_)
        matches, u_track, u_detection = matching.linear_assignment(dists, thresh=self.match_thresh)
        for itracked, idet in matches:
            track = strack_pool[itracked]
            det = detections[idet]
            if track.state == TrackState.Tracked:
                track.update(detections[idet], self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)
        ' Step 3: Second association, with low score detection boxes'
        if len(dets_second) > 0:
            'Detections'
            detections_second = [STrack(STrack.tlbr_to_tlwh(tlbr), s, c) for tlbr, s, c in zip(dets_second, scores_second, clss_second)]
        else:
            detections_second = []
        r_tracked_stracks = [strack_pool[i] for i in u_track if strack_pool[i].state == TrackState.Tracked]
        dists = matching.iou_distance(r_tracked_stracks, detections_second)
        matches, u_track, u_detection_second = matching.linear_assignment(dists, thresh=0.5)
        for itracked, idet in matches:
            track = r_tracked_stracks[itracked]
            det = detections_second[idet]
            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
                activated_starcks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)
        for it in u_track:
            track = r_tracked_stracks[it]
            if not track.state == TrackState.Lost:
                track.mark_lost()
                lost_stracks.append(track)
        'Deal with unconfirmed tracks, usually tracks with only one beginning frame'
        detections = [detections[i] for i in u_detection]
        ious_dists = matching.iou_distance(unconfirmed, detections)
        ious_dists_mask = ious_dists > self.proximity_thresh
        ious_dists = matching.fuse_score(ious_dists, detections)
        emb_dists = matching.embedding_distance(unconfirmed, detections) / 2.0
        raw_emb_dists = emb_dists.copy()
        emb_dists[emb_dists > self.appearance_thresh] = 1.0
        emb_dists[ious_dists_mask] = 1.0
        dists = np.minimum(ious_dists, emb_dists)
        matches, u_unconfirmed, u_detection = matching.linear_assignment(dists, thresh=0.7)
        for itracked, idet in matches:
            unconfirmed[itracked].update(detections[idet], self.frame_id)
            activated_starcks.append(unconfirmed[itracked])
        for it in u_unconfirmed:
            track = unconfirmed[it]
            track.mark_removed()
            removed_stracks.append(track)
        ' Step 4: Init new stracks'
        for inew in u_detection:
            track = detections[inew]
            if track.score < self.new_track_thresh:
                continue
            track.activate(self.kalman_filter, self.frame_id)
            activated_starcks.append(track)
        ' Step 5: Update state'
        for track in self.lost_stracks:
            if self.frame_id - track.end_frame > self.max_time_lost:
                track.mark_removed()
                removed_stracks.append(track)
        ' Merge '
        self.tracked_stracks = [t for t in self.tracked_stracks if t.state == TrackState.Tracked]
        self.tracked_stracks = joint_stracks(self.tracked_stracks, activated_starcks)
        self.tracked_stracks = joint_stracks(self.tracked_stracks, refind_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.tracked_stracks)
        self.lost_stracks.extend(lost_stracks)
        self.lost_stracks = sub_stracks(self.lost_stracks, self.removed_stracks)
        self.removed_stracks.extend(removed_stracks)
        self.tracked_stracks, self.lost_stracks = remove_duplicate_stracks(self.tracked_stracks, self.lost_stracks)
        output_stracks = [track for track in self.tracked_stracks if track.is_activated]
        outputs = []
        for t in output_stracks:
            output = []
            tlwh = t.tlwh
            tid = t.track_id
            tlwh = np.expand_dims(tlwh, axis=0)
            xyxy = xywh2xyxy(tlwh)
            xyxy = np.squeeze(xyxy, axis=0)
            output.extend(xyxy)
            output.append(tid)
            output.append(t.cls)
            output.append(t.score)
            outputs.append(output)
        return outputs

    def _xywh_to_xyxy(self, bbox_xywh):
        x, y, w, h = bbox_xywh
        x1 = max(int(x - w / 2), 0)
        x2 = min(int(x + w / 2), self.width - 1)
        y1 = max(int(y - h / 2), 0)
        y2 = min(int(y + h / 2), self.height - 1)
        return (x1, y1, x2, y2)

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

def update(self, output_results, img):
    self.frame_id += 1
    activated_starcks = []
    refind_stracks = []
    lost_stracks = []
    removed_stracks = []
    xyxys = output_results[:, 0:4]
    xywh = xyxy2xywh(xyxys.numpy())
    confs = output_results[:, 4]
    clss = output_results[:, 5]
    classes = clss.numpy()
    xyxys = xyxys.numpy()
    confs = confs.numpy()
    remain_inds = confs > self.track_high_thresh
    inds_low = confs > 0.1
    inds_high = confs < self.track_high_thresh
    inds_second = np.logical_and(inds_low, inds_high)
    dets_second = xywh[inds_second]
    dets = xywh[remain_inds]
    scores_keep = confs[remain_inds]
    scores_second = confs[inds_second]
    classes_keep = classes[remain_inds]
    clss_second = classes[inds_second]
    self.height, self.width = img.shape[:2]
    'Extract embeddings '
    features_keep = self._get_features(dets, img)
    if len(dets) > 0:
        'Detections'
        detections = [STrack(xyxy, s, c, f.cpu().numpy()) for xyxy, s, c, f in zip(dets, scores_keep, classes_keep, features_keep)]
    else:
        detections = []
    ' Add newly detected tracklets to tracked_stracks'
    unconfirmed = []
    tracked_stracks = []
    for track in self.tracked_stracks:
        if not track.is_activated:
            unconfirmed.append(track)
        else:
            tracked_stracks.append(track)
    ' Step 2: First association, with high score detection boxes'
    strack_pool = joint_stracks(tracked_stracks, self.lost_stracks)
    STrack.multi_predict(strack_pool)
    warp = self.gmc.apply(img, dets)
    STrack.multi_gmc(strack_pool, warp)
    STrack.multi_gmc(unconfirmed, warp)
    raw_emb_dists = matching.embedding_distance(strack_pool, detections)
    dists = matching.fuse_motion(self.kalman_filter, raw_emb_dists, strack_pool, detections, only_position=False, lambda_=self.lambda_)
    matches, u_track, u_detection = matching.linear_assignment(dists, thresh=self.match_thresh)
    for itracked, idet in matches:
        track = strack_pool[itracked]
        det = detections[idet]
        if track.state == TrackState.Tracked:
            track.update(detections[idet], self.frame_id)
            activated_starcks.append(track)
        else:
            track.re_activate(det, self.frame_id, new_id=False)
            refind_stracks.append(track)
    ' Step 3: Second association, with low score detection boxes'
    if len(dets_second) > 0:
        'Detections'
        detections_second = [STrack(STrack.tlbr_to_tlwh(tlbr), s, c) for tlbr, s, c in zip(dets_second, scores_second, clss_second)]
    else:
        detections_second = []
    r_tracked_stracks = [strack_pool[i] for i in u_track if strack_pool[i].state == TrackState.Tracked]
    dists = matching.iou_distance(r_tracked_stracks, detections_second)
    matches, u_track, u_detection_second = matching.linear_assignment(dists, thresh=0.5)
    for itracked, idet in matches:
        track = r_tracked_stracks[itracked]
        det = detections_second[idet]
        if track.state == TrackState.Tracked:
            track.update(det, self.frame_id)
            activated_starcks.append(track)
        else:
            track.re_activate(det, self.frame_id, new_id=False)
            refind_stracks.append(track)
    for it in u_track:
        track = r_tracked_stracks[it]
        if not track.state == TrackState.Lost:
            track.mark_lost()
            lost_stracks.append(track)
    'Deal with unconfirmed tracks, usually tracks with only one beginning frame'
    detections = [detections[i] for i in u_detection]
    ious_dists = matching.iou_distance(unconfirmed, detections)
    ious_dists_mask = ious_dists > self.proximity_thresh
    ious_dists = matching.fuse_score(ious_dists, detections)
    emb_dists = matching.embedding_distance(unconfirmed, detections) / 2.0
    raw_emb_dists = emb_dists.copy()
    emb_dists[emb_dists > self.appearance_thresh] = 1.0
    emb_dists[ious_dists_mask] = 1.0
    dists = np.minimum(ious_dists, emb_dists)
    matches, u_unconfirmed, u_detection = matching.linear_assignment(dists, thresh=0.7)
    for itracked, idet in matches:
        unconfirmed[itracked].update(detections[idet], self.frame_id)
        activated_starcks.append(unconfirmed[itracked])
    for it in u_unconfirmed:
        track = unconfirmed[it]
        track.mark_removed()
        removed_stracks.append(track)
    ' Step 4: Init new stracks'
    for inew in u_detection:
        track = detections[inew]
        if track.score < self.new_track_thresh:
            continue
        track.activate(self.kalman_filter, self.frame_id)
        activated_starcks.append(track)
    ' Step 5: Update state'
    for track in self.lost_stracks:
        if self.frame_id - track.end_frame > self.max_time_lost:
            track.mark_removed()
            removed_stracks.append(track)
    ' Merge '
    self.tracked_stracks = [t for t in self.tracked_stracks if t.state == TrackState.Tracked]
    self.tracked_stracks = joint_stracks(self.tracked_stracks, activated_starcks)
    self.tracked_stracks = joint_stracks(self.tracked_stracks, refind_stracks)
    self.lost_stracks = sub_stracks(self.lost_stracks, self.tracked_stracks)
    self.lost_stracks.extend(lost_stracks)
    self.lost_stracks = sub_stracks(self.lost_stracks, self.removed_stracks)
    self.removed_stracks.extend(removed_stracks)
    self.tracked_stracks, self.lost_stracks = remove_duplicate_stracks(self.tracked_stracks, self.lost_stracks)
    output_stracks = [track for track in self.tracked_stracks if track.is_activated]
    outputs = []
    for t in output_stracks:
        output = []
        tlwh = t.tlwh
        tid = t.track_id
        tlwh = np.expand_dims(tlwh, axis=0)
        xyxy = xywh2xyxy(tlwh)
        xyxy = np.squeeze(xyxy, axis=0)
        output.extend(xyxy)
        output.append(tid)
        output.append(t.cls)
        output.append(t.score)
        outputs.append(output)
    return outputs

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

class GMC:

    def __init__(self, method='sparseOptFlow', downscale=2, verbose=None):
        super(GMC, self).__init__()
        self.method = method
        self.downscale = max(1, int(downscale))
        if self.method == 'orb':
            self.detector = cv2.FastFeatureDetector_create(20)
            self.extractor = cv2.ORB_create()
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        elif self.method == 'sift':
            self.detector = cv2.SIFT_create(nOctaveLayers=3, contrastThreshold=0.02, edgeThreshold=20)
            self.extractor = cv2.SIFT_create(nOctaveLayers=3, contrastThreshold=0.02, edgeThreshold=20)
            self.matcher = cv2.BFMatcher(cv2.NORM_L2)
        elif self.method == 'ecc':
            number_of_iterations = 5000
            termination_eps = 1e-06
            self.warp_mode = cv2.MOTION_EUCLIDEAN
            self.criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, number_of_iterations, termination_eps)
        elif self.method == 'sparseOptFlow':
            self.feature_params = dict(maxCorners=1000, qualityLevel=0.01, minDistance=1, blockSize=3, useHarrisDetector=False, k=0.04)
        elif self.method == 'file' or self.method == 'files':
            seqName = verbose[0]
            ablation = verbose[1]
            if ablation:
                filePath = 'tracker/GMC_files/MOT17_ablation'
            else:
                filePath = 'tracker/GMC_files/MOTChallenge'
            if '-FRCNN' in seqName:
                seqName = seqName[:-6]
            elif '-DPM' in seqName:
                seqName = seqName[:-4]
            elif '-SDP' in seqName:
                seqName = seqName[:-4]
            self.gmcFile = open(filePath + '/GMC-' + seqName + '.txt', 'r')
            if self.gmcFile is None:
                raise ValueError('Error: Unable to open GMC file in directory:' + filePath)
        elif self.method == 'none' or self.method == 'None':
            self.method = 'none'
        else:
            raise ValueError('Error: Unknown CMC method:' + method)
        self.prevFrame = None
        self.prevKeyPoints = None
        self.prevDescriptors = None
        self.initializedFirstFrame = False

    def apply(self, raw_frame, detections=None):
        if self.method == 'orb' or self.method == 'sift':
            return self.applyFeaures(raw_frame, detections)
        elif self.method == 'ecc':
            return self.applyEcc(raw_frame, detections)
        elif self.method == 'sparseOptFlow':
            return self.applySparseOptFlow(raw_frame, detections)
        elif self.method == 'file':
            return self.applyFile(raw_frame, detections)
        elif self.method == 'none':
            return np.eye(2, 3)
        else:
            return np.eye(2, 3)

    def applyEcc(self, raw_frame, detections=None):
        height, width, _ = raw_frame.shape
        frame = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY)
        H = np.eye(2, 3, dtype=np.float32)
        if self.downscale > 1.0:
            frame = cv2.GaussianBlur(frame, (3, 3), 1.5)
            frame = cv2.resize(frame, (width // self.downscale, height // self.downscale))
            width = width // self.downscale
            height = height // self.downscale
        if not self.initializedFirstFrame:
            self.prevFrame = frame.copy()
            self.initializedFirstFrame = True
            return H
        try:
            cc, H = cv2.findTransformECC(self.prevFrame, frame, H, self.warp_mode, self.criteria, None, 1)
        except:
            print('Warning: find transform failed. Set warp as identity')
        return H

    def applyFeaures(self, raw_frame, detections=None):
        height, width, _ = raw_frame.shape
        frame = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY)
        H = np.eye(2, 3)
        if self.downscale > 1.0:
            frame = cv2.resize(frame, (width // self.downscale, height // self.downscale))
            width = width // self.downscale
            height = height // self.downscale
        mask = np.zeros_like(frame)
        mask[int(0.02 * height):int(0.98 * height), int(0.02 * width):int(0.98 * width)] = 255
        if detections is not None:
            for det in detections:
                tlbr = (det[:4] / self.downscale).astype(np.int_)
                mask[tlbr[1]:tlbr[3], tlbr[0]:tlbr[2]] = 0
        keypoints = self.detector.detect(frame, mask)
        keypoints, descriptors = self.extractor.compute(frame, keypoints)
        if not self.initializedFirstFrame:
            self.prevFrame = frame.copy()
            self.prevKeyPoints = copy.copy(keypoints)
            self.prevDescriptors = copy.copy(descriptors)
            self.initializedFirstFrame = True
            return H
        knnMatches = self.matcher.knnMatch(self.prevDescriptors, descriptors, 2)
        matches = []
        spatialDistances = []
        maxSpatialDistance = 0.25 * np.array([width, height])
        if len(knnMatches) == 0:
            self.prevFrame = frame.copy()
            self.prevKeyPoints = copy.copy(keypoints)
            self.prevDescriptors = copy.copy(descriptors)
            return H
        for m, n in knnMatches:
            if m.distance < 0.9 * n.distance:
                prevKeyPointLocation = self.prevKeyPoints[m.queryIdx].pt
                currKeyPointLocation = keypoints[m.trainIdx].pt
                spatialDistance = (prevKeyPointLocation[0] - currKeyPointLocation[0], prevKeyPointLocation[1] - currKeyPointLocation[1])
                if np.abs(spatialDistance[0]) < maxSpatialDistance[0] and np.abs(spatialDistance[1]) < maxSpatialDistance[1]:
                    spatialDistances.append(spatialDistance)
                    matches.append(m)
        meanSpatialDistances = np.mean(spatialDistances, 0)
        stdSpatialDistances = np.std(spatialDistances, 0)
        inliesrs = spatialDistances - meanSpatialDistances < 2.5 * stdSpatialDistances
        goodMatches = []
        prevPoints = []
        currPoints = []
        for i in range(len(matches)):
            if inliesrs[i, 0] and inliesrs[i, 1]:
                goodMatches.append(matches[i])
                prevPoints.append(self.prevKeyPoints[matches[i].queryIdx].pt)
                currPoints.append(keypoints[matches[i].trainIdx].pt)
        prevPoints = np.array(prevPoints)
        currPoints = np.array(currPoints)
        if 0:
            matches_img = np.hstack((self.prevFrame, frame))
            matches_img = cv2.cvtColor(matches_img, cv2.COLOR_GRAY2BGR)
            W = np.size(self.prevFrame, 1)
            for m in goodMatches:
                prev_pt = np.array(self.prevKeyPoints[m.queryIdx].pt, dtype=np.int_)
                curr_pt = np.array(keypoints[m.trainIdx].pt, dtype=np.int_)
                curr_pt[0] += W
                color = np.random.randint(0, 255, (3,))
                color = (int(color[0]), int(color[1]), int(color[2]))
                matches_img = cv2.line(matches_img, prev_pt, curr_pt, tuple(color), 1, cv2.LINE_AA)
                matches_img = cv2.circle(matches_img, prev_pt, 2, tuple(color), -1)
                matches_img = cv2.circle(matches_img, curr_pt, 2, tuple(color), -1)
            plt.figure()
            plt.imshow(matches_img)
            plt.show()
        if np.size(prevPoints, 0) > 4 and np.size(prevPoints, 0) == np.size(prevPoints, 0):
            H, inliesrs = cv2.estimateAffinePartial2D(prevPoints, currPoints, cv2.RANSAC)
            if self.downscale > 1.0:
                H[0, 2] *= self.downscale
                H[1, 2] *= self.downscale
        else:
            print('Warning: not enough matching points')
        self.prevFrame = frame.copy()
        self.prevKeyPoints = copy.copy(keypoints)
        self.prevDescriptors = copy.copy(descriptors)
        return H

    def applySparseOptFlow(self, raw_frame, detections=None):
        t0 = time.time()
        height, width, _ = raw_frame.shape
        frame = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY)
        H = np.eye(2, 3)
        if self.downscale > 1.0:
            frame = cv2.resize(frame, (width // self.downscale, height // self.downscale))
        keypoints = cv2.goodFeaturesToTrack(frame, mask=None, **self.feature_params)
        if not self.initializedFirstFrame:
            self.prevFrame = frame.copy()
            self.prevKeyPoints = copy.copy(keypoints)
            self.initializedFirstFrame = True
            return H
        matchedKeypoints, status, err = cv2.calcOpticalFlowPyrLK(self.prevFrame, frame, self.prevKeyPoints, None)
        prevPoints = []
        currPoints = []
        for i in range(len(status)):
            if status[i]:
                prevPoints.append(self.prevKeyPoints[i])
                currPoints.append(matchedKeypoints[i])
        prevPoints = np.array(prevPoints)
        currPoints = np.array(currPoints)
        if np.size(prevPoints, 0) > 4 and np.size(prevPoints, 0) == np.size(prevPoints, 0):
            H, inliesrs = cv2.estimateAffinePartial2D(prevPoints, currPoints, cv2.RANSAC)
            if self.downscale > 1.0:
                H[0, 2] *= self.downscale
                H[1, 2] *= self.downscale
        else:
            print('Warning: not enough matching points')
        self.prevFrame = frame.copy()
        self.prevKeyPoints = copy.copy(keypoints)
        t1 = time.time()
        return H

    def applyFile(self, raw_frame, detections=None):
        line = self.gmcFile.readline()
        tokens = line.split('\t')
        H = np.eye(2, 3, dtype=np.float_)
        H[0, 0] = float(tokens[1])
        H[0, 1] = float(tokens[2])
        H[0, 2] = float(tokens[3])
        H[1, 0] = float(tokens[4])
        H[1, 1] = float(tokens[5])
        H[1, 2] = float(tokens[6])
        return H

def apply(self, raw_frame, detections=None):
    if self.method == 'orb' or self.method == 'sift':
        return self.applyFeaures(raw_frame, detections)
    elif self.method == 'ecc':
        return self.applyEcc(raw_frame, detections)
    elif self.method == 'sparseOptFlow':
        return self.applySparseOptFlow(raw_frame, detections)
    elif self.method == 'file':
        return self.applyFile(raw_frame, detections)
    elif self.method == 'none':
        return np.eye(2, 3)
    else:
        return np.eye(2, 3)

def applyEcc(self, raw_frame, detections=None):
    height, width, _ = raw_frame.shape
    frame = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY)
    H = np.eye(2, 3, dtype=np.float32)
    if self.downscale > 1.0:
        frame = cv2.GaussianBlur(frame, (3, 3), 1.5)
        frame = cv2.resize(frame, (width // self.downscale, height // self.downscale))
        width = width // self.downscale
        height = height // self.downscale
    if not self.initializedFirstFrame:
        self.prevFrame = frame.copy()
        self.initializedFirstFrame = True
        return H
    try:
        cc, H = cv2.findTransformECC(self.prevFrame, frame, H, self.warp_mode, self.criteria, None, 1)
    except:
        print('Warning: find transform failed. Set warp as identity')
    return H

def applySparseOptFlow(self, raw_frame, detections=None):
    t0 = time.time()
    height, width, _ = raw_frame.shape
    frame = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY)
    H = np.eye(2, 3)
    if self.downscale > 1.0:
        frame = cv2.resize(frame, (width // self.downscale, height // self.downscale))
    keypoints = cv2.goodFeaturesToTrack(frame, mask=None, **self.feature_params)
    if not self.initializedFirstFrame:
        self.prevFrame = frame.copy()
        self.prevKeyPoints = copy.copy(keypoints)
        self.initializedFirstFrame = True
        return H
    matchedKeypoints, status, err = cv2.calcOpticalFlowPyrLK(self.prevFrame, frame, self.prevKeyPoints, None)
    prevPoints = []
    currPoints = []
    for i in range(len(status)):
        if status[i]:
            prevPoints.append(self.prevKeyPoints[i])
            currPoints.append(matchedKeypoints[i])
    prevPoints = np.array(prevPoints)
    currPoints = np.array(currPoints)
    if np.size(prevPoints, 0) > 4 and np.size(prevPoints, 0) == np.size(prevPoints, 0):
        H, inliesrs = cv2.estimateAffinePartial2D(prevPoints, currPoints, cv2.RANSAC)
        if self.downscale > 1.0:
            H[0, 2] *= self.downscale
            H[1, 2] *= self.downscale
    else:
        print('Warning: not enough matching points')
    self.prevFrame = frame.copy()
    self.prevKeyPoints = copy.copy(keypoints)
    t1 = time.time()
    return H

