# Cluster 38

class MessageTemplates:
    """Message templates implementing the proven MassGen approach."""

    def __init__(self, **template_overrides):
        """Initialize with optional template overrides."""
        self._template_overrides = template_overrides

    def evaluation_system_message(self) -> str:
        """Standard evaluation system message for all cases."""
        if 'evaluation_system_message' in self._template_overrides:
            return str(self._template_overrides['evaluation_system_message'])
        import time
        return f'You are evaluating answers from multiple agents for final response to a message.\nDifferent agents may have different builtin tools and capabilities.\nDoes the best CURRENT ANSWER address the ORIGINAL MESSAGE well?\n\nIf YES, use the `vote` tool to record your vote and skip the `new_answer` tool.\nOtherwise, digest existing answers, combine their strengths, and do additional work to address their weaknesses,\nthen use the `new_answer` tool to record a better answer to the ORIGINAL MESSAGE.\nMake sure you actually call `vote` or `new_answer` (in tool call format).\n\n*Note*: The CURRENT TIME is **{time.strftime('%Y-%m-%d %H:%M:%S')}**.'

    def format_original_message(self, task: str) -> str:
        """Format the original message section."""
        if 'format_original_message' in self._template_overrides:
            override = self._template_overrides['format_original_message']
            if callable(override):
                return override(task)
            return str(override).format(task=task)
        return f'<ORIGINAL MESSAGE> {task} <END OF ORIGINAL MESSAGE>'

    def format_conversation_history(self, conversation_history: List[Dict[str, str]]) -> str:
        """Format conversation history for agent context."""
        if 'format_conversation_history' in self._template_overrides:
            override = self._template_overrides['format_conversation_history']
            if callable(override):
                return override(conversation_history)
            return str(override)
        if not conversation_history:
            return ''
        lines = ['<CONVERSATION_HISTORY>']
        for message in conversation_history:
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            if role == 'user':
                lines.append(f'User: {content}')
            elif role == 'assistant':
                lines.append(f'Assistant: {content}')
            elif role == 'system':
                continue
        lines.append('<END OF CONVERSATION_HISTORY>')
        return '\n'.join(lines)

    def system_message_with_context(self, conversation_history: Optional[List[Dict[str, str]]]=None) -> str:
        """Evaluation system message with conversation context awareness."""
        if 'system_message_with_context' in self._template_overrides:
            override = self._template_overrides['system_message_with_context']
            if callable(override):
                return override(conversation_history)
            return str(override)
        base_message = self.evaluation_system_message()
        if conversation_history and len(conversation_history) > 0:
            context_note = '\n\nIMPORTANT: You are responding to the latest message in an ongoing conversation. Consider the full conversation context when evaluating answers and providing your response.'
            return base_message + context_note
        return base_message

    def format_current_answers_empty(self) -> str:
        """Format current answers section when no answers exist (Case 1)."""
        if 'format_current_answers_empty' in self._template_overrides:
            return str(self._template_overrides['format_current_answers_empty'])
        return '<CURRENT ANSWERS from the agents>\n(no answers available yet)\n<END OF CURRENT ANSWERS>'

    def format_current_answers_with_summaries(self, agent_summaries: Dict[str, str]) -> str:
        """Format current answers section with agent summaries (Case 2) using anonymous agent IDs."""
        if 'format_current_answers_with_summaries' in self._template_overrides:
            override = self._template_overrides['format_current_answers_with_summaries']
            if callable(override):
                return override(agent_summaries)
        lines = ['<CURRENT ANSWERS from the agents>']
        agent_mapping = {}
        for i, agent_id in enumerate(sorted(agent_summaries.keys()), 1):
            agent_mapping[agent_id] = f'agent{i}'
        for agent_id, summary in agent_summaries.items():
            anon_id = agent_mapping[agent_id]
            lines.append(f'<{anon_id}> {summary} <end of {anon_id}>')
        lines.append('<END OF CURRENT ANSWERS>')
        return '\n'.join(lines)

    def enforcement_message(self) -> str:
        """Enforcement message for Case 3 (non-workflow responses)."""
        if 'enforcement_message' in self._template_overrides:
            return str(self._template_overrides['enforcement_message'])
        return 'Finish your work above by making a tool call of `vote` or `new_answer`. Make sure you actually call the tool.'

    def tool_error_message(self, error_msg: str) -> Dict[str, str]:
        """Create a tool role message for tool usage errors."""
        return {'role': 'tool', 'content': error_msg}

    def enforcement_user_message(self) -> Dict[str, str]:
        """Create a user role message for enforcement."""
        return {'role': 'user', 'content': self.enforcement_message()}

    def get_new_answer_tool(self) -> Dict[str, Any]:
        """Get new_answer tool definition.

        TODO: Consider extending with optional context parameters for stateful backends:
        - cwd: Working directory for Claude Code sessions
        - session_id: Backend session identifier for continuity
        - model: Model used to generate the answer
        - tools_used: List of tools actually utilized
        This would enable better context preservation in multi-iteration workflows.
        """
        if 'new_answer_tool' in self._template_overrides:
            return self._template_overrides['new_answer_tool']
        return {'type': 'function', 'function': {'name': 'new_answer', 'description': 'Provide an improved answer to the ORIGINAL MESSAGE', 'parameters': {'type': 'object', 'properties': {'content': {'type': 'string', 'description': 'Your improved answer. If any builtin tools like search or code execution were used, mention how they are used here.'}}, 'required': ['content']}}}

    def get_vote_tool(self, valid_agent_ids: Optional[List[str]]=None) -> Dict[str, Any]:
        """Get vote tool definition with anonymous agent IDs."""
        if 'vote_tool' in self._template_overrides:
            override = self._template_overrides['vote_tool']
            if callable(override):
                return override(valid_agent_ids)
            return override
        tool_def = {'type': 'function', 'function': {'name': 'vote', 'description': 'Vote for the best agent to present final answer', 'parameters': {'type': 'object', 'properties': {'agent_id': {'type': 'string', 'description': "Anonymous agent ID to vote for (e.g., 'agent1', 'agent2')"}, 'reason': {'type': 'string', 'description': 'Brief reason why this agent has the best answer'}}, 'required': ['agent_id', 'reason']}}}
        if valid_agent_ids:
            anon_agent_ids = [f'agent{i}' for i in range(1, len(valid_agent_ids) + 1)]
            tool_def['function']['parameters']['properties']['agent_id']['enum'] = anon_agent_ids
        return tool_def

    def get_standard_tools(self, valid_agent_ids: Optional[List[str]]=None) -> List[Dict[str, Any]]:
        """Get standard tools for MassGen framework."""
        return [self.get_new_answer_tool(), self.get_vote_tool(valid_agent_ids)]

    def final_presentation_system_message(self, original_system_message: Optional[str]=None, enable_image_generation: bool=False, enable_audio_generation: bool=False, has_irreversible_actions: bool=False, enable_command_execution: bool=False) -> str:
        """System message for final answer presentation by winning agent.

        Args:
            original_system_message: The agent's original system message to preserve
            enable_image_generation: Whether image generation is enabled
            enable_audio_generation: Whether audio generation is enabled
            has_irreversible_actions: Whether agent has write access to context paths (requires actual file delivery)
            enable_command_execution: Whether command execution is enabled for this agent
        """
        if 'final_presentation_system_message' in self._template_overrides:
            return str(self._template_overrides['final_presentation_system_message'])
        presentation_instructions = 'You have been selected as the winning presenter in a coordination process.\nPresent the best possible coordinated answer by combining the strengths from all participants.\n\n'
        if enable_image_generation:
            presentation_instructions += 'For image generation tasks:\n- Extract image paths from the existing answer and resolve them in the shared reference.\n- Gather all agent-produced images (ignore non-existent files).\n- MUST call the generate-image tool with these input images to synthesize one final image combining their strengths.\n- MUST save the final outputand output the saved path.\n'
        if enable_audio_generation:
            presentation_instructions += 'For audio generation tasks:\n- Extract audio paths from the existing answer and resolve them in the shared reference.\n- Gather ALL audio files produced by EVERY agent (ignore non-existent files).\n  IMPORTANT: You MUST call the generate_text_with_input_audio tool to obtain transcriptions\n  for EACH AND EVERY audio file from ALL agents - no audio should be skipped or overlooked.\n- MUST combine the strengths of all transcriptions into one final detailed transcription that captures the best elements from each.\n- MUST use the convert_text_to_audio tool to convert this final transcription to a new audio file and save it, then output the saved path.\n'
        if has_irreversible_actions:
            presentation_instructions += '### Write Access to Target Path:\n\nReminder: File Delivery Required. You should first place your final answer in your workspace. However, note your workspace is NOT the final destination. You MUST copy/write files to the Target Path using FULL ABSOLUTE PATHS. Then, clean up this Target Path by deleting any outdated or unused files. Then, you must ALWAYS verify that the Target Path contains the correct final files, as no other agents were allowed to write to this path.\n'
        if enable_command_execution:
            presentation_instructions += '### Package Dependencies:\n\nCreate a `requirements.txt` file listing all Python packages needed to run your code. This helps users reproduce your work later. Include only the packages you actually used in your solution.\n'
        if original_system_message:
            return f'{original_system_message}\n\n{presentation_instructions}'
        else:
            return presentation_instructions

    def build_case1_user_message(self, task: str) -> str:
        """Build Case 1 user message (no summaries exist)."""
        return f'{self.format_original_message(task)}\n\n{self.format_current_answers_empty()}'

    def build_case2_user_message(self, task: str, agent_summaries: Dict[str, str]) -> str:
        """Build Case 2 user message (summaries exist)."""
        return f'{self.format_original_message(task)}\n\n{self.format_current_answers_with_summaries(agent_summaries)}'

    def build_evaluation_message(self, task: str, agent_answers: Optional[Dict[str, str]]=None) -> str:
        """Build evaluation user message for any case."""
        if agent_answers:
            return self.build_case2_user_message(task, agent_answers)
        else:
            return self.build_case1_user_message(task)

    def build_coordination_context(self, current_task: str, conversation_history: Optional[List[Dict[str, str]]]=None, agent_answers: Optional[Dict[str, str]]=None) -> str:
        """Build coordination context including conversation history and current state."""
        if 'build_coordination_context' in self._template_overrides:
            override = self._template_overrides['build_coordination_context']
            if callable(override):
                return override(current_task, conversation_history, agent_answers)
            return str(override)
        context_parts = []
        if conversation_history and len(conversation_history) > 0:
            history_formatted = self.format_conversation_history(conversation_history)
            if history_formatted:
                context_parts.append(history_formatted)
                context_parts.append('')
        context_parts.append(self.format_original_message(current_task))
        context_parts.append('')
        if agent_answers:
            context_parts.append(self.format_current_answers_with_summaries(agent_answers))
        else:
            context_parts.append(self.format_current_answers_empty())
        return '\n'.join(context_parts)

    def build_initial_conversation(self, task: str, agent_summaries: Optional[Dict[str, str]]=None, valid_agent_ids: Optional[List[str]]=None, base_system_message: Optional[str]=None) -> Dict[str, Any]:
        """Build complete initial conversation for MassGen evaluation."""
        if base_system_message:
            system_message = f'{self.evaluation_system_message()}\n\n#Special Requirement\n{base_system_message}'
        else:
            system_message = self.evaluation_system_message()
        return {'system_message': system_message, 'user_message': self.build_evaluation_message(task, agent_summaries), 'tools': self.get_standard_tools(valid_agent_ids)}

    def build_conversation_with_context(self, current_task: str, conversation_history: Optional[List[Dict[str, str]]]=None, agent_summaries: Optional[Dict[str, str]]=None, valid_agent_ids: Optional[List[str]]=None, base_system_message: Optional[str]=None) -> Dict[str, Any]:
        """Build complete conversation with conversation history context for MassGen evaluation."""
        if base_system_message:
            system_message = f'{base_system_message}\n\n{self.system_message_with_context(conversation_history)}'
        else:
            system_message = self.system_message_with_context(conversation_history)
        return {'system_message': system_message, 'user_message': self.build_coordination_context(current_task, conversation_history, agent_summaries), 'tools': self.get_standard_tools(valid_agent_ids)}

    def build_final_presentation_message(self, original_task: str, vote_summary: str, all_answers: Dict[str, str], selected_agent_id: str) -> str:
        """Build final presentation message for winning agent."""
        answers_section = 'All answers provided during coordination:\n'
        for agent_id, answer in all_answers.items():
            marker = ' (YOUR ANSWER)' if agent_id == selected_agent_id else ''
            answers_section += f'\n{agent_id}{marker}: "{answer}"\n'
        return f'{self.format_original_message(original_task)}\n\nVOTING RESULTS:\n{vote_summary}\n\n{answers_section}\n\nBased on the coordination process above, present your final answer:'

    def add_enforcement_message(self, conversation_messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Add enforcement message to existing conversation (Case 3)."""
        messages = conversation_messages.copy()
        messages.append({'role': 'user', 'content': self.enforcement_message()})
        return messages

    def command_execution_system_message(self) -> str:
        """Generate concise command execution instructions when command line execution is enabled."""
        parts = ['## Command Execution']
        parts.append('You can run command line commands using the `execute_command` tool.\n')
        parts.append('If a `.venv` directory exists in your workspace, it will be automatically used.')
        return '\n'.join(parts)

    def filesystem_system_message(self, main_workspace: Optional[str]=None, temp_workspace: Optional[str]=None, context_paths: Optional[List[Dict[str, str]]]=None, previous_turns: Optional[List[Dict[str, Any]]]=None, workspace_prepopulated: bool=False, enable_image_generation: bool=False, agent_answers: Optional[Dict[str, str]]=None, enable_command_execution: bool=False) -> str:
        """Generate filesystem access instructions for agents with filesystem support.

        Args:
            main_workspace: Path to agent's main workspace
            temp_workspace: Path to shared reference workspace
            context_paths: List of context paths with permissions
            previous_turns: List of previous turn metadata
            workspace_prepopulated: Whether workspace is pre-populated
            enable_image_generation: Whether image generation is enabled
            agent_answers: Dict of agent answers (keys are agent IDs) to show workspace structure
            enable_command_execution: Whether command line execution is enabled
        """
        if 'filesystem_system_message' in self._template_overrides:
            return str(self._template_overrides['filesystem_system_message'])
        parts = ['## Filesystem Access']
        parts.append('Your working directory is set to your workspace, so all relative paths in your file operations will be resolved from there. This ensures each agent works in isolation while having access to shared references. Only include in your workspace files that should be used in your answer.\n')
        if main_workspace:
            workspace_note = f'**Your Workspace**: `{main_workspace}` - Write actual files here using file tools. All your file operations will be relative to this directory.'
            if workspace_prepopulated:
                workspace_note += " **Note**: Your workspace already contains a writable copy of the previous turn's results - you can modify or build upon these files. The original unmodified version is also available as a read-only context path if you need to reference what was originally there."
            parts.append(workspace_note)
        if temp_workspace:
            workspace_tree = f'**Shared Reference**: `{temp_workspace}` - Contains previous answers from all agents (read/execute-only)\n'
            if agent_answers:
                agent_mapping = {}
                for i, agent_id in enumerate(sorted(agent_answers.keys()), 1):
                    agent_mapping[agent_id] = f'agent{i}'
                workspace_tree += '   Available agent workspaces:\n'
                agent_items = list(agent_mapping.items())
                for idx, (agent_id, anon_id) in enumerate(agent_items):
                    is_last = idx == len(agent_items) - 1
                    prefix = '   └── ' if is_last else '   ├── '
                    workspace_tree += f'{prefix}{temp_workspace}/{anon_id}/\n'
            workspace_tree += '   - To improve upon existing answers: Copy files from Shared Reference to your workspace using `copy_file` or `copy_directory` tools, then modify them\n   - These correspond directly to the answers shown in the CURRENT ANSWERS section\n   - However, not all workspaces may have a matching answer (e.g., if an agent was in the middle of working but restarted before submitting an answer). So, it is wise to check the actual files in the Shared Reference, not rely solely on the CURRENT ANSWERS section.\n'
            parts.append(workspace_tree)
        if context_paths:
            has_target = any((p.get('will_be_writable', False) for p in context_paths))
            has_readonly_context = any((not p.get('will_be_writable', False) and p.get('permission') == 'read' for p in context_paths))
            if has_target:
                parts.append("\n**Important Context**: If the user asks about improving, fixing, debugging, or understanding an existing code/project (e.g., 'Why is this code not working?', 'Fix this bug', 'Add feature X'), they are referring to the Target Path below. First READ the existing files from that path to understand what's there, then make your changes based on that codebase. Final deliverables must end up there.\n")
            elif has_readonly_context:
                parts.append("\n**Important Context**: If the user asks about debugging or understanding an existing code/project (e.g., 'Why is this code not working?', 'Explain this bug'), they are referring to (one of) the Context Path(s) below. Read then provide analysis/explanation based on that codebase - you cannot modify it directly.\n")
            for path_config in context_paths:
                path = path_config.get('path', '')
                permission = path_config.get('permission', 'read')
                will_be_writable = path_config.get('will_be_writable', False)
                if path:
                    if permission == 'read' and will_be_writable:
                        parts.append(f'**Target Path**: `{path}` (read-only now, write access later) - This is where your changes will be delivered. Work in your workspace first, then the final presenter will place or update files DIRECTLY into `{path}` using the FULL ABSOLUTE PATH.')
                    elif permission == 'write':
                        parts.append(f'**Target Path**: `{path}` (write access) - This is where your changes must be delivered. First, ensure you place your answer in your workspace, then copy/write files DIRECTLY into `{path}` using FULL ABSOLUTE PATH (not relative paths). Files must go directly into the target path itself (e.g., `{path}/file.txt`), NOT into a `.massgen/` subdirectory within it.')
                    else:
                        parts.append(f'**Context Path**: `{path}` (read-only) - Use FULL ABSOLUTE PATH when reading.')
        if previous_turns:
            parts.append("\n**Note**: This is a multi-turn conversation. Each User/Assistant exchange in the conversation history represents one turn. The workspace from each turn is available as a read-only context path listed above (e.g., turn 1's workspace is at the path ending in `/turn_1/workspace`).")
        parts.append('\n**Task Handling Priority**: When responding to user requests, follow this priority order:\n1. **Use MCP Tools First**: If you have specialized MCP tools available, call them DIRECTLY to complete the task\n   - Save any outputs/artifacts from MCP tools to your workspace\n2. **Write Code If Needed**: If MCP tools cannot complete the task, write and execute code\n3. **Create Other Files**: Create configs, documents, or other deliverables as needed\n4. **Text Response Otherwise**: If no tools or files are needed, provide a direct text answer\n\n**Important**: Do NOT ask the user for clarification or additional input. Make reasonable assumptions and proceed with sensible defaults. You will not receive user feedback, so complete the task autonomously based on the original request.\n')
        new_answer_guidance = '\n**New Answer**: When calling `new_answer`:\n'
        if enable_command_execution:
            new_answer_guidance += '- If you executed commands (e.g., running tests), explain the results in your answer (what passed, what failed, what the output shows)\n'
        new_answer_guidance += '- If you created files, list your cwd and file paths (but do NOT paste full file contents)\n'
        new_answer_guidance += '- If providing a text response, include your analysis/explanation in the `content` field\n'
        parts.append(new_answer_guidance)
        parts.append('**Workspace Cleanup**: Before submitting your answer with `new_answer`, ensure that your workspace contains only the files relevant to your final answer.\n')
        parts.append("**Comparison Tools**: Use `compare_directories` to see differences between two directories (e.g., comparing your workspace to another agent's workspace or a previous version), or `compare_files` to see line-by-line diffs between two files. These read-only tools help you understand what changed, build upon existing work effectively, or verify solutions before voting.\n")
        parts.append("**Evaluation**: When evaluating agents' answers, do NOT base your decision solely on the answer text. Instead, read and verify the actual files in their workspaces (via Shared Reference) to ensure the work matches their claims.\n")
        if enable_command_execution:
            command_exec_message = self.command_execution_system_message()
            parts.append(f'\n{command_exec_message}')
        return '\n'.join(parts)

def get_standard_tools(self, valid_agent_ids: Optional[List[str]]=None) -> List[Dict[str, Any]]:
    """Get standard tools for MassGen framework."""
    return [self.get_new_answer_tool(), self.get_vote_tool(valid_agent_ids)]

