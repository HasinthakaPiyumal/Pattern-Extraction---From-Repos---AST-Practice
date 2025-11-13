# Cluster 9

def create_app():
    app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
    session_manager = SessionManager(app)
    app.config['session_manager'] = session_manager
    asset_config = AssetConfig()
    app.config['asset_config'] = asset_config

    @app.context_processor
    def inject_asset_url():
        return {'asset_url': asset_config.asset_url, 'get_asset_url': asset_config.get_asset_url}

    @app.route('/api/chat', methods=['POST'])
    def chat():
        try:
            data = request.get_json()
            if not data:
                return (jsonify({'error': 'Invalid JSON payload', 'done': True, 'done_reason': 'error'}), 400)
            session_id = session.get('session_id')
            abort_flag = session_manager.get_abort_flag(session_id)
            session_manager.reset_abort_flag(session_id)
            if data.get('stream', True):
                api_response = make_api_request('/api/chat', data, stream=True)

                def generate():
                    try:
                        for chunk in api_response.iter_lines():
                            if abort_flag.is_set():
                                logger.info(f'Aborting stream for session {session_id[:8]}...')
                                api_response.close()
                                yield 'data: {"type": "abort", "content": "Request aborted"}\n\n'
                                break
                            if chunk:
                                yield f'data: {chunk.decode()}\n\n'
                    except Exception as e:
                        logger.error(f'Stream error: {str(e)}')
                        yield f'data: {{"error": "{str(e)}", "done": true}}\n\n'
                return Response(stream_with_context(generate()), mimetype='application/x-ndjson', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'})
            else:
                logger.info('Processing non-streaming request')
                response = make_api_request('/api/chat', data)
                return response.json()
        except (ConnectionError, Timeout):
            return (jsonify({'error': 'Connection error', 'done': True, 'done_reason': 'error'}), 503)
        except RequestException as e:
            status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else 500
            logger.error(f'RequestException: {str(e)}')
            return (jsonify({'error': 'An internal error has occurred', 'done': True, 'done_reason': 'error'}), status_code)

    @app.route('/api/chat/abort', methods=['POST'])
    def abort_chat():
        try:
            session_id = session.get('session_id')
            if not session_id:
                return (jsonify({'error': 'No active session'}), 400)
            session_manager.abort_chat(session_id)
            return jsonify({'status': 'success', 'message': 'Chat aborted'})
        except Exception as e:
            logger.error(f'Error aborting chat: {str(e)}', exc_info=True)
            return (jsonify({'error': 'An internal error has occurred'}), 500)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/assets/config', methods=['GET'])
    def get_asset_config():
        return jsonify({'assetUrl': asset_config.asset_url, 'cacheTimeout': asset_config.cache_timeout, 'debugMode': asset_config.debug_assets, 'version': asset_config.asset_version})

    @app.route('/health', methods=['GET'])
    def health_check():
        api_health = get_api_health()
        current_time = datetime.now(timezone.utc).isoformat()
        response = {'service': 'chipper-web', 'version': APP_VERSION, 'build': BUILD_NUMBER, 'status': 'healthy', 'timestamp': current_time, 'api': api_health}
        if api_health.get('status') == 'unhealthy':
            response['status'] = 'degraded'
        return jsonify(response)

    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f'404 error: {request.url}')
        return ('', 404)

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f'500 error: {str(error)}')
        return ('', 500)
    return app

