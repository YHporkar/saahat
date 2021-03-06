from flask import Blueprint, g, jsonify, make_response, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, Resource, abort
from sqlalchemy.exc import SQLAlchemyError
from marshmallow.exceptions import ValidationError

import status
from auth import (HeyatAuthRequiredResource, basic_auth,
                  roles_required, token_auth)
from helpers import PaginationHelper
from models.HeyatModel import Heyat, HeyatSchema, HeyatUsers, HeyatUsersSchema
from models.UserModel import Message, User, db

heyat_api_bp = Blueprint('heyat_api', __name__)

heyat_api = Api(heyat_api_bp)


heyat_schema = HeyatSchema()
heyat_users_schema = HeyatUsersSchema()


class HeyatListResource(HeyatAuthRequiredResource):
    def get(self):
        pagination_helper = PaginationHelper(
            request,
            query=Heyat.query,
            resource_for_url='heyat_api.heyatlistresource',
            key_name='results',
            schema=heyat_schema)
        result = pagination_helper.paginate_query()
        return result
    
    def post(self):
        request_dict = request.get_json(force=True)
        errors = heyat_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        compere = None
        speaker = None
        singer = None
        meal = None
        if 'compere' in request_dict:
            compere = request_dict['compere']
        if 'speaker' in request_dict:
            speaker = request_dict['speaker']
        if 'singer' in request_dict:
            singer = request_dict['singer']
        if 'meal' in request_dict:
            meal = request_dict['meal']
        try:
            heyat = Heyat(compere=compere, speaker=speaker, singer=singer, meal=meal, type=request_dict['type'], reason=request_dict['reason'], datetime=request_dict['datetime'])
            heyat.add(heyat)
            query = Heyat.query.get(heyat.id)
            result = heyat_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class HeyatResource(HeyatAuthRequiredResource):
    def get(self, heyat_id):
        heyat = Heyat.query.get_or_404(heyat_id)
        result = heyat_schema.dump(heyat)
        return result

    def patch(self, heyat_id):
        heyat = Heyat.query.get_or_404(heyat_id)
        heyat_dict = request.get_json(force=True)
        if 'compere' in heyat_dict:
            heyat.compere = heyat_dict['compere']
        if 'speaker' in heyat_dict:
            heyat.speaker = heyat_dict['speaker']
        if 'singer' in heyat_dict:
            heyat.singer = heyat_dict['singer']
        if 'meal' in heyat_dict:
            heyat.meal = heyat_dict['meal']
        if 'type' in heyat_dict:
            heyat.type = heyat_dict['type']
        if 'reason' in heyat_dict:
            heyat.reason = heyat_dict['reason']
        if 'datetime' in heyat_dict:
            heyat.datetime = heyat_dict['datetime']
        try:
            heyat_schema.load(heyat_dict, partial=True)
        except ValidationError as e:
            return e.args[0], status.HTTP_400_BAD_REQUEST
        try:
            heyat.update()
            return self.get(heyat_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, heyat_id):
        heyat = Heyat.query.get_or_404(heyat_id)
        try:
            heyat.delete(heyat)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class HeyatUsersListResource(HeyatAuthRequiredResource):
    def get(self, heyat_id):
        pagination_helper = PaginationHelper(
            request,
            query=HeyatUsers.query.filter_by(heyat_id=heyat_id),
            resource_for_url='heyat_api.heyatuserslistresource',
            key_name='results',
            schema=heyat_users_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, heyat_id):
        request_dict = request.get_json(force=True)
        Heyat.query.get_or_404(heyat_id)
        errors = heyat_users_schema.validate(request_dict)
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
            heyat_users = HeyatUsers(user_id=user_id, heyat_id=heyat_id, present=present, rate=rate, description=description)
            heyat_users.add(heyat_users)
            query = HeyatUsers.query.filter_by(user_id=user_id, heyat_id=heyat_id).first()
            result = heyat_users_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST
    
class HeyatUsersResource(HeyatAuthRequiredResource):
    def get(self, user_id, heyat_id):
        heyat_users = HeyatUsers.query.filiter_by(heyat_id=heyat_id, user_id=user_id).first()
        result = heyat_users_schema.dump(heyat_users)
        return result

    def patch(self, user_id, heyat_id):
        heyat_users = HeyatUsers.query.filter_by(heyat_id=heyat_id, user_id=user_id).first()
        heyat_users_dict = request.get_json(force=True)
        if 'present' in heyat_users_dict:
            heyat_users.present = heyat_users_dict['present']
        if 'rate' in heyat_users_dict:
            heyat_users.rate = heyat_users_dict['rate']
        if 'description' in heyat_users_dict:
            heyat_users.description = heyat_users_dict['description']
        try:
            heyat_users_schema.load(heyat_users_dict, partial=True)
        except ValidationError as e:
            return e.args[0], status.HTTP_400_BAD_REQUEST
        try:
            heyat_users.update()
            return self.get(user_id, heyat_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, user_id, heyat_id):
        heyat_users = HeyatUsers.query.filter_by(heyat_id=heyat_id, user_id=user_id).first()
        try:
            heyat_users.delete(heyat_users)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST


heyat_api.add_resource(HeyatListResource, '/heyats')
heyat_api.add_resource(HeyatResource, '/heyats/<int:heyat_id>')

heyat_api.add_resource(HeyatUsersListResource, '/heyats/<int:heyat_id>/users')
heyat_api.add_resource(HeyatUsersResource, '/heyats/<int:heyat_id>/users/<int:user_id>')
