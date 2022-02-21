from flask import Flask, request
from rainbond_python.parameter import Parameter
from rainbond_python.error_handler import error_handler

app = Flask(__name__)
error_handler(app)


@app.route('/api/v1/demo', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_demo():
    parameter = Parameter(request)

    if parameter.method == 'GET':
        return parameter.param_url

    elif parameter.method == 'POST':
        return parameter.param_json

    elif parameter.method == 'PUT':
        return parameter.param_json

    elif parameter.method == 'DELETE':
        return parameter.param_json


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
