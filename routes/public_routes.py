from flask import Blueprint, render_template, jsonify, request
from models import Timetable, RoomAllocation, InvigilatorAllocation, Exam, Subject, User, Department
from extensions import db
from datetime import datetime

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    """Public home page"""
    return render_template('index.html')

@public_bp.route('/public-timetable')
def public_timetable():
    """View public timetable"""
    departments = Department.query.all()
    return render_template('public/public_timetable.html', departments=departments)

@public_bp.route('/public-room-allocation')
def public_room_allocation():
    """View public room allocations"""
    exams = Exam.query.filter(Exam.exam_date >= datetime.now().date()).order_by(Exam.exam_date).all()
    return render_template('public/public_room_allocation.html', exams=exams)

@public_bp.route('/public-invigilator')
def public_invigilator():
    """View public invigilator assignments"""
    allocations = InvigilatorAllocation.query.join(Exam).filter(
        Exam.exam_date >= datetime.now().date()
    ).order_by(Exam.exam_date).all()
    return render_template('public/public_invigilator.html', allocations=allocations)

@public_bp.route('/notifications')
def notifications():
    """View public notifications"""
    return render_template('public/notifications.html')

@public_bp.route('/announcements')
def announcements():
    """View public announcements"""
    return render_template('public/announcements.html')

@public_bp.route('/calendar')
def calendar():
    """View academic calendar"""
    return render_template('public/calendar.html')

@public_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('public/contact.html')

@public_bp.route('/about')
def about():
    """About page"""
    return render_template('public/about.html')