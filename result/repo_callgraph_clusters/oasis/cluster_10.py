# Cluster 10

def hierarchy_pos(G, root=None, width=1.0, vert_gap=0.2, vert_loc=0, xcenter=0.5):
    """
    Compute the positions of all nodes in the tree starting from a given root
    node position
    """
    pos = _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)
    return pos

def _hierarchy_pos(G, root, width=1.0, vert_gap=0.2, vert_loc=0, xcenter=0.5, pos=None, parent=None, parsed=None):
    if pos is None:
        pos = {root: (xcenter, vert_loc)}
    else:
        pos[root] = (xcenter, vert_loc)
    if parsed is None:
        parsed = {root}
    else:
        parsed.add(root)
    neighbors = list(G.neighbors(root))
    if not isinstance(G, nx.DiGraph) and parent is not None:
        neighbors.remove(parent)
    if len(neighbors) != 0:
        dx = width / len(neighbors)
        nextx = xcenter - width / 2 - dx / 2
        for neighbor in neighbors:
            nextx += dx
            pos = _hierarchy_pos(G, neighbor, width=dx, vert_gap=vert_gap, vert_loc=vert_loc - vert_gap, xcenter=nextx, pos=pos, parent=root, parsed=parsed)
    return pos

def my_function(x):
    if isinstance(x, str):
        return x.encode('utf-8', 'replace').decode('utf-8')
    return x

class SocialAgent(ChatAgent):
    """Social Agent."""

    def __init__(self, agent_id: int, user_info: UserInfo, user_info_template: TextPrompt | None=None, channel: Channel | None=None, model: Optional[Union[BaseModelBackend, List[BaseModelBackend], ModelManager]]=None, agent_graph: 'AgentGraph'=None, available_actions: list[ActionType]=None, tools: Optional[List[Union[FunctionTool, Callable]]]=None, max_iteration: int=1, interview_record: bool=False):
        self.social_agent_id = agent_id
        self.user_info = user_info
        self.channel = channel or Channel()
        self.env = SocialEnvironment(SocialAction(agent_id, self.channel))
        if user_info_template is None:
            system_message_content = self.user_info.to_system_message()
        else:
            system_message_content = self.user_info.to_custom_system_message(user_info_template)
        system_message = BaseMessage.make_assistant_message(role_name='system', content=system_message_content)
        if not available_actions:
            agent_log.info('No available actions defined, using all actions.')
            self.action_tools = self.env.action.get_openai_function_list()
        else:
            all_tools = self.env.action.get_openai_function_list()
            all_possible_actions = [tool.func.__name__ for tool in all_tools]
            for action in available_actions:
                action_name = action.value if isinstance(action, ActionType) else action
                if action_name not in all_possible_actions:
                    agent_log.warning(f'Action {action_name} is not supported. Supported actions are: {', '.join(all_possible_actions)}')
            self.action_tools = [tool for tool in all_tools if tool.func.__name__ in [a.value if isinstance(a, ActionType) else a for a in available_actions]]
        all_tools = (tools or []) + (self.action_tools or [])
        super().__init__(system_message=system_message, model=model, scheduling_strategy='random_model', tools=all_tools)
        self.max_iteration = max_iteration
        self.interview_record = interview_record
        self.agent_graph = agent_graph
        self.test_prompt = '\nHelen is a successful writer who usually writes popular western novels. Now, she has an idea for a new novel that could really make a big impact. If it works out, it could greatly improve her career. But if it fails, she will have spent a lot of time and effort for nothing.\n\nWhat do you think Helen should do?'

    async def perform_action_by_llm(self):
        env_prompt = await self.env.to_text_prompt()
        user_msg = BaseMessage.make_user_message(role_name='User', content=f"Please perform social media actions after observing the platform environments. Notice that don't limit your actions for example to just like the posts. Here is your social media environment: {env_prompt}")
        try:
            agent_log.info(f'Agent {self.social_agent_id} observing environment: {env_prompt}')
            response = await self.astep(user_msg)
            for tool_call in response.info['tool_calls']:
                action_name = tool_call.tool_name
                args = tool_call.args
                agent_log.info(f'Agent {self.social_agent_id} performed action: {action_name} with args: {args}')
                if action_name not in ALL_SOCIAL_ACTIONS:
                    agent_log.info(f'Agent {self.social_agent_id} get the result: {tool_call.result}')
                return response
        except Exception as e:
            agent_log.error(f'Agent {self.social_agent_id} error: {e}')
            return e

    async def perform_test(self):
        """
        doing group polarization test for all agents.
        TODO: rewrite the function according to the ChatAgent.
        TODO: unify the test and interview function.
        """
        _ = BaseMessage.make_user_message(role_name='User', content='You are a twitter user.')
        openai_messages, num_tokens = self.memory.get_context()
        openai_messages = [{'role': self.system_message.role_name, 'content': self.system_message.content.split('# RESPONSE FORMAT')[0]}] + openai_messages + [{'role': 'user', 'content': self.test_prompt}]
        agent_log.info(f'Agent {self.social_agent_id}: {openai_messages}')
        response = await self._aget_model_response(openai_messages=openai_messages, num_tokens=num_tokens)
        content = response.output_messages[0].content
        agent_log.info(f'Agent {self.social_agent_id} receive response: {content}')
        return {'user_id': self.social_agent_id, 'prompt': openai_messages, 'content': content}

    async def perform_interview(self, interview_prompt: str):
        """
        Perform an interview with the agent.
        """
        user_msg = BaseMessage.make_user_message(role_name='User', content='You are a twitter user.')
        if self.interview_record:
            self.update_memory(message=user_msg, role=OpenAIBackendRole.SYSTEM)
        openai_messages, num_tokens = self.memory.get_context()
        openai_messages = [{'role': self.system_message.role_name, 'content': self.system_message.content.split('# RESPONSE FORMAT')[0]}] + openai_messages + [{'role': 'user', 'content': interview_prompt}]
        agent_log.info(f'Agent {self.social_agent_id}: {openai_messages}')
        response = await self._aget_model_response(openai_messages=openai_messages, num_tokens=num_tokens)
        content = response.output_messages[0].content
        if self.interview_record:
            self.update_memory(message=response.output_messages[0], role=OpenAIBackendRole.USER)
        agent_log.info(f'Agent {self.social_agent_id} receive response: {content}')
        interview_data = {'prompt': interview_prompt, 'response': content}
        result = await self.env.action.perform_action(interview_data, ActionType.INTERVIEW.value)
        return {'user_id': self.social_agent_id, 'prompt': openai_messages, 'content': content, 'success': result.get('success', False)}

    async def perform_action_by_hci(self) -> Any:
        print('Please choose one function to perform:')
        function_list = self.env.action.get_openai_function_list()
        for i in range(len(function_list)):
            agent_log.info(f'Agent {self.social_agent_id} function: {function_list[i].func.__name__}')
        selection = int(input('Enter your choice: '))
        if not 0 <= selection < len(function_list):
            agent_log.error(f'Agent {self.social_agent_id} invalid input.')
            return
        func = function_list[selection].func
        params = inspect.signature(func).parameters
        args = []
        for param in params.values():
            while True:
                try:
                    value = input(f'Enter value for {param.name}: ')
                    args.append(value)
                    break
                except ValueError:
                    agent_log.error('Invalid input, please enter an integer.')
        result = await func(*args)
        return result

    async def perform_action_by_data(self, func_name, *args, **kwargs) -> Any:
        func_name = func_name.value if isinstance(func_name, ActionType) else func_name
        function_list = self.env.action.get_openai_function_list()
        for i in range(len(function_list)):
            if function_list[i].func.__name__ == func_name:
                func = function_list[i].func
                result = await func(*args, **kwargs)
                self.update_memory(message=BaseMessage.make_user_message(role_name=OpenAIBackendRole.SYSTEM, content=f'Agent {self.social_agent_id} performed {func_name} with args: {args} and kwargs: {kwargs}and the result is {result}'), role=OpenAIBackendRole.SYSTEM)
                agent_log.info(f'Agent {self.social_agent_id}: {result}')
                return result
        raise ValueError(f'Function {func_name} not found in the list.')

    def perform_agent_graph_action(self, action_name: str, arguments: dict[str, Any]):
        """Remove edge if action is unfollow or add edge
        if action is follow to the agent graph.
        """
        if 'unfollow' in action_name:
            followee_id: int | None = arguments.get('followee_id', None)
            if followee_id is None:
                return
            self.agent_graph.remove_edge(self.social_agent_id, followee_id)
            agent_log.info(f'Agent {self.social_agent_id} unfollowed Agent {followee_id}')
        elif 'follow' in action_name:
            followee_id: int | None = arguments.get('followee_id', None)
            if followee_id is None:
                return
            self.agent_graph.add_edge(self.social_agent_id, followee_id)
            agent_log.info(f'Agent {self.social_agent_id} followed Agent {followee_id}')

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(agent_id={self.social_agent_id}, model_type={self.model_type.value})'

