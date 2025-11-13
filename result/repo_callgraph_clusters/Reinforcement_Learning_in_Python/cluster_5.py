# Cluster 5

class QLearningTable:

    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)
        self.q_table_final = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)
        if np.random.uniform() < self.epsilon:
            state_action = self.q_table.loc[observation, :]
            state_action = state_action.reindex(np.random.permutation(state_action.index))
            action = state_action.idxmax()
        else:
            action = np.random.choice(self.actions)
        return action

    def learn(self, state, action, reward, next_state):
        self.check_state_exist(next_state)
        q_predict = self.q_table.loc[state, action]
        if next_state != 'goal' or next_state != 'obstacle':
            q_target = reward + self.gamma * self.q_table.loc[next_state, :].max()
        else:
            q_target = reward
        self.q_table.loc[state, action] += self.lr * (q_target - q_predict)
        return self.q_table.loc[state, action]

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            self.q_table = self.q_table.append(pd.Series([0] * len(self.actions), index=self.q_table.columns, name=state))

    def print_q_table(self):
        e = final_states()
        for i in range(len(e)):
            state = str(e[i])
            for j in range(len(self.q_table.index)):
                if self.q_table.index[j] == state:
                    self.q_table_final.loc[state, :] = self.q_table.loc[state, :]
        print()
        print('Length of final Q-table =', len(self.q_table_final.index))
        print('Final Q-table with values from the final route:')
        print(self.q_table_final)
        print()
        print('Length of full Q-table =', len(self.q_table.index))
        print('Full Q-table:')
        print(self.q_table)

    def plot_results(self, steps, cost):
        f, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
        ax1.plot(np.arange(len(steps)), steps, 'b')
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Steps')
        ax1.set_title('Episode via steps')
        ax2.plot(np.arange(len(cost)), cost, 'r')
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Cost')
        ax2.set_title('Episode via cost')
        plt.tight_layout()
        plt.figure()
        plt.plot(np.arange(len(steps)), steps, 'b')
        plt.title('Episode via steps')
        plt.xlabel('Episode')
        plt.ylabel('Steps')
        plt.figure()
        plt.plot(np.arange(len(cost)), cost, 'r')
        plt.title('Episode via cost')
        plt.xlabel('Episode')
        plt.ylabel('Cost')
        plt.show()

def print_q_table(self):
    e = final_states()
    for i in range(len(e)):
        state = str(e[i])
        for j in range(len(self.q_table.index)):
            if self.q_table.index[j] == state:
                self.q_table_final.loc[state, :] = self.q_table.loc[state, :]
    print()
    print('Length of final Q-table =', len(self.q_table_final.index))
    print('Final Q-table with values from the final route:')
    print(self.q_table_final)
    print()
    print('Length of full Q-table =', len(self.q_table.index))
    print('Full Q-table:')
    print(self.q_table)

def update():
    steps = []
    all_costs = []
    for episode in range(100000):
        observation = env.reset()
        i = 0
        cost = 0
        while True:
            env.render()
            action = RL.choose_action(str(observation))
            observation_, reward, done = env.step(action)
            cost += RL.learn(str(observation), action, reward, str(observation_))
            observation = observation_
            i += 1
            if done:
                steps += [i]
                all_costs += [cost]
                break
    env.final()
    RL.print_q_table()
    RL.plot_results(steps, all_costs)

