# Cluster 5

class sparse_data_repos:

    def __init__(self, n_user, n_item, n_user_attr=0, n_item_attr=0):
        self.n_user = n_user
        self.n_item = n_item
        self.n_user_attr = n_user_attr
        self.n_item_attr = n_item_attr
        self.user_attr = []
        self.item_attr = []
        self.training_ratings_user = []
        self.training_ratings_item = []
        self.training_ratings_item02 = []
        self.training_ratings_score = []
        self.test_ratings_user = []
        self.test_ratings_item = []
        self.test_ratings_item02 = []
        self.test_ratings_score = []
        self.eval_ratings_user = []
        self.eval_ratings_item = []
        self.eval_ratings_score = []

    def load_user_attributes(self, infile, spliter='\t'):
        self.load_attributes(self.user_attr, self.n_user, self.n_user_attr, infile, spliter)

    def load_item_attributes(self, infile, spliter='\t'):
        self.load_attributes(self.item_attr, self.n_item, self.n_item_attr, infile, spliter)

    def load_attributes(self, res, n, m, infile, spliter):
        del res[:]
        for i in range(n):
            res.append([])
        with open(infile, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.replace('\r\n', '').replace('\n', '').split(spliter)
                uid = int(words[0])
                for i in range(len(words) - 1):
                    tokens = words[i + 1].split(':')
                    res[uid].append([int(tokens[0]), float(tokens[1])])

    def load_trainging_ratings(self, infile, spliter='\t'):
        self.load_rating_file(infile, self.training_ratings_user, self.training_ratings_item, self.training_ratings_score, spliter)

    def load_test_ratings(self, infile, spliter='\t'):
        self.load_rating_file(infile, self.test_ratings_user, self.test_ratings_item, self.test_ratings_score, spliter)

    def load_eval_ratings(self, infile, spliter='\t'):
        self.load_rating_file(infile, self.eval_ratings_user, self.eval_ratings_item, self.eval_ratings_score, spliter)

    def load_rating_file(self, infile, rating_user, rating_item, rating_score, spliter):
        del rating_user[:]
        del rating_item[:]
        del rating_score[:]
        with open(infile, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.replace('\r\n', '').replace('\n', '').split(spliter)
                rating_user.append(int(words[0]))
                rating_item.append(int(words[1]))
                rating_score.append(float(words[2]))

    def load_trainging_pairwise_ratings(self, infile, spliter='\t'):
        self.load_pairwise_rating_file(infile, self.training_ratings_user, self.training_ratings_item, self.training_ratings_item02, self.training_ratings_score, spliter)

    def load_test_pairwise_ratings(self, infile, spliter='\t'):
        self.load_pairwise_rating_file(infile, self.test_ratings_user, self.test_ratings_item, self.test_ratings_item02, self.test_ratings_score, spliter)

    def load_pairwise_rating_file(self, infile, rating_user, rating_item01, rating_item02, rating_score, spliter):
        del rating_user[:]
        del rating_item01[:]
        del rating_item02[:]
        del rating_score[:]
        with open(infile, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.replace('\r\n', '').replace('\n', '').split(spliter)
                rating_user.append(int(words[0]))
                rating_item01.append(int(words[1]))
                rating_item02.append(int(words[2]))
                rating_score.append(float(words[3]))

def load_trainging_ratings(self, infile, spliter='\t'):
    self.load_rating_file(infile, self.training_ratings_user, self.training_ratings_item, self.training_ratings_score, spliter)

def load_test_ratings(self, infile, spliter='\t'):
    self.load_rating_file(infile, self.test_ratings_user, self.test_ratings_item, self.test_ratings_score, spliter)

def load_eval_ratings(self, infile, spliter='\t'):
    self.load_rating_file(infile, self.eval_ratings_user, self.eval_ratings_item, self.eval_ratings_score, spliter)

class dense_data_repos:

    def __init__(self, n_user, n_item, n_user_attr=0, n_item_attr=0):
        self.n_user = n_user
        self.n_item = n_item
        self.n_user_attr = n_user_attr
        self.n_item_attr = n_item_attr
        self.user_attr = []
        self.item_attr = []
        self.training_ratings = []
        self.test_ratings = []

    def load_user_attributes(self, infile, spliter='\t'):
        self.load_attributes(self.user_attr, self.n_user, self.n_user_attr, infile, spliter)

    def load_item_attributes(self, infile, spliter='\t'):
        self.load_attributes(self.item_attr, self.n_item, self.n_item_attr, infile, spliter)

    def load_attributes(self, res, n, m, infile, spliter):
        del res[:]
        for i in range(n):
            res.append([0.0] * m)
        with open(infile, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.replace('\r\n', '').replace('\n', '').split(spliter)
                uid = int(words[0])
                for i in range(len(words) - 1):
                    tokens = words[i + 1].split(':')
                    res[uid][int(tokens[0])] = float(tokens[1])

    def load_trainging_ratings(self, infile, spliter='\t'):
        self.load_rating_file(infile, self.training_ratings, spliter)

    def load_test_ratings(self, infile, spliter='\t'):
        self.load_rating_file(infile, self.test_ratings, spliter)

    def load_rating_file(self, infile, rating_list, spliter):
        del rating_list[:]
        with open(infile, 'r') as rd:
            while True:
                line = rd.readline()
                if not line:
                    break
                words = line.replace('\r\n', '').replace('\n', '').split(spliter)
                rating_list.append([int(words[0]), int(words[1]), float(words[2])])

def load_trainging_ratings(self, infile, spliter='\t'):
    self.load_rating_file(infile, self.training_ratings, spliter)

def load_test_ratings(self, infile, spliter='\t'):
    self.load_rating_file(infile, self.test_ratings, spliter)

