import uuid

from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy_utils.types import UUIDType

from models.UserModel import AddUpdateDelete, db

ma = Marshmallow()


class Lecture(db.Model, AddUpdateDelete):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50), nullable=False)
	group = db.Column(db.String(50))
	teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
	course = db.relationship('Course', back_populates='lecture', uselist=False, cascade='all,delete')
	sessions = db.relationship('LectureSession', back_populates='lecture', cascade='all,delete')
	users = db.relationship('LectureUser', back_populates='lecture_user', cascade='all,delete')
	exams = db.relationship('Exam', back_populates='lecture', cascade='all,delete')
	report = db.relationship('LectureReport', back_populates='lecture', uselist=False)

	def __init__(self, name, group, teacher_id, course_id):
		self.name = name
		self.group = group
		self.teacher_id = teacher_id
		self.course_id = course_id

class LectureUser(db.Model, AddUpdateDelete):
	student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'), nullable=False)
	lecture_user = db.relationship('Lecture', back_populates='users')

	__table_args__ = (
		db.PrimaryKeyConstraint('student_id', 'lecture_id'),
	)

	def __init__(self, student_id, lecture_id):
		self.student_id = student_id
		self.lecture_id = lecture_id

class LectureSession(db.Model, AddUpdateDelete):
	id = db.Column(db.Integer, primary_key=True)
	datetime = db.Column(db.DateTime, nullable=False)
	end_time = db.Column(db.Time, nullable=False)
	subject = db.Column(db.String(100))
	number = db.Column(db.Integer)
	location = db.Column(db.String(50))
	lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'), nullable=False)
	lecture = db.relationship('Lecture', back_populates='sessions')
	users = db.relationship('LectureUserSession', back_populates='lecture_session')
	def __init__(self, datetime, end_time, subject, location, lecture_id):
		self.datetime = datetime
		self.end_time = end_time
		self.subject = subject
		self.number = LectureSession.query.filter_by(lecture_id=lecture_id).count() + 1
		self.location = location
		self.lecture_id = lecture_id

class LectureUserSession(db.Model, AddUpdateDelete):
	student_id = db.Column(db.Integer, db.ForeignKey('lecture_user.student_id'), nullable=False)
	session_id = db.Column(db.Integer, db.ForeignKey('lecture_session.id'), nullable=False)
	description = db.Column(db.Text)
	present = db.Column(db.Boolean, default=False)
	homework_mark = db.Column(db.Integer)
	lecture_session = db.relationship('LectureSession', back_populates='users')
    
	__table_args__ = (
		db.PrimaryKeyConstraint('student_id', 'session_id'),
    )

	def __init__(self, student_id, session_id, description, present, homework_mark):
		self.student_id = student_id
		self.session_id = session_id
		self.description = description
		self.present = present
		self.homework_mark = homework_mark

class Course(db.Model, AddUpdateDelete):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50), nullable=False)
	fac = db.Column(db.Integer, nullable=False)
	grade = db.Column(db.Integer, nullable=False)
	major = db.Column(db.String(50))
	lecture = db.relationship('Lecture', back_populates='course')

	def __init__(self, name, fac, grade, major):
		self.name = name
		self.fac = fac
		self.grade = grade
		self.major = major

class Exam(db.Model, AddUpdateDelete):
	id = db.Column(db.Integer, primary_key=True)
	datetime = db.Column(db.DateTime, nullable=False) # required
	type = db.Column(db.String(50), nullable=False)
	file = db.Column(db.String(100))
	lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'), nullable=False)
	lecture = db.relationship('Lecture', back_populates='exams')
	results = db.relationship('ExamResult', back_populates='exam', cascade='all,delete')

	def __init__(self, datetime, type, file, lecture_id):
		self.datetime = datetime
		self.type = type
		self.file = file
		self.lecture_id = lecture_id

class ExamResult(db.Model, AddUpdateDelete):
	score = db.Column(db.Integer, nullable=False)
	student_id = db.Column(db.Integer, db.ForeignKey('lecture_user.student_id'), nullable=False)
	exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
	exam = db.relationship('Exam', back_populates='results')
    
	__table_args__ = (
		db.PrimaryKeyConstraint('student_id', 'exam_id'),
    )

	def __init__(self, score, student_id, exam_id):
		self.score = score
		self.student_id = student_id
		self.exam_id = exam_id


class LectureSchema(ma.Schema):
	name = fields.String(required=True)
	group = fields.String()
	start_time = fields.Time(required=True)
	end_time = fields.Time(required=True)
	# teacher_username = fields.String(required=True, validate=validate.Regexp(regex=r'^(?=.{5,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$'))
	teacher_id = fields.Integer(required=True)
	_links = ma.Hyperlinks(
			{
			 "sessions": ma.URLFor('education_api.lecturesessionlistresource', course_id='<course_id>', lecture_id='<id>'),
			 "users": ma.URLFor('education_api.lectureuserlistresource', course_id='<course_id>', lecture_id='<id>'),
			 "exams": ma.URLFor('education_api.examlistresource', course_id='<course_id>', lecture_id='<id>')
			}
		)

class LectureUserSchema(ma.Schema):
	student_id = fields.Integer(required=True)
	# username = fields.String(required=True, validate=validate.Regexp(regex=r'^(?=.{5,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$'))

class LectureSessionSchema(ma.Schema):
	datetime = fields.DateTime(required=True)
	subject = fields.String()
	number = fields.Integer()
	location = fields.String()
	users = fields.List(fields.Nested('LectureUserSchema'))
	# _links = ma.Hyperlinks(
	# 		{
	# 			"self": ma.URLFor('education_api.lecturesessionlistresource', course_id='<id>', lecture_id='<lecture_id>')
	# 		#  "users": ma.URLFor('education_api.lectureusersessionresource', course_id='<course_id>', lecture_id='<lecture_id>')
	# 		}
	# 	)

class LectureUserSessionSchema(ma.Schema):
	# student_username = fields.String(required=True, validate=validate.Regexp(regex=r'^(?=.{5,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$'))
	student_id = fields.Integer(required=True)
	description = fields.String()
	present = fields.Boolean()
	homework_mark = fields.Integer()

class CourseSchema(ma.Schema):
	name = fields.String(required=True)
	fac = fields.Integer(required=True, validate=validate.Range(min=1, max=4))
	grade = fields.Integer(required=True)
	major = fields.String()
	_links = ma.Hyperlinks(
			{
			 "lectures": ma.URLFor('education_api.lecturelistresource', course_id='<id>')
			}
		)

class ExamSchema(ma.Schema):
	datetime = fields.DateTime(required=True) # required
	type = fields.String(required=True, validate=validate.OneOf(choices=['quiz', 'midterm', 'final']))
	file = fields.String()
	_links = ma.Hyperlinks(
			{
			 "results": ma.URLFor('education_api.examresultlistresource', course_id='<course_id>', lecture_id='<lecture_id>', exam_id='<id>')
			}
		)

class ExamResultSchema(ma.Schema):
	student_id = fields.Integer(required=True)
	score = fields.Integer(required=True)
