from flask import Blueprint, request, jsonify, make_response
from flask_restful import Api, Resource, abort
from sqlalchemy.exc import SQLAlchemyError
from marshmallow.exceptions import ValidationError

import status
from flask_httpauth import HTTPBasicAuth
from flask import g

from models.UserModel import db
from models.AccountingModel import Expense, ExpenseSchema

from helpers import PaginationHelper
from auth import ExpenseAuthRequiredResource, basic_auth, roles_required, token_auth


accounting_api_bp = Blueprint('accounting_api', __name__)
accounting_api = Api(accounting_api_bp)

expense_schema = ExpenseSchema()

class ExpenseListResource(ExpenseAuthRequiredResource):
    def get(self):
        pagination_helper = PaginationHelper(
            request,
            query=Expense.query,
            resource_for_url='accounting_api.expenselistresource',
            key_name='results',
            schema=expense_schema)
        result = pagination_helper.paginate_query()
        return result
    
    def post(self):
        request_dict = request.get_json(force=True)
        errors = expense_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        description = None
        if 'description' in request_dict:
            description = request_dict['description']
        try:
            expense = Expense(topic=request_dict['topic'], invoice=request_dict['invoice'], description=description, cost=request_dict['cost'],
                            date=request_dict['date'], user_id=g.user.id, state=request_dict['state'], owner=request_dict['owner'])
            expense.add(expense)
            query = Expense.query.get(expense.id)
            result = expense_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class ExpenseResource(ExpenseAuthRequiredResource):
    def get(self, expense_id):
        expense = Expense.query.get_or_404(expense_id)
        result = expense_schema.dump(expense)
        return result

    def patch(self, expense_id):
        expense = Expense.query.get_or_404(expense_id)
        expense_dict = request.get_json(force=True)
        if 'invoice' in expense_dict:
            expense.invoice = expense_dict['invoice']
        if 'topic' in expense_dict:
            expense.topic = expense_dict['topic']
        if 'description' in expense_dict:
            expense.description = expense_dict['description']
        if 'cost' in expense_dict:
            expense.cost = expense_dict['cost']
        if 'date' in expense_dict:
            expense.date = expense_dict['date']
        if 'state' in expense_dict:
            expense.state = expense_dict['state']
        if 'owner' in expense_dict:
            expense.owner = expense_dict['owner']
        try:
            expense_schema.load(expense_dict, partial=True)
        except ValidationError as e:
            return e.args[0], status.HTTP_400_BAD_REQUEST
        try:
            expense.update()
            return self.get(expense_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, expense_id):
        expense = Expense.query.get_or_404(expense_id)
        try:
            expense.delete(expense)
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST


accounting_api.add_resource(ExpenseListResource, '/expenses')
accounting_api.add_resource(ExpenseResource, '/expenses/<int:expense_id>')