# Cluster 12

def get_model(mtype, name, training):
    model = None
    if mtype == 'DCGAN':
        model = dcgan.DCGAN
    elif mtype == 'LSGAN':
        model = lsgan.LSGAN
    elif mtype == 'WGAN':
        model = wgan.WGAN
    elif mtype == 'WGAN-GP':
        model = wgan_gp.WGAN_GP
    elif mtype == 'EBGAN':
        model = ebgan.EBGAN
    elif mtype == 'BEGAN':
        model = began.BEGAN
    elif mtype == 'DRAGAN':
        model = dragan.DRAGAN
    elif mtype == 'COULOMBGAN':
        model = coulombgan.CoulombGAN
    else:
        assert False, mtype + ' is not in the model zoo'
    assert model, mtype + ' is work in progress'
    return model(name=name, training=training)

