from flask import Blueprint, g, jsonify, make_response, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, Resource, abort
from sqlalchemy.exc import SQLAlchemyError

import status
from auth import (SessionAuthRequiredResource, access_denied, basic_auth,
                  roles_required, token_auth)
from helpers import PaginationHelper
from models.SessionModel import (Deadline, DeadlineSchema, Session,
                                 SessionDetails, SessionDetailsSchema,
                                 SessionSchema, SessionUser, SessionUserSchema,
                                 Task, TaskSchema)
from models.UserModel import Message, User, db

session_api_bp = Blueprint('session_api', __name__)

session_api = Api(session_api_bp)


session_schema = SessionSchema()
details_schema = SessionDetailsSchema()
session_user_schema = SessionUserSchema()
task_schema = TaskSchema()
deadline_schema = DeadlineSchema()


class SessionListResource(SessionAuthRequiredResource):
    def get(self):
        pagination_helper = PaginationHelper(
            request,
            query=Session.query,
            resource_for_url='session_api.sessionlistresource',
            key_name='results',
            schema=session_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self):
        request_dict = request.get_json(force=True)
        errors = session_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        if 'done' in request_dict:
            done = request_dict['done']
        else:
            done = False
        try:
            session = Session(subject=request_dict['subject'], datetime=request_dict['datetime'], done=done)
            session.add(session)
            query = Session.query.get(session.id)
            result = session_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class SessionResource(SessionAuthRequiredResource):
    def get(self, session_id):
        session = Session.query.get_or_404(session_id)
        result = session_schema.dump(session)
        return result

    def patch(self, session_id):
        session = Session.query.get_or_404(session_id)
        # session is for current user or not
        # user_session_auth_fail(session)
        session_dict = request.get_json(force=True)
        if 'done' in session_dict:
            session.done = session_dict['done']
        if 'subject' in session_dict:
            session.subject = session_dict['subject']
        if 'datetime' in session_dict:
            session.datetime = session_dict['datetime']
        dumped_session = session_schema.dump(session)
        validate_errors = session_schema.validate(dumped_session)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            session.update()
            return self.get(session_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, session_id):
        session = Session.query.get_or_404(session_id)
        try:
            session.delete(session)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class SessionDetailsResource(SessionAuthRequiredResource):
    def get(self, session_id):
        details = SessionDetails.query.filter_by(session_id=session_id).first()
        result = details_schema.dump(details)
        return result

    def post(self, session_id):
        request_dict = request.get_json(force=True)
        Session.query.get_or_404(session_id)
        if not request_dict:
            response = {'details': 'No input data provided'}
            return response, status.HTTP_400_BAD_REQUEST
        errors = details_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        if SessionDetails.details_exists(session_id):
            response = {'error': 'A session details already exists'}
            return response, status.HTTP_400_BAD_REQUEST
        try:
            # create a new SessionDetails
            details = SessionDetails(session_id=session_id, kwargs=request_dict)
            details.add(details)
            query = SessionDetails.query.filter_by(session_id=details.session_id).first()
            result = details_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def patch(self, session_id):
        details = SessionDetails.query.filter_by(session_id=session_id).first()
        # details is for current user or not
        details_dict = request.get_json(force=True)
        if 'number' in details_dict:
            details.number = details_dict['number']
        if 'kind' in details_dict:
            details.kind = details_dict['kind']
        if 'location' in details_dict:
            details.location = details_dict['location']
        if 'approvals' in details_dict:
            details.approvals = details_dict['approvals']

        dumped_details = details_schema.dump(details)
        validate_errors = details_schema.validate(dumped_details)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            details.update()
            query = SessionDetails.query.filter_by(session_id=details.session_id).first()
            result = details_schema.dump(query)
            return result
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class SessionUsersListResource(SessionAuthRequiredResource):
    def get(self, session_id):
        pagination_helper = PaginationHelper(
            request,
            query=SessionUser.query.filter_by(session_id=session_id),
            resource_for_url='session_api.sessionuserslistresource',
            key_name='results',
            schema=session_user_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, session_id):
        request_dict = request.get_json(force=True)
        session = Session.query.get_or_404(session_id)
        errors = session_user_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        user_id = request_dict['user_id']
        User.query.get_or_404(user_id)
        if 'present' in request_dict:
            present = request_dict['present']
        else:
            present = False

        try:
            session_user = SessionUser(user_id=user_id, session_id=session_id, present=present)
            session_user.add(session_user)
            message = Message(subject='session invited: {}'.format(session_id), user_id=user_id, text=session.subject)
            message.add(message)
            query = SessionUser.query.filter_by(user_id=user_id, session_id=session_id).first()
            result = session_user_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class SessionUsersResource(SessionAuthRequiredResource):
    def get(self, user_id, session_id):
        session_user = SessionUser.query.filiter_by(session_id=session_id, user_id=user_id).first()
        result = session_user_schema.dump(session_user)
        return result

    def patch(self, user_id, session_id):
        session_user = SessionUser.query.filter_by(session_id=session_id, user_id=user_id).first()
        session_user_dict = request.get_json(force=True)
        if 'present' in session_user_dict:
            session_user.present = session_user_dict['present']
        dumped_session_user = session_user_schema.dump(session_user)
        validate_errors = session_user_schema.validate(dumped_session_user)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            session_user.update()
            return self.get(user_id, session_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, user_id, session_id):
        session_user = SessionUser.query.filter_by(session_id=session_id, user_id=user_id).first()
        try:
            session_user.delete(session_user)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class TaskListResource(SessionAuthRequiredResource):
    def get(self, user_id, session_id):
        pagination_helper = PaginationHelper(
            request,
            query=Task.query.filter_by(user_id=user_id, session_id=session_id),
            resource_for_url='session_api.tasklistresource',
            key_name='results',
            schema=task_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, user_id, session_id):
        Session.query.get_or_404(session_id)
        User.query.get_or_404(user_id)
        session_user = SessionUser.query.filter_by(user_id=user_id, session_id=session_id).first()
        if not session_user:
            resp = {'error': 'this user is not in this session'}
            return resp, status.HTTP_404_NOT_FOUND

        request_dict = request.get_json(force=True)
        errors = task_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        description = None
        priority = 'normal'
        if 'description' in request_dict:
            description = request_dict['description']
        if 'priority' in request_dict:
            priority = request_dict['priority']
        try:
            task = Task(user_id=user_id, session_id=session_id, subject=request_dict['subject'], description=description, priority=priority)
            task.add(task)
            message = Message(subject='your task: {}'.format(task.id), user_id=user_id, text=task.subject)
            message.add(message)
            query = Task.query.filter_by(user_id=user_id, session_id=session_id).first()
            result = task_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class TaskResource(SessionAuthRequiredResource):
    def get(self, session_id, user_id, task_id):
        task = Task.query.get_or_404(task_id)
        result = task_schema.dump(task)
        return result

    def patch(self, user_id, session_id, task_id):
        task = Task.query.get_or_404(task_id)
        task_dict = request.get_json(force=True)
        if 'present' in task_dict:
            task.present = task_dict['present']
        dumped_task = task_schema.dump(task_dict)
        validate_errors = task_schema.validate(dumped_task)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            task.update()
            return self.get(session_id, user_id, task_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, user_id, session_id, task_id):
        task = Task.query.get_or_404(task_id)
        try:
            task.delete(task)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class DeadlineListResource(SessionAuthRequiredResource):
    def get(self, session_id, user_id, task_id):
        pagination_helper = PaginationHelper(
            request,
            query=Deadline.query.filter_by(task_id=task_id),
            resource_for_url='session_api.deadlinelistresource',
            key_name='results',
            schema=deadline_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, session_id, user_id, task_id):
        Task.query.get_or_404(task_id)
        request_dict = request.get_json(force=True)
        errors = deadline_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        try:
            deadline = Deadline(task_id=task_id, expiration_datetime=request_dict['expiration_datetime'])
            deadline.add(deadline)

            query = Deadline.query.filter_by(task_id=task_id).first()
            result = deadline_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class DeadlineResource(SessionAuthRequiredResource):
    def get(self, session_id, user_id, task_id, deadline_id):
        deadline = Deadline.query.get_or_404(deadline_id)
        result = deadline_schema.dump(deadline)
        return result

    def patch(self, user_id, session_id, task_id, deadline_id):
        deadline = Deadline.query.get_or_404(deadline_id)
        deadline_dict = request.get_json(force=True)
        if 'expiration_datetime' in deadline_dict:
            deadline.expiration_datetime = deadline_dict['expiration_datetime']
        dumped_deadline = deadline_schema.dump(deadline_dict)
        validate_errors = deadline_schema.validate(dumped_deadline)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            deadline.update()
            return self.get(session_id, user_id, task_id, deadline_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, user_id, session_id, task_id, deadline_id):
        deadline = Deadline.query.get_or_404(deadline_id)
        try:
            deadline.delete(deadline)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST


session_api.add_resource(SessionListResource, '/sessions')
session_api.add_resource(SessionResource, '/sessions/<int:session_id>')

session_api.add_resource(SessionDetailsResource, '/sessions/<int:session_id>/details')

session_api.add_resource(SessionUsersListResource, '/sessions/<int:session_id>/users')
session_api.add_resource(SessionUsersResource, '/sessions/<int:session_id>/users/<int:user_id>')

session_api.add_resource(TaskListResource, '/sessions/<int:session_id>/users/<int:user_id>/tasks')
session_api.add_resource(TaskResource, '/sessions/<int:session_id>/users/<int:user_id>/tasks/<int:task_id>')

session_api.add_resource(DeadlineListResource, '/sessions/<int:session_id>/users/<int:user_id>/tasks/<int:task_id>/deadlines')
session_api.add_resource(DeadlineResource, '/sessions/<int:session_id>/users/<int:user_id>/tasks/<int:task_id>/deadlines/<int:deadline_id>')
