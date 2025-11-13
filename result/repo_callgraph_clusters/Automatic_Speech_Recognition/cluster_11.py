# Cluster 11

def getAttrs(object, name):
    """ get attributes for object
    """
    assert type(name) == list, 'name must be a list'
    value = []
    for n in name:
        value.append(getattr(object, n, 'None'))
    return value

def setAttrs(object, attrsName, attrsValue):
    """ register attributes for this class """
    assert type(attrsName) == list, 'attrsName must be a list'
    assert type(attrsValue) == list, 'attrsValue must be a list'
    for name, value in zip(attrsName, attrsValue):
        object.__dict__[name] = value

def output_to_sequence(lmt, type='phn'):
    """ convert the output into sequences of characters or phonemes
    """
    phn = ['aa', 'ae', 'ah', 'ao', 'aw', 'ax', 'ax-h', 'axr', 'ay', 'b', 'bcl', 'ch', 'd', 'dcl', 'dh', 'dx', 'eh', 'el', 'em', 'en', 'eng', 'epi', 'er', 'ey', 'f', 'g', 'gcl', 'h#', 'hh', 'hv', 'ih', 'ix', 'iy', 'jh', 'k', 'kcl', 'l', 'm', 'n', 'ng', 'nx', 'ow', 'oy', 'p', 'pau', 'pcl', 'q', 'r', 's', 'sh', 't', 'tcl', 'th', 'uh', 'uw', 'ux', 'v', 'w', 'y', 'z', 'zh']
    sequences = []
    start = 0
    sequences.append([])
    for i in range(len(lmt[0])):
        if lmt[0][i][0] == start:
            sequences[start].append(lmt[1][i])
        else:
            start = start + 1
            sequences.append([])
    indexes = sequences[0]
    if type == 'phn':
        seq = []
        for ind in indexes:
            if ind == len(phn):
                pass
            else:
                seq.append(phn[ind])
        seq = ' '.join(seq)
        return seq
    elif type == 'cha':
        seq = []
        for ind in indexes:
            if ind == 0:
                seq.append(' ')
            elif ind == 27:
                seq.append("'")
            elif ind == 28:
                pass
            else:
                seq.append(chr(ind + 96))
        seq = ''.join(seq)
        return seq
    else:
        raise TypeError('mode should be phoneme or character')

def target2phoneme(target):
    seq = []
    for t in target:
        if t == len(phn):
            pass
        else:
            seq.append(phn[t])
    seq = ' '.join(seq)
    return seq

def group_phoneme(orig_phn, mapping):
    group_phn = []
    for val in orig_phn:
        group_phn.append(val)
    group_phn.append('sil')
    for key in mapping.keys():
        if key in orig_phn:
            group_phn.remove(key)
    group_phn.sort()
    return group_phn

def calc_PER(pred, ground_truth, normalize=True, merge_phn=True):
    """Calculates the Phoneme Error Rate based on python package leven, which produce the same results as 
    tf.edit_distance and tf.reduce_mean based calculation
    
    :param pred: tuple with 3 numpy-typed element representing sparse tensor
    :param ground_truth: tuple with 3 numpy-typed element representing sparse tensor
    :param normalize: if True, the distance between sequence will be divided by the length of the ground_truth length
    :param merge_phn: if True, 61 phonemes will be merged into 39 phonemes, then do the distance calculation
    :return: the PER
    """
    pred_seq_list = seq_to_single_char_strings(sparse_tensor_to_seq_list(pred, merge_phn=merge_phn))
    truth_seq_list = seq_to_single_char_strings(sparse_tensor_to_seq_list(ground_truth, merge_phn=merge_phn))
    assert len(truth_seq_list) == len(pred_seq_list)
    distances = []
    for i in range(len(truth_seq_list)):
        dist_i = leven.levenshtein(pred_seq_list[i], truth_seq_list[i])
        if normalize:
            dist_i /= float(len(truth_seq_list[i]))
        distances.append(dist_i)
    return np.mean(distances)

