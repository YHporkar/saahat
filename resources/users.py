from flask import Blueprint, g, jsonify, make_response, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, Resource, abort
from sqlalchemy.exc import SQLAlchemyError

import status
from auth import (AdminAuthRequiredResource, AuthRequiredResource,
                  access_denied, basic_auth, roles_required, token_auth)
from helpers import PaginationHelper
from models.UserModel import (AdminMessageSchema, AdminRoleSchema,
                              AdminUserSchema, AdminStudentSchema, AdminOfficerSchema,
                              Dial, DialSchema, Grade,
                              GradeSchema, Message, MessageSchema,
                              Notification, NotificationSchema, Officer,
                              OfficerSchema, RoleSchema, Student,
                              StudentSchema, User, UserDetails, Friend, FriendSchema,
                              UserDetailsSchema, UserRoles, UserSchema, TypeSchema, db, ma)

user_api_bp = Blueprint('user_api', __name__)

student_schema = StudentSchema()
officer_schema = OfficerSchema()
user_schema = UserSchema()

type_schema = TypeSchema()

admin_user_schema = AdminUserSchema()
admin_student_schema = StudentSchema()
admin_officer_schema = OfficerSchema()

dial_schema = DialSchema()
role_schema = RoleSchema()
grade_schema = GradeSchema()
message_schema = MessageSchema()
notif_schema = NotificationSchema()
details_schema = UserDetailsSchema()

admin_message_schema = AdminMessageSchema()
admin_role_schema = AdminRoleSchema()

friend_schema = FriendSchema()

user_api = Api(user_api_bp)


def get_admins():
    return UserRoles.query.filter_by(role_name='admin').all()