class SarsaTable:

    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)
        self.q_table_final = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)
        if np.random.uniform() < self.epsilon:
            state_action = self.q_table.loc[observation, :]
            state_action = state_action.reindex(np.random.permutation(state_action.index))
            action = state_action.idxmax()
        else:
            action = np.random.choice(self.actions)
        return action

    def learn(self, state, action, reward, next_state, next_action):
        self.check_state_exist(next_state)
        q_predict = self.q_table.loc[state, action]
        if next_state != 'goal' or next_state != 'obstacle':
            q_target = reward + self.gamma * self.q_table.loc[next_state, next_action]
        else:
            q_target = reward
        self.q_table.loc[state, action] += self.lr * (q_target - q_predict)
        return self.q_table.loc[state, action]

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            self.q_table = self.q_table.append(pd.Series([0] * len(self.actions), index=self.q_table.columns, name=state))

    def print_q_table(self):
        e = final_states()
        for i in range(len(e)):
            state = str(e[i])
            for j in range(len(self.q_table.index)):
                if self.q_table.index[j] == state:
                    self.q_table_final.loc[state, :] = self.q_table.loc[state, :]
        print()
        print('Length of final Q-table =', len(self.q_table_final.index))
        print('Final Q-table with values from the final route:')
        print(self.q_table_final)
        print()
        print('Length of full Q-table =', len(self.q_table.index))
        print('Full Q-table:')
        print(self.q_table)

    def plot_results(self, steps, cost):
        f, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
        ax1.plot(np.arange(len(steps)), steps, 'b')
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Steps')
        ax1.set_title('Episode via steps')
        ax2.plot(np.arange(len(cost)), cost, 'r')
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Cost')
        ax2.set_title('Episode via cost')
        plt.tight_layout()
        plt.figure()
        plt.plot(np.arange(len(steps)), steps, 'b')
        plt.title('Episode via steps')
        plt.xlabel('Episode')
        plt.ylabel('Steps')
        plt.figure()
        plt.plot(np.arange(len(cost)), cost, 'r')
        plt.title('Episode via cost')
        plt.xlabel('Episode')
        plt.ylabel('Cost')
        plt.show()

def print_q_table(self):
    e = final_states()
    for i in range(len(e)):
        state = str(e[i])
        for j in range(len(self.q_table.index)):
            if self.q_table.index[j] == state:
                self.q_table_final.loc[state, :] = self.q_table.loc[state, :]
    print()
    print('Length of final Q-table =', len(self.q_table_final.index))
    print('Final Q-table with values from the final route:')
    print(self.q_table_final)
    print()
    print('Length of full Q-table =', len(self.q_table.index))
    print('Full Q-table:')
    print(self.q_table)

def update():
    steps = []
    all_costs = []
    for episode in range(1000):
        observation = env.reset()
        i = 0
        cost = 0
        action = RL.choose_action(str(observation))
        while True:
            env.render()
            observation_, reward, done = env.step(action)
            action_ = RL.choose_action(str(observation_))
            cost += RL.learn(str(observation), action, reward, str(observation_), action_)
            observation = observation_
            action = action_
            i += 1
            if done:
                steps += [i]
                all_costs += [cost]
                break
    env.final()
    RL.print_q_table()
    RL.plot_results(steps, all_costs)

class SarsaTable:

    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)
        self.q_table_final = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)
        if np.random.uniform() < self.epsilon:
            state_action = self.q_table.loc[observation, :]
            state_action = state_action.reindex(np.random.permutation(state_action.index))
            action = state_action.idxmax()
        else:
            action = np.random.choice(self.actions)
        return action

    def learn(self, state, action, reward, next_state, next_action):
        self.check_state_exist(next_state)
        q_predict = self.q_table.loc[state, action]
        if next_state != 'goal' or next_state != 'obstacle':
            q_target = reward + self.gamma * self.q_table.loc[next_state, next_action]
        else:
            q_target = reward
        self.q_table.loc[state, action] += self.lr * (q_target - q_predict)
        return self.q_table.loc[state, action]

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            self.q_table = self.q_table.append(pd.Series([0] * len(self.actions), index=self.q_table.columns, name=state))

    def print_q_table(self):
        e = final_states()
        for i in range(len(e)):
            state = str(e[i])
            for j in range(len(self.q_table.index)):
                if self.q_table.index[j] == state:
                    self.q_table_final.loc[state, :] = self.q_table.loc[state, :]
        print()
        print('Length of final Q-table =', len(self.q_table_final.index))
        print('Final Q-table with values from the final route:')
        print(self.q_table_final)
        print()
        print('Length of full Q-table =', len(self.q_table.index))
        print('Full Q-table:')
        print(self.q_table)

    def plot_results(self, steps, cost):
        f, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
        ax1.plot(np.arange(len(steps)), steps, 'b')
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Steps')
        ax1.set_title('Episode via steps')
        ax2.plot(np.arange(len(cost)), cost, 'r')
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Cost')
        ax2.set_title('Episode via cost')
        plt.tight_layout()
        plt.figure()
        plt.plot(np.arange(len(steps)), steps, 'b')
        plt.title('Episode via steps')
        plt.xlabel('Episode')
        plt.ylabel('Steps')
        plt.figure()
        plt.plot(np.arange(len(cost)), cost, 'r')
        plt.title('Episode via cost')
        plt.xlabel('Episode')
        plt.ylabel('Cost')
        plt.show()

