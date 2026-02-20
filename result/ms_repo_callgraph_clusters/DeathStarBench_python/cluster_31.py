# Cluster 31

async def upload_cast_info(session, addr, cast):
    async with session.post(addr + '/wrk2-api/cast-info/write', json=cast) as resp:
        return await resp.text()

# Node: post
# Node: text
async def upload_plot(session, addr, plot):
    async with session.post(addr + '/wrk2-api/plot/write', json=plot) as resp:
        return await resp.text()

async def upload_movie_info(session, addr, movie):
    async with session.post(addr + '/wrk2-api/movie-info/write', json=movie) as resp:
        return await resp.text()

async def register_movie(session, addr, movie):
    params = {'title': movie['title'], 'movie_id': movie['movie_id']}
    async with session.post(addr + '/wrk2-api/movie/register', data=params) as resp:
        return await resp.text()

# Node: print
# Node: int
# Node: time
# Node: sleep
# Node: filter
# Node: loads
# Node: dumps
async def upload_follow(session, addr, user_0, user_1):
    payload = {'user_name': 'username_' + user_0, 'followee_name': 'username_' + user_1}
    async with session.post(addr + '/wrk2-api/user/follow', data=payload) as resp:
        return await resp.text()

async def upload_register(session, addr, user):
    payload = {'first_name': 'first_name_' + user, 'last_name': 'last_name_' + user, 'username': 'username_' + user, 'password': 'password_' + user, 'user_id': user}
    async with session.post(addr + '/wrk2-api/user/register', data=payload) as resp:
        return await resp.text()

def getNumNodes(file):
    return int(file.readline())

# Node: readline
def reviews():
    url = 'http://localhost:5000/review'
    payload = {'hotelId': '2', 'username': 'Cornell_0', 'password': '0000000000'}
    t_before = time.time()
    r = requests.get(url, params=payload)
    t_after = time.time()
    t = t_after - t_before
    print(r.text)
    print('review=', t)

# Node: get
@app.method(name='forward')
def forward(request: InvokeMethodRequest) -> InvokeMethodResponse:
    global promLat
    if request.content_type != 'application/json':
        logging.error('Invalid content type: %s' % request.content_type)
        return InvokeMethodResponse(data='Invalid content type: %s' % request.content_type, content_type='text/plain')
    req = json.loads(request.text())
    send_unix_ms = float(req['send_unix_ms'])
    method = req['method']
    del req['method']
    downstream = req['downstream']
    del req['downstream']
    epoch = time.time() * 1000
    req['send_unix_ms'] = int(epoch)
    serv_lat = epoch - send_unix_ms
    with DaprClient(max_grpc_message_length=MAX_PAYLOAD) as d:
        resp = d.invoke_method(downstream, method, data=json.dumps(req))
    is_resp_json = True
    try:
        resp_data = json.loads(resp.text())
    except:
        is_resp_json = False
    if is_resp_json:
        epoch = time.time() * 1000
        if 'send_unix_ms' in resp_data:
            serv_lat += epoch - resp_data['send_unix_ms']
            resp_data['send_unix_ms'] = int(epoch)
        promLat.observe(serv_lat)
        return InvokeMethodResponse(data=json.dumps(resp_data), content_type='application/json')
    else:
        promLat.observe(serv_lat)
        return InvokeMethodResponse(data=resp.text(), content_type='application/octet-stream')

# Node: error
# Node: InvokeMethodResponse
# Node: float
# Node: DaprClient
# Node: invoke_method
# Node: observe
# Node: method
def forward(text):
    service_url = 'http://localhost:31789/v1.0/invoke/dapr-proxy/method/forward'
    cont = {'user_id': 'Integrity', 'text': 'Where is the drone?', 'images': []}
    epoch = int(time.time() * 1000)
    post_id = 'Integrity*' + str(epoch)
    payload = {'downstream': 'dapr-post', 'method': 'save', 'post_id': post_id, 'content': cont, 'send_unix_ms': epoch}
    r = requests.post(service_url, json=payload)
    print(r.text)

