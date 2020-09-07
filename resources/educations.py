from flask import Blueprint, g, jsonify, make_response, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, Resource, abort
from sqlalchemy.exc import SQLAlchemyError

import status
from auth import (EducationAuthRequiredResource, access_denied, basic_auth,
                  roles_required, token_auth)
from helpers import PaginationHelper
from models.EduModel import (Course, CourseSchema, Exam, ExamResult,
                             ExamResultSchema, ExamSchema, Lecture,
                             LectureSchema, LectureSession,
                             LectureSessionSchema, LectureUser,
                             LectureUserSchema, LectureUserSession,
                             LectureUserSessionSchema)
from models.UserModel import Message, User, db

education_api_bp = Blueprint('education_api', __name__)

education_api = Api(education_api_bp)

course_schema = CourseSchema()
lecture_schema = LectureSchema()
lecture_user_schema = LectureUserSchema()
lecture_session_schema = LectureSessionSchema()
lecture_user_session_schema = LectureUserSessionSchema()
exam_schema = ExamSchema()
exam_result_schema = ExamResultSchema()


class CourseListResource(EducationAuthRequiredResource):
    def get(self):
        pagination_helper = PaginationHelper(
            request,
            query=Course.query,
            resource_for_url='education_api.courselistresource',
            key_name='results',
            schema=course_schema)
        result = pagination_helper.paginate_query()
        return result
    
    def post(self):
        request_dict = request.get_json(force=True)
        errors = course_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        major = None
        if 'major' in request_dict:
            major = request_dict['major']
        try:
            course = Course(name=request_dict['name'], fac=request_dict['fac'], major=major, grade=request_dict['grade'])
            course.add(course)
            query = Course.query.get(course.id)
            result = course_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class CourseResource(EducationAuthRequiredResource):
    def get(self, course_id):
        course = Course.query.get_or_404(course_id)
        result = course_schema.dump(course)
        return result

    def patch(self, course_id):
        course = Course.query.get_or_404(course_id)
        # course is for current user or not
        # user_course_auth_fail(course)
        course_dict = request.get_json(force=True)
        if 'name' in course_dict:
            course.name = course_dict['name']
        if 'fac' in course_dict:
            course.fac = course_dict['fac']
        if 'grade' in course_dict:
            course.grade = course_dict['grade']
        if 'major' in course_dict:
            course.major = course_dict['major']
        dumped_course = course_schema.dump(course)
        validate_errors = course_schema.validate(dumped_course)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            course.update()
            return self.get(course_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, course_id):
        course = Course.query.get_or_404(course_id)
        try:
            course.delete(course)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class LectureListResource(EducationAuthRequiredResource):
    def get(self, course_id):
        pagination_helper = PaginationHelper(
            request,
            query=Lecture.query.filter_by(course_id=course_id),
            resource_for_url='education_api.lecturelistresource',
            key_name='results',
            schema=lecture_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, course_id):
        request_dict = request.get_json(force=True)
        Course.query.get_or_404(course_id)
        errors = lecture_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        teacher_id = request_dict['teacher_id']
        User.query.get_or_404(teacher_id)
        if 'group' in request_dict:
            group = request_dict['group']
        else:
            group = False
        try:
            lecture = Lecture(course_id=course_id, group=group, teacher_id=teacher_id, name=request_dict['name'])
            lecture.add(lecture)
            query = Lecture.query.get(lecture.id)
            result = lecture_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class LectureResource(EducationAuthRequiredResource):
    def get(self, lecture_id, course_id):
        lecture = Lecture.query.get_or_404(lecture_id)
        result = lecture_schema.dump(lecture)
        return result

    def patch(self, lecture_id, course_id):
        lecture = Lecture.query.get_or_404(lecture_id)
        lecture_dict = request.get_json(force=True)
        if 'name' in lecture_dict:
            lecture.name = lecture_dict['name']
        if 'group' in lecture_dict:
            lecture.group = lecture_dict['group']

        dumped_lecture = lecture_schema.dump(lecture)
        validate_errors = lecture_schema.validate(dumped_lecture)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            lecture.update()
            return self.get(lecture_id, course_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, lecture_id, course_id):
        lecture = Lecture.query.get_or_404(lecture_id)
        try:
            lecture.delete(lecture)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class LectureSessionListResource(EducationAuthRequiredResource):
    def get(self, course_id, lecture_id):
        pagination_helper = PaginationHelper(
            request,
            query=LectureSession.query.filter_by(lecture_id=lecture_id),
            resource_for_url='education_api.lecturesessionlistresource',
            key_name='results',
            schema=lecture_session_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, course_id, lecture_id):
        # lecture_students = LectureUser.query.filter_by(lecture_id=lecture_id).all()
        # if not lecture_students:
        #     abort(status.HTTP_400_BAD_REQUEST, message='this lecture has no student')
        request_dict = request.get_json(force=True)
        Lecture.query.get_or_404(lecture_id)
        # if not request_dict:
        #     response = {'lecture_session': 'No input data provided'}
        #     return response, status.HTTP_400_BAD_REQUEST
        errors = lecture_session_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        subject = None
        location = None
        if 'subject' in request_dict:
            subject = request_dict['subject']
        if 'location' in request_dict:
            location = request_dict['location']
        try:
            # create a new LectureSession
            lecture_session = LectureSession(lecture_id=lecture_id, datetime=request_dict['datetime'], end_time=request_dict['end_time'], subject=subject, location=location)
            lecture_session.add(lecture_session)
            # for st in lecture_students:
            #     lecture_user_session = LectureUserSession(student_id=st.student_id, session_id=lecture_session.id)
            #     lecture_user_session.add(lecture_user_session)
            query = LectureSession.query.get(lecture_session.id)
            result = lecture_session_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class LectureSessionResource(EducationAuthRequiredResource):
    def get(self, course_id, lecture_id, session_id):
        lecture_session = LectureSession.query.get_or_404(session_id)
        result = lecture_session_schema.dump(lecture_session)
        return result

    def patch(self, course_id, lecture_id, session_id):
        lecture_session = LectureSession.query.get_or_404(session_id)
        lecture_session_dict = request.get_json(force=True)
        if 'datetime' in lecture_session_dict:
            lecture_session.datetime = lecture_session_dict['datetime']
        if 'end_time' in lecture_session_dict:
            lecture_session.end_time = lecture_session_dict['end_time']
        if 'subject' in lecture_session_dict:
            lecture_session.subject = lecture_session_dict['subject']
        if 'location' in lecture_session_dict:
            lecture_session.location = lecture_session_dict['location']
        dumped_lecture_session = lecture_session_schema.dump(lecture_session)
        validate_errors = lecture_session_schema.validate(dumped_lecture_session)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            lecture_session.update()
            return self.get(course_id, lecture_id, session_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, course_id, lecture_id, session_id):
        lecture_session = LectureSession.query.get_or_404(session_id)
        try:
            lecture_session.delete(lecture_session)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST
            return resp, status.HTTP_400_BAD_REQUEST

