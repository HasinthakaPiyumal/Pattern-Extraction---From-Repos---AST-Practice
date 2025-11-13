# Cluster 43

class Toolkit(BaseModule):
    name: str
    tools: List[Tool]

    def get_tool_names(self) -> List[str]:
        return [tool.name for tool in self.tools]

    def get_tool_descriptions(self) -> List[str]:
        return [tool.description for tool in self.tools]

    def get_tool_inputs(self) -> List[Dict]:
        return [tool.inputs for tool in self.tools]

    def add_tool(self, tool: Tool):
        self.tools.append(tool)

    def remove_tool(self, tool_name: str):
        self.tools = [tool for tool in self.tools if tool.name != tool_name]

    def get_tool(self, tool_name: str) -> Tool:
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        raise ValueError(f"Tool '{tool_name}' not found")

    def get_tools(self) -> List[Tool]:
        return self.tools

    def get_tool_schemas(self) -> List[Dict]:
        return [tool.get_tool_schema() for tool in self.tools]

def get_tool_schemas(self) -> List[Dict]:
    return [tool.get_tool_schema() for tool in self.tools]

