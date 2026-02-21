from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from utils.decorators import principal_required
from extensions import db
from models import User, Student, Department, Subject, Attendance, Marks, Risk
from datetime import datetime
from sqlalchemy import func

principal_bp = Blueprint('principal', __name__)

@principal_bp.route('/dashboard')
@login_required
@principal_required
def dashboard():
    """Principal dashboard"""
    return render_template('principal/dashboard.html')

@principal_bp.route('/analytics')
@login_required
@principal_required
def analytics():
    """Institutional analytics"""
    return render_template('principal/analytics.html')

@principal_bp.route('/reports')
@login_required
@principal_required
def reports():
    """Generate reports"""
    return render_template('principal/reports.html')

@principal_bp.route('/departments')
@login_required
@principal_required
def departments():
    """View all departments"""
    departments = Department.query.all()
    return render_template('principal/departments.html', departments=departments)

@principal_bp.route('/teachers')
@login_required
@principal_required
def teachers():
    """View all teachers"""
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('principal/teachers.html', teachers=teachers)

@principal_bp.route('/students')
@login_required
@principal_required
def students():
    """View all students"""
    students = Student.query.all()
    return render_template('principal/students.html', students=students)

@principal_bp.route('/risk-analysis')
@login_required
@principal_required
def risk_analysis():
    """View risk analysis across institution"""
    return render_template('principal/risk_analysis.html')

@principal_bp.route('/ml-predictions')
@login_required
@principal_required
def ml_predictions():
    """View ML predictions"""
    return render_template('principal/ml_predictions.html')

@principal_bp.route('/ai-insights')
@login_required
@principal_required
def ai_insights():
    """View AI insights"""
    return render_template('principal/ai_insights.html')

@principal_bp.route('/settings')
@login_required
@principal_required
def settings():
    """System settings"""
    return render_template('principal/settings.html')