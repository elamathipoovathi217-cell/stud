from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from utils.decorators import student_required
from extensions import db
from models import Student, Attendance, Marks, Risk, Subject, QuestionPaper, AnswerKey, Notification
from datetime import datetime

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    """Student dashboard"""
    student = current_user.student_record
    marks = Marks.query.filter_by(student_id=student.id).all()
    risk = Risk.query.filter_by(student_id=student.id).order_by(Risk.predicted_at.desc()).first()
    current_avg = (sum((m.total_marks or 0) for m in marks) / len(marks)) if marks else 0
    target = 15
    improvement_needed = max(0, target - current_avg)
    return render_template(
        'student/dashboard.html',
        student=student,
        marks=marks,
        risk=risk,
        current_avg=current_avg,
        improvement_needed=improvement_needed,
    )

@student_bp.route('/performance-report')
@login_required
@student_required
def performance_report():
    """View performance report"""
    student = current_user.student_record
    marks = Marks.query.filter_by(student_id=student.id).all()
    return render_template('student/performance_report.html', student=student, marks=marks)

@student_bp.route('/attendance')
@login_required
@student_required
def attendance():
    """View attendance"""
    student = current_user.student_record
    attendance = Attendance.query.filter_by(student_id=student.id).all()
    return render_template('student/attendance.html', student=student, attendance=attendance)

@student_bp.route('/marks')
@login_required
@student_required
def marks():
    """View marks"""
    student = current_user.student_record
    marks = Marks.query.filter_by(student_id=student.id).all()
    return render_template('student/marks.html', student=student, marks=marks)

@student_bp.route('/risk-status')
@login_required
@student_required
def risk_status():
    """View risk status"""
    student = current_user.student_record
    risk = Risk.query.filter_by(student_id=student.id).order_by(Risk.predicted_at.desc()).first()
    return render_template('student/risk_status.html', student=student, risk=risk)

@student_bp.route('/improvement-plan')
@login_required
@student_required
def improvement_plan():
    """View improvement plan"""
    student = current_user.student_record
    marks = Marks.query.filter_by(student_id=student.id).all()
    current_avg = (sum((m.total_marks or 0) for m in marks) / len(marks)) if marks else 0
    target = 15
    improvement_needed = max(0, target - current_avg)
    return render_template('student/improvement_plan.html', student=student, current_avg=current_avg, improvement_needed=improvement_needed)

@student_bp.route('/ai-recommendations')
@login_required
@student_required
def ai_recommendations():
    """View AI recommendations"""
    student = current_user.student_record
    return render_template('student/ai_recommendations.html', student=student)

@student_bp.route('/question-papers')
@login_required
@student_required
def question_papers():
    """View question papers"""
    student = current_user.student_record
    papers = QuestionPaper.query.filter_by(
        semester_id=student.current_semester,
        is_published=True
    ).all()
    return render_template('student/question_papers.html', papers=papers)

@student_bp.route('/answer-keys')
@login_required
@student_required
def answer_keys():
    """View answer keys"""
    student = current_user.student_record
    keys = AnswerKey.query.join(QuestionPaper).filter(
        QuestionPaper.semester_id == student.current_semester,
        AnswerKey.is_published == True
    ).all()
    return render_template('student/answer_keys.html', keys=keys)

@student_bp.route('/notifications')
@login_required
@student_required
def notifications():
    """View notifications"""
    notifications = Notification.query.filter(
        (Notification.target_role == 'student') | (Notification.target_role == 'all')
    ).order_by(Notification.created_at.desc()).all()
    return render_template('student/notifications.html', notifications=notifications)

@student_bp.route('/timetable')
@login_required
@student_required
def timetable():
    """View timetable"""
    student = current_user.student_record
    return render_template('student/timetable.html', student=student)

@student_bp.route('/profile')
@login_required
@student_required
def profile():
    """Student profile"""
    student = current_user.student_record
    return render_template('student/profile.html', student=student)