def save_post(user: str, num_img: int):
    post_images = []
    img_list = list(images.keys())
    random.shuffle(img_list)
    sel_img = img_list[:num_img]
    for img in sel_img:
        post_images.append(b64_images[img])
    unix_ms = int(time.time() * 1000)
    text = '%s shouts out at %d: Fakers get out of academia!' % (user, unix_ms)
    payload = {'user_id': user, 'text': text, 'images': post_images, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.post(save_url, json=payload)
    return json.loads(r.text)['post_id']

# Node: shuffle
def del_post(user: str, post: str):
    payload = {'user_id': user, 'post_id': post, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.post(del_url, json=payload)
    return json.loads(r.text)['post_id']

def read_tl(user: str, earl_unix_ms: int, num_posts: int, user_tl: bool):
    payload = {'user_id': user, 'user_tl': user_tl, 'earl_unix_milli': earl_unix_ms, 'posts': num_posts, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.get(timeline_url, json=payload)
    return json.loads(r.text)

def print_tl(tl: dict):
    print('-- num_posts: %d' % len(tl['posts']))
    for post_id in tl['posts']:
        print_post(tl['posts'][post_id])
    print('########################')

# Node: print_post
def print_tl_post(tl: dict, post: str):
    if post not in tl['posts']:
        print('Error: post %s not in timeline of user %s' % (post, user))
    else:
        print_post(tl['posts'][post])
    print('########################')

def print_post(post: dict):
    print('-- post_id: %s' % post['post_id'])
    print('---- contents:')
    print('------ user_id: %s' % post['content']['user_id'])
    print('------ text: %s' % post['content']['text'])
    if post['content']['images'] != None:
        print('------ images: %s' % ','.join(post['content']['images']))
    print('---- meta:')
    if post['meta']['sentiment'] != None:
        print('------ sentiment: %s' % post['meta']['sentiment'])
    if post['meta']['objects'] != None:
        print('------ objects:')
        for img in post['meta']['objects']:
            print('-------- %s: %s' % (img, post['meta']['objects'][img]))
    if post['comments']['comments'] != None:
        print('---- comments:')
        for com in post['comments']['comments']:
            print('------ comment_id: %s, user_id: %s, reply_to: %s, text: %s' % (com['comment_id'], com['user_id'], com['reply_to'], com['text']))
    if post['upvotes'] != None:
        print('---- upvotes: %s' % ','.join(post['upvotes']))

def comment_tl_post(tl: dict, user: str, post_id: str, text: str):
    print('-- num_posts: %d' % len(tl['posts']))
    if post_id not in tl['posts']:
        print('Error: post %s not in timeline of user %s' % (post_id, user))
    else:
        post = tl['posts'][post_id]
        reply_to = ''
        if post['comments']['comments'] != None:
            reply_to = post['comments']['comments'][-1]['comment_id']
        payload = {'post_id': post_id, 'send_unix_ms': int(time.time() * 1000), 'user_id': user, 'reply_to': reply_to, 'text': text}
        r = requests.post(comment_url, json=payload)
        return json.loads(r.text)['post_id']

def transl(text):
    payload = {'send_unix_ms': int(round(time.time() * 1000)), 'text': text}
    r = requests.post(transl_url, json=payload)
    tr = json.loads(r.text)['translation']
    print('%s -> %s' % (text, tr))

# Node: round
def save_post(user: str, num_img: int):
    post_images = []
    img_list = list(images.keys())
    random.shuffle(img_list)
    sel_img = img_list[:num_img]
    for img in sel_img:
        post_images.append(b64_images[img])
    unix_ms = int(time.time() * 1000)
    text = '%s shouts out at %d: Fakers get out of academia!' % (user, unix_ms)
    payload = {'user_id': user, 'text': text, 'images': post_images, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.post(save_url, json=payload)
    return json.loads(r.text)['post_id']

def del_post(user: str, post: str):
    payload = {'user_id': user, 'post_id': post, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.post(del_url, json=payload)
    return json.loads(r.text)['post_id']

def read_tl(user: str, earl_unix_ms: int, num_posts: int, user_tl: bool):
    payload = {'user_id': user, 'user_tl': user_tl, 'earl_unix_milli': earl_unix_ms, 'posts': num_posts, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.get(timeline_url, json=payload)
    return json.loads(r.text)

def print_tl(tl: dict):
    print('-- num_posts: %d' % len(tl['posts']))
    for post_id in tl['posts']:
        print_post(tl['posts'][post_id])
    print('########################')

def print_post(post: dict):
    print('-- post_id: %s' % post['post_id'])
    print('---- contents:')
    print('------ user_id: %s' % post['content']['user_id'])
    print('------ text: %s' % post['content']['text'])
    if post['content']['images'] != None:
        print('------ images: %s' % ','.join(post['content']['images']))
    print('---- meta:')
    if post['meta']['sentiment'] != None:
        print('------ sentiment: %s' % post['meta']['sentiment'])
    if post['meta']['objects'] != None:
        print('------ objects:')
        for img in post['meta']['objects']:
            print('-------- %s: %s' % (img, post['meta']['objects'][img]))
    if post['comments']['comments'] != None:
        print('---- comments:')
        for com in post['comments']['comments']:
            print('------ comment_id: %s, user_id: %s, reply_to: %s, text: %s' % (com['comment_id'], com['user_id'], com['reply_to'], com['text']))
    if post['upvotes'] != None:
        print('---- upvotes: %s' % ','.join([post['upvotes']]))

def test_tl_img(tl):
    print('-- num_posts: %d' % len(tl['posts']))
    for post_id in tl['posts']:
        if tl['posts'][post_id]['content']['images'] != None:
            print('-- images in post: %s' % post_id)
            for img in tl['posts'][post_id]['content']['images']:
                payload = {'image': img, 'send_unix_ms': int(time.time() * 1000)}
                r = requests.get(image_url, json=payload)
                print(len(r.text))
                pil_img = Image.open(io.BytesIO(base64.b64decode(r.text)))
                print('----', pil_img)
    print('########################')

# Node: BytesIO
# Node: b64decode
def save_post(user: str, num_img: int):
    post_images = []
    img_list = list(images.keys())
    random.shuffle(img_list)
    sel_img = img_list[:num_img]
    for img in sel_img:
        post_images.append(b64_images[img])
    unix_ms = int(time.time() * 1000)
    text = '%s shouts out at %d: Fakers get out of academia!' % (user, unix_ms)
    payload = {'user_id': user, 'text': text, 'images': post_images, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.post(save_url, json=payload)
    return json.loads(r.text)['post_id']

def del_post(user: str, post: str):
    payload = {'user_id': user, 'post_id': post, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.post(del_url, json=payload)
    return json.loads(r.text)['post_id']

def read_tl(user: str, earl_unix_ms: int, num_posts: int, user_tl: bool):
    payload = {'user_id': user, 'user_tl': user_tl, 'earl_unix_milli': earl_unix_ms, 'posts': num_posts, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.get(timeline_url, json=payload)
    return json.loads(r.text)

def print_tl(tl: dict):
    print('-- num_posts: %d' % len(tl['posts']))
    for post_id in tl['posts']:
        print_post(tl['posts'][post_id])
    print('########################')

def print_tl_post(tl: dict, post: str, user: str):
    if post not in tl['posts']:
        print('Error: post %s not in timeline of user %s' % (post, user))
    else:
        print_post(tl['posts'][post])
    print('########################')

def print_post(post: dict):
    print('-- post_id: %s' % post['post_id'])
    print('---- contents:')
    print('------ user_id: %s' % post['content']['user_id'])
    print('------ text: %s' % post['content']['text'])
    if post['content']['images'] != None:
        print('------ images: %s' % ','.join(post['content']['images']))
    print('---- meta:')
    if post['meta']['sentiment'] != None:
        print('------ sentiment: %s' % post['meta']['sentiment'])
    if post['meta']['objects'] != None:
        print('------ objects:')
        for img in post['meta']['objects']:
            print('-------- %s: %s' % (img, post['meta']['objects'][img]))
    if post['comments']['comments'] != None:
        print('---- comments:')
        for com in post['comments']['comments']:
            print('------ comment_id: %s, user_id: %s, reply_to: %s, text: %s' % (com['comment_id'], com['user_id'], com['reply_to'], com['text']))
    if post['upvotes'] != None:
        print('---- upvotes: %s' % ','.join(post['upvotes']))

def upvote_tl_post(tl: dict, user: str, post: str):
    print('-- num_posts: %d' % len(tl['posts']))
    if post not in tl['posts']:
        print('Error: post %s not in timeline of user %s' % (post, user))
    else:
        payload = {'user_id': user, 'post_id': post, 'send_unix_ms': int(time.time() * 1000)}
        r = requests.post(upvote_url, json=payload)
        return json.loads(r.text)['post_id']

def upload_video(user: str, video_b64: str, desc: str, dt: str):
    unix_ms = int(time.time() * 1000)
    payload = {'user': user, 'video_b64': video_b64, 'description': desc, 'date': dt, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.post(upload_url, json=payload)
    print(r.text)
    return json.loads(r.text)['video_id']

def get_video(video: str, res: str):
    payload = {'video': video, 'resolution': res, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.get(video_url, json=payload)
    if len(r.text) < 2000:
        print(r.text)
    return json.loads(r.text)['data']

def get_info(videos: List[str]):
    payload = {'videos': videos, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.get(info_url, json=payload)
    return json.loads(r.text)['video_info']

def print_info(vid: str, data: dict):
    info = data['info']
    thumbnail = data['thumbnail']
    print('---- video: %s' % vid)
    print('-------- thumbnail size: %d' % len(thumbnail))
    print('-------- views: %d' % info['views'])
    print('-------- score: %.3f' % info['score'])
    print('-------- num: %d' % info['num'])
    print('-------- user: %s' % info['meta']['user_id'])
    print('-------- reso: %s' % ','.join(info['meta']['resolutions']))
    print('-------- dur: %.1fs' % info['meta']['duration'])
    print('-------- desc: %s' % info['meta']['description'])
    print('-------- date: %s' % info['meta']['date'])
    print('------------------------------')

def get_trending(start_dt: str, end_dt: str):
    payload = {'start_date': start_dt, 'end_date': end_dt, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.get(trending_url, json=payload)
    return json.loads(r.text)['videos']

def upload_rate(user_id: str, video_id: str, comment: str, score: float):
    payload = {'user': user_id, 'video': video_id, 'comment': comment, 'score': score, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.post(rate_url, json=payload)
    return json.loads(r.text)['video_id']

def get_info(videos: List[str]):
    payload = {'videos': videos, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.get(info_url, json=payload)
    return json.loads(r.text)['video_info']

def get_rate(user_id: str, video_id: str):
    payload = {'user': user_id, 'video': video_id, 'send_unix_ms': int(time.time() * 1000)}
    r = requests.get(get_rate_url, json=payload)
    return json.loads(r.text)

def print_info(vid: str, data: dict):
    info = data['info']
    thumbnail = data['thumbnail']
    print('---- video: %s' % vid)
    print('-------- views: %d' % info['views'])
    print('-------- score: %.3f' % info['score'])
    print('-------- num: %d' % info['num'])

def print_trending(vids):
    print('---- trending: ')
    for v in vids:
        print('-------- %s' % v)
    print('------------------------------')

def print_user_rate(user: str, vid: str, rate: dict):
    print('---- rate video: %s, user: %s' % (vid, user))
    print('-------- exist: %s' % str(rate['exist']))
    print('-------- score: %.1f' % rate['score'])
    print('-------- comment: %s' % rate['comment'])

def make_rate(user_id: str, video_id: str, score: float, comment: str):
    return {'user_id': user_id, 'video_id': video_id, 'score': score, 'comment': comment, 'send_unix_ms': int(time.time() * 1000)}

def make_get(user_id: str, video_id: str):
    return {'user_id': user_id, 'video_id': video_id, 'send_unix_ms': int(time.time() * 1000)}

def show_get_resp(user_id, video_id, respjson):
    respdata = json.loads(respjson)
    print('-- user_id: %s, video_id: %s' % (user_id, video_id))
    print('------ exist: %s' % respdata['exist'])
    print('------ score: %.3f' % respdata['score'])
    print('------ comment: %s' % respdata['comment'])

def show_rate_resp(respjson):
    respdata = json.loads(respjson)
    print('------ exist: %s' % respdata['exist'])
    print('------ ori_score: %.3f' % respdata['ori_score'])

def update_rate(user_id: str, video_id: str, score: float, comment: str):
    rate_req = make_rate(user_id=user_id, video_id=video_id, score=score, comment=comment)
    r = requests.post(rate_url, json=rate_req)

# Node: make_rate
def make_rate(user_id: str, video_id: str, score: float, comment: str):
    return {'user_id': user_id, 'video_id': video_id, 'score': score, 'comment': comment, 'send_unix_ms': int(time.time() * 1000)}

def make_get(user_id: str, video_id: str):
    return {'user_id': user_id, 'video_id': video_id, 'send_unix_ms': int(time.time() * 1000)}

def show_get_resp(user_id, video_id, respjson):
    respdata = json.loads(respjson)
    print('-- user_id: %s, video_id: %s' % (user_id, video_id))
    print('------ exist: %s' % respdata['exist'])
    print('------ score: %.3f' % respdata['score'])
    print('------ comment: %s' % respdata['comment'])

def show_rate_resp(respjson):
    respdata = json.loads(respjson)
    print('------ exist: %s' % respdata['exist'])
    print('------ ori_score: %.3f' % respdata['ori_score'])

def videoProcessor(req):
    t = int(time.time() * 1000)
    data_id = req['data_id']
    width = req['width']
    height = req['height']
    video_path = req['video_path']
    scaled_data_path = req['scaled_data_path']
    resp = {'succ': False, 'error': ''}
    try:
        ffmpeg.input(str(video_path)).filter('scale', width, height).output(str(scaled_data_path), preset='slow', crf=18).overwrite_output().run(capture_stdout=True, capture_stderr=True)
        resp['succ'] = True
    except ffmpeg.Error as e:
        out = e.stdout.decode()
        err = e.stderr.decode()
        resp['error'] = 'FFmpeg (data_id: %s) std_err: %s, std_out: %s' % (data_id, err, out)
    return resp

# Node: run
# Node: overwrite_output
# Node: output
# Node: input
@app.subscribe(pubsub_name=pubsubName, topic=topicName)
def scaleVideo(event) -> None:
    global promReq
    global servLat
    global workerPool
    global grpcOptions
    promReq.inc()
    data = json.loads(event.Data())
    video_id = data['video_id']
    data_id = data['data_id']
    width = data['width']
    height = data['height']
    send_unix_ms = float(data['send_unix_ms'])
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    store_lat = 0
    unique_id = getCtr()
    video_path = dataDir / ('%s-%d-%d' % (data_id, unique_id, width))
    scaled_data_id = pyutil.scaledVideoDataId(video_id, width)
    scaled_data_path = dataDir / ('%d-%s' % (unique_id, scaled_data_id))
    with DaprClient(max_grpc_message_length=MAX_PAYLOAD) as d:
        try:
            logging.debug('%s width=%d' % (data['data_id'], data['width']))
            video = d.get_state(store_name=videoStore, key=data_id).data
            cur_unix_ms = time.time() * 1000
            store_lat += cur_unix_ms - epoch
            epoch = cur_unix_ms
            if len(video) == 0:
                logging.error('Cannot find video data: %s in %s, or video is empty' % (data_id, videoStore))
                promReq.inc()
                storeLat.observe(store_lat)
                servLat.observe(serv_lat)
                e2eVideoScaleLat.observe(cur_unix_ms - send_unix_ms)
                return
            with open(str(video_path), 'wb+') as f:
                f.write(video)
        except Exception as e:
            logging.error('Failed to read %s from %s: %s' % (data_id, videoStore, str(e)))
            return
        work = {'data_id': data_id, 'width': width, 'video_path': video_path, 'scaled_data_path': scaled_data_path, 'height': height}
        fresult = workerPool.apply_async(videoProcessor, (work,))
        result = fresult.get()
        if not result['succ']:
            logging.error('FFmpeg error: %s' % result['error'])
        else:
            cur_unix_ms = time.time() * 1000
            serv_lat += cur_unix_ms - epoch
            epoch = cur_unix_ms
            logging.debug('video_scale serv dur_ms=%.1f' % serv_lat)
            with open(str(scaled_data_path), 'rb') as f:
                scaled_video = f.read()
                d.save_state(store_name=videoStore, key=scaled_data_id, value=scaled_video)
            cur_unix_ms = time.time() * 1000
            store_lat += cur_unix_ms - epoch
            epoch = cur_unix_ms
        if os.path.exists(str(video_path)):
            os.remove(str(video_path))
        if os.path.exists(str(scaled_data_path)):
            os.remove(str(scaled_data_path))
        serv_lat += time.time() * 1000 - epoch
        storeLat.observe(store_lat)
        servLat.observe(serv_lat)
        logging.debug('e2e lat = %.1fms' % (cur_unix_ms - send_unix_ms))
        e2eVideoScaleLat.observe(cur_unix_ms - send_unix_ms)

# Node: inc
# Node: Data
# Node: getCtr
# Node: scaledVideoDataId
# Node: debug
# Node: get_state
# Node: apply_async
# Node: save_state
# Node: exists
# Node: remove
# Node: subscribe
def scaledVideoId(video_id: str, width: int):
    if width == 640:
        return '480p-%s' % video_id
    elif width == 1280:
        return '720p-%s' % video_id
    elif width == 1920:
        return '1080p-%s' % video_id
    else:
        print('Invalid video width %d' % width)
        return None

def scale_video(video_id: str, width: int, height: int):
    with MyDaprClient(options=grpcOptions) as d:
        req_data = {'video_id': video_id, 'data_id': video_id, 'width': width, 'height': height, 'send_unix_ms': int(time.time() * 1000)}
        resp = d.publish_event(pubsub_name=pubsub_name, topic_name=scale_topic_name, data=json.dumps(req_data), data_content_type='application/json')
        print(resp)

# Node: MyDaprClient
# Node: publish_event
def scaledVideoId(video_id: str, width: int):
    if width == 640:
        return '480p-%s' % video_id
    elif width == 1280:
        return '720p-%s' % video_id
    elif width == 1920:
        return '1080p-%s' % video_id
    else:
        print('Invalid video width %d' % width)
        return None

def scale_video(video_id: str, width: int):
    with DaprClient() as d:
        req_data = {'video_id': video_id, 'data_id': video_id, 'width': width, 'send_unix_ms': int(time.time() * 1000), 'client_unix_ms': int(time.time() * 1000)}
        resp = d.publish_event(pubsub_name=pubsub_name, topic_name=scale_topic_name, data=json.dumps(req_data), data_content_type='application/json')
        print(resp)

def scaledVideoId(video_id: str, width: int):
    if width == 640:
        return '480p-%s' % video_id
    elif width == 1280:
        return '720p-%s' % video_id
    elif width == 1920:
        return '1080p-%s' % video_id
    else:
        print('Invalid video width %d' % width)
        return None

def scale_video(video_id: str, width: int):
    with MyDaprClient(options=grpcOptions) as d:
        req_data = {'video_id': video_id, 'data_id': video_id, 'width': width, 'send_unix_ms': int(time.time() * 1000), 'client_unix_ms': int(time.time() * 1000)}
        resp = d.publish_event(pubsub_name=pubsub_name, topic_name=scale_topic_name, data=json.dumps(req_data), data_content_type='application/json')
        print(resp)

def get_videos(video_ids):
    global grpcOptions
    with MyDaprClient(options=grpcOptions) as d:
        items = d.get_bulk_state(store_name=video_store, keys=video_ids).items
        for idx, i in enumerate(items):
            video_name = video_ids[idx]
            etag = i.etag
            logging.info('%s, len=%d, local_len=%d; size=%d, local_size=%d' % (video_ids[idx], len(i.data), len(local_data[video_name]), sys.getsizeof(video_data), sys.getsizeof(local_data[video_name])))

# Node: get_bulk_state
# Node: enumerate
# Node: info
# Node: getsizeof
@app.method(name='dummy')
def dummy(request: InvokeMethodRequest) -> InvokeMethodResponse:
    resp = {'texts': 'Hi!'}
    return InvokeMethodResponse(data=json.dumps(resp), content_type='application/json')

def make_upload(video_id: str, user_id: str, reso: List[str], dur: float, desc: str):
    return {'video_id': video_id, 'user_id': user_id, 'resolutions': reso, 'duration': dur, 'description': desc, 'date': make_date(), 'send_unix_ms': int(time.time() * 1000)}

# Node: make_date
def make_rate(video_id: str, change: bool, score: float, ori_score: float):
    return {'video_id': video_id, 'change': change, 'score': score, 'ori_score': ori_score, 'send_unix_ms': int(time.time() * 1000)}

def make_view(video_id: str):
    return {'video_id': video_id, 'send_unix_ms': int(time.time() * 1000)}

def make_info(video_ids: List[str]):
    return {'video_ids': video_ids, 'send_unix_ms': int(time.time() * 1000)}

def show_info(infojson: str):
    infodata = json.loads(infojson)
    info = infodata['info']
    for video_id in info:
        video = info[video_id]
        print('-- video_id:', video_id)
        print('------ user:', video['meta']['user_id'])
        print('------ reso:', video['meta']['resolutions'])
        print('------ dur:', video['meta']['duration'])
        print('------ desc:', video['meta']['description'])
        print('------ date:', video['meta']['date'])
        print('------ rate_num:', video['rating']['num'])
        print('------ rate_score:', video['rating']['score'])
        print('------ rate_score_sq:', video['rating']['score_sq'])
        print('------ views:', video['views'])

def update_view(video_id: str):
    view_req = make_view(video_id=video_id)
    r = requests.post(view_url, json=view_req)

# Node: make_view
def make_upload(video_id: str, user_id: str, reso: List[str], dur: float, desc: str):
    return {'video_id': video_id, 'user_id': user_id, 'resolutions': reso, 'duration': dur, 'description': desc, 'date': make_date(), 'send_unix_ms': int(time.time() * 1000)}

def make_rate(video_id: str, change: bool, score: float, ori_score: float):
    return {'video_id': video_id, 'change': change, 'score': score, 'ori_score': ori_score, 'send_unix_ms': int(time.time() * 1000)}

def make_view(video_id: str):
    return {'video_id': video_id, 'send_unix_ms': int(time.time() * 1000)}

def make_info(video_ids: List[str]):
    return {'video_ids': video_ids, 'send_unix_ms': int(time.time() * 1000)}

def show_info(infojson: str):
    infodata = json.loads(infojson)
    info = infodata['info']
    for video_id in info:
        video = info[video_id]
        print('-- video_id:', video_id)
        print('------ user:', video['meta']['user_id'])
        print('------ reso:', video['meta']['resolutions'])
        print('------ dur:', video['meta']['duration'])
        print('------ desc:', video['meta']['description'])
        print('------ date:', video['meta']['date'])
        print('------ rate_num:', video['rating']['num'])
        print('------ rate_score:', video['rating']['score'])
        print('------ rate_score_sq:', video['rating']['score_sq'])
        print('------ views:', video['views'])

def update_rate(video_id: str, score: float):
    rate_req = make_rate(video_id=video_id, change=False, score=score, ori_score=0.0)
    r = requests.post(rate_url, json=rate_req)

def make_upload(video_id: str, user_id: str, reso: List[str], dur: float, desc: str):
    return {'video_id': video_id, 'user_id': user_id, 'resolutions': reso, 'duration': dur, 'description': desc, 'date': make_date(), 'send_unix_ms': int(time.time() * 1000)}

def make_rate(video_id: str, change: bool, score: float, ori_score: float):
    return {'video_id': video_id, 'change': change, 'score': score, 'ori_score': ori_score, 'send_unix_ms': int(time.time() * 1000)}

def make_view(video_id: str):
    return {'video_id': video_id, 'send_unix_ms': int(time.time() * 1000)}

def make_info(video_ids: List[str]):
    return {'video_ids': video_ids, 'send_unix_ms': int(time.time() * 1000)}

def show_info(infojson: str):
    infodata = json.loads(infojson)
    info = infodata['info']
    for video_id in info:
        video = info[video_id]
        print('-- video_id:', video_id)
        print('------ user:', video['meta']['user_id'])
        print('------ reso:', video['meta']['resolutions'])
        print('------ dur:', video['meta']['duration'])
        print('------ desc:', video['meta']['description'])
        print('------ date:', video['meta']['date'])
        print('------ rate_num:', video['rating']['num'])
        print('------ rate_score:', video['rating']['score'])
        print('------ rate_score_sq:', video['rating']['score_sq'])
        print('------ views:', video['views'])

def make_date_upload(video_id: str, dt: str):
    return {'video_id': video_id, 'date': dt, 'send_unix_ms': int(time.time() * 1000)}

def make_dates_get(dts: List[str]):
    return {'dates': dts, 'send_unix_ms': int(time.time() * 1000)}

def show_dates_get_resp(respjson):
    respdata = json.loads(respjson)
    print(respdata)
    for dt in respdata['videos']:
        print('-- date: %s' % dt)
        print('------ videos: %s' % ', '.join(respdata['videos'][dt]))

def store_date(d: str, videos: List[str]):
    for v in videos:
        req = make_date_upload(v, d)
        r = requests.post(dates_upload_url, json=req)
        print(r.text)

# Node: make_date_upload
def get_dates(ds: List[str]):
    req = make_dates_get(ds)
    r = requests.get(dates_get_url, json=req)
    show_dates_get_resp(r.text)

# Node: make_dates_get
# Node: show_dates_get_resp
def make_info_upload(video_id: str, user_id: str, reso: List[str], dur: float, desc: str):
    return {'video_id': video_id, 'user_id': user_id, 'resolutions': reso, 'duration': dur, 'description': desc, 'date': make_date(), 'send_unix_ms': int(time.time() * 1000)}

def make_rate(video_id: str, change: bool, score: float, ori_score: float):
    return {'video_id': video_id, 'change': change, 'score': score, 'ori_score': ori_score, 'send_unix_ms': int(time.time() * 1000)}

def make_view(video_id: str):
    return {'video_id': video_id, 'send_unix_ms': int(time.time() * 1000)}

def make_trending(start_d: str, end_d: str):
    return {'start_date': start_d, 'end_date': end_d, 'send_unix_ms': int(time.time() * 1000)}

def make_upload(video_id: str, dt: str):
    return {'video_id': video_id, 'date': dt, 'send_unix_ms': int(time.time() * 1000)}

def make_get(dts: List[str]):
    return {'dates': dts, 'send_unix_ms': int(time.time() * 1000)}

def show_get_resp(respjson):
    respdata = json.loads(respjson)
    print(respdata)
    for dt in respdata['videos']:
        print('-- date: %s' % dt)
        print('------ videos: %s' % ', '.join(respdata['videos'][dt]))

def make_upload(video_id: str, dt: str):
    return {'video_id': video_id, 'date': dt, 'send_unix_ms': int(time.time() * 1000)}

def make_get(dts: List[str]):
    return {'dates': dts, 'send_unix_ms': int(time.time() * 1000)}

def show_get_resp(respjson):
    respdata = json.loads(respjson)
    print(respdata)
    for dt in respdata['videos']:
        print('-- date: %s' % dt)
        print('------ videos: %s' % ', '.join(respdata['videos'][dt]))

def upload(video_id: str, dt: str):
    upload_req = make_upload(dt=dt, video_id=video_id)
    r = requests.post(upload_url, json=upload_req)

# Node: make_upload
def videoProcessor(req):
    data_id = req['data_id']
    duration = req['duration']
    video_path = req['video_path']
    thumbnail_path = req['thumbnail_path']
    resp = {'succ': False, 'error': ''}
    ss = min(0.1, duration / 10)
    try:
        ffmpeg.input(str(video_path), ss=ss).output(str(thumbnail_path), vframes=1, format='image2', vcodec='mjpeg').overwrite_output().run(quiet=True)
        resp['succ'] = True
    except ffmpeg.Error as e:
        out = e.stdout.decode()
        err = e.stderr.decode()
        resp['error'] = 'FFmpeg (data_id: %s) std_err: %s, std_out: %s' % (data_id, err, out)
    return resp

# Node: min
@app.subscribe(pubsub_name=pubsubName, topic=topicName)
def videoThumbnail(event) -> None:
    global promReq
    global servLat
    global workerPool
    promReq.inc()
    data = json.loads(event.Data())
    video_id = data['video_id']
    data_id = data['data_id']
    duration = data['duration']
    send_unix_ms = float(data['send_unix_ms'])
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    store_lat = 0
    unique_id = getCtr()
    video_path = dataDir / ('%s-%d' % (data_id, unique_id))
    thumbnail_id = pyutil.thumbnailId(video_id)
    thumbnail_path = dataDir / ('%d-%s' % (unique_id, thumbnail_id))
    with DaprClient(max_grpc_message_length=MAX_PAYLOAD) as d:
        try:
            logging.debug('%s -> %s' % (data_id, thumbnail_id))
            logging.debug('%s -> %s' % (str(video_path), str(thumbnail_path)))
            video = d.get_state(store_name=videoStore, key=data_id).data
            cur_unix_ms = time.time() * 1000
            store_lat += cur_unix_ms - epoch
            epoch = cur_unix_ms
            if len(video) == 0:
                logging.error('Cannot find video: %s in %s, or video is empty' % (data_id, videoStore))
                promReq.inc()
                storeLat.observe(store_lat)
                servLat.observe(serv_lat)
                e2eVideoThumbnailLat.observe(cur_unix_ms - send_unix_ms)
                return
            with open(str(video_path), 'wb+') as f:
                f.write(video)
        except Exception as e:
            logging.error('Failed to read %s from %s: %s' % (data_id, videoStore, str(e)))
            return
        work = {'data_id': data_id, 'duration': duration, 'video_path': video_path, 'thumbnail_path': thumbnail_path}
        fresult = workerPool.apply_async(videoProcessor, (work,))
        result = fresult.get()
        if not result['succ']:
            logging.error('FFmpeg error: %s' % result['error'])
        else:
            cur_unix_ms = time.time() * 1000
            serv_lat += cur_unix_ms - epoch
            epoch = cur_unix_ms
            logging.debug('video_thumbnail serv dur_ms=%.1f' % serv_lat)
            with open(str(thumbnail_path), 'rb') as f:
                thumbnail = f.read()
                resp = d.save_state(store_name=thumbnailStore, key=thumbnail_id, value=thumbnail)
            cur_unix_ms = time.time() * 1000
            store_lat += cur_unix_ms - epoch
            epoch = cur_unix_ms
        if os.path.exists(str(video_path)):
            os.remove(str(video_path))
        if os.path.exists(str(thumbnail_path)):
            os.remove(str(thumbnail_path))
        serv_lat += time.time() * 1000 - epoch
        storeLat.observe(store_lat)
        servLat.observe(serv_lat)
        logging.debug('e2e lat = %.1fms' % (cur_unix_ms - send_unix_ms))
        e2eVideoThumbnailLat.observe(cur_unix_ms - send_unix_ms)

# Node: thumbnailId
def thumbnail_video(video_id: str):
    with MyDaprClient(options=grpcOptions) as d:
        req_data = {'video_id': video_id, 'data_id': video_id, 'duration': video_dur[video_id], 'send_unix_ms': int(time.time() * 1000), 'client_unix_ms': int(time.time() * 1000)}
        resp = d.publish_event(pubsub_name=pubsub_name, topic_name=thumbnail_topic_name, data=json.dumps(req_data), data_content_type='application/json')
        print(resp)

def thumbnail_video(video_id: str):
    with MyDaprClient(options=grpcOptions) as d:
        req_data = {'video_id': video_id, 'data_id': video_id, 'duration': video_dur[video_id], 'send_unix_ms': int(time.time() * 1000), 'client_unix_ms': int(time.time() * 1000)}
        resp = d.publish_event(pubsub_name=pubsub_name, topic_name=thumbnail_topic_name, data=json.dumps(req_data), data_content_type='application/json')
        print(resp)

def get_videos(video_ids):
    global grpcOptions
    with MyDaprClient(options=grpcOptions) as d:
        items = d.get_bulk_state(store_name=video_store, keys=video_ids).items
        for idx, i in enumerate(items):
            video_name = video_ids[idx]
            etag = i.etag
            logging.info('%s, len=%d, local_len=%d; size=%d, local_size=%d' % (video_ids[idx], len(i.data), len(local_data[video_name]), sys.getsizeof(video_data), sys.getsizeof(local_data[video_name])))

@app.method(name='dummy')
def dummy(request: InvokeMethodRequest) -> InvokeMethodResponse:
    resp = {'texts': 'Hi!'}
    return InvokeMethodResponse(data=json.dumps(resp), content_type='application/json')

def videoProcessor(req):
    t = int(time.time() * 1000)
    tempf = req['tempf']
    resp = {'succ': False, 'err': None, 'probe': None}
    try:
        resp['probe'] = ffmpeg.probe(str(tempf))
        resp['succ'] = True
    except ffmpeg.Error as e:
        resp['err'] = e
    return resp

# Node: probe
@app.method(name='upload')
def uploadVideo(request: InvokeMethodRequest) -> InvokeMethodResponse:
    global uploadReq
    global uploadLat
    global uploadStoreLat
    global e2eUploadLat
    global workerPool
    uploadReq.inc()
    ts = int(time.time() * 1000)
    dt = datetime.now()
    dt_str = ''
    data = json.loads(request.text())
    user_id = data['user']
    video_b64 = data['video_b64']
    desc = data['description']
    if 'date' in data and data['date'] != '':
        if checkDate(data['date']):
            dt_str = data['date']
        else:
            raise ValueError('Error: invalid date in user request: %s' % data['date'])
    else:
        dt_str = pyutil.dtToDate(dt)
    send_unix_ms = data['send_unix_ms']
    client_unix_ms = send_unix_ms
    if len(video_b64) == 0:
        raise ValueError('Empty video uploaded')
    tmp_video_id = pyutil.videoId(user_id, ts, None)
    tempf = dataDir / ('%d-%s' % (getCtr(), tmp_video_id))
    video_bytes = base64.b64decode(video_b64)
    with open(str(tempf), 'wb+') as f:
        f.write(video_bytes)
    work = {'tempf': tempf}
    fresult = workerPool.apply_async(videoProcessor, (work,))
    result = fresult.get()
    if not result['succ']:
        e = result['err']
        raise RuntimeError('ffprobe stdout: %s, stderr: %s' % (e.stdout, e.stderr))
    if os.path.exists(str(tempf)):
        os.remove(str(tempf))
    probe = result['probe']
    dur = float(probe['format']['duration'])
    format = pyutil.pickFormat(probe['format']['format_name'])
    video_id = pyutil.videoId(user_id, ts, format)
    width = None
    height = None
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if video_stream != None:
        width = video_stream['width']
        height = video_stream['height']
    res = pyutil.widthToResolution(width)
    native_data_id = pyutil.videoDataId(video_id, res)
    avail_reso = pyutil.availResolution(res)
    scale_widths = pyutil.scaleWidth(width)
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    with DaprClient(max_grpc_message_length=MAX_PAYLOAD) as d:
        d.save_state(store_name=videoStore, key=native_data_id, value=video_bytes, options=StateOptions(consistency=Consistency.strong, concurrency=Concurrency.last_write))
        uploadStoreLat.observe(time.time() * 1000 - epoch)
        epoch = time.time() * 1000
        for w in scale_widths:
            h = int(w / width * height)
            if h % 2 == 1:
                h += 1
            scale_req = {'video_id': video_id, 'data_id': native_data_id, 'width': w, 'height': h, 'send_unix_ms': int(time.time() * 1000), 'client_unix_ms': int(client_unix_ms)}
            resp = d.publish_event(pubsub_name=videoPubsub, topic_name=scaleTopic, data=json.dumps(scale_req), data_content_type='application/json')
            scaleReq.inc()
        if video_stream != None:
            thumbnail_req = {'video_id': video_id, 'data_id': native_data_id, 'duration': dur, 'send_unix_ms': int(time.time() * 1000), 'client_unix_ms': int(client_unix_ms)}
            resp = d.publish_event(pubsub_name=videoPubsub, topic_name=thumbnailTopic, data=json.dumps(thumbnail_req), data_content_type='application/json')
            thumbnailReq.inc()
        serv_lat += time.time() * 1000 - epoch
        meta_req = {'video_id': video_id, 'user_id': user_id, 'resolutions': avail_reso, 'duration': dur, 'date': dt_str, 'description': desc, 'send_unix_ms': int(time.time() * 1000)}
        resp = d.invoke_method('dapr-video-info', 'upload', data=json.dumps(meta_req))
        resp_data = json.loads(resp.text())
        epoch = time.time() * 1000
        serv_lat += epoch - resp_data['send_unix_ms']
        dates_req = {'date': dt_str, 'video_id': video_id, 'send_unix_ms': int(time.time() * 1000)}
        resp = d.invoke_method('dapr-dates', 'upload', data=json.dumps(dates_req))
        resp_data = json.loads(resp.text())
        epoch = time.time() * 1000
        serv_lat += epoch - resp_data['send_unix_ms']
        uploadLat.observe(serv_lat)
        e2eUploadLat.observe(epoch - client_unix_ms)
        resp = {'video_id': video_id}
        return InvokeMethodResponse(json.dumps(resp), 'application/json')

# Node: checkDate
# Node: ValueError
# Node: dtToDate
# Node: videoId
# Node: RuntimeError
# Node: pickFormat
# Node: next
# Node: widthToResolution
# Node: videoDataId
# Node: availResolution
# Node: scaleWidth
# Node: StateOptions
@app.method(name='info')
def getVideoInfo(request: InvokeMethodRequest) -> InvokeMethodResponse:
    global infoReq
    global infoLat
    global infoStoreLat
    global e2eInfoLat
    infoReq.inc()
    data = json.loads(request.text())
    video_ids = data['videos']
    send_unix_ms = data['send_unix_ms']
    client_unix_ms = send_unix_ms
    thumbnail_ids = []
    video_info = {}
    for vid in video_ids:
        thumbnail_ids.append(pyutil.thumbnailId(vid))
        video_info[vid] = {}
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    with DaprClient(max_grpc_message_length=MAX_PAYLOAD) as d:
        items = d.get_bulk_state(store_name=thumbnailStore, keys=thumbnail_ids).items
        infoStoreLat.observe(time.time() * 1000 - epoch)
        epoch = time.time() * 1000
        for it in items:
            k = it.key
            vid = pyutil.thumbnailToVideo(k)
            if vid not in video_info:
                raise ValueError('Extracted video id %s does not match given videos' % vid)
            elif isinstance(d, str):
                video_info[vid]['thumbnail'] = base64.b64encode(it.data.encode('ascii')).decode('ascii')
            else:
                video_info[vid]['thumbnail'] = base64.b64encode(it.data).decode('ascii')
        info_req = {'video_ids': video_ids, 'upstream': 'frontend', 'send_unix_ms': int(time.time() * 1000)}
        serv_lat += time.time() * 1000 - epoch
        resp = d.invoke_method('dapr-video-info', 'info', data=json.dumps(info_req))
        resp_data = json.loads(resp.text())
        for vid in video_info:
            if vid not in resp_data['info']:
                raise RuntimeError('missing info of video %s' % vid)
            else:
                video_info[vid]['info'] = {'score': resp_data['info'][vid]['rating']['score'], 'num': resp_data['info'][vid]['rating']['num'], 'views': resp_data['info'][vid]['views'], 'meta': resp_data['info'][vid]['meta']}
        epoch = time.time() * 1000
        serv_lat += epoch - resp_data['send_unix_ms']
        infoLat.observe(serv_lat)
        e2eInfoLat.observe(epoch - client_unix_ms)
        resp = {'video_info': video_info}
        return InvokeMethodResponse(json.dumps(resp), 'application/json')

# Node: thumbnailToVideo
# Node: b64encode
@app.method(name='video')
def getVideoData(request: InvokeMethodRequest) -> InvokeMethodResponse:
    global videoReq
    global videoLat
    global videoStoreLat
    global e2eVideoLat
    videoReq.inc()
    data = json.loads(request.text())
    video_id = data['video']
    res = data['resolution']
    data_id = pyutil.videoDataId(video_id=video_id, res=res)
    send_unix_ms = float(data['send_unix_ms'])
    client_unix_ms = send_unix_ms
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    with DaprClient(max_grpc_message_length=MAX_PAYLOAD) as d:
        view_req = {'video_id': video_id, 'send_unix_ms': int(epoch)}
        resp = d.invoke_method('dapr-video-info', 'view', data=json.dumps(view_req))
        resp_data = json.loads(resp.text())
        epoch = time.time() * 1000
        serv_lat += epoch - resp_data['send_unix_ms']
        state = d.get_state(store_name=videoStore, key=data_id)
        videoStoreLat.observe(time.time() * 1000 - epoch)
        epoch = time.time() * 1000
        data = state.data
        resp = {}
        if isinstance(data, str):
            resp['data'] = base64.b64encode(data.encode('ascii')).decode('ascii')
        else:
            resp['data'] = base64.b64encode(data).decode('ascii')
        final_epoch = time.time() * 1000
        serv_lat += final_epoch - epoch
        videoLat.observe(serv_lat)
        e2eVideoLat.observe(final_epoch - client_unix_ms)
        return InvokeMethodResponse(json.dumps(resp), 'application/json')

@app.method(name='rate')
def rateVideo(request: InvokeMethodRequest) -> InvokeMethodResponse:
    global rateReq
    global rateLat
    global e2eRateLat
    rateReq.inc()
    data = json.loads(request.text())
    video_id = data['video']
    user_id = data['user']
    comment = data['comment']
    score = data['score']
    send_unix_ms = data['send_unix_ms']
    client_unix_ms = send_unix_ms
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    with DaprClient() as d:
        ur_req = {'user_id': user_id, 'video_id': video_id, 'comment': comment, 'score': score, 'send_unix_ms': int(epoch)}
        resp = d.invoke_method('dapr-user-rating', 'rate', data=json.dumps(ur_req))
        resp_data = json.loads(resp.text())
        rate_exist = resp_data['exist']
        ori_score = resp_data['ori_score']
        epoch = time.time() * 1000
        serv_lat += epoch - resp_data['send_unix_ms']
        vr_req = {'video_id': video_id, 'change': rate_exist, 'score': score, 'ori_score': ori_score, 'send_unix_ms': int(time.time() * 1000)}
        resp = d.invoke_method('dapr-video-info', 'rate', data=json.dumps(vr_req))
        resp_data = json.loads(resp.text())
        epoch = time.time() * 1000
        serv_lat += epoch - resp_data['send_unix_ms']
        rateLat.observe(serv_lat)
        e2eRateLat.observe(epoch - client_unix_ms)
        resp = {'video_id': video_id}
        return InvokeMethodResponse(json.dumps(resp), 'application/json')

@app.method(name='get_rate')
def getVideoRating(request: InvokeMethodRequest) -> InvokeMethodResponse:
    global getRateReq
    global getRateLat
    global e2eGetRateLat
    getRateReq.inc()
    data = json.loads(request.text())
    video_id = data['video']
    user_id = data['user']
    send_unix_ms = float(data['send_unix_ms'])
    client_unix_ms = send_unix_ms
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    with DaprClient() as d:
        ur_req = {'user_id': user_id, 'video_id': video_id, 'send_unix_ms': int(epoch)}
        resp = d.invoke_method('dapr-user-rating', 'get', data=json.dumps(ur_req))
        resp_data = json.loads(resp.text())
        rate_exist = resp_data['exist']
        comment = resp_data['comment']
        score = float(resp_data['score'])
        epoch = time.time() * 1000
        serv_lat += epoch - resp_data['send_unix_ms']
        getRateLat.observe(serv_lat)
        e2eGetRateLat.observe(epoch - client_unix_ms)
        resp = {'exist': rate_exist, 'comment': comment, 'score': score}
        return InvokeMethodResponse(json.dumps(resp), 'application/json')

def thumbnail_video(video_id: str):
    with DaprClient() as d:
        req_data = {'video_id': video_id, 'duration': video_dur[video], 'send_unix_ms': int(time.time() * 1000), 'client_unix_ms': int(time.time() * 1000)}
        resp = d.publish_event(pubsub_name=pubsub_name, topic_name=thumbnail_topic_name, data=json.dumps(req_data), data_content_type='application/json')
        print(resp)

def get_videos(video_ids):
    with DaprClient() as d:
        items = d.get_bulk_state(store_name=video_store, keys=video_ids).items
        for idx, i in enumerate(items):
            video_name = video_ids[idx]
            etag = i.etag
            logging.info('%s, len=%d, local_len=%d; size=%d, local_size=%d' % (video_ids[idx], len(i.data), len(local_data[video_name]), sys.getsizeof(video_data), sys.getsizeof(local_data[video_name])))

def make_meta_req(video_id: str, req_id: str, priority: int):
    assert priority == 1 or priority == 2
    return {'video_id': video_id, 'req_id': req_id, 'send_unix_ms': int(time.time() * 1000), 'priority': priority}

def make_meta_req(video_id: str, req_id: str, priority: int):
    assert priority == 1 or priority == 2
    return {'video_id': video_id, 'req_id': req_id, 'send_unix_ms': int(time.time() * 1000), 'priority': priority}

def faceDetect(data):
    image_id = data['image_id']
    send_unix_ms = data['send_unix_ms']
    client_unix_ms = data['client_unix_ms']
    is_high_prio = data['priority'] == 1
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    read_store_lat = 0
    image = None
    with DaprClient(max_grpc_message_length=MAX_PAYLOAD) as d:
        max_trial = 3
        data_fetched = False
        trials = 0
        while True:
            try:
                ts_start = time.time() * 1000
                image_bytes = d.get_state(store_name=imageStore, key=image_id).data
                ts_end = time.time() * 1000
                read_store_lat += ts_end - ts_start
                if len(image_bytes) > 0:
                    check_chars = image_bytes[-2:]
                    if check_chars != b'\xff\xd9':
                        serv_lat += time.time() * 1000 - ts_end
                        raise ValueError('Incomplete image data')
                    else:
                        image_np = np.frombuffer(image_bytes, np.uint8)
                        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
                        serv_lat += time.time() * 1000 - ts_end
                        data_fetched = True
            except cv2.error as e:
                logging.error('Failed to read %s from %s: %s' % (image_id, imageStore, str(e)))
            except Exception as e:
                logging.error('Failed to read %s from %s: %s' % (image_id, imageStore, str(e)))
            trials += 1
            if data_fetched or trials >= max_trial:
                break
            else:
                time.sleep(0.01)
        if not data_fetched or image is None:
            logging.error('Key: %s is not available in %s' % (image_id, imageStore))
            return False
        epoch = time.time() * 1000
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)
            for x, y, w, h in faces:
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            image_bytes = cv2.imencode('.jpg', image)[1].tobytes()
        except cv2.error as e:
            logging.error('Failed detect face in image %s for cv2 error: %s' % (image_id, str(e)))
            return False
        except Exception as e:
            logging.error('Failed to detect face in image %s: %s' % (image_id, str(e)))
        imageStoreReadLat.observe(read_store_lat)
        cur_unix_ms = time.time() * 1000
        serv_lat += cur_unix_ms - epoch
        epoch = cur_unix_ms
        d.save_state(store_name=imageStore, key=image_id, value=image_bytes, options=StateOptions(consistency=Consistency.strong, concurrency=Concurrency.last_write))
        cur_unix_ms = time.time() * 1000
        img_store_lat = cur_unix_ms - epoch
        epoch = cur_unix_ms
        imageStoreUpdateLat.observe(img_store_lat)
        cur_unix_ms = time.time() * 1000
        serv_lat += cur_unix_ms - epoch
        if is_high_prio:
            highPrioLat.observe(serv_lat)
            e2eHighPrioLat.observe(cur_unix_ms - client_unix_ms)
        else:
            lowPrioLat.observe(serv_lat)
            e2eLowPrioLat.observe(cur_unix_ms - client_unix_ms)
        logging.debug('Processed req_id=%s, image_id=%s, priority=%d, serv=%d, read_store=%d, write_store=%d, e2e=%d' % (data['req_id'], image_id, data['priority'], serv_lat, read_store_lat, img_store_lat, cur_unix_ms - client_unix_ms))
        return True

# Node: frombuffer
# Node: imdecode
# Node: cvtColor
# Node: detectMultiScale
# Node: rectangle
# Node: tobytes
# Node: imencode
def faceDetectWorker(high_prio_queue: Queue, low_prio_queue: Queue, max_timeout: float=maxTimeout, idle_time: float=idleTime, interval: float=60):
    low_prio_ctr = 0
    low_prio_rps = 0
    stats_ts = time.time()
    ts_empty = True
    timeout = 0.05
    while True:
        high_prio_empty = False
        low_prio_empty = False
        while True:
            epoch = time.time()
            if epoch - stats_ts >= interval:
                rps = low_prio_ctr / (epoch - stats_ts)
                if ts_empty:
                    low_prio_rps = rps
                    ts_empty = False
                else:
                    low_prio_rps = rps * 0.4 + low_prio_rps * 0.6
                if rps > 0:
                    timeout = min(idle_time / low_prio_rps, max_timeout)
                else:
                    timeout = max_timeout
                logging.debug('low_prio_rps = %.3f, timeout set to %.3fs' % (low_prio_rps, timeout))
                low_prio_ctr = 0
                stats_ts = epoch
            try:
                req = high_prio_queue.get(block=True, timeout=timeout)
                faceDetect(data=req)
            except queue.Empty:
                high_prio_empty = True
                break
        try:
            req = low_prio_queue.get(block=False)
            faceDetect(data=req)
            low_prio_ctr += 1
        except queue.Empty:
            low_prio_empty = True
        if high_prio_empty and low_prio_empty:
            time.sleep(0.01)

# Node: faceDetect
@app.subscribe(pubsub_name=videoPipePubsub, topic=faceTopic)
def videoScene(event) -> None:
    global highPrioQueue
    global lowPrioQueue
    data = json.loads(event.Data())
    if data['priority'] == 1:
        highPriReqTotal.inc()
        highPrioQueue.put(data)
    elif data['priority'] == 2:
        lowPriReqTotal.inc()
        lowPrioQueue.put(data)

# Node: put
def extractScene(data, video_dir: Path, image_dir: Path):
    video_id = data['video_id']
    req_id = data['req_id']
    send_unix_ms = data['send_unix_ms']
    is_high_prio = data['priority'] == 1
    duration = data['meta']['duration']
    if is_high_prio:
        highPriDurTotal.inc(duration)
    else:
        lowPriDurTotal.inc(duration)
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    tmp_video_id = '%s-%s' % (req_id, video_id)
    tempf = video_dir / tmp_video_id
    with DaprClient(max_grpc_message_length=MAX_PAYLOAD) as d:
        try:
            video_b64 = d.get_state(store_name=videoStore, key=video_id).data
            cur_unix_ms = time.time() * 1000
            video_store_lat = cur_unix_ms - epoch
            videoStoreLat.observe(video_store_lat)
            epoch = cur_unix_ms
            video_bytes = base64.b64decode(video_b64)
            with open(str(tempf), 'wb+') as f:
                f.write(video_bytes)
        except Exception as e:
            logging.error('Failed to read %s from %s: %s' % (video_id, videoStore, str(e)))
            return False
        temp_img_dir = image_dir / tmp_video_id
        if not os.path.isdir(temp_img_dir):
            os.makedirs(temp_img_dir)
        try:
            rate = max(1 / sceneInterval, maxScenes / duration)
            ffmpeg.input(str(tempf)).output(str(temp_img_dir) + '/' + str(req_id) + '_%02d.jpg', r=rate, format='image2', vcodec='mjpeg').overwrite_output().run(capture_stdout=True, capture_stderr=True)
        except ffmpeg.Error as e:
            out = e.stdout.decode()
            err = e.stderr.decode()
            logging.error('FFmpeg (req_id: %s) std_err: %s, std_out: %s' % (req_id, err, out))
            if os.path.exists(str(tempf)):
                os.remove(str(tempf))
            return False
        if os.path.exists(str(tempf)):
            os.remove(str(tempf))
        state_items = []
        image_ids = []
        num_images = 0
        ignored_images = []
        max_img_id = ''
        for img in os.listdir(str(temp_img_dir)):
            this_img_id = img.split('_')[-1].replace('.jpg', '')
            if max_img_id == '' or int(this_img_id.lstrip('0')) > int(max_img_id.lstrip('0')):
                max_img_id = this_img_id
            num_images += 1
        if num_images > 2:
            ignored_images = [str(req_id) + '_01.jpg', str(req_id) + '_%s.jpg' % max_img_id]
            logging.debug('ignored images: %s' % ','.join(ignored_images))
        for img in os.listdir(str(temp_img_dir)):
            if img in ignored_images:
                logging.debug('images:%s ignored' % img)
                continue
            img_id = img.split('/')[-1]
            if os.path.isfile(str(temp_img_dir / img)):
                image_ids.append(img_id)
                with open(str(temp_img_dir / img), 'rb') as f:
                    img_bytes = f.read()
                    state_items.append(StateItem(key=img_id, value=img_bytes))
        cur_unix_ms = time.time() * 1000
        serv_lat += cur_unix_ms - epoch
        epoch = cur_unix_ms
        if len(state_items) > 0:
            d.save_bulk_state(store_name=imageStore, states=state_items)
        cur_unix_ms = time.time() * 1000
        img_store_lat = cur_unix_ms - epoch
        imageStoreLat.observe(img_store_lat)
        epoch = cur_unix_ms
        subprocess.run('rm -rf %s' % str(temp_img_dir), shell=True)
        if len(image_ids) > 0:
            for img_id in image_ids:
                req_data = copy.copy(data)
                req_data['send_unix_ms'] = int(time.time() * 1000)
                req_data['image_id'] = img_id
                resp = d.publish_event(pubsub_name=videoPipePubsub, topic_name=faceTopic, data=json.dumps(req_data), data_content_type='application/json')
        cur_unix_ms = time.time() * 1000
        serv_lat += cur_unix_ms - epoch
        if is_high_prio:
            highPrioLat.observe(serv_lat)
        else:
            lowPrioLat.observe(serv_lat)
        logging.debug('Processed req_id=%s, video_id=%s, images=%d, priority=%d, serv_lat=%d, video_store_lat=%d, img_store_lat=%d' % (req_id, video_id, len(image_ids), data['priority'], serv_lat, video_store_lat, img_store_lat))
        return True

# Node: isdir
# Node: makedirs
# Node: max
# Node: listdir
# Node: lstrip
# Node: isfile
# Node: StateItem
# Node: save_bulk_state
# Node: copy
def sceneWorker(worker_id: int, high_prio_queue: Queue, low_prio_queue: Queue, max_timeout: float=maxTimeout, idle_time: float=idleTime, interval: float=60):
    video_dir = Path('/tmp') / str(worker_id) / 'video'
    image_dir = Path('/tmp') / str(worker_id) / 'image'
    os.makedirs(str(video_dir), exist_ok=True)
    os.makedirs(str(image_dir), exist_ok=True)
    low_prio_ctr = 0
    low_prio_rps = 0
    stats_ts = time.time()
    ts_empty = True
    timeout = 0.05
    while True:
        high_prio_empty = False
        low_prio_empty = False
        while True:
            epoch = time.time()
            if epoch - stats_ts >= interval:
                rps = low_prio_ctr / (epoch - stats_ts)
                if ts_empty:
                    low_prio_rps = rps
                    ts_empty = False
                else:
                    low_prio_rps = rps * 0.4 + low_prio_rps * 0.6
                if rps > 0:
                    timeout = min(idle_time / low_prio_rps, max_timeout)
                else:
                    timeout = max_timeout
                logging.debug('low_prio_rps = %.3f, timeout set to %.3fs' % (low_prio_rps, timeout))
                low_prio_ctr = 0
                stats_ts = epoch
            try:
                req = high_prio_queue.get(block=True, timeout=timeout)
                extractScene(data=req, video_dir=video_dir, image_dir=image_dir)
            except queue.Empty:
                high_prio_empty = True
                break
        try:
            req = low_prio_queue.get(block=False)
            extractScene(data=req, video_dir=video_dir, image_dir=image_dir)
            low_prio_ctr += 1
        except queue.Empty:
            low_prio_empty = True
        if high_prio_empty and low_prio_empty:
            time.sleep(0.01)

# Node: Path
# Node: extractScene
@app.subscribe(pubsub_name=videoPipePubsub, topic=sceneTopic)
def videoScene(event) -> None:
    global highPrioQueue
    global lowPrioQueue
    data = json.loads(event.Data())
    if data['priority'] == 1:
        highPriReqTotal.inc()
        highPrioQueue.put(data)
    elif data['priority'] == 2:
        lowPriReqTotal.inc()
        lowPrioQueue.put(data)

def extractMeta(data, video_dir: Path):
    global MAX_PAYLOAD
    video_id = data['video_id']
    req_id = data['req_id']
    send_unix_ms = data['send_unix_ms']
    is_high_prio = data['priority'] == 1
    client_unix_ms = send_unix_ms
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    tempf = video_dir / video_id
    with DaprClient(max_grpc_message_length=MAX_PAYLOAD) as d:
        try:
            video_b64 = d.get_state(store_name=videoStore, key=video_id).data
            cur_unix_ms = time.time() * 1000
            store_lat = cur_unix_ms - epoch
            videoStoreLat.observe(store_lat)
            epoch = cur_unix_ms
            video_bytes = base64.b64decode(video_b64)
            with open(str(tempf), 'wb+') as f:
                f.write(video_bytes)
        except Exception as e:
            logging.error('Failed to read %s from %s: %s' % (video_id, videoStore, str(e)))
            return False
        probe = None
        try:
            probe = ffmpeg.probe(str(tempf))
        except ffmpeg.Error as e:
            logging.error('ffprobe stdout: %s, stderr: %s' % (e.stdout, e.stderr))
            return False
        if os.path.exists(str(tempf)):
            os.remove(str(tempf))
        duration = float(probe['format']['duration'])
        format = pyutil.pickFormat(probe['format']['format_name'])
        width = None
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream != None:
            width = video_stream['width']
        data['meta'] = {'duration': duration, 'format': format, 'width': width}
        data['send_unix_ms'] = int(time.time() * 1000)
        data['client_unix_ms'] = int(client_unix_ms)
        resp = d.publish_event(pubsub_name=videoPipePubsub, topic_name=sceneTopic, data=json.dumps(data), data_content_type='application/json')
        cur_unix_ms = time.time() * 1000
        serv_lat += cur_unix_ms - epoch
        if is_high_prio:
            highPrioLat.observe(serv_lat)
        else:
            lowPrioLat.observe(serv_lat)
        logging.debug('Processed req_id=%s, video_id=%s, priority=%d, serv_lat=%d, store_lat=%d' % (req_id, video_id, data['priority'], serv_lat, store_lat))
        return True

def metaWorker(worker_id: int, high_prio_queue: Queue, low_prio_queue: Queue, max_timeout: float=maxTimeout, idle_time: float=idleTime, interval: float=60):
    video_dir = Path('/tmp') / str(worker_id) / 'video'
    os.makedirs(str(video_dir), exist_ok=True)
    low_prio_ctr = 0
    low_prio_rps = 0
    stats_ts = time.time()
    ts_empty = True
    timeout = 0.05
    while True:
        high_prio_empty = False
        low_prio_empty = False
        while True:
            epoch = time.time()
            if epoch - stats_ts >= interval:
                rps = low_prio_ctr / (epoch - stats_ts)
                if ts_empty:
                    low_prio_rps = rps
                    ts_empty = False
                else:
                    low_prio_rps = rps * 0.4 + low_prio_rps * 0.6
                if rps > 0:
                    timeout = min(idle_time / low_prio_rps, max_timeout)
                else:
                    timeout = max_timeout
                logging.debug('low_prio_rps = %.3f, timeout set to %.3fs' % (low_prio_rps, timeout))
                low_prio_ctr = 0
                stats_ts = epoch
            try:
                req = high_prio_queue.get(block=True, timeout=timeout)
                extractMeta(data=req, video_dir=video_dir)
                low_prio_ctr += 1
            except queue.Empty:
                high_prio_empty = True
                break
        try:
            req = low_prio_queue.get(block=False)
            extractMeta(data=req, video_dir=video_dir)
        except queue.Empty:
            low_prio_empty = True
        if high_prio_empty and low_prio_empty:
            time.sleep(0.01)

# Node: extractMeta
@app.subscribe(pubsub_name=videoPipePubsub, topic=metaTopic)
def videoMeta(event) -> None:
    global highPrioQueue
    global lowPrioQueue
    data = json.loads(event.Data())
    if data['priority'] == 1:
        highPriReqTotal.inc()
        highPrioQueue.put(data)
    elif data['priority'] == 2:
        lowPriReqTotal.inc()
        lowPrioQueue.put(data)

@app.method(name='en_to_de')
def transEnToDe(request: InvokeMethodRequest) -> InvokeMethodResponse:
    global translator
    global promReq
    global promLat
    if 'application/json' not in request.content_type:
        logging.error('Invalid content type: %s' % request.content_type)
        return InvokeMethodResponse(data='Invalid content type: %s' % request.content_type, content_type='text/plain')
    promReq.inc()
    req = json.loads(request.text())
    de_text = translator(req['text'])
    send_unix_ms = float(req['send_unix_ms'])
    cur_unix_ms = time.time() * 1000
    resp = {'translation': de_text, 'send_unix_ms': int(cur_unix_ms)}
    logging.info('en: %s, de: %s, lat: %.3fms' % (req['text'], de_text, cur_unix_ms - send_unix_ms))
    promLat.observe(cur_unix_ms - send_unix_ms)
    return InvokeMethodResponse(data=json.dumps(resp), content_type='application/json')

# Node: translator
def transl(text):
    service_url = 'http://localhost:31999/v1.0/invoke/dapr-transl-en-to-de/method/en_to_de'
    payload = {'send_unix_ms': int(round(time.time() * 1000)), 'text': text}
    r = requests.post(service_url, json=payload)
    print(r.text)

def make_save_post(post_id: str, user_id: str, text: str, images: List[str]):
    cont = {'user_id': user_id, 'text': text, 'images': images}
    return {'send_unix_ms': int(time.time() * 1000), 'post_id': post_id, 'content': cont}

def make_meta(post_id: str, sent: Optional[str]=None, objects: Optional[dict]=None):
    payload = {'post_id': post_id}
    if sent != None:
        payload['sentiment'] = sent
    if objects != None:
        payload['objects'] = objects
    payload['send_unix_ms'] = int(time.time() * 1000)
    return payload

def make_read(post_ids: List[str]):
    return {'post_ids': post_ids, 'send_unix_ms': int(time.time() * 1000)}

def make_comment(post_id: str, user_id: str, comm_id: str, reply_to: str, text: str):
    comm = {'comment_id': comm_id, 'user_id': user_id, 'reply_to': reply_to, 'text': text}
    return {'post_id': post_id, 'comm': comm, 'send_unix_ms': int(time.time() * 1000)}

def make_upvote(post_id: str, user_id: str):
    return {'post_id': post_id, 'user_id': user_id, 'send_unix_ms': int(time.time() * 1000)}

def show_posts(postsjson: str):
    postsdata = json.loads(postsjson)
    posts = postsdata['posts']
    for post_id in posts:
        post = posts[post_id]
        print('-- post_id:', post_id)
        print('------ content:', post['content'])
        print('------ meta:', post['meta'])
        print('------ comments:', post['comments'])
        print('------ upvotes:', post['upvotes'])
    if not post['comments']['comments'] is None:
        print('#comments = ', len(post['comments']['comments']))

def make_save_post(post_id: str, user_id: str, text: str, images: List[str]):
    cont = {'user_id': user_id, 'text': text, 'images': images}
    return {'send_unix_ms': int(time.time() * 1000), 'post_id': post_id, 'content': cont}

def make_meta(post_id: str, sent: Optional[str]=None, objects: Optional[dict]=None):
    payload = {'post_id': post_id}
    if sent != None:
        payload['sentiment'] = sent
    if objects != None:
        payload['objects'] = objects
    payload['send_unix_ms'] = int(time.time() * 1000)
    return payload

def make_read(post_ids: List[str]):
    return {'post_ids': post_ids, 'send_unix_ms': int(time.time() * 1000)}

def make_comment(post_id: str, user_id: str, comm_id: str, reply_to: str, text: str):
    comm = {'comment_id': comm_id, 'user_id': user_id, 'reply_to': reply_to, 'text': text}
    return {'post_id': post_id, 'comm': comm, 'send_unix_ms': int(time.time() * 1000)}

def make_upvote(post_id: str, user_id: str):
    return {'post_id': post_id, 'user_id': user_id, 'send_unix_ms': int(time.time() * 1000)}

def show_posts(postsjson: str):
    postsdata = json.loads(postsjson)
    posts = postsdata['posts']
    for post_id in posts:
        post = posts[post_id]
        print('-- post_id:', post_id)
        print('------ content:', post['content'])
        print('------ meta:', post['meta'])
        print('------ comments:', post['comments'])
        print('------ upvotes:', post['upvotes'])

def make_save_post(post_id: str, user_id: str, text: str, images: List[str]):
    cont = {'user_id': user_id, 'text': text, 'images': images}
    return {'send_unix_ms': int(time.time() * 1000), 'post_id': post_id, 'content': cont}

def make_meta(post_id: str, sent: Optional[str]=None, objects: Optional[dict]=None):
    payload = {'post_id': post_id}
    if sent != None:
        payload['sentiment'] = sent
    if objects != None:
        payload['objects'] = objects
    payload['send_unix_ms'] = int(time.time() * 1000)
    return payload

def make_read(post_ids: List[str]):
    return {'post_ids': post_ids, 'send_unix_ms': int(time.time() * 1000)}

def make_comment(post_id: str, user_id: str, comm_id: str, reply_to: str, text: str):
    comm = {'comment_id': comm_id, 'user_id': user_id, 'reply_to': reply_to, 'text': text}
    return {'post_id': post_id, 'comm': comm, 'send_unix_ms': int(time.time() * 1000)}

def make_upvote(post_id: str, user_id: str):
    return {'post_id': post_id, 'user_id': user_id, 'send_unix_ms': int(time.time() * 1000)}

def show_posts(postsjson: str):
    postsdata = json.loads(postsjson)
    posts = postsdata['posts']
    for post_id in posts:
        post = posts[post_id]
        print('-- post_id:', post_id)
        print('------ content:', post['content'])
        print('------ meta:', post['meta'])
        print('------ comments:', post['comments'])
        print('------ upvotes:', post['upvotes'])

def update_sent(post_id: str, sent: str):
    meta_req = make_meta(post_id=post_id, sent=sent)
    r = requests.post(meta_url, json=meta_req)

# Node: make_meta
def update_objects(post_id: str, objects: dict):
    meta_req = make_meta(post_id=post_id, objects=objects)
    r = requests.post(meta_url, json=meta_req)

def make_save_post(post_id: str, user_id: str, text: str, images: List[str]):
    cont = {'user_id': user_id, 'text': text, 'images': images}
    return {'send_unix_ms': int(time.time() * 1000), 'post_id': post_id, 'content': cont}

def make_meta(post_id: str, sent: Optional[str]=None, objects: Optional[dict]=None):
    payload = {'post_id': post_id}
    if sent != None:
        payload['sentiment'] = sent
    if objects != None:
        payload['objects'] = objects
    payload['send_unix_ms'] = int(time.time() * 1000)
    return payload

def make_read(post_ids: List[str]):
    return {'post_ids': post_ids, 'send_unix_ms': int(time.time() * 1000)}

def make_comment(post_id: str, user_id: str, comm_id: str, reply_to: str, text: str):
    comm = {'comment_id': comm_id, 'user_id': user_id, 'reply_to': reply_to, 'text': text}
    return {'post_id': post_id, 'comm': comm, 'send_unix_ms': int(time.time() * 1000)}

def make_upvote(post_id: str, user_id: str):
    return {'post_id': post_id, 'user_id': user_id, 'send_unix_ms': int(time.time() * 1000)}

def show_posts(postsjson: str):
    postsdata = json.loads(postsjson)
    posts = postsdata['posts']
    for post_id in posts:
        post = posts[post_id]
        print('-- post_id:', post_id)
        print('------ content:', post['content'])
        print('------ meta:', post['meta'])
        print('------ comments:', post['comments'])
        print('------ upvotes:', post['upvotes'])

def genPostId(user):
    return '%s*%d' % (user, int(time.time() * 1000))

def genPostId(user):
    return '%s*%d' % (user, int(time.time() * 1000))

def genPostId(user):
    return '%s*%d' % (user, int(time.time() * 1000))

def genPostId(user):
    return '%s*%d' % (user, int(time.time() * 1000))

def updater(user, posts):
    for i in range(0, posts):
        payload = {'user_id': user, 'post_id': genPostId(user), 'add': True, 'send_unix_ms': int(time.time() * 1000)}
        r = requests.post(update_tl_url, json=payload)

# Node: genPostId
def newMetaReq(post_id: str, objects: dict):
    jsobj = {}
    for o in objects:
        jsobj[o] = json.dumps(objects[o])
    return {'post_id': post_id, 'sentiment': '', 'objects': jsobj, 'send_unix_ms': int(time.time() * 1000)}

@app.subscribe(pubsub_name=pubsubName, topic=topicName)
def objectDetect(event) -> None:
    global objectDetector
    global promReq
    global servLat
    data = json.loads(event.Data())
    post_id = data['post_id']
    send_unix_ms = float(data['send_unix_ms'])
    client_unix_ms = float(data['client_unix_ms'])
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    redeliver = False
    if serv_lat >= pyutil.redeliverInterval():
        redeliver = True
    if len(data['images']) > 0:
        promReq.inc()
        pil_images = []
        with DaprClient() as d:
            try:
                logging.info(data['images'])
                items = d.get_bulk_state(store_name=imageStore, keys=data['images']).items
                cur_unix_ms = time.time() * 1000
                storeLat.observe(cur_unix_ms - epoch)
                epoch = cur_unix_ms
                for i in items:
                    img = Image.open(io.BytesIO(i.data))
                    pil_images.append(img)
            except Exception as e:
                logging.error('Failed to read from %s: %s' % (imageStore, str(e)))
                return
            pred = objectDetector(pil_images)
            if not redeliver:
                cur_unix_ms = time.time() * 1000
                serv_lat += cur_unix_ms - epoch
                servLat.observe(serv_lat)
                e2eObjDetLat.observe(cur_unix_ms - client_unix_ms)
            objects = {}
            for img_id, p in zip(data['images'], pred):
                logging.info('%s: %s' % (img_id, str(p)))
                '\n                each prediction should be a list of dicts,\n                and each dict has the following keys: \n                    label (str) — The class label identified by the model.\n                    score (float) — The score attributed by the model for that label.\n                    box (List[Dict[str, int]]) — The bounding box of detected object in image original size.\n                '
                objects[img_id] = p
            meta_req = newMetaReq(post_id, objects)
            try:
                resp = d.invoke_method('dapr-post', 'meta', data=json.dumps(meta_req))
                logging.info(resp.headers)
            except Exception as e:
                logging.error('Failed to invoke dapr-post:meta %s' % str(e))
    else:
        logging.warning('Empty event with no images')

# Node: redeliverInterval
# Node: objectDetector
# Node: zip
# Node: newMetaReq
# Node: warning
def get_images(image_ids):
    with DaprClient() as d:
        items = d.get_bulk_state(store_name=img_store, keys=image_ids).items
        pil_images = []
        for idx, i in enumerate(items):
            img_name = image_ids[idx]
            etag = i.etag
            logging.info('%s, len=%d, local_len=%d; size=%d, local_size=%d' % (image_ids[idx], len(i.data), len(local_data[img_name]), sys.getsizeof(img_data), sys.getsizeof(local_data[img_name])))

def object_detect(post_id: str, images: List[str]):
    with DaprClient() as d:
        ts = int(time.time() * 1000)
        req_data = {'post_id': post_id, 'pubsub_name': pubsub_name, 'topic_name': topic_name, 'images': images, 'send_unix_ms': ts, 'client_unix_ms': ts}
        resp = d.publish_event(pubsub_name=pubsub_name, topic_name=topic_name, data=json.dumps(req_data), data_content_type='application/json')
        print(resp)

@app.method(name='dummy')
def dummy(request: InvokeMethodRequest) -> InvokeMethodResponse:
    resp = {'texts': 'Hi!'}
    return InvokeMethodResponse(data=json.dumps(resp), content_type='application/json')

def updater(id, key, updates):
    for i in range(0, updates):
        follow_id = 'sickle-%d-%d' % (id, i)
        payload = {'send_unix_ms': int(time.time() * 1000), 'user_id': follow_id, 'follow_id': key}
        r = requests.post(follow_url, json=payload)
        print(r.text)

def newMetaReq(post_id: str, sentiment: list):
    jssent = json.dumps(sentiment)
    return {'post_id': post_id, 'sentiment': jssent, 'objects': None, 'send_unix_ms': int(time.time() * 1000)}

@app.subscribe(pubsub_name=pubsubName, topic=topicName)
def sentimentAnalysis(event) -> None:
    global sentiment
    global promReq
    global promLat
    data = json.loads(event.Data())
    promReq.inc()
    post_id = data['post_id']
    send_unix_ms = float(data['send_unix_ms'])
    image_included = bool(data['image_included'])
    client_unix_ms = float(data['client_unix_ms'])
    pred = sentiment(data['text'])
    cur_unix_ms = time.time() * 1000
    redeliver = False
    if cur_unix_ms - send_unix_ms >= pyutil.redeliverInterval():
        redeliver = True
    if not redeliver:
        if image_included:
            promLatImg.observe(cur_unix_ms - send_unix_ms)
            e2eSentiImgLat.observe(cur_unix_ms - client_unix_ms)
        else:
            promLat.observe(cur_unix_ms - send_unix_ms)
            e2eSentiLat.observe(cur_unix_ms - client_unix_ms)
    logging.info('recv_unix_ms: %.1f, compl_unix_ms: %.1f, dur_ms=%.1f, sentiment=%s' % (send_unix_ms, cur_unix_ms, cur_unix_ms - send_unix_ms, str(pred)))
    meta_req = newMetaReq(post_id, pred)
    with DaprClient() as d:
        try:
            resp = d.invoke_method('dapr-post', 'meta', data=json.dumps(meta_req))
            logging.info(resp.headers)
        except Exception as e:
            logging.error('Failed to invoke dapr-post:meta %s' % str(e))

# Node: bool
# Node: sentiment
def sentiment(post_id, text):
    global dest_pubsub
    global dest_topic
    service_url = 'http://localhost:31998/v1.0/publish/sentiment-pubsub/sentiment'
    ts = int(round(time.time() * 1000))
    payload = {'post_id': post_id, 'text': text, 'send_unix_ms': ts, 'client_unix_ms': ts}
    r = requests.post(service_url, json=payload)
    print(r.text)

def newMetaReq(post_id: str, objects: dict):
    jsobj = {}
    for o in objects:
        jsobj[o] = json.dumps(objects[o])
    return {'post_id': post_id, 'sentiment': '', 'objects': jsobj, 'send_unix_ms': int(time.time() * 1000)}

@app.subscribe(pubsub_name=pubsubName, topic=topicName)
def objectDetect(event) -> None:
    global objectDetector
    global promReq
    global servLat
    data = json.loads(event.Data())
    post_id = data['post_id']
    send_unix_ms = float(data['send_unix_ms'])
    client_unix_ms = float(data['client_unix_ms'])
    epoch = time.time() * 1000
    serv_lat = epoch - send_unix_ms
    redeliver = False
    if serv_lat >= pyutil.redeliverInterval():
        redeliver = True
    if len(data['images']) > 0:
        promReq.inc()
        pil_images = []
        with DaprClient() as d:
            try:
                logging.info(data['images'])
                items = d.get_bulk_state(store_name=imageStore, keys=data['images']).items
                cur_unix_ms = time.time() * 1000
                storeLat.observe(cur_unix_ms - epoch)
                epoch = cur_unix_ms
                for i in items:
                    img = Image.open(io.BytesIO(i.data))
                    pil_images.append(img)
            except Exception as e:
                logging.error('Failed to read from %s: %s' % (imageStore, str(e)))
                return
            pred = objectDetector(pil_images)
            if not redeliver:
                cur_unix_ms = time.time() * 1000
                serv_lat += cur_unix_ms - epoch
                servLat.observe(serv_lat)
                e2eObjDetLat.observe(cur_unix_ms - client_unix_ms)
            objects = {}
            for img_id, p in zip(data['images'], pred):
                logging.info('%s: %s' % (img_id, str(p)))
                '\n                each prediction should be a list of dicts,\n                and each dict has the following keys: \n                    label (str) — The class label identified by the model.\n                    score (float) — The score attributed by the model for that label.\n                    box (List[Dict[str, int]]) — The bounding box of detected object in image original size.\n                '
                objects[img_id] = p
            meta_req = newMetaReq(post_id, objects)
            try:
                resp = d.invoke_method('dapr-post', 'meta', data=json.dumps(meta_req))
                logging.info(resp.headers)
            except Exception as e:
                logging.error('Failed to invoke dapr-post:meta %s' % str(e))
    else:
        logging.warning('Empty event with no images')

def get_images(image_ids):
    with DaprClient() as d:
        items = d.get_bulk_state(store_name=img_store, keys=image_ids).items
        pil_images = []
        for idx, i in enumerate(items):
            img_name = image_ids[idx]
            etag = i.etag
            logging.info('%s, len=%d, local_len=%d; size=%d, local_size=%d' % (image_ids[idx], len(i.data), len(local_data[img_name]), sys.getsizeof(img_data), sys.getsizeof(local_data[img_name])))

def object_detect(post_id: str, images: List[str]):
    with DaprClient() as d:
        ts = int(time.time() * 1000)
        req_data = {'post_id': post_id, 'pubsub_name': pubsub_name, 'topic_name': topic_name, 'images': images, 'send_unix_ms': ts, 'client_unix_ms': ts}
        resp = d.publish_event(pubsub_name=pubsub_name, topic_name=topic_name, data=json.dumps(req_data), data_content_type='application/json')
        print(resp)

@app.method(name='dummy')
def dummy(request: InvokeMethodRequest) -> InvokeMethodResponse:
    resp = {'texts': 'Hi!'}
    return InvokeMethodResponse(data=json.dumps(resp), content_type='application/json')

