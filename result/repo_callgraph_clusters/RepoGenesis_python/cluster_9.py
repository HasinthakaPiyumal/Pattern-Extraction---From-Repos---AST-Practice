# Cluster 9

def create_minimal_app() -> Flask:
    app = Flask(__name__)

    @app.get('/health')
    def health() -> t.Any:
        return (jsonify({'status': 'ok'}), 200)

    @app.post('/echo')
    def echo() -> t.Any:
        if not request.is_json:
            return (jsonify({'error': 'invalid content-type'}), 400)
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or 'message' not in data or (not isinstance(data['message'], str)):
            return (jsonify({'error': 'invalid payload'}), 400)
        message: str = data['message']
        return (jsonify({'message': message, 'length': len(message)}), 200)

    @app.get('/sum')
    def sum_view() -> t.Any:
        a = request.args.get('a')
        b = request.args.get('b')
        try:
            a_int = int(a) if a is not None else None
            b_int = int(b) if b is not None else None
        except (TypeError, ValueError):
            return (jsonify({'error': 'parameters must be integers'}), 400)
        if a_int is None or b_int is None:
            return (jsonify({'error': 'missing parameters'}), 400)
        return (jsonify({'result': a_int + b_int}), 200)
    return app

# Node: Flask
