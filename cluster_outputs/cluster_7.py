# Cluster 7

class PPOAgent(object):

    def __init__(self, town, action_std_init=0.4):
        self.obs_dim = 100
        self.action_dim = 2
        self.clip = POLICY_CLIP
        self.gamma = GAMMA
        self.n_updates_per_iteration = 7
        self.lr = PPO_LEARNING_RATE
        self.action_std = action_std_init
        self.encode = EncodeState(LATENT_DIM)
        self.memory = Buffer()
        self.town = town
        self.checkpoint_file_no = 0
        self.policy = ActorCritic(self.obs_dim, self.action_dim, self.action_std)
        self.optimizer = torch.optim.Adam([{'params': self.policy.actor.parameters(), 'lr': self.lr}, {'params': self.policy.critic.parameters(), 'lr': self.lr}])
        self.old_policy = ActorCritic(self.obs_dim, self.action_dim, self.action_std)
        self.old_policy.load_state_dict(self.policy.state_dict())
        self.MseLoss = nn.MSELoss()

    def get_action(self, obs, train):
        with torch.no_grad():
            if isinstance(obs, np.ndarray):
                obs = torch.tensor(obs, dtype=torch.float)
            action, logprob = self.old_policy.get_action_and_log_prob(obs.to(device))
        if train:
            self.memory.observation.append(obs.to(device))
            self.memory.actions.append(action)
            self.memory.log_probs.append(logprob)
        return action.detach().cpu().numpy().flatten()

    def set_action_std(self, new_action_std):
        self.action_std = new_action_std
        self.policy.set_action_std(new_action_std)
        self.old_policy.set_action_std(new_action_std)

    def decay_action_std(self, action_std_decay_rate, min_action_std):
        self.action_std = self.action_std - action_std_decay_rate
        if self.action_std <= min_action_std:
            self.action_std = min_action_std
        self.set_action_std(self.action_std)
        return self.action_std

    def learn(self):
        rewards = []
        discounted_reward = 0
        for reward, is_terminal in zip(reversed(self.memory.rewards), reversed(self.memory.dones)):
            if is_terminal:
                discounted_reward = 0
            discounted_reward = reward + self.gamma * discounted_reward
            rewards.insert(0, discounted_reward)
        rewards = torch.tensor(rewards, dtype=torch.float32).to(device)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-07)
        old_states = torch.squeeze(torch.stack(self.memory.observation, dim=0)).detach().to(device)
        old_actions = torch.squeeze(torch.stack(self.memory.actions, dim=0)).detach().to(device)
        old_logprobs = torch.squeeze(torch.stack(self.memory.log_probs, dim=0)).detach().to(device)
        for _ in range(self.n_updates_per_iteration):
            logprobs, values, dist_entropy = self.policy.evaluate(old_states, old_actions)
            values = torch.squeeze(values)
            ratios = torch.exp(logprobs - old_logprobs.detach())
            advantages = rewards - values.detach()
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1 - self.clip, 1 + self.clip) * advantages
            loss = -torch.min(surr1, surr2) + 0.5 * self.MseLoss(values, rewards) - 0.01 * dist_entropy
            self.optimizer.zero_grad()
            loss.mean().backward()
            self.optimizer.step()
        self.old_policy.load_state_dict(self.policy.state_dict())
        self.memory.clear()

    def save(self):
        self.checkpoint_file_no = len(next(os.walk(PPO_CHECKPOINT_DIR + self.town))[2])
        checkpoint_file = PPO_CHECKPOINT_DIR + self.town + '/ppo_policy_' + str(self.checkpoint_file_no) + '_.pth'
        torch.save(self.old_policy.state_dict(), checkpoint_file)

    def chkpt_save(self):
        self.checkpoint_file_no = len(next(os.walk(PPO_CHECKPOINT_DIR + self.town))[2])
        if self.checkpoint_file_no != 0:
            self.checkpoint_file_no -= 1
        checkpoint_file = PPO_CHECKPOINT_DIR + self.town + '/ppo_policy_' + str(self.checkpoint_file_no) + '_.pth'
        torch.save(self.old_policy.state_dict(), checkpoint_file)

    def load(self):
        self.checkpoint_file_no = len(next(os.walk(PPO_CHECKPOINT_DIR + self.town))[2]) - 1
        checkpoint_file = PPO_CHECKPOINT_DIR + self.town + '/ppo_policy_' + str(self.checkpoint_file_no) + '_.pth'
        self.old_policy.load_state_dict(torch.load(checkpoint_file))
        self.policy.load_state_dict(torch.load(checkpoint_file))

