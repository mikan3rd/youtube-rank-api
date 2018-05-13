from app.config import current_config


def after_request(response):
    server_config = current_config().get('server')

    origin = server_config.get('access_control_allow_origin')

    response.headers['Access-Control-Allow-Origin'] = origin

    methods = server_config.get('access_control_allow_methods')
    response.headers['Access-Control-Allow-Methods'] = methods

    headers = server_config.get('access_control_allow_headers')
    response.headers['Access-Control-Allow-Headers'] = headers

    print(response.headers)

    return response
