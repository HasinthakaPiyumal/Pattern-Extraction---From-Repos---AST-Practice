# Cluster 18

@dataclass
class Query:
    text: str = None
    image: str = None
    audio: str = None

    def __str__(self) -> str:
        """Override __str__ to restrict it to text, image and audio."""
        formatted = ''
        if self.text is not None:
            formatted += f"text='{self.text}' "
        if self.image is not None:
            formatted += f"image='{self.image}' "
        if self.audio is not None:
            formatted += f"audio='{self.audio}' "
        return formatted

    def __repr__(self) -> str:
        return self.__str__()

def __repr__(self) -> str:
    return self.__str__()

@dataclass
class Chunk:
    """Class for storing a piece of text and associated metadata.

    Example:

        .. code-block:: python

            from huixiangdou.primitive import Chunk

            chunk = Chunk(
                content_or_path="Hello, world!",
                metadata={"source": "https://example.com"}
            )
    """
    content_or_path: str = ''
    metadata: dict = field(default_factory=dict)
    modal: str = 'text'

    def __post_init__(self):
        if self.modal not in ['text', 'image', 'audio', 'qa']:
            raise ValueError(f'Invalid modal: {self.modal}. Allowed values are: `text`, `image`, `audio`, `qa`')

    def __str__(self) -> str:
        """Override __str__ to restrict it to content_or_path and metadata."""
        if self.metadata:
            return f"modal='{self.modal}' content_or_path='{self.content_or_path}' metadata={self.metadata}"
        else:
            return f"modal='{self.modal}' content_or_path='{self.content_or_path}'"

    def __repr__(self) -> str:
        return self.__str__()

def __repr__(self) -> str:
    return self.__str__()

