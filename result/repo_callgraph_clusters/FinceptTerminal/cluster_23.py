# Cluster 23

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

class MaritimeMapWindow(QMainWindow):
    """Maritime Map Window with drag and resize"""

    def __init__(self):
        super().__init__()
        self.markers_file = 'maritime_markers.json'
        self.commands_file = 'map_commands.json'
        self.status_file = 'map_status.json'
        self.markers_data = self.load_markers()
        self.existing_markers = set()
        self.selected_marker_type = 'Ship'
        self.last_modified = 0
        for marker in self.markers_data:
            key = f'{marker['lat']:.6f}_{marker['lng']:.6f}'
            self.existing_markers.add(key)
        logger.info('Maritime map initialized')
        self.init_ui()
        self.create_map()
        self.start_file_watcher()

    def init_ui(self):
        """Initialize UI with drag bar and resize"""
        self.setWindowTitle('FINCEPT MARITIME MAP')
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.drag_bar = DragBar(self)
        main_layout.addWidget(self.drag_bar)
        self.web_view = QWebEngineView()
        main_layout.addWidget(self.web_view)
        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet('background: #ff8c00; width: 16px; height: 16px;')
        grip_layout = QHBoxLayout()
        grip_layout.addStretch()
        grip_layout.addWidget(self.size_grip)
        grip_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(grip_layout)
        self.setStyleSheet('\n            QMainWindow { \n                background-color: #000000; \n                border: 2px solid #ff8c00; \n            }\n        ')
        logger.info('UI initialized with drag and resize')

    @monitor_performance
    def create_map(self):
        """Create enhanced Leaflet map with India trade routes"""
        with operation('create_map'):
            try:
                markers_json = json.dumps(self.markers_data)
                html_content = f"""\n<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="utf-8" />\n    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />\n    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css" />\n    <style>\n        body {{ margin: 0; padding: 0; background: #000; }}\n        #map {{ height: 100vh; width: 100vw; }}\n        .ocean-route {{ stroke: #00bfff; stroke-width: 3; stroke-opacity: 0.8; stroke-dasharray: 8,4; }}\n        .route-animation {{ animation: routeFlow 3s linear infinite; }}\n        @keyframes routeFlow {{ 0% {{ stroke-dashoffset: 0; }} 100% {{ stroke-dashoffset: -24; }} }}\n        .ship-marker {{ animation: shipBob 2s ease-in-out infinite; z-index: 1000 !important; }}\n        @keyframes shipBob {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-3px); }} }}\n        .custom-marker {{ z-index: 1000 !important; }}\n        .leaflet-marker-icon {{ z-index: 1000 !important; }}\n    </style>\n</head>\n<body>\n    <div id="map"></div>\n    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>\n    <script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js"></script>\n    <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>\n    <script>\n        var map = L.map('map').setView([20.0, 75.0], 4);\n        \n        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{\n            attribution: 'FINCEPT MARITIME'\n        }}).addTo(map);\n\n        var markerCluster = L.markerClusterGroup();\n        map.addLayer(markerCluster);\n        var markers = [];\n        var markerObjects = [];\n        var heatmapData = [];\n        var heatLayer = null;\n        var routesLayer = null;\n        var liveShipsLayer = null;\n        var deleteMode = false;\n\n        var markersData = {markers_json};\n\n        function createCustomIcon(type, size = 24) {{\n            var icons = {{\n                'Ship': {{ symbol: '🚢', color: '#1e90ff' }},\n                'Port': {{ symbol: '⚓', color: '#8b4513' }},\n                'Industry': {{ symbol: '🏭', color: '#ff4500' }},\n                'Bank': {{ symbol: '🏦', color: '#ffd700' }},\n                'Exchange': {{ symbol: '💱', color: '#ff1493' }}\n            }};\n            var config = icons[type] || icons['Ship'];\n            return L.divIcon({{\n                html: `<div style="width:${{size}}px;height:${{size}}px;border-radius:50%;background:#fff;border:3px solid ${{config.color}};display:flex;align-items:center;justify-content:center;font-size:${{size-8}}px;box-shadow:0 2px 5px rgba(0,0,0,0.3);">${{config.symbol}}</div>`,\n                iconSize: [size, size],\n                iconAnchor: [size/2, size/2],\n                popupAnchor: [0, -size/2],\n                className: type === 'Ship' ? 'ship-marker' : 'custom-marker'\n            }});\n        }}\n\n        // Enhanced India-focused trade routes\n        var oceanRoutes = [\n            {{\n                name: "Mumbai-Rotterdam (Europe)",\n                coords: [[19.0760, 72.8777], [15.0, 60.0], [12.0, 45.0], [15.0, 35.0], [30.0, 32.0], [35.0, 25.0], [38.0, 15.0], [40.0, 5.0], [42.0, -5.0], [45.0, -15.0], [51.9244, 4.4777]],\n                value: "45B USD"\n            }},\n            {{\n                name: "Mumbai-Shanghai (China)",\n                coords: [[19.0760, 72.8777], [15.0, 68.0], [10.0, 75.0], [5.0, 85.0], [10.0, 95.0], [20.0, 110.0], [31.2304, 121.4737]],\n                value: "156B USD"\n            }},\n            {{\n                name: "Mumbai-Singapore",\n                coords: [[19.0760, 72.8777], [15.0, 75.0], [10.0, 80.0], [5.0, 90.0], [1.3521, 103.8198]],\n                value: "89B USD"\n            }},\n            {{\n                name: "Chennai-Tokyo (Japan)",\n                coords: [[13.0827, 80.2707], [10.0, 90.0], [15.0, 105.0], [25.0, 125.0], [35.6762, 139.6503]],\n                value: "67B USD"\n            }},\n            {{\n                name: "Kolkata-Hong Kong",\n                coords: [[22.5726, 88.3639], [18.0, 95.0], [15.0, 105.0], [22.3193, 114.1694]],\n                value: "45B USD"\n            }},\n            {{\n                name: "Mumbai-Dubai (UAE)",\n                coords: [[19.0760, 72.8777], [20.0, 65.0], [23.0, 58.0], [25.2048, 55.2708]],\n                value: "78B USD"\n            }},\n            {{\n                name: "Mumbai-New York (USA)",\n                coords: [[19.0760, 72.8777], [15.0, 60.0], [10.0, 40.0], [5.0, 20.0], [0.0, 0.0], [10.0, -20.0], [25.0, -40.0], [35.0, -60.0], [40.7128, -74.0060]],\n                value: "123B USD"\n            }},\n            {{\n                name: "Chennai-Sydney (Australia)",\n                coords: [[13.0827, 80.2707], [5.0, 90.0], [-10.0, 105.0], [-25.0, 130.0], [-33.8688, 151.2093]],\n                value: "54B USD"\n            }},\n            {{\n                name: "Cochin-Colombo-Malacca",\n                coords: [[9.9312, 76.2673], [7.0, 79.0], [6.9271, 79.8612], [3.0, 95.0], [1.3521, 103.8198]],\n                value: "34B USD"\n            }},\n            {{\n                name: "Mumbai-Cape Town (Africa)",\n                coords: [[19.0760, 72.8777], [10.0, 60.0], [-5.0, 50.0], [-20.0, 35.0], [-33.9249, 18.4241]],\n                value: "28B USD"\n            }}\n        ];\n\n        function addMarker(lat, lng, title, type) {{\n            var key = `${{lat.toFixed(4)}}_${{lng.toFixed(4)}}`;\n            for (let m of markers) {{\n                if (`${{m.lat.toFixed(4)}}_${{m.lng.toFixed(4)}}` === key) {{\n                    return false;\n                }}\n            }}\n            \n            var marker = L.marker([lat, lng], {{ icon: createCustomIcon(type, 28), zIndexOffset: 1000 }});\n            marker.bindPopup(`<div style="background:#1e1e1e;color:#fff;padding:10px;border-radius:6px;border:2px solid #ff8c00;"><h3 style="color:#ff8c00;margin:0 0 8px 0;">${{title}}</h3><p><strong>Type:</strong> ${{type}}</p><p><strong>Coords:</strong> ${{lat.toFixed(4)}}, ${{lng.toFixed(4)}}</p></div>`);\n            markerCluster.addLayer(marker);\n            markers.push({{lat, lng, title, type, key}});\n            markerObjects.push(marker);\n            heatmapData.push([lat, lng, 1]);\n            return true;\n        }}\n\n        markersData.forEach(m => addMarker(m.lat, m.lng, m.title, m.type));\n\n        function createOceanRoutes() {{\n            if (routesLayer) map.removeLayer(routesLayer);\n            routesLayer = L.layerGroup();\n            oceanRoutes.forEach(route => {{\n                var polyline = L.polyline(route.coords, {{\n                    color: '#00bfff',\n                    weight: 4,\n                    opacity: 0.8,\n                    className: 'route-animation ocean-route'\n                }});\n                polyline.bindPopup(`<div style="background:#1e1e1e;color:#fff;padding:10px;border-radius:6px;"><h3 style="color:#00bfff;margin:0 0 8px 0;">${{route.name}}</h3><p><strong>Trade Value:</strong> ${{route.value}}</p></div>`);\n                routesLayer.addLayer(polyline);\n            }});\n            map.addLayer(routesLayer);\n        }}\n\n        function createLiveShips() {{\n            if (liveShipsLayer) map.removeLayer(liveShipsLayer);\n            liveShipsLayer = L.layerGroup();\n            oceanRoutes.forEach(route => {{\n                for (var i = 1; i < route.coords.length - 1; i += 2) {{\n                    var ship = L.marker(route.coords[i], {{ icon: createCustomIcon('Ship', 32), zIndexOffset: 1500 }});\n                    ship.bindPopup(`<div style="background:#1e1e1e;color:#fff;padding:10px;border-radius:6px;"><h3 style="color:#ff8c00;">🚢 Cargo Ship</h3><p><strong>Route:</strong> ${{route.name.split(' ')[0]}}</p><p><strong>Speed:</strong> ${{Math.floor(Math.random()*10+15)}} knots</p></div>`);\n                    liveShipsLayer.addLayer(ship);\n                }}\n            }});\n            map.addLayer(liveShipsLayer);\n        }}\n\n        map.on('click', function(e) {{\n            if (deleteMode) return;\n            var title = prompt("Enter marker name:");\n            if (title && title.trim()) {{\n                var type = window.currentMarkerType || "Ship";\n                if (addMarker(e.latlng.lat, e.latlng.lng, title.trim(), type)) {{\n                    updateHeatmap();\n                    try {{\n                        var clickMarkers = JSON.parse(localStorage.getItem('clickMarkers') || '[]');\n                        clickMarkers.push({{lat: e.latlng.lat, lng: e.latlng.lng, title: title.trim(), type: type, timestamp: Date.now()}});\n                        localStorage.setItem('clickMarkers', JSON.stringify(clickMarkers));\n                    }} catch(err) {{}}\n                }}\n            }}\n        }});\n\n        function updateHeatmap() {{\n            if (heatLayer) map.removeLayer(heatLayer);\n            if (heatmapData.length > 0) {{\n                heatLayer = L.heatLayer(heatmapData, {{radius: 25, blur: 15, gradient: {{0.0:'#000080', 0.5:'#00ff80', 1.0:'#ff0000'}}}});\n            }}\n        }}\n\n        window.addMarkerFromQt = function(lat, lng, title, type) {{\n            var result = addMarker(lat, lng, title, type);\n            if (result) updateHeatmap();\n            return result;\n        }};\n\n        window.setCurrentMarkerType = function(type) {{ window.currentMarkerType = type; }};\n\n        window.clearAllMarkers = function() {{\n            markerCluster.clearLayers();\n            markers = [];\n            markerObjects = [];\n            heatmapData = [];\n            updateHeatmap();\n        }};\n\n        window.toggleHeatmap = function() {{\n            if (map.hasLayer(heatLayer)) map.removeLayer(heatLayer);\n            else if (heatLayer) map.addLayer(heatLayer);\n        }};\n\n        window.toggleTradeRoutes = function() {{\n            if (map.hasLayer(routesLayer)) map.removeLayer(routesLayer);\n            else createOceanRoutes();\n        }};\n\n        window.toggleLiveShips = function() {{\n            if (map.hasLayer(liveShipsLayer)) map.removeLayer(liveShipsLayer);\n            else createLiveShips();\n        }};\n\n        window.setDeleteMode = function(mode) {{ deleteMode = mode; }};\n\n        window.getClickMarkers = function() {{\n            try {{\n                var clickMarkers = JSON.parse(localStorage.getItem('clickMarkers') || '[]');\n                localStorage.removeItem('clickMarkers');\n                return clickMarkers;\n            }} catch(e) {{ return []; }}\n        }};\n\n        window.currentMarkerType = "Ship";\n        createOceanRoutes();\n        createLiveShips();\n        updateHeatmap();\n    </script>\n</body>\n</html>"""
                html_path = 'maritime_map.html'
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.web_view.loadFinished.connect(self.on_loaded)
                self.web_view.load(QUrl.fromLocalFile(os.path.abspath(html_path)))
                logger.info('Map created successfully')
            except Exception as e:
                logger.error(f'Map creation failed: {e}', exc_info=True)

    def on_loaded(self, success):
        """Map loaded callback"""
        if success:
            logger.info('Map loaded successfully')
            js_code = f"if(window.setCurrentMarkerType) window.setCurrentMarkerType('{self.selected_marker_type}');"
            self.web_view.page().runJavaScript(js_code)
            self.write_status('ready')
        else:
            logger.error('Map load failed')
            self.write_status('error')

    def start_file_watcher(self):
        """Watch for file changes"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_files)
        self.timer.start(500)

    def check_files(self):
        """Check for file updates"""
        try:
            if os.path.exists(self.markers_file):
                mtime = os.path.getmtime(self.markers_file)
                if mtime > self.last_modified:
                    self.last_modified = mtime
                    self.load_markers()
            self.check_click_markers()
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r') as f:
                    commands = json.load(f)
                for cmd in commands.get('commands', []):
                    self.execute_command(cmd)
                with open(self.commands_file, 'w') as f:
                    json.dump({'commands': []}, f)
        except Exception as e:
            logger.error(f'File check error: {e}', exc_info=True)

    def check_click_markers(self):
        """Check for click-added markers"""
        try:
            self.web_view.page().runJavaScript('if(window.getClickMarkers) window.getClickMarkers(); else [];', self.process_click_markers)
        except Exception as e:
            logger.error(f'Click marker check failed: {e}', exc_info=True)

    def process_click_markers(self, click_markers):
        """Process click markers"""
        if click_markers and len(click_markers) > 0:
            existing = self.load_markers_data()
            added = 0
            for marker in click_markers:
                is_dup = False
                for ex in existing:
                    if abs(ex['lat'] - marker['lat']) < 0.0005 and abs(ex['lng'] - marker['lng']) < 0.0005:
                        is_dup = True
                        break
                if not is_dup:
                    existing.append({'lat': marker['lat'], 'lng': marker['lng'], 'title': marker['title'], 'type': marker['type']})
                    added += 1
            if added > 0:
                with open(self.markers_file, 'w') as f:
                    json.dump(existing, f, indent=2)
                logger.info(f'Added {added} new markers')

    def load_markers(self):
        """Load markers from file"""
        try:
            if os.path.exists(self.markers_file):
                with open(self.markers_file, 'r') as f:
                    data = json.load(f)
                self.web_view.page().runJavaScript('if(window.clearAllMarkers) window.clearAllMarkers();')
                for marker in data:
                    js = f"if(window.addMarkerFromQt) window.addMarkerFromQt({marker['lat']}, {marker['lng']}, '{marker['title']}', '{marker['type']}');"
                    self.web_view.page().runJavaScript(js)
                self.markers_data = data
                logger.info(f'Loaded {len(data)} markers')
                return data
        except Exception as e:
            logger.error(f'Load markers failed: {e}', exc_info=True)
        return []

    def load_markers_data(self):
        """Load markers data"""
        try:
            if os.path.exists(self.markers_file):
                with open(self.markers_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    def execute_command(self, cmd):
        """Execute command"""
        try:
            if cmd == 'toggle_routes':
                self.web_view.page().runJavaScript('if(window.toggleTradeRoutes) window.toggleTradeRoutes();')
            elif cmd == 'toggle_ships':
                self.web_view.page().runJavaScript('if(window.toggleLiveShips) window.toggleLiveShips();')
            elif cmd == 'clear_all':
                self.web_view.page().runJavaScript('if(window.clearAllMarkers) window.clearAllMarkers();')
                with open(self.markers_file, 'w') as f:
                    json.dump([], f)
                self.markers_data = []
                self.existing_markers.clear()
            elif cmd.startswith('set_marker_type:'):
                marker_type = cmd.split(':', 1)[1]
                self.web_view.page().runJavaScript(f"if(window.setCurrentMarkerType) window.setCurrentMarkerType('{marker_type}');")
                self.selected_marker_type = marker_type
        except Exception as e:
            logger.error(f'Command execution failed: {e}', exc_info=True)

    def write_status(self, status):
        """Write status"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump({'status': status, 'timestamp': time.time()}, f)
        except Exception as e:
            logger.error(f'Status write failed: {e}', exc_info=True)

    def closeEvent(self, event):
        """Handle close event"""
        self.close_application()
        event.accept()

    def close_application(self):
        """Close application"""
        try:
            logger.info('Closing maritime map')
            self.write_status('closed')
            if hasattr(self, 'timer'):
                self.timer.stop()
            for f in ['maritime_map.html', self.commands_file, self.status_file]:
                if os.path.exists(f):
                    os.remove(f)
            self.close()
            QApplication.quit()
            sys.exit(0)
        except Exception as e:
            logger.error(f'Close error: {e}', exc_info=True)
            sys.exit(1)

