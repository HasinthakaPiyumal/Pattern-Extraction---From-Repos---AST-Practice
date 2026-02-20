# Cluster 3

# Node: UploadText
# Node: UploadMovieReview
# Node: ReadMovieReviews
# Node: WritePlot
# Node: ReadPlot
# Node: WriteMovieInfo
# Node: ReadMovieInfo
# Node: RegisterUserWithId
# Node: UploadUserWithUserId
# Node: UploadUserWithUsername
# Node: UploadMovieId
# Node: RegisterMovieId
# Node: StoreReview
# Node: ReadReviews
# Node: ReadPage
# Node: WriteCastInfo
# Node: ReadCastInfo
# Node: UploadUserReview
# Node: ReadUserReviews
# Node: UploadRating
# Node: UploadUniqueId
# Node: UploadUserId
# Node: str
def wrtie_movie_info():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10012)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = MovieInfoService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        movie_id = 'movie_id_' + str(i)
        title = 'movie_' + str(i)
        cast_id = random.randint(0, 96)
        casts = []
        for j in range(3):
            cast = Cast(cast_id=j, character='character_' + str(j), cast_info_id=cast_id + j)
            casts.append(cast)
        plot_id = i
        thumbnail_ids = []
        photo_ids = []
        video_ids = []
        for j in range(3):
            thumbnail_ids.append(random.getrandbits(63))
            photo_ids.append(random.getrandbits(63))
            video_ids.append(random.getrandbits(63))
        avg_rating = random.randint(0, 10)
        num_rating = random.randint(1, 100)
        client.WriteMovieInfo(req_id, movie_id, title, casts, plot_id, thumbnail_ids, photo_ids, video_ids, avg_rating, num_rating, {})
    transport.close()

# Node: TSocket
# Node: TFramedTransport
# Node: TBinaryProtocol
# Node: Client
# Node: open
# Node: getrandbits
# Node: randint
# Node: close
def read_movie_info():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10012)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = MovieInfoService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        movie_id = 'movie_id_' + str(random.randint(0, 99))
        print(client.ReadMovieInfo(req_id, movie_id, {}))
    transport.close()

def write_movie_review():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = MovieReviewService.Client(protocol)
    transport.open()
    for i in range(101, 200):
        req_id = random.getrandbits(63)
        timestamp = int(time() * 1000)
        movie_num = random.randint(0, 5)
        movie_id = 'movie_id_' + str(movie_num)
        client.UploadMovieReview(req_id, movie_id, i, timestamp, {})
    transport.close()

def read_movie_reviews():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = MovieReviewService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        movie_num = random.randint(0, 5)
        movie_id = 'movie_id_' + str(movie_num)
        start = random.randint(0, 10)
        stop = start + random.randint(1, 10)
        print(client.ReadMovieReviews(req_id, movie_id, start, stop, {}))
    transport.close()

def upload_rating():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = RatingService.Client(protocol)
    transport.open()
    for i in range(1, 100):
        req_id = random.getrandbits(63)
        movie_id = 'movie_id_' + str(random.randint(0, 4))
        rating = random.randint(0, 10)
        client.UploadRating(req_id, movie_id, rating, {})
    transport.close()

def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UserService.Client(protocol)
    transport.open()
    req_id = uuid.uuid4().int & 1 << 32
    username = 'username' + str(1)
    password = 'password' + str(1)
    try:
        client.UploadUserWithUsername(req_id, username, {'': ''})
    except ttypes.ServiceException as se:
        print('%s' % se.message)
    transport.close()

# Node: uuid4
def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = TextService.Client(protocol)
    transport.open()
    for i in range(1, 2):
        req_id = random.getrandbits(64) - 2 ** 63
        text = ''.join(random.choices(string.ascii_lowercase + string.digits, k=128))
        client.UploadText(req_id, text)
    transport.close()

