from flask import Blueprint, render_template
from models import Timetable, RoomAllocation, InvigilatorAllocation, Exam, Department, Notification
from datetime import datetime

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    """Public home page with key allocations and announcements."""
    upcoming_exams = Exam.query.filter(Exam.exam_date >= datetime.now().date()).order_by(Exam.exam_date).limit(8).all()
    room_allocations = RoomAllocation.query.join(Exam).filter(Exam.exam_date >= datetime.now().date()).order_by(Exam.exam_date).limit(8).all()
    invigilations = InvigilatorAllocation.query.join(Exam).filter(Exam.exam_date >= datetime.now().date()).order_by(Exam.exam_date).limit(8).all()
    notices = Notification.query.filter_by(is_published=True).order_by(Notification.created_at.desc()).limit(5).all()
    return render_template(
        'index.html',
        upcoming_exams=upcoming_exams,
        room_allocations=room_allocations,
        invigilations=invigilations,
        notices=notices,
    )


@public_bp.route('/public-timetable')
def public_timetable():
    departments = Department.query.all()
    exams = Exam.query.filter(Exam.exam_date >= datetime.now().date()).order_by(Exam.exam_date).all()
    return render_template('public/public_timetable.html', departments=departments, exams=exams)


@public_bp.route('/public-room-allocation')
def public_room_allocation():
    exams = Exam.query.filter(Exam.exam_date >= datetime.now().date()).order_by(Exam.exam_date).all()
    return render_template('public/public_room_allocation.html', exams=exams)


@public_bp.route('/public-invigilator')
def public_invigilator():
    allocations = InvigilatorAllocation.query.join(Exam).filter(
        Exam.exam_date >= datetime.now().date()
    ).order_by(Exam.exam_date).all()
    return render_template('public/public_invigilator.html', allocations=allocations)


@public_bp.route('/notifications')
def notifications():
    notifications = Notification.query.filter_by(is_published=True).order_by(Notification.created_at.desc()).all()
    return render_template('public/notifications.html', notifications=notifications)


@public_bp.route('/announcements')
def announcements():
    announcements = Notification.query.filter_by(is_published=True).order_by(Notification.created_at.desc()).all()
    return render_template('public/announcements.html', announcements=announcements)


@public_bp.route('/calendar')
def calendar():
    return render_template('public/calendar.html')


@public_bp.route('/contact')
def contact():
    return render_template('public/contact.html')


@public_bp.route('/about')
def about():
    return render_template('public/about.html')
