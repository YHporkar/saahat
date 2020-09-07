import uuid

from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy_utils.types import UUIDType

from models.UserModel import AddUpdateDelete, db

ma = Marshmallow()

class Report(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    datetime = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    description = db.Column(db.Text)
    multimedias = db.relationship('Multimedia', back_populates='report', cascade='all,delete')
    type = db.Column(db.String(20), nullable=False)
    # reporter = db.relationship('SuperUser', backref='report', uselist=False)
    
    __mapper_args__ = {'polymorphic_identity': 'report',
                        'polymorphic_on': type}
    
    def __init__(self, reporter_id, description, type):
        self.reporter_id = reporter_id
        self.description = description
        self.type = type

class HeyatReport(Report):
    id = db.Column(db.Integer, db.ForeignKey('report.id'), primary_key=True)
    heyat_id = db.Column(db.Integer, db.ForeignKey('heyat.id'))
    heyat = db.relationship('Heyat', back_populates='report')
    
    __mapper_args__ = {'polymorphic_identity': 'heyat'}
    
    def __init__(self, heyat_id, reporter_id, description):
        super().__init__(reporter_id, description, type='heyat')
        self.heyat_id = heyat_id

class CampReport(Report):
    id = db.Column(db.Integer, db.ForeignKey('report.id'), primary_key=True)
    camp_id = db.Column(db.Integer, db.ForeignKey('camp.id'))
    camp = db.relationship('Camp', back_populates='report')
    
    __mapper_args__ = {'polymorphic_identity': 'camp'}

    def __init__(self, camp_id, reporter_id, description):
        super().__init__(reporter_id, description, type='camp')
        self.camp_id = camp_id

class LectureReport(Report):
    id = db.Column(db.Integer, db.ForeignKey('report.id'), primary_key=True)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'))
    lecture = db.relationship('Lecture', back_populates='report')
    
    __mapper_args__ = {'polymorphic_identity': 'lecture'}
    
    def __init__(self, lecture_id, reporter_id, description):
        super().__init__(reporter_id, description, type='lecture')
        self.lecture_id = lecture_id


class Multimedia(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(50), nullable=False)
    format = db.Column(db.String(20), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=False)
    report = db.relationship('Report', back_populates='multimedias')

    def __init__(self, path, format, report_id):
        self.path = path
        self.format = format
        self.report_id = report_id


class ReportSchema(ma.Schema):
    description = fields.String()
    creation_datetime = fields.DateTime(dump_only=True)
    _links = ma.Hyperlinks(
        {
         "multimedias": ma.URLFor('report_api.multimedialistresource', report_id='<id>')
         }
    )

class ReportArgsSchema(ma.Schema):
    field = fields.String(required=True, validate=validate.OneOf(choices=['heyat', 'camp', 'lecture', 'user']))
    id = fields.Integer(required=True)

class MultimediaSchema(ma.Schema):
    path = fields.String(required=True)
    format = fields.String(required=True, validate=validate.OneOf(choices=['mp3', 'mp4', 'xlsx', 'docx', 'pdf']))
    _links = ma.Hyperlinks(
        {
            "self": ma.URLFor('report_api.multimediaresource', report_id='<report_id>', multimedia_id='<id>')
        }
    )