# Cluster 2

def deserialize_bytesio(obj):
    if isinstance(obj, dict) and '_type' in obj and (obj['_type'] == 'BytesIO'):
        return BytesIO(base64.b64decode(obj['data']))
    return obj

def safe_process_message(web_scraper_chat, message):
    if message is None or message.strip() == '':
        return "I'm sorry, but I didn't receive any input. Could you please try again?"
    try:
        progress_placeholder = st.empty()
        progress_placeholder.text('Initializing scraper...')
        start_time = time.time()
        response = web_scraper_chat.process_message(message)
        end_time = time.time()
        progress_placeholder.text(f'Scraping completed in {end_time - start_time:.2f} seconds.')
        st.write('Debug: Response type:', type(response))
        if isinstance(response, str):
            if 'Error:' in response:
                st.error(response)
            else:
                st.write('Debug: Response content:', response[:500] + '...' if len(response) > 500 else response)
        if isinstance(response, tuple):
            st.write('Debug: Response is a tuple')
            if len(response) == 2 and isinstance(response[1], pd.DataFrame):
                st.write('Debug: CSV data detected')
                csv_string, df = response
                st.text('CSV Data:')
                st.code(csv_string, language='csv')
                st.text('Interactive Table:')
                st.dataframe(df)
                csv_buffer = BytesIO()
                df.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)
                st.download_button(label='Download CSV', data=csv_buffer, file_name='data.csv', mime='text/csv')
                return csv_string
            elif len(response) == 2 and isinstance(response[0], BytesIO):
                st.write('Debug: Excel data detected')
                excel_buffer, df = response
                st.text('Excel Data:')
                st.dataframe(df)
                excel_buffer.seek(0)
                st.download_button(label='Download Original Excel file', data=excel_buffer, file_name='data_original.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                excel_data = BytesIO()
                with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sheet1')
                excel_data.seek(0)
                st.download_button(label='Download Excel (from DataFrame)', data=excel_data, file_name='data_from_df.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                return ('Excel data displayed and available for download.', excel_buffer)
        elif isinstance(response, pd.DataFrame):
            st.write('Debug: Response is a DataFrame')
            st.text('Data:')
            st.dataframe(response)
            csv_buffer = BytesIO()
            response.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            st.download_button(label='Download CSV', data=csv_buffer, file_name='data.csv', mime='text/csv')
            return 'DataFrame displayed and available for download as CSV.'
        else:
            st.write('Debug: Response is not a tuple or DataFrame')
        return response
    except Exception as e:
        st.error(f'An error occurred during scraping: {str(e)}')
        return f'An unexpected error occurred: {str(e)}. Please try again or contact support if the issue persists.'

def display_message_with_sheets_upload(message, message_index):
    content = message['content']
    if isinstance(content, (str, bytes, BytesIO)):
        data = extract_data_from_markdown(content)
        if data is not None:
            try:
                is_excel = isinstance(data, BytesIO) or (isinstance(content, str) and 'excel' in content.lower())
                if is_excel:
                    df = format_data(data, 'excel')
                else:
                    df = format_data(data, 'csv')
                if df is not None:
                    st.dataframe(df)
                    if not is_excel:
                        csv_buffer = BytesIO()
                        df.to_csv(csv_buffer, index=False)
                        csv_buffer.seek(0)
                        st.download_button(label='📥 Download as CSV', data=csv_buffer, file_name='data.csv', mime='text/csv', key=f'csv_download_{message_index}')
                    else:
                        excel_buffer = BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Sheet1')
                        excel_buffer.seek(0)
                        st.download_button(label='📥 Download as Excel', data=excel_buffer, file_name='data.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key=f'excel_download_{message_index}')
                    display_google_sheets_button(df, f'sheets_upload_{message_index}')
                else:
                    st.warning('Failed to display data as a table. Showing raw content:')
                    st.code(content)
            except Exception as e:
                st.error(f'Error processing data: {str(e)}')
                st.code(content)
        else:
            st.markdown(content)
    else:
        st.markdown(str(content))

def display_info_icons():
    if 'info_icons_displayed' not in st.session_state:
        st.session_state.info_icons_displayed = True
        st.session_state.info_icons_time = time.time()
    if st.session_state.info_icons_displayed:
        st.markdown('\n            <div style="display: flex; justify-content: center; align-items: center; flex-direction: column; gap: 10px; padding: 20px;">\n                <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; max-width: 800px;">\n                    <div class="info-box" data-type="enter-url">\n                        <h3 style="color: #0066cc;">💻 Enter URL</h3>\n                        <p style="color: #000000;">Fetch webpage content for extraction.</p>\n                    </div>\n                    <div class="info-box" data-type="specify-data">\n                        <h3 style="color: #cc6600;">🔍 Specify Data</h3>\n                        <p style="color: #000000;">Define what data you want to extract.</p>\n                    </div>\n                    <div class="info-box" data-type="save-data">\n                        <h3 style="color: #006600;">💾 Save Data</h3>\n                        <p style="color: #000000;">Save in JSON, CSV, or Excel format.</p>\n                    </div>\n                    <div class="info-box" data-type="convert-data">\n                        <h3 style="color: #cc0000;">🔄 Convert Data</h3>\n                        <p style="color: #000000;">Convert between different formats.</p>\n                    </div>\n                </div>\n            </div>\n            ', unsafe_allow_html=True)
        if time.time() - st.session_state.info_icons_time > 10 or ('messages' in st.session_state and len(st.session_state.messages) > 0):
            st.session_state.info_icons_displayed = False

def display_message(message):
    content = message['content']
    if isinstance(content, (str, bytes, io.BytesIO)):
        data = extract_data_from_markdown(content)
        if data is not None:
            if isinstance(data, io.BytesIO) or (isinstance(content, str) and 'excel' in content.lower()):
                df = format_data(data, 'excel')
            else:
                df = format_data(data, 'csv')
            if df is not None:
                st.dataframe(df)
            else:
                st.warning('Failed to display data as a table. Showing raw content:')
                st.code(content)
        else:
            st.markdown(content)
    else:
        st.markdown(str(content))

class WebExtractor:

    def __init__(self, model_name: str='gpt-4o-mini', model_kwargs: Dict[str, Any]=None, proxy: Optional[str]=None, scraper_config: ScraperConfig=None, tor_config: TorConfig=None):
        model_kwargs = model_kwargs or {}
        if isinstance(model_name, str) and model_name.startswith('ollama:'):
            self.model = OllamaModelManager.get_model(model_name[7:])
        elif isinstance(model_name, OllamaModel):
            self.model = model_name
        elif model_name.startswith('gemini-'):
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            self.model = ChatGoogleGenerativeAI(model=model_name, **model_kwargs)
        else:
            self.model = Models.get_model(model_name, **model_kwargs)
        self.model_name = model_name
        self.scraper_config = scraper_config or ScraperConfig()
        self.playwright_scraper = PlaywrightScraper(config=self.scraper_config)
        self.html_scraper = HTMLScraper()
        self.json_scraper = JSONScraper()
        self.proxy_manager = ProxyManager(proxy)
        self.markdown_formatter = MarkdownFormatter()
        self.current_url = None
        self.current_content = None
        self.preprocessed_content = None
        self.conversation_history: List[str] = []
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=32000, chunk_overlap=200, length_function=self.num_tokens_from_string)
        self.max_tokens = 128000 if model_name == 'gpt-4o-mini' else 16385
        self.query_cache = {}
        self.content_hash = None
        self.tor_config = tor_config or TorConfig()
        self.tor_scraper = TorScraper(self.tor_config)

    @staticmethod
    def num_tokens_from_string(string: str) -> int:
        encoding = tiktoken.encoding_for_model('gpt-4o-mini')
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def _hash_content(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def get_website_name(self, url: str) -> str:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.split('.')[0].capitalize()

    @lru_cache(maxsize=100)
    async def _cached_api_call(self, content_hash: str, query: str) -> str:
        prompt_template = get_prompt_for_model(self.model_name)
        full_prompt = prompt_template.format(webpage_content=self.preprocessed_content, query=query)
        if isinstance(self.model, OllamaModel):
            return await self.model.generate(prompt=full_prompt)
        else:
            chain = prompt_template | self.model
            response = await chain.ainvoke({'webpage_content': self.preprocessed_content, 'query': query})
            return response.content

    async def process_query(self, user_input: str, progress_callback=None) -> str:
        if user_input.lower().startswith('http'):
            parts = user_input.split(maxsplit=3)
            url = parts[0]
            pages = parts[1] if len(parts) > 1 and (not parts[1].startswith('-')) else None
            url_pattern = parts[2] if len(parts) > 2 and (not parts[2].startswith('-')) else None
            handle_captcha = '-captcha' in user_input.lower()
            website_name = self.get_website_name(url)
            if progress_callback:
                progress_callback(f'Fetching content from {website_name}...')
            response = await self._fetch_url(url, pages, url_pattern, handle_captcha, progress_callback)
        elif not self.current_content:
            response = 'Please provide a URL first before asking for information.'
        else:
            if progress_callback:
                progress_callback('Extracting information...')
            response = await self._extract_info(user_input)
        self.conversation_history.append(f'Human: {user_input}')
        self.conversation_history.append(f'AI: {response}')
        return response

    async def _fetch_url(self, url: str, pages: Optional[str]=None, url_pattern: Optional[str]=None, handle_captcha: bool=False, progress_callback=None) -> str:
        self.current_url = url
        try:
            if TorScraper.is_onion_url(url):
                if progress_callback:
                    progress_callback('Fetching content through Tor network...')
                content = await self.tor_scraper.fetch_content(url)
                self.current_content = content
            else:
                if progress_callback:
                    progress_callback(f'Fetching content from {url}')
                contents = await self.playwright_scraper.fetch_content(url, proxy=None, pages=pages, url_pattern=url_pattern, handle_captcha=handle_captcha)
                self.current_content = '\n'.join(contents)
            if progress_callback:
                progress_callback('Preprocessing content...')
            self.preprocessed_content = self._preprocess_content(self.current_content)
            new_hash = self._hash_content(self.preprocessed_content)
            if self.content_hash != new_hash:
                self.content_hash = new_hash
                self.query_cache.clear()
            source_type = 'Tor network' if TorScraper.is_onion_url(url) else 'regular web'
            return f"I've fetched and preprocessed the content from {self.current_url} via {source_type}" + (f' (pages: {pages})' if pages else '') + '. What would you like to know about it?'
        except TorException as e:
            return f'Error accessing onion service: {str(e)}'
        except Exception as e:
            return f'Error fetching content: {str(e)}'

    def _preprocess_content(self, content: str) -> str:
        soup = BeautifulSoup(content, 'html.parser')
        for script in soup(['script', 'style']):
            script.decompose()
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        for tag in soup(['header', 'footer', 'nav', 'aside']):
            tag.decompose()
        for tag in soup.find_all():
            if len(tag.get_text(strip=True)) == 0:
                tag.extract()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
        text = '\n'.join((chunk for chunk in chunks if chunk))
        return text

    async def _extract_info(self, query: str) -> str:
        if not self.preprocessed_content:
            return 'Please provide a URL first before asking for information.'
        content_hash = self._hash_content(self.preprocessed_content)
        if self.content_hash != content_hash:
            self.content_hash = content_hash
            self.query_cache.clear()
        cache_key = (content_hash, query)
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        content_tokens = self.num_tokens_from_string(self.preprocessed_content)
        if content_tokens <= self.max_tokens - 1000:
            extracted_data = await self._cached_api_call(content_hash, query)
        else:
            chunks = self.optimized_text_splitter(self.preprocessed_content)
            all_extracted_data = []
            for i, chunk in enumerate(chunks):
                chunk_data = await self._cached_api_call(self._hash_content(chunk), query)
                all_extracted_data.append(chunk_data)
            extracted_data = self._merge_json_chunks(all_extracted_data)
        formatted_result = self._format_result(extracted_data, query)
        self.query_cache[cache_key] = formatted_result
        return formatted_result

    def _format_result(self, extracted_data: str, query: str) -> Union[str, Tuple[str, pd.DataFrame], BytesIO]:
        try:
            json_data = json.loads(extracted_data)
            if 'json' in query.lower():
                return self._format_as_json(json.dumps(json_data))
            elif 'csv' in query.lower():
                csv_string, df = self._format_as_csv(json.dumps(json_data))
                return (f'```csv\n{csv_string}\n```', df)
            elif 'excel' in query.lower():
                return self._format_as_excel(json.dumps(json_data))
            elif 'sql' in query.lower():
                return self._format_as_sql(json.dumps(json_data))
            elif 'html' in query.lower():
                return self._format_as_html(json.dumps(json_data))
            elif isinstance(json_data, list) and all((isinstance(item, dict) for item in json_data)):
                csv_string, df = self._format_as_csv(json.dumps(json_data))
                return (f'```csv\n{csv_string}\n```', df)
            else:
                return self._format_as_json(json.dumps(json_data))
        except json.JSONDecodeError:
            return self._format_as_text(extracted_data)

    def optimized_text_splitter(self, text: str) -> List[str]:
        return self.text_splitter.split_text(text)

    def _merge_json_chunks(self, chunks: List[str]) -> str:
        merged_data = []
        for chunk in chunks:
            try:
                data = json.loads(chunk)
                if isinstance(data, list):
                    merged_data.extend(data)
                else:
                    merged_data.append(data)
            except json.JSONDecodeError:
                print(f'Error decoding JSON chunk: {chunk[:100]}...')
        return json.dumps(merged_data)

    def _format_as_json(self, data: str) -> str:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        try:
            parsed_data = json.loads(data)
            return f'```json\n{json.dumps(parsed_data, indent=2)}\n```'
        except json.JSONDecodeError:
            return f'Error: Invalid JSON data. Raw data: {data[:500]}...'

    def _format_as_csv(self, data: str) -> Tuple[str, pd.DataFrame]:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        else:
            code_block_pattern = '```\\s*([\\s\\S]*?)\\s*```'
            match = re.search(code_block_pattern, data)
            if match:
                data = match.group(1)
        try:
            parsed_data = json.loads(data)
            if not parsed_data:
                return ('No data to convert to CSV.', pd.DataFrame())
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=parsed_data[0].keys())
            writer.writeheader()
            writer.writerows(parsed_data)
            csv_string = output.getvalue()
            df = pd.DataFrame(parsed_data)
            return (csv_string, df)
        except json.JSONDecodeError as e:
            error_msg = f'Error: Invalid JSON data. Raw data: {data[:500]}...'
            return (error_msg, pd.DataFrame())
        except Exception as e:
            error_msg = f'Error: Failed to convert data to CSV. {str(e)}'
            return (error_msg, pd.DataFrame())

    def _format_as_excel(self, data: str) -> Tuple[BytesIO, pd.DataFrame]:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        try:
            parsed_data = json.loads(data)
            if not parsed_data:
                return (BytesIO(b'No data to convert to Excel.'), pd.DataFrame())
            df = pd.DataFrame(parsed_data)
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            excel_buffer.seek(0)
            return (excel_buffer, df)
        except json.JSONDecodeError:
            error_msg = f'Error: Invalid JSON data. Raw data: {data[:500]}...'
            return (BytesIO(error_msg.encode()), pd.DataFrame())
        except Exception as e:
            error_msg = f'Error: Failed to convert data to Excel. {str(e)}'
            return (BytesIO(error_msg.encode()), pd.DataFrame())

    def _format_as_sql(self, data: str) -> str:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        try:
            parsed_data = json.loads(data)
            if not parsed_data:
                return 'No data to convert to SQL.'
            fields = ', '.join([f'{k} TEXT' for k in parsed_data[0].keys()])
            sql = f'CREATE TABLE extracted_data ({fields});\n'
            for row in parsed_data:
                escaped_values = [str(v).replace("'", "''") for v in row.values()]
                values = ', '.join([f"'{v}'" for v in escaped_values])
                sql += f'INSERT INTO extracted_data VALUES ({values});\n'
            return f'```sql\n{sql}\n```'
        except json.JSONDecodeError:
            return f'Error: Invalid JSON data. Raw data: {data[:500]}...'

    def _format_as_html(self, data: str) -> str:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        try:
            parsed_data = json.loads(data)
            if not parsed_data:
                return 'No data to convert to HTML.'
            html = '<table>\n<tr>\n'
            html += ''.join([f'<th>{k}</th>' for k in parsed_data[0].keys()])
            html += '</tr>\n'
            for row in parsed_data:
                html += '<tr>\n'
                html += ''.join([f'<td>{v}</td>' for v in row.values()])
                html += '</tr>\n'
            html += '</table>'
            return f'```html\n{html}\n```'
        except json.JSONDecodeError:
            return f'Error: Invalid JSON data. Raw data: {data[:500]}...'

    def _format_as_text(self, data: str) -> str:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        try:
            parsed_data = json.loads(data)
            return '\n'.join([', '.join([f'{k}: {v}' for k, v in item.items()]) for item in parsed_data])
        except json.JSONDecodeError:
            return data

    def format_to_markdown(self, text: str) -> str:
        return self.markdown_formatter.to_markdown(text)

    def format_from_markdown(self, markdown_text: str) -> str:
        return self.markdown_formatter.from_markdown(markdown_text)

    @staticmethod
    async def list_ollama_models() -> List[str]:
        return await OllamaModel.list_models()

def _format_as_excel(self, data: str) -> Tuple[BytesIO, pd.DataFrame]:
    json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
    match = re.search(json_pattern, data)
    if match:
        data = match.group(1)
    try:
        parsed_data = json.loads(data)
        if not parsed_data:
            return (BytesIO(b'No data to convert to Excel.'), pd.DataFrame())
        df = pd.DataFrame(parsed_data)
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        excel_buffer.seek(0)
        return (excel_buffer, df)
    except json.JSONDecodeError:
        error_msg = f'Error: Invalid JSON data. Raw data: {data[:500]}...'
        return (BytesIO(error_msg.encode()), pd.DataFrame())
    except Exception as e:
        error_msg = f'Error: Failed to convert data to Excel. {str(e)}'
        return (BytesIO(error_msg.encode()), pd.DataFrame())

class MarkdownFormatter:

    @staticmethod
    def to_markdown(text: str) -> str:
        return markdown.markdown(text)

    @staticmethod
    def from_markdown(markdown_text: str) -> str:
        return markdown_text.replace('#', '').replace('*', '').replace('_', '')

@staticmethod
def to_markdown(text: str) -> str:
    return markdown.markdown(text)

def clean_value(val):
    if pd.isna(val):
        return ''
    if isinstance(val, (int, float)):
        return str(val)
    return str(val).replace('\n', ' ').replace('\r', '')

