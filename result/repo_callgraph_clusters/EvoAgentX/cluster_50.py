# Cluster 50

class OptimizableField:
    """Expose a concrete runtime attribute via get/set."""

    def __init__(self, name: str, getter: Callable[[], Any], setter: Callable[[Any], None]):
        self.name, self._get, self._set = (name, getter, setter)

    def get(self) -> Any:
        return self._get()

    def set(self, value: Any) -> None:
        self._set(value)

def get(self) -> Any:
    return self._get()

class OptimizableField:
    """
    Represents a parameter that can be optimized.

    This class encapsulates a runtime attribute using dynamic getter and setter
    functions. It allows the parameter to be exposed and manipulated by an external
    optimizer. An initial snapshot of the field can be stored and later used to reset
    the field to its original value.
    """

    def __init__(self, name: str, getter: Callable[[], Any], setter: Callable[[Any], None]):
        """
        Initialize an OptimizableField instance.

        Parameters
        ----------
        name : str
            The alias used to register the field in the registry.
        getter : Callable[[], Any]
            A function that returns the current value of the field.
        setter : Callable[[Any], None]
            A function that sets a new value to the field.
        """
        self.name = name
        self._get = getter
        self._set = setter
        self._initial_value = None

    def get(self) -> Any:
        """
        Retrieve the current value of the field.

        Returns
        -------
        Any
            The current value of the field.
        """
        return self._get()

    def set(self, value: Any) -> None:
        """
        Update the field with a new value.

        Parameters
        ----------
        value : Any
            The new value to assign to the field.
        """
        self._set(value)

    def init_snapshot(self) -> None:
        """
        Capture a snapshot of the current field value.

        This method stores a deep copy of the current field value so that it
        can be restored later using `reset()`.
        """
        current = self.get()
        self._initial_value = safe_deepcopy(current)

    def reset(self) -> None:
        """
        Reset the field to its initial value.

        If the current value object defines a `__reset__()` method, it will be
        called to perform the reset. Otherwise, the field is reset to the deep-copied
        initial value stored by `init_snapshot()`.

        Raises
        ------
        ValueError
            If `init_snapshot()` has not been called before `reset()`.
        """
        current = self.get()
        if self._initial_value is None:
            raise ValueError(f"Field '{self.name}' has no snapshot. Call init_snapshot() first.")
        if hasattr(current, '__reset__') and callable(current.__reset__):
            current.__reset__()
        else:
            self.set(safe_deepcopy(self._initial_value))

def get(self) -> Any:
    """
        Retrieve the current value of the field.

        Returns
        -------
        Any
            The current value of the field.
        """
    return self._get()

