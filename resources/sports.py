from flask import Blueprint, g, jsonify, make_response, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, Resource, abort
from sqlalchemy.exc import SQLAlchemyError
from marshmallow.exceptions import ValidationError

import status
from auth import (SportAuthRequiredResource, basic_auth,
                  roles_required, token_auth)
from helpers import PaginationHelper
from models.SportModel import Sport, SportSchema, SportUsers, SportUsersSchema
from models.UserModel import Message, User, db

sport_api_bp = Blueprint('sport_api', __name__)

sport_api = Api(sport_api_bp)


sport_schema = SportSchema()
sport_users_schema = SportUsersSchema()


class SportListResource(SportAuthRequiredResource):
    def get(self):
        pagination_helper = PaginationHelper(
            request,
            query=Sport.query,
            resource_for_url='sport_api.sportlistresource',
            key_name='results',
            schema=sport_schema)
        result = pagination_helper.paginate_query()
        return result
    
    def post(self):
        request_dict = request.get_json(force=True)
        errors = sport_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        try:
            sport = Sport(type=request_dict['type'], datetime=request_dict['datetime'], venue=request_dict['venue'])
            sport.add(sport)
            query = Sport.query.get(sport.id)
            result = sport_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class SportResource(SportAuthRequiredResource):
    def get(self, sport_id):
        sport = Sport.query.get_or_404(sport_id)
        result = sport_schema.dump(sport)
        return result

    def patch(self, sport_id):
        sport = Sport.query.get_or_404(sport_id)
        sport_dict = request.get_json(force=True)
        if 'type' in sport_dict:
            sport.type = sport_dict['type']
        if 'datetime' in sport_dict:
            sport.datetime = sport_dict['subject']
        if 'venue' in sport_dict:
            sport.venue = sport_dict['venue']
        try:
            sport_schema.load(sport_dict, partial=True)
        except ValidationError as e:
            return e.args[0], status.HTTP_400_BAD_REQUEST
        try:
            sport.update()
            return self.get(sport_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, sport_id):
        sport = Sport.query.get_or_404(sport_id)
        try:
            sport.delete(sport)
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class SportUsersListResource(SportAuthRequiredResource):
    def get(self, sport_id):
        pagination_helper = PaginationHelper(
            request,
            query=SportUsers.query.filter_by(sport_id=sport_id),
            resource_for_url='sport_api.sportuserslistresource',
            key_name='results',
            schema=sport_users_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, sport_id):
        request_dict = request.get_json(force=True)
        Sport.query.get_or_404(sport_id)
        errors = sport_users_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        user_id = request_dict['user_id']
        User.query.get_or_404(user_id)
        present = False
        description = None
        rate = None
        if 'present' in request_dict:
            present = request_dict['present']
        if 'description' in request_dict:
            description = request_dict['description']
        if 'rate' in request_dict:
            rate = request_dict['rate']
        try:
            sport_users = SportUsers(user_id=user_id, sport_id=sport_id, present=present, description=description, rate=rate)
            sport_users.add(sport_users)
            query = SportUsers.query.filter_by(user_id=user_id, sport_id=sport_id).first()
            result = sport_users_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST
    
class SportUsersResource(SportAuthRequiredResource):
    def get(self, user_id, sport_id):
        sport_users = SportUsers.query.filiter_by(sport_id=sport_id, user_id=user_id).first()
        result = sport_users_schema.dump(sport_users)
        return result

    def patch(self, user_id, sport_id):
        sport_users = SportUsers.query.filter_by(sport_id=sport_id, user_id=user_id).first()
        sport_users_dict = request.get_json(force=True)
        if 'present' in sport_users_dict:
            sport_users.present = sport_users_dict['present']
        if 'rate' in sport_users_dict:
            sport_users.rate = sport_users_dict['rate']
        if 'description' in sport_users_dict:
            sport_users.description = sport_users_dict['description']
        try:
            sport_users_schema.load(sport_users_dict, partial=True)
        except ValidationError as e:
            return e.args[0], status.HTTP_400_BAD_REQUEST
        try:
            sport_users.update()
            return self.get(user_id, sport_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, user_id, sport_id):
        sport_users = SportUsers.query.filter_by(sport_id=sport_id, user_id=user_id).first()
        try:
            sport_users.delete(sport_users)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST


sport_api.add_resource(SportListResource, '/sports')
sport_api.add_resource(SportResource, '/sports/<int:sport_id>')

sport_api.add_resource(SportUsersListResource, '/sports/<int:sport_id>/users')
sport_api.add_resource(SportUsersResource, '/sports/<int:sport_id>/users/<int:user_id>')
