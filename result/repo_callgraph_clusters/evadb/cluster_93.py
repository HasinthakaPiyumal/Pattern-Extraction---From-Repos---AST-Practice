# Cluster 93

def _lazy_import_loader():
    try_to_import_langchain()
    from langchain.document_loaders import CSVLoader, EverNoteLoader, PDFMinerLoader, TextLoader, UnstructuredEmailLoader, UnstructuredEPubLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader, UnstructuredPowerPointLoader, UnstructuredWordDocumentLoader
    LOADER_MAPPING = {'.doc': (UnstructuredWordDocumentLoader, {}), '.docx': (UnstructuredWordDocumentLoader, {}), '.enex': (EverNoteLoader, {}), '.eml': (UnstructuredEmailLoader, {}), '.epub': (UnstructuredEPubLoader, {}), '.html': (UnstructuredHTMLLoader, {}), '.csv': (CSVLoader, {}), '.md': (UnstructuredMarkdownLoader, {}), '.pdf': (PDFMinerLoader, {}), '.ppt': (UnstructuredPowerPointLoader, {}), '.pptx': (UnstructuredPowerPointLoader, {}), '.txt': (TextLoader, {'encoding': 'utf8'})}
    return LOADER_MAPPING

def _lazy_import_text_splitter():
    try_to_import_langchain()
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    return RecursiveCharacterTextSplitter

