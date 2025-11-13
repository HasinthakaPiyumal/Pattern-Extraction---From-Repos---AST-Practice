# Cluster 21

def actor_process(opt, shared_data):
    actor = Actor(opt, shared_data)
    actor.run()

def record_process(opt, shared_data):
    recorder = Recorder(opt, shared_data)
    recorder.run()

def learner_process(opt, shared_data):
    learner = Learner(opt, shared_data)
    learner.run()

def eval_process(eid, opt, shared_data):
    evaluator = Evaluator(eid, opt, shared_data)
    evaluator.run()