# Node: choices
def compose_review():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = ComposeReviewService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        unique_id = random.getrandbits(63)
        text = ''.join(random.choices(string.ascii_lowercase + string.digits, k=128))
        user_id = random.randint(0, 5)
        movie_id = 'movie_id_' + str(random.randint(0, 5))
        rating = random.randint(0, 10)
        client.UploadUniqueId(req_id, unique_id, {})
        client.UploadUserId(req_id, user_id, {})
        client.UploadRating(req_id, rating, {})
        client.UploadText(req_id, text, {})
        client.UploadMovieId(req_id, movie_id, {})
    transport.close()

def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UniqueIdService.Client(protocol)
    transport.open()
    for i in range(1, 100):
        req_id = random.getrandbits(64) - 2 ** 63
        client.UploadUniqueId(req_id)
    transport.close()

def register_movies():
    movie_id_socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10002)
    movie_id_transport = TTransport.TFramedTransport(movie_id_socket)
    movie_id_protocol = TBinaryProtocol.TBinaryProtocol(movie_id_transport)
    movie_id_client = MovieIdService.Client(movie_id_protocol)
    movie_id_transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        title = 'movie_title_' + str(i)
        movie_id = 'movie_id_' + str(i)
        movie_id_client.RegisterMovieId(req_id, title, movie_id, {})
    movie_id_transport.close()

def register_users():
    user_socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10005)
    user_transport = TTransport.TFramedTransport(user_socket)
    user_protocol = TBinaryProtocol.TBinaryProtocol(user_transport)
    user_client = UserService.Client(user_protocol)
    user_transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        first_name = 'first_' + str(i)
        last_name = 'last_' + str(i)
        username = 'username_' + str(i)
        password = 'password_' + str(i)
        user_client.RegisterUserWithId(req_id, first_name, last_name, username, password, i, {})
    user_transport.close()

def worker():
    text_socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10003)
    text_transport = TTransport.TFramedTransport(text_socket)
    text_protocol = TBinaryProtocol.TBinaryProtocol(text_transport)
    text_client = TextService.Client(text_protocol)
    unique_id_socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10001)
    unique_id_transport = TTransport.TFramedTransport(unique_id_socket)
    unique_id_protocol = TBinaryProtocol.TBinaryProtocol(unique_id_transport)
    unique_id_client = UniqueIdService.Client(unique_id_protocol)
    movie_id_socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10002)
    movie_id_transport = TTransport.TFramedTransport(movie_id_socket)
    movie_id_protocol = TBinaryProtocol.TBinaryProtocol(movie_id_transport)
    movie_id_client = MovieIdService.Client(movie_id_protocol)
    user_socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10005)
    user_transport = TTransport.TFramedTransport(user_socket)
    user_protocol = TBinaryProtocol.TBinaryProtocol(user_transport)
    user_client = UserService.Client(user_protocol)
    text_transport.open()
    unique_id_transport.open()
    movie_id_transport.open()
    user_transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        user_id = random.randint(0, 99)
        movie_num = random.randint(0, 99)
        rating = random.randint(0, 10)
        text = ''.join(random.choices(string.ascii_lowercase + string.digits, k=256))
        title = 'movie_title_' + str(movie_num)
        unique_id_client.UploadUniqueId(req_id, {})
        user_client.UploadUserWithUserId(req_id, user_id, {})
        text_client.UploadText(req_id, text, {})
        movie_id_client.UploadMovieId(req_id, title, rating, {})
    text_transport.close()
    unique_id_transport.close()
    movie_id_transport.close()
    user_transport.close()

def wrtie_cast_info():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10010)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = CastInfoService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        cast_id = i
        name = 'name_' + str(i)
        gender = random.randint(0, 1)
        intro = 'intro_' + str(i)
        client.WriteCastInfo(req_id, cast_id, name, gender, intro, {})
    transport.close()

def read_cast_info():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10010)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = CastInfoService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        cast_ids = set()
        for j in range(10):
            cast_ids.add(random.randint(0, 99))
        print(client.ReadCastInfo(req_id, cast_ids, {}))
    transport.close()

# Node: set
# Node: add
def register_movie():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = MovieIdService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        movie_index = i
        title = 'movie_' + str(movie_index)
        movie_id = 'movie_id_' + str(movie_index)
        client.RegisterMovieId(req_id, title, movie_id, {})
    transport.close()

