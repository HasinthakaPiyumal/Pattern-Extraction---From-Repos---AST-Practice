# Cluster 15

def read_parse_preproc(filename_queue):
    """ read, parse, and preproc single example. """
    with tf.variable_scope('read_parse_preproc'):
        reader = tf.TFRecordReader()
        key, records = reader.read(filename_queue)
        features = tf.parse_single_example(records, features={'image': tf.FixedLenFeature([], tf.string)})
        image = tf.decode_raw(features['image'], tf.uint8)
        image = tf.reshape(image, [128, 128, 3])
        image = tf.image.resize_images(image, [64, 64])
        image = tf.cast(image, tf.float32)
        image = image / 127.5 - 1.0
        return [image]

def sd_matrix(a, b, name='square_distance_matrix'):
    with tf.variable_scope(name):
        'Square distance matrix\n        a, b: [N, tensor] (N = batch size)\n        return: [N, N] (square distance matrix for every tensor pairs)\n        '
        batch_size = tf.shape(a)[0]
        a = tf.reshape(a, [batch_size, 1, -1])
        b = tf.reshape(b, [1, batch_size, -1])
        return tf.reduce_sum((b - a) ** 2, axis=2)

def get_potentials(x, y, kernel_dim, kernel_eps):
    """
    This is alsmost the same `calculate_potential`, but
        px, py = get_potentials(x, y)
    is faster than:
        px = calculate_potential(x, y, x)
        py = calculate_potential(x, y, y)
    because we calculate the cross terms only once.
    """
    x_fixed = tf.stop_gradient(x)
    y_fixed = tf.stop_gradient(y)
    pk_xx = plummer_kernel(x_fixed, x, kernel_dim, kernel_eps)
    pk_yx = plummer_kernel(y, x, kernel_dim, kernel_eps)
    pk_yy = plummer_kernel(y_fixed, y, kernel_dim, kernel_eps)
    batch_size = tf.shape(x)[0]
    pk_xx = tf.matrix_set_diag(pk_xx, tf.ones(shape=[batch_size], dtype=pk_xx.dtype))
    pk_yy = tf.matrix_set_diag(pk_yy, tf.ones(shape=[batch_size], dtype=pk_yy.dtype))
    kxx = tf.reduce_mean(pk_xx, axis=0)
    kyx = tf.reduce_mean(pk_yx, axis=0)
    kxy = tf.reduce_mean(pk_yx, axis=1)
    kyy = tf.reduce_mean(pk_yy, axis=0)
    pot_x = kyx - kxx
    pot_y = kyy - kyx
    pot_x = tf.reshape(pot_x, [batch_size, -1])
    pot_y = tf.reshape(pot_y, [batch_size, -1])
    return (pot_x, pot_y)

def calc_potential(x, y, a, kernel_dim, kernel_eps, name='potential'):
    """Paper notations are used in this function
    x: fake
    y: real
    
    return: potential of a
    """
    with tf.variable_scope(name):
        x = tf.stop_gradient(x)
        y = tf.stop_gradient(y)
        kxa = tf.reduce_mean(plummer_kernel(x, a, kernel_dim, kernel_eps), axis=0)
        kya = tf.reduce_mean(plummer_kernel(y, a, kernel_dim, kernel_eps), axis=0)
        p = kya - kxa
        p = tf.reshape(p, [-1, 1])
        return p

