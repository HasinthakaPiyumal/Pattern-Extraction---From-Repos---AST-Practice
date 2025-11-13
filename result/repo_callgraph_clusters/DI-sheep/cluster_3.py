# Cluster 3

@name_space.route('/')
class MainClass(Resource):

    def options(self):
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response

    @app.expect(model)
    def post(self):
        try:
            t_start = time.time()
            data = request.json
            cmd, arg, uid = (data['command'], data['argument'], data['uid'])
            ip = request.remote_addr + uid
            if ip not in envs:
                if cmd == 'reset':
                    if len(envs) >= MAX_ENV_NUM:
                        response = jsonify({'statusCode': 501, 'status': 'No enough env resource, please wait a moment'})
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response
                    else:
                        env = SheepEnv(1, agent=True, max_padding=True)
                        env.seed(0)
                        envs[ip] = {'env': env, 'update_time': time.time()}
                else:
                    response = jsonify({'statusCode': 501, 'status': 'No response for too long time, please reset the game'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
            else:
                env = envs[ip]['env']
                envs[ip]['update_time'] = time.time()
            if cmd == 'reset':
                obs = env.reset(arg)
                action = model.compute_action(obs)
                scene = [item.to_json() for item in env.scene if item is not None]
                response = jsonify({'statusCode': 200, 'status': 'Execution action', 'result': {'scene': scene, 'max_item_num': env.total_item_num, 'action': action}})
            elif cmd == 'step':
                obs, _, done, _ = env.step(arg)
                action = model.compute_action(obs)
                scene = [item.to_json() for item in env.scene if item is not None]
                bucket = [item.to_json() for item in env.bucket]
                response = jsonify({'statusCode': 200, 'status': 'Execution action', 'result': {'scene': scene, 'bucket': bucket, 'done': done, 'action': action}})
            else:
                response = jsonify({'statusCode': 500, 'status': 'Invalid command: {}'.format(cmd)})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            print('backend process time: {}'.format(time.time() - t_start))
            print('current env number: {}'.format(len(envs)))
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            import traceback
            print(repr(e))
            print(traceback.format_exc())
            response = jsonify({'statusCode': 500, 'status': 'Could not execute action'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

def options(self):
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    return response

@app.expect(model)
def post(self):
    try:
        t_start = time.time()
        data = request.json
        cmd, arg, uid = (data['command'], data['argument'], data['uid'])
        ip = request.remote_addr + uid
        if ip not in envs:
            if cmd == 'reset':
                if len(envs) >= MAX_ENV_NUM:
                    response = jsonify({'statusCode': 501, 'status': 'No enough env resource, please wait a moment'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
                else:
                    env = SheepEnv(1, agent=True, max_padding=True)
                    env.seed(0)
                    envs[ip] = {'env': env, 'update_time': time.time()}
            else:
                response = jsonify({'statusCode': 501, 'status': 'No response for too long time, please reset the game'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
        else:
            env = envs[ip]['env']
            envs[ip]['update_time'] = time.time()
        if cmd == 'reset':
            obs = env.reset(arg)
            action = model.compute_action(obs)
            scene = [item.to_json() for item in env.scene if item is not None]
            response = jsonify({'statusCode': 200, 'status': 'Execution action', 'result': {'scene': scene, 'max_item_num': env.total_item_num, 'action': action}})
        elif cmd == 'step':
            obs, _, done, _ = env.step(arg)
            action = model.compute_action(obs)
            scene = [item.to_json() for item in env.scene if item is not None]
            bucket = [item.to_json() for item in env.bucket]
            response = jsonify({'statusCode': 200, 'status': 'Execution action', 'result': {'scene': scene, 'bucket': bucket, 'done': done, 'action': action}})
        else:
            response = jsonify({'statusCode': 500, 'status': 'Invalid command: {}'.format(cmd)})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        print('backend process time: {}'.format(time.time() - t_start))
        print('current env number: {}'.format(len(envs)))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        import traceback
        print(repr(e))
        print(traceback.format_exc())
        response = jsonify({'statusCode': 500, 'status': 'Could not execute action'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@name_space.route('/')
class MainClass(Resource):

    def options(self):
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response

    @app.expect(model)
    def post(self):
        try:
            t_start = time.time()
            data = request.json
            cmd, arg, uid = (data['command'], data['argument'], data['uid'])
            ip = request.remote_addr
            ip = str(ip) + str(uid)
            if ip not in envs:
                if cmd == 'reset':
                    if len(envs) >= MAX_ENV_NUM:
                        response = jsonify({'statusCode': 501, 'status': 'No enough env resource, please wait a moment'})
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response
                    else:
                        env = SheepEnv(1, agent=False)
                        envs[ip] = {'env': env, 'update_time': time.time()}
                else:
                    response = jsonify({'statusCode': 501, 'status': 'No response for too long time, please reset the game'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
            else:
                env = envs[ip]['env']
                envs[ip]['update_time'] = time.time()
            if cmd == 'reset':
                env.reset(arg)
                scene = [item.to_json() for item in env.scene if item is not None]
                response = jsonify({'statusCode': 200, 'status': 'Execution action', 'result': {'scene': scene, 'max_item_num': env.total_item_num}})
            elif cmd == 'step':
                _, _, done, _ = env.step(arg)
                scene = [item.to_json() for item in env.scene if item is not None]
                bucket = [item.to_json() for item in env.bucket]
                response = jsonify({'statusCode': 200, 'status': 'Execution action', 'result': {'scene': scene, 'bucket': bucket, 'done': done}})
            else:
                response = jsonify({'statusCode': 500, 'status': 'Invalid command: {}'.format(cmd)})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            print('backend process time: {}'.format(time.time() - t_start))
            print('current env number: {}'.format(len(envs)))
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            import traceback
            print(repr(e))
            print(traceback.format_exc())
            response = jsonify({'statusCode': 500, 'status': 'Could not execute action'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

def options(self):
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    return response

@app.expect(model)
def post(self):
    try:
        t_start = time.time()
        data = request.json
        cmd, arg, uid = (data['command'], data['argument'], data['uid'])
        ip = request.remote_addr
        ip = str(ip) + str(uid)
        if ip not in envs:
            if cmd == 'reset':
                if len(envs) >= MAX_ENV_NUM:
                    response = jsonify({'statusCode': 501, 'status': 'No enough env resource, please wait a moment'})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
                else:
                    env = SheepEnv(1, agent=False)
                    envs[ip] = {'env': env, 'update_time': time.time()}
            else:
                response = jsonify({'statusCode': 501, 'status': 'No response for too long time, please reset the game'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
        else:
            env = envs[ip]['env']
            envs[ip]['update_time'] = time.time()
        if cmd == 'reset':
            env.reset(arg)
            scene = [item.to_json() for item in env.scene if item is not None]
            response = jsonify({'statusCode': 200, 'status': 'Execution action', 'result': {'scene': scene, 'max_item_num': env.total_item_num}})
        elif cmd == 'step':
            _, _, done, _ = env.step(arg)
            scene = [item.to_json() for item in env.scene if item is not None]
            bucket = [item.to_json() for item in env.bucket]
            response = jsonify({'statusCode': 200, 'status': 'Execution action', 'result': {'scene': scene, 'bucket': bucket, 'done': done}})
        else:
            response = jsonify({'statusCode': 500, 'status': 'Invalid command: {}'.format(cmd)})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        print('backend process time: {}'.format(time.time() - t_start))
        print('current env number: {}'.format(len(envs)))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        import traceback
        print(repr(e))
        print(traceback.format_exc())
        response = jsonify({'statusCode': 500, 'status': 'Could not execute action'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

class Item:

    def __init__(self, icon, offset, row, column):
        self.icon = icon
        self.offset = offset
        self.row = row
        self.column = column
        self.uid = str(uuid.uuid4())
        self.x = column * 100 + offset
        self.y = row * 100 + offset
        self.grid_x = self.x % 25
        self.grid_y = self.y % 25
        self.accessible = 1
        self.visible = 1

    def __repr__(self) -> str:
        return 'icon({})'.format(self.icon)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=2)

def __init__(self, icon, offset, row, column):
    self.icon = icon
    self.offset = offset
    self.row = row
    self.column = column
    self.uid = str(uuid.uuid4())
    self.x = column * 100 + offset
    self.y = row * 100 + offset
    self.grid_x = self.x % 25
    self.grid_y = self.y % 25
    self.accessible = 1
    self.visible = 1

def __repr__(self) -> str:
    return 'icon({})'.format(self.icon)

class SheepModel(nn.Module):
    mode = ['compute_actor', 'compute_critic', 'compute_actor_critic']

    def __init__(self, item_obs_size=60, item_num=30, item_encoder_type='TF', bucket_obs_size=30, global_obs_size=17, hidden_size=64, activation=nn.ReLU(), ttorch_return=False):
        super(SheepModel, self).__init__()
        self.item_encoder = ItemEncoder(item_obs_size, item_num, item_encoder_type, hidden_size, activation=activation)
        self.bucket_encoder = MLP(bucket_obs_size, hidden_size, hidden_size, layer_num=3, activation=activation)
        self.global_encoder = MLP(global_obs_size, hidden_size, hidden_size, layer_num=2, activation=activation)
        self.value_head = nn.Sequential(MLP(hidden_size, hidden_size, hidden_size, layer_num=2, activation=activation), nn.Linear(hidden_size, 1))
        self.ttorch_return = ttorch_return

    def compute_actor(self, x):
        item_embedding = self.item_encoder(x['item_obs'])
        bucket_embedding = self.bucket_encoder(x['bucket_obs'])
        global_embedding = self.global_encoder(x['global_obs'])
        key = item_embedding
        query = bucket_embedding + global_embedding
        query = query.unsqueeze(1)
        logit = (key * query).sum(2)
        logit.masked_fill_(~x['action_mask'].bool(), value=-1000000000.0)
        if self.ttorch_return:
            return logit
        else:
            return {'logit': logit}

    def compute_critic(self, x):
        item_embedding = self.item_encoder(x['item_obs'])
        bucket_embedding = self.bucket_encoder(x['bucket_obs'])
        global_embedding = self.global_encoder(x['global_obs'])
        embedding = item_embedding.mean(1) + bucket_embedding + global_embedding
        value = self.value_head(embedding)
        if self.ttorch_return:
            return value.squeeze(1)
        else:
            return {'value': value.squeeze(1)}

    def compute_actor_critic(self, x):
        item_embedding = self.item_encoder(x['item_obs'])
        bucket_embedding = self.bucket_encoder(x['bucket_obs'])
        global_embedding = self.global_encoder(x['global_obs'])
        key = item_embedding
        query = bucket_embedding + global_embedding
        query = query.unsqueeze(1)
        logit = (key * query).sum(2)
        logit.masked_fill_(~x['action_mask'].bool(), value=-1000000000.0)
        embedding = item_embedding.mean(1) + bucket_embedding + global_embedding
        value = self.value_head(embedding)
        if self.ttorch_return:
            return ttorch.as_tensor({'logit': logit, 'value': value.squeeze(1)})
        else:
            return {'logit': logit, 'value': value.squeeze(1)}

    def forward(self, x, mode):
        assert mode in self.mode, 'not support forward mode: {}/{}'.format(mode, self.mode)
        return getattr(self, mode)(x)

    def compute_action(self, x):
        x = unsqueeze(to_tensor(x))
        with torch.no_grad():
            logit = self.compute_actor(x)['logit']
            return logit.argmax(dim=-1)[0].item()

def forward(self, x, mode):
    assert mode in self.mode, 'not support forward mode: {}/{}'.format(mode, self.mode)
    return getattr(self, mode)(x)