def upload_movie_id():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = MovieIdService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        movie_index = random.randint(0, 4)
        title = 'movie_' + str(movie_index)
        rating = random.randint(0, 10)
        client.UploadMovieId(req_id, title, rating, {})
    transport.close()

def write_user_review():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UserReviewService.Client(protocol)
    transport.open()
    for i in range(0, 100):
        req_id = random.getrandbits(63)
        timestamp = int(time() * 1000)
        user_id = random.randint(0, 5)
        client.UploadUserReview(req_id, user_id, i, timestamp, {})
    transport.close()

def read_user_reviews():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UserReviewService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        user_id = random.randint(0, 5)
        start = random.randint(0, 10)
        stop = start + random.randint(1, 10)
        print(client.ReadUserReviews(req_id, user_id, start, stop, {}))
    transport.close()

def read_page():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = PageService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        movie_id = 'movie_id_' + str(i)
        print(client.ReadPage(req_id, movie_id, 0, 10, {}))
    transport.close()

def wrtie_plot():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10011)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = PlotService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        plot_id = i
        plot = 'plot: ' + str(i)
        client.WritePlot(req_id, plot_id, plot, {})
    transport.close()

def read_plot():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10011)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = PlotService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        plot_id = random.randint(0, 99)
        print(client.ReadPlot(req_id, i, {}))
    transport.close()

def write_review():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10007)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = ReviewStorageService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.getrandbits(63)
        timestamp = int(time())
        review_id = i
        movie_num = random.randint(0, 99)
        user_id = random.randint(0, 99)
        rating = random.randint(0, 10)
        text = ''.join(random.choices(string.ascii_lowercase + string.digits, k=256))
        movie_id = 'movie_id_' + str(movie_num)
        review = Review()
        review.req_id = req_id
        review.user_id = user_id
        review.review_id = review_id
        review.text = text
        review.movie_id = movie_id
        review.rating = rating
        review.timestamp = timestamp
        client.StoreReview(req_id, review, {})
    transport.close()

def read_reviews():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10007)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = ReviewStorageService.Client(protocol)
    transport.open()
    for i in range(100):
        req_id = random.randint(0, 99)
        review_ids = set()
        for j in range(10):
            review_ids.add(random.randint(0, 99))
        print(client.ReadReviews(req_id, review_ids, {}))
    transport.close()

def worker(api_key, page_start, page_stop):
    movies_url = 'https://api.themoviedb.org/3/movie/popular'
    language = 'en-US'
    movies = []
    for page in range(page_start, page_stop):
        parameter = {'language': language, 'page': page, 'api_key': api_key}
        r = requests.request('GET', movies_url, params=parameter)
        if r.status_code != 200:
            print('Failed to get popular_movie', 'status_code:', r.status_code, 'message:', r.text)
        movies += r.json()['results']
        for i in range(len(movies)):
            movie_id = movies[i]['id']
            casts_url = 'https://api.themoviedb.org/3/movie/' + str(movie_id) + '/credits'
            r = requests.request('GET', casts_url, params={'api_key': api_key})
            if r.status_code != 200:
                print('Failed to get popular_movie', 'status_code:', r.status_code, 'message:', r.text)
            movies[i]['cast'] = r.json()['cast']
            if len(movies[i]['cast']) > 10:
                movies[i]['cast'] = movies[i]['cast'][:10]
            time.sleep(0.25)
        print('page', page, 'success')
    return movies

# Node: request
# Node: json
def main():
    parser = optparse.OptionParser()
    parser.add_option('--start', type='int', dest='start')
    parser.add_option('--stop', type='int', dest='stop')
    parser.add_option('--key', type='string', dest='api_key')
    options, args = parser.parse_args()
    movies = worker(options.api_key, options.start, options.stop + 1)
    filename = 'movies_' + str(options.start) + '_' + str(options.stop) + '.json'
    with open(filename, 'w') as file:
        json.dump(movies, file, indent=2)

