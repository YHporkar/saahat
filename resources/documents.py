from flask import Blueprint, g, jsonify, make_response, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, Resource, abort
from sqlalchemy.exc import SQLAlchemyError
from marshmallow.exceptions import ValidationError

import status
from auth import (DocumentAuthRequiredResource, basic_auth,
                  roles_required, token_auth)
from helpers import PaginationHelper
from models.UserModel import db
from models.DocumentModel import Document, Voice, Book, Booklet, Category
from models.DocumentModel import DocumentSchema, VoiceSchema, BookSchema, BookletSchema, TypeSchema, CategorySchema


document_api_bp = Blueprint('document_api', __name__)
document_api = Api(document_api_bp)

document_schema = DocumentSchema()
voice_schema = VoiceSchema()
book_schema = BookSchema()
booklet_schema = BookletSchema()

type_schema = TypeSchema()
category_schema = CategorySchema()

class CategoryListResource(DocumentAuthRequiredResource):
    def get(self):
        pagination_helper = PaginationHelper(
            request,
            query=Category.query,
            resource_for_url='category_api.categorylistresource',
            key_name='results',
            schema=category_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self):
        request_dict = request.get_json(force=True)
        errors = category_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        try:
            category = Category(name=request_dict['name'])
            category.add(category)
            query = Category.query.get(category.id)
            result = category_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class CategoryResource(DocumentAuthRequiredResource):
    def patch(self, category_id):
        category = Category.query.get_or_404(category_id)
        category_dict = request.get_json(force=True)
        if 'name' in category_dict:
            category.name = category_dict['name']
        try:
            category_schema.load(category_dict, partial=True)
        except ValidationError as e:
            return e.args[0], status.HTTP_400_BAD_REQUEST
        try:
            category.update()
            return self.get(category_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, category_id):
        category = Category.query.get_or_404(category_id)
        try:
            category.delete(category)
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class DocumentListResource(DocumentAuthRequiredResource):
    def get(self, category_id):
        request_params = request.args
        errors = type_schema.validate(request_params, partial=True)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        if 'type' in request_params:
            type = request_params['type']       
            if type == 'book':
                query = Book.query.filter_by(category_id=category_id)
                schema = book_schema
            elif type == 'booklet':
                query = Booklet.query.filter_by(category_id=category_id)
                schema = booklet_schema
            elif type == 'voice':
                query = Voice.query.filter_by(category_id=category_id)
                schema = voice_schema
        else:
            query = Document.query.filter_by(category_id=category_id)
            schema = document_schema
        pagination_helper = PaginationHelper(
            request,
            query=query,
            resource_for_url='document_api.documentlistresource',
            key_name='results',
            schema=schema)
        result = pagination_helper.paginate_query()
        return result
    
    def post(self, category_id):
        request_params = request.args
        errors = type_schema.validate(request_params)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        type = request_params['type']
        request_dict = request.get_json(force=True)
        if type == 'book':
            errors = book_schema.validate(request_dict)
        elif type == 'booklet':
            errors = booklet_schema.validate(request_dict)
        elif type == 'voice':
            errors = voice_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        subject = None
        level = None
        if 'subject' in request_dict:
            subject = request_dict['subject']
        if 'level' in request_dict:
            level = request_dict['level']
        if type == 'book':
            translator = None
            if 'translator' in request_dict:
                translator = request_dict['translator']
                document = Book(category_id=category_id, topic=request_dict['topic'], file_path=request_dict['file_path'],
                                subject=subject, level=level, author=request_dict['author'],
                                publish_date=request_dict['publish_date'], translator=translator)
        elif type == 'voice':
            document = Voice(category_id=category_id, topic=request_dict['topic'], file_path=request_dict['file_path'],
                             subject=subject, level=level, speaker=request_dict['speaker'],
                             production_date=request_dict['production_date'])
        elif type == 'booklet':
            document = Booklet(category_id=category_id, topic=request_dict['topic'], file_path=request_dict['file_path'],
                               subject=subject, level=level, author=request_dict['author'], production_date=request_dict['production_date'])
        try:
            document.add(document)
            if type == 'book':
                query = Book.query.get(document.id)
                result = book_schema.dump(query)
            elif type == 'voice':
                query = Voice.query.get(document.id)
                result = voice_schema.dump(query)
            elif type == 'booklet':
                query = Booklet.query.get(document.id)
                result = booklet_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class DocumentResource(DocumentAuthRequiredResource):
    def get(self, category_id, document_id):
        document = Document.query.get_or_404(document_id)
        if document.type == 'book':
            document = Book.query.get_or_404(document_id)
            result = book_schema.dump(document)
        elif document.type == 'voice':
            document = Voice.query.get_or_404(document_id)
            result = voice_schema.dump(document)
        elif document.type == 'booklet':
            document = Booklet.query.get_or_404(document_id)
            result = booklet_schema.dump(document)
        return result

    def patch(self, category_id, document_id):
        document = Document.query.get_or_404(document_id)
        document_dict = request.get_json(force=True)
        try:
            if document.type == 'book':
                document = Book.query.get_or_404(document_id)
                book_schema.load(document_dict, partial=True)
                if 'author' in document_dict:
                    document.author = document_dict['author']
                if 'publish_date' in document_dict:
                    document.publish_date = document_dict['publish_date']
                if 'translator' in document_dict:
                    document.translator = document_dict['translator']
            elif document.type == 'voice':
                document = Voice.query.get_or_404(document_id)
                voice_schema.load(document_dict, partial=True)
                if 'speaker' in document_dict:
                    document.speaker = document_dict['speaker']
                if 'production_date' in document_dict:
                    document.production_date = document_dict['production_date']
            elif document.type == 'booklet':
                document = Booklet.query.get_or_404(document_id)
                booklet_schema.load(document_dict, partial=True)
                if 'author' in document_dict:
                    document.author = document_dict['author']
                if 'production_date' in document_dict:
                    document.production_date = document_dict['production_date']
        except ValidationError as e:
            return e.args[0], status.HTTP_400_BAD_REQUEST
        if 'topic' in document_dict:
            document.topic = document_dict['topic']
        if 'subject' in document_dict:
            document.subject = document_dict['subject']
        if 'file_path' in document_dict:
            document.file_path = document_dict['file_path']
        if 'level' in document_dict:
            document.level = document_dict['level']
        if 'category_id' in document_dict:
            document.category_id = document_dict['category_id']
        try:
            document.update()
            return self.get(document_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, category_id, document_id):
        document = Document.query.get_or_404(document_id)
        try:
            document.delete(document)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST


document_api.add_resource(CategoryListResource, '/category')
document_api.add_resource(CategoryResource, '/category/<int:category_id>')

document_api.add_resource(DocumentListResource, '/category/<int:category_id>/documents')
document_api.add_resource(DocumentResource, '/category/<int:category_id>/documents/<int:document_id>')