# Cluster 27

@contextlib.contextmanager
def local_seed(vmas_random_state):
    torch_state = torch.random.get_rng_state()
    np_state = np.random.get_state()
    py_state = random.getstate()
    torch.random.set_rng_state(vmas_random_state[0])
    np.random.set_state(vmas_random_state[1])
    random.setstate(vmas_random_state[2])
    yield
    vmas_random_state[0] = torch.random.get_rng_state()
    vmas_random_state[1] = np.random.get_state()
    vmas_random_state[2] = random.getstate()
    torch.random.set_rng_state(torch_state)
    np.random.set_state(np_state)
    random.setstate(py_state)