# Node: OptionParser
# Node: add_option
# Node: parse_args
# Node: worker
# Node: dump
def worker(api_key, movies):
    language = 'en-US'
    casts = []
    cast_ids = set()
    for movie in movies:
        for cast in movie['cast']:
            cast_ids.add(cast['id'])
    print('num_of_casts:', len(cast_ids))
    for cast_id in cast_ids:
        cast_url = 'https://api.themoviedb.org/3/person/' + str(cast_id)
        r = requests.request('GET', cast_url, params={'language': language, 'api_key': api_key})
        if r.status_code != 200:
            print('Failed to get popular_movie', 'status_code:', r.status_code, 'message:', r.text)
        casts.append(r.json())
        time.sleep(0.25)
        print('cast', cast_id, 'success')
    return casts

def main():
    parser = optparse.OptionParser()
    parser.add_option('--rfile', type='string', dest='rfile')
    parser.add_option('--wfile', type='string', dest='wfile')
    parser.add_option('--key', type='string', dest='api_key')
    options, args = parser.parse_args()
    with open(options.rfile, 'r') as movie_file:
        movies = json.load(movie_file)
        casts = worker(options.api_key, movies)
        with open(options.wfile, 'w') as cast_file:
            json.dump(casts, cast_file, indent=2)

# Node: load
def collect_trace_data(path):
    with open(path) as f:
        res = json.load(f)['data']
    service_id_mapping = pd.json_normalize(res).filter(regex='serviceName|traceID|tags').rename(columns=lambda x: re.sub('processes\\.(.*)\\.serviceName|processes\\.(.*)\\.tags', lambda match_obj: match_obj.group(1) if match_obj.group(1) else f'{match_obj.group(2)}Pod', x)).rename(columns={'traceID': 'traceId'})
    service_id_mapping = service_id_mapping.filter(regex='.*Pod').applymap(lambda x: [v['value'] for v in x if v['key'] == 'hostname'][0] if isinstance(x, list) else '').combine_first(service_id_mapping)
    spans_data = pd.json_normalize(res, record_path='spans')[['traceID', 'spanID', 'operationName', 'duration', 'processID', 'references', 'startTime']]
    spans_with_parent = spans_data[~(spans_data['references'].astype(str) == '[]')]
    root_spans = spans_data[spans_data['references'].astype(str) == '[]']
    root_spans = root_spans.rename(columns={'traceID': 'traceId', 'startTime': 'traceTime', 'duration': 'traceLatency'})[['traceId', 'traceTime', 'traceLatency']]
    spans_with_parent.loc[:, 'parentId'] = spans_with_parent['references'].map(lambda x: x[0]['spanID'])
    temp_parent_spans = spans_data[['traceID', 'spanID', 'operationName', 'duration', 'processID']].rename(columns={'spanID': 'parentId', 'processID': 'parentProcessId', 'operationName': 'parentOperation', 'duration': 'parentDuration', 'traceID': 'traceId'})
    temp_children_spans = spans_with_parent[['operationName', 'duration', 'parentId', 'traceID', 'spanID', 'processID', 'startTime']].rename(columns={'spanID': 'childId', 'processID': 'childProcessId', 'operationName': 'childOperation', 'duration': 'childDuration', 'traceID': 'traceId'})
    merged_df = pd.merge(temp_parent_spans, temp_children_spans, on=['parentId', 'traceId'])
    merged_df = merged_df[['traceId', 'childOperation', 'childDuration', 'parentOperation', 'parentDuration', 'parentId', 'childId', 'parentProcessId', 'childProcessId', 'startTime']]
    merged_df = merged_df.merge(service_id_mapping, on='traceId')
    merged_df = merged_df.merge(root_spans, on='traceId')
    merged_df = merged_df.assign(childMS=merged_df.apply(lambda x: x[x['childProcessId']], axis=1), childPod=merged_df.apply(lambda x: x[f'{str(x['childProcessId'])}Pod'], axis=1), parentMS=merged_df.apply(lambda x: x[x['parentProcessId']], axis=1), parentPod=merged_df.apply(lambda x: x[f'{str(x['parentProcessId'])}Pod'], axis=1), endTime=merged_df['startTime'] + merged_df['childDuration'])
    merged_df = merged_df[['traceId', 'traceTime', 'startTime', 'endTime', 'parentId', 'childId', 'childOperation', 'parentOperation', 'childMS', 'childPod', 'parentMS', 'parentPod', 'parentDuration', 'childDuration']]
    print(merged_df)
    merged_df.to_csv('trace.csv', index=False)

