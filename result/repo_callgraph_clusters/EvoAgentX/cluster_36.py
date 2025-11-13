# Cluster 36

class ArxivDownloadTool(Tool):
    """Tool for downloading papers from arXiv."""
    name: str = 'arxiv_download'
    description: str = 'Download PDF papers from arXiv'
    inputs: Dict[str, Dict[str, str]] = {'pdf_url': {'type': 'string', 'description': 'URL of the PDF to download'}, 'save_path': {'type': 'string', 'description': 'Local path to save the PDF file'}}
    required: Optional[List[str]] = ['pdf_url', 'save_path']

    def __init__(self, arxiv_base: ArxivBase=None, storage_handler: FileStorageHandler=None):
        super().__init__()
        self.arxiv_base = arxiv_base
        self.storage_handler = storage_handler

    def __call__(self, pdf_url: str, save_path: str) -> Dict[str, Any]:
        """
        Download a PDF from arXiv.
        
        Args:
            pdf_url: URL of the PDF
            save_path: Where to save the file
            
        Returns:
            Dictionary with download status
        """
        return self.arxiv_base.download_pdf(pdf_url, save_path, self.storage_handler)

def __call__(self, pdf_url: str, save_path: str) -> Dict[str, Any]:
    """
        Download a PDF from arXiv.
        
        Args:
            pdf_url: URL of the PDF
            save_path: Where to save the file
            
        Returns:
            Dictionary with download status
        """
    return self.arxiv_base.download_pdf(pdf_url, save_path, self.storage_handler)

