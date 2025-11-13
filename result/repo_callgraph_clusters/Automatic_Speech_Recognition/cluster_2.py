# Cluster 2

def list_to_sparse_tensor(targetList, level):
    """ turn 2-D List to SparseTensor
    """
    indices = []
    vals = []
    assert level == 'phn' or level == 'cha', 'type must be phoneme or character, seq2seq will be supported in future'
    phn = ['aa', 'ae', 'ah', 'ao', 'aw', 'ax', 'ax-h', 'axr', 'ay', 'b', 'bcl', 'ch', 'd', 'dcl', 'dh', 'dx', 'eh', 'el', 'em', 'en', 'eng', 'epi', 'er', 'ey', 'f', 'g', 'gcl', 'h#', 'hh', 'hv', 'ih', 'ix', 'iy', 'jh', 'k', 'kcl', 'l', 'm', 'n', 'ng', 'nx', 'ow', 'oy', 'p', 'pau', 'pcl', 'q', 'r', 's', 'sh', 't', 'tcl', 'th', 'uh', 'uw', 'ux', 'v', 'w', 'y', 'z', 'zh']
    mapping = {'ah': 'ax', 'ax-h': 'ax', 'ux': 'uw', 'aa': 'ao', 'ih': 'ix', 'axr': 'er', 'el': 'l', 'em': 'm', 'en': 'n', 'nx': 'n', 'eng': 'ng', 'sh': 'zh', 'hv': 'hh', 'bcl': 'h#', 'pcl': 'h#', 'dcl': 'h#', 'tcl': 'h#', 'gcl': 'h#', 'kcl': 'h#', 'q': 'h#', 'epi': 'h#', 'pau': 'h#'}
    group_phn = ['ae', 'ao', 'aw', 'ax', 'ay', 'b', 'ch', 'd', 'dh', 'dx', 'eh', 'er', 'ey', 'f', 'g', 'h#', 'hh', 'ix', 'iy', 'jh', 'k', 'l', 'm', 'n', 'ng', 'ow', 'oy', 'p', 'r', 's', 't', 'th', 'uh', 'uw', 'v', 'w', 'y', 'z', 'zh']
    mapping = {'ah': 'ax', 'ax-h': 'ax', 'ux': 'uw', 'aa': 'ao', 'ih': 'ix', 'axr': 'er', 'el': 'l', 'em': 'm', 'en': 'n', 'nx': 'n', 'eng': 'ng', 'sh': 'zh', 'hv': 'hh', 'bcl': 'h#', 'pcl': 'h#', 'dcl': 'h#', 'tcl': 'h#', 'gcl': 'h#', 'kcl': 'h#', 'q': 'h#', 'epi': 'h#', 'pau': 'h#'}
    group_phn = ['ae', 'ao', 'aw', 'ax', 'ay', 'b', 'ch', 'd', 'dh', 'dx', 'eh', 'er', 'ey', 'f', 'g', 'h#', 'hh', 'ix', 'iy', 'jh', 'k', 'l', 'm', 'n', 'ng', 'ow', 'oy', 'p', 'r', 's', 't', 'th', 'uh', 'uw', 'v', 'w', 'y', 'z', 'zh']
    if level == 'cha':
        for tI, target in enumerate(targetList):
            for seqI, val in enumerate(target):
                indices.append([tI, seqI])
                vals.append(val)
        shape = [len(targetList), np.asarray(indices).max(axis=0)[1] + 1]
        return (np.array(indices), np.array(vals), np.array(shape))
    elif level == 'phn':
        '\n        for phn level, we should collapse 61 labels into 39 labels before scoring\n        \n        Reference:\n          Heterogeneous Acoustic Measurements and Multiple Classifiers for Speech Recognition(1986), \n            Andrew K. Halberstadt, https://groups.csail.mit.edu/sls/publications/1998/phdthesis-drew.pdf\n        '
        for tI, target in enumerate(targetList):
            for seqI, val in enumerate(target):
                if val < len(phn) and phn[val] in mapping.keys():
                    val = group_phn.index(mapping[phn[val]])
                indices.append([tI, seqI])
                vals.append(val)
        shape = [len(targetList), np.asarray(indices).max(0)[1] + 1]
        return (np.array(indices), np.array(vals), np.array(shape))
    else:
        raise ValueError('Invalid level: %s' % str(level))

