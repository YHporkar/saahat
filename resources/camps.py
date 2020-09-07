from flask import Blueprint, request, jsonify, make_response
from flask_restful import Api, Resource, abort
from sqlalchemy.exc import SQLAlchemyError
import status
from flask_httpauth import HTTPBasicAuth
from flask import g

from models.UserModel import db, Message, User
from models.CampModel import Camp, UserPayments
from models.CampModel import CampSchema, UserPaymentSchema

from helpers import PaginationHelper
from auth import CampAuthRequiredResource, basic_auth, roles_required, access_denied, token_auth


camp_api_bp = Blueprint('camp_api', __name__)
camp_api = Api(camp_api_bp)


camp_schema = CampSchema()
user_payments_schema = UserPaymentSchema()


class CampListResource(CampAuthRequiredResource):
    def get(self):
        pagination_helper = PaginationHelper(
            request,
            query=Camp.query,
            resource_for_url='camp_api.camplistresource',
            key_name='results',
            schema=camp_schema)
        result = pagination_helper.paginate_query()
        return result
    
    def post(self):
        request_dict = request.get_json(force=True)
        errors = camp_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        go_time = None
        back_time = None
        if 'go_time' in request_dict:
            go_time = request_dict['go_time']
        if 'back_time' in request_dict:
            back_time = request_dict['back_time']
        try:
            camp = Camp(subject=request_dict['subject'], location=request_dict['location'], go_time=go_time, back_time=back_time, cost_per_person=request_dict['cost_per_person'])
            camp.add(camp)
            query = Camp.query.get(camp.id)
            result = camp_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class CampResource(CampAuthRequiredResource):
    def get(self, camp_id):
        camp = Camp.query.get_or_404(camp_id)
        result = camp_schema.dump(camp)
        return result

    def patch(self, camp_id):
        camp = Camp.query.get_or_404(camp_id)
        # camp is for current user or not
        # user_camp_auth_fail(camp)
        camp_dict = request.get_json(force=True)
        if 'location' in camp_dict:
            camp.location = camp_dict['location']
        if 'subject' in camp_dict:
            camp.subject = camp_dict['subject']
        if 'back_time' in camp_dict:
            camp.back_time = camp_dict['back_time']
        if 'go_time' in camp_dict:
            camp.go_time = camp_dict['go_time']
        if 'cost_per_person' in camp_dict:
            camp.cost_per_person = camp_dict['cost_per_person']
        dumped_camp = camp_schema.dump(camp)
        validate_errors = camp_schema.validate(dumped_camp)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            camp.update()
            return self.get(camp_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, camp_id):
        camp = Camp.query.get_or_404(camp_id)
        try:
            camp.delete(camp)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class UserPaymentsListResource(CampAuthRequiredResource):
    def get(self, camp_id):
        pagination_helper = PaginationHelper(
            request,
            query=UserPayments.query.filter_by(camp_id=camp_id),
            resource_for_url='camp_api.userpaymentslistresource',
            key_name='results',
            schema=user_payments_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, camp_id):
        request_dict = request.get_json(force=True)
        Camp.query.get_or_404(camp_id)
        errors = user_payments_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        user_id = request_dict['user_id']
        User.query.get_or_404(user_id)
        if 'paid_value' in request_dict:
            paid_value = request_dict['paid_value']
        else:
            paid_value = 0
        try:
            user_payments = UserPayments(user_id=user_id, camp_id=camp_id, paid_value=paid_value)
            user_payments.add(user_payments)
            query = UserPayments.query.filter_by(user_id=user_id, camp_id=camp_id).first()
            result = user_payments_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST
    
class UserPaymentsResource(CampAuthRequiredResource):
    def get(self, user_id, camp_id):
        user_payments = UserPayments.query.filiter_by(camp_id=camp_id, user_id=user_id).first()
        result = user_payments_schema.dump(user_payments)
        return result

    def patch(self, user_id, camp_id):
        user_payments = UserPayments.query.filter_by(camp_id=camp_id, user_id=user_id).first()
        user_payments_dict = request.get_json(force=True)
        if 'paid_value' in user_payments_dict:
            user_payments.paid_value = user_payments_dict['paid_value']
        dumped_user_payments = user_payments_schema.dump(user_payments)
        validate_errors = user_payments_schema.validate(dumped_user_payments)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            user_payments.update()
            return self.get(user_id, camp_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, user_id, camp_id):
        user_payments = UserPayments.query.filter_by(camp_id=camp_id, user_id=user_id).first()
        try:
            user_payments.delete(user_payments)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST


camp_api.add_resource(CampListResource, '/camps')
camp_api.add_resource(CampResource, '/camps/<int:camp_id>')

camp_api.add_resource(UserPaymentsListResource, '/camps/<int:camp_id>/users')
camp_api.add_resource(UserPaymentsResource, '/camps/<int:camp_id>/users/<int:user_id>')