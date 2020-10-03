
from models.UserModel import AddUpdateDelete
from sqlalchemy_utils.types import UUIDType
import uuid

from models.UserModel import db

from marshmallow import Schema, fields, validate
from flask_marshmallow import Marshmallow

ma = Marshmallow()


class Expense(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(50), nullable=False)    
    invoice = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    cost = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('officer_details.user_id'), nullable=False)
    owner = db.Column(db.String(200), nullable=False)
    # user = db.relationship('OfficerDetails', back_populates='expenses')
    state = db.Column(db.Boolean, nullable=False)

    def __init__(self, topic, invoice, description, cost, date, user_id, state, owner):
        self.topic = topic
        self.description = description
        self.cost = cost
        self.date = date
        self.user_id = user_id
        self.state = state
        self.owner = owner

class ExpenseSchema(ma.Schema):
    topic = fields.String(required=True)
    invoice = fields.String(required=True)
    description = fields.String()
    cost = fields.Float(required=True)
    date = fields.Date(required=True)
    user_id = fields.Integer(required=True)
    state = fields.String(required=True)
    owner = fields.String(required=True)