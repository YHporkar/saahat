from models.UserModel import AddUpdateDelete
from sqlalchemy_utils.types import UUIDType
import uuid

from models.UserModel import db

from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from flask_marshmallow import Marshmallow

ma = Marshmallow()

class Session(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer,primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    datetime = db.Column(db.DateTime(), nullable=False)
    done = db.Column(db.Boolean, default=False)
    creation_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    details = db.relationship('SessionDetails', cascade='all,delete', uselist=False, back_populates='session')
    users = db.relationship('SessionUser', cascade='all,delete', back_populates='session')
    # type_id = db.Column(db.Integer, default=3)
    
    # __table_args__ = (
    #     db.ForeignKeyConstraint(["id", "type_id"], ["report.id", "report.type_id"]),
    # )
    # report = db.relationship('Report', backref='session', uselist=False)

    def __init__(self, subject, datetime, done):
        self.subject = subject
        self.datetime = datetime
        self.done = done

class SessionDetails(db.Model, AddUpdateDelete):
    session_id = db.Column(db.Integer,db.ForeignKey('session.id'), primary_key=True)
    session = db.relationship('Session', back_populates='details')
    number = db.Column(db.Integer)
    kind = db.Column(db.String(50)) # constraint
    location = db.Column(db.String(100))
    approvals = db.Column(db.Text)

    def __init__(self, session_id, **kwargs):
        self.session_id = session_id
        details_dict = kwargs.get('kwargs')
        if 'number' in details_dict:
            self.number = details_dict['number']
        if 'kind' in details_dict:
            self.kind = details_dict['kind']
        if 'location' in details_dict:
            self.location = details_dict['location']
        if 'approvals' in details_dict:
            self.birth_date = details_dict['birth_date']

    @classmethod
    def details_exists(cls, session_id):
        existing_details = cls.query.filter_by(session_id=session_id).first()
        if not existing_details:
            return False
        return True

class SessionUser(db.Model, AddUpdateDelete):
    __tablename__ = 'session_user'
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    session_id = db.Column(db.Integer,db.ForeignKey('session.id'))
    session = db.relationship('Session', back_populates='users')
    present = db.Column(db.Boolean)

    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'session_id'),
    )

    def __init__(self, user_id, session_id, present):
        self.user_id = user_id
        self.session_id = session_id
        self.present = present

class Task(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer,primary_key=True)
    subject = db.Column(db.String(50), nullable=False)
    done = db.Column(db.Boolean, default=False)
    done_time = db.Column(db.DateTime)
    priority = db.Column(db.String(50), default='medium')
    description = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('session_user.user_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session_user.session_id'), nullable=False)
    uis = db.relationship('SessionUser', backref='tasks', foreign_keys=[user_id, session_id])
    deadlines = db.relationship('Deadline', back_populates='task')

    # type_id = db.Column(db.Integer, default=4)

    # report = db.relationship('Report', backref='task', uselist=False)

    __table_args__ = (
        db.ForeignKeyConstraint(["user_id", "session_id"], ["session_user.user_id", "session_user.session_id"]),
        # db.ForeignKeyConstraint(["id", "type_id"], ["report.id", "report.type_id"]),
    )

    # __table_args__ = (
    #     db.UniqueConstraint('user_id', 'session_id'),
    # )

    def __init__(self, subject, priority, description, user_id, session_id):
        self.subject = subject
        self.description = description
        self.user_id = user_id
        self.session_id = session_id
        self.priority = priority

class Deadline(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer,primary_key=True)
    expiration_datetime = db.Column(db.DateTime, nullable=False) # required
    task_id = db.Column(db.Integer,db.ForeignKey('task.id'))
    task = db.relationship('Task', back_populates='deadlines')

    def __init__(self, task_id, expiration_datetime):
        self.task_id = task_id
        self.expiration_datetime = expiration_datetime

class SessionSchema(ma.Schema):
    subject = fields.String(required=True)
    datetime = fields.DateTime(required=True)
    done = fields.Boolean()
    
    _links = ma.Hyperlinks(
        {
         "details": ma.URLFor('session_api.sessiondetailsresource', session_id="<id>"),
         "users": ma.URLFor('session_api.sessionuserslistresource', session_id="<id>")
        }
    )
    class Meta:
        model = Session
        ordered = True
        # include_relationships = True
        # load_instance = True

class SessionDetailsSchema(ma.Schema):
    number = fields.Integer()
    kind = fields.String()
    location = fields.String()
    approvals = fields.String()

    class Meta:
        ordered = True

class SessionUserSchema(ma.Schema):
    user_id = fields.Integer(required=True)
    present = fields.Boolean()
    _links = ma.Hyperlinks(
        {
         "tasks": ma.URLFor('session_api.tasklistresource', session_id="<session_id>", user_id="<user_id>"),
        }
    )

class TaskSchema(ma.Schema):
    subject = fields.String(required=True)
    description = fields.String()
    priority = fields.String(validate=validate.OneOf(choices=['high', 'normal', 'low']))
    done = fields.Boolean()
    done_time = fields.DateTime()

    _links = ma.Hyperlinks(
        {
         "deadlines": ma.URLFor('session_api.deadlinelistresource', session_id="<session_id>", user_id="<user_id>", task_id="<id>"),
        }
    )
    class Meta:
        model = Task
        ordered = True

class DeadlineSchema(ma.Schema):
    expiration_datetime = fields.DateTime(required=True)