from models.UserModel import AddUpdateDelete
from sqlalchemy_utils.types import UUIDType
import uuid

from models.UserModel import db

from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from flask_marshmallow import Marshmallow

ma = Marshmallow()


class Heyat(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(50), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False) # required
    compere = db.Column(db.String(50))	# mojri
    speaker = db.Column(db.String(50))	# sokhanran
    singer = db.Column(db.String(50))
    meal = db.Column(db.String(50))
    users = db.relationship('HeyatUsers', cascade='all,delete', back_populates='heyat')

    report = db.relationship('HeyatReport', back_populates='heyat', uselist=False)

    def __init__(self, type, reason, datetime, compere, speaker, singer, meal):
        self.type = type
        self.reason = reason
        self.datetime = datetime
        self.compere = compere
        self.speaker = speaker
        self.singer = singer
        self.meal = meal

class HeyatUsers(db.Model, AddUpdateDelete):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    heyat_id = db.Column(db.Integer, db.ForeignKey('heyat.id'))
    rate = db.Column(db.Integer)
    description = db.Column(db.Text)
    present = db.Column(db.Boolean)
    heyat = db.relationship('Heyat', back_populates='users')

    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'heyat_id'),
    )
    
    def __init__(self, user_id, heyat_id, present, rate, description):
        self.user_id = user_id
        self.heyat_id = heyat_id
        self.present = present
        self.rate = rate
        self.description = description


class HeyatSchema(ma.Schema):
    type = fields.String(required=True, validate=validate.OneOf(choices=['celebration', 'mourning']))
    reason = fields.String(required=True)
    datetime = fields.DateTime(required=True)
    compere = fields.String()
    speaker = fields.String()
    singer = fields.String()
    meal = fields.String()
    _links = ma.Hyperlinks(
        {
         "users": ma.URLFor('heyat_api.heyatuserslistresource', heyat_id="<id>")
        }
    )

class HeyatUsersSchema(ma.Schema):
    user_id = fields.Integer(required=True)
    present = fields.Boolean()
    rate = fields.Float(validate=validate.Range(min=0, max=10))
    description = fields.String()
