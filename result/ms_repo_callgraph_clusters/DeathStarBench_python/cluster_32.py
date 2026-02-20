# Cluster 32

async def write_cast_info(addr, raw_casts):
    idx = 0
    tasks = []
    conn = aiohttp.TCPConnector(limit=200)
    async with aiohttp.ClientSession(connector=conn) as session:
        for raw_cast in raw_casts:
            try:
                cast = dict()
                cast['cast_info_id'] = raw_cast['id']
                cast['name'] = raw_cast['name']
                cast['gender'] = True if raw_cast['gender'] == 2 else False
                cast['intro'] = raw_cast['biography']
                task = asyncio.ensure_future(upload_cast_info(session, addr, cast))
                tasks.append(task)
                idx += 1
            except:
                print('Warning: cast info missing!')
            if idx % 200 == 0:
                resps = await asyncio.gather(*tasks)
                print(idx, 'casts finished')
        resps = await asyncio.gather(*tasks)
        print(idx, 'casts finished')

# Node: TCPConnector
# Node: ClientSession
# Node: dict
# Node: ensure_future
# Node: upload_cast_info
# Node: gather
async def write_movie_info(addr, raw_movies):
    idx = 0
    tasks = []
    conn = aiohttp.TCPConnector(limit=200)
    async with aiohttp.ClientSession(connector=conn) as session:
        for raw_movie in raw_movies:
            movie = dict()
            casts = list()
            movie['movie_id'] = str(raw_movie['id'])
            movie['title'] = raw_movie['title']
            movie['plot_id'] = raw_movie['id']
            for raw_cast in raw_movie['cast']:
                try:
                    cast = dict()
                    cast['cast_id'] = raw_cast['cast_id']
                    cast['character'] = raw_cast['character']
                    cast['cast_info_id'] = raw_cast['id']
                    casts.append(cast)
                except:
                    print('Warning: cast info missing!')
            movie['casts'] = casts
            movie['thumbnail_ids'] = [raw_movie['poster_path']]
            movie['photo_ids'] = []
            movie['video_ids'] = []
            movie['avg_rating'] = raw_movie['vote_average']
            movie['num_rating'] = raw_movie['vote_count']
            task = asyncio.ensure_future(upload_movie_info(session, addr, movie))
            tasks.append(task)
            plot = dict()
            plot['plot_id'] = raw_movie['id']
            plot['plot'] = raw_movie['overview']
            task = asyncio.ensure_future(upload_plot(session, addr, plot))
            tasks.append(task)
            task = asyncio.ensure_future(register_movie(session, addr, movie))
            tasks.append(task)
            idx += 1
            if idx % 200 == 0:
                resps = await asyncio.gather(*tasks)
                print(idx, 'movies finished')
        resps = await asyncio.gather(*tasks)
        print(idx, 'movies finished')

# Node: list
# Node: upload_movie_info
# Node: upload_plot
# Node: register_movie
async def register(addr, nodes, limit=200):
    tasks = []
    conn = aiohttp.TCPConnector(limit=limit)
    async with aiohttp.ClientSession(connector=conn) as session:
        print('Registering Users...')
        for i in range(nodes):
            task = asyncio.ensure_future(upload_register(session, addr, str(i)))
            tasks.append(task)
            if i % limit == 0:
                _ = await asyncio.gather(*tasks)
                print(i)
        results = await asyncio.gather(*tasks)
        printResults(results)

# Node: upload_register
# Node: printResults
async def follow(addr, edges, limit=200):
    idx = 0
    tasks = []
    conn = aiohttp.TCPConnector(limit=limit)
    async with aiohttp.ClientSession(connector=conn) as session:
        print('Adding follows...')
        for edge in edges:
            task = asyncio.ensure_future(upload_follow(session, addr, edge[0], edge[1]))
            tasks.append(task)
            task = asyncio.ensure_future(upload_follow(session, addr, edge[1], edge[0]))
            tasks.append(task)
            idx += 1
            if idx % limit == 0:
                _ = await asyncio.gather(*tasks)
                print(idx)
        results = await asyncio.gather(*tasks)
        printResults(results)

# Node: upload_follow
async def compose(addr, nodes, limit=200):
    idx = 0
    tasks = []
    conn = aiohttp.TCPConnector(limit=limit)
    async with aiohttp.ClientSession(connector=conn) as session:
        print('Composing posts...')
        for i in range(nodes):
            for _ in range(random.randint(0, 20)):
                task = asyncio.ensure_future(upload_compose(session, addr, i + 1, nodes))
                tasks.append(task)
                idx += 1
                if idx % limit == 0:
                    _ = await asyncio.gather(*tasks)
                    print(idx)
        results = await asyncio.gather(*tasks)
        printResults(results)

# Node: upload_compose
def latBuckets():
    buckets = list(np.arange(1.0, 201.0, 1.0))
    buckets += list(np.arange(205.0, 505.0, 5.0))
    buckets += list(np.arange(510.0, 1010.0, 10.0))
    buckets += list(np.arange(1100.0, 5100.0, 100.0))
    buckets += list(np.arange(10000.0, 65000.0, 5000.0))
    return buckets

# Node: arange
# Node: keys
def tl_last_post(tl: dict):
    all_posts = list(tl['posts'].keys())
    all_posts = sorted(all_posts)
    return all_posts[-1]

# Node: sorted
def tl_last_post(tl: dict):
    all_posts = list(tl['posts'].keys())
    all_posts = sorted(all_posts)
    return all_posts[-1]

def tl_last_post(tl: dict):
    all_posts = list(tl['posts'].keys())
    all_posts = sorted(all_posts)
    return all_posts[-1]

def latBuckets():
    buckets = list(np.arange(1.0, 201.0, 1.0))
    buckets += list(np.arange(205.0, 505.0, 5.0))
    buckets += list(np.arange(510.0, 5010.0, 10.0))
    buckets += list(np.arange(5025.0, 10025.0, 25.0))
    buckets += list(np.arange(11000.0, 61000.0, 1000.0))
    return buckets

def latBucketsLong():
    buckets = list(np.arange(5.0, 5005.0, 5.0))
    buckets += list(np.arange(5010.0, 10010.0, 10.0))
    buckets += list(np.arange(10020.0, 60020.0, 20.0))
    buckets += list(np.arange(60200.0, 150200.0, 200.0))
    return buckets

def latBuckets():
    buckets = list(np.arange(1.0, 101.0, 1.0))
    buckets += list(np.arange(105.0, 505.0, 5.0))
    buckets += list(np.arange(510.0, 1010.0, 10.0))
    buckets += list(np.arange(1050.0, 2550.0, 50.0))
    buckets += list(np.arange(2600.0, 5100.0, 100.0))
    buckets += list(np.arange(10000.0, 65000.0, 5000.0))
    return buckets

def latBucketsMl():
    buckets = list(np.arange(10.0, 1010.0, 10.0))
    buckets += list(np.arange(1025.0, 2525.0, 25.0))
    buckets += list(np.arange(2550.0, 5050.0, 50.0))
    buckets += list(np.arange(10000.0, 65000.0, 5000.0))
    return buckets

def latBucketsLongMl():
    buckets = list(np.arange(25.0, 5025.0, 25.0))
    buckets += list(np.arange(5050.0, 10050.0, 50.0))
    buckets += list(np.arange(10100.0, 30100.0, 100.0))
    buckets += list(np.arange(31000.0, 61000.0, 1000.0))
    return buckets

