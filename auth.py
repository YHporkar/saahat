from functools import wraps
from flask import g, session
from flask_restful import Resource, abort
import argon2
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth

import status


from models.UserModel import User

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth(scheme='Token')


# auth = MultiAuth(token_auth, basic_auth)


@basic_auth.verify_password
def verify_user_password(username_or_email, password):
    try:
        user = User.query.filter_by(username=username_or_email).first()
        if not user:
            user = User.query.filter_by(email=username_or_email.lower()).first()
            # app.logger.info('%s failed to log in', username_or_email)
        if not user or not user.verify_password(password):
            return False
    except argon2.exceptions.VerifyMismatchError:
        return False
    # app.logger.info('{} logged in successfully'.format(user.username))
    g.user = user
    return True


def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not role_authenticated(get_current_user_role(), list(roles)):
                # roles_list = ' or '.join(list(roles))
                # abort(status.HTTP_403_FORBIDDEN, message='you need {} access'.format(roles_list))
                return 'Unauthorized Access', status.HTTP_403_FORBIDDEN
                
            return f(*args, **kwargs)
        return wrapped
    return wrapper
 

def is_accepted_by_admin(user):
    return user.authorized

def role_authenticated(user_roles, required_roles):
    for role in user_roles:
        if role in required_roles:
            return True
    return False


def get_current_user_role():
    roles = g.user.roles
    ret_roles = []
    for role in roles:
        ret_roles.append(role.role_name)
    return ret_roles


@token_auth.verify_token
def verify_token(token):
    user = User.verify_auth_token(token)
    if user is not None and is_accepted_by_admin(user):
        g.user = user
        return True
    return False


class AuthRequiredResource(Resource):
    method_decorators = [token_auth.login_required]

class AdminAuthRequiredResource(Resource):
    method_decorators = [roles_required('admin'), token_auth.login_required]

class MentorAuthRequiredResource(Resource):
    method_decorators = [roles_required('admin', 'mentor'), token_auth.login_required]

class SessionAuthRequiredResource(Resource):
    method_decorators = [roles_required('admin', 'session'), token_auth.login_required]

class CampAuthRequiredResource(Resource):
    method_decorators = [roles_required('admin', 'camp'), token_auth.login_required]

class HeyatAuthRequiredResource(Resource):
    method_decorators = [roles_required('admin', 'camp'), token_auth.login_required]

class EducationAuthRequiredResource(Resource):
    method_decorators = [roles_required('admin', 'education'), token_auth.login_required]

class DocumentAuthRequiredResource(Resource):
    method_decorators = [roles_required('admin', 'document', 'mentor'), token_auth.login_required]

class AccountingAuthRequiredResource(Resource):
    method_decorators = [roles_required('admin', 'accounting' 'mentor'), token_auth.login_required]

class SportAuthRequiredResource(Resource):
    method_decorators = [roles_required('admin', 'sport'), token_auth.login_required]

class FormAuthRequiredResource(Resource):
    method_decorators = [roles_required('admin', 'form'), token_auth.login_required]