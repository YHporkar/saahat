from models.UserModel import AddUpdateDelete
from sqlalchemy_utils.types import UUIDType
import uuid

from models.UserModel import db

from marshmallow import Schema, fields, validate
from flask_marshmallow import Marshmallow

ma = Marshmallow()

class Form(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer, nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(100), nullable=False)

    def __init__(self, code, topic, file_path):
        self.code = code
        self.topic = topic
        self.file_path = file_path
    
class FormSchema(ma.Schema):
    code = fields.Integer(required=True)
    topic = fields.String(required=True)
    file_path = fields.String(required=True)
