# Cluster 42

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

def test_connection(self) -> bool:
    return self.database.test_connection() if self.database else False

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

def test_connection(self) -> bool:
    """Test MongoDB connection"""
    return self.database.test_connection() if self.database else False

