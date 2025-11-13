# Cluster 7

class MyDataset(Dataset):
    """加载数据
    这里保存了多个文件到sample的映射, 以便于节约内存
    """

    def __init__(self, filenames):
        self.data = []
        self.index_map = {}
        self.token_size, self.smp_size = (0, 0)
        for fi, filename in enumerate(filenames):
            with open(filename, 'r') as f:
                nbytes = f.seek(0, 2)
                flen = f.tell() // np.dtype('uint16').itemsize
            self.token_size += flen
            self.index_map.update({self.smp_size + i: (fi, i) for i in range(flen // args.max_length)})
            self.smp_size += flen // args.max_length
            self.data.append(np.memmap(filename, dtype=np.dtype('uint16'), shape=(flen // args.max_length, args.max_length)))
        log_info(f'token_size: {self.token_size}, smp_size: {self.smp_size}')

    def __len__(self):
        return self.smp_size

    def __getitem__(self, index: int):
        fi, i = self.index_map[index]
        sample = self.data[fi][i]
        X = np.array(sample[:-1]).astype(np.int64)
        Y = np.array(sample[1:]).astype(np.int64)
        return (torch.from_numpy(X), torch.from_numpy(Y))

def __getitem__(self, index: int):
    fi, i = self.index_map[index]
    sample = self.data[fi][i]
    X = np.array(sample[:-1]).astype(np.int64)
    Y = np.array(sample[1:]).astype(np.int64)
    return (torch.from_numpy(X), torch.from_numpy(Y))

