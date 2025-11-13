# Cluster 97

@dataclass(frozen=True)
class S3FileContent:
    """S3 file contents."""
    filename: Optional[str] = None
    last_modified: Optional[datetime] = None
    size: Optional[int] = None

    @property
    def date_string(self) -> Optional[str]:
        """Return date string format."""
        if not self.last_modified:
            return None
        return self.last_modified.strftime('%m/%d/%Y %H:%M:%S %Z')

    @property
    def last_modified_day(self) -> Optional[str]:
        """Return last modified day."""
        if not self.last_modified:
            return None
        datetime_now = datetime.now(timezone.utc)
        difference_day = (datetime_now - self.last_modified).days
        if difference_day == 0:
            return 'Less than 24 hours'
        elif difference_day < 30:
            return f'{difference_day} days ago'
        elif 30 <= difference_day < 60:
            return 'a month ago'
        else:
            return f'{difference_day / 30} months ago'

    def kb_size(self, decimals: int=2) -> Optional[float]:
        """
        Return file size in KB.
        :param decimals: Decimal points.
        """
        if not self.size:
            return None
        return float(np.round(self.size / 1024, decimals))

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the class.
        :return A dict of object variables.
        """
        return {'filename': self.filename, 'last_modified': str(self.last_modified), 'size': self.size}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> S3FileContent:
        """
        Deserialize data to s3 file content.
        :param data: A dictionary of data.
        :return S3FileContent after loaded the data.
        """
        return S3FileContent(filename=data['filename'], last_modified=datetime.fromisoformat(data['last_modified']), size=data['size'])

@property
def last_modified_day(self) -> Optional[str]:
    """Return last modified day."""
    if not self.last_modified:
        return None
    datetime_now = datetime.now(timezone.utc)
    difference_day = (datetime_now - self.last_modified).days
    if difference_day == 0:
        return 'Less than 24 hours'
    elif difference_day < 30:
        return f'{difference_day} days ago'
    elif 30 <= difference_day < 60:
        return 'a month ago'
    else:
        return f'{difference_day / 30} months ago'

