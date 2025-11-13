# Cluster 13

def initialize_database():
    global conn
    create_database()
    initial_users = [(1, 'Alice', 'Smith', 'alice@test.com', '123-456-7890'), (2, 'Bob', 'Johnson', 'bob@test.com', '234-567-8901'), (3, 'Sarah', 'Brown', 'sarah@test.com', '555-567-8901')]
    for user in initial_users:
        add_user(*user)
    initial_purchases = [(1, '2024-01-01', 101, 99.99), (2, '2023-12-25', 100, 39.99), (3, '2023-11-14', 307, 49.99)]
    for purchase in initial_purchases:
        add_purchase(*purchase)
    initial_products = [(7, 'Hat', 19.99), (8, 'Wool socks', 29.99), (9, 'Shoes', 39.99)]
    for product in initial_products:
        add_product(*product)