class UserResource(AuthRequiredResource):
    def get(self):
        user = User.query.get_or_404(g.user.id)
        if user.type == 'officer':
            user = Officer.query.get_or_404(user.id)
            result = officer_schema.dump(user)
        elif user.type == 'student':
            user = Student.query.get_or_404(user.id)
            result = student_schema.dump(user)
        # result = user_schema.dump(user)
        return result

    def patch(self):
        user = User.query.get_or_404(g.user.id)
        user_dict = request.get_json(force=True)
        if 'password' in user_dict:
            user.password = User.set_password(user_dict['password'])
        if 'email' in user_dict:
            user.email = user_dict['email']
        if user.type == 'student':
            user = Student.query.get_or_404(user.id)
            if 'group' in user_dict:
                user.group = user_dict['group']
            if 'grade' in user_dict:
                user.grade = user_dict['grade']
            dumped_user = student_schema.dump(user)
            validate_errors = student_schema.validate(dumped_user)
        elif user.type == 'officer':
            user = Officer.query.get_or_404(user.id)
            dumped_user = officer_schema.dump(user)
            validate_errors = officer_schema.validate(dumped_user)

        # dumped_user = user_schema.dump(user)
        # validate_errors = user_schema.validate(dumped_user)

        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            user.update()
            return self.get()
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class UserListResource(Resource):
    @token_auth.login_required
    @roles_required('admin')
    def get(self):
        # if 'type' not in request.args:
        #     response = {'user': 'you have to specify type query param'}
        #     return response, status.HTTP_400_BAD_REQUEST
        query = User.query
        schema = admin_user_schema
        if 'type' in request.args:
            errors = type_schema.validate(request.args)
            if errors:
                return errors, status.HTTP_400_BAD_REQUEST
            type = request.args['type']
            if type == 'officer':
                query = Officer.query
                schema = officer_schema
            elif type == 'student':
                query = Student.query
                schema = student_schema
        pagination_helper = PaginationHelper(
            request,
            query=query,
            resource_for_url='user_api.userlistresource',
            key_name='results',
            schema=schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self):
        request_dict = request.get_json(force=True)
        # if not request_dict:
        #     response = {'user': 'No input data provided'}
        #     return response, status.HTTP_400_BAD_REQUEST
        # errors = user_schema.validate(request_dict)
        errors = {}
        if 'type' not in request_dict:
            errors.update({'type': ["Missing data for required field."]})
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        type = request_dict['type']
        if type == 'officer':
            errors.update(officer_schema.validate(request_dict))
        elif type == 'student':
            errors.update(student_schema.validate(request_dict))
        # errors.update(user_schema.validate(request_dict))
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        username = request_dict['username']
        password = request_dict['password']
        email = request_dict['email']
        existing_username = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        if existing_username or existing_email:
            response = {'user': 'An user with the same username or email already exists'}
            return response, status.HTTP_409_CONFLICT
        try:
            if type == 'officer':
                officer = Officer(username=username, password=password, email=email, type=type)
                officer.add(officer)
                query = Officer.query.get(officer.id)
                result = officer_schema.dump(query)
            elif type == 'student':
                student = Student(username=username, email=email, password=password, type=type, group=request_dict['group'], grade=request_dict['grade'])
                student.add(student)
                query = Student.query.get(student.id)
                result = student_schema.dump(query)
            # user = User(username=username, password=password, email=email, type=type)
            # user.add(user)
            # query = User.query.get(user.id)
            # result = user_schema.dump(query)
            if type == 'officer':
                for admin in get_admins():
                    message = Message(subject='new user created', text='set roles for user: {}'.format(officer.id), user_id=admin.user_id)
                    message.add(message)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class UserDetailsResource(AuthRequiredResource):
    def get(self):
        details = UserDetails.query.filter_by(user_id=g.user.id).first()
        result = details_schema.dump(details)
        return result

    def post(self):
        user_id = g.user.id
        request_dict = request.get_json(force=True)
        User.query.get_or_404(user_id)
        if not request_dict:
            response = {'details': 'No input data provided'}
            return response, status.HTTP_400_BAD_REQUEST
        errors = details_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        if UserDetails.details_exists(user_id):
            response = {'error': 'A user details already exists'}
            return response, status.HTTP_400_BAD_REQUEST
        try:
            # create a new UserDetails
            details = UserDetails(user_id=user_id, kwargs=request_dict)
            details.add(details)
            query = UserDetails.query.filter_by(user_id=details.user_id).first()
            result = details_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def patch(self):
        details = UserDetails.query.filter_by(user_id=g.user.id).first()
        # details is for current user or not
        details_dict = request.get_json(force=True)
        if 'firstname' in details_dict:
            details.firstname = details_dict['firstname']
        if 'lastname' in details_dict:
            details.lastname = details_dict['lastname']
        if 'birthdate' in details_dict:
            details.birthdate = details_dict['birthdate']
        if 'nat_id' in details_dict:
            details.nat_id = details_dict['nat_id']
        if 'fathername' in details_dict:
            details.fathername = details_dict['fathername']
        if 'user_pic' in details_dict:
            details.user_pic = details_dict['user_pic']
        if 'nat_pic' in details_dict:
            details.nat_pic = details_dict['nat_pic']
        if 'birth_certificate_pic' in details_dict:
            details.birth_certificate_pic = details_dict['birth_certificate_pic']

        dumped_details = details_schema.dump(details)
        validate_errors = details_schema.validate(dumped_details)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            details.update()
            query = UserDetails.query.filter_by(user_id=details.user_id).first()
            result = details_schema.dump(query)
            return result
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class DialResource(AuthRequiredResource):
    def get(self, dial_id):
        dial = Dial.query.get_or_404(dial_id)
        result = dial_schema.dump(dial)
        return result

    def patch(self, dial_id):
        dial = Dial.query.get_or_404(dial_id)
        dial_dict = request.get_json(force=True)
        if 'number' in dial_dict:
            dial.number = dial_dict['number']
        if 'type' in dial_dict:
            dial.type = dial_dict['type']
        dumped_dial = dial_schema.dump(dial)
        validate_errors = dial_schema.validate(dumped_dial)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            dial.update()
            return self.get(dial_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, dial_id):
        dial = Dial.query.get_or_404(dial_id)
        try:
            dial.delete(dial)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class DialListResource(AuthRequiredResource):
    def get(self):
        user_id = g.user.id
        User.query.get_or_404(user_id)
        pagination_helper = PaginationHelper(
            request,
            query=Dial.query.filter_by(user_id=user_id),
            resource_for_url='user_api.diallistresource',
            key_name='results',
            schema=dial_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self):
        user_id = g.user.id
        request_dict = request.get_json(force=True)
        User.query.get_or_404(user_id)
        # if not request_dict:
        #     response = {'dial': 'No input data provided'}
        #     return response, status.HTTP_400_BAD_REQUEST
        errors = dial_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST

        number = request_dict['number']
        if not Dial.is_unique(user_id, number):
            response = {'error': 'A dial with the same number already exists'}
            return response, status.HTTP_409_CONFLICT
        try:
            # create a new Dial
            dial = Dial(
                number=number,
                type=request_dict['type'],
                user_id=user_id)
            dial.add(dial)
            query = Dial.query.get(dial.id)
            result = dial_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class GradeResource(AuthRequiredResource):
    def get(self, grade_id):
        grade = Grade.query.get_or_404(grade_id)
        result = grade_schema.dump(grade)
        return result

    def patch(self, grade_id):
        grade = Grade.query.get_or_404(grade_id)
        grade_dict = request.get_json(force=True)
        if 'major' in grade_dict:
            grade.major = grade_dict['major']
        if 'college' in grade_dict:
            grade.college = grade_dict['college']
        if 'degree' in grade_dict:
            grade.degree = grade_dict['degree']
        if 'pic' in grade_dict:
            grade.pic = grade_dict['pic']
        dumped_grade = grade_schema.dump(grade)
        validate_errors = grade_schema.validate(dumped_grade)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            grade.update()
            return self.get(grade_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, grade_id):
        grade = Grade.query.get_or_404(grade_id)
        try:
            grade.delete(grade)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class GradeListResource(AuthRequiredResource):
    def get(self):
        user_id = g.user.id
        User.query.get_or_404(user_id)
        pagination_helper = PaginationHelper(
            request,
            query=Grade.query.filter_by(user_id=user_id),
            resource_for_url='user_api.gradelistresource',
            key_name='results',
            schema=grade_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self):
        user_id = g.user.id
        request_dict = request.get_json(force=True)
        user = User.query.get_or_404(user_id)
        # if not request_dict:
        #     response = {'grade': 'No input data provided'}
        #     return response, status.HTTP_400_BAD_REQUEST
        errors = grade_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST

        major = request_dict['major']
        degree = request_dict['degree']
        if not Grade.is_unique(user_id, major, degree):
            response = {'error': 'A grade with the same major and degree already exists'}
            return response, status.HTTP_400_BAD_REQUEST
        try:
            # create a new Grade
            grade = Grade(
                major=major,
                college=request_dict['college'],
                degree=degree,
                user_id=user_id)
            grade.add(grade)
            query = Grade.query.get(grade.id)
            result = grade_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class RoleListResource(AuthRequiredResource):
    def get(self):
        pagination_helper = PaginationHelper(
            request,
            query=UserRoles.query.filter_by(user_id=g.user.id),
            resource_for_url='user_api.rolelistresource',
            key_name='results',
            schema=role_schema)
        result = pagination_helper.paginate_query()
        return result