def data_lists_to_batches(inputList, targetList, batchSize, level):
    """ padding the input list to a same dimension, integrate all data into batchInputs
    """
    assert len(inputList) == len(targetList)
    nFeatures = inputList[0].shape[0]
    maxLength = 0
    for inp in inputList:
        maxLength = max(maxLength, inp.shape[1])
    randIxs = np.random.permutation(len(inputList))
    start, end = (0, batchSize)
    dataBatches = []
    while end <= len(inputList):
        batchSeqLengths = np.zeros(batchSize)
        for batchI, origI in enumerate(randIxs[start:end]):
            batchSeqLengths[batchI] = inputList[origI].shape[-1]
        batchInputs = np.zeros((maxLength, batchSize, nFeatures))
        batchTargetList = []
        for batchI, origI in enumerate(randIxs[start:end]):
            padSecs = maxLength - inputList[origI].shape[1]
            batchInputs[:, batchI, :] = np.pad(inputList[origI].T, ((0, padSecs), (0, 0)), 'constant', constant_values=0)
            batchTargetList.append(targetList[origI])
        dataBatches.append((batchInputs, list_to_sparse_tensor(batchTargetList, level), batchSeqLengths))
        start += batchSize
        end += batchSize
    return (dataBatches, maxLength)

def _get_dims(shape):
    """get shape for initialization
    """
    fan_in = shape[0] if len(shape) == 2 else np.prod(shape[:-1])
    fan_out = shape[1] if len(shape) == 2 else shape[-1]
    return (fan_in, fan_out)

def list_to_sparse_tensor(targetList, mode='train'):
    """ turn 2-D List to SparseTensor
    """
    indices = []
    vals = []
    group_phn = group_phoneme(phn, mapping)
    for tI, target in enumerate(targetList):
        for seqI, val in enumerate(target):
            if mode == 'train':
                indices.append([tI, seqI])
                vals.append(val)
            elif mode == 'test':
                if phn[val] in mapping.keys():
                    val = group_phn.index(mapping[phn[val]])
                indices.append([tI, seqI])
                vals.append(val)
            else:
                raise ValueError('Invalid mode.', mode)
    shape = [len(targetList), np.asarray(indices).max(0)[1] + 1]
    return (np.array(indices), np.array(vals), np.array(shape))

def sparse_tensor_to_seq_list(sparse_seq, merge_phn=True):
    phonemes_list = []
    it = 0
    num_samples = np.max(sparse_seq.indices, axis=0)[0] + 1
    for n in range(num_samples):
        cur_sample_indices = sparse_seq.indices[sparse_seq.indices[:, 0] == n, 1]
        if len(cur_sample_indices) == 0:
            seq_length = 0
        else:
            seq_length = np.max(cur_sample_indices) + 1
        seq = sparse_seq.vals[it:it + seq_length]
        _seq = [IDX_MAPPING[p] for p in seq] if merge_phn else seq
        phonemes_list.append(_seq)
        it += seq_length
    return phonemes_list

