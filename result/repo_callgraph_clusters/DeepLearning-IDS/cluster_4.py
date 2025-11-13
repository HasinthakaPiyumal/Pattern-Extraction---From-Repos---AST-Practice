# Cluster 4

def experiment(dataFile, optimizer, epochs, batch_size):
    seed = 7
    numpy.random.seed(seed)
    cvscores = []
    print('optimizer: {} epochs: {} batch_size: {}'.format(optimizer, epochs, batch_size))
    data = loadData(dataFile)
    data_y = data.pop('Label').values
    data_x = data.as_matrix()
    kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    for train, test in kfold.split(data_x, data_y):
        model = Sequential()
        model.add(Dense(80, activation='relu', input_dim=80))
        model.add(Dense(80, activation='relu', input_dim=80))
        model.add(Dense(1, activation='softmax'))
        model.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy'])
        model.fit(data_x[train], data_y[train], epochs=10, batch_size=100, verbose=0)
        scores = model.evaluate(data_x[test], data_y[test], verbose=0)
        print('{}: {:.2f}%'.format(model.metrics_names[1], scores[1] * 100))
        cvscores.append(scores[1] * 100)
        resultFile = os.path.join(resultPath, dataFile)
        with open('{}.result'.format(resultFile), 'a') as fout:
            fout.write('accuracy: {:.2f} std-dev: {:.2f}\n'.format(np.mean(cvscores), np.std(cvscores)))

def experimentIndividual(dataFile, epochs=5, normalize=False):
    procs = [FillMissing, Categorify]
    if normalize:
        procs.append(Normalize)
    seed = 7
    np.random.seed(seed)
    data = loadData(dataFile)
    kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    cvscores = []
    fold = 1
    for train_idx, test_idx in kfold.split(data.index, data[dep_var]):
        print('running fold = ', fold)
        fold += 1
        data_fold = TabularList.from_df(data, path=dataPath, cat_names=cat_names, cont_names=cont_names, procs=procs).split_by_idxs(train_idx, test_idx).label_from_df(cols=dep_var).databunch()
        model = tabular_learner(data_fold, layers=[200, 100], metrics=accuracy, callback_fns=ShowGraph)
        model.fit(epochs, 0.01)
        model.save('{}.model'.format(os.path.basename(dataFile)))
        loss, acc = model.validate()
        print('loss {}: accuracy: {:.2f}%'.format(loss, acc * 100))
        cvscores.append(acc * 100)
        resultFile = os.path.join(resultPath, dataFile)
        with open('{}.result'.format(resultFile), 'a') as fout:
            fout.write('accuracy: {:.2f} std-dev: {:.2f}\n'.format(np.mean(cvscores), np.std(cvscores)))