class AdminRoleResource(AdminAuthRequiredResource):
    def delete(self, user_id, role_id):
        role = UserRoles.query.get_or_404(role_id)
        try:
            role.delete(role)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class AdminRoleListResource(AuthRequiredResource):
    def get(self, user_id):
        # if 'user_id' not in request.args:
        #     response = {'role': 'you have to specify user_id query param'}
        #     return response, status.HTTP_400_BAD_REQUEST
        # request_dict = request.args
        # if not request_dict:
        #     response = {'role': 'you have to specify role_name query param'}
        #     return response, status.HTTP_400_BAD_REQUEST
        # errors = role_schema.validate(request_dict)
        # if errors:
        #     return errors, status.HTTP_400_BAD_REQUEST
        # role_name = request_dict['role_name']
        pagination_helper = PaginationHelper(
            request,
            query=UserRoles.query.filter_by(user_id=user_id),
            resource_for_url='user_api.adminrolelistresource',
            key_name='results',
            schema=admin_role_schema)
        result = pagination_helper.paginate_query()
        return result
    
    def post(self, user_id):
        # if User.query.get_or_404(user_id).type == 'student':
        #     response = {'roles': 'students are not allowed to have more access!'}
        #     return response, status.HTTP_403_FORBIDDEN
        
        request_dict = request.get_json(force=True)
        if not request_dict:
            response = {'role': 'No input data provided'}
            return response, status.HTTP_400_BAD_REQUEST

        errors = role_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        role_name = request_dict['role_name']
        if not UserRoles.is_unique(user_id, role_name):
            response = {'error': 'A role with the same role_name already exists'}
            return response, status.HTTP_400_BAD_REQUEST
        try:
            # create a new UserRole
            role = UserRoles(
                role_name=request_dict['role_name'],
                user_id=user_id)
            role.add(role)
            query = UserRoles.query.filter_by(role_name=role.role_name, user_id=user_id).first()
            result = admin_role_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class MessageListResource(AuthRequiredResource):
    def get(self):
        query = Message.query.filter_by(user_id=g.user.id)
        if 'filter' in request.args:
            if request.args['filter'] in ['read', 'unread']:
                query = Message.query.filter_by(user_id=g.user.id, read=True if request.args['filter']=='read' else False)
            else:
                return {'error': 'filter choices: read, unread'}, status.HTTP_400_BAD_REQUEST
        pagination_helper = PaginationHelper(
            request,
            query=query,
            resource_for_url='user_api.messagelistresource',
            key_name='results',
            schema=message_schema)
        result = pagination_helper.paginate_query()
        for message in query:
            if not message.read:
                message.read = True
                message.update()
        return result