def print_q_table(self):
    e = final_states()
    for i in range(len(e)):
        state = str(e[i])
        for j in range(len(self.q_table.index)):
            if self.q_table.index[j] == state:
                self.q_table_final.loc[state, :] = self.q_table.loc[state, :]
    print()
    print('Length of final Q-table =', len(self.q_table_final.index))
    print('Final Q-table with values from the final route:')
    print(self.q_table_final)
    print()
    print('Length of full Q-table =', len(self.q_table.index))
    print('Full Q-table:')
    print(self.q_table)

def update():
    steps = []
    all_costs = []
    for episode in range(6000):
        observation = env.reset()
        i = 0
        cost = 0
        action = RL.choose_action(str(observation))
        while True:
            env.render()
            observation_, reward, done = env.step(action)
            action_ = RL.choose_action(str(observation_))
            cost += RL.learn(str(observation), action, reward, str(observation_), action_)
            observation = observation_
            action = action_
            i += 1
            if done:
                steps += [i]
                all_costs += [cost]
                break
    env.final()
    RL.print_q_table()
    RL.plot_results(steps, all_costs)

class QLearningTable:

    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)
        self.q_table_final = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)
        if np.random.uniform() < self.epsilon:
            state_action = self.q_table.loc[observation, :]
            state_action = state_action.reindex(np.random.permutation(state_action.index))
            action = state_action.idxmax()
        else:
            action = np.random.choice(self.actions)
        return action

    def learn(self, state, action, reward, next_state):
        self.check_state_exist(next_state)
        q_predict = self.q_table.loc[state, action]
        if next_state != 'goal' or next_state != 'obstacle':
            q_target = reward + self.gamma * self.q_table.loc[next_state, :].max()
        else:
            q_target = reward
        self.q_table.loc[state, action] += self.lr * (q_target - q_predict)
        return self.q_table.loc[state, action]

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            self.q_table = self.q_table.append(pd.Series([0] * len(self.actions), index=self.q_table.columns, name=state))

    def print_q_table(self):
        e = final_states()
        for i in range(len(e)):
            state = str(e[i])
            for j in range(len(self.q_table.index)):
                if self.q_table.index[j] == state:
                    self.q_table_final.loc[state, :] = self.q_table.loc[state, :]
        print()
        print('Length of final Q-table =', len(self.q_table_final.index))
        print('Final Q-table with values from the final route:')
        print(self.q_table_final)
        print()
        print('Length of full Q-table =', len(self.q_table.index))
        print('Full Q-table:')
        print(self.q_table)

    def plot_results(self, steps, cost):
        f, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
        ax1.plot(np.arange(len(steps)), steps, 'b')
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Steps')
        ax1.set_title('Episode via steps')
        ax2.plot(np.arange(len(cost)), cost, 'r')
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Cost')
        ax2.set_title('Episode via cost')
        plt.tight_layout()
        plt.figure()
        plt.plot(np.arange(len(steps)), steps, 'b')
        plt.title('Episode via steps')
        plt.xlabel('Episode')
        plt.ylabel('Steps')
        plt.figure()
        plt.plot(np.arange(len(cost)), cost, 'r')
        plt.title('Episode via cost')
        plt.xlabel('Episode')
        plt.ylabel('Cost')
        plt.show()

