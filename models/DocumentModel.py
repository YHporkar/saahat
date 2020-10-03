from models.UserModel import AddUpdateDelete
from sqlalchemy_utils.types import UUIDType
import uuid

from models.UserModel import db

from marshmallow import Schema, fields, validate
from flask_marshmallow import Marshmallow

ma = Marshmallow()


class Document(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(50))
    file_path = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer)
    creation_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', back_populates='documents')

    def __init__(self, category_id, topic, file_path, subject, level, type):
        self.category_id = category_id
        self.topic = topic
        self.file_path = file_path
        self.subject = subject
        self.level = level
        self.type = type

class Book(Document):
    id = db.Column(db.Integer, primary_key=True, db.ForeignKey('document.id'))
    author = db.Column(db.String(50), nullable=False)
    publish_date = db.Column(db.Date, nullable=False)
    translator = db.Column(db.String(50))

    def __init__(self, category_id, topic, file_path, subject, level, author, publish_date, translator):
        super().__init__(category_id, topic, file_path, subject, level, type='book')
        self.author = author
        self.publish_date = publish_date
        self.translator = translator

class Voice(Document):
    id = db.Column(db.Integer, primary_key=True, db.ForeignKey('document.id'))
    speaker = db.Column(db.String(50), nullable=False)
    production_date = db.Column(db.Date, nullable=False)

    def __init__(self, category_id, topic, file_path, subject, level, speaker, production_date):
        super().__init__(category_id, topic, file_path, subject, level, type='voice')
        self.speaker = speaker
        self.production_date = production_date

class Booklet(Document):
    id = db.Column(db.Integer, primary_key=True, db.ForeignKey('document.id'))
    author = db.Column(db.String(50), nullable=False)
    production_date = db.Column(db.Date, nullable=False)

    def __init__(self, category_id, topic, file_path, subject, level, author, production_date):
        super().__init__(category_id, topic, file_path, subject, level, type='booklet')
        self.author = author
        self.production_date = production_date

class Category(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    documents = db.relationship('Document', back_populates='category')

    def __init__(self, name):
        self.name = name


class DocumentSchema(ma.Schema):
    topic = fields.String(required=True)
    subject = fields.String()
    file_path = fields.String(required=True)
    level = fields.Integer()
    category_id = fields.Integer(required=True)

class BookSchema(DocumentSchema):
    author = fields.String(required=True)
    publish_date = fields.Date(required=True)
    translator = fields.String()

class VoiceSchema(DocumentSchema):
    speaker = fields.String(required=True)
    production_date = fields.Date(required=True)

class BookletSchema(DocumentSchema):
    author = fields.String(required=True)
    production_date = fields.Date(required=True)

class CategorySchema(ma.Schema):
    name = fields.String(required=True)
    _links = ma.Hyperlinks(
			{
			 "documents": ma.URLFor('document_api.documentlistresource', category_id='<id>')
			}
		)

class TypeSchema(ma.Schema):
    type = fields.String(validate=validate.OneOf(choices=['voice', 'book', 'booklet']), required=True)
