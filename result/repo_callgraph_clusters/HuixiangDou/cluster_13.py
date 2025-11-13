# Cluster 13

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Reconstruct group chat.')
    parser.add_argument('--output_dir', type=str, default='groups', help='Splitted group messages.')
    parser.add_argument('--input', type=str, default='/home/khj/github/huixiangdou/tests/history_recv_send.txt', help='Raw input messages.')
    parser.add_argument('--action', type=str, default='intention', help='"split"): split raw input into group messages; "intention"): decide which query being a question')
    args = parser.parse_args()
    return args

def main():
    """
    split: 把单个群聊文件，划分成多个。
    intention: 用 LLM 计算 is_question cr_need
    """
    args = parse_args()
    if args.action == 'split':
        split(args.input, args.output_dir)
    elif args.action == 'intention':
        intention(args.output_dir)

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Annotate and metric LLM with CR task.')
    parser.add_argument('--group-id', type=str, default='20814553575', help='Group ID')
    parser.add_argument('--input', type=str, default='/home/khj/github/huixiangdou/tests/history_recv_send.txt', help='Raw input messages.')
    parser.add_argument('--action', type=str, default='metric', help='"annotate"): manually annotate query; "metric"): test with LLM and metric')
    parser.add_argument('--llm-type', type=str, default='Qwen1.5-1.8B-Chat', help='LLM type, use qwen moe by default.')
    args = parser.parse_args()
    return args

def make_parser():
    parser = argparse.ArgumentParser('Doc link checker')
    parser.add_argument('--http', default=False, type=bool, help='check http or not ')
    parser.add_argument('--target', default='./docs', type=str, help='the directory or file to check')
    return parser

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description='OpenXLabWorker.')
    parser.add_argument('work_dir', type=str, help='Working directory.')
    parser.add_argument('--config_path', default='config.ini', help='OpenXLabWorker configuration path. Default value is config.ini')
    return parser.parse_args()

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Gradio UI for parallel/serial pipeline.')
    parser.add_argument('--work_dir', type=str, default='workdir', help='Working directory.')
    parser.add_argument('--pipeline-count', type=int, default=2, help='Support user choosing all pipeline types.')
    parser.add_argument('--config_path', default='config.ini', type=str, help='Pipeline configuration path. Default value is config.ini')
    parser.add_argument('--no-standalone', action='store_false', dest='standalone', help='Do not auto deploy required Hybrid LLM Service.')
    parser.add_argument('--placeholder', type=str, default='How to install HuixiangDou ?', help='Placeholder for user query.')
    parser.add_argument('--image', action='store_true', default=True, help='')
    parser.add_argument('--no-image', action='store_false', dest='image', help='Close some components for readthedocs.')
    parser.add_argument('--theme', type=str, default='soft', help='Gradio theme, default value is `soft`. Open https://www.gradio.app/guides/theming-guide for all themes.')
    args = parser.parse_args()
    return args

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='SerialPipeline.')
    parser.add_argument('--work_dir', type=str, default='workdir', help='Working directory.')
    parser.add_argument('--config_path', default='config.ini', type=str, help='SerialPipeline configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Serial or Parallel Pipeline.')
    parser.add_argument('--work_dir', type=str, default='workdir', help='Working directory.')
    parser.add_argument('--config_path', default='config.ini', type=str, help='Configuration path. Default value is config.ini')
    parser.add_argument('--pipeline', type=str, choices=['chat_with_repo', 'chat_in_group'], default='chat_with_repo', help='Select pipeline type for difference scenario, default value is `chat_with_repo`')
    parser.add_argument('--port', type=int, default=23333, help='Bind port, use 23333 by default.')
    args = parser.parse_args()
    return args

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Lark group for save group message.')
    parser.add_argument('--port', type=int, default=6666, help='Listen port for lark group message. Use 6666 by default.')
    parser.add_argument('--config_path', default='config.ini', type=str, help='Lark group configuration path. Default value is config.ini')
    return parser.parse_args()

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='wechat server.')
    parser.add_argument('--work_dir', type=str, default='workdir', help='Working directory.')
    parser.add_argument('--config_path', default='config.ini', type=str, help='Configuration path. Default value is config.ini')
    parser.add_argument('--login', action='store_true', default=False, help='Login wkteam')
    parser.add_argument('--serve', action='store_true', default=True, help='Bind port and listen WeChat message callback')
    parser.add_argument('--forward', action='store_true', default=False, help='Forward all message to all groups')
    args = parser.parse_args()
    return args

