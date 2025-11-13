# Cluster 4

def calculate_state_prediction_loss(model, tbatch_interactionids, user_embeddings_time_series, y_true, loss_function):
    prob = model.predict_label(user_embeddings_time_series[tbatch_interactionids, :])
    y = Variable(torch.LongTensor(y_true).cuda()[tbatch_interactionids])
    loss = loss_function(prob, y)
    return loss

def load_model(model, optimizer, args, epoch):
    modelname = args.model
    filename = PATH + 'saved_models/%s/checkpoint.%s.ep%d.tp%.1f.pth.tar' % (args.network, modelname, epoch, args.train_proportion)
    checkpoint = torch.load(filename)
    print('Loading saved embeddings and model: %s' % filename)
    args.start_epoch = checkpoint['epoch']
    user_embeddings = Variable(torch.from_numpy(checkpoint['user_embeddings']).cuda())
    item_embeddings = Variable(torch.from_numpy(checkpoint['item_embeddings']).cuda())
    try:
        train_end_idx = checkpoint['train_end_idx']
    except KeyError:
        train_end_idx = None
    try:
        user_embeddings_time_series = Variable(torch.from_numpy(checkpoint['user_embeddings_time_series']).cuda())
        item_embeddings_time_series = Variable(torch.from_numpy(checkpoint['item_embeddings_time_series']).cuda())
    except:
        user_embeddings_time_series = None
        item_embeddings_time_series = None
    model.load_state_dict(checkpoint['state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer'])
    return [model, optimizer, user_embeddings, item_embeddings, user_embeddings_time_series, item_embeddings_time_series, train_end_idx]

