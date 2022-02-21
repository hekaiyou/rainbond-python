from flask_cors import CORS
from .tools import handle_abnormal


def error_handler(app, simple_cors: bool = True):
    app.config["JSON_AS_ASCII"] = False
    if simple_cors:
        CORS(app, supports_credentials=True)

    @app.errorhandler(400)
    def handle_400_error(error):
        return handle_abnormal(message='请求参数错误', status=400, is_raw=True)

    @app.errorhandler(403)
    def handle_403_error(error):
        return handle_abnormal(message='资源不可用', status=403, is_raw=True)

    @app.errorhandler(404)
    def handle_404_error(error):
        return handle_abnormal(message='资源不存在', status=404, is_raw=True)

    @app.errorhandler(406)
    def handle_406_error(error):
        return handle_abnormal(message='不支持所需表示', status=406, is_raw=True)

    @app.errorhandler(409)
    def handle_409_error(error):
        return handle_abnormal(message='发生冲突', status=409, is_raw=True)

    @app.errorhandler(412)
    def handle_412_error(error):
        return handle_abnormal(message='前置条件失败', status=412, is_raw=True)

    @app.errorhandler(415)
    def handle_415_error(error):
        return handle_abnormal(message='不支持收到的表示', status=415, is_raw=True)

    @app.errorhandler(500)
    def handle_500_error(error):
        return handle_abnormal(message='服务内部错误', status=500, is_raw=True)

    @app.errorhandler(503)
    def handle_503_error(error):
        return handle_abnormal(message='服务无法处理请求', status=503, is_raw=True)

    @app.errorhandler(504)
    def handle_504_error(error):
        return handle_abnormal(message='服务网关超时', status=504, is_raw=True)