def save(self):
    self.checkpoint_file_no = len(next(os.walk(PPO_CHECKPOINT_DIR + self.town))[2])
    checkpoint_file = PPO_CHECKPOINT_DIR + self.town + '/ppo_policy_' + str(self.checkpoint_file_no) + '_.pth'
    torch.save(self.old_policy.state_dict(), checkpoint_file)

def chkpt_save(self):
    self.checkpoint_file_no = len(next(os.walk(PPO_CHECKPOINT_DIR + self.town))[2])
    if self.checkpoint_file_no != 0:
        self.checkpoint_file_no -= 1
    checkpoint_file = PPO_CHECKPOINT_DIR + self.town + '/ppo_policy_' + str(self.checkpoint_file_no) + '_.pth'
    torch.save(self.old_policy.state_dict(), checkpoint_file)

def load(self):
    self.checkpoint_file_no = len(next(os.walk(PPO_CHECKPOINT_DIR + self.town))[2]) - 1
    checkpoint_file = PPO_CHECKPOINT_DIR + self.town + '/ppo_policy_' + str(self.checkpoint_file_no) + '_.pth'
    self.old_policy.load_state_dict(torch.load(checkpoint_file))
    self.policy.load_state_dict(torch.load(checkpoint_file))

class ReplayBuffer(object):

    def __init__(self, max_size, observation, n_actions):
        self.n_actions = n_actions
        self.buffer_size = max_size
        self.counter = 0
        self.state_memory = torch.zeros((self.buffer_size, observation), dtype=torch.float32)
        self.new_state_memory = torch.zeros((self.buffer_size, observation), dtype=torch.float32)
        self.action_memory = torch.zeros(self.buffer_size, dtype=torch.int64)
        self.reward_memory = torch.zeros(self.buffer_size, dtype=torch.float32)
        self.terminal_memory = torch.zeros(self.buffer_size, dtype=torch.bool)

    def save_transition(self, state, action, reward, new_state, done):
        index = self.counter % self.buffer_size
        self.state_memory[index] = state
        self.new_state_memory[index] = new_state
        self.action_memory[index] = action
        self.reward_memory[index] = reward
        self.terminal_memory[index] = done
        self.counter += 1

    def sample_buffer(self):
        max = min(self.counter, self.buffer_size)
        batch = np.random.choice(max, BATCH_SIZE, replace=False)
        states = self.state_memory[batch]
        new_states = self.new_state_memory[batch]
        actions = self.action_memory[batch]
        rewards = self.reward_memory[batch]
        dones = self.terminal_memory[batch]
        return (states, actions, rewards, new_states, dones)

    def __len__(self):
        return len(self.buffer_size)

def __len__(self):
    return len(self.buffer_size)

class DuelingDQnetwork(nn.Module):

    def __init__(self, n_actions, model):
        super(DuelingDQnetwork, self).__init__()
        self.n_actions = n_actions
        self.checkpoint_file = os.path.join(DQN_CHECKPOINT_DIR + '/' + TOWN7, model)
        self.Linear1 = nn.Sequential(nn.Linear(95 + 5, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 64), nn.ReLU())
        self.V = nn.Linear(64, 1)
        self.A = nn.Linear(64, self.n_actions)
        self.optimizer = optim.Adam(self.parameters(), lr=DQN_LEARNING_RATE)
        self.loss = nn.MSELoss()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.to(self.device)

    def forward(self, x):
        fc = self.Linear1(x)
        V = self.V(fc)
        A = self.A(fc)
        return (V, A)

    def save_checkpoint(self):
        torch.save(self.state_dict(), self.checkpoint_file)

    def load_checkpoint(self):
        self.load_state_dict(torch.load(self.checkpoint_file))

def save_checkpoint(self):
    torch.save(self.state_dict(), self.checkpoint_file)

def load_checkpoint(self):
    self.load_state_dict(torch.load(self.checkpoint_file))

class Decoder(nn.Module):

    def __init__(self, latent_dims):
        super().__init__()
        self.model_file = os.path.join('autoencoder/model', 'decoder_model.pth')
        self.decoder_linear = nn.Sequential(nn.Linear(latent_dims, 1024), nn.LeakyReLU(), nn.Linear(1024, 9 * 4 * 256), nn.LeakyReLU())
        self.unflatten = nn.Unflatten(dim=1, unflattened_size=(256, 4, 9))
        self.decoder = nn.Sequential(nn.ConvTranspose2d(256, 128, 3, stride=2), nn.LeakyReLU(), nn.ConvTranspose2d(128, 64, 4, stride=2), nn.LeakyReLU(), nn.ConvTranspose2d(64, 32, 3, stride=2, padding=1), nn.LeakyReLU(), nn.ConvTranspose2d(32, 3, 4, stride=2), nn.Sigmoid())

    def forward(self, x):
        x = self.decoder_linear(x)
        x = self.unflatten(x)
        x = self.decoder(x)
        return x

    def save(self):
        torch.save(self.state_dict(), self.model_file)

    def load(self):
        self.load_state_dict(torch.load(self.model_file))