# Node: rename
# Node: json_normalize
# Node: sub
# Node: group
# Node: combine_first
# Node: applymap
# Node: astype
# Node: map
# Node: merge
# Node: assign
# Node: apply
# Node: to_csv
# Node: ReadHomeTimeline
# Node: Media
# Node: StorePost
# Node: ReadPost
# Node: ReadPosts
# Node: GetFollowers
# Node: GetFollowees
# Node: Follow
# Node: Unfollow
# Node: ReadUserTimeline
def config_thrift(tls):
    if tls:
        f = open('/social-network-microservices/config/service-config.json')
        content = f.read()
        j = json.loads(content)
        j['ssl']['enabled'] = True
        f.close()
        f = open('/social-network-microservices/config/service-config.json', 'w')
        f.write(json.dumps(j, indent=2))
        f.close()
    else:
        f = open('/social-network-microservices/config/service-config.json')
        content = f.read()
        j = json.loads(content)
        j['ssl']['enabled'] = False
        f.close()
        f = open('/social-network-microservices/config/service-config.json', 'w')
        f.write(json.dumps(j, indent=2))
        f.close()

def config_mongod(tls):
    if tls:
        f = open('/social-network-microservices/config/mongod.conf')
        content = f.read()
        y = yaml.load(content)
        y['net']['tls']['mode'] = 'requireTLS'
        y['net']['tls']['certificateKeyFile'] = '/keys/server.pem'
        f.close()
        f = open('/social-network-microservices/config/mongod.conf', 'w')
        f.write(yaml.dump(y, default_flow_style=False))
        f.close()
    else:
        f = open('/social-network-microservices/config/mongod.conf')
        content = f.read()
        y = yaml.load(content)
        y['net']['tls']['mode'] = 'disabled'
        try:
            del y['net']['tls']['certificateKeyFile']
        except:
            pass
        f.close()
        f = open('/social-network-microservices/config/mongod.conf', 'w')
        f.write(yaml.dump(y, default_flow_style=False))
        f.close()

def config_redis(tls):
    if tls:
        f = open('/social-network-microservices/config/redis.conf')
        content = f.read()
        content = content.replace('port 6379', 'port 0')
        content = content.replace('tls-port 0', 'tls-port 6379')
        f.close()
        f = open('/social-network-microservices/config/redis.conf', 'w')
        f.write(content)
        f.close()
    else:
        f = open('/social-network-microservices/config/redis.conf')
        content = f.read()
        content = content.replace('port 0', 'port 6379')
        content = content.replace('tls-port 6379', 'tls-port 0')
        f.close()
        f = open('/social-network-microservices/config/redis.conf', 'w')
        f.write(content)
        f.close()

# Node: replace
async def upload_compose(session, addr, user_id, num_users):
    text = ''.join(random.choices(string.ascii_letters + string.digits, k=256))
    for _ in range(random.randint(0, 5)):
        text += ' @username_' + str(random.randint(0, num_users))
    for _ in range(random.randint(0, 5)):
        text += ' http://' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))
    media_ids = []
    media_types = []
    for _ in range(random.randint(0, 5)):
        media_ids.append('"' + ''.join(random.choices(string.digits, k=18)) + '"')
        media_types.append('"png"')
    payload = {'username': 'username_' + str(user_id), 'user_id': str(user_id), 'text': text, 'media_ids': '[' + ','.join(media_ids) + ']', 'media_types': '[' + ','.join(media_types) + ']', 'post_type': '0'}
    async with session.post(addr + '/wrk2-api/post/compose', data=payload) as resp:
        return await resp.text()

