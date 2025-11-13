# Cluster 61

class ParamRegistry:
    """
    Central registry for all parameters that can be exposed to optimization.

    Allows dynamic binding and tracking of runtime attributes via dot-paths,
    dictionary keys, or list indices. Provides getter/setter access to all
    registered parameters for optimizers.
    """

    def __init__(self) -> None:
        """Initialize an empty registry of optimizable fields."""
        self.fields: Dict[str, OptimizableField] = {}

    def register_field(self, field: OptimizableField):
        """Manually register an OptimizableField with its alias name."""
        field.init_snapshot()
        self.fields[field.name] = field

    def get(self, name: str) -> Any:
        """Retrieve the current value of a registered field by name."""
        return self.fields[name].get()

    def get_field(self, name: str) -> OptimizableField:
        """Retrieve the OptimizableField object by name."""
        if name not in self.fields:
            raise ValueError(f"Field '{name}' is not registered.")
        else:
            return self.fields[name]

    def set(self, name: str, value: Any):
        """Set the value of a registered field by name."""
        self.fields[name].set(value)

    def names(self) -> List[str]:
        """Return a list of all registered field names (aliases)."""
        return list(self.fields.keys())

    def reset(self):
        """Roll back all registered fields to their initial values."""
        for field in self.fields.values():
            field.reset()

    def reset_field(self, name: str):
        """Roll back a registered field to its initial value."""
        self.fields[name].reset()

    def track(self, root_or_obj: Any, path_or_attr: str, *, name: str | None=None):
        """
        Register a parameter to be optimized. Supports both nested paths and direct attributes.

        Parameters:
        - root_or_obj (Any): the base object or container
        - path_or_attr (str): a path like 'prompt.template' or a direct attribute like 'template'
        - name (str | None): optional alias for this parameter

        Supported formats:
        - registry.track(program, "prompt.template")              # nested attribute
        - registry.track(program, "metadata['style']")           # dictionary key
        - registry.track(program, "components[2].prefix")        # list index
        - registry.track(program.prompt, "template")             # direct object + attribute
        - registry.track([
            (program, "prompt.template"),
            (program, "metadata['style']", "style"),
            (program.prompt, "prefix", "prompt_prefix")
          ])                                                    # batch registration
        - registry.track(program, "prompt.template").track(program, "prompt.prefix")  # chained calls
        
        - registry.track(program, "prompt_template_obj")  # register a prompt_template instance

        Returns:
        - self (PromptRegistry): for chaining
        """
        if isinstance(root_or_obj, list | tuple):
            for item in root_or_obj:
                if len(item) == 2:
                    self.track(item[0], item[1])
                elif len(item) == 3:
                    self.track(item[0], item[1], name=item[2])
            return self
        if '.' in path_or_attr or '[' in path_or_attr:
            return self._track_path(root_or_obj, path_or_attr, name)
        else:
            key = name or path_or_attr

            def getter():
                return getattr(root_or_obj, path_or_attr)

            def setter(v):
                setattr(root_or_obj, path_or_attr, v)
            field = OptimizableField(key, getter, setter)
            if key in self.fields:
                import warnings
                warnings.warn(f"Field '{key}' is already registered. Overwriting.")
            self.register_field(field)
            return self

    def _track_path(self, root: Any, path: str, name: str | None=None):
        """
        Internal helper that registers a nested field (via dot path, index, or key)
        as an OptimizableField by dynamically creating getter and setter functions.

        Parameters:
        - root (Any): the root object to start walking from
        - path (str): dot-separated path supporting list/dict access
        - name (Optional[str]): alias for the parameter (defaults to last path segment)

        Returns:
        - self
        """
        key = name if name is not None else path
        parent, leaf = self._walk(root, path)

        def getter():
            return parent[leaf] if isinstance(parent, (list, dict)) else getattr(parent, leaf)

        def setter(v):
            if isinstance(parent, (list, dict)):
                parent[leaf] = v
            else:
                setattr(parent, leaf, v)
        field = OptimizableField(key, getter, setter)
        self.register_field(field)
        return self

    def _walk(self, root, path: str):
        """
        Internal helper to resolve a dot-separated path string into its parent container
        and the leaf attribute/key/index for assignment or retrieval.

        Supports:
        - Nested attributes: e.g. "a.b.c"
        - Dict key access: e.g. "config['key']"
        - List index access: e.g. "layers[0]"

        Parameters:
        - root (Any): root object to walk from
        - path (str): path string to resolve
        - create_missing (bool): unused placeholder for future extensions

        Returns:
        - (parent, leaf): where parent[leaf] or getattr(parent, leaf) is the target
        """
        cur = root
        parts = []
        for match in _PATH_RE.finditer(path):
            attr, idx, key = match.groups()
            if attr:
                parts.append(attr)
            elif idx:
                parts.append(int(idx))
            elif key:
                parts.append(key)
        for part in parts[:-1]:
            if isinstance(part, int):
                cur = cur[part]
            else:
                cur = getattr(cur, part) if hasattr(cur, part) else cur[part]
        leaf = parts[-1]
        parent = cur
        return (parent, leaf)

    def _walk_old(self, root, path: str):
        """
        Unused Function
        Internal helper to resolve a dot-separated path string into its parent container
        and the leaf attribute/key/index for assignment or retrieval.

        Supports:
        - Nested attributes: e.g. "a.b.c"
        - Dict key access: e.g. "config['key']"
        - List index access: e.g. "layers[0]"

        Parameters:
        - root (Any): root object to walk from
        - path (str): path string to resolve
        - create_missing (bool): unused placeholder for future extensions

        Returns:
        - (parent, leaf): where parent[leaf] or getattr(parent, leaf) is the target
        """
        cur = root
        parts = path.split('.')
        for part in parts[:-1]:
            m = _INDEX_RE.match(part)
            if m:
                attr, idx = m.groups()
                cur = getattr(cur, attr) if attr else cur
                idx = idx.strip()
                if idx.startswith("'") and idx.endswith("'") or (idx.startswith('"') and idx.endswith('"')):
                    idx = idx[1:-1]
                elif idx.isdigit():
                    idx = int(idx)
                cur = cur[idx]
            else:
                cur = getattr(cur, part)
        leaf = parts[-1]
        m = _INDEX_RE.match(leaf)
        if m:
            attr, idx = m.groups()
            parent = getattr(cur, attr) if attr else cur
            idx = idx.strip()
            if idx.startswith("'") and idx.endswith("'") or (idx.startswith('"') and idx.endswith('"')):
                idx = idx[1:-1]
            elif idx.isdigit():
                idx = int(idx)
            return (parent, idx)
        return (cur, leaf)

def register_field(self, field: OptimizableField):
    """Manually register an OptimizableField with its alias name."""
    field.init_snapshot()
    self.fields[field.name] = field

