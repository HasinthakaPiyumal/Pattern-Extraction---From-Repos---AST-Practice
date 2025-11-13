# Cluster 2

def baseline_model(inputDim=-1, out_shape=(-1,)):
    global model_name
    model = Sequential()
    if inputDim > 0 and out_shape[1] > 0:
        model.add(Dense(79, activation='relu', input_shape=(inputDim,)))
        print(f'out_shape[1]:{out_shape[1]}')
        model.add(Dense(128, activation='relu'))
        model.add(Dense(out_shape[1], activation='softmax'))
        if out_shape[1] > 2:
            print('Categorical Cross-Entropy Loss Function')
            model_name += '_categorical'
            model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        else:
            model_name += '_binary'
            print('Binary Cross-Entropy Loss Function')
            model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

def baseline_model(inputDim=-1, out_shape=(-1,)):
    global model_name
    model = Sequential()
    if inputDim > 0 and out_shape[1] > 0:
        model.add(Dense(79, activation='relu', input_shape=(inputDim,)))
        print(f'out_shape[1]:{out_shape[1]}')
        model.add(Dense(128, activation='relu'))
        model.add(Dense(out_shape[1], activation='softmax'))
        if out_shape[1] > 2:
            print('Categorical Cross-Entropy Loss Function')
            model_name += '_categorical'
            model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        else:
            model_name += '_binary'
            print('Binary Cross-Entropy Loss Function')
            model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