def getEdges(file):
    edges = []
    lines = file.readlines()
    for line in lines:
        edges.append(line.split())
    return edges

# Node: readlines
# Node: split
def main():
    req_id = uuid.uuid4().int & 9223372036854775807
    text = 'text'
    post_tyoe = PostType.POST
    media_types = ['png', 'png', 'png', 'png']
    media_ids = [1, 2, 3, 4]
    creator = 'username_0'
    text_socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10007)
    text_transport = TTransport.TFramedTransport(text_socket)
    text_protocol = TBinaryProtocol.TBinaryProtocol(text_transport)
    text_client = TextService.Client(text_protocol)
    text_transport.open()
    text_client.UploadText(req_id, text, {})
    text_transport.close()
    media_socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10006)
    media_transport = TTransport.TFramedTransport(media_socket)
    media_protocol = TBinaryProtocol.TBinaryProtocol(media_transport)
    media_client = MediaService.Client(media_protocol)
    media_transport.open()
    print(media_client.UploadMedia(req_id, media_types, media_ids, {}))
    media_transport.close()
    user_socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10005)
    user_transport = TTransport.TFramedTransport(user_socket)
    user_protocol = TBinaryProtocol.TBinaryProtocol(user_transport)
    user_client = UserService.Client(user_protocol)
    user_transport.open()
    user_client.UploadCreatorWithUsername(req_id, creator, {})
    user_transport.close()
    post_id_socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10008)
    post_id_transport = TTransport.TFramedTransport(post_id_socket)
    post_id_protocol = TBinaryProtocol.TBinaryProtocol(post_id_transport)
    post_id_client = UniqueIdService.Client(post_id_protocol)
    post_id_transport.open()
    post_id_client.UploadUniqueId(req_id, post_tyoe, {})
    post_id_transport.close()

# Node: UploadMedia
# Node: UploadCreatorWithUsername
def register():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10005)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UserService.Client(protocol)
    transport.open()
    req_id = uuid.uuid4().int & 9223372036854775807
    client.RegisterUser(req_id, 'first_name_0', 'last_name_0', 'username_11114', 'password_0', {})
    client.RegisterUserWithId(req_id, 'first_name_1', 'last_name_1', 'username_1', 'password_1', 1, {})
    client.RegisterUserWithId(req_id, 'first_name_2', 'last_name_2', 'username_2', 'password_2', 2, {})
    transport.close()

def login():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10005)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UserService.Client(protocol)
    transport.open()
    req_id = uuid.uuid4().int & 9223372036854775807
    print(client.Login(req_id, 'username_0', 'password_0', {}))
    transport.close()

def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UrlShortenService.Client(protocol)
    transport.open()
    req_id = uuid.uuid4().int & 1 << 32
    urls = ['https://url_0.com', 'https://url_1.com', 'https://url_2.com']
    print(client.UploadUrls(req_id, urls, {}))
    transport.close()

# Node: UploadUrls
def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UserMentionService.Client(protocol)
    transport.open()
    req_id = uuid.uuid4().int & 9223372036854775807
    user_mentions = ['username_0', 'username_1', 'username_2']
    print(client.UploadUserMentions(req_id, user_mentions, {}))
    transport.close()

# Node: UploadUserMentions
def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UniqueIdService.Client(protocol)
    transport.open()
    req_id = uuid.uuid4().int & 1 << 32
    print(client.UploadUniqueId(req_id, PostType.POST, {}))
    transport.close()

def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = UserTimelineService.Client(protocol)
    transport.open()
    req_id = uuid.uuid4().int & 9223372036854775807
    user_id = 0
    start = 0
    stop = 5
    print(client.ReadUserTimeline(req_id, user_id, start, stop, {}))
    transport.close()

