# Cluster 110

@dataclass(frozen=True)
class S3TabObjectColumnConfig:
    """Config for s3 tab object column tag."""
    field: ClassVar[str] = 'object'
    title: ClassVar[str] = 'Object'
    width: ClassVar[int] = 200
    sortable: ClassVar[bool] = False
    formatter_template: ClassVar[str] = '<a href="#"><%= value %></a>'

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get configs as a dict."""
        return {'field': cls.field, 'title': cls.title, 'width': cls.width, 'sortable': cls.sortable, 'formatter': HTMLTemplateFormatter(template=cls.formatter_template)}

@classmethod
def get_config(cls) -> Dict[str, Any]:
    """Get configs as a dict."""
    return {'field': cls.field, 'title': cls.title, 'width': cls.width, 'sortable': cls.sortable, 'formatter': HTMLTemplateFormatter(template=cls.formatter_template)}

