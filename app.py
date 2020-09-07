from flask import Flask


def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename)
    
    from models.UserModel import db
    db.init_app(app)
    
    from resources.users import user_api_bp
    from resources.sessions import session_api_bp
    from resources.camps import camp_api_bp
    from resources.heyats import heyat_api_bp
    from resources.educations import education_api_bp
    from resources.reports import report_api_bp

    app.register_blueprint(user_api_bp, url_prefix='/api')
    app.register_blueprint(session_api_bp, url_prefix='/api')
    app.register_blueprint(camp_api_bp, url_prefix='/api')
    app.register_blueprint(heyat_api_bp, url_prefix='/api')
    app.register_blueprint(education_api_bp, url_prefix='/api')
    app.register_blueprint(report_api_bp, url_prefix='/api')

    return app