def store_post():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = PostStorageService.Client(protocol)
    transport.open()
    req_id = random.getrandbits(63)
    text = 'HelloWorld'
    media_0 = Media(media_id=0, media_type=MediaType.PHOTO)
    media_1 = Media(media_id=1, media_type=MediaType.PHOTO)
    media = [media_0, media_1]
    post_id = 0
    post_type = PostType.POST
    creator = Creator(username='user_0', user_id=0)
    url_0 = Url(shortened_url='shortened_url_0', expanded_url='expanded_url_0')
    url_1 = Url(shortened_url='shortened_url_1', expanded_url='expanded_url_1')
    urls = [url_0, url_1]
    user_mention_0 = UserMention(user_id=1, username='user_1')
    user_mention_1 = UserMention(user_id=2, username='user_2')
    user_mentions = [user_mention_0, user_mention_1]
    post = Post(user_mentions=user_mentions, req_id=req_id, creator=creator, post_type=post_type, urls=urls, media=media, post_id=post_id, text=text)
    client.StorePost(req_id, post, {})
    transport.close()

def read_post():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = PostStorageService.Client(protocol)
    transport.open()
    req_id = random.getrandbits(63)
    post_id = 0
    post = client.ReadPost(req_id, post_id, {})
    print(post)

def read_posts():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = PostStorageService.Client(protocol)
    transport.open()
    req_id = random.getrandbits(63)
    post_id = [783799431931478016, 783799431931547648, 783799431931551744]
    posts = client.ReadPosts(req_id, post_id, {})
    print(posts)

def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10001)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = ComposePostService.Client(protocol)
    transport.open()
    req_id = random.getrandbits(63)
    text = 'HelloWorld'
    media_0 = Media(media_id=0, media_type='png')
    media_1 = Media(media_id=1, media_type='png')
    medias = [media_0, media_1]
    post_id = random.getrandbits(63)
    post_type = PostType.POST
    creator = Creator(username='user_0', user_id=0)
    url_0 = Url(shortened_url='shortened_url_0', expanded_url='expanded_url_0')
    url_1 = Url(shortened_url='shortened_url_1', expanded_url='expanded_url_1')
    urls = [url_0, url_1]
    user_mention_0 = UserMention(user_id=1, username='user_1')
    user_mention_1 = UserMention(user_id=2, username='user_2')
    user_mentions = [user_mention_0, user_mention_1]
    client.UploadText(req_id, text, {})
    client.UploadMedia(req_id, medias, {})
    client.UploadUniqueId(req_id, post_id, post_type, {})
    client.UploadCreator(req_id, creator, {})
    client.UploadUrls(req_id, urls, {})
    client.UploadUserMentions(req_id, user_mentions, {})
    transport.close()

# Node: UploadCreator
def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = HomeTimelineService.Client(protocol)
    transport.open()
    req_id = uuid.uuid4().int & 9223372036854775807
    user_id = 1
    start = 0
    stop = 10
    print(client.ReadHomeTimeline(req_id, user_id, start, stop, {}))
    transport.close()

def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 10000)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = SocialGraphService.Client(protocol)
    transport.open()
    req_id = uuid.uuid4().int & 1 << 32
    client.Follow(req_id, 0, 1, {})
    client.Follow(req_id, 0, 2, {})
    client.Follow(req_id, 1, 2, {})
    client.Follow(req_id, 1, 0, {})
    client.Follow(req_id, 2, 1, {})
    client.Follow(req_id, 2, 0, {})
    client.Follow(req_id, 2, 0, {})
    client.Unfollow(req_id, 1, 0, {})
    client.Unfollow(req_id, 1, 2, {})
    client.Follow(req_id, 1, 0, {})
    client.Follow(req_id, 1, 2, {})
    print(client.GetFollowers(req_id, 0, {}))
    print(client.GetFollowers(req_id, 1, {}))
    print(client.GetFollowers(req_id, 2, {}))
    print(client.GetFollowees(req_id, 0, {}))
    print(client.GetFollowees(req_id, 1, {}))
    print(client.GetFollowees(req_id, 2, {}))
    transport.close()

