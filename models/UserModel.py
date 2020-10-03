from marshmallow import Schema, fields, validate
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from sqlalchemy_utils.types import UUIDType
from flask_sqlalchemy import SQLAlchemy

from argon2 import PasswordHasher
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

from enum import Enum
import uuid

import config

ma = Marshmallow()
HASHER = PasswordHasher()
db = SQLAlchemy()

class AddUpdateDelete():
    def add(self, resource):
        db.session.add(resource)
        return db.session.commit()

    def update(self):
        return db.session.commit()

    def delete(self, resource):
        db.session.delete(resource)
        return db.session.commit()

# ---------- Models ----------- #
class User(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    creation_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    authorized = db.Column(db.Boolean, default=0, nullable=False)
    details = db.relationship('UserDetails', cascade='all,delete', uselist=False, back_populates='user')
    dials = db.relationship('Dial', cascade='all,delete', back_populates='user')
    grades = db.relationship('Grade', cascade='all,delete', back_populates='user')
    messages = db.relationship('Message', cascade='all,delete', back_populates='user')
    roles = db.relationship('UserRoles', cascade='all,delete', back_populates='user')

    # __mapper_args__ = {'polymorphic_identity': 'user',
    #                     'polymorphic_on': type}

    def __init__(self, username, password, email, type):
        self.username = username
        self.password = self.set_password(password)
        self.email = email
        self.type = type

    # I save the hashed password
    @staticmethod
    def set_password(password):
        return HASHER.hash(password)

    def verify_password(self, password):
        return HASHER.verify(self.password, password)

    def generate_auth_token(self, expiration = 360000):
        s = Serializer(config.SECRET_KEY, expires_in=expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(config.SECRET_KEY)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user
    
# class Officer(User):
#     id = db.Column(db.Integer,db.ForeignKey('user.id'), primary_key=True)

#     __mapper_args__ = {'polymorphic_identity': 'officer'}

#     def __init__(self, username, password, email, type):
#         super().__init__(username, password, email, type)

# class Student(User):
#     id = db.Column(db.Integer,db.ForeignKey('user.id'), primary_key=True)

#     __mapper_args__ = {'polymorphic_identity': 'student'}

#     def __init__(self, username, password, email, type):
#         super().__init__(username, password, email, type)

class UserDetails(db.Model, AddUpdateDelete):
    # id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User', back_populates='details')
    profile_photo = db.Column(db.String(50))
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    instagram = db.Column(db.String(20))
    birth_date = db.Column(db.DateTime)
    nat_id = db.Column(db.String(10))
    fathername = db.Column(db.String(50))

    def __init__(self, user_id, firstname, lastname, instagram, birth_date, nat_id, fathername, profile_photo):
        self.user_id = user_id
        self.firstname = firstname
        self.lastname = lastname
        self.instagram = instagram
        self.birth_date = birth_date
        self.nat_id = nat_id
        self.fathername = fathername
        self.profile_photo = profile_photo
        
    @classmethod
    def details_exists(cls, user_id):
        existing_details = cls.query.filter_by(user_id=user_id).first()
        if not existing_details:
            return False
        return True

class StudentDetails(UserDetails):
    id = db.Column(db.Integer, db.ForeignKey('user_details.user_id'), primary_key=True)
    school = db.Column(db.String(50))
    major = db.Column(db.String(50))
    last_average = db.Column(db.Float)
    grade = db.Column(db.Integer, nullable=False)
    group = db.Column(db.String(50), nullable=False)

    def __init__(self, user_id, firstname, lastname, instagram, birth_date, nat_id, fathername, school, major, last_average, grade, group):
        super().__init__(user_id, firstname, lastname, instagram, birth_date, nat_id, fathername)
        self.school = school
        self.major = major
        self.last_average = last_average
        self.grade = grade
        self.group = group

class OfficerDetails(UserDetails):
    id = db.Column(db.Integer,db.ForeignKey('user_details.user_id'), primary_key=True)
    coop_start_date = db.Column(db.DateTime, nullable=False)
    work_experience = db.Column(db.Integer, nullable=False)
    expenses = db.relationship('Expense', back_populates='user')

    def __init__(self, user_id, firstname, lastname, instagram, birth_date, nat_id, fathername, coop_start_date, work_experience):
        super().__init__(user_id, firstname, lastname, instagram, birth_date, nat_id, fathername)
        self.coop_start_date = coop_start_date
        self.work_experience = work_experience

class RolesEnum(Enum):
    ADMIN = 0
    MENTOR = 1
    CAMP = 2
    SESSION = 3
    HEYAT = 4
    EDUCATION = 5
    ACCOUNTING = 6
    DOCUMENT = 7
    FORM = 8
    SPORT = 9
    REPORT = 10

class UserRoles(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='roles')
    role_name = db.Column(db.String(20))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'role_name'),
    )

    @classmethod
    def is_unique(cls, user_id, role_name):
        existing_role = cls.query.filter_by(user_id=user_id, role_name=role_name).first()
        if not existing_role:
            return True
        return False
    
    def __init__(self, user_id, role_name):
        self.user_id = user_id
        self.role_name = role_name