def save(self):
    torch.save(self.state_dict(), self.model_file)

def load(self):
    self.load_state_dict(torch.load(self.model_file))

class VariationalAutoencoder(nn.Module):

    def __init__(self, latent_dims):
        super(VariationalAutoencoder, self).__init__()
        self.model_file = os.path.join('autoencoder/model', 'var_autoencoder.pth')
        self.encoder = VariationalEncoder(latent_dims)
        self.decoder = Decoder(latent_dims)

    def forward(self, x):
        x = x.to(device)
        z = self.encoder(x)
        return self.decoder(z)

    def save(self):
        torch.save(self.state_dict(), self.model_file)
        self.encoder.save()
        self.decoder.save()

    def load(self):
        self.load_state_dict(torch.load(self.model_file))
        self.encoder.load()
        self.decoder.load()

def save(self):
    torch.save(self.state_dict(), self.model_file)
    self.encoder.save()
    self.decoder.save()

def load(self):
    self.load_state_dict(torch.load(self.model_file))
    self.encoder.load()
    self.decoder.load()

class VariationalEncoder(nn.Module):

    def __init__(self, latent_dims):
        super(VariationalEncoder, self).__init__()
        self.model_file = os.path.join('autoencoder/model', 'var_encoder_model.pth')
        self.encoder_layer1 = nn.Sequential(nn.Conv2d(3, 32, 4, stride=2), nn.LeakyReLU())
        self.encoder_layer2 = nn.Sequential(nn.Conv2d(32, 64, 3, stride=2, padding=1), nn.BatchNorm2d(64), nn.LeakyReLU())
        self.encoder_layer3 = nn.Sequential(nn.Conv2d(64, 128, 4, stride=2), nn.LeakyReLU())
        self.encoder_layer4 = nn.Sequential(nn.Conv2d(128, 256, 3, stride=2), nn.BatchNorm2d(256), nn.LeakyReLU())
        self.linear = nn.Sequential(nn.Linear(9 * 4 * 256, 1024), nn.LeakyReLU())
        self.mu = nn.Linear(1024, latent_dims)
        self.sigma = nn.Linear(1024, latent_dims)
        self.N = torch.distributions.Normal(0, 1)
        self.N.loc = self.N.loc.to(device)
        self.N.scale = self.N.scale.to(device)
        self.kl = 0

    def forward(self, x):
        x = x.to(device)
        x = self.encoder_layer1(x)
        x = self.encoder_layer2(x)
        x = self.encoder_layer3(x)
        x = self.encoder_layer4(x)
        x = torch.flatten(x, start_dim=1)
        x = self.linear(x)
        mu = self.mu(x)
        sigma = torch.exp(self.sigma(x))
        z = mu + sigma * self.N.sample(mu.shape)
        self.kl = (sigma ** 2 + mu ** 2 - torch.log(sigma) - 1 / 2).sum()
        return z

    def save(self):
        torch.save(self.state_dict(), self.model_file)

    def load(self):
        self.load_state_dict(torch.load(self.model_file))

def save(self):
    torch.save(self.state_dict(), self.model_file)

def load(self):
    self.load_state_dict(torch.load(self.model_file))

class VariationalAutoencoder(nn.Module):

    def __init__(self, latent_dims):
        super(VariationalAutoencoder, self).__init__()
        self.model_file = os.path.join('autoencoder/model', 'var_autoencoder.pth')
        self.encoder = VariationalEncoder(latent_dims)
        self.decoder = Decoder(latent_dims)

    def forward(self, x):
        x = x.to(device)
        z = self.encoder(x)
        return self.decoder(z)

    def save(self):
        torch.save(self.state_dict(), self.model_file)
        self.encoder.save()
        self.decoder.save()

    def load(self):
        self.load_state_dict(torch.load(self.model_file))
        self.encoder.load()
        self.decoder.load()

def save(self):
    torch.save(self.state_dict(), self.model_file)
    self.encoder.save()
    self.decoder.save()

def load(self):
    self.load_state_dict(torch.load(self.model_file))
    self.encoder.load()
    self.decoder.load()

