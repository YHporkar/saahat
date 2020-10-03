from models.UserModel import AddUpdateDelete
from sqlalchemy_utils.types import UUIDType
import uuid

from models.UserModel import db

from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from flask_marshmallow import Marshmallow

ma = Marshmallow()


class Sport(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    venue = db.Column(db.String(50), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False) # required
    users = db.relationship('SportUsers', cascade='all,delete', back_populates='sport')

    report = db.relationship('SportReport', back_populates='sport', uselist=False)

    def __init__(self, type, datetime, venue):
        self.type = type
        self.datetime = datetime
        self.venue = venue

class SportUsers(db.Model, AddUpdateDelete):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sport_id = db.Column(db.Integer, db.ForeignKey('sport.id'))
    rate = db.Column(db.Integer)
    description = db.Column(db.Text)
    present = db.Column(db.Boolean)
    sport = db.relationship('Sport', back_populates='users')

    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'sport_id'),
    )
    
    def __init__(self, user_id, sport_id, present, rate, description):
        self.user_id = user_id
        self.sport_id = sport_id
        self.present = present
        self.rate = rate
        self.description = description


class SportSchema(ma.Schema):
    type = fields.String(required=True, validate=validate.OneOf(choices=['football', 'judo']))
    venue = fields.String(required=True)
    datetime = fields.DateTime(required=True)
    _links = ma.Hyperlinks(
        {
         "users": ma.URLFor('sport_api.sportuserslistresource', sport_id="<id>")
        }
    )

class SportUsersSchema(ma.Schema):
    user_id = fields.Integer(required=True)
    present = fields.Boolean()
    rate = fields.Float(validate=validate.Range(min=0, max=10))
    description = fields.String()