class Dial(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer,primary_key=True)
    number = db.Column(db.String(11), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='dials')


    @classmethod
    def is_unique(cls, user_id, number):
        existing_dial = cls.query.filter_by(user_id=user_id, number=number).first()
        if not existing_dial:
            return True
        return False


    def __init__(self, number, type, user_id):
        self.user_id = user_id
        self.type = type
        self.number = number

class Grade(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer,primary_key=True)
    major = db.Column(db.String(50), nullable=False)
    college = db.Column(db.String(100), nullable=False)
    degree = db.Column(db.String(50), nullable=False)
    pic = db.Column(db.String(100))
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='grades')

    @classmethod
    def is_unique(cls, user_id, major, degree):
        existing_grade = cls.query.filter_by(user_id=user_id, major=major, degree=degree).first()
        if not existing_grade:
            return True
        return False


    def __init__(self, major, college, grade, user_id):
        self.major = major
        self.college = college
        self.grade = grade
        # self.pic = pic
        self.user_id = user_id

class Message(db.Model, AddUpdateDelete):
    id = db.Column(db.Integer,primary_key=True)
    subject = db.Column(db.String(100))
    text = db.Column(db.String(500))
    read = db.Column(db.Boolean, default=0)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='messages')
    notification = db.relationship('Notification', back_populates='message', uselist=False, cascade='all,delete')

    def __init__(self, subject, text, user_id):
        self.subject = subject
        self.text = text
        self.user_id = user_id

class Notification(db.Model, AddUpdateDelete):
    message_id = db.Column(db.Integer,db.ForeignKey('message.id'), primary_key=True)
    message = db.relationship('Message', back_populates='notification')
    # text = db.relationship('Message', back_populates='subject', foreign_keys=[message_id])
    text = db.Column(db.String(100))

    def __init__(self, message_id):
        self.message_id = message_id

# --------- Schemas --------- #
class NotificationSchema(ma.Schema):
    text = fields.String(required=True)
    message = ma.URLFor('user_api.messageresource', message_id='<message_id>')

class UserSchema(ma.Schema):
    # id = fields.Integer(dump_only=True)
    username = fields.String(required=True, validate=validate.Regexp(regex=r'^(?=.{5,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$'))
    password = fields.String(required=True, load_only=True)
    type = fields.String(required=True, validate=validate.OneOf(choices=['student', 'officer']))
    email = fields.Email(required=True)
    creation_date = fields.DateTime()
    
    _links = ma.Hyperlinks(
        {
         "details": ma.URLFor('user_api.userdetailsresource'),
         "dials": ma.URLFor('user_api.diallistresource'),
         "roles": ma.URLFor('user_api.rolelistresource'),
         "grades": ma.URLFor('user_api.diallistresource'),
         "messages": ma.URLFor('user_api.messagelistresource')
        }
    )

    class Meta:
        ordered = True

