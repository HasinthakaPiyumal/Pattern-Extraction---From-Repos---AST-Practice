# Cluster 0

def experiment(dataFile, optimizer='adam', epochs=10, batch_size=10):
    time_gen = int(time.time())
    global model_name
    model_name = f'{dataFile}_{time_gen}'
    tensorboard = TensorBoard(log_dir='logs/{}'.format(model_name))
    seed = 7
    np.random.seed(seed)
    cvscores = []
    print('optimizer: {} epochs: {} batch_size: {}'.format(optimizer, epochs, batch_size))
    data = loadData(dataFile)
    data_y = data.pop('Label')
    encoder = LabelEncoder()
    encoder.fit(data_y)
    data_y = encoder.transform(data_y)
    dummy_y = to_categorical(data_y)
    data_x = normalize(data.values)
    inputDim = len(data_x[0])
    print('inputdim = ', inputDim)
    num = 0
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=7)
    start = timer()
    for train_index, test_index in sss.split(X=np.zeros(data_x.shape[0]), y=dummy_y):
        X_train, X_test = (data_x[train_index], data_x[test_index])
        y_train, y_test = (dummy_y[train_index], dummy_y[test_index])
        model = baseline_model(inputDim, y_train.shape)
        print('Training ' + dataFile + ' on split ' + str(num))
        model.fit(x=X_train, y=y_train, epochs=epochs, batch_size=batch_size, verbose=2, callbacks=[tensorboard], validation_data=(X_test, y_test))
        model.save(f'{resultPath}/models/{model_name}.model')
        num += 1
    elapsed = timer() - start
    scores = model.evaluate(X_test, y_test, verbose=1)
    print(model.metrics_names)
    acc, loss = (scores[1] * 100, scores[0] * 100)
    print('Baseline: accuracy: {:.2f}%: loss: {:.2f}'.format(acc, loss))
    resultFile = os.path.join(resultPath, dataFile)
    with open('{}.result'.format(resultFile), 'a') as fout:
        fout.write('{} results...'.format(model_name))
        fout.write('\taccuracy: {:.2f} loss: {:.2f}'.format(acc, loss))
        fout.write('\telapsed time: {:.2f} sec\n'.format(elapsed))

def experiment(dataFile, optimizer='adam', epochs=10, batch_size=10):
    time_gen = int(time.time())
    global model_name
    model_name = f'{dataFile}_{time_gen}'
    tensorboard = TensorBoard(log_dir='logs/{}'.format(model_name))
    seed = 7
    np.random.seed(seed)
    cvscores = []
    print('optimizer: {} epochs: {} batch_size: {}'.format(optimizer, epochs, batch_size))
    data = loadData(dataFile)
    data_y = data.pop('Label')
    encoder = LabelEncoder()
    encoder.fit(data_y)
    data_y = encoder.transform(data_y)
    dummy_y = to_categorical(data_y)
    data_x = normalize(data.values)
    inputDim = len(data_x[0])
    print('inputdim = ', inputDim)
    num = 0
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=7)
    start = timer()
    for train_index, test_index in sss.split(X=np.zeros(data_x.shape[0]), y=dummy_y):
        X_train, X_test = (data_x[train_index], data_x[test_index])
        y_train, y_test = (dummy_y[train_index], dummy_y[test_index])
        model = baseline_model(inputDim, y_train.shape)
        print('Training ' + dataFile + ' on split ' + str(num))
        model.fit(x=X_train, y=y_train, epochs=epochs, batch_size=batch_size, verbose=2, callbacks=[tensorboard], validation_data=(X_test, y_test))
        model.save(f'{resultPath}/models/{model_name}.model')
        num += 1
    elapsed = timer() - start
    scores = model.evaluate(X_test, y_test, verbose=1)
    print(model.metrics_names)
    acc, loss = (scores[1] * 100, scores[0] * 100)
    print('Baseline: accuracy: {:.2f}%: loss: {:.2f}'.format(acc, loss))
    resultFile = os.path.join(resultPath, dataFile)
    with open('{}.result'.format(resultFile), 'a') as fout:
        fout.write('{} results...'.format(model_name))
        fout.write('\taccuracy: {:.2f} loss: {:.2f}'.format(acc, loss))
        fout.write('\telapsed time: {:.2f} sec\n'.format(elapsed))

