from models.UserModel import AddUpdateDelete
from sqlalchemy_utils.types import UUIDType
import uuid

from models.UserModel import db

from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from flask_marshmallow import Marshmallow

ma = Marshmallow()

class Camp(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=False)
    go_time = db.Column(db.DateTime, nullable=False)
    back_time = db.Column(db.DateTime, nullable=False)
    cost_per_person = db.Column(db.String(50))
    users = db.relationship('UserPayments', cascade='all,delete', back_populates='camp')
    report = db.relationship('CampReport', back_populates='camp', uselist=False)

    def __init__(self, subject, location, go_time, back_time, cost_per_person):
        self.subject = subject
        self.location = location
        self.go_time = go_time
        self.back_time = back_time
        self.cost_per_person = cost_per_person

class UserPayments(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer, primary_key=True)
    paid_value = db.Column(db.String(50), default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    camp_id = db.Column(db.Integer, db.ForeignKey('camp.id'), nullable=False)
    rate = db.Column(db.Integer)
    description = db.Column(db.Text)
    # user = db.relationship('User', backref='payments')
    camp = db.relationship('Camp', back_populates='users')

    def __init__(self, paid_value, user_id, camp_id, rate, description):
        self.paid_value = paid_value
        self.user_id = user_id
        self.camp_id = camp_id
        self.rate = rate
        self.description = description

        if Camp.query.get(camp_id).cost_per_person == paid_value:
            self.full_paid = 1


class CampSchema(ma.Schema):
    subject = fields.String(required=True)
    location = fields.String(required=True)
    go_time = fields.DateTime(required=True)
    back_time = fields.DateTime(required=True)
    cost_per_person = fields.String(required=True)
    _links = ma.Hyperlinks(
        {
         "users": ma.URLFor('camp_api.userpaymentslistresource', camp_id="<id>")
        }
    )

class UserPaymentSchema(ma.Schema):
    user_id = fields.Integer(required=True)
    paid_value = fields.String()
    rate = fields.Float(validate=validate.Range(min=0, max=10))
    description = fields.String()