class Runner(object):

    def _default_configs(self):
        return {'level': level, 'rnncell': rnncell, 'batch_size': batch_size, 'num_hidden': num_hidden, 'num_feature': num_feature, 'num_classes': num_classes, 'num_layer': num_layer, 'num_iter': num_iter, 'activation': activation_fn, 'optimizer': optimizer_fn, 'learning_rate': lr, 'keep_prob': keep_prob, 'grad_clip': grad_clip}

    @describe
    def load_data(self, args, mode, type):
        if mode == 'train':
            return load_batched_data(train_mfcc_dir, train_label_dir, batch_size, mode, type)
        elif mode == 'test':
            return load_batched_data(test_mfcc_dir, test_label_dir, batch_size, mode, type)
        else:
            raise TypeError('mode should be train or test.')

    def run(self):
        args_dict = self._default_configs()
        args = dotdict(args_dict)
        batchedData, maxTimeSteps, totalN = self.load_data(args, mode=mode, type=level)
        model = model_fn(args, maxTimeSteps)
        num_params = count_params(model, mode='trainable')
        all_num_params = count_params(model, mode='all')
        model.config['trainable params'] = num_params
        model.config['all params'] = all_num_params
        print(model.config)
        with tf.Session() as sess:
            if keep == True:
                ckpt = tf.train.get_checkpoint_state(savedir)
                if ckpt and ckpt.model_checkpoint_path:
                    model.saver.restore(sess, ckpt.model_checkpoint_path)
                    print('Model restored from:' + savedir)
            else:
                print('Initializing')
                sess.run(model.initial_op)
            for epoch in range(num_epochs):
                start = time.time()
                if mode == 'train':
                    print('Epoch', epoch + 1, '...')
                batchErrors = np.zeros(len(batchedData))
                batchRandIxs = np.random.permutation(len(batchedData))
                for batch, batchOrigI in enumerate(batchRandIxs):
                    batchInputs, batchTargetSparse, batchSeqLengths = batchedData[batchOrigI]
                    batchTargetIxs, batchTargetVals, batchTargetShape = batchTargetSparse
                    feedDict = {model.inputX: batchInputs, model.targetIxs: batchTargetIxs, model.targetVals: batchTargetVals, model.targetShape: batchTargetShape, model.seqLengths: batchSeqLengths}
                    if level == 'cha':
                        if mode == 'train':
                            _, l, pre, y, er = sess.run([model.optimizer, model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                            batchErrors[batch] = er
                            print('\n{} mode, total:{},batch:{}/{},epoch:{}/{},train loss={:.3f},mean train CER={:.3f}\n'.format(level, totalN, batch + 1, len(batchRandIxs), epoch + 1, num_epochs, l, er / batch_size))
                        elif mode == 'test':
                            l, pre, y, er = sess.run([model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                            batchErrors[batch] = er
                            print('\n{} mode, total:{},batch:{}/{},test loss={:.3f},mean test CER={:.3f}\n'.format(level, totalN, batch + 1, len(batchRandIxs), l, er / batch_size))
                    elif level == 'phn':
                        if mode == 'train':
                            _, l, pre, y = sess.run([model.optimizer, model.loss, model.predictions, model.targetY], feed_dict=feedDict)
                            er = get_edit_distance([pre.values], [y.values], True, level)
                            print('\n{} mode, total:{},batch:{}/{},epoch:{}/{},train loss={:.3f},mean train PER={:.3f}\n'.format(level, totalN, batch + 1, len(batchRandIxs), epoch + 1, num_epochs, l, er))
                            batchErrors[batch] = er * len(batchSeqLengths)
                        elif mode == 'test':
                            l, pre, y = sess.run([model.loss, model.predictions, model.targetY], feed_dict=feedDict)
                            er = get_edit_distance([pre.values], [y.values], True, level)
                            print('\n{} mode, total:{},batch:{}/{},test loss={:.3f},mean test PER={:.3f}\n'.format(level, totalN, batch + 1, len(batchRandIxs), l, er))
                            batchErrors[batch] = er * len(batchSeqLengths)
                    if er / batch_size == 1.0:
                        break
                    if batch % 30 == 0:
                        print('Truth:\n' + output_to_sequence(y, type=level))
                        print('Output:\n' + output_to_sequence(pre, type=level))
                    if mode == 'train' and ((epoch * len(batchRandIxs) + batch + 1) % 20 == 0 or (epoch == num_epochs - 1 and batch == len(batchRandIxs) - 1)):
                        checkpoint_path = os.path.join(savedir, 'model.ckpt')
                        model.saver.save(sess, checkpoint_path, global_step=epoch)
                        print('Model has been saved in {}'.format(savedir))
                end = time.time()
                delta_time = end - start
                print('Epoch ' + str(epoch + 1) + ' needs time:' + str(delta_time) + ' s')
                if mode == 'train':
                    if (epoch + 1) % 1 == 0:
                        checkpoint_path = os.path.join(savedir, 'model.ckpt')
                        model.saver.save(sess, checkpoint_path, global_step=epoch)
                        print('Model has been saved in {}'.format(savedir))
                    epochER = batchErrors.sum() / totalN
                    print('Epoch', epoch + 1, 'mean train error rate:', epochER)
                    logging(model, logfile, epochER, epoch, delta_time, mode='config')
                    logging(model, logfile, epochER, epoch, delta_time, mode=mode)
                if mode == 'test':
                    with open(os.path.join(resultdir, level + '_result.txt'), 'a') as result:
                        result.write(output_to_sequence(y, type=level) + '\n')
                        result.write(output_to_sequence(pre, type=level) + '\n')
                        result.write('\n')
                    epochER = batchErrors.sum() / totalN
                    print(' test error rate:', epochER)
                    logging(model, logfile, epochER, mode=mode)

def run(self):
    args_dict = self._default_configs()
    args = dotdict(args_dict)
    batchedData, maxTimeSteps, totalN = self.load_data(args, mode=mode, type=level)
    model = model_fn(args, maxTimeSteps)
    num_params = count_params(model, mode='trainable')
    all_num_params = count_params(model, mode='all')
    model.config['trainable params'] = num_params
    model.config['all params'] = all_num_params
    print(model.config)
    with tf.Session() as sess:
        if keep == True:
            ckpt = tf.train.get_checkpoint_state(savedir)
            if ckpt and ckpt.model_checkpoint_path:
                model.saver.restore(sess, ckpt.model_checkpoint_path)
                print('Model restored from:' + savedir)
        else:
            print('Initializing')
            sess.run(model.initial_op)
        for epoch in range(num_epochs):
            start = time.time()
            if mode == 'train':
                print('Epoch', epoch + 1, '...')
            batchErrors = np.zeros(len(batchedData))
            batchRandIxs = np.random.permutation(len(batchedData))
            for batch, batchOrigI in enumerate(batchRandIxs):
                batchInputs, batchTargetSparse, batchSeqLengths = batchedData[batchOrigI]
                batchTargetIxs, batchTargetVals, batchTargetShape = batchTargetSparse
                feedDict = {model.inputX: batchInputs, model.targetIxs: batchTargetIxs, model.targetVals: batchTargetVals, model.targetShape: batchTargetShape, model.seqLengths: batchSeqLengths}
                if level == 'cha':
                    if mode == 'train':
                        _, l, pre, y, er = sess.run([model.optimizer, model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                        batchErrors[batch] = er
                        print('\n{} mode, total:{},batch:{}/{},epoch:{}/{},train loss={:.3f},mean train CER={:.3f}\n'.format(level, totalN, batch + 1, len(batchRandIxs), epoch + 1, num_epochs, l, er / batch_size))
                    elif mode == 'test':
                        l, pre, y, er = sess.run([model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                        batchErrors[batch] = er
                        print('\n{} mode, total:{},batch:{}/{},test loss={:.3f},mean test CER={:.3f}\n'.format(level, totalN, batch + 1, len(batchRandIxs), l, er / batch_size))
                elif level == 'phn':
                    if mode == 'train':
                        _, l, pre, y = sess.run([model.optimizer, model.loss, model.predictions, model.targetY], feed_dict=feedDict)
                        er = get_edit_distance([pre.values], [y.values], True, level)
                        print('\n{} mode, total:{},batch:{}/{},epoch:{}/{},train loss={:.3f},mean train PER={:.3f}\n'.format(level, totalN, batch + 1, len(batchRandIxs), epoch + 1, num_epochs, l, er))
                        batchErrors[batch] = er * len(batchSeqLengths)
                    elif mode == 'test':
                        l, pre, y = sess.run([model.loss, model.predictions, model.targetY], feed_dict=feedDict)
                        er = get_edit_distance([pre.values], [y.values], True, level)
                        print('\n{} mode, total:{},batch:{}/{},test loss={:.3f},mean test PER={:.3f}\n'.format(level, totalN, batch + 1, len(batchRandIxs), l, er))
                        batchErrors[batch] = er * len(batchSeqLengths)
                if er / batch_size == 1.0:
                    break
                if batch % 30 == 0:
                    print('Truth:\n' + output_to_sequence(y, type=level))
                    print('Output:\n' + output_to_sequence(pre, type=level))
                if mode == 'train' and ((epoch * len(batchRandIxs) + batch + 1) % 20 == 0 or (epoch == num_epochs - 1 and batch == len(batchRandIxs) - 1)):
                    checkpoint_path = os.path.join(savedir, 'model.ckpt')
                    model.saver.save(sess, checkpoint_path, global_step=epoch)
                    print('Model has been saved in {}'.format(savedir))
            end = time.time()
            delta_time = end - start
            print('Epoch ' + str(epoch + 1) + ' needs time:' + str(delta_time) + ' s')
            if mode == 'train':
                if (epoch + 1) % 1 == 0:
                    checkpoint_path = os.path.join(savedir, 'model.ckpt')
                    model.saver.save(sess, checkpoint_path, global_step=epoch)
                    print('Model has been saved in {}'.format(savedir))
                epochER = batchErrors.sum() / totalN
                print('Epoch', epoch + 1, 'mean train error rate:', epochER)
                logging(model, logfile, epochER, epoch, delta_time, mode='config')
                logging(model, logfile, epochER, epoch, delta_time, mode=mode)
            if mode == 'test':
                with open(os.path.join(resultdir, level + '_result.txt'), 'a') as result:
                    result.write(output_to_sequence(y, type=level) + '\n')
                    result.write(output_to_sequence(pre, type=level) + '\n')
                    result.write('\n')
                epochER = batchErrors.sum() / totalN
                print(' test error rate:', epochER)
                logging(model, logfile, epochER, mode=mode)

class Runner(object):

    def _default_configs(self):
        return {'level': level, 'rnncell': rnncell, 'batch_size': batch_size, 'num_hidden': num_hidden, 'num_feature': num_feature, 'num_class': num_classes, 'num_layer': num_layer, 'activation': activation_fn, 'optimizer': optimizer_fn, 'learning_rate': lr, 'keep_prob': keep_prob, 'grad_clip': grad_clip}

    @describe
    def load_data(self, feature_dir, label_dir, mode, level):
        return load_batched_data(feature_dir, label_dir, batch_size, mode, level)

    def run(self):
        args_dict = self._default_configs()
        args = dotdict(args_dict)
        feature_dirs, label_dirs = get_data(datadir, level, train_dataset, dev_dataset, test_dataset, mode)
        batchedData, maxTimeSteps, totalN = self.load_data(feature_dirs[0], label_dirs[0], mode, level)
        model = model_fn(args, maxTimeSteps)
        FL_pair = list(zip(feature_dirs, label_dirs))
        random.shuffle(FL_pair)
        feature_dirs, label_dirs = zip(*FL_pair)
        for feature_dir, label_dir in zip(feature_dirs, label_dirs):
            id_dir = feature_dirs.index(feature_dir)
            print('dir id:{}'.format(id_dir))
            batchedData, maxTimeSteps, totalN = self.load_data(feature_dir, label_dir, mode, level)
            model = model_fn(args, maxTimeSteps)
            num_params = count_params(model, mode='trainable')
            all_num_params = count_params(model, mode='all')
            model.config['trainable params'] = num_params
            model.config['all params'] = all_num_params
            print(model.config)
            with tf.Session(graph=model.graph) as sess:
                if keep == True:
                    ckpt = tf.train.get_checkpoint_state(savedir)
                    if ckpt and ckpt.model_checkpoint_path:
                        model.saver.restore(sess, ckpt.model_checkpoint_path)
                        print('Model restored from:' + savedir)
                else:
                    print('Initializing')
                    sess.run(model.initial_op)
                for epoch in range(num_epochs):
                    start = time.time()
                    if mode == 'train':
                        print('Epoch {} ...'.format(epoch + 1))
                    batchErrors = np.zeros(len(batchedData))
                    batchRandIxs = np.random.permutation(len(batchedData))
                    for batch, batchOrigI in enumerate(batchRandIxs):
                        batchInputs, batchTargetSparse, batchSeqLengths = batchedData[batchOrigI]
                        batchTargetIxs, batchTargetVals, batchTargetShape = batchTargetSparse
                        feedDict = {model.inputX: batchInputs, model.targetIxs: batchTargetIxs, model.targetVals: batchTargetVals, model.targetShape: batchTargetShape, model.seqLengths: batchSeqLengths}
                        if level == 'cha':
                            if mode == 'train':
                                _, l, pre, y, er = sess.run([model.optimizer, model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                                batchErrors[batch] = er
                                print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},epoch:{}/{},train loss={:.3f},mean train CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), epoch + 1, num_epochs, l, er / batch_size))
                            elif mode == 'dev':
                                l, pre, y, er = sess.run([model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                                batchErrors[batch] = er
                                print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},dev loss={:.3f},mean dev CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), l, er / batch_size))
                            elif mode == 'test':
                                l, pre, y, er = sess.run([model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                                batchErrors[batch] = er
                                print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},test loss={:.3f},mean test CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), l, er / batch_size))
                        elif level == 'seq2seq':
                            raise ValueError('level %s is not supported now' % str(level))
                        if er / batch_size == 1.0:
                            break
                        if batch % 20 == 0:
                            print('Truth:\n' + output_to_sequence(y, type=level))
                            print('Output:\n' + output_to_sequence(pre, type=level))
                        if mode == 'train' and ((epoch * len(batchRandIxs) + batch + 1) % 20 == 0 or (epoch == num_epochs - 1 and batch == len(batchRandIxs) - 1)):
                            checkpoint_path = os.path.join(savedir, 'model.ckpt')
                            model.saver.save(sess, checkpoint_path, global_step=epoch)
                            print('Model has been saved in {}'.format(savedir))
                    end = time.time()
                    delta_time = end - start
                    print('Epoch ' + str(epoch + 1) + ' needs time:' + str(delta_time) + ' s')
                    if mode == 'train':
                        if (epoch + 1) % 1 == 0:
                            checkpoint_path = os.path.join(savedir, 'model.ckpt')
                            model.saver.save(sess, checkpoint_path, global_step=epoch)
                            print('Model has been saved in {}'.format(savedir))
                        epochER = batchErrors.sum() / totalN
                        print('Epoch', epoch + 1, 'mean train error rate:', epochER)
                        logging(model, logfile, epochER, epoch, delta_time, mode='config')
                        logging(model, logfile, epochER, epoch, delta_time, mode=mode)
                    if mode == 'test' or mode == 'dev':
                        with open(os.path.join(resultdir, level + '_result.txt'), 'a') as result:
                            result.write(output_to_sequence(y, type=level) + '\n')
                            result.write(output_to_sequence(pre, type=level) + '\n')
                            result.write('\n')
                        epochER = batchErrors.sum() / totalN
                        print(' test error rate:', epochER)
                        logging(model, logfile, epochER, mode=mode)

def run(self):
    args_dict = self._default_configs()
    args = dotdict(args_dict)
    feature_dirs, label_dirs = get_data(datadir, level, train_dataset, dev_dataset, test_dataset, mode)
    batchedData, maxTimeSteps, totalN = self.load_data(feature_dirs[0], label_dirs[0], mode, level)
    model = model_fn(args, maxTimeSteps)
    FL_pair = list(zip(feature_dirs, label_dirs))
    random.shuffle(FL_pair)
    feature_dirs, label_dirs = zip(*FL_pair)
    for feature_dir, label_dir in zip(feature_dirs, label_dirs):
        id_dir = feature_dirs.index(feature_dir)
        print('dir id:{}'.format(id_dir))
        batchedData, maxTimeSteps, totalN = self.load_data(feature_dir, label_dir, mode, level)
        model = model_fn(args, maxTimeSteps)
        num_params = count_params(model, mode='trainable')
        all_num_params = count_params(model, mode='all')
        model.config['trainable params'] = num_params
        model.config['all params'] = all_num_params
        print(model.config)
        with tf.Session(graph=model.graph) as sess:
            if keep == True:
                ckpt = tf.train.get_checkpoint_state(savedir)
                if ckpt and ckpt.model_checkpoint_path:
                    model.saver.restore(sess, ckpt.model_checkpoint_path)
                    print('Model restored from:' + savedir)
            else:
                print('Initializing')
                sess.run(model.initial_op)
            for epoch in range(num_epochs):
                start = time.time()
                if mode == 'train':
                    print('Epoch {} ...'.format(epoch + 1))
                batchErrors = np.zeros(len(batchedData))
                batchRandIxs = np.random.permutation(len(batchedData))
                for batch, batchOrigI in enumerate(batchRandIxs):
                    batchInputs, batchTargetSparse, batchSeqLengths = batchedData[batchOrigI]
                    batchTargetIxs, batchTargetVals, batchTargetShape = batchTargetSparse
                    feedDict = {model.inputX: batchInputs, model.targetIxs: batchTargetIxs, model.targetVals: batchTargetVals, model.targetShape: batchTargetShape, model.seqLengths: batchSeqLengths}
                    if level == 'cha':
                        if mode == 'train':
                            _, l, pre, y, er = sess.run([model.optimizer, model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                            batchErrors[batch] = er
                            print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},epoch:{}/{},train loss={:.3f},mean train CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), epoch + 1, num_epochs, l, er / batch_size))
                        elif mode == 'dev':
                            l, pre, y, er = sess.run([model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                            batchErrors[batch] = er
                            print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},dev loss={:.3f},mean dev CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), l, er / batch_size))
                        elif mode == 'test':
                            l, pre, y, er = sess.run([model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                            batchErrors[batch] = er
                            print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},test loss={:.3f},mean test CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), l, er / batch_size))
                    elif level == 'seq2seq':
                        raise ValueError('level %s is not supported now' % str(level))
                    if er / batch_size == 1.0:
                        break
                    if batch % 20 == 0:
                        print('Truth:\n' + output_to_sequence(y, type=level))
                        print('Output:\n' + output_to_sequence(pre, type=level))
                    if mode == 'train' and ((epoch * len(batchRandIxs) + batch + 1) % 20 == 0 or (epoch == num_epochs - 1 and batch == len(batchRandIxs) - 1)):
                        checkpoint_path = os.path.join(savedir, 'model.ckpt')
                        model.saver.save(sess, checkpoint_path, global_step=epoch)
                        print('Model has been saved in {}'.format(savedir))
                end = time.time()
                delta_time = end - start
                print('Epoch ' + str(epoch + 1) + ' needs time:' + str(delta_time) + ' s')
                if mode == 'train':
                    if (epoch + 1) % 1 == 0:
                        checkpoint_path = os.path.join(savedir, 'model.ckpt')
                        model.saver.save(sess, checkpoint_path, global_step=epoch)
                        print('Model has been saved in {}'.format(savedir))
                    epochER = batchErrors.sum() / totalN
                    print('Epoch', epoch + 1, 'mean train error rate:', epochER)
                    logging(model, logfile, epochER, epoch, delta_time, mode='config')
                    logging(model, logfile, epochER, epoch, delta_time, mode=mode)
                if mode == 'test' or mode == 'dev':
                    with open(os.path.join(resultdir, level + '_result.txt'), 'a') as result:
                        result.write(output_to_sequence(y, type=level) + '\n')
                        result.write(output_to_sequence(pre, type=level) + '\n')
                        result.write('\n')
                    epochER = batchErrors.sum() / totalN
                    print(' test error rate:', epochER)
                    logging(model, logfile, epochER, mode=mode)

