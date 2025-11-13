# Cluster 5

def start_server(llm: Llama, port: int):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(1)
    while True:
        i = 0
        conn, addr = server.accept()
        print('Connected by', addr)
        proc = threading.Thread(target=app, args=(conn, i, llm))
        proc.start()
    server.close()

