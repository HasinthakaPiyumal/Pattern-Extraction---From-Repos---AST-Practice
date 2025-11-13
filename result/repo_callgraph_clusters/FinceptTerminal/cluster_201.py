# Cluster 201

class DebugIMFGUI:

    def __init__(self):
        self.imf_wrapper = DebugIMFWrapper()
        self.current_data = None

    def setup_gui(self):
        dpg.create_context()
        with dpg.window(label='Debug IMF Data Terminal', tag='main_window'):
            with dpg.group(horizontal=True):
                dpg.add_text('IMF Data Provider (Debug Mode)')
                dpg.add_button(label='Test Connection', callback=self.test_connection)
                dpg.add_button(label='Clear Debug', callback=self.clear_debug)
            dpg.add_text('', tag='connection_status')
            dpg.add_separator()
            dpg.add_text('Direction of Trade Parameters:')
            with dpg.group(horizontal=True):
                dpg.add_text('Country:')
                dpg.add_input_text(tag='country', default_value='US', width=80)
                dpg.add_text('Counterpart:')
                dpg.add_input_text(tag='counterpart', default_value='CN', width=80)
            with dpg.group(horizontal=True):
                dpg.add_text('Direction:')
                dpg.add_combo(['exports', 'imports', 'balance'], tag='direction', default_value='exports', width=100)
                dpg.add_text('Frequency:')
                dpg.add_combo(['A', 'Q', 'M'], tag='frequency', default_value='A', width=60)
            with dpg.group(horizontal=True):
                dpg.add_text('Start Year:')
                dpg.add_input_text(tag='start_date', default_value='2022', width=80)
                dpg.add_text('End Year:')
                dpg.add_input_text(tag='end_date', default_value='2023', width=80)
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label='Get Trade Data', callback=self.get_trade_data)
                dpg.add_button(label='Export CSV', callback=self.export_csv)
                dpg.add_button(label='Clear Data', callback=self.clear_data)
            dpg.add_separator()
            dpg.add_text('Status:')
            dpg.add_text('', tag='status_text')
            dpg.add_separator()
            dpg.add_text('Debug Log:')
            dpg.add_input_text(tag='debug_log', multiline=True, height=200, width=750, readonly=True)
            dpg.add_separator()
            dpg.add_text('Data Preview:')
            with dpg.table(header_row=True, tag='data_table', height=200):
                pass
            dpg.add_text('Summary:')
            dpg.add_text('', tag='data_summary')
        dpg.create_viewport(title='Debug IMF Terminal', width=800, height=800)
        dpg.setup_dearpygui()
        dpg.set_primary_window('main_window', True)
        dpg.show_viewport()

    def clear_debug(self):
        self.imf_wrapper.debug_log = []
        dpg.set_value('debug_log', '')

    def update_debug_display(self):
        debug_text = self.imf_wrapper.get_debug_log()
        dpg.set_value('debug_log', debug_text)

    def test_connection(self):
        try:
            dpg.set_value('connection_status', 'Testing connection...')
            result = self.imf_wrapper.test_simple_connection()
            if result.success:
                dpg.set_value('connection_status', '✓ Connection successful')
            else:
                dpg.set_value('connection_status', f'✗ Connection failed: {result.error}')
            self.update_debug_display()
        except Exception as e:
            dpg.set_value('connection_status', f'✗ Test error: {str(e)}')
            self.update_debug_display()

    def get_trade_data(self):
        try:
            params = {'country': dpg.get_value('country'), 'counterpart': dpg.get_value('counterpart'), 'direction': dpg.get_value('direction'), 'frequency': dpg.get_value('frequency'), 'start_date': dpg.get_value('start_date'), 'end_date': dpg.get_value('end_date')}
            dpg.set_value('status_text', 'Fetching trade data...')
            result = self.imf_wrapper.get_direction_of_trade(**params)
            if result.success:
                self.current_data = result.data
                self._display_data(result.data)
                dpg.set_value('status_text', f'✓ {result.message}')
                self._update_summary(result.data)
            else:
                dpg.set_value('status_text', f'✗ {result.error}')
            self.update_debug_display()
        except Exception as e:
            dpg.set_value('status_text', f'✗ Error: {str(e)}')
            self.update_debug_display()

    def export_csv(self):
        if self.current_data is None:
            dpg.set_value('status_text', 'No data to export')
            return
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'imf_debug_{timestamp}.csv'
            self.current_data.to_csv(filename, index=False)
            dpg.set_value('status_text', f'✓ Exported to {filename}')
        except Exception as e:
            dpg.set_value('status_text', f'✗ Export error: {str(e)}')

    def clear_data(self):
        self.current_data = None
        dpg.delete_item('data_table', children_only=True)
        dpg.set_value('data_summary', '')
        dpg.set_value('status_text', 'Data cleared')

    def _display_data(self, df: pd.DataFrame):
        dpg.delete_item('data_table', children_only=True)
        if df is None or df.empty:
            return
        columns = list(df.columns)
        for col in columns:
            dpg.add_table_column(label=col, parent='data_table')
        display_df = df.head(20)
        for _, row in display_df.iterrows():
            with dpg.table_row(parent='data_table'):
                for col in columns:
                    value = str(row[col])
                    if len(value) > 15:
                        value = value[:12] + '...'
                    dpg.add_text(value)

    def _update_summary(self, df: pd.DataFrame):
        if df is None or df.empty:
            return
        summary = f'Rows: {len(df)}, Columns: {len(df.columns)}\n'
        summary += f'Columns: {', '.join(df.columns)}\n'
        if 'date' in df.columns:
            summary += f'Date range: {df['date'].min()} to {df['date'].max()}\n'
        if 'value' in df.columns:
            summary += f'Value range: {df['value'].min():.2f} to {df['value'].max():.2f}'
        dpg.set_value('data_summary', summary)

    def run(self):
        self.setup_gui()
        dpg.start_dearpygui()
        dpg.destroy_context()

def __init__(self):
    self.imf_wrapper = DebugIMFWrapper()
    self.current_data = None

