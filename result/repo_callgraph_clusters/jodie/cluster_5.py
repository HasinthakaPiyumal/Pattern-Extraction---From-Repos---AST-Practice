# Cluster 5

def save_model(model, optimizer, args, epoch, user_embeddings, item_embeddings, train_end_idx, user_embeddings_time_series=None, item_embeddings_time_series=None, path=PATH):
    print('*** Saving embeddings and model ***')
    state = {'user_embeddings': user_embeddings.data.cpu().numpy(), 'item_embeddings': item_embeddings.data.cpu().numpy(), 'epoch': epoch, 'state_dict': model.state_dict(), 'optimizer': optimizer.state_dict(), 'train_end_idx': train_end_idx}
    if user_embeddings_time_series is not None:
        state['user_embeddings_time_series'] = user_embeddings_time_series.data.cpu().numpy()
        state['item_embeddings_time_series'] = item_embeddings_time_series.data.cpu().numpy()
    directory = os.path.join(path, 'saved_models/%s' % args.network)
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, 'checkpoint.%s.ep%d.tp%.1f.pth.tar' % (args.model, epoch, args.train_proportion))
    torch.save(state, filename)
    print('*** Saved embeddings and model to file: %s ***\n\n' % filename)

