"""
run.py
====================================
The core module of my project
"""

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from app import create_app
from auth import basic_auth
from flask import g, jsonify
from flask_swagger import swagger
# from flask_login import current_user, LoginManager


# login_manager = LoginManager()

app = create_app('config')

spec = APISpec(
    title="Saahat",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)


# login_manager.init_app(app)

# @login_manager.user_loader
# def load_user(user_id):
#     return User.get(user_id)

# @app.before_request
# def before_request():
#     g.user = current_user


@app.route('/api/gettoken', methods=['GET'])
@basic_auth.login_required
def get_auth_token():
    """
    return Authentication token as json
    """
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


with app.test_request_context():
    spec.path(view=get_auth_token)


# @app.route('/api/spec')
# def spec():
#     return jsonify(swagger(app))

if __name__ == '__main__':
    app.run(host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'])