class Runner(object):

    def _default_configs(self):
        return {'level': level, 'rnncell': rnncell, 'batch_size': batch_size, 'num_hidden': num_hidden, 'num_feature': num_feature, 'num_class': num_classes, 'num_layer': num_layer, 'activation': activation_fn, 'optimizer': optimizer_fn, 'learning_rate': lr, 'keep_prob': keep_prob, 'grad_clip': grad_clip}

    @describe
    def load_data(self, feature_dir, label_dir, mode, level):
        return load_batched_data(feature_dir, label_dir, batch_size, mode, level)

    def run(self):
        args_dict = self._default_configs()
        args = dotdict(args_dict)
        feature_dirs, label_dirs = get_data(datadir, level, train_dataset, dev_dataset, test_dataset, mode)
        batchedData, maxTimeSteps, totalN = self.load_data(feature_dirs[0], label_dirs[0], mode, level)
        model = model_fn(args, maxTimeSteps)
        FL_pair = list(zip(feature_dirs, label_dirs))
        random.shuffle(FL_pair)
        feature_dirs, label_dirs = zip(*FL_pair)
        for feature_dir, label_dir in zip(feature_dirs, label_dirs):
            id_dir = feature_dirs.index(feature_dir)
            print('dir id:{}'.format(id_dir))
            batchedData, maxTimeSteps, totalN = self.load_data(feature_dir, label_dir, mode, level)
            model = model_fn(args, maxTimeSteps)
            num_params = count_params(model, mode='trainable')
            all_num_params = count_params(model, mode='all')
            model.config['trainable params'] = num_params
            model.config['all params'] = all_num_params
            print(model.config)
            with tf.Session(graph=model.graph) as sess:
                if keep == True:
                    ckpt = tf.train.get_checkpoint_state(savedir)
                    if ckpt and ckpt.model_checkpoint_path:
                        model.saver.restore(sess, ckpt.model_checkpoint_path)
                        print('Model restored from:' + savedir)
                else:
                    print('Initializing')
                    sess.run(model.initial_op)
                for epoch in range(num_epochs):
                    start = time.time()
                    if mode == 'train':
                        print('Epoch {} ...'.format(epoch + 1))
                    batchErrors = np.zeros(len(batchedData))
                    batchRandIxs = np.random.permutation(len(batchedData))
                    for batch, batchOrigI in enumerate(batchRandIxs):
                        batchInputs, batchTargetSparse, batchSeqLengths = batchedData[batchOrigI]
                        batchTargetIxs, batchTargetVals, batchTargetShape = batchTargetSparse
                        feedDict = {model.inputX: batchInputs, model.targetIxs: batchTargetIxs, model.targetVals: batchTargetVals, model.targetShape: batchTargetShape, model.seqLengths: batchSeqLengths}
                        if level == 'cha':
                            if mode == 'train':
                                _, l, pre, y, er = sess.run([model.optimizer, model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                                batchErrors[batch] = er
                                print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},epoch:{}/{},train loss={:.3f},mean train CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), epoch + 1, num_epochs, l, er / batch_size))
                            elif mode == 'dev':
                                l, pre, y, er = sess.run([model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                                batchErrors[batch] = er
                                print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},dev loss={:.3f},mean dev CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), l, er / batch_size))
                            elif mode == 'test':
                                l, pre, y, er = sess.run([model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                                batchErrors[batch] = er
                                print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},test loss={:.3f},mean test CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), l, er / batch_size))
                        elif level == 'seq2seq':
                            raise ValueError('level %s is not supported now' % str(level))
                        if er / batch_size == 1.0:
                            break
                        if batch % 20 == 0:
                            print('Truth:\n' + output_to_sequence(y, type=level))
                            print('Output:\n' + output_to_sequence(pre, type=level))
                        if mode == 'train' and ((epoch * len(batchRandIxs) + batch + 1) % 20 == 0 or (epoch == num_epochs - 1 and batch == len(batchRandIxs) - 1)):
                            checkpoint_path = os.path.join(savedir, 'model.ckpt')
                            model.saver.save(sess, checkpoint_path, global_step=epoch)
                            print('Model has been saved in {}'.format(savedir))
                    end = time.time()
                    delta_time = end - start
                    print('Epoch ' + str(epoch + 1) + ' needs time:' + str(delta_time) + ' s')
                    if mode == 'train':
                        if (epoch + 1) % 1 == 0:
                            checkpoint_path = os.path.join(savedir, 'model.ckpt')
                            model.saver.save(sess, checkpoint_path, global_step=epoch)
                            print('Model has been saved in {}'.format(savedir))
                        epochER = batchErrors.sum() / totalN
                        print('Epoch', epoch + 1, 'mean train error rate:', epochER)
                        logging(model, logfile, epochER, epoch, delta_time, mode='config')
                        logging(model, logfile, epochER, epoch, delta_time, mode=mode)
                    if mode == 'test' or mode == 'dev':
                        with open(os.path.join(resultdir, level + '_result.txt'), 'a') as result:
                            result.write(output_to_sequence(y, type=level) + '\n')
                            result.write(output_to_sequence(pre, type=level) + '\n')
                            result.write('\n')
                        epochER = batchErrors.sum() / totalN
                        print(' test error rate:', epochER)
                        logging(model, logfile, epochER, mode=mode)

