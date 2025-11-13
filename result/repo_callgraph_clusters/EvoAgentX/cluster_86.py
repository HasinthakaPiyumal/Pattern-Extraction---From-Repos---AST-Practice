# Cluster 86

class MarkdownParser:
    """Parses markdown content and extracts structured data."""

    def __init__(self, md_content: str):
        self.md_content = md_content
        self.sections = {}
        self.metadata = {}
        self.parse_content()

    def parse_content(self):
        """Parse the markdown content into structured sections."""
        lines = self.md_content.split('\n')
        current_section = None
        current_content = []
        self.metadata = self._extract_metadata(lines)
        for line in lines:
            line = line.strip()
            if line.startswith('## '):
                if current_section:
                    section_data = {'subsections': self._parse_subsections(current_content), 'raw_content': '\n'.join(current_content)}
                    if section_data['subsections']:
                        self.sections[current_section] = section_data
                current_section = line[3:].strip()
                current_content = []
            elif line.startswith('### '):
                current_content.append(line)
            else:
                current_content.append(line)
        if current_section:
            section_data = {'subsections': self._parse_subsections(current_content), 'raw_content': '\n'.join(current_content)}
            if section_data['subsections']:
                self.sections[current_section] = section_data

    def _extract_metadata(self, lines: List[str]) -> Dict[str, str]:
        """Extract metadata from the markdown header."""
        metadata = {}
        for line in lines:
            if '**' in line and ':' in line:
                match = re.search('\\*\\*([^*]+)\\*\\*:\\s*(.+)', line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    metadata[key] = value
        return metadata

    def _parse_subsections(self, content: List[str]) -> Dict[str, Any]:
        """Parse subsections from content lines."""
        subsections = {}
        current_subsection = None
        current_content = []
        for line in content:
            if line.startswith('### '):
                if current_subsection:
                    subsection_data = self._parse_subsection_content(current_content)
                    if self._has_content(subsection_data):
                        subsections[current_subsection] = subsection_data
                current_subsection = line[4:].strip()
                current_content = []
            else:
                current_content.append(line)
        if current_subsection:
            subsection_data = self._parse_subsection_content(current_content)
            if self._has_content(subsection_data):
                subsections[current_subsection] = subsection_data
        return subsections

    def _has_content(self, subsection_data: Dict[str, Any]) -> bool:
        """Check if subsection has meaningful content."""
        tables = subsection_data.get('tables', [])
        lists = subsection_data.get('lists', [])
        text = subsection_data.get('text', [])
        meaningful_tables = []
        for table in tables:
            rows = table.get('rows', [])
            if rows and (not all((all((cell in ['', '-', 'N/A', '无', '0'] for cell in row)) for row in rows))):
                meaningful_tables.append(table)
        meaningful_lists = [lst for lst in lists if lst and any((item.strip() for item in lst))]
        meaningful_text = [line for line in text if line.strip() and line.strip() not in ['---', '无', '-']]
        return bool(meaningful_tables or meaningful_lists or meaningful_text)

    def _parse_subsection_content(self, content: List[str]) -> Dict[str, Any]:
        """Parse subsection content including tables, lists, and text."""
        tables = []
        lists = []
        text_content = []
        i = 0
        while i < len(content):
            line = content[i].strip()
            if not line:
                i += 1
                continue
            if '|' in line and line.count('|') >= 2:
                table_data, consumed_lines = self._extract_table(content, i)
                if table_data:
                    tables.append(table_data)
                    i += consumed_lines
                    continue
            elif line.startswith('- ') or line.startswith('* '):
                list_items, consumed_lines = self._extract_list(content, i)
                if list_items:
                    lists.append(list_items)
                    i += consumed_lines
                    continue
            elif line and (not line.startswith('---')):
                text_content.append(line)
            i += 1
        return {'tables': tables, 'lists': lists, 'text': text_content}

    def _extract_table(self, content: List[str], start_idx: int) -> Tuple[Optional[Dict[str, Any]], int]:
        """Extract table data starting from start_idx and return consumed lines count."""
        if start_idx >= len(content):
            return (None, 0)
        table_lines = []
        i = start_idx
        while i < len(content) and content[i].strip() and ('|' in content[i]):
            table_lines.append(content[i].strip())
            i += 1
        if len(table_lines) < 2:
            return (None, 1)
        header_line = table_lines[0]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        data_start_idx = 1
        if len(table_lines) > 1 and all((c in '-|: ' for c in table_lines[1])):
            data_start_idx = 2
        rows = []
        for line in table_lines[data_start_idx:]:
            if '|' in line:
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if len(cells) == len(headers):
                    rows.append(cells)
        consumed_lines = len(table_lines)
        if headers and rows:
            return ({'headers': headers, 'rows': rows}, consumed_lines)
        return (None, consumed_lines)

    def _extract_list(self, content: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Extract list items starting from start_idx and return consumed lines count."""
        items = []
        i = start_idx
        while i < len(content):
            line = content[i].strip()
            if line.startswith('- ') or line.startswith('* '):
                items.append(line[2:].strip())
                i += 1
            else:
                break
        consumed_lines = i - start_idx
        return (items, consumed_lines)

    def get_metadata(self) -> Dict[str, str]:
        """Get extracted metadata."""
        return self.metadata

def __init__(self, md_content: str):
    self.md_content = md_content
    self.sections = {}
    self.metadata = {}
    self.parse_content()

class MarkdownParser:
    """Parses markdown content and extracts structured data."""

    def __init__(self, md_content: str):
        self.md_content = md_content
        self.sections = {}
        self.metadata = {}
        self.parse_content()

    def parse_content(self):
        """Parse the markdown content into structured sections."""
        lines = self.md_content.split('\n')
        current_section = None
        current_content = []
        self.metadata = self._extract_metadata(lines)
        for line in lines:
            line = line.strip()
            if line.startswith('## '):
                if current_section:
                    section_data = {'subsections': self._parse_subsections(current_content), 'raw_content': '\n'.join(current_content)}
                    if section_data['subsections']:
                        self.sections[current_section] = section_data
                current_section = line[3:].strip()
                current_content = []
            elif line.startswith('### '):
                current_content.append(line)
            else:
                current_content.append(line)
        if current_section:
            section_data = {'subsections': self._parse_subsections(current_content), 'raw_content': '\n'.join(current_content)}
            if section_data['subsections']:
                self.sections[current_section] = section_data

    def _extract_metadata(self, lines: List[str]) -> Dict[str, str]:
        """Extract metadata from the markdown header."""
        metadata = {}
        for line in lines:
            if '**' in line and ':' in line:
                match = re.search('\\*\\*([^*]+)\\*\\*:\\s*(.+)', line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    metadata[key] = value
        return metadata

    def _parse_subsections(self, content: List[str]) -> Dict[str, Any]:
        """Parse subsections from content lines."""
        subsections = {}
        current_subsection = None
        current_content = []
        for line in content:
            if line.startswith('### '):
                if current_subsection:
                    subsection_data = self._parse_subsection_content(current_content)
                    if self._has_content(subsection_data):
                        subsections[current_subsection] = subsection_data
                current_subsection = line[4:].strip()
                current_content = []
            else:
                current_content.append(line)
        if current_subsection:
            subsection_data = self._parse_subsection_content(current_content)
            if self._has_content(subsection_data):
                subsections[current_subsection] = subsection_data
        return subsections

    def _has_content(self, subsection_data: Dict[str, Any]) -> bool:
        """Check if subsection has meaningful content."""
        tables = subsection_data.get('tables', [])
        lists = subsection_data.get('lists', [])
        text = subsection_data.get('text', [])
        meaningful_tables = []
        for table in tables:
            rows = table.get('rows', [])
            if rows and (not all((all((cell in ['', '-', 'N/A', '无', '0'] for cell in row)) for row in rows))):
                meaningful_tables.append(table)
        meaningful_lists = [lst for lst in lists if lst and any((item.strip() for item in lst))]
        meaningful_text = [line for line in text if line.strip() and line.strip() not in ['---', '无', '-']]
        return bool(meaningful_tables or meaningful_lists or meaningful_text)

    def _parse_subsection_content(self, content: List[str]) -> Dict[str, Any]:
        """Parse subsection content including tables, lists, and text."""
        tables = []
        lists = []
        text_content = []
        i = 0
        while i < len(content):
            line = content[i].strip()
            if not line:
                i += 1
                continue
            if '|' in line and line.count('|') >= 2:
                table_data, consumed_lines = self._extract_table(content, i)
                if table_data:
                    tables.append(table_data)
                    i += consumed_lines
                    continue
            elif line.startswith('- ') or line.startswith('* '):
                list_items, consumed_lines = self._extract_list(content, i)
                if list_items:
                    lists.append(list_items)
                    i += consumed_lines
                    continue
            elif line and (not line.startswith('---')):
                text_content.append(line)
            i += 1
        return {'tables': tables, 'lists': lists, 'text': text_content}

    def _extract_table(self, content: List[str], start_idx: int) -> Tuple[Optional[Dict[str, Any]], int]:
        """Extract table data starting from start_idx and return consumed lines count."""
        if start_idx >= len(content):
            return (None, 0)
        table_lines = []
        i = start_idx
        while i < len(content) and content[i].strip() and ('|' in content[i]):
            table_lines.append(content[i].strip())
            i += 1
        if len(table_lines) < 2:
            return (None, 1)
        header_line = table_lines[0]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        data_start_idx = 1
        if len(table_lines) > 1 and all((c in '-|: ' for c in table_lines[1])):
            data_start_idx = 2
        rows = []
        for line in table_lines[data_start_idx:]:
            if '|' in line:
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if len(cells) == len(headers):
                    rows.append(cells)
        consumed_lines = len(table_lines)
        if headers and rows:
            return ({'headers': headers, 'rows': rows}, consumed_lines)
        return (None, consumed_lines)

    def _extract_list(self, content: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Extract list items starting from start_idx and return consumed lines count."""
        items = []
        i = start_idx
        while i < len(content):
            line = content[i].strip()
            if line.startswith('- ') or line.startswith('* '):
                items.append(line[2:].strip())
                i += 1
            else:
                break
        consumed_lines = i - start_idx
        return (items, consumed_lines)

    def get_metadata(self) -> Dict[str, str]:
        """Get extracted metadata."""
        return self.metadata

def __init__(self, md_content: str):
    self.md_content = md_content
    self.sections = {}
    self.metadata = {}
    self.parse_content()

