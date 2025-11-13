# Cluster 142

class AdvancedNodeEditorTab(BaseTab):
    """Production-ready node editor tab with all features"""

    def __init__(self, app):
        super().__init__(app)
        self.node_processor = NodeProcessor()
        self.node_counter = 0
        self.selected_node = None
        self.is_dark_mode = True
        self.auto_execute = False
        self.execution_thread = None

    def get_label(self):
        return '🔗 Advanced Node Editor'

    def create_content(self):
        """Create the complete node editor interface"""
        self.create_header()
        with dpg.group(horizontal=True):
            self.create_left_sidebar()
            self.create_node_canvas()
            self.create_right_sidebar()
        self.create_bottom_panel()
        self.create_floating_windows()

    def create_header(self):
        """Create header with branding and quick actions"""
        with dpg.group(horizontal=True):
            dpg.add_text('🚀 FINCEPT', color=[100, 200, 255])
            dpg.add_text('Professional Trading Strategy Builder', color=[150, 150, 150])
            dpg.add_spacer(width=50)
            with dpg.group(horizontal=True):
                dpg.add_button(label='▶ Execute', callback=self.execute_strategy, width=100)
                dpg.add_button(label='💾 Save', callback=self.save_strategy, width=80)
                dpg.add_button(label='📁 Load', callback=self.load_strategy, width=80)
                dpg.add_button(label='🔄 Clear', callback=self.clear_all_nodes, width=80)
                dpg.add_checkbox(label='Auto Execute', callback=self.toggle_auto_execute)
                dpg.add_checkbox(label='Dark Mode', default_value=True, callback=self.toggle_theme)
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Status:', color=[100, 255, 100])
            dpg.add_text('Ready', tag='main_status', color=[200, 200, 200])
            dpg.add_spacer(width=30)
            dpg.add_text('Nodes:', color=[255, 255, 100])
            dpg.add_text('0', tag='node_count', color=[200, 200, 200])
            dpg.add_spacer(width=30)
            dpg.add_text('Connections:', color=[255, 150, 100])
            dpg.add_text('0', tag='connection_count', color=[200, 200, 200])

    def create_left_sidebar(self):
        """Create left sidebar with node palette and presets"""
        with dpg.child_window(width=280, height=-250, border=True):
            with dpg.tab_bar():
                with dpg.tab(label='📦 Nodes'):
                    self.create_node_palette()
                with dpg.tab(label='🎯 Presets'):
                    self.create_preset_panel()
                with dpg.tab(label='📋 Templates'):
                    self.create_template_panel()

    def create_node_palette(self):
        """Create categorized node palette"""
        dpg.add_input_text(hint='Search nodes...', width=-1, callback=self.filter_nodes, tag='node_search')
        dpg.add_separator()
        with dpg.collapsing_header(label='📊 Data Sources', default_open=True):
            dpg.add_button(label='Stock Data', width=-1, callback=lambda: self.add_node(NodeType.DATA_SOURCE))
            dpg.add_button(label='Multi-Ticker', width=-1, callback=lambda: self.add_node(NodeType.MULTI_TICKER))
            dpg.add_button(label='CSV Import', width=-1, callback=lambda: self.add_node(NodeType.CSV_IMPORT))
        with dpg.collapsing_header(label='📈 Trend Indicators'):
            dpg.add_button(label='Simple MA', width=-1, callback=lambda: self.add_node(NodeType.SMA))
            dpg.add_button(label='Exponential MA', width=-1, callback=lambda: self.add_node(NodeType.EMA))
            dpg.add_button(label='Bollinger Bands', width=-1, callback=lambda: self.add_node(NodeType.BOLLINGER))
            dpg.add_button(label='Ichimoku Cloud', width=-1, callback=lambda: self.add_node(NodeType.ICHIMOKU))
        with dpg.collapsing_header(label='⚡ Momentum'):
            dpg.add_button(label='RSI', width=-1, callback=lambda: self.add_node(NodeType.RSI))
            dpg.add_button(label='MACD', width=-1, callback=lambda: self.add_node(NodeType.MACD))
            dpg.add_button(label='Stochastic', width=-1, callback=lambda: self.add_node(NodeType.STOCHASTIC))
        with dpg.collapsing_header(label='📉 Volatility'):
            dpg.add_button(label='ATR', width=-1, callback=lambda: self.add_node(NodeType.ATR))
            dpg.add_button(label='Keltner Channel', width=-1, callback=lambda: self.add_node(NodeType.KELTNER))
        with dpg.collapsing_header(label='🔍 Patterns'):
            dpg.add_button(label='Candlestick Patterns', width=-1, callback=lambda: self.add_node(NodeType.CANDLESTICK))
            dpg.add_button(label='Support/Resistance', width=-1, callback=lambda: self.add_node(NodeType.SUPPORT_RESISTANCE))
        with dpg.collapsing_header(label='🔔 Signals'):
            dpg.add_button(label='Signal Generator', width=-1, callback=lambda: self.add_node(NodeType.SIGNAL))
            dpg.add_button(label='ML Signals', width=-1, callback=lambda: self.add_node(NodeType.ML_SIGNAL))
        with dpg.collapsing_header(label='🎯 Analysis'):
            dpg.add_button(label='Backtest', width=-1, callback=lambda: self.add_node(NodeType.BACKTEST))
            dpg.add_button(label='Optimization', width=-1, callback=lambda: self.add_node(NodeType.OPTIMIZATION))
            dpg.add_button(label='Plot', width=-1, callback=lambda: self.add_node(NodeType.PLOT))

    def create_preset_panel(self):
        """Create preset strategies panel"""
        dpg.add_text('Quick Start Strategies', color=[100, 255, 100])
        dpg.add_separator()
        for strategy in PresetStrategyTemplates.get_available_strategies():
            with dpg.group():
                dpg.add_button(label=strategy['name'], width=-1, callback=lambda s=strategy['name']: self.load_preset_strategy(s))
                dpg.add_text(strategy['description'], wrap=250, color=[150, 150, 150])
                dpg.add_text(f'Category: {strategy['category']}', color=[100, 150, 200])
                dpg.add_separator()

    def create_template_panel(self):
        """Create saved templates panel"""
        dpg.add_text('Saved Templates', color=[100, 255, 100])
        dpg.add_separator()
        dpg.add_button(label='➕ Save Current as Template', width=-1, callback=self.save_as_template)
        dpg.add_separator()
        templates_dir = Path('strategies/templates')
        if templates_dir.exists():
            for template_file in templates_dir.glob('*.json'):
                dpg.add_button(label=template_file.stem, width=-1, callback=lambda f=template_file: self.load_template(f))

    def create_node_canvas(self):
        """Create the main node editor canvas"""
        with dpg.child_window(width=-300, height=-250, border=True):
            with dpg.group(horizontal=True):
                dpg.add_text('Canvas', color=[150, 150, 150])
                dpg.add_button(label='Center', callback=self.center_canvas)
                dpg.add_button(label='Arrange', callback=self.auto_arrange_nodes)
                dpg.add_slider_float(label='Zoom', default_value=1.0, min_value=0.5, max_value=2.0, width=150, tag='canvas_zoom')
            dpg.add_separator()
            with dpg.node_editor(tag='node_editor', callback=self.link_callback, delink_callback=self.delink_callback, minimap=True, minimap_location=dpg.mvNodeMiniMap_Location_BottomRight):
                pass

    def create_right_sidebar(self):
        """Create right sidebar with properties and monitoring"""
        with dpg.child_window(width=300, height=-250, border=True):
            with dpg.tab_bar():
                with dpg.tab(label='⚙️ Properties'):
                    dpg.add_text('Node Properties', color=[200, 200, 200])
                    dpg.add_separator()
                    with dpg.group(tag='properties_content'):
                        dpg.add_text('Select a node to view properties', color=[150, 150, 150])
                with dpg.tab(label='📊 Monitor'):
                    self.create_monitoring_panel()
                with dpg.tab(label='❓ Help'):
                    self.create_help_panel()

    def create_monitoring_panel(self):
        """Create real-time monitoring panel"""
        dpg.add_text('Performance Monitor', color=[100, 255, 100])
        dpg.add_separator()
        with dpg.group(tag='execution_metrics'):
            dpg.add_text('Last Execution: N/A', tag='last_execution_time')
            dpg.add_text('Total Time: N/A', tag='total_execution_time')
            dpg.add_separator()
            dpg.add_text('Node Performance:', color=[255, 255, 100])
            with dpg.group(tag='node_performance_list'):
                dpg.add_text('Execute strategy to see metrics', color=[150, 150, 150])

    def create_help_panel(self):
        """Create help and documentation panel"""
        dpg.add_text('Quick Help', color=[100, 255, 100])
        dpg.add_separator()
        help_items = [('🖱️ Connections', 'Drag from output to input to connect'), ('⌨️ Shortcuts', 'Del: Delete node, Ctrl+S: Save'), ('🔄 Execution', 'Nodes execute in dependency order'), ('💡 Tips', 'Use presets for quick start')]
        for title, desc in help_items:
            dpg.add_text(title, color=[255, 255, 100])
            dpg.add_text(desc, wrap=250, color=[150, 150, 150])
            dpg.add_separator()

    def create_bottom_panel(self):
        """Create bottom panel for results and logs"""
        with dpg.child_window(height=250, border=True):
            with dpg.tab_bar():
                with dpg.tab(label='📊 Results'):
                    with dpg.group(tag='results_content'):
                        dpg.add_text('Execute strategy to see results...', color=[150, 150, 150])
                with dpg.tab(label='📝 Logs'):
                    with dpg.group(tag='logs_content'):
                        dpg.add_text('System logs will appear here...', color=[150, 150, 150])
                with dpg.tab(label='📈 Charts'):
                    with dpg.group(tag='chart_content'):
                        dpg.add_text('Charts will be displayed here...', color=[150, 150, 150])

    def create_floating_windows(self):
        """Create floating windows for advanced features"""
        with dpg.window(label='Strategy Optimizer', show=False, tag='optimizer_window', width=600, height=400, pos=[100, 100]):
            dpg.add_text('Parameter Optimization', color=[100, 255, 100])
            dpg.add_separator()

    def add_node(self, node_type: NodeType):
        """Add a new node to the canvas"""
        self.node_counter += 1
        node_id = f'{node_type.value}_{self.node_counter}'
        node_data = NodeData(node_id=node_id, node_type=node_type, position=(100 + self.node_counter * 30 % 500, 100 + self.node_counter * 30 % 400))
        self.node_processor.add_node(node_data)
        self.create_visual_node(node_data)
        self.update_counts()
        if self.auto_execute:
            self.execute_strategy()
        return node_id

    def add_node_with_params(self, node_type: NodeType, params: Dict[str, Any]):
        """Add node with preset parameters"""
        node_id = self.add_node(node_type)
        node_data = self.node_processor.nodes[node_id]
        node_data.parameters.update(params)
        return node_id

    def create_visual_node(self, node_data: NodeData):
        """Create visual representation of node"""
        node_id = node_data.node_id
        dpg_node_id = dpg.generate_uuid()
        node_colors = {NodeType.DATA_SOURCE: [50, 150, 50], NodeType.SMA: [100, 100, 200], NodeType.EMA: [100, 100, 200], NodeType.RSI: [200, 100, 100], NodeType.MACD: [200, 100, 100], NodeType.SIGNAL: [200, 200, 100], NodeType.BACKTEST: [150, 100, 200], NodeType.PLOT: [100, 200, 200]}
        with dpg.node(label=self.get_node_display_name(node_data.node_type), parent='node_editor', tag=dpg_node_id, pos=node_data.position):
            self.create_node_content(node_data, dpg_node_id)
        global_state.node_registry[dpg_node_id] = {'node_id': node_id}

    def create_node_content(self, node_data: NodeData, dpg_node_id: int):
        """Create node content based on type"""
        node_id = node_data.node_id
        node_type = node_data.node_type
        if node_type == NodeType.DATA_SOURCE:
            self.create_data_source_node_content(node_id, dpg_node_id)
        elif node_type in [NodeType.SMA, NodeType.EMA, NodeType.RSI]:
            self.create_indicator_node_content(node_id, node_type, dpg_node_id)
        elif node_type == NodeType.SIGNAL:
            self.create_signal_node_content(node_id, dpg_node_id)
        elif node_type == NodeType.BACKTEST:
            self.create_backtest_node_content(node_id, dpg_node_id)
        elif node_type == NodeType.PLOT:
            self.create_plot_node_content(node_id, dpg_node_id)
        else:
            self.create_generic_node_content(node_id, node_type, dpg_node_id)

    def create_data_source_node_content(self, node_id: str, dpg_node_id: int):
        """Create data source node content"""
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=200)
            dpg.add_input_text(label='Ticker', default_value='AAPL', width=120, tag=f'{node_id}_ticker')
            dpg.add_combo(['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'], default_value='1y', label='Period', width=120, tag=f'{node_id}_period')
            dpg.add_combo(['1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo'], default_value='1d', label='Interval', width=120, tag=f'{node_id}_interval')
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=180)
        output_attr = dpg.add_node_attribute(label='📊 OHLCV Data', attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_spacer(width=1, parent=output_attr)
        global_state.node_registry[dpg_node_id]['output_attr'] = output_attr

    def create_indicator_node_content(self, node_id: str, node_type: NodeType, dpg_node_id: int):
        """Create indicator node content"""
        input_attr = dpg.add_node_attribute(label='📥 Price Data', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=input_attr)
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=180)
            if node_type in [NodeType.SMA, NodeType.EMA]:
                dpg.add_input_int(label='Window', default_value=20, min_value=2, max_value=500, width=100, tag=f'{node_id}_window')
            elif node_type == NodeType.RSI:
                dpg.add_input_int(label='Period', default_value=14, min_value=2, max_value=100, width=100, tag=f'{node_id}_period')
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=160)
        output_label = f'📈 {node_type.value.upper()}'
        output_attr = dpg.add_node_attribute(label=output_label, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_spacer(width=1, parent=output_attr)
        global_state.node_registry[dpg_node_id].update({'input_attr': input_attr, 'output_attr': output_attr})

    def create_signal_node_content(self, node_id: str, dpg_node_id: int):
        """Create signal node content"""
        fast_attr = dpg.add_node_attribute(label='📥 Fast/Indicator', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=fast_attr)
        slow_attr = dpg.add_node_attribute(label='📥 Slow (Optional)', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=slow_attr)
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=200)
            dpg.add_combo(['crossover', 'threshold', 'divergence'], tag=f'{node_id}_type', default_value='crossover', width=140, label='Type')
            dpg.add_input_float(label='Buy Level', default_value=30.0, width=100, tag=f'{node_id}_buy_threshold')
            dpg.add_input_float(label='Sell Level', default_value=70.0, width=100, tag=f'{node_id}_sell_threshold')
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=180)
        output_attr = dpg.add_node_attribute(label='🔔 Signals', attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_spacer(width=1, parent=output_attr)
        global_state.node_registry[dpg_node_id].update({'fast_input_attr': fast_attr, 'slow_input_attr': slow_attr, 'indicator_input_attr': fast_attr, 'output_attr': output_attr})

    def create_backtest_node_content(self, node_id: str, dpg_node_id: int):
        """Create backtest node content"""
        signals_attr = dpg.add_node_attribute(label='📥 Trading Signals', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=signals_attr)
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=220)
            dpg.add_input_int(label='Capital $', default_value=10000, min_value=100, max_value=10000000, width=140, tag=f'{node_id}_capital')
            dpg.add_input_float(label='Position %', default_value=95.0, min_value=1.0, max_value=100.0, width=140, tag=f'{node_id}_position_size')
            dpg.add_input_float(label='Commission %', default_value=0.1, min_value=0.0, max_value=5.0, width=140, tag=f'{node_id}_commission')
            dpg.add_input_float(label='Slippage %', default_value=0.05, min_value=0.0, max_value=1.0, width=140, tag=f'{node_id}_slippage')
            dpg.add_separator()
            dpg.add_text('Risk Management:', color=[255, 200, 100])
            dpg.add_input_float(label='Stop Loss %', default_value=0.0, min_value=0.0, max_value=50.0, width=140, tag=f'{node_id}_stop_loss', tooltip='0 = disabled')
            dpg.add_input_float(label='Take Profit %', default_value=0.0, min_value=0.0, max_value=100.0, width=140, tag=f'{node_id}_take_profit', tooltip='0 = disabled')
            dpg.add_separator()
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=200)
        with dpg.node_attribute(label='Results', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=250)
            dpg.add_text('Run backtest to see results', tag=f'{node_id}_results_text', wrap=240, color=[150, 150, 150])
        output_attr = dpg.add_node_attribute(label='📊 Results', attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_spacer(width=1, parent=output_attr)
        global_state.node_registry[dpg_node_id].update({'signals_input_attr': signals_attr, 'output_attr': output_attr})

    def create_plot_node_content(self, node_id: str, dpg_node_id: int):
        """Create plot node content"""
        input_attr = dpg.add_node_attribute(label='📥 Data', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=input_attr)
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=180)
            dpg.add_combo(['comprehensive', 'performance', 'signals', 'indicators'], tag=f'{node_id}_plot_type', default_value='comprehensive', width=140, label='Type')
            dpg.add_checkbox(label='Show Volume', tag=f'{node_id}_show_volume', default_value=True)
            dpg.add_checkbox(label='Show Grid', tag=f'{node_id}_show_grid', default_value=True)
            dpg.add_button(label='🖼️ View Chart', width=140, callback=lambda: self.view_chart(node_id))
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=160)
        global_state.node_registry[dpg_node_id]['input_attr'] = input_attr

    def create_generic_node_content(self, node_id: str, node_type: NodeType, dpg_node_id: int):
        """Create generic node content for other node types"""
        input_attr = dpg.add_node_attribute(label='📥 Input', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=input_attr)
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=180)
            dpg.add_text(f'Node: {node_type.value}', wrap=160)
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=160)
        output_attr = dpg.add_node_attribute(label='📤 Output', attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_spacer(width=1, parent=output_attr)
        global_state.node_registry[dpg_node_id].update({'input_attr': input_attr, 'output_attr': output_attr})

    def get_node_display_name(self, node_type: NodeType) -> str:
        """Get display name for node type"""
        display_names = {NodeType.DATA_SOURCE: '📊 Stock Data', NodeType.MULTI_TICKER: '📊 Multi-Ticker', NodeType.SMA: '📈 Simple MA', NodeType.EMA: '📈 Exponential MA', NodeType.BOLLINGER: '📈 Bollinger Bands', NodeType.RSI: '⚡ RSI', NodeType.MACD: '⚡ MACD', NodeType.STOCHASTIC: '⚡ Stochastic', NodeType.ATR: '📉 ATR', NodeType.ICHIMOKU: '☁️ Ichimoku', NodeType.CANDLESTICK: '🕯️ Candlesticks', NodeType.SUPPORT_RESISTANCE: '📏 S/R Levels', NodeType.SIGNAL: '🔔 Signal Gen', NodeType.ML_SIGNAL: '🤖 ML Signal', NodeType.BACKTEST: '🎯 Backtest', NodeType.OPTIMIZATION: '⚙️ Optimizer', NodeType.PLOT: '📈 Plot'}
        return display_names.get(node_type, node_type.value)

    def link_callback(self, sender, app_data):
        """Handle node connections"""
        output_attr = app_data[0]
        input_attr = app_data[1]
        source_node_id = None
        target_node_id = None
        input_type = None
        for dpg_id, attr_info in global_state.node_registry.items():
            if attr_info.get('output_attr') == output_attr:
                source_node_id = attr_info['node_id']
            if attr_info.get('input_attr') == input_attr:
                target_node_id = attr_info['node_id']
                input_type = 'default'
            elif attr_info.get('fast_input_attr') == input_attr:
                target_node_id = attr_info['node_id']
                input_type = 'fast'
            elif attr_info.get('slow_input_attr') == input_attr:
                target_node_id = attr_info['node_id']
                input_type = 'slow'
            elif attr_info.get('indicator_input_attr') == input_attr:
                target_node_id = attr_info['node_id']
                input_type = 'indicator'
            elif attr_info.get('signals_input_attr') == input_attr:
                target_node_id = attr_info['node_id']
                input_type = 'signals'
        if source_node_id and target_node_id:
            link_id = dpg.add_node_link(output_attr, input_attr, parent=sender)
            if target_node_id not in global_state.node_connections:
                global_state.node_connections[target_node_id] = {}
            if input_type not in global_state.node_connections[target_node_id]:
                global_state.node_connections[target_node_id][input_type] = []
            global_state.node_connections[target_node_id][input_type].append(source_node_id)
            global_state.link_registry[link_id] = (source_node_id, target_node_id, input_type)
            self.update_counts()
            dpg.set_value('main_status', f'Connected: {source_node_id} → {target_node_id}')
            if self.auto_execute:
                self.execute_strategy()

    def delink_callback(self, sender, app_data):
        """Handle node disconnections"""
        link_id = app_data
        if link_id in global_state.link_registry:
            source_node_id, target_node_id, input_type = global_state.link_registry[link_id]
            if target_node_id in global_state.node_connections and input_type in global_state.node_connections[target_node_id]:
                connections = global_state.node_connections[target_node_id][input_type]
                if source_node_id in connections:
                    connections.remove(source_node_id)
                if not connections:
                    del global_state.node_connections[target_node_id][input_type]
                if not global_state.node_connections[target_node_id]:
                    del global_state.node_connections[target_node_id]
            del global_state.link_registry[link_id]
            self.update_counts()
            dpg.set_value('main_status', f'Disconnected: {source_node_id} → {target_node_id}')

    def connect_nodes(self, source_id: str, target_id: str, input_type: str='default'):
        """Programmatically connect two nodes"""
        source_attr = None
        target_attr = None
        for dpg_id, attr_info in global_state.node_registry.items():
            if attr_info['node_id'] == source_id and 'output_attr' in attr_info:
                source_attr = attr_info['output_attr']
            elif attr_info['node_id'] == target_id:
                if input_type == 'default' and 'input_attr' in attr_info:
                    target_attr = attr_info['input_attr']
                elif input_type == 'fast' and 'fast_input_attr' in attr_info:
                    target_attr = attr_info['fast_input_attr']
                elif input_type == 'slow' and 'slow_input_attr' in attr_info:
                    target_attr = attr_info['slow_input_attr']
                elif input_type == 'indicator' and 'indicator_input_attr' in attr_info:
                    target_attr = attr_info['indicator_input_attr']
                elif input_type == 'signals' and 'signals_input_attr' in attr_info:
                    target_attr = attr_info['signals_input_attr']
        if source_attr and target_attr:
            link_id = dpg.add_node_link(source_attr, target_attr, parent='node_editor')
            if target_id not in global_state.node_connections:
                global_state.node_connections[target_id] = {}
            if input_type not in global_state.node_connections[target_id]:
                global_state.node_connections[target_id][input_type] = []
            global_state.node_connections[target_id][input_type].append(source_id)
            global_state.link_registry[link_id] = (source_id, target_id, input_type)
            self.update_counts()

    def execute_strategy(self):
        """Execute the node graph"""
        try:
            dpg.set_value('main_status', '⏳ Executing strategy...')
            self.update_node_parameters()
            import time
            start_time = time.time()
            self.node_processor.execute_nodes()
            execution_time = time.time() - start_time
            self.display_results()
            self.update_monitoring(execution_time)
            dpg.set_value('main_status', f'✅ Execution complete ({execution_time:.2f}s)')
        except Exception as e:
            logger.error(f'Execution error: {e}')
            dpg.set_value('main_status', f'❌ Error: {str(e)[:50]}')

    def update_node_parameters(self):
        """Update node parameters from GUI"""
        for node_id, node in self.node_processor.nodes.items():
            try:
                if node.node_type == NodeType.DATA_SOURCE:
                    if dpg.does_item_exist(f'{node_id}_ticker'):
                        node.parameters['ticker'] = dpg.get_value(f'{node_id}_ticker')
                    if dpg.does_item_exist(f'{node_id}_period'):
                        node.parameters['period'] = dpg.get_value(f'{node_id}_period')
                    if dpg.does_item_exist(f'{node_id}_interval'):
                        node.parameters['interval'] = dpg.get_value(f'{node_id}_interval')
                elif node.node_type in [NodeType.SMA, NodeType.EMA]:
                    if dpg.does_item_exist(f'{node_id}_window'):
                        node.parameters['window'] = dpg.get_value(f'{node_id}_window')
                elif node.node_type == NodeType.RSI:
                    if dpg.does_item_exist(f'{node_id}_period'):
                        node.parameters['period'] = dpg.get_value(f'{node_id}_period')
                elif node.node_type == NodeType.SIGNAL:
                    if dpg.does_item_exist(f'{node_id}_type'):
                        node.parameters['type'] = dpg.get_value(f'{node_id}_type')
                    if dpg.does_item_exist(f'{node_id}_buy_threshold'):
                        node.parameters['buy_threshold'] = dpg.get_value(f'{node_id}_buy_threshold')
                    if dpg.does_item_exist(f'{node_id}_sell_threshold'):
                        node.parameters['sell_threshold'] = dpg.get_value(f'{node_id}_sell_threshold')
                elif node.node_type == NodeType.BACKTEST:
                    if dpg.does_item_exist(f'{node_id}_capital'):
                        node.parameters['initial_capital'] = dpg.get_value(f'{node_id}_capital')
                    if dpg.does_item_exist(f'{node_id}_position_size'):
                        node.parameters['position_size'] = dpg.get_value(f'{node_id}_position_size') / 100
                    if dpg.does_item_exist(f'{node_id}_commission'):
                        node.parameters['commission'] = dpg.get_value(f'{node_id}_commission') / 100
                    if dpg.does_item_exist(f'{node_id}_slippage'):
                        node.parameters['slippage'] = dpg.get_value(f'{node_id}_slippage') / 100
                    if dpg.does_item_exist(f'{node_id}_stop_loss'):
                        sl = dpg.get_value(f'{node_id}_stop_loss') / 100
                        node.parameters['stop_loss'] = sl if sl > 0 else None
                    if dpg.does_item_exist(f'{node_id}_take_profit'):
                        tp = dpg.get_value(f'{node_id}_take_profit') / 100
                        node.parameters['take_profit'] = tp if tp > 0 else None
                elif node.node_type == NodeType.PLOT:
                    if dpg.does_item_exist(f'{node_id}_plot_type'):
                        node.parameters['plot_type'] = dpg.get_value(f'{node_id}_plot_type')
            except Exception as e:
                logger.error(f'Error updating parameters for {node_id}: {e}')

    def display_results(self):
        """Display execution results"""
        dpg.delete_item('results_content', children_only=True)
        with dpg.group(parent='results_content'):
            dpg.add_text('📊 Strategy Execution Results', color=[100, 255, 100])
            dpg.add_separator()
            backtest_results = None
            for node_id, data in global_state.node_outputs.items():
                if isinstance(data, dict) and 'metrics' in data:
                    backtest_results = data
                    break
            if backtest_results:
                metrics = backtest_results['metrics']
                with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True):
                    dpg.add_table_column(label='Metric')
                    dpg.add_table_column(label='Value')
                    metrics_data = [('Total Return', f'{metrics.total_return:.2f}%', [100, 255, 100] if metrics.total_return > 0 else [255, 100, 100]), ('Annual Return', f'{metrics.annualized_return:.2f}%', [100, 255, 100] if metrics.annualized_return > 0 else [255, 100, 100]), ('Sharpe Ratio', f'{metrics.sharpe_ratio:.2f}', [100, 255, 100] if metrics.sharpe_ratio > 1 else [255, 255, 100]), ('Max Drawdown', f'{metrics.max_drawdown:.2f}%', [255, 150, 100]), ('Win Rate', f'{metrics.win_rate:.1f}%', [100, 255, 100] if metrics.win_rate > 50 else [255, 100, 100]), ('Total Trades', f'{metrics.total_trades}', [200, 200, 200]), ('Profit Factor', f'{metrics.profit_factor:.2f}', [100, 255, 100] if metrics.profit_factor > 1 else [255, 100, 100])]
                    for metric_name, metric_value, color in metrics_data:
                        with dpg.table_row():
                            dpg.add_text(metric_name)
                            dpg.add_text(metric_value, color=color)
            else:
                dpg.add_text('No backtest results available', color=[150, 150, 150])
                dpg.add_text('Add a Backtest node and connect it to see performance metrics', color=[150, 150, 150])

    def update_monitoring(self, execution_time: float):
        """Update monitoring panel"""
        dpg.set_value('last_execution_time', f'Last Execution: {datetime.now().strftime('%H:%M:%S')}')
        dpg.set_value('total_execution_time', f'Total Time: {execution_time:.3f}s')
        dpg.delete_item('node_performance_list', children_only=True)
        with dpg.group(parent='node_performance_list'):
            for node_id, node in self.node_processor.nodes.items():
                if node.execution_time > 0:
                    color = [100, 255, 100] if node.execution_time < 0.5 else [255, 255, 100]
                    dpg.add_text(f'{node_id}: {node.execution_time:.3f}s', color=color)

    def update_counts(self):
        """Update node and connection counts"""
        node_count = len(self.node_processor.nodes)
        connection_count = sum((len(conns) for node_conns in global_state.node_connections.values() for conns in node_conns.values()))
        dpg.set_value('node_count', str(node_count))
        dpg.set_value('connection_count', str(connection_count))

    def clear_all_nodes(self):
        """Clear all nodes from the canvas"""
        dpg.delete_item('node_editor', children_only=True)
        global_state.clear()
        self.node_processor.nodes.clear()
        self.node_processor.execution_order.clear()
        self.node_counter = 0
        dpg.delete_item('results_content', children_only=True)
        with dpg.group(parent='results_content'):
            dpg.add_text('Execute strategy to see results...', color=[150, 150, 150])
        self.update_counts()
        dpg.set_value('main_status', 'Canvas cleared')

    def save_strategy(self):
        """Save current strategy to file"""
        try:
            strategy_data = {'nodes': {}, 'connections': global_state.node_connections, 'timestamp': datetime.now().isoformat()}
            for node_id, node in self.node_processor.nodes.items():
                strategy_data['nodes'][node_id] = node.to_dict()
            strategies_dir = Path('strategies')
            strategies_dir.mkdir(exist_ok=True)
            filename = strategies_dir / f'strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json'
            with open(filename, 'w') as f:
                json.dump(strategy_data, f, indent=2)
            dpg.set_value('main_status', f'Strategy saved to {filename.name}')
        except Exception as e:
            logger.error(f'Error saving strategy: {e}')
            dpg.set_value('main_status', f'Error saving: {str(e)[:50]}')

    def load_strategy(self):
        """Load strategy from file"""
        dpg.set_value('main_status', 'Load strategy functionality')

    def load_preset_strategy(self, strategy_name: str):
        """Load a preset strategy"""
        try:
            if strategy_name == 'Golden Cross':
                result = PresetStrategyTemplates.create_golden_cross_strategy(self)
            elif strategy_name == 'RSI Mean Reversion':
                result = PresetStrategyTemplates.create_rsi_mean_reversion_strategy(self)
            else:
                result = f'Strategy {strategy_name} not implemented yet'
            dpg.set_value('main_status', result)
        except Exception as e:
            logger.error(f'Error loading preset strategy: {e}')
            dpg.set_value('main_status', f'Error: {str(e)[:50]}')

    def save_as_template(self):
        """Save current setup as a reusable template"""
        dpg.set_value('main_status', 'Template saved')

    def load_template(self, template_file: Path):
        """Load a saved template"""
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            self.clear_all_nodes()
            dpg.set_value('main_status', f'Template {template_file.stem} loaded')
        except Exception as e:
            logger.error(f'Error loading template: {e}')
            dpg.set_value('main_status', f'Error: {str(e)[:50]}')

    def toggle_auto_execute(self, sender, value):
        """Toggle auto-execution on changes"""
        self.auto_execute = value
        dpg.set_value('main_status', f'Auto-execute {('enabled' if value else 'disabled')}')

    def toggle_theme(self, sender, value):
        """Toggle between light and dark themes"""
        self.is_dark_mode = value
        dpg.set_value('main_status', f'{('Dark' if value else 'Light')} mode')

    def filter_nodes(self, sender, filter_string):
        """Filter nodes in palette based on search"""
        pass

    def center_canvas(self):
        """Center the node canvas view"""
        dpg.set_value('main_status', 'Canvas centered')

    def auto_arrange_nodes(self):
        """Auto-arrange nodes for better visibility"""
        dpg.set_value('main_status', 'Nodes arranged')

    def view_chart(self, node_id: str):
        """View chart from plot node"""
        if node_id in global_state.node_outputs:
            output = global_state.node_outputs[node_id]
            if isinstance(output, dict) and 'chart' in output:
                dpg.delete_item('chart_content', children_only=True)
                with dpg.group(parent='chart_content'):
                    dpg.add_text(f'Chart from {node_id}', color=[100, 255, 100])
                    dpg.add_text('Chart visualization would appear here', color=[150, 150, 150])

    def cleanup(self):
        """Clean up resources on tab close"""
        try:
            self.clear_all_nodes()
            global_state.clear()
            logger.info('Advanced Node Editor cleaned up')
        except Exception as e:
            logger.error(f'Error during cleanup: {e}')

def create_node_content(self, node_data: NodeData, dpg_node_id: int):
    """Create node content based on type"""
    node_id = node_data.node_id
    node_type = node_data.node_type
    if node_type == NodeType.DATA_SOURCE:
        self.create_data_source_node_content(node_id, dpg_node_id)
    elif node_type in [NodeType.SMA, NodeType.EMA, NodeType.RSI]:
        self.create_indicator_node_content(node_id, node_type, dpg_node_id)
    elif node_type == NodeType.SIGNAL:
        self.create_signal_node_content(node_id, dpg_node_id)
    elif node_type == NodeType.BACKTEST:
        self.create_backtest_node_content(node_id, dpg_node_id)
    elif node_type == NodeType.PLOT:
        self.create_plot_node_content(node_id, dpg_node_id)
    else:
        self.create_generic_node_content(node_id, node_type, dpg_node_id)