def __init__(self, agent_id: int, user_info: UserInfo, user_info_template: TextPrompt | None=None, channel: Channel | None=None, model: Optional[Union[BaseModelBackend, List[BaseModelBackend], ModelManager]]=None, agent_graph: 'AgentGraph'=None, available_actions: list[ActionType]=None, tools: Optional[List[Union[FunctionTool, Callable]]]=None, max_iteration: int=1, interview_record: bool=False):
    self.social_agent_id = agent_id
    self.user_info = user_info
    self.channel = channel or Channel()
    self.env = SocialEnvironment(SocialAction(agent_id, self.channel))
    if user_info_template is None:
        system_message_content = self.user_info.to_system_message()
    else:
        system_message_content = self.user_info.to_custom_system_message(user_info_template)
    system_message = BaseMessage.make_assistant_message(role_name='system', content=system_message_content)
    if not available_actions:
        agent_log.info('No available actions defined, using all actions.')
        self.action_tools = self.env.action.get_openai_function_list()
    else:
        all_tools = self.env.action.get_openai_function_list()
        all_possible_actions = [tool.func.__name__ for tool in all_tools]
        for action in available_actions:
            action_name = action.value if isinstance(action, ActionType) else action
            if action_name not in all_possible_actions:
                agent_log.warning(f'Action {action_name} is not supported. Supported actions are: {', '.join(all_possible_actions)}')
        self.action_tools = [tool for tool in all_tools if tool.func.__name__ in [a.value if isinstance(a, ActionType) else a for a in available_actions]]
    all_tools = (tools or []) + (self.action_tools or [])
    super().__init__(system_message=system_message, model=model, scheduling_strategy='random_model', tools=all_tools)
    self.max_iteration = max_iteration
    self.interview_record = interview_record
    self.agent_graph = agent_graph
    self.test_prompt = '\nHelen is a successful writer who usually writes popular western novels. Now, she has an idea for a new novel that could really make a big impact. If it works out, it could greatly improve her career. But if it fails, she will have spent a lot of time and effort for nothing.\n\nWhat do you think Helen should do?'

