# Cluster 1

def get_definition_name(node: Node) -> str:
    for child in node.children:
        if child.type == NodeType.IDENTIFIER.value:
            return child.text.decode('utf8')

class ExecuteCommandTool(Tool):
    name: str = 'execute_command'
    description: str = 'Execute a command line operation with permission checking and cross-platform support. Can handle all command line operations including directory creation, file listing, system info, and more.'
    inputs: Dict[str, Dict[str, str]] = {'command': {'type': 'string', 'description': "The command to execute (e.g., 'ls -la', 'dir', 'mkdir test', 'pwd', 'whoami', 'date', etc.)"}, 'timeout': {'type': 'integer', 'description': 'Command timeout in seconds (default: 30)'}, 'working_directory': {'type': 'string', 'description': 'Working directory for command execution (optional)'}}
    required: Optional[List[str]] = ['command']

    def __init__(self, cmd_base: CMDBase=None):
        super().__init__()
        self.cmd_base = cmd_base or CMDBase()

    def __call__(self, command: str, timeout: int=30, working_directory: str=None) -> Dict[str, Any]:
        """
        Execute a command with permission checking.
        
        Args:
            command: The command to execute
            timeout: Command timeout in seconds
            working_directory: Working directory for command execution
            
        Returns:
            Dictionary containing the command execution result
        """
        try:
            result = self.cmd_base.execute_command(command=command, timeout=timeout, cwd=working_directory)
            if result['success']:
                logger.info(f'Successfully executed command: {command}')
            else:
                logger.error(f'Failed to execute command {command}: {result.get('error', 'Unknown error')}')
            return result
        except Exception as e:
            logger.error(f'Error in execute_command tool: {str(e)}')
            return {'success': False, 'error': str(e), 'command': command}

def __call__(self, command: str, timeout: int=30, working_directory: str=None) -> Dict[str, Any]:
    """
        Execute a command with permission checking.
        
        Args:
            command: The command to execute
            timeout: Command timeout in seconds
            working_directory: Working directory for command execution
            
        Returns:
            Dictionary containing the command execution result
        """
    try:
        result = self.cmd_base.execute_command(command=command, timeout=timeout, cwd=working_directory)
        if result['success']:
            logger.info(f'Successfully executed command: {command}')
        else:
            logger.error(f'Failed to execute command {command}: {result.get('error', 'Unknown error')}')
        return result
    except Exception as e:
        logger.error(f'Error in execute_command tool: {str(e)}')
        return {'success': False, 'error': str(e), 'command': command}

class StorageBase(BaseModule, ABC):
    """
    Abstract base class for comprehensive storage operations supporting various file types.
    Provides unified interface for local and remote storage operations.
    """

    def __init__(self, base_path: str='.', **kwargs):
        """
        Initialize the StorageBase with configuration options.
        
        Args:
            base_path (str): Base directory for storage operations (default: current directory)
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(**kwargs)
        self.base_path = base_path
        self.appendable_formats = {'.txt': self._append_text, '.json': self._append_json, '.csv': self._append_csv, '.yaml': self._append_yaml, '.yml': self._append_yaml, '.pickle': self._append_pickle, '.xlsx': self._append_excel}
        self._initialize_storage()

    @abstractmethod
    def _initialize_storage(self):
        """
        Initialize storage-specific setup. Override in subclasses for storage-specific initialization.
        """
        pass

    @abstractmethod
    def _read_raw(self, path: str, **kwargs) -> bytes:
        """Read raw file content - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _write_raw(self, path: str, content: bytes, **kwargs) -> bool:
        """Write raw file content - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _delete_raw(self, path: str) -> bool:
        """Delete file or directory - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _list_raw(self, path: str=None, **kwargs) -> List[Dict[str, Any]]:
        """List files and directories - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _exists_raw(self, path: str) -> bool:
        """Check if path exists - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _create_directory_raw(self, path: str) -> bool:
        """Create directory - must be implemented by subclasses"""
        pass

    def translate_in(self, file_path: str) -> str:
        """
        Translate input file path by combining it with base_path.
        This method takes a user-provided path and converts it to the full system path.
        
        Args:
            file_path (str): User-provided file path (can be relative or absolute)
            
        Returns:
            str: Full system path combining base_path and file_path
        """
        if os.path.isabs(file_path):
            return file_path
        if hasattr(self, 'bucket_name') and hasattr(self, 'supabase'):
            if self.base_path.startswith('/'):
                clean_base = self.base_path.lstrip('/')
                if clean_base:
                    return f'{clean_base}/{file_path}'
                else:
                    return file_path
            else:
                return f'{self.base_path}/{file_path}'
        else:
            combined_path = os.path.join(self.base_path, file_path)
            normalized_path = os.path.normpath(combined_path)
            return normalized_path

    def translate_out(self, full_path: str) -> str:
        """
        Translate output full path by removing the base_path prefix.
        This method takes a full system path and converts it back to the user-relative path.
        
        Args:
            full_path (str): Full system path
            
        Returns:
            str: User-relative path with base_path removed
        """
        if self.base_path in ['.', '', None]:
            return full_path
        if hasattr(self, 'bucket_name') and hasattr(self, 'supabase'):
            if self.base_path.startswith('/'):
                clean_base = self.base_path.lstrip('/')
            else:
                clean_base = self.base_path
            if clean_base and full_path.startswith(f'{clean_base}/'):
                relative_path = full_path[len(f'{clean_base}/'):]
                return relative_path
            elif clean_base and full_path == clean_base:
                return ''
            else:
                return full_path
        else:
            base_abs = os.path.abspath(self.base_path)
            full_abs = os.path.abspath(full_path)
            if full_abs.startswith(base_abs):
                relative_path = full_abs[len(base_abs):]
                if relative_path.startswith(os.sep):
                    relative_path = relative_path[1:]
                return relative_path
            return full_path

    def get_file_type(self, file_path: str) -> str:
        """Get the file extension from a file path"""
        return Path(file_path).suffix.lower()

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive information about a file"""
        try:
            target_path = self.translate_in(file_path)
            if not self._exists_raw(target_path):
                return {'success': False, 'error': f'File {file_path} does not exist'}
            return {'success': True, 'file_path': target_path, 'file_name': Path(target_path).name, 'file_extension': Path(target_path).suffix.lower(), 'exists': True}
        except Exception as e:
            logger.error(f'Error getting file info for {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create directory"""
        try:
            target_path = self.translate_in(path)
            success = self._create_directory_raw(target_path)
            if success:
                return {'success': True, 'path': target_path, 'message': 'Directory created successfully'}
            else:
                return {'success': False, 'error': 'Failed to create directory', 'path': target_path}
        except Exception as e:
            logger.error(f'Error creating directory {path}: {str(e)}')
            return {'success': False, 'error': str(e), 'path': path}

    def exists(self, path: str) -> bool:
        """Check if path exists"""
        target_path = self.translate_in(path)
        return self._exists_raw(target_path)

    def delete(self, path: str) -> Dict[str, Any]:
        """Delete file or directory"""
        try:
            target_path = self.translate_in(path)
            success = self._delete_raw(target_path)
            if success:
                return {'success': True, 'path': target_path, 'message': 'Deleted successfully'}
            else:
                return {'success': False, 'error': 'Failed to delete', 'path': target_path}
        except Exception as e:
            logger.error(f'Error deleting {path}: {str(e)}')
            return {'success': False, 'error': str(e), 'path': path}

    def move(self, source: str, destination: str) -> Dict[str, Any]:
        """Move/rename file or directory"""
        try:
            resolved_source = self.translate_in(source)
            resolved_destination = self.translate_in(destination)
            content = self._read_raw(resolved_source)
            success = self._write_raw(resolved_destination, content)
            if success:
                self._delete_raw(resolved_source)
                return {'success': True, 'source': resolved_source, 'destination': resolved_destination, 'message': 'Moved successfully'}
            else:
                return {'success': False, 'error': 'Failed to write to destination', 'source': resolved_source, 'destination': resolved_destination}
        except Exception as e:
            logger.error(f'Error moving {source} to {destination}: {str(e)}')
            return {'success': False, 'error': str(e), 'source': source, 'destination': destination}

    def copy(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy file"""
        try:
            resolved_source = self.translate_in(source)
            resolved_destination = self.translate_in(destination)
            content = self._read_raw(resolved_source)
            success = self._write_raw(resolved_destination, content)
            if success:
                return {'success': True, 'source': resolved_source, 'destination': resolved_destination, 'message': 'Copied successfully'}
            else:
                return {'success': False, 'error': 'Failed to write to destination', 'source': resolved_source, 'destination': resolved_destination}
        except Exception as e:
            logger.error(f'Error copying {source} to {destination}: {str(e)}')
            return {'success': False, 'error': str(e), 'source': source, 'destination': destination}

    def list(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
        """List files and directories"""
        try:
            target_path = self.translate_in(path) if path else str(self.base_path)
            items = self._list_raw(target_path, max_depth=max_depth, include_hidden=include_hidden)
            return {'success': True, 'path': target_path, 'items': items, 'total_count': len(items)}
        except Exception as e:
            logger.error(f'Error listing {path}: {str(e)}')
            return {'success': False, 'error': str(e), 'path': path}

    def save(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """
        Save content to a file with automatic format detection.
        This method replaces the old save method with the improved create_file logic.
        
        Args:
            file_path (str): Path where the file should be saved
            content (Any): Content to save to the file
            **kwargs: Additional arguments for file creation (encoding, format, etc.)
            
        Returns:
            Dict[str, Any]: Result of the operation with success status and details
        """
        try:
            file_extension = self.get_file_type(file_path)
            target_file_path = self.translate_in(file_path)
            if file_extension == '.json':
                return self._save_json(target_file_path, content, **kwargs)
            elif file_extension in ['.txt', '.md', '.log']:
                return self._save_text(target_file_path, content, **kwargs)
            elif file_extension == '.csv':
                return self._save_csv(target_file_path, content, **kwargs)
            elif file_extension in ['.yaml', '.yml']:
                return self._save_yaml(target_file_path, content, **kwargs)
            elif file_extension == '.xml':
                return self._save_xml(target_file_path, content, **kwargs)
            elif file_extension == '.xlsx':
                return self._save_excel(target_file_path, content, **kwargs)
            elif file_extension == '.pickle':
                return self._save_pickle(target_file_path, content, **kwargs)
            elif file_extension == '.pdf':
                return self._save_pdf(target_file_path, content, **kwargs)
            elif file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
                return self._save_image(target_file_path, content, **kwargs)
            else:
                if isinstance(content, str):
                    content_bytes = content.encode(kwargs.get('encoding', 'utf-8'))
                elif isinstance(content, bytes):
                    content_bytes = content
                else:
                    content_bytes = str(content).encode(kwargs.get('encoding', 'utf-8'))
                success = self._write_raw(target_file_path, content_bytes, **kwargs)
                if success:
                    return {'success': True, 'message': f"File '{file_path}' saved successfully", 'file_path': file_path, 'full_path': target_file_path, 'size': len(content_bytes)}
                else:
                    return {'success': False, 'message': f"Failed to save file '{file_path}'", 'file_path': file_path, 'full_path': target_file_path}
        except Exception as e:
            logger.error(f'Error saving file {file_path}: {str(e)}')
            return {'success': False, 'message': f'Error saving file: {str(e)}', 'file_path': file_path}

    def read(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read content from a file with automatic format detection"""
        try:
            target_file_path = self.translate_in(file_path)
            file_extension = Path(target_file_path).suffix.lower()
            if file_extension == '.json':
                return self._read_json(target_file_path, **kwargs)
            elif file_extension in ['.yaml', '.yml']:
                return self._read_yaml(target_file_path, **kwargs)
            elif file_extension == '.csv':
                return self._read_csv(target_file_path, **kwargs)
            elif file_extension == '.xlsx':
                return self._read_excel(target_file_path, **kwargs)
            elif file_extension == '.xml':
                return self._read_xml(target_file_path, **kwargs)
            elif file_extension == '.pickle':
                return self._read_pickle(target_file_path, **kwargs)
            elif file_extension == '.pdf':
                return self._read_pdf(target_file_path, **kwargs)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                return self._read_image(target_file_path, **kwargs)
            else:
                return self._read_text(target_file_path, **kwargs)
        except Exception as e:
            logger.error(f'Error reading {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def append(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Append content to a file (only for supported formats)"""
        try:
            target_file_path = self.translate_in(file_path)
            file_extension = Path(target_file_path).suffix.lower()
            if file_extension in self.appendable_formats:
                return self.appendable_formats[file_extension](target_file_path, content, **kwargs)
            else:
                return {'success': False, 'error': f'Append not supported for {file_extension} files'}
        except Exception as e:
            logger.error(f'Error appending to {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_text(self, file_path: str, content: Any, encoding: str='utf-8', **kwargs) -> Dict[str, Any]:
        """Save text content to a file"""
        try:
            if isinstance(content, str):
                content_bytes = content.encode(encoding)
            else:
                content_bytes = str(content).encode(encoding)
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'File saved to {file_path}', 'file_path': file_path, 'content_length': len(content_bytes)}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving text file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_text(self, file_path: str, encoding: str='utf-8', **kwargs) -> Dict[str, Any]:
        """Read text content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content = content_bytes.decode(encoding)
            return {'success': True, 'content': content, 'file_path': file_path, 'content_length': len(content)}
        except Exception as e:
            logger.error(f'Error reading text file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_text(self, file_path: str, content: str, encoding: str='utf-8', **kwargs) -> Dict[str, Any]:
        """Append text content to a file"""
        try:
            content_bytes = str(content).encode(encoding)
            existing_bytes = b''
            if self._exists_raw(file_path):
                existing_bytes = self._read_raw(file_path, **kwargs)
            combined_bytes = existing_bytes + content_bytes
            success = self._write_raw(file_path, combined_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to file {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to text file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_json(self, file_path: str, content: Any, indent: int=2, **kwargs) -> Dict[str, Any]:
        """Save JSON content to a file"""
        try:
            if isinstance(content, str):
                json.loads(content)
                json_content = content
            else:
                json_content = json.dumps(content, indent=indent, ensure_ascii=False)
            content_bytes = json_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'JSON file saved to {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving JSON file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_json(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read JSON content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content_str = content_bytes.decode('utf-8')
            content = json.loads(content_str)
            return {'success': True, 'content': content, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading JSON file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_json(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Append content to JSON file (for arrays)"""
        try:
            existing_content = []
            if self._exists_raw(file_path):
                existing_bytes = self._read_raw(file_path, **kwargs)
                existing_str = existing_bytes.decode('utf-8')
                existing_content = json.loads(existing_str)
            if isinstance(existing_content, list):
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            elif isinstance(existing_content, dict):
                if isinstance(content, dict):
                    existing_content.update(content)
                else:
                    return {'success': False, 'error': 'Cannot append non-dict to JSON dict'}
            else:
                existing_content = [existing_content]
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            json_content = json.dumps(existing_content, indent=2, ensure_ascii=False)
            content_bytes = json_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to JSON file {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to JSON file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_csv(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Save CSV content to a file - handles both raw CSV strings and structured data"""
        try:
            if not content:
                return {'success': False, 'error': 'No content to save'}
            from io import StringIO
            csv_buffer = StringIO()
            if isinstance(content, str):
                csv_content = content
                rows = content.count('\n')
            elif isinstance(content, list) and content and isinstance(content[0], dict):
                fieldnames = content[0].keys()
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(content)
                csv_content = csv_buffer.getvalue()
                rows = len(content)
            elif isinstance(content, list) and content and isinstance(content[0], list):
                writer = csv.writer(csv_buffer)
                writer.writerows(content)
                csv_content = csv_buffer.getvalue()
                rows = len(content)
            else:
                return {'success': False, 'error': 'CSV content must be a string, list of dictionaries, or list of lists'}
            content_bytes = csv_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'CSV file saved to {file_path}', 'file_path': file_path, 'rows': rows}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving CSV file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_csv(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read CSV content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content_str = content_bytes.decode('utf-8')
            from io import StringIO
            reader = csv.DictReader(StringIO(content_str))
            content = list(reader)
            return {'success': True, 'content': content, 'file_path': file_path, 'rows': len(content)}
        except Exception as e:
            logger.error(f'Error reading CSV file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_csv(self, file_path: str, content: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Append content to CSV file"""
        try:
            if not content:
                return {'success': False, 'error': 'No content to append'}
            existing_content = []
            if self._exists_raw(file_path):
                existing_bytes = self._read_raw(file_path, **kwargs)
                existing_str = existing_bytes.decode('utf-8')
                from io import StringIO
                reader = csv.DictReader(StringIO(existing_str))
                existing_content = list(reader)
            combined_content = existing_content + content
            from io import StringIO
            csv_buffer = StringIO()
            if combined_content:
                fieldnames = combined_content[0].keys()
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(combined_content)
            csv_content = csv_buffer.getvalue()
            content_bytes = csv_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to CSV file {file_path}', 'file_path': file_path, 'appended_rows': len(content)}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to CSV file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_yaml(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Save YAML content to a file"""
        try:
            yaml_content = yaml.dump(content, default_flow_style=False, allow_unicode=True)
            content_bytes = yaml_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'YAML file saved to {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving YAML file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_yaml(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read YAML content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content_str = content_bytes.decode('utf-8')
            content = yaml.safe_load(content_str)
            return {'success': True, 'content': content, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading YAML file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_yaml(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Append content to YAML file (for lists)"""
        try:
            existing_content = []
            if self._exists_raw(file_path):
                existing_bytes = self._read_raw(file_path, **kwargs)
                existing_str = existing_bytes.decode('utf-8')
                existing_content = yaml.safe_load(existing_str) or []
            if isinstance(existing_content, list):
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            elif isinstance(existing_content, dict):
                if isinstance(content, dict):
                    existing_content.update(content)
                else:
                    return {'success': False, 'error': 'Cannot append non-dict to YAML dict'}
            else:
                existing_content = [existing_content]
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            yaml_content = yaml.dump(existing_content, default_flow_style=False, allow_unicode=True)
            content_bytes = yaml_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to YAML file {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to YAML file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_xml(self, file_path: str, content: Any, root_tag: str='root', **kwargs) -> Dict[str, Any]:
        """Save XML content to a file"""
        try:
            if isinstance(content, str):
                try:
                    ET.fromstring(content)
                    xml_content = content
                except ET.ParseError:
                    root = ET.Element(root_tag)
                    root.text = content
                    xml_content = ET.tostring(root, encoding='unicode')
            elif isinstance(content, dict):

                def dict_to_xml(data, root):
                    for key, value in data.items():
                        child = ET.SubElement(root, key)
                        if isinstance(value, dict):
                            dict_to_xml(value, child)
                        else:
                            child.text = str(value)
                root = ET.Element(root_tag)
                dict_to_xml(content, root)
                xml_content = ET.tostring(root, encoding='unicode')
            else:
                root = ET.Element(root_tag)
                root.text = str(content)
                xml_content = ET.tostring(root, encoding='unicode')
            content_bytes = xml_content.encode('utf-8')
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'XML file saved to {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving XML file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_xml(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read XML content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content_str = content_bytes.decode('utf-8')
            root = ET.fromstring(content_str)

            def xml_to_dict(element):
                result = {}
                for child in element:
                    if len(child) == 0:
                        result[child.tag] = child.text
                    else:
                        result[child.tag] = xml_to_dict(child)
                return result
            content = xml_to_dict(root)
            return {'success': True, 'content': content, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading XML file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_excel(self, file_path: str, content: List[List[Any]], sheet_name: str='Sheet1', **kwargs) -> Dict[str, Any]:
        """Save Excel content to a file"""
        if not EXCEL_AVAILABLE:
            return {'success': False, 'error': 'openpyxl library not available'}
        try:
            from io import BytesIO
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = sheet_name
            for row in content:
                worksheet.append(row)
            buffer = BytesIO()
            workbook.save(buffer)
            content_bytes = buffer.getvalue()
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Excel file saved to {file_path}', 'file_path': file_path, 'rows': len(content)}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving Excel file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_excel(self, file_path: str, sheet_name: str=None, **kwargs) -> Dict[str, Any]:
        """Read Excel content from a file"""
        if not EXCEL_AVAILABLE:
            return {'success': False, 'error': 'openpyxl library not available'}
        try:
            from io import BytesIO
            content_bytes = self._read_raw(file_path, **kwargs)
            workbook = load_workbook(BytesIO(content_bytes), data_only=True)
            sheet_names = workbook.sheetnames
            if sheet_name is None:
                sheet_name = sheet_names[0]
            if sheet_name not in sheet_names:
                return {'success': False, 'error': f"Sheet '{sheet_name}' not found"}
            worksheet = workbook[sheet_name]
            content = []
            for row in worksheet.iter_rows(values_only=True):
                if any((cell is not None for cell in row)):
                    content.append(list(row))
            return {'success': True, 'content': content, 'file_path': file_path, 'sheet_name': sheet_name, 'rows': len(content)}
        except Exception as e:
            logger.error(f'Error reading Excel file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_excel(self, file_path: str, content: List[List[Any]], sheet_name: str=None, **kwargs) -> Dict[str, Any]:
        """Append content to Excel file"""
        if not EXCEL_AVAILABLE:
            return {'success': False, 'error': 'openpyxl library not available'}
        try:
            from io import BytesIO
            if not self._exists_raw(file_path):
                return self._save_excel(file_path, content, sheet_name or 'Sheet1', **kwargs)
            content_bytes = self._read_raw(file_path, **kwargs)
            workbook = load_workbook(BytesIO(content_bytes))
            sheet_names = workbook.sheetnames
            if sheet_name is None:
                sheet_name = sheet_names[0]
            if sheet_name not in sheet_names:
                return {'success': False, 'error': f"Sheet '{sheet_name}' not found"}
            worksheet = workbook[sheet_name]
            for row in content:
                worksheet.append(row)
            buffer = BytesIO()
            workbook.save(buffer)
            updated_bytes = buffer.getvalue()
            success = self._write_raw(file_path, updated_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to Excel file {file_path}', 'file_path': file_path, 'appended_rows': len(content)}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to Excel file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_pickle(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Save pickle content to a file"""
        try:
            content_bytes = pickle.dumps(content)
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Pickle file saved to {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error saving pickle file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_pickle(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read pickle content from a file"""
        try:
            content_bytes = self._read_raw(file_path, **kwargs)
            content = pickle.loads(content_bytes)
            return {'success': True, 'content': content, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading pickle file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _append_pickle(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Append content to pickle file (for lists)"""
        try:
            existing_content = []
            if self._exists_raw(file_path):
                existing_bytes = self._read_raw(file_path, **kwargs)
                existing_content = pickle.loads(existing_bytes)
            if isinstance(existing_content, list):
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            elif isinstance(existing_content, dict):
                if isinstance(content, dict):
                    existing_content.update(content)
                elif isinstance(content, list):
                    existing_content['appended_list'] = content
                else:
                    existing_content['appended_value'] = content
            else:
                existing_content = [existing_content]
                if isinstance(content, list):
                    existing_content.extend(content)
                else:
                    existing_content.append(content)
            content_bytes = pickle.dumps(existing_content)
            success = self._write_raw(file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f'Content appended to pickle file {file_path}', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error appending to pickle file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_pdf(self, file_path: str, content: str, **kwargs) -> Dict[str, Any]:
        """Save content to a PDF file"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            paragraphs = content.split('\n')
            for para_text in paragraphs:
                if para_text.strip():
                    para = Paragraph(para_text, styles['Normal'])
                    story.append(para)
                    story.append(Spacer(1, 12))
                else:
                    story.append(Spacer(1, 12))
            doc.build(story)
            return {'success': True, 'message': f'PDF file saved to {file_path}', 'file_path': file_path}
        except ImportError:
            return {'success': False, 'error': 'reportlab library not available for PDF creation'}
        except Exception as e:
            logger.error(f'Error saving PDF file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_pdf(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read content from a PDF file"""
        if not PDF_AVAILABLE:
            return {'success': False, 'error': 'unstructured library not available'}
        try:
            doc = pymupdf.open(file_path)
            all_text = []
            for page in doc:
                text = page.get_text()
                all_text.append(text)
            text = '\n\n'.join(all_text)
            return {'success': True, 'content': text, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading PDF file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _save_image(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        """Save image content to a file"""
        if not PILLOW_AVAILABLE:
            return {'success': False, 'error': 'Pillow library not available'}
        try:
            from io import BytesIO
            if hasattr(content, 'save') and callable(getattr(content, 'save', None)):
                buffer = BytesIO()
                content.save(buffer, format=content.format or 'PNG')
                content_bytes = buffer.getvalue()
                success = self._write_raw(file_path, content_bytes, **kwargs)
                if success:
                    return {'success': True, 'message': f'Image saved to {file_path}', 'file_path': file_path, 'format': content.format, 'size': content.size}
                else:
                    return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
            elif isinstance(content, bytes):
                success = self._write_raw(file_path, content, **kwargs)
                if success:
                    return {'success': True, 'message': f'Image saved to {file_path}', 'file_path': file_path}
                else:
                    return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
            elif isinstance(content, str) and Path(content).exists():
                with open(content, 'rb') as f:
                    content_bytes = f.read()
                success = self._write_raw(file_path, content_bytes, **kwargs)
                if success:
                    return {'success': True, 'message': f'Image copied from {content} to {file_path}', 'file_path': file_path}
                else:
                    return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
            else:
                return {'success': False, 'error': 'Content must be a PIL Image object, binary data, or valid file path'}
        except Exception as e:
            logger.error(f'Error saving image file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _read_image(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Read image and return PIL Image object"""
        if not PILLOW_AVAILABLE:
            return {'success': False, 'error': 'Pillow library not available'}
        try:
            from io import BytesIO
            content_bytes = self._read_raw(file_path, **kwargs)
            with Image.open(BytesIO(content_bytes)) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                metadata = {'format': img.format, 'mode': img.mode, 'size': img.size, 'width': img.width, 'height': img.height}
                return {'success': True, 'content': img, 'metadata': metadata, 'file_path': file_path}
        except Exception as e:
            logger.error(f'Error reading image file {file_path}: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

    def _get_database_connection(self, db_type: str, connection_string: str) -> Any:
        """Placeholder for future database integration"""
        raise NotImplementedError('Database integration not yet implemented')

def translate_in(self, file_path: str) -> str:
    """
        Translate input file path by combining it with base_path.
        This method takes a user-provided path and converts it to the full system path.
        
        Args:
            file_path (str): User-provided file path (can be relative or absolute)
            
        Returns:
            str: Full system path combining base_path and file_path
        """
    if os.path.isabs(file_path):
        return file_path
    if hasattr(self, 'bucket_name') and hasattr(self, 'supabase'):
        if self.base_path.startswith('/'):
            clean_base = self.base_path.lstrip('/')
            if clean_base:
                return f'{clean_base}/{file_path}'
            else:
                return file_path
        else:
            return f'{self.base_path}/{file_path}'
    else:
        combined_path = os.path.join(self.base_path, file_path)
        normalized_path = os.path.normpath(combined_path)
        return normalized_path

def translate_out(self, full_path: str) -> str:
    """
        Translate output full path by removing the base_path prefix.
        This method takes a full system path and converts it back to the user-relative path.
        
        Args:
            full_path (str): Full system path
            
        Returns:
            str: User-relative path with base_path removed
        """
    if self.base_path in ['.', '', None]:
        return full_path
    if hasattr(self, 'bucket_name') and hasattr(self, 'supabase'):
        if self.base_path.startswith('/'):
            clean_base = self.base_path.lstrip('/')
        else:
            clean_base = self.base_path
        if clean_base and full_path.startswith(f'{clean_base}/'):
            relative_path = full_path[len(f'{clean_base}/'):]
            return relative_path
        elif clean_base and full_path == clean_base:
            return ''
        else:
            return full_path
    else:
        base_abs = os.path.abspath(self.base_path)
        full_abs = os.path.abspath(full_path)
        if full_abs.startswith(base_abs):
            relative_path = full_abs[len(base_abs):]
            if relative_path.startswith(os.sep):
                relative_path = relative_path[1:]
            return relative_path
        return full_path

def get_file_info(self, file_path: str) -> Dict[str, Any]:
    """Get comprehensive information about a file"""
    try:
        target_path = self.translate_in(file_path)
        if not self._exists_raw(target_path):
            return {'success': False, 'error': f'File {file_path} does not exist'}
        return {'success': True, 'file_path': target_path, 'file_name': Path(target_path).name, 'file_extension': Path(target_path).suffix.lower(), 'exists': True}
    except Exception as e:
        logger.error(f'Error getting file info for {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def create_directory(self, path: str) -> Dict[str, Any]:
    """Create directory"""
    try:
        target_path = self.translate_in(path)
        success = self._create_directory_raw(target_path)
        if success:
            return {'success': True, 'path': target_path, 'message': 'Directory created successfully'}
        else:
            return {'success': False, 'error': 'Failed to create directory', 'path': target_path}
    except Exception as e:
        logger.error(f'Error creating directory {path}: {str(e)}')
        return {'success': False, 'error': str(e), 'path': path}

def exists(self, path: str) -> bool:
    """Check if path exists"""
    target_path = self.translate_in(path)
    return self._exists_raw(target_path)

def delete(self, path: str) -> Dict[str, Any]:
    """Delete file or directory"""
    try:
        target_path = self.translate_in(path)
        success = self._delete_raw(target_path)
        if success:
            return {'success': True, 'path': target_path, 'message': 'Deleted successfully'}
        else:
            return {'success': False, 'error': 'Failed to delete', 'path': target_path}
    except Exception as e:
        logger.error(f'Error deleting {path}: {str(e)}')
        return {'success': False, 'error': str(e), 'path': path}

def move(self, source: str, destination: str) -> Dict[str, Any]:
    """Move/rename file or directory"""
    try:
        resolved_source = self.translate_in(source)
        resolved_destination = self.translate_in(destination)
        content = self._read_raw(resolved_source)
        success = self._write_raw(resolved_destination, content)
        if success:
            self._delete_raw(resolved_source)
            return {'success': True, 'source': resolved_source, 'destination': resolved_destination, 'message': 'Moved successfully'}
        else:
            return {'success': False, 'error': 'Failed to write to destination', 'source': resolved_source, 'destination': resolved_destination}
    except Exception as e:
        logger.error(f'Error moving {source} to {destination}: {str(e)}')
        return {'success': False, 'error': str(e), 'source': source, 'destination': destination}

def copy(self, source: str, destination: str) -> Dict[str, Any]:
    """Copy file"""
    try:
        resolved_source = self.translate_in(source)
        resolved_destination = self.translate_in(destination)
        content = self._read_raw(resolved_source)
        success = self._write_raw(resolved_destination, content)
        if success:
            return {'success': True, 'source': resolved_source, 'destination': resolved_destination, 'message': 'Copied successfully'}
        else:
            return {'success': False, 'error': 'Failed to write to destination', 'source': resolved_source, 'destination': resolved_destination}
    except Exception as e:
        logger.error(f'Error copying {source} to {destination}: {str(e)}')
        return {'success': False, 'error': str(e), 'source': source, 'destination': destination}

def list(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
    """List files and directories"""
    try:
        target_path = self.translate_in(path) if path else str(self.base_path)
        items = self._list_raw(target_path, max_depth=max_depth, include_hidden=include_hidden)
        return {'success': True, 'path': target_path, 'items': items, 'total_count': len(items)}
    except Exception as e:
        logger.error(f'Error listing {path}: {str(e)}')
        return {'success': False, 'error': str(e), 'path': path}

def save(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
    """
        Save content to a file with automatic format detection.
        This method replaces the old save method with the improved create_file logic.
        
        Args:
            file_path (str): Path where the file should be saved
            content (Any): Content to save to the file
            **kwargs: Additional arguments for file creation (encoding, format, etc.)
            
        Returns:
            Dict[str, Any]: Result of the operation with success status and details
        """
    try:
        file_extension = self.get_file_type(file_path)
        target_file_path = self.translate_in(file_path)
        if file_extension == '.json':
            return self._save_json(target_file_path, content, **kwargs)
        elif file_extension in ['.txt', '.md', '.log']:
            return self._save_text(target_file_path, content, **kwargs)
        elif file_extension == '.csv':
            return self._save_csv(target_file_path, content, **kwargs)
        elif file_extension in ['.yaml', '.yml']:
            return self._save_yaml(target_file_path, content, **kwargs)
        elif file_extension == '.xml':
            return self._save_xml(target_file_path, content, **kwargs)
        elif file_extension == '.xlsx':
            return self._save_excel(target_file_path, content, **kwargs)
        elif file_extension == '.pickle':
            return self._save_pickle(target_file_path, content, **kwargs)
        elif file_extension == '.pdf':
            return self._save_pdf(target_file_path, content, **kwargs)
        elif file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
            return self._save_image(target_file_path, content, **kwargs)
        else:
            if isinstance(content, str):
                content_bytes = content.encode(kwargs.get('encoding', 'utf-8'))
            elif isinstance(content, bytes):
                content_bytes = content
            else:
                content_bytes = str(content).encode(kwargs.get('encoding', 'utf-8'))
            success = self._write_raw(target_file_path, content_bytes, **kwargs)
            if success:
                return {'success': True, 'message': f"File '{file_path}' saved successfully", 'file_path': file_path, 'full_path': target_file_path, 'size': len(content_bytes)}
            else:
                return {'success': False, 'message': f"Failed to save file '{file_path}'", 'file_path': file_path, 'full_path': target_file_path}
    except Exception as e:
        logger.error(f'Error saving file {file_path}: {str(e)}')
        return {'success': False, 'message': f'Error saving file: {str(e)}', 'file_path': file_path}

def append(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
    """Append content to a file (only for supported formats)"""
    try:
        target_file_path = self.translate_in(file_path)
        file_extension = Path(target_file_path).suffix.lower()
        if file_extension in self.appendable_formats:
            return self.appendable_formats[file_extension](target_file_path, content, **kwargs)
        else:
            return {'success': False, 'error': f'Append not supported for {file_extension} files'}
    except Exception as e:
        logger.error(f'Error appending to {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _save_text(self, file_path: str, content: Any, encoding: str='utf-8', **kwargs) -> Dict[str, Any]:
    """Save text content to a file"""
    try:
        if isinstance(content, str):
            content_bytes = content.encode(encoding)
        else:
            content_bytes = str(content).encode(encoding)
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'File saved to {file_path}', 'file_path': file_path, 'content_length': len(content_bytes)}
        else:
            return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error saving text file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _read_text(self, file_path: str, encoding: str='utf-8', **kwargs) -> Dict[str, Any]:
    """Read text content from a file"""
    try:
        content_bytes = self._read_raw(file_path, **kwargs)
        content = content_bytes.decode(encoding)
        return {'success': True, 'content': content, 'file_path': file_path, 'content_length': len(content)}
    except Exception as e:
        logger.error(f'Error reading text file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _append_text(self, file_path: str, content: str, encoding: str='utf-8', **kwargs) -> Dict[str, Any]:
    """Append text content to a file"""
    try:
        content_bytes = str(content).encode(encoding)
        existing_bytes = b''
        if self._exists_raw(file_path):
            existing_bytes = self._read_raw(file_path, **kwargs)
        combined_bytes = existing_bytes + content_bytes
        success = self._write_raw(file_path, combined_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'Content appended to file {file_path}', 'file_path': file_path}
        else:
            return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error appending to text file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _save_json(self, file_path: str, content: Any, indent: int=2, **kwargs) -> Dict[str, Any]:
    """Save JSON content to a file"""
    try:
        if isinstance(content, str):
            json.loads(content)
            json_content = content
        else:
            json_content = json.dumps(content, indent=indent, ensure_ascii=False)
        content_bytes = json_content.encode('utf-8')
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'JSON file saved to {file_path}', 'file_path': file_path}
        else:
            return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error saving JSON file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _read_json(self, file_path: str, **kwargs) -> Dict[str, Any]:
    """Read JSON content from a file"""
    try:
        content_bytes = self._read_raw(file_path, **kwargs)
        content_str = content_bytes.decode('utf-8')
        content = json.loads(content_str)
        return {'success': True, 'content': content, 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error reading JSON file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _append_json(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
    """Append content to JSON file (for arrays)"""
    try:
        existing_content = []
        if self._exists_raw(file_path):
            existing_bytes = self._read_raw(file_path, **kwargs)
            existing_str = existing_bytes.decode('utf-8')
            existing_content = json.loads(existing_str)
        if isinstance(existing_content, list):
            if isinstance(content, list):
                existing_content.extend(content)
            else:
                existing_content.append(content)
        elif isinstance(existing_content, dict):
            if isinstance(content, dict):
                existing_content.update(content)
            else:
                return {'success': False, 'error': 'Cannot append non-dict to JSON dict'}
        else:
            existing_content = [existing_content]
            if isinstance(content, list):
                existing_content.extend(content)
            else:
                existing_content.append(content)
        json_content = json.dumps(existing_content, indent=2, ensure_ascii=False)
        content_bytes = json_content.encode('utf-8')
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'Content appended to JSON file {file_path}', 'file_path': file_path}
        else:
            return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error appending to JSON file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _save_csv(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
    """Save CSV content to a file - handles both raw CSV strings and structured data"""
    try:
        if not content:
            return {'success': False, 'error': 'No content to save'}
        from io import StringIO
        csv_buffer = StringIO()
        if isinstance(content, str):
            csv_content = content
            rows = content.count('\n')
        elif isinstance(content, list) and content and isinstance(content[0], dict):
            fieldnames = content[0].keys()
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(content)
            csv_content = csv_buffer.getvalue()
            rows = len(content)
        elif isinstance(content, list) and content and isinstance(content[0], list):
            writer = csv.writer(csv_buffer)
            writer.writerows(content)
            csv_content = csv_buffer.getvalue()
            rows = len(content)
        else:
            return {'success': False, 'error': 'CSV content must be a string, list of dictionaries, or list of lists'}
        content_bytes = csv_content.encode('utf-8')
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'CSV file saved to {file_path}', 'file_path': file_path, 'rows': rows}
        else:
            return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error saving CSV file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _read_csv(self, file_path: str, **kwargs) -> Dict[str, Any]:
    """Read CSV content from a file"""
    try:
        content_bytes = self._read_raw(file_path, **kwargs)
        content_str = content_bytes.decode('utf-8')
        from io import StringIO
        reader = csv.DictReader(StringIO(content_str))
        content = list(reader)
        return {'success': True, 'content': content, 'file_path': file_path, 'rows': len(content)}
    except Exception as e:
        logger.error(f'Error reading CSV file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _append_csv(self, file_path: str, content: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
    """Append content to CSV file"""
    try:
        if not content:
            return {'success': False, 'error': 'No content to append'}
        existing_content = []
        if self._exists_raw(file_path):
            existing_bytes = self._read_raw(file_path, **kwargs)
            existing_str = existing_bytes.decode('utf-8')
            from io import StringIO
            reader = csv.DictReader(StringIO(existing_str))
            existing_content = list(reader)
        combined_content = existing_content + content
        from io import StringIO
        csv_buffer = StringIO()
        if combined_content:
            fieldnames = combined_content[0].keys()
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(combined_content)
        csv_content = csv_buffer.getvalue()
        content_bytes = csv_content.encode('utf-8')
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'Content appended to CSV file {file_path}', 'file_path': file_path, 'appended_rows': len(content)}
        else:
            return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error appending to CSV file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _save_yaml(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
    """Save YAML content to a file"""
    try:
        yaml_content = yaml.dump(content, default_flow_style=False, allow_unicode=True)
        content_bytes = yaml_content.encode('utf-8')
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'YAML file saved to {file_path}', 'file_path': file_path}
        else:
            return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error saving YAML file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _read_yaml(self, file_path: str, **kwargs) -> Dict[str, Any]:
    """Read YAML content from a file"""
    try:
        content_bytes = self._read_raw(file_path, **kwargs)
        content_str = content_bytes.decode('utf-8')
        content = yaml.safe_load(content_str)
        return {'success': True, 'content': content, 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error reading YAML file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _append_yaml(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
    """Append content to YAML file (for lists)"""
    try:
        existing_content = []
        if self._exists_raw(file_path):
            existing_bytes = self._read_raw(file_path, **kwargs)
            existing_str = existing_bytes.decode('utf-8')
            existing_content = yaml.safe_load(existing_str) or []
        if isinstance(existing_content, list):
            if isinstance(content, list):
                existing_content.extend(content)
            else:
                existing_content.append(content)
        elif isinstance(existing_content, dict):
            if isinstance(content, dict):
                existing_content.update(content)
            else:
                return {'success': False, 'error': 'Cannot append non-dict to YAML dict'}
        else:
            existing_content = [existing_content]
            if isinstance(content, list):
                existing_content.extend(content)
            else:
                existing_content.append(content)
        yaml_content = yaml.dump(existing_content, default_flow_style=False, allow_unicode=True)
        content_bytes = yaml_content.encode('utf-8')
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'Content appended to YAML file {file_path}', 'file_path': file_path}
        else:
            return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error appending to YAML file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _save_xml(self, file_path: str, content: Any, root_tag: str='root', **kwargs) -> Dict[str, Any]:
    """Save XML content to a file"""
    try:
        if isinstance(content, str):
            try:
                ET.fromstring(content)
                xml_content = content
            except ET.ParseError:
                root = ET.Element(root_tag)
                root.text = content
                xml_content = ET.tostring(root, encoding='unicode')
        elif isinstance(content, dict):

            def dict_to_xml(data, root):
                for key, value in data.items():
                    child = ET.SubElement(root, key)
                    if isinstance(value, dict):
                        dict_to_xml(value, child)
                    else:
                        child.text = str(value)
            root = ET.Element(root_tag)
            dict_to_xml(content, root)
            xml_content = ET.tostring(root, encoding='unicode')
        else:
            root = ET.Element(root_tag)
            root.text = str(content)
            xml_content = ET.tostring(root, encoding='unicode')
        content_bytes = xml_content.encode('utf-8')
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'XML file saved to {file_path}', 'file_path': file_path}
        else:
            return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error saving XML file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def dict_to_xml(data, root):
    for key, value in data.items():
        child = ET.SubElement(root, key)
        if isinstance(value, dict):
            dict_to_xml(value, child)
        else:
            child.text = str(value)

def _read_xml(self, file_path: str, **kwargs) -> Dict[str, Any]:
    """Read XML content from a file"""
    try:
        content_bytes = self._read_raw(file_path, **kwargs)
        content_str = content_bytes.decode('utf-8')
        root = ET.fromstring(content_str)

        def xml_to_dict(element):
            result = {}
            for child in element:
                if len(child) == 0:
                    result[child.tag] = child.text
                else:
                    result[child.tag] = xml_to_dict(child)
            return result
        content = xml_to_dict(root)
        return {'success': True, 'content': content, 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error reading XML file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def xml_to_dict(element):
    result = {}
    for child in element:
        if len(child) == 0:
            result[child.tag] = child.text
        else:
            result[child.tag] = xml_to_dict(child)
    return result

def _save_excel(self, file_path: str, content: List[List[Any]], sheet_name: str='Sheet1', **kwargs) -> Dict[str, Any]:
    """Save Excel content to a file"""
    if not EXCEL_AVAILABLE:
        return {'success': False, 'error': 'openpyxl library not available'}
    try:
        from io import BytesIO
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = sheet_name
        for row in content:
            worksheet.append(row)
        buffer = BytesIO()
        workbook.save(buffer)
        content_bytes = buffer.getvalue()
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'Excel file saved to {file_path}', 'file_path': file_path, 'rows': len(content)}
        else:
            return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error saving Excel file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _read_excel(self, file_path: str, sheet_name: str=None, **kwargs) -> Dict[str, Any]:
    """Read Excel content from a file"""
    if not EXCEL_AVAILABLE:
        return {'success': False, 'error': 'openpyxl library not available'}
    try:
        from io import BytesIO
        content_bytes = self._read_raw(file_path, **kwargs)
        workbook = load_workbook(BytesIO(content_bytes), data_only=True)
        sheet_names = workbook.sheetnames
        if sheet_name is None:
            sheet_name = sheet_names[0]
        if sheet_name not in sheet_names:
            return {'success': False, 'error': f"Sheet '{sheet_name}' not found"}
        worksheet = workbook[sheet_name]
        content = []
        for row in worksheet.iter_rows(values_only=True):
            if any((cell is not None for cell in row)):
                content.append(list(row))
        return {'success': True, 'content': content, 'file_path': file_path, 'sheet_name': sheet_name, 'rows': len(content)}
    except Exception as e:
        logger.error(f'Error reading Excel file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _append_excel(self, file_path: str, content: List[List[Any]], sheet_name: str=None, **kwargs) -> Dict[str, Any]:
    """Append content to Excel file"""
    if not EXCEL_AVAILABLE:
        return {'success': False, 'error': 'openpyxl library not available'}
    try:
        from io import BytesIO
        if not self._exists_raw(file_path):
            return self._save_excel(file_path, content, sheet_name or 'Sheet1', **kwargs)
        content_bytes = self._read_raw(file_path, **kwargs)
        workbook = load_workbook(BytesIO(content_bytes))
        sheet_names = workbook.sheetnames
        if sheet_name is None:
            sheet_name = sheet_names[0]
        if sheet_name not in sheet_names:
            return {'success': False, 'error': f"Sheet '{sheet_name}' not found"}
        worksheet = workbook[sheet_name]
        for row in content:
            worksheet.append(row)
        buffer = BytesIO()
        workbook.save(buffer)
        updated_bytes = buffer.getvalue()
        success = self._write_raw(file_path, updated_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'Content appended to Excel file {file_path}', 'file_path': file_path, 'appended_rows': len(content)}
        else:
            return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error appending to Excel file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _save_pickle(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
    """Save pickle content to a file"""
    try:
        content_bytes = pickle.dumps(content)
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'Pickle file saved to {file_path}', 'file_path': file_path}
        else:
            return {'success': False, 'error': 'Failed to write file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error saving pickle file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _read_pickle(self, file_path: str, **kwargs) -> Dict[str, Any]:
    """Read pickle content from a file"""
    try:
        content_bytes = self._read_raw(file_path, **kwargs)
        content = pickle.loads(content_bytes)
        return {'success': True, 'content': content, 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error reading pickle file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _append_pickle(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
    """Append content to pickle file (for lists)"""
    try:
        existing_content = []
        if self._exists_raw(file_path):
            existing_bytes = self._read_raw(file_path, **kwargs)
            existing_content = pickle.loads(existing_bytes)
        if isinstance(existing_content, list):
            if isinstance(content, list):
                existing_content.extend(content)
            else:
                existing_content.append(content)
        elif isinstance(existing_content, dict):
            if isinstance(content, dict):
                existing_content.update(content)
            elif isinstance(content, list):
                existing_content['appended_list'] = content
            else:
                existing_content['appended_value'] = content
        else:
            existing_content = [existing_content]
            if isinstance(content, list):
                existing_content.extend(content)
            else:
                existing_content.append(content)
        content_bytes = pickle.dumps(existing_content)
        success = self._write_raw(file_path, content_bytes, **kwargs)
        if success:
            return {'success': True, 'message': f'Content appended to pickle file {file_path}', 'file_path': file_path}
        else:
            return {'success': False, 'error': 'Failed to append to file', 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error appending to pickle file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

def _read_image(self, file_path: str, **kwargs) -> Dict[str, Any]:
    """Read image and return PIL Image object"""
    if not PILLOW_AVAILABLE:
        return {'success': False, 'error': 'Pillow library not available'}
    try:
        from io import BytesIO
        content_bytes = self._read_raw(file_path, **kwargs)
        with Image.open(BytesIO(content_bytes)) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            metadata = {'format': img.format, 'mode': img.mode, 'size': img.size, 'width': img.width, 'height': img.height}
            return {'success': True, 'content': img, 'metadata': metadata, 'file_path': file_path}
    except Exception as e:
        logger.error(f'Error reading image file {file_path}: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

class DockerInterpreter(BaseInterpreter):
    """
    A Docker-based interpreter for executing Python, Bash, and R scripts in an isolated environment.
    """
    CODE_EXECUTE_CMD_MAPPING: ClassVar[Dict[str, str]] = {'python': 'python {file_name}'}
    CODE_TYPE_MAPPING: ClassVar[Dict[str, str]] = {'python': 'python', 'py3': 'python', 'python3': 'python', 'py': 'python'}
    require_confirm: bool = Field(default=False, description='Whether to require confirmation before executing code')
    print_stdout: bool = Field(default=True, description='Whether to print stdout')
    print_stderr: bool = Field(default=True, description='Whether to print stderr')
    host_directory: str = Field(default='', description='The path to the host directory to use for the container')
    container_directory: str = Field(default='/home/app/', description='The directory to use for the container')
    container_command: str = Field(default='tail -f /dev/null', description='The command to use for the container')
    tmp_directory: str = Field(default='/tmp', description='The directory to use for the container')
    image_tag: Optional[str] = Field(default=None, description='The Docker image tag to use')
    dockerfile_path: Optional[str] = Field(default=None, description='Path to the Dockerfile to build')
    auto_cleanup: bool = Field(default=True, description='Whether to automatically cleanup container on cleanup() call')
    auto_destroy: bool = Field(default=True, description='Whether to automatically cleanup container on object destruction')

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, name: str='DockerInterpreter', image_tag: Optional[str]=None, dockerfile_path: Optional[str]=None, require_confirm: bool=False, print_stdout: bool=True, print_stderr: bool=True, host_directory: str='', container_directory: str='/home/app/', container_command: str='tail -f /dev/null', tmp_directory: str='/tmp', storage_handler: FileStorageHandler=None, auto_cleanup: bool=True, auto_destroy: bool=True, **data):
        """
        Initialize a Docker-based interpreter for executing code in an isolated environment.
        
        Args:
            name (str): The name of the interpreter
            image_tag (str, optional): The Docker image tag to use. Must be provided if dockerfile_path is not.
            dockerfile_path (str, optional): Path to the Dockerfile to build. Must be provided if image_tag is not.
            require_confirm (bool): Whether to require confirmation before executing code
            print_stdout (bool): Whether to print stdout from code execution
            print_stderr (bool): Whether to print stderr from code execution
            host_directory (str): The path to the host directory to mount in the container
            container_directory (str): The target directory inside the container
            container_command (str): The command to run in the container
            tmp_directory (str): The temporary directory to use for file creation in the container
            **data: Additional data to pass to the parent class
        """
        super().__init__(name=name, **data)
        self.require_confirm = require_confirm
        self.print_stdout = print_stdout
        self.print_stderr = print_stderr
        self.host_directory = host_directory
        self.container_directory = container_directory
        self.container_command = container_command
        self.tmp_directory = tmp_directory
        self.client = docker.from_env()
        self.container = None
        self.image_tag = image_tag
        self.dockerfile_path = dockerfile_path
        self.storage_handler = storage_handler
        self.auto_cleanup = auto_cleanup
        self.auto_destroy = auto_destroy
        self._initialize_if_needed()
        if self.host_directory:
            self._upload_directory_to_container(self.host_directory)

    def __del__(self):
        try:
            if hasattr(self, 'auto_destroy') and self.auto_destroy and hasattr(self, 'container') and (self.container is not None):
                self.container.remove(force=True)
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Explicitly clean up the container and Docker client."""
        if self.auto_cleanup:
            try:
                if hasattr(self, 'container') and self.container is not None:
                    self.container.remove(force=True)
                    self.container = None
            except Exception:
                pass
            try:
                if hasattr(self, 'client') and self.client is not None:
                    self.client.close()
                    self.client = None
            except Exception:
                pass

    def _initialize_if_needed(self):
        image_tag = self.image_tag
        dockerfile_path = self.dockerfile_path
        if image_tag:
            try:
                self.client.images.get(image_tag)
            except Exception as e:
                raise ValueError(f'Image provided in image_tag but not found: {e}')
        else:
            if not dockerfile_path:
                raise ValueError('dockerfile_path or image_tag must be provided to build the image')
            dockerfile_path = Path(dockerfile_path)
            if not dockerfile_path.exists():
                raise FileNotFoundError(f'Dockerfile not found at provided path: {dockerfile_path}')
            dockerfile_dir = dockerfile_path.parent
            self.client.images.build(path=str(dockerfile_dir), tag=image_tag, rm=True, buildargs={})
        try:
            self.client.ping()
        except Exception as e:
            raise RuntimeError(f'Docker daemon is not running: {e}')
        self.container = self.client.containers.run(image_tag, detach=True, command=self.container_command, working_dir=self.container_directory)

    def _upload_directory_to_container(self, host_directory: str):
        """
        Uploads all files and directories from the given host directory to the container directory.

        :param host_directory: Path to the local directory containing files to upload.
        :param container_directory: Target directory inside the container (defaults to self.container_directory).
        """
        host_directory = Path(host_directory).resolve()
        if not host_directory.exists() or not host_directory.is_dir():
            raise FileNotFoundError(f'Directory not found: {host_directory}')
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            for file_path in host_directory.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(host_directory)
                    target_path = Path(self.container_directory) / relative_path
                    tarinfo = tarfile.TarInfo(name=str(target_path.relative_to(self.container_directory)))
                    tarinfo.size = file_path.stat().st_size
                    with open(file_path, 'rb') as f:
                        tar.addfile(tarinfo, f)
        tar_stream.seek(0)
        if self.container is None:
            raise RuntimeError('Container is not initialized.')
        self.container.put_archive(self.container_directory, tar_stream)

    def _create_file_in_container(self, content: str) -> Path:
        filename = str(uuid.uuid4())
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content.encode('utf-8'))
            tar.addfile(tarinfo, io.BytesIO(content.encode('utf-8')))
        tar_stream.seek(0)
        if self.container is None:
            raise RuntimeError('Container is not initialized.')
        try:
            self.container.put_archive(self.tmp_directory, tar_stream)
        except Exception as e:
            raise RuntimeError(f'Failed to create file in container: {e}')
        return Path(f'{self.tmp_directory}/{filename}')

    def _run_file_in_container(self, file: Path, language: str) -> str:
        """Execute a file in the container with timeout and security checks."""
        if not self.container:
            raise RuntimeError('Container is not initialized')
        container_info = self.client.api.inspect_container(self.container.id)
        if not container_info['State']['Running']:
            raise RuntimeError('Container is not running')
        language = self._check_language(language)
        command = shlex.split(self.CODE_EXECUTE_CMD_MAPPING[language].format(file_name=file.as_posix()))
        if self.container is None:
            raise RuntimeError('Container is not initialized.')
        result = self.container.exec_run(command, demux=True)
        stdout, stderr = result.output
        if self.print_stdout and stdout:
            print(stdout.decode())
        if self.print_stderr and stderr:
            print(stderr.decode())
        stdout_str = stdout.decode() if stdout else ''
        stderr_str = stderr.decode() if stderr else ''
        return stdout_str + stderr_str

    def execute(self, code: str, language: str) -> str:
        """
        Executes code in a Docker container.
        
        Args:
            code (str): The code to execute
            language (str): The programming language to use
            
        Returns:
            str: The execution output
            
        Raises:
            RuntimeError: If container is not properly initialized or execution fails
            ValueError: If code content is invalid or exceeds limits
        """
        if not code or not code.strip():
            raise ValueError('Code content cannot be empty')
        if not self.container:
            raise RuntimeError('Container is not initialized')
        try:
            container_info = self.client.api.inspect_container(self.container.id)
            if not container_info['State']['Running']:
                raise RuntimeError('Container is not running')
        except Exception as e:
            raise RuntimeError(f'Failed to check container status: {e}')
        if self.host_directory:
            code = f"import sys; sys.path.insert(0, '{self.container_directory}');" + code
        language = self._check_language(language)
        if self.require_confirm:
            confirmation = input(f'Confirm execution of {language} code? [Y/n]: ')
            if confirmation.lower() not in ['y', 'yes', '']:
                raise RuntimeError('Execution aborted by user.')
        try:
            file_path = self._create_file_in_container(code)
            return self._run_file_in_container(file_path, language)
        except Exception as e:
            raise RuntimeError(f'Code execution failed: {e}')
        finally:
            try:
                if hasattr(self, 'container') and self.container:
                    self.container.exec_run(f'rm -f {file_path}')
            except Exception:
                pass

    def execute_script(self, file_path: str, language: str=None) -> str:
        """
        Reads code from a file and executes it in a Docker container.
        
        Args:
            file_path (str): The path to the script file to execute
            language (str, optional): The programming language of the code. If None, will be determined from the file extension.
                                    
        Returns:
            str: The execution output
            
        Raises:
            FileNotFoundError: If the script file does not exist
            RuntimeError: If container is not properly initialized or execution fails
            ValueError: If file content is invalid or exceeds limits
        """
        result = self.storage_handler.read(file_path)
        if result['success']:
            code = result['content']
        else:
            raise RuntimeError(f"Could not read file '{file_path}': {result.get('error', 'Unknown error')}")
        return self.execute(code, language)

    def _check_language(self, language: str) -> str:
        if language not in self.CODE_TYPE_MAPPING:
            raise ValueError(f'Unsupported language: {language}')
        return self.CODE_TYPE_MAPPING[language]

def _initialize_if_needed(self):
    image_tag = self.image_tag
    dockerfile_path = self.dockerfile_path
    if image_tag:
        try:
            self.client.images.get(image_tag)
        except Exception as e:
            raise ValueError(f'Image provided in image_tag but not found: {e}')
    else:
        if not dockerfile_path:
            raise ValueError('dockerfile_path or image_tag must be provided to build the image')
        dockerfile_path = Path(dockerfile_path)
        if not dockerfile_path.exists():
            raise FileNotFoundError(f'Dockerfile not found at provided path: {dockerfile_path}')
        dockerfile_dir = dockerfile_path.parent
        self.client.images.build(path=str(dockerfile_dir), tag=image_tag, rm=True, buildargs={})
    try:
        self.client.ping()
    except Exception as e:
        raise RuntimeError(f'Docker daemon is not running: {e}')
    self.container = self.client.containers.run(image_tag, detach=True, command=self.container_command, working_dir=self.container_directory)

def _upload_directory_to_container(self, host_directory: str):
    """
        Uploads all files and directories from the given host directory to the container directory.

        :param host_directory: Path to the local directory containing files to upload.
        :param container_directory: Target directory inside the container (defaults to self.container_directory).
        """
    host_directory = Path(host_directory).resolve()
    if not host_directory.exists() or not host_directory.is_dir():
        raise FileNotFoundError(f'Directory not found: {host_directory}')
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        for file_path in host_directory.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(host_directory)
                target_path = Path(self.container_directory) / relative_path
                tarinfo = tarfile.TarInfo(name=str(target_path.relative_to(self.container_directory)))
                tarinfo.size = file_path.stat().st_size
                with open(file_path, 'rb') as f:
                    tar.addfile(tarinfo, f)
    tar_stream.seek(0)
    if self.container is None:
        raise RuntimeError('Container is not initialized.')
    self.container.put_archive(self.container_directory, tar_stream)

def _create_file_in_container(self, content: str) -> Path:
    filename = str(uuid.uuid4())
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        tarinfo = tarfile.TarInfo(name=filename)
        tarinfo.size = len(content.encode('utf-8'))
        tar.addfile(tarinfo, io.BytesIO(content.encode('utf-8')))
    tar_stream.seek(0)
    if self.container is None:
        raise RuntimeError('Container is not initialized.')
    try:
        self.container.put_archive(self.tmp_directory, tar_stream)
    except Exception as e:
        raise RuntimeError(f'Failed to create file in container: {e}')
    return Path(f'{self.tmp_directory}/{filename}')

class DockerExecuteTool(Tool):
    name: str = 'docker_execute'
    description: str = 'Execute code in a secure Docker container environment'
    inputs: Dict[str, Dict[str, str]] = {'code': {'type': 'string', 'description': 'The code to execute'}, 'language': {'type': 'string', 'description': 'The programming language of the code (e.g., python, py, python3)'}}
    required: Optional[List[str]] = ['code', 'language']

    def __init__(self, docker_interpreter: DockerInterpreter=None):
        super().__init__()
        self.docker_interpreter = docker_interpreter

    def __call__(self, code: str, language: str) -> str:
        """Execute code using the Docker interpreter."""
        if not self.docker_interpreter:
            raise RuntimeError('Docker interpreter not initialized')
        try:
            return self.docker_interpreter.execute(code, language)
        except Exception as e:
            return f'Error executing code: {str(e)}'

def __call__(self, code: str, language: str) -> str:
    """Execute code using the Docker interpreter."""
    if not self.docker_interpreter:
        raise RuntimeError('Docker interpreter not initialized')
    try:
        return self.docker_interpreter.execute(code, language)
    except Exception as e:
        return f'Error executing code: {str(e)}'

class DockerExecuteScriptTool(Tool):
    name: str = 'docker_execute_script'
    description: str = 'Execute code from a script file in a secure Docker container environment'
    inputs: Dict[str, Dict[str, str]] = {'file_path': {'type': 'string', 'description': 'The path to the script file to execute'}, 'language': {'type': 'string', 'description': 'The programming language of the code. If not provided, will be determined from file extension'}}
    required: Optional[List[str]] = ['file_path', 'language']

    def __init__(self, docker_interpreter: DockerInterpreter=None):
        super().__init__()
        self.docker_interpreter = docker_interpreter

    def __call__(self, file_path: str, language: str) -> str:
        """Execute script file using the Docker interpreter."""
        if not self.docker_interpreter:
            raise RuntimeError('Docker interpreter not initialized')
        try:
            return self.docker_interpreter.execute_script(file_path, language)
        except Exception as e:
            return f'Error executing script: {str(e)}'

def __call__(self, file_path: str, language: str) -> str:
    """Execute script file using the Docker interpreter."""
    if not self.docker_interpreter:
        raise RuntimeError('Docker interpreter not initialized')
    try:
        return self.docker_interpreter.execute_script(file_path, language)
    except Exception as e:
        return f'Error executing script: {str(e)}'

class WikipediaSearchTool(Tool):
    name: str = 'wikipedia_search'
    description: str = 'Search Wikipedia for relevant articles and content'
    inputs: Dict[str, Dict[str, str]] = {'query': {'type': 'string', 'description': 'The search query to look up on Wikipedia'}, 'num_search_pages': {'type': 'integer', 'description': 'Number of search results to retrieve. Default: 5'}, 'max_content_words': {'type': 'integer', 'description': 'Maximum number of words to include in content per result. None means no limit. Default: None'}, 'max_summary_sentences': {'type': 'integer', 'description': 'Maximum number of sentences in the summary. None means no limit. Default: None'}}
    required: Optional[List[str]] = ['query']

    def __init__(self, search_wiki: SearchWiki=None):
        super().__init__()
        self.search_wiki = search_wiki

    def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None, max_summary_sentences: int=None) -> Dict[str, Any]:
        """Execute Wikipedia search using the SearchWiki instance."""
        if not self.search_wiki:
            raise RuntimeError('Wikipedia search instance not initialized')
        try:
            return self.search_wiki.search(query, num_search_pages, max_content_words, max_summary_sentences)
        except Exception as e:
            return {'results': [], 'error': f'Error executing Wikipedia search: {str(e)}'}

def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None, max_summary_sentences: int=None) -> Dict[str, Any]:
    """Execute Wikipedia search using the SearchWiki instance."""
    if not self.search_wiki:
        raise RuntimeError('Wikipedia search instance not initialized')
    try:
        return self.search_wiki.search(query, num_search_pages, max_content_words, max_summary_sentences)
    except Exception as e:
        return {'results': [], 'error': f'Error executing Wikipedia search: {str(e)}'}

class PythonExecuteTool(Tool):
    name: str = 'python_execute'
    description: str = 'Execute Python code in a controlled environment with safety checks'
    inputs: Dict[str, Dict[str, str]] = {'code': {'type': 'string', 'description': 'The Python code to execute'}, 'language': {'type': 'string', 'description': "The programming language of the code (only 'python' is supported)"}}
    required: Optional[List[str]] = ['code']

    def __init__(self, python_interpreter: PythonInterpreter=None):
        super().__init__()
        self.python_interpreter = python_interpreter

    def __call__(self, code: str, language: str='python') -> str:
        """Execute Python code using the Python interpreter."""
        if not self.python_interpreter:
            raise RuntimeError('Python interpreter not initialized')
        try:
            return self.python_interpreter.execute(code, language)
        except Exception as e:
            return f'Error executing code: {str(e)}'

def __call__(self, code: str, language: str='python') -> str:
    """Execute Python code using the Python interpreter."""
    if not self.python_interpreter:
        raise RuntimeError('Python interpreter not initialized')
    try:
        return self.python_interpreter.execute(code, language)
    except Exception as e:
        return f'Error executing code: {str(e)}'

class PythonExecuteScriptTool(Tool):
    name: str = 'python_execute_script'
    description: str = 'Execute Python code from a file in a controlled environment with safety checks'
    inputs: Dict[str, Dict[str, str]] = {'file_path': {'type': 'string', 'description': 'The path to the Python file to be executed'}, 'language': {'type': 'string', 'description': "The programming language of the code (only 'python' is supported)"}}
    required: Optional[List[str]] = ['file_path']

    def __init__(self, python_interpreter: PythonInterpreter=None):
        super().__init__()
        self.python_interpreter = python_interpreter

    def __call__(self, file_path: str, language: str='python') -> str:
        """Execute Python script file using the Python interpreter."""
        if not self.python_interpreter:
            raise RuntimeError('Python interpreter not initialized')
        try:
            return self.python_interpreter.execute_script(file_path, language)
        except Exception as e:
            return f'Error executing script: {str(e)}'

def __call__(self, file_path: str, language: str='python') -> str:
    """Execute Python script file using the Python interpreter."""
    if not self.python_interpreter:
        raise RuntimeError('Python interpreter not initialized')
    try:
        return self.python_interpreter.execute_script(file_path, language)
    except Exception as e:
        return f'Error executing script: {str(e)}'

class RSSBase(RequestBase):
    """
    Base class for RSS feed operations.
    Provides common functionality for fetching, parsing, and processing RSS feeds.
    """

    def __init__(self, timeout: int=30, max_retries: int=3, delay_between_requests: float=1.0):
        """
        Initialize the RSS base with configuration options.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            delay_between_requests: Delay between requests in seconds
        """
        super().__init__(timeout=timeout, max_retries=max_retries, delay_between_requests=delay_between_requests)

    def fetch_rss_feed(self, feed_url: str, max_entries: Optional[int]=10, fetch_webpage_content: bool=True) -> Dict[str, Any]:
        """
        Fetch and parse an RSS feed from a URL.
        
        Args:
            feed_url: URL of the RSS feed
            max_entries: Maximum number of entries to return (default: 10, None for all)
            fetch_webpage_content: Whether to fetch and extract content from article webpages (default: True)
            
        Returns:
            Dictionary containing parsed feed information
        """
        try:
            response = self.request(url=feed_url, method='GET')
            feed = feedparser.parse(response.content)
            if feed.bozo:
                logger.warning(f'RSS feed parsing warnings for {feed_url}: {feed.bozo_exception}')
            feed_info = {'success': True, 'feed_url': feed_url, 'title': getattr(feed.feed, 'title', 'Unknown'), 'description': getattr(feed.feed, 'description', ''), 'link': getattr(feed.feed, 'link', ''), 'language': getattr(feed.feed, 'language', ''), 'updated': getattr(feed.feed, 'updated', ''), 'generator': getattr(feed.feed, 'generator', ''), 'total_entries': len(feed.entries), 'entries': []}
            entries = feed.entries[:max_entries] if max_entries is not None else feed.entries
            for entry in entries:
                processed_entry = self._process_entry(entry, feed_url, fetch_webpage_content)
                feed_info['entries'].append(processed_entry)
            return feed_info
        except Exception as e:
            logger.error(f'Error fetching RSS feed from {feed_url}: {str(e)}')
            return {'success': False, 'error': str(e), 'feed_url': feed_url}

    def _process_entry(self, entry, base_url: str, fetch_webpage_content: bool=True) -> Dict[str, Any]:
        """
        Process a single RSS entry and extract relevant information.
        
        Args:
            entry: FeedParser entry object
            base_url: Base URL for resolving relative links
            fetch_webpage_content: Whether to fetch and extract content from the article webpage
            
        Returns:
            Dictionary with processed entry information
        """
        processed_entry = {'title': getattr(entry, 'title', ''), 'description': getattr(entry, 'description', ''), 'link': getattr(entry, 'link', ''), 'published': getattr(entry, 'published', ''), 'author': getattr(entry, 'author', ''), 'id': getattr(entry, 'id', ''), 'summary': getattr(entry, 'summary', ''), 'content': getattr(entry, 'content', []), 'tags': [], 'categories': [], 'enclosures': []}
        if processed_entry['link'] and (not processed_entry['link'].startswith(('http://', 'https://'))):
            processed_entry['link'] = urljoin(base_url, processed_entry['link'])
        if hasattr(entry, 'tags'):
            processed_entry['tags'] = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
        if hasattr(entry, 'category'):
            processed_entry['categories'] = [entry.category] if isinstance(entry.category, str) else entry.category
        if hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                processed_entry['enclosures'].append({'url': getattr(enclosure, 'href', ''), 'type': getattr(enclosure, 'type', ''), 'length': getattr(enclosure, 'length', ''), 'title': getattr(enclosure, 'title', '')})
        processed_entry['published_parsed'] = self._parse_date(entry.published_parsed)
        processed_entry['title'] = self._clean_text(processed_entry['title'])
        processed_entry['description'] = self._clean_text(processed_entry['description'])
        processed_entry['summary'] = self._clean_text(processed_entry['summary'])
        if fetch_webpage_content and processed_entry['link']:
            result = self.request_and_process(url=processed_entry['link'], method='GET')
            if result.get('success') and result.get('content'):
                text_content = self._clean_text(result['content'])
                if len(text_content) > 10000:
                    text_content = text_content[:10000] + '... [Content truncated]'
                processed_entry['webpage_content'] = text_content
                processed_entry['webpage_content_fetched'] = True
            else:
                processed_entry['webpage_content_fetched'] = False
        else:
            processed_entry['webpage_content_fetched'] = False
        return processed_entry

    def _parse_date(self, date_tuple) -> Optional[str]:
        """
        Parse a date tuple from feedparser into ISO format string.
        
        Args:
            date_tuple: Date tuple from feedparser
            
        Returns:
            ISO format date string or None
        """
        if not date_tuple:
            return None
        try:
            dt = datetime(*date_tuple[:6])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            return None

    def _clean_text(self, text: str) -> str:
        """
        Clean HTML tags and normalize whitespace in text.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text content
        """
        if not text:
            return ''
        text = re.sub('<[^>]+>', '', text)
        text = re.sub('\\s+', ' ', text.strip())
        return text

    def validate_rss_url(self, url: str) -> Dict[str, Any]:
        """
        Validate if a URL contains a valid RSS feed.
        
        Args:
            url: URL to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            response = self.request(url=url, method='GET')
            content = response.content
            try:
                root = ET.fromstring(content)
            except ET.ParseError:
                return {'success': False, 'error': 'Invalid XML content', 'url': url}
            is_rss = root.tag.endswith('rss') or root.tag.endswith('RDF')
            is_atom = root.tag.endswith('feed') or 'atom' in root.tag
            if is_rss or is_atom:
                return {'success': True, 'is_valid': True, 'feed_type': 'RSS' if is_rss else 'Atom', 'url': url, 'title': self._extract_feed_title(root)}
            else:
                return {'success': True, 'is_valid': False, 'error': 'Not a valid RSS or Atom feed', 'url': url}
        except Exception as e:
            return {'success': False, 'error': str(e), 'url': url}

    def _extract_feed_title(self, root) -> str:
        """
        Extract feed title from XML root element.
        
        Args:
            root: XML root element
            
        Returns:
            Feed title or empty string
        """
        title_selectors = ['.//title', './/channel/title', './/feed/title']
        for selector in title_selectors:
            title_elem = root.find(selector)
            if title_elem is not None and title_elem.text:
                return self._clean_text(title_elem.text)
        return ''

def validate_rss_url(self, url: str) -> Dict[str, Any]:
    """
        Validate if a URL contains a valid RSS feed.
        
        Args:
            url: URL to validate
            
        Returns:
            Dictionary with validation results
        """
    try:
        response = self.request(url=url, method='GET')
        content = response.content
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return {'success': False, 'error': 'Invalid XML content', 'url': url}
        is_rss = root.tag.endswith('rss') or root.tag.endswith('RDF')
        is_atom = root.tag.endswith('feed') or 'atom' in root.tag
        if is_rss or is_atom:
            return {'success': True, 'is_valid': True, 'feed_type': 'RSS' if is_rss else 'Atom', 'url': url, 'title': self._extract_feed_title(root)}
        else:
            return {'success': True, 'is_valid': False, 'error': 'Not a valid RSS or Atom feed', 'url': url}
    except Exception as e:
        return {'success': False, 'error': str(e), 'url': url}

def _ensure_database_path(db_path: str) -> str:
    """
    Ensure the database path exists and is properly configured.
    
    Args:
        db_path (str): The database file path
        
    Returns:
        str: The validated and prepared database path
        
    Raises:
        ValueError: If the path is invalid or cannot be created
    """
    if not db_path:
        raise ValueError('Database path cannot be empty')
    path = Path(db_path).resolve()
    if path.exists() and path.is_dir():
        raise ValueError(f'Database path points to a directory: {db_path}')
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ValueError(f'Cannot create directory for database path {db_path}: {e}')
    if path.exists():
        logger.info(f'Found existing database at: {db_path}')
        try:
            import sqlite3
            conn = sqlite3.connect(str(path))
            conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            conn.close()
            logger.info('Database validation successful')
        except Exception as e:
            logger.warning(f'Database validation failed: {e}. Will create new database.')
            try:
                path.unlink()
            except Exception as unlink_error:
                logger.error(f'Failed to remove corrupted database file: {unlink_error}')
                raise ValueError(f'Cannot remove corrupted database file: {unlink_error}')
    else:
        logger.info(f'Database not found at: {db_path}. Will create new database.')
    return str(path)

class FaissDatabase(BaseModule):
    """
    A high-level interface for FAISS vector database operations.
    
    This class wraps the RAGEngine and StorageHandler to provide a unified interface
    for vector database operations including document ingestion, semantic search,
    and corpus management.
    
    Attributes:
        rag_engine (RAGEngine): The RAG engine for document processing and retrieval
        storage_handler (StorageHandler): The storage handler for persistence
        default_corpus_id (str): Default corpus ID for operations
        default_index_type (str): Default index type for vector operations
    """

    def __init__(self, storage_config: StoreConfig, rag_config: RAGConfig, default_corpus_id: str='default', default_index_type: str='vector', storage_handler: StorageHandler=None, file_handler: FileStorageHandler=None, **kwargs):
        """
        Initialize the FAISS database.
        
        Args:
            storage_config (StoreConfig): Configuration for storage backends
            rag_config (RAGConfig): Configuration for RAG pipeline
            default_corpus_id (str): Default corpus ID for operations
            default_index_type (str): Default index type for vector operations
            storage_handler (StorageHandler, optional): Storage handler for file operations
            **kwargs: Additional arguments for BaseModule
        """
        super().__init__(**kwargs)
        self.storage_handler = StorageHandler(storageConfig=storage_config)
        self.rag_engine = RAGEngine(config=rag_config, storage_handler=self.storage_handler)
        if storage_handler is None:
            storage_handler = LocalStorageHandler(base_path='./workplace/storage')
        self.file_storage_handler = storage_handler
        self.default_corpus_id = default_corpus_id
        self.default_index_type = default_index_type
        logger.info(f'Initialized FAISS database with corpus_id: {default_corpus_id}')

    def query(self, query: str, corpus_id: Optional[str]=None, top_k: int=5, similarity_threshold: float=0.0, metadata_filters: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """
        Query the vector database with semantic search.
        
        Args:
            query (str): The query string to search for
            corpus_id (str, optional): Corpus ID to search in
            top_k (int): Number of top results to return
            similarity_threshold (float): Minimum similarity threshold
            metadata_filters (Dict[str, Any], optional): Metadata filters for search
            
        Returns:
            Dict[str, Any]: Search results with chunks and scores
        """
        try:
            try:
                asyncio.get_running_loop()
                logger.info('Detected running event loop, using thread executor for query')
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._query_sync, query, corpus_id, top_k, similarity_threshold, metadata_filters)
                    return future.result()
            except RuntimeError:
                logger.info('No event loop detected, using direct query processing')
                return self._query_sync(query, corpus_id, top_k, similarity_threshold, metadata_filters)
        except Exception as e:
            logger.error(f'Query failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def _query_sync(self, query: str, corpus_id: Optional[str]=None, top_k: int=5, similarity_threshold: float=0.0, metadata_filters: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """
        Synchronous version of query that can be safely called from a thread.
        
        Args:
            query (str): The query string to search for
            corpus_id (str, optional): Corpus ID to search in
            top_k (int): Number of top results to return
            similarity_threshold (float): Minimum similarity threshold
            metadata_filters (Dict[str, Any], optional): Metadata filters for search
            
        Returns:
            Dict[str, Any]: Search results with chunks and scores
        """
        try:
            corpus_id = corpus_id or self.default_corpus_id
            if corpus_id not in self.rag_engine.indices:
                logger.warning(f'Corpus {corpus_id} not found. Returning empty results.')
                return {'success': True, 'data': {'query': query, 'corpus_id': corpus_id, 'total_results': 0, 'results': []}}
            query_obj = Query(query_str=query, top_k=top_k, similarity_cutoff=similarity_threshold, metadata_filters=metadata_filters)
            results = self.rag_engine.query(query_obj, corpus_id=corpus_id)
            if not results or not results.corpus:
                logger.warning(f'Query returned no results for corpus {corpus_id}')
                return {'success': True, 'data': {'query': query, 'corpus_id': corpus_id, 'total_results': 0, 'results': []}}
            chunks = results.corpus.chunks if results.corpus.chunks else []
            formatted_results = {'query': query, 'corpus_id': corpus_id, 'total_results': len(chunks), 'results': []}
            for i, chunk in enumerate(chunks):
                score = results.scores[i] if results.scores and i < len(results.scores) else 0.0
                formatted_results['results'].append({'chunk_id': chunk.chunk_id, 'content': chunk.text, 'score': score, 'metadata': chunk.metadata.model_dump() if chunk.metadata else {}, 'doc_id': chunk.metadata.doc_id if chunk.metadata else None})
            logger.info(f'Query executed successfully. Found {len(formatted_results['results'])} results.')
            return {'success': True, 'data': formatted_results}
        except Exception as e:
            logger.error(f'Query failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def _is_file_path(self, text: str) -> bool:
        """
        Check if a string appears to be a file path.
        
        Args:
            text (str): The string to check
            
        Returns:
            bool: True if the string looks like a file path
        """
        path_indicators = ['/', '\\', '.txt', '.pdf', '.md', '.doc', '.docx', '.csv', '.json', '.xml', '.html', '.htm']
        return any((indicator in text for indicator in path_indicators)) and os.path.exists(text)

    def _process_file_path(self, file_path: str, doc_index: int, metadata: Optional[Dict[str, Any]]=None) -> List[Document]:
        """
        Process a file path and return Document objects.
        
        Args:
            file_path (str): Path to the file
            doc_index (int): Index of the document in the batch
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            List[Document]: List of Document objects created from the file
        """
        try:
            try:
                asyncio.get_running_loop()
                logger.info(f'Detected running event loop, using thread executor for {file_path}')
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._process_file_path_sync, file_path, doc_index, metadata)
                    return future.result()
            except RuntimeError:
                logger.info(f'No event loop detected, using direct processing for {file_path}')
                return self._process_file_path_sync(file_path, doc_index, metadata)
        except Exception as e:
            logger.error(f'Failed to process file {file_path}: {str(e)}')
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'error': str(e)})
            document_metadata = DocumentMetadata(**doc_metadata)
            return [Document(text=f'Error reading file {file_path}: {str(e)}', metadata=document_metadata, doc_id=str(uuid4()))]

    def _process_file_path_sync(self, file_path: str, doc_index: int, metadata: Optional[Dict[str, Any]]=None) -> List[Document]:
        """
        Synchronous version of file processing that can be safely called from a thread.
        
        Args:
            file_path (str): Path to the file
            doc_index (int): Index of the document in the batch
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            List[Document]: List of Document objects created from the file
        """
        try:
            if self.file_storage_handler:
                result = self.file_storage_handler.read(file_path)
                if result['success']:
                    file_content = result['content']
                else:
                    raise Exception(f'Failed to read file: {result.get('error', 'Unknown error')}')
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            temp_corpus_id = f'temp_file_{uuid4().hex[:8]}'
            temp_doc = Document(text=file_content, metadata=DocumentMetadata(source_file=file_path, doc_index=doc_index, insertion_time=datetime.now().isoformat()), doc_id=str(uuid4()))
            corpus = self.rag_engine.process_documents([temp_doc], corpus_id=temp_corpus_id)
            documents = []
            for chunk in corpus.chunks:
                doc_metadata = metadata.copy() if metadata else {}
                doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'original_chunk_id': chunk.chunk_id})
                document_metadata = DocumentMetadata(**doc_metadata)
                documents.append(Document(text=chunk.text, metadata=document_metadata, doc_id=chunk.chunk_id))
            self.rag_engine.clear(corpus_id=temp_corpus_id)
            logger.info(f'Processed file {file_path} into {len(documents)} chunks')
            return documents
        except Exception as e:
            logger.error(f'Failed to process file {file_path} in sync mode: {str(e)}')
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'error': str(e)})
            document_metadata = DocumentMetadata(**doc_metadata)
            return [Document(text=f'Error reading file {file_path}: {str(e)}', metadata=document_metadata, doc_id=str(uuid4()))]

    def insert(self, documents: list, corpus_id: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None, batch_size: int=100) -> Dict[str, Any]:
        """
        Insert documents into the vector database.
        
        Args:
            documents (Union[List[str], List[Dict[str, Any]]]): Documents to insert. 
                Strings can be either text content or file paths (if they look like paths and exist)
            corpus_id (str, optional): Corpus ID to insert into
            metadata (Dict[str, Any], optional): Additional metadata for all documents
            batch_size (int): Batch size for processing
            
        Returns:
            Dict[str, Any]: Insertion results
        """
        try:
            corpus_id = corpus_id or self.default_corpus_id
            processed_docs = []
            file_paths_processed = []
            for i, doc in enumerate(documents):
                if isinstance(doc, str):
                    if self._is_file_path(doc):
                        logger.info(f'Detected file path: {doc}')
                        file_docs = self._process_file_path(doc, i, metadata)
                        processed_docs.extend(file_docs)
                        file_paths_processed.append(doc)
                    else:
                        doc_metadata = metadata.copy() if metadata else {}
                        doc_metadata.update({'doc_index': i, 'insertion_time': datetime.now().isoformat()})
                        document_metadata = DocumentMetadata(**doc_metadata)
                        processed_docs.append(Document(text=doc, metadata=document_metadata, doc_id=str(uuid4())))
                elif isinstance(doc, dict):
                    doc_metadata = metadata.copy() if metadata else {}
                    doc_metadata.update(doc.get('metadata', {}))
                    doc_metadata.update({'doc_index': i, 'insertion_time': datetime.now().isoformat()})
                    document_metadata = DocumentMetadata(**doc_metadata)
                    processed_docs.append(Document(text=doc.get('text', ''), metadata=document_metadata, doc_id=doc.get('doc_id', str(uuid4()))))
            corpus = Corpus(corpus_id=corpus_id)
            total_processed = 0
            for i in range(0, len(processed_docs), batch_size):
                batch = processed_docs[i:i + batch_size]
                batch_corpus = self.rag_engine.chunker.chunk(batch)
                batch_corpus.corpus_id = corpus_id
                self.rag_engine.add(self.default_index_type, batch_corpus, corpus_id=corpus_id)
                corpus.chunks.extend(batch_corpus.chunks)
                total_processed += len(batch)
                logger.info(f'Processed batch {i // batch_size + 1}, total processed: {total_processed}')
            self.rag_engine.save(corpus_id=corpus_id, index_type=self.default_index_type)
            result = {'corpus_id': corpus_id, 'documents_inserted': len(documents), 'chunks_created': len(corpus.chunks), 'total_processed': total_processed, 'file_paths_processed': file_paths_processed}
            logger.info(f'Successfully inserted {len(documents)} documents into corpus {corpus_id}')
            if file_paths_processed:
                logger.info(f'Processed {len(file_paths_processed)} file paths: {file_paths_processed}')
            return {'success': True, 'data': result}
        except Exception as e:
            logger.error(f'Insert failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def delete(self, corpus_id: Optional[str]=None, doc_ids: Optional[List[str]]=None, metadata_filters: Optional[Dict[str, Any]]=None, clear_all: bool=False) -> Dict[str, Any]:
        """
        Delete documents or chunks from the vector database.
        
        Args:
            corpus_id (str, optional): Corpus ID to delete from
            doc_ids (List[str], optional): Document IDs to delete
            metadata_filters (Dict[str, Any], optional): Metadata filters for deletion
            clear_all (bool): Whether to clear the entire corpus
            
        Returns:
            Dict[str, Any]: Deletion results
        """
        try:
            corpus_id = corpus_id or self.default_corpus_id
            if clear_all:
                self.rag_engine.clear(corpus_id=corpus_id)
                logger.info(f'Cleared entire corpus: {corpus_id}')
                return {'success': True, 'data': {'operation': 'clear_all', 'corpus_id': corpus_id}}
            if corpus_id not in self.rag_engine.indices:
                logger.warning(f'Corpus {corpus_id} not found. Nothing to delete.')
                return {'success': True, 'data': {'operation': 'selective_delete', 'corpus_id': corpus_id, 'message': 'Corpus not found, nothing to delete'}}
            if doc_ids or metadata_filters:
                self.rag_engine.delete(corpus_id=corpus_id, index_type=self.default_index_type, node_ids=doc_ids, metadata_filters=metadata_filters)
                result = {'corpus_id': corpus_id, 'operation': 'selective_delete', 'doc_ids': doc_ids, 'metadata_filters': metadata_filters}
                logger.info(f'Successfully deleted from corpus {corpus_id}')
                return {'success': True, 'data': result}
            else:
                logger.warning(f'No deletion criteria provided for corpus {corpus_id}')
                return {'success': True, 'data': {'operation': 'selective_delete', 'corpus_id': corpus_id, 'message': 'No deletion criteria provided'}}
        except Exception as e:
            logger.error(f'Delete failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def list_corpora(self) -> Dict[str, Any]:
        """
        List all available corpora and their metadata.
        
        Returns:
            Dict[str, Any]: List of corpora with metadata
        """
        try:
            corpora = []
            for corpus_id, indices in self.rag_engine.indices.items():
                corpus_info = {'corpus_id': corpus_id, 'index_types': list(indices.keys()), 'retrievers': list(self.rag_engine.retrievers.get(corpus_id, {}).keys())}
                corpora.append(corpus_info)
            return {'success': True, 'data': {'corpora': corpora, 'total': len(corpora)}}
        except Exception as e:
            logger.error(f'List corpora failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def get_stats(self, corpus_id: Optional[str]=None) -> Dict[str, Any]:
        """
        Get statistics about the database or a specific corpus.
        
        Args:
            corpus_id (str, optional): Corpus ID to get stats for
            
        Returns:
            Dict[str, Any]: Database statistics
        """
        try:
            if corpus_id:
                corpus_id = corpus_id or self.default_corpus_id
                stats = {'corpus_id': corpus_id, 'exists': corpus_id in self.rag_engine.indices, 'index_types': list(self.rag_engine.indices.get(corpus_id, {}).keys()), 'retrievers': list(self.rag_engine.retrievers.get(corpus_id, {}).keys())}
                if corpus_id in self.rag_engine.indices:
                    vector_index = self.rag_engine.indices[corpus_id].get(self.default_index_type)
                    if vector_index and hasattr(vector_index, 'get_index'):
                        try:
                            index = vector_index.get_index()
                            if hasattr(index, 'vector_store'):
                                vector_store = index.vector_store
                                if hasattr(vector_store, 'faiss_index'):
                                    stats['vector_count'] = vector_store.faiss_index.ntotal
                                    stats['dimensions'] = vector_store.faiss_index.d
                        except Exception:
                            pass
                return {'success': True, 'data': stats}
            else:
                stats = {'total_corpora': len(self.rag_engine.indices), 'corpora': list(self.rag_engine.indices.keys()), 'embedding_model': self.rag_engine.config.embedding.model_name, 'vector_store_type': self.rag_engine.storage_handler.storageConfig.vectorConfig.vector_name if self.rag_engine.storage_handler.storageConfig.vectorConfig else None}
                return {'success': True, 'data': stats}
        except Exception as e:
            logger.error(f'Get stats failed: {str(e)}')
            return {'success': False, 'error': str(e)}

def query(self, query: str, corpus_id: Optional[str]=None, top_k: int=5, similarity_threshold: float=0.0, metadata_filters: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
    """
        Query the vector database with semantic search.
        
        Args:
            query (str): The query string to search for
            corpus_id (str, optional): Corpus ID to search in
            top_k (int): Number of top results to return
            similarity_threshold (float): Minimum similarity threshold
            metadata_filters (Dict[str, Any], optional): Metadata filters for search
            
        Returns:
            Dict[str, Any]: Search results with chunks and scores
        """
    try:
        try:
            asyncio.get_running_loop()
            logger.info('Detected running event loop, using thread executor for query')
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._query_sync, query, corpus_id, top_k, similarity_threshold, metadata_filters)
                return future.result()
        except RuntimeError:
            logger.info('No event loop detected, using direct query processing')
            return self._query_sync(query, corpus_id, top_k, similarity_threshold, metadata_filters)
    except Exception as e:
        logger.error(f'Query failed: {str(e)}')
        return {'success': False, 'error': str(e)}

def _process_file_path(self, file_path: str, doc_index: int, metadata: Optional[Dict[str, Any]]=None) -> List[Document]:
    """
        Process a file path and return Document objects.
        
        Args:
            file_path (str): Path to the file
            doc_index (int): Index of the document in the batch
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            List[Document]: List of Document objects created from the file
        """
    try:
        try:
            asyncio.get_running_loop()
            logger.info(f'Detected running event loop, using thread executor for {file_path}')
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._process_file_path_sync, file_path, doc_index, metadata)
                return future.result()
        except RuntimeError:
            logger.info(f'No event loop detected, using direct processing for {file_path}')
            return self._process_file_path_sync(file_path, doc_index, metadata)
    except Exception as e:
        logger.error(f'Failed to process file {file_path}: {str(e)}')
        doc_metadata = metadata.copy() if metadata else {}
        doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'error': str(e)})
        document_metadata = DocumentMetadata(**doc_metadata)
        return [Document(text=f'Error reading file {file_path}: {str(e)}', metadata=document_metadata, doc_id=str(uuid4()))]

def _process_file_path_sync(self, file_path: str, doc_index: int, metadata: Optional[Dict[str, Any]]=None) -> List[Document]:
    """
        Synchronous version of file processing that can be safely called from a thread.
        
        Args:
            file_path (str): Path to the file
            doc_index (int): Index of the document in the batch
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            List[Document]: List of Document objects created from the file
        """
    try:
        if self.file_storage_handler:
            result = self.file_storage_handler.read(file_path)
            if result['success']:
                file_content = result['content']
            else:
                raise Exception(f'Failed to read file: {result.get('error', 'Unknown error')}')
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        temp_corpus_id = f'temp_file_{uuid4().hex[:8]}'
        temp_doc = Document(text=file_content, metadata=DocumentMetadata(source_file=file_path, doc_index=doc_index, insertion_time=datetime.now().isoformat()), doc_id=str(uuid4()))
        corpus = self.rag_engine.process_documents([temp_doc], corpus_id=temp_corpus_id)
        documents = []
        for chunk in corpus.chunks:
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'original_chunk_id': chunk.chunk_id})
            document_metadata = DocumentMetadata(**doc_metadata)
            documents.append(Document(text=chunk.text, metadata=document_metadata, doc_id=chunk.chunk_id))
        self.rag_engine.clear(corpus_id=temp_corpus_id)
        logger.info(f'Processed file {file_path} into {len(documents)} chunks')
        return documents
    except Exception as e:
        logger.error(f'Failed to process file {file_path} in sync mode: {str(e)}')
        doc_metadata = metadata.copy() if metadata else {}
        doc_metadata.update({'doc_index': doc_index, 'insertion_time': datetime.now().isoformat(), 'source_file': file_path, 'error': str(e)})
        document_metadata = DocumentMetadata(**doc_metadata)
        return [Document(text=f'Error reading file {file_path}: {str(e)}', metadata=document_metadata, doc_id=str(uuid4()))]

def insert(self, documents: list, corpus_id: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None, batch_size: int=100) -> Dict[str, Any]:
    """
        Insert documents into the vector database.
        
        Args:
            documents (Union[List[str], List[Dict[str, Any]]]): Documents to insert. 
                Strings can be either text content or file paths (if they look like paths and exist)
            corpus_id (str, optional): Corpus ID to insert into
            metadata (Dict[str, Any], optional): Additional metadata for all documents
            batch_size (int): Batch size for processing
            
        Returns:
            Dict[str, Any]: Insertion results
        """
    try:
        corpus_id = corpus_id or self.default_corpus_id
        processed_docs = []
        file_paths_processed = []
        for i, doc in enumerate(documents):
            if isinstance(doc, str):
                if self._is_file_path(doc):
                    logger.info(f'Detected file path: {doc}')
                    file_docs = self._process_file_path(doc, i, metadata)
                    processed_docs.extend(file_docs)
                    file_paths_processed.append(doc)
                else:
                    doc_metadata = metadata.copy() if metadata else {}
                    doc_metadata.update({'doc_index': i, 'insertion_time': datetime.now().isoformat()})
                    document_metadata = DocumentMetadata(**doc_metadata)
                    processed_docs.append(Document(text=doc, metadata=document_metadata, doc_id=str(uuid4())))
            elif isinstance(doc, dict):
                doc_metadata = metadata.copy() if metadata else {}
                doc_metadata.update(doc.get('metadata', {}))
                doc_metadata.update({'doc_index': i, 'insertion_time': datetime.now().isoformat()})
                document_metadata = DocumentMetadata(**doc_metadata)
                processed_docs.append(Document(text=doc.get('text', ''), metadata=document_metadata, doc_id=doc.get('doc_id', str(uuid4()))))
        corpus = Corpus(corpus_id=corpus_id)
        total_processed = 0
        for i in range(0, len(processed_docs), batch_size):
            batch = processed_docs[i:i + batch_size]
            batch_corpus = self.rag_engine.chunker.chunk(batch)
            batch_corpus.corpus_id = corpus_id
            self.rag_engine.add(self.default_index_type, batch_corpus, corpus_id=corpus_id)
            corpus.chunks.extend(batch_corpus.chunks)
            total_processed += len(batch)
            logger.info(f'Processed batch {i // batch_size + 1}, total processed: {total_processed}')
        self.rag_engine.save(corpus_id=corpus_id, index_type=self.default_index_type)
        result = {'corpus_id': corpus_id, 'documents_inserted': len(documents), 'chunks_created': len(corpus.chunks), 'total_processed': total_processed, 'file_paths_processed': file_paths_processed}
        logger.info(f'Successfully inserted {len(documents)} documents into corpus {corpus_id}')
        if file_paths_processed:
            logger.info(f'Processed {len(file_paths_processed)} file paths: {file_paths_processed}')
        return {'success': True, 'data': result}
    except Exception as e:
        logger.error(f'Insert failed: {str(e)}')
        return {'success': False, 'error': str(e)}

class APITool(Tool):
    """
    API tool wrapper that encapsulates a single API endpoint as a Tool
    
    Attributes:
        name: Tool name
        description: Tool description
        inputs: Input parameter schema
        required: List of required parameters
        endpoint_config: API endpoint configuration
        auth_config: Authentication configuration
        function: Actual execution function
    """

    def __init__(self, name: str, description: str, inputs: Dict[str, Dict[str, Any]], required: Optional[List[str]]=None, endpoint_config: Dict[str, Any]=None, auth_config: Dict[str, Any]=None, function: Callable=None):
        super().__init__(name=name, description=description, inputs=inputs, required=required)
        self.endpoint_config = endpoint_config or {}
        self.auth_config = auth_config or {}
        self.function = function

    @property
    def __name__(self):
        return self.name

    def __call__(self, **kwargs):
        """Execute the API call"""
        if not self.function:
            raise ValueError('Function not set for APITool')
        try:
            result = self.function(**kwargs)
            return self._process_result(result)
        except Exception as e:
            logger.error(f'Error calling API tool {self.name}: {str(e)}')
            raise

    def _process_result(self, result: Any) -> Any:
        """Process API response"""
        if isinstance(result, requests.Response):
            try:
                return result.json()
            except (ValueError, json.JSONDecodeError):
                return result.text
        return result

    @classmethod
    def validate_attributes(cls):
        """Validate attributes"""
        if cls.__name__ == 'APITool':
            return
        required_attributes = {'name': str, 'description': str, 'inputs': dict}
        for attr, attr_type in required_attributes.items():
            if not hasattr(cls, attr):
                raise ValueError(f'Attribute {attr} is required')
            if not isinstance(getattr(cls, attr), attr_type):
                raise ValueError(f'Attribute {attr} must be of type {attr_type}')
        if hasattr(cls, 'required') and cls.required:
            for required_input in cls.required:
                if required_input not in cls.inputs:
                    raise ValueError(f"Required input '{required_input}' is not found in inputs")

def __call__(self, **kwargs):
    """Execute the API call"""
    if not self.function:
        raise ValueError('Function not set for APITool')
    try:
        result = self.function(**kwargs)
        return self._process_result(result)
    except Exception as e:
        logger.error(f'Error calling API tool {self.name}: {str(e)}')
        raise

class APIToolkit(Toolkit):
    """
    API tool collection representing all endpoints of an API service
    
    Attributes:
        name: Service name
        tools: List of API tools
        base_url: Base URL
        auth_config: Authentication configuration
        common_headers: Common request headers
    """

    def __init__(self, name: str, tools: List[APITool], base_url: str='', auth_config: Dict[str, Any]=None, common_headers: Dict[str, str]=None):
        super().__init__(name=name, tools=tools)
        self.base_url = base_url
        self.auth_config = auth_config or {}
        self.common_headers = common_headers or {}

    def add_auth_to_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Add authentication information to request headers"""
        headers = headers.copy()
        headers.update(self.common_headers)
        if 'api_key' in self.auth_config:
            key_name = self.auth_config.get('key_name', 'X-API-Key')
            headers[key_name] = self.auth_config['api_key']
        if 'bearer_token' in self.auth_config:
            headers['Authorization'] = f'Bearer {self.auth_config['bearer_token']}'
        return headers

def add_auth_to_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
    """Add authentication information to request headers"""
    headers = headers.copy()
    headers.update(self.common_headers)
    if 'api_key' in self.auth_config:
        key_name = self.auth_config.get('key_name', 'X-API-Key')
        headers[key_name] = self.auth_config['api_key']
    if 'bearer_token' in self.auth_config:
        headers['Authorization'] = f'Bearer {self.auth_config['bearer_token']}'
    return headers

class SerpAPITool(Tool):
    name: str = 'serpapi_search'
    description: str = 'Search multiple search engines using SerpAPI with comprehensive result processing and content scraping'
    inputs: Dict[str, Dict[str, str]] = {'query': {'type': 'string', 'description': 'The search query to execute'}, 'num_search_pages': {'type': 'integer', 'description': 'Number of search results to retrieve. Default: 5'}, 'max_content_words': {'type': 'integer', 'description': 'Maximum number of words to include in content per result. None means no limit. Default: None'}, 'engine': {'type': 'string', 'description': 'Search engine to use: google, bing, baidu, yahoo, duckduckgo. Default: google'}, 'location': {'type': 'string', 'description': "Geographic location for localized results (e.g., 'New York, NY', 'London, UK')"}, 'language': {'type': 'string', 'description': "Interface language code (e.g., 'en', 'es', 'fr', 'de'). Default: en"}, 'country': {'type': 'string', 'description': "Country code for country-specific results (e.g., 'us', 'uk', 'ca'). Default: us"}, 'search_type': {'type': 'string', 'description': 'Type of search: web, images, news, shopping, maps. Default: web'}}
    required: Optional[List[str]] = ['query']

    def __init__(self, search_serpapi: SearchSerpAPI=None):
        super().__init__()
        self.search_serpapi = search_serpapi

    def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None, engine: str=None, location: str=None, language: str=None, country: str=None, search_type: str=None) -> Dict[str, Any]:
        """Execute SerpAPI search using the SearchSerpAPI instance."""
        if not self.search_serpapi:
            raise RuntimeError('SerpAPI search instance not initialized')
        try:
            return self.search_serpapi.search(query=query, num_search_pages=num_search_pages, max_content_words=max_content_words, engine=engine, location=location, language=language, country=country, search_type=search_type)
        except Exception as e:
            return {'results': [], 'error': f'Error executing SerpAPI search: {str(e)}'}

def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None, engine: str=None, location: str=None, language: str=None, country: str=None, search_type: str=None) -> Dict[str, Any]:
    """Execute SerpAPI search using the SearchSerpAPI instance."""
    if not self.search_serpapi:
        raise RuntimeError('SerpAPI search instance not initialized')
    try:
        return self.search_serpapi.search(query=query, num_search_pages=num_search_pages, max_content_words=max_content_words, engine=engine, location=location, language=language, country=country, search_type=search_type)
    except Exception as e:
        return {'results': [], 'error': f'Error executing SerpAPI search: {str(e)}'}

class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL-specific connection management"""

    def __init__(self, connection_string: str, **kwargs):
        super().__init__(connection_string, **kwargs)
        self.conn = None

    def connect(self) -> bool:
        try:
            self.conn = psycopg2.connect(self.connection_string, **self.connection_params)
            self._is_connected = True
            logger.info('Successfully connected to PostgreSQL')
            return True
        except Exception as e:
            logger.error(f'Failed to connect to PostgreSQL: {str(e)}')
            self._is_connected = False
            return False

    def disconnect(self) -> bool:
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                self._is_connected = False
                logger.info('Disconnected from PostgreSQL')
            return True
        except Exception as e:
            logger.error(f'Error disconnecting from PostgreSQL: {str(e)}')
            return False

    def test_connection(self) -> bool:
        try:
            if self.conn:
                with self.conn.cursor() as cur:
                    cur.execute('SELECT 1;')
                return True
            return False
        except Exception:
            return False

def connect(self) -> bool:
    try:
        self.conn = psycopg2.connect(self.connection_string, **self.connection_params)
        self._is_connected = True
        logger.info('Successfully connected to PostgreSQL')
        return True
    except Exception as e:
        logger.error(f'Failed to connect to PostgreSQL: {str(e)}')
        self._is_connected = False
        return False

def disconnect(self) -> bool:
    try:
        if self.conn:
            self.conn.close()
            self.conn = None
            self._is_connected = False
            logger.info('Disconnected from PostgreSQL')
        return True
    except Exception as e:
        logger.error(f'Error disconnecting from PostgreSQL: {str(e)}')
        return False

class PostgreSQLDatabase(DatabaseBase):
    """
    PostgreSQL database implementation with automatic initialization.
    Handles remote connections, existing local databases, and new local database creation.
    """

    def __init__(self, connection_string: str=None, database_name: str=None, local_path: str=None, auto_save: bool=True, **kwargs):
        init_params = {'connection_string': connection_string, 'database_name': database_name}
        super().__init__(**init_params, **kwargs)
        self.local_path = Path(local_path) if local_path else None
        self.auto_save = auto_save
        self.connection_params = kwargs
        self.is_local_database = False
        self.conn = None
        self.cursor = None
        self.file_based_mode = False
        self.tables = {}
        if self._is_remote_connection():
            self._init_remote_database()
        elif self._is_existing_local_database():
            self._init_existing_local_database()
        else:
            self._init_new_local_database()

    def _is_remote_connection(self) -> bool:
        return self.connection_string and ('@' in self.connection_string or 'postgresql://' in self.connection_string)

    def _is_existing_local_database(self) -> bool:
        if not self.local_path:
            return False
        if not self.local_path.exists():
            return False
        db_info_file = self.local_path / 'db_info.json'
        return db_info_file.exists()

    def _init_remote_database(self):
        """Initialize remote PostgreSQL connection"""
        try:
            connection_params = self.connection_params.copy()
            connection_params.update({'connect_timeout': 5, 'options': '-c statement_timeout=5000'})
            self.conn = psycopg2.connect(self.connection_string, **connection_params)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if self.database_name:
                self.conn.set_isolation_level(0)
                self.cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (self.database_name,))
            self._is_initialized = True
            self.is_local_database = False
            self.file_based_mode = False
            logger.info(f'Connected to remote PostgreSQL: {self.database_name}')
        except Exception as e:
            logger.error(f'Failed to connect to remote PostgreSQL: {str(e)}')
            self._is_initialized = False
            logger.info('Falling back to local database mode')

    def _init_existing_local_database(self):
        """Initialize existing local file-based database"""
        try:
            if not self.database_name:
                self.database_name = self.local_path.name
            self._load_tables_from_files()
            self._is_initialized = True
            self.is_local_database = True
            self.file_based_mode = True
            logger.info(f'Loaded existing local file-based database from: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to load existing local database: {str(e)}')
            self._is_initialized = False
            logger.info('Falling back to new local database mode')
            self._init_new_local_database()

    def _init_new_local_database(self):
        """Initialize new local file-based database"""
        try:
            if not self.local_path:
                self.local_path = Path('./workplace/postgresql_local')
            self.local_path.mkdir(parents=True, exist_ok=True)
            if not self.database_name:
                self.database_name = self.local_path.name
            self._create_db_info_file()
            self._is_initialized = True
            self.is_local_database = True
            self.file_based_mode = True
            logger.info(f'Created new local file-based database at: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to create new local database: {str(e)}')
            self._is_initialized = False
            logger.info('Database initialization failed, but toolkit is still usable')

    def _create_db_info_file(self):
        """Create database info file"""
        try:
            db_info = {'database_name': self.database_name, 'created_at': time.time(), 'local_path': str(self.local_path.absolute()), 'auto_save': self.auto_save, 'version': '1.0', 'mode': 'file_based'}
            info_file = self.local_path / 'db_info.json'
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(db_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f'Failed to create db info file: {str(e)}')

    def _load_tables_from_files(self):
        """Load tables from JSON files"""
        try:
            for json_file in self.local_path.glob('*.json'):
                if json_file.name == 'db_info.json':
                    continue
                table_name = json_file.stem
                with open(json_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    if not isinstance(loaded_data, list):
                        logger.warning(f'Table {table_name} file contains non-list data: {type(loaded_data)}, converting to empty list')
                        self.tables[table_name] = []
                    else:
                        self.tables[table_name] = loaded_data
        except Exception as e:
            logger.warning(f'Error loading tables from files: {str(e)}')

    def _save_table_to_file(self, table_name: str):
        """Save table data to JSON file"""
        try:
            if table_name in self.tables:
                table_file = self.local_path / f'{table_name}.json'
                with open(table_file, 'w', encoding='utf-8') as f:
                    json.dump(self.tables[table_name], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f'Error saving table {table_name}: {str(e)}')

    def _parse_sql_query(self, sql: str) -> Dict[str, Any]:
        """Enhanced SQL parser for file-based mode - now supports JOINs and complex queries"""
        sql = sql.strip()
        upper_sql = sql.upper()
        if upper_sql.startswith('CREATE TABLE'):
            match = re.search('CREATE TABLE (?:IF NOT EXISTS )?(\\w+) *\\((.*?)\\)', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                columns = match.group(2)
                col_defs = [c.strip() for c in columns.split(',') if c.strip()]
                col_names = [c.split()[0] for c in col_defs]
                return {'type': 'CREATE', 'table': table, 'columns': col_names}
        elif upper_sql.startswith('INSERT'):
            match = re.search('INSERT INTO (\\w+) *\\((.*?)\\) *VALUES', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                columns = [c.strip() for c in match.group(2).split(',')]
                values_match = re.search('VALUES\\s*(.*)', sql, re.IGNORECASE | re.DOTALL)
                if values_match:
                    values_str = values_match.group(1)
                    value_groups = re.findall('\\(([^)]+)\\)', values_str)
                    all_values = []
                    for group in value_groups:
                        values = [v.strip().strip('\'"') for v in group.split(',')]
                        all_values.append(values)
                    return {'type': 'INSERT', 'table': table, 'columns': columns, 'values': all_values}
        elif upper_sql.startswith('SELECT'):
            if 'JOIN' in upper_sql:
                match = re.search('SELECT (.*?) FROM (\\w+)(?:\\s+(\\w+))?\\s+(?:(\\w+)\\s+)?JOIN\\s+(\\w+)(?:\\s+(\\w+))?\\s+ON\\s+(.*?)(?: WHERE (.*?))?(?: ORDER BY (.*?))?(?: LIMIT (\\d+))?', sql, re.IGNORECASE | re.DOTALL)
                if match:
                    columns = [c.strip() for c in match.group(1).split(',')]
                    table1 = match.group(2).lower()
                    alias1 = match.group(3)
                    join_type = match.group(4) or 'INNER'
                    table2 = match.group(5).lower()
                    alias2 = match.group(6)
                    join_condition = match.group(7)
                    where = match.group(8)
                    order_by = match.group(9)
                    limit = match.group(10)
                    return {'type': 'SELECT_JOIN', 'columns': columns, 'table1': table1, 'alias1': alias1, 'join_type': join_type, 'table2': table2, 'alias2': alias2, 'join_condition': join_condition, 'where': where, 'order_by': order_by, 'limit': limit}
                elif 'CROSS JOIN' in upper_sql:
                    match = re.search('SELECT (.*?) FROM (\\w+)(?:\\s+(\\w+))?\\s+CROSS\\s+JOIN\\s+(\\w+)(?:\\s+(\\w+))?(?: WHERE (.*?))?(?: ORDER BY (.*?))?(?: LIMIT (\\d+))?', sql, re.IGNORECASE | re.DOTALL)
                    if match:
                        columns = [c.strip() for c in match.group(1).split(',')]
                        table1 = match.group(2).lower()
                        alias1 = match.group(3)
                        table2 = match.group(4).lower()
                        alias2 = match.group(5)
                        where = match.group(6)
                        order_by = match.group(7)
                        limit = match.group(8)
                        return {'type': 'SELECT_CROSS_JOIN', 'columns': columns, 'table1': table1, 'alias1': alias1, 'table2': table2, 'alias2': alias2, 'where': where, 'order_by': order_by, 'limit': limit}
            else:
                match = re.search('SELECT (.*?) FROM (\\w+)(?: WHERE (.*?))?(?: GROUP BY (.*?))?(?: ORDER BY (.*?))?(?: LIMIT (\\d+))?', sql, re.IGNORECASE | re.DOTALL)
                if match:
                    columns = [c.strip() for c in match.group(1).split(',')]
                    table = match.group(2).lower()
                    where = match.group(3)
                    group_by = match.group(4)
                    order_by = match.group(5)
                    limit = match.group(6)
                    return {'type': 'SELECT', 'table': table, 'columns': columns, 'where': where, 'group_by': group_by, 'order_by': order_by, 'limit': limit}
        elif upper_sql.startswith('UPDATE'):
            match = re.search('UPDATE (\\w+) SET (.*?)(?: WHERE (.*?))?$', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                set_clause = match.group(2)
                where = match.group(3)
                return {'type': 'UPDATE', 'table': table, 'set': set_clause, 'where': where}
        elif upper_sql.startswith('DELETE'):
            match = re.search('DELETE FROM (\\w+)(?: WHERE (.*?))?', sql, re.IGNORECASE | re.DOTALL)
            if match:
                table = match.group(1).lower()
                where = match.group(2)
                return {'type': 'DELETE', 'table': table, 'where': where}
        return {'type': 'UNKNOWN'}

    def _apply_where_filter(self, rows: List[Dict], where: str) -> List[Dict]:
        """Apply WHERE filter to rows"""
        if not where:
            return rows
        if not isinstance(rows, list):
            logger.warning(f'_apply_where_filter: rows is not a list: {type(rows)}')
            return []
        valid_rows = [r for r in rows if isinstance(r, dict)]
        if len(valid_rows) != len(rows):
            logger.warning(f'_apply_where_filter: filtered out {len(rows) - len(valid_rows)} non-dict rows')
        m = re.match("(\\w+) *([=><]+) *'?([\\w@.\\- ]+)'?", where)
        if m:
            col, op, val = (m.group(1), m.group(2), m.group(3))
            if op == '=':
                return [r for r in valid_rows if str(r.get(col, '')) == val]
            elif op == '>':
                try:
                    val_num = int(val)
                    return [r for r in valid_rows if int(r.get(col, 0)) > val_num]
                except ValueError:
                    pass
            elif op == '<':
                try:
                    val_num = int(val)
                    return [r for r in valid_rows if int(r.get(col, 0)) < val_num]
                except ValueError:
                    pass
        return valid_rows

    def _apply_column_selection(self, rows: List[Dict], columns: List[str]) -> List[Dict]:
        """Apply column selection to rows"""
        if columns == ['*']:
            return rows
        if not isinstance(rows, list):
            logger.warning(f'_apply_column_selection: rows is not a list: {type(rows)}')
            return []
        valid_rows = [r for r in rows if isinstance(r, dict)]
        if len(valid_rows) != len(rows):
            logger.warning(f'_apply_column_selection: filtered out {len(rows) - len(valid_rows)} non-dict rows')
        filtered_rows = []
        for row in valid_rows:
            filtered_row = {}
            for col in columns:
                if col in row:
                    filtered_row[col] = row[col]
            filtered_rows.append(filtered_row)
        return filtered_rows

    def _apply_group_by(self, rows: List[Dict], group_by: str) -> List[Dict]:
        """Apply GROUP BY aggregation to rows"""
        if not group_by:
            return rows
        if not isinstance(rows, list):
            logger.warning(f'_apply_group_by: rows is not a list: {type(rows)}')
            return []
        valid_rows = [r for r in rows if isinstance(r, dict)]
        if len(valid_rows) != len(rows):
            logger.warning(f'_apply_group_by: filtered out {len(rows) - len(valid_rows)} non-dict rows')
        group_col = group_by.strip()
        groups = {}
        for row in valid_rows:
            group_val = row.get(group_col, 'Unknown')
            if group_val not in groups:
                groups[group_val] = []
            groups[group_val].append(row)
        result = []
        for group_val, group_rows in groups.items():
            group_result = {group_col: group_val}
            group_result['employee_count'] = len(group_rows)
            salaries = [float(r.get('salary', 0)) for r in group_rows if r.get('salary') is not None]
            group_result['avg_salary'] = sum(salaries) / len(salaries) if salaries else 0
            group_result['max_salary'] = max(salaries) if salaries else 0
            result.append(group_result)
        return result

    def _execute_join_query(self, parsed: Dict) -> Dict[str, Any]:
        """Execute JOIN query in file-based mode"""
        try:
            table1 = parsed['table1']
            table2 = parsed['table2']
            columns = parsed['columns']
            join_condition = parsed['join_condition']
            where = parsed.get('where')
            rows1 = self.tables.get(table1, [])
            rows2 = self.tables.get(table2, [])
            if not isinstance(rows1, list):
                logger.warning(f'Table {table1} contains non-list data: {type(rows1)}')
                rows1 = []
            if not isinstance(rows2, list):
                logger.warning(f'Table {table2} contains non-list data: {type(rows2)}')
                rows2 = []
            join_match = re.match('(\\w+)\\.(\\w+)\\s*=\\s*(\\w+)\\.(\\w+)', join_condition)
            if not join_match:
                return {'error': 'Invalid join condition format'}
            col1, col2 = (join_match.group(2), join_match.group(4))
            result_rows = []
            for row1 in rows1:
                if not isinstance(row1, dict):
                    logger.warning(f'Skipping non-dict row1 in JOIN: {type(row1)}')
                    continue
                for row2 in rows2:
                    if not isinstance(row2, dict):
                        logger.warning(f'Skipping non-dict row2 in JOIN: {type(row2)}')
                        continue
                    if str(row1.get(col1, '')) == str(row2.get(col2, '')):
                        combined_row = {}
                        for col in columns:
                            if '.' in col:
                                table_alias, col_name = col.split('.', 1)
                                if table_alias == parsed.get('alias1') or table_alias == table1:
                                    combined_row[col] = row1.get(col_name, '')
                                elif table_alias == parsed.get('alias2') or table_alias == table2:
                                    combined_row[col] = row2.get(col_name, '')
                            elif col in row1:
                                combined_row[col] = row1[col]
                            elif col in row2:
                                combined_row[col] = row2[col]
                        result_rows.append(combined_row)
            if where:
                result_rows = self._apply_where_filter(result_rows, where)
            return result_rows
        except Exception as e:
            logger.error(f'Error executing JOIN query: {str(e)}')
            return {'error': str(e)}

    def _execute_cross_join_query(self, parsed: Dict) -> Dict[str, Any]:
        """Execute CROSS JOIN query in file-based mode"""
        try:
            table1 = parsed['table1']
            table2 = parsed['table2']
            columns = parsed['columns']
            where = parsed.get('where')
            rows1 = self.tables.get(table1, [])
            rows2 = self.tables.get(table2, [])
            if not isinstance(rows1, list):
                logger.warning(f'Table {table1} contains non-list data: {type(rows1)}')
                rows1 = []
            if not isinstance(rows2, list):
                logger.warning(f'Table {table2} contains non-list data: {type(rows2)}')
                rows2 = []
            result_rows = []
            for row1 in rows1:
                if not isinstance(row1, dict):
                    logger.warning(f'Skipping non-dict row1 in CROSS JOIN: {type(row1)}')
                    continue
                for row2 in rows2:
                    if not isinstance(row2, dict):
                        logger.warning(f'Skipping non-dict row2 in CROSS JOIN: {type(row2)}')
                        continue
                    combined_row = {}
                    for col in columns:
                        if '.' in col:
                            table_alias, col_name = col.split('.', 1)
                            if table_alias == parsed.get('alias1') or table_alias == table1:
                                combined_row[col] = row1.get(col_name, '')
                            elif table_alias == parsed.get('alias2') or table_alias == table2:
                                combined_row[col] = row2.get(col_name, '')
                        elif col in row1:
                            combined_row[col] = row1[col]
                        elif col in row2:
                            combined_row[col] = row2[col]
                    result_rows.append(combined_row)
            if where:
                result_rows = self._apply_where_filter(result_rows, where)
            return result_rows
        except Exception as e:
            logger.error(f'Error executing CROSS JOIN query: {str(e)}')
            return {'error': str(e)}

    def _get_database_type(self) -> DatabaseType:
        return DatabaseType.POSTGRESQL

    def connect(self) -> bool:
        return self._is_initialized

    def disconnect(self) -> bool:
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                self.cursor = None
                self._is_initialized = False
                logger.info('Disconnected from PostgreSQL')
            return True
        except Exception as e:
            logger.error(f'Error disconnecting: {str(e)}')
            return False

    def test_connection(self) -> bool:
        if self.file_based_mode:
            return self._is_initialized
        try:
            if self.conn:
                with self.conn.cursor() as cur:
                    cur.execute('SELECT 1;')
                return True
            return False
        except Exception:
            return False

    def execute_query(self, query: Union[str, Dict, List], query_type: QueryType=None, **kwargs) -> Dict[str, Any]:
        if not self._is_initialized:
            return self.format_error_result('Database not initialized')
        if self.file_based_mode:
            return self._execute_file_based_query(query, query_type)
        if self.conn is None:
            return self.format_error_result('PostgreSQL server not available')
        start_time = time.time()
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if isinstance(query, str):
                    cur.execute(query)
                elif isinstance(query, dict):
                    sql = query.get('sql')
                    params = query.get('params', None)
                    if params:
                        cur.execute(sql, params)
                    else:
                        cur.execute(sql)
                elif isinstance(query, list):
                    for q in query:
                        if isinstance(q, str):
                            cur.execute(q)
                        elif isinstance(q, dict):
                            sql = q.get('sql')
                            params = q.get('params', None)
                            if params:
                                cur.execute(sql, params)
                            else:
                                cur.execute(sql)
                else:
                    return self.format_error_result('Unsupported query format', query_type)
                if cur.description:
                    result = cur.fetchall()
                else:
                    result = {'rowcount': cur.rowcount}
                self.conn.commit()
            execution_time = time.time() - start_time
            return self.format_query_result(result, query_type or QueryType.SELECT, execution_time=execution_time)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f'Error executing PostgreSQL query: {str(e)}')
            try:
                if self.conn:
                    self.conn.rollback()
            except Exception as rollback_error:
                logger.warning(f'Error during rollback: {str(rollback_error)}')
            return self.format_error_result(str(e), query_type, execution_time=execution_time)

    def _execute_file_based_query(self, query: Union[str, Dict, List], query_type: QueryType=None) -> Dict[str, Any]:
        """Execute query in file-based mode"""
        start_time = time.time()
        try:
            if isinstance(query, str):
                parsed = self._parse_sql_query(query)
                query_type = query_type or QueryType.SELECT
                if not isinstance(parsed, dict) or 'type' not in parsed:
                    logger.error(f'_execute_file_based_query: parsed is not a valid dict: {parsed}')
                    return self.format_error_result(f'Failed to parse SQL query: {query}', query_type)
                logger.debug(f'Executing {parsed['type']} query: {parsed}')
                if parsed['type'] == 'CREATE':
                    table_name = parsed['table']
                    columns = parsed.get('columns', ['id'])
                    if table_name not in self.tables:
                        self.tables[table_name] = []
                    if not isinstance(self.tables[table_name], list):
                        logger.warning(f'Reinitializing table {table_name} as list (was {type(self.tables[table_name])})')
                        self.tables[table_name] = []
                    self.tables[f'__schema__{table_name}'] = columns
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': 0}
                elif parsed['type'] == 'INSERT':
                    table_name = parsed['table']
                    columns = parsed['columns']
                    all_values = parsed['values']
                    if table_name not in self.tables:
                        self.tables[table_name] = []
                    if not isinstance(self.tables[table_name], list):
                        logger.warning(f'Reinitializing table {table_name} as list (was {type(self.tables[table_name])})')
                        self.tables[table_name] = []
                    valid_rows = 0
                    for values in all_values:
                        if len(values) != len(columns):
                            logger.warning(f'Skipping invalid row: {values} (expected {len(columns)} values, got {len(values)})')
                            continue
                        if not isinstance(values, list):
                            logger.warning(f'Skipping non-list values: {type(values)}')
                            continue
                        row = {col: val for col, val in zip(columns, values)}
                        row['id'] = len(self.tables[table_name]) + 1
                        self.tables[table_name].append(row)
                        valid_rows += 1
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': valid_rows}
                elif parsed['type'] == 'SELECT':
                    table_name = parsed['table']
                    columns = parsed['columns']
                    where = parsed.get('where')
                    group_by = parsed.get('group_by')
                    rows = self.tables.get(table_name, [])
                    if not isinstance(rows, list):
                        logger.warning(f'Table {table_name} contains non-list data: {type(rows)}')
                        rows = []
                    logger.debug(f'SELECT query: table={table_name}, columns={columns}, where={where}, group_by={group_by}')
                    logger.debug(f'Rows from table: {type(rows)}, length={(len(rows) if isinstance(rows, list) else 'N/A')}')
                    if isinstance(rows, list) and rows:
                        logger.debug(f'First row type: {type(rows[0])}, content: {rows[0]}')
                    if where:
                        rows = self._apply_where_filter(rows, where)
                    if group_by:
                        result = self._apply_group_by(rows, group_by)
                    else:
                        result = {'data': self._apply_column_selection(rows, columns)}
                elif parsed['type'] == 'SELECT_JOIN':
                    logger.debug(f'Executing JOIN query: {parsed}')
                    join_result = self._execute_join_query(parsed)
                    if isinstance(join_result, dict) and 'error' in join_result:
                        result = {'error': join_result['error']}
                    else:
                        result = {'data': join_result}
                elif parsed['type'] == 'SELECT_CROSS_JOIN':
                    logger.debug(f'Executing CROSS JOIN query: {parsed}')
                    cross_join_result = self._execute_cross_join_query(parsed)
                    if isinstance(cross_join_result, dict) and 'error' in cross_join_result:
                        result = {'error': cross_join_result['error']}
                    else:
                        result = {'data': cross_join_result}
                elif parsed['type'] == 'UPDATE':
                    table_name = parsed['table']
                    set_clause = parsed['set']
                    where = parsed.get('where')
                    rows = self.tables.get(table_name, [])
                    if not isinstance(rows, list):
                        logger.warning(f'Table {table_name} contains non-list data: {type(rows)}')
                        rows = []
                    updates = dict(re.findall("(\\w+) *= *'?([\\w@.\\- ]+)'?", set_clause))
                    count = 0
                    for r in rows:
                        if not isinstance(r, dict):
                            logger.warning(f'Skipping non-dict row in UPDATE: {type(r)}')
                            continue
                        match = True
                        if where:
                            m = re.match("(\\w+) *([=><]+) *'?([\\w@.\\- ]+)'?", where)
                            if m:
                                col, op, val = (m.group(1), m.group(2), m.group(3))
                                if op == '=' and str(r.get(col, '')) != val:
                                    match = False
                                elif op == '>' and int(r.get(col, 0)) <= int(val):
                                    match = False
                                elif op == '<' and int(r.get(col, 0)) >= int(val):
                                    match = False
                        if match:
                            r.update(updates)
                            count += 1
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': count}
                elif parsed['type'] == 'DELETE':
                    table_name = parsed['table']
                    where = parsed.get('where')
                    rows = self.tables.get(table_name, [])
                    if not isinstance(rows, list):
                        logger.warning(f'Table {table_name} contains non-list data: {type(rows)}')
                        rows = []
                    if where:
                        m = re.match("(\\w+) *([=><]+) *'?([\\w@.\\- ]+)'?", where)
                        if m:
                            col, op, val = (m.group(1), m.group(2), m.group(3))
                            if op == '=':
                                new_rows = [r for r in rows if isinstance(r, dict) and str(r.get(col, '')) != val]
                            elif op == '>':
                                try:
                                    val_num = int(val)
                                    new_rows = [r for r in rows if isinstance(r, dict) and int(r.get(col, 0)) <= val_num]
                                except ValueError:
                                    new_rows = rows
                            else:
                                new_rows = rows
                            deleted_count = len(rows) - len(new_rows)
                            self.tables[table_name] = new_rows
                        else:
                            deleted_count = 0
                    else:
                        deleted_count = len(rows)
                        self.tables[table_name] = []
                    if self.auto_save:
                        self._save_table_to_file(table_name)
                    result = {'rowcount': deleted_count}
                else:
                    return self.format_error_result('Unsupported query type in file-based mode', query_type)
                execution_time = time.time() - start_time
                return self.format_query_result(result, query_type, execution_time=execution_time)
            else:
                return self.format_error_result('Unsupported query format in file-based mode', query_type)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f'Error executing file-based query: {str(e)}')
            logger.error(f'Query that caused error: {query}')
            logger.error(f'Query type: {query_type}')
            import traceback
            logger.error(f'Traceback: {traceback.format_exc()}')
            return self.format_error_result(str(e), query_type, execution_time=execution_time)

    def get_database_info(self) -> Dict[str, Any]:
        try:
            if not self._is_initialized:
                return self.format_error_result('Database not initialized')
            if self.file_based_mode:
                info = {'database': self.database_name, 'user': 'file_based', 'table_count': len(self.tables), 'connection_string': 'file_based', 'is_connected': True, 'mode': 'file_based'}
            else:
                if self.conn is None:
                    return self.format_error_result('PostgreSQL server not available')
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute('SELECT current_database() as database, current_user as user')
                    db_info = cur.fetchone()
                    cur.execute("SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'")
                    table_count = cur.fetchone()['table_count']
                info = {'database': db_info['database'], 'user': db_info['user'], 'table_count': table_count, 'connection_string': self.connection_string, 'is_connected': self._is_initialized}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def list_collections(self) -> List[str]:
        try:
            if self.file_based_mode:
                return list(self.tables.keys())
            if not self._is_initialized or self.conn is None:
                return []
            with self.conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = [row[0] for row in cur.fetchall()]
            return tables
        except Exception as e:
            logger.error(f'Error listing tables: {str(e)}')
            return []

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        try:
            if not self._is_initialized:
                return self.format_error_result('Database not initialized')
            if self.file_based_mode:
                if collection_name in self.tables:
                    row_count = len(self.tables[collection_name])
                    info = {'table_name': collection_name, 'row_count': row_count, 'columns': ['id']}
                else:
                    return self.format_error_result(f'Table {collection_name} not found')
            else:
                if self.conn is None:
                    return self.format_error_result('PostgreSQL server not available')
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(f'SELECT COUNT(*) as row_count FROM {collection_name}')
                    row_count = cur.fetchone()['row_count']
                    cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (collection_name,))
                    columns = cur.fetchall()
                info = {'table_name': collection_name, 'row_count': row_count, 'columns': columns}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def get_schema(self, collection_name: str=None) -> Dict[str, Any]:
        try:
            if not self._is_initialized:
                return self.format_error_result('Database not initialized')
            if self.file_based_mode:
                if collection_name:
                    if collection_name in self.tables:
                        schema = {'id': 'integer'}
                        return self.format_query_result({'table_name': collection_name, 'schema': schema}, QueryType.SELECT)
                    else:
                        return self.format_error_result(f'Table {collection_name} not found')
                else:
                    schemas = {}
                    for table_name in self.tables:
                        schemas[table_name] = {'id': 'integer'}
                    return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
            else:
                if self.conn is None:
                    return self.format_error_result('PostgreSQL server not available')
                with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if collection_name:
                        cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (collection_name,))
                        columns = cur.fetchall()
                        schema = {col['column_name']: col['data_type'] for col in columns}
                        return self.format_query_result({'table_name': collection_name, 'schema': schema}, QueryType.SELECT)
                    else:
                        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                        tables = [row[0] for row in cur.fetchall()]
                        schemas = {}
                        for table in tables:
                            cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s', (table,))
                            columns = cur.fetchall()
                            schemas[table] = {col['column_name']: col['data_type'] for col in columns}
                        return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def get_supported_query_types(self) -> List[QueryType]:
        return [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP, QueryType.ALTER, QueryType.INDEX]

    def get_capabilities(self) -> Dict[str, Any]:
        base_capabilities = super().get_capabilities()
        base_capabilities.update({'supports_sql': True, 'supports_transactions': not self.file_based_mode, 'supports_indexing': not self.file_based_mode, 'schema_flexible': self.file_based_mode, 'file_based_mode': self.file_based_mode})
        return base_capabilities

def _init_remote_database(self):
    """Initialize remote PostgreSQL connection"""
    try:
        connection_params = self.connection_params.copy()
        connection_params.update({'connect_timeout': 5, 'options': '-c statement_timeout=5000'})
        self.conn = psycopg2.connect(self.connection_string, **connection_params)
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if self.database_name:
            self.conn.set_isolation_level(0)
            self.cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (self.database_name,))
        self._is_initialized = True
        self.is_local_database = False
        self.file_based_mode = False
        logger.info(f'Connected to remote PostgreSQL: {self.database_name}')
    except Exception as e:
        logger.error(f'Failed to connect to remote PostgreSQL: {str(e)}')
        self._is_initialized = False
        logger.info('Falling back to local database mode')

def _init_existing_local_database(self):
    """Initialize existing local file-based database"""
    try:
        if not self.database_name:
            self.database_name = self.local_path.name
        self._load_tables_from_files()
        self._is_initialized = True
        self.is_local_database = True
        self.file_based_mode = True
        logger.info(f'Loaded existing local file-based database from: {self.local_path}')
    except Exception as e:
        logger.error(f'Failed to load existing local database: {str(e)}')
        self._is_initialized = False
        logger.info('Falling back to new local database mode')
        self._init_new_local_database()

def disconnect(self) -> bool:
    try:
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            self._is_initialized = False
            logger.info('Disconnected from PostgreSQL')
        return True
    except Exception as e:
        logger.error(f'Error disconnecting: {str(e)}')
        return False

class PostgreSQLExecuteTool(Tool):
    name: str = 'postgresql_execute'
    description: str = 'Execute arbitrary SQL queries on PostgreSQL.'
    inputs: Dict[str, Dict[str, str]] = {'query': {'type': 'string', 'description': 'SQL query to execute (can be SELECT, INSERT, UPDATE, DELETE, etc.)'}, 'query_type': {'type': 'string', 'description': 'Type of query (select, insert, update, delete, create, drop, alter, index) - auto-detected if not provided'}}
    required: Optional[List[str]] = ['query']

    def __init__(self, database: PostgreSQLDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, query: str, query_type: str=None) -> Dict[str, Any]:
        try:
            if not self.database:
                return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
            query_type_enum = None
            if query_type:
                try:
                    query_type_enum = QueryType(query_type.lower())
                except ValueError:
                    return {'success': False, 'error': f'Invalid query type: {query_type}', 'data': None}
            result = self.database.execute_query(query=query, query_type=query_type_enum)
            return result
        except Exception as e:
            logger.error(f'Error in postgresql_execute tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

def __call__(self, query: str, query_type: str=None) -> Dict[str, Any]:
    try:
        if not self.database:
            return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
        query_type_enum = None
        if query_type:
            try:
                query_type_enum = QueryType(query_type.lower())
            except ValueError:
                return {'success': False, 'error': f'Invalid query type: {query_type}', 'data': None}
        result = self.database.execute_query(query=query, query_type=query_type_enum)
        return result
    except Exception as e:
        logger.error(f'Error in postgresql_execute tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

class PostgreSQLFindTool(Tool):
    name: str = 'postgresql_find'
    description: str = 'Find (SELECT) rows from a PostgreSQL table.'
    inputs: Dict[str, Dict[str, str]] = {'table_name': {'type': 'string', 'description': 'Table name to query'}, 'where': {'type': 'string', 'description': "WHERE clause (optional, e.g., 'age > 18')"}, 'columns': {'type': 'string', 'description': "Comma-separated columns to select (default '*')"}, 'limit': {'type': 'integer', 'description': 'Maximum number of rows to return (optional)'}, 'offset': {'type': 'integer', 'description': 'Number of rows to skip (optional)'}, 'sort': {'type': 'string', 'description': "ORDER BY clause (optional, e.g., 'age ASC')"}}
    required: Optional[List[str]] = ['table_name']

    def __init__(self, database: PostgreSQLDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, table_name: str, where: str=None, columns: str='*', limit: int=None, offset: int=None, sort: str=None) -> Dict[str, Any]:
        try:
            if not self.database:
                return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
            sql = f'SELECT {columns} FROM {table_name}'
            if where:
                sql += f' WHERE {where}'
            if sort:
                sql += f' ORDER BY {sort}'
            if limit is not None:
                sql += f' LIMIT {limit}'
            if offset is not None:
                sql += f' OFFSET {offset}'
            result = self.database.execute_query(sql, QueryType.SELECT)
            return result
        except Exception as e:
            logger.error(f'Error in postgresql_find tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

def __call__(self, table_name: str, where: str=None, columns: str='*', limit: int=None, offset: int=None, sort: str=None) -> Dict[str, Any]:
    try:
        if not self.database:
            return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
        sql = f'SELECT {columns} FROM {table_name}'
        if where:
            sql += f' WHERE {where}'
        if sort:
            sql += f' ORDER BY {sort}'
        if limit is not None:
            sql += f' LIMIT {limit}'
        if offset is not None:
            sql += f' OFFSET {offset}'
        result = self.database.execute_query(sql, QueryType.SELECT)
        return result
    except Exception as e:
        logger.error(f'Error in postgresql_find tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

class PostgreSQLUpdateTool(Tool):
    name: str = 'postgresql_update'
    description: str = 'Update rows in a PostgreSQL table.'
    inputs: Dict[str, Dict[str, str]] = {'table_name': {'type': 'string', 'description': 'Table name to update'}, 'set': {'type': 'string', 'description': "SET clause (e.g., 'status = 'active'')"}, 'where': {'type': 'string', 'description': 'WHERE clause (optional)'}}
    required: Optional[List[str]] = ['table_name', 'set']

    def __init__(self, database: PostgreSQLDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, table_name: str, set: str, where: str=None) -> Dict[str, Any]:
        try:
            if not self.database:
                return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
            sql = f'UPDATE {table_name} SET {set}'
            if where:
                sql += f' WHERE {where}'
            result = self.database.execute_query(sql, QueryType.UPDATE)
            return result
        except Exception as e:
            logger.error(f'Error in postgresql_update tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

def __call__(self, table_name: str, set: str, where: str=None) -> Dict[str, Any]:
    try:
        if not self.database:
            return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
        sql = f'UPDATE {table_name} SET {set}'
        if where:
            sql += f' WHERE {where}'
        result = self.database.execute_query(sql, QueryType.UPDATE)
        return result
    except Exception as e:
        logger.error(f'Error in postgresql_update tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

class PostgreSQLCreateTool(Tool):
    name: str = 'postgresql_create'
    description: str = 'Create a table or other object in PostgreSQL.'
    inputs: Dict[str, Dict[str, str]] = {'query': {'type': 'string', 'description': 'CREATE statement (e.g., CREATE TABLE ...)'}}
    required: Optional[List[str]] = ['query']

    def __init__(self, database: PostgreSQLDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, query: str) -> Dict[str, Any]:
        try:
            if not self.database:
                return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
            result = self.database.execute_query(query, QueryType.CREATE)
            return result
        except Exception as e:
            logger.error(f'Error in postgresql_create tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

def __call__(self, query: str) -> Dict[str, Any]:
    try:
        if not self.database:
            return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
        result = self.database.execute_query(query, QueryType.CREATE)
        return result
    except Exception as e:
        logger.error(f'Error in postgresql_create tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

class PostgreSQLDeleteTool(Tool):
    name: str = 'postgresql_delete'
    description: str = 'Delete rows from a PostgreSQL table.'
    inputs: Dict[str, Dict[str, str]] = {'table_name': {'type': 'string', 'description': 'Table name to delete from'}, 'where': {'type': 'string', 'description': 'WHERE clause (optional)'}}
    required: Optional[List[str]] = ['table_name']

    def __init__(self, database: PostgreSQLDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, table_name: str, where: str=None) -> Dict[str, Any]:
        try:
            if not self.database:
                return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
            sql = f'DELETE FROM {table_name}'
            if where:
                sql += f' WHERE {where}'
            result = self.database.execute_query(sql, QueryType.DELETE)
            return result
        except Exception as e:
            logger.error(f'Error in postgresql_delete tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

def __call__(self, table_name: str, where: str=None) -> Dict[str, Any]:
    try:
        if not self.database:
            return {'success': False, 'error': 'PostgreSQL database not initialized', 'data': None}
        sql = f'DELETE FROM {table_name}'
        if where:
            sql += f' WHERE {where}'
        result = self.database.execute_query(sql, QueryType.DELETE)
        return result
    except Exception as e:
        logger.error(f'Error in postgresql_delete tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

class PostgreSQLToolkit(Toolkit):

    def __init__(self, name: str='PostgreSQLToolkit', connection_string: str=None, database_name: str=None, local_path: str=None, auto_save: bool=True, **kwargs):
        database = PostgreSQLDatabase(connection_string=connection_string, database_name=database_name, local_path=local_path, auto_save=auto_save, **kwargs)
        tools = [PostgreSQLExecuteTool(database=database), PostgreSQLFindTool(database=database), PostgreSQLUpdateTool(database=database), PostgreSQLCreateTool(database=database), PostgreSQLDeleteTool(database=database), PostgreSQLInfoTool(database=database)]
        super().__init__(name=name, tools=tools)
        self.database = database
        self.connection_string = connection_string
        self.database_name = database_name
        self.local_path = local_path
        self.auto_save = auto_save
        import atexit
        atexit.register(self._cleanup)

    def _cleanup(self):
        try:
            if self.database:
                self.database.disconnect()
                logger.info('Disconnected from PostgreSQL database')
        except Exception as e:
            logger.warning(f'Error during cleanup: {str(e)}')

    def get_capabilities(self) -> Dict[str, Any]:
        if self.database:
            capabilities = self.database.get_capabilities()
            capabilities.update({'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save})
            return capabilities
        return {'error': 'PostgreSQL database not initialized'}

    def connect(self) -> bool:
        return self.database.connect() if self.database else False

    def disconnect(self) -> bool:
        return self.database.disconnect() if self.database else False

    def test_connection(self) -> bool:
        return self.database.test_connection() if self.database else False

    def get_database(self) -> PostgreSQLDatabase:
        return self.database

    def get_local_info(self) -> Dict[str, Any]:
        return {'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save, 'database_name': self.database_name, 'connection_string': self.connection_string} if self.database else {'error': 'Database not initialized'}

def connect(self) -> bool:
    return self.database.connect() if self.database else False

def get_local_info(self) -> Dict[str, Any]:
    return {'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save, 'database_name': self.database_name, 'connection_string': self.connection_string} if self.database else {'error': 'Database not initialized'}

class RequestBase(BaseModule):
    """
    Base class for handling HTTP requests, parsing content, and saving data.
    This class provides common functionality for web scraping and HTTP operations.
    """

    def __init__(self, timeout: int=30, max_retries: int=3, delay_between_requests: float=1.0):
        """
        Initialize the RequestBase with configuration options.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            delay_between_requests: Delay between requests in seconds
        """
        super().__init__()
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.session = requests.Session()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})

    def request(self, url: str, method: str='GET', headers: Optional[Dict[str, str]]=None, params: Optional[Dict[str, Any]]=None, data: Optional[Dict[str, Any]]=None, json_data: Optional[Dict[str, Any]]=None) -> requests.Response:
        """
        Make an HTTP request with retry logic and error handling.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Additional headers to include
            params: URL parameters
            data: Form data to send
            json_data: JSON data to send
            
        Returns:
            requests.Response object
            
        Raises:
            requests.RequestException: If request fails after all retries
        """
        if headers:
            request_headers = {**self.session.headers, **headers}
        else:
            request_headers = self.session.headers
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method=method.upper(), url=url, headers=request_headers, params=params, data=data, json=json_data, timeout=self.timeout)
                response.raise_for_status()
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_requests)
                return response
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(self.delay_between_requests * (attempt + 1))

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content using BeautifulSoup.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            BeautifulSoup object for parsing
        """
        return BeautifulSoup(html_content, 'html.parser')

    def parse_json(self, json_content: str) -> Dict[str, Any]:
        """
        Parse JSON content.
        
        Args:
            json_content: Raw JSON content
            
        Returns:
            Parsed JSON as dictionary
        """
        return json.loads(json_content)

    def extract_text(self, html_content: str, selector: Optional[str]=None) -> str:
        """
        Extract text content from HTML using html2text.
        
        Args:
            html_content: Raw HTML content
            selector: CSS selector to extract specific elements (optional)
            
        Returns:
            Extracted text content
        """
        if selector:
            soup = self.parse_html(html_content)
            elements = soup.select(selector)
            combined_html = '\n'.join([str(elem) for elem in elements])
            return self.html_converter.handle(combined_html)
        else:
            return self.html_converter.handle(html_content)

    def extract_links(self, html_content: str, base_url: str=None) -> list:
        """
        Extract all links from HTML content.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL to resolve relative links
            
        Returns:
            List of extracted URLs
        """
        soup = self.parse_html(html_content)
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if base_url and (not href.startswith(('http://', 'https://', 'mailto:', 'tel:'))):
                href = urljoin(base_url, href)
            links.append(href)
        return links

    def save_content(self, content: Union[str, Dict[str, Any], bytes], file_path: str, content_type: str='text') -> bool:
        """
        Save content to a file.
        
        Args:
            content: Content to save (string, dictionary, or bytes)
            file_path: Path where to save the file
            content_type: Type of content ('text', 'json', 'html', 'pdf', 'binary')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if content_type.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
            elif content_type.lower() in ['pdf', 'binary'] or isinstance(content, bytes):
                with open(file_path, 'wb') as f:
                    if isinstance(content, bytes):
                        f.write(content)
                    else:
                        f.write(str(content).encode('utf-8'))
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            return True
        except Exception as e:
            print(f'Error saving content to {file_path}: {e}')
            return False

    def get_page_info(self, url: str) -> Dict[str, Any]:
        """
        Get basic information about a webpage.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary containing page information
        """
        try:
            response = self.request(url)
            soup = self.parse_html(response.text)
            info = {'url': url, 'status_code': response.status_code, 'title': soup.title.string if soup.title else '', 'content_type': response.headers.get('content-type', ''), 'content_length': len(response.text), 'links_count': len(soup.find_all('a', href=True)), 'images_count': len(soup.find_all('img'))}
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                info['description'] = meta_desc.get('content', '')
            return info
        except Exception as e:
            return {'error': str(e), 'url': url}

    def request_and_process(self, url: str, method: str='GET', headers: Optional[Dict[str, str]]=None, params: Optional[Dict[str, Any]]=None, data: Optional[Dict[str, Any]]=None, json_data: Optional[Dict[str, Any]]=None, return_raw: bool=False, save_file_path: Optional[str]=None) -> Dict[str, Any]:
        """
        Make a request and process the response with comprehensive error handling.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Additional headers to include
            params: URL parameters
            data: Form data to send
            json_data: JSON data to send
            return_raw: If True, return raw HTML content, otherwise processed text
            save_file_path: Optional path to save the content
            
        Returns:
            Dictionary containing processed response data
        """
        try:
            response = self.request(url=url, method=method, headers=headers, params=params, data=data, json_data=json_data)
            content_type = response.headers.get('content-type', '').lower()
            result = {'url': url, 'method': method.upper(), 'status_code': response.status_code, 'success': True, 'content_type': content_type, 'content_length': len(response.text), 'headers': dict(response.headers)}
            if return_raw:
                result['content'] = response.text
            elif 'json' in content_type:
                try:
                    result['content'] = response.json()
                except json.JSONDecodeError:
                    result['content'] = response.text
                    result['warning'] = 'Content-Type indicates JSON but parsing failed'
            else:
                result['content'] = self.extract_text(response.text)
            if save_file_path:
                save_success = self._save_response_content(response, save_file_path, content_type)
                result['saved_to_file'] = save_file_path if save_success else None
                if not save_success:
                    result['save_warning'] = f'Failed to save content to {save_file_path}'
            return result
        except Exception as e:
            return {'url': url, 'method': method.upper(), 'error': str(e), 'success': False}

    def _save_response_content(self, response: requests.Response, file_path: str, content_type: str) -> bool:
        """
        Save response content to file with appropriate format.
        
        Args:
            response: The response object
            file_path: Path to save the file
            content_type: Content type of the response
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if 'json' in content_type:
                try:
                    json_content = response.json()
                    return self.save_content(json_content, file_path, 'json')
                except json.JSONDecodeError:
                    return self.save_content(response.text, file_path, 'text')
            elif 'html' in content_type:
                return self.save_content(response.text, file_path, 'html')
            else:
                return self.save_content(response.text, file_path, 'text')
        except Exception as e:
            print(f'Error saving response content: {e}')
            return False

    def close(self):
        """Close the session."""
        self.session.close()

def parse_json(self, json_content: str) -> Dict[str, Any]:
    """
        Parse JSON content.
        
        Args:
            json_content: Raw JSON content
            
        Returns:
            Parsed JSON as dictionary
        """
    return json.loads(json_content)

class MongoDBConnection(DatabaseConnection):
    """MongoDB-specific connection management"""

    def __init__(self, connection_string: str, **kwargs):
        super().__init__(connection_string, **kwargs)
        self.client = None
        self.database = None

    def connect(self) -> bool:
        """Establish connection to MongoDB"""
        try:
            if 'mongodb://' in self.connection_string or 'mongodb+srv://' in self.connection_string:
                self.client = MongoClient(self.connection_string, **self.connection_params)
            else:
                self.client = MongoClient(self.connection_string, **self.connection_params)
            self.client.admin.command('ping')
            self._is_connected = True
            logger.info('Successfully connected to MongoDB')
            return True
        except Exception as e:
            logger.error(f'Failed to connect to MongoDB: {str(e)}')
            self._is_connected = False
            return False

    def disconnect(self) -> bool:
        """Close MongoDB connection"""
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.database = None
                self._is_connected = False
                logger.info('Disconnected from MongoDB')
            return True
        except Exception as e:
            logger.error(f'Error disconnecting from MongoDB: {str(e)}')
            return False

    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False

    def get_database(self, database_name: str):
        """Get database instance"""
        if self.client and database_name:
            return self.client[database_name]
        return None

def connect(self) -> bool:
    """Establish connection to MongoDB"""
    try:
        if 'mongodb://' in self.connection_string or 'mongodb+srv://' in self.connection_string:
            self.client = MongoClient(self.connection_string, **self.connection_params)
        else:
            self.client = MongoClient(self.connection_string, **self.connection_params)
        self.client.admin.command('ping')
        self._is_connected = True
        logger.info('Successfully connected to MongoDB')
        return True
    except Exception as e:
        logger.error(f'Failed to connect to MongoDB: {str(e)}')
        self._is_connected = False
        return False

def disconnect(self) -> bool:
    """Close MongoDB connection"""
    try:
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self._is_connected = False
            logger.info('Disconnected from MongoDB')
        return True
    except Exception as e:
        logger.error(f'Error disconnecting from MongoDB: {str(e)}')
        return False

def test_connection(self) -> bool:
    """Test MongoDB connection"""
    try:
        if self.client:
            self.client.admin.command('ping')
            return True
        return False
    except Exception:
        return False

class MongoDBDatabase(DatabaseBase):
    """
    MongoDB database implementation with automatic initialization.
    Handles remote connections, existing local databases, and new local database creation.
    """

    def __init__(self, connection_string: str=None, database_name: str=None, local_path: str=None, auto_save: bool=True, read_only: bool=False, **kwargs):
        """
        Initialize MongoDB database with automatic detection and setup.
        
        Args:
            connection_string: MongoDB connection string (for remote)
            database_name: Name of the database
            local_path: Path for local file-based database
            auto_save: Automatically save changes to local files
            read_only: If True, only read operations are allowed (no insert, update, delete)
            **kwargs: Additional connection parameters
        """
        init_params = {'connection_string': connection_string, 'database_name': database_name}
        super().__init__(**init_params, **kwargs)
        self.local_path = Path(local_path) if local_path else None
        self.auto_save = auto_save
        self.read_only = read_only
        self.connection_params = kwargs
        self.is_local_database = False
        self.client = None
        self.database = None
        if self._is_remote_connection():
            self._init_remote_database()
        elif self._is_existing_local_database():
            self._init_existing_local_database()
        else:
            self._init_new_local_database()

    def _is_remote_connection(self) -> bool:
        """Check if this is a remote MongoDB connection"""
        return self.connection_string and (self.connection_string.startswith(('mongodb://', 'mongodb+srv://')) or 'localhost' in self.connection_string or '127.0.0.1' in self.connection_string)

    def _is_existing_local_database(self) -> bool:
        """Check if there's an existing local database"""
        if not self.local_path:
            return False
        if not self.local_path.exists():
            return False
        json_files = list(self.local_path.glob('*.json'))
        db_info_file = self.local_path / 'db_info.json'
        return len(json_files) > 0 or db_info_file.exists()

    def _init_remote_database(self):
        """Initialize remote MongoDB connection"""
        try:
            self.client = MongoClient(self.connection_string, **self.connection_params)
            self.client.admin.command('ping')
            if self.database_name:
                self.database = self.client[self.database_name]
            self._is_initialized = True
            self.is_local_database = False
            logger.info(f'Connected to remote MongoDB: {self.database_name}')
        except Exception as e:
            logger.error(f'Failed to connect to remote MongoDB: {str(e)}')
            self._is_initialized = False
            raise

    def _init_existing_local_database(self):
        """Initialize existing local database"""
        try:
            self.connection_string = 'mongodb://localhost:27017'
            self.client = MongoClient(self.connection_string, **self.connection_params)
            if not self.database_name:
                self.database_name = self.local_path.name
            self.database = self.client[self.database_name]
            self._load_local_collections()
            self._is_initialized = True
            self.is_local_database = True
            logger.info(f'Loaded existing local database from: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to load existing local database: {str(e)}')
            self._is_initialized = False
            raise

    def _init_new_local_database(self):
        """Initialize new local database"""
        try:
            if not self.local_path:
                self.local_path = Path('./mongodb_local')
            self.local_path.mkdir(parents=True, exist_ok=True)
            self.connection_string = 'mongodb://localhost:27017'
            self.client = MongoClient(self.connection_string, **self.connection_params)
            if not self.database_name:
                self.database_name = self.local_path.name
            self.database = self.client[self.database_name]
            self._create_db_info_file()
            self._is_initialized = True
            self.is_local_database = True
            logger.info(f'Created new local database at: {self.local_path}')
        except Exception as e:
            logger.error(f'Failed to create new local database: {str(e)}')
            self._is_initialized = False
            raise

    def _load_local_collections(self):
        """Load collections from local JSON files"""
        if not self.local_path or not self.local_path.exists():
            return
        json_files = [f for f in self.local_path.glob('*.json') if f.name != 'db_info.json']
        for json_file in json_files:
            collection_name = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    documents = [data]
                elif isinstance(data, list):
                    documents = data
                else:
                    continue
                if documents:
                    cleaned_documents = []
                    for doc in documents:
                        cleaned_doc = self._clean_document_for_insert(doc)
                        cleaned_documents.append(cleaned_doc)
                    collection = self.database[collection_name]
                    collection.drop()
                    if cleaned_documents:
                        collection.insert_many(cleaned_documents)
                        logger.info(f"Loaded {len(cleaned_documents)} documents into '{collection_name}'")
            except Exception as e:
                logger.warning(f'Failed to load collection from {json_file}: {str(e)}')

    def _clean_document_for_insert(self, doc: Dict) -> Dict:
        """Clean document by removing problematic MongoDB-specific fields"""
        if isinstance(doc, dict):
            cleaned = {}
            for key, value in doc.items():
                if key == '_id' and isinstance(value, dict) and ('$oid' in value):
                    continue
                elif isinstance(value, dict):
                    cleaned[key] = self._clean_document_for_insert(value)
                elif isinstance(value, list):
                    cleaned[key] = [self._clean_document_for_insert(item) if isinstance(item, dict) else item for item in value]
                else:
                    cleaned[key] = value
            return cleaned
        return doc

    def _create_db_info_file(self):
        """Create database info file for new local database"""
        try:
            db_info = {'database_name': self.database_name, 'created_at': time.time(), 'local_path': str(self.local_path.absolute()), 'auto_save': self.auto_save, 'version': '1.0'}
            info_file = self.local_path / 'db_info.json'
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(db_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f'Failed to create db info file: {str(e)}')

    def _save_collection_to_file(self, collection_name: str):
        """Save collection to local JSON file"""
        if not self.is_local_database or not self.local_path:
            return
        try:
            collection = self.database[collection_name]
            documents = list(collection.find())
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            file_path = self.local_path / f'{collection_name}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(documents, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"Saved collection '{collection_name}' to {file_path}")
        except Exception as e:
            logger.warning(f"Failed to save collection '{collection_name}': {str(e)}")

    def _auto_save_if_needed(self, collection_name: str):
        """Auto-save collection if local database and auto_save is enabled"""
        if self.is_local_database and self.auto_save:
            self._save_collection_to_file(collection_name)

    def _get_database_type(self) -> DatabaseType:
        return DatabaseType.MONGODB

    def connect(self) -> bool:
        """Connection is already established in __init__"""
        return self._is_initialized

    def disconnect(self) -> bool:
        """Close MongoDB connection"""
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.database = None
                self._is_initialized = False
                logger.info('Disconnected from MongoDB')
            return True
        except Exception as e:
            logger.error(f'Error disconnecting: {str(e)}')
            return False

    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False

    def execute_query(self, query: Union[str, Dict, List], query_type: QueryType=None, collection_name: str=None, **kwargs) -> Dict[str, Any]:
        """Execute a query on MongoDB with automatic result handling"""
        if not self._is_initialized or self.database is None:
            return self.format_error_result('Database not connected')
        if not collection_name:
            return self.format_error_result('Collection name is required')
        start_time = time.time()
        try:
            collection = self.database[collection_name]
            if not query_type:
                query_type = self._infer_query_type(query)
            if self.read_only and query_type in [QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP]:
                return self.format_error_result(f"Write operation '{query_type.value}' is not allowed in read-only mode. Only SELECT and AGGREGATE operations are permitted.", query_type, execution_time=time.time() - start_time)
            if query_type == QueryType.SELECT:
                result = self._execute_find(collection, query, **kwargs)
            elif query_type == QueryType.INSERT:
                result = self._execute_insert(collection, query, **kwargs)
                self._auto_save_if_needed(collection_name)
            elif query_type == QueryType.UPDATE:
                result = self._execute_update(collection, query, **kwargs)
                self._auto_save_if_needed(collection_name)
            elif query_type == QueryType.DELETE:
                result = self._execute_delete(collection, query, **kwargs)
                self._auto_save_if_needed(collection_name)
            elif query_type == QueryType.AGGREGATE:
                result = self._execute_aggregate(collection, query, **kwargs)
            else:
                return self.format_error_result(f'Unsupported query type: {query_type}')
            execution_time = time.time() - start_time
            if isinstance(result, dict):
                result['execution_time'] = execution_time
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f'Error executing MongoDB query: {str(e)}')
            return self.format_error_result(str(e), query_type, execution_time=execution_time)

    def _infer_query_type(self, query: Union[str, Dict, List]) -> QueryType:
        """Infer query type from the query structure"""
        if isinstance(query, list):
            return QueryType.AGGREGATE
        elif isinstance(query, dict):
            if self.read_only:
                if 'insert' in query or 'insertOne' in query or 'insertMany' in query:
                    return QueryType.SELECT
                elif 'update' in query or 'updateOne' in query or 'updateMany' in query:
                    return QueryType.SELECT
                elif 'delete' in query or 'deleteOne' in query or 'deleteMany' in query:
                    return QueryType.SELECT
                elif 'create' in query or 'createCollection' in query:
                    return QueryType.SELECT
                elif 'drop' in query or 'dropCollection' in query:
                    return QueryType.SELECT
                else:
                    return QueryType.SELECT
            elif 'insert' in query or 'insertOne' in query or 'insertMany' in query:
                return QueryType.INSERT
            elif 'update' in query or 'updateOne' in query or 'updateMany' in query:
                return QueryType.UPDATE
            elif 'delete' in query or 'deleteOne' in query or 'deleteMany' in query:
                return QueryType.DELETE
            elif 'create' in query or 'createCollection' in query:
                return QueryType.CREATE
            elif 'drop' in query or 'dropCollection' in query:
                return QueryType.DROP
            else:
                return QueryType.SELECT
        elif isinstance(query, str):
            query_lower = query.lower().strip()
            if self.read_only:
                return QueryType.SELECT
            elif query_lower.startswith(('insert', 'create')):
                return QueryType.INSERT
            elif query_lower.startswith('update'):
                return QueryType.UPDATE
            elif query_lower.startswith('delete'):
                return QueryType.DELETE
            elif query_lower.startswith('drop'):
                return QueryType.DROP
            else:
                return QueryType.SELECT
        return QueryType.SELECT

    def _execute_find(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
        """Execute find query"""
        try:
            if isinstance(query, str):
                if '=' in query:
                    field, value = query.split('=', 1)
                    query = {field.strip(): value.strip()}
                else:
                    query = {}
            filter_query = query.get('filter', query)
            projection = query.get('projection', {})
            sort = query.get('sort', None)
            limit = query.get('limit', kwargs.get('limit', 0))
            skip = query.get('skip', kwargs.get('skip', 0))
            cursor = collection.find(filter_query, projection)
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            results = []
            for doc in cursor:
                doc = json.loads(json_util.dumps(doc))
                results.append(doc)
            return self.format_query_result(results, QueryType.SELECT, collection_name=collection.name, filter_applied=filter_query)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.SELECT)

    def _execute_insert(self, collection, query: Union[Dict, List], **kwargs) -> Dict[str, Any]:
        """Execute insert operation"""
        try:
            if isinstance(query, dict):
                if 'document' in query:
                    document = query['document']
                else:
                    document = query
                result = collection.insert_one(document)
                return self.format_query_result({'inserted_id': str(result.inserted_id)}, QueryType.INSERT, collection_name=collection.name)
            elif isinstance(query, list):
                if all((isinstance(item, dict) for item in query)):
                    documents = query
                else:
                    documents = [{'documents': query}]
                result = collection.insert_many(documents)
                return self.format_query_result({'inserted_ids': [str(id) for id in result.inserted_ids]}, QueryType.INSERT, collection_name=collection.name)
            else:
                return self.format_error_result('Invalid insert query format', QueryType.INSERT)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.INSERT)

    def _execute_update(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
        """Execute update operation"""
        try:
            filter_query = query.get('filter', {})
            update_query = query.get('update', {})
            upsert = query.get('upsert', False)
            multi = query.get('multi', False)
            if multi:
                result = collection.update_many(filter_query, update_query, upsert=upsert)
            else:
                result = collection.update_one(filter_query, update_query, upsert=upsert)
            return self.format_query_result({'matched_count': result.matched_count, 'modified_count': result.modified_count, 'upserted_id': str(result.upserted_id) if result.upserted_id else None}, QueryType.UPDATE, collection_name=collection.name)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.UPDATE)

    def _execute_delete(self, collection, query: Dict, **kwargs) -> Dict[str, Any]:
        """Execute delete operation"""
        try:
            filter_query = query.get('filter', query)
            multi = query.get('multi', False)
            if multi:
                result = collection.delete_many(filter_query)
            else:
                result = collection.delete_one(filter_query)
            return self.format_query_result({'deleted_count': result.deleted_count}, QueryType.DELETE, collection_name=collection.name)
        except Exception as e:
            return self.format_error_result(str(e), QueryType.DELETE)

    def _execute_aggregate(self, collection, pipeline: List, **kwargs) -> Dict[str, Any]:
        """Execute aggregation pipeline"""
        try:
            cursor = collection.aggregate(pipeline)
            results = []
            for doc in cursor:
                doc = json.loads(json_util.dumps(doc))
                results.append(doc)
            return self.format_query_result(results, QueryType.AGGREGATE, collection_name=collection.name, pipeline_stages=len(pipeline))
        except Exception as e:
            return self.format_error_result(str(e), QueryType.AGGREGATE)

    def get_database_info(self) -> Dict[str, Any]:
        """Get MongoDB database information"""
        try:
            if not self._is_initialized or self.database is None:
                return self.format_error_result('Database not connected')
            stats = self.database.command('dbStats')
            server_info = self.client.server_info()
            info = {'database_name': self.database_name, 'collections': stats.get('collections', 0), 'data_size': stats.get('dataSize', 0), 'storage_size': stats.get('storageSize', 0), 'indexes': stats.get('indexes', 0), 'index_size': stats.get('indexSize', 0), 'server_version': server_info.get('version', 'Unknown'), 'server_type': server_info.get('type', 'Unknown'), 'connection_string': self.connection_string, 'is_connected': self._is_initialized}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def list_collections(self) -> List[str]:
        """List all collections in the database"""
        try:
            if not self._is_initialized or self.database is None:
                return []
            return self.database.list_collection_names()
        except Exception as e:
            logger.error(f'Error listing collections: {str(e)}')
            return []

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a specific collection"""
        try:
            if not self._is_initialized or not self.database:
                return self.format_error_result('Database not connected')
            collection = self.database[collection_name]
            stats = self.database.command('collStats', collection_name)
            indexes = list(collection.list_indexes())
            sample_docs = list(collection.find().limit(5))
            info = {'collection_name': collection_name, 'document_count': stats.get('count', 0), 'data_size': stats.get('size', 0), 'storage_size': stats.get('storageSize', 0), 'index_count': stats.get('nindexes', 0), 'indexes': [{'name': idx['name'], 'keys': idx['key']} for idx in indexes], 'sample_documents': sample_docs[:2]}
            return self.format_query_result(info, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def get_schema(self, collection_name: str=None) -> Dict[str, Any]:
        """Get schema information for database or specific collection"""
        try:
            if not self._is_initialized or not self.database:
                return self.format_error_result('Database not connected')
            if collection_name:
                collection = self.database[collection_name]
                sample_docs = list(collection.find().limit(100))
                if not sample_docs:
                    return self.format_query_result({'collection_name': collection_name, 'schema': {}, 'message': 'No documents found'}, QueryType.SELECT)
                schema = self._infer_schema_from_documents(sample_docs)
                return self.format_query_result({'collection_name': collection_name, 'schema': schema, 'sample_count': len(sample_docs)}, QueryType.SELECT)
            else:
                collections = self.list_collections()
                schemas = {}
                for coll_name in collections[:10]:
                    coll_schema = self.get_schema(coll_name)
                    if coll_schema.get('success'):
                        schemas[coll_name] = coll_schema.get('data', {}).get('schema', {})
                return self.format_query_result({'database_name': self.database_name, 'schemas': schemas}, QueryType.SELECT)
        except Exception as e:
            return self.format_error_result(str(e))

    def _infer_schema_from_documents(self, documents: List[Dict]) -> Dict[str, Any]:
        """Infer schema from a list of documents"""
        if not documents:
            return {}
        schema = {}
        for doc in documents:
            self._update_schema_from_document(schema, doc)
        return schema

    def _update_schema_from_document(self, schema: Dict, document: Dict, path: str=''):
        """Recursively update schema from a document"""
        for key, value in document.items():
            current_path = f'{path}.{key}' if path else key
            if isinstance(value, dict):
                if current_path not in schema:
                    schema[current_path] = {'type': 'object', 'fields': {}}
                self._update_schema_from_document(schema[current_path]['fields'], value, current_path)
            elif isinstance(value, list):
                if current_path not in schema:
                    schema[current_path] = {'type': 'array', 'element_types': set()}
                for item in value[:3]:
                    if isinstance(item, dict):
                        schema[current_path]['element_types'].add('object')
                    else:
                        schema[current_path]['element_types'].add(type(item).__name__)
                schema[current_path]['element_types'] = list(schema[current_path]['element_types'])
            elif current_path not in schema:
                schema[current_path] = {'type': type(value).__name__}
            elif schema[current_path]['type'] != type(value).__name__:
                schema[current_path]['type'] = 'mixed'

    def get_supported_query_types(self) -> List[QueryType]:
        """Get MongoDB-specific supported query types"""
        if self.read_only:
            return [QueryType.SELECT, QueryType.AGGREGATE]
        else:
            return [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP, QueryType.AGGREGATE, QueryType.INDEX]

    def get_capabilities(self) -> Dict[str, Any]:
        """Get MongoDB-specific capabilities"""
        base_capabilities = super().get_capabilities()
        base_capabilities.update({'supports_aggregation': True, 'supports_full_text_search': True, 'supports_geospatial_queries': True, 'supports_change_streams': True, 'supports_transactions': True, 'supports_indexing': True, 'document_oriented': True, 'schema_flexible': True, 'read_only': self.read_only, 'write_operations_allowed': not self.read_only})
        return base_capabilities

def _init_remote_database(self):
    """Initialize remote MongoDB connection"""
    try:
        self.client = MongoClient(self.connection_string, **self.connection_params)
        self.client.admin.command('ping')
        if self.database_name:
            self.database = self.client[self.database_name]
        self._is_initialized = True
        self.is_local_database = False
        logger.info(f'Connected to remote MongoDB: {self.database_name}')
    except Exception as e:
        logger.error(f'Failed to connect to remote MongoDB: {str(e)}')
        self._is_initialized = False
        raise

def _init_existing_local_database(self):
    """Initialize existing local database"""
    try:
        self.connection_string = 'mongodb://localhost:27017'
        self.client = MongoClient(self.connection_string, **self.connection_params)
        if not self.database_name:
            self.database_name = self.local_path.name
        self.database = self.client[self.database_name]
        self._load_local_collections()
        self._is_initialized = True
        self.is_local_database = True
        logger.info(f'Loaded existing local database from: {self.local_path}')
    except Exception as e:
        logger.error(f'Failed to load existing local database: {str(e)}')
        self._is_initialized = False
        raise

def disconnect(self) -> bool:
    """Close MongoDB connection"""
    try:
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self._is_initialized = False
            logger.info('Disconnected from MongoDB')
        return True
    except Exception as e:
        logger.error(f'Error disconnecting: {str(e)}')
        return False

def test_connection(self) -> bool:
    """Test MongoDB connection"""
    try:
        if self.client:
            self.client.admin.command('ping')
            return True
        return False
    except Exception:
        return False

def list_collections(self) -> List[str]:
    """List all collections in the database"""
    try:
        if not self._is_initialized or self.database is None:
            return []
        return self.database.list_collection_names()
    except Exception as e:
        logger.error(f'Error listing collections: {str(e)}')
        return []

class MongoDBExecuteQueryTool(Tool):
    name: str = 'mongodb_execute_query'
    description: str = 'Execute MongoDB queries including find and aggregation pipelines (read-only operations)'
    inputs: Dict[str, Dict[str, str]] = {'query': {'type': 'string', 'description': 'MongoDB query (JSON string for find, array for aggregation pipeline)'}, 'query_type': {'type': 'string', 'description': 'Type of query (select, aggregate) - auto-detected if not provided'}, 'collection_name': {'type': 'string', 'description': 'Collection name (required for all operations)'}}
    required: Optional[List[str]] = ['query', 'collection_name']

    def __init__(self, database: MongoDBDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, query: str, query_type: str=None, collection_name: str=None) -> Dict[str, Any]:
        """Execute a MongoDB query"""
        try:
            if not self.database:
                return {'success': False, 'error': 'MongoDB database not initialized', 'data': None}
            parsed_query = self._parse_query(query)
            query_type_enum = None
            if query_type:
                try:
                    query_type_enum = QueryType(query_type.lower())
                except ValueError:
                    return {'success': False, 'error': f'Invalid query type: {query_type}', 'data': None}
            result = self.database.execute_query(query=parsed_query, query_type=query_type_enum, collection_name=collection_name)
            if result['success']:
                logger.info(f'Successfully executed MongoDB query on collection {collection_name}')
            else:
                logger.error(f'Failed to execute MongoDB query: {result.get('error', 'Unknown error')}')
            return result
        except Exception as e:
            logger.error(f'Error in mongodb_execute_query tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

    def _parse_query(self, query: str) -> Union[str, Dict, List]:
        """Parse query string into appropriate format"""
        try:
            import json
            return json.loads(query)
        except (json.JSONDecodeError, ValueError):
            return query

def __call__(self, query: str, query_type: str=None, collection_name: str=None) -> Dict[str, Any]:
    """Execute a MongoDB query"""
    try:
        if not self.database:
            return {'success': False, 'error': 'MongoDB database not initialized', 'data': None}
        parsed_query = self._parse_query(query)
        query_type_enum = None
        if query_type:
            try:
                query_type_enum = QueryType(query_type.lower())
            except ValueError:
                return {'success': False, 'error': f'Invalid query type: {query_type}', 'data': None}
        result = self.database.execute_query(query=parsed_query, query_type=query_type_enum, collection_name=collection_name)
        if result['success']:
            logger.info(f'Successfully executed MongoDB query on collection {collection_name}')
        else:
            logger.error(f'Failed to execute MongoDB query: {result.get('error', 'Unknown error')}')
        return result
    except Exception as e:
        logger.error(f'Error in mongodb_execute_query tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

def _parse_query(self, query: str) -> Union[str, Dict, List]:
    """Parse query string into appropriate format"""
    try:
        import json
        return json.loads(query)
    except (json.JSONDecodeError, ValueError):
        return query

class MongoDBFindTool(Tool):
    name: str = 'mongodb_find'
    description: str = 'Find documents in a MongoDB collection with filtering, projection, sorting, and pagination'
    inputs: Dict[str, Dict[str, str]] = {'collection_name': {'type': 'string', 'description': 'Collection name to query'}, 'filter': {'type': 'string', 'description': 'MongoDB filter query (JSON string, e.g., \'{"age": {"$gt": 18}}\')'}, 'projection': {'type': 'string', 'description': 'Fields to include/exclude (JSON string, e.g., \'{"name": 1, "_id": 0}\')'}, 'sort': {'type': 'string', 'description': 'Sort criteria (JSON string, e.g., \'{"age": -1}\')'}, 'limit': {'type': 'integer', 'description': 'Maximum number of documents to return'}, 'skip': {'type': 'integer', 'description': 'Number of documents to skip'}}
    required: Optional[List[str]] = ['collection_name']

    def __init__(self, database: MongoDBDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, collection_name: str, filter: str='{}', projection: str='{}', sort: str=None, limit: int=0, skip: int=0) -> Dict[str, Any]:
        """Find documents in MongoDB collection"""
        try:
            if not self.database:
                return {'success': False, 'error': 'MongoDB database not initialized', 'data': None}
            import json
            filter_dict = json.loads(filter) if filter else {}
            projection_dict = json.loads(projection) if projection else {}
            sort_dict = json.loads(sort) if sort else None
            query = {'filter': filter_dict, 'projection': projection_dict, 'limit': limit, 'skip': skip}
            if sort_dict:
                query['sort'] = sort_dict
            result = self.database.execute_query(query=query, query_type=QueryType.SELECT, collection_name=collection_name)
            if result['success']:
                logger.info(f'Successfully found documents in collection {collection_name}')
            else:
                logger.error(f'Failed to find documents: {result.get('error', 'Unknown error')}')
            return result
        except Exception as e:
            logger.error(f'Error in mongodb_find tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

def __call__(self, collection_name: str, filter: str='{}', projection: str='{}', sort: str=None, limit: int=0, skip: int=0) -> Dict[str, Any]:
    """Find documents in MongoDB collection"""
    try:
        if not self.database:
            return {'success': False, 'error': 'MongoDB database not initialized', 'data': None}
        import json
        filter_dict = json.loads(filter) if filter else {}
        projection_dict = json.loads(projection) if projection else {}
        sort_dict = json.loads(sort) if sort else None
        query = {'filter': filter_dict, 'projection': projection_dict, 'limit': limit, 'skip': skip}
        if sort_dict:
            query['sort'] = sort_dict
        result = self.database.execute_query(query=query, query_type=QueryType.SELECT, collection_name=collection_name)
        if result['success']:
            logger.info(f'Successfully found documents in collection {collection_name}')
        else:
            logger.error(f'Failed to find documents: {result.get('error', 'Unknown error')}')
        return result
    except Exception as e:
        logger.error(f'Error in mongodb_find tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

class MongoDBUpdateTool(Tool):
    name: str = 'mongodb_update'
    description: str = 'Update documents in a MongoDB collection'
    inputs: Dict[str, Dict[str, str]] = {'collection_name': {'type': 'string', 'description': 'Collection name to update'}, 'filter': {'type': 'string', 'description': 'Filter to match documents to update (JSON string)'}, 'update': {'type': 'string', 'description': 'Update operations (JSON string, e.g., \'{"$set": {"status": "active"}}\')'}, 'upsert': {'type': 'boolean', 'description': "Create document if it doesn't exist"}, 'multi': {'type': 'boolean', 'description': 'Update multiple documents (default: false)'}}
    required: Optional[List[str]] = ['collection_name', 'filter', 'update']

    def __init__(self, database: MongoDBDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, collection_name: str, filter: str, update: str, upsert: bool=False, multi: bool=False) -> Dict[str, Any]:
        """Update documents in MongoDB collection"""
        try:
            if not self.database:
                return {'success': False, 'error': 'MongoDB database not initialized', 'data': None}
            import json
            filter_dict = json.loads(filter)
            update_dict = json.loads(update)
            query = {'filter': filter_dict, 'update': update_dict, 'upsert': upsert, 'multi': multi}
            result = self.database.execute_query(query=query, query_type=QueryType.UPDATE, collection_name=collection_name)
            if result['success']:
                logger.info(f'Successfully updated documents in collection {collection_name}')
            else:
                logger.error(f'Failed to update documents: {result.get('error', 'Unknown error')}')
            return result
        except Exception as e:
            logger.error(f'Error in mongodb_update tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

def __call__(self, collection_name: str, filter: str, update: str, upsert: bool=False, multi: bool=False) -> Dict[str, Any]:
    """Update documents in MongoDB collection"""
    try:
        if not self.database:
            return {'success': False, 'error': 'MongoDB database not initialized', 'data': None}
        import json
        filter_dict = json.loads(filter)
        update_dict = json.loads(update)
        query = {'filter': filter_dict, 'update': update_dict, 'upsert': upsert, 'multi': multi}
        result = self.database.execute_query(query=query, query_type=QueryType.UPDATE, collection_name=collection_name)
        if result['success']:
            logger.info(f'Successfully updated documents in collection {collection_name}')
        else:
            logger.error(f'Failed to update documents: {result.get('error', 'Unknown error')}')
        return result
    except Exception as e:
        logger.error(f'Error in mongodb_update tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

class MongoDBDeleteTool(Tool):
    name: str = 'mongodb_delete'
    description: str = 'Delete documents from a MongoDB collection'
    inputs: Dict[str, Dict[str, str]] = {'collection_name': {'type': 'string', 'description': 'Collection name to delete from'}, 'filter': {'type': 'string', 'description': 'Filter to match documents to delete (JSON string)'}, 'multi': {'type': 'boolean', 'description': 'Delete multiple documents (default: false)'}}
    required: Optional[List[str]] = ['collection_name', 'filter']

    def __init__(self, database: MongoDBDatabase=None):
        super().__init__()
        self.database = database

    def __call__(self, collection_name: str, filter: str, multi: bool=False) -> Dict[str, Any]:
        """Delete documents from MongoDB collection"""
        try:
            if not self.database:
                return {'success': False, 'error': 'MongoDB database not initialized', 'data': None}
            import json
            filter_dict = json.loads(filter)
            query = {'filter': filter_dict, 'multi': multi}
            result = self.database.execute_query(query=query, query_type=QueryType.DELETE, collection_name=collection_name)
            if result['success']:
                logger.info(f'Successfully deleted documents from collection {collection_name}')
            else:
                logger.error(f'Failed to delete documents: {result.get('error', 'Unknown error')}')
            return result
        except Exception as e:
            logger.error(f'Error in mongodb_delete tool: {str(e)}')
            return {'success': False, 'error': str(e), 'data': None}

def __call__(self, collection_name: str, filter: str, multi: bool=False) -> Dict[str, Any]:
    """Delete documents from MongoDB collection"""
    try:
        if not self.database:
            return {'success': False, 'error': 'MongoDB database not initialized', 'data': None}
        import json
        filter_dict = json.loads(filter)
        query = {'filter': filter_dict, 'multi': multi}
        result = self.database.execute_query(query=query, query_type=QueryType.DELETE, collection_name=collection_name)
        if result['success']:
            logger.info(f'Successfully deleted documents from collection {collection_name}')
        else:
            logger.error(f'Failed to delete documents: {result.get('error', 'Unknown error')}')
        return result
    except Exception as e:
        logger.error(f'Error in mongodb_delete tool: {str(e)}')
        return {'success': False, 'error': str(e), 'data': None}

class MongoDBToolkit(Toolkit):
    """
    MongoDB-specific toolkit with simplified design.
    Automatically handles remote, local file-based, or new database creation.
    """

    def __init__(self, name: str='MongoDBToolkit', connection_string: str=None, database_name: str=None, local_path: str=None, auto_save: bool=True, read_only: bool=False, **kwargs):
        """
        Initialize the MongoDB toolkit.
        
        Args:
            name: Name of the toolkit
            connection_string: MongoDB connection string (for remote/existing)
            database_name: Name of the database to use
            local_path: Path for local file-based database
            auto_save: Automatically save changes to local files
            read_only: If True, only read operations are allowed (no insert, update, delete)
            **kwargs: Additional connection parameters
        """
        database = MongoDBDatabase(connection_string=connection_string, database_name=database_name, local_path=local_path, auto_save=auto_save, read_only=read_only, **kwargs)
        if read_only:
            tools = [MongoDBExecuteQueryTool(database=database), MongoDBFindTool(database=database), MongoDBInfoTool(database=database)]
        else:
            tools = [MongoDBExecuteQueryTool(database=database), MongoDBFindTool(database=database), MongoDBUpdateTool(database=database), MongoDBDeleteTool(database=database), MongoDBInfoTool(database=database)]
        super().__init__(name=name, tools=tools)
        self.database = database
        self.connection_string = connection_string
        self.database_name = database_name
        self.local_path = local_path
        self.auto_save = auto_save
        import atexit
        atexit.register(self._cleanup)

    def _cleanup(self):
        """Cleanup function called when program exits"""
        try:
            if self.database.is_local_database and self.database.auto_save:
                logger.info('Auto-saving local database before exit...')
                collections = self.database.list_collections()
                for collection_name in collections:
                    self.database._save_collection_to_file(collection_name)
            if self.database:
                self.database.disconnect()
                logger.info('Disconnected from MongoDB database')
        except Exception as e:
            logger.warning(f'Error during cleanup: {str(e)}')

    def get_capabilities(self) -> Dict[str, Any]:
        """Get MongoDB-specific capabilities"""
        if self.database:
            capabilities = self.database.get_capabilities()
            capabilities.update({'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save, 'read_only': self.database.read_only})
            return capabilities
        return {'error': 'MongoDB database not initialized'}

    def connect(self) -> bool:
        """Connect to MongoDB"""
        return self.database.connect() if self.database else False

    def disconnect(self) -> bool:
        """Disconnect from MongoDB"""
        return self.database.disconnect() if self.database else False

    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        return self.database.test_connection() if self.database else False

    def get_database(self) -> MongoDBDatabase:
        """Get the underlying MongoDB database instance"""
        return self.database

    def get_local_info(self) -> Dict[str, Any]:
        """Get information about local database setup"""
        return {'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save, 'read_only': self.database.read_only, 'database_name': self.database_name, 'connection_string': self.connection_string} if self.database else {'error': 'Database not initialized'}

def connect(self) -> bool:
    """Connect to MongoDB"""
    return self.database.connect() if self.database else False

def get_local_info(self) -> Dict[str, Any]:
    """Get information about local database setup"""
    return {'is_local_database': self.database.is_local_database, 'local_path': str(self.database.local_path) if self.database.local_path else None, 'auto_save': self.database.auto_save, 'read_only': self.database.read_only, 'database_name': self.database_name, 'connection_string': self.connection_string} if self.database else {'error': 'Database not initialized'}

class GoogleFreeSearchTool(Tool):
    name: str = 'google_free_search'
    description: str = 'Search Google without requiring an API key and retrieve content from search results'
    inputs: Dict[str, Dict[str, str]] = {'query': {'type': 'string', 'description': 'The search query to execute on Google'}, 'num_search_pages': {'type': 'integer', 'description': 'Number of search results to retrieve. Default: 5'}, 'max_content_words': {'type': 'integer', 'description': 'Maximum number of words to include in content per result. None means no limit. Default: None'}}
    required: Optional[List[str]] = ['query']

    def __init__(self, search_google_free: SearchGoogleFree=None):
        super().__init__()
        self.search_google_free = search_google_free

    def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None) -> Dict[str, Any]:
        """Execute Google free search using the SearchGoogleFree instance."""
        if not self.search_google_free:
            raise RuntimeError('Google free search instance not initialized')
        try:
            return self.search_google_free.search(query, num_search_pages, max_content_words)
        except Exception as e:
            return {'results': [], 'error': f'Error executing Google free search: {str(e)}'}

def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None) -> Dict[str, Any]:
    """Execute Google free search using the SearchGoogleFree instance."""
    if not self.search_google_free:
        raise RuntimeError('Google free search instance not initialized')
    try:
        return self.search_google_free.search(query, num_search_pages, max_content_words)
    except Exception as e:
        return {'results': [], 'error': f'Error executing Google free search: {str(e)}'}

class DatabaseBase(ABC):
    """
    Abstract base class for database operations.
    Provides a common interface for different database types.
    """

    def __init__(self, connection_string: str=None, database_name: str=None, **kwargs):
        """
        Initialize the database base.
        
        Args:
            connection_string: Database connection string
            database_name: Name of the database to use
            **kwargs: Additional connection parameters
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.connection_params = kwargs
        self.db_type = self._get_database_type()
        self.connection = None
        self._is_initialized = False
        if connection_string:
            self.connect()

    @abstractmethod
    def _get_database_type(self) -> DatabaseType:
        """Return the database type"""
        pass

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to the database.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the database connection is working.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        pass

    @abstractmethod
    def execute_query(self, query: Union[str, Dict, List], query_type: QueryType=None, **kwargs) -> Dict[str, Any]:
        """
        Execute a query on the database.
        
        Args:
            query: The query to execute (string for SQL, dict/list for NoSQL)
            query_type: Type of query being executed
            **kwargs: Additional query parameters
            
        Returns:
            Dict containing query results and metadata
        """
        pass

    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database.
        
        Returns:
            Dict containing database information
        """
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        """
        List all collections/tables in the database.
        
        Returns:
            List of collection/table names
        """
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a specific collection/table.
        
        Args:
            collection_name: Name of the collection/table
            
        Returns:
            Dict containing collection/table information
        """
        pass

    @abstractmethod
    def get_schema(self, collection_name: str=None) -> Dict[str, Any]:
        """
        Get the schema/structure of the database or a specific collection.
        
        Args:
            collection_name: Name of the collection/table (optional)
            
        Returns:
            Dict containing schema information
        """
        pass

    def validate_query(self, query: Union[str, Dict, List]) -> Dict[str, Any]:
        """
        Validate a query before execution.
        
        Args:
            query: The query to validate
            
        Returns:
            Dict containing validation results
        """
        try:
            if isinstance(query, str):
                if not query.strip():
                    return {'valid': False, 'error': 'Query cannot be empty'}
            elif isinstance(query, (dict, list)):
                if not query:
                    return {'valid': False, 'error': 'Query cannot be empty'}
            else:
                return {'valid': False, 'error': f'Unsupported query type: {type(query)}'}
            return {'valid': True, 'error': None}
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def format_query_result(self, data: Any, query_type: QueryType, execution_time: float=None, **kwargs) -> Dict[str, Any]:
        """
        Format query results into a standard structure.
        
        Args:
            data: Raw query results
            query_type: Type of query that was executed
            execution_time: Time taken to execute the query
            **kwargs: Additional metadata
            
        Returns:
            Dict containing formatted results
        """
        return {'success': True, 'data': data, 'query_type': query_type.value if query_type else None, 'execution_time': execution_time, 'row_count': len(data) if isinstance(data, (list, tuple)) else 1, 'metadata': kwargs}

    def format_error_result(self, error: str, query_type: QueryType=None, **kwargs) -> Dict[str, Any]:
        """
        Format error results into a standard structure.
        
        Args:
            error: Error message
            query_type: Type of query that failed
            **kwargs: Additional error metadata
            
        Returns:
            Dict containing formatted error results
        """
        return {'success': False, 'error': error, 'query_type': query_type.value if query_type else None, 'data': None, 'execution_time': None, 'row_count': 0, 'metadata': kwargs}

    def get_supported_query_types(self) -> List[QueryType]:
        """
        Get list of supported query types for this database.
        
        Returns:
            List of supported QueryType enums
        """
        return [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.CREATE, QueryType.DROP]

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get database capabilities and features.
        
        Returns:
            Dict containing database capabilities
        """
        return {'database_type': self.db_type.value, 'supports_sql': False, 'supports_aggregation': False, 'supports_full_text_search': False, 'supports_vector_search': False, 'supports_transactions': False, 'supports_indexing': True, 'supported_query_types': [qt.value for qt in self.get_supported_query_types()], 'connection_info': {'is_connected': self.connection is not None, 'database_name': self.database_name}}

    def __enter__(self):
        """Context manager entry"""
        if not self.connection:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.disconnect()
        except Exception:
            pass

def __init__(self, connection_string: str=None, database_name: str=None, **kwargs):
    """
        Initialize the database base.
        
        Args:
            connection_string: Database connection string
            database_name: Name of the database to use
            **kwargs: Additional connection parameters
        """
    self.connection_string = connection_string
    self.database_name = database_name
    self.connection_params = kwargs
    self.db_type = self._get_database_type()
    self.connection = None
    self._is_initialized = False
    if connection_string:
        self.connect()

def __enter__(self):
    """Context manager entry"""
    if not self.connection:
        self.connect()
    return self

class BrowserBase(BaseModule):
    """
    A tool for interacting with web browsers using Selenium.
    Allows agents to navigate to URLs, interact with elements, extract information,
    and more from web pages.
    
    Key Features:
    - Auto-initialization: Browser is automatically initialized when any method is first called
    - Auto-cleanup: Browser is automatically closed when the instance is destroyed
    - No manual initialization or cleanup required
    """
    timeout: int = Field(default=10, description='Default timeout in seconds for browser operations')
    browser_type: str = Field(default='chrome', description="Type of browser to use ('chrome', 'firefox', 'safari', 'edge')")
    headless: bool = Field(default=False, description='Whether to run the browser in headless mode')
    user_data_dir: Optional[str] = Field(default=None, description='User data directory for persistent browser sessions')

    def __init__(self, name: str='Browser Tool', browser_type: str='chrome', headless: bool=False, timeout: int=10, **kwargs):
        """
        Initialize the browser tool with Selenium WebDriver.
        
        Args:
            name (str): Name of the tool
            browser_type (str): Type of browser to use ('chrome', 'firefox', 'safari', 'edge')
            headless (bool): Whether to run the browser in headless mode
            timeout (int): Default timeout in seconds for browser operations
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(name=name, timeout=timeout, browser_type=browser_type, headless=headless, **kwargs)
        self.driver = None
        self.element_references = {}

    def _check_driver_initialized(self) -> Union[None, Dict[str, Any]]:
        """
        Check if the browser driver is initialized. If not, initialize it automatically.
        
        Returns:
            Union[None, Dict[str, Any]]: None if driver is initialized, error response if initialization fails
        """
        if not self.driver:
            init_result = self.initialize_browser()
            if init_result['status'] == 'error':
                return init_result
        return None

    def _get_selector_by_type(self, selector_type: str) -> Union[str, Dict[str, Any]]:
        """
        Get the Selenium By selector for the given selector type.
        
        Args:
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            
        Returns:
            Union[str, Dict[str, Any]]: The By selector or error response
        """
        by_type = SELECTOR_MAP.get(selector_type.lower())
        if not by_type:
            return {'status': 'error', 'message': f'Invalid selector type: {selector_type}'}
        return by_type

    def _wait_for_page_load(self, timeout: Optional[int]=None) -> bool:
        """
        Wait for the page to load completely.
        
        Args:
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            bool: True if page loaded, False if timed out
        """
        timeout = timeout or self.timeout
        try:
            WebDriverWait(self.driver, timeout).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            return True
        except TimeoutException:
            return False

    def _parse_element_reference(self, ref: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse an element reference into selector type and selector.
        
        Args:
            ref (str): Element reference ID from the page snapshot
            
        Returns:
            Tuple[Optional[str], Optional[str], Optional[str]]: 
                (selector_type, selector, error_message) - error_message is None if successful
        """
        if not self.element_references:
            return (None, None, 'No page snapshot available. Use browser_snapshot or navigate_to_url first.')
        stored_ref = self.element_references.get(ref)
        if not stored_ref:
            return (None, None, f"Element reference '{ref}' not found. Use browser_snapshot or navigate_to_url first.")
        if ':' in stored_ref:
            ref_parts = stored_ref.split(':', 1)
            if len(ref_parts) != 2:
                return (None, None, f'Invalid stored reference format: {stored_ref}')
            selector_type, selector = ref_parts
            return (selector_type, selector, None)
        return (None, None, f'Invalid stored reference format: {stored_ref}')

    def _find_element_with_wait(self, by_type: str, selector: str, timeout: Optional[int]=None, wait_condition=EC.presence_of_element_located) -> Tuple[Optional[Any], Optional[str]]:
        """
        Find an element on the page with wait condition.
        
        Args:
            by_type (str): Selenium By selector type
            selector (str): The selector string
            timeout (int, optional): Custom timeout for this operation
            wait_condition: The EC condition to wait for
            
        Returns:
            Tuple[Optional[Any], Optional[str]]: (element, error_message) - error_message is None if successful
        """
        timeout = timeout or self.timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(wait_condition((by_type, selector)))
            return (element, None)
        except TimeoutException:
            return (None, f'Element not found or condition not met with selector: {selector}')
        except Exception as e:
            logger.error(f'Error finding element {selector}: {str(e)}')
            return (None, str(e))

    def _handle_function_params(self, function_params: Optional[list], function_name: str, param_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract parameters from nested function_params format.
        
        Args:
            function_params (list, optional): Nested function parameters
            function_name (str): The function name to look for
            param_mapping (Dict[str, str]): Mapping of parameter names
            
        Returns:
            Dict[str, Any]: Extracted parameters
        """
        result = {}
        if not function_params:
            return result
        for param in function_params:
            fn_name = param.get('function_name', '')
            if fn_name == function_name or fn_name in param_mapping.get('alt_names', []):
                args = param.get('function_args', {})
                for param_name, result_name in param_mapping.items():
                    if param_name == 'alt_names':
                        continue
                    if param_name in args:
                        result[result_name] = args[param_name]
                break
        return result

    def initialize_browser(self, function_params: list=None) -> Dict[str, Any]:
        """
        Start or restart a browser session. This method is called automatically when needed.
        
        Note: This method is now called automatically by other browser methods when the browser
        is not initialized. Manual initialization is no longer required.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "initialize_browser", "function_args": {}}]
           
        Args:
            function_params (list, optional): Nested function parameters
        
        Returns:
            Dict[str, Any]: Status information about the browser initialization
        """
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning(f'Error closing existing browser session: {str(e)}')
            options = None
            if self.browser_type == 'chrome':
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-gpu-sandbox')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                if self.user_data_dir:
                    options.add_argument(f'--user-data-dir={self.user_data_dir}')
                    logger.info(f'Using user data directory: {self.user_data_dir}')
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            elif self.browser_type == 'firefox':
                from selenium.webdriver.firefox.options import Options
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                self.driver = webdriver.Firefox(options=options)
            elif self.browser_type == 'safari':
                self.driver = webdriver.Safari()
            elif self.browser_type == 'edge':
                from selenium.webdriver.edge.options import Options
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-gpu-sandbox')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                if self.user_data_dir:
                    options.add_argument(f'--user-data-dir={self.user_data_dir}')
                    logger.info(f'Using user data directory: {self.user_data_dir}')
                self.driver = webdriver.Edge(options=options)
            else:
                return {'status': 'error', 'message': f'Unsupported browser type: {self.browser_type}'}
            self.driver.set_page_load_timeout(self.timeout)
            return {'status': 'success', 'message': f'Browser {self.browser_type} initialized successfully'}
        except Exception as e:
            logger.error(f'Error initializing browser: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def navigate_to_url(self, url: str=None, timeout: int=None, function_params: list=None) -> Dict[str, Any]:
        """
        Navigate to a URL and capture a snapshot of the page. This provides element references used for interaction.
        
        This function supports multiple parameter styles:
        1. Standard style: url parameter
        2. Nested function_params style:
           function_params=[{"function_name": "navigate_to_url", "function_args": {"url": "..."}}]
        
        Args:
            url (str, optional): The complete URL (with https://) to navigate to
            timeout (int, optional): Custom timeout in seconds (default: 10)
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Information about the navigation result and page snapshot
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        if function_params and (not url):
            params = self._handle_function_params(function_params, 'navigate_to_url', {'url': 'url', 'timeout': 'timeout', 'alt_names': ['browser_navigate']})
            url = params.get('url')
            timeout = params.get('timeout', timeout)
        if not url:
            return {'status': 'error', 'message': 'URL parameter is required'}
        timeout = timeout or self.timeout
        try:
            self.driver.get(url)
            page_loaded = self._wait_for_page_load(timeout)
            if not page_loaded:
                logger.warning(f'Page load timeout for URL: {url}, but continuing with snapshot')
            snapshot_result = self.browser_snapshot()
            if snapshot_result['status'] == 'success':
                return {'status': 'success', 'url': url, 'title': self.driver.title, 'current_url': self.driver.current_url, 'snapshot': {'interactive_elements': snapshot_result.get('interactive_elements', [])}}
            else:
                return {'status': 'partial_success', 'url': url, 'title': self.driver.title, 'current_url': self.driver.current_url, 'snapshot_error': snapshot_result.get('message', 'Unknown error capturing snapshot')}
        except TimeoutException:
            return {'status': 'timeout', 'message': f'Timed out loading URL: {url}'}
        except Exception as e:
            logger.error(f'Error navigating to URL {url}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def find_element(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
        """
        Find an element on the current page and return information about it.
        
        Args:
            selector (str): The selector to find the element
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Information about the found element
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        timeout = timeout or self.timeout
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            element, error = self._find_element_with_wait(by_type, selector, timeout, EC.presence_of_element_located)
            if error:
                return {'status': 'not_found', 'message': f'Element not found with {selector_type}: {selector}'}
            element_properties = self._extract_element_properties(element, selector)
            return {'status': 'success', 'element': element_properties}
        except Exception as e:
            logger.error(f'Error finding element {selector}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def _extract_element_properties(self, element, selector: str) -> Dict[str, Any]:
        """
        Extract common properties from a WebElement.
        
        Args:
            element: The Selenium WebElement
            selector (str): The selector used to find the element (for error messages)
            
        Returns:
            Dict[str, Any]: Element properties
        """
        element_properties = {'text': element.text, 'tag_name': element.tag_name, 'is_displayed': element.is_displayed(), 'is_enabled': element.is_enabled()}
        for attr in ['href', 'id', 'class']:
            try:
                value = element.get_attribute(attr)
                if value:
                    element_properties[attr] = value
            except StaleElementReferenceException:
                logger.warning(f'Element became stale when trying to get {attr} attribute for {selector}')
            except Exception as e:
                logger.warning(f'Could not get {attr} attribute for {selector}: {str(e)}')
        return element_properties

    def find_multiple_elements(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
        """
        Find multiple elements on the current page and return information about them.
        
        Args:
            selector (str): The selector to find the elements
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Information about the found elements
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        timeout = timeout or self.timeout
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            element, error = self._find_element_with_wait(by_type, selector, timeout, EC.presence_of_element_located)
            if error:
                return {'status': 'not_found', 'message': f'No elements found with {selector_type}: {selector}'}
            elements = self.driver.find_elements(by_type, selector)
            elements_properties = []
            for idx, element in enumerate(elements):
                try:
                    element_properties = self._extract_element_properties(element, f'{selector}[{idx}]')
                    element_properties['index'] = idx
                    elements_properties.append(element_properties)
                except StaleElementReferenceException:
                    logger.warning(f'Element {idx} became stale while extracting properties')
                except Exception as e:
                    logger.warning(f'Error extracting properties for element {idx}: {str(e)}')
            return {'status': 'success', 'count': len(elements_properties), 'elements': elements_properties}
        except Exception as e:
            logger.error(f'Error finding elements {selector}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def click_element(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
        """
        Click on an element on the current page.
        
        Args:
            selector (str): The selector to find the element
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Result of the click operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        timeout = timeout or self.timeout
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            element, error = self._find_element_with_wait(by_type, selector, timeout, EC.element_to_be_clickable)
            if error:
                return {'status': 'not_found', 'message': f'Element not clickable with {selector_type}: {selector}'}
            element.click()
            page_loaded = self._wait_for_page_load(timeout)
            if not page_loaded:
                return {'status': 'partial_success', 'message': 'Element clicked, but page load timed out', 'selector': selector, 'current_url': self.driver.current_url}
            return {'status': 'success', 'message': f'Clicked element with {selector_type}: {selector}', 'current_url': self.driver.current_url, 'title': self.driver.title}
        except Exception as e:
            logger.error(f'Error clicking element {selector}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def input_text(self, element: str=None, ref: str=None, text: str=None, submit: bool=False, slowly: bool=True, function_params: list=None) -> Dict[str, Any]:
        """
        Type text into a form field, search box, or other input element using a reference ID from a snapshot.
        
        This function only works with element references from a snapshot. Use browser_snapshot
        or navigate_to_url first to capture the page elements.
        
        This function supports multiple parameter styles:
        1. Standard style: element (description), ref (element ID), text
        2. Nested function_params style:
           function_params=[{"function_name": "browser_type", "function_args": {...}}]
        
        Args:
            element (str, optional): Human-readable description of the element (e.g., 'Search field', 'Username input')
            ref (str, optional): Element ID from the page snapshot (e.g., 'e0', 'e1', 'e2') - NOT a CSS selector
            text (str, optional): Text to input into the element
            submit (bool): Press Enter after typing to submit forms (default: false)
            slowly (bool): Type one character at a time to trigger JS events (default: true)
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Result of the text input operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        if function_params:
            params = self._handle_function_params(function_params, 'input_text', {'element': 'element', 'ref': 'ref', 'text': 'text', 'submit': 'submit', 'slowly': 'slowly', 'alt_names': ['browser_type']})
            element = params.get('element', element)
            ref = params.get('ref', ref)
            text = params.get('text', text)
            if 'submit' in params:
                submit = params['submit']
            if 'slowly' in params:
                slowly = params['slowly']
        if not ref or not text:
            return {'status': 'error', 'message': 'Both ref and text parameters are required'}
        selector_type, selector, error = self._parse_element_reference(ref)
        if error:
            return {'status': 'error', 'message': error}
        element_desc = element or ref
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            web_element, error = self._find_element_with_wait(by_type, selector, self.timeout, EC.element_to_be_clickable)
            if error:
                return {'status': 'not_found', 'message': f'Element not found: {element_desc}'}
            web_element.clear()
            if slowly:
                for char in text:
                    web_element.send_keys(char)
                    time.sleep(0.05)
            else:
                web_element.send_keys(text)
            if submit:
                from selenium.webdriver.common.keys import Keys
                web_element.send_keys(Keys.ENTER)
                page_loaded = self._wait_for_page_load(self.timeout)
                if not page_loaded:
                    self.browser_snapshot()
                    return {'status': 'partial_success', 'message': 'Text entered and submitted, but page load timed out', 'element': element_desc, 'text': text}
                snapshot_result = self.browser_snapshot()
                if snapshot_result['status'] != 'success':
                    logger.warning(f'Failed to capture snapshot after form submission: {snapshot_result.get('message')}')
            return {'status': 'success', 'message': f'Successfully input text into {element_desc}' + (' and submitted' if submit else ''), 'element': element_desc, 'text': text}
        except TimeoutException:
            return {'status': 'not_found', 'message': f'Element not found: {element_desc}'}
        except Exception as e:
            logger.error(f'Error inputting text to element {element_desc}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def get_page_content(self) -> Dict[str, Any]:
        """
        Get the current page title, URL and body content.
        
        Returns:
            Dict[str, Any]: Information about the current page
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            title = self.driver.title
            current_url = self.driver.current_url
            body_content = self.driver.execute_script('\n                var body = document.body;\n                return body ? body.outerHTML : "";\n            ')
            element_summary = self.driver.execute_script('\n                // Get common interactive elements\n                var summary = {\n                    links: [],\n                    buttons: [],\n                    inputs: [],\n                    forms: []\n                };\n                \n                // Get links\n                var links = document.querySelectorAll(\'a\');\n                for (var i = 0; i < Math.min(links.length, 20); i++) {\n                    var link = links[i];\n                    summary.links.push({\n                        text: link.textContent.trim().substring(0, 50),\n                        href: link.getAttribute(\'href\'),\n                        id: link.id,\n                        class: link.className\n                    });\n                }\n                \n                // Get buttons\n                var buttons = document.querySelectorAll(\'button, input[type="button"], input[type="submit"]\');\n                for (var i = 0; i < Math.min(buttons.length, 20); i++) {\n                    var button = buttons[i];\n                    summary.buttons.push({\n                        text: button.textContent ? button.textContent.trim().substring(0, 50) : button.value,\n                        id: button.id,\n                        class: button.className,\n                        type: button.type\n                    });\n                }\n                \n                // Get inputs\n                var inputs = document.querySelectorAll(\'input:not([type="button"]):not([type="submit"]), textarea, select\');\n                for (var i = 0; i < Math.min(inputs.length, 20); i++) {\n                    var input = inputs[i];\n                    summary.inputs.push({\n                        type: input.type,\n                        name: input.name,\n                        id: input.id,\n                        placeholder: input.placeholder\n                    });\n                }\n                \n                // Get forms\n                var forms = document.querySelectorAll(\'form\');\n                for (var i = 0; i < Math.min(forms.length, 10); i++) {\n                    var form = forms[i];\n                    summary.forms.push({\n                        id: form.id,\n                        action: form.action,\n                        method: form.method\n                    });\n                }\n                \n                return summary;\n            ')
            return {'status': 'success', 'title': title, 'url': current_url, 'body_content': body_content, 'element_summary': element_summary}
        except Exception as e:
            logger.error(f'Error getting page content: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def switch_to_frame(self, frame_reference: str, reference_type: str='index') -> Dict[str, Any]:
        """
        Switch to a frame on the page.
        
        Args:
            frame_reference (str): Reference to the frame (index, name, or ID)
            reference_type (str): Type of reference ('index', 'name', 'id', 'element')
            
        Returns:
            Dict[str, Any]: Result of the frame switch operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            if reference_type == 'index':
                try:
                    index = int(frame_reference)
                    self.driver.switch_to.frame(index)
                except ValueError:
                    return {'status': 'error', 'message': f'Invalid frame index: {frame_reference}'}
            elif reference_type == 'name' or reference_type == 'id':
                self.driver.switch_to.frame(frame_reference)
            elif reference_type == 'element':
                selector_parts = frame_reference.split(':', 1)
                if len(selector_parts) != 2:
                    return {'status': 'error', 'message': "Element reference must be in format 'selector_type:selector'"}
                selector_type, selector = selector_parts
                element_result = self.find_element(selector, selector_type)
                if element_result['status'] != 'success':
                    return {'status': 'error', 'message': f'Could not find frame element: {element_result['message']}'}
                selector_map = {'css': By.CSS_SELECTOR, 'xpath': By.XPATH, 'id': By.ID, 'class': By.CLASS_NAME, 'name': By.NAME, 'tag': By.TAG_NAME}
                by_type = selector_map.get(selector_type.lower())
                element = self.driver.find_element(by_type, selector)
                self.driver.switch_to.frame(element)
            else:
                return {'status': 'error', 'message': f'Invalid reference type: {reference_type}'}
            return {'status': 'success', 'message': f'Switched to frame using {reference_type}: {frame_reference}'}
        except Exception as e:
            logger.error(f'Error switching to frame {frame_reference}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def switch_to_window(self, window_reference: str, reference_type: str='index') -> Dict[str, Any]:
        """
        Switch to a window or tab.
        
        Args:
            window_reference (str): Reference to the window (index, handle, or title)
            reference_type (str): Type of reference ('index', 'handle', 'title')
            
        Returns:
            Dict[str, Any]: Result of the window switch operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            window_handles = self.driver.window_handles
            if not window_handles:
                return {'status': 'error', 'message': 'No window handles available'}
            if reference_type == 'index':
                try:
                    index = int(window_reference)
                    if index < 0 or index >= len(window_handles):
                        return {'status': 'error', 'message': f'Window index out of range: {index}'}
                    self.driver.switch_to.window(window_handles[index])
                except ValueError:
                    return {'status': 'error', 'message': f'Invalid window index: {window_reference}'}
            elif reference_type == 'handle':
                if window_reference not in window_handles:
                    return {'status': 'error', 'message': f'Window handle not found: {window_reference}'}
                self.driver.switch_to.window(window_reference)
            elif reference_type == 'title':
                current_handle = self.driver.current_window_handle
                window_found = False
                for handle in window_handles:
                    try:
                        self.driver.switch_to.window(handle)
                        if self.driver.title == window_reference:
                            window_found = True
                            break
                    except Exception:
                        pass
                if not window_found:
                    self.driver.switch_to.window(current_handle)
                    return {'status': 'error', 'message': f"No window with title '{window_reference}' found"}
            else:
                return {'status': 'error', 'message': f'Invalid reference type: {reference_type}'}
            return {'status': 'success', 'message': f'Switched to window using {reference_type}: {window_reference}', 'title': self.driver.title, 'url': self.driver.current_url}
        except Exception as e:
            logger.error(f'Error switching to window {window_reference}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def select_dropdown_option(self, select_selector: str, option_value: str, select_by: str='value', selector_type: str='css') -> Dict[str, Any]:
        """
        Select an option from a dropdown
        select_by can be 'value', 'text', or 'index'
        
        Args:
            select_selector (str): The selector to find the dropdown element
            option_value (str): The value to select (depends on select_by)
            select_by (str): Method to select by ('value', 'text', 'index')
            selector_type (str): Type of selector for the dropdown
            
        Returns:
            Dict[str, Any]: Result of the selection operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            from selenium.webdriver.support.ui import Select
            by_type = self._get_selector_by_type(selector_type)
            if isinstance(by_type, dict):
                return by_type
            element, error = self._find_element_with_wait(by_type, select_selector, self.timeout, EC.presence_of_element_located)
            if error:
                return {'status': 'not_found', 'message': f'Dropdown element not found with {selector_type}: {select_selector}'}
            select = Select(element)
            if select_by.lower() == 'value':
                select.select_by_value(option_value)
            elif select_by.lower() == 'text':
                select.select_by_visible_text(option_value)
            elif select_by.lower() == 'index':
                try:
                    select.select_by_index(int(option_value))
                except ValueError:
                    return {'status': 'error', 'message': f'Invalid index value: {option_value}. Must be an integer.'}
            else:
                return {'status': 'error', 'message': f'Invalid select_by option: {select_by}'}
            return {'status': 'success', 'message': f'Selected option with {select_by}: {option_value}'}
        except Exception as e:
            logger.error(f'Error selecting dropdown option: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def close_browser(self) -> Dict[str, Any]:
        """
        Close the browser and end the session. Call this when you're done to free resources.
        
        Returns:
            Dict[str, Any]: Status of the browser closure
        """
        if not self.driver:
            return {'status': 'success', 'message': 'Browser already closed'}
        try:
            self.driver.quit()
            self.driver = None
            return {'status': 'success', 'message': 'Browser closed successfully'}
        except Exception as e:
            logger.error(f'Error closing browser: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def browser_click(self, element: str=None, ref: str=None, function_params: list=None) -> Dict[str, Any]:
        """
        Click on a button, link, or other clickable element using a reference ID from a snapshot.
        
        This function only works with element references from a snapshot. You MUST call browser_snapshot
        or navigate_to_url first to capture the page elements.
        
        Common usage pattern:
        1. First get a snapshot: browser_snapshot() or navigate_to_url()
        2. Find the element reference (e.g. 'e0', 'e1') from the snapshot's interactive_elements
        3. Use that reference to click: browser_click(element='Login button', ref='e0')
        
        This function supports multiple parameter styles:
        1. Standard style: element (description), ref (element ID)
        2. Nested function_params style:
           function_params=[{"function_name": "browser_click", "function_args": {...}}]
        
        Args:
            element (str, optional): Human-readable description of what you're clicking (e.g., 'Login button', 'Next page link')
            ref (str, optional): Element ID from the page snapshot (e.g., 'e0', 'e1', 'e2') - NOT a CSS selector
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Result of the click operation with detailed feedback
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        if function_params and (not ref):
            params = self._handle_function_params(function_params, 'browser_click', {'element': 'element', 'ref': 'ref'})
            element = params.get('element', element)
            ref = params.get('ref', ref)
        if not ref:
            return {'status': 'error', 'message': 'Element reference (ref) parameter is required. You must first call browser_snapshot() or navigate_to_url() to get element references.', 'required_steps': ['1. Call browser_snapshot() or navigate_to_url() to get page elements', "2. Find the element reference (e.g. 'e0') in the response's interactive_elements", "3. Use that reference to click: browser_click(element='Button name', ref='e0')"]}
        if not self.element_references:
            return {'status': 'error', 'message': 'No element references found. You must first capture a page snapshot.', 'required_steps': ['1. Call browser_snapshot() or navigate_to_url() to capture the page state', '2. Use the element references returned in the snapshot']}
        selector_type, selector, error = self._parse_element_reference(ref)
        if error:
            return {'status': 'error', 'message': error, 'help': "Make sure you're using a valid element reference from a recent snapshot"}
        element_desc = element or ref
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            try:
                element_exists = self.driver.find_element(by_type, selector)
            except Exception:
                return {'status': 'not_found', 'message': f'Element not found: {element_desc}', 'suggestion': 'The page may have changed. Try getting a new snapshot with browser_snapshot()'}
            web_element, error = self._find_element_with_wait(by_type, selector, self.timeout, EC.element_to_be_clickable)
            if error:
                try:
                    is_visible = element_exists.is_displayed()
                    is_enabled = element_exists.is_enabled()
                    element_tag = element_exists.tag_name
                    element_classes = element_exists.get_attribute('class')
                    return {'status': 'not_clickable', 'message': f'Element found but not clickable: {element_desc}', 'element_state': {'visible': is_visible, 'enabled': is_enabled, 'tag': element_tag, 'classes': element_classes}, 'suggestion': 'The element might be disabled, hidden, or covered by another element'}
                except Exception:
                    return {'status': 'not_clickable', 'message': f'Element found but not clickable: {element_desc}', 'suggestion': 'The element might be disabled, hidden, or covered by another element'}
            web_element.click()
            page_loaded = self._wait_for_page_load(self.timeout)
            if not page_loaded:
                snapshot_result = self.browser_snapshot()
                return {'status': 'partial_success', 'message': 'Element clicked, but page load timed out', 'element': element_desc, 'current_url': self.driver.current_url, 'snapshot': snapshot_result if snapshot_result['status'] == 'success' else None, 'suggestion': 'The page might still be loading. You may want to wait and take another snapshot.'}
            snapshot_result = self.browser_snapshot()
            if snapshot_result['status'] == 'success':
                return {'status': 'success', 'message': f'Successfully clicked on {element_desc}', 'element': element_desc, 'current_url': self.driver.current_url, 'title': self.driver.title, 'snapshot': {'interactive_elements': snapshot_result.get('interactive_elements', [])}}
            else:
                return {'status': 'success', 'message': f'Successfully clicked on {element_desc} but snapshot failed', 'element': element_desc, 'current_url': self.driver.current_url, 'title': self.driver.title, 'snapshot_error': snapshot_result.get('message', 'Unknown error capturing snapshot'), 'suggestion': 'You may want to take another snapshot with browser_snapshot()'}
        except TimeoutException:
            return {'status': 'timeout', 'message': f'Timed out waiting for element to be clickable: {element_desc}', 'suggestion': 'The element might be taking too long to load or become clickable'}
        except Exception as e:
            logger.error(f'Error clicking element: {str(e)}')
            return {'status': 'error', 'message': str(e), 'element': element_desc, 'suggestion': 'Try getting a new snapshot of the page with browser_snapshot()'}

    def _classify_element_interactivity(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify an element's interactivity based on its properties.
        This method contains all rules for determining if an element is interactive or editable.
        
        Args:
            element_data (Dict[str, Any]): Element data including properties, attributes, etc.
            
        Returns:
            Dict[str, Any]: Element data with interactivity classifications added
        """
        element_data['interactable'] = False
        element_data['editable'] = False
        tag_name = element_data.get('properties', {}).get('tag', '').upper()
        role = element_data.get('attributes', {}).get('role', '').lower()
        is_disabled = element_data.get('attributes', {}).get('disabled') is not None or element_data.get('attributes', {}).get('aria-disabled') == 'true' or element_data.get('attributes', {}).get('aria-hidden') == 'true'
        is_visible = element_data.get('visible', True)
        if not is_disabled and is_visible:
            interactive_tags = {'A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'DETAILS', 'AUDIO', 'VIDEO', 'IFRAME', 'EMBED', 'OBJECT', 'SUMMARY', 'MENU'}
            interactive_roles = {'button', 'link', 'checkbox', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'option', 'radio', 'searchbox', 'slider', 'spinbutton', 'switch', 'tab', 'textbox', 'combobox', 'listbox', 'menu', 'menubar', 'radiogroup', 'tablist', 'toolbar', 'tree', 'treegrid'}
            has_interactive_attrs = any([element_data.get('attributes', {}).get(attr) is not None for attr in ['onclick', 'onkeydown', 'onkeyup', 'onmousedown', 'onmouseup', 'tabindex']])
            element_data['interactable'] = tag_name in interactive_tags or role in interactive_roles or has_interactive_attrs
            editable_input_types = {'text', 'search', 'email', 'number', 'tel', 'url', 'password'}
            editable_roles = {'textbox', 'searchbox', 'spinbutton'}
            element_data['editable'] = tag_name == 'INPUT' and element_data.get('attributes', {}).get('type', 'text').lower() in editable_input_types or tag_name == 'TEXTAREA' or element_data.get('attributes', {}).get('contenteditable') == 'true' or (role in editable_roles)
        return element_data

    def _process_accessibility_tree(self, accessibility_tree):
        """
        Process the accessibility tree to extract all elements and store their references.
        
        This method processes all elements in the page structure, assigns unique IDs,
        and stores their selectors for later interaction.
        
        Args:
            accessibility_tree (dict): The accessibility tree from JavaScript
            
        Returns:
            list: A list of all elements with their IDs and properties
        """
        all_elements = []

        def extract_elements(node, path='', index=0):
            if not node:
                return index
            current_path = path + '/' + (node.get('name') or node.get('role') or 'element')
            element_id = f'e{index}'
            element_info = {'id': element_id, 'description': current_path.strip('/'), 'purpose': node.get('semantic_info', {}).get('purpose', ''), 'label': node.get('semantic_info', {}).get('label', ''), 'category': node.get('semantic_info', {}).get('category', ''), 'isPrimary': node.get('semantic_info', {}).get('isPrimary', False), 'visible': node.get('visible', True), 'properties': node.get('properties', {}), 'attributes': node.get('attributes', {})}
            if 'all_refs' in node:
                self.element_references[element_id] = node['all_refs'][0]
            element_info = self._classify_element_interactivity(element_info)
            all_elements.append(element_info)
            index += 1
            for child in node.get('children', []):
                index = extract_elements(child, current_path, index)
            return index
        extract_elements(accessibility_tree)
        return all_elements

    def browser_snapshot(self, function_params: list=None) -> Dict[str, Any]:
        """
        Capture a fresh snapshot of the current page with all interactive elements. 
        Use after page state changes not caused by navigation or clicking.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "browser_snapshot", "function_args": {}}]
        
        Args:
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: The accessibility snapshot of the page with interactive elements
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            title = self.driver.title
            current_url = self.driver.current_url
            accessibility_tree = self.driver.execute_script("\n                function getAccessibilityTree(node, depth = 0, maxDepth = 10) {\n                    if (!node || depth > maxDepth) return null;\n                    \n                    let result = {\n                        role: node.role || node.tagName,\n                        name: node.name || '',\n                        type: node.type || '',\n                        value: node.value || '',\n                        description: node.description || '',\n                        properties: {},\n                        visible: isElementVisible(node)\n                    };\n                    \n                    // Helper function for element visibility\n                    function isElementVisible(element) {\n                        if (!element.getBoundingClientRect) return true;\n                        const style = window.getComputedStyle(element);\n                        const rect = element.getBoundingClientRect();\n                        \n                        // Check basic visibility\n                        const isVisible = style.display !== 'none' && \n                                        style.visibility !== 'hidden' && \n                                        style.opacity !== '0' &&\n                                        rect.width > 0 && \n                                        rect.height > 0;\n                                        \n                        // Check if element is in viewport\n                        const isInViewport = rect.top >= 0 &&\n                                           rect.left >= 0 &&\n                                           rect.bottom <= window.innerHeight &&\n                                           rect.right <= window.innerWidth;\n                                           \n                        return isVisible && isInViewport;\n                    }\n                    \n                    // Add text content\n                    if (node.textContent) {\n                        result.text_content = node.textContent.trim();\n                    }\n\n                    // Add identifier properties for references\n                    if (node.id) result.properties.id = node.id;\n                    if (node.className) result.properties.class = node.className;\n                    if (node.tagName) result.properties.tag = node.tagName.toLowerCase();\n                    \n                    // Add attributes\n                    if (node.attributes) {\n                        result.attributes = {};\n                        for (let attr of node.attributes) {\n                            result.attributes[attr.name] = attr.value;\n                        }\n                    }\n\n                    // Add custom ref property that combines selector types\n                    let refs = [];\n                    // Store all possible selectors, but don't use them as primary ref\n                    if (node.id) refs.push(`id:${node.id}`);\n                    if (node.className && typeof node.className === 'string') \n                        refs.push(`class:${node.className}`);\n                    if (node.tagName) refs.push(`tag:${node.tagName.toLowerCase()}`);\n                    \n                    // For inputs, add name attribute\n                    if (node.getAttribute && node.getAttribute('name')) {\n                        result.properties.name = node.getAttribute('name');\n                        refs.push(`name:${node.getAttribute('name')}`);\n                    }\n                    \n                    // Create XPath and CSS selectors\n                    try {\n                        // CSS selector\n                        let cssPath = getCssPath(node);\n                        if (cssPath) refs.push(`css:${cssPath}`);\n                        \n                        // XPath\n                        let xpath = getXPath(node);\n                        if (xpath) refs.push(`xpath:${xpath}`);\n                    } catch (e) {}\n                    \n                    // Store all refs but don't set primary ref here\n                    if (refs.length > 0) {\n                        result.all_refs = refs;\n                    }\n\n                    // Add semantic information about the element\n                    result.semantic_info = {\n                        // What the element represents\n                        purpose: (function() {\n                            if (node.tagName === 'INPUT') {\n                                if (node.type === 'submit') return 'submit button';\n                                if (node.type === 'search') return 'search box';\n                                if (node.type === 'text') return 'text input';\n                                return `${node.type || 'text'} input`;\n                            }\n                            if (node.tagName === 'BUTTON') return 'button';\n                            if (node.tagName === 'A') return 'link';\n                            if (node.tagName === 'SELECT') return 'dropdown';\n                            if (node.tagName === 'TEXTAREA') return 'text area';\n                            if (node.getAttribute('role')) return node.getAttribute('role');\n                            return 'interactive element';\n                        })(),\n                        \n                        // The visible or accessible text\n                        label: (function() {\n                            return node.getAttribute('aria-label') ||\n                                   node.getAttribute('title') ||\n                                   node.getAttribute('placeholder') ||\n                                   node.getAttribute('alt') ||\n                                   (node.tagName === 'INPUT' ? node.value : node.textContent.trim());\n                        })(),\n                        \n                        // Is this a primary action?\n                        isPrimary: !!(\n                            node.classList.contains('primary') ||\n                            node.getAttribute('aria-label')?.toLowerCase().includes('search') ||\n                            node.getAttribute('title')?.toLowerCase().includes('search') ||\n                            node.type === 'search' ||\n                            node.getAttribute('role') === 'main' ||\n                            node.id?.toLowerCase().includes('main') ||\n                            node.classList.contains('main')\n                        ),\n                        \n                        // Basic category\n                        category: (function() {\n                            if (node.type === 'search' || \n                                node.getAttribute('role') === 'searchbox') return 'search';\n                            if (node.type === 'submit' || \n                                node.tagName === 'BUTTON' ||\n                                node.getAttribute('role') === 'button') return 'action';\n                            if (node.tagName === 'A' ||\n                                node.getAttribute('role') === 'link') return 'navigation';\n                            if (node.tagName === 'INPUT' || \n                                node.tagName === 'TEXTAREA' ||\n                                node.getAttribute('role') === 'textbox') return 'input';\n                            if (node.tagName === 'SELECT' ||\n                                ['listbox', 'combobox'].includes(node.getAttribute('role'))) return 'selection';\n                            return 'interactive';\n                        })()\n                    };\n                    \n                    // Process children\n                    result.children = [];\n                    if (node.children) {\n                        for (let i = 0; i < node.children.length; i++) {\n                            const childTree = getAccessibilityTree(node.children[i], depth + 1, maxDepth);\n                            if (childTree) {\n                                result.children.push(childTree);\n                            }\n                        }\n                    }\n                    \n                    return result;\n                }\n                \n                return getAccessibilityTree(document.body);\n            ")
            all_elements = self._process_accessibility_tree(accessibility_tree)
            page_content = html2text.html2text(self.driver.page_source)
            return {'status': 'success', 'title': title, 'url': current_url, 'accessibility_tree': accessibility_tree, 'page_content': page_content, 'interactive_elements': [e for e in all_elements if e.get('interactable') or e.get('editable')]}
        except Exception as e:
            logger.error(f'Error generating accessibility snapshot: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def browser_console_messages(self, function_params: list=None) -> Dict[str, Any]:
        """
        Retrieve JavaScript console messages (logs, warnings, errors) from the browser for debugging.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "browser_console_messages", "function_args": {}}]
        
        Args:
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: The console messages including logs, warnings and errors
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            logs = self._collect_browser_logs()
            return {'status': 'success', 'console_messages': logs}
        except Exception as e:
            logger.error(f'Error retrieving console messages: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def _collect_browser_logs(self) -> List[Dict[str, Any]]:
        """
        Collect logs from both the browser driver and JavaScript console.
        
        Returns:
            List[Dict[str, Any]]: Combined logs from both sources
        """
        logs = []
        try:
            browser_logs = self.driver.get_log('browser')
            for log in browser_logs:
                level = log.get('level', '').upper()
                if level == 'SEVERE':
                    level = 'ERROR'
                elif level == 'INFO':
                    level = 'LOG'
                logs.append({'level': level, 'message': log.get('message', ''), 'timestamp': log.get('timestamp', '')})
        except Exception as log_error:
            logs.append({'level': 'WARNING', 'message': f'Could not retrieve browser logs: {str(log_error)}', 'timestamp': ''})
        try:
            self.driver.execute_script("\n                if (!window._consoleLogs) {\n                    window._consoleLogs = [];\n                    \n                    // Store original console methods\n                    const originalConsole = {\n                        log: console.log,\n                        info: console.info,\n                        warn: console.warn,\n                        error: console.error,\n                        debug: console.debug\n                    };\n                    \n                    // Helper function to add message with proper level\n                    function addMessage(level, args) {\n                        window._consoleLogs.push({\n                            level: level.toUpperCase(),\n                            message: Array.from(args).join(' '),\n                            timestamp: new Date().toISOString()\n                        });\n                    }\n                    \n                    // Override console methods to capture logs\n                    console.log = function() {\n                        addMessage('LOG', arguments);\n                        originalConsole.log.apply(console, arguments);\n                    };\n                    \n                    console.info = function() {\n                        addMessage('INFO', arguments);\n                        originalConsole.info.apply(console, arguments);\n                    };\n                    \n                    console.warn = function() {\n                        addMessage('WARN', arguments);\n                        originalConsole.warn.apply(console, arguments);\n                    };\n                    \n                    console.error = function() {\n                        addMessage('ERROR', arguments);\n                        originalConsole.error.apply(console, arguments);\n                    };\n                    \n                    console.debug = function() {\n                        addMessage('DEBUG', arguments);\n                        originalConsole.debug.apply(console, arguments);\n                    };\n                }\n            ")
            time.sleep(2)
            js_logs = self.driver.execute_script('return window._consoleLogs || [];')
            for log in js_logs:
                if log not in logs:
                    logs.append(log)
        except Exception as js_error:
            logs.append({'level': 'WARNING', 'message': f'Could not retrieve JavaScript console logs: {str(js_error)}', 'timestamp': ''})
        return logs

    def __del__(self):
        """
        Destructor to automatically close the browser when the instance is destroyed.
        """
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                logger.info('Browser automatically closed on cleanup')
            except Exception as e:
                logger.warning(f'Error during automatic browser cleanup: {str(e)}')

def _wait_for_page_load(self, timeout: Optional[int]=None) -> bool:
    """
        Wait for the page to load completely.
        
        Args:
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            bool: True if page loaded, False if timed out
        """
    timeout = timeout or self.timeout
    try:
        WebDriverWait(self.driver, timeout).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        return True
    except TimeoutException:
        return False

def _find_element_with_wait(self, by_type: str, selector: str, timeout: Optional[int]=None, wait_condition=EC.presence_of_element_located) -> Tuple[Optional[Any], Optional[str]]:
    """
        Find an element on the page with wait condition.
        
        Args:
            by_type (str): Selenium By selector type
            selector (str): The selector string
            timeout (int, optional): Custom timeout for this operation
            wait_condition: The EC condition to wait for
            
        Returns:
            Tuple[Optional[Any], Optional[str]]: (element, error_message) - error_message is None if successful
        """
    timeout = timeout or self.timeout
    try:
        element = WebDriverWait(self.driver, timeout).until(wait_condition((by_type, selector)))
        return (element, None)
    except TimeoutException:
        return (None, f'Element not found or condition not met with selector: {selector}')
    except Exception as e:
        logger.error(f'Error finding element {selector}: {str(e)}')
        return (None, str(e))

def initialize_browser(self, function_params: list=None) -> Dict[str, Any]:
    """
        Start or restart a browser session. This method is called automatically when needed.
        
        Note: This method is now called automatically by other browser methods when the browser
        is not initialized. Manual initialization is no longer required.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "initialize_browser", "function_args": {}}]
           
        Args:
            function_params (list, optional): Nested function parameters
        
        Returns:
            Dict[str, Any]: Status information about the browser initialization
        """
    try:
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f'Error closing existing browser session: {str(e)}')
        options = None
        if self.browser_type == 'chrome':
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-gpu-sandbox')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            if self.user_data_dir:
                options.add_argument(f'--user-data-dir={self.user_data_dir}')
                logger.info(f'Using user data directory: {self.user_data_dir}')
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        elif self.browser_type == 'firefox':
            from selenium.webdriver.firefox.options import Options
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            self.driver = webdriver.Firefox(options=options)
        elif self.browser_type == 'safari':
            self.driver = webdriver.Safari()
        elif self.browser_type == 'edge':
            from selenium.webdriver.edge.options import Options
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-gpu-sandbox')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            if self.user_data_dir:
                options.add_argument(f'--user-data-dir={self.user_data_dir}')
                logger.info(f'Using user data directory: {self.user_data_dir}')
            self.driver = webdriver.Edge(options=options)
        else:
            return {'status': 'error', 'message': f'Unsupported browser type: {self.browser_type}'}
        self.driver.set_page_load_timeout(self.timeout)
        return {'status': 'success', 'message': f'Browser {self.browser_type} initialized successfully'}
    except Exception as e:
        logger.error(f'Error initializing browser: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def navigate_to_url(self, url: str=None, timeout: int=None, function_params: list=None) -> Dict[str, Any]:
    """
        Navigate to a URL and capture a snapshot of the page. This provides element references used for interaction.
        
        This function supports multiple parameter styles:
        1. Standard style: url parameter
        2. Nested function_params style:
           function_params=[{"function_name": "navigate_to_url", "function_args": {"url": "..."}}]
        
        Args:
            url (str, optional): The complete URL (with https://) to navigate to
            timeout (int, optional): Custom timeout in seconds (default: 10)
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Information about the navigation result and page snapshot
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    if function_params and (not url):
        params = self._handle_function_params(function_params, 'navigate_to_url', {'url': 'url', 'timeout': 'timeout', 'alt_names': ['browser_navigate']})
        url = params.get('url')
        timeout = params.get('timeout', timeout)
    if not url:
        return {'status': 'error', 'message': 'URL parameter is required'}
    timeout = timeout or self.timeout
    try:
        self.driver.get(url)
        page_loaded = self._wait_for_page_load(timeout)
        if not page_loaded:
            logger.warning(f'Page load timeout for URL: {url}, but continuing with snapshot')
        snapshot_result = self.browser_snapshot()
        if snapshot_result['status'] == 'success':
            return {'status': 'success', 'url': url, 'title': self.driver.title, 'current_url': self.driver.current_url, 'snapshot': {'interactive_elements': snapshot_result.get('interactive_elements', [])}}
        else:
            return {'status': 'partial_success', 'url': url, 'title': self.driver.title, 'current_url': self.driver.current_url, 'snapshot_error': snapshot_result.get('message', 'Unknown error capturing snapshot')}
    except TimeoutException:
        return {'status': 'timeout', 'message': f'Timed out loading URL: {url}'}
    except Exception as e:
        logger.error(f'Error navigating to URL {url}: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def find_element(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
    """
        Find an element on the current page and return information about it.
        
        Args:
            selector (str): The selector to find the element
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Information about the found element
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    timeout = timeout or self.timeout
    by_type = self._get_selector_by_type(selector_type)
    if isinstance(by_type, dict):
        return by_type
    try:
        element, error = self._find_element_with_wait(by_type, selector, timeout, EC.presence_of_element_located)
        if error:
            return {'status': 'not_found', 'message': f'Element not found with {selector_type}: {selector}'}
        element_properties = self._extract_element_properties(element, selector)
        return {'status': 'success', 'element': element_properties}
    except Exception as e:
        logger.error(f'Error finding element {selector}: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def _extract_element_properties(self, element, selector: str) -> Dict[str, Any]:
    """
        Extract common properties from a WebElement.
        
        Args:
            element: The Selenium WebElement
            selector (str): The selector used to find the element (for error messages)
            
        Returns:
            Dict[str, Any]: Element properties
        """
    element_properties = {'text': element.text, 'tag_name': element.tag_name, 'is_displayed': element.is_displayed(), 'is_enabled': element.is_enabled()}
    for attr in ['href', 'id', 'class']:
        try:
            value = element.get_attribute(attr)
            if value:
                element_properties[attr] = value
        except StaleElementReferenceException:
            logger.warning(f'Element became stale when trying to get {attr} attribute for {selector}')
        except Exception as e:
            logger.warning(f'Could not get {attr} attribute for {selector}: {str(e)}')
    return element_properties

def find_multiple_elements(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
    """
        Find multiple elements on the current page and return information about them.
        
        Args:
            selector (str): The selector to find the elements
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Information about the found elements
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    timeout = timeout or self.timeout
    by_type = self._get_selector_by_type(selector_type)
    if isinstance(by_type, dict):
        return by_type
    try:
        element, error = self._find_element_with_wait(by_type, selector, timeout, EC.presence_of_element_located)
        if error:
            return {'status': 'not_found', 'message': f'No elements found with {selector_type}: {selector}'}
        elements = self.driver.find_elements(by_type, selector)
        elements_properties = []
        for idx, element in enumerate(elements):
            try:
                element_properties = self._extract_element_properties(element, f'{selector}[{idx}]')
                element_properties['index'] = idx
                elements_properties.append(element_properties)
            except StaleElementReferenceException:
                logger.warning(f'Element {idx} became stale while extracting properties')
            except Exception as e:
                logger.warning(f'Error extracting properties for element {idx}: {str(e)}')
        return {'status': 'success', 'count': len(elements_properties), 'elements': elements_properties}
    except Exception as e:
        logger.error(f'Error finding elements {selector}: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def click_element(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
    """
        Click on an element on the current page.
        
        Args:
            selector (str): The selector to find the element
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Result of the click operation
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    timeout = timeout or self.timeout
    by_type = self._get_selector_by_type(selector_type)
    if isinstance(by_type, dict):
        return by_type
    try:
        element, error = self._find_element_with_wait(by_type, selector, timeout, EC.element_to_be_clickable)
        if error:
            return {'status': 'not_found', 'message': f'Element not clickable with {selector_type}: {selector}'}
        element.click()
        page_loaded = self._wait_for_page_load(timeout)
        if not page_loaded:
            return {'status': 'partial_success', 'message': 'Element clicked, but page load timed out', 'selector': selector, 'current_url': self.driver.current_url}
        return {'status': 'success', 'message': f'Clicked element with {selector_type}: {selector}', 'current_url': self.driver.current_url, 'title': self.driver.title}
    except Exception as e:
        logger.error(f'Error clicking element {selector}: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def input_text(self, element: str=None, ref: str=None, text: str=None, submit: bool=False, slowly: bool=True, function_params: list=None) -> Dict[str, Any]:
    """
        Type text into a form field, search box, or other input element using a reference ID from a snapshot.
        
        This function only works with element references from a snapshot. Use browser_snapshot
        or navigate_to_url first to capture the page elements.
        
        This function supports multiple parameter styles:
        1. Standard style: element (description), ref (element ID), text
        2. Nested function_params style:
           function_params=[{"function_name": "browser_type", "function_args": {...}}]
        
        Args:
            element (str, optional): Human-readable description of the element (e.g., 'Search field', 'Username input')
            ref (str, optional): Element ID from the page snapshot (e.g., 'e0', 'e1', 'e2') - NOT a CSS selector
            text (str, optional): Text to input into the element
            submit (bool): Press Enter after typing to submit forms (default: false)
            slowly (bool): Type one character at a time to trigger JS events (default: true)
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Result of the text input operation
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    if function_params:
        params = self._handle_function_params(function_params, 'input_text', {'element': 'element', 'ref': 'ref', 'text': 'text', 'submit': 'submit', 'slowly': 'slowly', 'alt_names': ['browser_type']})
        element = params.get('element', element)
        ref = params.get('ref', ref)
        text = params.get('text', text)
        if 'submit' in params:
            submit = params['submit']
        if 'slowly' in params:
            slowly = params['slowly']
    if not ref or not text:
        return {'status': 'error', 'message': 'Both ref and text parameters are required'}
    selector_type, selector, error = self._parse_element_reference(ref)
    if error:
        return {'status': 'error', 'message': error}
    element_desc = element or ref
    by_type = self._get_selector_by_type(selector_type)
    if isinstance(by_type, dict):
        return by_type
    try:
        web_element, error = self._find_element_with_wait(by_type, selector, self.timeout, EC.element_to_be_clickable)
        if error:
            return {'status': 'not_found', 'message': f'Element not found: {element_desc}'}
        web_element.clear()
        if slowly:
            for char in text:
                web_element.send_keys(char)
                time.sleep(0.05)
        else:
            web_element.send_keys(text)
        if submit:
            from selenium.webdriver.common.keys import Keys
            web_element.send_keys(Keys.ENTER)
            page_loaded = self._wait_for_page_load(self.timeout)
            if not page_loaded:
                self.browser_snapshot()
                return {'status': 'partial_success', 'message': 'Text entered and submitted, but page load timed out', 'element': element_desc, 'text': text}
            snapshot_result = self.browser_snapshot()
            if snapshot_result['status'] != 'success':
                logger.warning(f'Failed to capture snapshot after form submission: {snapshot_result.get('message')}')
        return {'status': 'success', 'message': f'Successfully input text into {element_desc}' + (' and submitted' if submit else ''), 'element': element_desc, 'text': text}
    except TimeoutException:
        return {'status': 'not_found', 'message': f'Element not found: {element_desc}'}
    except Exception as e:
        logger.error(f'Error inputting text to element {element_desc}: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def get_page_content(self) -> Dict[str, Any]:
    """
        Get the current page title, URL and body content.
        
        Returns:
            Dict[str, Any]: Information about the current page
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    try:
        title = self.driver.title
        current_url = self.driver.current_url
        body_content = self.driver.execute_script('\n                var body = document.body;\n                return body ? body.outerHTML : "";\n            ')
        element_summary = self.driver.execute_script('\n                // Get common interactive elements\n                var summary = {\n                    links: [],\n                    buttons: [],\n                    inputs: [],\n                    forms: []\n                };\n                \n                // Get links\n                var links = document.querySelectorAll(\'a\');\n                for (var i = 0; i < Math.min(links.length, 20); i++) {\n                    var link = links[i];\n                    summary.links.push({\n                        text: link.textContent.trim().substring(0, 50),\n                        href: link.getAttribute(\'href\'),\n                        id: link.id,\n                        class: link.className\n                    });\n                }\n                \n                // Get buttons\n                var buttons = document.querySelectorAll(\'button, input[type="button"], input[type="submit"]\');\n                for (var i = 0; i < Math.min(buttons.length, 20); i++) {\n                    var button = buttons[i];\n                    summary.buttons.push({\n                        text: button.textContent ? button.textContent.trim().substring(0, 50) : button.value,\n                        id: button.id,\n                        class: button.className,\n                        type: button.type\n                    });\n                }\n                \n                // Get inputs\n                var inputs = document.querySelectorAll(\'input:not([type="button"]):not([type="submit"]), textarea, select\');\n                for (var i = 0; i < Math.min(inputs.length, 20); i++) {\n                    var input = inputs[i];\n                    summary.inputs.push({\n                        type: input.type,\n                        name: input.name,\n                        id: input.id,\n                        placeholder: input.placeholder\n                    });\n                }\n                \n                // Get forms\n                var forms = document.querySelectorAll(\'form\');\n                for (var i = 0; i < Math.min(forms.length, 10); i++) {\n                    var form = forms[i];\n                    summary.forms.push({\n                        id: form.id,\n                        action: form.action,\n                        method: form.method\n                    });\n                }\n                \n                return summary;\n            ')
        return {'status': 'success', 'title': title, 'url': current_url, 'body_content': body_content, 'element_summary': element_summary}
    except Exception as e:
        logger.error(f'Error getting page content: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def switch_to_frame(self, frame_reference: str, reference_type: str='index') -> Dict[str, Any]:
    """
        Switch to a frame on the page.
        
        Args:
            frame_reference (str): Reference to the frame (index, name, or ID)
            reference_type (str): Type of reference ('index', 'name', 'id', 'element')
            
        Returns:
            Dict[str, Any]: Result of the frame switch operation
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    try:
        if reference_type == 'index':
            try:
                index = int(frame_reference)
                self.driver.switch_to.frame(index)
            except ValueError:
                return {'status': 'error', 'message': f'Invalid frame index: {frame_reference}'}
        elif reference_type == 'name' or reference_type == 'id':
            self.driver.switch_to.frame(frame_reference)
        elif reference_type == 'element':
            selector_parts = frame_reference.split(':', 1)
            if len(selector_parts) != 2:
                return {'status': 'error', 'message': "Element reference must be in format 'selector_type:selector'"}
            selector_type, selector = selector_parts
            element_result = self.find_element(selector, selector_type)
            if element_result['status'] != 'success':
                return {'status': 'error', 'message': f'Could not find frame element: {element_result['message']}'}
            selector_map = {'css': By.CSS_SELECTOR, 'xpath': By.XPATH, 'id': By.ID, 'class': By.CLASS_NAME, 'name': By.NAME, 'tag': By.TAG_NAME}
            by_type = selector_map.get(selector_type.lower())
            element = self.driver.find_element(by_type, selector)
            self.driver.switch_to.frame(element)
        else:
            return {'status': 'error', 'message': f'Invalid reference type: {reference_type}'}
        return {'status': 'success', 'message': f'Switched to frame using {reference_type}: {frame_reference}'}
    except Exception as e:
        logger.error(f'Error switching to frame {frame_reference}: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def switch_to_window(self, window_reference: str, reference_type: str='index') -> Dict[str, Any]:
    """
        Switch to a window or tab.
        
        Args:
            window_reference (str): Reference to the window (index, handle, or title)
            reference_type (str): Type of reference ('index', 'handle', 'title')
            
        Returns:
            Dict[str, Any]: Result of the window switch operation
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    try:
        window_handles = self.driver.window_handles
        if not window_handles:
            return {'status': 'error', 'message': 'No window handles available'}
        if reference_type == 'index':
            try:
                index = int(window_reference)
                if index < 0 or index >= len(window_handles):
                    return {'status': 'error', 'message': f'Window index out of range: {index}'}
                self.driver.switch_to.window(window_handles[index])
            except ValueError:
                return {'status': 'error', 'message': f'Invalid window index: {window_reference}'}
        elif reference_type == 'handle':
            if window_reference not in window_handles:
                return {'status': 'error', 'message': f'Window handle not found: {window_reference}'}
            self.driver.switch_to.window(window_reference)
        elif reference_type == 'title':
            current_handle = self.driver.current_window_handle
            window_found = False
            for handle in window_handles:
                try:
                    self.driver.switch_to.window(handle)
                    if self.driver.title == window_reference:
                        window_found = True
                        break
                except Exception:
                    pass
            if not window_found:
                self.driver.switch_to.window(current_handle)
                return {'status': 'error', 'message': f"No window with title '{window_reference}' found"}
        else:
            return {'status': 'error', 'message': f'Invalid reference type: {reference_type}'}
        return {'status': 'success', 'message': f'Switched to window using {reference_type}: {window_reference}', 'title': self.driver.title, 'url': self.driver.current_url}
    except Exception as e:
        logger.error(f'Error switching to window {window_reference}: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def select_dropdown_option(self, select_selector: str, option_value: str, select_by: str='value', selector_type: str='css') -> Dict[str, Any]:
    """
        Select an option from a dropdown
        select_by can be 'value', 'text', or 'index'
        
        Args:
            select_selector (str): The selector to find the dropdown element
            option_value (str): The value to select (depends on select_by)
            select_by (str): Method to select by ('value', 'text', 'index')
            selector_type (str): Type of selector for the dropdown
            
        Returns:
            Dict[str, Any]: Result of the selection operation
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    try:
        from selenium.webdriver.support.ui import Select
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        element, error = self._find_element_with_wait(by_type, select_selector, self.timeout, EC.presence_of_element_located)
        if error:
            return {'status': 'not_found', 'message': f'Dropdown element not found with {selector_type}: {select_selector}'}
        select = Select(element)
        if select_by.lower() == 'value':
            select.select_by_value(option_value)
        elif select_by.lower() == 'text':
            select.select_by_visible_text(option_value)
        elif select_by.lower() == 'index':
            try:
                select.select_by_index(int(option_value))
            except ValueError:
                return {'status': 'error', 'message': f'Invalid index value: {option_value}. Must be an integer.'}
        else:
            return {'status': 'error', 'message': f'Invalid select_by option: {select_by}'}
        return {'status': 'success', 'message': f'Selected option with {select_by}: {option_value}'}
    except Exception as e:
        logger.error(f'Error selecting dropdown option: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def close_browser(self) -> Dict[str, Any]:
    """
        Close the browser and end the session. Call this when you're done to free resources.
        
        Returns:
            Dict[str, Any]: Status of the browser closure
        """
    if not self.driver:
        return {'status': 'success', 'message': 'Browser already closed'}
    try:
        self.driver.quit()
        self.driver = None
        return {'status': 'success', 'message': 'Browser closed successfully'}
    except Exception as e:
        logger.error(f'Error closing browser: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def browser_click(self, element: str=None, ref: str=None, function_params: list=None) -> Dict[str, Any]:
    """
        Click on a button, link, or other clickable element using a reference ID from a snapshot.
        
        This function only works with element references from a snapshot. You MUST call browser_snapshot
        or navigate_to_url first to capture the page elements.
        
        Common usage pattern:
        1. First get a snapshot: browser_snapshot() or navigate_to_url()
        2. Find the element reference (e.g. 'e0', 'e1') from the snapshot's interactive_elements
        3. Use that reference to click: browser_click(element='Login button', ref='e0')
        
        This function supports multiple parameter styles:
        1. Standard style: element (description), ref (element ID)
        2. Nested function_params style:
           function_params=[{"function_name": "browser_click", "function_args": {...}}]
        
        Args:
            element (str, optional): Human-readable description of what you're clicking (e.g., 'Login button', 'Next page link')
            ref (str, optional): Element ID from the page snapshot (e.g., 'e0', 'e1', 'e2') - NOT a CSS selector
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Result of the click operation with detailed feedback
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    if function_params and (not ref):
        params = self._handle_function_params(function_params, 'browser_click', {'element': 'element', 'ref': 'ref'})
        element = params.get('element', element)
        ref = params.get('ref', ref)
    if not ref:
        return {'status': 'error', 'message': 'Element reference (ref) parameter is required. You must first call browser_snapshot() or navigate_to_url() to get element references.', 'required_steps': ['1. Call browser_snapshot() or navigate_to_url() to get page elements', "2. Find the element reference (e.g. 'e0') in the response's interactive_elements", "3. Use that reference to click: browser_click(element='Button name', ref='e0')"]}
    if not self.element_references:
        return {'status': 'error', 'message': 'No element references found. You must first capture a page snapshot.', 'required_steps': ['1. Call browser_snapshot() or navigate_to_url() to capture the page state', '2. Use the element references returned in the snapshot']}
    selector_type, selector, error = self._parse_element_reference(ref)
    if error:
        return {'status': 'error', 'message': error, 'help': "Make sure you're using a valid element reference from a recent snapshot"}
    element_desc = element or ref
    by_type = self._get_selector_by_type(selector_type)
    if isinstance(by_type, dict):
        return by_type
    try:
        try:
            element_exists = self.driver.find_element(by_type, selector)
        except Exception:
            return {'status': 'not_found', 'message': f'Element not found: {element_desc}', 'suggestion': 'The page may have changed. Try getting a new snapshot with browser_snapshot()'}
        web_element, error = self._find_element_with_wait(by_type, selector, self.timeout, EC.element_to_be_clickable)
        if error:
            try:
                is_visible = element_exists.is_displayed()
                is_enabled = element_exists.is_enabled()
                element_tag = element_exists.tag_name
                element_classes = element_exists.get_attribute('class')
                return {'status': 'not_clickable', 'message': f'Element found but not clickable: {element_desc}', 'element_state': {'visible': is_visible, 'enabled': is_enabled, 'tag': element_tag, 'classes': element_classes}, 'suggestion': 'The element might be disabled, hidden, or covered by another element'}
            except Exception:
                return {'status': 'not_clickable', 'message': f'Element found but not clickable: {element_desc}', 'suggestion': 'The element might be disabled, hidden, or covered by another element'}
        web_element.click()
        page_loaded = self._wait_for_page_load(self.timeout)
        if not page_loaded:
            snapshot_result = self.browser_snapshot()
            return {'status': 'partial_success', 'message': 'Element clicked, but page load timed out', 'element': element_desc, 'current_url': self.driver.current_url, 'snapshot': snapshot_result if snapshot_result['status'] == 'success' else None, 'suggestion': 'The page might still be loading. You may want to wait and take another snapshot.'}
        snapshot_result = self.browser_snapshot()
        if snapshot_result['status'] == 'success':
            return {'status': 'success', 'message': f'Successfully clicked on {element_desc}', 'element': element_desc, 'current_url': self.driver.current_url, 'title': self.driver.title, 'snapshot': {'interactive_elements': snapshot_result.get('interactive_elements', [])}}
        else:
            return {'status': 'success', 'message': f'Successfully clicked on {element_desc} but snapshot failed', 'element': element_desc, 'current_url': self.driver.current_url, 'title': self.driver.title, 'snapshot_error': snapshot_result.get('message', 'Unknown error capturing snapshot'), 'suggestion': 'You may want to take another snapshot with browser_snapshot()'}
    except TimeoutException:
        return {'status': 'timeout', 'message': f'Timed out waiting for element to be clickable: {element_desc}', 'suggestion': 'The element might be taking too long to load or become clickable'}
    except Exception as e:
        logger.error(f'Error clicking element: {str(e)}')
        return {'status': 'error', 'message': str(e), 'element': element_desc, 'suggestion': 'Try getting a new snapshot of the page with browser_snapshot()'}

def browser_snapshot(self, function_params: list=None) -> Dict[str, Any]:
    """
        Capture a fresh snapshot of the current page with all interactive elements. 
        Use after page state changes not caused by navigation or clicking.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "browser_snapshot", "function_args": {}}]
        
        Args:
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: The accessibility snapshot of the page with interactive elements
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    try:
        title = self.driver.title
        current_url = self.driver.current_url
        accessibility_tree = self.driver.execute_script("\n                function getAccessibilityTree(node, depth = 0, maxDepth = 10) {\n                    if (!node || depth > maxDepth) return null;\n                    \n                    let result = {\n                        role: node.role || node.tagName,\n                        name: node.name || '',\n                        type: node.type || '',\n                        value: node.value || '',\n                        description: node.description || '',\n                        properties: {},\n                        visible: isElementVisible(node)\n                    };\n                    \n                    // Helper function for element visibility\n                    function isElementVisible(element) {\n                        if (!element.getBoundingClientRect) return true;\n                        const style = window.getComputedStyle(element);\n                        const rect = element.getBoundingClientRect();\n                        \n                        // Check basic visibility\n                        const isVisible = style.display !== 'none' && \n                                        style.visibility !== 'hidden' && \n                                        style.opacity !== '0' &&\n                                        rect.width > 0 && \n                                        rect.height > 0;\n                                        \n                        // Check if element is in viewport\n                        const isInViewport = rect.top >= 0 &&\n                                           rect.left >= 0 &&\n                                           rect.bottom <= window.innerHeight &&\n                                           rect.right <= window.innerWidth;\n                                           \n                        return isVisible && isInViewport;\n                    }\n                    \n                    // Add text content\n                    if (node.textContent) {\n                        result.text_content = node.textContent.trim();\n                    }\n\n                    // Add identifier properties for references\n                    if (node.id) result.properties.id = node.id;\n                    if (node.className) result.properties.class = node.className;\n                    if (node.tagName) result.properties.tag = node.tagName.toLowerCase();\n                    \n                    // Add attributes\n                    if (node.attributes) {\n                        result.attributes = {};\n                        for (let attr of node.attributes) {\n                            result.attributes[attr.name] = attr.value;\n                        }\n                    }\n\n                    // Add custom ref property that combines selector types\n                    let refs = [];\n                    // Store all possible selectors, but don't use them as primary ref\n                    if (node.id) refs.push(`id:${node.id}`);\n                    if (node.className && typeof node.className === 'string') \n                        refs.push(`class:${node.className}`);\n                    if (node.tagName) refs.push(`tag:${node.tagName.toLowerCase()}`);\n                    \n                    // For inputs, add name attribute\n                    if (node.getAttribute && node.getAttribute('name')) {\n                        result.properties.name = node.getAttribute('name');\n                        refs.push(`name:${node.getAttribute('name')}`);\n                    }\n                    \n                    // Create XPath and CSS selectors\n                    try {\n                        // CSS selector\n                        let cssPath = getCssPath(node);\n                        if (cssPath) refs.push(`css:${cssPath}`);\n                        \n                        // XPath\n                        let xpath = getXPath(node);\n                        if (xpath) refs.push(`xpath:${xpath}`);\n                    } catch (e) {}\n                    \n                    // Store all refs but don't set primary ref here\n                    if (refs.length > 0) {\n                        result.all_refs = refs;\n                    }\n\n                    // Add semantic information about the element\n                    result.semantic_info = {\n                        // What the element represents\n                        purpose: (function() {\n                            if (node.tagName === 'INPUT') {\n                                if (node.type === 'submit') return 'submit button';\n                                if (node.type === 'search') return 'search box';\n                                if (node.type === 'text') return 'text input';\n                                return `${node.type || 'text'} input`;\n                            }\n                            if (node.tagName === 'BUTTON') return 'button';\n                            if (node.tagName === 'A') return 'link';\n                            if (node.tagName === 'SELECT') return 'dropdown';\n                            if (node.tagName === 'TEXTAREA') return 'text area';\n                            if (node.getAttribute('role')) return node.getAttribute('role');\n                            return 'interactive element';\n                        })(),\n                        \n                        // The visible or accessible text\n                        label: (function() {\n                            return node.getAttribute('aria-label') ||\n                                   node.getAttribute('title') ||\n                                   node.getAttribute('placeholder') ||\n                                   node.getAttribute('alt') ||\n                                   (node.tagName === 'INPUT' ? node.value : node.textContent.trim());\n                        })(),\n                        \n                        // Is this a primary action?\n                        isPrimary: !!(\n                            node.classList.contains('primary') ||\n                            node.getAttribute('aria-label')?.toLowerCase().includes('search') ||\n                            node.getAttribute('title')?.toLowerCase().includes('search') ||\n                            node.type === 'search' ||\n                            node.getAttribute('role') === 'main' ||\n                            node.id?.toLowerCase().includes('main') ||\n                            node.classList.contains('main')\n                        ),\n                        \n                        // Basic category\n                        category: (function() {\n                            if (node.type === 'search' || \n                                node.getAttribute('role') === 'searchbox') return 'search';\n                            if (node.type === 'submit' || \n                                node.tagName === 'BUTTON' ||\n                                node.getAttribute('role') === 'button') return 'action';\n                            if (node.tagName === 'A' ||\n                                node.getAttribute('role') === 'link') return 'navigation';\n                            if (node.tagName === 'INPUT' || \n                                node.tagName === 'TEXTAREA' ||\n                                node.getAttribute('role') === 'textbox') return 'input';\n                            if (node.tagName === 'SELECT' ||\n                                ['listbox', 'combobox'].includes(node.getAttribute('role'))) return 'selection';\n                            return 'interactive';\n                        })()\n                    };\n                    \n                    // Process children\n                    result.children = [];\n                    if (node.children) {\n                        for (let i = 0; i < node.children.length; i++) {\n                            const childTree = getAccessibilityTree(node.children[i], depth + 1, maxDepth);\n                            if (childTree) {\n                                result.children.push(childTree);\n                            }\n                        }\n                    }\n                    \n                    return result;\n                }\n                \n                return getAccessibilityTree(document.body);\n            ")
        all_elements = self._process_accessibility_tree(accessibility_tree)
        page_content = html2text.html2text(self.driver.page_source)
        return {'status': 'success', 'title': title, 'url': current_url, 'accessibility_tree': accessibility_tree, 'page_content': page_content, 'interactive_elements': [e for e in all_elements if e.get('interactable') or e.get('editable')]}
    except Exception as e:
        logger.error(f'Error generating accessibility snapshot: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def browser_console_messages(self, function_params: list=None) -> Dict[str, Any]:
    """
        Retrieve JavaScript console messages (logs, warnings, errors) from the browser for debugging.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "browser_console_messages", "function_args": {}}]
        
        Args:
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: The console messages including logs, warnings and errors
        """
    driver_check = self._check_driver_initialized()
    if driver_check:
        return driver_check
    try:
        logs = self._collect_browser_logs()
        return {'status': 'success', 'console_messages': logs}
    except Exception as e:
        logger.error(f'Error retrieving console messages: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def _collect_browser_logs(self) -> List[Dict[str, Any]]:
    """
        Collect logs from both the browser driver and JavaScript console.
        
        Returns:
            List[Dict[str, Any]]: Combined logs from both sources
        """
    logs = []
    try:
        browser_logs = self.driver.get_log('browser')
        for log in browser_logs:
            level = log.get('level', '').upper()
            if level == 'SEVERE':
                level = 'ERROR'
            elif level == 'INFO':
                level = 'LOG'
            logs.append({'level': level, 'message': log.get('message', ''), 'timestamp': log.get('timestamp', '')})
    except Exception as log_error:
        logs.append({'level': 'WARNING', 'message': f'Could not retrieve browser logs: {str(log_error)}', 'timestamp': ''})
    try:
        self.driver.execute_script("\n                if (!window._consoleLogs) {\n                    window._consoleLogs = [];\n                    \n                    // Store original console methods\n                    const originalConsole = {\n                        log: console.log,\n                        info: console.info,\n                        warn: console.warn,\n                        error: console.error,\n                        debug: console.debug\n                    };\n                    \n                    // Helper function to add message with proper level\n                    function addMessage(level, args) {\n                        window._consoleLogs.push({\n                            level: level.toUpperCase(),\n                            message: Array.from(args).join(' '),\n                            timestamp: new Date().toISOString()\n                        });\n                    }\n                    \n                    // Override console methods to capture logs\n                    console.log = function() {\n                        addMessage('LOG', arguments);\n                        originalConsole.log.apply(console, arguments);\n                    };\n                    \n                    console.info = function() {\n                        addMessage('INFO', arguments);\n                        originalConsole.info.apply(console, arguments);\n                    };\n                    \n                    console.warn = function() {\n                        addMessage('WARN', arguments);\n                        originalConsole.warn.apply(console, arguments);\n                    };\n                    \n                    console.error = function() {\n                        addMessage('ERROR', arguments);\n                        originalConsole.error.apply(console, arguments);\n                    };\n                    \n                    console.debug = function() {\n                        addMessage('DEBUG', arguments);\n                        originalConsole.debug.apply(console, arguments);\n                    };\n                }\n            ")
        time.sleep(2)
        js_logs = self.driver.execute_script('return window._consoleLogs || [];')
        for log in js_logs:
            if log not in logs:
                logs.append(log)
    except Exception as js_error:
        logs.append({'level': 'WARNING', 'message': f'Could not retrieve JavaScript console logs: {str(js_error)}', 'timestamp': ''})
    return logs

def __del__(self):
    """
        Destructor to automatically close the browser when the instance is destroyed.
        """
    if hasattr(self, 'driver') and self.driver:
        try:
            self.driver.quit()
            logger.info('Browser automatically closed on cleanup')
        except Exception as e:
            logger.warning(f'Error during automatic browser cleanup: {str(e)}')

class NavigateToUrlTool(Tool):
    name: str = 'navigate_to_url'
    description: str = 'Navigate to a URL and capture a snapshot of all page elements'
    inputs: Dict[str, Dict[str, str]] = {'url': {'type': 'string', 'description': 'The complete URL (with https://) to navigate to'}, 'timeout': {'type': 'integer', 'description': 'Custom timeout in seconds (default: 10)'}}
    required: Optional[List[str]] = ['url']

    def __init__(self, browser_tool: BrowserBase=None):
        super().__init__()
        self.browser_tool = browser_tool

    def __call__(self, url: str, timeout: int=None, function_params: list=None) -> Dict[str, Any]:
        """Navigate to URL using the BrowserBase instance."""
        if not self.browser_tool:
            raise RuntimeError('Browser tool instance not initialized')
        try:
            return self.browser_tool.navigate_to_url(url, timeout, function_params)
        except Exception as e:
            return {'status': 'error', 'message': f'Error navigating to URL: {str(e)}'}

def __call__(self, url: str, timeout: int=None, function_params: list=None) -> Dict[str, Any]:
    """Navigate to URL using the BrowserBase instance."""
    if not self.browser_tool:
        raise RuntimeError('Browser tool instance not initialized')
    try:
        return self.browser_tool.navigate_to_url(url, timeout, function_params)
    except Exception as e:
        return {'status': 'error', 'message': f'Error navigating to URL: {str(e)}'}

class InputTextTool(Tool):
    name: str = 'input_text'
    description: str = 'Type text into a form field, search box, or other input element using a reference ID from a snapshot'
    inputs: Dict[str, Dict[str, str]] = {'element': {'type': 'string', 'description': "Human-readable description of the element (e.g., 'Search field', 'Username input')"}, 'ref': {'type': 'string', 'description': "Element ID from the page snapshot (e.g., 'e0', 'e1', 'e2'). Must refer to an editable element."}, 'text': {'type': 'string', 'description': 'Text to input into the element'}, 'submit': {'type': 'boolean', 'description': 'Press Enter after typing to submit forms (default: false)'}, 'slowly': {'type': 'boolean', 'description': 'Type one character at a time to trigger JS events (default: true)'}}
    required: Optional[List[str]] = ['element', 'ref', 'text']

    def __init__(self, browser_tool: BrowserBase=None):
        super().__init__()
        self.browser_tool = browser_tool

    def __call__(self, element: str, ref: str, text: str, submit: bool=False, slowly: bool=True, function_params: list=None) -> Dict[str, Any]:
        """Input text using the BrowserBase instance."""
        if not self.browser_tool:
            raise RuntimeError('Browser tool instance not initialized')
        try:
            return self.browser_tool.input_text(element, ref, text, submit, slowly, function_params)
        except Exception as e:
            return {'status': 'error', 'message': f'Error inputting text: {str(e)}'}

def __call__(self, element: str, ref: str, text: str, submit: bool=False, slowly: bool=True, function_params: list=None) -> Dict[str, Any]:
    """Input text using the BrowserBase instance."""
    if not self.browser_tool:
        raise RuntimeError('Browser tool instance not initialized')
    try:
        return self.browser_tool.input_text(element, ref, text, submit, slowly, function_params)
    except Exception as e:
        return {'status': 'error', 'message': f'Error inputting text: {str(e)}'}

class BrowserClickTool(Tool):
    name: str = 'browser_click'
    description: str = 'Click on a button, link, or other clickable element using a reference ID from a snapshot'
    inputs: Dict[str, Dict[str, str]] = {'element': {'type': 'string', 'description': "Human-readable description of what you're clicking (e.g., 'Login button', 'Next page link', 'Submit button')"}, 'ref': {'type': 'string', 'description': "Element ID from the page snapshot (e.g., 'e0', 'e1', 'e2'). You MUST get this ID from a previous snapshot's interactive_elements."}}
    required: Optional[List[str]] = []

    def __init__(self, browser_tool: BrowserBase=None):
        super().__init__()
        self.browser_tool = browser_tool

    def __call__(self, element: str, ref: str, function_params: list=None) -> Dict[str, Any]:
        """Click element using the BrowserBase instance."""
        if not self.browser_tool:
            raise RuntimeError('Browser tool instance not initialized')
        try:
            return self.browser_tool.browser_click(element, ref, function_params)
        except Exception as e:
            return {'status': 'error', 'message': f'Error clicking element: {str(e)}'}

def __call__(self, element: str, ref: str, function_params: list=None) -> Dict[str, Any]:
    """Click element using the BrowserBase instance."""
    if not self.browser_tool:
        raise RuntimeError('Browser tool instance not initialized')
    try:
        return self.browser_tool.browser_click(element, ref, function_params)
    except Exception as e:
        return {'status': 'error', 'message': f'Error clicking element: {str(e)}'}

class BrowserSnapshotTool(Tool):
    name: str = 'browser_snapshot'
    description: str = 'Capture a fresh snapshot of the current page, including all elements'
    inputs: Dict[str, Dict[str, str]] = {}
    required: Optional[List[str]] = []

    def __init__(self, browser_tool: BrowserBase=None):
        super().__init__()
        self.browser_tool = browser_tool

    def __call__(self, function_params: list=None) -> Dict[str, Any]:
        """Take browser snapshot using the BrowserBase instance."""
        if not self.browser_tool:
            raise RuntimeError('Browser tool instance not initialized')
        try:
            return self.browser_tool.browser_snapshot(function_params)
        except Exception as e:
            return {'status': 'error', 'message': f'Error taking snapshot: {str(e)}'}

def __call__(self, function_params: list=None) -> Dict[str, Any]:
    """Take browser snapshot using the BrowserBase instance."""
    if not self.browser_tool:
        raise RuntimeError('Browser tool instance not initialized')
    try:
        return self.browser_tool.browser_snapshot(function_params)
    except Exception as e:
        return {'status': 'error', 'message': f'Error taking snapshot: {str(e)}'}

class BrowserConsoleMessagesTool(Tool):
    name: str = 'browser_console_messages'
    description: str = 'Retrieve JavaScript console messages (logs, warnings, errors) from the browser for debugging'
    inputs: Dict[str, Dict[str, str]] = {}
    required: Optional[List[str]] = []

    def __init__(self, browser_tool: BrowserBase=None):
        super().__init__()
        self.browser_tool = browser_tool

    def __call__(self, function_params: list=None) -> Dict[str, Any]:
        """Get console messages using the BrowserBase instance."""
        if not self.browser_tool:
            raise RuntimeError('Browser tool instance not initialized')
        try:
            return self.browser_tool.browser_console_messages(function_params)
        except Exception as e:
            return {'status': 'error', 'message': f'Error getting console messages: {str(e)}'}

def __call__(self, function_params: list=None) -> Dict[str, Any]:
    """Get console messages using the BrowserBase instance."""
    if not self.browser_tool:
        raise RuntimeError('Browser tool instance not initialized')
    try:
        return self.browser_tool.browser_console_messages(function_params)
    except Exception as e:
        return {'status': 'error', 'message': f'Error getting console messages: {str(e)}'}

class MCPClient:

    def __init__(self, server_configs: Union[Dict[str, Any], List[Dict[str, Any]]], connect_timeout: float=120.0):
        if isinstance(server_configs, dict):
            self.server_configs = [server_configs]
        else:
            self.server_configs = server_configs
        self.event_loop = asyncio.new_event_loop()
        self.sessions: list[Client] = []
        self.mcp_tools: list[list[Any]] = []
        self.task = None
        self.thread_running = threading.Event()
        self.working_thread = threading.Thread(target=self._run_event, daemon=True)
        self.connect_timeout = connect_timeout
        self.tools = None
        self.tool_schemas = None
        self.tool_descriptions = None

    def _disconnect(self):
        if hasattr(self, 'shutdown_event') and self.shutdown_event:
            self.event_loop.call_soon_threadsafe(self.shutdown_event.set)
        if self.task and (not self.task.done()):
            self.event_loop.call_soon_threadsafe(self.task.cancel)
        if hasattr(self, 'working_thread') and self.working_thread.is_alive():
            self.working_thread.join(timeout=5)
        if hasattr(self, 'event_loop') and (not self.event_loop.is_closed()):
            self.event_loop.close()

    def _connect(self):
        self.working_thread.start()
        if not self.thread_running.wait(timeout=self.connect_timeout):
            self._disconnect()
            raise TimeoutError(f"Couldn't connect to the MCP server after {self.connect_timeout} seconds")

    def __enter__(self):
        self._connect()
        return self.get_toolkits()

    def __del__(self):
        try:
            self._disconnect()
        except Exception:
            pass

    def __exit__(self, exc_type, exc_value, traceback):
        self._disconnect()

    def _run_event(self):
        """Runs the event loop in a separate thread (for synchronous usage)."""
        print('Running event loop')
        asyncio.set_event_loop(self.event_loop)

        async def setup():
            try:
                async with AsyncExitStack() as stack:
                    connections = [await stack.enter_async_context(self._start_server(config)) for config in self.server_configs]
                    self.sessions, self.mcp_tools = [list(c) for c in zip(*connections)]
                    self.thread_running.set()
                    self.shutdown_event = asyncio.Event()
                    await self.shutdown_event.wait()
            except Exception as e:
                logger.error(f'Error in MCP event loop: {str(e)}')
                self.thread_running.set()
                raise
        self.task = self.event_loop.create_task(setup())
        try:
            self.event_loop.run_until_complete(self.task)
        except asyncio.CancelledError:
            logger.info('MCP client event loop was cancelled')
        except Exception as e:
            logger.error(f'Error in MCP event loop: {str(e)}')
        finally:
            if not self.event_loop.is_closed():
                self.event_loop.close()

    @asynccontextmanager
    async def _start_server(self, config: Dict[str, Any]):
        client = Client(config)
        async with client:
            tools = await client.list_tools()
            yield (client, tools)

    def create_tool(self, session: Client, mcp_tools: List[Any], config: Dict[str, Any]) -> Toolkit:

        def _sync_call_tool(name: str, **kwargs) -> Any:
            try:
                if 'arguments' in kwargs and len(kwargs) == 1:
                    arguments = kwargs['arguments']
                else:
                    arguments = kwargs
                logger.info(f'Calling MCP tool: {name} with arguments: {arguments}')
                future = asyncio.run_coroutine_threadsafe(session.call_tool(name, arguments), self.event_loop)
                result = future.result(timeout=30)
                logger.info(f'MCP tool {name} call completed successfully')
                return result
            except (TimeoutError, ClientError, McpError) as e:
                logger.error(f'Error calling MCP tool {name}: {str(e)}')
                raise
            except Exception as e:
                logger.error(f'Unexpected error calling MCP tool {name}: {str(e)}')
                raise
        all_tools = []
        for mcp_tool in mcp_tools:
            input_schema = getattr(mcp_tool, 'inputSchema', {})
            if not input_schema and hasattr(mcp_tool, 'input_schema'):
                input_schema = mcp_tool.input_schema
            properties = input_schema.get('properties', {})
            required = input_schema.get('required', [])
            inputs = properties
            partial_func = partial(_sync_call_tool, mcp_tool.name)
            partial_func.__name__ = mcp_tool.name
            tool = MCPTool(name=mcp_tool.name, description=getattr(mcp_tool, 'description', None) or '', inputs=inputs, required=required, function=partial_func)
            all_tools.append(tool)
        tool_collection = Toolkit(name=next(iter(config.get('mcpServers').keys())), tools=all_tools)
        return tool_collection

    def get_toolkits(self) -> List[Toolkit]:
        """Return a list ofToolkits, one per server."""
        if not self.sessions:
            raise RuntimeError('Session not initialized')
        return [self.create_tool(session, tools, config) for session, tools, config in zip(self.sessions, self.mcp_tools, self.server_configs)]

def _sync_call_tool(name: str, **kwargs) -> Any:
    try:
        if 'arguments' in kwargs and len(kwargs) == 1:
            arguments = kwargs['arguments']
        else:
            arguments = kwargs
        logger.info(f'Calling MCP tool: {name} with arguments: {arguments}')
        future = asyncio.run_coroutine_threadsafe(session.call_tool(name, arguments), self.event_loop)
        result = future.result(timeout=30)
        logger.info(f'MCP tool {name} call completed successfully')
        return result
    except (TimeoutError, ClientError, McpError) as e:
        logger.error(f'Error calling MCP tool {name}: {str(e)}')
        raise
    except Exception as e:
        logger.error(f'Unexpected error calling MCP tool {name}: {str(e)}')
        raise

class MCPToolkit:

    def __init__(self, servers: Optional[list[MCPClient]]=None, config_path: Optional[str]=None, config: Optional[dict[str, Any]]=None):
        parameters = []
        if config_path:
            parameters += self._from_config_file(config_path)
        if config:
            parameters += self._from_config(config)
        self.servers = []
        if parameters:
            self.servers.append(MCPClient(parameters))
        if servers:
            self.servers.extend(servers)
        failed_servers = []
        for server in self.servers:
            try:
                server._connect()
                logger.info('Successfully connected to MCP servers')
            except TimeoutError as e:
                logger.warning(f'Timeout connecting to MCP servers: {str(e)}. Some tools may not be available.')
                failed_servers.append(server)
            except Exception as e:
                logger.error(f'Error connecting to MCP servers: {str(e)}')
                failed_servers.append(server)
        for failed_server in failed_servers:
            if failed_server in self.servers:
                self.servers.remove(failed_server)

    def _from_config_file(self, config_path: str):
        try:
            with open(config_path, 'r') as f:
                server_configs = json.load(f)
            return self._from_config(server_configs)
        except FileNotFoundError:
            logger.error(f'Config file not found: {config_path}')
            return []
        except json.JSONDecodeError:
            logger.error(f'Invalid JSON in config file: {config_path}')
            return []

    def _from_config(self, server_configs: dict[str, Any]):
        if not isinstance(server_configs, dict):
            logger.error('Server configuration must be a dictionary')
            return []
        if 'mcpServers' not in server_configs:
            raise ValueError("Server configuration must contain 'mcpServers' key")
        server_list = []
        for server_name, server_config in server_configs['mcpServers'].items():
            individual_config = {'mcpServers': {server_name: server_config}}
            server_list.append(individual_config)
        return server_list

    def disconnect(self):
        for server in self.servers:
            try:
                server._disconnect()
            except Exception as e:
                logger.warning(f'Error disconnecting from MCP server: {str(e)}')
        self.servers.clear()

    def get_toolkits(self) -> List[Toolkit]:
        """Return a flattened list of all tools across all servers"""
        all_tools = []
        if not self.servers:
            logger.info('No MCP servers configured, returning empty toolkit list')
            return all_tools
        for server in self.servers:
            try:
                import threading
                import queue
                result_queue = queue.Queue()
                exception_queue = queue.Queue()

                def get_tools_with_timeout():
                    try:
                        tools = server.get_toolkits()
                        result_queue.put(tools)
                    except Exception as e:
                        exception_queue.put(e)
                thread = threading.Thread(target=get_tools_with_timeout)
                thread.daemon = True
                thread.start()
                thread.join(timeout=30)
                if thread.is_alive():
                    logger.warning('Timeout getting tools from MCP server after 30 seconds')
                    continue
                if not exception_queue.empty():
                    raise exception_queue.get()
                tools = result_queue.get()
                all_tools.extend(tools)
                logger.info(f'Added {len(tools)} tools from MCP server')
            except Exception as e:
                logger.error(f'Error getting tools from MCP server: {str(e)}')
        return all_tools

def __init__(self, servers: Optional[list[MCPClient]]=None, config_path: Optional[str]=None, config: Optional[dict[str, Any]]=None):
    parameters = []
    if config_path:
        parameters += self._from_config_file(config_path)
    if config:
        parameters += self._from_config(config)
    self.servers = []
    if parameters:
        self.servers.append(MCPClient(parameters))
    if servers:
        self.servers.extend(servers)
    failed_servers = []
    for server in self.servers:
        try:
            server._connect()
            logger.info('Successfully connected to MCP servers')
        except TimeoutError as e:
            logger.warning(f'Timeout connecting to MCP servers: {str(e)}. Some tools may not be available.')
            failed_servers.append(server)
        except Exception as e:
            logger.error(f'Error connecting to MCP servers: {str(e)}')
            failed_servers.append(server)
    for failed_server in failed_servers:
        if failed_server in self.servers:
            self.servers.remove(failed_server)

class DDGSSearchTool(Tool):
    name: str = 'ddgs_search'
    description: str = 'Search using DDGS (Dux Distributed Global Search) which aggregates results from multiple search engines including DuckDuckGo, Google, Bing, and others'
    inputs: Dict[str, Dict[str, str]] = {'query': {'type': 'string', 'description': 'The search query to execute'}, 'num_search_pages': {'type': 'integer', 'description': 'Number of search results to retrieve. Default: 5'}, 'max_content_words': {'type': 'integer', 'description': 'Maximum number of words to include in content per result. None means no limit. Default: None'}, 'backend': {'type': 'string', 'description': "Search backend to use. Options: 'auto', 'duckduckgo', 'google', 'bing', 'brave', 'yahoo'. Default: 'auto'"}, 'region': {'type': 'string', 'description': "Search region (e.g., 'us-en', 'uk-en', 'ru-ru'). Default: 'us-en'"}}
    required: Optional[List[str]] = ['query']

    def __init__(self, search_ddgs: SearchDDGS=None):
        super().__init__()
        self.search_ddgs = search_ddgs

    def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None, backend: str=None, region: str=None) -> Dict[str, Any]:
        """Execute DDGS search using the SearchDDGS instance."""
        if not self.search_ddgs:
            raise RuntimeError('DDGS search instance not initialized')
        try:
            return self.search_ddgs.search(query, num_search_pages, max_content_words, backend, region)
        except Exception as e:
            return {'results': [], 'error': f'Error executing DDGS search: {str(e)}'}

def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None, backend: str=None, region: str=None) -> Dict[str, Any]:
    """Execute DDGS search using the SearchDDGS instance."""
    if not self.search_ddgs:
        raise RuntimeError('DDGS search instance not initialized')
    try:
        return self.search_ddgs.search(query, num_search_pages, max_content_words, backend, region)
    except Exception as e:
        return {'results': [], 'error': f'Error executing DDGS search: {str(e)}'}

class FileStorageHandler(StorageBase):
    """
    Reference implementation showing all available _raw_xxx methods.
    This class serves as a template for developers creating new storage handlers.
    Concrete handlers only need to implement the _raw_xxx methods they need.
    """

    def __init__(self, base_path: str='.', **kwargs):
        """
        Initialize the storage handler.
        
        Args:
            base_path (str): Base directory for storage operations (default: current directory)
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(base_path=base_path, **kwargs)

    def create(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        return super().save(file_path, content, **kwargs)

    def read(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return super().read(file_path, **kwargs)

    def list(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
        return super().list(path, max_depth, include_hidden)

    def delete(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return super().delete(file_path, **kwargs)

    def move(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return super().move(source, destination, **kwargs)

    def copy(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return super().copy(source, destination, **kwargs)

    def create_directory(self, path: str, **kwargs) -> Dict[str, Any]:
        return super().create_directory(path, **kwargs)

    @abstractmethod
    def _initialize_storage(self):
        """Initialize storage - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _read_raw(self, path: str, **kwargs) -> bytes:
        """Read raw file content - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _write_raw(self, path: str, content: bytes, **kwargs) -> bool:
        """Write raw file content - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _delete_raw(self, path: str) -> bool:
        """Delete file or directory - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _exists_raw(self, path: str) -> bool:
        """Check if path exists - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _create_directory_raw(self, path: str) -> bool:
        """Create directory - must be implemented by subclasses"""
        pass

    @abstractmethod
    def _list_raw(self, path: str=None, **kwargs) -> List[Dict[str, Any]]:
        """List files and directories - must be implemented by subclasses"""
        pass

    def create_file(self, file_path: str, content: Any, **kwargs) -> Dict[str, Any]:
        return self.save(file_path, content, **kwargs)

    def read_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return self.read(file_path, **kwargs)

    def list_files(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
        return self.list(path, max_depth, include_hidden)

    def delete_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        return self.delete(file_path, **kwargs)

    def move_file(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return self.move(source, destination, **kwargs)

    def copy_file(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        return self.copy(source, destination, **kwargs)

def move(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
    return super().move(source, destination, **kwargs)

def copy(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
    return super().copy(source, destination, **kwargs)

def create_directory(self, path: str, **kwargs) -> Dict[str, Any]:
    return super().create_directory(path, **kwargs)

def move_file(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
    return self.move(source, destination, **kwargs)

def copy_file(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
    return self.copy(source, destination, **kwargs)

class LocalStorageHandler(FileStorageHandler):
    """
    Local filesystem storage implementation.
    Provides all file operations for local storage with default working directory.
    """

    def __init__(self, base_path: str='.', **kwargs):
        """
        Initialize local storage handler.
        
        Args:
            base_path (str): Base directory for storage operations (default: current directory)
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(base_path=base_path, **kwargs)

    def _initialize_storage(self):
        """Initialize local storage - ensure base directory exists"""
        try:
            Path(self.base_path).mkdir(parents=True, exist_ok=True)
            logger.info(f'Local storage initialized with base path: {self.base_path}')
        except Exception as e:
            logger.error(f'Error initializing local storage: {str(e)}')
            raise

    def _read_raw(self, path: str, **kwargs) -> bytes:
        """Read raw file content from local filesystem"""
        try:
            with open(path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f'Error reading file {path}: {str(e)}')
            raise

    def _write_raw(self, path: str, content: bytes, **kwargs) -> bool:
        """Write raw file content to local filesystem"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'wb') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f'Error writing file {path}: {str(e)}')
            return False

    def _delete_raw(self, path: str) -> bool:
        """Delete file or directory from local filesystem"""
        try:
            path_obj = Path(path)
            if path_obj.is_file():
                path_obj.unlink()
            elif path_obj.is_dir():
                shutil.rmtree(path_obj)
            else:
                return False
            return True
        except Exception as e:
            logger.error(f'Error deleting {path}: {str(e)}')
            return False

    def _list_raw(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> List[Dict[str, Any]]:
        """List files and directories in local filesystem"""
        try:
            if path is None:
                path = str(self.base_path)
            path_obj = Path(path)
            if not path_obj.exists() or not path_obj.is_dir():
                return []
            items = []

            def scan_directory(current_path: Path, current_depth: int):
                if current_depth > max_depth:
                    return
                try:
                    for item in current_path.iterdir():
                        if not include_hidden and item.name.startswith('.'):
                            continue
                        try:
                            stat = item.stat()
                            item_info = {'name': item.name, 'path': str(item), 'type': 'directory' if item.is_dir() else 'file', 'size_bytes': stat.st_size if item.is_file() else 0, 'size_mb': round(stat.st_size / (1024 * 1024), 2) if item.is_file() else 0, 'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(), 'extension': item.suffix.lower() if item.is_file() else '', 'is_hidden': item.name.startswith('.')}
                            items.append(item_info)
                            if item.is_dir() and current_depth < max_depth:
                                scan_directory(item, current_depth + 1)
                        except (PermissionError, OSError):
                            continue
                except (PermissionError, OSError) as e:
                    logger.warning(f'Error scanning directory {current_path}: {str(e)}')
            scan_directory(path_obj, 0)
            return items
        except Exception as e:
            logger.error(f'Error listing directory {path}: {str(e)}')
            return []

    def _exists_raw(self, path: str) -> bool:
        """Check if path exists in local filesystem"""
        return Path(path).exists()

    def _create_directory_raw(self, path: str) -> bool:
        """Create directory in local filesystem"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f'Error creating directory {path}: {str(e)}')
            return False

def _delete_raw(self, path: str) -> bool:
    """Delete file or directory from local filesystem"""
    try:
        path_obj = Path(path)
        if path_obj.is_file():
            path_obj.unlink()
        elif path_obj.is_dir():
            shutil.rmtree(path_obj)
        else:
            return False
        return True
    except Exception as e:
        logger.error(f'Error deleting {path}: {str(e)}')
        return False

def _list_raw(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> List[Dict[str, Any]]:
    """List files and directories in local filesystem"""
    try:
        if path is None:
            path = str(self.base_path)
        path_obj = Path(path)
        if not path_obj.exists() or not path_obj.is_dir():
            return []
        items = []

        def scan_directory(current_path: Path, current_depth: int):
            if current_depth > max_depth:
                return
            try:
                for item in current_path.iterdir():
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    try:
                        stat = item.stat()
                        item_info = {'name': item.name, 'path': str(item), 'type': 'directory' if item.is_dir() else 'file', 'size_bytes': stat.st_size if item.is_file() else 0, 'size_mb': round(stat.st_size / (1024 * 1024), 2) if item.is_file() else 0, 'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(), 'extension': item.suffix.lower() if item.is_file() else '', 'is_hidden': item.name.startswith('.')}
                        items.append(item_info)
                        if item.is_dir() and current_depth < max_depth:
                            scan_directory(item, current_depth + 1)
                    except (PermissionError, OSError):
                        continue
            except (PermissionError, OSError) as e:
                logger.warning(f'Error scanning directory {current_path}: {str(e)}')
        scan_directory(path_obj, 0)
        return items
    except Exception as e:
        logger.error(f'Error listing directory {path}: {str(e)}')
        return []

def scan_directory(current_path: Path, current_depth: int):
    if current_depth > max_depth:
        return
    try:
        for item in current_path.iterdir():
            if not include_hidden and item.name.startswith('.'):
                continue
            try:
                stat = item.stat()
                item_info = {'name': item.name, 'path': str(item), 'type': 'directory' if item.is_dir() else 'file', 'size_bytes': stat.st_size if item.is_file() else 0, 'size_mb': round(stat.st_size / (1024 * 1024), 2) if item.is_file() else 0, 'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(), 'extension': item.suffix.lower() if item.is_file() else '', 'is_hidden': item.name.startswith('.')}
                items.append(item_info)
                if item.is_dir() and current_depth < max_depth:
                    scan_directory(item, current_depth + 1)
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError) as e:
        logger.warning(f'Error scanning directory {current_path}: {str(e)}')

class SupabaseStorageHandler(FileStorageHandler):
    """
    Supabase remote storage implementation.
    Provides file operations via Supabase Storage API with environment-based configuration.
    """

    def __init__(self, bucket_name: str=None, base_path: str='/', **kwargs):
        """
        Initialize Supabase storage handler.
        
        Args:
            bucket_name: Supabase storage bucket name (default: from environment or "default")
            base_path: Base path for storage operations (default: "/")
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(base_path=base_path, **kwargs)
        self.bucket_name = bucket_name or os.getenv('SUPABASE_BUCKET_STORAGE') or 'default'
        self.supabase_url = os.getenv('SUPABASE_URL_STORAGE')
        self.supabase_key = os.getenv('SUPABASE_KEY_STORAGE')
        if not self.supabase_url or not self.supabase_key:
            raise ValueError('Supabase configuration not found in environment variables. Please set SUPABASE_URL/SUPABASE_KEY environment variables.')
        try:
            from supabase import create_client, Client
            logger.info(f'Creating Supabase client with URL: {self.supabase_url[:30]}...')
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info(f'Successfully initialized Supabase client for bucket: {bucket_name}')
        except ImportError:
            raise ImportError('Supabase Python client not installed. Please install it with: pip install supabase')
        except Exception as e:
            logger.error(f'Failed to initialize Supabase client: {str(e)}')
            raise Exception(f'Failed to initialize Supabase client: {str(e)}')
        self._initialize_storage()

    def _initialize_storage(self):
        """Initialize remote storage - verify bucket exists and is accessible"""
        if not hasattr(self, 'bucket_name') or not hasattr(self, 'supabase'):
            return
        try:
            logger.info(f'Testing bucket access for: {self.bucket_name}')
            self.supabase.storage.from_(self.bucket_name).list()
            logger.info(f'Successfully connected to Supabase bucket: {self.bucket_name}')
        except Exception as e:
            logger.warning(f'Could not verify bucket access: {str(e)}')

    def translate_in(self, file_path: str) -> str:
        """Resolve file path for remote storage"""
        if self.base_path == '/':
            return file_path.lstrip('/')
        else:
            return super().translate_in(file_path)

    def _read_raw(self, path: str, **kwargs) -> bytes:
        """Read raw file content from Supabase Storage"""
        try:
            file_path = path.lstrip('/')
            response = self.supabase.storage.from_(self.bucket_name).download(file_path)
            if isinstance(response, bytes):
                return response
            else:
                return bytes(response) if response else b''
        except Exception as e:
            logger.error(f'Error reading file {path} from Supabase: {str(e)}')
            raise

    def _write_raw(self, path: str, content: bytes, **kwargs) -> bool:
        """Write raw file content to Supabase Storage with smart insert/update logic"""
        try:
            file_path = path.lstrip('/')
            file_exists = self._exists_raw(file_path)
            if file_exists:
                logger.info(f'File {file_path} exists, using update method')
                response = self.supabase.storage.from_(self.bucket_name).update(path=file_path, file=content, file_options={'content-type': kwargs.get('content_type', 'application/octet-stream'), 'upsert': 'true'})
            else:
                logger.info(f"File {file_path} doesn't exist, using upload method")
                response = self.supabase.storage.from_(self.bucket_name).upload(path=file_path, file=content, file_options={'content-type': kwargs.get('content_type', 'application/octet-stream')})
            if response and (not isinstance(response, dict) or response.get('error') is None):
                operation = 'updated' if file_exists else 'uploaded'
                logger.info(f'Successfully {operation} file to Supabase: {file_path}')
                return True
            else:
                logger.error(f'Operation failed: {response}')
                return False
        except Exception as e:
            logger.error(f'Error writing file {path} to Supabase: {str(e)}')
            return False

    def _delete_raw(self, path: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            file_path = path.lstrip('/')
            response = self.supabase.storage.from_(self.bucket_name).remove([file_path])
            if response is not None:
                if isinstance(response, list):
                    logger.info(f'Successfully deleted file from Supabase: {file_path}')
                    return True
                elif isinstance(response, dict) and response.get('error') is None:
                    logger.info(f'Successfully deleted file from Supabase: {file_path}')
                    return True
                else:
                    logger.error(f'Deletion failed: {response}')
                    return False
            else:
                logger.error(f'Deletion failed: {response}')
                return False
        except Exception as e:
            logger.error(f'Error deleting {path} from Supabase: {str(e)}')
            return False

    def _list_raw(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> List[Dict[str, Any]]:
        """List files in Supabase Storage"""
        try:
            list_path = (path or self.base_path).lstrip('/')
            response = self.supabase.storage.from_(self.bucket_name).list(list_path)
            items = []
            if response and isinstance(response, list):
                for item in response:
                    if not include_hidden and item.get('name', '').startswith('.'):
                        continue
                    full_path = f'{list_path}/{item['name']}' if list_path else item['name']
                    items.append({'name': item.get('name', ''), 'path': full_path, 'type': 'directory' if item.get('metadata', {}).get('mimetype') == 'application/x-directory' else 'file', 'size_bytes': item.get('metadata', {}).get('size', 0), 'size_mb': round(item.get('metadata', {}).get('size', 0) / (1024 * 1024), 2), 'modified_time': item.get('updated_at', ''), 'extension': Path(item.get('name', '')).suffix.lower(), 'is_hidden': item.get('name', '').startswith('.'), 'mime_type': item.get('metadata', {}).get('mimetype', '')})
            return items
        except Exception as e:
            logger.error(f'Error listing directory {path} from Supabase: {str(e)}')
            return []

    def _exists_raw(self, path: str) -> bool:
        """Check if path exists in Supabase Storage"""
        try:
            file_path = path.lstrip('/')
            parent_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            if not parent_dir:
                parent_dir = ''
            try:
                response = self.supabase.storage.from_(self.bucket_name).list(parent_dir)
                if response and isinstance(response, list):
                    for item in response:
                        if item.get('name') == file_name:
                            return True
                return False
            except Exception as e:
                logger.warning(f'Error listing directory {parent_dir}: {str(e)}')
                return False
        except Exception as e:
            logger.warning(f'Error checking if file {path} exists: {str(e)}')
            return False

    def _create_directory_raw(self, path: str) -> bool:
        """Create directory in Supabase Storage"""
        try:
            dir_path = path.lstrip('/')
            placeholder_content = b'# Directory placeholder'
            placeholder_path = f'{dir_path}/.placeholder'
            response = self.supabase.storage.from_(self.bucket_name).upload(path=placeholder_path, file=placeholder_content, file_options={'content-type': 'text/plain'})
            if response and (not isinstance(response, dict)) or response.get('error') is None:
                return True
            else:
                logger.error(f'Directory creation failed: {response}')
                return False
        except Exception as e:
            logger.error(f'Error creating directory {path} in Supabase: {str(e)}')
            return False

def translate_in(self, file_path: str) -> str:
    """Resolve file path for remote storage"""
    if self.base_path == '/':
        return file_path.lstrip('/')
    else:
        return super().translate_in(file_path)

def _read_raw(self, path: str, **kwargs) -> bytes:
    """Read raw file content from Supabase Storage"""
    try:
        file_path = path.lstrip('/')
        response = self.supabase.storage.from_(self.bucket_name).download(file_path)
        if isinstance(response, bytes):
            return response
        else:
            return bytes(response) if response else b''
    except Exception as e:
        logger.error(f'Error reading file {path} from Supabase: {str(e)}')
        raise

def _write_raw(self, path: str, content: bytes, **kwargs) -> bool:
    """Write raw file content to Supabase Storage with smart insert/update logic"""
    try:
        file_path = path.lstrip('/')
        file_exists = self._exists_raw(file_path)
        if file_exists:
            logger.info(f'File {file_path} exists, using update method')
            response = self.supabase.storage.from_(self.bucket_name).update(path=file_path, file=content, file_options={'content-type': kwargs.get('content_type', 'application/octet-stream'), 'upsert': 'true'})
        else:
            logger.info(f"File {file_path} doesn't exist, using upload method")
            response = self.supabase.storage.from_(self.bucket_name).upload(path=file_path, file=content, file_options={'content-type': kwargs.get('content_type', 'application/octet-stream')})
        if response and (not isinstance(response, dict) or response.get('error') is None):
            operation = 'updated' if file_exists else 'uploaded'
            logger.info(f'Successfully {operation} file to Supabase: {file_path}')
            return True
        else:
            logger.error(f'Operation failed: {response}')
            return False
    except Exception as e:
        logger.error(f'Error writing file {path} to Supabase: {str(e)}')
        return False

def _delete_raw(self, path: str) -> bool:
    """Delete file from Supabase Storage"""
    try:
        file_path = path.lstrip('/')
        response = self.supabase.storage.from_(self.bucket_name).remove([file_path])
        if response is not None:
            if isinstance(response, list):
                logger.info(f'Successfully deleted file from Supabase: {file_path}')
                return True
            elif isinstance(response, dict) and response.get('error') is None:
                logger.info(f'Successfully deleted file from Supabase: {file_path}')
                return True
            else:
                logger.error(f'Deletion failed: {response}')
                return False
        else:
            logger.error(f'Deletion failed: {response}')
            return False
    except Exception as e:
        logger.error(f'Error deleting {path} from Supabase: {str(e)}')
        return False

def _create_directory_raw(self, path: str) -> bool:
    """Create directory in Supabase Storage"""
    try:
        dir_path = path.lstrip('/')
        placeholder_content = b'# Directory placeholder'
        placeholder_path = f'{dir_path}/.placeholder'
        response = self.supabase.storage.from_(self.bucket_name).upload(path=placeholder_path, file=placeholder_content, file_options={'content-type': 'text/plain'})
        if response and (not isinstance(response, dict)) or response.get('error') is None:
            return True
        else:
            logger.error(f'Directory creation failed: {response}')
            return False
    except Exception as e:
        logger.error(f'Error creating directory {path} in Supabase: {str(e)}')
        return False

class SaveTool(Tool):
    name: str = 'save'
    description: str = 'Save content to a file with automatic format detection and support for various file types including documents, data files, images, videos, and sound files'
    inputs: Dict[str, Dict[str, str]] = {'file_path': {'type': 'string', 'description': 'Path to the file to save'}, 'content': {'type': 'string', 'description': 'Content to save to the file (string for text, JSON string for structured data, or Python object for JSON files)'}, 'encoding': {'type': 'string', 'description': 'Text encoding for text files (default: utf-8)'}, 'indent': {'type': 'integer', 'description': 'Indentation for JSON files (default: 2)'}, 'sheet_name': {'type': 'string', 'description': 'Sheet name for Excel files (default: Sheet1)'}, 'root_tag': {'type': 'string', 'description': 'Root tag for XML files (default: root)'}}
    required: Optional[List[str]] = ['file_path', 'content']

    def __init__(self, storage_handler: FileStorageHandler=None):
        super().__init__()
        self.storage_handler = storage_handler or LocalStorageHandler()

    @classmethod
    def validate_attributes(cls):
        pass

    def __call__(self, file_path: str, content: Any, encoding: str='utf-8', indent: int=2, sheet_name: str='Sheet1', root_tag: str='root') -> Dict[str, Any]:
        """
        Save content to a file with automatic format detection.
        
        Args:
            file_path: Path to the file to save
            content: Content to save to the file (string for text, dict/list for JSON, list for CSV/Excel)
            encoding: Text encoding for text files
            indent: Indentation for JSON files
            sheet_name: Sheet name for Excel files
            root_tag: Root tag for XML files
            
        Returns:
            Dictionary containing the save operation result
        """
        try:
            file_extension = self.storage_handler.get_file_type(file_path)
            parsed_content = content
            if file_extension in ['.json', '.yaml', '.yml', '.xml']:
                if isinstance(content, str):
                    try:
                        import json
                        parsed_content = json.loads(content)
                    except json.JSONDecodeError:
                        parsed_content = content
                else:
                    parsed_content = content
            elif file_extension == '.csv':
                if isinstance(content, list):
                    parsed_content = content
                else:
                    try:
                        import json
                        parsed_content = json.loads(content)
                        if not isinstance(parsed_content, list):
                            parsed_content = content
                    except json.JSONDecodeError:
                        parsed_content = content
            elif file_extension == '.xlsx':
                if isinstance(content, list):
                    parsed_content = content
                else:
                    try:
                        import json
                        parsed_content = json.loads(content)
                        if not isinstance(parsed_content, list):
                            return {'success': False, 'error': 'Excel content must be a list of lists'}
                    except json.JSONDecodeError:
                        return {'success': False, 'error': 'Excel content must be valid JSON array'}
            kwargs = {'encoding': encoding, 'indent': indent, 'sheet_name': sheet_name, 'root_tag': root_tag}
            result = self.storage_handler.save(file_path, parsed_content, **kwargs)
            return result
        except Exception as e:
            logger.error(f'Error in SaveTool: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

def __call__(self, file_path: str, content: Any, encoding: str='utf-8', indent: int=2, sheet_name: str='Sheet1', root_tag: str='root') -> Dict[str, Any]:
    """
        Save content to a file with automatic format detection.
        
        Args:
            file_path: Path to the file to save
            content: Content to save to the file (string for text, dict/list for JSON, list for CSV/Excel)
            encoding: Text encoding for text files
            indent: Indentation for JSON files
            sheet_name: Sheet name for Excel files
            root_tag: Root tag for XML files
            
        Returns:
            Dictionary containing the save operation result
        """
    try:
        file_extension = self.storage_handler.get_file_type(file_path)
        parsed_content = content
        if file_extension in ['.json', '.yaml', '.yml', '.xml']:
            if isinstance(content, str):
                try:
                    import json
                    parsed_content = json.loads(content)
                except json.JSONDecodeError:
                    parsed_content = content
            else:
                parsed_content = content
        elif file_extension == '.csv':
            if isinstance(content, list):
                parsed_content = content
            else:
                try:
                    import json
                    parsed_content = json.loads(content)
                    if not isinstance(parsed_content, list):
                        parsed_content = content
                except json.JSONDecodeError:
                    parsed_content = content
        elif file_extension == '.xlsx':
            if isinstance(content, list):
                parsed_content = content
            else:
                try:
                    import json
                    parsed_content = json.loads(content)
                    if not isinstance(parsed_content, list):
                        return {'success': False, 'error': 'Excel content must be a list of lists'}
                except json.JSONDecodeError:
                    return {'success': False, 'error': 'Excel content must be valid JSON array'}
        kwargs = {'encoding': encoding, 'indent': indent, 'sheet_name': sheet_name, 'root_tag': root_tag}
        result = self.storage_handler.save(file_path, parsed_content, **kwargs)
        return result
    except Exception as e:
        logger.error(f'Error in SaveTool: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

class ReadTool(Tool):
    name: str = 'read'
    description: str = 'Read content from a file with automatic format detection and support for various file types including documents, data files, images, videos, and sound files'
    inputs: Dict[str, Dict[str, str]] = {'file_path': {'type': 'string', 'description': 'Path to the file to read'}, 'encoding': {'type': 'string', 'description': 'Text encoding for text files (default: utf-8)'}, 'sheet_name': {'type': 'string', 'description': 'Sheet name for Excel files (optional)'}, 'head': {'type': 'integer', 'description': 'Number of characters to return from the beginning of the file (default: 0 means return everything)'}}
    required: Optional[List[str]] = ['file_path']

    def __init__(self, storage_handler: FileStorageHandler=None):
        super().__init__()
        self.storage_handler = storage_handler or LocalStorageHandler()

    def __call__(self, file_path: str, encoding: str='utf-8', sheet_name: str=None, head: int=0) -> Dict[str, Any]:
        """
        Read content from a file with automatic format detection.
        
        Args:
            file_path: Path to the file to read
            encoding: Text encoding for text files
            sheet_name: Sheet name for Excel files
            head: Number of characters to return from the beginning
            
        Returns:
            Dictionary containing the read operation result
        """
        try:
            kwargs = {'encoding': encoding, 'sheet_name': sheet_name, 'head': head}
            result = self.storage_handler.read(file_path, **kwargs)
            return result
        except Exception as e:
            logger.error(f'Error in ReadTool: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

def __call__(self, file_path: str, encoding: str='utf-8', sheet_name: str=None, head: int=0) -> Dict[str, Any]:
    """
        Read content from a file with automatic format detection.
        
        Args:
            file_path: Path to the file to read
            encoding: Text encoding for text files
            sheet_name: Sheet name for Excel files
            head: Number of characters to return from the beginning
            
        Returns:
            Dictionary containing the read operation result
        """
    try:
        kwargs = {'encoding': encoding, 'sheet_name': sheet_name, 'head': head}
        result = self.storage_handler.read(file_path, **kwargs)
        return result
    except Exception as e:
        logger.error(f'Error in ReadTool: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

class AppendTool(Tool):
    name: str = 'append'
    description: str = 'Append content to a file (only for supported formats: txt, json, csv, yaml, pickle, xlsx)'
    inputs: Dict[str, Dict[str, str]] = {'file_path': {'type': 'string', 'description': 'Path to the file to append to'}, 'content': {'type': 'string', 'description': 'Content to append to the file (can be JSON string for structured data)'}, 'encoding': {'type': 'string', 'description': 'Text encoding for text files (default: utf-8)'}, 'sheet_name': {'type': 'string', 'description': 'Sheet name for Excel files (optional)'}}
    required: Optional[List[str]] = ['file_path', 'content']

    def __init__(self, storage_handler: FileStorageHandler=None):
        super().__init__()
        self.storage_handler = storage_handler or LocalStorageHandler()

    def __call__(self, file_path: str, content: str, encoding: str='utf-8', sheet_name: str=None) -> Dict[str, Any]:
        """
        Append content to a file with automatic format detection.
        
        Args:
            file_path: Path to the file to append to
            content: Content to append to the file
            encoding: Text encoding for text files
            sheet_name: Sheet name for Excel files
            
        Returns:
            Dictionary containing the append operation result
        """
        try:
            file_extension = self.storage_handler.get_file_type(file_path)
            parsed_content = content
            if file_extension in ['.json', '.yaml', '.yml']:
                try:
                    import json
                    parsed_content = json.loads(content)
                except json.JSONDecodeError:
                    parsed_content = content
            elif file_extension == '.csv':
                try:
                    import json
                    parsed_content = json.loads(content)
                    if not isinstance(parsed_content, list):
                        parsed_content = content
                except json.JSONDecodeError:
                    parsed_content = content
            elif file_extension == '.xlsx':
                try:
                    import json
                    parsed_content = json.loads(content)
                    if not isinstance(parsed_content, list):
                        return {'success': False, 'error': 'Excel content must be a list of lists'}
                except json.JSONDecodeError:
                    return {'success': False, 'error': 'Excel content must be valid JSON array'}
            kwargs = {'encoding': encoding, 'sheet_name': sheet_name}
            result = self.storage_handler.append(file_path, parsed_content, **kwargs)
            return result
        except Exception as e:
            logger.error(f'Error in AppendTool: {str(e)}')
            return {'success': False, 'error': str(e), 'file_path': file_path}

def __call__(self, file_path: str, content: str, encoding: str='utf-8', sheet_name: str=None) -> Dict[str, Any]:
    """
        Append content to a file with automatic format detection.
        
        Args:
            file_path: Path to the file to append to
            content: Content to append to the file
            encoding: Text encoding for text files
            sheet_name: Sheet name for Excel files
            
        Returns:
            Dictionary containing the append operation result
        """
    try:
        file_extension = self.storage_handler.get_file_type(file_path)
        parsed_content = content
        if file_extension in ['.json', '.yaml', '.yml']:
            try:
                import json
                parsed_content = json.loads(content)
            except json.JSONDecodeError:
                parsed_content = content
        elif file_extension == '.csv':
            try:
                import json
                parsed_content = json.loads(content)
                if not isinstance(parsed_content, list):
                    parsed_content = content
            except json.JSONDecodeError:
                parsed_content = content
        elif file_extension == '.xlsx':
            try:
                import json
                parsed_content = json.loads(content)
                if not isinstance(parsed_content, list):
                    return {'success': False, 'error': 'Excel content must be a list of lists'}
            except json.JSONDecodeError:
                return {'success': False, 'error': 'Excel content must be valid JSON array'}
        kwargs = {'encoding': encoding, 'sheet_name': sheet_name}
        result = self.storage_handler.append(file_path, parsed_content, **kwargs)
        return result
    except Exception as e:
        logger.error(f'Error in AppendTool: {str(e)}')
        return {'success': False, 'error': str(e), 'file_path': file_path}

class MoveTool(Tool):
    name: str = 'move'
    description: str = 'Move or rename a file or directory'
    inputs: Dict[str, Dict[str, str]] = {'source': {'type': 'string', 'description': 'Source path of the file or directory to move'}, 'destination': {'type': 'string', 'description': 'Destination path where to move the file or directory'}}
    required: Optional[List[str]] = ['source', 'destination']

    def __init__(self, storage_handler: FileStorageHandler=None):
        super().__init__()
        self.storage_handler = storage_handler or LocalStorageHandler()

    def __call__(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Move or rename a file or directory.
        
        Args:
            source: Source path of the file or directory to move
            destination: Destination path where to move the file or directory
            
        Returns:
            Dictionary containing the move operation result
        """
        try:
            result = self.storage_handler.move(source, destination)
            return result
        except Exception as e:
            logger.error(f'Error in MoveTool: {str(e)}')
            return {'success': False, 'error': str(e), 'source': source, 'destination': destination}

def __call__(self, source: str, destination: str) -> Dict[str, Any]:
    """
        Move or rename a file or directory.
        
        Args:
            source: Source path of the file or directory to move
            destination: Destination path where to move the file or directory
            
        Returns:
            Dictionary containing the move operation result
        """
    try:
        result = self.storage_handler.move(source, destination)
        return result
    except Exception as e:
        logger.error(f'Error in MoveTool: {str(e)}')
        return {'success': False, 'error': str(e), 'source': source, 'destination': destination}

class CopyTool(Tool):
    name: str = 'copy'
    description: str = 'Copy a file'
    inputs: Dict[str, Dict[str, str]] = {'source': {'type': 'string', 'description': 'Source path of the file to copy'}, 'destination': {'type': 'string', 'description': 'Destination path where to copy the file'}}
    required: Optional[List[str]] = ['source', 'destination']

    def __init__(self, storage_handler: FileStorageHandler=None):
        super().__init__()
        self.storage_handler = storage_handler or LocalStorageHandler()

    def __call__(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a file.
        
        Args:
            source: Source path of the file to copy
            destination: Destination path where to copy the file
            
        Returns:
            Dictionary containing the copy operation result
        """
        try:
            result = self.storage_handler.copy(source, destination)
            return result
        except Exception as e:
            logger.error(f'Error in CopyTool: {str(e)}')
            return {'success': False, 'error': str(e), 'source': source, 'destination': destination}

def __call__(self, source: str, destination: str) -> Dict[str, Any]:
    """
        Copy a file.
        
        Args:
            source: Source path of the file to copy
            destination: Destination path where to copy the file
            
        Returns:
            Dictionary containing the copy operation result
        """
    try:
        result = self.storage_handler.copy(source, destination)
        return result
    except Exception as e:
        logger.error(f'Error in CopyTool: {str(e)}')
        return {'success': False, 'error': str(e), 'source': source, 'destination': destination}

class CreateDirectoryTool(Tool):
    name: str = 'create_directory'
    description: str = 'Create a directory'
    inputs: Dict[str, Dict[str, str]] = {'path': {'type': 'string', 'description': 'Path of the directory to create'}}
    required: Optional[List[str]] = ['path']

    def __init__(self, storage_handler: FileStorageHandler=None):
        super().__init__()
        self.storage_handler = storage_handler or LocalStorageHandler()

    def __call__(self, path: str) -> Dict[str, Any]:
        """
        Create a directory.
        
        Args:
            path: Path of the directory to create
            
        Returns:
            Dictionary containing the create directory operation result
        """
        try:
            result = self.storage_handler.create_directory(path)
            return result
        except Exception as e:
            logger.error(f'Error in CreateDirectoryTool: {str(e)}')
            return {'success': False, 'error': str(e), 'path': path}

def __call__(self, path: str) -> Dict[str, Any]:
    """
        Create a directory.
        
        Args:
            path: Path of the directory to create
            
        Returns:
            Dictionary containing the create directory operation result
        """
    try:
        result = self.storage_handler.create_directory(path)
        return result
    except Exception as e:
        logger.error(f'Error in CreateDirectoryTool: {str(e)}')
        return {'success': False, 'error': str(e), 'path': path}

class ListFileTool(Tool):
    name: str = 'list_files'
    description: str = 'List files and directories in a path with structured information'
    inputs: Dict[str, Dict[str, str]] = {'path': {'type': 'string', 'description': 'Path to list files from (default: current working directory)'}, 'max_depth': {'type': 'integer', 'description': 'Maximum depth to traverse (default: 3)'}, 'include_hidden': {'type': 'boolean', 'description': 'Include hidden files and directories (default: false)'}}
    required: Optional[List[str]] = []

    def __init__(self, storage_handler: FileStorageHandler=None):
        super().__init__()
        self.storage_handler = storage_handler or LocalStorageHandler()

    def __call__(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
        """
        List files and directories in a path.
        
        Args:
            path: Path to list files from
            max_depth: Maximum depth to traverse
            include_hidden: Include hidden files and directories
            
        Returns:
            Dictionary containing the list operation result
        """
        try:
            result = self.storage_handler.list(path, max_depth=max_depth, include_hidden=include_hidden)
            return result
        except Exception as e:
            logger.error(f'Error in ListFileTool: {str(e)}')
            return {'success': False, 'error': str(e), 'path': path}

def __call__(self, path: str=None, max_depth: int=3, include_hidden: bool=False) -> Dict[str, Any]:
    """
        List files and directories in a path.
        
        Args:
            path: Path to list files from
            max_depth: Maximum depth to traverse
            include_hidden: Include hidden files and directories
            
        Returns:
            Dictionary containing the list operation result
        """
    try:
        result = self.storage_handler.list(path, max_depth=max_depth, include_hidden=include_hidden)
        return result
    except Exception as e:
        logger.error(f'Error in ListFileTool: {str(e)}')
        return {'success': False, 'error': str(e), 'path': path}

class ExistsTool(Tool):
    name: str = 'exists'
    description: str = 'Check if a file or directory exists'
    inputs: Dict[str, Dict[str, str]] = {'path': {'type': 'string', 'description': 'Path to check for existence'}}
    required: Optional[List[str]] = ['path']

    def __init__(self, storage_handler: FileStorageHandler=None):
        super().__init__()
        self.storage_handler = storage_handler or LocalStorageHandler()

    def __call__(self, path: str) -> Dict[str, Any]:
        """
        Check if a file or directory exists.
        
        Args:
            path: Path to check for existence
            
        Returns:
            Dictionary containing the existence check result
        """
        try:
            exists = self.storage_handler.exists(path)
            return {'success': True, 'path': path, 'exists': exists}
        except Exception as e:
            logger.error(f'Error in ExistsTool: {str(e)}')
            return {'success': False, 'error': str(e), 'path': path}

def __call__(self, path: str) -> Dict[str, Any]:
    """
        Check if a file or directory exists.
        
        Args:
            path: Path to check for existence
            
        Returns:
            Dictionary containing the existence check result
        """
    try:
        exists = self.storage_handler.exists(path)
        return {'success': True, 'path': path, 'exists': exists}
    except Exception as e:
        logger.error(f'Error in ExistsTool: {str(e)}')
        return {'success': False, 'error': str(e), 'path': path}

class GoogleSearchTool(Tool):
    name: str = 'google_search'
    description: str = 'Search Google using the Custom Search API and retrieve content from search results'
    inputs: Dict[str, Dict[str, str]] = {'query': {'type': 'string', 'description': 'The search query to execute on Google'}, 'num_search_pages': {'type': 'integer', 'description': 'Number of search results to retrieve. Default: 5'}, 'max_content_words': {'type': 'integer', 'description': 'Maximum number of words to include in content per result. None means no limit. Default: None'}}
    required: Optional[List[str]] = ['query']

    def __init__(self, search_google: SearchGoogle=None):
        super().__init__()
        self.search_google = search_google

    def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None) -> Dict[str, Any]:
        """Execute Google search using the SearchGoogle instance."""
        if not self.search_google:
            raise RuntimeError('Google search instance not initialized')
        try:
            return self.search_google.search(query, num_search_pages, max_content_words)
        except Exception as e:
            return {'results': [], 'error': f'Error executing Google search: {str(e)}'}

def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None) -> Dict[str, Any]:
    """Execute Google search using the SearchGoogle instance."""
    if not self.search_google:
        raise RuntimeError('Google search instance not initialized')
    try:
        return self.search_google.search(query, num_search_pages, max_content_words)
    except Exception as e:
        return {'results': [], 'error': f'Error executing Google search: {str(e)}'}

class SerperAPITool(Tool):
    name: str = 'serperapi_search'
    description: str = 'Search Google using SerperAPI with comprehensive result processing and content scraping'
    inputs: Dict[str, Dict[str, str]] = {'query': {'type': 'string', 'description': 'The search query to execute'}, 'num_search_pages': {'type': 'integer', 'description': 'Number of search results to retrieve. Default: 10'}, 'max_content_words': {'type': 'integer', 'description': 'Maximum number of words to include in content per result. None means no limit. Default: None'}, 'location': {'type': 'string', 'description': "Geographic location for localized results (e.g., 'New York, NY', 'London, UK')"}, 'language': {'type': 'string', 'description': "Interface language code (e.g., 'en', 'es', 'fr', 'de'). Default: en"}, 'country': {'type': 'string', 'description': "Country code for country-specific results (e.g., 'us', 'uk', 'ca'). Default: us"}}
    required: Optional[List[str]] = ['query']

    def __init__(self, search_serperapi: SearchSerperAPI=None):
        super().__init__()
        self.search_serperapi = search_serperapi

    def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None, location: str=None, language: str=None, country: str=None) -> Dict[str, Any]:
        """Execute SerperAPI search using the SearchSerperAPI instance."""
        if not self.search_serperapi:
            raise RuntimeError('SerperAPI search instance not initialized')
        try:
            return self.search_serperapi.search(query=query, num_search_pages=num_search_pages, max_content_words=max_content_words, location=location, language=language, country=country)
        except Exception as e:
            return {'results': [], 'error': f'Error executing SerperAPI search: {str(e)}'}

def __call__(self, query: str, num_search_pages: int=None, max_content_words: int=None, location: str=None, language: str=None, country: str=None) -> Dict[str, Any]:
    """Execute SerperAPI search using the SearchSerperAPI instance."""
    if not self.search_serperapi:
        raise RuntimeError('SerperAPI search instance not initialized')
    try:
        return self.search_serperapi.search(query=query, num_search_pages=num_search_pages, max_content_words=max_content_words, location=location, language=language, country=country)
    except Exception as e:
        return {'results': [], 'error': f'Error executing SerperAPI search: {str(e)}'}

class TelegramBase(BaseModule):
    """
    Base class for Telegram API interactions.
    Handles client management, authentication, and common utilities.
    """

    def __init__(self, api_id: str=None, api_hash: str=None, phone: str=None, **kwargs):
        """
        Initialize the Telegram base.
        
        Args:
            api_id (str, optional): Telegram API ID. If not provided, will try to get from TELEGRAM_API_ID environment variable.
            api_hash (str, optional): Telegram API Hash. If not provided, will try to get from TELEGRAM_API_HASH environment variable.
            phone (str, optional): Phone number for authentication. If not provided, will try to get from TELEGRAM_PHONE environment variable.
            **kwargs: Additional keyword arguments for parent class
        """
        super().__init__(**kwargs)
        self.api_id = api_id or os.getenv('TELEGRAM_API_ID')
        self.api_hash = api_hash or os.getenv('TELEGRAM_API_HASH')
        self.phone = phone or os.getenv('TELEGRAM_PHONE')
        if not self.api_id or not self.api_hash:
            logger.warning('No Telegram API credentials provided. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables or pass api_id and api_hash parameters. Get your credentials from: https://my.telegram.org/apps')

    def _get_client(self) -> TelegramClient:
        """
        Create and return a Telegram client instance.
        
        Returns:
            TelegramClient: Configured Telegram client
        """
        if not self.api_id or not self.api_hash:
            raise ValueError('Telegram API credentials not found. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables.')
        client = TelegramClient(SESSION_NAME, self.api_id, self.api_hash)
        return client

    def _format_message(self, message: Message) -> Dict[str, Any]:
        """
        Format a Telegram message for consistent output.
        
        Args:
            message: Telegram message object
            
        Returns:
            dict: Formatted message data
        """
        return {'id': message.id, 'text': message.text or '', 'date': message.date.isoformat() if message.date else None, 'sender_id': message.sender_id, 'chat_id': message.chat_id, 'is_reply': message.reply_to_msg_id is not None, 'reply_to_msg_id': message.reply_to_msg_id, 'has_media': message.media is not None, 'media_type': type(message.media).__name__ if message.media else None}

    def _format_chat(self, chat) -> Dict[str, Any]:
        """
        Format a Telegram chat for consistent output.
        
        Args:
            chat: Telegram chat object
            
        Returns:
            dict: Formatted chat data
        """
        chat_type = 'unknown'
        title = 'Unknown'
        if isinstance(chat, User):
            chat_type = 'user'
            title = f'{chat.first_name or ''} {chat.last_name or ''}'.strip() or chat.username or 'Unknown User'
        elif isinstance(chat, Chat):
            chat_type = 'group'
            title = chat.title or 'Unknown Group'
        elif isinstance(chat, Channel):
            chat_type = 'channel' if chat.broadcast else 'supergroup'
            title = chat.title or 'Unknown Channel'
        return {'id': chat.id, 'title': title, 'type': chat_type, 'username': getattr(chat, 'username', None)}

    def _run_async(self, coro):
        """
        Run an async coroutine, handling both sync and async contexts.
        
        Args:
            coro: Async coroutine to run
            
        Returns:
            Result of the coroutine
        """
        try:
            try:
                asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            except RuntimeError:
                return asyncio.run(coro)
        except Exception as e:
            return {'success': False, 'error': f'Failed to execute async operation: {str(e)}'}

def _run_async(self, coro):
    """
        Run an async coroutine, handling both sync and async contexts.
        
        Args:
            coro: Async coroutine to run
            
        Returns:
            Result of the coroutine
        """
    try:
        try:
            asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            return asyncio.run(coro)
    except Exception as e:
        return {'success': False, 'error': f'Failed to execute async operation: {str(e)}'}

def ensure_dir(path: str, storage_handler: Optional[FileStorageHandler]=None):
    """Ensure directory exists using storage handler or fallback to direct I/O"""
    if path:
        if storage_handler:
            storage_handler.create_directory(path)
        else:
            os.makedirs(path, exist_ok=True)

def file_to_base64(path: str, storage_handler: Optional[FileStorageHandler]=None) -> str:
    """Convert file to base64 using storage handler"""
    if storage_handler is None:
        storage_handler = LocalStorageHandler()
    result = storage_handler.read(path)
    if result['success']:
        if isinstance(result['content'], bytes):
            return base64.b64encode(result['content']).decode('utf-8')
        else:
            return base64.b64encode(str(result['content']).encode('utf-8')).decode('utf-8')
    else:
        raise FileNotFoundError(f'Could not read file {path}: {result.get('error', 'Unknown error')}')

def file_to_base64_legacy(path: str) -> str:
    """Legacy function for backward compatibility - uses direct file I/O"""
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

class OpenRouterImageGenerationEditTool(Tool):
    name: str = 'openrouter_image_generation_edit'
    description: str = 'Text-to-image and image-editing via OpenRouter models (e.g., google/gemini-2.5-flash-image-preview). No images → generate; with images (URLs or local paths) → edit/compose.'
    inputs: Dict[str, Dict] = {'prompt': {'type': 'string', 'description': 'Text prompt.'}, 'image_urls': {'type': 'array', 'description': 'Remote image URLs (optional).'}, 'image_paths': {'type': 'array', 'description': 'Local image paths (optional).'}, 'model': {'type': 'string', 'description': 'OpenRouter model id.', 'default': 'google/gemini-2.5-flash-image-preview'}, 'api_key': {'type': 'string', 'description': 'OpenRouter API key (fallback to env OPENROUTER_API_KEY).'}, 'save_path': {'type': 'string', 'description': 'Directory to save images (when data URLs).', 'default': './openrouter_images'}, 'output_basename': {'type': 'string', 'description': 'Base filename for outputs.', 'default': 'or_gen'}}
    required: List[str] = ['prompt']

    def __init__(self, api_key: str=None, storage_handler: Optional[FileStorageHandler]=None, base_path: str='./openrouter_images'):
        super().__init__()
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.storage_handler = storage_handler or LocalStorageHandler(base_path=base_path)

    def __call__(self, prompt: str, image_urls: list=None, image_paths: list=None, model: str='google/gemini-2.5-flash-image-preview', api_key: str=None, save_path: str='./openrouter_images', output_basename: str='or_gen'):
        key = api_key or self.api_key
        if not key:
            return {'error': 'OPENROUTER_API_KEY not provided.'}
        messages = [{'role': 'user', 'content': prompt}]
        payload = {'model': model, 'messages': messages, 'modalities': ['image', 'text']}
        content_parts = [{'type': 'text', 'text': prompt}]
        if image_urls:
            content_parts.extend(self._urls_to_image_parts(image_urls))
        if image_paths:
            content_parts.extend(self._paths_to_image_parts(image_paths))
        if len(content_parts) > 1:
            payload['messages'][0] = {'role': 'user', 'content': content_parts}
        headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
        url = 'https://openrouter.ai/api/v1/chat/completions'
        try:
            resp = requests.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = resp.json()
                return {'error': f'OpenRouter API error: {error_data}', 'status_code': resp.status_code}
            except Exception:
                return {'error': f'OpenRouter API error: {e}', 'status_code': resp.status_code}
        except Exception as e:
            return {'error': f'Request failed: {e}'}
        saved_paths: List[str] = []
        if data.get('choices'):
            msg = data['choices'][0]['message']
            images = msg.get('images') or []
            for im in images:
                image_url = im.get('image_url', {}).get('url')
                if not image_url:
                    continue
                if image_url.startswith('data:') and ',' in image_url:
                    import base64
                    header, b64data = image_url.split(',', 1)
                    mime = 'image/png'
                    if ';' in header:
                        mime = header.split(':', 1)[1].split(';', 1)[0] or mime
                    ext = '.png'
                    if mime == 'image/jpeg':
                        ext = '.jpg'
                    elif mime == 'image/webp':
                        ext = '.webp'
                    elif mime == 'image/heic':
                        ext = '.heic'
                    elif mime == 'image/heif':
                        ext = '.heif'
                    filename = self._get_unique_filename(output_basename or 'or_gen', ext)
                    image_content = base64.b64decode(b64data)
                    result = self.storage_handler.save(filename, image_content)
                    if result['success']:
                        saved_paths.append(filename)
                    else:
                        return {'error': f'Failed to save image: {result.get('error', 'Unknown error')}'}
        if saved_paths:
            return {'saved_paths': saved_paths}
        return {'warning': 'No image returned or saved.', 'raw': data}

    def _url_to_image_part(self, url: str) -> Dict:
        return {'type': 'image_url', 'image_url': {'url': url}}

    def _guess_mime_from_name(self, name: str, default: str='image/png') -> str:
        import mimetypes
        guess, _ = mimetypes.guess_type(name)
        return guess or default

    def _path_to_data_url(self, path: str) -> str:
        import base64
        mime = self._guess_mime_from_name(path)
        try:
            system_path = self.storage_handler.translate_in(path)
            content = self.storage_handler._read_raw(system_path)
        except Exception as e:
            raise FileNotFoundError(f'Could not read file {path}: {str(e)}')
        b64 = base64.b64encode(content).decode('utf-8')
        return f'data:{mime};base64,{b64}'

    def _get_unique_filename(self, base_name: str, extension: str) -> str:
        """Generate a unique filename for the image"""
        filename = f'{base_name}{extension}'
        counter = 1
        while self.storage_handler.exists(filename):
            filename = f'{base_name}_{counter}{extension}'
            counter += 1
        return filename

    def _paths_to_image_parts(self, paths: list) -> List[Dict]:
        parts: List[Dict] = []
        for p in paths:
            try:
                parts.append(self._url_to_image_part(self._path_to_data_url(p)))
            except Exception:
                continue
        return parts

    def _urls_to_image_parts(self, urls: list) -> List[Dict]:
        return [self._url_to_image_part(u) for u in urls]

def _guess_mime_from_name(self, name: str, default: str='image/png') -> str:
    import mimetypes
    guess, _ = mimetypes.guess_type(name)
    return guess or default

def _path_to_data_url(self, path: str) -> str:
    import base64
    mime = self._guess_mime_from_name(path)
    try:
        system_path = self.storage_handler.translate_in(path)
        content = self.storage_handler._read_raw(system_path)
    except Exception as e:
        raise FileNotFoundError(f'Could not read file {path}: {str(e)}')
    b64 = base64.b64encode(content).decode('utf-8')
    return f'data:{mime};base64,{b64}'

class ImageAnalysisTool(Tool):
    name: str = 'image_analysis'
    description: str = 'Analyze and understand images and PDF documents using a multimodal LLM (via OpenRouter). Supports image URLs, local image files, and local PDF files.'
    inputs: Dict[str, Dict[str, str]] = {'prompt': {'type': 'string', 'description': 'Question or instruction for image/PDF analysis.'}, 'image_url': {'type': 'string', 'description': 'URL of the image (optional).'}, 'image_path': {'type': 'string', 'description': 'Local image file path (optional).'}, 'pdf_path': {'type': 'string', 'description': 'Local PDF file path (optional).'}}
    required: Optional[List[str]] = ['prompt']

    def __init__(self, api_key, model='openai/gpt-4o', storage_handler: Optional[FileStorageHandler]=None):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.storage_handler = storage_handler or LocalStorageHandler()

    def __call__(self, prompt: str, image_url: str=None, image_path: str=None, pdf_path: str=None):
        messages = [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}]
        if image_url:
            messages[0]['content'].append({'type': 'image_url', 'image_url': {'url': image_url}})
        elif image_path:
            try:
                result = self.storage_handler.read(image_path)
                if not result['success']:
                    return {'error': f'Failed to read image: {result.get('error', 'Unknown error')}'}
                if isinstance(result['content'], bytes):
                    image_content = result['content']
                else:
                    image_content = str(result['content']).encode('utf-8')
                base64_image = base64.b64encode(image_content).decode('utf-8')
            except Exception as e:
                return {'error': f'Failed to read image: {e}'}
            data_url = f'data:image/jpeg;base64,{base64_image}'
            messages[0]['content'].append({'type': 'image_url', 'image_url': {'url': data_url}})
        elif pdf_path:
            try:
                result = self.storage_handler.read(pdf_path)
                if not result['success']:
                    return {'error': f'Failed to read PDF: {result.get('error', 'Unknown error')}'}
                if isinstance(result['content'], bytes):
                    pdf_content = result['content']
                else:
                    pdf_content = str(result['content']).encode('utf-8')
                base64_pdf = base64.b64encode(pdf_content).decode('utf-8')
            except Exception as e:
                return {'error': f'Failed to read PDF: {e}'}
            data_url = f'data:application/pdf;base64,{base64_pdf}'
            messages[0]['content'].append({'type': 'file', 'file': {'filename': pdf_path.split('/')[-1], 'file_data': data_url}})
        payload = {'model': self.model, 'messages': messages}
        url = 'https://openrouter.ai/api/v1/chat/completions'
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, json=payload)
        try:
            data = response.json()
            result = {'content': data.get('choices', [{}])[0].get('message', {}).get('content', ''), 'usage': data.get('usage', {})}
            return result
        except Exception as e:
            return {'error': f'Failed to parse OpenRouter response: {e}', 'raw': response.text}

def __call__(self, prompt: str, image_url: str=None, image_path: str=None, pdf_path: str=None):
    messages = [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}]
    if image_url:
        messages[0]['content'].append({'type': 'image_url', 'image_url': {'url': image_url}})
    elif image_path:
        try:
            result = self.storage_handler.read(image_path)
            if not result['success']:
                return {'error': f'Failed to read image: {result.get('error', 'Unknown error')}'}
            if isinstance(result['content'], bytes):
                image_content = result['content']
            else:
                image_content = str(result['content']).encode('utf-8')
            base64_image = base64.b64encode(image_content).decode('utf-8')
        except Exception as e:
            return {'error': f'Failed to read image: {e}'}
        data_url = f'data:image/jpeg;base64,{base64_image}'
        messages[0]['content'].append({'type': 'image_url', 'image_url': {'url': data_url}})
    elif pdf_path:
        try:
            result = self.storage_handler.read(pdf_path)
            if not result['success']:
                return {'error': f'Failed to read PDF: {result.get('error', 'Unknown error')}'}
            if isinstance(result['content'], bytes):
                pdf_content = result['content']
            else:
                pdf_content = str(result['content']).encode('utf-8')
            base64_pdf = base64.b64encode(pdf_content).decode('utf-8')
        except Exception as e:
            return {'error': f'Failed to read PDF: {e}'}
        data_url = f'data:application/pdf;base64,{base64_pdf}'
        messages[0]['content'].append({'type': 'file', 'file': {'filename': pdf_path.split('/')[-1], 'file_data': data_url}})
    payload = {'model': self.model, 'messages': messages}
    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, json=payload)
    try:
        data = response.json()
        result = {'content': data.get('choices', [{}])[0].get('message', {}).get('content', ''), 'usage': data.get('usage', {})}
        return result
    except Exception as e:
        return {'error': f'Failed to parse OpenRouter response: {e}', 'raw': response.text}

class OpenAIImageAnalysisTool(Tool):
    name: str = 'openai_image_analysis'
    description: str = 'Simple image analysis via OpenAI Responses API (input_text + input_image).'
    inputs: Dict[str, Dict[str, str]] = {'prompt': {'type': 'string', 'description': 'User question/instruction. Required.'}, 'image_url': {'type': 'string', 'description': 'HTTP(S) image URL. Optional if image_path provided.'}, 'image_path': {'type': 'string', 'description': 'Local image path; converted to data URL internally.'}, 'model': {'type': 'string', 'description': 'OpenAI model for responses.create (e.g., gpt-4o-mini, gpt-4.1, gpt-5). Optional.'}}
    required: Optional[List[str]] = ['prompt']

    def __init__(self, api_key: str, organization_id: str=None, model: str='gpt-4o-mini', storage_handler: Optional[FileStorageHandler]=None):
        super().__init__()
        self.api_key = api_key
        self.organization_id = organization_id
        self.model = model
        self.storage_handler = storage_handler or LocalStorageHandler()

    def __call__(self, prompt: str, image_url: str=None, image_path: str=None, model: str=None):
        try:
            client = create_openai_client(self.api_key, self.organization_id)
            actual_model = model if model else self.model
            final_image_url = image_url
            if not final_image_url and image_path:
                import base64
                import mimetypes
                mime, _ = mimetypes.guess_type(image_path)
                mime = mime or 'image/png'
                try:
                    system_path = self.storage_handler.translate_in(image_path)
                    content = self.storage_handler._read_raw(system_path)
                except Exception as e:
                    return {'error': f'Could not read image {image_path}: {str(e)}'}
                b64 = base64.b64encode(content).decode('utf-8')
                final_image_url = f'data:{mime};base64,{b64}'
            response = client.responses.create(model=actual_model, input=[{'role': 'user', 'content': [{'type': 'input_text', 'text': prompt}, {'type': 'input_image', 'image_url': final_image_url}]}])
            text = getattr(response, 'output_text', None)
            if text is None:
                try:
                    choices = getattr(response, 'output', None) or getattr(response, 'choices', None)
                    if choices and isinstance(choices, list):
                        first = choices[0]
                        text = getattr(first, 'message', {}).get('content', '') if isinstance(first, dict) else ''
                except Exception:
                    text = ''
            return {'content': text or ''}
        except Exception as e:
            return {'error': f'OpenAI image analysis failed: {e}'}

def __call__(self, prompt: str, image_url: str=None, image_path: str=None, model: str=None):
    try:
        client = create_openai_client(self.api_key, self.organization_id)
        actual_model = model if model else self.model
        final_image_url = image_url
        if not final_image_url and image_path:
            import base64
            import mimetypes
            mime, _ = mimetypes.guess_type(image_path)
            mime = mime or 'image/png'
            try:
                system_path = self.storage_handler.translate_in(image_path)
                content = self.storage_handler._read_raw(system_path)
            except Exception as e:
                return {'error': f'Could not read image {image_path}: {str(e)}'}
            b64 = base64.b64encode(content).decode('utf-8')
            final_image_url = f'data:{mime};base64,{b64}'
        response = client.responses.create(model=actual_model, input=[{'role': 'user', 'content': [{'type': 'input_text', 'text': prompt}, {'type': 'input_image', 'image_url': final_image_url}]}])
        text = getattr(response, 'output_text', None)
        if text is None:
            try:
                choices = getattr(response, 'output', None) or getattr(response, 'choices', None)
                if choices and isinstance(choices, list):
                    first = choices[0]
                    text = getattr(first, 'message', {}).get('content', '') if isinstance(first, dict) else ''
            except Exception:
                text = ''
        return {'content': text or ''}
    except Exception as e:
        return {'error': f'OpenAI image analysis failed: {e}'}

class Evaluator:
    """
    A class for evaluating the performance of a workflow.
    """

    def __init__(self, llm: BaseLLM, num_workers: int=1, agent_manager: Optional[AgentManager]=None, collate_func: Optional[Callable]=None, output_postprocess_func: Optional[Callable]=None, verbose: Optional[bool]=None, **kwargs):
        """
        Initialize the Evaluator.

        Args:
            llm (BaseLLM): The LLM to use for evaluation.
            num_workers (int): The number of parallel workers to use for evaluation. Default is 1. 
            agent_manager (AgentManager, optional): The agent manager used to construct the workflow. Only used when the workflow graph is a WorkFlowGraph.
            collate_func (Callable, optional): A function to collate the benchmark data. 
                It receives a single example from the benchmark and the output (which should be a dictionary) will serve as inputs  
                to the `execute` function of an WorkFlow (or ActionGraph) instance. 
                Note that the keys in the collated output should match the inputs of the workflow.
                The default is a lambda function that returns the example itself. 
            output_postprocess_func (Callable, optional): A function to postprocess the output of the workflow. 
                It receives the output of an WorkFlow instance (str) or an ActionGraph instance (dict) as input 
                and the output will be passed to the `evaluate` function of the benchmark. 
                The default is a lambda function that returns the output itself.
            verbose (bool, optional): Whether to print the evaluation progress.
        """
        self.llm = llm
        self.num_workers = num_workers
        self.agent_manager = agent_manager
        self._thread_agent_managers = {}
        self.collate_func = collate_func or (lambda x: x)
        self.output_postprocess_func = output_postprocess_func or (lambda x: x)
        self.verbose = verbose
        self._evaluation_records = {}
        self.kwargs = kwargs

    def _get_eval_data(self, benchmark: Benchmark, eval_mode: str='test', indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None) -> List[dict]:
        assert eval_mode in ['test', 'dev', 'train'], f"Invalid eval_mode: {eval_mode}. Choices: ['test', 'dev', 'train']"
        if eval_mode == 'test':
            data = benchmark.get_test_data(indices=indices, sample_k=sample_k, seed=seed)
        elif eval_mode == 'dev':
            data = benchmark.get_dev_data(indices=indices, sample_k=sample_k, seed=seed)
        else:
            data = benchmark.get_train_data(indices=indices, sample_k=sample_k, seed=seed)
        return data

    def evaluate(self, graph: Union[WorkFlowGraph, ActionGraph], benchmark: Benchmark, eval_mode: str='test', indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None, verbose: Optional[bool]=None, update_agents: Optional[bool]=False, **kwargs) -> dict:
        """
        Evaluate the performance of the workflow on the benchmark.

        Args:
            graph (WorkFlowGraph or ActionGraph): The workflow to evaluate.
            benchmark (Benchmark): The benchmark to evaluate the workflow on.
            eval_mode (str): which split of the benchmark to evaluate the workflow on. Choices: ["test", "dev", "train"].
            indices (List[int], optional): The indices of the data to evaluate the workflow on.
            sample_k (int, optional): The number of data to evaluate the workflow on. If provided, a random sample of size `sample_k` will be used.
            verbose (bool, optional): Whether to print the evaluation progress. If not provided, the `self.verbose` will be used.
            update_agents (bool, optional): Whether to update the agents in the agent manager. Only used when the workflow graph is a WorkFlowGraph.
        Returns:
            dict: The average metrics of the workflow evaluation.
        """
        self._evaluation_records.clear()
        if isinstance(graph, WorkFlowGraph) and update_agents:
            if self.agent_manager is None:
                raise ValueError(f'`agent_manager` is not provided in {type(self).__name__}. Please provide an agent manager when evaluating a WorkFlowGraph.')
            self.agent_manager.update_agents_from_workflow(workflow_graph=graph, llm_config=self.llm.config, **kwargs)
        data = self._get_eval_data(benchmark=benchmark, eval_mode=eval_mode, indices=indices, sample_k=sample_k, seed=seed)
        results = self._evaluate_graph(graph=graph, data=data, benchmark=benchmark, verbose=verbose, **kwargs)
        return results

    def _execute_workflow_graph(self, graph: WorkFlowGraph, inputs: dict, return_trajectory: bool=False, **kwargs) -> Union[str, Tuple[str, List[Message]]]:
        """
        Execute the workflow graph and return the output.

        Args:
            graph (WorkFlowGraph): The workflow graph to execute
            inputs (dict): The inputs to the workflow graph
            **kwargs: Additional arguments for workflow graph execution

        Returns:
            str: The output of the workflow graph
        """
        if self.agent_manager is None:
            raise ValueError(f'`agent_manager` is not provided in {type(self).__name__}. Please provide an agent manager when evaluating a WorkFlowGraph.')
        graph_copy = WorkFlowGraph(goal=graph.goal, graph=graph)
        graph_copy.reset_graph()
        workflow = WorkFlow(llm=self.llm, graph=graph_copy, agent_manager=self.agent_manager, **kwargs)
        output: str = workflow.execute(inputs=inputs, **kwargs)
        if return_trajectory:
            return (output, workflow.environment.get())
        return output

    def _execute_action_graph(self, graph: ActionGraph, inputs: dict, **kwargs) -> dict:
        """
        Execute the action graph and return the output.

        Args:
            graph (ActionGraph): The action graph to execute
            inputs (dict): The inputs to the action graph
            **kwargs: Additional arguments for action graph execution

        Returns:
            dict: The output of the action graph
        """
        output: dict = graph.execute(**inputs, **kwargs)
        return output

    def _evaluate_single_example(self, graph: Union[WorkFlowGraph, ActionGraph], example: dict, benchmark: Benchmark, **kwargs) -> Optional[dict]:
        """
        Evaluate a single data example through the workflow and save the evaluation metrics to the evaluation records.

        Args:
            graph (WorkFlowGraph or ActionGraph): The workflow to execute
            example (dict): Single input data example
            **kwargs: Additional arguments for workflow execution

        Returns:
            Optional[dict]: Evaluation metrics for this example, None if failed
        """
        try:
            inputs: dict = self.collate_func(example)
            if not isinstance(inputs, dict):
                raise ValueError(f'The collate_func should return a dictionary. Got {type(inputs)}.')
            if isinstance(graph, ActionGraph):
                output: dict = self._execute_action_graph(graph=graph, inputs=inputs, **kwargs)
            elif isinstance(graph, WorkFlowGraph):
                workflow_graph_outputs = self._execute_workflow_graph(graph=graph, inputs=inputs, return_trajectory=True, **kwargs)
                output: str = workflow_graph_outputs[0]
                trajectory: List[Message] = workflow_graph_outputs[1]
            else:
                raise ValueError(f'Invalid workflow type: {type(graph)}. Must be WorkFlowGraph or ActionGraph.')
            output = self.output_postprocess_func(output)
            label = benchmark.get_label(example)
            metrics = benchmark.evaluate(prediction=output, label=label)
            example_id = benchmark.get_id(example=example)
            self._evaluation_records[example_id] = {'prediction': output, 'label': label, 'metrics': metrics}
            if isinstance(graph, WorkFlowGraph):
                self._evaluation_records[example_id]['trajectory'] = trajectory
        except Exception as e:
            logger.warning(f'Error evaluating example and set the metrics to None:\nExample: {example}\nError: {str(e)}')
            return None
        return metrics

    def _single_evaluate(self, graph: Union[WorkFlowGraph, ActionGraph], data: List[dict], benchmark: Benchmark, verbose: Optional[bool]=None, **kwargs) -> List[dict]:
        """
        Evaluate workflow on data using single thread.

        Args:
            graph (WorkFlowGraph or ActionGraph): The workflow to evaluate
            data (List[dict]): List of input data
            benchmark (Benchmark): The benchmark to evaluate the workflow on
            verbose (bool): Whether to show progress bar
            **kwargs: Additional arguments for workflow execution

        Returns:
            List[dict]: List of valid evaluation metrics
        """
        if not data:
            logger.warning('No data to evaluate. Return an empty list.')
            return []
        results = []
        if verbose:
            progress_bar = tqdm(data, desc='Evaluating workflow', total=len(data))
        for example in data:
            result = self._evaluate_single_example(graph, example, benchmark, **kwargs)
            results.append(result)
            if verbose:
                progress_bar.update(1)
        if verbose:
            progress_bar.close()
        return results

    def _create_new_agent_manager(self) -> AgentManager:
        """Create a new agent manager with the same configuration but new locks"""
        if self.agent_manager is None:
            return None
        new_manager = AgentManager(agents=self.agent_manager.agents, storage_handler=self.agent_manager.storage_handler)
        return new_manager

    def _get_thread_agent_manager(self) -> AgentManager:
        """Get or create thread-specific agent manager"""
        if self.agent_manager is None:
            return None
        thread_id = threading.get_ident()
        if thread_id not in self._thread_agent_managers:
            new_manager = self._create_new_agent_manager()
            self._thread_agent_managers[thread_id] = new_manager
        return self._thread_agent_managers[thread_id]

    def _evaluate_single_example_with_context(self, graph: Union[WorkFlowGraph, ActionGraph], example: dict, benchmark: Benchmark, **kwargs) -> Optional[dict]:
        """Wrapper that sets up thread-specific context before running evaluation"""
        thread_agent_manager = self._get_thread_agent_manager()
        if thread_agent_manager is None:
            return self._evaluate_single_example(graph, example, benchmark, **kwargs)
        original_agent_manager = self.agent_manager
        try:
            self.agent_manager = thread_agent_manager
            return self._evaluate_single_example(graph, example, benchmark, **kwargs)
        finally:
            self.agent_manager = original_agent_manager

    def _parallel_evaluate(self, graph: Union[WorkFlowGraph, ActionGraph], data: List[dict], benchmark: Benchmark, verbose: Optional[bool]=None, **kwargs) -> List[dict]:
        if not data:
            logger.warning('No data to evaluate. Return an empty list.')
            return []
        results = []
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {executor.submit(contextvars.copy_context().run, self._evaluate_single_example_with_context, graph, example, benchmark, **kwargs): example for example in data}
            if verbose:
                progress_bar = tqdm(desc='Evaluating workflow', total=len(futures))
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results.append(result)
                if verbose:
                    progress_bar.update(1)
        if verbose:
            progress_bar.close()
        return results

    def _calculate_average_score(self, scores: List[dict]) -> dict:
        """
        Calculate the average score from a list of scores.

        Args:
            scores (List[dict]): List of evaluation scores

        Returns:
            dict: Average metrics
        """
        if not scores:
            logger.warning('No scores found. Return an empty dictionary.')
            return {}
        num_total_items = len(scores)
        first_valid_score = None
        for score in scores:
            if score is not None:
                first_valid_score = score
                break
        if first_valid_score is None:
            logger.warning('No valid scores found. Return an empty dictionary.')
            return {}
        return {k: sum((d[k] for d in scores if d is not None)) / num_total_items for k in first_valid_score}

    def _evaluate_graph(self, graph: Union[WorkFlowGraph, ActionGraph], data: List[dict], benchmark: Benchmark, verbose: Optional[bool]=None, **kwargs) -> dict:
        """
        Evaluate the workflow on the data.

        Args:
            graph (WorkFlowGraph or ActionGraph): The workflow to evaluate
            data (List[dict]): List of input data to evaluate
            benchmark (Benchmark): The benchmark to evaluate the workflow on
            verbose (bool, optional): Whether to print the evaluation progress. If not provided, the `self.verbose` will be used.
            **kwargs: Additional arguments passed to workflow execution

        Returns:
            dict: The average metrics of the workflow evaluation
        """
        if not data:
            logger.warning('No data to evaluate. Return an empty dictionary.')
            return {}
        verbose = verbose if verbose is not None else self.verbose
        if self.num_workers > 1:
            results = self._parallel_evaluate(graph, data, benchmark, verbose, **kwargs)
        else:
            results = self._single_evaluate(graph, data, benchmark, verbose, **kwargs)
        return self._calculate_average_score(results)

    def get_example_evaluation_record(self, benchmark: Benchmark, example: Any) -> Optional[dict]:
        """
        Get the evaluation record for a given example.
        """
        example_id = benchmark.get_id(example=example)
        return self._evaluation_records.get(example_id, None)

    def get_evaluation_record_by_id(self, benchmark: Benchmark, example_id: str, eval_mode: str='test') -> Optional[dict]:
        """
        Get the evaluation record for a given example id.
        """
        example = benchmark.get_example_by_id(example_id=example_id, mode=eval_mode)
        return self.get_example_evaluation_record(benchmark=benchmark, example=example)

    def get_all_evaluation_records(self) -> dict:
        """
        Get all the evaluation records.
        """
        return self._evaluation_records.copy()

    async def async_evaluate(self, graph: Union[WorkFlowGraph, ActionGraph], benchmark: Benchmark, eval_mode: str='test', indices: Optional[List[int]]=None, sample_k: Optional[int]=None, seed: Optional[int]=None, verbose: Optional[bool]=None, **kwargs) -> dict:
        """
        Asynchronously evaluate the performance of the workflow on the benchmark.

        Args:
            graph (WorkFlowGraph or ActionGraph): The workflow to evaluate.
            benchmark (Benchmark): The benchmark to evaluate the workflow on.
            eval_mode (str): which split of the benchmark to evaluate the workflow on. Choices: ["test", "dev", "train"].
            indices (List[int], optional): The indices of the data to evaluate the workflow on.
            sample_k (int, optional): The number of data to evaluate the workflow on. If provided, a random sample of size `sample_k` will be used.
            verbose (bool, optional): Whether to print the evaluation progress. If not provided, the `self.verbose` will be used.
        
        Returns:
            dict: The average metrics of the workflow evaluation.
        """
        self._evaluation_records.clear()
        data = self._get_eval_data(benchmark=benchmark, eval_mode=eval_mode, indices=indices, sample_k=sample_k, seed=seed)
        if not data:
            logger.warning('No data to evaluate. Return an empty dictionary.')
            return {}
        verbose = verbose if verbose is not None else self.verbose
        sem = asyncio.Semaphore(self.num_workers)

        async def process_with_semaphore(example):
            async with sem:
                try:
                    return await self._async_evaluate_single_example(graph=graph, example=example, benchmark=benchmark, **kwargs)
                except Exception as e:
                    logger.warning(f'Async evaluation failed for example with semaphore: {str(e)}')
                    return None
        tasks = [process_with_semaphore(example) for example in data]
        if verbose:
            results = await tqdm_asyncio.gather(*tasks, desc=f'Evaluating {benchmark.name}', total=len(data))
        else:
            results = await asyncio.gather(*tasks)
        return self._calculate_average_score(results)

    async def _async_evaluate_single_example(self, graph: Union[WorkFlowGraph, ActionGraph], example: dict, benchmark: Benchmark, **kwargs) -> Optional[dict]:
        """
        Asynchronously evaluate a single example. 
        """
        try:
            inputs: dict = self.collate_func(example)
            if not isinstance(inputs, dict):
                raise ValueError(f'The collate_func should return a dictionary. Got {type(inputs)}.')
            if isinstance(graph, ActionGraph):
                output: dict = await self._async_execute_action_graph(graph=graph, inputs=inputs, **kwargs)
            elif isinstance(graph, WorkFlowGraph):
                workflow_graph_outputs = await self._async_execute_workflow_graph(graph=graph, inputs=inputs, return_trajectory=True, **kwargs)
                output: str = workflow_graph_outputs[0]
                trajectory: List[Message] = workflow_graph_outputs[1]
            else:
                raise ValueError(f'Invalid workflow type: {type(graph)}. Must be WorkFlowGraph or ActionGraph.')
            output = self.output_postprocess_func(output)
            label = benchmark.get_label(example)
            if hasattr(benchmark, 'async_evaluate') and callable(getattr(benchmark, 'async_evaluate')):
                metrics = await benchmark.async_evaluate(prediction=output, label=label)
            else:
                metrics = benchmark.evaluate(prediction=output, label=label)
            example_id = benchmark.get_id(example=example)
            self._evaluation_records[example_id] = {'prediction': output, 'label': label, 'metrics': metrics}
            if isinstance(graph, WorkFlowGraph):
                self._evaluation_records[example_id]['trajectory'] = trajectory
        except Exception as e:
            logger.warning(f'Error evaluating example and set the metrics to None:\nExample: {example}\nError: {str(e)}')
            return None
        return metrics

    async def _async_execute_action_graph(self, graph: ActionGraph, inputs: dict, **kwargs) -> dict:
        """
        Asynchronously execute the action graph.
        """
        return await graph.async_execute(**inputs, **kwargs)

    async def _async_execute_workflow_graph(self, graph: WorkFlowGraph, inputs: dict, return_trajectory: bool=False, **kwargs) -> Union[str, Tuple[str, List[Message]]]:
        """
        Asynchronously execute the workflow graph.
        """
        if self.agent_manager is None:
            raise ValueError('`agent_manager` is not provided. Please provide an agent manager when evaluating a WorkFlowGraph.')
        graph_copy = WorkFlowGraph(goal=graph.goal, graph=graph)
        graph_copy.reset_graph()
        local_agent_manager = AgentManager(agents=self.agent_manager.agents, storage_handler=self.agent_manager.storage_handler)
        workflow = WorkFlow(llm=self.llm, graph=graph_copy, agent_manager=local_agent_manager, **kwargs)
        output: str = await workflow.async_execute(inputs=inputs, **kwargs)
        if return_trajectory:
            return (output, workflow.environment.get())
        return output

def _parallel_evaluate(self, graph: Union[WorkFlowGraph, ActionGraph], data: List[dict], benchmark: Benchmark, verbose: Optional[bool]=None, **kwargs) -> List[dict]:
    if not data:
        logger.warning('No data to evaluate. Return an empty list.')
        return []
    results = []
    with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
        futures = {executor.submit(contextvars.copy_context().run, self._evaluate_single_example_with_context, graph, example, benchmark, **kwargs): example for example in data}
        if verbose:
            progress_bar = tqdm(desc='Evaluating workflow', total=len(futures))
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)
            if verbose:
                progress_bar.update(1)
    if verbose:
        progress_bar.close()
    return results

def get_all_evaluation_records(self) -> dict:
    """
        Get all the evaluation records.
        """
    return self._evaluation_records.copy()

class StorageHandler(BaseModule):
    """
    Implementation of a storage handler for managing various storage backends.
    
    StorageHandler provides an abstraction for reading and writing data (e.g., memory, agents, workflows).
    It supports multiple storage types, including database, vector, and graph storage, initialized via factories.
    """
    storageConfig: StoreConfig = Field(..., description='Configuration for all storage backends')
    storageDB: Optional[Union[DBStoreBase, Any]] = Field(None, description='Database storage backend')
    vector_store: Optional[Union[VectorStoreBase, Any]] = Field(None, description='Single vector storage backend')
    graph_store: Optional[Union[GraphStoreBase, Any]] = Field(None, description='Optional graph storage backend')

    def init_module(self):
        """
        Initialize all storage backends based on the provided configuration.
        Calls individual initialization methods for database, vector, and graph stores.
        """
        if self.storageConfig.path is not None or self.storageConfig.path != ':memory:' or (not self.storageConfig.path):
            os.makedirs(os.path.dirname(self.storageConfig.path), exist_ok=True)
        self._init_db_store()
        self._init_vector_store()
        self._init_graph_store()

    def _init_db_store(self):
        """
        Initialize the database storage backend using the DBStoreFactory.
        Sets the storageDB attribute with the created instance.
        """
        db_config = self.storageConfig.dbConfig
        self.storageDB = DBStoreFactory.create(db_config.db_name, db_config)

    def _init_vector_store(self):
        """
        Initialize the vector storage backend using the VectorStoreFactory.
        Sets the storageVector attribute if the configuration is provided.
        """
        vector_config = self.storageConfig.vectorConfig
        if vector_config is not None:
            if self.vector_store is not None:
                del self.vector_store
            vector_config_dict = vector_config.model_dump()
            self.vector_store = VectorStoreFactory().create(store_type=vector_config.vector_name, store_config=vector_config_dict)

    def _init_graph_store(self):
        """
        Initialize the graph storage backend using the GraphStoreFactory.
        Sets the storageGraph attribute if the configuration is provided.
        """
        graph_config = self.storageConfig.graphConfig
        if graph_config is not None:
            self.graph_store = GraphStoreFactory().create(store_type=graph_config.graph_name, store_config=graph_config.model_dump())

    def load(self, tables: Optional[List[str]]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load all data from the database storage.

        Attributes:
            tables (Optional[List[str]]): List of table names to load; if None, loads all tables.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary with table names as keys and lists of records as values. You should parse the values by yourself.
        """
        result = {}
        table_info = self.storageDB.col_info()
        if tables is None:
            tables_to_load = [t.value for t in TableType]
        else:
            tables_to_load = tables
        for table_name in tables_to_load:
            table_data = []
            if any((t['table_name'] == table_name for t in table_info)):
                cursor = self.storageDB.connection.cursor()
                cursor.execute(f'SELECT * FROM {table_name}')
                columns = next((t['columns'].keys() for t in table_info if t['table_name'] == table_name))
                rows = cursor.fetchall()
                table_data = [dict(zip(columns, row)) for row in rows]
            result[table_name] = table_data
        return result

    def save(self, data: Dict[str, Any], *args, **kwargs):
        """
        Save all provided data to the database storage.

        Attributes:
            data (Dict[str, Any]): Dictionary with table names as keys and lists of records to save.

        Raises:
            ValueError: If an unknown table name is provided.
        """
        for table_name, records in data.items():
            store_type = None
            for st in TableType:
                if st.value == table_name:
                    store_type = st
                    break
            if store_type is None:
                raise ValueError(f'Unknown table: {table_name}')
            for record in records:
                self.storageDB.insert(metadata=record, store_type=store_type, table=table_name)

    def parse_result(self, results: Dict[str, str], store: Union[AgentStore, WorkflowStore, MemoryStore, HistoryStore]) -> Dict[str, Any]:
        """
        Parse database results, converting JSON strings to Python objects where applicable.

        Attributes:
            results (Dict[str, str]): Raw database results with column names as keys.
            store (Union[AgentStore, WorkflowStore, MemoryStore, HistoryStore]): Pydantic model for validation.

        Returns:
            Dict[str, Any]: Parsed results with JSON strings deserialized to Python objects.
        """
        for k, v in store.model_fields.items():
            if v.annotation not in [Optional[str], str]:
                try:
                    results[k] = json.loads(results[k])
                except (json.JSONDecodeError, KeyError, TypeError):
                    results[k] = results.get(k)
        return results

    def load_memory(self, memory_id: str, table: Optional[str]=None, **kwargs) -> Dict[str, Any]:
        """
        Load a single long-term memory data.

        Attributes:
            memory_id (str): The ID of the long-term memory.
            table (Optional[str]): The table name; defaults to 'memory' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create a LongTermMemory instance.
        """
        table = table or TableType.store_memory.value
        result = self.storageDB.get_by_id(memory_id, store_type='memory', table=table)
        if result is not None:
            result = self.parse_result(result, MemoryStore)
        return result

    def save_memory(self, memory_data: Dict[str, Any], table: Optional[str]=None, **kwargs):
        """
        Save or update a single memory.

        Attributes:
            memory_data (Dict[str, Any]): The long-term memory's data.
            table (Optional[str]): The table name; defaults to 'memory' if None.

        """
        table = table or TableType.store_memory.value
        memory_id = memory_data.get('memory_id')
        if not memory_id:
            raise ValueError("Memory data must include a 'memory_id' field")
        existing = self.storageDB.get_by_id(memory_id, store_type='memory', table=table)
        if existing:
            self.storageDB.update(memory_id, new_metadata=memory_data, store_type='memory', table=table)
        else:
            self.storageDB.insert(metadata=memory_data, store_type='memory', table=table)

    def load_agent(self, agent_name: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load a single agent's data.

        Attributes:
            agent_name (str): The unique name of the agent to retrieve.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create an Agent instance, or None if not found.
        """
        table = table or TableType.store_agent.value
        result = self.storageDB.get_by_id(agent_name, store_type='agent', table=table)
        if result is not None:
            result = self.parse_result(result, AgentStore)
        return result

    def remove_agent(self, agent_name: str, table: Optional[str]=None, *args, **kwargs):
        """
        Remove an agent from storage if the agent exists.

        Attributes:
            agent_name (str): The name of the agent to be deleted.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Raises:
            ValueError: If the agent does not exist in the specified table.
        """
        table = table or TableType.store_agent.value
        success = self.storageDB.delete(agent_name, store_type='agent', table=table)
        if not success:
            raise ValueError(f'Agent with name {agent_name} not found in table {table}')

    def save_agent(self, agent_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
        """
        Save or update a single agent's data.

        Attributes:
            agent_data (Dict[str, Any]): The agent's data, must include 'name' and 'content' keys.
            table (Optional[str]): The table name; defaults to 'agent' if None.

        Raises:
            ValueError: If 'name' field is missing or if Pydantic validation fails.
        """
        table = table or TableType.store_agent.value
        agent_name = agent_data.get('name')
        if not agent_name:
            raise ValueError("Agent data must include a 'name' field")
        existing = self.storageDB.get_by_id(agent_name, store_type='agent', table=table)
        if existing:
            self.storageDB.update(agent_name, new_metadata=agent_data, store_type='agent', table=table)
        else:
            self.storageDB.insert(metadata=agent_data, store_type='agent', table=table)

    def load_workflow(self, workflow_id: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load a single workflow's data.

        Attributes:
            workflow_id (str): The ID of the workflow.
            table (Optional[str]): The table name; defaults to 'workflow' if None.

        Returns:
            Dict[str, Any]: The data that can be used to create a WorkFlow instance, or None if not found.
        """
        table = table or TableType.store_workflow.value
        result = self.storageDB.get_by_id(workflow_id, store_type='workflow', table=table)
        if result is not None:
            result = self.parse_result(result, WorkflowStore)
        return result

    def save_workflow(self, workflow_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
        """
        Save or update a workflow's data.

        Attributes:
            workflow_data (Dict[str, Any]): The workflow's data, must include 'name' field.
            table (Optional[str]): The table name; defaults to 'workflow' if None.

        Raises:
            ValueError: If 'name' field is missing or if Pydantic validation fails.
        """
        table = table or TableType.store_workflow.value
        workflow_id = workflow_data.get('name')
        if not workflow_id:
            raise ValueError("Workflow data must include a 'name' field")
        existing = self.storageDB.get_by_id(workflow_id, store_type='workflow', table=table)
        if existing:
            self.storageDB.update(workflow_id, new_metadata=workflow_data, store_type='workflow', table=table)
        else:
            self.storageDB.insert(metadata=workflow_data, store_type='workflow', table=table)

    def load_history(self, memory_id: str, table: Optional[str]=None, *args, **kwargs) -> Dict[str, Any]:
        """
        Load a single history entry.

        Attributes:
            memory_id (str): The ID of the memory associated with the history entry.
            table (Optional[str]): The table name; defaults to 'history' if None.

        Returns:
            Dict[str, Any]: The history data, or None if not found.
        """
        table = table or TableType.store_history.value
        result = self.storageDB.get_by_id(memory_id, store_type='history', table=table)
        if result is not None:
            result = self.parse_result(result, HistoryStore)
        return result

    def save_history(self, history_data: Dict[str, Any], table: Optional[str]=None, *args, **kwargs):
        """
        Save or update a single history entry.

        Attributes:
            history_data (Dict[str, Any]): The history data, must include 'memory_id' field.
            table (Optional[str]): The table name; defaults to 'history' if None.

        Raises:
            ValueError: If 'memory_id' field is missing or if Pydantic validation fails.
        """
        table = table or TableType.store_history.value
        memory_id = history_data.get('memory_id')
        if not memory_id:
            raise ValueError("History data must include a 'memory_id' field")
        existing = self.storageDB.get_by_id(memory_id, store_type='history', table=table)
        if existing:
            result = HistoryStore.model_validate(self.parse_result(existing, HistoryStore))
            history_data['old_memory'] = result.old_memory
            self.storageDB.update(memory_id, new_metadata=history_data, store_type='history', table=table)
        else:
            self.storageDB.insert(metadata=history_data, store_type='history', table=table)

    def load_index(self, corpus_id: str, table: Optional[str]=None) -> Optional[Dict[str, Any]]:
        result = self.storageDB.get_by_id(corpus_id, store_type='indexing', table=table)
        if result is not None:
            result = self.parse_result(result, IndexStore)
        return result

    def save_index(self, index_data: Dict[str, Any], table: Optional[str]=None):
        corpus_id = index_data.get('corpus_id')
        if not corpus_id:
            raise ValueError("Index data must include an 'corpus_id' field")
        existing = self.storageDB.get_by_id(corpus_id, store_type='indexing', table=table)
        if existing:
            self.storageDB.update(corpus_id, new_metadata=index_data, store_type='indexing', table=table)
        else:
            self.storageDB.insert(metadata=index_data, store_type='indexing', table=table)

def _init_db_store(self):
    """
        Initialize the database storage backend using the DBStoreFactory.
        Sets the storageDB attribute with the created instance.
        """
    db_config = self.storageConfig.dbConfig
    self.storageDB = DBStoreFactory.create(db_config.db_name, db_config)

def parse_result(self, results: Dict[str, str], store: Union[AgentStore, WorkflowStore, MemoryStore, HistoryStore]) -> Dict[str, Any]:
    """
        Parse database results, converting JSON strings to Python objects where applicable.

        Attributes:
            results (Dict[str, str]): Raw database results with column names as keys.
            store (Union[AgentStore, WorkflowStore, MemoryStore, HistoryStore]): Pydantic model for validation.

        Returns:
            Dict[str, Any]: Parsed results with JSON strings deserialized to Python objects.
        """
    for k, v in store.model_fields.items():
        if v.annotation not in [Optional[str], str]:
            try:
                results[k] = json.loads(results[k])
            except (json.JSONDecodeError, KeyError, TypeError):
                results[k] = results.get(k)
    return results

class RAGEngine:

    def __init__(self, config: RAGConfig, storage_handler: StorageHandler, llm: Optional[BaseLLM]=None):
        self.config = config
        self.storage_handler = storage_handler
        self.embedding_factory = EmbeddingFactory()
        self.index_factory = IndexFactory()
        self.chunk_factory = ChunkFactory()
        self.retriever_factory = RetrieverFactory()
        self.postprocessor_factory = PostprocessorFactory()
        self.llm = llm
        logger.info(f'RAGEngine modality config: {self.config.modality}')
        if self.config.modality == 'multimodal':
            self.chunk_class = ImageChunk
        else:
            self.chunk_class = TextChunk
        if self.config.modality == 'multimodal':
            self.reader = MultimodalReader(recursive=self.config.reader.recursive, exclude_hidden=self.config.reader.exclude_hidden, num_files_limits=self.config.reader.num_files_limit, errors=self.config.reader.errors)
        else:
            self.reader = LLamaIndexReader(recursive=self.config.reader.recursive, exclude_hidden=self.config.reader.exclude_hidden, num_workers=self.config.num_workers, num_files_limits=self.config.reader.num_files_limit, custom_metadata_function=self.config.reader.custom_metadata_function, extern_file_extractor=self.config.reader.extern_file_extractor, errors=self.config.reader.errors, encoding=self.config.reader.encoding)
        self.embed_model = self.embedding_factory.create(provider=self.config.embedding.provider, model_config=self.config.embedding.model_dump(exclude_unset=True))
        if self.storage_handler.vector_store is not None and self.embed_model.dimensions is not None:
            if self.storage_handler.storageConfig.vectorConfig.dimensions != self.embed_model.dimensions:
                logger.warning('The dimensions in vector_store is not equal with embed_model. Reiniliaze vector_store.')
                self.storage_handler.storageConfig.vectorConfig.dimensions = self.embed_model.dimensions
                self.storage_handler._init_vector_store()
        if self.config.modality == 'multimodal':
            self.chunker = None
        else:
            self.chunker = self.chunk_factory.create(strategy=self.config.chunker.strategy, embed_model=self.embed_model.get_embedding_model(), chunker_config={'chunk_size': self.config.chunker.chunk_size, 'chunk_overlap': self.config.chunker.chunk_overlap, 'max_chunks': self.config.chunker.max_chunks})
        self.indices: Dict[str, Dict[str, BaseIndexWrapper]] = {}
        self.retrievers: Dict[str, Dict[str, BaseRetrieverWrapper]] = {}

    def read(self, file_paths: Union[Sequence[str], str], exclude_files: Optional[Union[str, List, Tuple, Sequence]]=None, filter_file_by_suffix: Optional[Union[str, List, Tuple, Sequence]]=None, merge_by_file: bool=False, show_progress: bool=False, corpus_id: str=None) -> Corpus:
        """Load and chunk documents from files.

        Reads files from specified paths, processes them into documents, and chunks them into a Corpus.

        Args:
            file_paths (Union[Sequence[str], str]): Path(s) to files or directories.
            exclude_files (Optional[Union[str, List, Tuple, Sequence]]): Files to exclude.
            filter_file_by_suffix (Optional[Union[str, List, Tuple, Sequence]]): Filter files by suffix (e.g., '.pdf').
            merge_by_file (bool): Merge documents by file.
            show_progress (bool): Show loading progress.
            corpus_id (Optional[str]): Identifier for the corpus. Defaults to a UUID if None.

        Returns:
            Corpus: The chunked corpus containing processed document chunks.

        Raises:
            Exception: If document reading or chunking fails.
        """
        try:
            corpus_id = corpus_id or str(uuid4())
            documents = self.reader.load(file_paths=file_paths, exclude_files=exclude_files, filter_file_by_suffix=filter_file_by_suffix, merge_by_file=merge_by_file, show_progress=show_progress)
            if self.config.modality == 'multimodal':
                image_chunks = []
                for doc in documents:
                    image_path = getattr(doc, 'image_path', None) or doc.metadata.get('file_path')
                    image_mimetype = getattr(doc, 'image_mimetype', None)
                    image_chunk = self.chunk_class(image_path=image_path, image_mimetype=image_mimetype, chunk_id=doc.metadata.get('file_name', f'img_{len(image_chunks)}'), metadata=ChunkMetadata(doc_id=doc.metadata.get('file_name', f'doc_{len(image_chunks)}'), corpus_id=corpus_id, **doc.metadata))
                    image_chunks.append(image_chunk)
                corpus = Corpus(chunks=image_chunks, corpus_id=corpus_id)
                logger.info(f'Read {len(documents)} multimodal documents (no chunking) for corpus {corpus_id}')
            else:
                corpus = self.chunker.chunk(documents)
                corpus.corpus_id = corpus_id
                logger.info(f'Read {len(documents)} documents and created {len(corpus.chunks)} chunks for corpus {corpus_id}')
            return corpus
        except Exception as e:
            logger.error(f'Failed to read documents for corpus {corpus_id}: {str(e)}')
            raise

    def add(self, index_type: str, nodes: Union[Corpus, List[NodeWithScore], List[TextNode], List[ImageNode]], corpus_id: str=None) -> None:
        """Add nodes to an index for a specific corpus.

        Initializes an index if it doesn't exist and inserts nodes, updating metadata with corpus_id and index_type.

        Args:
            index_type (str): Type of index (e.g., VECTOR, GRAPH).
            nodes (Union[Corpus, List[NodeWithScore], List[TextNode]]): Nodes or Corpus to add.
            corpus_id (str, optional): Identifier for the corpus. Defaults to a UUID if None.

        Return:
            return a sequence with id of each added node.
            
        Raises:
            Exception: If index creation or node insertion fails.
        """
        try:
            corpus_id = corpus_id or str(uuid4())
            if corpus_id not in self.indices:
                self.indices[corpus_id] = {}
                self.retrievers[corpus_id] = {}
            if index_type not in self.indices[corpus_id]:
                index = self.index_factory.create(index_type=index_type, embed_model=self.embed_model.get_embedding_model(), storage_handler=self.storage_handler, index_config=self.config.index.model_dump(exclude_unset=True) if self.config.index else {}, llm=self.llm)
                self.indices[corpus_id][index_type] = index
                self.retrievers[corpus_id][index_type] = self.retriever_factory.create(retriever_type=self.config.retrieval.retrivel_type, llm=self.llm, index=index.get_index(), graph_store=index.get_index().storage_context.graph_store, embed_model=self.embed_model.get_embedding_model(), query=Query(query_str='', top_k=self.config.retrieval.top_k if self.config.retrieval else 5), storage_handler=self.storage_handler, chunk_class=self.chunk_class)
            nodes_to_insert = nodes.to_llama_nodes() if isinstance(nodes, Corpus) else nodes
            for node in nodes_to_insert:
                node.metadata.update({'corpus_id': corpus_id, 'index_type': index_type})
            nodes_ids = self.indices[corpus_id][index_type].insert_nodes(nodes_to_insert)
            logger.info(f'Added {len(nodes_to_insert)} nodes to {index_type} index for corpus {corpus_id}')
            return nodes_ids
        except Exception as e:
            logger.error(f'Failed to add nodes to {index_type} index for corpus {corpus_id}: {str(e)}')
            return []

    def delete(self, corpus_id: str, index_type: Optional[str]=None, node_ids: Optional[Union[str, List[str]]]=None, metadata_filters: Optional[Dict[str, Any]]=None) -> None:
        """Delete nodes or an entire index from a corpus.

        Removes specific nodes by ID or metadata filters, or deletes the entire index if no filters are provided.

        Args:
            corpus_id (str): Identifier for the corpus.
            index_type (Optional[IndexType]): Specific index type to delete from. If None, affects all indices.
            node_ids (Union[str, Optional[List[str]]]): List of node IDs to delete.
            metadata_filters (Optional[Dict[str, Any]]): Metadata filters to select nodes for deletion.

        Raises:
            Exception: If deletion fails.
        """
        try:
            if corpus_id not in self.indices:
                logger.warning(f'No indices found for corpus {corpus_id}')
                return
            target_indices = [index_type] if index_type else self.indices[corpus_id].keys()
            for idx_type in list(target_indices):
                if idx_type not in self.indices[corpus_id]:
                    logger.warning(f'Index type {idx_type} not found for corpus {corpus_id}')
                    continue
                index = self.indices[corpus_id][idx_type]
                if node_ids or metadata_filters:
                    node_ids_list = [node_ids] if isinstance(node_ids, str) else node_ids
                    index.delete_nodes(node_ids=node_ids_list, metadata_filters=metadata_filters)
                    logger.info(f'Deleted nodes from {idx_type} index for corpus {corpus_id}')
                else:
                    index.clear()
                    del self.indices[corpus_id][idx_type]
                    del self.retrievers[corpus_id][idx_type]
                    logger.info(f'Deleted entire {idx_type} index for corpus {corpus_id}')
            if not self.indices[corpus_id]:
                del self.indices[corpus_id]
                del self.retrievers[corpus_id]
                logger.info(f'Removed empty corpus {corpus_id}')
        except Exception as e:
            logger.error(f'Failed to delete from corpus {corpus_id}, index {index_type}: {str(e)}')
            raise

    def clear(self, corpus_id: Optional[str]=None) -> None:
        """Clear all indices for a specific corpus or all corpora.

        Args:
            corpus_id (Optional[str]): Specific corpus to clear. If None, clears all corpora.

        Raises:
            Exception: If clearing fails.
        """
        try:
            target_corpora = [corpus_id] if corpus_id else list(self.indices.keys())
            for cid in target_corpora:
                if cid not in self.indices:
                    logger.warning(f'No indices found for corpus {cid}')
                    continue
                for idx_type in list(self.indices[cid].keys()):
                    index = self.indices[cid][idx_type]
                    index.clear()
                    del self.indices[cid][idx_type]
                    del self.retrievers[cid][idx_type]
                    logger.info(f'Cleared {idx_type} index for corpus {cid}')
                del self.indices[cid]
                del self.retrievers[cid]
                logger.info(f'Cleared corpus {cid}')
        except Exception as e:
            logger.error(f'Failed to clear indices for corpus {corpus_id or 'all'}: {str(e)}')
            raise

    def save(self, output_path: Optional[str]=None, corpus_id: Optional[str]=None, index_type: Optional[str]=None, table: Optional[str]=None, graph_exported: bool=False) -> None:
        """Save indices to files or database.

        Serializes corpus chunks to JSONL files and metadata to JSON files if output_path is provided,
        or saves to the SQLite database via StorageHandler if output_path is None.

        Args:
            output_path (Optional[str]): Directory to save JSONL and JSON files. If None, saves to database.
            corpus_id (Optional[str]): Specific corpus to save. If None, saves all corpora.
            index_type (Optional[str]): Specific index type to save. If None, saves all indices.
            table (Optional[str]): Database table name for index data. Defaults to 'indexing' if None.
            graph_exported (bool): If True, export graph nodes and relations for graph indices. Defaults to False.

        Raises:
            Exception: If saving fails or file operations encounter errors.
        """
        try:
            target_corpora = [corpus_id] if corpus_id else list(self.indices.keys())
            table = table or 'indexing'
            for cid in target_corpora:
                if cid not in self.indices:
                    logger.warning(f'No indices found for corpus {cid}')
                    continue
                target_indices = [index_type] if index_type and index_type in self.indices[cid] else self.indices[cid].keys()
                for idx_type in target_indices:
                    index = self.indices[cid][idx_type]
                    if idx_type == IndexType.GRAPH and (not graph_exported):
                        logger.warning(f'Skipping save for graph index {idx_type} in corpus {cid} as graph_exported is False')
                        continue
                    if idx_type == IndexType.GRAPH and graph_exported:
                        index.build_kv_store()
                    chunks = [self.chunk_class.from_llama_node(node_data) for node_id, node_data in index.id_to_node.items()]
                    corpus = Corpus(chunks=chunks, corpus_id=cid)
                    vector_config = self.storage_handler.storageConfig.vectorConfig.model_dump() if self.storage_handler.storageConfig.vectorConfig else {}
                    graph_config = self.storage_handler.storageConfig.graphConfig.model_dump() if self.storage_handler.storageConfig.graphConfig else {}
                    metadata = IndexMetadata(corpus_id=cid, index_type=idx_type, collection_name=vector_config.get('qdrant_collection_name', 'default_collection'), dimension=self.embed_model.dimensions, vector_db_type=vector_config.get('vector_name', None), graph_db_type=graph_config.get('graph_name', None), embedding_model_name=self.config.embedding.model_name, date=str(datetime.now()))
                    if output_path:
                        os.makedirs(output_path, exist_ok=True)
                        safe_cid = ''.join((c if c.isalnum() or c in ['-', '_'] else '_' for c in cid))
                        safe_idx_type = ''.join((c if c.isalnum() or c in ['-', '_'] else '_' for c in idx_type))
                        nodes_file = os.path.join(output_path, f'{safe_cid}_{safe_idx_type}_nodes.jsonl')
                        metadata_file = os.path.join(output_path, f'{safe_cid}_{safe_idx_type}_metadata.json')
                        corpus.to_jsonl(nodes_file, indent=0)
                        logger.info(f'Saved {len(corpus.chunks)} chunks to {nodes_file}')
                        with open(metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(metadata.model_dump(), f, indent=2, ensure_ascii=False)
                        logger.info(f'Saved metadata to {metadata_file}')
                    else:
                        index_data = {'corpus_id': cid, 'content': corpus.model_dump(), 'date': str(datetime.now()), 'metadata': metadata.model_dump()}
                        self.storage_handler.save_index(index_data, table=table)
                        logger.info(f'Saved {idx_type} index with {len(corpus.chunks)} chunks for corpus {cid} to database table {table}')
        except Exception as e:
            logger.error(f'Failed to save indices for corpus {corpus_id or 'all'}: {str(e)}')
            raise

    def load(self, source: Optional[str]=None, corpus_id: Optional[str]=None, index_type: Optional[str]=None, table: Optional[str]=None) -> None:
        """Load indices from files or database.

        Reconstructs indices and retrievers from JSONL/JSON files or SQLite database records.
        Validates the embedding model name and dimension before reinitializing the embedding model.

        Args:
            source (Optional[str]): Directory containing JSONL/JSON files. If None, loads from database.
            corpus_id (Optional[str]): Specific corpus to load. If None, loads all corpora.
            index_type (Optional[str]): Specific index type to load. If None, loads all indices.
            table (Optional[str]): Database table name for index data. Defaults to 'indexing' if None.

        Returns:
            The Sequence with id of loaded chunk.
        
        Raises:
            Exception: If loading fails due to file or database errors, invalid data, or unsupported embedding model/dimension.
        
        Warning:
            Try to call this function may cause some Bugs, when you load the nodes from file or database storage systems at twice. 
            Because All the indexing share the same storage backend from storageHandler.
            For example:
            The vector database (.e.g Faiss) can insert again, even thougt there is a same node.
        """
        try:
            table = table or 'indexing'
            config_dimension = self.storage_handler.storageConfig.vectorConfig.dimensions
            loaded_chunk_ids: List[str] = []
            if source:
                if not os.path.exists(source):
                    logger.error(f'Source directory {source} does not exist')
                    raise FileNotFoundError(f'Source directory {source} does not exist')
                for file_name in os.listdir(source):
                    if not file_name.endswith('_metadata.json'):
                        continue
                    parts = file_name.split('_')
                    if len(parts) < 3:
                        logger.warning(f'Skipping invalid metadata file: {file_name}')
                        continue
                    cid = '_'.join(parts[:-2])
                    idx_type = parts[-2]
                    if corpus_id and corpus_id != cid or (index_type and index_type != idx_type):
                        continue
                    metadata_file = os.path.join(source, file_name)
                    nodes_file = os.path.join(source, f'{cid}_{idx_type}_nodes.jsonl')
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = IndexMetadata.model_validate(json.load(f))
                    if not self.embed_model.validate_model(self.config.embedding.provider, metadata.embedding_model_name):
                        raise ValueError(f"Embedding model '{metadata.embedding_model_name}' is not supported by provider '{self.config.embedding.provider}'. Supported models: {EmbeddingProvider.SUPPORTED_MODELS.get(self.config.embedding.provider, [])}")
                    if metadata.dimension != config_dimension:
                        raise ValueError(f'Embedding dimension {metadata.dimension} in metadata does not match configured dimension {config_dimension}.')
                    if not os.path.exists(nodes_file):
                        logger.warning(f'Nodes file {nodes_file} not found for metadata {metadata_file}')
                        continue
                    corpus = Corpus.from_jsonl(nodes_file, corpus_id=cid)
                    if metadata.embedding_model_name != self.config.embedding.model_name:
                        logger.info(f'Reinitializing embedding model to {metadata.embedding_model_name}')
                        self.embed_model = self.embedding_factory.create(provider=self.config.embedding.provider, model_config=self.config.embedding.model_dump(exclude_unset=True))
                    chunk_ids = self._load_index(corpus, cid, idx_type)
                    loaded_chunk_ids.extend(chunk_ids)
                    logger.info(f'Loaded {idx_type} index with {len(corpus.chunks)} chunks for corpus {cid} from {nodes_file}')
            else:
                records = self.storage_handler.load(tables=[table]).get(table, [])
                if not records:
                    logger.warning(f'No records found in table {table}')
                    return
                for record in records:
                    parsed = self.storage_handler.parse_result(record, IndexStore)
                    cid = parsed['corpus_id']
                    idx_type = parsed['metadata']['index_type']
                    if corpus_id and corpus_id != cid or (index_type and index_type != idx_type):
                        continue
                    chunks = []
                    for chunk_data in parsed['content']['chunks']:
                        metadata = ChunkMetadata.model_validate(chunk_data['metadata'])
                        if self.config.modality == 'multimodal':
                            chunk = ImageChunk(chunk_id=chunk_data['chunk_id'], image_path=chunk_data['image_path'], image_mimetype=chunk_data.get('image_mimetype'), metadata=metadata, embedding=chunk_data['embedding'], excluded_embed_metadata_keys=chunk_data['excluded_embed_metadata_keys'], excluded_llm_metadata_keys=chunk_data['excluded_llm_metadata_keys'], relationships={k: RelatedNodeInfo(**v) for k, v in chunk_data['relationships'].items()})
                        else:
                            chunk = TextChunk(chunk_id=chunk_data['chunk_id'], text=chunk_data['text'], metadata=metadata, embedding=chunk_data['embedding'], start_char_idx=chunk_data['start_char_idx'], end_char_idx=chunk_data['end_char_idx'], excluded_embed_metadata_keys=chunk_data['excluded_embed_metadata_keys'], excluded_llm_metadata_keys=chunk_data['excluded_llm_metadata_keys'], relationships={k: RelatedNodeInfo(**v) for k, v in chunk_data['relationships'].items()})
                        chunks.append(chunk)
                    corpus = Corpus(chunks=chunks, corpus_id=cid, metadata=IndexMetadata.model_validate(parsed['metadata']))
                    metadata = IndexMetadata.model_validate(parsed['metadata'])
                    if not self.embed_model.validate_model(self.config.embedding.provider, metadata.embedding_model_name):
                        raise ValueError(f"Embedding model '{metadata.embedding_model_name}' is not supported by provider '{self.config.embedding.provider}'. Supported models: {EmbeddingProvider.SUPPORTED_MODELS.get(self.config.embedding.provider, [])}")
                    if metadata.dimension != config_dimension:
                        raise ValueError(f'Embedding dimension {metadata.dimension} in metadata does not match configured dimension {config_dimension}.')
                    if metadata.embedding_model_name != self.config.embedding.model_name:
                        logger.info(f'Reinitializing embedding model to {metadata.embedding_model_name}')
                        self.embed_model = self.embedding_factory.create(provider=self.config.embedding.provider, model_config=self.config.embedding.model_dump(exclude_unset=True))
                    chunk_ids = self._load_index(corpus, cid, idx_type)
                    loaded_chunk_ids.extend(chunk_ids)
                    logger.info(f'Loaded {idx_type} index with {len(corpus.chunks)} chunks for corpus {cid} from database table {table}')
            return loaded_chunk_ids
        except Exception as e:
            logger.error(f'Failed to load indices: {str(e)}')
            raise

    def _load_index(self, corpus: Corpus, corpus_id: str, index_type: str) -> Sequence[str]:
        """Helper method to load an index and its retriever."""
        try:
            if corpus_id not in self.indices:
                self.indices[corpus_id] = {}
                self.retrievers[corpus_id] = {}
            if index_type not in self.indices[corpus_id]:
                index = self.index_factory.create(index_type=index_type, embed_model=self.embed_model.get_embedding_model(), storage_handler=self.storage_handler, index_config=self.config.index.model_dump(exclude_unset=True) if self.config.index else {}, llm=self.llm)
                self.indices[corpus_id][index_type] = index
                retriever_type = RetrieverType.GRAPH if index_type == IndexType.GRAPH else RetrieverType.VECTOR
                self.retrievers[corpus_id][index_type] = self.retriever_factory.create(retriever_type=retriever_type, llm=self.llm, index=index.get_index(), graph_store=index.get_index().storage_context.graph_store, embed_model=self.embed_model.get_embedding_model(), query=Query(query_str='', top_k=self.config.retrieval.top_k if self.config.retrieval else 5), storage_handler=self.storage_handler)
            nodes = corpus.to_llama_nodes()
            for node in nodes:
                node.metadata.update({'corpus_id': corpus_id, 'index_type': index_type})
            chunk_ids = self.indices[corpus_id][index_type].load(nodes)
            logger.info(f'Inserted {len(nodes)} nodes into {index_type} index for corpus {corpus_id}')
            return chunk_ids
        except Exception as e:
            logger.error(f'Failed to load index for corpus {corpus_id}, index_type {index_type}: {str(e)}')
            raise

    async def aget(self, corpus_id: str, index_type: str, node_ids: List[str]) -> List[Union[TextChunk, ImageChunk]]:
        """Retrieve chunks by node_ids from the index."""
        try:
            chunks = await self.indices[corpus_id][index_type].get(node_ids=node_ids)
            logger.info(f'Retrieved {len(chunks)} chunks for node_ids: {node_ids}')
            return chunks
        except Exception as e:
            logger.error(f'Failed to get chunks: {str(e)}')
            return []

    async def query_async(self, query: Union[str, Query], corpus_id: Optional[str]=None, query_transforms: Optional[List]=None) -> RagResult:
        """Execute a query across indices and return processed results asynchronously.

        Performs query preprocessing, asynchronous retrieval, and post-processing.

        Args:
            query (Union[str, Query]): Query string or Query object.
            corpus_id (Optional[str]): Specific corpus to query. If None, queries all corpora.
            query_transforms (Optional[List]): Query Transforms is used to augment query in pre-processing.

        Returns:
            RagResult: Retrieved chunks with scores and metadata.

        Raises:
            Exception: If query processing fails.
        """
        try:
            if isinstance(query, str):
                query = Query(query_str=query, top_k=self.config.retrieval.top_k)
            if not self.indices or (corpus_id and corpus_id not in self.indices):
                logger.warning(f'No indices found for corpus {corpus_id or 'any'}')
                return RagResult(corpus=Corpus(chunks=[]), scores=[], metadata={'query': query.query_str})
            if query_transforms and query_transforms is not None:
                for t in query_transforms:
                    query = t(query)
            results = []
            target_corpora = [corpus_id] if corpus_id else self.indices.keys()
            tasks = []
            for cid in target_corpora:
                for idx_type, retriever in self.retrievers[cid].items():
                    if query.metadata_filters and query.metadata_filters.get('index_type') and (query.metadata_filters['index_type'] != idx_type):
                        continue
                    task = retriever.aretrieve(Query(query_str=query.query_str, top_k=query.top_k or self.config.retrieval.top_k, similarity_cutoff=query.similarity_cutoff, keyword_filters=query.keyword_filters, metadata_filters=query.metadata_filters))
                    tasks.append((task, cid, idx_type))
            retrieval_tasks = [task for task, _, _ in tasks]
            retrieval_results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)
            for (_, cid, idx_type), result in zip(tasks, retrieval_results):
                if isinstance(result, Exception):
                    logger.error(f'Retrieval failed for {idx_type} in corpus {cid}: {str(result)}')
                else:
                    results.append(result)
                    logger.info(f'Retrieved {len(result.corpus.chunks)} chunks from {idx_type} retriever for corpus {cid}')
            if not results:
                return RagResult(corpus=Corpus(chunks=[]), scores=[], metadata={'query': query.query_str})
            query.similarity_cutoff = self.config.retrieval.similarity_cutoff if query.similarity_cutoff is None else query.similarity_cutoff
            query.keyword_filters = self.config.retrieval.keyword_filters if query.keyword_filters is None else query.keyword_filters
            postprocessor = self.postprocessor_factory.create(self.config.retrieval.postprocessor_type, query=query)
            final_result = postprocessor.postprocess(query, results)
            if query.metadata_filters:
                final_result.corpus.chunks = [chunk for chunk in final_result.corpus.chunks if all((chunk.metadata.model_dump().get(k) == v for k, v in query.metadata_filters.items()))]
                final_result.scores = [chunk.metadata.similarity_score for chunk in final_result.corpus.chunks]
                logger.info(f'Applied metadata filters, retained {len(final_result.corpus.chunks)} chunks')
            logger.info(f'Query returned {len(final_result.corpus.chunks)} chunks after post-processing')
            return final_result
        except Exception as e:
            logger.error(f'Query failed: {str(e)}')
            raise

    def query(self, query: Union[str, Query], corpus_id: Optional[str]=None, query_transforms: Optional[List]=None) -> RagResult:
        """Synchronous wrapper for the async query method."""
        return asyncio.run(self.query_async(query, corpus_id, query_transforms))

def read(self, file_paths: Union[Sequence[str], str], exclude_files: Optional[Union[str, List, Tuple, Sequence]]=None, filter_file_by_suffix: Optional[Union[str, List, Tuple, Sequence]]=None, merge_by_file: bool=False, show_progress: bool=False, corpus_id: str=None) -> Corpus:
    """Load and chunk documents from files.

        Reads files from specified paths, processes them into documents, and chunks them into a Corpus.

        Args:
            file_paths (Union[Sequence[str], str]): Path(s) to files or directories.
            exclude_files (Optional[Union[str, List, Tuple, Sequence]]): Files to exclude.
            filter_file_by_suffix (Optional[Union[str, List, Tuple, Sequence]]): Filter files by suffix (e.g., '.pdf').
            merge_by_file (bool): Merge documents by file.
            show_progress (bool): Show loading progress.
            corpus_id (Optional[str]): Identifier for the corpus. Defaults to a UUID if None.

        Returns:
            Corpus: The chunked corpus containing processed document chunks.

        Raises:
            Exception: If document reading or chunking fails.
        """
    try:
        corpus_id = corpus_id or str(uuid4())
        documents = self.reader.load(file_paths=file_paths, exclude_files=exclude_files, filter_file_by_suffix=filter_file_by_suffix, merge_by_file=merge_by_file, show_progress=show_progress)
        if self.config.modality == 'multimodal':
            image_chunks = []
            for doc in documents:
                image_path = getattr(doc, 'image_path', None) or doc.metadata.get('file_path')
                image_mimetype = getattr(doc, 'image_mimetype', None)
                image_chunk = self.chunk_class(image_path=image_path, image_mimetype=image_mimetype, chunk_id=doc.metadata.get('file_name', f'img_{len(image_chunks)}'), metadata=ChunkMetadata(doc_id=doc.metadata.get('file_name', f'doc_{len(image_chunks)}'), corpus_id=corpus_id, **doc.metadata))
                image_chunks.append(image_chunk)
            corpus = Corpus(chunks=image_chunks, corpus_id=corpus_id)
            logger.info(f'Read {len(documents)} multimodal documents (no chunking) for corpus {corpus_id}')
        else:
            corpus = self.chunker.chunk(documents)
            corpus.corpus_id = corpus_id
            logger.info(f'Read {len(documents)} documents and created {len(corpus.chunks)} chunks for corpus {corpus_id}')
        return corpus
    except Exception as e:
        logger.error(f'Failed to read documents for corpus {corpus_id}: {str(e)}')
        raise

def add(self, index_type: str, nodes: Union[Corpus, List[NodeWithScore], List[TextNode], List[ImageNode]], corpus_id: str=None) -> None:
    """Add nodes to an index for a specific corpus.

        Initializes an index if it doesn't exist and inserts nodes, updating metadata with corpus_id and index_type.

        Args:
            index_type (str): Type of index (e.g., VECTOR, GRAPH).
            nodes (Union[Corpus, List[NodeWithScore], List[TextNode]]): Nodes or Corpus to add.
            corpus_id (str, optional): Identifier for the corpus. Defaults to a UUID if None.

        Return:
            return a sequence with id of each added node.
            
        Raises:
            Exception: If index creation or node insertion fails.
        """
    try:
        corpus_id = corpus_id or str(uuid4())
        if corpus_id not in self.indices:
            self.indices[corpus_id] = {}
            self.retrievers[corpus_id] = {}
        if index_type not in self.indices[corpus_id]:
            index = self.index_factory.create(index_type=index_type, embed_model=self.embed_model.get_embedding_model(), storage_handler=self.storage_handler, index_config=self.config.index.model_dump(exclude_unset=True) if self.config.index else {}, llm=self.llm)
            self.indices[corpus_id][index_type] = index
            self.retrievers[corpus_id][index_type] = self.retriever_factory.create(retriever_type=self.config.retrieval.retrivel_type, llm=self.llm, index=index.get_index(), graph_store=index.get_index().storage_context.graph_store, embed_model=self.embed_model.get_embedding_model(), query=Query(query_str='', top_k=self.config.retrieval.top_k if self.config.retrieval else 5), storage_handler=self.storage_handler, chunk_class=self.chunk_class)
        nodes_to_insert = nodes.to_llama_nodes() if isinstance(nodes, Corpus) else nodes
        for node in nodes_to_insert:
            node.metadata.update({'corpus_id': corpus_id, 'index_type': index_type})
        nodes_ids = self.indices[corpus_id][index_type].insert_nodes(nodes_to_insert)
        logger.info(f'Added {len(nodes_to_insert)} nodes to {index_type} index for corpus {corpus_id}')
        return nodes_ids
    except Exception as e:
        logger.error(f'Failed to add nodes to {index_type} index for corpus {corpus_id}: {str(e)}')
        return []

def _load_index(self, corpus: Corpus, corpus_id: str, index_type: str) -> Sequence[str]:
    """Helper method to load an index and its retriever."""
    try:
        if corpus_id not in self.indices:
            self.indices[corpus_id] = {}
            self.retrievers[corpus_id] = {}
        if index_type not in self.indices[corpus_id]:
            index = self.index_factory.create(index_type=index_type, embed_model=self.embed_model.get_embedding_model(), storage_handler=self.storage_handler, index_config=self.config.index.model_dump(exclude_unset=True) if self.config.index else {}, llm=self.llm)
            self.indices[corpus_id][index_type] = index
            retriever_type = RetrieverType.GRAPH if index_type == IndexType.GRAPH else RetrieverType.VECTOR
            self.retrievers[corpus_id][index_type] = self.retriever_factory.create(retriever_type=retriever_type, llm=self.llm, index=index.get_index(), graph_store=index.get_index().storage_context.graph_store, embed_model=self.embed_model.get_embedding_model(), query=Query(query_str='', top_k=self.config.retrieval.top_k if self.config.retrieval else 5), storage_handler=self.storage_handler)
        nodes = corpus.to_llama_nodes()
        for node in nodes:
            node.metadata.update({'corpus_id': corpus_id, 'index_type': index_type})
        chunk_ids = self.indices[corpus_id][index_type].load(nodes)
        logger.info(f'Inserted {len(nodes)} nodes into {index_type} index for corpus {corpus_id}')
        return chunk_ids
    except Exception as e:
        logger.error(f'Failed to load index for corpus {corpus_id}, index_type {index_type}: {str(e)}')
        raise

class ImageChunk(BaseModule):
    """An image-based chunk with lazy loading.
    
    Attributes:
        image_path (str): Path to the image file.
        image_mimetype (Optional[str]): MIME type of the image.
        chunk_id (str): Unique identifier for the chunk.
        metadata (ChunkMetadata): Metadata including embedding, similarity scores, etc.
    """

    def __init__(self, image_path: str, image_mimetype: Optional[str]=None, chunk_id: Optional[str]=None, embedding: Optional[List[float]]=None, excluded_embed_metadata_keys: List[str]=DEAFULT_EXCLUDED, excluded_llm_metadata_keys: List[str]=DEAFULT_EXCLUDED, text_template: str='{metadata_str}\n\n{content}', relationships: Dict[str, RelatedNodeInfo]={}, metadata: Optional[Union[Dict, ChunkMetadata]]=None):
        metadata = ChunkMetadata.model_validate(metadata) if isinstance(metadata, dict) else metadata or ChunkMetadata()
        super().__init__(image_path=image_path, image_mimetype=image_mimetype, chunk_id=chunk_id or str(uuid4()), embedding=embedding, excluded_embed_metadata_keys=list(set(DEAFULT_EXCLUDED + excluded_embed_metadata_keys)), excluded_llm_metadata_keys=list(set(DEAFULT_EXCLUDED + excluded_llm_metadata_keys)), text_template=text_template, relationships=relationships, metadata=metadata)
        self._cached_image = None

    def get_image(self):
        """Load PIL Image on-demand with caching."""
        if self._cached_image is None:
            from PIL import Image
            try:
                logger.debug(f'Loading image from path: {self.image_path}')
                if not self.image_path:
                    logger.error('Image path is None or empty!')
                    return None
                self._cached_image = Image.open(self.image_path)
                logger.debug(f'Successfully loaded image from {self.image_path}')
            except Exception as e:
                logger.error(f'Failed to load image from {self.image_path}: {str(e)}')
                return None
        return self._cached_image

    def get_image_bytes(self, format: str='PNG') -> Optional[bytes]:
        """Get image as bytes for embedding or processing."""
        import io
        image = self.get_image()
        if image is None:
            return None
        img_bytes = io.BytesIO()
        image.save(img_bytes, format=format)
        return img_bytes.getvalue()

    def to_llama_node(self) -> ImageNode:
        """Convert to LlamaIndex ImageNode with on-demand image loading."""
        relationships = dict()
        for k, v in self.relationships.items():
            relationships[k] = v if isinstance(v, RelatedNodeInfo) else RelatedNodeInfo.from_dict(v)
        return ImageNode(image=None, image_path=self.image_path, image_mimetype=self.image_mimetype, metadata=self.metadata.model_dump(), id_=self.chunk_id, embedding=self.embedding, excluded_llm_metadata_keys=self.excluded_llm_metadata_keys, excluded_embed_metadata_keys=self.excluded_embed_metadata_keys, text_template=self.text_template, relationships=relationships)

    @classmethod
    def from_llama_node(cls, node: ImageNode) -> 'ImageChunk':
        """Create ImageChunk from LlamaIndex ImageNode."""
        metadata = ChunkMetadata.model_validate(node.metadata)
        logger.debug(f'Creating ImageChunk from ImageNode - image_path: {node.image_path}')
        return cls(chunk_id=node.id_, image_path=node.image_path, image_mimetype=node.image_mimetype, metadata=metadata, embedding=node.embedding, excluded_embed_metadata_keys=node.excluded_embed_metadata_keys, excluded_llm_metadata_keys=node.excluded_llm_metadata_keys, text_template=node.text_template, relationships=node.relationships)

def get_image(self):
    """Load PIL Image on-demand with caching."""
    if self._cached_image is None:
        from PIL import Image
        try:
            logger.debug(f'Loading image from path: {self.image_path}')
            if not self.image_path:
                logger.error('Image path is None or empty!')
                return None
            self._cached_image = Image.open(self.image_path)
            logger.debug(f'Successfully loaded image from {self.image_path}')
        except Exception as e:
            logger.error(f'Failed to load image from {self.image_path}: {str(e)}')
            return None
    return self._cached_image

def get_image_bytes(self, format: str='PNG') -> Optional[bytes]:
    """Get image as bytes for embedding or processing."""
    import io
    image = self.get_image()
    if image is None:
        return None
    img_bytes = io.BytesIO()
    image.save(img_bytes, format=format)
    return img_bytes.getvalue()

class Corpus(BaseModule):
    """A generic collection of document chunks for RAG processing.

    Attributes:
        corpus_id (str): The unique id for corpus.
        chunks (List[Union[TextChunk, ImageChunk]]): List of chunks in the corpus.
        chunk_index (Dict[str, Union[TextChunk, ImageChunk]]): Index of chunks by chunk_id for fast lookup.
        metadata (Optional[IndexMetadata]): the metadata for this corpus.
    """

    def __init__(self, chunks: Optional[List[Union[TextChunk, ImageChunk]]]=None, corpus_id: Optional[str]=None, metadata: Optional[Union[IndexMetadata, Dict]]=None):
        corpus_id = uuid4() if corpus_id is None else corpus_id
        chunks = [] if chunks is None else chunks
        chunk_index = {} if chunks is None else {chunk.chunk_id: chunk for chunk in chunks}
        if metadata is None:
            metadata = {}
        elif isinstance(metadata, IndexMetadata):
            metadata = metadata.model_dump()
        super().__init__(corpus_id=corpus_id, chunks=chunks, chunk_index=chunk_index, metadata=metadata)

    def to_llama_nodes(self) -> List[BaseNode]:
        """Convert to list of LlamaIndex Nodes."""
        if not self.chunks:
            self.chunks = []
        return [chunk.to_llama_node() for chunk in self.chunks]

    @classmethod
    def from_llama_nodes(cls, nodes: List[BaseNode]) -> 'Corpus':
        """Create a Corpus from a list of LlamaIndex Nodes.

        Args:
            nodes (List[BaseNode]): The LlamaIndex Nodes to convert.

        Returns:
            Corpus: A new Corpus instance.
        """
        chunks = []
        for node in nodes:
            if isinstance(node, ImageNode):
                chunks.append(ImageChunk.from_llama_node(node))
            else:
                chunks.append(TextChunk.from_llama_node(node))
        return cls(chunks)

    def add_chunk(self, batch_chunk: Union[TextChunk, ImageChunk, List[Union[TextChunk, ImageChunk]]]):
        """Add a batch chunk to the corpus and update index."""
        if not isinstance(batch_chunk, list):
            batch_chunk = [batch_chunk]
        for chunk in batch_chunk:
            self.chunks.append(chunk)
            self.chunk_index[chunk.chunk_id] = chunk

    def get_chunk(self, chunk_id: str) -> Optional[Union[TextChunk, ImageChunk]]:
        """Retrieve a chunk by its ID."""
        return self.chunk_index.get(chunk_id)

    def remove_chunk(self, chunk_id: str):
        """Remove a chunk by its ID."""
        self.chunks = [chunk for chunk in self.chunks if chunk.chunk_id != chunk_id]
        self.chunk_index.pop(chunk_id, None)

    def filter_by_doc_id(self, doc_id: str) -> List[Union[TextChunk, ImageChunk]]:
        """Filter chunks by parent document ID."""
        return [chunk for chunk in self.chunks if hasattr(chunk.metadata, 'doc_id') and chunk.metadata.doc_id == doc_id]

    def filter_by_similarity(self, threshold: float) -> List[Union[TextChunk, ImageChunk]]:
        """Filter chunks by similarity score."""
        return [chunk for chunk in self.chunks if chunk.metadata.similarity_score and chunk.metadata.similarity_score >= threshold]

    def sort_by_similarity(self, reverse: bool=True) -> List[Union[TextChunk, ImageChunk]]:
        """Sort chunks by similarity score (descending by default)."""
        return sorted([chunk for chunk in self.chunks if chunk.metadata.similarity_score is not None], key=lambda x: x.metadata.similarity_score, reverse=reverse)

    def to_dict(self, round_trip=False) -> Dict:
        """Convert corpus to dictionary for serialization."""
        return [self.model_dump(round_trip=round_trip)]

    def to_json(self, indent: int=2, round_trip=True) -> str:
        """Convert corpus to JSON string."""
        return json.dumps(self.to_dict(round_trip), indent=indent, ensure_ascii=False)

    def to_jsonl(self, output_path: str, indent: int=0):
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in self.chunks:
                json_str = chunk.to_json(indent=None)
                if '\n' in json_str:
                    print(f'Chunk {chunk.chunk_id} contains newlines in JSON, which may break JSONL format.')
                f.write(json_str + '\n')

    @classmethod
    def from_jsonl(cls, input_path: str, corpus_id: Optional[str]=None) -> 'Corpus':
        chunks = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                chunk_dict = json.loads(line.strip())
                metadata = ChunkMetadata.model_validate(chunk_dict['metadata'])
                chunk = Chunk(chunk_id=chunk_dict['chunk_id'], text=chunk_dict['text'], metadata=metadata, embedding=chunk_dict['embedding'], start_char_idx=chunk_dict['start_char_idx'], end_char_idx=chunk_dict['end_char_idx'], excluded_embed_metadata_keys=chunk_dict['excluded_embed_metadata_keys'], excluded_llm_metadata_keys=chunk_dict['excluded_llm_metadata_keys'], relationships={k: RelatedNodeInfo(**v) for k, v in chunk_dict['relationships'].items()})
                chunks.append(chunk)
        return cls(chunks=chunks, corpus_id=corpus_id)

    def __str__(self) -> str:
        stats = self.get_stats()
        return f'Corpus(chunks={stats['chunk_count']}, unique_docs={stats['unique_docs']}, avg_word_count={stats['avg_word_count']:.1f}, strategies={stats['strategies']})'

    def __repr__(self) -> str:
        return f'Corpus(chunks={len(self.chunks)}, chunk_index_keys={list(self.chunk_index.keys())})'

    def __len__(self) -> int:
        return len(self.chunks)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the corpus."""
        if not self.chunks:
            return {'chunk_count': 0, 'unique_docs': 0, 'avg_word_count': 0.0, 'strategies': set()}
        unique_docs = set()
        total_word_count = 0
        strategies = set()
        for chunk in self.chunks:
            if hasattr(chunk.metadata, 'doc_id') and chunk.metadata.doc_id:
                unique_docs.add(chunk.metadata.doc_id)
            if hasattr(chunk.metadata, 'word_count') and chunk.metadata.word_count:
                total_word_count += chunk.metadata.word_count
            if hasattr(chunk.metadata, 'chunking_strategy') and chunk.metadata.chunking_strategy:
                strategies.add(chunk.metadata.chunking_strategy)
        avg_word_count = total_word_count / len(self.chunks) if self.chunks else 0.0
        return {'chunk_count': len(self.chunks), 'unique_docs': len(unique_docs), 'avg_word_count': avg_word_count, 'strategies': strategies}

def to_llama_nodes(self) -> List[BaseNode]:
    """Convert to list of LlamaIndex Nodes."""
    if not self.chunks:
        self.chunks = []
    return [chunk.to_llama_node() for chunk in self.chunks]

@classmethod
def from_llama_nodes(cls, nodes: List[BaseNode]) -> 'Corpus':
    """Create a Corpus from a list of LlamaIndex Nodes.

        Args:
            nodes (List[BaseNode]): The LlamaIndex Nodes to convert.

        Returns:
            Corpus: A new Corpus instance.
        """
    chunks = []
    for node in nodes:
        if isinstance(node, ImageNode):
            chunks.append(ImageChunk.from_llama_node(node))
        else:
            chunks.append(TextChunk.from_llama_node(node))
    return cls(chunks)

class HuggingFaceEmbedding(BaseEmbedding):
    """HuggingFace embedding model compatible with LlamaIndex BaseEmbedding."""
    model: SentenceTransformer = None
    _dimension: int = None
    model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'
    embed_batch_size: int = 10
    device: Optional[str] = None
    normalize: bool = False
    model_kwargs: Dict = {}

    def __init__(self, model_name: str='sentence-transformers/all-MiniLM-L6-v2', device: Optional[str]=None, normalize: bool=False, **model_kwargs):
        super().__init__(model_name=model_name, embed_batch_size=10)
        self.device = device
        self.normalize = normalize
        self.model_kwargs = model_kwargs or {}
        if not EmbeddingProvider.validate_model(EmbeddingProvider.HUGGINGFACE, model_name):
            raise ValueError(f'Unsupported HuggingFace model: {model_name}. Supported models: {SUPPORTED_MODELS['huggingface']}')
        try:
            self.model = SentenceTransformer(model_name, device=device, **model_kwargs)
            logger.debug(f'Initialized HuggingFace embedding model: {model_name}')
        except Exception as e:
            logger.error(f'Failed to initialize HuggingFace embedding: {str(e)}')
            raise
        self._dimension = self.model.get_sentence_embedding_dimension()

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a query string."""
        try:
            embedding = self.model.encode(query, normalize_embeddings=self.normalize, convert_to_numpy=True).tolist()
            return embedding
        except Exception as e:
            logger.error(f'Failed to encode query: {str(e)}')
            raise

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for a text string."""
        try:
            embedding = self.model.encode(text, normalize_embeddings=self.normalize, convert_to_numpy=True).tolist()
            return embedding
        except Exception as e:
            logger.error(f'Failed to encode text: {str(e)}')
            raise

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts synchronously."""
        try:
            embeddings = self.model.encode(texts, normalize_embeddings=self.normalize, convert_to_numpy=True, batch_size=self.embed_batch_size).tolist()
            return embeddings
        except Exception as e:
            logger.error(f'Failed to encode texts: {str(e)}')
            raise

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Asynchronous query embedding (falls back to sync)."""
        return self._get_query_embedding(query)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

def _get_query_embedding(self, query: str) -> List[float]:
    """Get embedding for a query string."""
    try:
        embedding = self.model.encode(query, normalize_embeddings=self.normalize, convert_to_numpy=True).tolist()
        return embedding
    except Exception as e:
        logger.error(f'Failed to encode query: {str(e)}')
        raise

def _get_text_embedding(self, text: str) -> List[float]:
    """Get embedding for a text string."""
    try:
        embedding = self.model.encode(text, normalize_embeddings=self.normalize, convert_to_numpy=True).tolist()
        return embedding
    except Exception as e:
        logger.error(f'Failed to encode text: {str(e)}')
        raise

def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
    """Get embeddings for a list of texts synchronously."""
    try:
        embeddings = self.model.encode(texts, normalize_embeddings=self.normalize, convert_to_numpy=True, batch_size=self.embed_batch_size).tolist()
        return embeddings
    except Exception as e:
        logger.error(f'Failed to encode texts: {str(e)}')
        raise

class HuggingFaceEmbeddingWrapper(BaseEmbeddingWrapper):
    """Wrapper for HuggingFace embedding models."""

    def __init__(self, model_name: str='sentence-transformers/all-MiniLM-L6-v2', device: Optional[str]=None, normalize: bool=True, **model_kwargs):
        self.model_name = model_name
        self.device = device
        self.normalize = normalize
        self.model_kwargs = model_kwargs
        self._embedding_model = None
        self._embedding_model = self.get_embedding_model()

    def get_embedding_model(self) -> BaseEmbedding:
        """Return the LlamaIndex-compatible embedding model."""
        if self._embedding_model is None:
            try:
                self._embedding_model = HuggingFaceEmbedding(model_name=self.model_name, device=self.device, normalize=self.normalize, **self.model_kwargs)
                logger.debug(f'Initialized HuggingFace embedding wrapper for model: {self.model_name}')
            except Exception as e:
                logger.error(f'Failed to initialize HuggingFace embedding wrapper: {str(e)}')
                raise
        return self._embedding_model

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self._embedding_model.dimension

def get_embedding_model(self) -> BaseEmbedding:
    """Return the LlamaIndex-compatible embedding model."""
    if self._embedding_model is None:
        try:
            self._embedding_model = HuggingFaceEmbedding(model_name=self.model_name, device=self.device, normalize=self.normalize, **self.model_kwargs)
            logger.debug(f'Initialized HuggingFace embedding wrapper for model: {self.model_name}')
        except Exception as e:
            logger.error(f'Failed to initialize HuggingFace embedding wrapper: {str(e)}')
            raise
    return self._embedding_model

class OpenAIEmbedding(BaseEmbedding):
    """OpenAI embedding model compatible with LlamaIndex BaseEmbedding."""
    api_key: str
    client: OpenAI = None
    base_url: str = 'https://api.openai.com/v1'
    model_name: str = 'text-embedding-3-small'
    embed_batch_size: int = 10
    dimensions: Optional[int] = None
    kwargs: Optional[Dict] = {}

    def __init__(self, model_name: str='text-embedding-3-small', api_key: str=None, dimensions: int=None, base_url: str=None, **kwargs):
        api_key = api_key or os.getenv('OPENAI_API_KEY') or ''
        super().__init__(api_key=api_key, model_name=model_name, embed_batch_size=10)
        base_url = base_url or os.getenv('OPENAI_API_BASE') or os.getenv('OPENAI_BASE_URL') or 'https://api.openai.com/v1'
        if os.environ.get('OPENAI_API_BASE'):
            warnings.warn("The environment variable 'OPENAI_API_BASE' is deprecated and will be removed in the 0.1.80. Please use 'OPENAI_BASE_URL' instead.", DeprecationWarning)
        self.base_url = base_url
        self.dimensions = dimensions
        self.kwargs = kwargs
        if not EmbeddingProvider.validate_model(EmbeddingProvider.OPENAI, model_name):
            raise ValueError(f'Unsupported OpenAI model: {model_name}. Supported models: {SUPPORTED_MODELS['openai']}')
        if dimensions is not None and model_name not in SUPPORTED_DIMENSIONS:
            logger.warning(f"Dimensions parameter is not supported for model {model_name}. Only '{SUPPORTED_DIMENSIONS}' support custom dimensions. Ignoring dimensions parameter.")
            self.dimensions = None
        elif dimensions is None and model_name in SUPPORTED_DIMENSIONS:
            self.dimensions = dimensions or MODEL_DIMENSIONS.get(model_name)
        try:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.debug(f'Initialized OpenAI embedding model: {model_name}')
        except Exception as e:
            logger.error(f'Failed to initialize OpenAI client: {str(e)}')
            raise

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a query string."""
        try:
            query = query.replace('\n', ' ')
            response = self.client.embeddings.create(input=[query], model=self.model_name, dimensions=self.dimensions, **self.kwargs)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f'Failed to encode query: {str(e)}')
            raise

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for a text string."""
        try:
            text = text.replace('\n', ' ')
            response = self.client.embeddings.create(input=[text], model=self.model_name, dimensions=self.dimensions, **self.kwargs)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f'Failed to encode text: {str(e)}')
            raise

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Asynchronous query embedding."""
        return self._get_query_embedding(query)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts synchronously."""
        try:
            texts = [text.replace('\n', ' ') for text in texts]
            response = self.client.embeddings.create(input=texts, model=self.model_name, dimensions=self.dimensions, **self.kwargs)
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f'Failed to encode texts: {str(e)}')
            raise

def _get_query_embedding(self, query: str) -> List[float]:
    """Get embedding for a query string."""
    try:
        query = query.replace('\n', ' ')
        response = self.client.embeddings.create(input=[query], model=self.model_name, dimensions=self.dimensions, **self.kwargs)
        return response.data[0].embedding
    except Exception as e:
        logger.error(f'Failed to encode query: {str(e)}')
        raise

def _get_text_embedding(self, text: str) -> List[float]:
    """Get embedding for a text string."""
    try:
        text = text.replace('\n', ' ')
        response = self.client.embeddings.create(input=[text], model=self.model_name, dimensions=self.dimensions, **self.kwargs)
        return response.data[0].embedding
    except Exception as e:
        logger.error(f'Failed to encode text: {str(e)}')
        raise

def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
    """Get embeddings for a list of texts synchronously."""
    try:
        texts = [text.replace('\n', ' ') for text in texts]
        response = self.client.embeddings.create(input=texts, model=self.model_name, dimensions=self.dimensions, **self.kwargs)
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f'Failed to encode texts: {str(e)}')
        raise

class OpenAIEmbeddingWrapper(BaseEmbeddingWrapper):
    """Wrapper for OpenAI embedding models."""

    def __init__(self, model_name: str='text-embedding-3-small', api_key: str=None, dimensions: int=None, base_url: str=None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self._dimensions = MODEL_DIMENSIONS.get(self.model_name, None) or dimensions
        self.base_url = base_url
        self.kwargs = kwargs
        self._embedding_model = None
        self._embedding_model = self.get_embedding_model()

    def get_embedding_model(self) -> BaseEmbedding:
        """Return the LlamaIndex-compatible embedding model."""
        if getattr(self, '_embedding_model', None) is None:
            try:
                self._embedding_model = OpenAIEmbedding(model_name=self.model_name, api_key=self.api_key, dimensions=self._dimensions, base_url=self.base_url, **self.kwargs)
                logger.debug(f'Initialized OpenAI embedding wrapper for model: {self.model_name}')
            except Exception as e:
                logger.error(f'Failed to initialize OpenAI embedding wrapper: {str(e)}')
                raise
        return self._embedding_model

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self._dimensions

def get_embedding_model(self) -> BaseEmbedding:
    """Return the LlamaIndex-compatible embedding model."""
    if getattr(self, '_embedding_model', None) is None:
        try:
            self._embedding_model = OpenAIEmbedding(model_name=self.model_name, api_key=self.api_key, dimensions=self._dimensions, base_url=self.base_url, **self.kwargs)
            logger.debug(f'Initialized OpenAI embedding wrapper for model: {self.model_name}')
        except Exception as e:
            logger.error(f'Failed to initialize OpenAI embedding wrapper: {str(e)}')
            raise
    return self._embedding_model

class OllamaEmbedding(BaseEmbedding):
    """Ollama embedding model compatible with LlamaIndex BaseEmbedding."""
    base_url: str = None
    client: Client = None
    model_name: str = 'nomic-embed-text'
    embed_batch_size: int = 10
    embedding_dims: int = None
    kwargs: Optional[Dict] = {}

    def __init__(self, model_name: str='nomic-embed-text', base_url: str=None, embedding_dims: int=None, **kwargs):
        super().__init__(model_name=model_name, embed_batch_size=10)
        self.base_url = base_url or 'http://localhost:11434'
        self.embedding_dims = embedding_dims or 512
        self.kwargs = kwargs
        if not EmbeddingProvider.validate_model(EmbeddingProvider.OLLAMA, model_name):
            raise ValueError(f'Unsupported Ollama model: {model_name}. Supported models: {SUPPORTED_MODELS['ollama']}')
        try:
            self.client = Client(host=self.base_url)
            self._ensure_model_exists()
            logger.debug(f'Initialized Ollama embedding model: {model_name}')
        except Exception as e:
            logger.error(f'Failed to initialize Ollama client: {str(e)}')
            raise

    def _ensure_model_exists(self):
        """Ensure the specified model exists locally, pulling it if necessary."""
        try:
            local_models = self.client.list()['models']
            if not any((model.get('name') == self.model_name for model in local_models)):
                logger.info(f'Pulling Ollama model: {self.model_name}')
                self.client.pull(self.model_name)
        except Exception as e:
            logger.error(f'Failed to ensure Ollama model exists: {str(e)}')
            raise

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a query string."""
        try:
            response = self.client.embeddings(model=self.model_name, prompt=query, **self.kwargs)
            return response['embedding']
        except Exception as e:
            logger.error(f'Failed to encode query: {str(e)}')
            raise

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for a text string."""
        try:
            response = self.client.embeddings(model=self.model_name, prompt=text, **self.kwargs)
            return response['embedding']
        except Exception as e:
            logger.error(f'Failed to encode text: {str(e)}')
            raise

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts synchronously."""
        try:
            embeddings = []
            for i in range(0, len(texts), self.embed_batch_size):
                batch = texts[i:i + self.embed_batch_size]
                batch_embeddings = [self._get_text_embedding(text) for text in batch]
                embeddings.extend(batch_embeddings)
            return embeddings
        except Exception as e:
            logger.error(f'Failed to encode texts: {str(e)}')
            raise

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Asynchronous query embedding (falls back to sync)."""
        return self._get_query_embedding(query)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self.embedding_dims

def _ensure_model_exists(self):
    """Ensure the specified model exists locally, pulling it if necessary."""
    try:
        local_models = self.client.list()['models']
        if not any((model.get('name') == self.model_name for model in local_models)):
            logger.info(f'Pulling Ollama model: {self.model_name}')
            self.client.pull(self.model_name)
    except Exception as e:
        logger.error(f'Failed to ensure Ollama model exists: {str(e)}')
        raise

def _get_query_embedding(self, query: str) -> List[float]:
    """Get embedding for a query string."""
    try:
        response = self.client.embeddings(model=self.model_name, prompt=query, **self.kwargs)
        return response['embedding']
    except Exception as e:
        logger.error(f'Failed to encode query: {str(e)}')
        raise

def _get_text_embedding(self, text: str) -> List[float]:
    """Get embedding for a text string."""
    try:
        response = self.client.embeddings(model=self.model_name, prompt=text, **self.kwargs)
        return response['embedding']
    except Exception as e:
        logger.error(f'Failed to encode text: {str(e)}')
        raise

def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
    """Get embeddings for a list of texts synchronously."""
    try:
        embeddings = []
        for i in range(0, len(texts), self.embed_batch_size):
            batch = texts[i:i + self.embed_batch_size]
            batch_embeddings = [self._get_text_embedding(text) for text in batch]
            embeddings.extend(batch_embeddings)
        return embeddings
    except Exception as e:
        logger.error(f'Failed to encode texts: {str(e)}')
        raise

class OllamaEmbeddingWrapper(BaseEmbeddingWrapper):
    """Wrapper for Ollama embedding models."""

    def __init__(self, model_name: str='nomic-embed-text', base_url: str=None, dimensions: int=None, **kwargs):
        self.model_name = model_name
        self.base_url = base_url
        self._dimensions = MODEL_DIMENSIONS.get(model_name, None) or dimensions
        self.kwargs = kwargs
        self._embedding_model = None
        self._embedding_model = self.get_embedding_model()

    def get_embedding_model(self) -> BaseEmbedding:
        """Return the LlamaIndex-compatible embedding model."""
        if self._embedding_model is None:
            try:
                self._embedding_model = OllamaEmbedding(model_name=self.model_name, base_url=self.base_url, embedding_dims=self._dimensions, **self.kwargs)
                logger.debug(f'Initialized Ollama embedding wrapper for model: {self.model_name}')
            except Exception as e:
                logger.error(f'Failed to initialize Ollama embedding wrapper: {str(e)}')
                raise
        return self._embedding_model

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self._dimensions

def get_embedding_model(self) -> BaseEmbedding:
    """Return the LlamaIndex-compatible embedding model."""
    if self._embedding_model is None:
        try:
            self._embedding_model = OllamaEmbedding(model_name=self.model_name, base_url=self.base_url, embedding_dims=self._dimensions, **self.kwargs)
            logger.debug(f'Initialized Ollama embedding wrapper for model: {self.model_name}')
        except Exception as e:
            logger.error(f'Failed to initialize Ollama embedding wrapper: {str(e)}')
            raise
    return self._embedding_model

class GraphRetriever(BaseRetrieverWrapper):
    """Wrapper for graph-based retrieval."""

    def __init__(self, llm: BaseLLM, graph_store: PropertyGraphStore, embed_model: Optional[BaseEmbedding], include_text: bool=True, _use_async: bool=True, vector_store: Optional[BasePydanticVectorStore]=None, top_k: int=5):
        super().__init__()
        self.graph_store = graph_store
        self._embed_model = embed_model
        self.vector_store = vector_store
        self._llm = llm
        sub_retrievers = [BasicLLMSynonymRetriever(graph_store=graph_store, include_text=include_text, llm=llm)]
        if self._embed_model and (self.graph_store.supports_vector_queries or self.vector_store):
            sub_retrievers.append(VectorContextRetriever(graph_store=self.graph_store, vector_store=self.vector_store, include_text=include_text, embed_model=self._embed_model, similarity_top_k=top_k))
        self.retriever = PGRetriever(sub_retrievers, use_async=_use_async)

    async def aretrieve(self, query: Query) -> RagResult:
        try:
            subretriever_bool = [isinstance(sub, VectorContextRetriever) for sub in self.retriever.sub_retrievers]
            if any(subretriever_bool):
                ind = subretriever_bool.index(True)
                self.retriever.sub_retrievers[ind]._similarity_top_k = query.top_k
            nodes = await self.retriever.aretrieve(query.query_str)
            corpus = Corpus()
            scores = []
            if nodes is None:
                return RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'graph'})
            for score_node in nodes:
                node = score_node.node
                node.metadata = json.loads(node.metadata.get('metadata', '{}'))
                chunk = Chunk.from_llama_node(node)
                chunk.metadata.similarity_score = score_node.score or 0.0
                corpus.add_chunk(chunk)
                scores.extend([score_node.score or 0.0])
            result = RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'graph'})
            logger.info(f'Graph retrieved {len(corpus.chunks)} chunks')
            return result
        except Exception as e:
            logger.error(f'Graph retrieval failed: {str(e)}')
            raise

    def retrieve(self, query: Query) -> RagResult:
        try:
            subretriever_bool = [isinstance(sub, VectorContextRetriever) for sub in self.retrieve.sub_retrievers]
            if any(subretriever_bool):
                ind = subretriever_bool.index(True)
                self.retriever[ind].similarity_top_k = query.top_k
            nodes = self.retriever.retrieve(query.query_str)
            corpus = Corpus()
            scores = []
            if nodes is None:
                return RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'graph'})
            for score_node in nodes:
                node = score_node.node
                flattened_metadata = {}
                for key, value in node.metadata.items():
                    flattened_metadata[key] = json.loads(value)
                node.metadata = flattened_metadata
                chunk = Chunk.from_llama_node(score_node.node)
                chunk.metadata.similarity_score = score_node.score or 0.0
                corpus.add_chunk(chunk)
                scores.extend([score_node.score or 0.0])
            result = RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'graph'})
            logger.info(f'Vector retrieved {len(corpus.chunks)} chunks')
            return result
        except Exception as e:
            logger.error(f'Vector retrieval failed: {str(e)}')
            raise

    def get_retriever(self) -> PGRetriever:
        logger.debug('Returning graph retriever')
        return self.retriever

def retrieve(self, query: Query) -> RagResult:
    try:
        subretriever_bool = [isinstance(sub, VectorContextRetriever) for sub in self.retrieve.sub_retrievers]
        if any(subretriever_bool):
            ind = subretriever_bool.index(True)
            self.retriever[ind].similarity_top_k = query.top_k
        nodes = self.retriever.retrieve(query.query_str)
        corpus = Corpus()
        scores = []
        if nodes is None:
            return RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'graph'})
        for score_node in nodes:
            node = score_node.node
            flattened_metadata = {}
            for key, value in node.metadata.items():
                flattened_metadata[key] = json.loads(value)
            node.metadata = flattened_metadata
            chunk = Chunk.from_llama_node(score_node.node)
            chunk.metadata.similarity_score = score_node.score or 0.0
            corpus.add_chunk(chunk)
            scores.extend([score_node.score or 0.0])
        result = RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'graph'})
        logger.info(f'Vector retrieved {len(corpus.chunks)} chunks')
        return result
    except Exception as e:
        logger.error(f'Vector retrieval failed: {str(e)}')
        raise

class VectorRetriever(BaseRetrieverWrapper):
    """Wrapper for vector-based retrieval."""

    def __init__(self, index: BaseIndex, top_k: int=5, chunk_class=None):
        super().__init__()
        self.index = index
        self.top_k = top_k
        self.chunk_class = chunk_class
        self.retriever = VectorIndexRetriever(index=self.index, similarity_top_k=self.top_k)

    async def aretrieve(self, query: Query) -> RagResult:
        try:
            self.retriever.similarity_top_k = query.top_k
            nodes = await self.retriever.aretrieve(query.query_str)
            corpus = Corpus()
            scores = []
            if nodes is None:
                return RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'vector'})
            for score_node in nodes:
                if self.chunk_class is None:
                    raise ValueError('chunk_class not set - RAGEngine must pass chunk class based on config')
                chunk = self.chunk_class.from_llama_node(score_node.node)
                chunk.metadata.similarity_score = score_node.score or 0.0
                corpus.add_chunk(chunk)
                scores.extend([score_node.score or 0.0])
            result = RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'vector'})
            logger.info(f'Vector retrieved {len(corpus.chunks)} chunks')
            return result
        except Exception as e:
            logger.error(f'Vector retrieval failed: {str(e)}')
            raise

    def retrieve(self, query: Query) -> RagResult:
        try:
            self.retriever.similarity_top_k = query.top_k
            nodes = self.retriever.retrieve(query.query_str)
            corpus = Corpus()
            scores = []
            if nodes is None:
                return RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'vector'})
            for score_node in nodes:
                if self.chunk_class is None:
                    raise ValueError('chunk_class not set - RAGEngine must pass chunk class based on config')
                chunk = self.chunk_class.from_llama_node(score_node.node)
                chunk.metadata.similarity_score = score_node.score or 0.0
                corpus.add_chunk(chunk)
                scores.extend([score_node.score or 0.0])
            result = RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'vector'})
            logger.info(f'Vector retrieved {len(corpus.chunks)} chunks')
            return result
        except Exception as e:
            logger.error(f'Vector retrieval failed: {str(e)}')
            raise

    def get_retriever(self) -> VectorIndexRetriever:
        logger.debug('Returning vector retriever')
        return self.retriever

def retrieve(self, query: Query) -> RagResult:
    try:
        self.retriever.similarity_top_k = query.top_k
        nodes = self.retriever.retrieve(query.query_str)
        corpus = Corpus()
        scores = []
        if nodes is None:
            return RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'vector'})
        for score_node in nodes:
            if self.chunk_class is None:
                raise ValueError('chunk_class not set - RAGEngine must pass chunk class based on config')
            chunk = self.chunk_class.from_llama_node(score_node.node)
            chunk.metadata.similarity_score = score_node.score or 0.0
            corpus.add_chunk(chunk)
            scores.extend([score_node.score or 0.0])
        result = RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'retriever': 'vector'})
        logger.info(f'Vector retrieved {len(corpus.chunks)} chunks')
        return result
    except Exception as e:
        logger.error(f'Vector retrieval failed: {str(e)}')
        raise

class LLamaIndexReader:
    """A universal file reader based on LlamaIndex's SimpleDirectoryReader.

    This class provides a flexible interface for loading documents from files or directories,
    supporting various formats (e.g., PDF, Word, Markdown) with customizable filtering and metadata.

    Attributes:
        recursive (bool): Whether to recursively load files from directories.
        exclude_hidden (bool): Whether to exclude hidden files (starting with '.').
        num_workers (Optional[int]): Number of worker threads for parallel loading.
        num_files_limits (Optional[int]): Maximum number of files to load.
        custom_metadata_function (Optional[Callable]): Custom function to extract metadata.
        extern_file_extractor (Optional[Dict]): Custom file extractors for specific file types.
        errors (str): Error handling strategy for file reading (e.g., 'ignore', 'strict').
        encoding (str): File encoding (default: 'utf-8').
    """

    def __init__(self, recursive: bool=False, exclude_hidden: bool=True, num_workers: Optional[int]=None, num_files_limits: Optional[int]=None, custom_metadata_function: Optional[Callable]=None, extern_file_extractor: Optional[Dict]=None, errors: str='ignore', encoding: str='utf-8'):
        self.recursive = recursive
        self.exclude_hidden = exclude_hidden
        self.num_workers = num_workers
        self.num_files_limits = num_files_limits
        self.custom_metadata_function = custom_metadata_function
        self.extern_file_extractor = extern_file_extractor
        self.errors = errors
        self.encoding = encoding

    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate and convert a path to a Path object.

        Args:
            path: A string or Path object representing a file or directory.

        Returns:
            Path: A validated Path object.

        Raises:
            FileNotFoundError: If the path does not exist.
            ValueError: If the path is invalid.
        """
        path = Path(path)
        if not path.exists():
            logger.error(f'Path does not exist: {path}')
            raise FileNotFoundError(f'Path does not exist: {path}')
        return path

    def _check_input(self, input_data: Union[str, List, Tuple], is_file: bool=True) -> Union[List[Path], Path]:
        """Check input to a list of Path objects or a single Path for directories.

        Args:
            input_data: A string, list, or tuple of file/directory paths.
            is_file: Whether to treat input as file paths (True) or directory (False).

        Returns:
            Union[List[Path], Path]: Valied file paths or directory path.

        Raises:
            ValueError: If input type is invalid.
        """
        if isinstance(input_data, str):
            return self._validate_path(input_data)
        elif isinstance(input_data, (list, tuple)):
            if is_file:
                return [self._validate_path(p) for p in input_data]
            else:
                return self._validate_path(input_data[0])
        else:
            logger.error(f'Invalid input type: {type(input_data)}')
            raise ValueError(f'Invalid input type: {type(input_data)}')

    def load(self, file_paths: Union[str, List, Tuple], exclude_files: Optional[Union[str, List, Tuple]]=None, filter_file_by_suffix: Optional[Union[str, List, Tuple]]=None, merge_by_file: bool=False, show_progress: bool=False, use_async: bool=False) -> List[Document]:
        """Load documents from files or directories.

        Args:
            file_paths: A string, list, or tuple of file paths or a directory path.
            exclude_files: Files to exclude from loading.
            filter_file_by_suffix: File extensions to include (e.g., ['.pdf', '.docx']).

        Returns:
            List[Document]: List of loaded documents.

        Raises:
            FileNotFoundError: If input paths are invalid.
            RuntimeError: If document loading fails.
        """
        try:
            input_files = None
            input_dir = None
            if isinstance(file_paths, (list, tuple)):
                input_files = self._check_input(file_paths, is_file=True)
            else:
                path = self._check_input(file_paths, is_file=False)
                if path.is_dir():
                    input_dir = path
                else:
                    input_files = [path]
            exclude_files = self._check_input(exclude_files, is_file=True) if exclude_files else None
            filter_file_by_suffix = list(filter_file_by_suffix) if isinstance(filter_file_by_suffix, (list, tuple)) else [filter_file_by_suffix] if isinstance(filter_file_by_suffix, str) else None
            reader = SimpleDirectoryReader(input_dir=input_dir, input_files=input_files, exclude=exclude_files, exclude_hidden=self.exclude_hidden, recursive=self.recursive, required_exts=filter_file_by_suffix, num_files_limit=self.num_files_limits, file_metadata=self.custom_metadata_function, file_extractor=self.extern_file_extractor, encoding=self.encoding, errors=self.errors)
            llama_docs = asyncio.run(reader.aload_data(show_progress=show_progress, num_workers=self.num_workers)) if use_async else reader.load_data(show_progress=show_progress)
            if merge_by_file:
                file_to_docs = {}
                for doc in llama_docs:
                    file_path = doc.metadata.get('file_path', '')
                    if file_path not in file_to_docs:
                        file_to_docs[file_path] = []
                    file_to_docs[file_path].append(doc)
                documents = []
                for file_path, docs in file_to_docs.items():
                    combined_text = '\n'.join((doc.text for doc in docs))
                    combined = docs[0].copy()
                    combined.text_resource.text = combined_text
                    combined.metadata['page_count'] = len(docs)
                    documents.append(Document.from_llama_document(combined))
            else:
                documents = [Document.from_llama_document(doc) for doc in llama_docs]
            logger.info(f'Loaded {len(documents)} documents')
            return documents
        except Exception as e:
            logger.error(f'Failed to load documents: {str(e)}')
            raise RuntimeError(f'Failed to load documents: {str(e)}')

def load(self, file_paths: Union[str, List, Tuple], exclude_files: Optional[Union[str, List, Tuple]]=None, filter_file_by_suffix: Optional[Union[str, List, Tuple]]=None, merge_by_file: bool=False, show_progress: bool=False, use_async: bool=False) -> List[Document]:
    """Load documents from files or directories.

        Args:
            file_paths: A string, list, or tuple of file paths or a directory path.
            exclude_files: Files to exclude from loading.
            filter_file_by_suffix: File extensions to include (e.g., ['.pdf', '.docx']).

        Returns:
            List[Document]: List of loaded documents.

        Raises:
            FileNotFoundError: If input paths are invalid.
            RuntimeError: If document loading fails.
        """
    try:
        input_files = None
        input_dir = None
        if isinstance(file_paths, (list, tuple)):
            input_files = self._check_input(file_paths, is_file=True)
        else:
            path = self._check_input(file_paths, is_file=False)
            if path.is_dir():
                input_dir = path
            else:
                input_files = [path]
        exclude_files = self._check_input(exclude_files, is_file=True) if exclude_files else None
        filter_file_by_suffix = list(filter_file_by_suffix) if isinstance(filter_file_by_suffix, (list, tuple)) else [filter_file_by_suffix] if isinstance(filter_file_by_suffix, str) else None
        reader = SimpleDirectoryReader(input_dir=input_dir, input_files=input_files, exclude=exclude_files, exclude_hidden=self.exclude_hidden, recursive=self.recursive, required_exts=filter_file_by_suffix, num_files_limit=self.num_files_limits, file_metadata=self.custom_metadata_function, file_extractor=self.extern_file_extractor, encoding=self.encoding, errors=self.errors)
        llama_docs = asyncio.run(reader.aload_data(show_progress=show_progress, num_workers=self.num_workers)) if use_async else reader.load_data(show_progress=show_progress)
        if merge_by_file:
            file_to_docs = {}
            for doc in llama_docs:
                file_path = doc.metadata.get('file_path', '')
                if file_path not in file_to_docs:
                    file_to_docs[file_path] = []
                file_to_docs[file_path].append(doc)
            documents = []
            for file_path, docs in file_to_docs.items():
                combined_text = '\n'.join((doc.text for doc in docs))
                combined = docs[0].copy()
                combined.text_resource.text = combined_text
                combined.metadata['page_count'] = len(docs)
                documents.append(Document.from_llama_document(combined))
        else:
            documents = [Document.from_llama_document(doc) for doc in llama_docs]
        logger.info(f'Loaded {len(documents)} documents')
        return documents
    except Exception as e:
        logger.error(f'Failed to load documents: {str(e)}')
        raise RuntimeError(f'Failed to load documents: {str(e)}')

class MultimodalReader:
    """An efficient image file reader for multimodal RAG.

    This class provides interface for loading images from files or directories,
    supporting various image formats with path-based lazy loading.

    Attributes:
        recursive (bool): Whether to recursively read directories.
        exclude_hidden (bool): Whether to exclude hidden files (starting with '.').
        num_files_limits (Optional[int]): Maximum number of files to read.
        errors (str): Error handling strategy for file reading (e.g., 'ignore', 'strict').
    """

    def __init__(self, recursive: bool=False, exclude_hidden: bool=True, num_files_limits: Optional[int]=None, errors: str='ignore'):
        self.recursive = recursive
        self.exclude_hidden = exclude_hidden
        self.num_files_limits = num_files_limits
        self.errors = errors

    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate and convert a path to a Path object.

        Args:
            path: A string or Path object representing a file or directory.

        Returns:
            Path: A validated Path object.

        Raises:
            FileNotFoundError: If the path does not exist.
            ValueError: If the path is invalid.
        """
        path = Path(path)
        if not path.exists():
            logger.error(f'Path does not exist: {path}')
            raise FileNotFoundError(f'Path does not exist: {path}')
        return path

    def _check_input(self, input_data: Union[str, List, Tuple], is_file: bool=True) -> Union[List[Path], Path]:
        """Check input to a list of Path objects or a single Path for directories.

        Args:
            input_data: A string, list, or tuple of file/directory paths.
            is_file: Whether to treat input as file paths (True) or directory (False).

        Returns:
            Union[List[Path], Path]: Valid file paths or directory path.

        Raises:
            ValueError: If input type is invalid.
        """
        if isinstance(input_data, str):
            return self._validate_path(input_data)
        elif isinstance(input_data, (list, tuple)):
            if is_file:
                return [self._validate_path(p) for p in input_data]
            else:
                return self._validate_path(input_data[0])
        else:
            logger.error(f'Invalid input type: {type(input_data)}')
            raise ValueError(f'Invalid input type: {type(input_data)}')

    def load(self, file_paths: Union[str, List, Tuple], exclude_files: Optional[Union[str, List, Tuple]]=None, filter_file_by_suffix: Optional[Union[str, List, Tuple]]=None, merge_by_file: bool=False, show_progress: bool=False) -> List[ImageDocument]:
        """Load images from files or directories.

        Args:
            file_paths: A string, list, or tuple of file paths or a directory path.
            exclude_files: Files to exclude from loading.
            filter_file_by_suffix: File extensions to include (e.g., ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']).
            merge_by_file: Whether to merge documents by file (unused for images, kept for compatibility).

        Returns:
            List[ImageDocument]: List of loaded ImageDocuments.

        Raises:
            FileNotFoundError: If input paths are invalid.
            RuntimeError: If image loading fails.
        """
        try:
            input_files = None
            input_dir = None
            if isinstance(file_paths, (list, tuple)):
                input_files = self._check_input(file_paths, is_file=True)
            else:
                path = self._check_input(file_paths, is_file=False)
                if path.is_dir():
                    input_dir = path
                else:
                    input_files = [path]
            exclude_files = self._check_input(exclude_files, is_file=True) if exclude_files else None
            filter_file_by_suffix = list(filter_file_by_suffix) if isinstance(filter_file_by_suffix, (list, tuple)) else [filter_file_by_suffix] if isinstance(filter_file_by_suffix, str) else None
            all_files = []
            if input_files:
                all_files = input_files
            elif input_dir:
                pattern = '**/*' if self.recursive else '*'
                all_files = [f for f in input_dir.glob(pattern) if f.is_file()]
                if self.exclude_hidden:
                    all_files = [f for f in all_files if not f.name.startswith('.')]
            if exclude_files:
                exclude_names = {f.name for f in exclude_files}
                all_files = [f for f in all_files if f.name not in exclude_names]
            if filter_file_by_suffix:
                all_files = [f for f in all_files if f.suffix.lower() in filter_file_by_suffix]
            if self.num_files_limits:
                all_files = all_files[:self.num_files_limits]
            documents = []
            for file_path in all_files:
                if show_progress:
                    logger.info(f'Processing: {file_path.name}')
                try:
                    if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']:
                        img_doc = self._process_image(file_path)
                        if img_doc:
                            documents.append(img_doc)
                except Exception as e:
                    logger.error(f'Failed to process {file_path}: {str(e)}')
                    if self.errors == 'strict':
                        raise
            logger.info(f'Loaded {len(documents)} image documents')
            return documents
        except Exception as e:
            logger.error(f'Failed to load documents: {str(e)}')
            raise RuntimeError(f'Failed to load documents: {str(e)}')

    def _process_image(self, file_path: Path) -> ImageDocument:
        """Process a single image file."""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format or 'Unknown'
            document = ImageDocument(text='', image=None, image_path=str(file_path), image_mimetype=f'image/{format_name.lower()}', metadata={'file_path': str(file_path), 'file_name': file_path.name, 'file_type': file_path.suffix, 'file_size': file_path.stat().st_size, 'creation_date': str(file_path.stat().st_ctime), 'last_modified_date': str(file_path.stat().st_mtime)})
            return document
        except Exception as e:
            logger.error(f'Failed to process image {file_path}: {str(e)}')
            if self.errors == 'strict':
                raise
            return None

def load(self, file_paths: Union[str, List, Tuple], exclude_files: Optional[Union[str, List, Tuple]]=None, filter_file_by_suffix: Optional[Union[str, List, Tuple]]=None, merge_by_file: bool=False, show_progress: bool=False) -> List[ImageDocument]:
    """Load images from files or directories.

        Args:
            file_paths: A string, list, or tuple of file paths or a directory path.
            exclude_files: Files to exclude from loading.
            filter_file_by_suffix: File extensions to include (e.g., ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']).
            merge_by_file: Whether to merge documents by file (unused for images, kept for compatibility).

        Returns:
            List[ImageDocument]: List of loaded ImageDocuments.

        Raises:
            FileNotFoundError: If input paths are invalid.
            RuntimeError: If image loading fails.
        """
    try:
        input_files = None
        input_dir = None
        if isinstance(file_paths, (list, tuple)):
            input_files = self._check_input(file_paths, is_file=True)
        else:
            path = self._check_input(file_paths, is_file=False)
            if path.is_dir():
                input_dir = path
            else:
                input_files = [path]
        exclude_files = self._check_input(exclude_files, is_file=True) if exclude_files else None
        filter_file_by_suffix = list(filter_file_by_suffix) if isinstance(filter_file_by_suffix, (list, tuple)) else [filter_file_by_suffix] if isinstance(filter_file_by_suffix, str) else None
        all_files = []
        if input_files:
            all_files = input_files
        elif input_dir:
            pattern = '**/*' if self.recursive else '*'
            all_files = [f for f in input_dir.glob(pattern) if f.is_file()]
            if self.exclude_hidden:
                all_files = [f for f in all_files if not f.name.startswith('.')]
        if exclude_files:
            exclude_names = {f.name for f in exclude_files}
            all_files = [f for f in all_files if f.name not in exclude_names]
        if filter_file_by_suffix:
            all_files = [f for f in all_files if f.suffix.lower() in filter_file_by_suffix]
        if self.num_files_limits:
            all_files = all_files[:self.num_files_limits]
        documents = []
        for file_path in all_files:
            if show_progress:
                logger.info(f'Processing: {file_path.name}')
            try:
                if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']:
                    img_doc = self._process_image(file_path)
                    if img_doc:
                        documents.append(img_doc)
            except Exception as e:
                logger.error(f'Failed to process {file_path}: {str(e)}')
                if self.errors == 'strict':
                    raise
        logger.info(f'Loaded {len(documents)} image documents')
        return documents
    except Exception as e:
        logger.error(f'Failed to load documents: {str(e)}')
        raise RuntimeError(f'Failed to load documents: {str(e)}')

def _process_image(self, file_path: Path) -> ImageDocument:
    """Process a single image file."""
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            format_name = img.format or 'Unknown'
        document = ImageDocument(text='', image=None, image_path=str(file_path), image_mimetype=f'image/{format_name.lower()}', metadata={'file_path': str(file_path), 'file_name': file_path.name, 'file_type': file_path.suffix, 'file_size': file_path.stat().st_size, 'creation_date': str(file_path.stat().st_ctime), 'last_modified_date': str(file_path.stat().st_mtime)})
        return document
    except Exception as e:
        logger.error(f'Failed to process image {file_path}: {str(e)}')
        if self.errors == 'strict':
            raise
        return None

class VectorIndexing(BaseIndexWrapper):
    """Wrapper for LlamaIndex VectorStoreIndex."""

    def __init__(self, embed_model: BaseEmbedding, storage_handler: StorageHandler, index_config: Dict[str, Any]=None):
        super().__init__()
        self.index_type = IndexType.VECTOR
        self.embed_model = embed_model
        self.storage_handler = storage_handler
        self._create_storage_context()
        self.id_to_node = dict()
        self.index_config = index_config or {}
        try:
            self.index = VectorStoreIndex(nodes=[], embed_model=self.embed_model, storage_context=self.storage_context, show_progress=self.index_config.get('show_progress', False))
        except Exception as e:
            logger.error(f'Failed to initialize VectorStoreIndex: {str(e)}')
            raise

    def _create_storage_context(self):
        assert self.storage_handler.vector_store is not None, "VectorIndexing must init a vector backend in 'storageHandler'"
        self.storage_context = StorageContext.from_defaults(vector_store=self.storage_handler.vector_store.get_vector_store())

    def get_index(self) -> VectorStoreIndex:
        return self.index

    def insert_nodes(self, nodes: List[Union[Chunk, BaseNode]]) -> Sequence[str]:
        """
        Insert or update nodes into the vector index.

        Converts Chunk objects to LlamaIndex nodes, serializes metadata as JSON strings, and inserts
        them into the VectorStoreIndex. Nodes are cached in id_to_node for quick access.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): List of nodes to insert, either Chunk or BaseNode.
        
        Returns:

        """
        try:
            filtered_nodes = []
            for node in nodes:
                llama_node = node.to_llama_node() if isinstance(node, Chunk) else node
                node_id = llama_node.id if hasattr(llama_node, 'id') else llama_node.id_
                if node_id in self.id_to_node:
                    self.delete_nodes([node_id])
                    logger.info(f'Find the same node in vector database: {node_id}. Update it.')
                filtered_nodes.extend([llama_node])
            nodes_with_embedding = self.index._get_node_with_embedding(nodes=filtered_nodes)
            for node in nodes_with_embedding:
                self.id_to_node[node.node_id] = node.model_copy()
            self.index.insert_nodes(nodes_with_embedding)
            logger.info(f'Inserted {len(nodes_with_embedding)} nodes into VectorStoreIndex')
            return list([n.node_id for n in filtered_nodes])
        except Exception as e:
            logger.error(f'Failed to insert nodes: {str(e)}')
            return []

    def delete_nodes(self, node_ids: Optional[List[str]]=None, metadata_filters: Optional[Dict[str, Any]]=None) -> None:
        """
        Delete nodes from the vector index based on node IDs or metadata filters.

        Removes specified nodes from the index and the id_to_node cache. If metadata_filters are
        provided, nodes matching the filters are deleted.

        Args:
            node_ids (Optional[List[str]]): List of node IDs to delete. Defaults to None.
            metadata_filters (Optional[Dict[str, Any]]): Metadata filters to select nodes for deletion. Defaults to None.
        """
        try:
            if node_ids:
                for node_id in node_ids:
                    if node_id in self.id_to_node:
                        self.index.delete_nodes([node_id], delete_from_docstore=False)
                        if self.index.storage_context.docstore._kvstore._collections_mappings.get(node_id, None) is not None:
                            self.index.storage_context.docstore._kvstore._collections_mappings.pop(node_id)
                        self.id_to_node.pop(node_id)
                        logger.info(f'Deleted node {node_id} from VectorStoreIndex')
            elif metadata_filters:
                nodes_to_delete = []
                for node_id, node in self.id_to_node.items():
                    if all((node.metadata.get(k) == v for k, v in metadata_filters.items())):
                        nodes_to_delete.append(node_id)
                if nodes_to_delete:
                    self.index.delete_nodes(nodes_to_delete, delete_from_docstore=True)
                    for node_id in nodes_to_delete:
                        del self.id_to_node[node_id]
                    logger.info(f'Deleted {len(nodes_to_delete)} nodes matching metadata filters from VectorStoreIndex')
            else:
                logger.warning('No node_ids or metadata_filters provided for deletion')
        except Exception as e:
            logger.error(f'Failed to delete nodes: {str(e)}')
            raise

    async def aload(self, nodes: List[Union[Chunk, BaseNode]]) -> Sequence[str]:
        """
        Asynchronously load nodes into the vector index and its backend store.

        Caches nodes in id_to_node and loads them into the FAISS vector store, ensuring
        no duplicates are inserted by relying on the backend's duplicate checking.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): The nodes to load.

        Returns:
            chunk_ids (List[str]): The id of loaded chunk.
        """
        try:
            node_ids = self.insert_nodes(nodes)
            return node_ids
        except Exception as e:
            logger.error(f'Failed to load nodes into VectorStoreIndex: {str(e)}')
            raise

    def load(self, nodes: List[Union[Chunk, BaseNode]]) -> Sequence[str]:
        """
        Synchronously load nodes into the vector index.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): The nodes to load.
        """
        return asyncio.run(self.aload(nodes))

    def clear(self) -> None:
        """
        Clear all nodes from the vector index and its cache.

        Deletes all nodes from the VectorStoreIndex and clears the id_to_node cache.
        """
        try:
            node_ids = list(self.id_to_node.keys())
            self.index.delete_nodes(node_ids, delete_from_docstore=False)
            self.id_to_node.clear()
            self.index.storage_context.docstore._kvstore._collections_mappings.clear()
            logger.info('Cleared all nodes from VectorStoreIndex')
        except Exception as e:
            logger.error(f'Failed to clear index: {str(e)}')
            raise

    async def _get(self, node_id: str) -> Optional[Chunk]:
        """Get a node by node_id from cache or vector store."""
        try:
            node = self.id_to_node.get(node_id, None)
            if node:
                if isinstance(node, Chunk):
                    return node.model_copy()
                return Chunk.from_llama_node(node)
            logger.warning(f'Node with ID {node_id} not found in cache or vector store')
            return None
        except Exception as e:
            logger.error(f'Failed to get node {node_id}: {str(e)}')
            return None

    async def get(self, node_ids: Sequence[str]) -> List[Chunk]:
        """Get nodes by node_ids from cache or vector store."""
        try:
            nodes = await asyncio.gather(*[self._get(node) for node in node_ids])
            nodes = [node for node in nodes if node is not None]
            logger.info(f'Retrieved {len(nodes)} nodes for node_ids: {node_ids}')
            return nodes
        except Exception as e:
            logger.error(f'Failed to get nodes: {str(e)}')
            return []

def insert_nodes(self, nodes: List[Union[Chunk, BaseNode]]) -> Sequence[str]:
    """
        Insert or update nodes into the vector index.

        Converts Chunk objects to LlamaIndex nodes, serializes metadata as JSON strings, and inserts
        them into the VectorStoreIndex. Nodes are cached in id_to_node for quick access.

        Args:
            nodes (List[Union[Chunk, BaseNode]]): List of nodes to insert, either Chunk or BaseNode.
        
        Returns:

        """
    try:
        filtered_nodes = []
        for node in nodes:
            llama_node = node.to_llama_node() if isinstance(node, Chunk) else node
            node_id = llama_node.id if hasattr(llama_node, 'id') else llama_node.id_
            if node_id in self.id_to_node:
                self.delete_nodes([node_id])
                logger.info(f'Find the same node in vector database: {node_id}. Update it.')
            filtered_nodes.extend([llama_node])
        nodes_with_embedding = self.index._get_node_with_embedding(nodes=filtered_nodes)
        for node in nodes_with_embedding:
            self.id_to_node[node.node_id] = node.model_copy()
        self.index.insert_nodes(nodes_with_embedding)
        logger.info(f'Inserted {len(nodes_with_embedding)} nodes into VectorStoreIndex')
        return list([n.node_id for n in filtered_nodes])
    except Exception as e:
        logger.error(f'Failed to insert nodes: {str(e)}')
        return []

class SemanticChunker(BaseChunker):
    """Chunker that splits documents based on semantic similarity.

    Uses LlamaIndex's SemanticChunker with an embedding model to create chunks that preserve
    semantic coherence, ideal for improving retrieval accuracy in RAG pipelines.

    Attributes:
        embed_model (BaseEmbedding): The embedding model for semantic similarity.
        parser (SemanticChunker): The LlamaIndex parser for semantic chunking.
    """

    def __init__(self, embed_model: BaseEmbedding, similarity_threshold: float=0.7, max_workers=4, **kwargs):
        """Initialize the SemanticChunker.

        Args:
            embed_model_name (BaseEmbedding): the embedding model.
            similarity_threshold (float, optional): Threshold for semantic similarity to split chunks (default: 0.7).
        """
        self.embed_model = embed_model
        self.parser = SemanticSplitterNodeParser(embed_model=self.embed_model, similarity_threshold=similarity_threshold)
        self.max_workers = max_workers

    def _process_document(self, doc: Document) -> List[Chunk]:
        """Process a single document into chunks.

        Args:
            doc (Document): The document to chunk.

        Returns:
            List[Chunk]: List of Chunk objects with metadata.
        """
        try:
            llama_doc = doc.to_llama_document()
            llama_doc.metadata['doc_id'] = doc.doc_id
            nodes = asyncio.run(self.parser.aget_nodes_from_documents([llama_doc]))
            chunks = []
            for idx, node in enumerate(nodes):
                chunk = Chunk.from_llama_node(node)
                chunk.metadata.chunking_strategy = ChunkingStrategy.SIMPLE
                chunks.extend([chunk])
            logger.debug(f'Processed document {doc.doc_id} into {len(chunks)} chunks')
            return chunks
        except Exception as e:
            logger.error(f'Failed to process document {doc.doc_id}: {str(e)}')
            return []

    def chunk(self, documents: List[Document], **kwargs) -> Corpus:
        """Chunk documents based on semantic similarity.

        Args:
            documents (List[Document]): List of Document objects to chunk.
            **kwargs: Additional parameters (e.g., max_chunk_size).

        Returns:
            Corpus: A collection of Chunk objects with semantic metadata.
        """
        if not documents:
            logger.info('No documents provided, returning empty Corpus')
            return Corpus([])
        chunks = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_doc = {executor.submit(self._process_document, doc): doc for doc in documents}
            for future in future_to_doc:
                doc = future_to_doc[future]
                try:
                    chunks.extend(future.result())
                except Exception as e:
                    logger.error(f'Error processing document {doc.doc_id}: {str(e)}')
        logger.info(f'Chunked {len(documents)} documents into {len(chunks)} chunks')
        return Corpus(chunks=chunks)

def _process_document(self, doc: Document) -> List[Chunk]:
    """Process a single document into chunks.

        Args:
            doc (Document): The document to chunk.

        Returns:
            List[Chunk]: List of Chunk objects with metadata.
        """
    try:
        llama_doc = doc.to_llama_document()
        llama_doc.metadata['doc_id'] = doc.doc_id
        nodes = asyncio.run(self.parser.aget_nodes_from_documents([llama_doc]))
        chunks = []
        for idx, node in enumerate(nodes):
            chunk = Chunk.from_llama_node(node)
            chunk.metadata.chunking_strategy = ChunkingStrategy.SIMPLE
            chunks.extend([chunk])
        logger.debug(f'Processed document {doc.doc_id} into {len(chunks)} chunks')
        return chunks
    except Exception as e:
        logger.error(f'Failed to process document {doc.doc_id}: {str(e)}')
        return []

def chunk(self, documents: List[Document], **kwargs) -> Corpus:
    """Chunk documents based on semantic similarity.

        Args:
            documents (List[Document]): List of Document objects to chunk.
            **kwargs: Additional parameters (e.g., max_chunk_size).

        Returns:
            Corpus: A collection of Chunk objects with semantic metadata.
        """
    if not documents:
        logger.info('No documents provided, returning empty Corpus')
        return Corpus([])
    chunks = []
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        future_to_doc = {executor.submit(self._process_document, doc): doc for doc in documents}
        for future in future_to_doc:
            doc = future_to_doc[future]
            try:
                chunks.extend(future.result())
            except Exception as e:
                logger.error(f'Error processing document {doc.doc_id}: {str(e)}')
    logger.info(f'Chunked {len(documents)} documents into {len(chunks)} chunks')
    return Corpus(chunks=chunks)

class SimpleChunker(BaseChunker):
    """Chunker that splits documents into fixed-size chunks using multi-threading and async parsing.

    Uses LlamaIndex's SimpleNodeParser with async support to create chunks with a specified size
    and overlap, suitable for general-purpose text splitting in RAG pipelines.

    Attributes:
        chunk_size (int): The target size of each chunk in characters.
        chunk_overlap (int): The number of overlapping characters between adjacent chunks.
        parser (SimpleNodeParser): The LlamaIndex parser for chunking.
        max_workers (int): Maximum number of threads for parallel processing.
    """

    def __init__(self, chunk_size: int=1024, chunk_overlap: int=20, tokenizer=None, chunking_tokenizer_fn=None, include_metadata: bool=True, include_prev_next_rel: bool=True, max_workers: int=4):
        """Initialize the SimpleChunker.

        Args:
            chunk_size (int, optional): Target size of each chunk in characters (default: 1024).
            chunk_overlap (int, optional): Overlap between adjacent chunks in characters (default: 20).
            tokenizer: Optional tokenizer for chunking.
            chunking_tokenizer_fn: Optional tokenizer function for chunking.
            include_metadata (bool): Whether to include metadata in nodes (default: True).
            include_prev_next_rel (bool): Whether to include previous/next relationships (default: True).
            max_workers (int): Maximum number of threads for parallel processing (default: 4).
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tokenizer
        self.chunking_tokenizer_fn = chunking_tokenizer_fn
        self.max_workers = max_workers
        self.parser = SimpleNodeParser(chunk_size=chunk_size, chunk_overlap=chunk_overlap, tokenizer=tokenizer, chunking_tokenizer_fn=chunking_tokenizer_fn, include_metadata=include_metadata, include_prev_next_rel=include_prev_next_rel)

    def _process_document(self, doc: Document) -> List[Chunk]:
        """Process a single document into chunks in a thread.

        Args:
            doc (Document): The document to chunk.

        Returns:
            List[Chunk]: List of Chunk objects with metadata.
        """
        try:
            llama_doc = doc.to_llama_document()
            llama_doc.metadata['doc_id'] = doc.doc_id
            nodes = asyncio.run(self.parser.aget_nodes_from_documents([llama_doc]))
            chunks = []
            for idx, node in enumerate(nodes):
                chunk = Chunk.from_llama_node(node)
                chunk.metadata.chunking_strategy = ChunkingStrategy.SIMPLE
                chunks.extend([chunk])
            logger.debug(f'Processed document {doc.doc_id} into {len(chunks)} chunks')
            return chunks
        except Exception as e:
            logger.error(f'Failed to process document {doc.doc_id}: {str(e)}')
            return []

    def chunk(self, documents: List[Document], **kwargs) -> Corpus:
        """Chunk documents into fixed-size chunks using multi-threading.

        Args:
            documents (List[Document]): List of Document objects to chunk.

        Returns:
            Corpus: A collection of Chunk objects with metadata.
        """
        if not documents:
            logger.info('No documents provided, returning empty Corpus')
            return Corpus([])
        chunks = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_doc = {executor.submit(self._process_document, doc): doc for doc in documents}
            for future in future_to_doc:
                doc = future_to_doc[future]
                try:
                    chunks.extend(future.result())
                except Exception as e:
                    logger.error(f'Error processing document {doc.doc_id}: {str(e)}')
        logger.info(f'Chunked {len(documents)} documents into {len(chunks)} chunks')
        return Corpus(chunks=chunks)

def _process_document(self, doc: Document) -> List[Chunk]:
    """Process a single document into chunks in a thread.

        Args:
            doc (Document): The document to chunk.

        Returns:
            List[Chunk]: List of Chunk objects with metadata.
        """
    try:
        llama_doc = doc.to_llama_document()
        llama_doc.metadata['doc_id'] = doc.doc_id
        nodes = asyncio.run(self.parser.aget_nodes_from_documents([llama_doc]))
        chunks = []
        for idx, node in enumerate(nodes):
            chunk = Chunk.from_llama_node(node)
            chunk.metadata.chunking_strategy = ChunkingStrategy.SIMPLE
            chunks.extend([chunk])
        logger.debug(f'Processed document {doc.doc_id} into {len(chunks)} chunks')
        return chunks
    except Exception as e:
        logger.error(f'Failed to process document {doc.doc_id}: {str(e)}')
        return []

def chunk(self, documents: List[Document], **kwargs) -> Corpus:
    """Chunk documents into fixed-size chunks using multi-threading.

        Args:
            documents (List[Document]): List of Document objects to chunk.

        Returns:
            Corpus: A collection of Chunk objects with metadata.
        """
    if not documents:
        logger.info('No documents provided, returning empty Corpus')
        return Corpus([])
    chunks = []
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        future_to_doc = {executor.submit(self._process_document, doc): doc for doc in documents}
        for future in future_to_doc:
            doc = future_to_doc[future]
            try:
                chunks.extend(future.result())
            except Exception as e:
                logger.error(f'Error processing document {doc.doc_id}: {str(e)}')
    logger.info(f'Chunked {len(documents)} documents into {len(chunks)} chunks')
    return Corpus(chunks=chunks)

class HierarchicalChunker(BaseChunker):
    """Enhanced hierarchical chunker with dynamic hierarchy level assignment.

    Creates a multi-level hierarchy of chunks with full node relationships:
    - SOURCE: The source document.
    - PREVIOUS/NEXT: Sequential nodes in the document.
    - PARENT/CHILD: Hierarchical relationships.

    Supports custom level parsers or default chunk sizes, with dynamic hierarchy level
    assignment based on node parser IDs. Uses multi-threading and async parsing.

    Attributes:
        level_parsers (Dict[str, BaseChunker]): Custom parsers for each hierarchy level.
        chunk_sizes (List[int]): Chunk sizes for default parsers (e.g., [2048, 512, 128]).
        chunk_overlap (int): Overlap between adjacent chunks.
        parser (HierarchicalNodeParser): LlamaIndex parser for hierarchical chunking.
        include_metadata (bool): Whether to include metadata in nodes.
        include_prev_next_rel (bool): Whether to include previous/next node relationships.
        max_workers (int): Maximum number of threads for parallel processing.
        parser_to_level (Dict[str, int]): Mapping of node_parser_id to hierarchy level.
    """

    def __init__(self, level_parsers: Dict[str, BaseChunker]=None, chunk_sizes: Optional[List[int]]=None, chunk_overlap: int=20, include_metadata: bool=True, include_prev_next_rel: bool=True, max_workers: int=4):
        """Initialize the HierarchicalChunker.

        Args:
            level_parsers (Dict[str, BaseChunker], optional): Custom parsers for hierarchy levels.
            chunk_sizes (List[int], optional): Chunk sizes for default parsers (default: [2048, 512, 128]).
            chunk_overlap (int): Overlap between adjacent chunks (default: 20).
            include_metadata (bool): Include metadata in nodes (default: True).
            include_prev_next_rel (bool): Include prev/next relationships (default: True).
            max_workers (int): Maximum number of threads for parallel processing (default: 4).
        """
        self.level_parsers = level_parsers or {}
        self.chunk_sizes = chunk_sizes or [2048, 512, 128]
        self.chunk_overlap = chunk_overlap
        self.include_metadata = include_metadata
        self.include_prev_next_rel = include_prev_next_rel
        self.max_workers = max_workers
        node_parser_ids = None
        node_parser_map = None
        if not self.level_parsers:
            node_parser_ids = [f'chunk_size_{size}' for size in self.chunk_sizes]
            node_parser_map = {node_id: SimpleChunker(chunk_size=size, chunk_overlap=chunk_overlap, include_metadata=include_metadata, include_prev_next_rel=include_prev_next_rel).parser for size, node_id in zip(self.chunk_sizes, node_parser_ids)}
        else:
            if chunk_sizes is not None:
                raise ValueError('If level_parsers is provided, chunk_sizes should be None.')
            node_parser_ids = list(self.level_parsers.keys())
            node_parser_map = {k: v.parser for k, v in self.level_parsers.items()}
        self.parser_to_level = {pid: idx + 1 for idx, pid in enumerate(node_parser_ids)}
        self.parser = HierarchicalNodeParser.from_defaults(chunk_sizes=None, chunk_overlap=self.chunk_overlap, node_parser_ids=node_parser_ids, node_parser_map=node_parser_map, include_metadata=include_metadata, include_prev_next_rel=include_prev_next_rel)

    def _process_document(self, doc: Document, custom_metadata: Dict=None) -> List[Chunk]:
        """Process a single document into chunks in a thread.

        Args:
            doc (Document): The document to chunk.
            custom_metadata (Dict, optional): User-defined metadata for sections.

        Returns:
            List[Chunk]: List of Chunk objects with metadata.
        """
        try:
            llama_doc = doc.to_llama_document()
            llama_doc.metadata['doc_id'] = doc.doc_id
            nodes = self.parser.get_nodes_from_documents([llama_doc])
            chunks = []
            for i, node in enumerate(nodes):
                chunk = Chunk.from_llama_node(node)
                chunk.metadata.chunking_strategy = ChunkingStrategy.HIERARCHICAL
                chunks.extend([chunk])
            logger.debug(f'Processed document {doc.doc_id} into {len(chunks)} chunks')
            return chunks
        except Exception as e:
            logger.error(f'Failed to process document {doc.doc_id}: {str(e)}')
            return []

    def chunk(self, documents: List[Document], **kwargs) -> Corpus:
        """Chunk documents using hierarchical strategy with dynamic chunk size adjustment.

        Args:
            documents (List[Document]): List of Document objects to chunk.
            **kwargs: Additional parameters, e.g., custom_metadata for section titles.

        Returns:
            Corpus: A collection of hierarchically organized chunks.
        """
        if not documents:
            logger.info('No documents provided, returning empty Corpus')
            return Corpus(chunks=[])
        chunks = []
        custom_metadata = kwargs.get('custom_metadata', {})
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_doc = {executor.submit(self._process_document, doc, custom_metadata): doc for doc in documents}
            for future in future_to_doc:
                doc = future_to_doc[future]
                try:
                    chunks.extend(future.result())
                except Exception as e:
                    logger.error(f'Error processing document {doc.doc_id}: {str(e)}')
        logger.info(f'Chunked {len(documents)} documents into {len(chunks)} chunks')
        return Corpus(chunks=chunks)

def _process_document(self, doc: Document, custom_metadata: Dict=None) -> List[Chunk]:
    """Process a single document into chunks in a thread.

        Args:
            doc (Document): The document to chunk.
            custom_metadata (Dict, optional): User-defined metadata for sections.

        Returns:
            List[Chunk]: List of Chunk objects with metadata.
        """
    try:
        llama_doc = doc.to_llama_document()
        llama_doc.metadata['doc_id'] = doc.doc_id
        nodes = self.parser.get_nodes_from_documents([llama_doc])
        chunks = []
        for i, node in enumerate(nodes):
            chunk = Chunk.from_llama_node(node)
            chunk.metadata.chunking_strategy = ChunkingStrategy.HIERARCHICAL
            chunks.extend([chunk])
        logger.debug(f'Processed document {doc.doc_id} into {len(chunks)} chunks')
        return chunks
    except Exception as e:
        logger.error(f'Failed to process document {doc.doc_id}: {str(e)}')
        return []

def chunk(self, documents: List[Document], **kwargs) -> Corpus:
    """Chunk documents using hierarchical strategy with dynamic chunk size adjustment.

        Args:
            documents (List[Document]): List of Document objects to chunk.
            **kwargs: Additional parameters, e.g., custom_metadata for section titles.

        Returns:
            Corpus: A collection of hierarchically organized chunks.
        """
    if not documents:
        logger.info('No documents provided, returning empty Corpus')
        return Corpus(chunks=[])
    chunks = []
    custom_metadata = kwargs.get('custom_metadata', {})
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        future_to_doc = {executor.submit(self._process_document, doc, custom_metadata): doc for doc in documents}
        for future in future_to_doc:
            doc = future_to_doc[future]
            try:
                chunks.extend(future.result())
            except Exception as e:
                logger.error(f'Error processing document {doc.doc_id}: {str(e)}')
    logger.info(f'Chunked {len(documents)} documents into {len(chunks)} chunks')
    return Corpus(chunks=chunks)

class SimpleReranker(BasePostprocessor):
    """Post-processor for reranking retrieval results."""

    def __init__(self, similarity_cutoff: Optional[float]=None, keyword_filters: Optional[List[str]]=None):
        super().__init__()
        self.postprocessors = []
        if similarity_cutoff:
            self.postprocessors.append(SimilarityPostprocessor(similarity_cutoff=similarity_cutoff))
        if keyword_filters:
            self.postprocessors.append(KeywordNodePostprocessor(required_keywords=keyword_filters))

    def postprocess(self, query: Query, results: List[RagResult]) -> RagResult:
        try:
            if not self.postprocessors:
                corpus = Corpus()
                scores = []
                for result in results:
                    for chunk in result.corpus.chunks:
                        corpus.add_chunk(chunk)
                    scores.extend(result.scores)
                final_result = RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'postprocessor': 'simple_passthrough'})
                self.logger.info(f'Simple passthrough: {len(corpus.chunks)} chunks')
                return final_result
            chunk_to_original = {}
            nodes = []
            for result in results:
                for chunk, score in zip(result.corpus.chunks, result.scores):
                    node = chunk.to_llama_node()
                    nodes.append(NodeWithScore(node=node, score=score))
                    chunk_to_original[node.id_] = chunk
            for postprocessor in self.postprocessors:
                nodes = postprocessor.postprocess_nodes(nodes)
            corpus = Corpus()
            scores = []
            for score_node in nodes:
                original_chunk = chunk_to_original.get(score_node.node.id_)
                if original_chunk:
                    original_chunk.metadata.similarity_score = score_node.score or 0.0
                    corpus.add_chunk(original_chunk)
                    scores.append(score_node.score or 0.0)
                else:
                    chunk_class = type(results[0].corpus.chunks[0]) if results and results[0].corpus.chunks else Chunk
                    try:
                        chunk = chunk_class.from_llama_node(score_node.node)
                        chunk.metadata.similarity_score = score_node.score or 0.0
                        corpus.add_chunk(chunk)
                        scores.append(score_node.score or 0.0)
                    except Exception as e:
                        self.logger.warning(f'Failed to reconstruct chunk from node: {e}')
                        continue
            result = RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'postprocessor': 'reranker'})
            self.logger.info(f'Reranked to {len(corpus.chunks)} chunks')
            return result
        except Exception as e:
            self.logger.error(f'Reranking failed: {str(e)}')
            raise

def postprocess(self, query: Query, results: List[RagResult]) -> RagResult:
    try:
        if not self.postprocessors:
            corpus = Corpus()
            scores = []
            for result in results:
                for chunk in result.corpus.chunks:
                    corpus.add_chunk(chunk)
                scores.extend(result.scores)
            final_result = RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'postprocessor': 'simple_passthrough'})
            self.logger.info(f'Simple passthrough: {len(corpus.chunks)} chunks')
            return final_result
        chunk_to_original = {}
        nodes = []
        for result in results:
            for chunk, score in zip(result.corpus.chunks, result.scores):
                node = chunk.to_llama_node()
                nodes.append(NodeWithScore(node=node, score=score))
                chunk_to_original[node.id_] = chunk
        for postprocessor in self.postprocessors:
            nodes = postprocessor.postprocess_nodes(nodes)
        corpus = Corpus()
        scores = []
        for score_node in nodes:
            original_chunk = chunk_to_original.get(score_node.node.id_)
            if original_chunk:
                original_chunk.metadata.similarity_score = score_node.score or 0.0
                corpus.add_chunk(original_chunk)
                scores.append(score_node.score or 0.0)
            else:
                chunk_class = type(results[0].corpus.chunks[0]) if results and results[0].corpus.chunks else Chunk
                try:
                    chunk = chunk_class.from_llama_node(score_node.node)
                    chunk.metadata.similarity_score = score_node.score or 0.0
                    corpus.add_chunk(chunk)
                    scores.append(score_node.score or 0.0)
                except Exception as e:
                    self.logger.warning(f'Failed to reconstruct chunk from node: {e}')
                    continue
        result = RagResult(corpus=corpus, scores=scores, metadata={'query': query.query_str, 'postprocessor': 'reranker'})
        self.logger.info(f'Reranked to {len(corpus.chunks)} chunks')
        return result
    except Exception as e:
        self.logger.error(f'Reranking failed: {str(e)}')
        raise

class Tokens(object):
    """A class to represent a list of tokenized text."""
    TEXT = 0
    TEXT_WS = 1
    SPAN = 2
    POS = 3
    LEMMA = 4
    NER = 5

    def __init__(self, data, annotators, opts=None):
        self.data = data
        self.annotators = annotators
        self.opts = opts or {}

    def __len__(self):
        """The number of tokens."""
        return len(self.data)

    def slice(self, i=None, j=None):
        """Return a view of the list of tokens from [i, j)."""
        new_tokens = copy.copy(self)
        new_tokens.data = self.data[i:j]
        return new_tokens

    def untokenize(self):
        """Returns the original text (with whitespace reinserted)."""
        return ''.join([t[self.TEXT_WS] for t in self.data]).strip()

    def words(self, uncased=False):
        """Returns a list of the text of each token

        Args:
            uncased: lower cases text
        """
        if uncased:
            return [t[self.TEXT].lower() for t in self.data]
        else:
            return [t[self.TEXT] for t in self.data]

    def offsets(self):
        """Returns a list of [start, end) character offsets of each token."""
        return [t[self.SPAN] for t in self.data]

    def pos(self):
        """Returns a list of part-of-speech tags of each token.
        Returns None if this annotation was not included.
        """
        if 'pos' not in self.annotators:
            return None
        return [t[self.POS] for t in self.data]

    def lemmas(self):
        """Returns a list of the lemmatized text of each token.
        Returns None if this annotation was not included.
        """
        if 'lemma' not in self.annotators:
            return None
        return [t[self.LEMMA] for t in self.data]

    def entities(self):
        """Returns a list of named-entity-recognition tags of each token.
        Returns None if this annotation was not included.
        """
        if 'ner' not in self.annotators:
            return None
        return [t[self.NER] for t in self.data]

    def ngrams(self, n=1, uncased=False, filter_fn=None, as_strings=True):
        """Returns a list of all ngrams from length 1 to n.

        Args:
            n: upper limit of ngram length
            uncased: lower cases text
            filter_fn: user function that takes in an ngram list and returns
              True or False to keep or not keep the ngram
            as_string: return the ngram as a string vs list
        """

        def _skip(gram):
            if not filter_fn:
                return False
            return filter_fn(gram)
        words = self.words(uncased)
        ngrams = [(s, e + 1) for s in range(len(words)) for e in range(s, min(s + n, len(words))) if not _skip(words[s:e + 1])]
        if as_strings:
            ngrams = ['{}'.format(' '.join(words[s:e])) for s, e in ngrams]
        return ngrams

    def entity_groups(self):
        """Group consecutive entity tokens with the same NER tag."""
        entities = self.entities()
        if not entities:
            return None
        non_ent = self.opts.get('non_ent', 'O')
        groups = []
        idx = 0
        while idx < len(entities):
            ner_tag = entities[idx]
            if ner_tag != non_ent:
                start = idx
                while idx < len(entities) and entities[idx] == ner_tag:
                    idx += 1
                groups.append((self.slice(start, idx).untokenize(), ner_tag))
            else:
                idx += 1
        return groups

def slice(self, i=None, j=None):
    """Return a view of the list of tokens from [i, j)."""
    new_tokens = copy.copy(self)
    new_tokens.data = self.data[i:j]
    return new_tokens

class Capturing(list):

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        self._stringio.close = lambda x: 1
        return self

    def __exit__(self, *args):
        self.append(self._stringio.getvalue())
        del self._stringio
        sys.stdout = self._stdout

def __enter__(self):
    self._stdout = sys.stdout
    sys.stdout = self._stringio = StringIO()
    self._stringio.close = lambda x: 1
    return self

def __exit__(self, *args):
    self.append(self._stringio.getvalue())
    del self._stringio
    sys.stdout = self._stdout

def evaluate_generations(samples_list: list, generations_list: list[list[str]], debug: bool=False, num_process_evaluate: int=16, timeout=6):
    """We take the list of code generations and try to compile them
     and the run their corresponding unit tests which are retrieved from the APPS dataset.

    Args:
        generations: list of code generations (same order as samples in APPS dataset)
        level: difficulty level used in the generation, can be "all", "introductory", "interview" or "competition"

    Returns:
        results: dictionary of results, key is the problem index, value is a list of results for each generation
    """
    inputs = [[(generations_list[index], samples_list[index], debug, timeout), index] for index in range(len(generations_list))]
    with ProcessPoolExecutor(max_workers=1 if debug else num_process_evaluate) as executor:
        futures = {executor.submit(evaluate_generations_by_problem, arg): index for arg, index in inputs}
        results = {}
        metadata = {}
        for future in as_completed(futures):
            index = futures[future]
            results[index], metadata[index] = future.result()
    assert len(results) == len(inputs), f'results = {len(results)} inputs = {len(inputs)} results={results!r}'
    return (results, metadata)

def escape_json_values(string: str) -> str:

    def escape_value(match):
        raw_value = match.group(1)
        raw_value = raw_value.replace('\n', '\\n')
        return f'"{raw_value}"'

    def fix_json(match):
        raw_key = match.group(1)
        raw_value = match.group(2)
        raw_value = raw_value.replace('\n', '\\n')
        raw_value = regex.sub('(?<!\\\\)"', '\\"', raw_value)
        return f'"{raw_key}": "{raw_value}"'
    try:
        json.loads(string)
        return string
    except json.JSONDecodeError:
        pass
    try:
        string = regex.sub('(?<!\\\\)"', '\\"', string)
        pattern_key = '\\\\"([^"]+)\\\\"(?=\\s*:\\s*)'
        string = regex.sub(pattern_key, '"\\1"', string)
        pattern_value = '(?<=:\\s*)\\\\"((?:\\\\.|[^"\\\\])*)\\\\"'
        string = regex.sub(pattern_value, escape_value, string, flags=regex.DOTALL)
        pattern_nested_json = '"([^"]+)"\\s*:\\s*\\\\"([^"]*\\{+[\\S\\s]*?\\}+)[\\r\\n\\\\n]*"'
        string = regex.sub(pattern_nested_json, fix_json, string, flags=regex.DOTALL)
        json.loads(string)
        return string
    except json.JSONDecodeError:
        pass
    return string

def parse_json_from_llm_output(text: str) -> dict:
    """
    Extract JSON str from LLM outputs and convert it to dict. 
    """
    json_list = parse_json_from_text(text=text)
    if json_list:
        json_text = json_list[0]
        try:
            data = yaml.safe_load(json_text)
        except Exception:
            raise ValueError(f'The following generated text is not a valid JSON string!\n{json_text}')
    else:
        raise ValueError(f'The follwoing generated text does not contain JSON string!\n{text}')
    return data

class BaseModule(BaseModel, metaclass=MetaModule):
    """
    Base module class that serves as the foundation for all modules in the EvoAgentX framework.
    
    This class provides serialization/deserialization capabilities, supports creating instances from
    dictionaries, JSON, or files, and exporting instances to these formats.
    
    Attributes:
        class_name: The class name, defaults to None but is automatically set during subclass initialization
        model_config: Pydantic model configuration that controls type matching and behavior
    """
    class_name: str = None
    model_config = {'arbitrary_types_allowed': True, 'extra': 'allow', 'protected_namespaces': (), 'validate_assignment': False}

    def __init_subclass__(cls, **kwargs):
        """
        Subclass initialization method that automatically sets the class_name attribute.
        
        Args:
            cls (Type): The subclass being initialized
            **kwargs (Any): Additional keyword arguments
        """
        super().__init_subclass__(**kwargs)
        cls.class_name = cls.__name__

    def __init__(self, **kwargs):
        """
        Initializes a BaseModule instance.
        
        Args:
            **kwargs (Any): Keyword arguments used to initialize the instance
        
        Raises:
            ValidationError: When parameter validation fails
            Exception: When other errors occur during initialization
        """
        try:
            for field_name, _ in type(self).model_fields.items():
                field_value = kwargs.get(field_name, None)
                if field_value:
                    kwargs[field_name] = self._process_data(field_value)
            super().__init__(**kwargs)
            self.init_module()
        except (ValidationError, Exception) as e:
            exception_handler = callback_manager.get_callback('exception_buffer')
            if exception_handler is None:
                error_message = get_base_module_init_error_message(cls=self.__class__, data=kwargs, errors=e)
                logger.error(error_message)
                raise
            else:
                exception_handler.add(e)

    def init_module(self):
        """
        Module initialization method that subclasses can override to provide additional initialization logic.
        """
        pass

    def __str__(self) -> str:
        """
        Returns a string representation of the object.
        
        Returns:
            str: String representation of the object
        """
        return self.to_str()

    @property
    def kwargs(self) -> dict:
        """
        Returns the extra fields of the model.
        
        Returns:
            dict: Dictionary containing all extra keyword arguments
        """
        return self.model_extra

    @classmethod
    def _create_instance(cls, data: Dict[str, Any]) -> 'BaseModule':
        """
        Internal method for creating an instance from a dictionary.
        
        Args:
            data: Dictionary containing instance data
        
        Returns:
            BaseModule: The created instance
        """
        processed_data = {k: cls._process_data(v) for k, v in data.items()}
        return cls.model_validate(processed_data)

    @classmethod
    def _process_data(cls, data: Any) -> Any:
        """
        Recursive method for processing data, with special handling for dictionaries containing class_name.
        
        Args:
            data: Data to be processed
        
        Returns:
            Processed data
        """
        if isinstance(data, dict):
            if 'class_name' in data:
                sub_class = MODULE_REGISTRY.get_module(data.get('class_name'))
                return sub_class._create_instance(data)
            else:
                return {k: cls._process_data(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [cls._process_data(x) for x in data]
        else:
            return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], **kwargs) -> 'BaseModule':
        """
        Instantiate the BaseModule from a dictionary.
        
        Args:
            data: Dictionary containing instance data
            **kwargs (Any): Additional keyword arguments, can include log to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            Exception: When errors occur during initialization
        """
        use_logger = kwargs.get('log', True)
        with exception_buffer() as buffer:
            try:
                class_name = data.get('class_name', None)
                if class_name:
                    cls = MODULE_REGISTRY.get_module(class_name)
                module = cls._create_instance(data)
                if len(buffer.exceptions) > 0:
                    error_message = get_base_module_init_error_message(cls, data, buffer.exceptions)
                    if use_logger:
                        logger.error(error_message)
                    raise Exception(get_error_message(buffer.exceptions))
            finally:
                pass
        return module

    @classmethod
    def from_json(cls, content: str, **kwargs) -> 'BaseModule':
        """
        Construct the BaseModule from a JSON string.
        
        This method uses yaml.safe_load to parse the JSON string into a Python object,
        which supports more flexible parsing than standard json.loads (including handling
        single quotes, trailing commas, etc). The parsed data is then passed to from_dict
        to create the instance.
        
        Args:
            content: JSON string
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the input is not a valid JSON string
        """
        use_logger = kwargs.get('log', True)
        try:
            data = yaml.safe_load(content)
        except Exception:
            error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_json is not a valid JSON string.'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        if not isinstance(data, (list, dict)):
            error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_json is not a valid JSON string.'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        return cls.from_dict(data, log=use_logger)

    @classmethod
    def from_str(cls, content: str, **kwargs) -> 'BaseModule':
        """
        Construct the BaseModule from a string that may contain JSON.
        
        This method is more forgiving than `from_json` as it can extract valid JSON
        objects embedded within larger text. It uses `parse_json_from_text` to extract 
        all potential JSON strings from the input text, then tries to create an instance 
        from each extracted JSON string until successful.
        
        Args:
            content: Text that may contain JSON strings
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the input does not contain valid JSON strings or the JSON is incompatible with the class
        """
        use_logger = kwargs.get('log', True)
        extracted_json_list = parse_json_from_text(content)
        if len(extracted_json_list) == 0:
            error_message = f'The input to {cls.__name__}.from_str does not contain any valid JSON str.'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        module = None
        for json_str in extracted_json_list:
            try:
                module = cls.from_json(json_str, log=False)
            except Exception:
                continue
            break
        if module is None:
            error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_str either does not contain a valide JSON str, or the JSON str is incomplete or incompatable (incorrect variables or types) with {cls.__name__}.'
            error_message += f'\nInput:\n{content}'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        return module

    @classmethod
    def load_module(cls, path: str, **kwargs) -> dict:
        """
        Load the values for a module from a file.
        
        By default, it opens the specified file and uses `yaml.safe_load` to parse its contents 
        into a Python object (typically a dictionary).
        
        Args:
            path: The path of the file
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            dict: The JSON object instantiated from the file
        """
        with open(path, mode='r', encoding='utf-8') as file:
            content = yaml.safe_load(file.read())
        return content

    @classmethod
    def from_file(cls, path: str, load_function: Callable=None, **kwargs) -> 'BaseModule':
        """
        Construct the BaseModule from a file.
        
        This method reads and parses a file into a data structure, then creates
        a module instance from that data. It first verifies that the file exists,
        then uses either the provided `load_function` or the default `load_module`
        method to read and parse the file content, and finally calls `from_dict`
        to create the instance.
        
        Args:
            path: The path of the file
            load_function: The function used to load the data, takes a file path as input and returns a JSON object
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the file does not exist
        """
        use_logger = kwargs.get('log', True)
        if not os.path.exists(path):
            error_message = f'File "{path}" does not exist!'
            if use_logger:
                logger.error(error_message)
            raise ValueError(error_message)
        function = load_function or cls.load_module
        content = function(path, **kwargs)
        module = cls.from_dict(content, log=use_logger)
        return module

    def to_dict(self, exclude_none: bool=True, ignore: List[str]=[], **kwargs) -> dict:
        """
        Convert the BaseModule to a dictionary.
        
        Args:
            exclude_none: Whether to exclude fields with None values
            ignore: List of field names to ignore
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            dict: Dictionary containing the object data
        """
        data = {}
        for field_name, _ in type(self).model_fields.items():
            if field_name in ignore:
                continue
            field_value = getattr(self, field_name, None)
            if exclude_none and field_value is None:
                continue
            if isinstance(field_value, BaseModule):
                data[field_name] = field_value.to_dict(exclude_none=exclude_none, ignore=ignore)
            elif isinstance(field_value, list):
                data[field_name] = [item.to_dict(exclude_none=exclude_none, ignore=ignore) if isinstance(item, BaseModule) else item for item in field_value]
            elif isinstance(field_value, dict):
                data[field_name] = {key: value.to_dict(exclude_none=exclude_none, ignore=ignore) if isinstance(value, BaseModule) else value for key, value in field_value.items()}
            else:
                data[field_name] = field_value
        return data

    def to_json(self, use_indent: bool=False, ignore: List[str]=[], **kwargs) -> str:
        """
        Convert the BaseModule to a JSON string.
        
        Args:
            use_indent: Whether to use indentation
            ignore: List of field names to ignore
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            str: The JSON string
        """
        if use_indent:
            kwargs['indent'] = kwargs.get('indent', 4)
        else:
            kwargs.pop('indent', None)
        if kwargs.get('default', None) is None:
            kwargs['default'] = custom_serializer
        data = self.to_dict(exclude_none=True)
        for ignore_field in ignore:
            data.pop(ignore_field, None)
        return json.dumps(data, **kwargs)

    def to_str(self, **kwargs) -> str:
        """
        Convert the BaseModule to a string. Use .to_json to output JSON string by default.
        
        Args:
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            str: The string
        """
        return self.to_json(use_indent=False)

    def save_module(self, path: str, ignore: List[str]=[], **kwargs) -> str:
        """
        Save the BaseModule to a file.
        
        This method will set non-serializable objects to None by default.
        If you want to save non-serializable objects, override this method.
        Remember to also override the `load_module` function to ensure the loaded
        object can be correctly parsed by `cls.from_dict`.
        
        Args:
            path: The path to save the file
            ignore: List of field names to ignore
            **kwargs (Any): Additional keyword arguments
        
        Returns:
            str: The path where the file is saved, same as the input path
        """
        logger.info('Saving {} to {}', self.__class__.__name__, path)
        return save_json(self.to_json(use_indent=True, default=lambda x: None, ignore=ignore), path=path)

    def deepcopy(self):
        """Deep copy the module.

        This is a tweak to the default python deepcopy that only deep copies `self.parameters()`, and for other
        attributes, we just do the shallow copy.
        """
        try:
            return copy.deepcopy(self)
        except Exception:
            pass
        new_instance = self.__class__.__new__(self.__class__)
        for attr, value in self.__dict__.items():
            if isinstance(value, BaseModule):
                setattr(new_instance, attr, value.deepcopy())
            else:
                try:
                    setattr(new_instance, attr, copy.deepcopy(value))
                except Exception:
                    logging.warning(f"Failed to deep copy attribute '{attr}' of {self.__class__.__name__}, falling back to shallow copy or reference copy.")
                    try:
                        setattr(new_instance, attr, copy.copy(value))
                    except Exception:
                        setattr(new_instance, attr, value)
        return new_instance

@classmethod
def from_json(cls, content: str, **kwargs) -> 'BaseModule':
    """
        Construct the BaseModule from a JSON string.
        
        This method uses yaml.safe_load to parse the JSON string into a Python object,
        which supports more flexible parsing than standard json.loads (including handling
        single quotes, trailing commas, etc). The parsed data is then passed to from_dict
        to create the instance.
        
        Args:
            content: JSON string
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the input is not a valid JSON string
        """
    use_logger = kwargs.get('log', True)
    try:
        data = yaml.safe_load(content)
    except Exception:
        error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_json is not a valid JSON string.'
        if use_logger:
            logger.error(error_message)
        raise ValueError(error_message)
    if not isinstance(data, (list, dict)):
        error_message = f'Can not instantiate {cls.__name__}. The input to {cls.__name__}.from_json is not a valid JSON string.'
        if use_logger:
            logger.error(error_message)
        raise ValueError(error_message)
    return cls.from_dict(data, log=use_logger)

@classmethod
def from_file(cls, path: str, load_function: Callable=None, **kwargs) -> 'BaseModule':
    """
        Construct the BaseModule from a file.
        
        This method reads and parses a file into a data structure, then creates
        a module instance from that data. It first verifies that the file exists,
        then uses either the provided `load_function` or the default `load_module`
        method to read and parse the file content, and finally calls `from_dict`
        to create the instance.
        
        Args:
            path: The path of the file
            load_function: The function used to load the data, takes a file path as input and returns a JSON object
            **kwargs (Any): Additional keyword arguments, can include `log` to control logging output
        
        Returns:
            BaseModule: The created module instance
        
        Raises:
            ValueError: When the file does not exist
        """
    use_logger = kwargs.get('log', True)
    if not os.path.exists(path):
        error_message = f'File "{path}" does not exist!'
        if use_logger:
            logger.error(error_message)
        raise ValueError(error_message)
    function = load_function or cls.load_module
    content = function(path, **kwargs)
    module = cls.from_dict(content, log=use_logger)
    return module

class LongTermMemory(BaseMemory):
    """
    Manages long-term storage and retrieval of memories, integrating with RAGEngine for indexing
    and StorageHandler for persistence.
    """
    storage_handler: StorageHandler = Field(..., description='Handler for persistent storage')
    rag_config: RAGConfig = Field(..., description='Configuration for RAG engine')
    rag_engine: RAGEngine = Field(default=None, description='RAG engine for indexing and retrieval')
    memory_table: str = Field(default='memory', description='Database table for storing memories')
    default_corpus_id: Optional[str] = Field(default=None, description='Default corpus ID for memory indexing')

    def init_module(self):
        """Initialize the RAG engine and memory indices."""
        super().init_module()
        if self.rag_engine is None:
            self.rag_engine = RAGEngine(config=self.rag_config, storage_handler=self.storage_handler)
        if self.default_corpus_id is None:
            self.default_corpus_id = str(uuid4())
        logger.info(f'Initialized LongTermMemory with corpus_id {self.default_corpus_id}')

    def _create_memory_chunk(self, message: Message, memory_id: str) -> Chunk:
        """Convert a Message to a Chunk for RAG indexing."""
        metadata = ChunkMetadata(corpus_id=self.default_corpus_id, memory_id=memory_id, timestamp=message.timestamp, action=message.action, wf_goal=message.wf_goal, agent=message.agent, msg_type=message.msg_type.value if message.msg_type else None, prompt=message.prompt, next_actions=message.next_actions, wf_task=message.wf_task, wf_task_desc=message.wf_task_desc, message_id=message.message_id, content=json.dumps(message.content))
        return Chunk(chunk_id=memory_id, text=str(message.content), metadata=metadata, start_char_idx=0, end_char_idx=len(str(message.content)))

    def _chunk_to_message(self, chunk: Chunk) -> Message:
        """Convert a Chunk to a Message object."""
        return Message(content=chunk.metadata.content, action=chunk.metadata.action, wf_goal=chunk.metadata.wf_goal, timestamp=chunk.metadata.timestamp, agent=chunk.metadata.agent, msg_type=chunk.metadata.msg_type, prompt=chunk.metadata.prompt, next_actions=chunk.metadata.next_actions, wf_task=chunk.metadata.wf_task, wf_task_desc=chunk.metadata.wf_task_desc, message_id=chunk.metadata.message_id)

    def add(self, messages: Union[Message, str, List[Union[Message, str]]]) -> List[str]:
        """Store messages in memory and index them in RAGEngine, returning memory_ids."""
        if not isinstance(messages, list):
            messages = [messages]
        messages = [Message(content=msg) if isinstance(msg, str) else msg for msg in messages]
        messages = [msg for msg in messages if msg.content]
        if not messages:
            logger.warning('No valid messages to add')
            return []
        existing_hashes = {record['content_hash'] for record in self.storage_handler.load(tables=[self.memory_table]).get(self.memory_table, []) if 'content_hash' in record}
        memory_ids = [str(uuid4()) for _ in messages]
        final_messages = []
        final_memory_ids = []
        final_chunks = []
        for msg, memory_id in zip(messages, memory_ids):
            content_hash = hashlib.sha256(str(msg.content).encode()).hexdigest()
            if content_hash in existing_hashes:
                logger.info(f'Duplicate message found (hash): {msg.content[:50]}...')
                existing_id = next((r['memory_id'] for r in self.storage_handler.load(tables=[self.memory_table]).get(self.memory_table, []) if r.get('content_hash') == content_hash), None)
                if existing_id:
                    final_memory_ids.append(existing_id)
                    continue
            final_messages.append(msg)
            final_memory_ids.append(memory_id)
            chunk = self._create_memory_chunk(msg, memory_id)
            chunk.metadata.content_hash = content_hash
            final_chunks.append(chunk)
        if not final_chunks:
            logger.info('No messages added after deduplication')
            return final_memory_ids
        for msg in final_messages:
            super().add_message(msg)
        corpus = Corpus(chunks=final_chunks, corpus_id=self.default_corpus_id)
        chunk_ids = self.rag_engine.add(index_type=self.rag_config.index.index_type, nodes=corpus, corpus_id=self.default_corpus_id)
        if not chunk_ids:
            logger.error('Failed to index memories')
            return final_memory_ids
        return final_memory_ids

    async def get(self, memory_ids: Union[str, List[str]], return_chunk: bool=True) -> List[Tuple[Union[Chunk, Message], str]]:
        """Retrieve memories by memory_ids, returning (Message/Chunk, memory_id) tuples."""
        if not isinstance(memory_ids, list):
            memory_ids = [memory_ids]
        if not memory_ids:
            logger.warning('No memory_ids provided for get')
            return []
        try:
            chunks = await self.rag_engine.aget(corpus_id=self.default_corpus_id, index_type=self.rag_config.index.index_type, node_ids=memory_ids)
            results = [(self._chunk_to_message(chunk), chunk.metadata.memory_id) if not return_chunk else (chunk, chunk.metadata.memory_id) for chunk in chunks if chunk]
            logger.info(f'Retrieved {len(results)} memories for memory_ids: {memory_ids}')
            return results
        except Exception as e:
            logger.error(f'Failed to get memories: {str(e)}')
            return []

    def delete(self, memory_ids: Union[str, List[str]]) -> List[bool]:
        """Delete memories by memory_ids, returning success status for each."""
        if not isinstance(memory_ids, list):
            memory_ids = [memory_ids]
        if not memory_ids:
            logger.warning('No memory_ids provided for deletion')
            return []
        successes = [False] * len(memory_ids)
        valid_memory_ids = []
        existing_chunks = asyncio.run(self.get(memory_ids, return_chunk=True))
        for idx, (chunk, mid) in enumerate(existing_chunks):
            if chunk:
                valid_memory_ids.append(mid)
                super().remove_message(self._chunk_to_message(chunk))
                successes[idx] = True
        if not valid_memory_ids:
            logger.info('No memories found for deletion')
            return successes
        self.rag_engine.delete(corpus_id=self.default_corpus_id, index_type=self.rag_config.index.index_type, node_ids=valid_memory_ids)
        return successes

    def update(self, updates: Union[Tuple[str, Union[Message, str]], List[Tuple[str, Union[Message, str]]]]) -> List[bool]:
        """Update memories with new content, returning success status for each."""
        if not isinstance(updates, list):
            updates = [updates]
        updates = [(mid, Message(content=msg) if isinstance(msg, str) else msg) for mid, msg in updates]
        updates_dict = {mid: msg for mid, msg in updates if msg.content}
        if not updates_dict:
            logger.warning('No valid updates provided')
            return []
        memory_ids = list(updates_dict.keys())
        existing_memories = asyncio.run(self.get(memory_ids, return_chunk=False))
        existing_dict = {mid: msg for msg, mid in existing_memories}
        successes = [False] * len(updates)
        final_updates = []
        final_memory_ids = []
        for mid, msg in updates_dict.items():
            if mid not in existing_dict:
                logger.warning(f'No memory found with memory_id {mid}')
                continue
            final_updates.append((mid, msg))
            final_memory_ids.append(mid)
            successes[memory_ids.index(mid)] = True
            super().remove_message(existing_dict[mid])
        if not final_updates:
            logger.info('No memories updated')
            return successes
        chunks = [self._create_memory_chunk(msg, mid) for mid, msg in final_updates]
        for msg in [msg for _, msg in final_updates]:
            super().add_message(msg)
        corpus = Corpus(chunks=chunks, corpus_id=self.default_corpus_id)
        chunk_ids = self.rag_engine.add(index_type=self.rag_config.index.index_type, nodes=corpus, corpus_id=self.default_corpus_id)
        if not chunk_ids:
            logger.error(f'Failed to update memories in RAG index: {final_memory_ids}')
            return [False] * len(updates)
        return successes

    async def search_async(self, query: Union[str, Query], n: Optional[int]=None, metadata_filters: Optional[Dict]=None, return_chunk=False) -> List[Tuple[Message, str]]:
        """Retrieve messages from RAG index asynchronously based on a query, returning messages and memory_ids."""
        if isinstance(query, str):
            query_obj = Query(query_str=query, top_k=n or self.rag_config.retrieval.top_k, metadata_filters=metadata_filters or {})
        else:
            query_obj = query
            query_obj.top_k = n or self.rag_config.retrieval.top_k
            if metadata_filters:
                query_obj.metadata_filters = {**query_obj.metadata_filters, **metadata_filters} if query_obj.metadata_filters else metadata_filters
        try:
            result: RagResult = await self.rag_engine.query_async(query_obj, corpus_id=self.default_corpus_id)
            if return_chunk:
                return [(chunk, chunk.metadata.memory_id) for chunk in result.corpus.chunks]
            else:
                messages = [(self._chunk_to_message(chunk), chunk.metadata.memory_id) for chunk in result.corpus.chunks]
            logger.info(f'Retrieved {len(messages)} memories for query: {query_obj.query_str}')
            return messages[:n] if n else messages
        except Exception as e:
            logger.error(f'Failed to search memories: {str(e)}')
            return []

    def search(self, query: Union[str, Query], n: Optional[int]=None, metadata_filters: Optional[Dict]=None) -> List[Tuple[Message, str]]:
        """Synchronous wrapper for searching memories."""
        return asyncio.run(self.search_async(query, n, metadata_filters))

    def clear(self) -> None:
        """Clear all messages and indices."""
        super().clear()
        self.rag_engine.clear(corpus_id=self.default_corpus_id)
        logger.info(f'Cleared LongTermMemory with corpus_id {self.default_corpus_id}')

    def save(self, save_path: Optional[str]=None) -> None:
        """Save all indices and memory data to database."""
        self.rag_engine.save(output_path=save_path, corpus_id=self.default_corpus_id, table=self.memory_table)

    def load(self, save_path: Optional[str]=None) -> List[str]:
        """Load memory data from database and reconstruct indices, returning memory_ids."""
        return self.rag_engine.load(source=save_path, corpus_id=self.default_corpus_id, table=self.memory_table)

def _create_memory_chunk(self, message: Message, memory_id: str) -> Chunk:
    """Convert a Message to a Chunk for RAG indexing."""
    metadata = ChunkMetadata(corpus_id=self.default_corpus_id, memory_id=memory_id, timestamp=message.timestamp, action=message.action, wf_goal=message.wf_goal, agent=message.agent, msg_type=message.msg_type.value if message.msg_type else None, prompt=message.prompt, next_actions=message.next_actions, wf_task=message.wf_task, wf_task_desc=message.wf_task_desc, message_id=message.message_id, content=json.dumps(message.content))
    return Chunk(chunk_id=memory_id, text=str(message.content), metadata=metadata, start_char_idx=0, end_char_idx=len(str(message.content)))

def get_openai_model_cost() -> dict:
    import json
    from importlib.resources import files
    json_path = files('litellm') / 'model_prices_and_context_window_backup.json'
    model_cost = json.loads(json_path.read_text(encoding='utf-8'))
    return model_cost

@register_model(config_cls=SiliconFlowConfig, alias=['siliconflow'])
class SiliconFlowLLM(OpenAILLM):

    def init_model(self):
        config: SiliconFlowConfig = self.config
        self._client = self._init_client(config)
        self._default_ignore_fields = ['llm_type', 'siliconflow_key', 'output_response']

    def _init_client(self, config: SiliconFlowConfig):
        client = OpenAI(api_key=config.siliconflow_key, base_url='https://api.siliconflow.cn/v1')
        return client

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.chat.completions.create(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._completion_cost(self.response)
            else:
                output: str = response.choices[0].message.content
                cost = self._completion_cost(response)
                if output_response:
                    print(output)
            self._update_cost(cost=cost)
        except Exception as e:
            if 'account balance is insufficient' in str(e):
                print('Warning: Account balance insufficient. Please recharge your account.')
                return ''
            raise RuntimeError(f'Error during single_generate of OpenAILLM: {str(e)}')
        return output

    def _completion_cost(self, response: ChatCompletion) -> Cost:
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        model: str = self.config.model
        if model not in model_cost:
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=0.0, output_cost=0.0)
        if 'token_cost' in model_cost[model]:
            input_cost = input_tokens * model_cost[model]['token_cost'] / 1000000.0
            output_cost = output_tokens * model_cost[model]['token_cost'] / 1000000.0
        else:
            input_cost = input_tokens * model_cost[model]['input_token_cost'] / 1000000.0
            output_cost = output_tokens * model_cost[model]['output_token_cost'] / 1000000.0
        return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)

    def get_cost(self) -> dict:
        cost_info = {}
        try:
            tokens = self.response.usage
            if tokens.prompt_tokens == -1:
                cost_info['note'] = 'Token counts not available in stream mode'
                cost_info['prompt_tokens'] = 0
                cost_info['completion_tokens'] = 0
                cost_info['total_tokens'] = 0
            else:
                cost_info['prompt_tokens'] = tokens.prompt_tokens
                cost_info['completion_tokens'] = tokens.completion_tokens
                cost_info['total_tokens'] = tokens.total_tokens
        except Exception as e:
            print(f'Error during get_cost of SiliconFlow: {str(e)}')
            cost_info['error'] = str(e)
        return cost_info

    def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
        output = ''
        last_chunk = None
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
            last_chunk = chunk
        if output_response:
            print('')
        if hasattr(last_chunk, 'usage'):
            self.response = last_chunk
        else:
            self.response = type('StreamResponse', (), {'usage': type('StreamUsage', (), {'prompt_tokens': -1, 'completion_tokens': -1, 'total_tokens': -1})})
        return output

    def _update_cost(self, cost: Cost):
        cost_manager.update_cost(cost=cost, model=self.config.model)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def single_generate(self, messages: List[dict], **kwargs) -> str:
    stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
    output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
    try:
        completion_params = self.get_completion_params(**kwargs)
        response = self._client.chat.completions.create(messages=messages, **completion_params)
        if stream:
            output = self.get_stream_output(response, output_response=output_response)
            cost = self._completion_cost(self.response)
        else:
            output: str = response.choices[0].message.content
            cost = self._completion_cost(response)
            if output_response:
                print(output)
        self._update_cost(cost=cost)
    except Exception as e:
        if 'account balance is insufficient' in str(e):
            print('Warning: Account balance insufficient. Please recharge your account.')
            return ''
        raise RuntimeError(f'Error during single_generate of OpenAILLM: {str(e)}')
    return output

@register_model(config_cls=OpenAILLMConfig, alias=['openai_llm'])
class OpenAILLM(BaseLLM):

    def init_model(self):
        config: OpenAILLMConfig = self.config
        self._client = self._init_client(config)
        self._default_ignore_fields = ['llm_type', 'output_response', 'openai_key', 'deepseek_key', 'anthropic_key', 'gemini_key', 'meta_llama_key', 'openrouter_key', 'openrouter_base', 'perplexity_key', 'groq_key']
        if self.config.model not in get_openai_model_cost():
            raise KeyError(f"'{self.config.model}' is not a valid OpenAI model name!")

    def _init_client(self, config: OpenAILLMConfig):
        client = OpenAI(api_key=config.openai_key)
        return client

    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        if system_messages:
            assert len(prompts) == len(system_messages), f'the number of prompts ({len(prompts)}) is different from the number of system_messages ({len(system_messages)})'
        else:
            system_messages = [None] * len(prompts)
        messages_list = []
        for prompt, system_message in zip(prompts, system_messages):
            messages = []
            if system_message:
                messages.append({'role': 'system', 'content': system_message})
            messages.append({'role': 'user', 'content': prompt})
            messages_list.append(messages)
        return messages_list

    def update_completion_params(self, params1: dict, params2: dict) -> dict:
        config_params: list = self.config.get_config_params()
        for key, value in params2.items():
            if key in self._default_ignore_fields:
                continue
            if key not in config_params:
                continue
            params1[key] = value
        return params1

    def get_completion_params(self, **kwargs):
        completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
        completion_params = self.update_completion_params(completion_params, kwargs)
        return completion_params

    def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
        """
        Process stream response and return the complete output.

        Args:
            response: The stream response from OpenAI
            output_response: Whether to print the response in real-time
            
        Returns:
            str: The complete output text
        """
        output = ''
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    async def get_stream_output_async(self, response, output_response: bool=False) -> str:
        """
        Process async stream response and return the complete output.
        
        Args:
            response (AsyncIterator[ChatCompletionChunk]): The async stream response from OpenAI
            output_response (bool): Whether to print the response in real-time
            
            
        Returns:
            str: The complete output text
        """
        output = ''
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    def get_completion_output(self, response: ChatCompletion, output_response: bool=True) -> str:
        output = response.choices[0].message.content
        if output_response:
            print(output)
        return output

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.chat.completions.create(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate of OpenAILLM: {str(e)}')
        return output

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            isolated_client = self._init_client(self.config)
            completion_params = self.get_completion_params(**kwargs)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: isolated_client.chat.completions.create(messages=messages, **completion_params))
            if stream:
                if hasattr(response, '__aiter__'):
                    output = await self.get_stream_output_async(response, output_response=output_response)
                else:
                    output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async of OpenAILLM: {str(e)}')
        return output

    def _completion_cost(self, response: ChatCompletion) -> Cost:
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _stream_cost(self, messages: List[dict], output: str) -> Cost:
        model: str = self.config.model
        input_tokens = token_counter(model=model, messages=messages)
        output_tokens = token_counter(model=model, text=output)
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        input_cost, output_cost = cost_per_token(model=self.config.model, prompt_tokens=input_tokens, completion_tokens=output_tokens)
        cost = Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)
        return cost

    def _update_cost(self, cost: Cost):
        cost_manager.update_cost(cost=cost, model=self.config.model)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def single_generate(self, messages: List[dict], **kwargs) -> str:
    stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
    output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
    try:
        completion_params = self.get_completion_params(**kwargs)
        response = self._client.chat.completions.create(messages=messages, **completion_params)
        if stream:
            output = self.get_stream_output(response, output_response=output_response)
            cost = self._stream_cost(messages=messages, output=output)
        else:
            output: str = self.get_completion_output(response=response, output_response=output_response)
            cost = self._completion_cost(response)
        self._update_cost(cost=cost)
    except Exception as e:
        raise RuntimeError(f'Error during single_generate of OpenAILLM: {str(e)}')
    return output

@register_model(config_cls=AliyunLLMConfig, alias=['aliyun_llm'])
class AliyunLLM(BaseLLM):

    def init_model(self):
        """
        Initialize the DashScope Generation client.
        """
        config: AliyunLLMConfig = self.config
        if not config.aliyun_api_key:
            raise ValueError('Aliyun API key is required. You should set `aliyun_api_key` in AliyunLLMConfig')
        os.environ['DASHSCOPE_API_KEY'] = config.aliyun_api_key
        dashscope.api_key = config.aliyun_api_key
        self._client = Generation()
        self._default_ignore_fields = ['llm_type', 'output_response', 'aliyun_api_key', 'aliyun_access_key_id', 'aliyun_access_key_secret', 'model_name']

    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        """
        Format messages for the Aliyun model.
        
        Args:
            prompts (List[str]): List of user prompts.
            system_messages (Optional[List[str]]): Optional list of system messages.
            
        Returns:
            List[List[dict]]: Formatted messages for the model.
        """
        if system_messages:
            assert len(prompts) == len(system_messages), f'the number of prompts ({len(prompts)}) is different from the number of system_messages ({len(system_messages)})'
        else:
            system_messages = [None] * len(prompts)
        messages_list = []
        for prompt, system_message in zip(prompts, system_messages):
            messages = []
            if system_message:
                messages.append({'role': 'system', 'content': system_message})
            messages.append({'role': 'user', 'content': prompt})
            messages_list.append(messages)
        return messages_list

    def update_completion_params(self, params1: dict, params2: dict) -> dict:
        """
        Update completion parameters with new values.
        
        Args:
            params1 (dict): Base parameters.
            params2 (dict): New parameters to update with.
            
        Returns:
            dict: Updated parameters.
        """
        config_params: list = self.config.get_config_params()
        for key, value in params2.items():
            if key in self._default_ignore_fields:
                continue
            if key not in config_params:
                continue
            params1[key] = value
        return params1

    def get_completion_params(self, **kwargs):
        """
        Get completion parameters for the model.
        
        Returns:
            dict: Parameters for model completion.
        """
        completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
        completion_params = self.update_completion_params(completion_params, kwargs)
        completion_params['model'] = self.config.model
        return completion_params

    def get_stream_output(self, response: Any, output_response: bool=True) -> str:
        """
        Process streaming response from the model.
        
        Args:
            response: The streaming response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
        output = ''
        try:
            for chunk in response:
                if not hasattr(chunk, 'output') or chunk.output is None:
                    error_msg = getattr(chunk, 'message', 'Invalid chunk format from model')
                    raise ValueError(f'Model stream chunk error: {error_msg}')
                if hasattr(chunk.output, 'text'):
                    content = chunk.output.text
                elif hasattr(chunk.output, 'choices') and chunk.output.choices:
                    content = chunk.output.choices[0].message.content
                else:
                    continue
                if content:
                    if output_response:
                        print(content, end='', flush=True)
                    output += content
        except Exception as e:
            print(f'Error processing stream: {str(e)}')
            if not output:
                raise RuntimeError(f'Failed to process stream response: {str(e)}')
        if output_response:
            print('')
        return output

    async def get_stream_output_async(self, response: Any, output_response: bool=False) -> str:
        """
        Process streaming response asynchronously.
        
        Args:
            response: The streaming response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
        output = ''
        try:
            async for chunk in response:
                if not hasattr(chunk, 'output') or chunk.output is None:
                    error_msg = getattr(chunk, 'message', 'Invalid chunk format from model')
                    raise ValueError(f'Model stream chunk error: {error_msg}')
                if hasattr(chunk.output, 'text'):
                    content = chunk.output.text
                elif hasattr(chunk.output, 'choices') and chunk.output.choices:
                    content = chunk.output.choices[0].message.content
                else:
                    continue
                if content:
                    if output_response:
                        print(content, end='', flush=True)
                    output += content
        except Exception as e:
            print(f'Error processing async stream: {str(e)}')
            if not output:
                raise RuntimeError(f'Failed to process async stream response: {str(e)}')
        if output_response:
            print('')
        return output

    def get_completion_output(self, response: Any, output_response: bool=True) -> str:
        """
        Process non-streaming response from the model.
        
        Args:
            response: The response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
        try:
            if not hasattr(response, 'output') or response.output is None:
                error_msg = getattr(response, 'message', 'Invalid response format from model')
                raise ValueError(f'Model response error: {error_msg}')
            if hasattr(response.output, 'text'):
                output = response.output.text
            elif hasattr(response.output, 'choices') and response.output.choices:
                output = response.output.choices[0].message.content
            else:
                raise ValueError('Unexpected response format')
            if output_response:
                print(output)
            return output
        except Exception as e:
            raise RuntimeError(f'Error processing completion response: {str(e)}')

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        """
        Generate a single response from the model.
        
        Args:
            messages (List[dict]): The conversation history.
            **kwargs: Additional parameters for generation.
            
        Returns:
            str: The generated response.
        """
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.call(messages=messages, **completion_params)
            if response is None:
                raise RuntimeError('Received empty response from model')
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(response)
            else:
                output = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
            return output
        except Exception as e:
            raise RuntimeError(f'Error during single_generate of AliyunLLM: {str(e)}')

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        """
        Generate responses for a batch of messages.
        
        Args:
            batch_messages (List[List[dict]]): List of conversation histories.
            **kwargs: Additional parameters for generation.
            
        Returns:
            List[str]: List of generated responses.
        """
        if not isinstance(batch_messages, list) or not batch_messages:
            raise ValueError('batch_messages must be a non-empty list of message lists')
        return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        """
        Asynchronously generate a single response.
        
        Args:
            messages (List[dict]): The conversation history.
            **kwargs: Additional parameters for the generation.
            
        Returns:
            str: The generated response.
        """
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            completion_params = self.get_completion_params(**kwargs)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self._client.call(messages=messages, **completion_params))
            if stream:
                output = await self.get_stream_output_async(response, output_response=output_response)
                cost = self._stream_cost(response)
            else:
                output = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
            return output
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async of AliyunLLM: {str(e)}')

    def _completion_cost(self, response: Any) -> Cost:
        """cost"""
        try:
            if not response:
                return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage'):
                usage = response.usage
                if hasattr(usage, 'input_tokens'):
                    input_tokens = usage.input_tokens
                elif hasattr(usage, 'prompt_tokens'):
                    input_tokens = usage.prompt_tokens
                if hasattr(usage, 'output_tokens'):
                    output_tokens = usage.output_tokens
                elif hasattr(usage, 'completion_tokens'):
                    output_tokens = usage.completion_tokens
            if input_tokens == 0 and output_tokens == 0 and hasattr(response, 'output'):
                if hasattr(response.output, 'text'):
                    output_tokens = len(response.output.text.split()) * 1.3
                elif hasattr(response.output, 'choices') and response.output.choices:
                    output_tokens = len(response.output.choices[0].message.content.split()) * 1.3
            total_cost = self._estimate_cost(input_tokens, output_tokens)
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=total_cost * 0.4, output_cost=total_cost * 0.6)
        except Exception as e:
            logger.warning(f'Error computing completion cost: {str(e)}')
            return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)

    def _stream_cost(self, response: Any) -> Cost:
        """cost"""
        try:
            if not response:
                return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage'):
                usage = response.usage
                if hasattr(usage, 'input_tokens'):
                    input_tokens = usage.input_tokens
                elif hasattr(usage, 'prompt_tokens'):
                    input_tokens = usage.prompt_tokens
                if hasattr(usage, 'output_tokens'):
                    output_tokens = usage.output_tokens
                elif hasattr(usage, 'completion_tokens'):
                    output_tokens = usage.completion_tokens
            if input_tokens == 0 and output_tokens == 0 and hasattr(response, 'output'):
                if hasattr(response.output, 'text'):
                    output_tokens = len(response.output.text.split()) * 1.3
                elif hasattr(response.output, 'choices') and response.output.choices:
                    output_tokens = len(response.output.choices[0].message.content.split()) * 1.3
            total_cost = self._estimate_cost(input_tokens, output_tokens)
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=total_cost * 0.4, output_cost=total_cost * 0.6)
        except Exception as e:
            logger.warning(f'Error computing stream cost: {str(e)}')
            return Cost(input_tokens=0, output_tokens=0, input_cost=0.0, output_cost=0.0)

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """cost
        
        """
        model = self.config.model.lower()
        if 'turbo' in model:
            input_cost = input_tokens / 1000 * 0.0005
            output_cost = output_tokens / 1000 * 0.001
        elif 'max' in model:
            input_cost = input_tokens / 1000 * 0.002
            output_cost = output_tokens / 1000 * 0.004
        else:
            input_cost = input_tokens / 1000 * 0.001
            output_cost = output_tokens / 1000 * 0.002
        return input_cost + output_cost

    def _update_cost(self, cost: Cost):
        """
        Update the cost manager with the new cost.
        
        Args:
            cost (Cost): The cost to update.
        """
        try:
            cost_manager.update_cost(cost=cost, model=self.config.model)
        except Exception as e:
            logger.warning(f'Error updating cost: {str(e)}')

def get_stream_output(self, response: Any, output_response: bool=True) -> str:
    """
        Process streaming response from the model.
        
        Args:
            response: The streaming response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
    output = ''
    try:
        for chunk in response:
            if not hasattr(chunk, 'output') or chunk.output is None:
                error_msg = getattr(chunk, 'message', 'Invalid chunk format from model')
                raise ValueError(f'Model stream chunk error: {error_msg}')
            if hasattr(chunk.output, 'text'):
                content = chunk.output.text
            elif hasattr(chunk.output, 'choices') and chunk.output.choices:
                content = chunk.output.choices[0].message.content
            else:
                continue
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
    except Exception as e:
        print(f'Error processing stream: {str(e)}')
        if not output:
            raise RuntimeError(f'Failed to process stream response: {str(e)}')
    if output_response:
        print('')
    return output

def get_completion_output(self, response: Any, output_response: bool=True) -> str:
    """
        Process non-streaming response from the model.
        
        Args:
            response: The response from the model.
            output_response (bool): Whether to print the response.
            
        Returns:
            str: The complete response text.
        """
    try:
        if not hasattr(response, 'output') or response.output is None:
            error_msg = getattr(response, 'message', 'Invalid response format from model')
            raise ValueError(f'Model response error: {error_msg}')
        if hasattr(response.output, 'text'):
            output = response.output.text
        elif hasattr(response.output, 'choices') and response.output.choices:
            output = response.output.choices[0].message.content
        else:
            raise ValueError('Unexpected response format')
        if output_response:
            print(output)
        return output
    except Exception as e:
        raise RuntimeError(f'Error processing completion response: {str(e)}')

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def single_generate(self, messages: List[dict], **kwargs) -> str:
    """
        Generate a single response from the model.
        
        Args:
            messages (List[dict]): The conversation history.
            **kwargs: Additional parameters for generation.
            
        Returns:
            str: The generated response.
        """
    stream = kwargs.get('stream', self.config.stream)
    output_response = kwargs.get('output_response', self.config.output_response)
    try:
        completion_params = self.get_completion_params(**kwargs)
        response = self._client.call(messages=messages, **completion_params)
        if response is None:
            raise RuntimeError('Received empty response from model')
        if stream:
            output = self.get_stream_output(response, output_response=output_response)
            cost = self._stream_cost(response)
        else:
            output = self.get_completion_output(response=response, output_response=output_response)
            cost = self._completion_cost(response)
        self._update_cost(cost=cost)
        return output
    except Exception as e:
        raise RuntimeError(f'Error during single_generate of AliyunLLM: {str(e)}')

@register_model(config_cls=OpenRouterConfig, alias=['openrouter'])
class OpenRouterLLM(BaseLLM):

    def init_model(self):
        config: OpenRouterConfig = self.config
        self._client = self._init_client(config)
        self._default_ignore_fields = ['llm_type', 'openrouter_key', 'openrouter_base', 'openrouter_model_base', 'output_response']

    def _init_client(self, config: OpenRouterConfig):
        client = OpenAI(api_key=config.openrouter_key, base_url=config.openrouter_base)
        return client

    def formulate_messages(self, prompts: List[str], system_messages: Optional[List[str]]=None) -> List[List[dict]]:
        if system_messages:
            assert len(prompts) == len(system_messages), f'the number of prompts ({len(prompts)}) is different from the number of system_messages ({len(system_messages)})'
        else:
            system_messages = [None] * len(prompts)
        messages_list = []
        for prompt, system_message in zip(prompts, system_messages):
            messages = []
            if system_message:
                messages.append({'role': 'system', 'content': system_message})
            messages.append({'role': 'user', 'content': prompt})
            messages_list.append(messages)
        return messages_list

    def update_completion_params(self, params1: dict, params2: dict) -> dict:
        config_params: list = self.config.get_config_params()
        for key, value in params2.items():
            if key in self._default_ignore_fields:
                continue
            if key not in config_params:
                continue
            params1[key] = value
        return params1

    def get_completion_params(self, **kwargs):
        completion_params = self.config.get_set_params(ignore=self._default_ignore_fields)
        completion_params = self.update_completion_params(completion_params, kwargs)
        return completion_params

    def get_stream_output(self, response: Stream, output_response: bool=True) -> str:
        output = ''
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    async def get_stream_output_async(self, response, output_response: bool=False) -> str:
        output = ''
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if output_response:
                    print(content, end='', flush=True)
                output += content
        if output_response:
            print('')
        return output

    def get_completion_output(self, response: ChatCompletion, output_response: bool=True) -> str:
        output = response.choices[0].message.content
        if output_response:
            print(output)
        return output

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            completion_params = self.get_completion_params(**kwargs)
            response = self._client.chat.completions.create(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate of OpenRouterLLM: {str(e)}')
        return output

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        return [self.single_generate(messages=one_messages, **kwargs) for one_messages in batch_messages]

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        stream = kwargs.get('stream', self.config.stream)
        output_response = kwargs.get('output_response', self.config.output_response)
        try:
            isolated_client = self._init_client(self.config)
            completion_params = self.get_completion_params(**kwargs)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: isolated_client.chat.completions.create(messages=messages, **completion_params))
            if stream:
                if hasattr(response, '__aiter__'):
                    output = await self.get_stream_output_async(response, output_response=output_response)
                else:
                    output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async of OpenRouterLLM: {str(e)}')
        return output

    def _completion_cost(self, response: ChatCompletion) -> Cost:
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _stream_cost(self, messages: List[dict], output: str) -> Cost:
        model: str = self.config.model
        input_tokens = token_counter(model=model, messages=messages)
        output_tokens = token_counter(model=model, text=output)
        return self._compute_cost(input_tokens=input_tokens, output_tokens=output_tokens)

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        input_cost_per_token, output_cost_per_token = self._get_cost()
        input_cost = input_tokens * input_cost_per_token
        output_cost = output_tokens * output_cost_per_token
        cost = Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=input_cost, output_cost=output_cost)
        return cost

    def _update_cost(self, cost: Cost):
        cost_manager.update_cost(cost=cost, model=self.config.model)

    def _get_cost(self):
        url = self.config.openrouter_model_base
        response = requests.get(url)
        data = response.json()
        for model in data['data']:
            if model['id'] == self.config.model:
                pricing = model.get('pricing', {})
                input_cost = float(pricing.get('prompt', 0))
                output_cost = float(pricing.get('completion', 0))
                return (input_cost, output_cost)
        return (0, 0)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def single_generate(self, messages: List[dict], **kwargs) -> str:
    stream = kwargs.get('stream', self.config.stream)
    output_response = kwargs.get('output_response', self.config.output_response)
    try:
        completion_params = self.get_completion_params(**kwargs)
        response = self._client.chat.completions.create(messages=messages, **completion_params)
        if stream:
            output = self.get_stream_output(response, output_response=output_response)
            cost = self._stream_cost(messages=messages, output=output)
        else:
            output: str = self.get_completion_output(response=response, output_response=output_response)
            cost = self._completion_cost(response)
        self._update_cost(cost=cost)
    except Exception as e:
        raise RuntimeError(f'Error during single_generate of OpenRouterLLM: {str(e)}')
    return output

class LLMOutputParser(Parser):
    """A basic parser for LLM-generated content.
    
    This parser stores the raw text generated by an LLM in the `.content` attribute
    and provides methods to extract structured data from this text using different
    parsing strategies.
    
    Attributes:
        content: The raw text generated by the LLM.
    """
    content: str = Field(default=None, exclude=True, description='the text generated by LLM')

    @classmethod
    def get_attrs(cls, return_type: bool=False) -> List[Union[str, tuple]]:
        """Returns the attributes of the LLMOutputParser class.
        
        Excludes ["class_name", "content"] by default.

        Args:
            return_type: Whether to return the type of the attributes along with their names.
        
        Returns:
            If `return_type` is True, returns a list of tuples where each tuple contains 
            the attribute name and its type. Otherwise, returns a list of attribute names.
        """
        attrs = []
        exclude_attrs = ['class_name', 'content']
        for field, field_info in cls.model_fields.items():
            if field not in exclude_attrs:
                if return_type:
                    field_type = get_type_name(field_info.annotation)
                    attrs.append((field, field_type))
                else:
                    attrs.append(field)
        return attrs

    @classmethod
    def get_attr_descriptions(cls) -> dict:
        """Returns the attributes and their descriptions.
        
        Returns:
            A dictionary mapping attribute names to their descriptions.
        """
        attrs = cls.get_attrs()
        results = {}
        for field_name, field_info in cls.model_fields.items():
            if field_name not in attrs:
                continue
            field_desc = field_info.description if field_info.description is not None else 'None'
            results[field_name] = field_desc
        return results

    @classmethod
    def get_content_data(cls, content: str, parse_mode: str='json', parse_func: Optional[Callable]=None, **kwargs) -> dict:
        """Parses LLM-generated content into a dictionary.
        
        This method takes content from an LLM response and converts it to a structured
        dictionary based on the specified parsing mode.

        Args:
            content: The content to parse.
            parse_mode: The mode to parse the content. Must be one of:
                - 'str': Assigns the raw text content to all attributes of the parser. 
                - 'json': Extracts and parses JSON objects from LLM output. It will return a dictionary parsed from the first valid JSON string.
                - 'xml': Parses content using XML tags. It will return a dictionary parsed from the XML tags.
                - 'title': Parses content with Markdown-style headings.
                - 'custom': Uses custom parsing logic. Requires providing `parse_func` parameter as a custom parsing function.
            parse_func: The function to parse the content, only valid when parse_mode is 'custom'.
            **kwargs (Any): Additional arguments passed to the parsing function.
        
        Returns:
            The parsed content as a dictionary.
            
        Raises:
            ValueError: If parse_mode is invalid or if parse_func is not provided when parse_mode is 'custom'.
        """
        attrs = cls.get_attrs()
        if len(attrs) <= 0:
            return {}
        if parse_mode == 'str':
            parse_func = cls._parse_str_content
        elif parse_mode == 'json':
            parse_func = cls._parse_json_content
        elif parse_mode == 'xml':
            parse_func = cls._parse_xml_content
        elif parse_mode == 'title':
            parse_func = cls._parse_title_content
        elif parse_mode == 'custom':
            if parse_func is None:
                raise ValueError("`parse_func` must be provided when `parse_mode` is 'custom'.")
            signature = inspect.signature(parse_func)
            if 'content' not in signature.parameters:
                raise ValueError('`parse_func` must have an input argument `content`.')
            func_args = {}
            func_args['content'] = content
            for param_name, param in signature.parameters.items():
                if param_name == 'content':
                    continue
                if param_name in kwargs:
                    func_args[param_name] = kwargs[param_name]
            data = parse_func(**func_args)
            if not isinstance(data, dict):
                raise ValueError(f'The output of `parse_func` must be a dictionary, but found {type(data)}.')
            return data
        else:
            raise ValueError(f"Invalid value '{parse_mode}' detected for `parse_mode`. Available choices: {PARSER_VALID_MODE}")
        data = parse_func(content=content, **kwargs)
        return data

    @classmethod
    def _parse_str_content(cls, content: str, **kwargs) -> dict:
        """Parses content by setting all attributes to the raw content.
        
        Args:
            content: The content to parse.
            **kwargs: Additional arguments (not used).
        
        Returns:
            A dictionary mapping all attributes to the raw content.
        """
        attrs = cls.get_attrs()
        return {attr: content for attr in attrs}

    @classmethod
    def _parse_json_content(cls, content: str, **kwargs) -> dict:
        """Parses content by extracting and parsing a JSON object. 
        If the content contains multiple JSON objects, only the first one will be used. 
        
        Args:
            content: The content containing a JSON object.
            **kwargs: Additional arguments (not used).
        
        Returns:
            The parsed JSON as a dictionary.
            
        Raises:
            ValueError: If the content doesn't contain a valid JSON object.
        """
        extracted_json_list = parse_json_from_text(content)
        if len(extracted_json_list) > 0:
            json_str = extracted_json_list[0]
            try:
                data = yaml.safe_load(json_str)
                if not isinstance(data, dict):
                    if isinstance(data, list):
                        attrs = cls.get_attrs()
                        if len(attrs) == 1:
                            return {attrs[0]: data}
                        else:
                            raise ValueError('The generated content is a list of JSON strings, but the attribute name for the list is not specified. You should instruct the LLM to specify the attribute name for the list.')
                    else:
                        raise ValueError(f'The generated content is not a valid JSON string:\n{json_str}')
            except Exception:
                raise ValueError(f'The generated content is not a valid JSON string:\n{json_str}')
        else:
            raise ValueError(f'The following generated content does not contain JSON string!\n{content}')
        return data

    @classmethod
    def _parse_xml_content(cls, content: str, **kwargs) -> dict:
        """Parses content by extracting values from XML tags.
        
        Each attribute of the parser is expected to be enclosed in XML tags
        with the attribute name as the tag name.
        
        Args:
            content: The content containing XML tags.
            **kwargs: Additional arguments (not used).
        
        Returns:
            A dictionary mapping attributes to their extracted values.
            
        Raises:
            ValueError: If the content is missing expected XML tags or if the
                        extracted values can't be converted to the expected types.
        """
        attrs_with_types: List[tuple] = cls.get_attrs(return_type=True)
        data = {}
        for attr, attr_type in attrs_with_types:
            attr_raw_value_list = parse_xml_from_text(text=content, label=attr)
            if len(attr_raw_value_list) > 0:
                attr_raw_value = attr_raw_value_list[0]
                try:
                    attr_value = parse_data_from_text(text=attr_raw_value, datatype=attr_type)
                except Exception:
                    raise ValueError(f'Cannot parse text: {attr_raw_value} into {attr_type} data!')
            else:
                raise ValueError(f'The following generated content does not contain xml label <{attr}>xxx</{attr}>!\n{content}')
            data[attr] = attr_value
        return data

    @classmethod
    def _parse_title_content(cls, content: str, title_format: str='## {title}', **kwargs) -> dict:
        """Parses content with markdown-style titles.
        
        Extracts sections from content that are divided by titles following
        the specified format described in `title_format`. The default format is "## {title}".
        For example:
        ```
        ## title1
        content1
        ## title2
        content2
        ```
        This content will be parsed into:
        ```
        {
            "title1": "content1",
            "title2": "content2"
        }
        ```
        Args:
            content: The content with title-divided sections.
            title_format: The format of the titles, default is "## {title}".
            **kwargs: Additional arguments (not used).

        Returns:
            A dictionary mapping title names to their section contents.
        """
        attrs: List[str] = cls.get_attrs()
        if not attrs:
            return {}
        output_titles = [title_format.format(title=attr) for attr in attrs]

        def is_output_title(text: str):
            for title in output_titles:
                if text.strip().lower().startswith(title.lower()):
                    return (True, title)
            return (False, None)
        data = {}
        current_output_name: str = None
        current_output_content: list = None
        for line in content.split('\n'):
            is_title, title = is_output_title(line)
            if is_title:
                if current_output_name is not None and current_output_content is not None:
                    data[current_output_name] = '\n'.join(current_output_content)
                current_output_content = []
                current_output_name = title.replace('#', '').strip()
                output_titles.remove(title)
            elif current_output_content is not None:
                current_output_content.append(line)
        if current_output_name is not None and current_output_content is not None:
            data[current_output_name] = '\n'.join(current_output_content)
        return data

    @classmethod
    def parse(cls, content: str, parse_mode: str='json', parse_func: Optional[Callable]=None, **kwargs) -> 'LLMOutputParser':
        """Parses LLM-generated text into a structured parser instance.
        
        This is the main method for creating parser instances from LLM output.
        
        Args:
            content: The text generated by the LLM.
            parse_mode: The mode to parse the content, must be one of:
                - 'str': Assigns the raw text content to all attributes of the parser. 
                - 'json': Extracts and parses JSON objects from LLM output. Uses the first valid JSON string to create an instance of LLMOutputParser.
                - 'xml': Parses content using XML tags. Uses the XML tags to create an instance of LLMOutputParser.
                - 'title': Parses content with Markdown-style headings. Uses the Markdown-style headings to create an instance of LLMOutputParser. The default title format is "## {title}", you can change it by providing `title_format` parameter, which should be a string that contains `{title}` placeholder. 
                - 'custom': Uses custom parsing logic. Requires providing `parse_func` parameter as a custom parsing function. The `parse_func` must have a parameter named `content` and return a dictionary where the keys are the attribute names and the values are the parsed data. 
            parse_func: The function to parse the content, only valid when `parse_mode` is 'custom'.
            **kwargs (Any): Additional arguments passed to parsing functions, such as:
                - `title_format` for `parse_mode="title"`.
            
        Returns:
            An instance of LLMOutputParser containing the parsed data.
            
        Raises:
            ValueError: If parse_mode is invalid or if content is not a string.
        """
        if parse_mode not in PARSER_VALID_MODE:
            raise ValueError(f"'{parse_mode}' is an invalid value for `parse_mode`. Available choices: {PARSER_VALID_MODE}.")
        if not isinstance(content, str):
            raise ValueError(f'The input to {cls.__name__}.parse should be a str, but found {type(content)}.')
        data = cls.get_content_data(content=content, parse_mode=parse_mode, parse_func=parse_func, **kwargs)
        data.update({'content': content})
        parser = cls.from_dict(data, **kwargs)
        return parser

    def __str__(self) -> str:
        """
        Returns a string representation of the parser.
        """
        return self.to_str()

    def to_str(self, **kwargs) -> str:
        """
        Converts the parser to a string.
        """
        return self.content

    def get_structured_data(self) -> dict:
        """Extracts structured data from the parser.
        
        Returns:
            A dictionary containing only the defined attributes and their values,
            excluding metadata like class_name.
        """
        attrs = type(self).get_attrs()
        data = self.to_dict(ignore=['class_name'])
        structured_data = {key: value for key, value in data.items() if key in attrs}
        return structured_data

@classmethod
def _parse_json_content(cls, content: str, **kwargs) -> dict:
    """Parses content by extracting and parsing a JSON object. 
        If the content contains multiple JSON objects, only the first one will be used. 
        
        Args:
            content: The content containing a JSON object.
            **kwargs: Additional arguments (not used).
        
        Returns:
            The parsed JSON as a dictionary.
            
        Raises:
            ValueError: If the content doesn't contain a valid JSON object.
        """
    extracted_json_list = parse_json_from_text(content)
    if len(extracted_json_list) > 0:
        json_str = extracted_json_list[0]
        try:
            data = yaml.safe_load(json_str)
            if not isinstance(data, dict):
                if isinstance(data, list):
                    attrs = cls.get_attrs()
                    if len(attrs) == 1:
                        return {attrs[0]: data}
                    else:
                        raise ValueError('The generated content is a list of JSON strings, but the attribute name for the list is not specified. You should instruct the LLM to specify the attribute name for the list.')
                else:
                    raise ValueError(f'The generated content is not a valid JSON string:\n{json_str}')
        except Exception:
            raise ValueError(f'The generated content is not a valid JSON string:\n{json_str}')
    else:
        raise ValueError(f'The following generated content does not contain JSON string!\n{content}')
    return data

def _get_image_data_url(image_chunk) -> str:
    """Convert ImageChunk to data URL format for model consumption."""
    try:
        image = image_chunk.get_image()
        if image is None:
            raise ValueError(f'Could not load image from path: {image_chunk.image_path}')
        buffer = io.BytesIO()
        format_name = 'PNG'
        if image_chunk.image_mimetype:
            format_name = image_chunk.image_mimetype.split('/')[-1].upper()
            if format_name not in ['PNG', 'JPEG', 'JPG', 'GIF', 'WEBP']:
                format_name = 'PNG'
        image.save(buffer, format=format_name)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        mime_type = image_chunk.image_mimetype or f'image/{format_name.lower()}'
        return f'data:{mime_type};base64,{image_data}'
    except Exception as e:
        raise RuntimeError(f'Failed to convert image to data URL: {str(e)}')

@register_model(config_cls=LiteLLMConfig, alias=['litellm'])
class LiteLLM(OpenAILLM):

    def init_model(self):
        """
        Initialize the model based on the configuration.
        """
        if self.config.llm_type != 'LiteLLM':
            raise ValueError("llm_type must be 'LiteLLM'")
        self.model = self.config.model
        self.api_base = self.config.api_base
        self.api_key = self.config.api_key
        company = infer_litellm_company_from_model(self.model)
        if self.config.is_local or company == 'local':
            if not self.api_base:
                raise ValueError('api_base is required for local models in LiteLLMConfig')
            litellm.api_base = self.api_base
            litellm.api_key = self.api_key
        elif company == 'openai':
            if not self.config.openai_key:
                raise ValueError('OpenAI API key is required for OpenAI models. You should set `openai_key` in LiteLLMConfig')
            os.environ['OPENAI_API_KEY'] = self.config.openai_key
        elif company == 'azure':
            if not self.config.azure_key or not self.config.azure_endpoint:
                raise ValueError('Azure OpenAI key and endpoint are required for Azure models. You should set `azure_key` and `azure_endpoint` in LiteLLMConfig')
            os.environ['AZURE_API_KEY'] = self.config.azure_key
            os.environ['AZURE_API_BASE'] = self.config.azure_endpoint
            if self.config.api_version:
                os.environ['AZURE_API_VERSION'] = self.config.api_version
        elif company == 'deepseek':
            if not self.config.deepseek_key:
                raise ValueError('DeepSeek API key is required for DeepSeek models. You should set `deepseek_key` in LiteLLMConfig')
            os.environ['DEEPSEEK_API_KEY'] = self.config.deepseek_key
        elif company == 'anthropic':
            if not self.config.anthropic_key:
                raise ValueError('Anthropic API key is required for Anthropic models. You should set `anthropic_key` in LiteLLMConfig')
            os.environ['ANTHROPIC_API_KEY'] = self.config.anthropic_key
        elif company == 'gemini':
            if not self.config.gemini_key:
                raise ValueError('Gemini API key is required for Gemini models. You should set `gemini_key` in LiteLLMConfig')
            os.environ['GEMINI_API_KEY'] = self.config.gemini_key
        elif company == 'meta_llama':
            if not self.config.meta_llama_key:
                raise ValueError('Meta Llama API key is required for Meta Llama models. You should set `meta_llama_key` in LiteLLMConfig')
            os.environ['LLAMA_API_KEY'] = self.config.meta_llama_key
        elif company == 'openrouter':
            if not self.config.openrouter_key:
                raise ValueError('OpenRouter API key is required for OpenRouter models. You should set `openrouter_key` in LiteLLMConfig. You can also set `openrouter_base` in LiteLLMConfig to use a custom base URL [optional]')
            os.environ['OPENROUTER_API_KEY'] = self.config.openrouter_key
            os.environ['OPENROUTER_API_BASE'] = self.config.openrouter_base
        elif company == 'perplexity':
            if not self.config.perplexity_key:
                raise ValueError('Perplexity API key is required for Perplexity models. You should set `perplexity_key` in LiteLLMConfig')
            os.environ['PERPLEXITYAI_API_KEY'] = self.config.perplexity_key
        elif company == 'groq':
            if not self.config.groq_key:
                raise ValueError('Groq API key is required for Groq models. You should set `groq_key` in LiteLLMConfig')
            os.environ['GROQ_API_KEY'] = self.config.groq_key
        else:
            raise ValueError(f'Unsupported company: {company}')
        self._default_ignore_fields = ['llm_type', 'output_response', 'openai_key', 'deepseek_key', 'anthropic_key', 'gemini_key', 'meta_llama_key', 'openrouter_key', 'openrouter_base', 'perplexity_key', 'groq_key', 'api_base', 'is_local', 'azure_endpoint', 'azure_key', 'api_version', 'api_key']

    def _compute_cost(self, input_tokens: int, output_tokens: int) -> Cost:
        if self.config.is_local:
            return Cost(input_tokens=input_tokens, output_tokens=output_tokens, input_cost=0.0, output_cost=0.0)
        return super()._compute_cost(input_tokens, output_tokens)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def single_generate(self, messages: List[dict], **kwargs) -> str:
        """
        Generate a single response using the completion function.

        Args: 
            messages (List[dict]): A list of dictionaries representing the conversation history.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            str: A string containing the model's response.
        """
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            company = infer_litellm_company_from_model(self.model)
            if self.config.is_local or company == 'local':
                completion_params['api_base'] = self.api_base
            elif company == 'azure':
                completion_params['api_base'] = self.config.azure_endpoint
                completion_params['api_version'] = self.config.api_version
                completion_params['api_key'] = self.config.azure_key
            response = completion(messages=messages, **completion_params)
            if stream:
                output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response=response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate: {str(e)}')
        return output

    def batch_generate(self, batch_messages: List[List[dict]], **kwargs) -> List[str]:
        """
        Generate responses for a batch of messages.

        Args: 
            batch_messages (List[List[dict]]): A list of message lists, where each sublist represents a conversation.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            List[str]: A list of responses for each conversation.
        """
        results = []
        for messages in batch_messages:
            response = self.single_generate(messages, **kwargs)
            results.append(response)
        return results

    async def single_generate_async(self, messages: List[dict], **kwargs) -> str:
        """
        Generate a single response using the async completion function.

        Args: 
            messages (List[dict]): A list of dictionaries representing the conversation history.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            str: A string containing the model's response.
        """
        stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
        output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
        try:
            completion_params = self.get_completion_params(**kwargs)
            company = infer_litellm_company_from_model(self.model)
            if self.config.is_local or company == 'local':
                completion_params['api_base'] = self.api_base
            elif company == 'azure':
                completion_params['api_base'] = self.config.azure_endpoint
                completion_params['api_version'] = self.config.api_version
                completion_params['api_key'] = self.config.azure_key
            response = await acompletion(messages=messages, **completion_params)
            if stream:
                if hasattr(response, '__aiter__'):
                    output = await self.get_stream_output_async(response, output_response=output_response)
                else:
                    output = self.get_stream_output(response, output_response=output_response)
                cost = self._stream_cost(messages=messages, output=output)
            else:
                output: str = self.get_completion_output(response=response, output_response=output_response)
                cost = self._completion_cost(response=response)
            self._update_cost(cost=cost)
        except Exception as e:
            raise RuntimeError(f'Error during single_generate_async: {str(e)}')
        return output

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def single_generate(self, messages: List[dict], **kwargs) -> str:
    """
        Generate a single response using the completion function.

        Args: 
            messages (List[dict]): A list of dictionaries representing the conversation history.
            **kwargs (Any): Additional parameters to be passed to the `completion` function.
        
        Returns: 
            str: A string containing the model's response.
        """
    stream = kwargs['stream'] if 'stream' in kwargs else self.config.stream
    output_response = kwargs['output_response'] if 'output_response' in kwargs else self.config.output_response
    try:
        completion_params = self.get_completion_params(**kwargs)
        company = infer_litellm_company_from_model(self.model)
        if self.config.is_local or company == 'local':
            completion_params['api_base'] = self.api_base
        elif company == 'azure':
            completion_params['api_base'] = self.config.azure_endpoint
            completion_params['api_version'] = self.config.api_version
            completion_params['api_key'] = self.config.azure_key
        response = completion(messages=messages, **completion_params)
        if stream:
            output = self.get_stream_output(response, output_response=output_response)
            cost = self._stream_cost(messages=messages, output=output)
        else:
            output: str = self.get_completion_output(response=response, output_response=output_response)
            cost = self._completion_cost(response=response)
        self._update_cost(cost=cost)
    except Exception as e:
        raise RuntimeError(f'Error during single_generate: {str(e)}')
    return output

class CustomizeAction(Action):
    parse_mode: Optional[str] = Field(default='title', description="the parse mode of the action, must be one of: ['title', 'str', 'json', 'xml', 'custom']")
    parse_func: Optional[Callable] = Field(default=None, exclude=True, description='the function to parse the LLM output. It receives the LLM output and returns a dict.')
    title_format: Optional[str] = Field(default='## {title}', exclude=True, description="the format of the title. It is used when the `parse_mode` is 'title'.")
    custom_output_format: Optional[str] = Field(default=None, exclude=True, description='the format of the output. It is used when the `prompt_template` is provided.')
    tools: Optional[List[Toolkit]] = Field(default=None, description='The tools that the action can use')
    conversation: Optional[Message] = Field(default=None, description='Current conversation state')
    max_tool_try: int = Field(default=2, description='Maximum number of tool calling attempts allowed')

    def __init__(self, **kwargs):
        name = kwargs.pop('name', 'CustomizeAction')
        description = kwargs.pop('description', 'Customized action that can use tools to accomplish its task')
        super().__init__(name=name, description=description, **kwargs)
        if not self.prompt and (not self.prompt_template):
            raise ValueError('`prompt` or `prompt_template` is required when creating CustomizeAction action')
        if self.prompt and self.prompt_template:
            logger.warning('Both `prompt` and `prompt_template` are provided for CustomizeAction action. Prioritizing `prompt_template` and ignoring `prompt`.')
        if self.tools:
            self.tools_caller = {}
            self.add_tools(self.tools)

    def prepare_action_prompt(self, inputs: Optional[dict]=None, system_prompt: Optional[str]=None, **kwargs) -> Union[str, List[dict]]:
        """Prepare prompt for action execution.
        
        This helper function transforms the input dictionary into a formatted prompt
        for the language model, handling different prompting modes.
        
        Args:
            inputs: Dictionary of input parameters
            system_prompt: Optional system prompt to include
            
        Returns:
            Union[str, List[dict]]: Formatted prompt ready for LLM (string or chat messages)
            
        Raises:
            TypeError: If an input value type is not supported
            ValueError: If neither prompt nor prompt_template is available
        """
        if inputs is None:
            inputs = {}
        prompt_params_names = self.inputs_format.get_attrs()
        prompt_params_values = {}
        for param in prompt_params_names:
            value = inputs.get(param, '')
            if isinstance(value, str):
                prompt_params_values[param] = value
            elif isinstance(value, (dict, list)):
                prompt_params_values[param] = json.dumps(value, indent=4)
            else:
                raise TypeError(f'The input type {type(value)} is invalid! Valid types: [str, dict, list].')
        if self.prompt:
            prompt = self.prompt.format(**prompt_params_values) if prompt_params_values else self.prompt
            if self.tools:
                tools_schemas = [j['function'] for i in [tool.get_tool_schemas() for tool in self.tools] for j in i]
                prompt += '\n\n' + TOOL_CALLING_TEMPLATE.format(tools_description=tools_schemas)
            return prompt
        else:
            if self.tools:
                self.prompt_template.set_tools(self.tools)
            return self.prompt_template.format(system_prompt=system_prompt, values=prompt_params_values, inputs_format=self.inputs_format, outputs_format=self.outputs_format, parse_mode=self.parse_mode, title_format=self.title_format, custom_output_format=self.custom_output_format, tools=self.tools)

    def prepare_extraction_prompt(self, llm_output_content: str) -> str:
        """Prepare extraction prompt for fallback extraction when parsing fails.
        
        Args:
            self: The action instance
            llm_output_content: Raw output content from LLM
            
        Returns:
            str: Formatted extraction prompt
        """
        attr_descriptions: dict = self.outputs_format.get_attr_descriptions()
        output_description_list = []
        for i, (name, desc) in enumerate(attr_descriptions.items()):
            output_description_list.append(f'{i + 1}. {name}\nDescription: {desc}')
        output_description = '\n\n'.join(output_description_list)
        return OUTPUT_EXTRACTION_PROMPT.format(text=llm_output_content, output_description=output_description)

    def _get_unique_class_name(self, candidate_name: str) -> str:
        """
        Get a unique class name by checking if it already exists in the registry.
        If it does, append "Vx" to make it unique.
        """
        if not MODULE_REGISTRY.has_module(candidate_name):
            return candidate_name
        i = 1
        while True:
            unique_name = f'{candidate_name}V{i}'
            if not MODULE_REGISTRY.has_module(unique_name):
                break
            i += 1
        return unique_name

    def add_tools(self, tools: Union[Toolkit, List[Toolkit]]):
        if not tools:
            return
        if isinstance(tools, Toolkit):
            tools = [tools]
        if not all((isinstance(tool, Toolkit) for tool in tools)):
            raise TypeError('`tools` must be a Toolkit or list of Toolkit instances.')
        if not self.tools:
            self.tools_caller = {}
            self.tools = []
        for toolkit in tools:
            try:
                tool_callers = toolkit.get_tools()
                if not isinstance(tool_callers, list):
                    logger.warning(f"Expected list of tool functions from '{toolkit.name}.get_tools()', got {type(tool_callers)}.")
                    continue
                valid_tools_count = 0
                valid_tools_names, valid_tool_callers = ([], [])
                for tool_caller in tool_callers:
                    tool_caller_name = getattr(tool_caller, 'name', None)
                    if not tool_caller_name or not callable(tool_caller):
                        logger.warning(f"Invalid tool function in '{toolkit.name}': missing name or not callable.")
                        continue
                    if tool_caller_name in self.tools_caller:
                        logger.warning(f"Duplicate tool function '{tool_caller_name}' detected. Overwriting previous function.")
                    valid_tools_count += 1
                    valid_tools_names.append(tool_caller_name)
                    valid_tool_callers.append(tool_caller)
                if valid_tools_count == 0:
                    logger.info(f"No valid tools found in toolkit '{toolkit.name}'. Skipping.")
                    continue
                if valid_tools_count > 0 and all((name in self.tools_caller for name in valid_tools_names)):
                    logger.info(f"All tools from toolkit '{toolkit.name}' are already added. Skipping.")
                    continue
                if valid_tools_count > 0:
                    self.tools_caller.update({name: caller for name, caller in zip(valid_tools_names, valid_tool_callers)})
                existing_toolkit_names = {tkt.name for tkt in self.tools}
                if valid_tools_count > 0 and toolkit.name not in existing_toolkit_names:
                    self.tools.append(toolkit)
                if valid_tools_count > 0:
                    logger.info(f"Added toolkit '{toolkit.name}' with {valid_tools_count} valid tools in {self.name}: {valid_tools_names}.")
            except Exception as e:
                logger.error(f"Failed to load tools from toolkit '{toolkit.name}': {e}")

    def _extract_tool_calls(self, llm_output: str, llm: Optional[BaseLLM]=None) -> List[dict]:
        pattern = '<ToolCalling>\\s*(.*?)\\s*</ToolCalling>'
        matches = re.findall(pattern, llm_output, re.DOTALL)
        if not matches:
            return []
        parsed_tool_calls = []
        for match_content in matches:
            try:
                json_content = match_content.strip()
                json_list = parse_json_from_text(json_content)
                if not json_list:
                    logger.warning('No valid JSON found in ToolCalling block')
                    continue
                parsed_tool_call = json.loads(json_list[0])
                if isinstance(parsed_tool_call, dict):
                    parsed_tool_calls.append(parsed_tool_call)
                elif isinstance(parsed_tool_call, list):
                    parsed_tool_calls.extend(parsed_tool_call)
                else:
                    logger.warning(f'Invalid tool call format: {parsed_tool_call}')
                    continue
            except (json.JSONDecodeError, IndexError) as e:
                logger.warning(f'Failed to parse tool calls from LLM output: {e}')
                if llm is not None:
                    retry_prompt = TOOL_CALLING_RETRY_PROMPT.format(text=match_content)
                    try:
                        fixed_output = llm.generate(prompt=retry_prompt).content.strip()
                        logger.info(f'Retrying tool call parse with fixed output:\n{fixed_output}')
                        fixed_list = parse_json_from_text(fixed_output)
                        if fixed_list:
                            parsed_tool_call = json.loads(fixed_list[0])
                            if isinstance(parsed_tool_call, dict):
                                parsed_tool_calls.append(parsed_tool_call)
                        elif isinstance(parsed_tool_call, list):
                            parsed_tool_calls.extend(parsed_tool_call)
                    except Exception as retry_err:
                        logger.error(f'Retry failed: {retry_err}')
                        continue
            else:
                continue
        return parsed_tool_calls

    def _extract_output(self, llm_output: Any, llm: BaseLLM=None, **kwargs):
        llm_output_content = getattr(llm_output, 'content', str(llm_output))
        output_attrs = self.outputs_format.get_attrs()
        if not output_attrs:
            output = self.outputs_format.parse(content=llm_output_content)
            return output
        try:
            parsed_output = self.outputs_format.parse(content=llm_output_content, parse_mode=self.parse_mode, parse_func=getattr(self, 'parse_func', None), title_format=getattr(self, 'title_format', '## {title}'))
            return parsed_output
        except Exception as e:
            logger.info(f"Failed to parse with action's parse settings: {e}")
            logger.info('Falling back to using LLM to extract outputs...')
            extraction_prompt = self.prepare_extraction_prompt(llm_output_content)
            llm_extracted_output: LLMOutputParser = llm.generate(prompt=extraction_prompt)
            llm_extracted_data: dict = parse_json_from_llm_output(llm_extracted_output.content)
            output = self.outputs_format.from_dict(llm_extracted_data)
            return output

    async def _async_extract_output(self, llm_output: Any, llm: BaseLLM=None, **kwargs):
        llm_output_content = getattr(llm_output, 'content', str(llm_output))
        output_attrs = self.outputs_format.get_attrs()
        if not output_attrs:
            output = self.outputs_format.parse(content=llm_output_content)
            return output
        try:
            parsed_output = self.outputs_format.parse(content=llm_output_content, parse_mode=self.parse_mode, parse_func=getattr(self, 'parse_func', None), title_format=getattr(self, 'title_format', '## {title}'))
            return parsed_output
        except Exception as e:
            logger.info(f"Failed to parse with action's parse settings: {e}")
            logger.info('Falling back to using LLM to extract outputs...')
            extraction_prompt = self.prepare_extraction_prompt(llm_output_content)
            llm_extracted_output = await llm.async_generate(prompt=extraction_prompt)
            llm_extracted_data: dict = parse_json_from_llm_output(llm_extracted_output.content)
            output = self.outputs_format.from_dict(llm_extracted_data)
            return output

    def _call_single_tool(self, function_param: dict) -> tuple:
        try:
            function_name = function_param.get('function_name')
            function_args = function_param.get('function_args') or {}
            if not function_name:
                return (None, 'No function name provided')
            callable_fn = self.tools_caller.get(function_name)
            if not callable(callable_fn):
                return (None, f"Function '{function_name}' not found or not callable")
            print('_____________________ Start Function Calling _____________________')
            print(f'Executing function calling: {function_name} with parameters: {function_args}')
            result = callable_fn(**function_args)
            return (result, None)
        except Exception as e:
            logger.error(f'Error executing tool {function_name}: {e}')
            return (None, f'Error executing tool {function_name}: {str(e)}')

    def _calling_tools(self, tool_call_args: List[dict]) -> dict:
        errors = []
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_tool = {executor.submit(self._call_single_tool, param): param for param in tool_call_args}
            for future in concurrent.futures.as_completed(future_to_tool):
                result, error = future.result()
                if error:
                    errors.append(error)
                if result is not None:
                    results.append(result)
        return {'result': results, 'error': errors}

    async def _async_call_single_tool(self, function_param: dict) -> tuple:
        try:
            function_name = function_param.get('function_name')
            function_args = function_param.get('function_args') or {}
            if not function_name:
                return (None, 'No function name provided')
            callable_fn = self.tools_caller.get(function_name)
            if not callable(callable_fn):
                return (None, f"Function '{function_name}' not found or not callable")
            print('_____________________ Start Function Calling _____________________')
            print(f'Executing function calling: {function_name} with parameters: {function_args}')
            if inspect.iscoroutinefunction(callable_fn):
                result = await callable_fn(**function_args)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: callable_fn(**function_args))
            return (result, None)
        except Exception as e:
            logger.error(f'Error executing tool {function_name}: {e}')
            return (None, f'Error executing tool {function_name}: {str(e)}')

    async def _async_calling_tools(self, tool_call_args: List[dict]) -> dict:
        tasks = [self._async_call_single_tool(param) for param in tool_call_args]
        results_with_errors = await asyncio.gather(*tasks)
        results = [res for res, err in results_with_errors if err is None and res is not None]
        errors = [err for _, err in results_with_errors if err is not None]
        return {'result': results, 'error': errors}

    def execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, time_out=0, **kwargs):
        input_attributes: dict = self.inputs_format.get_attr_descriptions()
        if not inputs and input_attributes:
            logger.error('CustomizeAction action received invalid `inputs`: None or empty.')
            raise ValueError('The `inputs` to CustomizeAction action is None or empty.')
        if inputs is None:
            inputs = {}
        final_llm_response = None
        if self.prompt_template:
            if isinstance(self.prompt_template, ChatTemplate):
                conversation = self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)
            elif isinstance(self.prompt_template, StringTemplate):
                conversation = [{'role': 'system', 'content': self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)}]
            else:
                raise ValueError(f'`prompt_template` must be a StringTemplate or ChatTemplate instance, but got {type(self.prompt_template)}')
        else:
            conversation = [{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)}]
        prompt_params_values = {k: inputs.get(k, '') for k in input_attributes.keys()}
        while True:
            if time_out > self.max_tool_try:
                current_prompt = self.prepare_action_prompt(inputs=prompt_params_values or {})
                content_to_extract = final_llm_response if final_llm_response is not None else '{content}'.format(content=conversation)
                if return_prompt:
                    return (self._extract_output(content_to_extract, llm=llm), current_prompt)
                return self._extract_output(content_to_extract, llm=llm)
            time_out += 1
            llm_response = llm.generate(messages=conversation)
            conversation.append({'role': 'assistant', 'content': llm_response.content})
            final_llm_response = llm_response
            tool_call_args = self._extract_tool_calls(llm_response.content)
            if not tool_call_args:
                break
            logger.info('Extracted tool call args:')
            logger.info(json.dumps(tool_call_args, indent=4))
            results = self._calling_tools(tool_call_args)
            logger.info('Tool call results:')
            logger.info(json.dumps(results, indent=4))
            conversation.append({'role': 'assistant', 'content': TOOL_CALLING_HISTORY_PROMPT.format(iteration_number=time_out, tool_call_args=f'{tool_call_args}', results=f'{results}')})
        current_prompt = self.prepare_action_prompt(inputs=prompt_params_values or {})
        content_to_extract = final_llm_response if final_llm_response is not None else '{content}'.format(content=conversation)
        if return_prompt:
            return (self._extract_output(content_to_extract, llm=llm), current_prompt)
        return self._extract_output(content_to_extract, llm=llm)

    async def async_execute(self, llm: Optional[BaseLLM]=None, inputs: Optional[dict]=None, sys_msg: Optional[str]=None, return_prompt: bool=False, time_out=0, **kwargs):
        input_attributes: dict = self.inputs_format.get_attr_descriptions()
        if not inputs and input_attributes:
            logger.error('CustomizeAction action received invalid `inputs`: None or empty.')
            raise ValueError('The `inputs` to CustomizeAction action is None or empty.')
        if inputs is None:
            inputs = {}
        final_llm_response = None
        if self.prompt_template:
            if isinstance(self.prompt_template, ChatTemplate):
                conversation = self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)
            elif isinstance(self.prompt_template, StringTemplate):
                conversation = [{'role': 'system', 'content': self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)}]
            else:
                raise ValueError(f'`prompt_template` must be a StringTemplate or ChatTemplate instance, but got {type(self.prompt_template)}')
        else:
            conversation = [{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': self.prepare_action_prompt(inputs=inputs, system_prompt=sys_msg)}]
        prompt_params_values = {k: inputs.get(k, '') for k in input_attributes.keys()}
        while True:
            if time_out > self.max_tool_try:
                current_prompt = self.prepare_action_prompt(inputs=prompt_params_values or {})
                content_to_extract = final_llm_response if final_llm_response is not None else '{content}'.format(content=conversation)
                if return_prompt:
                    return (await self._async_extract_output(content_to_extract, llm=llm), current_prompt)
                return await self._async_extract_output(content_to_extract, llm=llm)
            time_out += 1
            llm_response = await llm.async_generate(messages=conversation)
            conversation.append({'role': 'assistant', 'content': llm_response.content})
            final_llm_response = llm_response
            tool_call_args = self._extract_tool_calls(llm_response.content)
            if not tool_call_args:
                break
            logger.info('Extracted tool call args:')
            logger.info(json.dumps(tool_call_args, indent=4))
            results = self._calling_tools(tool_call_args)
            logger.info('Tool call results:')
            try:
                logger.info(json.dumps(results, indent=4))
            except Exception:
                logger.info(str(results))
            conversation.append({'role': 'assistant', 'content': TOOL_CALLING_HISTORY_PROMPT.format(iteration_number=time_out, tool_call_args=f'{tool_call_args}', results=f'{results}')})
        current_prompt = self.prepare_action_prompt(inputs=prompt_params_values or {})
        content_to_extract = final_llm_response if final_llm_response is not None else '{content}'.format(content=conversation)
        if return_prompt:
            return (await self._async_extract_output(content_to_extract, llm=llm), current_prompt)
        return await self._async_extract_output(content_to_extract, llm=llm)

def _extract_tool_calls(self, llm_output: str, llm: Optional[BaseLLM]=None) -> List[dict]:
    pattern = '<ToolCalling>\\s*(.*?)\\s*</ToolCalling>'
    matches = re.findall(pattern, llm_output, re.DOTALL)
    if not matches:
        return []
    parsed_tool_calls = []
    for match_content in matches:
        try:
            json_content = match_content.strip()
            json_list = parse_json_from_text(json_content)
            if not json_list:
                logger.warning('No valid JSON found in ToolCalling block')
                continue
            parsed_tool_call = json.loads(json_list[0])
            if isinstance(parsed_tool_call, dict):
                parsed_tool_calls.append(parsed_tool_call)
            elif isinstance(parsed_tool_call, list):
                parsed_tool_calls.extend(parsed_tool_call)
            else:
                logger.warning(f'Invalid tool call format: {parsed_tool_call}')
                continue
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f'Failed to parse tool calls from LLM output: {e}')
            if llm is not None:
                retry_prompt = TOOL_CALLING_RETRY_PROMPT.format(text=match_content)
                try:
                    fixed_output = llm.generate(prompt=retry_prompt).content.strip()
                    logger.info(f'Retrying tool call parse with fixed output:\n{fixed_output}')
                    fixed_list = parse_json_from_text(fixed_output)
                    if fixed_list:
                        parsed_tool_call = json.loads(fixed_list[0])
                        if isinstance(parsed_tool_call, dict):
                            parsed_tool_calls.append(parsed_tool_call)
                    elif isinstance(parsed_tool_call, list):
                        parsed_tool_calls.extend(parsed_tool_call)
                except Exception as retry_err:
                    logger.error(f'Retry failed: {retry_err}')
                    continue
        else:
            continue
    return parsed_tool_calls

def _call_single_tool(self, function_param: dict) -> tuple:
    try:
        function_name = function_param.get('function_name')
        function_args = function_param.get('function_args') or {}
        if not function_name:
            return (None, 'No function name provided')
        callable_fn = self.tools_caller.get(function_name)
        if not callable(callable_fn):
            return (None, f"Function '{function_name}' not found or not callable")
        print('_____________________ Start Function Calling _____________________')
        print(f'Executing function calling: {function_name} with parameters: {function_args}')
        result = callable_fn(**function_args)
        return (result, None)
    except Exception as e:
        logger.error(f'Error executing tool {function_name}: {e}')
        return (None, f'Error executing tool {function_name}: {str(e)}')

def _calling_tools(self, tool_call_args: List[dict]) -> dict:
    errors = []
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_tool = {executor.submit(self._call_single_tool, param): param for param in tool_call_args}
        for future in concurrent.futures.as_completed(future_to_tool):
            result, error = future.result()
            if error:
                errors.append(error)
            if result is not None:
                results.append(result)
    return {'result': results, 'error': errors}

class ContextExtraction(Action):
    """Action for extracting structured inputs from context.
    
    This action analyzes a conversation context to extract relevant information
    that can be used as inputs for other actions. It uses the LLM to interpret
    unstructured contextual information and format it according to the target
    action's input requirements.
    """

    def __init__(self, **kwargs):
        name = kwargs.pop('name') if 'name' in kwargs else CONTEXT_EXTRACTION['name']
        description = kwargs.pop('description') if 'description' in kwargs else CONTEXT_EXTRACTION['description']
        super().__init__(name=name, description=description, **kwargs)

    def get_context_from_messages(self, messages: List[Message]) -> str:
        str_context = '\n\n'.join([str(msg) for msg in messages])
        return str_context

    def execute(self, llm: Optional[BaseLLM]=None, action: Action=None, context: List[Message]=None, **kwargs) -> Union[dict, None]:
        """Extract structured inputs for an action from conversation context.
        
        This method uses the LLM to analyze the conversation context and extract
        information that matches the input requirements of the target action.
        
        Args:
            llm: The language model to use for extraction.
            action: The target action whose input requirements (`inputs_format`) define what to extract.
            context: List of messages providing the conversation context.
            **kwargs: Additional keyword arguments.
            
        Returns:
            A dictionary containing the extracted inputs for the target action,
            or None if extraction is not possible (e.g., if the action doesn't
            require inputs or if context is missing).
        """
        if action is None or context is None:
            return None
        action_inputs_cls: Type[ActionInput] = action.inputs_format
        if action_inputs_cls is None:
            return None
        action_inputs_desc = action_inputs_cls.get_input_specification()
        str_context = self.get_context_from_messages(messages=context)
        if not action_inputs_desc or not str_context:
            return None
        prompt = CONTEXT_EXTRACTION['prompt'].format(context=str_context, action_name=action.name, action_description=action.description, action_inputs=action_inputs_desc)
        action_inputs = llm.generate(prompt=prompt, system_message=CONTEXT_EXTRACTION['system_prompt'], parser=action_inputs_cls)
        action_inputs_data = action_inputs.get_structured_data()
        return action_inputs_data

def get_context_from_messages(self, messages: List[Message]) -> str:
    str_context = '\n\n'.join([str(msg) for msg in messages])
    return str_context

class StockDataFetcher:
    """股票数据抓取器 - 核心功能类"""

    def __init__(self, stock_code, auto_create_output_dir=True):
        """
        初始化数据抓取器
        
        Args:
            stock_code (str): 股票代码（如：300750、000001等）
            auto_create_output_dir (bool): 是否自动创建输出目录，默认True
        """
        self.stock_code = stock_code
        self.symbol_sz = f'sz{stock_code}' if stock_code.startswith('0') or stock_code.startswith('3') else f'sh{stock_code}'
        if auto_create_output_dir:
            self.output_dir = Path(f'output_{stock_code}')
        else:
            self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.stock_name = self._get_stock_name()

    def _get_stock_name(self):
        """获取股票名称"""
        try:
            stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
            if not stock_info.empty:
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    return name_row['value'].iloc[0]
            return f'股票{self.stock_code}'
        except:
            return f'股票{self.stock_code}'

    def get_timestamp(self):
        """获取当前日期用于文件命名"""
        return datetime.datetime.now().strftime('%Y%m%d')

    def save_data(self, data, filename_prefix, description=''):
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据（pandas DataFrame）
            filename_prefix (str): 文件名前缀
            description (str): 数据描述
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            timestamp = self.get_timestamp()
            filename = f'{filename_prefix}_{timestamp}_{self.stock_code}.csv'
            filepath = self.output_dir / filename
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath} (共{len(data)}条记录)')
            else:
                df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath}')
            return str(filepath)
        except Exception as e:
            self.logger.error(f'❌ 保存{description}失败: {str(e)}')
            return None

    def fetch_stock_daily(self, days=30):
        """
        抓取股票日线数据
        
        Args:
            days (int): 抓取最近多少天的数据，默认30天
            
        Returns:
            pandas.DataFrame: 股票日线数据
        """
        try:
            self.logger.info(f'📈 开始抓取{self.stock_code}日线数据...')
            stock_df = ak.stock_zh_a_daily(symbol=self.symbol_sz).reset_index()
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
            recent_data = stock_df[stock_df['date'] >= days_ago]
            self.save_data(recent_data, 'stock_daily_catl', f'{self.stock_code}日线数据')
            return recent_data
        except Exception as e:
            self.logger.error(f'❌ 抓取股票日线数据失败: {str(e)}')
            return None

    def fetch_china_cpi(self):
        """
        抓取中国CPI数据 (限制为过去2年)
        
        Returns:
            pandas.DataFrame: 中国CPI数据
        """
        try:
            self.logger.info('📊 开始抓取中国CPI数据...')
            cpi_df = ak.macro_china_cpi()
            if not cpi_df.empty:
                if '月份' in cpi_df.columns:

                    def convert_chinese_date(date_str):
                        try:
                            if '年' in date_str and '月' in date_str:
                                year = date_str.split('年')[0]
                                month = date_str.split('年')[1].split('月')[0]
                                return f'{year}-{month.zfill(2)}-01'
                            else:
                                return date_str
                        except:
                            return None
                    cpi_df['月份'] = cpi_df['月份'].apply(convert_chinese_date)
                    cpi_df['月份'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
                    cpi_df = cpi_df.dropna(subset=['月份'])
                    if not cpi_df.empty:
                        two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
                        cpi_df = cpi_df[cpi_df['月份'] >= two_years_ago]
                        self.logger.info(f'✅ CPI数据已限制为过去2年: {len(cpi_df)} 条记录')
            return cpi_df
        except Exception as e:
            self.logger.error(f'❌ 抓取CPI数据失败: {str(e)}')
            return None

    def fetch_china_gdp(self):
        """
        抓取中国GDP数据
        
        Returns:
            pandas.DataFrame: 中国GDP数据
        """
        try:
            self.logger.info('📊 开始抓取中国GDP数据...')
            gdp_df = ak.macro_china_gdp_yearly()
            return gdp_df
        except Exception as e:
            self.logger.error(f'❌ 抓取GDP数据失败: {str(e)}')
            return None

    def fetch_industry_fund_flow(self):
        """
        抓取行业资金流数据
        
        Returns:
            pandas.DataFrame: 行业资金流数据
        """
        try:
            self.logger.info('💰 开始抓取行业资金流数据...')
            industry_fund_df = ak.stock_fund_flow_industry()
            return industry_fund_df
        except Exception as e:
            self.logger.error(f'❌ 抓取行业资金流数据失败: {str(e)}')
            return None

    def fetch_stock_news(self):
        """
        抓取个股新闻数据
        
        Returns:
            pandas.DataFrame: 个股新闻数据
        """
        try:
            self.logger.info(f'📰 开始抓取{self.stock_name}({self.stock_code})新闻数据...')
            news_df = ak.stock_news_em(symbol=self.stock_code)
            return news_df
        except Exception as e:
            self.logger.error(f'❌ 抓取新闻数据失败: {str(e)}')
            return None

    def fetch_market_summary(self):
        """
        抓取上交所市场概况
        
        Returns:
            pandas.DataFrame: 市场概况数据
        """
        try:
            self.logger.info('🏛️ 开始抓取上交所市场概况...')
            sse_summary = ak.stock_sse_summary()
            return sse_summary
        except Exception as e:
            self.logger.error(f'❌ 抓取市场概况失败: {str(e)}')
            return None

    def fetch_market_indices(self):
        """
        抓取重要指数行情
        
        Returns:
            pandas.DataFrame: 重要指数数据
        """
        try:
            self.logger.info('📊 开始抓取重要指数行情...')
            market_indices = ak.stock_zh_index_spot_em(symbol='沪深重要指数')
            return market_indices
        except Exception as e:
            self.logger.error(f'❌ 抓取市场指数失败: {str(e)}')
            return None

    def fetch_option_volatility(self):
        """
        抓取50ETF期权波动率指数 (限制为过去1个月)
        
        Returns:
            pandas.DataFrame: 期权波动率数据
        """
        try:
            self.logger.info('📈 开始抓取50ETF波动率指数...')
            vol50 = ak.index_option_50etf_qvix()
            if not vol50.empty:
                if 'date' in vol50.columns:
                    vol50['date'] = pd.to_datetime(vol50['date'])
                    one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    vol50 = vol50[vol50['date'] >= one_month_ago]
                    self.logger.info(f'✅ 期权波动率数据已限制为过去1个月: {len(vol50)} 条记录')
            return vol50
        except Exception as e:
            self.logger.error(f'❌ 抓取期权波动率数据失败: {str(e)}')
            return None

    def fetch_institution_recommendation(self):
        """
        抓取机构评级数据 (限制为过去半年)
        
        Returns:
            pandas.DataFrame: 机构评级数据
        """
        try:
            self.logger.info(f'🏦 开始抓取{self.stock_name}({self.stock_code})机构评级...')
            inst_rec = ak.stock_institute_recommend_detail(symbol=self.stock_code)
            if not inst_rec.empty:
                date_columns = ['评级日期', 'date', '日期']
                date_col = None
                for col in date_columns:
                    if col in inst_rec.columns:
                        date_col = col
                        break
                if date_col:
                    inst_rec[date_col] = pd.to_datetime(inst_rec[date_col])
                    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                    inst_rec = inst_rec[inst_rec[date_col] >= six_months_ago]
                    self.logger.info(f'✅ 机构评级数据已限制为过去半年: {len(inst_rec)} 条记录')
            return inst_rec
        except Exception as e:
            self.logger.error(f'❌ 抓取机构评级数据失败: {str(e)}')
            return None

    def fetch_all_data(self):
        """
        抓取所有类型的数据
        
        Returns:
            dict: 包含所有数据的字典
        """
        self.logger.info('🚀 开始抓取全部数据...')
        results = {}
        tasks = [('stock_daily', lambda: self.fetch_stock_daily(), '股票日线数据'), ('china_cpi', lambda: self.fetch_china_cpi(), '中国CPI数据'), ('china_gdp', lambda: self.fetch_china_gdp(), '中国GDP数据'), ('industry_fund_flow', lambda: self.fetch_industry_fund_flow(), '行业资金流数据'), ('stock_news', lambda: self.fetch_stock_news(), '个股新闻数据'), ('market_summary', lambda: self.fetch_market_summary(), '市场整体概况'), ('market_indices', lambda: self.fetch_market_indices(), '重要指数行情'), ('option_volatility', lambda: self.fetch_option_volatility(), '期权波动率指数'), ('institution_recommendation', lambda: self.fetch_institution_recommendation(), '机构评级数据')]
        for task_name, task_func, description in tasks:
            try:
                self.logger.info(f'\n--- 开始执行: {description} ---')
                result = task_func()
                results[task_name] = result
                if result is not None:
                    filename_mapping = {'stock_daily': 'stock_daily_catl', 'china_cpi': 'china_cpi', 'china_gdp': 'china_gdp_yearly', 'industry_fund_flow': 'industry_fund_flow', 'stock_news': 'stock_news_catl', 'market_summary': 'market_summary_sse', 'market_indices': 'market_indices', 'option_volatility': 'option_volatility_50etf', 'institution_recommendation': 'institution_recommendation_catl'}
                    self.save_data(result, filename_mapping[task_name], description)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f'执行{description}时发生错误: {str(e)}')
                results[task_name] = None
        self.logger.info('🎉 全部数据抓取完成！')
        return results

    def create_data_documentation(self):
        """创建数据文件说明文档"""
        try:
            timestamp = self.get_timestamp()
            doc_content = f'# {self.stock_name}({self.stock_code})数据文件说明\n\n## 📋 文件命名规则\n\n所有数据文件按以下格式命名：\n```\n数据类型_日期_股票代码.csv\n```\n\n例如：`china_cpi_{timestamp}_{self.stock_code}.csv` 表示{timestamp[:4]}年{timestamp[4:6]}月{timestamp[6:8]}日抓取的中国CPI数据，与{self.stock_name}({self.stock_code})相关。\n\n---\n\n## 📊 数据文件详细说明\n\n### 1. 股票日线数据\n**文件名**: `stock_daily_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_a_daily()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘价（元）\n- **high** - 最高价（元）\n- **low** - 最低价（元）\n- **close** - 收盘价（元）\n- **volume** - 成交量（股）\n- **amount** - 成交额（元）\n- **outstanding_share** - 流通股数（股）\n- **turnover** - 换手率\n\n**用途**: 分析{self.stock_name}股价走势、成交情况，进行技术分析\n\n---\n\n### 2. 中国CPI数据\n**文件名**: `china_cpi_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_cpi()\n\n**中文指标说明**:\n- **月份** - 统计月份\n- **全国-当月** - 全国当月CPI指数\n- **全国-同比增长** - 全国CPI同比增长率(%)\n- **全国-环比增长** - 全国CPI环比增长率(%)\n- **全国-累计** - 全国累计CPI指数\n- **城市-当月** - 城市当月CPI指数\n- **城市-同比增长** - 城市CPI同比增长率(%)\n- **城市-环比增长** - 城市CPI环比增长率(%)\n- **城市-累计** - 城市累计CPI指数\n- **农村-当月** - 农村当月CPI指数\n- **农村-同比增长** - 农村CPI同比增长率(%)\n- **农村-环比增长** - 农村CPI环比增长率(%)\n- **农村-累计** - 农村累计CPI指数\n\n**用途**: 反映通胀水平，判断宏观经济环境对{self.stock_name}所在行业的影响\n\n---\n\n### 3. 中国GDP数据\n**文件名**: `china_gdp_yearly_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_gdp_yearly()\n\n**中文指标说明**:\n- **商品** - 数据类型（中国GDP年率报告）\n- **日期** - 发布日期\n- **今值** - 当期GDP增长率(%)\n- **预测值** - 市场预测GDP增长率(%)\n- **前值** - 前期GDP增长率(%)\n\n**用途**: 评估国家经济增长情况，判断宏观经济对{self.stock_name}所在行业需求的影响\n\n---\n\n### 4. 行业资金流数据\n**文件名**: `industry_fund_flow_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_fund_flow_industry()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **行业** - 行业名称\n- **行业指数** - 行业指数代码\n- **行业-涨跌幅** - 行业当日涨跌幅(%)\n- **流入资金** - 资金流入金额（万元）\n- **流出资金** - 资金流出金额（万元）\n- **净额** - 资金净流入金额（万元）\n- **公司家数** - 该行业公司数量\n- **领涨股** - 行业内领涨股票\n- **领涨股-涨跌幅** - 领涨股涨跌幅(%)\n- **当前价** - 领涨股当前价格（元）\n\n**用途**: 分析各行业资金流向，判断{self.stock_name}所在行业的资金关注度\n\n---\n\n### 5. 个股新闻数据\n**文件名**: `stock_news_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_news_em()\n\n**中文指标说明**:\n- **关键词** - 搜索关键词（股票代码）\n- **新闻标题** - 新闻标题\n- **新闻内容** - 新闻摘要/内容\n- **发布时间** - 新闻发布时间\n- **新闻来源** - 新闻来源媒体\n- **新闻链接** - 原文链接地址\n\n**用途**: 获取{self.stock_name}相关新闻资讯，进行舆情分析和基本面研究\n\n---\n\n### 6. 上交所市场概况\n**文件名**: `market_summary_sse_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_sse_summary()\n\n**中文指标说明**:\n- **项目** - 统计项目名称\n- **股票** - 股票相关数据\n- **主板** - 主板市场数据\n- **科创板** - 科创板市场数据\n\n**具体项目包括**:\n- **流通股本** - 流通股总数（亿股）\n- **总市值** - 总市值（亿元）\n- **平均市盈率** - 平均市盈率（倍）\n- **上市公司** - 上市公司数量（家）\n- **上市股票** - 上市股票数量（只）\n- **流通市值** - 流通市值（亿元）\n- **总股本** - 总股本（亿股）\n\n**用途**: 了解整体市场状况，判断市场环境对{self.stock_name}的影响\n\n---\n\n### 7. 重要指数行情\n**文件名**: `market_indices_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_index_spot_em()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **代码** - 指数代码\n- **名称** - 指数名称\n- **最新价** - 最新指数点位\n- **涨跌幅** - 当日涨跌幅(%)\n- **涨跌额** - 当日涨跌点数\n- **成交量** - 成交量（手）\n- **成交额** - 成交金额（万元）\n- **振幅** - 当日振幅(%)\n- **最高** - 当日最高点位\n- **最低** - 当日最低点位\n- **今开** - 今日开盘点位\n- **昨收** - 昨日收盘点位\n- **量比** - 量比\n\n**包含指数**:\n- 上证指数、深证成指、创业板指、科创综指、北证50等\n\n**用途**: 跟踪重要市场指数走势，判断整体市场方向\n\n---\n\n### 8. 50ETF期权波动率指数\n**文件名**: `option_volatility_50etf_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.index_option_50etf_qvix()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘波动率\n- **high** - 最高波动率\n- **low** - 最低波动率\n- **close** - 收盘波动率\n\n**用途**: 反映市场恐慌情绪和波动性预期，是重要的市场情绪指标\n\n---\n\n### 9. 机构评级数据\n**文件名**: `institution_recommendation_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_institute_recommend_detail()\n\n**中文指标说明**:\n- **股票代码** - 股票代码\n- **股票名称** - 股票名称\n- **目标价** - 机构给出的目标价格（元）\n- **最新评级** - 机构最新评级（买入/增持/中性/减持/卖出）\n- **评级机构** - 研究机构名称\n- **分析师** - 分析师姓名\n- **行业** - 所属行业\n- **评级日期** - 评级发布日期\n\n**评级含义**:\n- **买入** - 强烈推荐买入\n- **增持** - 推荐增加持仓\n- **中性** - 维持现有持仓\n- **减持** - 建议减少持仓\n- **卖出** - 建议卖出\n\n**用途**: 了解专业机构对{self.stock_name}的投资建议和价格预期\n\n---\n\n### 10. 数据收集报告\n**文件名**: `collection_report_{timestamp}_{self.stock_code}.csv`\n\n**自动生成的收集统计报告**\n\n**中文指标说明**:\n- **数据类型** - 数据收集任务名称\n- **收集状态** - 收集是否成功（成功/失败）\n- **记录数量** - 成功收集的数据条数\n- **时间戳** - 数据收集完成时间\n\n**用途**: 监控数据收集任务的执行情况，确保数据完整性\n\n---\n\n## 🔍 数据使用建议\n\n### 综合分析框架\n\n1. **宏观经济层面**\n   - 使用CPI、GDP数据判断宏观经济环境\n   - 分析对{self.stock_name}所在行业的影响\n\n2. **市场情绪层面**\n   - 使用期权波动率指数判断市场恐慌程度\n   - 使用重要指数走势判断市场整体方向\n\n3. **行业资金层面**\n   - 使用行业资金流数据判断资金偏好\n   - 关注{self.stock_name}所在行业的资金流向\n\n4. **个股基本面**\n   - 使用机构评级了解专业判断\n   - 使用新闻数据进行舆情分析\n\n5. **技术面分析**\n   - 使用股票日线数据进行技术分析\n   - 结合成交量判断趋势强度\n\n### 数据更新频率\n\n- **日更新**: 股票日线、新闻、指数行情、期权波动率\n- **月更新**: CPI数据\n- **季更新**: GDP数据\n- **实时更新**: 行业资金流、机构评级\n\n---\n\n## ⚠️ 使用注意事项\n\n1. **数据时效性**: 部分数据存在发布延迟，请注意数据的时效性\n2. **数据完整性**: 如遇到数据源问题，某些文件可能缺失，请查看收集报告\n3. **投资风险**: 数据仅供参考，不构成投资建议，投资需谨慎\n4. **版权声明**: 数据来源于公开渠道，请遵守相关使用条款\n\n---\n\n## 📞 技术支持\n\n如有数据解读疑问或技术问题，请参考：\n- akshare官方文档: https://akshare.readthedocs.io/\n- 数据抓取函数库: 本项目中的股票数据抓取函数\n\n**生成时间**: {datetime.datetime.now().strftime('%Y年%m月%d日')}\n**数据版本**: v2.0  \n**适用股票**: {self.stock_name}({self.stock_code})\n'
            doc_filepath = self.output_dir / '数据文件说明.md'
            with open(doc_filepath, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            self.logger.info(f'✅ 数据说明文档已生成: {doc_filepath}')
            return str(doc_filepath)
        except Exception as e:
            self.logger.error(f'❌ 生成数据说明文档失败: {str(e)}')
            return None

def fetch_china_gdp(self):
    """
        抓取中国GDP数据
        
        Returns:
            pandas.DataFrame: 中国GDP数据
        """
    try:
        self.logger.info('📊 开始抓取中国GDP数据...')
        gdp_df = ak.macro_china_gdp_yearly()
        return gdp_df
    except Exception as e:
        self.logger.error(f'❌ 抓取GDP数据失败: {str(e)}')
        return None

def fetch_industry_fund_flow(self):
    """
        抓取行业资金流数据
        
        Returns:
            pandas.DataFrame: 行业资金流数据
        """
    try:
        self.logger.info('💰 开始抓取行业资金流数据...')
        industry_fund_df = ak.stock_fund_flow_industry()
        return industry_fund_df
    except Exception as e:
        self.logger.error(f'❌ 抓取行业资金流数据失败: {str(e)}')
        return None

def fetch_stock_news(self):
    """
        抓取个股新闻数据
        
        Returns:
            pandas.DataFrame: 个股新闻数据
        """
    try:
        self.logger.info(f'📰 开始抓取{self.stock_name}({self.stock_code})新闻数据...')
        news_df = ak.stock_news_em(symbol=self.stock_code)
        return news_df
    except Exception as e:
        self.logger.error(f'❌ 抓取新闻数据失败: {str(e)}')
        return None

def fetch_market_summary(self):
    """
        抓取上交所市场概况
        
        Returns:
            pandas.DataFrame: 市场概况数据
        """
    try:
        self.logger.info('🏛️ 开始抓取上交所市场概况...')
        sse_summary = ak.stock_sse_summary()
        return sse_summary
    except Exception as e:
        self.logger.error(f'❌ 抓取市场概况失败: {str(e)}')
        return None

def fetch_market_indices(self):
    """
        抓取重要指数行情
        
        Returns:
            pandas.DataFrame: 重要指数数据
        """
    try:
        self.logger.info('📊 开始抓取重要指数行情...')
        market_indices = ak.stock_zh_index_spot_em(symbol='沪深重要指数')
        return market_indices
    except Exception as e:
        self.logger.error(f'❌ 抓取市场指数失败: {str(e)}')
        return None

class HTMLGenerator:
    """Generates the HTML report with neomorphism styling and optimized layout."""

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.assets_dir = self.output_path.parent / 'assets'
        self.assets_dir.mkdir(exist_ok=True)

    def encode_image_to_base64(self, image_path: str) -> str:
        """将图片编码为base64字符串"""
        try:
            if not image_path or not os.path.exists(image_path):
                return ''
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f'⚠️ 无法读取图片 {image_path}: {e}')
            return ''

    def _get_latest_close_price(self, stock_code: str, timestamp: str) -> str:
        """从股票日线数据CSV文件中读取最新的收盘价"""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/stock_daily_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                print(f'⚠️ 股票日线数据文件不存在: {csv_path}')
                return 'N/A'
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) < 2:
                print(f'⚠️ 股票日线数据文件为空或格式错误: {csv_path}')
                return 'N/A'
            last_line = lines[-1].strip()
            if not last_line:
                last_line = lines[-2].strip()
            fields = last_line.split(',')
            if len(fields) >= 6:
                close_price = fields[5]
                return close_price
            else:
                print(f'⚠️ 股票日线数据格式错误: {last_line}')
                return 'N/A'
        except Exception as e:
            print(f'⚠️ 读取股票收盘价失败: {e}')
            return 'N/A'

    def generate_report(self, md_file_path: str, technical_chart_path: str, price_volume_chart_path: str) -> str:
        """Generate the complete HTML report with base64 encoded images."""
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        parser = MarkdownParser(md_content)
        metadata = parser.get_metadata()
        technical_chart_base64 = self.encode_image_to_base64(technical_chart_path)
        price_volume_chart_base64 = self.encode_image_to_base64(price_volume_chart_path)
        html_content = self._generate_html_structure(parser, metadata, technical_chart_base64, price_volume_chart_base64)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return str(self.output_path)

    def _read_news_from_csv(self, stock_code: str, timestamp: str) -> List[Dict[str, str]]:
        """Read news data from CSV file and return the latest 10 entries."""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/stock_news_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                return []
            news_data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    news_data.append({'新闻标题': row.get('新闻标题', ''), '来源': row.get('文章来源', ''), '发布时间': row.get('发布时间', ''), '影响程度': '中', '解读': row.get('新闻内容', '')[:100] + '...' if len(row.get('新闻内容', '')) > 100 else row.get('新闻内容', ''), '链接': row.get('新闻链接', '')})
            news_data.sort(key=lambda x: x['发布时间'], reverse=True)
            return news_data[:10]
        except Exception as e:
            print(f'Error reading news CSV: {e}')
            return []

    def _read_ratings_from_csv(self, stock_code: str, timestamp: str) -> List[Dict[str, str]]:
        """Read institution rating data from CSV file and return the latest 10 entries."""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/institution_recommendation_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                return []
            ratings_data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ratings_data.append({'机构名称': row.get('评级机构', ''), '评级': row.get('最新评级', ''), '目标价': row.get('目标价', '-'), '评级日期': row.get('评级日期', ''), '分析师': row.get('分析师', '不详')})
            ratings_data.sort(key=lambda x: x['评级日期'], reverse=True)
            return ratings_data[:10]
        except Exception as e:
            print(f'Error reading ratings CSV: {e}')
            return []

    def _generate_fundamentals_section_from_csv(self, metadata: Dict[str, str]) -> str:
        """Generate fundamentals section content directly from CSV files."""
        if not metadata:
            return ''
        stock_code = metadata.get('股票代码', '300750')
        timestamp = metadata.get('日期', '')
        if not timestamp:
            timestamp = datetime.now().strftime('%Y%m%d')
        else:
            import re
            date_match = re.search('(\\d{4})年(\\d{2})月(\\d{2})日', timestamp)
            if date_match:
                year, month, day = date_match.groups()
                timestamp = f'{year}{month}{day}'
            else:
                timestamp = datetime.now().strftime('%Y%m%d')
        news_data = self._read_news_from_csv(stock_code, timestamp)
        ratings_data = self._read_ratings_from_csv(stock_code, timestamp)
        print(f'Debug: Stock code: {stock_code}, Timestamp: {timestamp}')
        print(f'Debug: Found {len(news_data)} news items')
        print(f'Debug: Found {len(ratings_data)} rating items')
        news_html = ''
        if news_data:
            news_headers = ['新闻标题', '来源', '发布时间', '影响程度', '解读', '链接']
            news_rows = []
            for news in news_data:
                news_rows.append([news['新闻标题'], news['来源'], news['发布时间'], news['影响程度'], news['解读'], news['链接']])
            news_table_data = {'headers': news_headers, 'rows': news_rows}
            news_html = f'\n            <div class="subsection">\n                <h3 class="subsection-title"><i class="fas fa-caret-right"></i> 4.1 最新新闻动态</h3>\n                <div class="scrollable-table-container">\n                    {self._generate_table(news_table_data)}\n                </div>\n            </div>\n            '
        ratings_html = ''
        if ratings_data:
            ratings_headers = ['机构名称', '评级', '目标价', '评级日期', '分析师']
            ratings_rows = []
            for rating in ratings_data:
                ratings_rows.append([rating['机构名称'], rating['评级'], rating['目标价'], rating['评级日期'], rating['分析师']])
            ratings_table_data = {'headers': ratings_headers, 'rows': ratings_rows}
            ratings_html = f'\n            <div class="subsection">\n                <h3 class="subsection-title"><i class="fas fa-caret-right"></i> 4.2 机构评级汇总</h3>\n                <div class="scrollable-table-container">\n                    {self._generate_table(ratings_table_data)}\n                </div>\n            </div>\n            '
        return news_html + ratings_html

    def _generate_html_structure(self, parser: MarkdownParser, metadata: Dict[str, str], technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the complete HTML structure with neomorphism design."""
        header_html = self._generate_neomorphism_header(metadata, parser.sections)
        charts_html = self._generate_charts_section(technical_chart_base64, price_volume_chart_base64)
        dashboard_html = self._generate_dashboard_overview(parser.sections, metadata)
        sections_html = self._generate_detailed_sections(parser.sections, metadata)
        footer_html = self._generate_footer(metadata)
        return f"""\n        <!DOCTYPE html>\n        <html lang="zh-CN">\n        <head>\n            <meta charset="UTF-8">\n            <meta name="viewport" content="width=device-width, initial-scale=1.0">\n            <title>{metadata.get('股票名称', 'Unknown')} ({metadata.get('股票代码', 'Unknown')}) - 投资分析报告</title>\n            <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">\n            <style>\n                {self._get_neomorphism_css()}\n            </style>\n        </head>\n        <body>\n            <div class="container">\n                {header_html}\n                {dashboard_html}\n                {charts_html}\n                {sections_html}\n                {footer_html}\n            </div>\n            \n            <script>\n                {self._get_javascript()}\n            </script>\n        </body>\n        </html>\n        """

    def _generate_neomorphism_header(self, metadata: Dict[str, str], sections: Dict[str, Any]) -> str:
        """Generate the neomorphism-style header exactly like the reference image."""
        stock_name = metadata.get('股票名称', 'Unknown')
        stock_code = metadata.get('股票代码', 'Unknown')
        now = datetime.now()
        date = now.strftime('%Y年%m月%d日')
        time = now.strftime('%H:%M:%S')
        current_price = 'N/A'
        if stock_code != 'Unknown':
            date_match = re.search('(\\d{4})年(\\d{2})月(\\d{2})日', date)
            if date_match:
                timestamp = f'{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}'
                current_price = self._get_latest_close_price(stock_code, timestamp)
        if current_price == 'N/A' and '当前持仓' in metadata:
            holding_info = metadata['当前持仓']
            if '平均成本' in holding_info:
                price_match = re.search('平均成本\\s*(\\d+(?:\\.\\d+)?)', holding_info)
                if price_match:
                    current_price = price_match.group(1)
        return f'\n            <div class="main-header">\n                <h1 class="main-title">{stock_name}({stock_code})</h1>\n                <p class="main-subtitle">新拟态风格投资分析报告</p>\n                \n                <div class="header-info-cards">\n                    <div class="info-card">\n                        <div class="info-icon">📅</div>\n                        <span>{date}</span>\n                    </div>\n                    <div class="info-card">\n                        <div class="info-icon">🕐</div>\n                        <span>{time}</span>\n                    </div>\n                    <div class="info-card">\n                        <div class="info-icon">📊</div>\n                        <span>当前价格: ¥{current_price}</span>\n                    </div>\n                </div>\n            </div>\n        '

    def _generate_dashboard_overview(self, sections: Dict[str, Any], metadata: Dict[str, str]) -> str:
        """Generate a dashboard overview with key metrics extracted from actual report data."""
        investment_advice = '持有'
        investment_reason = '基于技术分析和基本面评估的专业建议'
        risk_level = '中等'
        confidence_level = '中等'
        target_price = '285'
        stop_price = '270'
        expected_return = '2%'
        strategy_period = '短期持仓'
        trading_section = sections.get('一、交易操作决策', {})
        if trading_section:
            subsections = trading_section.get('subsections', {})
            core_decision = subsections.get('1.1 核心决策', {})
            if core_decision:
                tables = core_decision.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    if rows and len(rows) > 0:
                        row = rows[0]
                        if len(row) >= 4:
                            investment_advice = row[1] if row[1] else investment_advice
                            investment_reason = row[2] if row[2] else investment_reason
                            risk_level = row[3] if row[3] else risk_level
            price_targets = subsections.get('1.3 价格目标', {})
            if price_targets:
                tables = price_targets.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    if rows and len(rows) > 0:
                        row = rows[0]
                        if len(row) >= 4:
                            target_price = str(row[1]).replace('RMB', '').replace(' ', '') if row[1] else target_price
                            stop_price = str(row[2]).replace('RMB', '').replace(' ', '') if row[2] else stop_price
                            expected_return = str(row[3]) if row[3] else expected_return
        risk_section = sections.get('五、风险评估', {})
        if risk_section:
            subsections = risk_section.get('subsections', {})
            risk_factors = subsections.get('5.1 风险因素', {})
            if risk_factors:
                tables = risk_factors.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    risk_levels = []
                    for row in rows:
                        if len(row) >= 2 and row[1]:
                            risk_levels.append(row[1])
                    if risk_levels:
                        high_count = risk_levels.count('高')
                        mid_count = risk_levels.count('中')
                        low_count = risk_levels.count('低')
                        if high_count > mid_count and high_count > low_count:
                            risk_level = '高'
                        elif mid_count >= high_count and mid_count >= low_count:
                            risk_level = '中等'
                        else:
                            risk_level = '低'
        advice_section = sections.get('七、投资建议', {})
        if advice_section:
            subsections = advice_section.get('subsections', {})
            short_term = subsections.get('7.1 短期操作建议', {})
            if short_term:
                text_content = short_term.get('text_content', [])
                if text_content:
                    content_text = ' '.join(text_content)
                    return_match = re.search('预期收益[：:]\\s*([0-9.]+%)', content_text)
                    if return_match:
                        expected_return = return_match.group(1)
            long_term = subsections.get('7.2 中长期策略', {})
            if long_term:
                text_content = long_term.get('text_content', [])
                if text_content:
                    content_text = ' '.join(text_content)
                    period_match = re.search('持有周期[：:]\\s*([^。\\n]+)', content_text)
                    if period_match:
                        period = period_match.group(1).strip()
                        if '月' in period or '年' in period:
                            strategy_period = '中长期持仓'
                        else:
                            strategy_period = '短期持仓'
        if investment_advice in ['买入', '强烈买入']:
            confidence_level = '高'
        elif investment_advice in ['卖出', '强烈卖出']:
            confidence_level = '低'
        elif investment_advice in ['部分卖出', '部分买入']:
            confidence_level = '中等'
        else:
            confidence_level = '中等'
        target_price = re.sub('[^0-9.]', '', str(target_price))
        stop_price = re.sub('[^0-9.]', '', str(stop_price))
        return f'\n            <div class="analysis-summary">\n                <div class="summary-card">\n                    <div class="card-icon green">\n                        <i class="icon">👍</i>\n                    </div>\n                    <h3>投资建议</h3>\n                    <div class="main-value">{investment_advice}</div>\n                    <div class="sub-text">{investment_reason[:50]}{('...' if len(investment_reason) > 50 else '')}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon blue">\n                        <i class="icon">🎯</i>\n                    </div>\n                    <h3>价格目标</h3>\n                    <div class="price-targets">\n                        <div class="price-item">\n                            <span class="label">目标价</span>\n                            <span class="value">¥{target_price}</span>\n                        </div>\n                        <div class="price-item">\n                            <span class="label">止损价</span>\n                            <span class="value">¥{stop_price}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">预期收益: {expected_return}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon orange">\n                        <i class="icon">🛡️</i>\n                    </div>\n                    <h3>风险评估</h3>\n                    <div class="risk-levels">\n                        <div class="risk-item">\n                            <span class="label">风险级别</span>\n                            <span class="value">{risk_level}</span>\n                        </div>\n                        <div class="risk-item">\n                            <span class="label">信心级别</span>\n                            <span class="value">{confidence_level}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">{strategy_period}</div>\n                </div>\n            </div>\n        '

    def _get_neomorphism_css(self) -> str:
        """Get the enhanced neomorphism CSS styles for the report."""
        return "\n        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');\n        \n        * {\n            margin: 0;\n            padding: 0;\n            box-sizing: border-box;\n        }\n        \n        body {\n            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;\n            line-height: 1.6;\n            color: #2d3748;\n            background: #e0e5ec;\n            min-height: 100vh;\n        }\n        \n        .container {\n            max-width: 1200px;\n            margin: 0 auto;\n            padding: 40px 20px;\n        }\n        \n        /* Main Header Styles - Like Reference Image */\n        .main-header {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 60px 40px;\n            margin-bottom: 30px;\n            box-shadow: 20px 20px 60px #bebebe, -20px -20px 60px #ffffff;\n            text-align: center;\n        }\n        \n        .main-title {\n            font-size: 3rem;\n            font-weight: 800;\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            -webkit-background-clip: text;\n            -webkit-text-fill-color: transparent;\n            background-clip: text;\n            margin-bottom: 15px;\n        }\n        \n        .main-subtitle {\n            font-size: 1.2rem;\n            color: #64748b;\n            font-weight: 500;\n            margin-bottom: 40px;\n        }\n        \n        .header-info-cards {\n            display: flex;\n            justify-content: center;\n            gap: 30px;\n            flex-wrap: wrap;\n        }\n        \n        .info-card {\n            display: flex;\n            align-items: center;\n            gap: 10px;\n            background: #e0e5ec;\n            padding: 15px 25px;\n            border-radius: 15px;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .info-card:hover {\n            transform: translateY(-2px);\n            box-shadow: 12px 12px 24px #bebebe, -12px -12px 24px #ffffff;\n        }\n        \n        .info-icon {\n            font-size: 1.2rem;\n        }\n        \n        .info-card span {\n            font-weight: 600;\n            color: #2d3748;\n            font-size: 0.9rem;\n        }\n        \n        /* Analysis Summary - Like Reference Image */\n        .analysis-summary {\n            display: grid;\n            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));\n            gap: 30px;\n            margin-bottom: 30px;\n        }\n        \n        .summary-card {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            box-shadow: 25px 25px 75px #bebebe, -25px -25px 75px #ffffff;\n            text-align: center;\n            transition: all 0.3s ease;\n        }\n        \n        .summary-card:hover {\n            transform: translateY(-5px);\n            box-shadow: 30px 30px 90px #bebebe, -30px -30px 90px #ffffff;\n        }\n        \n        .card-icon {\n            width: 80px;\n            height: 80px;\n            border-radius: 20px;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n            margin: 0 auto 20px auto;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n        }\n        \n        .card-icon.green {\n            background: linear-gradient(135deg, #10b981, #059669);\n        }\n        \n        .card-icon.blue {\n            background: linear-gradient(135deg, #3b82f6, #1d4ed8);\n        }\n        \n        .card-icon.orange {\n            background: linear-gradient(135deg, #f59e0b, #d97706);\n        }\n        \n        .card-icon .icon {\n            font-size: 2.5rem;\n        }\n        \n        .summary-card h3 {\n            font-size: 1.4rem;\n            font-weight: 700;\n            color: #2d3748;\n            margin-bottom: 20px;\n        }\n        \n        .main-value {\n            font-size: 2.5rem;\n            font-weight: 800;\n            color: #10b981;\n            margin-bottom: 15px;\n        }\n        \n        .sub-text {\n            font-size: 0.9rem;\n            color: #6b7280;\n            font-weight: 500;\n            line-height: 1.4;\n        }\n        \n        .price-targets, .risk-levels {\n            display: flex;\n            justify-content: space-around;\n            gap: 20px;\n            margin: 20px 0;\n        }\n        \n        .price-item, .risk-item {\n            background: #e0e5ec;\n            padding: 15px 20px;\n            border-radius: 15px;\n            box-shadow: inset 5px 5px 10px #bebebe, inset -5px -5px 10px #ffffff;\n            text-align: center;\n            flex: 1;\n        }\n        \n        .price-item .label, .risk-item .label {\n            font-size: 0.8rem;\n            color: #6b7280;\n            font-weight: 600;\n            text-transform: uppercase;\n            letter-spacing: 0.5px;\n            margin-bottom: 8px;\n            display: block;\n        }\n        \n        .price-item .value, .risk-item .value {\n            font-size: 1.5rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        /* Chart Section Styles - Neomorphism Frames */\n        .chart-section {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            margin-bottom: 30px;\n            box-shadow: 25px 25px 75px #bebebe, -25px -25px 75px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .chart-section:hover {\n            transform: translateY(-3px);\n            box-shadow: 30px 30px 90px #bebebe, -30px -30px 90px #ffffff;\n        }\n        \n        .chart-header {\n            display: flex;\n            align-items: center;\n            gap: 12px;\n            margin-bottom: 25px;\n            padding-bottom: 15px;\n            border-bottom: 2px solid rgba(190, 190, 190, 0.2);\n        }\n        \n        .chart-icon {\n            font-size: 1.8rem;\n        }\n        \n        .chart-header h3 {\n            font-size: 1.4rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        .chart-container {\n            background: #e0e5ec;\n            border-radius: 20px;\n            padding: 20px;\n            box-shadow: inset 10px 10px 20px #bebebe, inset -10px -10px 20px #ffffff;\n            text-align: center;\n        }\n        \n        .chart-container img {\n            max-width: 100%;\n            height: auto;\n            border-radius: 15px;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .chart-container img:hover {\n            transform: scale(1.02);\n            box-shadow: 12px 12px 24px #bebebe, -12px -12px 24px #ffffff;\n        }\n        \n        /* Detail Sections */\n        .detail-section {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            margin-bottom: 30px;\n            box-shadow: 20px 20px 40px #bebebe, -20px -20px 40px #ffffff;\n        }\n        \n        .section-header {\n            display: flex;\n            align-items: center;\n            gap: 16px;\n            margin-bottom: 30px;\n            padding-bottom: 20px;\n            border-bottom: 2px solid rgba(190, 190, 190, 0.2);\n        }\n        \n        .section-icon {\n            width: 50px;\n            height: 50px;\n            border-radius: 15px;\n            background: #e0e5ec;\n            box-shadow: inset 8px 8px 16px #bebebe, inset -8px -8px 16px #ffffff;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n            font-size: 1.5rem;\n        }\n        \n        .section-title {\n            font-size: 1.6rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        /* Subsections */\n        .subsection {\n            margin-bottom: 25px;\n            padding: 20px;\n            background: #e0e5ec;\n            border-radius: 15px;\n            box-shadow: inset 10px 10px 20px #bebebe, inset -10px -10px 20px #ffffff;\n        }\n        \n        .subsection-title {\n            font-size: 1.2rem;\n            font-weight: 600;\n            color: #2d3748;\n            margin-bottom: 15px;\n            display: flex;\n            align-items: center;\n            gap: 8px;\n        }\n        \n        /* Tables */\n        .table-container {\n            overflow: hidden;\n            border-radius: 15px;\n            margin: 20px 0;\n            background: #e0e5ec;\n            box-shadow: inset 5px 5px 10px #bebebe, inset -5px -5px 10px #ffffff;\n        }\n        \n        .data-table {\n            width: 100%;\n            border-collapse: collapse;\n        }\n        \n        .data-table th {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            color: white;\n            padding: 15px;\n            text-align: left;\n            font-weight: 600;\n            font-size: 0.9rem;\n            border: none;\n        }\n        \n        .data-table td {\n            padding: 15px;\n            border-bottom: 1px solid rgba(190, 190, 190, 0.2);\n            font-size: 0.9rem;\n            color: #2d3748;\n            background: #e0e5ec;\n        }\n        \n        .data-table tr:nth-child(even) td {\n            background: rgba(255, 255, 255, 0.3);\n        }\n        \n        .data-table tr:hover td {\n            background: rgba(102, 126, 234, 0.1);\n        }\n        \n        /* Scrollable table container for news and ratings */\n        .scrollable-table-container {\n            max-height: 400px;\n            overflow-y: auto;\n            overflow-x: hidden;\n            border-radius: 15px;\n            background: #e0e5ec;\n            box-shadow: inset 8px 8px 16px #bebebe, inset -8px -8px 16px #ffffff;\n            padding: 5px;\n            margin: 10px 0;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar {\n            width: 8px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-track {\n            background: #e0e5ec;\n            border-radius: 4px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-thumb {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            border-radius: 4px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-thumb:hover {\n            background: linear-gradient(135deg, #5a67d8, #6b46c1);\n        }\n        \n        /* Status badges */\n        .status-badge {\n            padding: 8px 16px;\n            border-radius: 20px;\n            font-size: 0.8rem;\n            font-weight: 600;\n            text-transform: uppercase;\n            letter-spacing: 0.5px;\n            display: inline-block;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n        }\n        \n        .status-买入, .status-增持50股, .status-增持50100股 {\n            background: #10b981;\n            color: white;\n        }\n        \n        .status-卖出 {\n            background: #ef4444;\n            color: white;\n        }\n        \n        .status-持有 {\n            background: #f59e0b;\n            color: white;\n        }\n        \n        .risk-高 {\n            background: #ef4444;\n            color: white;\n        }\n        \n        .risk-中, .risk-中等 {\n            background: #f59e0b;\n            color: white;\n        }\n        \n        .risk-低 {\n            background: #10b981;\n            color: white;\n        }\n        \n        /* Links */\n        .news-title-link, .news-link {\n            color: #667eea;\n            text-decoration: none;\n            font-weight: 500;\n            transition: all 0.3s ease;\n        }\n        \n        .news-title-link:hover, .news-link:hover {\n            color: #5a67d8;\n            text-decoration: underline;\n        }\n        \n        /* Lists */\n        ul {\n            margin: 15px 0;\n            padding-left: 25px;\n        }\n        \n        li {\n            margin-bottom: 8px;\n            color: #2d3748;\n        }\n        \n        /* Footer */\n        .footer {\n            background: #2d3748;\n            color: white;\n            padding: 30px;\n            text-align: center;\n            border-radius: 20px;\n            margin-top: 30px;\n            box-shadow: 20px 20px 40px #bebebe, -20px -20px 40px #ffffff;\n        }\n        \n        .footer-content p {\n            margin-bottom: 8px;\n            opacity: 0.9;\n        }\n        \n        /* Responsive Design */\n        @media (max-width: 768px) {\n            .container {\n                padding: 20px 10px;\n            }\n            \n            .main-header {\n                padding: 40px 20px;\n            }\n            \n            .main-title {\n                font-size: 2.2rem;\n            }\n            \n            .header-info-cards {\n                flex-direction: column;\n                align-items: center;\n                gap: 15px;\n            }\n            \n            .info-card {\n                width: 100%;\n                max-width: 300px;\n                justify-content: center;\n            }\n            \n            .analysis-summary {\n                grid-template-columns: 1fr;\n            }\n            \n            .price-targets, .risk-levels {\n                flex-direction: column;\n                gap: 15px;\n            }\n            \n            .chart-section {\n                padding: 25px 15px;\n            }\n        }\n        \n        /* Animations */\n        @keyframes fadeInUp {\n            from {\n                opacity: 0;\n                transform: translateY(30px);\n            }\n            to {\n                opacity: 1;\n                transform: translateY(0);\n            }\n        }\n        \n        .detail-section, .chart-section, .analysis-summary {\n            animation: fadeInUp 0.6s ease forwards;\n        }\n        \n        /* Custom scrollbar */\n        ::-webkit-scrollbar {\n            width: 12px;\n        }\n        \n        ::-webkit-scrollbar-track {\n            background: #e0e5ec;\n            border-radius: 10px;\n        }\n        \n        ::-webkit-scrollbar-thumb {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            border-radius: 10px;\n            border: 2px solid #e0e5ec;\n        }\n        \n        ::-webkit-scrollbar-thumb:hover {\n            background: linear-gradient(135deg, #5a67d8, #6b46c1);\n        }\n        "

    def _get_section_icon(self, section_name: str) -> str:
        """Get appropriate icon for section based on name."""
        section_lower = section_name.lower()
        if '交易' in section_lower or '决策' in section_lower:
            return '💼'
        elif '市场' in section_lower or '环境' in section_lower:
            return '🌍'
        elif '技术' in section_lower or '分析' in section_lower:
            return '📈'
        elif '基本面' in section_lower or '资讯' in section_lower:
            return '📰'
        elif '风险' in section_lower or '评估' in section_lower:
            return '🛡️'
        elif '历史' in section_lower or '表现' in section_lower:
            return '📊'
        elif '投资' in section_lower or '建议' in section_lower:
            return '💡'
        else:
            return '📄'

    def _generate_charts_section(self, technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the charts section with neomorphism styling."""
        if not technical_chart_base64 and (not price_volume_chart_base64):
            return ''
        charts_html = []
        if price_volume_chart_base64:
            charts_html.append(f'\n                <div class="chart-section">\n                    <div class="chart-header">\n                        <div class="chart-icon">📊</div>\n                        <h3>K线图技术分析</h3>\n                    </div>\n                    <div class="chart-container">\n                        <img src="data:image/png;base64,{price_volume_chart_base64}" alt="K线图分析" />\n                    </div>\n                </div>\n            ')
        if technical_chart_base64:
            charts_html.append(f'\n                <div class="chart-section">\n                    <div class="chart-header">\n                        <div class="chart-icon">📈</div>\n                        <h3>技术指标综合分析</h3>\n                    </div>\n                    <div class="chart-container">\n                        <img src="data:image/png;base64,{technical_chart_base64}" alt="技术指标分析" />\n                    </div>\n                </div>\n            ')
        return ''.join(charts_html)

    def _generate_detailed_sections(self, sections, metadata: Dict[str, str]=None) -> str:
        """Generate detailed analysis sections with optimized layout."""
        sections_html = []
        section_order = ['1. 交易操作决策', '2. 市场环境分析', '3. 技术分析', '4. 基本面分析（资讯动向）', '5. 风险评估', '6. 历史表现回顾', '7. 投资建议']
        for section_key in section_order:
            if section_key in sections:
                section_data = sections[section_key]
                section_name = section_key.split('. ', 1)[1] if '. ' in section_key else section_key
                if '基本面分析' in section_name:
                    section_content = self._generate_fundamentals_section_from_csv(metadata)
                else:
                    section_content = self._generate_section_content(section_data)
                section_html = f'\n                    <div class="detail-section">\n                        <div class="section-header">\n                            <div class="section-icon">{self._get_section_icon(section_name)}</div>\n                            <h2 class="section-title">{section_name}</h2>\n                        </div>\n                        <div class="section-content">\n                            {section_content}\n                        </div>\n                    </div>\n                '
                sections_html.append(section_html)
        for section_key, section_data in sections.items():
            if section_key not in section_order:
                section_name = section_key.split('. ', 1)[1] if '. ' in section_key else section_key
                if '基本面分析' in section_name:
                    section_content = self._generate_fundamentals_section_from_csv(metadata)
                else:
                    section_content = self._generate_section_content(section_data)
                section_html = f'\n                    <div class="detail-section">\n                        <div class="section-header">\n                            <div class="section-icon">{self._get_section_icon(section_name)}</div>\n                            <h2 class="section-title">{section_name}</h2>\n                        </div>\n                        <div class="section-content">\n                            {section_content}\n                        </div>\n                    </div>\n                '
                sections_html.append(section_html)
        return ''.join(sections_html)

    def _generate_subsection(self, subsection_name: str, subsection_data: Dict[str, Any]) -> str:
        """Generate a single subsection."""
        content_parts = []
        for table in subsection_data.get('tables', []):
            content_parts.append(self._generate_table(table))
        for list_items in subsection_data.get('lists', []):
            content_parts.append(self._generate_list(list_items))
        if subsection_data.get('text'):
            content_parts.append(self._generate_text_content(subsection_data['text']))
        return f'\n        <div class="subsection">\n            <h3 class="subsection-title"><i class="fas fa-caret-right"></i> {subsection_name}</h3>\n            {''.join(content_parts)}\n        </div>\n        '

    def _generate_table(self, table_data: Dict[str, Any]) -> str:
        """Generate HTML table from table data."""
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        if not headers:
            return ''
        is_news_table = any((keyword in ' '.join(headers).lower() for keyword in ['新闻', 'news', '标题', 'title']))
        has_link_column = any((keyword in ' '.join(headers).lower() for keyword in ['链接', 'url', 'link']))
        header_html = '<tr>' + ''.join((f'<th>{header}</th>' for header in headers)) + '</tr>'
        rows_html = []
        for row in rows:
            cells_html = []
            for i, cell in enumerate(row):
                header_name = headers[i].lower()
                if any((keyword in header_name for keyword in ['决策', '操作建议', '决策类型'])):
                    cell_class = cell.replace(' ', '').replace('-', '').replace('股', '')
                    cells_html.append(f'<td><span class="status-badge status-{cell_class}">{cell}</span></td>')
                elif any((keyword in header_name for keyword in ['风险等级', '等级', '风险级别'])):
                    cells_html.append(f'<td><span class="status-badge risk-{cell}">{cell}</span></td>')
                elif is_news_table and has_link_column and any((keyword in header_name for keyword in ['新闻标题', '标题', 'title'])):
                    link_index = None
                    for j, header in enumerate(headers):
                        if any((keyword in header.lower() for keyword in ['链接', 'url', 'link'])):
                            link_index = j
                            break
                    if link_index is not None and link_index < len(row):
                        link_url = row[link_index]
                        if link_url and link_url.lower() not in ['n/a', '-', 'na', ''] and ('http://' in link_url.lower() or 'https://' in link_url.lower()):
                            cells_html.append(f'<td><a href="{link_url}" target="_blank" class="news-title-link">{cell}</a></td>')
                        else:
                            cells_html.append(f'<td>{cell}</td>')
                    else:
                        cells_html.append(f'<td>{cell}</td>')
                elif any((keyword in header_name for keyword in ['链接', 'url', 'link'])):
                    if cell and cell.lower() not in ['n/a', '-', 'na', ''] and ('http://' in cell.lower() or 'https://' in cell.lower()):
                        cells_html.append(f'<td><a href="{cell}" target="_blank" class="news-link">{cell}</a></td>')
                    else:
                        cells_html.append(f'<td>{cell}</td>')
                else:
                    cells_html.append(f'<td>{cell}</td>')
            rows_html.append('<tr>' + ''.join(cells_html) + '</tr>')
        return f'\n        <div class="table-container">\n            <table class="data-table">\n                <thead>{header_html}</thead>\n                <tbody>{''.join(rows_html)}</tbody>\n            </table>\n        </div>\n        '

    def _generate_list(self, list_items: List[str]) -> str:
        """Generate HTML list from list items."""
        items_html = ''.join((f'<li>{item}</li>' for item in list_items))
        return f'<ul style="margin: 1rem 0; padding-left: 2rem;">{items_html}</ul>'

    def _generate_text_content(self, text_lines: List[str]) -> str:
        """Generate HTML from text content."""
        filtered_lines = []
        for line in text_lines:
            if line and (not line.startswith('---')):
                line = re.sub('\\*\\*(.*?)\\*\\*', '<strong>\\1</strong>', line)
                line = re.sub('\\*(.*?)\\*', '<em>\\1</em>', line)
                filtered_lines.append(line)
        if not filtered_lines:
            return ''
        return f'<div style="margin: 1rem 0; line-height: 1.6;">{'<br>'.join(filtered_lines)}</div>'

    def _generate_section_content(self, section_data: Dict[str, Any]) -> str:
        """Generate content for a report section with subsections."""
        content_html = []
        subsections = section_data.get('subsections', {})
        for subsection_name, subsection_data in subsections.items():
            content_html.append(self._generate_subsection(subsection_name, subsection_data))
        return ''.join(content_html)

    def _generate_charts_section(self, technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the enhanced charts section exactly like reference report."""
        charts_html = []
        if price_volume_chart_base64:
            charts_html.append(f'\n        <div class="chart-section">\n            <h2 class="section-title">\n                <div class="section-icon">\n                    <i class="fas fa-chart-line"></i>\n                </div>\n                K线图技术分析\n            </h2>\n            <div class="chart-container">\n                <img src="data:image/png;base64,{price_volume_chart_base64}" alt="K线图分析" />\n            </div>\n        </div>\n            ')
        if technical_chart_base64:
            charts_html.append(f'\n        <div class="chart-section">\n            <h2 class="section-title">\n                <div class="section-icon">\n                    <i class="fas fa-chart-bar"></i>\n                </div>\n                技术指标综合分析\n            </h2>\n            <div class="chart-container">\n                <img src="data:image/png;base64,{technical_chart_base64}" alt="技术指标分析" />\n            </div>\n        </div>\n            ')
        return ''.join(charts_html)

    def _generate_footer(self, metadata: Dict[str, str]) -> str:
        """Generate the footer section."""
        return f'\n        <footer class="footer">\n            <div class="footer-content">\n                <p>报告生成时间: {metadata.get('报告生成时间', 'Unknown')}</p>\n                <p>数据来源: 股票市场数据、经济新闻、行业分析报告</p>\n                <p><strong>免责声明:</strong> 本报告仅供个人投资参考，不构成投资建议</p>\n            </div>\n        </footer>\n        '

    def _get_javascript(self) -> str:
        """Get the JavaScript for interactivity."""
        return "\n        // Intersection Observer for smooth animations\n        const observerOptions = {\n            threshold: 0.1,\n            rootMargin: '0px 0px -50px 0px'\n        };\n        \n        const observer = new IntersectionObserver((entries) => {\n            entries.forEach(entry => {\n                if (entry.isIntersecting) {\n                    entry.target.style.opacity = '1';\n                    entry.target.style.transform = 'translateY(0)';\n                }\n            });\n        }, observerOptions);\n        \n        // Initialize when DOM is ready\n        document.addEventListener('DOMContentLoaded', () => {\n            // Observe all sections for animations\n            const sections = document.querySelectorAll('.detail-section, .chart-section, .analysis-summary');\n            sections.forEach(section => {\n                observer.observe(section);\n            });\n            \n            // Add hover effects to tables\n            const tables = document.querySelectorAll('.data-table');\n            tables.forEach(table => {\n                const rows = table.querySelectorAll('tbody tr');\n                rows.forEach(row => {\n                    row.addEventListener('mouseenter', () => {\n                        row.style.transform = 'scale(1.01)';\n                        row.style.transition = 'transform 0.2s ease';\n                    });\n                    row.addEventListener('mouseleave', () => {\n                        row.style.transform = 'scale(1)';\n                    });\n                });\n            });\n            \n            // Add smooth hover effects to cards\n            const cards = document.querySelectorAll('.info-card, .summary-card');\n            cards.forEach(card => {\n                card.addEventListener('mouseenter', () => {\n                    card.style.transition = 'all 0.3s ease';\n                });\n            });\n        });\n        "

def _generate_dashboard_overview(self, sections: Dict[str, Any], metadata: Dict[str, str]) -> str:
    """Generate a dashboard overview with key metrics extracted from actual report data."""
    investment_advice = '持有'
    investment_reason = '基于技术分析和基本面评估的专业建议'
    risk_level = '中等'
    confidence_level = '中等'
    target_price = '285'
    stop_price = '270'
    expected_return = '2%'
    strategy_period = '短期持仓'
    trading_section = sections.get('一、交易操作决策', {})
    if trading_section:
        subsections = trading_section.get('subsections', {})
        core_decision = subsections.get('1.1 核心决策', {})
        if core_decision:
            tables = core_decision.get('tables', [])
            if tables and len(tables) > 0:
                rows = tables[0].get('rows', [])
                if rows and len(rows) > 0:
                    row = rows[0]
                    if len(row) >= 4:
                        investment_advice = row[1] if row[1] else investment_advice
                        investment_reason = row[2] if row[2] else investment_reason
                        risk_level = row[3] if row[3] else risk_level
        price_targets = subsections.get('1.3 价格目标', {})
        if price_targets:
            tables = price_targets.get('tables', [])
            if tables and len(tables) > 0:
                rows = tables[0].get('rows', [])
                if rows and len(rows) > 0:
                    row = rows[0]
                    if len(row) >= 4:
                        target_price = str(row[1]).replace('RMB', '').replace(' ', '') if row[1] else target_price
                        stop_price = str(row[2]).replace('RMB', '').replace(' ', '') if row[2] else stop_price
                        expected_return = str(row[3]) if row[3] else expected_return
    risk_section = sections.get('五、风险评估', {})
    if risk_section:
        subsections = risk_section.get('subsections', {})
        risk_factors = subsections.get('5.1 风险因素', {})
        if risk_factors:
            tables = risk_factors.get('tables', [])
            if tables and len(tables) > 0:
                rows = tables[0].get('rows', [])
                risk_levels = []
                for row in rows:
                    if len(row) >= 2 and row[1]:
                        risk_levels.append(row[1])
                if risk_levels:
                    high_count = risk_levels.count('高')
                    mid_count = risk_levels.count('中')
                    low_count = risk_levels.count('低')
                    if high_count > mid_count and high_count > low_count:
                        risk_level = '高'
                    elif mid_count >= high_count and mid_count >= low_count:
                        risk_level = '中等'
                    else:
                        risk_level = '低'
    advice_section = sections.get('七、投资建议', {})
    if advice_section:
        subsections = advice_section.get('subsections', {})
        short_term = subsections.get('7.1 短期操作建议', {})
        if short_term:
            text_content = short_term.get('text_content', [])
            if text_content:
                content_text = ' '.join(text_content)
                return_match = re.search('预期收益[：:]\\s*([0-9.]+%)', content_text)
                if return_match:
                    expected_return = return_match.group(1)
        long_term = subsections.get('7.2 中长期策略', {})
        if long_term:
            text_content = long_term.get('text_content', [])
            if text_content:
                content_text = ' '.join(text_content)
                period_match = re.search('持有周期[：:]\\s*([^。\\n]+)', content_text)
                if period_match:
                    period = period_match.group(1).strip()
                    if '月' in period or '年' in period:
                        strategy_period = '中长期持仓'
                    else:
                        strategy_period = '短期持仓'
    if investment_advice in ['买入', '强烈买入']:
        confidence_level = '高'
    elif investment_advice in ['卖出', '强烈卖出']:
        confidence_level = '低'
    elif investment_advice in ['部分卖出', '部分买入']:
        confidence_level = '中等'
    else:
        confidence_level = '中等'
    target_price = re.sub('[^0-9.]', '', str(target_price))
    stop_price = re.sub('[^0-9.]', '', str(stop_price))
    return f'\n            <div class="analysis-summary">\n                <div class="summary-card">\n                    <div class="card-icon green">\n                        <i class="icon">👍</i>\n                    </div>\n                    <h3>投资建议</h3>\n                    <div class="main-value">{investment_advice}</div>\n                    <div class="sub-text">{investment_reason[:50]}{('...' if len(investment_reason) > 50 else '')}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon blue">\n                        <i class="icon">🎯</i>\n                    </div>\n                    <h3>价格目标</h3>\n                    <div class="price-targets">\n                        <div class="price-item">\n                            <span class="label">目标价</span>\n                            <span class="value">¥{target_price}</span>\n                        </div>\n                        <div class="price-item">\n                            <span class="label">止损价</span>\n                            <span class="value">¥{stop_price}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">预期收益: {expected_return}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon orange">\n                        <i class="icon">🛡️</i>\n                    </div>\n                    <h3>风险评估</h3>\n                    <div class="risk-levels">\n                        <div class="risk-item">\n                            <span class="label">风险级别</span>\n                            <span class="value">{risk_level}</span>\n                        </div>\n                        <div class="risk-item">\n                            <span class="label">信心级别</span>\n                            <span class="value">{confidence_level}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">{strategy_period}</div>\n                </div>\n            </div>\n        '

class StockDataFetcher:
    """股票数据抓取器 - 核心功能类"""

    def __init__(self, stock_code, auto_create_output_dir=True):
        """
        初始化数据抓取器
        
        Args:
            stock_code (str): 股票代码（如：300750、000001等）
            auto_create_output_dir (bool): 是否自动创建输出目录，默认True
        """
        self.stock_code = stock_code
        self.symbol_sz = f'sz{stock_code}' if stock_code.startswith('0') or stock_code.startswith('3') else f'sh{stock_code}'
        if auto_create_output_dir:
            self.output_dir = Path(f'output_{stock_code}')
        else:
            self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.stock_name = self._get_stock_name()

    def _get_stock_name(self):
        """获取股票名称"""
        try:
            stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
            if not stock_info.empty:
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    return name_row['value'].iloc[0]
            return f'股票{self.stock_code}'
        except:
            return f'股票{self.stock_code}'

    def get_timestamp(self):
        """获取当前日期用于文件命名"""
        return datetime.datetime.now().strftime('%Y%m%d')

    def save_data(self, data, filename_prefix, description=''):
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据（pandas DataFrame）
            filename_prefix (str): 文件名前缀
            description (str): 数据描述
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            timestamp = self.get_timestamp()
            filename = f'{filename_prefix}_{timestamp}_{self.stock_code}.csv'
            filepath = self.output_dir / filename
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath} (共{len(data)}条记录)')
            else:
                df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath}')
            return str(filepath)
        except Exception as e:
            self.logger.error(f'❌ 保存{description}失败: {str(e)}')
            return None

    def fetch_stock_daily(self, days=30):
        """
        抓取股票日线数据
        
        Args:
            days (int): 抓取最近多少天的数据，默认30天
            
        Returns:
            pandas.DataFrame: 股票日线数据
        """
        try:
            self.logger.info(f'📈 开始抓取{self.stock_code}日线数据...')
            stock_df = ak.stock_zh_a_daily(symbol=self.symbol_sz).reset_index()
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
            recent_data = stock_df[stock_df['date'] >= days_ago]
            self.save_data(recent_data, 'stock_daily_catl', f'{self.stock_code}日线数据')
            return recent_data
        except Exception as e:
            self.logger.error(f'❌ 抓取股票日线数据失败: {str(e)}')
            return None

    def fetch_china_cpi(self):
        """
        抓取中国CPI数据 (限制为过去2年)
        
        Returns:
            pandas.DataFrame: 中国CPI数据
        """
        try:
            self.logger.info('📊 开始抓取中国CPI数据...')
            cpi_df = ak.macro_china_cpi()
            if not cpi_df.empty:
                if '月份' in cpi_df.columns:

                    def convert_chinese_date(date_str):
                        try:
                            if '年' in date_str and '月' in date_str:
                                year = date_str.split('年')[0]
                                month = date_str.split('年')[1].split('月')[0]
                                return f'{year}-{month.zfill(2)}-01'
                            else:
                                return date_str
                        except:
                            return None
                    cpi_df['月份'] = cpi_df['月份'].apply(convert_chinese_date)
                    cpi_df['月份'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
                    cpi_df = cpi_df.dropna(subset=['月份'])
                    if not cpi_df.empty:
                        two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
                        cpi_df = cpi_df[cpi_df['月份'] >= two_years_ago]
                        self.logger.info(f'✅ CPI数据已限制为过去2年: {len(cpi_df)} 条记录')
            return cpi_df
        except Exception as e:
            self.logger.error(f'❌ 抓取CPI数据失败: {str(e)}')
            return None

    def fetch_china_gdp(self):
        """
        抓取中国GDP数据
        
        Returns:
            pandas.DataFrame: 中国GDP数据
        """
        try:
            self.logger.info('📊 开始抓取中国GDP数据...')
            gdp_df = ak.macro_china_gdp_yearly()
            return gdp_df
        except Exception as e:
            self.logger.error(f'❌ 抓取GDP数据失败: {str(e)}')
            return None

    def fetch_industry_fund_flow(self):
        """
        抓取行业资金流数据
        
        Returns:
            pandas.DataFrame: 行业资金流数据
        """
        try:
            self.logger.info('💰 开始抓取行业资金流数据...')
            industry_fund_df = ak.stock_fund_flow_industry()
            return industry_fund_df
        except Exception as e:
            self.logger.error(f'❌ 抓取行业资金流数据失败: {str(e)}')
            return None

    def fetch_stock_news(self):
        """
        抓取个股新闻数据
        
        Returns:
            pandas.DataFrame: 个股新闻数据
        """
        try:
            self.logger.info(f'📰 开始抓取{self.stock_name}({self.stock_code})新闻数据...')
            news_df = ak.stock_news_em(symbol=self.stock_code)
            return news_df
        except Exception as e:
            self.logger.error(f'❌ 抓取新闻数据失败: {str(e)}')
            return None

    def fetch_market_summary(self):
        """
        抓取上交所市场概况
        
        Returns:
            pandas.DataFrame: 市场概况数据
        """
        try:
            self.logger.info('🏛️ 开始抓取上交所市场概况...')
            sse_summary = ak.stock_sse_summary()
            return sse_summary
        except Exception as e:
            self.logger.error(f'❌ 抓取市场概况失败: {str(e)}')
            return None

    def fetch_market_indices(self):
        """
        抓取重要指数行情
        
        Returns:
            pandas.DataFrame: 重要指数数据
        """
        try:
            self.logger.info('📊 开始抓取重要指数行情...')
            market_indices = ak.stock_zh_index_spot_em(symbol='沪深重要指数')
            return market_indices
        except Exception as e:
            self.logger.error(f'❌ 抓取市场指数失败: {str(e)}')
            return None

    def fetch_option_volatility(self):
        """
        抓取50ETF期权波动率指数 (限制为过去1个月)
        
        Returns:
            pandas.DataFrame: 期权波动率数据
        """
        try:
            self.logger.info('📈 开始抓取50ETF波动率指数...')
            vol50 = ak.index_option_50etf_qvix()
            if not vol50.empty:
                if 'date' in vol50.columns:
                    vol50['date'] = pd.to_datetime(vol50['date'])
                    one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    vol50 = vol50[vol50['date'] >= one_month_ago]
                    self.logger.info(f'✅ 期权波动率数据已限制为过去1个月: {len(vol50)} 条记录')
            return vol50
        except Exception as e:
            self.logger.error(f'❌ 抓取期权波动率数据失败: {str(e)}')
            return None

    def fetch_institution_recommendation(self):
        """
        抓取机构评级数据 (限制为过去半年)
        
        Returns:
            pandas.DataFrame: 机构评级数据
        """
        try:
            self.logger.info(f'🏦 开始抓取{self.stock_name}({self.stock_code})机构评级...')
            inst_rec = ak.stock_institute_recommend_detail(symbol=self.stock_code)
            if not inst_rec.empty:
                date_columns = ['评级日期', 'date', '日期']
                date_col = None
                for col in date_columns:
                    if col in inst_rec.columns:
                        date_col = col
                        break
                if date_col:
                    inst_rec[date_col] = pd.to_datetime(inst_rec[date_col])
                    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                    inst_rec = inst_rec[inst_rec[date_col] >= six_months_ago]
                    self.logger.info(f'✅ 机构评级数据已限制为过去半年: {len(inst_rec)} 条记录')
            return inst_rec
        except Exception as e:
            self.logger.error(f'❌ 抓取机构评级数据失败: {str(e)}')
            return None

    def fetch_all_data(self):
        """
        抓取所有类型的数据
        
        Returns:
            dict: 包含所有数据的字典
        """
        self.logger.info('🚀 开始抓取全部数据...')
        results = {}
        tasks = [('stock_daily', lambda: self.fetch_stock_daily(), '股票日线数据'), ('china_cpi', lambda: self.fetch_china_cpi(), '中国CPI数据'), ('china_gdp', lambda: self.fetch_china_gdp(), '中国GDP数据'), ('industry_fund_flow', lambda: self.fetch_industry_fund_flow(), '行业资金流数据'), ('stock_news', lambda: self.fetch_stock_news(), '个股新闻数据'), ('market_summary', lambda: self.fetch_market_summary(), '市场整体概况'), ('market_indices', lambda: self.fetch_market_indices(), '重要指数行情'), ('option_volatility', lambda: self.fetch_option_volatility(), '期权波动率指数'), ('institution_recommendation', lambda: self.fetch_institution_recommendation(), '机构评级数据')]
        for task_name, task_func, description in tasks:
            try:
                self.logger.info(f'\n--- 开始执行: {description} ---')
                result = task_func()
                results[task_name] = result
                if result is not None:
                    filename_mapping = {'stock_daily': 'stock_daily_catl', 'china_cpi': 'china_cpi', 'china_gdp': 'china_gdp_yearly', 'industry_fund_flow': 'industry_fund_flow', 'stock_news': 'stock_news_catl', 'market_summary': 'market_summary_sse', 'market_indices': 'market_indices', 'option_volatility': 'option_volatility_50etf', 'institution_recommendation': 'institution_recommendation_catl'}
                    self.save_data(result, filename_mapping[task_name], description)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f'执行{description}时发生错误: {str(e)}')
                results[task_name] = None
        self.logger.info('🎉 全部数据抓取完成！')
        return results

    def create_data_documentation(self):
        """创建数据文件说明文档"""
        try:
            timestamp = self.get_timestamp()
            doc_content = f'# {self.stock_name}({self.stock_code})数据文件说明\n\n## 📋 文件命名规则\n\n所有数据文件按以下格式命名：\n```\n数据类型_日期_股票代码.csv\n```\n\n例如：`china_cpi_{timestamp}_{self.stock_code}.csv` 表示{timestamp[:4]}年{timestamp[4:6]}月{timestamp[6:8]}日抓取的中国CPI数据，与{self.stock_name}({self.stock_code})相关。\n\n---\n\n## 📊 数据文件详细说明\n\n### 1. 股票日线数据\n**文件名**: `stock_daily_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_a_daily()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘价（元）\n- **high** - 最高价（元）\n- **low** - 最低价（元）\n- **close** - 收盘价（元）\n- **volume** - 成交量（股）\n- **amount** - 成交额（元）\n- **outstanding_share** - 流通股数（股）\n- **turnover** - 换手率\n\n**用途**: 分析{self.stock_name}股价走势、成交情况，进行技术分析\n\n---\n\n### 2. 中国CPI数据\n**文件名**: `china_cpi_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_cpi()\n\n**中文指标说明**:\n- **月份** - 统计月份\n- **全国-当月** - 全国当月CPI指数\n- **全国-同比增长** - 全国CPI同比增长率(%)\n- **全国-环比增长** - 全国CPI环比增长率(%)\n- **全国-累计** - 全国累计CPI指数\n- **城市-当月** - 城市当月CPI指数\n- **城市-同比增长** - 城市CPI同比增长率(%)\n- **城市-环比增长** - 城市CPI环比增长率(%)\n- **城市-累计** - 城市累计CPI指数\n- **农村-当月** - 农村当月CPI指数\n- **农村-同比增长** - 农村CPI同比增长率(%)\n- **农村-环比增长** - 农村CPI环比增长率(%)\n- **农村-累计** - 农村累计CPI指数\n\n**用途**: 反映通胀水平，判断宏观经济环境对{self.stock_name}所在行业的影响\n\n---\n\n### 3. 中国GDP数据\n**文件名**: `china_gdp_yearly_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_gdp_yearly()\n\n**中文指标说明**:\n- **商品** - 数据类型（中国GDP年率报告）\n- **日期** - 发布日期\n- **今值** - 当期GDP增长率(%)\n- **预测值** - 市场预测GDP增长率(%)\n- **前值** - 前期GDP增长率(%)\n\n**用途**: 评估国家经济增长情况，判断宏观经济对{self.stock_name}所在行业需求的影响\n\n---\n\n### 4. 行业资金流数据\n**文件名**: `industry_fund_flow_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_fund_flow_industry()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **行业** - 行业名称\n- **行业指数** - 行业指数代码\n- **行业-涨跌幅** - 行业当日涨跌幅(%)\n- **流入资金** - 资金流入金额（万元）\n- **流出资金** - 资金流出金额（万元）\n- **净额** - 资金净流入金额（万元）\n- **公司家数** - 该行业公司数量\n- **领涨股** - 行业内领涨股票\n- **领涨股-涨跌幅** - 领涨股涨跌幅(%)\n- **当前价** - 领涨股当前价格（元）\n\n**用途**: 分析各行业资金流向，判断{self.stock_name}所在行业的资金关注度\n\n---\n\n### 5. 个股新闻数据\n**文件名**: `stock_news_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_news_em()\n\n**中文指标说明**:\n- **关键词** - 搜索关键词（股票代码）\n- **新闻标题** - 新闻标题\n- **新闻内容** - 新闻摘要/内容\n- **发布时间** - 新闻发布时间\n- **新闻来源** - 新闻来源媒体\n- **新闻链接** - 原文链接地址\n\n**用途**: 获取{self.stock_name}相关新闻资讯，进行舆情分析和基本面研究\n\n---\n\n### 6. 上交所市场概况\n**文件名**: `market_summary_sse_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_sse_summary()\n\n**中文指标说明**:\n- **项目** - 统计项目名称\n- **股票** - 股票相关数据\n- **主板** - 主板市场数据\n- **科创板** - 科创板市场数据\n\n**具体项目包括**:\n- **流通股本** - 流通股总数（亿股）\n- **总市值** - 总市值（亿元）\n- **平均市盈率** - 平均市盈率（倍）\n- **上市公司** - 上市公司数量（家）\n- **上市股票** - 上市股票数量（只）\n- **流通市值** - 流通市值（亿元）\n- **总股本** - 总股本（亿股）\n\n**用途**: 了解整体市场状况，判断市场环境对{self.stock_name}的影响\n\n---\n\n### 7. 重要指数行情\n**文件名**: `market_indices_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_index_spot_em()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **代码** - 指数代码\n- **名称** - 指数名称\n- **最新价** - 最新指数点位\n- **涨跌幅** - 当日涨跌幅(%)\n- **涨跌额** - 当日涨跌点数\n- **成交量** - 成交量（手）\n- **成交额** - 成交金额（万元）\n- **振幅** - 当日振幅(%)\n- **最高** - 当日最高点位\n- **最低** - 当日最低点位\n- **今开** - 今日开盘点位\n- **昨收** - 昨日收盘点位\n- **量比** - 量比\n\n**包含指数**:\n- 上证指数、深证成指、创业板指、科创综指、北证50等\n\n**用途**: 跟踪重要市场指数走势，判断整体市场方向\n\n---\n\n### 8. 50ETF期权波动率指数\n**文件名**: `option_volatility_50etf_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.index_option_50etf_qvix()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘波动率\n- **high** - 最高波动率\n- **low** - 最低波动率\n- **close** - 收盘波动率\n\n**用途**: 反映市场恐慌情绪和波动性预期，是重要的市场情绪指标\n\n---\n\n### 9. 机构评级数据\n**文件名**: `institution_recommendation_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_institute_recommend_detail()\n\n**中文指标说明**:\n- **股票代码** - 股票代码\n- **股票名称** - 股票名称\n- **目标价** - 机构给出的目标价格（元）\n- **最新评级** - 机构最新评级（买入/增持/中性/减持/卖出）\n- **评级机构** - 研究机构名称\n- **分析师** - 分析师姓名\n- **行业** - 所属行业\n- **评级日期** - 评级发布日期\n\n**评级含义**:\n- **买入** - 强烈推荐买入\n- **增持** - 推荐增加持仓\n- **中性** - 维持现有持仓\n- **减持** - 建议减少持仓\n- **卖出** - 建议卖出\n\n**用途**: 了解专业机构对{self.stock_name}的投资建议和价格预期\n\n---\n\n### 10. 数据收集报告\n**文件名**: `collection_report_{timestamp}_{self.stock_code}.csv`\n\n**自动生成的收集统计报告**\n\n**中文指标说明**:\n- **数据类型** - 数据收集任务名称\n- **收集状态** - 收集是否成功（成功/失败）\n- **记录数量** - 成功收集的数据条数\n- **时间戳** - 数据收集完成时间\n\n**用途**: 监控数据收集任务的执行情况，确保数据完整性\n\n---\n\n## 🔍 数据使用建议\n\n### 综合分析框架\n\n1. **宏观经济层面**\n   - 使用CPI、GDP数据判断宏观经济环境\n   - 分析对{self.stock_name}所在行业的影响\n\n2. **市场情绪层面**\n   - 使用期权波动率指数判断市场恐慌程度\n   - 使用重要指数走势判断市场整体方向\n\n3. **行业资金层面**\n   - 使用行业资金流数据判断资金偏好\n   - 关注{self.stock_name}所在行业的资金流向\n\n4. **个股基本面**\n   - 使用机构评级了解专业判断\n   - 使用新闻数据进行舆情分析\n\n5. **技术面分析**\n   - 使用股票日线数据进行技术分析\n   - 结合成交量判断趋势强度\n\n### 数据更新频率\n\n- **日更新**: 股票日线、新闻、指数行情、期权波动率\n- **月更新**: CPI数据\n- **季更新**: GDP数据\n- **实时更新**: 行业资金流、机构评级\n\n---\n\n## ⚠️ 使用注意事项\n\n1. **数据时效性**: 部分数据存在发布延迟，请注意数据的时效性\n2. **数据完整性**: 如遇到数据源问题，某些文件可能缺失，请查看收集报告\n3. **投资风险**: 数据仅供参考，不构成投资建议，投资需谨慎\n4. **版权声明**: 数据来源于公开渠道，请遵守相关使用条款\n\n---\n\n## 📞 技术支持\n\n如有数据解读疑问或技术问题，请参考：\n- akshare官方文档: https://akshare.readthedocs.io/\n- 数据抓取函数库: 本项目中的股票数据抓取函数\n\n**生成时间**: {datetime.datetime.now().strftime('%Y年%m月%d日')}\n**数据版本**: v2.0  \n**适用股票**: {self.stock_name}({self.stock_code})\n'
            doc_filepath = self.output_dir / '数据文件说明.md'
            with open(doc_filepath, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            self.logger.info(f'✅ 数据说明文档已生成: {doc_filepath}')
            return str(doc_filepath)
        except Exception as e:
            self.logger.error(f'❌ 生成数据说明文档失败: {str(e)}')
            return None

def fetch_china_gdp(self):
    """
        抓取中国GDP数据
        
        Returns:
            pandas.DataFrame: 中国GDP数据
        """
    try:
        self.logger.info('📊 开始抓取中国GDP数据...')
        gdp_df = ak.macro_china_gdp_yearly()
        return gdp_df
    except Exception as e:
        self.logger.error(f'❌ 抓取GDP数据失败: {str(e)}')
        return None

def fetch_industry_fund_flow(self):
    """
        抓取行业资金流数据
        
        Returns:
            pandas.DataFrame: 行业资金流数据
        """
    try:
        self.logger.info('💰 开始抓取行业资金流数据...')
        industry_fund_df = ak.stock_fund_flow_industry()
        return industry_fund_df
    except Exception as e:
        self.logger.error(f'❌ 抓取行业资金流数据失败: {str(e)}')
        return None

def fetch_stock_news(self):
    """
        抓取个股新闻数据
        
        Returns:
            pandas.DataFrame: 个股新闻数据
        """
    try:
        self.logger.info(f'📰 开始抓取{self.stock_name}({self.stock_code})新闻数据...')
        news_df = ak.stock_news_em(symbol=self.stock_code)
        return news_df
    except Exception as e:
        self.logger.error(f'❌ 抓取新闻数据失败: {str(e)}')
        return None

def fetch_market_summary(self):
    """
        抓取上交所市场概况
        
        Returns:
            pandas.DataFrame: 市场概况数据
        """
    try:
        self.logger.info('🏛️ 开始抓取上交所市场概况...')
        sse_summary = ak.stock_sse_summary()
        return sse_summary
    except Exception as e:
        self.logger.error(f'❌ 抓取市场概况失败: {str(e)}')
        return None

def fetch_market_indices(self):
    """
        抓取重要指数行情
        
        Returns:
            pandas.DataFrame: 重要指数数据
        """
    try:
        self.logger.info('📊 开始抓取重要指数行情...')
        market_indices = ak.stock_zh_index_spot_em(symbol='沪深重要指数')
        return market_indices
    except Exception as e:
        self.logger.error(f'❌ 抓取市场指数失败: {str(e)}')
        return None

class HTMLGenerator:
    """Generates the HTML report with neomorphism styling and optimized layout."""

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.assets_dir = self.output_path.parent / 'assets'
        self.assets_dir.mkdir(exist_ok=True)

    def encode_image_to_base64(self, image_path: str) -> str:
        """将图片编码为base64字符串"""
        try:
            if not image_path or not os.path.exists(image_path):
                return ''
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f'⚠️ 无法读取图片 {image_path}: {e}')
            return ''

    def _get_latest_close_price(self, stock_code: str, timestamp: str) -> str:
        """从股票日线数据CSV文件中读取最新的收盘价"""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/stock_daily_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                print(f'⚠️ 股票日线数据文件不存在: {csv_path}')
                return 'N/A'
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) < 2:
                print(f'⚠️ 股票日线数据文件为空或格式错误: {csv_path}')
                return 'N/A'
            last_line = lines[-1].strip()
            if not last_line:
                last_line = lines[-2].strip()
            fields = last_line.split(',')
            if len(fields) >= 6:
                close_price = fields[5]
                return close_price
            else:
                print(f'⚠️ 股票日线数据格式错误: {last_line}')
                return 'N/A'
        except Exception as e:
            print(f'⚠️ 读取股票收盘价失败: {e}')
            return 'N/A'

    def generate_report(self, md_file_path: str, technical_chart_path: str, price_volume_chart_path: str) -> str:
        """Generate the complete HTML report with base64 encoded images."""
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        parser = MarkdownParser(md_content)
        metadata = parser.get_metadata()
        technical_chart_base64 = self.encode_image_to_base64(technical_chart_path)
        price_volume_chart_base64 = self.encode_image_to_base64(price_volume_chart_path)
        html_content = self._generate_html_structure(parser, metadata, technical_chart_base64, price_volume_chart_base64)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return str(self.output_path)

    def _read_news_from_csv(self, stock_code: str, timestamp: str) -> List[Dict[str, str]]:
        """Read news data from CSV file and return the latest 10 entries."""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/stock_news_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                return []
            news_data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    news_data.append({'新闻标题': row.get('新闻标题', ''), '来源': row.get('文章来源', ''), '发布时间': row.get('发布时间', ''), '影响程度': '中', '解读': row.get('新闻内容', '')[:100] + '...' if len(row.get('新闻内容', '')) > 100 else row.get('新闻内容', ''), '链接': row.get('新闻链接', '')})
            news_data.sort(key=lambda x: x['发布时间'], reverse=True)
            return news_data[:10]
        except Exception as e:
            print(f'Error reading news CSV: {e}')
            return []

    def _read_ratings_from_csv(self, stock_code: str, timestamp: str) -> List[Dict[str, str]]:
        """Read institution rating data from CSV file and return the latest 10 entries."""
        try:
            csv_path = Path(f'{stock_code}/{timestamp}/data/institution_recommendation_catl_{timestamp}_{stock_code}.csv')
            if not csv_path.exists():
                return []
            ratings_data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ratings_data.append({'机构名称': row.get('评级机构', ''), '评级': row.get('最新评级', ''), '目标价': row.get('目标价', '-'), '评级日期': row.get('评级日期', ''), '分析师': row.get('分析师', '不详')})
            ratings_data.sort(key=lambda x: x['评级日期'], reverse=True)
            return ratings_data[:10]
        except Exception as e:
            print(f'Error reading ratings CSV: {e}')
            return []

    def _generate_fundamentals_section_from_csv(self, metadata: Dict[str, str]) -> str:
        """Generate fundamentals section content directly from CSV files."""
        if not metadata:
            return ''
        stock_code = metadata.get('股票代码', '300750')
        timestamp = metadata.get('日期', '')
        if not timestamp:
            timestamp = datetime.now().strftime('%Y%m%d')
        else:
            import re
            date_match = re.search('(\\d{4})年(\\d{2})月(\\d{2})日', timestamp)
            if date_match:
                year, month, day = date_match.groups()
                timestamp = f'{year}{month}{day}'
            else:
                timestamp = datetime.now().strftime('%Y%m%d')
        news_data = self._read_news_from_csv(stock_code, timestamp)
        ratings_data = self._read_ratings_from_csv(stock_code, timestamp)
        print(f'Debug: Stock code: {stock_code}, Timestamp: {timestamp}')
        print(f'Debug: Found {len(news_data)} news items')
        print(f'Debug: Found {len(ratings_data)} rating items')
        news_html = ''
        if news_data:
            news_headers = ['新闻标题', '来源', '发布时间', '影响程度', '解读', '链接']
            news_rows = []
            for news in news_data:
                news_rows.append([news['新闻标题'], news['来源'], news['发布时间'], news['影响程度'], news['解读'], news['链接']])
            news_table_data = {'headers': news_headers, 'rows': news_rows}
            news_html = f'\n            <div class="subsection">\n                <h3 class="subsection-title"><i class="fas fa-caret-right"></i> 4.1 最新新闻动态</h3>\n                <div class="scrollable-table-container">\n                    {self._generate_table(news_table_data)}\n                </div>\n            </div>\n            '
        ratings_html = ''
        if ratings_data:
            ratings_headers = ['机构名称', '评级', '目标价', '评级日期', '分析师']
            ratings_rows = []
            for rating in ratings_data:
                ratings_rows.append([rating['机构名称'], rating['评级'], rating['目标价'], rating['评级日期'], rating['分析师']])
            ratings_table_data = {'headers': ratings_headers, 'rows': ratings_rows}
            ratings_html = f'\n            <div class="subsection">\n                <h3 class="subsection-title"><i class="fas fa-caret-right"></i> 4.2 机构评级汇总</h3>\n                <div class="scrollable-table-container">\n                    {self._generate_table(ratings_table_data)}\n                </div>\n            </div>\n            '
        return news_html + ratings_html

    def _generate_html_structure(self, parser: MarkdownParser, metadata: Dict[str, str], technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the complete HTML structure with neomorphism design."""
        header_html = self._generate_neomorphism_header(metadata, parser.sections)
        charts_html = self._generate_charts_section(technical_chart_base64, price_volume_chart_base64)
        dashboard_html = self._generate_dashboard_overview(parser.sections, metadata)
        sections_html = self._generate_detailed_sections(parser.sections, metadata)
        footer_html = self._generate_footer(metadata)
        return f"""\n        <!DOCTYPE html>\n        <html lang="zh-CN">\n        <head>\n            <meta charset="UTF-8">\n            <meta name="viewport" content="width=device-width, initial-scale=1.0">\n            <title>{metadata.get('股票名称', 'Unknown')} ({metadata.get('股票代码', 'Unknown')}) - 投资分析报告</title>\n            <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">\n            <style>\n                {self._get_neomorphism_css()}\n            </style>\n        </head>\n        <body>\n            <div class="container">\n                {header_html}\n                {dashboard_html}\n                {charts_html}\n                {sections_html}\n                {footer_html}\n            </div>\n            \n            <script>\n                {self._get_javascript()}\n            </script>\n        </body>\n        </html>\n        """

    def _generate_neomorphism_header(self, metadata: Dict[str, str], sections: Dict[str, Any]) -> str:
        """Generate the neomorphism-style header exactly like the reference image."""
        stock_name = metadata.get('股票名称', 'Unknown')
        stock_code = metadata.get('股票代码', 'Unknown')
        now = datetime.now()
        date = now.strftime('%Y年%m月%d日')
        time = now.strftime('%H:%M:%S')
        current_price = 'N/A'
        if stock_code != 'Unknown':
            date_match = re.search('(\\d{4})年(\\d{2})月(\\d{2})日', date)
            if date_match:
                timestamp = f'{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}'
                current_price = self._get_latest_close_price(stock_code, timestamp)
        if current_price == 'N/A' and '当前持仓' in metadata:
            holding_info = metadata['当前持仓']
            if '平均成本' in holding_info:
                price_match = re.search('平均成本\\s*(\\d+(?:\\.\\d+)?)', holding_info)
                if price_match:
                    current_price = price_match.group(1)
        return f'\n            <div class="main-header">\n                <h1 class="main-title">{stock_name}({stock_code})</h1>\n                <p class="main-subtitle">新拟态风格投资分析报告</p>\n                \n                <div class="header-info-cards">\n                    <div class="info-card">\n                        <div class="info-icon">📅</div>\n                        <span>{date}</span>\n                    </div>\n                    <div class="info-card">\n                        <div class="info-icon">🕐</div>\n                        <span>{time}</span>\n                    </div>\n                    <div class="info-card">\n                        <div class="info-icon">📊</div>\n                        <span>当前价格: ¥{current_price}</span>\n                    </div>\n                </div>\n            </div>\n        '

    def _generate_dashboard_overview(self, sections: Dict[str, Any], metadata: Dict[str, str]) -> str:
        """Generate a dashboard overview with key metrics extracted from actual report data."""
        investment_advice = '持有'
        investment_reason = '基于技术分析和基本面评估的专业建议'
        risk_level = '中等'
        confidence_level = '中等'
        target_price = '285'
        stop_price = '270'
        expected_return = '2%'
        strategy_period = '短期持仓'
        trading_section = sections.get('一、交易操作决策', {})
        if trading_section:
            subsections = trading_section.get('subsections', {})
            core_decision = subsections.get('1.1 核心决策', {})
            if core_decision:
                tables = core_decision.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    if rows and len(rows) > 0:
                        row = rows[0]
                        if len(row) >= 4:
                            investment_advice = row[1] if row[1] else investment_advice
                            investment_reason = row[2] if row[2] else investment_reason
                            risk_level = row[3] if row[3] else risk_level
            price_targets = subsections.get('1.3 价格目标', {})
            if price_targets:
                tables = price_targets.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    if rows and len(rows) > 0:
                        row = rows[0]
                        if len(row) >= 4:
                            target_price = str(row[1]).replace('RMB', '').replace(' ', '') if row[1] else target_price
                            stop_price = str(row[2]).replace('RMB', '').replace(' ', '') if row[2] else stop_price
                            expected_return = str(row[3]) if row[3] else expected_return
        risk_section = sections.get('五、风险评估', {})
        if risk_section:
            subsections = risk_section.get('subsections', {})
            risk_factors = subsections.get('5.1 风险因素', {})
            if risk_factors:
                tables = risk_factors.get('tables', [])
                if tables and len(tables) > 0:
                    rows = tables[0].get('rows', [])
                    risk_levels = []
                    for row in rows:
                        if len(row) >= 2 and row[1]:
                            risk_levels.append(row[1])
                    if risk_levels:
                        high_count = risk_levels.count('高')
                        mid_count = risk_levels.count('中')
                        low_count = risk_levels.count('低')
                        if high_count > mid_count and high_count > low_count:
                            risk_level = '高'
                        elif mid_count >= high_count and mid_count >= low_count:
                            risk_level = '中等'
                        else:
                            risk_level = '低'
        advice_section = sections.get('七、投资建议', {})
        if advice_section:
            subsections = advice_section.get('subsections', {})
            short_term = subsections.get('7.1 短期操作建议', {})
            if short_term:
                text_content = short_term.get('text_content', [])
                if text_content:
                    content_text = ' '.join(text_content)
                    return_match = re.search('预期收益[：:]\\s*([0-9.]+%)', content_text)
                    if return_match:
                        expected_return = return_match.group(1)
            long_term = subsections.get('7.2 中长期策略', {})
            if long_term:
                text_content = long_term.get('text_content', [])
                if text_content:
                    content_text = ' '.join(text_content)
                    period_match = re.search('持有周期[：:]\\s*([^。\\n]+)', content_text)
                    if period_match:
                        period = period_match.group(1).strip()
                        if '月' in period or '年' in period:
                            strategy_period = '中长期持仓'
                        else:
                            strategy_period = '短期持仓'
        if investment_advice in ['买入', '强烈买入']:
            confidence_level = '高'
        elif investment_advice in ['卖出', '强烈卖出']:
            confidence_level = '低'
        elif investment_advice in ['部分卖出', '部分买入']:
            confidence_level = '中等'
        else:
            confidence_level = '中等'
        target_price = re.sub('[^0-9.]', '', str(target_price))
        stop_price = re.sub('[^0-9.]', '', str(stop_price))
        return f'\n            <div class="analysis-summary">\n                <div class="summary-card">\n                    <div class="card-icon green">\n                        <i class="icon">👍</i>\n                    </div>\n                    <h3>投资建议</h3>\n                    <div class="main-value">{investment_advice}</div>\n                    <div class="sub-text">{investment_reason[:50]}{('...' if len(investment_reason) > 50 else '')}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon blue">\n                        <i class="icon">🎯</i>\n                    </div>\n                    <h3>价格目标</h3>\n                    <div class="price-targets">\n                        <div class="price-item">\n                            <span class="label">目标价</span>\n                            <span class="value">¥{target_price}</span>\n                        </div>\n                        <div class="price-item">\n                            <span class="label">止损价</span>\n                            <span class="value">¥{stop_price}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">预期收益: {expected_return}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon orange">\n                        <i class="icon">🛡️</i>\n                    </div>\n                    <h3>风险评估</h3>\n                    <div class="risk-levels">\n                        <div class="risk-item">\n                            <span class="label">风险级别</span>\n                            <span class="value">{risk_level}</span>\n                        </div>\n                        <div class="risk-item">\n                            <span class="label">信心级别</span>\n                            <span class="value">{confidence_level}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">{strategy_period}</div>\n                </div>\n            </div>\n        '

    def _get_neomorphism_css(self) -> str:
        """Get the enhanced neomorphism CSS styles for the report."""
        return "\n        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');\n        \n        * {\n            margin: 0;\n            padding: 0;\n            box-sizing: border-box;\n        }\n        \n        body {\n            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;\n            line-height: 1.6;\n            color: #2d3748;\n            background: #e0e5ec;\n            min-height: 100vh;\n        }\n        \n        .container {\n            max-width: 1200px;\n            margin: 0 auto;\n            padding: 40px 20px;\n        }\n        \n        /* Main Header Styles - Like Reference Image */\n        .main-header {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 60px 40px;\n            margin-bottom: 30px;\n            box-shadow: 20px 20px 60px #bebebe, -20px -20px 60px #ffffff;\n            text-align: center;\n        }\n        \n        .main-title {\n            font-size: 3rem;\n            font-weight: 800;\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            -webkit-background-clip: text;\n            -webkit-text-fill-color: transparent;\n            background-clip: text;\n            margin-bottom: 15px;\n        }\n        \n        .main-subtitle {\n            font-size: 1.2rem;\n            color: #64748b;\n            font-weight: 500;\n            margin-bottom: 40px;\n        }\n        \n        .header-info-cards {\n            display: flex;\n            justify-content: center;\n            gap: 30px;\n            flex-wrap: wrap;\n        }\n        \n        .info-card {\n            display: flex;\n            align-items: center;\n            gap: 10px;\n            background: #e0e5ec;\n            padding: 15px 25px;\n            border-radius: 15px;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .info-card:hover {\n            transform: translateY(-2px);\n            box-shadow: 12px 12px 24px #bebebe, -12px -12px 24px #ffffff;\n        }\n        \n        .info-icon {\n            font-size: 1.2rem;\n        }\n        \n        .info-card span {\n            font-weight: 600;\n            color: #2d3748;\n            font-size: 0.9rem;\n        }\n        \n        /* Analysis Summary - Like Reference Image */\n        .analysis-summary {\n            display: grid;\n            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));\n            gap: 30px;\n            margin-bottom: 30px;\n        }\n        \n        .summary-card {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            box-shadow: 25px 25px 75px #bebebe, -25px -25px 75px #ffffff;\n            text-align: center;\n            transition: all 0.3s ease;\n        }\n        \n        .summary-card:hover {\n            transform: translateY(-5px);\n            box-shadow: 30px 30px 90px #bebebe, -30px -30px 90px #ffffff;\n        }\n        \n        .card-icon {\n            width: 80px;\n            height: 80px;\n            border-radius: 20px;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n            margin: 0 auto 20px auto;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n        }\n        \n        .card-icon.green {\n            background: linear-gradient(135deg, #10b981, #059669);\n        }\n        \n        .card-icon.blue {\n            background: linear-gradient(135deg, #3b82f6, #1d4ed8);\n        }\n        \n        .card-icon.orange {\n            background: linear-gradient(135deg, #f59e0b, #d97706);\n        }\n        \n        .card-icon .icon {\n            font-size: 2.5rem;\n        }\n        \n        .summary-card h3 {\n            font-size: 1.4rem;\n            font-weight: 700;\n            color: #2d3748;\n            margin-bottom: 20px;\n        }\n        \n        .main-value {\n            font-size: 2.5rem;\n            font-weight: 800;\n            color: #10b981;\n            margin-bottom: 15px;\n        }\n        \n        .sub-text {\n            font-size: 0.9rem;\n            color: #6b7280;\n            font-weight: 500;\n            line-height: 1.4;\n        }\n        \n        .price-targets, .risk-levels {\n            display: flex;\n            justify-content: space-around;\n            gap: 20px;\n            margin: 20px 0;\n        }\n        \n        .price-item, .risk-item {\n            background: #e0e5ec;\n            padding: 15px 20px;\n            border-radius: 15px;\n            box-shadow: inset 5px 5px 10px #bebebe, inset -5px -5px 10px #ffffff;\n            text-align: center;\n            flex: 1;\n        }\n        \n        .price-item .label, .risk-item .label {\n            font-size: 0.8rem;\n            color: #6b7280;\n            font-weight: 600;\n            text-transform: uppercase;\n            letter-spacing: 0.5px;\n            margin-bottom: 8px;\n            display: block;\n        }\n        \n        .price-item .value, .risk-item .value {\n            font-size: 1.5rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        /* Chart Section Styles - Neomorphism Frames */\n        .chart-section {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            margin-bottom: 30px;\n            box-shadow: 25px 25px 75px #bebebe, -25px -25px 75px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .chart-section:hover {\n            transform: translateY(-3px);\n            box-shadow: 30px 30px 90px #bebebe, -30px -30px 90px #ffffff;\n        }\n        \n        .chart-header {\n            display: flex;\n            align-items: center;\n            gap: 12px;\n            margin-bottom: 25px;\n            padding-bottom: 15px;\n            border-bottom: 2px solid rgba(190, 190, 190, 0.2);\n        }\n        \n        .chart-icon {\n            font-size: 1.8rem;\n        }\n        \n        .chart-header h3 {\n            font-size: 1.4rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        .chart-container {\n            background: #e0e5ec;\n            border-radius: 20px;\n            padding: 20px;\n            box-shadow: inset 10px 10px 20px #bebebe, inset -10px -10px 20px #ffffff;\n            text-align: center;\n        }\n        \n        .chart-container img {\n            max-width: 100%;\n            height: auto;\n            border-radius: 15px;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n            transition: all 0.3s ease;\n        }\n        \n        .chart-container img:hover {\n            transform: scale(1.02);\n            box-shadow: 12px 12px 24px #bebebe, -12px -12px 24px #ffffff;\n        }\n        \n        /* Detail Sections */\n        .detail-section {\n            background: #e0e5ec;\n            border-radius: 25px;\n            padding: 40px;\n            margin-bottom: 30px;\n            box-shadow: 20px 20px 40px #bebebe, -20px -20px 40px #ffffff;\n        }\n        \n        .section-header {\n            display: flex;\n            align-items: center;\n            gap: 16px;\n            margin-bottom: 30px;\n            padding-bottom: 20px;\n            border-bottom: 2px solid rgba(190, 190, 190, 0.2);\n        }\n        \n        .section-icon {\n            width: 50px;\n            height: 50px;\n            border-radius: 15px;\n            background: #e0e5ec;\n            box-shadow: inset 8px 8px 16px #bebebe, inset -8px -8px 16px #ffffff;\n            display: flex;\n            align-items: center;\n            justify-content: center;\n            font-size: 1.5rem;\n        }\n        \n        .section-title {\n            font-size: 1.6rem;\n            font-weight: 700;\n            color: #2d3748;\n        }\n        \n        /* Subsections */\n        .subsection {\n            margin-bottom: 25px;\n            padding: 20px;\n            background: #e0e5ec;\n            border-radius: 15px;\n            box-shadow: inset 10px 10px 20px #bebebe, inset -10px -10px 20px #ffffff;\n        }\n        \n        .subsection-title {\n            font-size: 1.2rem;\n            font-weight: 600;\n            color: #2d3748;\n            margin-bottom: 15px;\n            display: flex;\n            align-items: center;\n            gap: 8px;\n        }\n        \n        /* Tables */\n        .table-container {\n            overflow: hidden;\n            border-radius: 15px;\n            margin: 20px 0;\n            background: #e0e5ec;\n            box-shadow: inset 5px 5px 10px #bebebe, inset -5px -5px 10px #ffffff;\n        }\n        \n        .data-table {\n            width: 100%;\n            border-collapse: collapse;\n        }\n        \n        .data-table th {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            color: white;\n            padding: 15px;\n            text-align: left;\n            font-weight: 600;\n            font-size: 0.9rem;\n            border: none;\n        }\n        \n        .data-table td {\n            padding: 15px;\n            border-bottom: 1px solid rgba(190, 190, 190, 0.2);\n            font-size: 0.9rem;\n            color: #2d3748;\n            background: #e0e5ec;\n        }\n        \n        .data-table tr:nth-child(even) td {\n            background: rgba(255, 255, 255, 0.3);\n        }\n        \n        .data-table tr:hover td {\n            background: rgba(102, 126, 234, 0.1);\n        }\n        \n        /* Scrollable table container for news and ratings */\n        .scrollable-table-container {\n            max-height: 400px;\n            overflow-y: auto;\n            overflow-x: hidden;\n            border-radius: 15px;\n            background: #e0e5ec;\n            box-shadow: inset 8px 8px 16px #bebebe, inset -8px -8px 16px #ffffff;\n            padding: 5px;\n            margin: 10px 0;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar {\n            width: 8px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-track {\n            background: #e0e5ec;\n            border-radius: 4px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-thumb {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            border-radius: 4px;\n        }\n        \n        .scrollable-table-container::-webkit-scrollbar-thumb:hover {\n            background: linear-gradient(135deg, #5a67d8, #6b46c1);\n        }\n        \n        /* Status badges */\n        .status-badge {\n            padding: 8px 16px;\n            border-radius: 20px;\n            font-size: 0.8rem;\n            font-weight: 600;\n            text-transform: uppercase;\n            letter-spacing: 0.5px;\n            display: inline-block;\n            box-shadow: 8px 8px 16px #bebebe, -8px -8px 16px #ffffff;\n        }\n        \n        .status-买入, .status-增持50股, .status-增持50100股 {\n            background: #10b981;\n            color: white;\n        }\n        \n        .status-卖出 {\n            background: #ef4444;\n            color: white;\n        }\n        \n        .status-持有 {\n            background: #f59e0b;\n            color: white;\n        }\n        \n        .risk-高 {\n            background: #ef4444;\n            color: white;\n        }\n        \n        .risk-中, .risk-中等 {\n            background: #f59e0b;\n            color: white;\n        }\n        \n        .risk-低 {\n            background: #10b981;\n            color: white;\n        }\n        \n        /* Links */\n        .news-title-link, .news-link {\n            color: #667eea;\n            text-decoration: none;\n            font-weight: 500;\n            transition: all 0.3s ease;\n        }\n        \n        .news-title-link:hover, .news-link:hover {\n            color: #5a67d8;\n            text-decoration: underline;\n        }\n        \n        /* Lists */\n        ul {\n            margin: 15px 0;\n            padding-left: 25px;\n        }\n        \n        li {\n            margin-bottom: 8px;\n            color: #2d3748;\n        }\n        \n        /* Footer */\n        .footer {\n            background: #2d3748;\n            color: white;\n            padding: 30px;\n            text-align: center;\n            border-radius: 20px;\n            margin-top: 30px;\n            box-shadow: 20px 20px 40px #bebebe, -20px -20px 40px #ffffff;\n        }\n        \n        .footer-content p {\n            margin-bottom: 8px;\n            opacity: 0.9;\n        }\n        \n        /* Responsive Design */\n        @media (max-width: 768px) {\n            .container {\n                padding: 20px 10px;\n            }\n            \n            .main-header {\n                padding: 40px 20px;\n            }\n            \n            .main-title {\n                font-size: 2.2rem;\n            }\n            \n            .header-info-cards {\n                flex-direction: column;\n                align-items: center;\n                gap: 15px;\n            }\n            \n            .info-card {\n                width: 100%;\n                max-width: 300px;\n                justify-content: center;\n            }\n            \n            .analysis-summary {\n                grid-template-columns: 1fr;\n            }\n            \n            .price-targets, .risk-levels {\n                flex-direction: column;\n                gap: 15px;\n            }\n            \n            .chart-section {\n                padding: 25px 15px;\n            }\n        }\n        \n        /* Animations */\n        @keyframes fadeInUp {\n            from {\n                opacity: 0;\n                transform: translateY(30px);\n            }\n            to {\n                opacity: 1;\n                transform: translateY(0);\n            }\n        }\n        \n        .detail-section, .chart-section, .analysis-summary {\n            animation: fadeInUp 0.6s ease forwards;\n        }\n        \n        /* Custom scrollbar */\n        ::-webkit-scrollbar {\n            width: 12px;\n        }\n        \n        ::-webkit-scrollbar-track {\n            background: #e0e5ec;\n            border-radius: 10px;\n        }\n        \n        ::-webkit-scrollbar-thumb {\n            background: linear-gradient(135deg, #667eea, #764ba2);\n            border-radius: 10px;\n            border: 2px solid #e0e5ec;\n        }\n        \n        ::-webkit-scrollbar-thumb:hover {\n            background: linear-gradient(135deg, #5a67d8, #6b46c1);\n        }\n        "

    def _get_section_icon(self, section_name: str) -> str:
        """Get appropriate icon for section based on name."""
        section_lower = section_name.lower()
        if '交易' in section_lower or '决策' in section_lower:
            return '💼'
        elif '市场' in section_lower or '环境' in section_lower:
            return '🌍'
        elif '技术' in section_lower or '分析' in section_lower:
            return '📈'
        elif '基本面' in section_lower or '资讯' in section_lower:
            return '📰'
        elif '风险' in section_lower or '评估' in section_lower:
            return '🛡️'
        elif '历史' in section_lower or '表现' in section_lower:
            return '📊'
        elif '投资' in section_lower or '建议' in section_lower:
            return '💡'
        else:
            return '📄'

    def _generate_charts_section(self, technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the charts section with neomorphism styling."""
        if not technical_chart_base64 and (not price_volume_chart_base64):
            return ''
        charts_html = []
        if price_volume_chart_base64:
            charts_html.append(f'\n                <div class="chart-section">\n                    <div class="chart-header">\n                        <div class="chart-icon">📊</div>\n                        <h3>K线图技术分析</h3>\n                    </div>\n                    <div class="chart-container">\n                        <img src="data:image/png;base64,{price_volume_chart_base64}" alt="K线图分析" />\n                    </div>\n                </div>\n            ')
        if technical_chart_base64:
            charts_html.append(f'\n                <div class="chart-section">\n                    <div class="chart-header">\n                        <div class="chart-icon">📈</div>\n                        <h3>技术指标综合分析</h3>\n                    </div>\n                    <div class="chart-container">\n                        <img src="data:image/png;base64,{technical_chart_base64}" alt="技术指标分析" />\n                    </div>\n                </div>\n            ')
        return ''.join(charts_html)

    def _generate_detailed_sections(self, sections, metadata: Dict[str, str]=None) -> str:
        """Generate detailed analysis sections with optimized layout."""
        sections_html = []
        section_order = ['1. 交易操作决策', '2. 市场环境分析', '3. 技术分析', '4. 基本面分析（资讯动向）', '5. 风险评估', '6. 历史表现回顾', '7. 投资建议']
        for section_key in section_order:
            if section_key in sections:
                section_data = sections[section_key]
                section_name = section_key.split('. ', 1)[1] if '. ' in section_key else section_key
                if '基本面分析' in section_name:
                    section_content = self._generate_fundamentals_section_from_csv(metadata)
                else:
                    section_content = self._generate_section_content(section_data)
                section_html = f'\n                    <div class="detail-section">\n                        <div class="section-header">\n                            <div class="section-icon">{self._get_section_icon(section_name)}</div>\n                            <h2 class="section-title">{section_name}</h2>\n                        </div>\n                        <div class="section-content">\n                            {section_content}\n                        </div>\n                    </div>\n                '
                sections_html.append(section_html)
        for section_key, section_data in sections.items():
            if section_key not in section_order:
                section_name = section_key.split('. ', 1)[1] if '. ' in section_key else section_key
                if '基本面分析' in section_name:
                    section_content = self._generate_fundamentals_section_from_csv(metadata)
                else:
                    section_content = self._generate_section_content(section_data)
                section_html = f'\n                    <div class="detail-section">\n                        <div class="section-header">\n                            <div class="section-icon">{self._get_section_icon(section_name)}</div>\n                            <h2 class="section-title">{section_name}</h2>\n                        </div>\n                        <div class="section-content">\n                            {section_content}\n                        </div>\n                    </div>\n                '
                sections_html.append(section_html)
        return ''.join(sections_html)

    def _generate_subsection(self, subsection_name: str, subsection_data: Dict[str, Any]) -> str:
        """Generate a single subsection."""
        content_parts = []
        for table in subsection_data.get('tables', []):
            content_parts.append(self._generate_table(table))
        for list_items in subsection_data.get('lists', []):
            content_parts.append(self._generate_list(list_items))
        if subsection_data.get('text'):
            content_parts.append(self._generate_text_content(subsection_data['text']))
        return f'\n        <div class="subsection">\n            <h3 class="subsection-title"><i class="fas fa-caret-right"></i> {subsection_name}</h3>\n            {''.join(content_parts)}\n        </div>\n        '

    def _generate_table(self, table_data: Dict[str, Any]) -> str:
        """Generate HTML table from table data."""
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        if not headers:
            return ''
        is_news_table = any((keyword in ' '.join(headers).lower() for keyword in ['新闻', 'news', '标题', 'title']))
        has_link_column = any((keyword in ' '.join(headers).lower() for keyword in ['链接', 'url', 'link']))
        header_html = '<tr>' + ''.join((f'<th>{header}</th>' for header in headers)) + '</tr>'
        rows_html = []
        for row in rows:
            cells_html = []
            for i, cell in enumerate(row):
                header_name = headers[i].lower()
                if any((keyword in header_name for keyword in ['决策', '操作建议', '决策类型'])):
                    cell_class = cell.replace(' ', '').replace('-', '').replace('股', '')
                    cells_html.append(f'<td><span class="status-badge status-{cell_class}">{cell}</span></td>')
                elif any((keyword in header_name for keyword in ['风险等级', '等级', '风险级别'])):
                    cells_html.append(f'<td><span class="status-badge risk-{cell}">{cell}</span></td>')
                elif is_news_table and has_link_column and any((keyword in header_name for keyword in ['新闻标题', '标题', 'title'])):
                    link_index = None
                    for j, header in enumerate(headers):
                        if any((keyword in header.lower() for keyword in ['链接', 'url', 'link'])):
                            link_index = j
                            break
                    if link_index is not None and link_index < len(row):
                        link_url = row[link_index]
                        if link_url and link_url.lower() not in ['n/a', '-', 'na', ''] and ('http://' in link_url.lower() or 'https://' in link_url.lower()):
                            cells_html.append(f'<td><a href="{link_url}" target="_blank" class="news-title-link">{cell}</a></td>')
                        else:
                            cells_html.append(f'<td>{cell}</td>')
                    else:
                        cells_html.append(f'<td>{cell}</td>')
                elif any((keyword in header_name for keyword in ['链接', 'url', 'link'])):
                    if cell and cell.lower() not in ['n/a', '-', 'na', ''] and ('http://' in cell.lower() or 'https://' in cell.lower()):
                        cells_html.append(f'<td><a href="{cell}" target="_blank" class="news-link">{cell}</a></td>')
                    else:
                        cells_html.append(f'<td>{cell}</td>')
                else:
                    cells_html.append(f'<td>{cell}</td>')
            rows_html.append('<tr>' + ''.join(cells_html) + '</tr>')
        return f'\n        <div class="table-container">\n            <table class="data-table">\n                <thead>{header_html}</thead>\n                <tbody>{''.join(rows_html)}</tbody>\n            </table>\n        </div>\n        '

    def _generate_list(self, list_items: List[str]) -> str:
        """Generate HTML list from list items."""
        items_html = ''.join((f'<li>{item}</li>' for item in list_items))
        return f'<ul style="margin: 1rem 0; padding-left: 2rem;">{items_html}</ul>'

    def _generate_text_content(self, text_lines: List[str]) -> str:
        """Generate HTML from text content."""
        filtered_lines = []
        for line in text_lines:
            if line and (not line.startswith('---')):
                line = re.sub('\\*\\*(.*?)\\*\\*', '<strong>\\1</strong>', line)
                line = re.sub('\\*(.*?)\\*', '<em>\\1</em>', line)
                filtered_lines.append(line)
        if not filtered_lines:
            return ''
        return f'<div style="margin: 1rem 0; line-height: 1.6;">{'<br>'.join(filtered_lines)}</div>'

    def _generate_section_content(self, section_data: Dict[str, Any]) -> str:
        """Generate content for a report section with subsections."""
        content_html = []
        subsections = section_data.get('subsections', {})
        for subsection_name, subsection_data in subsections.items():
            content_html.append(self._generate_subsection(subsection_name, subsection_data))
        return ''.join(content_html)

    def _generate_charts_section(self, technical_chart_base64: str, price_volume_chart_base64: str) -> str:
        """Generate the enhanced charts section exactly like reference report."""
        charts_html = []
        if price_volume_chart_base64:
            charts_html.append(f'\n        <div class="chart-section">\n            <h2 class="section-title">\n                <div class="section-icon">\n                    <i class="fas fa-chart-line"></i>\n                </div>\n                K线图技术分析\n            </h2>\n            <div class="chart-container">\n                <img src="data:image/png;base64,{price_volume_chart_base64}" alt="K线图分析" />\n            </div>\n        </div>\n            ')
        if technical_chart_base64:
            charts_html.append(f'\n        <div class="chart-section">\n            <h2 class="section-title">\n                <div class="section-icon">\n                    <i class="fas fa-chart-bar"></i>\n                </div>\n                技术指标综合分析\n            </h2>\n            <div class="chart-container">\n                <img src="data:image/png;base64,{technical_chart_base64}" alt="技术指标分析" />\n            </div>\n        </div>\n            ')
        return ''.join(charts_html)

    def _generate_footer(self, metadata: Dict[str, str]) -> str:
        """Generate the footer section."""
        return f'\n        <footer class="footer">\n            <div class="footer-content">\n                <p>报告生成时间: {metadata.get('报告生成时间', 'Unknown')}</p>\n                <p>数据来源: 股票市场数据、经济新闻、行业分析报告</p>\n                <p><strong>免责声明:</strong> 本报告仅供个人投资参考，不构成投资建议</p>\n            </div>\n        </footer>\n        '

    def _get_javascript(self) -> str:
        """Get the JavaScript for interactivity."""
        return "\n        // Intersection Observer for smooth animations\n        const observerOptions = {\n            threshold: 0.1,\n            rootMargin: '0px 0px -50px 0px'\n        };\n        \n        const observer = new IntersectionObserver((entries) => {\n            entries.forEach(entry => {\n                if (entry.isIntersecting) {\n                    entry.target.style.opacity = '1';\n                    entry.target.style.transform = 'translateY(0)';\n                }\n            });\n        }, observerOptions);\n        \n        // Initialize when DOM is ready\n        document.addEventListener('DOMContentLoaded', () => {\n            // Observe all sections for animations\n            const sections = document.querySelectorAll('.detail-section, .chart-section, .analysis-summary');\n            sections.forEach(section => {\n                observer.observe(section);\n            });\n            \n            // Add hover effects to tables\n            const tables = document.querySelectorAll('.data-table');\n            tables.forEach(table => {\n                const rows = table.querySelectorAll('tbody tr');\n                rows.forEach(row => {\n                    row.addEventListener('mouseenter', () => {\n                        row.style.transform = 'scale(1.01)';\n                        row.style.transition = 'transform 0.2s ease';\n                    });\n                    row.addEventListener('mouseleave', () => {\n                        row.style.transform = 'scale(1)';\n                    });\n                });\n            });\n            \n            // Add smooth hover effects to cards\n            const cards = document.querySelectorAll('.info-card, .summary-card');\n            cards.forEach(card => {\n                card.addEventListener('mouseenter', () => {\n                    card.style.transition = 'all 0.3s ease';\n                });\n            });\n        });\n        "

def _generate_dashboard_overview(self, sections: Dict[str, Any], metadata: Dict[str, str]) -> str:
    """Generate a dashboard overview with key metrics extracted from actual report data."""
    investment_advice = '持有'
    investment_reason = '基于技术分析和基本面评估的专业建议'
    risk_level = '中等'
    confidence_level = '中等'
    target_price = '285'
    stop_price = '270'
    expected_return = '2%'
    strategy_period = '短期持仓'
    trading_section = sections.get('一、交易操作决策', {})
    if trading_section:
        subsections = trading_section.get('subsections', {})
        core_decision = subsections.get('1.1 核心决策', {})
        if core_decision:
            tables = core_decision.get('tables', [])
            if tables and len(tables) > 0:
                rows = tables[0].get('rows', [])
                if rows and len(rows) > 0:
                    row = rows[0]
                    if len(row) >= 4:
                        investment_advice = row[1] if row[1] else investment_advice
                        investment_reason = row[2] if row[2] else investment_reason
                        risk_level = row[3] if row[3] else risk_level
        price_targets = subsections.get('1.3 价格目标', {})
        if price_targets:
            tables = price_targets.get('tables', [])
            if tables and len(tables) > 0:
                rows = tables[0].get('rows', [])
                if rows and len(rows) > 0:
                    row = rows[0]
                    if len(row) >= 4:
                        target_price = str(row[1]).replace('RMB', '').replace(' ', '') if row[1] else target_price
                        stop_price = str(row[2]).replace('RMB', '').replace(' ', '') if row[2] else stop_price
                        expected_return = str(row[3]) if row[3] else expected_return
    risk_section = sections.get('五、风险评估', {})
    if risk_section:
        subsections = risk_section.get('subsections', {})
        risk_factors = subsections.get('5.1 风险因素', {})
        if risk_factors:
            tables = risk_factors.get('tables', [])
            if tables and len(tables) > 0:
                rows = tables[0].get('rows', [])
                risk_levels = []
                for row in rows:
                    if len(row) >= 2 and row[1]:
                        risk_levels.append(row[1])
                if risk_levels:
                    high_count = risk_levels.count('高')
                    mid_count = risk_levels.count('中')
                    low_count = risk_levels.count('低')
                    if high_count > mid_count and high_count > low_count:
                        risk_level = '高'
                    elif mid_count >= high_count and mid_count >= low_count:
                        risk_level = '中等'
                    else:
                        risk_level = '低'
    advice_section = sections.get('七、投资建议', {})
    if advice_section:
        subsections = advice_section.get('subsections', {})
        short_term = subsections.get('7.1 短期操作建议', {})
        if short_term:
            text_content = short_term.get('text_content', [])
            if text_content:
                content_text = ' '.join(text_content)
                return_match = re.search('预期收益[：:]\\s*([0-9.]+%)', content_text)
                if return_match:
                    expected_return = return_match.group(1)
        long_term = subsections.get('7.2 中长期策略', {})
        if long_term:
            text_content = long_term.get('text_content', [])
            if text_content:
                content_text = ' '.join(text_content)
                period_match = re.search('持有周期[：:]\\s*([^。\\n]+)', content_text)
                if period_match:
                    period = period_match.group(1).strip()
                    if '月' in period or '年' in period:
                        strategy_period = '中长期持仓'
                    else:
                        strategy_period = '短期持仓'
    if investment_advice in ['买入', '强烈买入']:
        confidence_level = '高'
    elif investment_advice in ['卖出', '强烈卖出']:
        confidence_level = '低'
    elif investment_advice in ['部分卖出', '部分买入']:
        confidence_level = '中等'
    else:
        confidence_level = '中等'
    target_price = re.sub('[^0-9.]', '', str(target_price))
    stop_price = re.sub('[^0-9.]', '', str(stop_price))
    return f'\n            <div class="analysis-summary">\n                <div class="summary-card">\n                    <div class="card-icon green">\n                        <i class="icon">👍</i>\n                    </div>\n                    <h3>投资建议</h3>\n                    <div class="main-value">{investment_advice}</div>\n                    <div class="sub-text">{investment_reason[:50]}{('...' if len(investment_reason) > 50 else '')}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon blue">\n                        <i class="icon">🎯</i>\n                    </div>\n                    <h3>价格目标</h3>\n                    <div class="price-targets">\n                        <div class="price-item">\n                            <span class="label">目标价</span>\n                            <span class="value">¥{target_price}</span>\n                        </div>\n                        <div class="price-item">\n                            <span class="label">止损价</span>\n                            <span class="value">¥{stop_price}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">预期收益: {expected_return}</div>\n                </div>\n                \n                <div class="summary-card">\n                    <div class="card-icon orange">\n                        <i class="icon">🛡️</i>\n                    </div>\n                    <h3>风险评估</h3>\n                    <div class="risk-levels">\n                        <div class="risk-item">\n                            <span class="label">风险级别</span>\n                            <span class="value">{risk_level}</span>\n                        </div>\n                        <div class="risk-item">\n                            <span class="label">信心级别</span>\n                            <span class="value">{confidence_level}</span>\n                        </div>\n                    </div>\n                    <div class="sub-text">{strategy_period}</div>\n                </div>\n            </div>\n        '

def run_flux_image_toolkit_pipeline():
    """Pipeline: generate → edit → analyze using Flux backend (input_image editing)."""
    print('\n===== IMAGE TOOLKIT PIPELINE (GEN → EDIT → ANALYZE) =====\n')
    bfl_api_key = os.getenv('BFL_API_KEY')
    if not bfl_api_key:
        print('❌ BFL_API_KEY not found in environment variables')
        return
    flux = FluxImageGenerationToolkit(name='DemoFluxImageToolkitPipeline', api_key=bfl_api_key, save_path='./flux_generated_images')
    gen = flux.get_tool('flux_image_generation_edit')
    analyze = flux.get_tool('image_analysis') if flux.get_tool('image_analysis') else None
    gen_prompt = 'A neon-lit cyberpunk alley with rain reflections, cinematic'
    print(f'Generating: {gen_prompt}')
    gen_res = gen(prompt=gen_prompt, seed=42, output_format='jpeg', prompt_upsampling=False, safety_tolerance=2)
    if 'error' in gen_res:
        print(f'❌ Generation failed: {gen_res['error']}')
        return
    base_path = gen_res.get('file_path')
    if not base_path or not os.path.exists(base_path):
        print('❌ Generation did not return a valid file path')
        return
    print(f'Generated: {base_path}')
    try:
        import base64
        with open(base_path, 'rb') as f:
            b64_img = base64.b64encode(f.read()).decode('utf-8')
        edit_prompt = 'Add a glowing red umbrella held by a person in the foreground'
        print('Editing the generated image...')
        edit_res = gen(prompt=edit_prompt, input_image=b64_img, seed=43, output_format='jpeg', prompt_upsampling=False, safety_tolerance=2)
        if 'error' in edit_res:
            print(f'❌ Edit failed: {edit_res['error']}')
            return
        edited_path = edit_res.get('file_path')
        if not edited_path or not os.path.exists(edited_path):
            print('❌ Edit did not return a valid file path')
            return
        print(f'Edited: {edited_path}')
    except Exception as e:
        print(f'❌ Failed to edit: {e}')
    if analyze and edited_path and os.path.exists(edited_path):
        try:
            import base64, mimetypes
            with open(edited_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            mime, _ = mimetypes.guess_type(edited_path)
            mime = mime or 'image/jpeg'
            data_url = f'data:{mime};base64,{b64}'
            analysis = analyze(prompt="Summarize what's in this image in one sentence.", image_url=data_url)
            if 'error' in analysis:
                print(f'❌ Analyze failed: {analysis['error']}')
            else:
                print('✓ Analysis:')
                print(analysis.get('content', ''))
        except Exception as e:
            print(f'❌ Failed to analyze: {e}')

def create_corpus_from_context(context: List[List], corpus_id: str) -> Corpus:
    """Convert HotPotQA context into a Corpus for indexing."""
    chunks = []
    for title, sentences in context:
        for idx, sentence in enumerate(sentences):
            chunk = Chunk(chunk_id=f'{title}_{idx}', text=sentence, metadata=ChunkMetadata(doc_id=str(idx), corpus_id=corpus_id), start_char_idx=0, end_char_idx=len(sentence), excluded_embed_metadata_keys=[], excluded_llm_metadata_keys=[], relationships={})
            chunk.metadata.title = title
            chunks.append(chunk)
    return Corpus(chunks=chunks[:4], corpus_id=corpus_id)