def main():
    socket = TSocket.TSocket('ath-8.ece.cornell.edu', 9090)
    transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = TextService.Client(protocol)
    transport.open()
    for i in range(1):
        req_id = uuid.uuid4().int & 9223372036854775807
        text = 'TCoch8ij3Pgli6LlPcpoySmH9EDQB5klJmG7vCdhxQIEvjC6S5tKURvY796X4dePDKU0ELgBpVhYrqWG6YvW0Z77K2KStZsJQKH4Q5JPJ6yZ7Un2eCzwTh9diHBsn92MJIZuWmHocC3lkkpzeEcULzLM9UwbY3fsQ7k2v8qKL30qppxsDJLxqWa98svRtAGTI7v45vSFgAGnX9AvHlKHZ2GKewaiSMSoC8wJxDzPf9888OxD1wkA47l68EeOkGJr+%40username_916+%40username_338+%40username_67+%40username_505+http%3A%2F%2FPeTI0e2S444RVMCLVgCxUmwAeXx0unYHWqfQete796QXCdEIQg37F5UJH2HVhsEJ+http%3A%2F%2FsHigXpaLySE2B6nfakaNdKT3OpGNcuYUCFCYV6g3UKZxFoIBQLSFQyY0hpBAjzue+http%3A%2F%2F72OZBVSxRcGuRd456TIcAexMdomRWUYnnris1ZUztsQOnzEzN0Hne0ghoFLPpf9I+http%3A%2F%2FkyZiNjQ3W2W1a4p04Mn6MDa8j3IQuY9bSLYm97lQBZj9DQ9UjvWy0DejTAJSuH0K+http%3A%2F%2FbTuvQmVfordCTakXUZMUc3V1RRWPoQjU5b3cVHP6ZCKf609ELB0rJC4phcZnCq5J'
        print(client.UploadText(req_id, text, {}))
    transport.close()

def make_user(i: int):
    return 'tester-' + str(i)

def make_user(i: int):
    return 'tester-' + str(i)

def make_user(i: int):
    return 'tester-' + str(i)

def make_user(i):
    return 'tester-' + str(i)

def make_user(i):
    return 'tester-' + str(i)

def make_user(i: int):
    return 'tester-' + str(i)

def make_user(i: int):
    return 'tester-' + str(i)

def make_user(i: int):
    return 'tester-' + str(i)

def inc_user_id():
    global user_id
    user_id = int(user_id.split('-')[-1]) + 1
    user_id = 'test-ur-user-' + str(user_id)

def inc_video_id():
    global video_id
    video_id = int(video_id.split('-')[-1]) + 1
    video_id = 'test-ur-video-' + str(video_id)

def inc_video_id():
    global video_id
    video_id = int(video_id.split('-')[-1]) + 1
    video_id = 'video-' + str(video_id)

def inc_video_id():
    global video_id
    id = int(video_id.split('-')[-1]) + 1
    video_id = 'The fallen ca community - ' + str(id)

def pickFormat(format: str) -> str:
    if ',' not in format:
        return format
    else:
        all_formats = format.replace(' ', '').split(',')
        if 'mp4' in all_formats and 'mov' in all_formats:
            return 'mp4'
        else:
            return all_formats[0]

def update_comm(updates: int, post_id: str, user_id: str):
    ctr = 0
    for i in range(0, updates):
        comm_id = 'post-id-' + user_id + '-' + str(ctr)
        ctr += 1
        text = 'Get out of acamdemia! X' + str(ctr)
        comm_req = make_comment(post_id=post_id, user_id=user_id, comm_id=comm_id, reply_to='', text=text)
        r = requests.post(comment_url, json=comm_req)

# Node: make_comment
def inc_post_id():
    global post_id
    post_id = int(post_id.split('-')[-1]) + 1
    post_id = 'post-' + str(post_id)

def inc_post_id():
    global post_id
    post_id = int(post_id.split('-')[-1]) + 1
    post_id = 'multi-post-' + str(post_id)

def postIdTime(post_id: str):
    return int(post_id.split('*')[-1])

def make_user(i):
    return 'recmd-user-' + str(i)

def make_user(i):
    return 'recmd-user-' + str(i)

def make_user(i):
    return 'reg-user-' + str(i)