class AdminUserSchema(UserSchema):
    # url = ma.URLFor('user_api.adminuserresource', user_id='<id>', _external=True)
    _links = ma.Hyperlinks(
        {"self": ma.URLFor('user_api.adminuserresource', user_id="<id>"),
        #  "collection": ma.URLFor('user_api.userlistresource"),
         "roles": ma.URLFor('user_api.adminrolelistresource', user_id="<id>"),
         "messages": ma.URLFor('user_api.adminmessagelistresource', user_id='<id>')
        #  "notifications": ma.URLFor('user_api.adminnotiflistresource', user_id="<id>")
         }
    )
    
class MessageSchema(ma.Schema):
    subject = fields.String(required=True)
    text = fields.String(required=True)
    # url = ma.URLFor('user_api.notificationresource', notification_id='<id>')

class AdminMessageSchema(MessageSchema):
    url = ma.URLFor('user_api.adminmessageresource', user_id='<user_id>', message_id='<id>')

class GradeSchema(ma.Schema): 
    major = fields.String(required=True)
    college = fields.String(required=True)
    degree = fields.String(required=True, validate=validate.OneOf(choices=['diploma', 'bachelor', 'master', 'doctorate']))
    pic = fields.String()
    url = ma.URLFor('user_api.graderesource', grade_id='<id>')
    class Meta:
        ordered = True

class DialSchema(ma.Schema): 
    # id = fields.Integer(dump_only=True)
    number = fields.String(required=True, validate=validate.Length(equal=11), allow_none=True)
    type = fields.String(required=True, validate=validate.OneOf(choices=['home', 'mobile', 'work']))
    # user = fields.Nested("UserSchema", only=['username'])
    url = ma.URLFor('user_api.dialresource', dial_id='<id>')
    class Meta:
        ordered = True

class UserDetailsSchema(ma.Schema):
    nat_id = fields.String(validate=validate.Length(equal=10))
    birth_date = fields.Date()
    instagram = fields.String(validate=validate.Regexp(r'^(?!.*\.\.)(?!.*\.$)[^\W][\w.]{0,29}$'))
    firstname = fields.String()
    lastname = fields.String()
    fathername = fields.String()

class StudentSchema(UserDetailsSchema):
    group = fields.Integer(required=True)
    grade = fields.String(required=True)
    school = fields.String()
    major = fields.String()
    last_average = fields.Integer()

class OfficerSchema(UserDetailsSchema):
    coop_start_date = fields.Date(required=True)
    work_experience = fields.Integer(required=True)
    _links = ma.Hyperlinks(
        {"expenses": ma.URLFor('expense_api.expenselistresource')}
    )

class AdminStudentSchema(StudentSchema):
    url = ma.URLFor('user_api.adminuserresource', user_id='<id>', _external=True)

class AdminOfficerSchema(OfficerSchema):
    url = ma.URLFor('user_api.adminuserresource', user_id='<id>', _external=True)

class RoleSchema(ma.Schema):
    # id = fields.Integer(dump_only=True)
    role_name = fields.String(required=True, validate=validate.OneOf([role.name.lower() for role in RolesEnum]))
    
class AdminRoleSchema(RoleSchema):
    # user = ma.URLFor('user_api.adminuserresource', user_id='<id>')
    url = ma.URLFor('user_api.adminroleresource', user_id='<user_id>', role_id='<id>')

class TypeSchema(ma.Schema):
    type = fields.String(validate=validate.OneOf(choices=['officer', 'student']))

class Friend(db.Model, AddUpdateDelete):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # user who has friends
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id')) # friend of user_id
    user = db.relationship('User', backref='friends', foreign_keys=[user_id, friend_id])
    
    __table_args__ = (
        db.ForeignKeyConstraint(["user_id", "friend_id"], ["user.id", "user.id"]),
        db.PrimaryKeyConstraint("user_id", "friend_id"),
    )
    
    @classmethod
    def is_unique(cls, user_id, friend_id):
        if Friend.query.filter_by(user_id=user_id, friend_id=friend_id).first() or Friend.query.filter_by(user_id=friend_id, friend_id=user_id).first():
            return False
        return True

    def __init__(self, user_id, friend_id):
        self.user_id = user_id
        self.friend_id = friend_id

class FriendSchema(ma.Schema):
    friend_id = fields.Integer(required=True)