class EBGAN(BaseModel):

    def __init__(self, name, training, D_lr=0.001, G_lr=0.001, image_shape=[64, 64, 3], z_dim=100, pt_weight=0.1, margin=20.0):
        """ The default value of pt_weight and margin is taken from the paper for celebA. """
        self.pt_weight = pt_weight
        self.m = margin
        self.beta1 = 0.5
        super(EBGAN, self).__init__(name=name, training=training, D_lr=D_lr, G_lr=G_lr, image_shape=image_shape, z_dim=z_dim)

    def _build_train_graph(self):
        with tf.variable_scope(self.name):
            X = tf.placeholder(tf.float32, [None] + self.shape)
            z = tf.placeholder(tf.float32, [None, self.z_dim])
            global_step = tf.Variable(0, name='global_step', trainable=False)
            G = self._generator(z)
            D_real_latent, D_real_energy = self._discriminator(X)
            D_fake_latent, D_fake_energy = self._discriminator(G, reuse=True)
            D_fake_hinge = tf.maximum(0.0, self.m - D_fake_energy)
            D_loss = D_real_energy + D_fake_hinge
            G_loss = D_fake_energy
            PT = self.pt_regularizer(D_fake_latent)
            pt_loss = self.pt_weight * PT
            G_loss += pt_loss
            D_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=self.name + '/D/')
            G_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=self.name + '/G/')
            D_update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS, scope=self.name + '/D/')
            G_update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS, scope=self.name + '/G/')
            with tf.control_dependencies(D_update_ops):
                D_train_op = tf.train.AdamOptimizer(learning_rate=self.D_lr, beta1=self.beta1).minimize(D_loss, var_list=D_vars)
            with tf.control_dependencies(G_update_ops):
                G_train_op = tf.train.AdamOptimizer(learning_rate=self.G_lr, beta1=self.beta1).minimize(G_loss, var_list=G_vars, global_step=global_step)
            self.summary_op = tf.summary.merge([tf.summary.scalar('G_loss', G_loss), tf.summary.scalar('D_loss', D_loss), tf.summary.scalar('PT', PT), tf.summary.scalar('pt_loss', pt_loss), tf.summary.scalar('D_energy/real', D_real_energy), tf.summary.scalar('D_energy/fake', D_fake_energy), tf.summary.scalar('D_fake_hinge', D_fake_hinge)])
            tf.summary.image('fake_sample', G, max_outputs=self.FAKE_MAX_OUTPUT)
            self.all_summary_op = tf.summary.merge_all()
            self.X = X
            self.z = z
            self.D_train_op = D_train_op
            self.G_train_op = G_train_op
            self.fake_sample = G
            self.global_step = global_step

    def _discriminator(self, X, reuse=False):
        with tf.variable_scope('D', reuse=reuse):
            net = X
            with slim.arg_scope([slim.conv2d, slim.conv2d_transpose], kernel_size=[4, 4], stride=2, padding='SAME', activation_fn=ops.lrelu, normalizer_fn=slim.batch_norm, normalizer_params=self.bn_params):
                net = slim.conv2d(net, 64, normalizer_fn=None)
                net = slim.conv2d(net, 128)
                net = slim.conv2d(net, 256)
                latent = net
                expected_shape(latent, [8, 8, 256])
                net = slim.conv2d_transpose(net, 128)
                net = slim.conv2d_transpose(net, 64)
                x_recon = slim.conv2d_transpose(net, 3, activation_fn=None, normalizer_fn=None)
                expected_shape(x_recon, [64, 64, 3])
            energy = tf.sqrt(tf.reduce_sum(tf.square(X - x_recon), axis=[1, 2, 3]))
            energy = tf.reduce_mean(energy)
            return (latent, energy)

    def _generator(self, z, reuse=False):
        with tf.variable_scope('G', reuse=reuse):
            net = z
            net = slim.fully_connected(net, 4 * 4 * 1024, activation_fn=tf.nn.relu)
            net = tf.reshape(net, [-1, 4, 4, 1024])
            with slim.arg_scope([slim.conv2d_transpose], kernel_size=[4, 4], stride=2, padding='SAME', activation_fn=tf.nn.relu, normalizer_fn=slim.batch_norm, normalizer_params=self.bn_params):
                net = slim.conv2d_transpose(net, 512)
                expected_shape(net, [8, 8, 512])
                net = slim.conv2d_transpose(net, 256)
                expected_shape(net, [16, 16, 256])
                net = slim.conv2d_transpose(net, 128)
                expected_shape(net, [32, 32, 128])
                net = slim.conv2d_transpose(net, 3, activation_fn=tf.nn.tanh, normalizer_fn=None)
                expected_shape(net, [64, 64, 3])
                return net

    def pt_regularizer(self, lf):
        eps = 1e-08
        lf = slim.flatten(lf)
        l2_norm = tf.norm(lf, axis=1, keep_dims=True)
        expected_shape(l2_norm, [1])
        unit_lf = lf / (l2_norm + eps)
        cos_sim = tf.square(tf.matmul(unit_lf, unit_lf, transpose_b=True))
        N = tf.cast(tf.shape(lf)[0], tf.float32)
        pt_loss = (tf.reduce_sum(cos_sim) - N) / (N * (N - 1))
        return pt_loss

def pt_regularizer(self, lf):
    eps = 1e-08
    lf = slim.flatten(lf)
    l2_norm = tf.norm(lf, axis=1, keep_dims=True)
    expected_shape(l2_norm, [1])
    unit_lf = lf / (l2_norm + eps)
    cos_sim = tf.square(tf.matmul(unit_lf, unit_lf, transpose_b=True))
    N = tf.cast(tf.shape(lf)[0], tf.float32)
    pt_loss = (tf.reduce_sum(cos_sim) - N) / (N * (N - 1))
    return pt_loss

