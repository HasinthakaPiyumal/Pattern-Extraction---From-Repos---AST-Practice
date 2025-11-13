# Cluster 32

def create_access_token(subject: str, expires_delta: Optional[timedelta]=None) -> str:
    """Create a new JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {'exp': expire, 'sub': subject}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

class ConvergenceUtils:

    def __init__(self, root_path):
        self.root_path = root_path
        self.data = None
        self.rounds = None
        self.avg_scores, self.stds = (None, None)

    def load_data(self, root_path):
        """
        Read JSON file, create a new file if it doesn't exist, then return the data.
        """
        rounds_dir = self.root_path
        result_file = os.path.join(rounds_dir, 'results.json')
        os.makedirs(rounds_dir, exist_ok=True)
        if not os.path.exists(result_file):
            with open(result_file, 'w') as file:
                json.dump([], file)
        with open(result_file, 'r') as file:
            return json.load(file)

    def process_rounds(self):
        """
        Organize data by round, return a dictionary of scores by round.
        """
        self.data = self.load_data(root_path=self.root_path)
        rounds = {}
        for entry in self.data:
            round_number = entry['round']
            score = entry['score']
            if round_number not in rounds:
                rounds[round_number] = []
            rounds[round_number].append(score)
        return rounds

    def calculate_avg_and_std(self):
        """
        Calculate average score and standard deviation for each round, return two lists: average scores and standard deviations.
        """
        self.rounds = self.process_rounds()
        sorted_rounds = sorted(self.rounds.items(), key=lambda x: x[0])
        avg_scores = []
        stds = []
        for round_number, scores in sorted_rounds:
            avg_scores.append(np.mean(scores))
            stds.append(np.std(scores))
        return (avg_scores, stds)

    def check_convergence(self, top_k=3, z=0, consecutive_rounds=5):
        """
        Check for convergence. z is the z-score corresponding to the confidence level.
        consecutive_rounds is the number of consecutive rounds that must meet the stop condition.
        """
        self.avg_scores, self.stds = self.calculate_avg_and_std()
        if len(self.avg_scores) < top_k + 1:
            return (False, None, None)
        convergence_count = 0
        previous_y = None
        sigma_y_previous = None
        for i in range(len(self.avg_scores)):
            top_k_indices = np.argsort(self.avg_scores[:i + 1])[::-1][:top_k]
            top_k_scores = [self.avg_scores[j] for j in top_k_indices]
            top_k_stds = [self.stds[j] for j in top_k_indices]
            y_current = np.mean(top_k_scores)
            sigma_y_current = np.sqrt(np.sum([s ** 2 for s in top_k_stds]) / top_k ** 2)
            if previous_y is not None:
                delta_y = y_current - previous_y
                sigma_delta_y = np.sqrt(sigma_y_current ** 2 + sigma_y_previous ** 2)
                if abs(delta_y) <= z * sigma_delta_y:
                    convergence_count += 1
                    if convergence_count >= consecutive_rounds:
                        return (True, i - consecutive_rounds + 1, i)
                else:
                    convergence_count = 0
            previous_y = y_current
            sigma_y_previous = sigma_y_current
        return (False, None, None)

    def print_results(self):
        """
        Print average score and standard deviation for all rounds.
        """
        self.avg_scores, self.stds = self.calculate_avg_and_std()
        for i, (avg_score, std) in enumerate(zip(self.avg_scores, self.stds), 1):
            logger.info(f'Round {i}: Average Score = {avg_score:.4f}, Standard Deviation = {std:.4f}')

def calculate_avg_and_std(self):
    """
        Calculate average score and standard deviation for each round, return two lists: average scores and standard deviations.
        """
    self.rounds = self.process_rounds()
    sorted_rounds = sorted(self.rounds.items(), key=lambda x: x[0])
    avg_scores = []
    stds = []
    for round_number, scores in sorted_rounds:
        avg_scores.append(np.mean(scores))
        stds.append(np.std(scores))
    return (avg_scores, stds)

class RequestBase(BaseModule):
    """
    Base class for handling HTTP requests, parsing content, and saving data.
    This class provides common functionality for web scraping and HTTP operations.
    """

    def __init__(self, timeout: int=30, max_retries: int=3, delay_between_requests: float=1.0):
        """
        Initialize the RequestBase with configuration options.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            delay_between_requests: Delay between requests in seconds
        """
        super().__init__()
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.session = requests.Session()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})

    def request(self, url: str, method: str='GET', headers: Optional[Dict[str, str]]=None, params: Optional[Dict[str, Any]]=None, data: Optional[Dict[str, Any]]=None, json_data: Optional[Dict[str, Any]]=None) -> requests.Response:
        """
        Make an HTTP request with retry logic and error handling.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Additional headers to include
            params: URL parameters
            data: Form data to send
            json_data: JSON data to send
            
        Returns:
            requests.Response object
            
        Raises:
            requests.RequestException: If request fails after all retries
        """
        if headers:
            request_headers = {**self.session.headers, **headers}
        else:
            request_headers = self.session.headers
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method=method.upper(), url=url, headers=request_headers, params=params, data=data, json=json_data, timeout=self.timeout)
                response.raise_for_status()
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_requests)
                return response
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(self.delay_between_requests * (attempt + 1))

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content using BeautifulSoup.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            BeautifulSoup object for parsing
        """
        return BeautifulSoup(html_content, 'html.parser')

    def parse_json(self, json_content: str) -> Dict[str, Any]:
        """
        Parse JSON content.
        
        Args:
            json_content: Raw JSON content
            
        Returns:
            Parsed JSON as dictionary
        """
        return json.loads(json_content)

    def extract_text(self, html_content: str, selector: Optional[str]=None) -> str:
        """
        Extract text content from HTML using html2text.
        
        Args:
            html_content: Raw HTML content
            selector: CSS selector to extract specific elements (optional)
            
        Returns:
            Extracted text content
        """
        if selector:
            soup = self.parse_html(html_content)
            elements = soup.select(selector)
            combined_html = '\n'.join([str(elem) for elem in elements])
            return self.html_converter.handle(combined_html)
        else:
            return self.html_converter.handle(html_content)

    def extract_links(self, html_content: str, base_url: str=None) -> list:
        """
        Extract all links from HTML content.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL to resolve relative links
            
        Returns:
            List of extracted URLs
        """
        soup = self.parse_html(html_content)
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if base_url and (not href.startswith(('http://', 'https://', 'mailto:', 'tel:'))):
                href = urljoin(base_url, href)
            links.append(href)
        return links

    def save_content(self, content: Union[str, Dict[str, Any], bytes], file_path: str, content_type: str='text') -> bool:
        """
        Save content to a file.
        
        Args:
            content: Content to save (string, dictionary, or bytes)
            file_path: Path where to save the file
            content_type: Type of content ('text', 'json', 'html', 'pdf', 'binary')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if content_type.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
            elif content_type.lower() in ['pdf', 'binary'] or isinstance(content, bytes):
                with open(file_path, 'wb') as f:
                    if isinstance(content, bytes):
                        f.write(content)
                    else:
                        f.write(str(content).encode('utf-8'))
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            return True
        except Exception as e:
            print(f'Error saving content to {file_path}: {e}')
            return False

    def get_page_info(self, url: str) -> Dict[str, Any]:
        """
        Get basic information about a webpage.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary containing page information
        """
        try:
            response = self.request(url)
            soup = self.parse_html(response.text)
            info = {'url': url, 'status_code': response.status_code, 'title': soup.title.string if soup.title else '', 'content_type': response.headers.get('content-type', ''), 'content_length': len(response.text), 'links_count': len(soup.find_all('a', href=True)), 'images_count': len(soup.find_all('img'))}
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                info['description'] = meta_desc.get('content', '')
            return info
        except Exception as e:
            return {'error': str(e), 'url': url}

    def request_and_process(self, url: str, method: str='GET', headers: Optional[Dict[str, str]]=None, params: Optional[Dict[str, Any]]=None, data: Optional[Dict[str, Any]]=None, json_data: Optional[Dict[str, Any]]=None, return_raw: bool=False, save_file_path: Optional[str]=None) -> Dict[str, Any]:
        """
        Make a request and process the response with comprehensive error handling.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Additional headers to include
            params: URL parameters
            data: Form data to send
            json_data: JSON data to send
            return_raw: If True, return raw HTML content, otherwise processed text
            save_file_path: Optional path to save the content
            
        Returns:
            Dictionary containing processed response data
        """
        try:
            response = self.request(url=url, method=method, headers=headers, params=params, data=data, json_data=json_data)
            content_type = response.headers.get('content-type', '').lower()
            result = {'url': url, 'method': method.upper(), 'status_code': response.status_code, 'success': True, 'content_type': content_type, 'content_length': len(response.text), 'headers': dict(response.headers)}
            if return_raw:
                result['content'] = response.text
            elif 'json' in content_type:
                try:
                    result['content'] = response.json()
                except json.JSONDecodeError:
                    result['content'] = response.text
                    result['warning'] = 'Content-Type indicates JSON but parsing failed'
            else:
                result['content'] = self.extract_text(response.text)
            if save_file_path:
                save_success = self._save_response_content(response, save_file_path, content_type)
                result['saved_to_file'] = save_file_path if save_success else None
                if not save_success:
                    result['save_warning'] = f'Failed to save content to {save_file_path}'
            return result
        except Exception as e:
            return {'url': url, 'method': method.upper(), 'error': str(e), 'success': False}

    def _save_response_content(self, response: requests.Response, file_path: str, content_type: str) -> bool:
        """
        Save response content to file with appropriate format.
        
        Args:
            response: The response object
            file_path: Path to save the file
            content_type: Content type of the response
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if 'json' in content_type:
                try:
                    json_content = response.json()
                    return self.save_content(json_content, file_path, 'json')
                except json.JSONDecodeError:
                    return self.save_content(response.text, file_path, 'text')
            elif 'html' in content_type:
                return self.save_content(response.text, file_path, 'html')
            else:
                return self.save_content(response.text, file_path, 'text')
        except Exception as e:
            print(f'Error saving response content: {e}')
            return False

    def close(self):
        """Close the session."""
        self.session.close()

def close(self):
    """Close the session."""
    self.session.close()

