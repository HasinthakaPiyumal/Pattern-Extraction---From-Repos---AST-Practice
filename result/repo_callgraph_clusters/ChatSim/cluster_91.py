# Cluster 91

def search_bruteforce(searcher):
    return searcher.score_brute_force().build()

def search_partioned_ah(searcher, dims_per_block, aiq_threshold, reorder_k, partioning_trainsize, num_leaves, num_leaves_to_search):
    return searcher.tree(num_leaves=num_leaves, num_leaves_to_search=num_leaves_to_search, training_sample_size=partioning_trainsize).score_ah(dims_per_block, anisotropic_quantization_threshold=aiq_threshold).reorder(reorder_k).build()

def search_ah(searcher, dims_per_block, aiq_threshold, reorder_k):
    return searcher.score_ah(dims_per_block, anisotropic_quantization_threshold=aiq_threshold).reorder(reorder_k).build()

def train_searcher(opt, metric='dot_product', partioning_trainsize=None, reorder_k=None, aiq_thld=0.2, dims_per_block=2, num_leaves=None, num_leaves_to_search=None):
    data_pool = load_datapool(opt.database)
    k = opt.knn
    if not reorder_k:
        reorder_k = 2 * k
    searcher = scann.scann_ops_pybind.builder(data_pool['embedding'] / np.linalg.norm(data_pool['embedding'], axis=1)[:, np.newaxis], k, metric)
    pool_size = data_pool['embedding'].shape[0]
    print(*['#'] * 100)
    print('Initializing scaNN searcher with the following values:')
    print(f'k: {k}')
    print(f'metric: {metric}')
    print(f'reorder_k: {reorder_k}')
    print(f'anisotropic_quantization_threshold: {aiq_thld}')
    print(f'dims_per_block: {dims_per_block}')
    print(*['#'] * 100)
    print('Start training searcher....')
    print(f'N samples in pool is {pool_size}')
    if pool_size < 20000.0:
        print('Using brute force search.')
        searcher = search_bruteforce(searcher)
    elif 20000.0 <= pool_size and pool_size < 100000.0:
        print('Using asymmetric hashing search and reordering.')
        searcher = search_ah(searcher, dims_per_block, aiq_thld, reorder_k)
    else:
        print('Using using partioning, asymmetric hashing search and reordering.')
        if not partioning_trainsize:
            partioning_trainsize = data_pool['embedding'].shape[0] // 10
        if not num_leaves:
            num_leaves = int(np.sqrt(pool_size))
        if not num_leaves_to_search:
            num_leaves_to_search = max(num_leaves // 20, 1)
        print('Partitioning params:')
        print(f'num_leaves: {num_leaves}')
        print(f'num_leaves_to_search: {num_leaves_to_search}')
        searcher = search_partioned_ah(searcher, dims_per_block, aiq_thld, reorder_k, partioning_trainsize, num_leaves, num_leaves_to_search)
    print('Finish training searcher')
    searcher_savedir = opt.target_path
    os.makedirs(searcher_savedir, exist_ok=True)
    searcher.serialize(searcher_savedir)
    print(f'Saved trained searcher under "{searcher_savedir}"')

class Searcher(object):

    def __init__(self, database, retriever_version='ViT-L/14'):
        assert database in DATABASES
        self.database_name = database
        self.searcher_savedir = f'data/rdm/searchers/{self.database_name}'
        self.database_path = f'data/rdm/retrieval_databases/{self.database_name}'
        self.retriever = self.load_retriever(version=retriever_version)
        self.database = {'embedding': [], 'img_id': [], 'patch_coords': []}
        self.load_database()
        self.load_searcher()

    def train_searcher(self, k, metric='dot_product', searcher_savedir=None):
        print('Start training searcher')
        searcher = scann.scann_ops_pybind.builder(self.database['embedding'] / np.linalg.norm(self.database['embedding'], axis=1)[:, np.newaxis], k, metric)
        self.searcher = searcher.score_brute_force().build()
        print('Finish training searcher')
        if searcher_savedir is not None:
            print(f'Save trained searcher under "{searcher_savedir}"')
            os.makedirs(searcher_savedir, exist_ok=True)
            self.searcher.serialize(searcher_savedir)

    def load_single_file(self, saved_embeddings):
        compressed = np.load(saved_embeddings)
        self.database = {key: compressed[key] for key in compressed.files}
        print('Finished loading of clip embeddings.')

    def load_multi_files(self, data_archive):
        out_data = {key: [] for key in self.database}
        for d in tqdm(data_archive, desc=f'Loading datapool from {len(data_archive)} individual files.'):
            for key in d.files:
                out_data[key].append(d[key])
        return out_data

    def load_database(self):
        print(f'Load saved patch embedding from "{self.database_path}"')
        file_content = glob.glob(os.path.join(self.database_path, '*.npz'))
        if len(file_content) == 1:
            self.load_single_file(file_content[0])
        elif len(file_content) > 1:
            data = [np.load(f) for f in file_content]
            prefetched_data = parallel_data_prefetch(self.load_multi_files, data, n_proc=min(len(data), cpu_count()), target_data_type='dict')
            self.database = {key: np.concatenate([od[key] for od in prefetched_data], axis=1)[0] for key in self.database}
        else:
            raise ValueError(f'No npz-files in specified path "{self.database_path}" is this directory existing?')
        print(f'Finished loading of retrieval database of length {self.database['embedding'].shape[0]}.')

    def load_retriever(self, version='ViT-L/14'):
        model = FrozenClipImageEmbedder(model=version)
        if torch.cuda.is_available():
            model.cuda()
        model.eval()
        return model

    def load_searcher(self):
        print(f'load searcher for database {self.database_name} from {self.searcher_savedir}')
        self.searcher = scann.scann_ops_pybind.load_searcher(self.searcher_savedir)
        print('Finished loading searcher.')

    def search(self, x, k):
        if self.searcher is None and self.database['embedding'].shape[0] < 20000.0:
            self.train_searcher(k)
        assert self.searcher is not None, 'Cannot search with uninitialized searcher'
        if isinstance(x, torch.Tensor):
            x = x.detach().cpu().numpy()
        if len(x.shape) == 3:
            x = x[:, 0]
        query_embeddings = x / np.linalg.norm(x, axis=1)[:, np.newaxis]
        start = time.time()
        nns, distances = self.searcher.search_batched(query_embeddings, final_num_neighbors=k)
        end = time.time()
        out_embeddings = self.database['embedding'][nns]
        out_img_ids = self.database['img_id'][nns]
        out_pc = self.database['patch_coords'][nns]
        out = {'nn_embeddings': out_embeddings / np.linalg.norm(out_embeddings, axis=-1)[..., np.newaxis], 'img_ids': out_img_ids, 'patch_coords': out_pc, 'queries': x, 'exec_time': end - start, 'nns': nns, 'q_embeddings': query_embeddings}
        return out

    def __call__(self, x, n):
        return self.search(x, n)

def train_searcher(self, k, metric='dot_product', searcher_savedir=None):
    print('Start training searcher')
    searcher = scann.scann_ops_pybind.builder(self.database['embedding'] / np.linalg.norm(self.database['embedding'], axis=1)[:, np.newaxis], k, metric)
    self.searcher = searcher.score_brute_force().build()
    print('Finish training searcher')
    if searcher_savedir is not None:
        print(f'Save trained searcher under "{searcher_savedir}"')
        os.makedirs(searcher_savedir, exist_ok=True)
        self.searcher.serialize(searcher_savedir)

