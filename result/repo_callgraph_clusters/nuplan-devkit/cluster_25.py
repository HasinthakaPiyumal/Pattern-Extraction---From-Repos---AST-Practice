# Cluster 25

class Category(Base):
    """
    A category within our taxonomy. Includes both things (e.g. cars) or stuff (e.g. lanes, sidewalks).
    Subcategories are delineated by a period.
    """
    __tablename__ = 'category'
    token = Column(sql_types.HexLen8, primary_key=True)
    name = Column(String(64))
    description = Column(Text)

    @property
    def _session(self) -> Any:
        """
        Get the underlying session.
        :return: The underlying session.
        """
        return inspect(self).session

    def __repr__(self) -> str:
        """
        Return the string representation.
        :return: The string representation.
        """
        desc: str = simple_repr(self)
        return desc

    @property
    def color(self) -> Tuple[int, int, int]:
        """
        Get category color.
        :return: The category color tuple.
        """
        c: Tuple[int, int, int] = default_color(self.name)
        return c

    @property
    def color_np(self) -> npt.NDArray[np.float64]:
        """
        Get category color in numpy.
        :return: The category color in numpy.
        """
        c: npt.NDArray[np.float64] = default_color_np(self.name)
        return c

@property
def color_np(self) -> npt.NDArray[np.float64]:
    """
        Get category color in numpy.
        :return: The category color in numpy.
        """
    c: npt.NDArray[np.float64] = default_color_np(self.name)
    return c