def closeEvent(self, event):
    """Handle close event"""
    self.close_application()
    event.accept()

class ProfileTab(BaseTab):
    """Enhanced profile tab - refactored and optimized"""

    def __init__(self, app):
        super().__init__(app)
        self.constants = ProfileConstants()
        self.last_refresh = None
        self.usage_stats = {}
        self.request_count = 0
        self.logout_in_progress = False
        self.api_client = create_api_client(self._get_initial_session_data())
        self.data_manager = ProfileDataManager(app, self.api_client)
        self.ui_builder = ProfileUIBuilder(self)
        logger.info('ProfileTab initialized', context={'api_url': config.get_api_url()})

    def _get_initial_session_data(self):
        """Get initial session data safely"""
        if hasattr(self.app, 'get_session_data'):
            return self.app.get_session_data()
        elif hasattr(self.app, 'session_data'):
            return self.app.session_data
        return {self.constants.USER_TYPE_KEY: self.constants.UNKNOWN_USER_TYPE}

    def get_label(self):
        return 'Profile'

    @handle_errors('create_profile_content')
    def create_content(self):
        """Create profile content based on user type"""
        self.refresh_data()
        session_data = self.data_manager.get_session_data()
        user_type = session_data.get(self.constants.USER_TYPE_KEY, self.constants.UNKNOWN_USER_TYPE)
        content_creators = {self.constants.GUEST_USER_TYPE: self._create_guest_profile, self.constants.REGISTERED_USER_TYPE: self._create_user_profile, self.constants.UNKNOWN_USER_TYPE: self._create_unknown_profile}
        creator = content_creators.get(user_type, self._create_unknown_profile)
        creator()

    @handle_errors('refresh_profile_data')
    def refresh_data(self):
        """Refresh all profile data"""
        self.last_refresh = datetime.now()
        self.data_manager.invalidate_cache()
        session_data = self.data_manager.get_session_data()
        self.api_client = create_api_client(session_data)
        if session_data.get(self.constants.AUTHENTICATED_KEY) and self.api_client:
            self._fetch_authenticated_data()
        self._update_request_count()

    def _fetch_authenticated_data(self):
        """Fetch data for authenticated users"""
        try:
            if self.api_client.is_registered():
                profile_result = self.api_client.get_user_profile()
                if profile_result.get(self.constants.SUCCESS_KEY):
                    self.data_manager.update_session_data({'user_info': profile_result['profile']})
                usage_result = self.api_client.get_user_usage()
                if usage_result.get(self.constants.SUCCESS_KEY):
                    self.usage_stats = usage_result['usage']
            elif self.api_client.is_guest():
                status_result = self.api_client.get_guest_status()
                if status_result.get(self.constants.SUCCESS_KEY):
                    self.data_manager.update_session_data(status_result['status'])
        except Exception as e:
            logger.warning('Failed to fetch authenticated data', context={'error': str(e)})

    def _update_request_count(self):
        """Update request count from various sources"""
        if self.api_client:
            self.request_count = self.api_client.get_request_count()
        elif hasattr(self.app, 'api_request_count'):
            self.request_count = self.app.api_request_count
        else:
            session_data = self.data_manager.get_session_data()
            self.request_count = session_data.get('requests_today', 0)

    def _create_guest_profile(self):
        """Create guest user profile"""
        session_data = self.data_manager.get_session_data()
        api_key = session_data.get(self.constants.API_KEY_KEY)
        self.ui_builder.create_header('👤 Guest Profile', self.last_refresh)
        self.ui_builder.create_two_column_layout(lambda: self._create_guest_status_info(session_data, api_key), lambda: self._create_guest_upgrade_info(session_data))
        dpg.add_spacer(height=20)
        self._create_session_stats(session_data)

    def _create_user_profile(self):
        """Create registered user profile"""
        session_data = self.data_manager.get_session_data()
        user_info = session_data.get('user_info', {})
        username = user_info.get('username', 'User')
        self.ui_builder.create_header(f"🔑 {username}'s Profile", self.last_refresh)
        self.ui_builder.create_two_column_layout(lambda: self._create_user_account_info(user_info, session_data), lambda: self._create_user_usage_info(user_info, session_data))
        dpg.add_spacer(height=20)
        self._create_user_stats()

    def _create_unknown_profile(self):
        """Create unknown state profile"""
        self.ui_builder.create_header('❓ Unknown Session State', self.last_refresh)
        info_items = ['Unable to determine authentication status', 'This may indicate a configuration issue.', None, {'text': 'Try refreshing or restarting the application', 'color': self.constants.COLORS['warning']}]
        self.ui_builder.create_info_widget('Session Status', info_items, width=500, height=200)
        buttons = [{'label': '🔄 Refresh Profile', 'callback': self.manual_refresh}, {'label': 'Clear Session & Restart', 'callback': self.logout_user}]
        self.ui_builder.create_button_group(buttons)

    def _create_guest_status_info(self, session_data, api_key):
        """Create guest status information widget"""
        device_id = session_data.get(self.constants.DEVICE_ID_KEY, 'Unknown')
        display_device_id = device_id[:20] + '...' if len(device_id) > 20 else device_id
        daily_limit = session_data.get('daily_limit', self.constants.GUEST_DAILY_LIMIT)
        requests_today = session_data.get('requests_today', 0)
        remaining = max(0, daily_limit - requests_today)
        info_items = ['Account Type: Guest User', f'Device ID: {display_device_id}', None, self._get_api_key_info(api_key), None, f'Session Requests: {self.request_count}', f"Today's Requests: {requests_today}/{daily_limit}", {'text': f'Remaining Today: {remaining}', 'color': self.constants.COLORS['success'] if remaining > 10 else self.constants.COLORS['error']}, None, '✓ Basic market data', '✓ Real-time quotes', '✓ Public databases']
        self.ui_builder.create_info_widget('Current Session Status', info_items)

    def _create_guest_upgrade_info(self, session_data):
        """Create guest upgrade information widget"""
        api_key = session_data.get(self.constants.API_KEY_KEY)
        if api_key and api_key.startswith('fk_guest_'):
            current_status = '🔄 Current: Guest API Key'
            status_items = ['• Temporary access (24 hours)', '• 50 requests per day']
        else:
            current_status = '🔄 Current: Offline Mode'
            status_items = ['• No API access']
        info_items = [{'text': current_status, 'color': self.constants.COLORS['warning']}, None, *status_items, None, {'text': '🔑 Create Account', 'color': self.constants.COLORS['info']}, 'Get unlimited access:', '• Permanent API key', '• Unlimited requests', '• All databases access', '• Premium features']
        self.ui_builder.create_info_widget('Upgrade Your Access', info_items)
        buttons = [{'label': 'Create Free Account', 'callback': self.show_signup_info}, {'label': 'Sign In to Account', 'callback': self.show_login_info}]
        self.ui_builder.create_button_group(buttons)

    def _create_user_account_info(self, user_info, session_data):
        """Create user account information widget"""
        api_key = session_data.get(self.constants.API_KEY_KEY)
        info_items = [f'Username: {user_info.get('username', 'N/A')}', f'Email: {user_info.get('email', 'N/A')}', f'Account Type: {user_info.get('account_type', 'free').title()}', f'Member Since: {self._format_date(user_info.get('created_at'))}', None, {'text': 'Authentication:', 'color': self.constants.COLORS['info']}, self._get_api_key_info(api_key, is_user=True), None, '✓ Unlimited API requests', '✓ All database access', '✓ Premium features']
        self.ui_builder.create_info_widget('Account Details', info_items)
        buttons = [{'label': 'Regenerate API Key', 'callback': self.regenerate_api_key}, {'label': 'Switch Account', 'callback': self.logout_user}]
        self.ui_builder.create_button_group(buttons)

    def _create_user_usage_info(self, user_info, session_data):
        """Create user usage information widget"""
        credit_balance = user_info.get('credit_balance', 0)
        if credit_balance > 1000:
            balance_color, status = (self.constants.COLORS['success'], 'Excellent')
        elif credit_balance > 100:
            balance_color, status = (self.constants.COLORS['warning'], 'Good')
        else:
            balance_color, status = (self.constants.COLORS['error'], 'Low Credits')
        info_items = [f'Current Balance: {credit_balance} credits', {'text': f'Status: {status}', 'color': balance_color}, None, {'text': 'Live Usage Stats:', 'color': self.constants.COLORS['info']}, f'Total Requests: {self.usage_stats.get('total_requests', 'Loading...')}', f'Credits Used: {self.usage_stats.get('total_credits_used', 'Loading...')}', f'This Session: {self.request_count}', None, 'Quick Actions:']
        self.ui_builder.create_info_widget('Credits & Usage', info_items)
        buttons = [{'label': 'View Usage Details', 'callback': self.view_usage_stats}, {'label': 'API Documentation', 'callback': self.show_api_docs}, {'label': 'Subscription Info', 'callback': self.show_subscription_info}]
        self.ui_builder.create_button_group(buttons)

    def _create_session_stats(self, session_data):
        """Create session statistics for guest users"""
        dpg.add_text('📊 Live Session Statistics', color=self.constants.COLORS['info'])
        dpg.add_separator()
        dpg.add_spacer(height=10)
        api_key = session_data.get(self.constants.API_KEY_KEY)
        daily_limit = session_data.get('daily_limit', self.constants.GUEST_DAILY_LIMIT)
        requests_today = session_data.get('requests_today', 0)
        stats_text = [f'Session Requests: {self.request_count}', f'Daily Progress: {requests_today}/{daily_limit}', f'Authentication: {('API Key' if api_key else 'Offline')}', f'Server: {config.get_api_url()}']
        for stat in stats_text:
            dpg.add_text(stat)

    def _create_user_stats(self):
        """Create user statistics for registered users"""
        dpg.add_text('📊 Live Account Overview', color=self.constants.COLORS['info'])
        dpg.add_separator()
        dpg.add_spacer(height=10)
        stats_text = [f'Session Requests: {self.request_count}', f'Total Requests: {self.usage_stats.get('total_requests', 'Loading...')}', f'Success Rate: 100%', f'Server: {config.get_api_url()}', f'Last Update: {(self.last_refresh.strftime('%H:%M:%S') if self.last_refresh else 'Never')}']
        for stat in stats_text:
            dpg.add_text(stat)

    def _get_api_key_info(self, api_key, is_user=False):
        """Get API key information text"""
        if not api_key:
            return {'text': 'Method: No API Key', 'color': self.constants.COLORS['error']}
        if api_key.startswith('fk_user_'):
            return {'text': f'Method: Permanent API Key\nAPI Key: {api_key[:25]}...', 'color': self.constants.COLORS['success']}
        elif api_key.startswith('fk_guest_'):
            return {'text': f'Method: Temporary API Key\nAPI Key: {api_key[:20]}...', 'color': self.constants.COLORS['warning']}
        else:
            return {'text': f'Method: Legacy API Key\nAPI Key: {api_key[:20]}...', 'color': self.constants.COLORS['warning']}

    @lru_cache(maxsize=32)
    def _format_date(self, date_str):
        """Format date string for display"""
        if not date_str:
            return 'Never'
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str

    @handle_errors('manual_refresh')
    def manual_refresh(self):
        """Manual refresh with error handling"""
        self.refresh_data()
        self._recreate_content()
        self.show_message('Profile refreshed successfully', 'success')

    @handle_errors('logout_user')
    def logout_user(self):
        """Complete logout process"""
        if self.logout_in_progress:
            return
        self.logout_in_progress = True
        try:
            self._update_logout_button_state(True)
            logger.info('Starting logout process')
            self._perform_api_logout()
            self.data_manager.clear_session()
            self._clear_saved_credentials()
            self._complete_logout()
        finally:
            self.logout_in_progress = False

    def _perform_api_logout(self):
        """Perform API logout with fallbacks"""
        if not self.api_client or not self.data_manager.get_session_data().get(self.constants.AUTHENTICATED_KEY):
            return True
        try:
            result = self.api_client.make_request('POST', '/auth/logout')
            if result.get(self.constants.SUCCESS_KEY):
                logger.info('API logout successful')
                return True
        except Exception as e:
            logger.warning('API logout failed, performing local cleanup', context={'error': str(e)})
        return True

    def _clear_saved_credentials(self):
        """Clear saved credentials"""
        try:
            from fincept_terminal.utils.Managers.session_manager import session_manager
            session_manager.clear_credentials()
            logger.info('Saved credentials cleared')
        except ImportError:
            logger.debug('Session manager not available')
        except Exception as e:
            logger.warning('Could not clear credentials', context={'error': str(e)})

    def _complete_logout(self):
        """Complete logout and exit"""
        logger.info('Logout completed successfully')
        print('\n✅ Logout completed successfully!\n🚪 Closing Fincept Terminal...\n\nTo access Fincept again:\n1. 🔄 Run the application\n2. 🔑 Choose authentication method\n3. 👤 Sign in or continue as guest\n\n👋 Thank you for using Fincept!\n        '.strip())
        threading.Timer(self.constants.LOGOUT_TIMER_DELAY, self._exit_application).start()

    def _update_logout_button_state(self, logging_out=False):
        """Update logout button state"""
        try:
            if dpg.does_item_exist('logout_btn'):
                if logging_out:
                    dpg.set_item_label('logout_btn', 'Logging out...')
                    dpg.disable_item('logout_btn')
                else:
                    dpg.set_item_label('logout_btn', '🚪 Logout')
                    dpg.enable_item('logout_btn')
        except Exception as e:
            logger.debug('Could not update logout button', context={'error': str(e)})

    def _exit_application(self):
        """Exit application with fallbacks"""
        exit_methods = [lambda: self.app.close_application(), lambda: self.app.shutdown(), lambda: dpg.stop_dearpygui(), lambda: __import__('sys').exit(0)]
        for exit_method in exit_methods:
            try:
                exit_method()
                return
            except:
                continue

    @handle_errors('regenerate_api_key')
    def regenerate_api_key(self):
        """Regenerate API key for authenticated users"""
        if not self.api_client or not self.api_client.is_registered():
            self.show_message('API key regeneration requires authenticated user', 'error')
            return
        result = self.api_client.regenerate_api_key()
        if result.get(self.constants.SUCCESS_KEY):
            new_api_key = result.get(self.constants.API_KEY_KEY)
            if new_api_key:
                self.data_manager.update_session_data({self.constants.API_KEY_KEY: new_api_key})
                threading.Timer(1.0, self.manual_refresh).start()
                self.show_message('API key regenerated successfully!', 'success')
            else:
                self.show_message('No new API key received', 'error')
        else:
            self.show_message('API key regeneration failed', 'error')

    def view_usage_stats(self):
        """Display detailed usage statistics"""
        stats = [f'📊 Detailed Usage Statistics:', f'Total Requests: {self.usage_stats.get('total_requests', 0)}', f'Credits Used: {self.usage_stats.get('total_credits_used', 0)}', f'Session Requests: {self.request_count}', f'Success Rate: {self.usage_stats.get('success_rate', 100)}%']
        for stat in stats:
            print(stat)

    def show_api_docs(self):
        """Open API documentation"""
        try:
            api_docs_url = f'{config.get_api_url()}/docs'
            webbrowser.open(api_docs_url)
            print(f'✅ Opened API docs: {api_docs_url}')
        except Exception as e:
            print(f'📖 Manual URL: {config.get_api_url()}/docs')

    def show_subscription_info(self):
        """Display subscription information"""
        session_data = self.data_manager.get_session_data()
        user_type = session_data.get(self.constants.USER_TYPE_KEY)
        if user_type == self.constants.REGISTERED_USER_TYPE:
            print('💳 Registered Account - Full access to all features')
        else:
            print('💳 Guest Account - Limited access. Create account for full features')

    def show_signup_info(self):
        """Display signup information"""
        print('📝 Create Account: Use logout button to return to authentication screen')

    def show_login_info(self):
        """Display login information"""
        print('🔑 Sign In: Use logout button to return to authentication screen')

    def show_message(self, message: str, msg_type: str='info'):
        """Display message with appropriate styling"""
        icons = {'success': '✅', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}
        icon = icons.get(msg_type, 'ℹ️')
        print(f'{icon} {message}')
        if msg_type == 'error':
            logger.error(message)
        elif msg_type == 'warning':
            logger.warning(message)
        else:
            logger.info(message)

    def _recreate_content(self):
        """Safely recreate tab content"""
        try:
            if hasattr(self, 'content_tag') and dpg.does_item_exist(self.content_tag):
                children = dpg.get_item_children(self.content_tag, 1)
                for child in children:
                    if dpg.does_item_exist(child):
                        dpg.delete_item(child)
            self.create_content()
        except Exception as e:
            logger.warning('Could not recreate content', context={'error': str(e)})

    @handle_errors('cleanup')
    def cleanup(self):
        """Cleanup resources"""
        self.api_client = None
        self.usage_stats = {}
        self.request_count = 0
        self.data_manager.invalidate_cache()
        self._format_date.cache_clear()
        logger.info('ProfileTab cleanup completed')

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass

