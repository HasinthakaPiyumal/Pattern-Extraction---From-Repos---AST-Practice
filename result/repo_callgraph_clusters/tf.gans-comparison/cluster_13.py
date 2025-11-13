# Cluster 13

def lrelu(inputs, leak=0.2, scope='lrelu'):
    """
    https://github.com/tensorflow/tensorflow/issues/4079
    """
    with tf.variable_scope(scope):
        f1 = 0.5 * (1 + leak)
        f2 = 0.5 * (1 - leak)
        return f1 * inputs + f2 * abs(inputs)

class BEGAN(BaseModel):

    def __init__(self, name, training, D_lr=0.0001, G_lr=0.0001, image_shape=[64, 64, 3], z_dim=64, gamma=0.5):
        self.gamma = gamma
        self.decay_step = 3000
        self.decay_rate = 0.95
        self.beta1 = 0.5
        self.lambd_k = 0.001
        self.nf = 128
        self.lr_lower_bound = 2e-05
        super(BEGAN, self).__init__(name=name, training=training, D_lr=D_lr, G_lr=G_lr, image_shape=image_shape, z_dim=z_dim)

    def _build_train_graph(self):
        with tf.variable_scope(self.name):
            X = tf.placeholder(tf.float32, [None] + self.shape)
            z = tf.placeholder(tf.float32, [None, self.z_dim])
            global_step = tf.Variable(0, name='global_step', trainable=False)
            G = self._generator(z)
            D_real_energy = self._discriminator(X)
            D_fake_energy = self._discriminator(G, reuse=True)
            k = tf.Variable(0.0, name='k', trainable=False)
            with tf.variable_scope('D_loss'):
                D_loss = D_real_energy - k * D_fake_energy
            with tf.variable_scope('G_loss'):
                G_loss = D_fake_energy
            with tf.variable_scope('balance'):
                balance = self.gamma * D_real_energy - D_fake_energy
            with tf.variable_scope('M'):
                M = D_real_energy + tf.abs(balance)
            D_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=self.name + '/D/')
            G_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=self.name + '/G/')
            D_update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS, scope=self.name + '/D/')
            G_update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS, scope=self.name + '/G/')
            D_lr = tf.train.exponential_decay(self.D_lr, global_step, self.decay_step, self.decay_rate, staircase=True)
            D_lr = tf.maximum(D_lr, self.lr_lower_bound)
            G_lr = tf.train.exponential_decay(self.G_lr, global_step, self.decay_step, self.decay_rate, staircase=True)
            G_lr = tf.maximum(G_lr, self.lr_lower_bound)
            with tf.variable_scope('D_train_op'):
                with tf.control_dependencies(D_update_ops):
                    D_train_op = tf.train.AdamOptimizer(learning_rate=D_lr, beta1=self.beta1).minimize(D_loss, var_list=D_vars)
            with tf.variable_scope('G_train_op'):
                with tf.control_dependencies(G_update_ops):
                    G_train_op = tf.train.AdamOptimizer(learning_rate=G_lr, beta1=self.beta1).minimize(G_loss, var_list=G_vars, global_step=global_step)
            with tf.control_dependencies([D_train_op]):
                with tf.variable_scope('update_k'):
                    update_k = tf.assign(k, tf.clip_by_value(k + self.lambd_k * balance, 0.0, 1.0))
            D_train_op = update_k
            self.summary_op = tf.summary.merge([tf.summary.scalar('G_loss', G_loss), tf.summary.scalar('D_loss', D_loss), tf.summary.scalar('D_energy/real', D_real_energy), tf.summary.scalar('D_energy/fake', D_fake_energy), tf.summary.scalar('convergence_measure', M), tf.summary.scalar('balance', balance), tf.summary.scalar('k', k), tf.summary.scalar('D_lr', D_lr), tf.summary.scalar('G_lr', G_lr)])
            fake_sample = tf.clip_by_value(G, -1.0, 1.0)
            tf.summary.image('fake_sample', fake_sample, max_outputs=self.FAKE_MAX_OUTPUT)
            tf.summary.histogram('G_hist', G)
            self.all_summary_op = tf.summary.merge_all()
            self.X = X
            self.z = z
            self.D_train_op = D_train_op
            self.G_train_op = G_train_op
            self.fake_sample = fake_sample
            self.global_step = global_step

    def _encoder(self, X, reuse=False):
        with tf.variable_scope('encoder', reuse=reuse):
            nf = self.nf
            nh = self.z_dim
            with slim.arg_scope([slim.conv2d], kernel_size=[3, 3], padding='SAME', activation_fn=tf.nn.elu):
                net = slim.conv2d(X, nf)
                net = slim.conv2d(net, nf)
                net = slim.conv2d(net, nf)
                net = slim.conv2d(net, nf * 2, stride=2)
                net = slim.conv2d(net, nf * 2)
                net = slim.conv2d(net, nf * 2)
                net = slim.conv2d(net, nf * 3, stride=2)
                net = slim.conv2d(net, nf * 3)
                net = slim.conv2d(net, nf * 3)
                net = slim.conv2d(net, nf * 4, stride=2)
                net = slim.conv2d(net, nf * 4)
                net = slim.conv2d(net, nf * 4)
                net = slim.conv2d(net, nf * 4)
            net = slim.flatten(net)
            h = slim.fully_connected(net, nh, activation_fn=None)
            return h

    def _decoder(self, h, reuse=False):
        with tf.variable_scope('decoder', reuse=reuse):
            nf = self.nf
            nh = self.z_dim
            h0 = slim.fully_connected(h, 8 * 8 * nf, activation_fn=None)
            net = tf.reshape(h0, [-1, 8, 8, nf])
            with slim.arg_scope([slim.conv2d], kernel_size=[3, 3], padding='SAME', activation_fn=tf.nn.elu):
                net = slim.conv2d(net, nf)
                net = slim.conv2d(net, nf)
                net = tf.image.resize_nearest_neighbor(net, [16, 16])
                net = slim.conv2d(net, nf)
                net = slim.conv2d(net, nf)
                net = tf.image.resize_nearest_neighbor(net, [32, 32])
                net = slim.conv2d(net, nf)
                net = slim.conv2d(net, nf)
                net = tf.image.resize_nearest_neighbor(net, [64, 64])
                net = slim.conv2d(net, nf)
                net = slim.conv2d(net, nf)
                net = slim.conv2d(net, 3, activation_fn=None)
            return net

    def _discriminator(self, X, reuse=False):
        with tf.variable_scope('D', reuse=reuse):
            h = self._encoder(X, reuse=reuse)
            x_recon = self._decoder(h, reuse=reuse)
            energy = tf.abs(X - x_recon)
            energy = tf.reduce_mean(energy)
            return energy

    def _generator(self, z, reuse=False):
        with tf.variable_scope('G', reuse=reuse):
            x_fake = self._decoder(z, reuse=reuse)
            return x_fake

def _discriminator(self, X, reuse=False):
    with tf.variable_scope('D', reuse=reuse):
        h = self._encoder(X, reuse=reuse)
        x_recon = self._decoder(h, reuse=reuse)
        energy = tf.abs(X - x_recon)
        energy = tf.reduce_mean(energy)
        return energy

def _generator(self, z, reuse=False):
    with tf.variable_scope('G', reuse=reuse):
        x_fake = self._decoder(z, reuse=reuse)
        return x_fake

