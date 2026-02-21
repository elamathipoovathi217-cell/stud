# app.py
from flask import Flask, render_template
from config import config
from extensions import db, login_manager, migrate, mail  # Import from extensions
import os

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with the app - THIS IS CRITICAL
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User  # Import here to avoid circular imports
        return User.query.get(int(user_id))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from extensions import db
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Root route
    @app.route('/')
    def index():
        return render_template('index.html')
    @app.context_processor
    def utility_processor():
     
     return {'now': datetime.now}  # This passes the value, not the function
    from datetime import datetime
    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.principal_routes import principal_bp
    from routes.hod_routes import hod_bp
    from routes.teacher_routes import teacher_bp
    from routes.student_routes import student_bp
    from routes.coordinator_routes import coordinator_bp
    from routes.public_routes import public_bp
    from routes.api_routes import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(principal_bp, url_prefix='/principal')
    app.register_blueprint(hod_bp, url_prefix='/hod')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(coordinator_bp, url_prefix='/coordinator')
    app.register_blueprint(public_bp, url_prefix='/')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
    