class Platform:
    """Platform."""

    def __init__(self, db_path: str, channel: Any=None, sandbox_clock: Clock | None=None, start_time: datetime | None=None, show_score: bool=False, allow_self_rating: bool=True, recsys_type: str | RecsysType='reddit', refresh_rec_post_count: int=1, max_rec_post_len: int=2, following_post_count=3, use_openai_embedding: bool=False):
        self.db_path = db_path
        self.recsys_type = recsys_type
        if sandbox_clock is None:
            sandbox_clock = Clock(60)
        if start_time is None:
            start_time = datetime.now()
        self.start_time = start_time
        self.sandbox_clock = sandbox_clock
        self.db, self.db_cursor = create_db(self.db_path)
        self.db.execute('PRAGMA synchronous = OFF')
        self.channel = channel or Channel()
        self.recsys_type = RecsysType(recsys_type)
        self.show_score = show_score
        self.allow_self_rating = allow_self_rating
        self.refresh_rec_post_count = refresh_rec_post_count
        self.following_post_count = following_post_count
        self.max_rec_post_len = max_rec_post_len
        self.rec_prob = 0.7
        self.use_openai_embedding = use_openai_embedding
        self.trend_num_days = 7
        self.trend_top_k = 1
        self.report_threshold = 2
        self.pl_utils = PlatformUtils(self.db, self.db_cursor, self.start_time, self.sandbox_clock, self.show_score, self.recsys_type, self.report_threshold)

    async def running(self):
        while True:
            message_id, data = await self.channel.receive_from()
            agent_id, message, action = data
            action = ActionType(action)
            if action == ActionType.EXIT:
                if self.db_path == ':memory:':
                    dst = sqlite3.connect('mock.db')
                    with dst:
                        self.db.backup(dst)
                self.db_cursor.close()
                self.db.close()
                break
            action_function = getattr(self, action.value, None)
            if action_function:
                func_code = action_function.__code__
                param_names = func_code.co_varnames[:func_code.co_argcount]
                len_param_names = len(param_names)
                if len_param_names > 3:
                    raise ValueError(f'Functions with {len_param_names} parameters are not supported.')
                params = {}
                if len_param_names >= 2:
                    params['agent_id'] = agent_id
                if len_param_names == 3:
                    second_param_name = param_names[2]
                    params[second_param_name] = message
                result = await action_function(**params)
                await self.channel.send_to((message_id, agent_id, result))
            else:
                raise ValueError(f'Action {action} is not supported')

    def run(self):
        asyncio.run(self.running())

    async def sign_up(self, agent_id, user_message):
        user_name, name, bio = user_message
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_insert_query = 'INSERT INTO user (user_id, agent_id, user_name, name, bio, created_at, num_followings, num_followers) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
            self.pl_utils._execute_db_command(user_insert_query, (agent_id, agent_id, user_name, name, bio, current_time, 0, 0), commit=True)
            user_id = agent_id
            action_info = {'name': name, 'user_name': user_name, 'bio': bio}
            self.pl_utils._record_trace(user_id, ActionType.SIGNUP.value, action_info, current_time)
            return {'success': True, 'user_id': user_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def sign_up_product(self, product_id: int, product_name: str):
        try:
            product_insert_query = 'INSERT INTO product (product_id, product_name) VALUES (?, ?)'
            self.pl_utils._execute_db_command(product_insert_query, (product_id, product_name), commit=True)
            return {'success': True, 'product_id': product_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def purchase_product(self, agent_id, purchase_message):
        product_name, purchase_num = purchase_message
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        user_id = agent_id
        product_check_query = "SELECT * FROM 'product' WHERE product_name = ?"
        self.pl_utils._execute_db_command(product_check_query, (product_name,))
        check_result = self.db_cursor.fetchone()
        if not check_result:
            return {'success': False, 'error': 'No such product.'}
        else:
            product_id = check_result[0]
        product_update_query = 'UPDATE product SET sales = sales + ? WHERE product_name = ?'
        self.pl_utils._execute_db_command(product_update_query, (purchase_num, product_name), commit=True)
        action_info = {'product_name': product_name, 'purchase_num': purchase_num}
        self.pl_utils._record_trace(user_id, ActionType.PURCHASE_PRODUCT.value, action_info, current_time)
        return {'success': True, 'product_id': product_id}

    async def refresh(self, agent_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            rec_query = 'SELECT post_id FROM rec WHERE user_id = ?'
            self.pl_utils._execute_db_command(rec_query, (user_id,))
            rec_results = self.db_cursor.fetchall()
            post_ids = [row[0] for row in rec_results]
            selected_post_ids = post_ids
            if len(selected_post_ids) >= self.refresh_rec_post_count:
                selected_post_ids = random.sample(selected_post_ids, self.refresh_rec_post_count)
            if self.recsys_type != RecsysType.REDDIT:
                query_following_post = 'SELECT post.post_id, post.user_id, post.content, post.created_at, post.num_likes FROM post JOIN follow ON post.user_id = follow.followee_id WHERE follow.follower_id = ? ORDER BY post.num_likes DESC LIMIT ?'
                self.pl_utils._execute_db_command(query_following_post, (user_id, self.following_post_count))
                following_posts = self.db_cursor.fetchall()
                following_posts_ids = [row[0] for row in following_posts]
                selected_post_ids = following_posts_ids + selected_post_ids
                selected_post_ids = list(set(selected_post_ids))
            placeholders = ', '.join(('?' for _ in selected_post_ids))
            post_query = f'SELECT post_id, user_id, original_post_id, content, quote_content, created_at, num_likes, num_dislikes, num_shares FROM post WHERE post_id IN ({placeholders})'
            self.pl_utils._execute_db_command(post_query, selected_post_ids)
            results = self.db_cursor.fetchall()
            if not results:
                return {'success': False, 'message': 'No posts found.'}
            results_with_comments = self.pl_utils._add_comments_to_posts(results)
            action_info = {'posts': results_with_comments}
            self.pl_utils._record_trace(user_id, ActionType.REFRESH.value, action_info, current_time)
            return {'success': True, 'posts': results_with_comments}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def update_rec_table(self):
        twitter_log.info('Starting to refresh recommendation system cache...')
        user_table = fetch_table_from_db(self.db_cursor, 'user')
        post_table = fetch_table_from_db(self.db_cursor, 'post')
        trace_table = fetch_table_from_db(self.db_cursor, 'trace')
        rec_matrix = fetch_rec_table_as_matrix(self.db_cursor)
        if self.recsys_type == RecsysType.RANDOM:
            new_rec_matrix = rec_sys_random(post_table, rec_matrix, self.max_rec_post_len)
        elif self.recsys_type == RecsysType.TWITTER:
            new_rec_matrix = rec_sys_personalized_with_trace(user_table, post_table, trace_table, rec_matrix, self.max_rec_post_len)
        elif self.recsys_type == RecsysType.TWHIN:
            try:
                latest_post_time = post_table[-1]['created_at']
                second_latest_post_time = post_table[-2]['created_at'] if len(post_table) > 1 else latest_post_time
                post_query = '\n                    SELECT COUNT(*)\n                    FROM post\n                    WHERE created_at = ? OR created_at = ?\n                '
                self.pl_utils._execute_db_command(post_query, (latest_post_time, second_latest_post_time))
                result = self.db_cursor.fetchone()
                latest_post_count = result[0]
                if not latest_post_count:
                    return {'success': False, 'message': 'Fail to get latest posts count'}
                new_rec_matrix = rec_sys_personalized_twh(user_table, post_table, latest_post_count, trace_table, rec_matrix, self.max_rec_post_len, self.sandbox_clock.time_step, use_openai_embedding=self.use_openai_embedding)
            except Exception as e:
                twitter_log.error(e)
                return
        elif self.recsys_type == RecsysType.REDDIT:
            new_rec_matrix = rec_sys_reddit(post_table, rec_matrix, self.max_rec_post_len)
        else:
            raise ValueError('Unsupported recommendation system type, please check the `RecsysType`.')
        sql_query = 'DELETE FROM rec'
        self.pl_utils._execute_db_command(sql_query, commit=True)
        insert_values = [(user_id, post_id) for user_id in range(len(new_rec_matrix)) for post_id in new_rec_matrix[user_id]]
        self.pl_utils._execute_many_db_command('INSERT INTO rec (user_id, post_id) VALUES (?, ?)', insert_values, commit=True)

    async def create_post(self, agent_id: int, content: str):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            post_insert_query = 'INSERT INTO post (user_id, content, created_at, num_likes, num_dislikes, num_shares) VALUES (?, ?, ?, ?, ?, ?)'
            self.pl_utils._execute_db_command(post_insert_query, (user_id, content, current_time, 0, 0, 0), commit=True)
            post_id = self.db_cursor.lastrowid
            action_info = {'content': content, 'post_id': post_id}
            self.pl_utils._record_trace(user_id, ActionType.CREATE_POST.value, action_info, current_time)
            return {'success': True, 'post_id': post_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def repost(self, agent_id: int, post_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            repost_check_query = "SELECT * FROM 'post' WHERE original_post_id = ? AND user_id = ?"
            self.pl_utils._execute_db_command(repost_check_query, (post_id, user_id))
            if self.db_cursor.fetchone():
                return {'success': False, 'error': 'Repost record already exists.'}
            post_type_result = self.pl_utils._get_post_type(post_id)
            post_insert_query = 'INSERT INTO post (user_id, original_post_id, created_at) VALUES (?, ?, ?)'
            update_shares_query = 'UPDATE post SET num_shares = num_shares + 1 WHERE post_id = ?'
            if not post_type_result:
                return {'success': False, 'error': 'Post not found.'}
            elif post_type_result['type'] == 'common' or post_type_result['type'] == 'quote':
                self.pl_utils._execute_db_command(post_insert_query, (user_id, post_id, current_time), commit=True)
                self.pl_utils._execute_db_command(update_shares_query, (post_id,), commit=True)
            elif post_type_result['type'] == 'repost':
                repost_check_query = "SELECT * FROM 'post' WHERE original_post_id = ? AND user_id = ?"
                self.pl_utils._execute_db_command(repost_check_query, (post_type_result['root_post_id'], user_id))
                if self.db_cursor.fetchone():
                    return {'success': False, 'error': 'Repost record already exists.'}
                self.pl_utils._execute_db_command(post_insert_query, (user_id, post_type_result['root_post_id'], current_time), commit=True)
                self.pl_utils._execute_db_command(update_shares_query, (post_type_result['root_post_id'],), commit=True)
            new_post_id = self.db_cursor.lastrowid
            action_info = {'reposted_id': post_id, 'new_post_id': new_post_id}
            self.pl_utils._record_trace(user_id, ActionType.REPOST.value, action_info, current_time)
            return {'success': True, 'post_id': new_post_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def quote_post(self, agent_id: int, quote_message: tuple):
        post_id, quote_content = quote_message
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            post_query = 'SELECT content FROM post WHERE post_id = ?'
            post_type_result = self.pl_utils._get_post_type(post_id)
            post_insert_query = 'INSERT INTO post (user_id, original_post_id, content, quote_content, created_at) VALUES (?, ?, ?, ?, ?)'
            update_shares_query = 'UPDATE post SET num_shares = num_shares + 1 WHERE post_id = ?'
            if not post_type_result:
                return {'success': False, 'error': 'Post not found.'}
            elif post_type_result['type'] == 'common':
                self.pl_utils._execute_db_command(post_query, (post_id,))
                post_content = self.db_cursor.fetchone()[0]
                self.pl_utils._execute_db_command(post_insert_query, (user_id, post_id, post_content, quote_content, current_time), commit=True)
                self.pl_utils._execute_db_command(update_shares_query, (post_id,), commit=True)
            elif post_type_result['type'] == 'repost' or post_type_result['type'] == 'quote':
                self.pl_utils._execute_db_command(post_query, (post_type_result['root_post_id'],))
                post_content = self.db_cursor.fetchone()[0]
                self.pl_utils._execute_db_command(post_insert_query, (user_id, post_type_result['root_post_id'], post_content, quote_content, current_time), commit=True)
                self.pl_utils._execute_db_command(update_shares_query, (post_type_result['root_post_id'],), commit=True)
            new_post_id = self.db_cursor.lastrowid
            action_info = {'quoted_id': post_id, 'new_post_id': new_post_id}
            self.pl_utils._record_trace(user_id, ActionType.QUOTE_POST.value, action_info, current_time)
            return {'success': True, 'post_id': new_post_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def like_post(self, agent_id: int, post_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            post_type_result = self.pl_utils._get_post_type(post_id)
            if post_type_result['type'] == 'repost':
                post_id = post_type_result['root_post_id']
            user_id = agent_id
            like_check_query = "SELECT * FROM 'like' WHERE post_id = ? AND user_id = ?"
            self.pl_utils._execute_db_command(like_check_query, (post_id, user_id))
            if self.db_cursor.fetchone():
                return {'success': False, 'error': 'Like record already exists.'}
            if self.allow_self_rating is False:
                check_result = self.pl_utils._check_self_post_rating(post_id, user_id)
                if check_result:
                    return check_result
            post_update_query = 'UPDATE post SET num_likes = num_likes + 1 WHERE post_id = ?'
            self.pl_utils._execute_db_command(post_update_query, (post_id,), commit=True)
            like_insert_query = "INSERT INTO 'like' (post_id, user_id, created_at) VALUES (?, ?, ?)"
            self.pl_utils._execute_db_command(like_insert_query, (post_id, user_id, current_time), commit=True)
            like_id = self.db_cursor.lastrowid
            action_info = {'post_id': post_id, 'like_id': like_id}
            self.pl_utils._record_trace(user_id, ActionType.LIKE_POST.value, action_info, current_time)
            return {'success': True, 'like_id': like_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def unlike_post(self, agent_id: int, post_id: int):
        try:
            post_type_result = self.pl_utils._get_post_type(post_id)
            if post_type_result['type'] == 'repost':
                post_id = post_type_result['root_post_id']
            user_id = agent_id
            like_check_query = "SELECT * FROM 'like' WHERE post_id = ? AND user_id = ?"
            self.pl_utils._execute_db_command(like_check_query, (post_id, user_id))
            result = self.db_cursor.fetchone()
            if not result:
                return {'success': False, 'error': 'Like record does not exist.'}
            like_id, _, _, _ = result
            post_update_query = 'UPDATE post SET num_likes = num_likes - 1 WHERE post_id = ?'
            self.pl_utils._execute_db_command(post_update_query, (post_id,), commit=True)
            like_delete_query = "DELETE FROM 'like' WHERE like_id = ?"
            self.pl_utils._execute_db_command(like_delete_query, (like_id,), commit=True)
            action_info = {'post_id': post_id, 'like_id': like_id}
            self.pl_utils._record_trace(user_id, ActionType.UNLIKE_POST.value, action_info)
            return {'success': True, 'like_id': like_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def dislike_post(self, agent_id: int, post_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            post_type_result = self.pl_utils._get_post_type(post_id)
            if post_type_result['type'] == 'repost':
                post_id = post_type_result['root_post_id']
            user_id = agent_id
            like_check_query = "SELECT * FROM 'dislike' WHERE post_id = ? AND user_id = ?"
            self.pl_utils._execute_db_command(like_check_query, (post_id, user_id))
            if self.db_cursor.fetchone():
                return {'success': False, 'error': 'Dislike record already exists.'}
            if self.allow_self_rating is False:
                check_result = self.pl_utils._check_self_post_rating(post_id, user_id)
                if check_result:
                    return check_result
            post_update_query = 'UPDATE post SET num_dislikes = num_dislikes + 1 WHERE post_id = ?'
            self.pl_utils._execute_db_command(post_update_query, (post_id,), commit=True)
            dislike_insert_query = "INSERT INTO 'dislike' (post_id, user_id, created_at) VALUES (?, ?, ?)"
            self.pl_utils._execute_db_command(dislike_insert_query, (post_id, user_id, current_time), commit=True)
            dislike_id = self.db_cursor.lastrowid
            action_info = {'post_id': post_id, 'dislike_id': dislike_id}
            self.pl_utils._record_trace(user_id, ActionType.DISLIKE_POST.value, action_info, current_time)
            return {'success': True, 'dislike_id': dislike_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def undo_dislike_post(self, agent_id: int, post_id: int):
        try:
            post_type_result = self.pl_utils._get_post_type(post_id)
            if post_type_result['type'] == 'repost':
                post_id = post_type_result['root_post_id']
            user_id = agent_id
            like_check_query = "SELECT * FROM 'dislike' WHERE post_id = ? AND user_id = ?"
            self.pl_utils._execute_db_command(like_check_query, (post_id, user_id))
            result = self.db_cursor.fetchone()
            if not result:
                return {'success': False, 'error': 'Dislike record does not exist.'}
            dislike_id, _, _, _ = result
            post_update_query = 'UPDATE post SET num_dislikes = num_dislikes - 1 WHERE post_id = ?'
            self.pl_utils._execute_db_command(post_update_query, (post_id,), commit=True)
            like_delete_query = "DELETE FROM 'dislike' WHERE dislike_id = ?"
            self.pl_utils._execute_db_command(like_delete_query, (dislike_id,), commit=True)
            action_info = {'post_id': post_id, 'dislike_id': dislike_id}
            self.pl_utils._record_trace(user_id, ActionType.UNDO_DISLIKE_POST.value, action_info)
            return {'success': True, 'dislike_id': dislike_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def search_posts(self, agent_id: int, query: str):
        try:
            user_id = agent_id
            sql_query = 'SELECT post_id, user_id, original_post_id, content, quote_content, created_at, num_likes, num_dislikes, num_shares FROM post WHERE content LIKE ? OR CAST(post_id AS TEXT) LIKE ? OR CAST(user_id AS TEXT) LIKE ?'
            self.pl_utils._execute_db_command(sql_query, ('%' + query + '%', '%' + query + '%', '%' + query + '%'), commit=True)
            results = self.db_cursor.fetchall()
            action_info = {'query': query}
            self.pl_utils._record_trace(user_id, ActionType.SEARCH_POSTS.value, action_info)
            if not results:
                return {'success': False, 'message': 'No posts found matching the query.'}
            results_with_comments = self.pl_utils._add_comments_to_posts(results)
            return {'success': True, 'posts': results_with_comments}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def search_user(self, agent_id: int, query: str):
        try:
            user_id = agent_id
            sql_query = 'SELECT user_id, user_name, name, bio, created_at, num_followings, num_followers FROM user WHERE user_name LIKE ? OR name LIKE ? OR bio LIKE ? OR CAST(user_id AS TEXT) LIKE ?'
            self.pl_utils._execute_db_command(sql_query, ('%' + query + '%', '%' + query + '%', '%' + query + '%', '%' + query + '%'), commit=True)
            results = self.db_cursor.fetchall()
            action_info = {'query': query}
            self.pl_utils._record_trace(user_id, ActionType.SEARCH_USER.value, action_info)
            if not results:
                return {'success': False, 'message': 'No users found matching the query.'}
            users = [{'user_id': user_id, 'user_name': user_name, 'name': name, 'bio': bio, 'created_at': created_at, 'num_followings': num_followings, 'num_followers': num_followers} for user_id, user_name, name, bio, created_at, num_followings, num_followers in results]
            return {'success': True, 'users': users}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def follow(self, agent_id: int, followee_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            follow_check_query = 'SELECT * FROM follow WHERE follower_id = ? AND followee_id = ?'
            self.pl_utils._execute_db_command(follow_check_query, (user_id, followee_id))
            if self.db_cursor.fetchone():
                return {'success': False, 'error': 'Follow record already exists.'}
            follow_insert_query = 'INSERT INTO follow (follower_id, followee_id, created_at) VALUES (?, ?, ?)'
            self.pl_utils._execute_db_command(follow_insert_query, (user_id, followee_id, current_time), commit=True)
            follow_id = self.db_cursor.lastrowid
            user_update_query1 = 'UPDATE user SET num_followings = num_followings + 1 WHERE user_id = ?'
            self.pl_utils._execute_db_command(user_update_query1, (user_id,), commit=True)
            user_update_query2 = 'UPDATE user SET num_followers = num_followers + 1 WHERE user_id = ?'
            self.pl_utils._execute_db_command(user_update_query2, (followee_id,), commit=True)
            action_info = {'follow_id': follow_id}
            self.pl_utils._record_trace(user_id, ActionType.FOLLOW.value, action_info, current_time)
            return {'success': True, 'follow_id': follow_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def unfollow(self, agent_id: int, followee_id: int):
        try:
            user_id = agent_id
            follow_check_query = 'SELECT follow_id FROM follow WHERE follower_id = ? AND followee_id = ?'
            self.pl_utils._execute_db_command(follow_check_query, (user_id, followee_id))
            follow_record = self.db_cursor.fetchone()
            if not follow_record:
                return {'success': False, 'error': 'Follow record does not exist.'}
            follow_id = follow_record[0]
            follow_delete_query = 'DELETE FROM follow WHERE follow_id = ?'
            self.pl_utils._execute_db_command(follow_delete_query, (follow_id,), commit=True)
            user_update_query1 = 'UPDATE user SET num_followings = num_followings - 1 WHERE user_id = ?'
            self.pl_utils._execute_db_command(user_update_query1, (user_id,), commit=True)
            user_update_query2 = 'UPDATE user SET num_followers = num_followers - 1 WHERE user_id = ?'
            self.pl_utils._execute_db_command(user_update_query2, (followee_id,), commit=True)
            action_info = {'followee_id': followee_id}
            self.pl_utils._record_trace(user_id, ActionType.UNFOLLOW.value, action_info)
            return {'success': True, 'follow_id': follow_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def mute(self, agent_id: int, mutee_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            mute_check_query = 'SELECT * FROM mute WHERE muter_id = ? AND mutee_id = ?'
            self.pl_utils._execute_db_command(mute_check_query, (user_id, mutee_id))
            if self.db_cursor.fetchone():
                return {'success': False, 'error': 'Mute record already exists.'}
            mute_insert_query = 'INSERT INTO mute (muter_id, mutee_id, created_at) VALUES (?, ?, ?)'
            self.pl_utils._execute_db_command(mute_insert_query, (user_id, mutee_id, current_time), commit=True)
            mute_id = self.db_cursor.lastrowid
            action_info = {'mutee_id': mutee_id}
            self.pl_utils._record_trace(user_id, ActionType.MUTE.value, action_info, current_time)
            return {'success': True, 'mute_id': mute_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def unmute(self, agent_id: int, mutee_id: int):
        try:
            user_id = agent_id
            mute_check_query = 'SELECT mute_id FROM mute WHERE muter_id = ? AND mutee_id = ?'
            self.pl_utils._execute_db_command(mute_check_query, (user_id, mutee_id))
            mute_record = self.db_cursor.fetchone()
            if not mute_record:
                return {'success': False, 'error': 'No mute record exists.'}
            mute_id = mute_record[0]
            mute_delete_query = 'DELETE FROM mute WHERE mute_id = ?'
            self.pl_utils._execute_db_command(mute_delete_query, (mute_id,), commit=True)
            action_info = {'mutee_id': mutee_id}
            self.pl_utils._record_trace(user_id, ActionType.UNMUTE.value, action_info)
            return {'success': True, 'mute_id': mute_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def trend(self, agent_id: int):
        """
        Get the top K trending posts in the last num_days days.
        """
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            if self.recsys_type == RecsysType.REDDIT:
                start_time = current_time - timedelta(days=self.trend_num_days)
            else:
                start_time = int(current_time) - self.trend_num_days * 24 * 60
            sql_query = '\n                SELECT post_id, user_id, original_post_id, content,\n                quote_content, created_at, num_likes, num_dislikes,\n                num_shares FROM post\n                WHERE created_at >= ?\n                ORDER BY num_likes DESC\n                LIMIT ?\n            '
            self.pl_utils._execute_db_command(sql_query, (start_time, self.trend_top_k), commit=True)
            results = self.db_cursor.fetchall()
            if not results:
                return {'success': False, 'message': 'No trending posts in the specified period.'}
            results_with_comments = self.pl_utils._add_comments_to_posts(results)
            action_info = {'posts': results_with_comments}
            self.pl_utils._record_trace(user_id, ActionType.TREND.value, action_info, current_time)
            return {'success': True, 'posts': results_with_comments}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def create_comment(self, agent_id: int, comment_message: tuple):
        post_id, content = comment_message
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            post_type_result = self.pl_utils._get_post_type(post_id)
            if post_type_result['type'] == 'repost':
                post_id = post_type_result['root_post_id']
            user_id = agent_id
            comment_insert_query = 'INSERT INTO comment (post_id, user_id, content, created_at) VALUES (?, ?, ?, ?)'
            self.pl_utils._execute_db_command(comment_insert_query, (post_id, user_id, content, current_time), commit=True)
            comment_id = self.db_cursor.lastrowid
            action_info = {'content': content, 'comment_id': comment_id}
            self.pl_utils._record_trace(user_id, ActionType.CREATE_COMMENT.value, action_info, current_time)
            return {'success': True, 'comment_id': comment_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def like_comment(self, agent_id: int, comment_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            like_check_query = 'SELECT * FROM comment_like WHERE comment_id = ? AND user_id = ?'
            self.pl_utils._execute_db_command(like_check_query, (comment_id, user_id))
            if self.db_cursor.fetchone():
                return {'success': False, 'error': 'Comment like record already exists.'}
            if self.allow_self_rating is False:
                check_result = self.pl_utils._check_self_comment_rating(comment_id, user_id)
                if check_result:
                    return check_result
            comment_update_query = 'UPDATE comment SET num_likes = num_likes + 1 WHERE comment_id = ?'
            self.pl_utils._execute_db_command(comment_update_query, (comment_id,), commit=True)
            like_insert_query = 'INSERT INTO comment_like (comment_id, user_id, created_at) VALUES (?, ?, ?)'
            self.pl_utils._execute_db_command(like_insert_query, (comment_id, user_id, current_time), commit=True)
            comment_like_id = self.db_cursor.lastrowid
            action_info = {'comment_id': comment_id, 'comment_like_id': comment_like_id}
            self.pl_utils._record_trace(user_id, ActionType.LIKE_COMMENT.value, action_info, current_time)
            return {'success': True, 'comment_like_id': comment_like_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def unlike_comment(self, agent_id: int, comment_id: int):
        try:
            user_id = agent_id
            like_check_query = 'SELECT * FROM comment_like WHERE comment_id = ? AND user_id = ?'
            self.pl_utils._execute_db_command(like_check_query, (comment_id, user_id))
            result = self.db_cursor.fetchone()
            if not result:
                return {'success': False, 'error': 'Comment like record does not exist.'}
            comment_like_id = result[0]
            comment_update_query = 'UPDATE comment SET num_likes = num_likes - 1 WHERE comment_id = ?'
            self.pl_utils._execute_db_command(comment_update_query, (comment_id,), commit=True)
            like_delete_query = 'DELETE FROM comment_like WHERE comment_like_id = ?'
            self.pl_utils._execute_db_command(like_delete_query, (comment_like_id,), commit=True)
            action_info = {'comment_id': comment_id, 'comment_like_id': comment_like_id}
            self.pl_utils._record_trace(user_id, ActionType.UNLIKE_COMMENT.value, action_info)
            return {'success': True, 'comment_like_id': comment_like_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def dislike_comment(self, agent_id: int, comment_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            dislike_check_query = 'SELECT * FROM comment_dislike WHERE comment_id = ? AND user_id = ?'
            self.pl_utils._execute_db_command(dislike_check_query, (comment_id, user_id))
            if self.db_cursor.fetchone():
                return {'success': False, 'error': 'Comment dislike record already exists.'}
            if self.allow_self_rating is False:
                check_result = self.pl_utils._check_self_comment_rating(comment_id, user_id)
                if check_result:
                    return check_result
            comment_update_query = 'UPDATE comment SET num_dislikes = num_dislikes + 1 WHERE comment_id = ?'
            self.pl_utils._execute_db_command(comment_update_query, (comment_id,), commit=True)
            dislike_insert_query = 'INSERT INTO comment_dislike (comment_id, user_id, created_at) VALUES (?, ?, ?)'
            self.pl_utils._execute_db_command(dislike_insert_query, (comment_id, user_id, current_time), commit=True)
            comment_dislike_id = self.db_cursor.lastrowid
            action_info = {'comment_id': comment_id, 'comment_dislike_id': comment_dislike_id}
            self.pl_utils._record_trace(user_id, ActionType.DISLIKE_COMMENT.value, action_info, current_time)
            return {'success': True, 'comment_dislike_id': comment_dislike_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def undo_dislike_comment(self, agent_id: int, comment_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            dislike_check_query = 'SELECT comment_dislike_id FROM comment_dislike WHERE comment_id = ? AND user_id = ?'
            self.pl_utils._execute_db_command(dislike_check_query, (comment_id, user_id))
            dislike_record = self.db_cursor.fetchone()
            if not dislike_record:
                return {'success': False, 'error': 'Comment dislike record does not exist.'}
            comment_dislike_id = dislike_record[0]
            dislike_delete_query = 'DELETE FROM comment_dislike WHERE comment_id = ? AND user_id = ?'
            self.pl_utils._execute_db_command(dislike_delete_query, (comment_id, user_id), commit=True)
            comment_update_query = 'UPDATE comment SET num_dislikes = num_dislikes - 1 WHERE comment_id = ?'
            self.pl_utils._execute_db_command(comment_update_query, (comment_id,), commit=True)
            action_info = {'comment_id': comment_id, 'comment_dislike_id': comment_dislike_id}
            self.pl_utils._record_trace(user_id, ActionType.UNDO_DISLIKE_COMMENT.value, action_info, current_time)
            return {'success': True, 'comment_dislike_id': comment_dislike_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def do_nothing(self, agent_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            action_info = {}
            self.pl_utils._record_trace(user_id, ActionType.DO_NOTHING.value, action_info, current_time)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def interview(self, agent_id: int, interview_data):
        """Interview an agent with the given prompt and record the response.

        Args:
            agent_id (int): The ID of the agent being interviewed.
            interview_data: Either a string (prompt only) or dict with prompt
                and response.

        Returns:
            dict: A dictionary with success status.
        """
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            if isinstance(interview_data, str):
                prompt = interview_data
                response = None
                interview_id = f'{current_time}_{user_id}'
                action_info = {'prompt': prompt, 'interview_id': interview_id}
            else:
                prompt = interview_data.get('prompt', '')
                response = interview_data.get('response', '')
                interview_id = f'{current_time}_{user_id}'
                action_info = {'prompt': prompt, 'response': response, 'interview_id': interview_id}
            self.pl_utils._record_trace(user_id, ActionType.INTERVIEW.value, action_info, current_time)
            return {'success': True, 'interview_id': interview_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def report_post(self, agent_id: int, report_message: tuple):
        post_id, report_reason = report_message
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            post_type_result = self.pl_utils._get_post_type(post_id)
            check_report_query = 'SELECT * FROM report WHERE user_id = ? AND post_id = ?'
            self.pl_utils._execute_db_command(check_report_query, (user_id, post_id))
            if self.db_cursor.fetchone():
                return {'success': False, 'error': 'Report record already exists.'}
            if not post_type_result:
                return {'success': False, 'error': 'Post not found.'}
            update_reports_query = 'UPDATE post SET num_reports = num_reports + 1 WHERE post_id = ?'
            self.pl_utils._execute_db_command(update_reports_query, (post_id,), commit=True)
            report_insert_query = 'INSERT INTO report (post_id, user_id, report_reason, created_at) VALUES (?, ?, ?, ?)'
            self.pl_utils._execute_db_command(report_insert_query, (post_id, user_id, report_reason, current_time), commit=True)
            report_id = self.db_cursor.lastrowid
            action_info = {'post_id': post_id, 'report_id': report_id}
            self.pl_utils._record_trace(user_id, ActionType.REPORT_POST.value, action_info, current_time)
            return {'success': True, 'report_id': report_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def send_to_group(self, agent_id: int, message: tuple):
        group_id, content = message
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            check_query = 'SELECT * FROM group_members WHERE group_id = ? AND agent_id = ?'
            self.pl_utils._execute_db_command(check_query, (group_id, user_id))
            if not self.db_cursor.fetchone():
                return {'success': False, 'error': 'User is not a member of this group.'}
            insert_query = '\n                INSERT INTO group_messages\n                (group_id, sender_id, content, sent_at)\n                VALUES (?, ?, ?, ?)\n            '
            self.pl_utils._execute_db_command(insert_query, (group_id, user_id, content, current_time), commit=True)
            message_id = self.db_cursor.lastrowid
            members_query = 'SELECT agent_id FROM group_members WHERE group_id = ? AND agent_id != ?'
            self.pl_utils._execute_db_command(members_query, (group_id, user_id))
            members = [row[0] for row in self.db_cursor.fetchall()]
            action_info = {'group_id': group_id, 'message_id': message_id, 'content': content}
            self.pl_utils._record_trace(user_id, ActionType.SEND_TO_GROUP.value, action_info, current_time)
            return {'success': True, 'message_id': message_id, 'to': members}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def create_group(self, agent_id: int, group_name: str):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            insert_query = '\n                INSERT INTO chat_group (name, created_at) VALUES (?, ?)\n            '
            self.pl_utils._execute_db_command(insert_query, (group_name, current_time), commit=True)
            group_id = self.db_cursor.lastrowid
            join_query = '\n                INSERT INTO group_members (group_id, agent_id, joined_at)\n                VALUES (?, ?, ?)\n            '
            self.pl_utils._execute_db_command(join_query, (group_id, user_id, current_time), commit=True)
            action_info = {'group_id': group_id, 'group_name': group_name}
            self.pl_utils._record_trace(user_id, ActionType.CREATE_GROUP.value, action_info, current_time)
            return {'success': True, 'group_id': group_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def join_group(self, agent_id: int, group_id: int):
        if self.recsys_type == RecsysType.REDDIT:
            current_time = self.sandbox_clock.time_transfer(datetime.now(), self.start_time)
        else:
            current_time = self.sandbox_clock.get_time_step()
        try:
            user_id = agent_id
            check_group_query = 'SELECT * FROM chat_group\n                WHERE group_id = ?'
            self.pl_utils._execute_db_command(check_group_query, (group_id,))
            if not self.db_cursor.fetchone():
                return {'success': False, 'error': 'Group does not exist.'}
            check_member_query = 'SELECT * FROM group_members WHERE group_id = ? AND agent_id = ?'
            self.pl_utils._execute_db_command(check_member_query, (group_id, user_id))
            if self.db_cursor.fetchone():
                return {'success': False, 'error': 'User is already in the group.'}
            join_query = '\n                INSERT INTO group_members\n                (group_id, agent_id, joined_at) VALUES (?, ?, ?)\n            '
            self.pl_utils._execute_db_command(join_query, (group_id, user_id, current_time), commit=True)
            action_info = {'group_id': group_id}
            self.pl_utils._record_trace(user_id, ActionType.JOIN_GROUP.value, action_info, current_time)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def leave_group(self, agent_id: int, group_id: int):
        try:
            user_id = agent_id
            check_query = 'SELECT * FROM group_members WHERE group_id = ? AND agent_id = ?'
            self.pl_utils._execute_db_command(check_query, (group_id, user_id))
            if not self.db_cursor.fetchone():
                return {'success': False, 'error': 'User is not a member of this group.'}
            delete_query = 'DELETE FROM group_members WHERE group_id = ? AND agent_id = ?'
            self.pl_utils._execute_db_command(delete_query, (group_id, user_id), commit=True)
            action_info = {'group_id': group_id}
            self.pl_utils._record_trace(user_id, ActionType.LEAVE_GROUP.value, action_info)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def listen_from_group(self, agent_id: int):
        try:
            query = ' SELECT * FROM chat_group '
            self.pl_utils._execute_db_command(query)
            all_groups = {}
            for row in self.db_cursor.fetchall():
                all_groups[row[0]] = row[1]
            in_query = '\n                SELECT group_id FROM group_members WHERE agent_id = ?\n            '
            self.pl_utils._execute_db_command(in_query, (agent_id,))
            joined_group_ids = [row[0] for row in self.db_cursor.fetchall()]
            messages = {}
            for group_id in joined_group_ids:
                select_query = '\n                    SELECT message_id, content, sender_id,\n                    sent_at FROM group_messages WHERE group_id = ?\n                '
                self.pl_utils._execute_db_command(select_query, (group_id,))
                messages[group_id] = [{'message_id': row[0], 'content': row[1], 'sender_id': row[2], 'sent_at': row[3]} for row in self.db_cursor.fetchall()]
            return {'success': True, 'all_groups': all_groups, 'joined_groups': joined_group_ids, 'messages': messages}
        except Exception as e:
            return {'success': False, 'error': str(e)}

def __init__(self, db_path: str, channel: Any=None, sandbox_clock: Clock | None=None, start_time: datetime | None=None, show_score: bool=False, allow_self_rating: bool=True, recsys_type: str | RecsysType='reddit', refresh_rec_post_count: int=1, max_rec_post_len: int=2, following_post_count=3, use_openai_embedding: bool=False):
    self.db_path = db_path
    self.recsys_type = recsys_type
    if sandbox_clock is None:
        sandbox_clock = Clock(60)
    if start_time is None:
        start_time = datetime.now()
    self.start_time = start_time
    self.sandbox_clock = sandbox_clock
    self.db, self.db_cursor = create_db(self.db_path)
    self.db.execute('PRAGMA synchronous = OFF')
    self.channel = channel or Channel()
    self.recsys_type = RecsysType(recsys_type)
    self.show_score = show_score
    self.allow_self_rating = allow_self_rating
    self.refresh_rec_post_count = refresh_rec_post_count
    self.following_post_count = following_post_count
    self.max_rec_post_len = max_rec_post_len
    self.rec_prob = 0.7
    self.use_openai_embedding = use_openai_embedding
    self.trend_num_days = 7
    self.trend_top_k = 1
    self.report_threshold = 2
    self.pl_utils = PlatformUtils(self.db, self.db_cursor, self.start_time, self.sandbox_clock, self.show_score, self.recsys_type, self.report_threshold)

class OasisEnv:

    def __init__(self, agent_graph: AgentGraph, platform: Union[DefaultPlatformType, Platform], database_path: str=None, semaphore: int=128) -> None:
        """Init the oasis environment.

        Args:
            agent_graph: The AgentGraph to use in the simulation.
            platform: The platform type to use. Including
                `DefaultPlatformType.TWITTER` or `DefaultPlatformType.REDDIT`.
                Or you can pass a custom `Platform` instance.
            database_path: The path to create a sqlite3 database. The file
                extension must be `.db` such as `twitter_simulation.db`.
        """
        self.agent_graph = agent_graph
        self.llm_semaphore = asyncio.Semaphore(semaphore)
        if isinstance(platform, DefaultPlatformType):
            if database_path is None:
                raise ValueError('database_path is required for DefaultPlatformType')
            self.platform = platform
            if platform == DefaultPlatformType.TWITTER:
                self.channel = Channel()
                self.platform = Platform(db_path=database_path, channel=self.channel, recsys_type='twhin-bert', refresh_rec_post_count=2, max_rec_post_len=2, following_post_count=3)
                self.platform_type = DefaultPlatformType.TWITTER
            elif platform == DefaultPlatformType.REDDIT:
                self.channel = Channel()
                self.platform = Platform(db_path=database_path, channel=self.channel, recsys_type='reddit', allow_self_rating=True, show_score=True, max_rec_post_len=100, refresh_rec_post_count=5)
                self.platform_type = DefaultPlatformType.REDDIT
            else:
                raise ValueError(f'Invalid platform: {platform}. Only DefaultPlatformType.TWITTER or DefaultPlatformType.REDDIT are supported.')
        elif isinstance(platform, Platform):
            if database_path != platform.db_path:
                env_log.warning('database_path is not the same as the platform.db_path, using the platform.db_path')
            self.platform = platform
            self.channel = platform.channel
            if platform.recsys_type == RecsysType.REDDIT:
                self.platform_type = DefaultPlatformType.REDDIT
            else:
                self.platform_type = DefaultPlatformType.TWITTER
        else:
            raise ValueError(f'Invalid platform: {platform}. You should pass a DefaultPlatformType or a Platform instance.')

    async def reset(self) -> None:
        """Start the platform and sign up the agents."""
        self.platform_task = asyncio.create_task(self.platform.running())
        self.agent_graph = await generate_custom_agents(channel=self.channel, agent_graph=self.agent_graph)

    async def _perform_llm_action(self, agent):
        """Send the request to the llm model and execute the action.
        """
        async with self.llm_semaphore:
            return await agent.perform_action_by_llm()

    async def _perform_interview_action(self, agent, interview_prompt: str):
        """Send the request to the llm model and execute the interview.
        """
        async with self.llm_semaphore:
            return await agent.perform_interview(interview_prompt)

    async def step(self, actions: dict[SocialAgent, Union[ManualAction, LLMAction, List[Union[ManualAction, LLMAction]]]]) -> None:
        """Update the recommendation system and perform the actions.

        Args:
            actions(dict[SocialAgent, Union[ManualAction, LLMAction,
                List[Union[ManualAction, LLMAction]]]]): The actions to
                perform, including the manual(pre-defined) actions and llm
                actions.
        Returns:
            None
        """
        await self.platform.update_rec_table()
        env_log.info('update rec table.')
        tasks = []
        for agent, action in actions.items():
            if isinstance(action, list):
                for single_action in action:
                    if isinstance(single_action, ManualAction):
                        if single_action.action_type == ActionType.INTERVIEW:
                            interview_prompt = single_action.action_args.get('prompt', '')
                            tasks.append(self._perform_interview_action(agent, interview_prompt))
                        else:
                            tasks.append(agent.perform_action_by_data(single_action.action_type, **single_action.action_args))
                    elif isinstance(single_action, LLMAction):
                        tasks.append(self._perform_llm_action(agent))
            elif isinstance(action, ManualAction):
                if action.action_type == ActionType.INTERVIEW:
                    interview_prompt = action.action_args.get('prompt', '')
                    tasks.append(self._perform_interview_action(agent, interview_prompt))
                else:
                    tasks.append(agent.perform_action_by_data(action.action_type, **action.action_args))
            elif isinstance(action, LLMAction):
                tasks.append(self._perform_llm_action(agent))
        await asyncio.gather(*tasks)
        env_log.info('performed all actions.')
        if self.platform_type == DefaultPlatformType.TWITTER:
            self.platform.sandbox_clock.time_step += 1

    async def close(self) -> None:
        """Stop the platform and close the environment.
        """
        await self.channel.write_to_receive_queue((None, None, ActionType.EXIT))
        await self.platform_task
        env_log.info(f'Simulation finished! Please check the results in the database: {self.platform.db_path}. Note that the trace table stored all the actions of the agents.')

def __init__(self, agent_graph: AgentGraph, platform: Union[DefaultPlatformType, Platform], database_path: str=None, semaphore: int=128) -> None:
    """Init the oasis environment.

        Args:
            agent_graph: The AgentGraph to use in the simulation.
            platform: The platform type to use. Including
                `DefaultPlatformType.TWITTER` or `DefaultPlatformType.REDDIT`.
                Or you can pass a custom `Platform` instance.
            database_path: The path to create a sqlite3 database. The file
                extension must be `.db` such as `twitter_simulation.db`.
        """
    self.agent_graph = agent_graph
    self.llm_semaphore = asyncio.Semaphore(semaphore)
    if isinstance(platform, DefaultPlatformType):
        if database_path is None:
            raise ValueError('database_path is required for DefaultPlatformType')
        self.platform = platform
        if platform == DefaultPlatformType.TWITTER:
            self.channel = Channel()
            self.platform = Platform(db_path=database_path, channel=self.channel, recsys_type='twhin-bert', refresh_rec_post_count=2, max_rec_post_len=2, following_post_count=3)
            self.platform_type = DefaultPlatformType.TWITTER
        elif platform == DefaultPlatformType.REDDIT:
            self.channel = Channel()
            self.platform = Platform(db_path=database_path, channel=self.channel, recsys_type='reddit', allow_self_rating=True, show_score=True, max_rec_post_len=100, refresh_rec_post_count=5)
            self.platform_type = DefaultPlatformType.REDDIT
        else:
            raise ValueError(f'Invalid platform: {platform}. Only DefaultPlatformType.TWITTER or DefaultPlatformType.REDDIT are supported.')
    elif isinstance(platform, Platform):
        if database_path != platform.db_path:
            env_log.warning('database_path is not the same as the platform.db_path, using the platform.db_path')
        self.platform = platform
        self.channel = platform.channel
        if platform.recsys_type == RecsysType.REDDIT:
            self.platform_type = DefaultPlatformType.REDDIT
        else:
            self.platform_type = DefaultPlatformType.TWITTER
    else:
        raise ValueError(f'Invalid platform: {platform}. You should pass a DefaultPlatformType or a Platform instance.')

