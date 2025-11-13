# Cluster 5

class GenTrainLoader(Callback):
    """当前dataloader消耗完，自动用下一个文件生成dataloder
    """

    def on_dataloader_end(self, logs=None):
        model.train_dataloader = get_trainloader(args)

def on_dataloader_end(self, logs=None):
    model.train_dataloader = get_trainloader(args)

