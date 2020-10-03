from flask import Blueprint, g, jsonify, make_response, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, Resource, abort
from sqlalchemy.exc import SQLAlchemyError
from marshmallow.exceptions import ValidationError

import status
from auth import (AuthRequiredResource, basic_auth,
                  role_authenticated, get_current_user_role, token_auth)
from helpers import PaginationHelper
from models.ReportModel import (CampReport, HeyatReport, LectureReport,
                                Multimedia, MultimediaSchema, Report,
                                ReportSchema, ReportArgsSchema)

from models.UserModel import db

report_api_bp = Blueprint('report_api', __name__)

report_api = Api(report_api_bp)

report_schema = ReportSchema()
report_args_schema = ReportArgsSchema()
multimedia_schema = MultimediaSchema()

class ReportListResource(AuthRequiredResource):
    def get(self):
        param_args = request.args
        errors = report_args_schema.validate(param_args)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        field = param_args['field']
        id = param_args['id']
        if not role_authenticated(get_current_user_role(), [field, 'admin']):
            return "Unauthorized Access", status.HTTP_403_FORBIDDEN
        if field == 'camp':
            report = CampReport.query.filter_by(camp_id=id).first()
        elif field == 'heyat':
            report = HeyatReport.query.filter_by(heyat_id=id).first()
        elif field == 'lecture':
            report = LectureReport.query.filter_by(lecture_id=id).first()
        result = report_schema.dump(report)
        return result

    def post(self):
        param_args = request.args
        errors = report_args_schema.validate(param_args)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        field = param_args['field']
        id = param_args['id']
        if not role_authenticated(get_current_user_role(), [field, 'admin']):
            return 'Unauthorized Access!', status.HTTP_403_FORBIDDEN
        request_dict = request.get_json(force=True)
        errors = report_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        description = None
        if 'description' in request_dict:
            description = request_dict['description']
        try:
            if field == 'camp':
                report = CampReport(id, reporter_id=g.user.id, description=description)
            elif field == 'heyat':
                report = HeyatReport(id, reporter_id=g.user.id, description=description)
            elif field == 'lecture':
                report = LectureReport(id, reporter_id=g.user.id, description=description)
            report.add(report)
            query = Report.query.get(report.id)
            result = report_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class ReportResource(AuthRequiredResource):
    def get(self, report_id):
        report = Report.query.get_or_404(report_id)
        if not role_authenticated(get_current_user_role(), [report.type, 'admin']):
            return 'Unauthorized Access!', status.HTTP_403_FORBIDDEN
        result = report_schema.dump(report)
        return result

    def patch(self, report_id):
        report = Report.query.get_or_404(report_id)
        if not role_authenticated(get_current_user_role(), [report.type, 'admin']):
            return 'Unauthorized Access!', status.HTTP_403_FORBIDDEN
        request_dict = request.get_json(force=True)
        errors = report_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        if 'description' in request_dict:
            report.description = request_dict['description']
        try:
            report_schema.load(report_dict, partial=True)
        except ValidationError as e:
            return e.args[0], status.HTTP_400_BAD_REQUEST
        try:
            report.update()
            return report_schema.dump(report)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, report_id):
        report = Report.query.get_or_404(report_id)
        if not role_authenticated(get_current_user_role(), [report.type, 'admin']):
            return 'Unauthorized Access!', status.HTTP_403_FORBIDDEN
        try:
            report.delete(report)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class MultimediaListResource(AuthRequiredResource):
    def get(self, report_id):
        report = Report.query.get_or_404(report_id)
        required_role = [report.type, 'admin']
        if not role_authenticated(get_current_user_role(), required_role):
            return "Unauthorized Access", status.HTTP_403_FORBIDDEN
        pagination_helper = PaginationHelper(
            request,
            query=Multimedia.query.filter_by(report_id=report_id),
            resource_for_url='report_api.multimedialistresource',
            key_name='results',
            schema=multimedia_schema)
        result = pagination_helper.paginate_query()
        return result

    def post(self, report_id):
        report = Report.query.get_or_404(report_id)
        required_role = [report.type, 'admin']
        if not role_authenticated(get_current_user_role(), required_role):
            return "Unauthorized Access", status.HTTP_403_FORBIDDEN
        request_dict = request.get_json(force=True)
        errors = multimedia_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        try:
            multimedia = Multimedia(path=request_dict['path'], format=request_dict['format'], report_id=report_id)
            multimedia.add(multimedia)
            query = Multimedia.query.get(multimedia.id)
            result = multimedia_schema.dump(query)
            return result, status.HTTP_201_CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

class MultimediaResource(AuthRequiredResource):
    def get(self, report_id, multimedia_id):
        report = Report.query.get_or_404(report_id)
        required_role = [report.type, 'admin']
        if not role_authenticated(get_current_user_role(), required_role):
            return "Unauthorized Access", status.HTTP_403_FORBIDDEN
        multimedia = Multimedia.query.get_or_404(multimedia_id)
        return multimedia_schema.dump(multimedia)

    def patch(self, report_id, multimedia_id):
        report = Report.query.get_or_404(report_id)
        required_role = [report.type, 'admin']
        if not role_authenticated(get_current_user_role(), required_role):
            return "Unauthorized Access", status.HTTP_403_FORBIDDEN
        multimedia = Multimedia.query.get_or_404(multimedia_id)
        request_dict = request.get_json(force=True)
        errors = multimedia_schema.validate(request_dict)
        if errors:
            return errors, status.HTTP_400_BAD_REQUEST
        if 'path' in request_dict:
            multimedia.path = request_dict['path']
        if 'format' in request_dict:
            multimedia.format = request_dict['format']
        try:
            multimedia_schema.load(multimedia_dict, partial=True)
        except ValidationError as e:
            return e.args[0], status.HTTP_400_BAD_REQUEST
        try:
            multimedia.update()
            return multimedia_schema.dump(multimedia)
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

    def delete(self, report_id, multimedia_id):
        report = Report.query.get_or_404(report_id)
        required_role = [report.type, 'admin']
        if not role_authenticated(get_current_user_role(), required_role):
            return 'Unauthorized Access!', status.HTTP_403_FORBIDDEN
        multimedia = Multimedia.query.get_or_404(multimedia_id)
        try:
            multimedia.delete(multimedia)
            # response = make_response()
            return '', status.HTTP_204_NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            resp = {"error": str(e)}
            return resp, status.HTTP_400_BAD_REQUEST

report_api.add_resource(ReportListResource, '/report')
report_api.add_resource(ReportResource, '/report/<int:report_id>')
report_api.add_resource(MultimediaListResource, '/report/<int:report_id>/multimedias')
report_api.add_resource(MultimediaResource, '/report/<int:report_id>/multimedias/<int:multimedia_id>')