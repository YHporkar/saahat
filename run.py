"""
run.py
====================================
The core module of my project
"""

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from app import create_app
from auth import basic_auth, roles_required, token_auth
from flask import g, jsonify
from flask_swagger import swagger
from models.UserModel import User
from resources.users import user_schema, db

from sqlalchemy.exc import SQLAlchemyError
import status

# from flask_login import current_user, LoginManager


# login_manager = LoginManager()

app = create_app('config')

spec = APISpec(
    title="Saahat",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)


@app.route('/api/gettoken', methods=['GET'])
@basic_auth.login_required
def get_auth_token():
    """
    return Authentication token as json
    """
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})

@app.route('/api/users/<int:user_id>/accept', methods=['POST'])
@token_auth.login_required
@roles_required('admin')
def accept_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user.authorized = 1
        user.update()
        return user_schema.dump(user)
    except SQLAlchemyError as e:
        db.session.rollback()
        resp = {"error": str(e)}
        return resp, status.HTTP_400_BAD_REQUEST





with app.test_request_context():
    spec.path(view=get_auth_token)


# @app.route('/api/spec')
# def spec():
#     return jsonify(swagger(app))

if __name__ == '__main__':
    app.run(host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'])