def parse_args():
    """Parse command-line arguments.

    Please `export LOGURU_LEVEL=WARNING` before running.
    """
    parser = argparse.ArgumentParser(description='Knowledge graph for processing directories.')
    parser.add_argument('--repo_dir', type=str, default='repodir', help='Root directory where the docs are located.')
    parser.add_argument('--config_path', default='config.ini', help='Configuration path. Default value is config.ini')
    parser.add_argument('--override', action='store_true', default=False, help='Remove old data and rebuild knowledge graph from scratch.')
    parser.add_argument('--build', action='store_true', default=False, help='Build knowledge graph from repodir.')
    parser.add_argument('--dump-networkx', action='store_true', default=False, help='Load jsonl data and dump to networkx gpickle format.')
    parser.add_argument('--dump-neo4j', action='store_true', default=False, help='Load jsonl data and dump to neo4j for viewing knowledge graph.')
    parser.add_argument('--neo4j-uri', type=str, default='bolt://10.1.52.85:7687', help='neo4j URI, see https://neo4j.com/')
    parser.add_argument('--neo4j-user', type=str, default='neo4j', help='neo4j username')
    parser.add_argument('--neo4j-passwd', type=str, default='neo4j', help='neo4j password')
    parser.add_argument('--query', type=str, default=None, help='Information Retrieval based on knowledge graph.')
    parser.add_argument('--retry', type=int, default=1, help='Retry count for LLM NER.')
    args = parser.parse_args()
    return args

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Hybrid LLM Server.')
    parser.add_argument('--config_path', default='config.ini', help='Hybrid LLM Server configuration path. Default value is config.ini')
    parser.add_argument('--unittest', action='store_true', default=False, help='Test with samples.')
    args = parser.parse_args()
    return args

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Feature store for processing directories.')
    parser.add_argument('--work_dir', type=str, default='workdir', help='Working directory.')
    parser.add_argument('--repo_dir', type=str, default='repodir', help='Root directory where the repositories are located.')
    parser.add_argument('--config_path', default='config.ini', help='Feature store configuration path. Default value is config.ini')
    parser.add_argument('--good_questions', default='resource/good_questions.json', help='Positive examples in the dataset. Default value is resource/good_questions.json')
    parser.add_argument('--bad_questions', default='resource/bad_questions.json', help='Negative examples json path. Default value is resource/bad_questions.json')
    parser.add_argument('--ner-file', default=None, help='The path of NER file, which is a dumped json list. HuixiangDou would build relationship between entities and chunks for retrieve.')
    parser.add_argument('--qa-pair', default=None, help='Path to a CSV or JSON file containing QA pairs. For CSV, the first column is the key and the second column is the value. For JSON, the format should be {"key":"value"} or a list of {"key":"key1", "value":"value1"}.')
    parser.add_argument('--sample', help='Input an json file, save reject and search output.')
    parser.add_argument('--override', action='store_true', default=False, help='Remove old data and rebuild knowledge graph from scratch.')
    args = parser.parse_args()
    return args

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description='SerialPipeline.')
    parser.add_argument('work_dir', type=str, help='Working directory.')
    parser.add_argument('--config_path', default='config.ini', help='SerialPipeline configuration path. Default value is config.ini')
    return parser.parse_args()

def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description='Source graph proxy search')
    parser.add_argument('--config_path', default='config.ini', help='Source graph proxy configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Client for hybrid llm service.')
    parser.add_argument('--config_path', default='config.ini', help='Configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description='SerialPipeline.')
    parser.add_argument('work_dir', type=str, help='Working directory.')
    parser.add_argument('--config_path', default='config.ini', help='SerialPipeline configuration path. Default value is config.ini')
    return parser.parse_args()

def parse_args():
    """Parses command-line arguments for web search."""
    parser = argparse.ArgumentParser(description='Web search.')
    parser.add_argument('--keywords', type=str, help='Keywords for search and parse.')
    parser.add_argument('--config_path', default='config.ini', help='Feature store configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args

def parse_args():
    parser = argparse.ArgumentParser(description='Knowledge graph for processing directories.')
    parser.add_argument('--config_path', default='config-kg.ini', help='Configuration path. Default value is config.ini')
    parser.add_argument('--retrieve', default=False, help='Retrieve result from knowledge graph.')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    if args.retrieve:
        calculate(args.config_path)
    else:
        summarize()

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Feature store for processing directories.')
    parser.add_argument('--work_dir_base', type=str, default='workdir basename', help='Working directory.')
    parser.add_argument('--repo_dir', type=str, default='repodir', help='Root directory where the repositories are located.')
    parser.add_argument('--config_path', default='config.ini', help='Feature store configuration path. Default value is config.ini')
    parser.add_argument('--chunk-size', default=768, help='Text chunksize')
    parser.add_argument('--hybrid', default=False, help='Combine knowledge graph evaluation and dense feature score')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    best_f1 = 0.0
    best_chunk_size = -1
    calculate(832)

def parse_config():
    parser = argparse.ArgumentParser(description='arg parser')
    parser.add_argument('--max_tokens', type=int, default=782000, help='maximum token length for evaluation')
    parser.add_argument('--num_tests', type=int, default=1, help='number of repeat testing for each length')
    args = parser.parse_args()
    return args

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Feature store for processing directories.')
    parser.add_argument('--work_dir_base', type=str, default='workdir basename', help='Working directory.')
    parser.add_argument('--repo_dir', type=str, default='repodir', help='Root directory where the repositories are located.')
    parser.add_argument('--config_path', default='config.ini', help='Feature store configuration path. Default value is config.ini')
    parser.add_argument('--chunk-size', default=768, help='Text chunksize')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    best_f1 = 0.0
    best_chunk_size = -1
    calculate(2048)