def _exit_application(self):
    """Exit application with fallbacks"""
    exit_methods = [lambda: self.app.close_application(), lambda: self.app.shutdown(), lambda: dpg.stop_dearpygui(), lambda: __import__('sys').exit(0)]
    for exit_method in exit_methods:
        try:
            exit_method()
            return
        except:
            continue

class OECDDataTab(BaseTab):
    """OECD Economic Data tab for displaying economic indicators from OECD"""

    def __init__(self, app):
        super().__init__(app)
        self.tab_id = str(uuid.uuid4())[:8]
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=2)
        try:
            from fincept_terminal.DatabaseConnector.DataSources.oced_data.oced_provider import OECDProvider
            self.oecd_provider = OECDProvider()
            print('✅ OECD Provider initialized successfully')
        except ImportError as e:
            error(f'Failed to import OECD provider: {e}', module='OECDDataTab')
            self.oecd_provider = None
            print(f'❌ OECD Provider import failed: {e}')
        try:
            from fincept_terminal.DatabaseConnector.DataSources.oced_data.constants import COUNTRY_TO_CODE_GDP, COUNTRY_TO_CODE_CPI, COUNTRY_TO_CODE_UNEMPLOYMENT, COUNTRY_TO_CODE_IR, COUNTRY_TO_CODE_CLI, COUNTRY_TO_CODE_SHARES, COUNTRY_TO_CODE_RGDP, COUNTRY_TO_CODE_GDP_FORECAST
            self.constants = {'gdp': list(COUNTRY_TO_CODE_GDP.keys())[:20], 'cpi': list(COUNTRY_TO_CODE_CPI.keys())[:20], 'unemployment': list(COUNTRY_TO_CODE_UNEMPLOYMENT.keys())[:20], 'interest_rates': list(COUNTRY_TO_CODE_IR.keys())[:20], 'cli': list(COUNTRY_TO_CODE_CLI.keys())[:20], 'shares': list(COUNTRY_TO_CODE_SHARES.keys())[:20], 'housing': list(COUNTRY_TO_CODE_RGDP.keys())[:20], 'forecast': list(COUNTRY_TO_CODE_GDP_FORECAST.keys())[:20]}
            print('✅ Constants imported successfully')
        except ImportError as e:
            self.constants = {'gdp': ['united_states', 'germany', 'japan', 'united_kingdom', 'france', 'italy', 'canada', 'australia', 'spain', 'netherlands', 'g7', 'g20', 'oecd', 'all']}
            print(f'⚠️ Using fallback constants: {e}')
        self.current_data = {}
        self.last_refresh = None
        self.indicators = {'GDP Nominal': {'method': 'get_gdp_nominal', 'params': ['countries', 'frequency', 'units', 'price_base'], 'countries_key': 'gdp', 'description': 'Gross Domestic Product at market prices', 'y_label': 'GDP Value', 'units_info': {'level': 'USD (Millions)', 'index': 'Index (2015=100)', 'capita': 'USD per Capita', 'growth': 'Growth Rate (%)'}}, 'GDP Real': {'method': 'get_gdp_real', 'params': ['countries', 'frequency'], 'countries_key': 'gdp', 'description': 'Real GDP (PPP-adjusted, constant prices)', 'y_label': 'Real GDP (USD PPP)', 'units_info': {'default': 'USD PPP (Millions)'}}, 'Consumer Price Index': {'method': 'get_cpi', 'params': ['countries', 'frequency', 'transform', 'harmonized', 'expenditure'], 'countries_key': 'cpi', 'description': 'Consumer Price Index - Inflation measure', 'y_label': 'CPI Value', 'units_info': {'index': 'Index (2015=100)', 'yoy': 'Year-over-Year (%)', 'mom': 'Month-over-Month (%)'}}, 'Unemployment Rate': {'method': 'get_unemployment', 'params': ['countries', 'frequency', 'sex', 'age', 'seasonal_adjustment'], 'countries_key': 'unemployment', 'description': 'Unemployment rate as % of labor force', 'y_label': 'Unemployment Rate (%)', 'units_info': {'default': 'Percentage (%)'}}, 'Interest Rates': {'method': 'get_interest_rates', 'params': ['countries', 'duration', 'frequency'], 'countries_key': 'interest_rates', 'description': 'Interest rates by duration', 'y_label': 'Interest Rate (%)', 'units_info': {'default': 'Percentage (%)'}}}
        self.param_options = {'frequency': ['monthly', 'quarter', 'annual'], 'units': ['level', 'index', 'capita', 'volume', 'current_prices', 'growth', 'deflator'], 'price_base': ['current_prices', 'volume'], 'transform': ['index', 'yoy', 'mom', 'period'], 'expenditure': ['total', 'food_non_alcoholic_beverages', 'housing_water_electricity_gas', 'transport', 'energy'], 'sex': ['total', 'male', 'female'], 'age': ['total', '15-24', '25+'], 'duration': ['immediate', 'short', 'long'], 'adjustment': ['amplitude', 'normalized']}

    def get_label(self):
        return 'OECD'

    def get_countries_for_indicator(self, indicator: str) -> List[str]:
        """Get available countries for a specific indicator"""
        if indicator in self.indicators:
            countries_key = self.indicators[indicator].get('countries_key', 'gdp')
            return self.constants.get(countries_key, self.constants.get('gdp', []))
        return self.constants.get('gdp', [])

    def format_number(self, value: float, unit_type: str='default') -> str:
        """Format numbers for better readability"""
        try:
            if value is None or str(value).lower() == 'nan':
                return 'N/A'
            num_value = float(value)
            if '%' in unit_type or 'percentage' in unit_type.lower():
                return f'{num_value:.2f}%'
            abs_value = abs(num_value)
            if abs_value >= 1000000000000:
                return f'{num_value / 1000000000000:.2f}T'
            elif abs_value >= 1000000000:
                return f'{num_value / 1000000000:.2f}B'
            elif abs_value >= 1000000:
                return f'{num_value / 1000000:.2f}M'
            elif abs_value >= 1000:
                return f'{num_value:,.0f}'
            elif abs_value >= 1:
                return f'{num_value:.2f}'
            else:
                return f'{num_value:.4f}'
        except (ValueError, TypeError):
            return str(value) if value is not None else 'N/A'

    def get_y_axis_label(self, indicator: str, params: Dict[str, Any]) -> str:
        """Generate appropriate Y-axis label based on indicator and parameters"""
        if indicator not in self.indicators:
            return 'Value'
        config = self.indicators[indicator]
        base_label = config.get('y_label', 'Value')
        units_info = config.get('units_info', {})
        unit_key = params.get('units', params.get('transform', 'default'))
        unit_desc = units_info.get(unit_key, units_info.get('default', ''))
        if unit_desc:
            return f'{base_label} ({unit_desc})'
        return base_label

    def create_content(self):
        """Create the enhanced OECD data interface"""
        try:
            print('🔧 Creating enhanced OECD content...')
            with dpg.group():
                dpg.add_text('🌍 OECD Economic Indicators', color=[100, 200, 255])
                dpg.add_text('Access comprehensive economic data from OECD countries with enhanced visualizations', color=[180, 180, 180])
                with dpg.group(horizontal=True):
                    dpg.add_text('Last Updated:', color=[150, 150, 150])
                    dpg.add_text('Not yet loaded', tag=f'last_update_{self.tab_id}', color=[120, 120, 120])
            dpg.add_spacer(height=15)
            if not self.oecd_provider:
                dpg.add_text('❌ OECD Provider not available. Check import paths.', color=[255, 100, 100])
                return
            with dpg.child_window(height=750, border=True):
                with dpg.collapsing_header(label='📊 Data Selection & Parameters', default_open=True):
                    dpg.add_spacer(height=5)
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            dpg.add_text('Economic Indicator:', color=[200, 200, 100])
                            dpg.add_combo(list(self.indicators.keys()), tag=f'indicator_{self.tab_id}', default_value='GDP Nominal', width=220, callback=self.on_indicator_change)
                        dpg.add_text('', tag=f'indicator_desc_{self.tab_id}', color=[160, 160, 160], wrap=600)
                    dpg.add_spacer(height=10)
                    with dpg.group(horizontal=True):
                        dpg.add_text('Country/Region:')
                        initial_countries = self.get_countries_for_indicator('GDP Nominal')
                        dpg.add_combo(initial_countries, tag=f'countries_{self.tab_id}', default_value=initial_countries[0] if initial_countries else 'united_states', width=150)
                        dpg.add_spacer(width=30)
                        dpg.add_text('Start Date:')
                        dpg.add_input_text(tag=f'start_date_{self.tab_id}', default_value='2020-01-01', width=110, hint='YYYY-MM-DD')
                        dpg.add_spacer(width=15)
                        dpg.add_text('End Date:')
                        dpg.add_input_text(tag=f'end_date_{self.tab_id}', default_value='2024-12-31', width=110, hint='YYYY-MM-DD')
                    dpg.add_spacer(height=10)
                    with dpg.group(tag=f'dynamic_params_{self.tab_id}'):
                        self.create_parameter_controls('GDP Nominal')
                    dpg.add_spacer(height=15)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label='📈 Fetch Data', callback=self.fetch_data, width=130, height=35)
                        dpg.add_button(label='🔄 Refresh', callback=self.refresh_data, width=100, height=35)
                        dpg.add_button(label='🧹 Clear', callback=self.clear_data, width=90, height=35)
                        dpg.add_button(label='📊 Export CSV', callback=self.export_data, width=130, height=35)
                    dpg.add_spacer(height=10)
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            dpg.add_text('Status:', color=[150, 150, 150])
                            dpg.add_text('Ready', tag=f'status_{self.tab_id}', color=[100, 255, 100])
                        dpg.add_text('', tag=f'data_summary_{self.tab_id}', color=[140, 140, 140])
                dpg.add_separator()
                dpg.add_spacer(height=5)
                with dpg.tab_bar():
                    with dpg.tab(label='📈 Interactive Chart'):
                        dpg.add_spacer(height=8)
                        with dpg.group():
                            with dpg.group(horizontal=True):
                                dpg.add_text('Chart Type:')
                                dpg.add_combo(['Line', 'Bar', 'Scatter'], tag=f'chart_type_{self.tab_id}', default_value='Line', width=100, callback=self.on_chart_type_change)
                                dpg.add_spacer(width=20)
                                dpg.add_checkbox(label='Show Grid', tag=f'show_grid_{self.tab_id}', default_value=True, callback=self.update_chart)
                                dpg.add_spacer(width=20)
                                dpg.add_checkbox(label='Auto-scale Y', tag=f'auto_scale_{self.tab_id}', default_value=True)
                                dpg.add_spacer(width=30)
                                dpg.add_button(label='🔄 Refresh Chart', callback=self.update_chart, width=140)
                        dpg.add_spacer(height=10)
                        with dpg.plot(tag=f'chart_plot_{self.tab_id}', label='Economic Data Visualization', height=400, width=-1):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label='Time Period', tag=f'x_axis_{self.tab_id}')
                            dpg.add_plot_axis(dpg.mvYAxis, label='Value', tag=f'y_axis_{self.tab_id}')
                        with dpg.group():
                            dpg.add_text('Chart Information:', color=[150, 150, 200])
                            dpg.add_text('', tag=f'chart_info_{self.tab_id}', color=[130, 130, 130], wrap=800)
                    with dpg.tab(label='📊 Data Table'):
                        dpg.add_spacer(height=8)
                        with dpg.group(horizontal=True):
                            dpg.add_text('Show rows:')
                            dpg.add_combo(['25', '50', '100', 'All'], tag=f'table_limit_{self.tab_id}', default_value='50', width=80, callback=self.update_table)
                            dpg.add_spacer(width=20)
                            dpg.add_text('Search:')
                            dpg.add_input_text(tag=f'table_search_{self.tab_id}', width=150, hint='Filter data...', callback=self.update_table)
                        dpg.add_spacer(height=10)
                        with dpg.table(tag=f'data_table_{self.tab_id}', header_row=True, resizable=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=380, sortable=True):
                            dpg.add_table_column(label='Date', width_fixed=True, init_width_or_weight=120)
                            dpg.add_table_column(label='Country', width_fixed=True, init_width_or_weight=140)
                            dpg.add_table_column(label='Value', width_fixed=True, init_width_or_weight=180)
                            dpg.add_table_column(label='Frequency', width_fixed=True, init_width_or_weight=100)
                            dpg.add_table_column(label='Indicator', width_fixed=True, init_width_or_weight=160)
                    with dpg.tab(label='📈 Statistics'):
                        dpg.add_spacer(height=10)
                        with dpg.group():
                            dpg.add_text('Data Statistics & Analysis', color=[200, 200, 100])
                            dpg.add_spacer(height=10)
                            with dpg.group(tag=f'stats_display_{self.tab_id}'):
                                dpg.add_text('No data loaded for analysis...', color=[140, 140, 140])
                    with dpg.tab(label='🔍 Raw Data'):
                        dpg.add_spacer(height=8)
                        with dpg.group(horizontal=True):
                            dpg.add_button(label='📋 Copy JSON', callback=self.copy_raw_data, width=130)
                            dpg.add_button(label='💾 Save JSON', callback=self.save_raw_data, width=130)
                        dpg.add_spacer(height=10)
                        dpg.add_input_text(tag=f'raw_display_{self.tab_id}', multiline=True, height=380, width=-1, readonly=True, default_value='No data loaded...')
            print('✅ Enhanced OECD content created successfully')
        except Exception as e:
            error(f'Error creating OECD tab content: {str(e)}', module='OECDDataTab')
            print(f'❌ Error creating content: {str(e)}')
            print(f'❌ Traceback: {traceback.format_exc()}')
            dpg.add_text(f'Error: {str(e)}', color=[255, 100, 100])

    def create_parameter_controls(self, indicator: str):
        """Create dynamic parameter controls with better layout and error handling"""
        try:
            print(f'🔧 Creating enhanced parameters for {indicator}')
            if not dpg.does_item_exist(f'dynamic_params_{self.tab_id}'):
                print(f'❌ Parent container dynamic_params_{self.tab_id} does not exist')
                return
            children = dpg.get_item_children(f'dynamic_params_{self.tab_id}', 1)
            if children:
                for child in children:
                    try:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
                    except Exception as e:
                        print(f'⚠️ Error deleting child item {child}: {e}')
            if indicator not in self.indicators:
                print(f'❌ Indicator {indicator} not found in indicators')
                return
            if dpg.does_item_exist(f'indicator_desc_{self.tab_id}'):
                desc = self.indicators[indicator].get('description', 'Economic data indicator')
                dpg.set_value(f'indicator_desc_{self.tab_id}', f'📝 {desc}')
            params = self.indicators[indicator]['params']
            filtered_params = [param for param in params if param != 'countries']
            if not filtered_params:
                dpg.add_text('No additional parameters required for this indicator', parent=f'dynamic_params_{self.tab_id}', color=[140, 140, 140])
                return
            param_count = 0
            current_row = None
            for param in filtered_params:
                try:
                    if param_count % 3 == 0:
                        current_row = dpg.add_group(horizontal=True, parent=f'dynamic_params_{self.tab_id}')
                        if not dpg.does_item_exist(current_row):
                            print(f'❌ Failed to create row group')
                            continue
                    param_group = dpg.add_group(horizontal=True, parent=current_row)
                    if not dpg.does_item_exist(param_group):
                        print(f'❌ Failed to create parameter group for {param}')
                        continue
                    label_text = f'{param.replace('_', ' ').title()}:'
                    dpg.add_text(label_text, parent=param_group)
                    param_tag = f'{param}_{self.tab_id}'
                    if param in self.param_options:
                        dpg.add_combo(self.param_options[param], tag=param_tag, default_value=self.param_options[param][0], width=130, parent=param_group)
                    elif param in ['harmonized', 'seasonal_adjustment', 'growth_rate']:
                        dpg.add_checkbox(tag=param_tag, default_value=False, parent=param_group)
                    else:
                        dpg.add_input_text(tag=param_tag, width=130, hint=f'Enter {param}', parent=param_group)
                    if param_count % 3 < 2 and param_count < len(filtered_params) - 1:
                        dpg.add_spacer(width=20, parent=current_row)
                    param_count += 1
                except Exception as param_error:
                    print(f'❌ Error creating control for parameter {param}: {param_error}')
                    continue
            print(f'✅ Enhanced parameters created for {indicator} ({param_count} parameters)')
        except Exception as e:
            error(f'Error creating parameter controls: {str(e)}', module='OECDDataTab')
            print(f'❌ Error creating parameters: {str(e)}')
            print(f'❌ Traceback: {traceback.format_exc()}')
            try:
                if dpg.does_item_exist(f'dynamic_params_{self.tab_id}'):
                    dpg.add_text(f'Error loading parameters for {indicator}', parent=f'dynamic_params_{self.tab_id}', color=[255, 100, 100])
            except Exception as fallback_error:
                print(f'❌ Even fallback failed: {fallback_error}')

    def on_indicator_change(self, sender, app_data):
        """Handle indicator selection change with enhanced feedback"""
        try:
            print(f'🔧 Indicator changed to: {app_data}')
            countries = self.get_countries_for_indicator(app_data)
            if dpg.does_item_exist(f'countries_{self.tab_id}'):
                dpg.configure_item(f'countries_{self.tab_id}', items=countries)
                if countries:
                    dpg.set_value(f'countries_{self.tab_id}', countries[0])
            self.create_parameter_controls(app_data)
            self.update_status('Indicator changed - ready for new data', [200, 200, 100])
        except Exception as e:
            error(f'Error in indicator change: {str(e)}', module='OECDDataTab')
            print(f'❌ Error in indicator change: {str(e)}')

    def on_chart_type_change(self, sender, app_data):
        """Handle chart type change"""
        try:
            if self.current_data:
                self.update_chart()
        except Exception as e:
            print(f'❌ Error in chart type change: {str(e)}')

    def fetch_data(self):
        """Fetch OECD data with enhanced error handling"""
        try:
            print('🔧 Starting enhanced data fetch...')
            if not self.oecd_provider:
                self.update_status('❌ OECD Provider not available', [255, 100, 100])
                return
            indicator = dpg.get_value(f'indicator_{self.tab_id}')
            if indicator not in self.indicators:
                self.update_status('❌ Invalid indicator selected', [255, 100, 100])
                return
            print(f'🔧 Fetching {indicator} data...')
            self.update_status('🔄 Fetching data from OECD...', [255, 255, 100])
            params = self.prepare_parameters(indicator)
            future = self.process_executor.submit(_fetch_data_in_process, self.indicators[indicator], params)
            monitor_thread = threading.Thread(target=self._monitor_fetch_completion, args=(future, indicator), daemon=True)
            monitor_thread.start()
        except Exception as e:
            error(f'Error fetching data: {str(e)}', module='OECDDataTab')
            print(f'❌ Error fetching data: {str(e)}')
            self.update_status(f'❌ Error: {str(e)}', [255, 100, 100])

    def refresh_data(self):
        """Refresh current data"""
        try:
            if self.current_data:
                self.fetch_data()
            else:
                self.update_status('⚠️ No data to refresh - fetch data first', [255, 200, 100])
        except Exception as e:
            print(f'❌ Error refreshing data: {str(e)}')

    def _monitor_fetch_completion(self, future: concurrent.futures.Future, indicator: str):
        """Enhanced monitoring with better error handling"""
        try:
            data = future.result(timeout=120)

            def update_ui():
                try:
                    if data.get('success'):
                        self.current_data = data
                        self.update_displays(data, indicator)
                        self.update_statistics(data)
                        data_count = len(data.get('data', []))
                        country = data.get('countries', 'Unknown')
                        freq = data.get('frequency', 'Unknown')
                        self.update_status(f'✅ Loaded {data_count} data points', [100, 255, 100])
                        self.update_data_summary(f'📊 {data_count} records • {country} • {freq} frequency')
                        self.last_refresh = datetime.now()
                        if dpg.does_item_exist(f'last_update_{self.tab_id}'):
                            dpg.set_value(f'last_update_{self.tab_id}', self.last_refresh.strftime('%Y-%m-%d %H:%M:%S'))
                            dpg.configure_item(f'last_update_{self.tab_id}', color=[100, 255, 100])
                    else:
                        error_msg = data.get('error', 'Unknown error occurred')
                        print(f'❌ Data fetch failed: {error_msg}')
                        self.update_status(f'❌ {error_msg}', [255, 100, 100])
                        self.update_data_summary('No data available')
                except Exception as ui_error:
                    print(f'❌ Error updating UI: {ui_error}')
                    self.update_status(f'❌ UI Error: {str(ui_error)}', [255, 100, 100])
            threading.Timer(0.1, update_ui).start()
        except concurrent.futures.TimeoutError:
            print('❌ Fetch operation timed out')

            def timeout_update():
                self.update_status('❌ Request timed out (120s)', [255, 100, 100])
            threading.Timer(0.1, timeout_update).start()
        except Exception as e:
            print(f'❌ Error in fetch monitoring: {str(e)}')

            def error_update():
                self.update_status(f'❌ Monitoring error: {str(e)}', [255, 100, 100])
            threading.Timer(0.1, error_update).start()

    def prepare_parameters(self, indicator: str) -> Dict[str, Any]:
        """Prepare API parameters with validation"""
        try:
            params = {}
            params['countries'] = dpg.get_value(f'countries_{self.tab_id}')
            start_date = dpg.get_value(f'start_date_{self.tab_id}')
            end_date = dpg.get_value(f'end_date_{self.tab_id}')
            if start_date and start_date.strip():
                params['start_date'] = start_date.strip()
            if end_date and end_date.strip():
                params['end_date'] = end_date.strip()
            for param in self.indicators[indicator]['params']:
                if param == 'countries':
                    continue
                param_tag = f'{param}_{self.tab_id}'
                if dpg.does_item_exist(param_tag):
                    value = dpg.get_value(param_tag)
                    if value is not None and (value != '' or isinstance(value, bool)):
                        params[param] = value
            return params
        except Exception as e:
            error(f'Error preparing parameters: {str(e)}', module='OECDDataTab')
            print(f'❌ Error preparing parameters: {str(e)}')
            return {'countries': 'united_states'}

    def update_displays(self, data: Dict[str, Any], indicator: str):
        """Update all display components with enhanced formatting"""
        try:
            print('🔧 Updating enhanced displays...')
            self.update_chart(data=data, indicator=indicator)
            self.update_table(data=data)
            self.update_raw_display(data)
            self.update_chart_info(data, indicator)
            print('✅ Enhanced displays updated')
        except Exception as e:
            error(f'Error updating displays: {str(e)}', module='OECDDataTab')
            print(f'❌ Error updating displays: {str(e)}')

    def update_chart(self, sender=None, app_data=None, data=None, indicator=None):
        """Update chart with enhanced formatting and proper axis labels"""
        try:
            if data is None:
                data = self.current_data
            if not data or 'data' not in data:
                print('❌ No data for chart')
                return
            chart_data = data['data']
            if not isinstance(chart_data, list) or not chart_data:
                print('❌ Invalid chart data')
                return
            print(f'🔧 Updating enhanced chart with {len(chart_data)} data points')
            if dpg.does_item_exist(f'y_axis_{self.tab_id}'):
                children = dpg.get_item_children(f'y_axis_{self.tab_id}', 1)
                if children:
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
            plot_data = []
            date_labels = []
            for item in chart_data:
                value = item.get('value')
                date_str = item.get('date', '')
                if value is not None and str(value).lower() != 'nan':
                    try:
                        float_value = float(value)
                        plot_data.append(float_value)
                        date_labels.append(date_str)
                    except (ValueError, TypeError):
                        continue
            if not plot_data:
                print('❌ No valid plot data')
                return
            x_values = list(range(len(plot_data)))
            y_values = plot_data
            chart_type = dpg.get_value(f'chart_type_{self.tab_id}') if dpg.does_item_exist(f'chart_type_{self.tab_id}') else 'Line'
            show_grid = dpg.get_value(f'show_grid_{self.tab_id}') if dpg.does_item_exist(f'show_grid_{self.tab_id}') else True
            country = data.get('countries', 'Data').replace('_', ' ').title()
            indicator_name = data.get('indicator', indicator or 'Economic Data').replace('_', ' ').title()
            frequency = data.get('frequency', '').title()
            series_label = f'{country} - {indicator_name}'
            if frequency:
                series_label += f' ({frequency})'
            if dpg.does_item_exist(f'x_axis_{self.tab_id}'):
                dpg.configure_item(f'x_axis_{self.tab_id}', label='Time Period')
            if dpg.does_item_exist(f'y_axis_{self.tab_id}'):
                current_indicator = dpg.get_value(f'indicator_{self.tab_id}') if dpg.does_item_exist(f'indicator_{self.tab_id}') else indicator
                params = self.prepare_parameters(current_indicator) if current_indicator else {}
                y_label = self.get_y_axis_label(current_indicator, params)
                dpg.configure_item(f'y_axis_{self.tab_id}', label=y_label)
            if chart_type == 'Line':
                dpg.add_line_series(x_values, y_values, label=series_label, parent=f'y_axis_{self.tab_id}')
            elif chart_type == 'Bar':
                dpg.add_bar_series(x_values, y_values, label=series_label, parent=f'y_axis_{self.tab_id}')
            elif chart_type == 'Scatter':
                dpg.add_scatter_series(x_values, y_values, label=series_label, parent=f'y_axis_{self.tab_id}')
            if dpg.does_item_exist(f'chart_plot_{self.tab_id}'):
                if show_grid:
                    pass
            auto_scale = dpg.get_value(f'auto_scale_{self.tab_id}') if dpg.does_item_exist(f'auto_scale_{self.tab_id}') else True
            if auto_scale:
                if dpg.does_item_exist(f'x_axis_{self.tab_id}'):
                    dpg.fit_axis_data(f'x_axis_{self.tab_id}')
                if dpg.does_item_exist(f'y_axis_{self.tab_id}'):
                    dpg.fit_axis_data(f'y_axis_{self.tab_id}')
            print('✅ Enhanced chart updated successfully')
        except Exception as e:
            error(f'Error updating chart: {str(e)}', module='OECDDataTab')
            print(f'❌ Error updating chart: {str(e)}')

    def update_chart_info(self, data: Dict[str, Any], indicator: str):
        """Update chart information panel"""
        try:
            if not dpg.does_item_exist(f'chart_info_{self.tab_id}'):
                return
            chart_data = data.get('data', [])
            if not chart_data:
                dpg.set_value(f'chart_info_{self.tab_id}', 'No data to display')
                return
            values = []
            for item in chart_data:
                try:
                    val = float(item.get('value'))
                    if str(val).lower() != 'nan':
                        values.append(val)
                except:
                    continue
            if values:
                info_text = f'Data Points: {len(values)} | Min: {self.format_number(min(values))} | Max: {self.format_number(max(values))} | Avg: {self.format_number(sum(values) / len(values))}'
                if len(chart_data) > 1:
                    date_range = f' | Period: {chart_data[0].get('date', 'N/A')} to {chart_data[-1].get('date', 'N/A')}'
                    info_text += date_range
                dpg.set_value(f'chart_info_{self.tab_id}', info_text)
            else:
                dpg.set_value(f'chart_info_{self.tab_id}', 'No valid numerical data found')
        except Exception as e:
            print(f'❌ Error updating chart info: {str(e)}')

    def update_table(self, sender=None, app_data=None, data=None):
        """Update data table with enhanced formatting and search"""
        try:
            if data is None:
                data = self.current_data
            if not data or 'data' not in data:
                return
            table_data = data['data']
            if not isinstance(table_data, list):
                return
            print(f'🔧 Updating enhanced table with {len(table_data)} rows')
            if dpg.does_item_exist(f'data_table_{self.tab_id}'):
                children = dpg.get_item_children(f'data_table_{self.tab_id}', 1)
                if children:
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
            search_term = ''
            if dpg.does_item_exist(f'table_search_{self.tab_id}'):
                search_term = dpg.get_value(f'table_search_{self.tab_id}').lower()
            filtered_data = table_data
            if search_term:
                filtered_data = []
                for item in table_data:
                    searchable_text = f'{item.get('country', '')} {item.get('date', '')} {item.get('value', '')}'.lower()
                    if search_term in searchable_text:
                        filtered_data.append(item)
            limit_str = dpg.get_value(f'table_limit_{self.tab_id}') if dpg.does_item_exist(f'table_limit_{self.tab_id}') else '50'
            limit = len(filtered_data) if limit_str == 'All' else min(int(limit_str), len(filtered_data))
            current_indicator = dpg.get_value(f'indicator_{self.tab_id}') if dpg.does_item_exist(f'indicator_{self.tab_id}') else ''
            params = self.prepare_parameters(current_indicator) if current_indicator else {}
            unit_type = params.get('units', params.get('transform', 'default'))
            for i in range(min(limit, len(filtered_data))):
                item = filtered_data[i]
                with dpg.table_row(parent=f'data_table_{self.tab_id}'):
                    date_str = str(item.get('date', 'N/A'))
                    dpg.add_text(date_str)
                    country_str = str(item.get('country', 'N/A')).replace('_', ' ').title()
                    dpg.add_text(country_str)
                    value = item.get('value')
                    formatted_value = self.format_number(value, unit_type)
                    dpg.add_text(formatted_value)
                    freq_str = str(item.get('FREQ', data.get('frequency', 'N/A'))).title()
                    dpg.add_text(freq_str)
                    indicator_str = str(data.get('indicator', 'N/A')).replace('_', ' ').title()
                    dpg.add_text(indicator_str)
            print('✅ Enhanced table updated successfully')
        except Exception as e:
            error(f'Error updating table: {str(e)}', module='OECDDataTab')
            print(f'❌ Error updating table: {str(e)}')

    def update_statistics(self, data: Dict[str, Any]):
        """Update statistics panel with comprehensive analysis"""
        try:
            if not dpg.does_item_exist(f'stats_display_{self.tab_id}'):
                return
            children = dpg.get_item_children(f'stats_display_{self.tab_id}', 1)
            if children:
                for child in children:
                    if dpg.does_item_exist(child):
                        dpg.delete_item(child)
            chart_data = data.get('data', [])
            if not chart_data:
                dpg.add_text('No data available for statistical analysis', color=[140, 140, 140], parent=f'stats_display_{self.tab_id}')
                return
            values = []
            for item in chart_data:
                try:
                    val = float(item.get('value'))
                    if str(val).lower() != 'nan':
                        values.append(val)
                except:
                    continue
            if not values:
                dpg.add_text('No valid numerical data for analysis', color=[140, 140, 140], parent=f'stats_display_{self.tab_id}')
                return
            n = len(values)
            mean_val = sum(values) / n
            sorted_values = sorted(values)
            median_val = sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val
            variance = sum(((x - mean_val) ** 2 for x in values)) / n
            std_dev = variance ** 0.5
            current_indicator = dpg.get_value(f'indicator_{self.tab_id}') if dpg.does_item_exist(f'indicator_{self.tab_id}') else ''
            params = self.prepare_parameters(current_indicator) if current_indicator else {}
            unit_type = params.get('units', params.get('transform', 'default'))
            with dpg.group(parent=f'stats_display_{self.tab_id}'):
                dpg.add_text('📊 Descriptive Statistics', color=[200, 200, 100])
                dpg.add_spacer(height=5)
                with dpg.table(header_row=True, borders_innerH=True, borders_innerV=True):
                    dpg.add_table_column(label='Statistic', width_fixed=True, init_width_or_weight=150)
                    dpg.add_table_column(label='Value', width_fixed=True, init_width_or_weight=200)
                    stats = [('Count', str(n)), ('Mean', self.format_number(mean_val, unit_type)), ('Median', self.format_number(median_val, unit_type)), ('Minimum', self.format_number(min_val, unit_type)), ('Maximum', self.format_number(max_val, unit_type)), ('Range', self.format_number(range_val, unit_type)), ('Std Deviation', self.format_number(std_dev, unit_type))]
                    for stat_name, stat_value in stats:
                        with dpg.table_row():
                            dpg.add_text(stat_name)
                            dpg.add_text(stat_value)
                dpg.add_spacer(height=10)
                dpg.add_text('📈 Trend Analysis', color=[200, 200, 100])
                dpg.add_spacer(height=5)
                if n > 1:
                    first_val = values[0]
                    last_val = values[-1]
                    change = last_val - first_val
                    change_pct = change / first_val * 100 if first_val != 0 else 0
                    trend_text = 'Increasing' if change > 0 else 'Decreasing' if change < 0 else 'Stable'
                    trend_color = [100, 255, 100] if change > 0 else [255, 100, 100] if change < 0 else [200, 200, 200]
                    dpg.add_text(f'Trend: {trend_text}', color=trend_color)
                    dpg.add_text(f'Total Change: {self.format_number(change, unit_type)}')
                    dpg.add_text(f'Percentage Change: {change_pct:.2f}%')
        except Exception as e:
            error(f'Error updating statistics: {str(e)}', module='OECDDataTab')
            print(f'❌ Error updating statistics: {str(e)}')

    def update_raw_display(self, data: Dict[str, Any]):
        """Update raw JSON display with better formatting"""
        try:
            formatted_json = json.dumps(data, indent=2, default=str)
            if dpg.does_item_exist(f'raw_display_{self.tab_id}'):
                dpg.set_value(f'raw_display_{self.tab_id}', formatted_json)
        except Exception as e:
            error(f'Error updating raw display: {str(e)}', module='OECDDataTab')

    def copy_raw_data(self):
        """Copy raw data to clipboard"""
        try:
            if self.current_data:
                formatted_json = json.dumps(self.current_data, indent=2, default=str)
                dpg.set_clipboard_text(formatted_json)
                self.update_status('📋 Data copied to clipboard', [100, 255, 100])
            else:
                self.update_status('⚠️ No data to copy', [255, 200, 100])
        except Exception as e:
            error(f'Error copying data: {str(e)}', module='OECDDataTab')

    def save_raw_data(self):
        """Save raw data to file"""
        try:
            if not self.current_data:
                self.update_status('⚠️ No data to save', [255, 200, 100])
                return
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            indicator = self.current_data.get('indicator', 'data')
            country = self.current_data.get('countries', 'unknown')
            filename = f'oecd_{indicator}_{country}_{timestamp}.json'
            with open(filename, 'w') as f:
                json.dump(self.current_data, f, indent=2, default=str)
            self.update_status(f'💾 Data saved to {filename}', [100, 255, 100])
        except Exception as e:
            error(f'Error saving data: {str(e)}', module='OECDDataTab')
            self.update_status(f'❌ Save error: {str(e)}', [255, 100, 100])

    def export_data(self):
        """Export data to CSV with enhanced formatting"""
        try:
            if not self.current_data or 'data' not in self.current_data:
                self.update_status('❌ No data to export', [255, 100, 100])
                return
            import csv
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            indicator = self.current_data.get('indicator', 'data')
            country = self.current_data.get('countries', 'unknown')
            filename = f'oecd_{indicator}_{country}_{timestamp}.csv'
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Date', 'Country', 'Value', 'Indicator', 'Frequency', 'Units', 'Source', 'Fetched_At'])
                units = self.current_data.get('units', 'N/A')
                frequency = self.current_data.get('frequency', 'N/A')
                indicator_name = self.current_data.get('indicator', 'N/A')
                fetched_at = self.current_data.get('fetched_at', 'N/A')
                for item in self.current_data['data']:
                    writer.writerow([item.get('date', ''), item.get('country', ''), item.get('value', ''), indicator_name, item.get('FREQ', frequency), units, 'OECD', fetched_at])
            self.update_status(f'📊 Exported to {filename}', [100, 255, 100])
        except Exception as e:
            error(f'Error exporting data: {str(e)}', module='OECDDataTab')
            self.update_status(f'❌ Export error: {str(e)}', [255, 100, 100])

    def clear_data(self):
        """Clear all data and displays"""
        try:
            print('🔧 Clearing all data...')
            self.current_data = {}
            if dpg.does_item_exist(f'y_axis_{self.tab_id}'):
                children = dpg.get_item_children(f'y_axis_{self.tab_id}', 1)
                if children:
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
            if dpg.does_item_exist(f'data_table_{self.tab_id}'):
                children = dpg.get_item_children(f'data_table_{self.tab_id}', 1)
                if children:
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
            if dpg.does_item_exist(f'stats_display_{self.tab_id}'):
                children = dpg.get_item_children(f'stats_display_{self.tab_id}', 1)
                if children:
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
                dpg.add_text('No data loaded for analysis...', color=[140, 140, 140], parent=f'stats_display_{self.tab_id}')
            if dpg.does_item_exist(f'raw_display_{self.tab_id}'):
                dpg.set_value(f'raw_display_{self.tab_id}', 'No data loaded...')
            if dpg.does_item_exist(f'chart_info_{self.tab_id}'):
                dpg.set_value(f'chart_info_{self.tab_id}', 'No chart data available')
            self.update_status('🧹 Data cleared', [200, 200, 200])
            self.update_data_summary('Ready for new data')
            if dpg.does_item_exist(f'last_update_{self.tab_id}'):
                dpg.set_value(f'last_update_{self.tab_id}', 'Not yet loaded')
                dpg.configure_item(f'last_update_{self.tab_id}', color=[120, 120, 120])
            print('✅ All data cleared successfully')
        except Exception as e:
            error(f'Error clearing data: {str(e)}', module='OECDDataTab')
            print(f'❌ Error clearing data: {str(e)}')

    def update_status(self, message: str, color: List[int]=None):
        """Update status message"""
        try:
            if color is None:
                color = [200, 200, 200]
            if dpg.does_item_exist(f'status_{self.tab_id}'):
                dpg.set_value(f'status_{self.tab_id}', message)
                dpg.configure_item(f'status_{self.tab_id}', color=color)
                print(f'📊 Status: {message}')
        except Exception as e:
            error(f'Error updating status: {str(e)}', module='OECDDataTab')
            print(f'❌ Error updating status: {str(e)}')

    def update_data_summary(self, summary: str):
        """Update data summary information"""
        try:
            if dpg.does_item_exist(f'data_summary_{self.tab_id}'):
                dpg.set_value(f'data_summary_{self.tab_id}', summary)
        except Exception as e:
            print(f'❌ Error updating data summary: {str(e)}')

    async def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
                print('✅ Thread pool shutdown completed')
            if hasattr(self, 'process_executor'):
                self.process_executor.shutdown(wait=True)
                print('✅ Process pool shutdown completed')
            if hasattr(self, 'oecd_provider') and self.oecd_provider:
                await self.oecd_provider.close()
                print('✅ OECD provider cleanup completed')
            self.current_data = {}
            print('✅ OECD cleanup completed')
        except Exception as e:
            error(f'Error during cleanup: {str(e)}', module='OECDDataTab')
            print(f'❌ Error during cleanup: {str(e)}')

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
            if hasattr(self, 'process_executor'):
                self.process_executor.shutdown(wait=False)
        except Exception:
            pass

def __del__(self):
    """Destructor to ensure cleanup"""
    try:
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        if hasattr(self, 'process_executor'):
            self.process_executor.shutdown(wait=False)
    except Exception:
        pass

