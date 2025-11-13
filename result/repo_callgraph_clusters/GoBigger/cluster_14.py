# Cluster 14

def get_lstm(lstm_type, input_size, hidden_size, num_layers=1, norm_type='LN', dropout=0.0):
    """
    Overview:
        build and return the corresponding LSTM cell
    Arguments:
        - lstm_type (:obj:`str`): version of lstm cell, now support ['normal', 'pytorch']
        - input_size (:obj:`int`): size of the input vector
        - hidden_size (:obj:`int`): size of the hidden state vector
        - num_layers (:obj:`int`): number of lstm layers
        - norm_type (:obj:`str`): type of the normaliztion, (default: None)
        - dropout (:obj:float):  dropout rate, default set to .0
    Returns:
        - lstm (:obj:`LSTM` or :obj:`PytorchLSTM`): the corresponding lstm cell
    """
    assert lstm_type in ['normal', 'pytorch']
    if lstm_type == 'normal':
        return LSTM(input_size, hidden_size, num_layers, norm_type, dropout=dropout)
    elif lstm_type == 'pytorch':
        return PytorchLSTM(input_size, hidden_size, num_layers, dropout=dropout)

