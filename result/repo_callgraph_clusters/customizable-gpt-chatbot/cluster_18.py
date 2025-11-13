# Cluster 18

def generate_secure_random_id():
    min_value = 10 ** 10
    max_value = 10 ** 11 - 1
    return secrets.randbelow(max_value - min_value) + min_value