def seq_to_single_char_strings(seq):
    strings = []
    for s in seq:
        strings.append(''.join([chr(65 + p) for p in s]))
    return strings

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

@describe
def load_data(self, args, mode, type):
    if mode == 'train':
        return load_batched_data(train_mfcc_dir, train_label_dir, batch_size, mode, type)
    elif mode == 'test':
        return load_batched_data(test_mfcc_dir, test_label_dir, batch_size, mode, type)
    else:
        raise TypeError('mode should be train or test.')

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

@describe
def load_data(self, feature_dir, label_dir, mode, level):
    return load_batched_data(feature_dir, label_dir, batch_size, mode, level)

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

@describe
def load_data(self, feature_dir, label_dir, mode, level):
    return load_batched_data(feature_dir, label_dir, batch_size, mode, level)

def pre_emphasis(signal, coefficient=0.95):
    """Pre-emphasis.
    Args:
        signal: 1-D numpy array.
        coefficient:Coefficient for pre-emphasis. Defauted to 0.95.
    Returns:
        pre-emphasis signal.
    """
    return numpy.append(signal[0], signal[1:] - coefficient * signal[:-1])

def spectrogramPower(audio, window_size=0.02, window_stride=0.01):
    """ short time fourier transform

    Details:
        audio - This is the input time-domain signal you wish to find the spectrogram of. It can't get much simpler than that. In your case, the 
                signal you want to find the spectrogram of is defined in the following code:

        win_length - If you recall, we decompose the image into chunks, and each chunk has a specified width.  window defines the width of each 
                 chunkin terms of samples. As this is a discrete-time signal, you know that this signal was sampled with a particular sampling 
                 frequency and sampling period. You can determine how large the window is in terms of samples by:

                 window_samples = window_time/Ts
        hop_length - the same as stride in convolution network, overlapping width

    """
    samplingRate, samples = wav.read(audio)
    win_length = int(window_size * samplingRate)
    hop_length = int(window_stride * samplingRate)
    n_fft = win_length
    D = librosa.core.stft(samples, n_fft=n_fft, hop_length=hop_length, win_length=win_length)
    mag = np.abs(D)
    log_mag = np.log1p(mag)
    log_mag = preprocessing.scale(log_mag)
    return log_mag

def _replaceDecimal(decimal_set, sub_str):
    """ 
    Replacing decimal numbers with Chinese expression
    """
    dec_str_set = []
    for dec in decimal_set:
        dec_str = _float2Chinese(float(dec))
        dec_str_set.append(dec_str)
    newStr = ''
    count = 0
    for c in sub_str:
        if c == '_':
            newStr += dec_str_set[count]
            count += 1
        else:
            newStr += c
    return newStr

def _replaceInteger(integer_set, sub_str):
    """ 
    Replacing integer numbers with Chinese expression
    """
    int_str_set = []
    for inte in integer_set:
        int_str = _integer2Chinese(int(inte))
        int_str_set.append(int_str)
    newStr = ''
    count = 0
    for c in sub_str:
        if c == '_':
            newStr += int_str_set[count]
            count += 1
        else:
            newStr += c
    return newStr

def _replaceSpecial(integer_set, sub_str):
    """ 
    Replacing special numbers with Chinese expression, eg: 2018年 --> 二年一八年
    """
    charNumSet = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九']
    int_str_set = []
    for inte in integer_set:
        int_sub_result = ''
        for c in inte:
            if c == '年':
                int_sub_result += '年'
            else:
                int_sub_result += charNumSet[int(c)]
        int_str_set.append(int_sub_result)
    newStr = ''
    count = 0
    for c in sub_str:
        if c == '_':
            newStr += int_str_set[count]
            count += 1
        else:
            newStr += c
    return newStr

def _float2Chinese(number):
    """
    Converting floating number to Chinese expression
    """
    charNumSet = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九']
    integer_part, decimal_part = str(number).split('.')
    int_result = _integer2Chinese(int(integer_part))
    dec_result = ''
    for c in decimal_part:
        dec_result += charNumSet[int(c)]
    return int_result + '点' + dec_result