def print_q_table(self):
    e = final_states()
    for i in range(len(e)):
        state = str(e[i])
        for j in range(len(self.q_table.index)):
            if self.q_table.index[j] == state:
                self.q_table_final.loc[state, :] = self.q_table.loc[state, :]
    print()
    print('Length of final Q-table =', len(self.q_table_final.index))
    print('Final Q-table with values from the final route:')
    print(self.q_table_final)
    print()
    print('Length of full Q-table =', len(self.q_table.index))
    print('Full Q-table:')
    print(self.q_table)

def update():
    steps = []
    all_costs = []
    for episode in range(5000):
        observation = env.reset()
        i = 0
        cost = 0
        while True:
            env.render()
            action = RL.choose_action(str(observation))
            observation_, reward, done = env.step(action)
            cost += RL.learn(str(observation), action, reward, str(observation_))
            observation = observation_
            i += 1
            if done:
                steps += [i]
                all_costs += [cost]
                break
    env.final()
    RL.print_q_table()
    RL.plot_results(steps, all_costs)

class QLearningTable:

    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)
        self.q_table_final = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)
        if np.random.uniform() < self.epsilon:
            state_action = self.q_table.loc[observation, :]
            state_action = state_action.reindex(np.random.permutation(state_action.index))
            action = state_action.idxmax()
        else:
            action = np.random.choice(self.actions)
        return action

    def learn(self, state, action, reward, next_state):
        self.check_state_exist(next_state)
        q_predict = self.q_table.loc[state, action]
        if next_state != 'goal' or next_state != 'obstacle':
            q_target = reward + self.gamma * self.q_table.loc[next_state, :].max()
        else:
            q_target = reward
        self.q_table.loc[state, action] += self.lr * (q_target - q_predict)
        return self.q_table.loc[state, action]

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            self.q_table = self.q_table.append(pd.Series([0] * len(self.actions), index=self.q_table.columns, name=state))

    def print_q_table(self):
        e = final_states()
        for i in range(len(e)):
            state = str(e[i])
            for j in range(len(self.q_table.index)):
                if self.q_table.index[j] == state:
                    self.q_table_final.loc[state, :] = self.q_table.loc[state, :]
        print()
        print('Length of final Q-table =', len(self.q_table_final.index))
        print('Final Q-table with values from the final route:')
        print(self.q_table_final)
        print()
        print('Length of full Q-table =', len(self.q_table.index))
        print('Full Q-table:')
        print(self.q_table)

    def plot_results(self, steps, cost):
        f, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
        ax1.plot(np.arange(len(steps)), steps, 'b')
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Steps')
        ax1.set_title('Episode via steps')
        ax2.plot(np.arange(len(cost)), cost, 'r')
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Cost')
        ax2.set_title('Episode via cost')
        plt.tight_layout()
        plt.figure()
        plt.plot(np.arange(len(steps)), steps, 'b')
        plt.title('Episode via steps')
        plt.xlabel('Episode')
        plt.ylabel('Steps')
        plt.figure()
        plt.plot(np.arange(len(cost)), cost, 'r')
        plt.title('Episode via cost')
        plt.xlabel('Episode')
        plt.ylabel('Cost')
        plt.show()

def print_q_table(self):
    e = final_states()
    for i in range(len(e)):
        state = str(e[i])
        for j in range(len(self.q_table.index)):
            if self.q_table.index[j] == state:
                self.q_table_final.loc[state, :] = self.q_table.loc[state, :]
    print()
    print('Length of final Q-table =', len(self.q_table_final.index))
    print('Final Q-table with values from the final route:')
    print(self.q_table_final)
    print()
    print('Length of full Q-table =', len(self.q_table.index))
    print('Full Q-table:')
    print(self.q_table)

def update():
    steps = []
    all_costs = []
    for episode in range(1000):
        observation = env.reset()
        i = 0
        cost = 0
        while True:
            env.render()
            action = RL.choose_action(str(observation))
            observation_, reward, done = env.step(action)
            cost += RL.learn(str(observation), action, reward, str(observation_))
            observation = observation_
            i += 1
            if done:
                steps += [i]
                all_costs += [cost]
                break
    env.final()
    RL.print_q_table()
    RL.plot_results(steps, all_costs)