class AdminMessageResource(AdminAuthRequiredResource):
    def patch(self, user_id, message_id):
        message = Message.query.get_or_404(message_id)
        # notif is for current user or not
        # user_notif_auth_fail(notif)
        message_dict = request.get_json(force=True)
        if 'text' in message_dict:
            message.text = message_dict['text']
        if 'subject' in message_dict:
            message.subject = message_dict['subject']
        dumped_message = message_schema.dump(message)
        validate_errors = message_schema.validate(dumped_message)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            message.update()
            query = Message.query.get_or_404(message_id)
            result = message_schema.dump(query)
            return result
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, user_id, message_id):
        message = Message.query.get_or_404(message_id)
        try:
            message.delete(message)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class AdminMessageListResource(AdminAuthRequiredResource):
    def post(self, user_id):
        request_dict = request.get_json(force=True)
        if not request_dict:
            response = {'messages': 'No input data provided'}
            return response, status.HTTP_400_BAD_REQUEST

        errors = message_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        try:
            # create a new UserNotif
            message = Message(user_id=user_id, subject=request_dict['subject'], text=request_dict['text'])
            message.add(message)
            # notification = Notification(message_id=message.id)
            # notification.add(notification)
            query = Message.query.get_or_404(message.id)
            result = admin_message_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class AdminUserResource(AdminAuthRequiredResource):
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        if user.type == 'officer':
            user = Officer.query.get_or_404(user_id)
            result = admin_officer_schema.dump(user)
        elif user.type == 'student':
            user = Student.query.get_or_404(user_id)
            result = admin_student_schema.dump(user)
        # result = admin_user_schema.dump(user)
        return result

    def patch(self, user_id):
        user = User.query.get_or_404(user_id)
        request_dict = request.get_json(force=True)
        dumped_user = user_schema.dump(user)
        validate_errors = user_schema.validate(dumped_user)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST

        try:
            if user.type == 'officer':
                if request_dict['type'] == 'student':
                    of = Officer.query.get_or_404(user_id)
                    of.delete(of)
                    st = Student(of.username, of.password, of.email, 'student', '0', '0')

            elif user.type == 'officer':
                st = Student.query.get_or_404(user_id)
                st.delete(st)
            user.update()
            
            return self.get(user_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    
    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        try:
            # if user.type == 'student':
            #     st = Student.query.get_or_404(user_id)
            #     st.delete(st)
            # elif user.type == 'officer':
            #     of = Officer.query.get_or_404(user_id)
            #     of.delete(of)
            user.delete(user)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class FriendListResource(AuthRequiredResource):
    def get(self, user_id):
        pagination_helper = PaginationHelper(
            request,
            query=Friend.query.filter_by(user_id=user_id),
            resource_for_url='user_api.friendlistresource',
            key_name='results',
            schema=friend_schema)
        result = pagination_helper.paginate_query()
        return result
    
    def post(self, user_id):
        request_dict = request.get_json(force=True)
        if not request_dict:
            response = {'friend': 'No input data provided'}
            return response, status.HTTP_400_BAD_REQUEST

        errors = friend_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        friend_id = request_dict['friend_id']
        if not Friend.is_unique(user_id, friend_id):
            response = {'error': 'A friend with the same id already exists'}
            return response, status.HTTP_400_BAD_REQUEST
        try:
            # create a new UserRole
            friend = Friend(
                friend_id=friend_id,
                user_id=user_id)
            friend.add(friend)
            query = Friend.query.filter_by(user_id=user_id, friend_id=friend_id).first()
            result = friend_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class FriendResource(AuthRequiredResource):
    def delete(self, user_id, friend_id):
        friend = Friend.query.filter_by(user_id=user_id, friend_id=friend_id).first()
        try:
            friend.delete(friend)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST


user_api.add_resource(UserListResource, '/users')
user_api.add_resource(UserResource, '/users/self')
user_api.add_resource(UserDetailsResource, '/users/self/details')

user_api.add_resource(DialListResource, '/users/self/dials')
user_api.add_resource(DialResource, '/users/self/dials/<int:dial_id>')

user_api.add_resource(GradeListResource, '/users/self/grades')
user_api.add_resource(GradeResource, '/users/self/grades/<int:grade_id>')

user_api.add_resource(RoleListResource, '/users/self/roles')

user_api.add_resource(MessageListResource, '/users/self/messages')

user_api.add_resource(AdminUserResource, '/users/<int:user_id>')

user_api.add_resource(AdminRoleListResource, '/users/<int:user_id>/roles')
user_api.add_resource(AdminRoleResource, '/users/<int:user_id>/roles/<int:role_id>')

user_api.add_resource(AdminMessageListResource, '/users/<int:user_id>/messages')
user_api.add_resource(AdminMessageResource, '/users/<int:user_id>/messages/<int:message_id>')

user_api.add_resource(FriendListResource, '/users/<int:user_id>/friends')
user_api.add_resource(FriendResource, '/users/<int:user_id>/friends/<int:friend_id>')