class EvopromptOptimizer(BaseOptimizer):
    """
    Base class for evolutionary prompt optimization algorithms.
    
    This optimizer uses evolutionary algorithms to improve prompts in multi-agent workflows.
    It supports both node-based and combination-based evolution strategies.
    """

    def __init__(self, registry: ParamRegistry, program: Callable, population_size: int, iterations: int, llm_config: OpenAILLMConfig, concurrency_limit: int=10, combination_sample_size: int=None, enable_logging: bool=True, log_dir: str=None, enable_early_stopping: bool=True, early_stopping_patience: int=3):
        """
        Initialize the EvoPrompt optimizer.

        Args:
            registry: Parameter registry for tracking prompt nodes
            program: The program/workflow to optimize
            population_size: Size of the evolution population
            iterations: Number of evolution iterations
            llm_config: Configuration for the LLM used in evolution
            concurrency_limit: Maximum concurrent API calls
            combination_sample_size: Sample size for combination evaluation
            enable_logging: Whether to enable detailed logging
            log_dir: Directory for saving logs
            enable_early_stopping: Whether to enable early stopping
            early_stopping_patience: Number of generations to wait before stopping
        """
        super().__init__(registry=registry, program=program)
        self.population_size = population_size
        self.iterations = iterations
        self.llm_config = llm_config
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.combination_sample_size = combination_sample_size
        self.enable_logging = enable_logging
        self.log_dir_base = log_dir
        self.log_dir = None
        self.enable_early_stopping = enable_early_stopping
        self.early_stopping_patience = early_stopping_patience
        self._best_score_so_far = -float('inf')
        self._generations_without_improvement = 0
        self._eval_cache = {}
        self.node_populations: Dict[str, List[str]] = {}
        self.node_scores: Dict[str, List[float]] = {}
        self.best_scores_per_gen: Dict[str, Dict[str, float]] = {}
        self.avg_scores_per_gen: Dict[str, Dict[str, float]] = {}
        self.best_combo_scores_per_gen: Dict[str, float] = {}
        self.avg_combo_scores_per_gen: Dict[str, float] = {}
        self.paraphrase_agent = CustomizeAgent(name='ParaphraseAgent', description='An agent that paraphrases a given instruction.', prompt='Task: Generate a semantically equivalent but differently worded version of the user-provided instruction.\n                    \nNow, please process the following instruction:\nInput: {instruction}\n\nPlease provide the paraphrased version in the following format:\n\n## paraphrased_instruction\n[Your paraphrased version here]', llm_config=self.llm_config, inputs=[{'name': 'instruction', 'type': 'string', 'description': 'The instruction to paraphrase.'}], outputs=[{'name': 'paraphrased_instruction', 'type': 'string', 'description': 'The paraphrased instruction.'}], parse_mode='title')

    def _setup_logging_directory(self, benchmark: BIGBenchHard):
        """
        Set up logging directory for evolution tracking.
        
        Args:
            benchmark: The benchmark instance containing task information
        """
        if not self.enable_logging or self.log_dir:
            return
        task_name = benchmark.task if hasattr(benchmark, 'task') else 'unknown_task'
        if self.log_dir_base is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            algo_name = self.__class__.__name__.replace('Optimizer', '')
            self.log_dir = f'node_evolution_logs_{algo_name}_{self.llm_config.model}_{task_name}_{timestamp}'
        else:
            self.log_dir = self.log_dir_base
        os.makedirs(self.log_dir, exist_ok=True)
        logger.info(f'Logging enabled. Log files will be saved to: {self.log_dir}')

    def _log_generation_summary(self, generation: int, operation: str='Evolution'):
        """
        Log detailed summary of each generation's population and scores.
        
        Args:
            generation: The current generation number
            operation: Type of operation (Evolution, Initial, etc.)
        """
        if not self.enable_logging:
            return
        filename = f'generation_{generation:02d}_{operation.lower()}.csv'
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Node_Name', 'Individual_ID', 'Prompt_Text', 'Fitness_Score', 'Status', 'Rank_in_Node', 'Generation', 'Timestamp'])
            timestamp = datetime.now().isoformat()
            for node_name in self.node_populations.keys():
                node_pop = self.node_populations.get(node_name, [])
                node_scores = self.node_scores.get(node_name, [])
                if not node_pop:
                    continue
                sorted_indices = sorted(range(len(node_scores)), key=lambda i: node_scores[i], reverse=True)
                for rank, idx in enumerate(sorted_indices, 1):
                    prompt = node_pop[idx]
                    score = node_scores[idx]
                    status = 'Best' if rank == 1 else 'Survivor' if rank <= self.population_size else 'Eliminated'
                    writer.writerow([node_name, f'{node_name}_{idx}', prompt[:200] + '...' if len(prompt) > 200 else prompt, f'{score:.6f}', status, rank, generation, timestamp])

    def _log_detailed_evaluation(self, generation: int, combinations: List[Dict[str, str]], combination_scores: List[float]):
        if not self.enable_logging:
            return
        filename = f'combo_evaluation_gen_{generation:02d}.csv'
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            node_names = list(combinations[0].keys()) if combinations else []
            header = ['Combination_ID', 'Average_Score']
            for node_name in node_names:
                header.append(f'{node_name}_Prompt_Preview')
            header.extend(['Generation', 'Timestamp'])
            writer.writerow(header)
            timestamp = datetime.now().isoformat()
            for combo_id, (combination, avg_score) in enumerate(zip(combinations, combination_scores)):
                try:
                    row = [f'combo_{combo_id}', f'{avg_score:.6f}']
                    for node_name in node_names:
                        prompt = combination[node_name]
                        row.append(prompt[:50] + '...' if len(prompt) > 50 else prompt)
                    row.extend([generation, timestamp])
                    writer.writerow(row)
                except Exception as e:
                    logger.error(f'Error logging evaluation for combination {combo_id}: {e}')

    def _create_single_metric_plot(self, metric_name: str, generations: List[int], best_scores: List[float], avg_scores: List[float], algorithm_name: str, plot_dir: str):
        fig, ax = plt.subplots(figsize=(12, 7))
        ax.plot(generations, best_scores, marker='o', linestyle='-', linewidth=2, markersize=8, label='Best Score')
        ax.plot(generations, avg_scores, marker='x', linestyle='--', linewidth=2, markersize=8, label='Average Score')
        title = f"Performance for '{metric_name}' ({algorithm_name})"
        ax.set_title(title, fontsize=16, weight='bold')
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Fitness Score', fontsize=12)
        ax.set_xticks(generations)
        ax.set_xticklabels([f'Gen {g}' for g in generations], rotation=45, ha='right')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        safe_metric_name = re.sub('[^a-zA-Z0-9_-]', '_', metric_name)
        filename = f'performance_plot_{safe_metric_name}.png'
        filepath = os.path.join(plot_dir, filename)
        try:
            plt.savefig(filepath, dpi=200, bbox_inches='tight')
        except Exception as e:
            logger.error(f'Failed to save individual plot for {metric_name}: {e}')
        finally:
            plt.close(fig)

    def _plot_and_save_performance_graph(self, algorithm_name: str):
        if not self.enable_logging or plt is None:
            if plt is None:
                logger.warning('Matplotlib not found, skipping plot generation.')
            return
        if not self.best_scores_per_gen and (not self.best_combo_scores_per_gen):
            logger.warning('No performance data to plot.')
            return
        plt.style.use('seaborn-v0_8-whitegrid')
        all_gen_keys = set(self.best_scores_per_gen.keys()) | set(self.best_combo_scores_per_gen.keys())
        generations = sorted([int(re.search('\\d+', gen).group()) for gen in all_gen_keys if re.search('\\d+', gen)])
        fig_combined, ax_combined = plt.subplots(figsize=(16, 9))
        if self.best_combo_scores_per_gen:
            combo_best = [self.best_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
            combo_avg = [self.avg_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
            ax_combined.plot(generations, combo_best, marker='*', linestyle='-', linewidth=2.5, markersize=10, label='Best Combination Score (Overall)')
            ax_combined.plot(generations, combo_avg, marker='D', linestyle='--', linewidth=2.5, markersize=8, label='Average Combination Score (Overall)')
        all_node_metrics = set()
        for gen_data in self.best_scores_per_gen.values():
            all_node_metrics.update(gen_data.keys())
        for metric in sorted(list(all_node_metrics)):
            best_scores = [self.best_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
            avg_scores = [self.avg_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
            ax_combined.plot(generations, best_scores, marker='o', linestyle='-', alpha=0.7, label=f'Best Score ({metric})')
            ax_combined.plot(generations, avg_scores, marker='x', linestyle='--', alpha=0.7, label=f'Average Score ({metric})')
        ax_combined.set_title(f'Overall Performance Evolution ({algorithm_name})', fontsize=18, weight='bold')
        ax_combined.set_xlabel('Generation', fontsize=14)
        ax_combined.set_ylabel('Fitness Score', fontsize=14)
        ax_combined.set_xticks(generations)
        ax_combined.set_xticklabels([f'Gen {g}' for g in generations], rotation=45, ha='right')
        handles, labels = ax_combined.get_legend_handles_labels()
        combo_indices = [i for i, label in enumerate(labels) if 'Combination' in label]
        node_indices = [i for i, label in enumerate(labels) if 'Combination' not in label]
        ax_combined.legend([handles[i] for i in combo_indices + node_indices], [labels[i] for i in combo_indices + node_indices], loc='best', fontsize=10)
        ax_combined.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        combined_filepath = os.path.join(self.log_dir, 'performance_summary_OVERALL.png')
        try:
            plt.savefig(combined_filepath, dpi=300, bbox_inches='tight')
            logger.info(f'Overall performance plot saved to: {combined_filepath}')
        except Exception as e:
            logger.error(f'Failed to save overall performance plot: {e}')
        finally:
            plt.close(fig_combined)
        individual_plot_dir = os.path.join(self.log_dir, 'individual_plots')
        os.makedirs(individual_plot_dir, exist_ok=True)
        for metric in sorted(list(all_node_metrics)):
            best_scores = [self.best_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
            avg_scores = [self.avg_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
            self._create_single_metric_plot(metric, generations, best_scores, avg_scores, algorithm_name, individual_plot_dir)
        if self.best_combo_scores_per_gen:
            combo_best = [self.best_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
            combo_avg = [self.avg_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
            self._create_single_metric_plot('Combination', generations, combo_best, combo_avg, algorithm_name, individual_plot_dir)
        logger.info(f'Individual performance plots saved to: {individual_plot_dir}')

    def _log_optimization_summary(self, algorithm_name: str, best_config: Dict[str, str], test_accuracy: float=None):
        if not self.enable_logging:
            return
        filename = f'optimization_summary_{algorithm_name.lower()}.csv'
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value', 'Timestamp'])
            timestamp = datetime.now().isoformat()
            writer.writerow(['Algorithm', algorithm_name, timestamp])
            writer.writerow(['Population_Size', self.population_size, timestamp])
            writer.writerow(['Iterations', self.iterations, timestamp])
            writer.writerow(['Combination_Sample_Size', self.combination_sample_size, timestamp])
            writer.writerow(['Early_Stopping_Enabled', self.enable_early_stopping, timestamp])
            if self.enable_early_stopping:
                writer.writerow(['Early_Stopping_Patience', self.early_stopping_patience, timestamp])
            if test_accuracy is not None:
                writer.writerow(['Final_Test_Accuracy', f'{test_accuracy:.6f}', timestamp])
            for node_name, prompt in best_config.items():
                writer.writerow([f'Best_{node_name}', prompt, timestamp])
            for gen_name in self.best_scores_per_gen.keys():
                for metric_name, best_score in self.best_scores_per_gen[gen_name].items():
                    writer.writerow([f'{gen_name}_{metric_name}_Best', f'{best_score:.6f}', timestamp])
                if gen_name in self.avg_scores_per_gen:
                    for metric_name, avg_score in self.avg_scores_per_gen[gen_name].items():
                        writer.writerow([f'{gen_name}_{metric_name}_Avg', f'{avg_score:.6f}', timestamp])
        self._plot_and_save_performance_graph(algorithm_name)
        try:
            self._save_best_config_json(best_config)
        except Exception as e:
            logger.error(f'Failed to save best_config.json: {e}')

    def _save_best_config_json(self, best_config: Dict[str, str], filename: str='best_config.json') -> None:
        """
        Save the best configuration to a JSON file in the log directory.

        This is a convenience artifact for downstream automation to reload and
        apply the optimized prompt set without parsing CSVs.

        Note: optimize() already applies the best config to the in-memory
        program. This JSON is intended for persistence and later reuse.
        """
        if not self.enable_logging:
            return
        if not self.log_dir:
            return
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(best_config, f, ensure_ascii=False, indent=2)
        logger.info(f'Best config JSON saved to: {filepath}')

    def load_and_apply_config(self, path: str) -> Dict[str, str]:
        """
        Load a JSON best_config from disk and apply it to the registered program.

        Returns the loaded configuration dictionary.
        """
        with open(path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        self.apply_cfg(cfg)
        logger.info(f'Applied configuration from JSON: {path}')
        return cfg

    async def _log_evaluation_details(self, benchmark: BIGBenchHard, dataset: List[Dict], predictions: List[str], scores: List[float], eval_mode: str, accuracy: float, correct_count: int, total_count: int):
        if not self.enable_logging:
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'evaluation_testset_{eval_mode}_{timestamp}.csv'
        filepath = os.path.join(self.log_dir, filename)
        logger.info(f'Logging detailed evaluation results to {filepath}')
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Overall_Accuracy', f'{accuracy:.6f}'])
            writer.writerow(['Correct_Count', correct_count])
            writer.writerow(['Total_Count', total_count])
            writer.writerow([])
            writer.writerow(['example_id', 'input_text', 'prediction', 'ground_truth', 'score'])
            for i, example in enumerate(dataset):
                example_id = benchmark._get_id(example)
                input_text = example.get('input', '')
                label = benchmark.get_label(example)
                writer.writerow([example_id, input_text[:200] + '...' if len(input_text) > 200 else input_text, predictions[i], label, scores[i]])

    def _log_generation(self, generation: int, combos_with_scores: List[tuple]):
        """
        Log generation data for combination-based evolution.
        """
        if not self.enable_logging:
            return
        filename = f'combo_generation_{generation:02d}_log.csv'
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            header = ['Combination_ID', 'Combination_Score', 'Node_Name', 'Prompt_Text', 'Generation', 'Timestamp']
            writer.writerow(header)
            timestamp = datetime.now().isoformat()
            sorted_combos = sorted(combos_with_scores, key=lambda x: x[1], reverse=True)
            for combo_rank, (combination, avg_score) in enumerate(sorted_combos):
                combo_id = f'combo_rank_{combo_rank + 1}'
                for node_name, prompt_text in combination.items():
                    writer.writerow([combo_id, f'{avg_score:.6f}', node_name, prompt_text[:200] + '...' if len(prompt_text) > 200 else prompt_text, generation, timestamp])

    async def _evaluate_combination_list(self, combinations: List[Dict], benchmark: BIGBenchHard, dev_set: list) -> List[float]:
        if not combinations:
            return []
        eval_dev_set = dev_set[:50] if len(dev_set) > 50 else dev_set
        all_scores = []
        pbar = aio_tqdm(total=len(combinations), desc='Evaluating batch', leave=False)
        for combo in combinations:
            tasks = [self._evaluate_combination_on_example(combo, benchmark, ex) for ex in eval_dev_set]
            example_scores = await asyncio.gather(*tasks)
            avg_score = sum(example_scores) / len(example_scores) if example_scores else 0.0
            all_scores.append(avg_score)
            pbar.update(1)
        pbar.close()
        return all_scores

    def _generate_combinations(self, node_populations: Dict[str, List[str]]) -> List[Dict[str, str]]:
        node_names = list(node_populations.keys())
        node_prompts = [node_populations[node] for node in node_names]
        total_possible = np.prod([len(p) for p in node_prompts if p]) if all((p for p in node_prompts)) else 0
        if total_possible == 0:
            logger.warning('Cannot generate combinations, one or more node populations are empty.')
            return []
        if self.combination_sample_size is None:
            target_size = min(self.population_size, int(total_possible), 200)
        else:
            target_size = min(self.combination_sample_size, int(total_possible))
        logger.info(f'Total possible combinations: {total_possible}, sampling: {target_size}')
        if target_size >= total_possible:
            all_combinations = []
            for combination in itertools.product(*node_prompts):
                combo_dict = {node_names[i]: combination[i] for i in range(len(node_names))}
                all_combinations.append(combo_dict)
            return all_combinations
        sampled_combinations = []
        sampled_keys = set()
        max_attempts = target_size * 5
        attempts = 0
        while len(sampled_combinations) < target_size and attempts < max_attempts:
            combination = {name: random.choice(prompts) for name, prompts in node_populations.items()}
            combo_key = tuple(sorted(combination.items()))
            if combo_key not in sampled_keys:
                sampled_combinations.append(combination)
                sampled_keys.add(combo_key)
            attempts += 1
        logger.info(f'Generated {len(sampled_combinations)} unique combinations')
        return sampled_combinations

    async def _evaluate_combination_on_example(self, combination: Dict[str, str], benchmark: BIGBenchHard, example: Dict) -> float:
        combo_key = tuple(sorted(combination.items()))
        example_key = str(hash(str(example)))
        cache_key = hash((combo_key, example_key))
        if not hasattr(self, '_eval_cache'):
            self._eval_cache = {}
        if cache_key in self._eval_cache:
            return self._eval_cache[cache_key]
        async with self.semaphore:
            try:
                original_config = self.get_current_cfg()
                self.apply_cfg(combination)
                inputs = {k: v for k, v in example.items() if k in benchmark.get_input_keys()}
                prediction, _ = await asyncio.to_thread(self.program, **inputs)
                label = benchmark.get_label(example)
                score_dict = benchmark.evaluate(prediction, label)
                score = score_dict.get('em', 0.0)
                self.apply_cfg(original_config)
                self._eval_cache[cache_key] = score
                if len(self._eval_cache) > 5000:
                    keys_to_del = list(self._eval_cache.keys())[:1000]
                    for key in keys_to_del:
                        del self._eval_cache[key]
                return score
            except Exception as e:
                logger.error(f'Error evaluating combination: {e}')
                return 0.0

    async def _evaluate_combinations_and_update_node_scores(self, combinations: List[Dict[str, str]], benchmark: BIGBenchHard, dev_set: list) -> List[float]:
        eval_dev_set = dev_set[:50] if len(dev_set) > 50 else dev_set
        combination_scores = []
        print(f'Evaluating {len(combinations)} combinations on {len(eval_dev_set)} examples...')
        combo_pbar = aio_tqdm(total=len(combinations), desc='Evaluating Combinations')
        for combination in combinations:
            tasks = [self._evaluate_combination_on_example(combination, benchmark, ex) for ex in eval_dev_set]
            example_scores = await asyncio.gather(*tasks)
            avg_score = sum(example_scores) / len(example_scores) if example_scores else 0.0
            combination_scores.append(avg_score)
            combo_pbar.update(1)
        combo_pbar.close()
        for node_name in self.node_populations.keys():
            self.node_scores[node_name] = [0.0] * len(self.node_populations[node_name])
            for prompt_idx, prompt in enumerate(self.node_populations[node_name]):
                participating_scores = [combo_score for combo_idx, combo_score in enumerate(combination_scores) if combinations[combo_idx].get(node_name) == prompt]
                if participating_scores:
                    self.node_scores[node_name][prompt_idx] = sum(participating_scores) / len(participating_scores)
                else:
                    self.node_scores[node_name][prompt_idx] = 0.0
        return combination_scores

    async def _perform_paraphrase(self, prompt: str) -> str:
        async with self.semaphore:
            output = await asyncio.to_thread(self.paraphrase_agent, inputs={'instruction': prompt})
            return output.content.paraphrased_instruction.strip()

    async def _perform_evolution(self, agent: Callable, inputs: Dict[str, str]) -> str:
        async with self.semaphore:
            output = await asyncio.to_thread(agent, inputs=inputs)
            if hasattr(output.content, 'evolved_prompt'):
                return output.content.evolved_prompt.strip()
            return str(output.content).strip()

    async def _initialize_node_populations(self, initial_config: Dict[str, any]):
        for node_name, initial_value in initial_config.items():
            node_population = []
            if isinstance(initial_value, list):
                provided_size = len(initial_value)
                if self.population_size < provided_size:
                    logger.info(f"Node '{node_name}': Provided population ({provided_size}) is larger than target size ({self.population_size}). Randomly sampling.")
                    node_population = random.sample(initial_value, self.population_size)
                elif self.population_size == provided_size:
                    logger.info(f"Node '{node_name}': Provided population size ({provided_size}) matches target size. Using directly.")
                    node_population = list(initial_value)
                else:
                    logger.info(f"Node '{node_name}': Target population size ({self.population_size}) is larger than provided ({provided_size}). Expanding.")
                    node_population = list(initial_value)
                    num_to_generate = self.population_size - provided_size
                    source_prompts_for_generation = random.choices(initial_value, k=num_to_generate)
                    paraphrase_tasks = [self._perform_paraphrase(prompt) for prompt in source_prompts_for_generation]
                    new_prompts = await aio_tqdm.gather(*paraphrase_tasks, desc=f'Expanding population for {node_name}')
                    node_population.extend(new_prompts)
            elif isinstance(initial_value, str):
                logger.info(f"Node '{node_name}': Generating population from a single initial prompt.")
                node_population = [initial_value]
                if self.population_size > 1:
                    num_to_generate = self.population_size - 1
                    paraphrase_tasks = [self._perform_paraphrase(initial_value) for _ in range(num_to_generate)]
                    new_prompts = await aio_tqdm.gather(*paraphrase_tasks, desc=f'Generating initial population for {node_name}')
                    node_population.extend(new_prompts)
            else:
                raise TypeError(f"Unsupported type for tracked parameter '{node_name}': {type(initial_value)}. Must be str or list.")
            self.node_populations[node_name] = node_population
            self.node_scores[node_name] = [0.0] * self.population_size

    async def evaluate(self, benchmark: BIGBenchHard, eval_mode: str='test') -> Dict[str, float]:
        """
        Evaluates the optimized program on a specified dataset.

        Args:
            benchmark (BIGBenchHard): The benchmark instance containing the data.
            eval_mode (str): The evaluation mode, either "test" or "dev".

        Returns:
            Dict[str, float]: A dictionary containing evaluation metrics.
        """
        logger.info(f"--- Evaluating optimized program on '{eval_mode}' set ---")
        dataset = benchmark.get_test_data() if eval_mode == 'test' else benchmark.get_dev_data()
        if not dataset:
            logger.warning(f"No data found for '{eval_mode}' set. Returning empty results.")
            return {}

        async def evaluate_example(example: Dict) -> tuple[float, str]:
            prediction, _ = await asyncio.to_thread(self.program, input=example['input'])
            score_dict = benchmark.evaluate(prediction, benchmark.get_label(example))
            score = score_dict.get('em', 0.0)
            return (score, prediction)
        tasks = [evaluate_example(ex) for ex in dataset]
        results = await aio_tqdm.gather(*tasks, desc=f'Evaluating on {eval_mode.capitalize()} Set')
        scores, predictions = zip(*results) if results else ([], [])
        correct_count = sum(scores)
        total_count = len(dataset)
        accuracy = correct_count / total_count if total_count > 0 else 0.0
        logger.info(f'{eval_mode.capitalize()} Set Accuracy: {accuracy:.4f} ({int(correct_count)}/{total_count})')
        if self.enable_logging:
            await self._log_evaluation_details(benchmark, dataset, predictions, scores, eval_mode, accuracy, int(correct_count), total_count)
        return {'accuracy': accuracy}

def _create_single_metric_plot(self, metric_name: str, generations: List[int], best_scores: List[float], avg_scores: List[float], algorithm_name: str, plot_dir: str):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(generations, best_scores, marker='o', linestyle='-', linewidth=2, markersize=8, label='Best Score')
    ax.plot(generations, avg_scores, marker='x', linestyle='--', linewidth=2, markersize=8, label='Average Score')
    title = f"Performance for '{metric_name}' ({algorithm_name})"
    ax.set_title(title, fontsize=16, weight='bold')
    ax.set_xlabel('Generation', fontsize=12)
    ax.set_ylabel('Fitness Score', fontsize=12)
    ax.set_xticks(generations)
    ax.set_xticklabels([f'Gen {g}' for g in generations], rotation=45, ha='right')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    safe_metric_name = re.sub('[^a-zA-Z0-9_-]', '_', metric_name)
    filename = f'performance_plot_{safe_metric_name}.png'
    filepath = os.path.join(plot_dir, filename)
    try:
        plt.savefig(filepath, dpi=200, bbox_inches='tight')
    except Exception as e:
        logger.error(f'Failed to save individual plot for {metric_name}: {e}')
    finally:
        plt.close(fig)

def _plot_and_save_performance_graph(self, algorithm_name: str):
    if not self.enable_logging or plt is None:
        if plt is None:
            logger.warning('Matplotlib not found, skipping plot generation.')
        return
    if not self.best_scores_per_gen and (not self.best_combo_scores_per_gen):
        logger.warning('No performance data to plot.')
        return
    plt.style.use('seaborn-v0_8-whitegrid')
    all_gen_keys = set(self.best_scores_per_gen.keys()) | set(self.best_combo_scores_per_gen.keys())
    generations = sorted([int(re.search('\\d+', gen).group()) for gen in all_gen_keys if re.search('\\d+', gen)])
    fig_combined, ax_combined = plt.subplots(figsize=(16, 9))
    if self.best_combo_scores_per_gen:
        combo_best = [self.best_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
        combo_avg = [self.avg_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
        ax_combined.plot(generations, combo_best, marker='*', linestyle='-', linewidth=2.5, markersize=10, label='Best Combination Score (Overall)')
        ax_combined.plot(generations, combo_avg, marker='D', linestyle='--', linewidth=2.5, markersize=8, label='Average Combination Score (Overall)')
    all_node_metrics = set()
    for gen_data in self.best_scores_per_gen.values():
        all_node_metrics.update(gen_data.keys())
    for metric in sorted(list(all_node_metrics)):
        best_scores = [self.best_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
        avg_scores = [self.avg_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
        ax_combined.plot(generations, best_scores, marker='o', linestyle='-', alpha=0.7, label=f'Best Score ({metric})')
        ax_combined.plot(generations, avg_scores, marker='x', linestyle='--', alpha=0.7, label=f'Average Score ({metric})')
    ax_combined.set_title(f'Overall Performance Evolution ({algorithm_name})', fontsize=18, weight='bold')
    ax_combined.set_xlabel('Generation', fontsize=14)
    ax_combined.set_ylabel('Fitness Score', fontsize=14)
    ax_combined.set_xticks(generations)
    ax_combined.set_xticklabels([f'Gen {g}' for g in generations], rotation=45, ha='right')
    handles, labels = ax_combined.get_legend_handles_labels()
    combo_indices = [i for i, label in enumerate(labels) if 'Combination' in label]
    node_indices = [i for i, label in enumerate(labels) if 'Combination' not in label]
    ax_combined.legend([handles[i] for i in combo_indices + node_indices], [labels[i] for i in combo_indices + node_indices], loc='best', fontsize=10)
    ax_combined.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    combined_filepath = os.path.join(self.log_dir, 'performance_summary_OVERALL.png')
    try:
        plt.savefig(combined_filepath, dpi=300, bbox_inches='tight')
        logger.info(f'Overall performance plot saved to: {combined_filepath}')
    except Exception as e:
        logger.error(f'Failed to save overall performance plot: {e}')
    finally:
        plt.close(fig_combined)
    individual_plot_dir = os.path.join(self.log_dir, 'individual_plots')
    os.makedirs(individual_plot_dir, exist_ok=True)
    for metric in sorted(list(all_node_metrics)):
        best_scores = [self.best_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
        avg_scores = [self.avg_scores_per_gen.get(f'Gen_{g}', {}).get(metric) for g in generations]
        self._create_single_metric_plot(metric, generations, best_scores, avg_scores, algorithm_name, individual_plot_dir)
    if self.best_combo_scores_per_gen:
        combo_best = [self.best_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
        combo_avg = [self.avg_combo_scores_per_gen.get(f'Gen_{g}') for g in generations]
        self._create_single_metric_plot('Combination', generations, combo_best, combo_avg, algorithm_name, individual_plot_dir)
    logger.info(f'Individual performance plots saved to: {individual_plot_dir}')

class GSM8K(Benchmark):
    """Benchmark class for evaluating math reasoning on GSM8K dataset.
    
    GSM8K (Grade School Math 8K) is a dataset of math word problems that
    test a model's ability to solve grade school level math problems requiring
    multi-step reasoning. This class handles loading the dataset, evaluating
    solutions, and computing metrics based on answer accuracy.
    
    Each GSM8K example has the following structure:
    {
        "id": "test-1", 
        "question": "the question", 
        "answer": "the answer"
    }
    
    The benchmark evaluates answers by extracting the final numerical value
    and comparing it to the ground truth answer.
    """

    def __init__(self, path: str=None, mode: str='all', **kwargs):
        path = os.path.expanduser(path or '~/.evoagentx/data/gsm8k')
        super().__init__(name=type(self).__name__, path=path, mode=mode, **kwargs)

    def _load_data_from_file(self, file_name: str):
        if file_name is None:
            return None
        file_path = os.path.join(self.path, file_name)
        if not os.path.exists(file_path):
            download_raw_gsm8k_data(name=file_name, save_folder=self.path)
        logger.info(f'loading GSM8K data from {file_path} ...')
        return load_gsm8k_data(file_path=file_path)

    def _load_data(self):
        if self.mode == 'train' or self.mode == 'all':
            self._train_data = self._load_data_from_file(file_name=GSM8K_FILES_MAP['train'])
        if self.mode == 'dev' or self.mode == 'all':
            self._dev_data = self._load_data_from_file(file_name=GSM8K_FILES_MAP['dev'])
        if self.mode == 'test' or self.mode == 'all':
            self._test_data = self._load_data_from_file(file_name=GSM8K_FILES_MAP['test'])

    def _get_label(self, example: Any) -> Any:
        return example['answer']

    def _get_id(self, example: Any) -> Any:
        return example['id']

    def extract_last_number(self, text: str) -> float:
        """
        Extract the last number from a text.
        """
        matches = regex.findall('[-+]?\\d+(?:,\\d{3})*(?:\\.\\d+)?|\\d+\\.\\d+', str(text))
        if matches:
            last_number = matches[-1].replace(',', '').strip()
            try:
                last_number = float(last_number)
                return last_number
            except ValueError:
                return None
        return None

    def evaluate(self, prediction: Any, label: Any) -> dict:
        ground_truth_answer = self.extract_last_number(label)
        predicted_answer = self.extract_last_number(prediction)
        if predicted_answer is None:
            return {'solve_rate': 0.0}
        solve_rate = 1.0 if abs(predicted_answer - ground_truth_answer) < 1e-06 else 0.0
        return {'solve_rate': solve_rate}

def evaluate(self, prediction: Any, label: Any) -> dict:
    ground_truth_answer = self.extract_last_number(label)
    predicted_answer = self.extract_last_number(prediction)
    if predicted_answer is None:
        return {'solve_rate': 0.0}
    solve_rate = 1.0 if abs(predicted_answer - ground_truth_answer) < 1e-06 else 0.0
    return {'solve_rate': solve_rate}

class StockDataFetcher:
    """股票数据抓取器 - 核心功能类"""

    def __init__(self, stock_code, auto_create_output_dir=True):
        """
        初始化数据抓取器
        
        Args:
            stock_code (str): 股票代码（如：300750、000001等）
            auto_create_output_dir (bool): 是否自动创建输出目录，默认True
        """
        self.stock_code = stock_code
        self.symbol_sz = f'sz{stock_code}' if stock_code.startswith('0') or stock_code.startswith('3') else f'sh{stock_code}'
        if auto_create_output_dir:
            self.output_dir = Path(f'output_{stock_code}')
        else:
            self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.stock_name = self._get_stock_name()

    def _get_stock_name(self):
        """获取股票名称"""
        try:
            stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
            if not stock_info.empty:
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    return name_row['value'].iloc[0]
            return f'股票{self.stock_code}'
        except:
            return f'股票{self.stock_code}'

    def get_timestamp(self):
        """获取当前日期用于文件命名"""
        return datetime.datetime.now().strftime('%Y%m%d')

    def save_data(self, data, filename_prefix, description=''):
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据（pandas DataFrame）
            filename_prefix (str): 文件名前缀
            description (str): 数据描述
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            timestamp = self.get_timestamp()
            filename = f'{filename_prefix}_{timestamp}_{self.stock_code}.csv'
            filepath = self.output_dir / filename
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath} (共{len(data)}条记录)')
            else:
                df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath}')
            return str(filepath)
        except Exception as e:
            self.logger.error(f'❌ 保存{description}失败: {str(e)}')
            return None

    def fetch_stock_daily(self, days=30):
        """
        抓取股票日线数据
        
        Args:
            days (int): 抓取最近多少天的数据，默认30天
            
        Returns:
            pandas.DataFrame: 股票日线数据
        """
        try:
            self.logger.info(f'📈 开始抓取{self.stock_code}日线数据...')
            stock_df = ak.stock_zh_a_daily(symbol=self.symbol_sz).reset_index()
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
            recent_data = stock_df[stock_df['date'] >= days_ago]
            self.save_data(recent_data, 'stock_daily_catl', f'{self.stock_code}日线数据')
            return recent_data
        except Exception as e:
            self.logger.error(f'❌ 抓取股票日线数据失败: {str(e)}')
            return None

    def fetch_china_cpi(self):
        """
        抓取中国CPI数据 (限制为过去2年)
        
        Returns:
            pandas.DataFrame: 中国CPI数据
        """
        try:
            self.logger.info('📊 开始抓取中国CPI数据...')
            cpi_df = ak.macro_china_cpi()
            if not cpi_df.empty:
                if '月份' in cpi_df.columns:

                    def convert_chinese_date(date_str):
                        try:
                            if '年' in date_str and '月' in date_str:
                                year = date_str.split('年')[0]
                                month = date_str.split('年')[1].split('月')[0]
                                return f'{year}-{month.zfill(2)}-01'
                            else:
                                return date_str
                        except:
                            return None
                    cpi_df['月份'] = cpi_df['月份'].apply(convert_chinese_date)
                    cpi_df['月份'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
                    cpi_df = cpi_df.dropna(subset=['月份'])
                    if not cpi_df.empty:
                        two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
                        cpi_df = cpi_df[cpi_df['月份'] >= two_years_ago]
                        self.logger.info(f'✅ CPI数据已限制为过去2年: {len(cpi_df)} 条记录')
            return cpi_df
        except Exception as e:
            self.logger.error(f'❌ 抓取CPI数据失败: {str(e)}')
            return None

    def fetch_china_gdp(self):
        """
        抓取中国GDP数据
        
        Returns:
            pandas.DataFrame: 中国GDP数据
        """
        try:
            self.logger.info('📊 开始抓取中国GDP数据...')
            gdp_df = ak.macro_china_gdp_yearly()
            return gdp_df
        except Exception as e:
            self.logger.error(f'❌ 抓取GDP数据失败: {str(e)}')
            return None

    def fetch_industry_fund_flow(self):
        """
        抓取行业资金流数据
        
        Returns:
            pandas.DataFrame: 行业资金流数据
        """
        try:
            self.logger.info('💰 开始抓取行业资金流数据...')
            industry_fund_df = ak.stock_fund_flow_industry()
            return industry_fund_df
        except Exception as e:
            self.logger.error(f'❌ 抓取行业资金流数据失败: {str(e)}')
            return None

    def fetch_stock_news(self):
        """
        抓取个股新闻数据
        
        Returns:
            pandas.DataFrame: 个股新闻数据
        """
        try:
            self.logger.info(f'📰 开始抓取{self.stock_name}({self.stock_code})新闻数据...')
            news_df = ak.stock_news_em(symbol=self.stock_code)
            return news_df
        except Exception as e:
            self.logger.error(f'❌ 抓取新闻数据失败: {str(e)}')
            return None

    def fetch_market_summary(self):
        """
        抓取上交所市场概况
        
        Returns:
            pandas.DataFrame: 市场概况数据
        """
        try:
            self.logger.info('🏛️ 开始抓取上交所市场概况...')
            sse_summary = ak.stock_sse_summary()
            return sse_summary
        except Exception as e:
            self.logger.error(f'❌ 抓取市场概况失败: {str(e)}')
            return None

    def fetch_market_indices(self):
        """
        抓取重要指数行情
        
        Returns:
            pandas.DataFrame: 重要指数数据
        """
        try:
            self.logger.info('📊 开始抓取重要指数行情...')
            market_indices = ak.stock_zh_index_spot_em(symbol='沪深重要指数')
            return market_indices
        except Exception as e:
            self.logger.error(f'❌ 抓取市场指数失败: {str(e)}')
            return None

    def fetch_option_volatility(self):
        """
        抓取50ETF期权波动率指数 (限制为过去1个月)
        
        Returns:
            pandas.DataFrame: 期权波动率数据
        """
        try:
            self.logger.info('📈 开始抓取50ETF波动率指数...')
            vol50 = ak.index_option_50etf_qvix()
            if not vol50.empty:
                if 'date' in vol50.columns:
                    vol50['date'] = pd.to_datetime(vol50['date'])
                    one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    vol50 = vol50[vol50['date'] >= one_month_ago]
                    self.logger.info(f'✅ 期权波动率数据已限制为过去1个月: {len(vol50)} 条记录')
            return vol50
        except Exception as e:
            self.logger.error(f'❌ 抓取期权波动率数据失败: {str(e)}')
            return None

    def fetch_institution_recommendation(self):
        """
        抓取机构评级数据 (限制为过去半年)
        
        Returns:
            pandas.DataFrame: 机构评级数据
        """
        try:
            self.logger.info(f'🏦 开始抓取{self.stock_name}({self.stock_code})机构评级...')
            inst_rec = ak.stock_institute_recommend_detail(symbol=self.stock_code)
            if not inst_rec.empty:
                date_columns = ['评级日期', 'date', '日期']
                date_col = None
                for col in date_columns:
                    if col in inst_rec.columns:
                        date_col = col
                        break
                if date_col:
                    inst_rec[date_col] = pd.to_datetime(inst_rec[date_col])
                    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                    inst_rec = inst_rec[inst_rec[date_col] >= six_months_ago]
                    self.logger.info(f'✅ 机构评级数据已限制为过去半年: {len(inst_rec)} 条记录')
            return inst_rec
        except Exception as e:
            self.logger.error(f'❌ 抓取机构评级数据失败: {str(e)}')
            return None

    def fetch_all_data(self):
        """
        抓取所有类型的数据
        
        Returns:
            dict: 包含所有数据的字典
        """
        self.logger.info('🚀 开始抓取全部数据...')
        results = {}
        tasks = [('stock_daily', lambda: self.fetch_stock_daily(), '股票日线数据'), ('china_cpi', lambda: self.fetch_china_cpi(), '中国CPI数据'), ('china_gdp', lambda: self.fetch_china_gdp(), '中国GDP数据'), ('industry_fund_flow', lambda: self.fetch_industry_fund_flow(), '行业资金流数据'), ('stock_news', lambda: self.fetch_stock_news(), '个股新闻数据'), ('market_summary', lambda: self.fetch_market_summary(), '市场整体概况'), ('market_indices', lambda: self.fetch_market_indices(), '重要指数行情'), ('option_volatility', lambda: self.fetch_option_volatility(), '期权波动率指数'), ('institution_recommendation', lambda: self.fetch_institution_recommendation(), '机构评级数据')]
        for task_name, task_func, description in tasks:
            try:
                self.logger.info(f'\n--- 开始执行: {description} ---')
                result = task_func()
                results[task_name] = result
                if result is not None:
                    filename_mapping = {'stock_daily': 'stock_daily_catl', 'china_cpi': 'china_cpi', 'china_gdp': 'china_gdp_yearly', 'industry_fund_flow': 'industry_fund_flow', 'stock_news': 'stock_news_catl', 'market_summary': 'market_summary_sse', 'market_indices': 'market_indices', 'option_volatility': 'option_volatility_50etf', 'institution_recommendation': 'institution_recommendation_catl'}
                    self.save_data(result, filename_mapping[task_name], description)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f'执行{description}时发生错误: {str(e)}')
                results[task_name] = None
        self.logger.info('🎉 全部数据抓取完成！')
        return results

    def create_data_documentation(self):
        """创建数据文件说明文档"""
        try:
            timestamp = self.get_timestamp()
            doc_content = f'# {self.stock_name}({self.stock_code})数据文件说明\n\n## 📋 文件命名规则\n\n所有数据文件按以下格式命名：\n```\n数据类型_日期_股票代码.csv\n```\n\n例如：`china_cpi_{timestamp}_{self.stock_code}.csv` 表示{timestamp[:4]}年{timestamp[4:6]}月{timestamp[6:8]}日抓取的中国CPI数据，与{self.stock_name}({self.stock_code})相关。\n\n---\n\n## 📊 数据文件详细说明\n\n### 1. 股票日线数据\n**文件名**: `stock_daily_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_a_daily()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘价（元）\n- **high** - 最高价（元）\n- **low** - 最低价（元）\n- **close** - 收盘价（元）\n- **volume** - 成交量（股）\n- **amount** - 成交额（元）\n- **outstanding_share** - 流通股数（股）\n- **turnover** - 换手率\n\n**用途**: 分析{self.stock_name}股价走势、成交情况，进行技术分析\n\n---\n\n### 2. 中国CPI数据\n**文件名**: `china_cpi_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_cpi()\n\n**中文指标说明**:\n- **月份** - 统计月份\n- **全国-当月** - 全国当月CPI指数\n- **全国-同比增长** - 全国CPI同比增长率(%)\n- **全国-环比增长** - 全国CPI环比增长率(%)\n- **全国-累计** - 全国累计CPI指数\n- **城市-当月** - 城市当月CPI指数\n- **城市-同比增长** - 城市CPI同比增长率(%)\n- **城市-环比增长** - 城市CPI环比增长率(%)\n- **城市-累计** - 城市累计CPI指数\n- **农村-当月** - 农村当月CPI指数\n- **农村-同比增长** - 农村CPI同比增长率(%)\n- **农村-环比增长** - 农村CPI环比增长率(%)\n- **农村-累计** - 农村累计CPI指数\n\n**用途**: 反映通胀水平，判断宏观经济环境对{self.stock_name}所在行业的影响\n\n---\n\n### 3. 中国GDP数据\n**文件名**: `china_gdp_yearly_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_gdp_yearly()\n\n**中文指标说明**:\n- **商品** - 数据类型（中国GDP年率报告）\n- **日期** - 发布日期\n- **今值** - 当期GDP增长率(%)\n- **预测值** - 市场预测GDP增长率(%)\n- **前值** - 前期GDP增长率(%)\n\n**用途**: 评估国家经济增长情况，判断宏观经济对{self.stock_name}所在行业需求的影响\n\n---\n\n### 4. 行业资金流数据\n**文件名**: `industry_fund_flow_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_fund_flow_industry()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **行业** - 行业名称\n- **行业指数** - 行业指数代码\n- **行业-涨跌幅** - 行业当日涨跌幅(%)\n- **流入资金** - 资金流入金额（万元）\n- **流出资金** - 资金流出金额（万元）\n- **净额** - 资金净流入金额（万元）\n- **公司家数** - 该行业公司数量\n- **领涨股** - 行业内领涨股票\n- **领涨股-涨跌幅** - 领涨股涨跌幅(%)\n- **当前价** - 领涨股当前价格（元）\n\n**用途**: 分析各行业资金流向，判断{self.stock_name}所在行业的资金关注度\n\n---\n\n### 5. 个股新闻数据\n**文件名**: `stock_news_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_news_em()\n\n**中文指标说明**:\n- **关键词** - 搜索关键词（股票代码）\n- **新闻标题** - 新闻标题\n- **新闻内容** - 新闻摘要/内容\n- **发布时间** - 新闻发布时间\n- **新闻来源** - 新闻来源媒体\n- **新闻链接** - 原文链接地址\n\n**用途**: 获取{self.stock_name}相关新闻资讯，进行舆情分析和基本面研究\n\n---\n\n### 6. 上交所市场概况\n**文件名**: `market_summary_sse_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_sse_summary()\n\n**中文指标说明**:\n- **项目** - 统计项目名称\n- **股票** - 股票相关数据\n- **主板** - 主板市场数据\n- **科创板** - 科创板市场数据\n\n**具体项目包括**:\n- **流通股本** - 流通股总数（亿股）\n- **总市值** - 总市值（亿元）\n- **平均市盈率** - 平均市盈率（倍）\n- **上市公司** - 上市公司数量（家）\n- **上市股票** - 上市股票数量（只）\n- **流通市值** - 流通市值（亿元）\n- **总股本** - 总股本（亿股）\n\n**用途**: 了解整体市场状况，判断市场环境对{self.stock_name}的影响\n\n---\n\n### 7. 重要指数行情\n**文件名**: `market_indices_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_index_spot_em()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **代码** - 指数代码\n- **名称** - 指数名称\n- **最新价** - 最新指数点位\n- **涨跌幅** - 当日涨跌幅(%)\n- **涨跌额** - 当日涨跌点数\n- **成交量** - 成交量（手）\n- **成交额** - 成交金额（万元）\n- **振幅** - 当日振幅(%)\n- **最高** - 当日最高点位\n- **最低** - 当日最低点位\n- **今开** - 今日开盘点位\n- **昨收** - 昨日收盘点位\n- **量比** - 量比\n\n**包含指数**:\n- 上证指数、深证成指、创业板指、科创综指、北证50等\n\n**用途**: 跟踪重要市场指数走势，判断整体市场方向\n\n---\n\n### 8. 50ETF期权波动率指数\n**文件名**: `option_volatility_50etf_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.index_option_50etf_qvix()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘波动率\n- **high** - 最高波动率\n- **low** - 最低波动率\n- **close** - 收盘波动率\n\n**用途**: 反映市场恐慌情绪和波动性预期，是重要的市场情绪指标\n\n---\n\n### 9. 机构评级数据\n**文件名**: `institution_recommendation_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_institute_recommend_detail()\n\n**中文指标说明**:\n- **股票代码** - 股票代码\n- **股票名称** - 股票名称\n- **目标价** - 机构给出的目标价格（元）\n- **最新评级** - 机构最新评级（买入/增持/中性/减持/卖出）\n- **评级机构** - 研究机构名称\n- **分析师** - 分析师姓名\n- **行业** - 所属行业\n- **评级日期** - 评级发布日期\n\n**评级含义**:\n- **买入** - 强烈推荐买入\n- **增持** - 推荐增加持仓\n- **中性** - 维持现有持仓\n- **减持** - 建议减少持仓\n- **卖出** - 建议卖出\n\n**用途**: 了解专业机构对{self.stock_name}的投资建议和价格预期\n\n---\n\n### 10. 数据收集报告\n**文件名**: `collection_report_{timestamp}_{self.stock_code}.csv`\n\n**自动生成的收集统计报告**\n\n**中文指标说明**:\n- **数据类型** - 数据收集任务名称\n- **收集状态** - 收集是否成功（成功/失败）\n- **记录数量** - 成功收集的数据条数\n- **时间戳** - 数据收集完成时间\n\n**用途**: 监控数据收集任务的执行情况，确保数据完整性\n\n---\n\n## 🔍 数据使用建议\n\n### 综合分析框架\n\n1. **宏观经济层面**\n   - 使用CPI、GDP数据判断宏观经济环境\n   - 分析对{self.stock_name}所在行业的影响\n\n2. **市场情绪层面**\n   - 使用期权波动率指数判断市场恐慌程度\n   - 使用重要指数走势判断市场整体方向\n\n3. **行业资金层面**\n   - 使用行业资金流数据判断资金偏好\n   - 关注{self.stock_name}所在行业的资金流向\n\n4. **个股基本面**\n   - 使用机构评级了解专业判断\n   - 使用新闻数据进行舆情分析\n\n5. **技术面分析**\n   - 使用股票日线数据进行技术分析\n   - 结合成交量判断趋势强度\n\n### 数据更新频率\n\n- **日更新**: 股票日线、新闻、指数行情、期权波动率\n- **月更新**: CPI数据\n- **季更新**: GDP数据\n- **实时更新**: 行业资金流、机构评级\n\n---\n\n## ⚠️ 使用注意事项\n\n1. **数据时效性**: 部分数据存在发布延迟，请注意数据的时效性\n2. **数据完整性**: 如遇到数据源问题，某些文件可能缺失，请查看收集报告\n3. **投资风险**: 数据仅供参考，不构成投资建议，投资需谨慎\n4. **版权声明**: 数据来源于公开渠道，请遵守相关使用条款\n\n---\n\n## 📞 技术支持\n\n如有数据解读疑问或技术问题，请参考：\n- akshare官方文档: https://akshare.readthedocs.io/\n- 数据抓取函数库: 本项目中的股票数据抓取函数\n\n**生成时间**: {datetime.datetime.now().strftime('%Y年%m月%d日')}\n**数据版本**: v2.0  \n**适用股票**: {self.stock_name}({self.stock_code})\n'
            doc_filepath = self.output_dir / '数据文件说明.md'
            with open(doc_filepath, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            self.logger.info(f'✅ 数据说明文档已生成: {doc_filepath}')
            return str(doc_filepath)
        except Exception as e:
            self.logger.error(f'❌ 生成数据说明文档失败: {str(e)}')
            return None

def fetch_stock_daily(self, days=30):
    """
        抓取股票日线数据
        
        Args:
            days (int): 抓取最近多少天的数据，默认30天
            
        Returns:
            pandas.DataFrame: 股票日线数据
        """
    try:
        self.logger.info(f'📈 开始抓取{self.stock_code}日线数据...')
        stock_df = ak.stock_zh_a_daily(symbol=self.symbol_sz).reset_index()
        stock_df['date'] = pd.to_datetime(stock_df['date'])
        days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
        recent_data = stock_df[stock_df['date'] >= days_ago]
        self.save_data(recent_data, 'stock_daily_catl', f'{self.stock_code}日线数据')
        return recent_data
    except Exception as e:
        self.logger.error(f'❌ 抓取股票日线数据失败: {str(e)}')
        return None

def fetch_china_cpi(self):
    """
        抓取中国CPI数据 (限制为过去2年)
        
        Returns:
            pandas.DataFrame: 中国CPI数据
        """
    try:
        self.logger.info('📊 开始抓取中国CPI数据...')
        cpi_df = ak.macro_china_cpi()
        if not cpi_df.empty:
            if '月份' in cpi_df.columns:

                def convert_chinese_date(date_str):
                    try:
                        if '年' in date_str and '月' in date_str:
                            year = date_str.split('年')[0]
                            month = date_str.split('年')[1].split('月')[0]
                            return f'{year}-{month.zfill(2)}-01'
                        else:
                            return date_str
                    except:
                        return None
                cpi_df['月份'] = cpi_df['月份'].apply(convert_chinese_date)
                cpi_df['月份'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
                cpi_df = cpi_df.dropna(subset=['月份'])
                if not cpi_df.empty:
                    two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
                    cpi_df = cpi_df[cpi_df['月份'] >= two_years_ago]
                    self.logger.info(f'✅ CPI数据已限制为过去2年: {len(cpi_df)} 条记录')
        return cpi_df
    except Exception as e:
        self.logger.error(f'❌ 抓取CPI数据失败: {str(e)}')
        return None

def fetch_option_volatility(self):
    """
        抓取50ETF期权波动率指数 (限制为过去1个月)
        
        Returns:
            pandas.DataFrame: 期权波动率数据
        """
    try:
        self.logger.info('📈 开始抓取50ETF波动率指数...')
        vol50 = ak.index_option_50etf_qvix()
        if not vol50.empty:
            if 'date' in vol50.columns:
                vol50['date'] = pd.to_datetime(vol50['date'])
                one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                vol50 = vol50[vol50['date'] >= one_month_ago]
                self.logger.info(f'✅ 期权波动率数据已限制为过去1个月: {len(vol50)} 条记录')
        return vol50
    except Exception as e:
        self.logger.error(f'❌ 抓取期权波动率数据失败: {str(e)}')
        return None

def fetch_institution_recommendation(self):
    """
        抓取机构评级数据 (限制为过去半年)
        
        Returns:
            pandas.DataFrame: 机构评级数据
        """
    try:
        self.logger.info(f'🏦 开始抓取{self.stock_name}({self.stock_code})机构评级...')
        inst_rec = ak.stock_institute_recommend_detail(symbol=self.stock_code)
        if not inst_rec.empty:
            date_columns = ['评级日期', 'date', '日期']
            date_col = None
            for col in date_columns:
                if col in inst_rec.columns:
                    date_col = col
                    break
            if date_col:
                inst_rec[date_col] = pd.to_datetime(inst_rec[date_col])
                six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                inst_rec = inst_rec[inst_rec[date_col] >= six_months_ago]
                self.logger.info(f'✅ 机构评级数据已限制为过去半年: {len(inst_rec)} 条记录')
        return inst_rec
    except Exception as e:
        self.logger.error(f'❌ 抓取机构评级数据失败: {str(e)}')
        return None

class StockChartGenerator:
    """股票技术分析图表生成器"""

    def __init__(self, symbol: str, output_dir: str='output'):
        """
        初始化图表生成器
        
        Args:
            symbol (str): 股票代码（如：300750、600519等）
            output_dir (str): 输出目录，默认为"output"
        """
        self.symbol = symbol
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.stock_data = None
        self.processed_data = None

    def generate_mock_data(self) -> pd.DataFrame:
        """生成模拟股票数据用于演示"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
        dates = [d for d in dates if d.weekday() < 5]
        np.random.seed(42)
        base_price = 1500 if self.symbol == '600519' else 100
        prices = []
        current_price = base_price
        for i in range(len(dates)):
            change = np.random.normal(0, 0.02)
            current_price = current_price * (1 + change)
            prices.append(current_price)
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            volatility = close * 0.03
            high = close + np.random.uniform(0, volatility)
            low = close - np.random.uniform(0, volatility)
            open_price = prices[i - 1] if i > 0 else close
            volume = np.random.randint(100000, 1000000)
            data.append({'date': date.strftime('%Y-%m-%d'), 'open': round(open_price, 2), 'high': round(high, 2), 'low': round(low, 2), 'close': round(close, 2), 'volume': volume})
        df = pd.DataFrame(data)
        print(f'生成了 {len(df)} 条模拟数据')
        return df

    def get_stock_data(self) -> pd.DataFrame:
        """获取股票数据"""
        if self.stock_data is not None:
            return self.stock_data
        try:
            import akshare as ak
            print(f'获取股票 {self.symbol} 的数据...')
            try:
                df = ak.stock_zh_a_hist(symbol=self.symbol, period='daily', adjust='qfq')
            except:
                try:
                    formatted_symbol = f'sh{self.symbol}' if self.symbol.startswith('6') else f'sz{self.symbol}'
                    df = ak.stock_zh_a_hist(symbol=formatted_symbol, period='daily', adjust='qfq')
                except:
                    print('获取真实数据失败，使用模拟数据...')
                    return self.generate_mock_data()
            if df.empty:
                return self.generate_mock_data()
            df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'})
            print(f'成功获取 {len(df)} 条真实数据')
            self.stock_data = df.tail(250)
            return self.stock_data
        except Exception as e:
            print(f'获取数据失败，使用模拟数据: {e}')
            return self.generate_mock_data()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = df.copy()
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - 100 / (1 + rs)
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + bb_std * 2
        df['BB_lower'] = df['BB_middle'] - bb_std * 2
        df = df.fillna(method='ffill').fillna(method='bfill')
        self.processed_data = df
        return df

    def create_technical_chart(self) -> Optional[str]:
        """创建技术分析图表"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib import rcParams
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            if self.processed_data is None:
                df = self.get_stock_data()
                df = self.calculate_indicators(df)
            else:
                df = self.processed_data
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            fig, axes = plt.subplots(4, 1, figsize=(15, 20))
            fig.suptitle(f'{self.symbol} 技术分析图表', fontsize=16, fontweight='bold')
            ax1 = axes[0]
            ax1.plot(df['date'], df['close'], label='收盘价', linewidth=2, color='blue')
            ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange')
            ax1.plot(df['date'], df['MA10'], label='MA10', alpha=0.8, color='green')
            ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='red')
            ax1.fill_between(df['date'], df['BB_upper'], df['BB_lower'], alpha=0.1, color='gray', label='布林带')
            ax1.plot(df['date'], df['BB_upper'], alpha=0.5, color='gray', linestyle='--')
            ax1.plot(df['date'], df['BB_lower'], alpha=0.5, color='gray', linestyle='--')
            ax1.set_title('价格走势与技术指标')
            ax1.set_ylabel('价格 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax2 = axes[1]
            colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
            ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7)
            ax2.set_title('成交量')
            ax2.set_ylabel('成交量')
            ax2.grid(True, alpha=0.3)
            ax3 = axes[2]
            ax3.plot(df['date'], df['RSI'], label='RSI', color='purple', linewidth=2)
            ax3.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='超买线(70)')
            ax3.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='超卖线(30)')
            ax3.fill_between(df['date'], 30, 70, alpha=0.1, color='yellow', label='正常区间')
            ax3.set_title('RSI指标')
            ax3.set_ylabel('RSI')
            ax3.set_ylim(0, 100)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            ax4 = axes[3]
            ax4.plot(df['date'], df['MACD'], label='MACD', color='blue', linewidth=2)
            ax4.plot(df['date'], df['MACD_signal'], label='信号线', color='red', linewidth=2)
            colors = ['red' if x > 0 else 'green' for x in df['MACD_histogram']]
            ax4.bar(df['date'], df['MACD_histogram'], color=colors, alpha=0.6, label='MACD柱状图')
            ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax4.set_title('MACD指标')
            ax4.set_ylabel('MACD')
            ax4.set_xlabel('日期')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            for ax in axes:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            plt.tight_layout()
            chart_path = self.output_dir / f'{self.symbol}_technical_charts.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f'📊 技术分析图表已保存: {chart_path}')
            return str(chart_path)
        except ImportError:
            print('⚠️ matplotlib未安装，跳过图表生成')
            return None
        except Exception as e:
            print(f'❌ 生成技术分析图表失败: {e}')
            return None

    def create_candlestick_chart(self) -> Optional[str]:
        """创建K线图（蜡烛图）"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib.patches import Rectangle
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            if self.processed_data is None:
                df = self.get_stock_data()
                df = self.calculate_indicators(df)
            else:
                df = self.processed_data
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').tail(60)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), height_ratios=[3, 1])
            fig.suptitle(f'{self.symbol} K线图分析', fontsize=16, fontweight='bold')
            for i, row in df.iterrows():
                date = row['date']
                open_price = row['open']
                high_price = row['high']
                low_price = row['low']
                close_price = row['close']
                color = 'red' if close_price >= open_price else 'green'
                ax1.plot([date, date], [low_price, high_price], color='black', linewidth=1)
                body_height = abs(close_price - open_price)
                body_bottom = min(open_price, close_price)
                rect = Rectangle((mdates.date2num(date) - 0.3, body_bottom), 0.6, body_height, facecolor=color, alpha=0.8, edgecolor='black', linewidth=0.5)
                ax1.add_patch(rect)
            ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange', linewidth=1.5)
            ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='blue', linewidth=1.5)
            ax1.set_title('K线图与移动平均线')
            ax1.set_ylabel('价格 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
            ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7, width=0.8)
            ax2.set_title('成交量')
            ax2.set_ylabel('成交量')
            ax2.set_xlabel('日期')
            ax2.grid(True, alpha=0.3)
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            plt.tight_layout()
            chart_path = self.output_dir / f'{self.symbol}_candlestick_chart.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f'📊 K线图已保存: {chart_path}')
            return str(chart_path)
        except Exception as e:
            print(f'❌ 生成K线图失败: {e}')
            return None

    def generate_all_charts(self) -> Dict[str, Optional[str]]:
        """生成所有类型的图表"""
        print(f'🚀 生成股票 {self.symbol} 的技术分析图表')
        print('=' * 60)
        print(f'📊 开始分析股票: {self.symbol}')
        print('🔄 获取股票数据...')
        df = self.get_stock_data()
        if df is None:
            print('❌ 无法获取数据')
            return {}
        print('🔢 计算技术指标...')
        self.calculate_indicators(df)
        chart_paths = {}
        print('📊 生成技术分析图表...')
        technical_path = self.create_technical_chart()
        if technical_path:
            chart_paths['technical'] = technical_path
        print('🕯️ 生成K线图...')
        candlestick_path = self.create_candlestick_chart()
        if candlestick_path:
            chart_paths['candlestick'] = candlestick_path
        if chart_paths:
            print(f'✅ 图表生成成功:')
            for chart_type, path in chart_paths.items():
                print(f'   {chart_type}: {os.path.abspath(path)}')
        else:
            print('❌ 图表生成失败')
        return chart_paths

def get_stock_data(self) -> pd.DataFrame:
    """获取股票数据"""
    if self.stock_data is not None:
        return self.stock_data
    try:
        import akshare as ak
        print(f'获取股票 {self.symbol} 的数据...')
        try:
            df = ak.stock_zh_a_hist(symbol=self.symbol, period='daily', adjust='qfq')
        except:
            try:
                formatted_symbol = f'sh{self.symbol}' if self.symbol.startswith('6') else f'sz{self.symbol}'
                df = ak.stock_zh_a_hist(symbol=formatted_symbol, period='daily', adjust='qfq')
            except:
                print('获取真实数据失败，使用模拟数据...')
                return self.generate_mock_data()
        if df.empty:
            return self.generate_mock_data()
        df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'})
        print(f'成功获取 {len(df)} 条真实数据')
        self.stock_data = df.tail(250)
        return self.stock_data
    except Exception as e:
        print(f'获取数据失败，使用模拟数据: {e}')
        return self.generate_mock_data()

def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
    """计算技术指标"""
    df = df.copy()
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - 100 / (1 + rs)
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + bb_std * 2
    df['BB_lower'] = df['BB_middle'] - bb_std * 2
    df = df.fillna(method='ffill').fillna(method='bfill')
    self.processed_data = df
    return df

def create_technical_chart(self) -> Optional[str]:
    """创建技术分析图表"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib import rcParams
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        if self.processed_data is None:
            df = self.get_stock_data()
            df = self.calculate_indicators(df)
        else:
            df = self.processed_data
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        fig, axes = plt.subplots(4, 1, figsize=(15, 20))
        fig.suptitle(f'{self.symbol} 技术分析图表', fontsize=16, fontweight='bold')
        ax1 = axes[0]
        ax1.plot(df['date'], df['close'], label='收盘价', linewidth=2, color='blue')
        ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange')
        ax1.plot(df['date'], df['MA10'], label='MA10', alpha=0.8, color='green')
        ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='red')
        ax1.fill_between(df['date'], df['BB_upper'], df['BB_lower'], alpha=0.1, color='gray', label='布林带')
        ax1.plot(df['date'], df['BB_upper'], alpha=0.5, color='gray', linestyle='--')
        ax1.plot(df['date'], df['BB_lower'], alpha=0.5, color='gray', linestyle='--')
        ax1.set_title('价格走势与技术指标')
        ax1.set_ylabel('价格 (元)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax2 = axes[1]
        colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
        ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7)
        ax2.set_title('成交量')
        ax2.set_ylabel('成交量')
        ax2.grid(True, alpha=0.3)
        ax3 = axes[2]
        ax3.plot(df['date'], df['RSI'], label='RSI', color='purple', linewidth=2)
        ax3.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='超买线(70)')
        ax3.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='超卖线(30)')
        ax3.fill_between(df['date'], 30, 70, alpha=0.1, color='yellow', label='正常区间')
        ax3.set_title('RSI指标')
        ax3.set_ylabel('RSI')
        ax3.set_ylim(0, 100)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax4 = axes[3]
        ax4.plot(df['date'], df['MACD'], label='MACD', color='blue', linewidth=2)
        ax4.plot(df['date'], df['MACD_signal'], label='信号线', color='red', linewidth=2)
        colors = ['red' if x > 0 else 'green' for x in df['MACD_histogram']]
        ax4.bar(df['date'], df['MACD_histogram'], color=colors, alpha=0.6, label='MACD柱状图')
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax4.set_title('MACD指标')
        ax4.set_ylabel('MACD')
        ax4.set_xlabel('日期')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        plt.tight_layout()
        chart_path = self.output_dir / f'{self.symbol}_technical_charts.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f'📊 技术分析图表已保存: {chart_path}')
        return str(chart_path)
    except ImportError:
        print('⚠️ matplotlib未安装，跳过图表生成')
        return None
    except Exception as e:
        print(f'❌ 生成技术分析图表失败: {e}')
        return None

def create_candlestick_chart(self) -> Optional[str]:
    """创建K线图（蜡烛图）"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.patches import Rectangle
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        if self.processed_data is None:
            df = self.get_stock_data()
            df = self.calculate_indicators(df)
        else:
            df = self.processed_data
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').tail(60)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), height_ratios=[3, 1])
        fig.suptitle(f'{self.symbol} K线图分析', fontsize=16, fontweight='bold')
        for i, row in df.iterrows():
            date = row['date']
            open_price = row['open']
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            color = 'red' if close_price >= open_price else 'green'
            ax1.plot([date, date], [low_price, high_price], color='black', linewidth=1)
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            rect = Rectangle((mdates.date2num(date) - 0.3, body_bottom), 0.6, body_height, facecolor=color, alpha=0.8, edgecolor='black', linewidth=0.5)
            ax1.add_patch(rect)
        ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange', linewidth=1.5)
        ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='blue', linewidth=1.5)
        ax1.set_title('K线图与移动平均线')
        ax1.set_ylabel('价格 (元)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
        ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7, width=0.8)
        ax2.set_title('成交量')
        ax2.set_ylabel('成交量')
        ax2.set_xlabel('日期')
        ax2.grid(True, alpha=0.3)
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        plt.tight_layout()
        chart_path = self.output_dir / f'{self.symbol}_candlestick_chart.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f'📊 K线图已保存: {chart_path}')
        return str(chart_path)
    except Exception as e:
        print(f'❌ 生成K线图失败: {e}')
        return None

def generate_all_charts(self) -> Dict[str, Optional[str]]:
    """生成所有类型的图表"""
    print(f'🚀 生成股票 {self.symbol} 的技术分析图表')
    print('=' * 60)
    print(f'📊 开始分析股票: {self.symbol}')
    print('🔄 获取股票数据...')
    df = self.get_stock_data()
    if df is None:
        print('❌ 无法获取数据')
        return {}
    print('🔢 计算技术指标...')
    self.calculate_indicators(df)
    chart_paths = {}
    print('📊 生成技术分析图表...')
    technical_path = self.create_technical_chart()
    if technical_path:
        chart_paths['technical'] = technical_path
    print('🕯️ 生成K线图...')
    candlestick_path = self.create_candlestick_chart()
    if candlestick_path:
        chart_paths['candlestick'] = candlestick_path
    if chart_paths:
        print(f'✅ 图表生成成功:')
        for chart_type, path in chart_paths.items():
            print(f'   {chart_type}: {os.path.abspath(path)}')
    else:
        print('❌ 图表生成失败')
    return chart_paths

def generate_stock_charts(symbol: str='300750', output_dir: str='output', chart_types: List[str]=None) -> Dict[str, Optional[str]]:
    """
    生成股票技术分析图表的主函数
    
    Args:
        symbol (str): 股票代码（如：300750、000001、000858等）
        output_dir (str): 输出目录，默认为"output"
        chart_types (List[str]): 图表类型列表，可选 "technical", "candlestick"
                                默认生成所有类型
        
    Returns:
        Dict[str, Optional[str]]: 生成的图表路径字典
        
    Example:
        # 生成宁德时代的所有图表
        charts = generate_stock_charts("300750")
        
        # 只生成K线图
        charts = generate_stock_charts("600519", chart_types=["candlestick"])
        
        # 生成到指定目录
        charts = generate_stock_charts("000001", output_dir="my_charts")
    """
    if chart_types is None:
        chart_types = ['technical', 'candlestick']
    generator = StockChartGenerator(symbol, output_dir)
    if set(chart_types) == {'technical', 'candlestick'}:
        return generator.generate_all_charts()
    print(f'🚀 生成股票 {symbol} 的指定图表类型')
    print('=' * 60)
    chart_paths = {}
    df = generator.get_stock_data()
    if df is None:
        print('❌ 无法获取数据')
        return {}
    generator.calculate_indicators(df)
    if 'technical' in chart_types:
        print('📊 生成技术分析图表...')
        technical_path = generator.create_technical_chart()
        if technical_path:
            chart_paths['technical'] = technical_path
    if 'candlestick' in chart_types:
        print('🕯️ 生成K线图...')
        candlestick_path = generator.create_candlestick_chart()
        if candlestick_path:
            chart_paths['candlestick'] = candlestick_path
    if chart_paths:
        print(f'✅ 图表生成成功:')
        for chart_type, path in chart_paths.items():
            print(f'   {chart_type}: {os.path.abspath(path)}')
    else:
        print('❌ 图表生成失败')
    return chart_paths

class CSVToLLMConverter:
    """CSV转LLM JSON格式转换器"""

    def __init__(self, data_dir: str):
        """
        初始化转换器
        
        Args:
            data_dir (str): 数据目录路径（如 output_300750）
        """
        self.data_dir = Path(data_dir)
        self.file_priority = {'stock_daily_catl': {'weight': 'high', 'max_rows': 30}, 'institution_recommendation_catl': {'weight': 'high', 'max_rows': 20}, 'stock_news_catl': {'weight': 'high', 'max_rows': 15}, 'china_cpi': {'weight': 'medium', 'max_rows': 10}, 'china_gdp': {'weight': 'medium', 'max_rows': 10}, 'industry_fund_flow': {'weight': 'medium', 'max_rows': 15}, 'market_overview': {'weight': 'normal', 'max_rows': 5}, 'regional_indices': {'weight': 'normal', 'max_rows': 10}, 'option_volatility': {'weight': 'normal', 'max_rows': 8}, 'fund_flow_industry': {'weight': 'normal', 'max_rows': 12}}

    def find_csv_files(self) -> Dict[str, Dict]:
        """查找并分类CSV文件"""
        csv_files = {}
        if not self.data_dir.exists():
            print(f'❌ 数据目录不存在: {self.data_dir}')
            return csv_files
        for file_path in self.data_dir.glob('*.csv'):
            filename = file_path.name
            if 'collection_report' in filename.lower():
                continue
            file_type = self._identify_file_type(filename)
            if file_type:
                csv_files[file_type] = {'file_path': file_path, 'filename': filename, 'config': self.file_priority.get(file_type, {'weight': 'normal', 'max_rows': 10})}
        return csv_files

    def _identify_file_type(self, filename: str) -> Optional[str]:
        """根据文件名识别数据类型"""
        filename_lower = filename.lower()
        type_mapping = {'stock_daily_catl': ['stock_daily'], 'institution_recommendation_catl': ['institution_recommendation'], 'stock_news_catl': ['stock_news'], 'china_cpi': ['china_cpi'], 'china_gdp': ['china_gdp'], 'industry_fund_flow': ['industry_fund_flow'], 'market_overview': ['market_overview'], 'regional_indices': ['regional_indices'], 'option_volatility': ['option_volatility'], 'fund_flow_industry': ['fund_flow_industry']}
        for file_type, keywords in type_mapping.items():
            if any((keyword in filename_lower for keyword in keywords)):
                return file_type
        return None

    def read_and_process_csv(self, file_path: Path, max_rows: int, weight: str) -> List[Dict]:
        """读取并处理CSV文件"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            if df.empty:
                print(f'⚠️ 文件为空: {file_path.name}')
                return []
            if weight == 'high':
                processed_df = df.tail(max_rows)
            else:
                processed_df = df.head(max_rows)
            processed_df = processed_df.fillna('')
            records = processed_df.to_dict(orient='records')
            print(f'✅ 处理完成 {file_path.name}: {len(records)} 条记录')
            return records
        except Exception as e:
            print(f'❌ 处理文件失败 {file_path.name}: {e}')
            return []

    def generate_llm_analysis_prompt(self) -> str:
        """生成适合LLM分析的提示格式"""
        csv_files = self.find_csv_files()
        if not csv_files:
            return 'No valid CSV files found in the specified directory.'

        def sort_priority(item):
            file_type, file_info = item
            weight = file_info['config']['weight']
            if 'stock_daily_catl' in file_type:
                return (0, 0)
            weight_order = {'high': 1, 'medium': 2, 'normal': 3}
            base_priority = weight_order.get(weight, 4)
            if weight == 'high':
                if 'institution_recommendation' in file_type:
                    return (base_priority, 1)
                elif 'stock_news' in file_type:
                    return (base_priority, 2)
            return (base_priority, 0)
        sorted_files = sorted(csv_files.items(), key=sort_priority)
        prompt_parts = []
        stock_code = self._extract_stock_code()
        prompt_parts.append(f'# 股票 {stock_code} 综合数据分析')
        prompt_parts.append('\n以下是该股票的各类数据，请进行综合分析并给出投资建议：\n')
        prompt_parts.append('## 📊 数据概览')
        for i, (file_type, file_info) in enumerate(sorted_files, 1):
            weight_emoji = {'high': '🔥', 'medium': '⭐', 'normal': '📋'}
            emoji = weight_emoji.get(file_info['config']['weight'], '📋')
            prompt_parts.append(f'{i}. {emoji} {self._get_chinese_name(file_type)} ({file_info['filename']})')
        prompt_parts.append('\n## 📈 详细数据\n')
        for i, (file_type, file_info) in enumerate(sorted_files, 1):
            file_path = file_info['file_path']
            config = file_info['config']
            data = self.read_and_process_csv(file_path, config['max_rows'], config['weight'])
            if not data:
                continue
            chinese_name = self._get_chinese_name(file_type)
            priority_label = {'high': '(重点关注)', 'medium': '(重要参考)', 'normal': '(背景信息)'}
            priority = priority_label.get(config['weight'], '')
            prompt_parts.append(f'### Dataset {i}: {chinese_name} {priority}')
            prompt_parts.append(f'文件: {file_info['filename']}')
            prompt_parts.append(f'数据量: {len(data)} 条记录\n')
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            prompt_parts.append('```json')
            prompt_parts.append(json_data)
            prompt_parts.append('```\n')
        prompt_parts.append('## 🎯 分析要求')
        prompt_parts.append('请基于以上数据进行以下分析：')
        prompt_parts.append('1. **价格趋势分析**: 根据股票日线数据分析价格走势')
        prompt_parts.append('2. **技术指标评估**: 结合移动平均线、成交量等技术指标')
        prompt_parts.append('3. **机构观点**: 分析机构评级和目标价')
        prompt_parts.append('4. **市场环境**: 考虑宏观经济数据和行业资金流向')
        prompt_parts.append('5. **新闻影响**: 评估相关新闻对股价的潜在影响')
        prompt_parts.append('6. **投资建议**: 给出明确的买入/持有/卖出建议及理由')
        prompt_parts.append('\n请用中文回答，并提供具体的数据支撑。')
        return '\n'.join(prompt_parts)

    def _extract_stock_code(self) -> str:
        """从目录名提取股票代码"""
        dir_name = self.data_dir.name
        if 'output_' in dir_name:
            return dir_name.replace('output_', '')
        return dir_name

    def _get_chinese_name(self, file_type: str) -> str:
        """获取数据类型的中文名称"""
        name_mapping = {'stock_daily_catl': 'Stock Daily Price Data (股票日线数据)', 'institution_recommendation_catl': 'Institution Recommendations (机构评级)', 'stock_news_catl': 'Stock News (股票新闻)', 'china_cpi': 'China CPI (中国CPI)', 'china_gdp': 'China GDP (中国GDP)', 'industry_fund_flow': 'Industry Fund Flow (行业资金流)', 'market_overview': 'Market Overview (市场概况)', 'regional_indices': 'Regional Indices (区域指数)', 'option_volatility': 'Option Volatility (期权波动率)', 'fund_flow_industry': 'Fund Flow Industry (行业资金流向)'}
        return name_mapping.get(file_type, file_type)

    def save_prompt_to_file(self, output_path: str=None) -> str:
        """保存提示内容到文件"""
        if output_path is None:
            output_path = self.data_dir / 'llm_analysis_prompt.txt'
        prompt_content = self.generate_llm_analysis_prompt()
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(prompt_content)
            file_size = os.path.getsize(output_path)
            print(f'✅ LLM分析提示已保存: {output_path}')
            print(f'📄 文件大小: {file_size:,} 字节')
            return str(output_path)
        except Exception as e:
            print(f'❌ 保存文件失败: {e}')
            return ''

    def get_json_data(self) -> Dict[str, List[Dict]]:
        """直接获取JSON格式的数据字典"""
        csv_files = self.find_csv_files()
        json_data = {}
        for file_type, file_info in csv_files.items():
            config = file_info['config']
            data = self.read_and_process_csv(file_info['file_path'], config['max_rows'], config['weight'])
            if data:
                chinese_name = self._get_chinese_name(file_type)
                json_data[chinese_name] = data
        return json_data

def read_and_process_csv(self, file_path: Path, max_rows: int, weight: str) -> List[Dict]:
    """读取并处理CSV文件"""
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if df.empty:
            print(f'⚠️ 文件为空: {file_path.name}')
            return []
        if weight == 'high':
            processed_df = df.tail(max_rows)
        else:
            processed_df = df.head(max_rows)
        processed_df = processed_df.fillna('')
        records = processed_df.to_dict(orient='records')
        print(f'✅ 处理完成 {file_path.name}: {len(records)} 条记录')
        return records
    except Exception as e:
        print(f'❌ 处理文件失败 {file_path.name}: {e}')
        return []

def convert_csv_to_llm_json(data_dir: str, output_file: str=None) -> str:
    """
    快速转换CSV数据为LLM JSON格式的主函数
    
    Args:
        data_dir (str): 数据目录路径（如 output_300750）
        output_file (str): 输出文件路径（可选）
        
    Returns:
        str: 生成的提示文件路径
        
    Example:
        convert_csv_to_llm_json("output_300750")
        convert_csv_to_llm_json("output_600519", "my_prompt.txt")
    """
    print(f'🔄 开始转换 {data_dir} 中的CSV数据...')
    converter = CSVToLLMConverter(data_dir)
    result_path = converter.save_prompt_to_file(output_file)
    if result_path:
        print(f'✅ 转换完成: {os.path.abspath(result_path)}')
    else:
        print('❌ 转换失败')
    return result_path

def get_stock_data_json(data_dir: str) -> Dict[str, List[Dict]]:
    """
    获取股票数据的JSON格式字典
    
    Args:
        data_dir (str): 数据目录路径（如 output_300750）
        
    Returns:
        Dict[str, List[Dict]]: 包含所有数据的字典
        
    Example:
        data = get_stock_data_json("output_300750")
        print(data.keys())  # 查看所有数据类型
    """
    converter = CSVToLLMConverter(data_dir)
    return converter.get_json_data()

class StockDataFetcher:
    """股票数据抓取器 - 核心功能类"""

    def __init__(self, stock_code, auto_create_output_dir=True):
        """
        初始化数据抓取器
        
        Args:
            stock_code (str): 股票代码（如：300750、000001等）
            auto_create_output_dir (bool): 是否自动创建输出目录，默认True
        """
        self.stock_code = stock_code
        self.symbol_sz = f'sz{stock_code}' if stock_code.startswith('0') or stock_code.startswith('3') else f'sh{stock_code}'
        if auto_create_output_dir:
            self.output_dir = Path(f'output_{stock_code}')
        else:
            self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.stock_name = self._get_stock_name()

    def _get_stock_name(self):
        """获取股票名称"""
        try:
            stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
            if not stock_info.empty:
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    return name_row['value'].iloc[0]
            return f'股票{self.stock_code}'
        except:
            return f'股票{self.stock_code}'

    def get_timestamp(self):
        """获取当前日期用于文件命名"""
        return datetime.datetime.now().strftime('%Y%m%d')

    def save_data(self, data, filename_prefix, description=''):
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据（pandas DataFrame）
            filename_prefix (str): 文件名前缀
            description (str): 数据描述
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            timestamp = self.get_timestamp()
            filename = f'{filename_prefix}_{timestamp}_{self.stock_code}.csv'
            filepath = self.output_dir / filename
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath} (共{len(data)}条记录)')
            else:
                df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath}')
            return str(filepath)
        except Exception as e:
            self.logger.error(f'❌ 保存{description}失败: {str(e)}')
            return None

    def fetch_stock_daily(self, days=30):
        """
        抓取股票日线数据
        
        Args:
            days (int): 抓取最近多少天的数据，默认30天
            
        Returns:
            pandas.DataFrame: 股票日线数据
        """
        try:
            self.logger.info(f'📈 开始抓取{self.stock_code}日线数据...')
            stock_df = ak.stock_zh_a_daily(symbol=self.symbol_sz).reset_index()
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
            recent_data = stock_df[stock_df['date'] >= days_ago]
            self.save_data(recent_data, 'stock_daily_catl', f'{self.stock_code}日线数据')
            return recent_data
        except Exception as e:
            self.logger.error(f'❌ 抓取股票日线数据失败: {str(e)}')
            return None

    def fetch_china_cpi(self):
        """
        抓取中国CPI数据 (限制为过去2年)
        
        Returns:
            pandas.DataFrame: 中国CPI数据
        """
        try:
            self.logger.info('📊 开始抓取中国CPI数据...')
            cpi_df = ak.macro_china_cpi()
            if not cpi_df.empty:
                if '月份' in cpi_df.columns:

                    def convert_chinese_date(date_str):
                        try:
                            if '年' in date_str and '月' in date_str:
                                year = date_str.split('年')[0]
                                month = date_str.split('年')[1].split('月')[0]
                                return f'{year}-{month.zfill(2)}-01'
                            else:
                                return date_str
                        except:
                            return None
                    cpi_df['月份'] = cpi_df['月份'].apply(convert_chinese_date)
                    cpi_df['月份'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
                    cpi_df = cpi_df.dropna(subset=['月份'])
                    if not cpi_df.empty:
                        two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
                        cpi_df = cpi_df[cpi_df['月份'] >= two_years_ago]
                        self.logger.info(f'✅ CPI数据已限制为过去2年: {len(cpi_df)} 条记录')
            return cpi_df
        except Exception as e:
            self.logger.error(f'❌ 抓取CPI数据失败: {str(e)}')
            return None

    def fetch_china_gdp(self):
        """
        抓取中国GDP数据
        
        Returns:
            pandas.DataFrame: 中国GDP数据
        """
        try:
            self.logger.info('📊 开始抓取中国GDP数据...')
            gdp_df = ak.macro_china_gdp_yearly()
            return gdp_df
        except Exception as e:
            self.logger.error(f'❌ 抓取GDP数据失败: {str(e)}')
            return None

    def fetch_industry_fund_flow(self):
        """
        抓取行业资金流数据
        
        Returns:
            pandas.DataFrame: 行业资金流数据
        """
        try:
            self.logger.info('💰 开始抓取行业资金流数据...')
            industry_fund_df = ak.stock_fund_flow_industry()
            return industry_fund_df
        except Exception as e:
            self.logger.error(f'❌ 抓取行业资金流数据失败: {str(e)}')
            return None

    def fetch_stock_news(self):
        """
        抓取个股新闻数据
        
        Returns:
            pandas.DataFrame: 个股新闻数据
        """
        try:
            self.logger.info(f'📰 开始抓取{self.stock_name}({self.stock_code})新闻数据...')
            news_df = ak.stock_news_em(symbol=self.stock_code)
            return news_df
        except Exception as e:
            self.logger.error(f'❌ 抓取新闻数据失败: {str(e)}')
            return None

    def fetch_market_summary(self):
        """
        抓取上交所市场概况
        
        Returns:
            pandas.DataFrame: 市场概况数据
        """
        try:
            self.logger.info('🏛️ 开始抓取上交所市场概况...')
            sse_summary = ak.stock_sse_summary()
            return sse_summary
        except Exception as e:
            self.logger.error(f'❌ 抓取市场概况失败: {str(e)}')
            return None

    def fetch_market_indices(self):
        """
        抓取重要指数行情
        
        Returns:
            pandas.DataFrame: 重要指数数据
        """
        try:
            self.logger.info('📊 开始抓取重要指数行情...')
            market_indices = ak.stock_zh_index_spot_em(symbol='沪深重要指数')
            return market_indices
        except Exception as e:
            self.logger.error(f'❌ 抓取市场指数失败: {str(e)}')
            return None

    def fetch_option_volatility(self):
        """
        抓取50ETF期权波动率指数 (限制为过去1个月)
        
        Returns:
            pandas.DataFrame: 期权波动率数据
        """
        try:
            self.logger.info('📈 开始抓取50ETF波动率指数...')
            vol50 = ak.index_option_50etf_qvix()
            if not vol50.empty:
                if 'date' in vol50.columns:
                    vol50['date'] = pd.to_datetime(vol50['date'])
                    one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    vol50 = vol50[vol50['date'] >= one_month_ago]
                    self.logger.info(f'✅ 期权波动率数据已限制为过去1个月: {len(vol50)} 条记录')
            return vol50
        except Exception as e:
            self.logger.error(f'❌ 抓取期权波动率数据失败: {str(e)}')
            return None

    def fetch_institution_recommendation(self):
        """
        抓取机构评级数据 (限制为过去半年)
        
        Returns:
            pandas.DataFrame: 机构评级数据
        """
        try:
            self.logger.info(f'🏦 开始抓取{self.stock_name}({self.stock_code})机构评级...')
            inst_rec = ak.stock_institute_recommend_detail(symbol=self.stock_code)
            if not inst_rec.empty:
                date_columns = ['评级日期', 'date', '日期']
                date_col = None
                for col in date_columns:
                    if col in inst_rec.columns:
                        date_col = col
                        break
                if date_col:
                    inst_rec[date_col] = pd.to_datetime(inst_rec[date_col])
                    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                    inst_rec = inst_rec[inst_rec[date_col] >= six_months_ago]
                    self.logger.info(f'✅ 机构评级数据已限制为过去半年: {len(inst_rec)} 条记录')
            return inst_rec
        except Exception as e:
            self.logger.error(f'❌ 抓取机构评级数据失败: {str(e)}')
            return None

    def fetch_all_data(self):
        """
        抓取所有类型的数据
        
        Returns:
            dict: 包含所有数据的字典
        """
        self.logger.info('🚀 开始抓取全部数据...')
        results = {}
        tasks = [('stock_daily', lambda: self.fetch_stock_daily(), '股票日线数据'), ('china_cpi', lambda: self.fetch_china_cpi(), '中国CPI数据'), ('china_gdp', lambda: self.fetch_china_gdp(), '中国GDP数据'), ('industry_fund_flow', lambda: self.fetch_industry_fund_flow(), '行业资金流数据'), ('stock_news', lambda: self.fetch_stock_news(), '个股新闻数据'), ('market_summary', lambda: self.fetch_market_summary(), '市场整体概况'), ('market_indices', lambda: self.fetch_market_indices(), '重要指数行情'), ('option_volatility', lambda: self.fetch_option_volatility(), '期权波动率指数'), ('institution_recommendation', lambda: self.fetch_institution_recommendation(), '机构评级数据')]
        for task_name, task_func, description in tasks:
            try:
                self.logger.info(f'\n--- 开始执行: {description} ---')
                result = task_func()
                results[task_name] = result
                if result is not None:
                    filename_mapping = {'stock_daily': 'stock_daily_catl', 'china_cpi': 'china_cpi', 'china_gdp': 'china_gdp_yearly', 'industry_fund_flow': 'industry_fund_flow', 'stock_news': 'stock_news_catl', 'market_summary': 'market_summary_sse', 'market_indices': 'market_indices', 'option_volatility': 'option_volatility_50etf', 'institution_recommendation': 'institution_recommendation_catl'}
                    self.save_data(result, filename_mapping[task_name], description)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f'执行{description}时发生错误: {str(e)}')
                results[task_name] = None
        self.logger.info('🎉 全部数据抓取完成！')
        return results

    def create_data_documentation(self):
        """创建数据文件说明文档"""
        try:
            timestamp = self.get_timestamp()
            doc_content = f'# {self.stock_name}({self.stock_code})数据文件说明\n\n## 📋 文件命名规则\n\n所有数据文件按以下格式命名：\n```\n数据类型_日期_股票代码.csv\n```\n\n例如：`china_cpi_{timestamp}_{self.stock_code}.csv` 表示{timestamp[:4]}年{timestamp[4:6]}月{timestamp[6:8]}日抓取的中国CPI数据，与{self.stock_name}({self.stock_code})相关。\n\n---\n\n## 📊 数据文件详细说明\n\n### 1. 股票日线数据\n**文件名**: `stock_daily_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_a_daily()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘价（元）\n- **high** - 最高价（元）\n- **low** - 最低价（元）\n- **close** - 收盘价（元）\n- **volume** - 成交量（股）\n- **amount** - 成交额（元）\n- **outstanding_share** - 流通股数（股）\n- **turnover** - 换手率\n\n**用途**: 分析{self.stock_name}股价走势、成交情况，进行技术分析\n\n---\n\n### 2. 中国CPI数据\n**文件名**: `china_cpi_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_cpi()\n\n**中文指标说明**:\n- **月份** - 统计月份\n- **全国-当月** - 全国当月CPI指数\n- **全国-同比增长** - 全国CPI同比增长率(%)\n- **全国-环比增长** - 全国CPI环比增长率(%)\n- **全国-累计** - 全国累计CPI指数\n- **城市-当月** - 城市当月CPI指数\n- **城市-同比增长** - 城市CPI同比增长率(%)\n- **城市-环比增长** - 城市CPI环比增长率(%)\n- **城市-累计** - 城市累计CPI指数\n- **农村-当月** - 农村当月CPI指数\n- **农村-同比增长** - 农村CPI同比增长率(%)\n- **农村-环比增长** - 农村CPI环比增长率(%)\n- **农村-累计** - 农村累计CPI指数\n\n**用途**: 反映通胀水平，判断宏观经济环境对{self.stock_name}所在行业的影响\n\n---\n\n### 3. 中国GDP数据\n**文件名**: `china_gdp_yearly_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_gdp_yearly()\n\n**中文指标说明**:\n- **商品** - 数据类型（中国GDP年率报告）\n- **日期** - 发布日期\n- **今值** - 当期GDP增长率(%)\n- **预测值** - 市场预测GDP增长率(%)\n- **前值** - 前期GDP增长率(%)\n\n**用途**: 评估国家经济增长情况，判断宏观经济对{self.stock_name}所在行业需求的影响\n\n---\n\n### 4. 行业资金流数据\n**文件名**: `industry_fund_flow_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_fund_flow_industry()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **行业** - 行业名称\n- **行业指数** - 行业指数代码\n- **行业-涨跌幅** - 行业当日涨跌幅(%)\n- **流入资金** - 资金流入金额（万元）\n- **流出资金** - 资金流出金额（万元）\n- **净额** - 资金净流入金额（万元）\n- **公司家数** - 该行业公司数量\n- **领涨股** - 行业内领涨股票\n- **领涨股-涨跌幅** - 领涨股涨跌幅(%)\n- **当前价** - 领涨股当前价格（元）\n\n**用途**: 分析各行业资金流向，判断{self.stock_name}所在行业的资金关注度\n\n---\n\n### 5. 个股新闻数据\n**文件名**: `stock_news_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_news_em()\n\n**中文指标说明**:\n- **关键词** - 搜索关键词（股票代码）\n- **新闻标题** - 新闻标题\n- **新闻内容** - 新闻摘要/内容\n- **发布时间** - 新闻发布时间\n- **新闻来源** - 新闻来源媒体\n- **新闻链接** - 原文链接地址\n\n**用途**: 获取{self.stock_name}相关新闻资讯，进行舆情分析和基本面研究\n\n---\n\n### 6. 上交所市场概况\n**文件名**: `market_summary_sse_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_sse_summary()\n\n**中文指标说明**:\n- **项目** - 统计项目名称\n- **股票** - 股票相关数据\n- **主板** - 主板市场数据\n- **科创板** - 科创板市场数据\n\n**具体项目包括**:\n- **流通股本** - 流通股总数（亿股）\n- **总市值** - 总市值（亿元）\n- **平均市盈率** - 平均市盈率（倍）\n- **上市公司** - 上市公司数量（家）\n- **上市股票** - 上市股票数量（只）\n- **流通市值** - 流通市值（亿元）\n- **总股本** - 总股本（亿股）\n\n**用途**: 了解整体市场状况，判断市场环境对{self.stock_name}的影响\n\n---\n\n### 7. 重要指数行情\n**文件名**: `market_indices_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_index_spot_em()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **代码** - 指数代码\n- **名称** - 指数名称\n- **最新价** - 最新指数点位\n- **涨跌幅** - 当日涨跌幅(%)\n- **涨跌额** - 当日涨跌点数\n- **成交量** - 成交量（手）\n- **成交额** - 成交金额（万元）\n- **振幅** - 当日振幅(%)\n- **最高** - 当日最高点位\n- **最低** - 当日最低点位\n- **今开** - 今日开盘点位\n- **昨收** - 昨日收盘点位\n- **量比** - 量比\n\n**包含指数**:\n- 上证指数、深证成指、创业板指、科创综指、北证50等\n\n**用途**: 跟踪重要市场指数走势，判断整体市场方向\n\n---\n\n### 8. 50ETF期权波动率指数\n**文件名**: `option_volatility_50etf_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.index_option_50etf_qvix()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘波动率\n- **high** - 最高波动率\n- **low** - 最低波动率\n- **close** - 收盘波动率\n\n**用途**: 反映市场恐慌情绪和波动性预期，是重要的市场情绪指标\n\n---\n\n### 9. 机构评级数据\n**文件名**: `institution_recommendation_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_institute_recommend_detail()\n\n**中文指标说明**:\n- **股票代码** - 股票代码\n- **股票名称** - 股票名称\n- **目标价** - 机构给出的目标价格（元）\n- **最新评级** - 机构最新评级（买入/增持/中性/减持/卖出）\n- **评级机构** - 研究机构名称\n- **分析师** - 分析师姓名\n- **行业** - 所属行业\n- **评级日期** - 评级发布日期\n\n**评级含义**:\n- **买入** - 强烈推荐买入\n- **增持** - 推荐增加持仓\n- **中性** - 维持现有持仓\n- **减持** - 建议减少持仓\n- **卖出** - 建议卖出\n\n**用途**: 了解专业机构对{self.stock_name}的投资建议和价格预期\n\n---\n\n### 10. 数据收集报告\n**文件名**: `collection_report_{timestamp}_{self.stock_code}.csv`\n\n**自动生成的收集统计报告**\n\n**中文指标说明**:\n- **数据类型** - 数据收集任务名称\n- **收集状态** - 收集是否成功（成功/失败）\n- **记录数量** - 成功收集的数据条数\n- **时间戳** - 数据收集完成时间\n\n**用途**: 监控数据收集任务的执行情况，确保数据完整性\n\n---\n\n## 🔍 数据使用建议\n\n### 综合分析框架\n\n1. **宏观经济层面**\n   - 使用CPI、GDP数据判断宏观经济环境\n   - 分析对{self.stock_name}所在行业的影响\n\n2. **市场情绪层面**\n   - 使用期权波动率指数判断市场恐慌程度\n   - 使用重要指数走势判断市场整体方向\n\n3. **行业资金层面**\n   - 使用行业资金流数据判断资金偏好\n   - 关注{self.stock_name}所在行业的资金流向\n\n4. **个股基本面**\n   - 使用机构评级了解专业判断\n   - 使用新闻数据进行舆情分析\n\n5. **技术面分析**\n   - 使用股票日线数据进行技术分析\n   - 结合成交量判断趋势强度\n\n### 数据更新频率\n\n- **日更新**: 股票日线、新闻、指数行情、期权波动率\n- **月更新**: CPI数据\n- **季更新**: GDP数据\n- **实时更新**: 行业资金流、机构评级\n\n---\n\n## ⚠️ 使用注意事项\n\n1. **数据时效性**: 部分数据存在发布延迟，请注意数据的时效性\n2. **数据完整性**: 如遇到数据源问题，某些文件可能缺失，请查看收集报告\n3. **投资风险**: 数据仅供参考，不构成投资建议，投资需谨慎\n4. **版权声明**: 数据来源于公开渠道，请遵守相关使用条款\n\n---\n\n## 📞 技术支持\n\n如有数据解读疑问或技术问题，请参考：\n- akshare官方文档: https://akshare.readthedocs.io/\n- 数据抓取函数库: 本项目中的股票数据抓取函数\n\n**生成时间**: {datetime.datetime.now().strftime('%Y年%m月%d日')}\n**数据版本**: v2.0  \n**适用股票**: {self.stock_name}({self.stock_code})\n'
            doc_filepath = self.output_dir / '数据文件说明.md'
            with open(doc_filepath, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            self.logger.info(f'✅ 数据说明文档已生成: {doc_filepath}')
            return str(doc_filepath)
        except Exception as e:
            self.logger.error(f'❌ 生成数据说明文档失败: {str(e)}')
            return None

def fetch_stock_daily(self, days=30):
    """
        抓取股票日线数据
        
        Args:
            days (int): 抓取最近多少天的数据，默认30天
            
        Returns:
            pandas.DataFrame: 股票日线数据
        """
    try:
        self.logger.info(f'📈 开始抓取{self.stock_code}日线数据...')
        stock_df = ak.stock_zh_a_daily(symbol=self.symbol_sz).reset_index()
        stock_df['date'] = pd.to_datetime(stock_df['date'])
        days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
        recent_data = stock_df[stock_df['date'] >= days_ago]
        self.save_data(recent_data, 'stock_daily_catl', f'{self.stock_code}日线数据')
        return recent_data
    except Exception as e:
        self.logger.error(f'❌ 抓取股票日线数据失败: {str(e)}')
        return None

def fetch_china_cpi(self):
    """
        抓取中国CPI数据 (限制为过去2年)
        
        Returns:
            pandas.DataFrame: 中国CPI数据
        """
    try:
        self.logger.info('📊 开始抓取中国CPI数据...')
        cpi_df = ak.macro_china_cpi()
        if not cpi_df.empty:
            if '月份' in cpi_df.columns:

                def convert_chinese_date(date_str):
                    try:
                        if '年' in date_str and '月' in date_str:
                            year = date_str.split('年')[0]
                            month = date_str.split('年')[1].split('月')[0]
                            return f'{year}-{month.zfill(2)}-01'
                        else:
                            return date_str
                    except:
                        return None
                cpi_df['月份'] = cpi_df['月份'].apply(convert_chinese_date)
                cpi_df['月份'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
                cpi_df = cpi_df.dropna(subset=['月份'])
                if not cpi_df.empty:
                    two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
                    cpi_df = cpi_df[cpi_df['月份'] >= two_years_ago]
                    self.logger.info(f'✅ CPI数据已限制为过去2年: {len(cpi_df)} 条记录')
        return cpi_df
    except Exception as e:
        self.logger.error(f'❌ 抓取CPI数据失败: {str(e)}')
        return None

def fetch_option_volatility(self):
    """
        抓取50ETF期权波动率指数 (限制为过去1个月)
        
        Returns:
            pandas.DataFrame: 期权波动率数据
        """
    try:
        self.logger.info('📈 开始抓取50ETF波动率指数...')
        vol50 = ak.index_option_50etf_qvix()
        if not vol50.empty:
            if 'date' in vol50.columns:
                vol50['date'] = pd.to_datetime(vol50['date'])
                one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                vol50 = vol50[vol50['date'] >= one_month_ago]
                self.logger.info(f'✅ 期权波动率数据已限制为过去1个月: {len(vol50)} 条记录')
        return vol50
    except Exception as e:
        self.logger.error(f'❌ 抓取期权波动率数据失败: {str(e)}')
        return None

def fetch_institution_recommendation(self):
    """
        抓取机构评级数据 (限制为过去半年)
        
        Returns:
            pandas.DataFrame: 机构评级数据
        """
    try:
        self.logger.info(f'🏦 开始抓取{self.stock_name}({self.stock_code})机构评级...')
        inst_rec = ak.stock_institute_recommend_detail(symbol=self.stock_code)
        if not inst_rec.empty:
            date_columns = ['评级日期', 'date', '日期']
            date_col = None
            for col in date_columns:
                if col in inst_rec.columns:
                    date_col = col
                    break
            if date_col:
                inst_rec[date_col] = pd.to_datetime(inst_rec[date_col])
                six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                inst_rec = inst_rec[inst_rec[date_col] >= six_months_ago]
                self.logger.info(f'✅ 机构评级数据已限制为过去半年: {len(inst_rec)} 条记录')
        return inst_rec
    except Exception as e:
        self.logger.error(f'❌ 抓取机构评级数据失败: {str(e)}')
        return None

class StockChartGenerator:
    """股票技术分析图表生成器"""

    def __init__(self, symbol: str, output_dir: str='output'):
        """
        初始化图表生成器
        
        Args:
            symbol (str): 股票代码（如：300750、600519等）
            output_dir (str): 输出目录，默认为"output"
        """
        self.symbol = symbol
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.stock_data = None
        self.processed_data = None

    def generate_mock_data(self) -> pd.DataFrame:
        """生成模拟股票数据用于演示"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
        dates = [d for d in dates if d.weekday() < 5]
        np.random.seed(42)
        base_price = 1500 if self.symbol == '600519' else 100
        prices = []
        current_price = base_price
        for i in range(len(dates)):
            change = np.random.normal(0, 0.02)
            current_price = current_price * (1 + change)
            prices.append(current_price)
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            volatility = close * 0.03
            high = close + np.random.uniform(0, volatility)
            low = close - np.random.uniform(0, volatility)
            open_price = prices[i - 1] if i > 0 else close
            volume = np.random.randint(100000, 1000000)
            data.append({'date': date.strftime('%Y-%m-%d'), 'open': round(open_price, 2), 'high': round(high, 2), 'low': round(low, 2), 'close': round(close, 2), 'volume': volume})
        df = pd.DataFrame(data)
        print(f'生成了 {len(df)} 条模拟数据')
        return df

    def get_stock_data(self) -> pd.DataFrame:
        """获取股票数据"""
        if self.stock_data is not None:
            return self.stock_data
        try:
            import akshare as ak
            print(f'获取股票 {self.symbol} 的数据...')
            try:
                df = ak.stock_zh_a_hist(symbol=self.symbol, period='daily', adjust='qfq')
            except:
                try:
                    formatted_symbol = f'sh{self.symbol}' if self.symbol.startswith('6') else f'sz{self.symbol}'
                    df = ak.stock_zh_a_hist(symbol=formatted_symbol, period='daily', adjust='qfq')
                except:
                    print('获取真实数据失败，使用模拟数据...')
                    return self.generate_mock_data()
            if df.empty:
                return self.generate_mock_data()
            df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'})
            print(f'成功获取 {len(df)} 条真实数据')
            self.stock_data = df.tail(250)
            return self.stock_data
        except Exception as e:
            print(f'获取数据失败，使用模拟数据: {e}')
            return self.generate_mock_data()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = df.copy()
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - 100 / (1 + rs)
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + bb_std * 2
        df['BB_lower'] = df['BB_middle'] - bb_std * 2
        df = df.fillna(method='ffill').fillna(method='bfill')
        self.processed_data = df
        return df

    def create_technical_chart(self) -> Optional[str]:
        """创建技术分析图表"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib import rcParams
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            if self.processed_data is None:
                df = self.get_stock_data()
                df = self.calculate_indicators(df)
            else:
                df = self.processed_data
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            fig, axes = plt.subplots(4, 1, figsize=(15, 20))
            fig.suptitle(f'{self.symbol} 技术分析图表', fontsize=16, fontweight='bold')
            ax1 = axes[0]
            ax1.plot(df['date'], df['close'], label='收盘价', linewidth=2, color='blue')
            ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange')
            ax1.plot(df['date'], df['MA10'], label='MA10', alpha=0.8, color='green')
            ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='red')
            ax1.fill_between(df['date'], df['BB_upper'], df['BB_lower'], alpha=0.1, color='gray', label='布林带')
            ax1.plot(df['date'], df['BB_upper'], alpha=0.5, color='gray', linestyle='--')
            ax1.plot(df['date'], df['BB_lower'], alpha=0.5, color='gray', linestyle='--')
            ax1.set_title('价格走势与技术指标')
            ax1.set_ylabel('价格 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax2 = axes[1]
            colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
            ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7)
            ax2.set_title('成交量')
            ax2.set_ylabel('成交量')
            ax2.grid(True, alpha=0.3)
            ax3 = axes[2]
            ax3.plot(df['date'], df['RSI'], label='RSI', color='purple', linewidth=2)
            ax3.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='超买线(70)')
            ax3.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='超卖线(30)')
            ax3.fill_between(df['date'], 30, 70, alpha=0.1, color='yellow', label='正常区间')
            ax3.set_title('RSI指标')
            ax3.set_ylabel('RSI')
            ax3.set_ylim(0, 100)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            ax4 = axes[3]
            ax4.plot(df['date'], df['MACD'], label='MACD', color='blue', linewidth=2)
            ax4.plot(df['date'], df['MACD_signal'], label='信号线', color='red', linewidth=2)
            colors = ['red' if x > 0 else 'green' for x in df['MACD_histogram']]
            ax4.bar(df['date'], df['MACD_histogram'], color=colors, alpha=0.6, label='MACD柱状图')
            ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax4.set_title('MACD指标')
            ax4.set_ylabel('MACD')
            ax4.set_xlabel('日期')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            for ax in axes:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            plt.tight_layout()
            chart_path = self.output_dir / f'{self.symbol}_technical_charts.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f'📊 技术分析图表已保存: {chart_path}')
            return str(chart_path)
        except ImportError:
            print('⚠️ matplotlib未安装，跳过图表生成')
            return None
        except Exception as e:
            print(f'❌ 生成技术分析图表失败: {e}')
            return None

    def create_candlestick_chart(self) -> Optional[str]:
        """创建K线图（蜡烛图）"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib.patches import Rectangle
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            if self.processed_data is None:
                df = self.get_stock_data()
                df = self.calculate_indicators(df)
            else:
                df = self.processed_data
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').tail(60)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), height_ratios=[3, 1])
            fig.suptitle(f'{self.symbol} K线图分析', fontsize=16, fontweight='bold')
            for i, row in df.iterrows():
                date = row['date']
                open_price = row['open']
                high_price = row['high']
                low_price = row['low']
                close_price = row['close']
                color = 'red' if close_price >= open_price else 'green'
                ax1.plot([date, date], [low_price, high_price], color='black', linewidth=1)
                body_height = abs(close_price - open_price)
                body_bottom = min(open_price, close_price)
                rect = Rectangle((mdates.date2num(date) - 0.3, body_bottom), 0.6, body_height, facecolor=color, alpha=0.8, edgecolor='black', linewidth=0.5)
                ax1.add_patch(rect)
            ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange', linewidth=1.5)
            ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='blue', linewidth=1.5)
            ax1.set_title('K线图与移动平均线')
            ax1.set_ylabel('价格 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
            ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7, width=0.8)
            ax2.set_title('成交量')
            ax2.set_ylabel('成交量')
            ax2.set_xlabel('日期')
            ax2.grid(True, alpha=0.3)
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            plt.tight_layout()
            chart_path = self.output_dir / f'{self.symbol}_candlestick_chart.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f'📊 K线图已保存: {chart_path}')
            return str(chart_path)
        except Exception as e:
            print(f'❌ 生成K线图失败: {e}')
            return None

    def generate_all_charts(self) -> Dict[str, Optional[str]]:
        """生成所有类型的图表"""
        print(f'🚀 生成股票 {self.symbol} 的技术分析图表')
        print('=' * 60)
        print(f'📊 开始分析股票: {self.symbol}')
        print('🔄 获取股票数据...')
        df = self.get_stock_data()
        if df is None:
            print('❌ 无法获取数据')
            return {}
        print('🔢 计算技术指标...')
        self.calculate_indicators(df)
        chart_paths = {}
        print('📊 生成技术分析图表...')
        technical_path = self.create_technical_chart()
        if technical_path:
            chart_paths['technical'] = technical_path
        print('🕯️ 生成K线图...')
        candlestick_path = self.create_candlestick_chart()
        if candlestick_path:
            chart_paths['candlestick'] = candlestick_path
        if chart_paths:
            print(f'✅ 图表生成成功:')
            for chart_type, path in chart_paths.items():
                print(f'   {chart_type}: {os.path.abspath(path)}')
        else:
            print('❌ 图表生成失败')
        return chart_paths

def get_stock_data(self) -> pd.DataFrame:
    """获取股票数据"""
    if self.stock_data is not None:
        return self.stock_data
    try:
        import akshare as ak
        print(f'获取股票 {self.symbol} 的数据...')
        try:
            df = ak.stock_zh_a_hist(symbol=self.symbol, period='daily', adjust='qfq')
        except:
            try:
                formatted_symbol = f'sh{self.symbol}' if self.symbol.startswith('6') else f'sz{self.symbol}'
                df = ak.stock_zh_a_hist(symbol=formatted_symbol, period='daily', adjust='qfq')
            except:
                print('获取真实数据失败，使用模拟数据...')
                return self.generate_mock_data()
        if df.empty:
            return self.generate_mock_data()
        df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'})
        print(f'成功获取 {len(df)} 条真实数据')
        self.stock_data = df.tail(250)
        return self.stock_data
    except Exception as e:
        print(f'获取数据失败，使用模拟数据: {e}')
        return self.generate_mock_data()

def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
    """计算技术指标"""
    df = df.copy()
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - 100 / (1 + rs)
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + bb_std * 2
    df['BB_lower'] = df['BB_middle'] - bb_std * 2
    df = df.fillna(method='ffill').fillna(method='bfill')
    self.processed_data = df
    return df

def create_technical_chart(self) -> Optional[str]:
    """创建技术分析图表"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib import rcParams
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        if self.processed_data is None:
            df = self.get_stock_data()
            df = self.calculate_indicators(df)
        else:
            df = self.processed_data
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        fig, axes = plt.subplots(4, 1, figsize=(15, 20))
        fig.suptitle(f'{self.symbol} 技术分析图表', fontsize=16, fontweight='bold')
        ax1 = axes[0]
        ax1.plot(df['date'], df['close'], label='收盘价', linewidth=2, color='blue')
        ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange')
        ax1.plot(df['date'], df['MA10'], label='MA10', alpha=0.8, color='green')
        ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='red')
        ax1.fill_between(df['date'], df['BB_upper'], df['BB_lower'], alpha=0.1, color='gray', label='布林带')
        ax1.plot(df['date'], df['BB_upper'], alpha=0.5, color='gray', linestyle='--')
        ax1.plot(df['date'], df['BB_lower'], alpha=0.5, color='gray', linestyle='--')
        ax1.set_title('价格走势与技术指标')
        ax1.set_ylabel('价格 (元)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax2 = axes[1]
        colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
        ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7)
        ax2.set_title('成交量')
        ax2.set_ylabel('成交量')
        ax2.grid(True, alpha=0.3)
        ax3 = axes[2]
        ax3.plot(df['date'], df['RSI'], label='RSI', color='purple', linewidth=2)
        ax3.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='超买线(70)')
        ax3.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='超卖线(30)')
        ax3.fill_between(df['date'], 30, 70, alpha=0.1, color='yellow', label='正常区间')
        ax3.set_title('RSI指标')
        ax3.set_ylabel('RSI')
        ax3.set_ylim(0, 100)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax4 = axes[3]
        ax4.plot(df['date'], df['MACD'], label='MACD', color='blue', linewidth=2)
        ax4.plot(df['date'], df['MACD_signal'], label='信号线', color='red', linewidth=2)
        colors = ['red' if x > 0 else 'green' for x in df['MACD_histogram']]
        ax4.bar(df['date'], df['MACD_histogram'], color=colors, alpha=0.6, label='MACD柱状图')
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax4.set_title('MACD指标')
        ax4.set_ylabel('MACD')
        ax4.set_xlabel('日期')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        plt.tight_layout()
        chart_path = self.output_dir / f'{self.symbol}_technical_charts.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f'📊 技术分析图表已保存: {chart_path}')
        return str(chart_path)
    except ImportError:
        print('⚠️ matplotlib未安装，跳过图表生成')
        return None
    except Exception as e:
        print(f'❌ 生成技术分析图表失败: {e}')
        return None

def create_candlestick_chart(self) -> Optional[str]:
    """创建K线图（蜡烛图）"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.patches import Rectangle
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        if self.processed_data is None:
            df = self.get_stock_data()
            df = self.calculate_indicators(df)
        else:
            df = self.processed_data
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').tail(60)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), height_ratios=[3, 1])
        fig.suptitle(f'{self.symbol} K线图分析', fontsize=16, fontweight='bold')
        for i, row in df.iterrows():
            date = row['date']
            open_price = row['open']
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            color = 'red' if close_price >= open_price else 'green'
            ax1.plot([date, date], [low_price, high_price], color='black', linewidth=1)
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            rect = Rectangle((mdates.date2num(date) - 0.3, body_bottom), 0.6, body_height, facecolor=color, alpha=0.8, edgecolor='black', linewidth=0.5)
            ax1.add_patch(rect)
        ax1.plot(df['date'], df['MA5'], label='MA5', alpha=0.8, color='orange', linewidth=1.5)
        ax1.plot(df['date'], df['MA20'], label='MA20', alpha=0.8, color='blue', linewidth=1.5)
        ax1.set_title('K线图与移动平均线')
        ax1.set_ylabel('价格 (元)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' for i in range(len(df))]
        ax2.bar(df['date'], df['volume'], color=colors, alpha=0.7, width=0.8)
        ax2.set_title('成交量')
        ax2.set_ylabel('成交量')
        ax2.set_xlabel('日期')
        ax2.grid(True, alpha=0.3)
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        plt.tight_layout()
        chart_path = self.output_dir / f'{self.symbol}_candlestick_chart.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f'📊 K线图已保存: {chart_path}')
        return str(chart_path)
    except Exception as e:
        print(f'❌ 生成K线图失败: {e}')
        return None

def generate_all_charts(self) -> Dict[str, Optional[str]]:
    """生成所有类型的图表"""
    print(f'🚀 生成股票 {self.symbol} 的技术分析图表')
    print('=' * 60)
    print(f'📊 开始分析股票: {self.symbol}')
    print('🔄 获取股票数据...')
    df = self.get_stock_data()
    if df is None:
        print('❌ 无法获取数据')
        return {}
    print('🔢 计算技术指标...')
    self.calculate_indicators(df)
    chart_paths = {}
    print('📊 生成技术分析图表...')
    technical_path = self.create_technical_chart()
    if technical_path:
        chart_paths['technical'] = technical_path
    print('🕯️ 生成K线图...')
    candlestick_path = self.create_candlestick_chart()
    if candlestick_path:
        chart_paths['candlestick'] = candlestick_path
    if chart_paths:
        print(f'✅ 图表生成成功:')
        for chart_type, path in chart_paths.items():
            print(f'   {chart_type}: {os.path.abspath(path)}')
    else:
        print('❌ 图表生成失败')
    return chart_paths

def generate_stock_charts(symbol: str='300750', output_dir: str='output', chart_types: List[str]=None) -> Dict[str, Optional[str]]:
    """
    生成股票技术分析图表的主函数
    
    Args:
        symbol (str): 股票代码（如：300750、000001、000858等）
        output_dir (str): 输出目录，默认为"output"
        chart_types (List[str]): 图表类型列表，可选 "technical", "candlestick"
                                默认生成所有类型
        
    Returns:
        Dict[str, Optional[str]]: 生成的图表路径字典
        
    Example:
        # 生成宁德时代的所有图表
        charts = generate_stock_charts("300750")
        
        # 只生成K线图
        charts = generate_stock_charts("600519", chart_types=["candlestick"])
        
        # 生成到指定目录
        charts = generate_stock_charts("000001", output_dir="my_charts")
    """
    if chart_types is None:
        chart_types = ['technical', 'candlestick']
    generator = StockChartGenerator(symbol, output_dir)
    if set(chart_types) == {'technical', 'candlestick'}:
        return generator.generate_all_charts()
    print(f'🚀 生成股票 {symbol} 的指定图表类型')
    print('=' * 60)
    chart_paths = {}
    df = generator.get_stock_data()
    if df is None:
        print('❌ 无法获取数据')
        return {}
    generator.calculate_indicators(df)
    if 'technical' in chart_types:
        print('📊 生成技术分析图表...')
        technical_path = generator.create_technical_chart()
        if technical_path:
            chart_paths['technical'] = technical_path
    if 'candlestick' in chart_types:
        print('🕯️ 生成K线图...')
        candlestick_path = generator.create_candlestick_chart()
        if candlestick_path:
            chart_paths['candlestick'] = candlestick_path
    if chart_paths:
        print(f'✅ 图表生成成功:')
        for chart_type, path in chart_paths.items():
            print(f'   {chart_type}: {os.path.abspath(path)}')
    else:
        print('❌ 图表生成失败')
    return chart_paths

class CSVToLLMConverter:
    """CSV转LLM JSON格式转换器"""

    def __init__(self, data_dir: str):
        """
        初始化转换器
        
        Args:
            data_dir (str): 数据目录路径（如 output_300750）
        """
        self.data_dir = Path(data_dir)
        self.file_priority = {'stock_daily_catl': {'weight': 'high', 'max_rows': 30}, 'institution_recommendation_catl': {'weight': 'high', 'max_rows': 20}, 'stock_news_catl': {'weight': 'high', 'max_rows': 15}, 'china_cpi': {'weight': 'medium', 'max_rows': 10}, 'china_gdp': {'weight': 'medium', 'max_rows': 10}, 'industry_fund_flow': {'weight': 'medium', 'max_rows': 15}, 'market_overview': {'weight': 'normal', 'max_rows': 5}, 'regional_indices': {'weight': 'normal', 'max_rows': 10}, 'option_volatility': {'weight': 'normal', 'max_rows': 8}, 'fund_flow_industry': {'weight': 'normal', 'max_rows': 12}}

    def find_csv_files(self) -> Dict[str, Dict]:
        """查找并分类CSV文件"""
        csv_files = {}
        if not self.data_dir.exists():
            print(f'❌ 数据目录不存在: {self.data_dir}')
            return csv_files
        for file_path in self.data_dir.glob('*.csv'):
            filename = file_path.name
            if 'collection_report' in filename.lower():
                continue
            file_type = self._identify_file_type(filename)
            if file_type:
                csv_files[file_type] = {'file_path': file_path, 'filename': filename, 'config': self.file_priority.get(file_type, {'weight': 'normal', 'max_rows': 10})}
        return csv_files

    def _identify_file_type(self, filename: str) -> Optional[str]:
        """根据文件名识别数据类型"""
        filename_lower = filename.lower()
        type_mapping = {'stock_daily_catl': ['stock_daily'], 'institution_recommendation_catl': ['institution_recommendation'], 'stock_news_catl': ['stock_news'], 'china_cpi': ['china_cpi'], 'china_gdp': ['china_gdp'], 'industry_fund_flow': ['industry_fund_flow'], 'market_overview': ['market_overview'], 'regional_indices': ['regional_indices'], 'option_volatility': ['option_volatility'], 'fund_flow_industry': ['fund_flow_industry']}
        for file_type, keywords in type_mapping.items():
            if any((keyword in filename_lower for keyword in keywords)):
                return file_type
        return None

    def read_and_process_csv(self, file_path: Path, max_rows: int, weight: str) -> List[Dict]:
        """读取并处理CSV文件"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            if df.empty:
                print(f'⚠️ 文件为空: {file_path.name}')
                return []
            if weight == 'high':
                processed_df = df.tail(max_rows)
            else:
                processed_df = df.head(max_rows)
            processed_df = processed_df.fillna('')
            records = processed_df.to_dict(orient='records')
            print(f'✅ 处理完成 {file_path.name}: {len(records)} 条记录')
            return records
        except Exception as e:
            print(f'❌ 处理文件失败 {file_path.name}: {e}')
            return []

    def generate_llm_analysis_prompt(self) -> str:
        """生成适合LLM分析的提示格式"""
        csv_files = self.find_csv_files()
        if not csv_files:
            return 'No valid CSV files found in the specified directory.'

        def sort_priority(item):
            file_type, file_info = item
            weight = file_info['config']['weight']
            if 'stock_daily_catl' in file_type:
                return (0, 0)
            weight_order = {'high': 1, 'medium': 2, 'normal': 3}
            base_priority = weight_order.get(weight, 4)
            if weight == 'high':
                if 'institution_recommendation' in file_type:
                    return (base_priority, 1)
                elif 'stock_news' in file_type:
                    return (base_priority, 2)
            return (base_priority, 0)
        sorted_files = sorted(csv_files.items(), key=sort_priority)
        prompt_parts = []
        stock_code = self._extract_stock_code()
        prompt_parts.append(f'# 股票 {stock_code} 综合数据分析')
        prompt_parts.append('\n以下是该股票的各类数据，请进行综合分析并给出投资建议：\n')
        prompt_parts.append('## 📊 数据概览')
        for i, (file_type, file_info) in enumerate(sorted_files, 1):
            weight_emoji = {'high': '🔥', 'medium': '⭐', 'normal': '📋'}
            emoji = weight_emoji.get(file_info['config']['weight'], '📋')
            prompt_parts.append(f'{i}. {emoji} {self._get_chinese_name(file_type)} ({file_info['filename']})')
        prompt_parts.append('\n## 📈 详细数据\n')
        for i, (file_type, file_info) in enumerate(sorted_files, 1):
            file_path = file_info['file_path']
            config = file_info['config']
            data = self.read_and_process_csv(file_path, config['max_rows'], config['weight'])
            if not data:
                continue
            chinese_name = self._get_chinese_name(file_type)
            priority_label = {'high': '(重点关注)', 'medium': '(重要参考)', 'normal': '(背景信息)'}
            priority = priority_label.get(config['weight'], '')
            prompt_parts.append(f'### Dataset {i}: {chinese_name} {priority}')
            prompt_parts.append(f'文件: {file_info['filename']}')
            prompt_parts.append(f'数据量: {len(data)} 条记录\n')
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            prompt_parts.append('```json')
            prompt_parts.append(json_data)
            prompt_parts.append('```\n')
        prompt_parts.append('## 🎯 分析要求')
        prompt_parts.append('请基于以上数据进行以下分析：')
        prompt_parts.append('1. **价格趋势分析**: 根据股票日线数据分析价格走势')
        prompt_parts.append('2. **技术指标评估**: 结合移动平均线、成交量等技术指标')
        prompt_parts.append('3. **机构观点**: 分析机构评级和目标价')
        prompt_parts.append('4. **市场环境**: 考虑宏观经济数据和行业资金流向')
        prompt_parts.append('5. **新闻影响**: 评估相关新闻对股价的潜在影响')
        prompt_parts.append('6. **投资建议**: 给出明确的买入/持有/卖出建议及理由')
        prompt_parts.append('\n请用中文回答，并提供具体的数据支撑。')
        return '\n'.join(prompt_parts)

    def _extract_stock_code(self) -> str:
        """从目录名提取股票代码"""
        dir_name = self.data_dir.name
        if 'output_' in dir_name:
            return dir_name.replace('output_', '')
        return dir_name

    def _get_chinese_name(self, file_type: str) -> str:
        """获取数据类型的中文名称"""
        name_mapping = {'stock_daily_catl': 'Stock Daily Price Data (股票日线数据)', 'institution_recommendation_catl': 'Institution Recommendations (机构评级)', 'stock_news_catl': 'Stock News (股票新闻)', 'china_cpi': 'China CPI (中国CPI)', 'china_gdp': 'China GDP (中国GDP)', 'industry_fund_flow': 'Industry Fund Flow (行业资金流)', 'market_overview': 'Market Overview (市场概况)', 'regional_indices': 'Regional Indices (区域指数)', 'option_volatility': 'Option Volatility (期权波动率)', 'fund_flow_industry': 'Fund Flow Industry (行业资金流向)'}
        return name_mapping.get(file_type, file_type)

    def save_prompt_to_file(self, output_path: str=None) -> str:
        """保存提示内容到文件"""
        if output_path is None:
            output_path = self.data_dir / 'llm_analysis_prompt.txt'
        prompt_content = self.generate_llm_analysis_prompt()
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(prompt_content)
            file_size = os.path.getsize(output_path)
            print(f'✅ LLM分析提示已保存: {output_path}')
            print(f'📄 文件大小: {file_size:,} 字节')
            return str(output_path)
        except Exception as e:
            print(f'❌ 保存文件失败: {e}')
            return ''

    def get_json_data(self) -> Dict[str, List[Dict]]:
        """直接获取JSON格式的数据字典"""
        csv_files = self.find_csv_files()
        json_data = {}
        for file_type, file_info in csv_files.items():
            config = file_info['config']
            data = self.read_and_process_csv(file_info['file_path'], config['max_rows'], config['weight'])
            if data:
                chinese_name = self._get_chinese_name(file_type)
                json_data[chinese_name] = data
        return json_data

def read_and_process_csv(self, file_path: Path, max_rows: int, weight: str) -> List[Dict]:
    """读取并处理CSV文件"""
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if df.empty:
            print(f'⚠️ 文件为空: {file_path.name}')
            return []
        if weight == 'high':
            processed_df = df.tail(max_rows)
        else:
            processed_df = df.head(max_rows)
        processed_df = processed_df.fillna('')
        records = processed_df.to_dict(orient='records')
        print(f'✅ 处理完成 {file_path.name}: {len(records)} 条记录')
        return records
    except Exception as e:
        print(f'❌ 处理文件失败 {file_path.name}: {e}')
        return []

def convert_csv_to_llm_json(data_dir: str, output_file: str=None) -> str:
    """
    快速转换CSV数据为LLM JSON格式的主函数
    
    Args:
        data_dir (str): 数据目录路径（如 output_300750）
        output_file (str): 输出文件路径（可选）
        
    Returns:
        str: 生成的提示文件路径
        
    Example:
        convert_csv_to_llm_json("output_300750")
        convert_csv_to_llm_json("output_600519", "my_prompt.txt")
    """
    print(f'🔄 开始转换 {data_dir} 中的CSV数据...')
    converter = CSVToLLMConverter(data_dir)
    result_path = converter.save_prompt_to_file(output_file)
    if result_path:
        print(f'✅ 转换完成: {os.path.abspath(result_path)}')
    else:
        print('❌ 转换失败')
    return result_path

def get_stock_data_json(data_dir: str) -> Dict[str, List[Dict]]:
    """
    获取股票数据的JSON格式字典
    
    Args:
        data_dir (str): 数据目录路径（如 output_300750）
        
    Returns:
        Dict[str, List[Dict]]: 包含所有数据的字典
        
    Example:
        data = get_stock_data_json("output_300750")
        print(data.keys())  # 查看所有数据类型
    """
    converter = CSVToLLMConverter(data_dir)
    return converter.get_json_data()

class TestStorageHandler(unittest.TestCase):
    """
    Test suite for StorageHandler's database operations on Workflow, Agent, and History.
    Uses an in-memory SQLite database for isolated testing.
    """

    def setUp(self):
        """
        Set up the test environment by initializing StorageHandler with an in-memory SQLite database.
        """
        db_config = DBConfig(db_name='sqlite', path=':memory:')
        store_config = StoreConfig(dbConfig=db_config)
        self.storage = StorageHandler(storageConfig=store_config)
        self.agent_data = {'name': 'test_agent', 'content': {'role': 'assistant', 'settings': {'active': True}}, 'date': '2025-05-13'}
        self.workflow_data = {'name': 'test_workflow', 'content': {'class_name': 'WorkFlowGraph', 'goal': 'Generate html code for the Tetris game that can be played in the browser.', 'nodes': [{'class_name': 'WorkFlowNode', 'name': 'game_structure_design', 'description': "Create an outline of the Tetris game's structure, including the main game area, score display, and control buttons.", 'inputs': [{'class_name': 'Parameter', 'name': 'goal', 'type': 'string', 'description': "The user's goal in textual format.", 'required': True}], 'outputs': [{'class_name': 'Parameter', 'name': 'html_structure', 'type': 'string', 'description': 'The basic HTML structure outlining the game area, score display, and buttons.', 'required': True}], 'reason': 'This sub-task establishes the foundational layout required for a functional Tetris game in HTML.', 'agents': [{'name': 'tetris_game_structure_agent', 'description': "This agent creates the basic HTML structure for the Tetris game, including the game area, score display, and control buttons based on the user's goal.", 'inputs': [{'name': 'goal', 'type': 'string', 'description': "The user's goal in textual format.", 'required': True}], 'outputs': [{'name': 'html_structure', 'type': 'string', 'description': 'The basic HTML structure outlining the game area, score display, and buttons.', 'required': True}], 'prompt': "### Objective\nCreate the basic HTML structure for a Tetris game, incorporating the main game area, score display, and control buttons based on the user's goal.\n\n### Instructions\n1. Read the user's goal: <input>{goal}</input>\n2. Design the main game area where the Tetris pieces will fall.\n3. Create an element to display the current score.\n4. Include buttons to control the game (e.g., start, pause, reset).\n5. Assemble these elements into a coherent HTML structure that can be utilized in a web environment.\n6. Output the generated HTML structure.\n\n### Output Format\nYour final output should ALWAYS in the following format:\n\n## Thought\nBriefly explain the reasoning process for creating the HTML structure of the Tetris game.\n\n## html_structure\nThe basic HTML structure outlining the game area, score display, and buttons."}], 'status': 'pending'}, {'class_name': 'WorkFlowNode', 'name': 'style_application', 'description': 'Add CSS styles to the HTML structure for visual aesthetics and layout to make the game look visually appealing.', 'inputs': [{'class_name': 'Parameter', 'name': 'html_structure', 'type': 'string', 'description': 'The basic HTML structure of the Tetris game.', 'required': True}], 'outputs': [{'class_name': 'Parameter', 'name': 'styled_game', 'type': 'string', 'description': 'The styled HTML code that includes CSS for the Tetris game.', 'required': True}], 'reason': 'Styling is essential for enhancing the user experience and ensuring the game is visually organized and engaging.', 'agents': [{'name': 'css_style_application_agent', 'description': 'This agent applies CSS styles to the given HTML structure to create a visually appealing layout for the Tetris game.', 'inputs': [{'name': 'html_structure', 'type': 'string', 'description': 'The basic HTML structure of the Tetris game.', 'required': True}], 'outputs': [{'name': 'styled_game', 'type': 'string', 'description': 'The styled HTML code that includes CSS for the Tetris game.', 'required': True}], 'prompt': '### Objective\nEnhance the provided HTML structure by applying CSS styles to create a visually appealing layout for the Tetris game.\n\n### Instructions\n1. Begin with the provided HTML structure: <input>{html_structure}</input>\n2. Analyze the elements in the HTML to decide the appropriate CSS styles that will enhance its appearance.\n3. Write CSS styles that cater to visual aesthetics such as colors, fonts, borders, and spacing.\n4. Integrate the CSS styles into the HTML structure properly.\n5. Ensure the output is a well-formatted HTML document that includes the applied CSS styles.\n\n### Output Format\nYour final output should ALWAYS in the following format:\n\n## Thought\nBriefly explain the reasoning process for achieving the objective.\n\n## styled_game\nThe styled HTML code that includes CSS for the Tetris game.'}], 'status': 'pending'}, {'class_name': 'WorkFlowNode', 'name': 'game_logic_implementation', 'description': 'Implement the JavaScript logic for the Tetris game, including piece movement, collision detection, and score tracking.', 'inputs': [{'class_name': 'Parameter', 'name': 'styled_game', 'type': 'string', 'description': 'The styled HTML code for the Tetris game.', 'required': True}], 'outputs': [{'class_name': 'Parameter', 'name': 'complete_game_code', 'type': 'string', 'description': 'The complete HTML, CSS, and JavaScript code for a functional Tetris game.', 'required': True}], 'reason': 'This sub-task is crucial for making the game interactive and functional, allowing users to play.', 'agents': [{'name': 'tetris_logic_agent', 'description': 'This agent implements the JavaScript logic required for the Tetris game, ensuring piece movements, collision detection, and score tracking functionalities are properly integrated.', 'inputs': [{'name': 'styled_game', 'type': 'string', 'description': 'The styled HTML code for the Tetris game.', 'required': True}], 'outputs': [{'name': 'complete_game_code', 'type': 'string', 'description': 'The complete HTML, CSS, and JavaScript code for a functional Tetris game.', 'required': True}], 'prompt': "### Objective\nImplement the JavaScript logic for the Tetris game, ensuring functionalities for piece movement, collision detection, and score tracking are included in the output.\n\n### Instructions\n1. Analyze the styled HTML code provided: <input>{styled_game}</input>\n2. Develop JavaScript functions that handle the movement of Tetris pieces, including left, right, and rotation controls.\n3. Implement collision detection logic to ensure pieces do not fall through the bottom or collide with existing pieces.\n4. Create a scoring system that tracks the player's progress and updates the score based on cleared lines.\n5. Combine the JavaScript logic with the existing styled HTML to create a complete game code output.\n\n### Output Format\nYour final output should ALWAYS in the following format:\n\n## Thought\nBriefly explain the reasoning process for implementing the game logic for Tetris.\n\n## complete_game_code\nThe completed HTML, CSS, and JavaScript code for a functional Tetris game."}], 'status': 'pending'}, {'class_name': 'WorkFlowNode', 'name': 'testing_and_refinement', 'description': 'Test the generated Tetris game for bugs and usability issues, refining the code as necessary.', 'inputs': [{'class_name': 'Parameter', 'name': 'complete_game_code', 'type': 'string', 'description': 'The complete HTML, CSS, and JavaScript code for the Tetris game.', 'required': True}], 'outputs': [{'class_name': 'Parameter', 'name': 'final_output', 'type': 'string', 'description': 'The final tested and refined code for the Tetris game.', 'required': True}], 'reason': 'Testing is vital to ensure that the game functions correctly across different browsers and provides a smooth user experience.', 'agents': [{'name': 'tetris_game_testing_agent', 'description': 'This agent tests the generated Tetris game code for functionality, identifies bugs, and provides refinements as needed to ensure smooth gameplay and usability.', 'inputs': [{'name': 'complete_game_code', 'type': 'string', 'description': 'The complete HTML, CSS, and JavaScript code for the Tetris game.', 'required': True}], 'outputs': [{'name': 'final_output', 'type': 'string', 'description': 'The final tested and refined code for the Tetris game.', 'required': True}], 'prompt': '### Objective\nTest the complete Tetris game code for bugs and usability issues, and refine the code as necessary for improved performance.\n\n### Instructions\n1. Load the complete game code: <input>{complete_game_code}</input> into a browser.\n2. Test the game functionality, focusing on user controls, collision detection, and game progression.\n3. Identify any bugs or usability issues that arise during testing.\n4. Document the identified issues and make necessary adjustments to the code to resolve them.\n5. Ensure that the final code adheres to best practices for HTML, CSS, and JavaScript.\n6. Output the refined and tested code as the final result.\n\n### Output Format\nYour final output should ALWAYS in the following format:\n\n## Thought\nBriefly explain the reasoning process for testing and refining the Tetris game code.\n\n## final_output\nThe final tested and refined code for the Tetris game.'}], 'status': 'pending'}], 'edges': [{'class_name': 'WorkFlowEdge', 'source': 'game_structure_design', 'target': 'style_application', 'priority': 0}, {'class_name': 'WorkFlowEdge', 'source': 'style_application', 'target': 'game_logic_implementation', 'priority': 0}, {'class_name': 'WorkFlowEdge', 'source': 'game_logic_implementation', 'target': 'testing_and_refinement', 'priority': 0}], 'graph': None}, 'date': '2025-05-13'}
        self.history_data = {'memory_id': 'mem_001', 'old_memory': 'Initial content', 'new_memory': 'Updated content', 'event': 'update', 'created_at': '2025-05-13T09:00:00', 'updated_at': '2025-05-13T09:30:00'}

    def test_save_and_load_agent(self):
        """
        Test saving and loading an agent, verifying data integrity and JSON parsing.
        """
        self.storage.save_agent(self.agent_data)
        self.storage.save_agent(self.agent_data, 'nihao')
        loaded = self.storage.load_agent('test_agent')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['name'], 'test_agent')
        self.assertEqual(loaded['content'], self.agent_data['content'])
        self.assertEqual(loaded['date'], '2025-05-13')

    def test_save_and_load_workflow(self):
        """
        Test saving and loading a workflow, verifying data integrity and JSON parsing.
        """
        self.storage.save_workflow(self.workflow_data)
        loaded = self.storage.load_workflow('test_workflow')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['name'], 'test_workflow')
        self.assertEqual(loaded['content'], self.workflow_data['content'])
        self.assertEqual(loaded['date'], '2025-05-13')

    def test_save_and_load_history(self):
        """
        Test saving and loading a history entry, verifying data integrity.
        """
        self.storage.save_history(self.history_data)
        loaded = self.storage.load_history('mem_001')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['memory_id'], 'mem_001')
        self.assertEqual(loaded['old_memory'], 'Initial content')
        self.assertEqual(loaded['new_memory'], 'Updated content')
        self.assertEqual(loaded['event'], 'update')
        self.assertEqual(loaded['created_at'], '2025-05-13T09:00:00')
        self.assertEqual(loaded['updated_at'], '2025-05-13T09:30:00')

    def test_load_non_existent_agent(self):
        """
        Test loading a non-existent agent returns None.
        """
        loaded = self.storage.load_agent('non_existent_agent')
        self.assertIsNone(loaded)

    def test_load_non_existent_workflow(self):
        """
        Test loading a non-existent workflow returns None.
        """
        loaded = self.storage.load_workflow('non_existent_workflow')
        self.assertIsNone(loaded)

    def test_load_non_existent_history(self):
        """
        Test loading a non-existent history entry returns None.
        """
        loaded = self.storage.load_history('non_existent_mem')
        self.assertIsNone(loaded)

    def test_save_invalid_agent(self):
        """
        Test saving an agent without a 'name' field raises ValueError.
        """
        invalid_data = {'content': {'role': 'assistant'}, 'date': '2025-05-13'}
        with self.assertRaises(ValueError):
            self.storage.save_agent(invalid_data)

    def test_save_invalid_workflow(self):
        """
        Test saving a workflow without a 'name' field raises ValueError.
        """
        invalid_data = {'content': {'steps': ['step1']}, 'date': '2025-05-13'}
        with self.assertRaises(ValueError):
            self.storage.save_workflow(invalid_data)

    def test_save_invalid_history(self):
        """
        Test saving a history entry without a 'memory_id' field raises ValueError.
        """
        invalid_data = {'old_memory': 'Initial', 'new_memory': 'Updated', 'event': 'update'}
        with self.assertRaises(ValueError):
            self.storage.save_history(invalid_data)

    def test_remove_agent(self):
        """
        Test removing an agent and verify it's no longer loadable.
        """
        self.storage.save_agent(self.agent_data)
        self.storage.remove_agent('test_agent')
        loaded = self.storage.load_agent('test_agent')
        self.assertIsNone(loaded)

    def test_remove_non_existent_agent(self):
        """
        Test removing a non-existent agent raises ValueError.
        """
        with self.assertRaises(ValueError):
            self.storage.remove_agent('non_existent_agent')

    def test_update_agent(self):
        """
        Test updating an existing agent's data.
        """
        self.storage.save_agent(self.agent_data)
        updated_data = {'name': 'test_agent', 'content': {'role': 'admin', 'settings': {'active': False}}, 'date': '2025-05-14'}
        self.storage.save_agent(updated_data)
        loaded = self.storage.load_agent('test_agent')
        self.assertEqual(loaded['content'], updated_data['content'])
        self.assertEqual(loaded['date'], '2025-05-14')

    def test_update_workflow(self):
        """
        Test updating an existing workflow's data.
        """
        self.storage.save_workflow(self.workflow_data)
        updated_data = {'name': 'test_workflow', 'content': {'test': True}, 'date': '2025-05-15'}
        self.storage.save_workflow(updated_data)
        loaded = self.storage.load_workflow('test_workflow')
        self.assertEqual(loaded['content'], updated_data['content'])
        self.assertEqual(loaded['date'], '2025-05-15')

    def test_update_history(self):
        """
        Test updating an existing history entry.
        """
        self.storage.save_history(self.history_data)
        updated_data = {'memory_id': 'mem_001', 'old_memory': 'Initial content', 'new_memory': 'Further updated content', 'event': 'modify', 'created_at': '2025-05-13T09:00:00', 'updated_at': '2025-05-13T10:00:00'}
        self.storage.save_history(updated_data)
        loaded = self.storage.load_history('mem_001')
        self.assertEqual(loaded['new_memory'], 'Further updated content')
        self.assertEqual(loaded['event'], 'modify')
        self.assertEqual(loaded['updated_at'], '2025-05-13T10:00:00')

    def test_bulk_save_and_load(self):
        """
        Test saving multiple records to all tables and loading them.
        """
        agent_data2 = {'name': 'test_agent2', 'content': {'role': 'user', 'settings': {'active': True}}, 'date': '2025-05-13'}
        workflow_data2 = {'name': 'test_workflow2', 'content': {'steps': ['stepA', 'stepB'], 'config': {'timeout': 45}}, 'date': '2025-05-13'}
        history_data2 = {'memory_id': 'mem_002', 'old_memory': 'Old content', 'new_memory': 'New content', 'event': 'create', 'created_at': '2025-05-13T10:00:00', 'updated_at': '2025-05-13T10:00:00'}
        bulk_data = {TableType.store_agent.value: [self.agent_data, agent_data2], TableType.store_workflow.value: [self.workflow_data, workflow_data2], TableType.store_history.value: [self.history_data, history_data2]}
        self.storage.save(bulk_data)
        all_data = self.storage.load()
        self.assertIn(TableType.store_agent.value, all_data)
        self.assertIn(TableType.store_workflow.value, all_data)
        self.assertIn(TableType.store_history.value, all_data)
        self.assertEqual(len(all_data[TableType.store_agent.value]), 2)
        self.assertEqual(len(all_data[TableType.store_workflow.value]), 2)
        self.assertEqual(len(all_data[TableType.store_history.value]), 2)
        agent_names = [record['name'] for record in all_data[TableType.store_agent.value]]
        self.assertIn('test_agent', agent_names)
        self.assertIn('test_agent2', agent_names)
        workflow_names = [record['name'] for record in all_data[TableType.store_workflow.value]]
        self.assertIn('test_workflow', workflow_names)
        self.assertIn('test_workflow2', workflow_names)
        history_ids = [record['memory_id'] for record in all_data[TableType.store_history.value]]
        self.assertIn('mem_001', history_ids)
        self.assertIn('mem_002', history_ids)

    def test_save_invalid_table(self):
        """
        Test saving data to an unknown table raises ValueError.
        """
        invalid_data = {'unknown_table': [self.agent_data]}
        with self.assertRaises(ValueError):
            self.storage.save(invalid_data)

    def tearDown(self):
        """
        Clean up by closing the database connection.
        """
        self.storage.storageDB.connection.close()

def tearDown(self):
    """
        Clean up by closing the database connection.
        """
    self.storage.storageDB.connection.close()

