from flask import Blueprint, request, jsonify, make_response
from flask_restful import Api, Resource, abort
from sqlalchemy.exc import SQLAlchemyError
from marshmallow.exceptions import ValidationError

import status
from flask_httpauth import HTTPBasicAuth
from flask import g

from models.UserModel import db
from models.FormModel import Form, FormSchema

from helpers import PaginationHelper
from auth import FormAuthRequiredResource, basic_auth, roles_required, token_auth


form_api_bp = Blueprint('form_api', __name__)
form_api = Api(form_api_bp)

form_schema = FormSchema()

class FormListResource(FormAuthRequiredResource):
    def get(self):
        pagination_helper = PaginationHelper(
            request,
            query=Form.query,
            resource_for_url='form_api.formlistresource',
            key_name='results',
            schema=form_schema)
        result = pagination_helper.paginate_query()
        return result
    
    def post(self):
        request_dict = request.get_json(force=True)
        errors = form_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        try:
            form = Form(code=request_dict['code'], topic=request_dict['topic'], file_path=request_dict['file_path'])
            form.add(form)
            query = Form.query.get(form.id)
            result = form_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class FormResource(FormAuthRequiredResource):
    def get(self, form_id):
        form = Form.query.get_or_404(form_id)
        result = form_schema.dump(form)
        return result

    def patch(self, form_id):
        form = Form.query.get_or_404(form_id)
        form_dict = request.get_json(force=True)
        if 'code' in form_dict:
            form.code = form_dict['code']
        if 'topic' in form_dict:
            form.topic = form_dict['topic']
        if 'file_path' in form_dict:
            form.file_path = form_dict['file_path']
        try:
            form_schema.load(form_dict, partial=True)
        except ValidationError as e:
            return e.args[0], status.HTTP_400_BAD_REQUEST
        try:
            form.update()
            return self.get(form_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, form_id):
        form = Form.query.get_or_404(form_id)
        try:
            form.delete(form)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST


form_api.add_resource(FormListResource, '/forms')
form_api.add_resource(FormResource, '/forms/<int:form_id>')