def run(self):
    args_dict = self._default_configs()
    args = dotdict(args_dict)
    feature_dirs, label_dirs = get_data(datadir, level, train_dataset, dev_dataset, test_dataset, mode)
    batchedData, maxTimeSteps, totalN = self.load_data(feature_dirs[0], label_dirs[0], mode, level)
    model = model_fn(args, maxTimeSteps)
    FL_pair = list(zip(feature_dirs, label_dirs))
    random.shuffle(FL_pair)
    feature_dirs, label_dirs = zip(*FL_pair)
    for feature_dir, label_dir in zip(feature_dirs, label_dirs):
        id_dir = feature_dirs.index(feature_dir)
        print('dir id:{}'.format(id_dir))
        batchedData, maxTimeSteps, totalN = self.load_data(feature_dir, label_dir, mode, level)
        model = model_fn(args, maxTimeSteps)
        num_params = count_params(model, mode='trainable')
        all_num_params = count_params(model, mode='all')
        model.config['trainable params'] = num_params
        model.config['all params'] = all_num_params
        print(model.config)
        with tf.Session(graph=model.graph) as sess:
            if keep == True:
                ckpt = tf.train.get_checkpoint_state(savedir)
                if ckpt and ckpt.model_checkpoint_path:
                    model.saver.restore(sess, ckpt.model_checkpoint_path)
                    print('Model restored from:' + savedir)
            else:
                print('Initializing')
                sess.run(model.initial_op)
            for epoch in range(num_epochs):
                start = time.time()
                if mode == 'train':
                    print('Epoch {} ...'.format(epoch + 1))
                batchErrors = np.zeros(len(batchedData))
                batchRandIxs = np.random.permutation(len(batchedData))
                for batch, batchOrigI in enumerate(batchRandIxs):
                    batchInputs, batchTargetSparse, batchSeqLengths = batchedData[batchOrigI]
                    batchTargetIxs, batchTargetVals, batchTargetShape = batchTargetSparse
                    feedDict = {model.inputX: batchInputs, model.targetIxs: batchTargetIxs, model.targetVals: batchTargetVals, model.targetShape: batchTargetShape, model.seqLengths: batchSeqLengths}
                    if level == 'cha':
                        if mode == 'train':
                            _, l, pre, y, er = sess.run([model.optimizer, model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                            batchErrors[batch] = er
                            print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},epoch:{}/{},train loss={:.3f},mean train CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), epoch + 1, num_epochs, l, er / batch_size))
                        elif mode == 'dev':
                            l, pre, y, er = sess.run([model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                            batchErrors[batch] = er
                            print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},dev loss={:.3f},mean dev CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), l, er / batch_size))
                        elif mode == 'test':
                            l, pre, y, er = sess.run([model.loss, model.predictions, model.targetY, model.errorRate], feed_dict=feedDict)
                            batchErrors[batch] = er
                            print('\n{} mode, total:{},subdir:{}/{},batch:{}/{},test loss={:.3f},mean test CER={:.3f}\n'.format(level, totalN, id_dir + 1, len(feature_dirs), batch + 1, len(batchRandIxs), l, er / batch_size))
                    elif level == 'seq2seq':
                        raise ValueError('level %s is not supported now' % str(level))
                    if er / batch_size == 1.0:
                        break
                    if batch % 20 == 0:
                        print('Truth:\n' + output_to_sequence(y, type=level))
                        print('Output:\n' + output_to_sequence(pre, type=level))
                    if mode == 'train' and ((epoch * len(batchRandIxs) + batch + 1) % 20 == 0 or (epoch == num_epochs - 1 and batch == len(batchRandIxs) - 1)):
                        checkpoint_path = os.path.join(savedir, 'model.ckpt')
                        model.saver.save(sess, checkpoint_path, global_step=epoch)
                        print('Model has been saved in {}'.format(savedir))
                end = time.time()
                delta_time = end - start
                print('Epoch ' + str(epoch + 1) + ' needs time:' + str(delta_time) + ' s')
                if mode == 'train':
                    if (epoch + 1) % 1 == 0:
                        checkpoint_path = os.path.join(savedir, 'model.ckpt')
                        model.saver.save(sess, checkpoint_path, global_step=epoch)
                        print('Model has been saved in {}'.format(savedir))
                    epochER = batchErrors.sum() / totalN
                    print('Epoch', epoch + 1, 'mean train error rate:', epochER)
                    logging(model, logfile, epochER, epoch, delta_time, mode='config')
                    logging(model, logfile, epochER, epoch, delta_time, mode=mode)
                if mode == 'test' or mode == 'dev':
                    with open(os.path.join(resultdir, level + '_result.txt'), 'a') as result:
                        result.write(output_to_sequence(y, type=level) + '\n')
                        result.write(output_to_sequence(pre, type=level) + '\n')
                        result.write('\n')
                    epochER = batchErrors.sum() / totalN
                    print(' test error rate:', epochER)
                    logging(model, logfile, epochER, mode=mode)

def delta(feat, N=2):
    """Compute delta features from a feature vector sequence.

    Args:
        feat: A numpy array of size (NUMFRAMES by number of features) containing features. Each row holds 1 feature vector.
        N: For each frame, calculate delta features based on preceding and following N frames.
    Returns:
        A numpy array of size (NUMFRAMES by number of features) containing delta features. Each row holds 1 delta feature vector.
    """
    NUMFRAMES = len(feat)
    feat = numpy.concatenate(([feat[0] for i in range(N)], feat, [feat[-1] for i in range(N)]))
    denom = sum([2 * i * i for i in range(1, N + 1)])
    dfeat = []
    for j in range(NUMFRAMES):
        dfeat.append(numpy.sum([n * feat[N + j + n] for n in range(-1 * N, N + 1)], axis=0) / denom)
    return dfeat

