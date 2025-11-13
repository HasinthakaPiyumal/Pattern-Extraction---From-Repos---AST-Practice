# Cluster 8

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

class DQNAgent(object):

    def __init__(self, n_actions):
        self.gamma = GAMMA
        self.alpha = DQN_LEARNING_RATE
        self.epsilon = EPSILON
        self.epsilon_end = EPSILON_END
        self.action_space = [i for i in range(n_actions)]
        self.mem_size = MEMORY_SIZE
        self.batch_size = BATCH_SIZE
        self.train_step = 0
        self.replay_buffer = ReplayBuffer(MEMORY_SIZE, 100, n_actions)
        self.q_network_eval = DuelingDQnetwork(n_actions, MODEL_ONLINE)
        self.q_network_target = DuelingDQnetwork(n_actions, MODEL_TARGET)

    def save_transition(self, observation, action, reward, new_observation, done):
        self.replay_buffer.save_transition(observation, action, reward, new_observation, done)

    def get_action(self, observation):
        if np.random.random() > self.epsilon:
            _, advantage = self.q_network_eval.forward(observation)
            action = torch.argmax(advantage).item()
        else:
            action = np.random.choice(self.action_space)
        return action

    def decrese_epsilon(self):
        if self.epsilon > self.epsilon_end:
            self.epsilon -= EPSILON_DECREMENT
        else:
            self.epsilon = self.epsilon_end

    def save_model(self):
        self.q_network_eval.save_checkpoint()
        self.q_network_target.save_checkpoint()

    def load_model(self):
        self.q_network_eval.load_checkpoint()
        self.q_network_target.load_checkpoint()

    def learn(self):
        if self.replay_buffer.counter < self.batch_size:
            return
        self.q_network_eval.optimizer.zero_grad()
        if self.train_step % REPLACE_NETWORK == 0:
            self.q_network_target.load_state_dict(self.q_network_eval.state_dict())
        observation, action, reward, new_observation, done = self.replay_buffer.sample_buffer()
        observation = observation.to(self.q_network_eval.device)
        action = action.to(self.q_network_eval.device)
        reward = reward.to(self.q_network_eval.device)
        new_observation = new_observation.to(self.q_network_eval.device)
        done = done.to(self.q_network_eval.device)
        Vs, As = self.q_network_eval.forward(observation)
        nVs, nAs = self.q_network_target.forward(new_observation)
        q_pred = torch.add(Vs, As - As.mean(dim=1, keepdim=True)).gather(1, action.unsqueeze(-1)).squeeze(-1)
        q_next = torch.add(nVs, nAs - nAs.mean(dim=1, keepdim=True))
        q_target = reward + self.gamma * torch.max(q_next, dim=1)[0].detach()
        q_next[done] = 0.0
        loss = self.q_network_eval.loss(q_target, q_pred).to(self.q_network_eval.device)
        loss.backward()
        self.q_network_eval.optimizer.step()
        self.train_step += 1
        self.decrese_epsilon()

def get_action(self, observation):
    if np.random.random() > self.epsilon:
        _, advantage = self.q_network_eval.forward(observation)
        action = torch.argmax(advantage).item()
    else:
        action = np.random.choice(self.action_space)
    return action

def learn(self):
    if self.replay_buffer.counter < self.batch_size:
        return
    self.q_network_eval.optimizer.zero_grad()
    if self.train_step % REPLACE_NETWORK == 0:
        self.q_network_target.load_state_dict(self.q_network_eval.state_dict())
    observation, action, reward, new_observation, done = self.replay_buffer.sample_buffer()
    observation = observation.to(self.q_network_eval.device)
    action = action.to(self.q_network_eval.device)
    reward = reward.to(self.q_network_eval.device)
    new_observation = new_observation.to(self.q_network_eval.device)
    done = done.to(self.q_network_eval.device)
    Vs, As = self.q_network_eval.forward(observation)
    nVs, nAs = self.q_network_target.forward(new_observation)
    q_pred = torch.add(Vs, As - As.mean(dim=1, keepdim=True)).gather(1, action.unsqueeze(-1)).squeeze(-1)
    q_next = torch.add(nVs, nAs - nAs.mean(dim=1, keepdim=True))
    q_target = reward + self.gamma * torch.max(q_next, dim=1)[0].detach()
    q_next[done] = 0.0
    loss = self.q_network_eval.loss(q_target, q_pred).to(self.q_network_eval.device)
    loss.backward()
    self.q_network_eval.optimizer.step()
    self.train_step += 1
    self.decrese_epsilon()

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

def forward(self, x):
    x = self.decoder_linear(x)
    x = self.unflatten(x)
    x = self.decoder(x)
    return x

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

def forward(self, x):
    x = x.to(device)
    z = self.encoder(x)
    return self.decoder(z)

def train(model, trainloader, optim):
    model.train()
    train_loss = 0.0
    for x, _ in trainloader:
        x = x.to(device)
        x_hat = model(x)
        loss = ((x - x_hat) ** 2).sum() + model.encoder.kl
        optim.zero_grad()
        loss.backward()
        optim.step()
        train_loss += loss.item()
    return train_loss / len(trainloader.dataset)

def test(model, testloader):
    model.eval()
    val_loss = 0.0
    with torch.no_grad():
        for x, _ in testloader:
            x = x.to(device)
            encoded_data = model.encoder(x)
            x_hat = model(x)
            loss = ((x - x_hat) ** 2).sum() + model.encoder.kl
            val_loss += loss.item()
    return val_loss / len(testloader.dataset)

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

def forward(self, x):
    x = x.to(device)
    z = self.encoder(x)
    return self.decoder(z)