class LectureUserListResource(EducationAuthRequiredResource):
    def get(self, course_id, lecture_id):
        pagination_helper = PaginationHelper(
            request,
            query=LectureUser.query.filter_by(lecture_id=lecture_id),
            resource_for_url='education_api.lectureuserlistresource',
            key_name='results',
            schema=lecture_user_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, course_id, lecture_id):
        request_dict = request.get_json(force=True)
        Lecture.query.get_or_404(lecture_id)
        errors = lecture_user_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        student_id = request_dict['student_id']
        User.query.get_or_404(student_id)
        try:
            lecture_user = LectureUser(student_id=student_id, lecture_id=lecture_id)
            lecture_user.add(lecture_user)
            query = LectureUser.query.filter_by(student_id=student_id, lecture_id=lecture_id).first()
            result = lecture_user_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST
    
class LectureUserResource(EducationAuthRequiredResource):
    def delete(self, course_id, lecture_id, user_id):
        lecture_user = LectureUser.query.filter_by(lecture_id=lecture_id, user_id=user_id).first()
        try:
            lecture_user.delete(lecture_user)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class LectureUserSessionListResource(EducationAuthRequiredResource):
    def post(self, course_id, lecture_id, session_id):
        request_dict = request.get_json(force=True)
        Course.query.get_or_404(course_id)
        Lecture.query.get_or_404(lecture_id)
        LectureSession.query.get_or_404(session_id)
        errors = lecture_user_session_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        student_id = request_dict['student_id']
        User.query.get_or_404(student_id)
        description = None
        present = False
        homework_mark = 0
        if 'description' in request_dict:
            description = request_dict['description']
        if 'present' in request_dict:
            present = request_dict['present']
        if 'homework_mark' in request_dict:
            homework_mark = request_dict['homework_mark']
        try:
            lecture_user_session = LectureUserSession(student_id=student_id, session_id=session_id, description=description, present=present, homework_mark=homework_mark)
            lecture_user_session.add(lecture_user_session)
            query = LectureUserSession.query.filter_by(student_id=student_id, session_id=session_id).first()
            result = lecture_user_session.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class LectureUserSessionResource(EducationAuthRequiredResource):
    def get(self, course_id, lecture_id, session_id, user_id):
        lecture_user_session = LectureUserSession.query.filter_by(session_id=session_id, student_id=user_id)
        result = lecture_user_session_schema.dump(lecture_user_session)
        return result

    def patch(self, course_id, lecture_id, session_id, user_id):
        lecture_user_session = LectureUserSession.query.filter_by(session_id=session_id, student_id=user_id)
        lecture_user_session_dict = request.get_json(force=True)
        if 'description' in lecture_user_session_dict:
            lecture_user_session.description = lecture_user_session_dict['description']
        if 'homework_mark' in lecture_user_session_dict:
            lecture_user_session.homework_mark = lecture_user_session_dict['homework_mark']
        if 'present' in lecture_user_session_dict:
            lecture_user_session.present = lecture_user_session_dict['present']
        dumped_lecture_user_session = lecture_user_session_schema.dump(lecture_user_session)
        validate_errors = lecture_user_session_schema.validate(dumped_lecture_user_session)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            lecture_user_session.update()
            return self.get(course_id, lecture_id, session_id, user_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class ExamListResource(EducationAuthRequiredResource):
    def get(self, course_id, lecture_id):
        pagination_helper = PaginationHelper(
            request,
            query=Exam.query.filter_by(lecture_id=lecture_id),
            resource_for_url='education_api.examlistresource',
            key_name='results',
            schema=exam_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, course_id, lecture_id):
        request_dict = request.get_json(force=True)
        Course.query.get_or_404(course_id)
        Lecture.query.get_or_404(lecture_id)
        if not request_dict:
            response = {'exams': 'No input data provided'}
            return response, status.HTTP_400_BAD_REQUEST
        errors = exam_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        file = None
        if 'file' in request_dict:
            file = request_dict['file']
        try:
            # create a new LectureSession
            exam = Exam(lecture_id=lecture_id, datetime=request_dict['datetime'], type=request_dict['type'], file=file)
            exam.add(exam)
            query = Exam.query.get(exam.id)
            result = exam_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class ExamResource(EducationAuthRequiredResource):
    def get(self, course_id, lecture_id, exam_id):
        exam = Exam.query.get_or_404(exam_id)
        result = exam_schema.dump(exam)
        return result

    def patch(self, course_id, lecture_id, exam_id):
        exam = Exam.query.get_or_404(exam_id)
        exam_dict = request.get_json(force=True)
        if 'datetime' in exam_dict:
            exam.datetime = exam_dict['datetime']
        if 'file' in exam_dict:
            exam.file = exam_dict['file']
        if 'type' in exam_dict:
            exam.type = exam_dict['type']
        dumped_exam = exam_schema.dump(exam)
        validate_errors = exam_schema.validate(dumped_exam)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            exam.update()
            return self.get(course_id, lecture_id, session_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, course_id, lecture_id, exam_id):
        exam = Exam.query.get_or_404(exam_id)
        try:
            exam.delete(exam)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class ExamResultListResource(EducationAuthRequiredResource):
    def get(self, course_id, lecture_id, exam_id):
        pagination_helper = PaginationHelper(
            request,
            query=ExamResult.query.filter_by(exam_id=exam_id),
            resource_for_url='education_api.examlistresource',
            key_name='results',
            schema=exam_result_schema)
        result = pagination_helper.paginate_query()
        return result
    
    def post(self, course_id, lecture_id, exam_id):
        request_dict = request.get_json(force=True)
        Course.query.get_or_404(course_id)
        Lecture.query.get_or_404(lecture_id)
        Exam.query.get_or_404(exam_id)
        if not request_dict:
            response = {'exams': 'No input data provided'}
            return response, status.HTTP_400_BAD_REQUEST
        errors = exam_result_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        student_id = request_dict['student_id']
        try:
            # create a new LectureSession
            exam_result = ExamResult(exam_id=exam_id, student_id=student_id, score=request_dict['score'])
            exam_result.add(exam_result)
            query = ExamResult.query.filter_by(exam_id=exam_id, student_id=student_id).first()
            result = exam_result_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class ExamResultResource(EducationAuthRequiredResource):
    def get(self, course_id, exam_id, user_id):
        exam_result = ExamResult.query.filter_by(exam_id=exam_id, student_id=user_id).first()
        result = exam_result_schema.dump(exam_result)
        return result

    def patch(self, course_id, exam_id, user_id):
        exam_result = ExamResult.query.filter_by(exam_id=exam_id, student_id=user_id).first()
        exam_dict = request.get_json(force=True)
        if 'datetime' in exam_dict:
            exam_result.datetime = exam_dict['datetime']
        if 'file' in exam_dict:
            exam_result.file = exam_dict['file']
        if 'type' in exam_dict:
            exam_result.type = exam_dict['type']
        dumped_exam_result = exam_result_schema.dump(exam_result)
        validate_errors = exam_result_schema.validate(dumped_exam_result)
        if validate_errors:
            return validate_errors, status.HTTP_400_BAD_REQUEST
        try:
            exam_result.update()
            return self.get(course_id, exam_id, user_id)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, course_id, exam_id, user_id):
        exam_result = ExamResult.query.filter_by(exam_id=exam_id, student_id=user_id).first()
        try:
            exam_result.delete(exam_result)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST


education_api.add_resource(CourseListResource, '/courses')
education_api.add_resource(CourseResource, '/courses/<int:course_id>')

education_api.add_resource(LectureListResource, '/courses/<int:course_id>/lectures')
education_api.add_resource(LectureResource, '/courses/<int:course_id>/lectures/<int:lecture_id>')

education_api.add_resource(LectureUserListResource, ('/courses/<int:course_id>/lectures/<int:lecture_id>/users'))
education_api.add_resource(LectureUserResource, ('/courses/<int:course_id>/lectures/<int:lecture_id>/users/<int:user_id>'))

education_api.add_resource(LectureSessionListResource, '/courses/<int:course_id>/lectures/<int:lecture_id>/sessions')
education_api.add_resource(LectureSessionResource, '/courses/<int:course_id>/lectures/<int:lecture_id>/sessions/<int:session_id>')

education_api.add_resource(LectureUserSessionListResource, '/courses/<int:course_id>/lectures/<int:lecture_id>/sessions/<int:session_id>/users')
education_api.add_resource(LectureUserSessionResource, '/courses/<int:course_id>/lectures/<int:lecture_id>/sessions/<int:session_id>/users/<int:user_id>')

education_api.add_resource(ExamListResource, '/courses/<int:course_id>/lectures/<int:lecture_id>/exams')
education_api.add_resource(ExamResource, '/courses/<int:course_id>/lectures/<int:lecture_id>/exams/<int:exam_id>')

education_api.add_resource(ExamResultListResource, '/courses/<int:course_id>/lectures/<int:lecture_id>/exams/<int:exam_id>/users')
education_api.add_resource(ExamResultResource, '/courses/<int:course_id>/lectures/<int:lecture_id>/exams/<int:exam_id>/users/<int:user_id>')
