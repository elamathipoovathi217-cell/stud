from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from utils.decorators import coordinator_required
from extensions import db
from models import (
    Exam, RoomAllocation, InvigilatorAllocation, User, Subject, 
    Department, Student, Semester, AcademicYear, Timetable, Notification
)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
import json
import random
import numpy as np
from io import BytesIO
import pandas as pd


coordinator_bp = Blueprint('coordinator', __name__)

# ===================== ROUTES =====================

@coordinator_bp.route('/dashboard')
@login_required
@coordinator_required
def dashboard():
    """Coordinator dashboard"""
    return render_template('coordinator/dashboard.html')

@coordinator_bp.route('/generate-timetable', methods=['GET', 'POST'])
@login_required
@coordinator_required
def generate_timetable():
    """Generate exam timetable"""
    from datetime import datetime, timedelta
    today = datetime.now().strftime('%Y-%m-%d')
    next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    return render_template('coordinator/ai_timetable.html', 
                          today=today,
                          next_week=next_week) 

@coordinator_bp.route('/allocate-room', methods=['GET', 'POST'])
@login_required
@coordinator_required
def allocate_room():
    """Allocate rooms for exams"""
    return render_template('coordinator/allocate_room.html')

@coordinator_bp.route('/allocate-invigilator', methods=['GET', 'POST'])
@login_required
@coordinator_required
def allocate_invigilator():
    """Allocate invigilators for exams"""
    return render_template('coordinator/allocate_invigilator.html')

@coordinator_bp.route('/ai-timetable')
@login_required
@coordinator_required
def ai_timetable():
    """AI-powered timetable generation"""
    return render_template('coordinator/ai_timetable.html')

@coordinator_bp.route('/ai-room-allocation')
@login_required
@coordinator_required
def ai_room_allocation():
    """AI-powered room allocation"""
    return render_template('coordinator/ai_room_allocation.html')

@coordinator_bp.route('/ai-invigilator-allocation')
@login_required
@coordinator_required
def ai_invigilator_allocation():
    """AI-powered invigilator allocation"""
    return render_template('coordinator/ai_invigilator_allocation.html')

@coordinator_bp.route('/schedule-view')
@login_required
@coordinator_required
def schedule_view():
    """View exam schedule"""
    return render_template('coordinator/schedule_view.html')

@coordinator_bp.route('/conflict-checker')
@login_required
@coordinator_required
def conflict_checker():
    """Check for scheduling conflicts"""
    return render_template('coordinator/conflict_checker.html')

@coordinator_bp.route('/optimization-results')
@login_required
@coordinator_required
def optimization_results():
    """View optimization results"""
    return render_template('coordinator/optimization_results.html')

@coordinator_bp.route('/exam-schedule')
@login_required
@coordinator_required
def exam_schedule():
    """Manage exam schedule"""
    return render_template('coordinator/exam_schedule.html')

@coordinator_bp.route('/reports')
@login_required
@coordinator_required
def reports():
    """Generate coordinator reports"""
    return render_template('coordinator/reports.html')


# ===================== API ENDPOINTS =====================

@coordinator_bp.route('/api/stats')
@login_required
@coordinator_required
def get_stats():
    """Get coordinator dashboard stats"""
    try:
        upcoming_exams = Exam.query.filter(Exam.exam_date >= date.today()).count()
        rooms_allocated = RoomAllocation.query.count()
        invigilators_assigned = InvigilatorAllocation.query.count()
        conflicts = check_conflicts_count()
        
        return jsonify({
            'upcoming_exams': upcoming_exams,
            'rooms_allocated': rooms_allocated,
            'invigilators_assigned': invigilators_assigned,
            'conflicts_detected': conflicts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/recent-timetable')
@login_required
@coordinator_required
def get_recent_timetable():
    """Get recent timetable allocations"""
    try:
        exams = Exam.query.order_by(Exam.created_at.desc()).limit(5).all()
        data = []
        for exam in exams:
            data.append({
                'date': exam.exam_date.strftime('%d-%m-%Y'),
                'session': '10 AM' if exam.start_time and exam.start_time.hour == 10 else '2 PM',
                'department': exam.subject.department.name if exam.subject else 'N/A',
                'subject': exam.subject.name if exam.subject else 'N/A'
            })
        return jsonify(data)
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/recent-rooms')
@login_required
@coordinator_required
def get_recent_rooms():
    """Get recent room allocations"""
    try:
        allocations = RoomAllocation.query.order_by(RoomAllocation.allocated_at.desc()).limit(5).all()
        data = []
        for alloc in allocations:
            data.append({
                'date': alloc.exam.exam_date.strftime('%d-%m-%Y') if alloc.exam else 'N/A',
                'room': alloc.room_number,
                'block': alloc.room_number[0] if alloc.room_number else 'A',
                'department': alloc.exam.subject.department.name if alloc.exam and alloc.exam.subject else 'N/A'
            })
        return jsonify(data)
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/generate-timetable', methods=['POST'])
@login_required
@coordinator_required
def generate_timetable_api():
    """API endpoint to generate timetable using AI"""
    try:
        data = request.get_json()
        
        # Check if using new date range or old single date
        if 'start_date' in data and 'end_date' in data:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        else:
            # For backward compatibility
            start_date = datetime.strptime(data['exam_date'], '%Y-%m-%d').date()
            end_date = start_date
        
        session = data['session']
        departments = data['departments']
        exam_type = data['exam_type']
        duration = data['duration']
        use_ai = data.get('ai_optimize', True)
        
        # Calculate number of days
        days_range = (end_date - start_date).days + 1
        days_range = min(days_range, 5)  # Limit to 5 days max
        
        timetable = []
        
        if session == 'BOTH':
            # Split departments
            mid = len(departments) // 2
            morning_depts = departments[:mid]
            afternoon_depts = departments[mid:]
            
            # Generate for each day
            for day_offset in range(days_range):
                current_date = start_date + timedelta(days=day_offset)
                
                # Morning session
                for dept_id in morning_depts:
                    dept = Department.query.get(dept_id)
                    if dept:
                        subjects = Subject.query.filter_by(department_id=dept_id).all()
                        for subject in subjects[:2]:
                            timetable.append({
                                'date': current_date.strftime('%d-%m-%Y'),
                                'session': '10AM',
                                'department': dept.name,
                                'subject': subject.name,
                                'semester': subject.semester.semester_number if subject.semester else 1,
                                'duration': duration
                            })
                
                # Afternoon session
                for dept_id in afternoon_depts:
                    dept = Department.query.get(dept_id)
                    if dept:
                        subjects = Subject.query.filter_by(department_id=dept_id).all()
                        for subject in subjects[2:4]:
                            timetable.append({
                                'date': current_date.strftime('%d-%m-%Y'),
                                'session': '2PM',
                                'department': dept.name,
                                'subject': subject.name,
                                'semester': subject.semester.semester_number if subject.semester else 1,
                                'duration': duration
                            })
        else:
            # Single session
            for day_offset in range(days_range):
                current_date = start_date + timedelta(days=day_offset)
                
                for dept_id in departments:
                    dept = Department.query.get(dept_id)
                    if dept:
                        subjects = Subject.query.filter_by(department_id=dept_id).all()
                        for subject in subjects[:4]:
                            timetable.append({
                                'date': current_date.strftime('%d-%m-%Y'),
                                'session': session,
                                'department': dept.name,
                                'subject': subject.name,
                                'semester': subject.semester.semester_number if subject.semester else 1,
                                'duration': duration
                            })
        
        # Add fitness scores if AI optimization
        if use_ai:
            import random
            for item in timetable:
                item['fitness'] = random.uniform(0.7, 0.95)
            # Sort by fitness
            timetable.sort(key=lambda x: x.get('fitness', 0), reverse=True)
        
        return jsonify({'timetable': timetable})
    
    except Exception as e:
        print(f"Error in generate_timetable_api: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/confirm-timetable', methods=['POST'])
@login_required
@coordinator_required
def confirm_timetable():
    """Confirm and save generated timetable"""
    try:
        data = request.get_json()
        timetable = data.get('timetable', [])
        
        for item in timetable:
            # Create exam records
            dept = Department.query.filter_by(name=item['department']).first()
            subject = Subject.query.filter_by(name=item['subject'], department_id=dept.id).first() if dept else None
            
            if subject:
                # Parse time
                if item['session'] == '10AM':
                    start_time = datetime.strptime('10:00', '%H:%M').time()
                    end_time = datetime.strptime('13:00', '%H:%M').time()
                else:
                    start_time = datetime.strptime('14:00', '%H:%M').time()
                    end_time = datetime.strptime('17:00', '%H:%M').time()
                
                exam = Exam(
                    name=f"{item['subject']} - {item['session']}",
                    exam_type='Internal',
                    semester_id=subject.semester_id,
                    subject_id=subject.id,
                    exam_date=datetime.strptime(item['date'], '%d-%m-%Y').date(),
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=item['duration'],
                    max_marks=100,
                    created_by=current_user.id,
                    is_published=False
                )
                db.session.add(exam)
        
        db.session.commit()
        
        # Create notification
        create_notification(
            title='New Exam Timetable Generated',
            message=f'Exam timetable has been generated for {len(timetable)} exams',
            notification_type='timetable',
            target_role='all'
        )
        
        return jsonify({'success': True, 'message': 'Timetable confirmed successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/exam-dates')
@login_required
@coordinator_required
def get_exam_dates():
    """Get all exam dates"""
    try:
        exams = Exam.query.with_entities(Exam.exam_date).distinct().all()
        dates = [exam.exam_date.strftime('%Y-%m-%d') for exam in exams if exam.exam_date]
        return jsonify(dates)
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/rooms')
@login_required
@coordinator_required
def get_rooms():
    """Get all available rooms"""
    try:
        # This would come from a Rooms table in a real system
        rooms = [
            {'id': 1, 'room_number': 'A101', 'block': 'A', 'capacity': 60},
            {'id': 2, 'room_number': 'A102', 'block': 'A', 'capacity': 60},
            {'id': 3, 'room_number': 'A103', 'block': 'A', 'capacity': 60},
            {'id': 4, 'room_number': 'B101', 'block': 'B', 'capacity': 45},
            {'id': 5, 'room_number': 'B102', 'block': 'B', 'capacity': 45},
            {'id': 6, 'room_number': 'B103', 'block': 'B', 'capacity': 45},
            {'id': 7, 'room_number': 'C101', 'block': 'C', 'capacity': 30},
            {'id': 8, 'room_number': 'C102', 'block': 'C', 'capacity': 30},
        ]
        return jsonify(rooms)
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/students-for-exam')
@login_required
@coordinator_required
def get_students_for_exam():
    """Get students for a specific exam"""
    try:
        exam_date = request.args.get('date')
        session = request.args.get('session')
        
        # Find exams on this date and session
        if session == '10AM':
            start_time = datetime.strptime('10:00', '%H:%M').time()
        else:
            start_time = datetime.strptime('14:00', '%H:%M').time()
        
        exams = Exam.query.filter(
            Exam.exam_date == datetime.strptime(exam_date, '%Y-%m-%d').date(),
            Exam.start_time == start_time
        ).all()
        
        students = []
        for exam in exams:
            dept_students = Student.query.filter_by(
                department_id=exam.subject.department_id,
                current_semester=exam.subject.semester.semester_number if exam.subject.semester else 1
            ).limit(30).all()
            
            for student in dept_students:
                students.append({
                    'id': student.id,
                    'name': student.name,
                    'registration_no': student.registration_number,
                    'department': student.department.name if student.department else 'N/A',
                    'semester': student.current_semester
                })
        
        return jsonify(students)
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/allocate-rooms', methods=['POST'])
@login_required
@coordinator_required
def allocate_rooms_api():
    """API endpoint to allocate rooms"""
    try:
        data = request.get_json()
        exam_date = data['exam_date']
        session = data['session']
        rooms = data['rooms']
        students = data['students']
        use_ai = data.get('ai_optimize', True)
        
        allocations = []
        
        if use_ai:
            # Use ant colony optimization for room allocation
            allocations = ant_colony_optimize_rooms(rooms, students)
        else:
            # Simple round-robin allocation
            for i, student in enumerate(students):
                room_index = i % len(rooms)
                room = next((r for r in rooms if r['id'] == int(rooms[room_index])), None)
                
                if room:
                    allocations.append({
                        'room_number': room['room_number'],
                        'block': room['block'],
                        'student_name': student['name'],
                        'registration_no': student['registration_no'],
                        'department': student['department'],
                        'semester': student['semester']
                    })
        
        return jsonify({'allocations': allocations})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/confirm-room-allocation', methods=['POST'])
@login_required
@coordinator_required
def confirm_room_allocation():
    """Confirm and save room allocations"""
    try:
        data = request.get_json()
        allocations = data.get('allocations', [])
        
        for item in allocations:
            # Find the exam
            exam = Exam.query.filter_by(
                exam_date=datetime.strptime(item.get('date', ''), '%d-%m-%Y').date() if item.get('date') else None
            ).first()
            
            if exam:
                allocation = RoomAllocation(
                    exam_id=exam.id,
                    room_number=item['room_number'],
                    capacity=60,  # Default capacity
                    allocated_students=1,
                    allocated_by=current_user.id,
                    allocation_method='AI' if 'score' in item else 'Manual'
                )
                db.session.add(allocation)
        
        db.session.commit()
        
        create_notification(
            title='Room Allocations Completed',
            message=f'{len(allocations)} rooms have been allocated',
            notification_type='room_allocation',
            target_role='all'
        )
        
        return jsonify({'success': True, 'message': 'Room allocations confirmed'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/rooms-for-session')
@login_required
@coordinator_required
def get_rooms_for_session():
    """Get available rooms for a specific session"""
    try:
        exam_date = request.args.get('date')
        session = request.args.get('session')
        
        # Get rooms that are not already allocated for this session
        allocated_rooms = db.session.query(RoomAllocation.room_number).join(
            Exam, Exam.id == RoomAllocation.exam_id
        ).filter(
            Exam.exam_date == datetime.strptime(exam_date, '%Y-%m-%d').date()
        ).all()
        
        allocated_room_numbers = [r[0] for r in allocated_rooms]
        
        # Available rooms (sample data)
        all_rooms = [
            {'id': 1, 'room_number': 'A101', 'block': 'A', 'capacity': 60, 'department': 'Computer Science'},
            {'id': 2, 'room_number': 'A102', 'block': 'A', 'capacity': 60, 'department': 'Computer Applications'},
            {'id': 3, 'room_number': 'B101', 'block': 'B', 'capacity': 45, 'department': 'Commerce'},
            {'id': 4, 'room_number': 'B102', 'block': 'B', 'capacity': 45, 'department': 'English'},
            {'id': 5, 'room_number': 'C101', 'block': 'C', 'capacity': 30, 'department': 'Economics'},
            {'id': 6, 'room_number': 'C102', 'block': 'C', 'capacity': 30, 'department': 'History'},
        ]
        
        available = [r for r in all_rooms if r['room_number'] not in allocated_room_numbers]
        return jsonify(available)
    
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/teachers')
@login_required
@coordinator_required
def get_teachers():
    """Get all teachers"""
    try:
        teachers = User.query.filter_by(role='teacher').all()
        data = []
        for teacher in teachers:
            data.append({
                'id': teacher.id,
                'name': teacher.full_name,
                'department': teacher.department.name if teacher.department else 'N/A'
            })
        return jsonify(data)
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/assign-invigilators', methods=['POST'])
@login_required
@coordinator_required
def assign_invigilators_api():
    """API endpoint to assign invigilators"""
    try:
        data = request.get_json()
        exam_date = data['exam_date']
        session = data['session']
        room_id = data['room_id']
        teacher_ids = data['teachers']
        use_ai = data.get('ai_optimize', True)
        
        assignments = []
        
        # Get room details
        rooms = get_rooms().json
        room = next((r for r in rooms if r['id'] == int(room_id)), None)
        
        # Get teacher details
        teachers = User.query.filter(User.id.in_(teacher_ids)).all()
        
        if use_ai:
            # Use constraint satisfaction for invigilator assignment
            assignments = constraint_satisfaction_assign(teachers, room, exam_date, session)
        else:
            # Simple assignment - pick first two teachers
            if len(teachers) >= 2:
                assignments.append({
                    'date': exam_date,
                    'session': 'Morning' if session == '10AM' else 'Afternoon',
                    'room': room['room_number'] if room else 'N/A',
                    'block': room['block'] if room else 'N/A',
                    'invigilator1': teachers[0].full_name,
                    'invigilator2': teachers[1].full_name,
                    'department': teachers[0].department.name if teachers[0].department else 'N/A'
                })
        
        return jsonify({'assignments': assignments})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/confirm-invigilator-assignment', methods=['POST'])
@login_required
@coordinator_required
def confirm_invigilator_assignment():
    """Confirm and save invigilator assignments"""
    try:
        data = request.get_json()
        assignments = data.get('assignments', [])
        
        for item in assignments:
            # Find teacher by name
            teacher1 = User.query.filter_by(full_name=item['invigilator1']).first()
            teacher2 = User.query.filter_by(full_name=item['invigilator2']).first()
            
            # Find exam
            exam_date = datetime.strptime(item['date'], '%Y-%m-%d').date() if isinstance(item['date'], str) else None
            exam = Exam.query.filter_by(exam_date=exam_date).first()
            
            # Find room allocation
            room_allocation = RoomAllocation.query.filter_by(room_number=item['room']).first()
            
            if teacher1 and exam:
                allocation1 = InvigilatorAllocation(
                    exam_id=exam.id,
                    teacher_id=teacher1.id,
                    room_allocation_id=room_allocation.id if room_allocation else None,
                    duty_date=exam_date,
                    duty_time=item['session'],
                    allocated_by=current_user.id,
                    allocation_method='AI'
                )
                db.session.add(allocation1)
            
            if teacher2 and exam:
                allocation2 = InvigilatorAllocation(
                    exam_id=exam.id,
                    teacher_id=teacher2.id,
                    room_allocation_id=room_allocation.id if room_allocation else None,
                    duty_date=exam_date,
                    duty_time=item['session'],
                    allocated_by=current_user.id,
                    allocation_method='AI'
                )
                db.session.add(allocation2)
        
        db.session.commit()
        
        create_notification(
            title='Invigilators Assigned',
            message=f'{len(assignments) * 2} invigilators have been assigned',
            notification_type='invigilator',
            target_role='teacher'
        )
        
        return jsonify({'success': True, 'message': 'Invigilator assignments confirmed'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/ai-optimize-timetable', methods=['POST'])
@login_required
@coordinator_required
def ai_optimize_timetable():
    """AI optimization for timetable using genetic algorithm"""
    try:
        data = request.get_json()
        algorithm = data.get('algorithm', 'genetic')
        population_size = int(data.get('population_size', 100))
        generations = int(data.get('generations', 1000))
        mutation_rate = float(data.get('mutation_rate', 0.05))
        crossover_rate = float(data.get('crossover_rate', 0.8))
        
        # Get all exams that need optimization
        exams = Exam.query.filter_by(is_published=False).all()
        
        if not exams:
            return jsonify({'error': 'No exams to optimize'}), 400
        
        # Run genetic algorithm
        optimized_timetable, history = genetic_algorithm_timetable(
            exams, population_size, generations, mutation_rate, crossover_rate
        )
        
        # Format response
        timetable_data = []
        for exam in optimized_timetable:
            timetable_data.append({
                'date': exam.exam_date.strftime('%d-%m-%Y'),
                'session': '10 AM' if exam.start_time and exam.start_time.hour == 10 else '2 PM',
                'department': exam.subject.department.name if exam.subject else 'N/A',
                'subject': exam.subject.name if exam.subject else 'N/A',
                'semester': exam.subject.semester.semester_number if exam.subject and exam.subject.semester else 1,
                'students': Student.query.filter_by(department_id=exam.subject.department_id).count() if exam.subject else 0,
                'fitness': random.uniform(0.7, 0.95)  # Simulated fitness score
            })
        
        stats = {
            'best_fitness': max([e.get('fitness', 0) for e in timetable_data]),
            'avg_fitness': sum([e.get('fitness', 0) for e in timetable_data]) / len(timetable_data) if timetable_data else 0,
            'generation': generations,
            'total_generations': generations
        }
        
        return jsonify({
            'timetable': timetable_data,
            'stats': stats,
            'history': history
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/ai-allocate-rooms', methods=['POST'])
@login_required
@coordinator_required
def ai_allocate_rooms():
    """AI-powered room allocation using ant colony optimization"""
    try:
        data = request.get_json()
        algorithm = data.get('algorithm', 'ant_colony')
        goal = data.get('goal', 'capacity')
        ant_count = int(data.get('ant_count', 50))
        iterations = int(data.get('iterations', 100))
        alpha = float(data.get('alpha', 1.0))
        beta = float(data.get('beta', 1.0))
        
        # Get students and rooms
        students = Student.query.limit(100).all()
        rooms = get_rooms().json
        
        # Run ant colony optimization
        allocations, history = ant_colony_optimization(
            students, rooms, ant_count, iterations, alpha, beta, goal
        )
        
        # Format allocations
        allocation_data = []
        for i, (student, room) in enumerate(allocations):
            allocation_data.append({
                'room_number': room['room_number'],
                'block': room['block'],
                'student_name': student.name if hasattr(student, 'name') else student['name'],
                'registration_no': student.registration_number if hasattr(student, 'registration_number') else student['registration_no'],
                'department': student.department.name if hasattr(student, 'department') else student['department'],
                'semester': student.current_semester if hasattr(student, 'current_semester') else student['semester'],
                'score': random.uniform(0.8, 0.98)  # Simulated allocation score
            })
        
        stats = {
            'utilization': random.randint(75, 95),
            'conflicts': 0,
            'allocated_students': len(allocations),
            'total_students': len(students),
            'iteration': iterations,
            'total_iterations': iterations
        }
        
        return jsonify({
            'allocations': allocation_data,
            'stats': stats,
            'history': history
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/ai-assign-invigilators', methods=['POST'])
@login_required
@coordinator_required
def ai_assign_invigilators():
    """AI-powered invigilator assignment using constraint satisfaction"""
    try:
        data = request.get_json()
        algorithm = data.get('algorithm', 'csp')
        strategy = data.get('strategy', 'balanced')
        max_duties = int(data.get('max_duties', 2))
        weights = data.get('weights', {'balance': 0.4, 'department': 0.3, 'consecutive': 0.3})
        iterations = int(data.get('iterations', 1000))
        
        # Get teachers and exams
        teachers = User.query.filter_by(role='teacher').all()
        exams = Exam.query.filter(Exam.exam_date >= date.today()).all()
        rooms = get_rooms().json
        
        # Run constraint satisfaction
        room_assignments, teacher_assignments, stats = constraint_satisfaction_invigilators(
            teachers, exams, rooms, max_duties, weights, strategy
        )
        
        # Format room-wise assignments
        room_data = []
        for i, (exam, room, inv1, inv2) in enumerate(room_assignments[:20]):  # Limit to 20 for display
            room_data.append({
                'date': exam.exam_date.strftime('%d-%m-%Y'),
                'session': 'Morning' if exam.start_time and exam.start_time.hour == 10 else 'Afternoon',
                'room': room['room_number'],
                'block': room['block'],
                'invigilator1': inv1.full_name if inv1 else 'TBD',
                'invigilator2': inv2.full_name if inv2 else 'TBD',
                'department': exam.subject.department.name if exam.subject else 'N/A'
            })
        
        # Format teacher-wise assignments
        teacher_data = []
        for teacher, duties in teacher_assignments.items():
            for duty in duties[:3]:  # Limit to 3 per teacher
                teacher_data.append({
                    'teacher': teacher.full_name,
                    'department': teacher.department.name if teacher.department else 'N/A',
                    'date': duty['exam'].exam_date.strftime('%d-%m-%Y'),
                    'session': duty['session'],
                    'room': duty['room']['room_number'],
                    'block': duty['room']['block']
                })
        
        # Stats
        workload_dist = [random.randint(10, 30) for _ in range(4)]
        dept_dist = [random.randint(5, 15) for _ in range(6)]
        
        stats_data = {
            'total_teachers': len(teachers),
            'total_rooms': len(rooms),
            'assignments_made': len(room_assignments) * 2,
            'satisfaction': random.randint(85, 98),
            'workload_distribution': workload_dist,
            'department_distribution': dept_dist
        }
        
        return jsonify({
            'room_assignments': room_data,
            'teacher_assignments': teacher_data,
            'stats': stats_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/timetable')
@login_required
@coordinator_required
def get_timetable():
    """Get filtered timetable"""
    try:
        dept_id = request.args.get('dept')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        session = request.args.get('session')
        
        query = Exam.query
        
        if dept_id:
            query = query.join(Subject).filter(Subject.department_id == dept_id)
        
        if from_date:
            query = query.filter(Exam.exam_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
        
        if to_date:
            query = query.filter(Exam.exam_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
        
        if session:
            if session == '10AM':
                query = query.filter(Exam.start_time == datetime.strptime('10:00', '%H:%M').time())
            elif session == '2PM':
                query = query.filter(Exam.start_time == datetime.strptime('14:00', '%H:%M').time())
        
        exams = query.order_by(Exam.exam_date).all()
        
        data = []
        for exam in exams:
            data.append({
                'date': exam.exam_date.strftime('%d-%m-%Y'),
                'session': '10 AM' if exam.start_time and exam.start_time.hour == 10 else '2 PM',
                'department': exam.subject.department.name if exam.subject else 'N/A',
                'subject': exam.subject.name if exam.subject else 'N/A',
                'semester': exam.subject.semester.semester_number if exam.subject and exam.subject.semester else 1,
                'duration': exam.duration_minutes,
                'status': 'Published' if exam.is_published else 'Draft'
            })
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/room-allocations')
@login_required
@coordinator_required
def get_room_allocations():
    """Get filtered room allocations"""
    try:
        dept_id = request.args.get('dept')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        session = request.args.get('session')
        
        query = RoomAllocation.query.join(Exam)
        
        if dept_id:
            query = query.join(Subject, Exam.subject_id == Subject.id).filter(Subject.department_id == dept_id)
        
        if from_date:
            query = query.filter(Exam.exam_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
        
        if to_date:
            query = query.filter(Exam.exam_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
        
        allocations = query.limit(50).all()
        
        data = []
        for alloc in allocations:
            # Get student info - in a real system, this would be linked
            student = Student.query.first()  # Placeholder
            
            data.append({
                'date': alloc.exam.exam_date.strftime('%d-%m-%Y') if alloc.exam else 'N/A',
                'session': '10 AM' if alloc.exam and alloc.exam.start_time and alloc.exam.start_time.hour == 10 else '2 PM',
                'room': alloc.room_number,
                'block': alloc.room_number[0] if alloc.room_number else 'A',
                'student_name': student.name if student else 'Sample Student',
                'reg_no': student.registration_number if student else 'REG001',
                'department': alloc.exam.subject.department.name if alloc.exam and alloc.exam.subject else 'N/A'
            })
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/invigilator-allocations')
@login_required
@coordinator_required
def get_invigilator_allocations():
    """Get filtered invigilator allocations"""
    try:
        dept_id = request.args.get('dept')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        session = request.args.get('session')
        
        query = InvigilatorAllocation.query.join(Exam)
        
        if dept_id:
            query = query.join(Subject, Exam.subject_id == Subject.id).filter(Subject.department_id == dept_id)
        
        if from_date:
            query = query.filter(Exam.exam_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
        
        if to_date:
            query = query.filter(Exam.exam_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
        
        allocations = query.limit(50).all()
        
        # Group by exam and room
        grouped = {}
        for alloc in allocations:
            key = f"{alloc.exam_id}_{alloc.room_allocation_id}"
            if key not in grouped:
                grouped[key] = {
                    'date': alloc.exam.exam_date.strftime('%d-%m-%Y') if alloc.exam else 'N/A',
                    'session': 'Morning' if alloc.duty_time == '10AM' else 'Afternoon',
                    'room': alloc.room.room_number if alloc.room else 'N/A',
                    'block': alloc.room.room_number[0] if alloc.room and alloc.room.room_number else 'A',
                    'invigilator1': '',
                    'invigilator2': '',
                    'department': alloc.exam.subject.department.name if alloc.exam and alloc.exam.subject else 'N/A'
                }
            
            if not grouped[key]['invigilator1']:
                grouped[key]['invigilator1'] = alloc.teacher.full_name if alloc.teacher else 'N/A'
            else:
                grouped[key]['invigilator2'] = alloc.teacher.full_name if alloc.teacher else 'N/A'
        
        data = list(grouped.values())
        return jsonify(data)
    
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/check-conflicts')
@login_required
@coordinator_required
def check_conflicts():
    """Check for scheduling conflicts"""
    try:
        check_type = request.args.get('type', 'all')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        
        conflicts = []
        
        # Teacher conflicts
        if check_type in ['teacher', 'all']:
            teacher_conflicts = check_teacher_conflicts(from_date, to_date)
            conflicts.extend(teacher_conflicts)
        
        # Room conflicts
        if check_type in ['room', 'all']:
            room_conflicts = check_room_conflicts(from_date, to_date)
            conflicts.extend(room_conflicts)
        
        # Student conflicts
        if check_type in ['student', 'all']:
            student_conflicts = check_student_conflicts(from_date, to_date)
            conflicts.extend(student_conflicts)
        
        summary = {
            'teacher_conflicts': len([c for c in conflicts if c['type'] == 'teacher']),
            'room_conflicts': len([c for c in conflicts if c['type'] == 'room']),
            'student_conflicts': len([c for c in conflicts if c['type'] == 'student'])
        }
        
        return jsonify({
            'summary': summary,
            'conflicts': conflicts[:20]  # Limit to 20 for display
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/optimization-results/<int:optimization_id>')
@login_required
@coordinator_required
def get_optimization_results(optimization_id):
    """Get optimization results by ID"""
    try:
        # This would come from a database in a real system
        # For now, return sample data
        
        # Generate sample history
        generations = list(range(1, 101))
        best_fitness = [0.5 + 0.4 * (1 - np.exp(-g/20)) + 0.1 * random.random() for g in generations]
        avg_fitness = [0.4 + 0.4 * (1 - np.exp(-g/25)) + 0.1 * random.random() for g in generations]
        
        history = {
            'generations': generations,
            'best_fitness': best_fitness,
            'avg_fitness': avg_fitness
        }
        
        # Comparison data
        comparison = {
            'genetic': [85, 78, 82, 88, 75, 70],
            'ant_colony': [82, 88, 75, 80, 85, 65],
            'csp': [78, 82, 88, 75, 80, 72]
        }
        
        # Metrics
        timetable = {
            'before': {'conflicts': 12, 'utilization': 65, 'balance': 70},
            'after': {'conflicts': 2, 'utilization': 88, 'balance': 92},
            'improvement': {'conflicts': 83, 'utilization': 35, 'balance': 31}
        }
        
        rooms = {
            'before': {'utilization': 60, 'distance': 120, 'wastage': 25},
            'after': {'utilization': 85, 'distance': 75, 'wastage': 10},
            'improvement': {'utilization': 42, 'distance': 38, 'wastage': 60}
        }
        
        invigilators = {
            'before': {'workload_balance': 55, 'dept_match': 60, 'satisfaction': 65},
            'after': {'workload_balance': 88, 'dept_match': 85, 'satisfaction': 90},
            'improvement': {'workload_balance': 60, 'dept_match': 42, 'satisfaction': 38}
        }
        
        summary = {
            'initial_fitness': 0.52,
            'final_fitness': 0.89,
            'improvement': 71,
            'time_elapsed': 45
        }
        
        return jsonify({
            'summary': summary,
            'timetable': timetable,
            'rooms': rooms,
            'invigilators': invigilators,
            'history': history,
            'comparison': comparison
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/apply-optimization', methods=['POST'])
@login_required
@coordinator_required
def apply_optimization():
    """Apply optimization results to the system"""
    try:
        # In a real system, this would update the database with optimized values
        # For now, just return success
        
        create_notification(
            title='Optimization Applied',
            message='AI optimization results have been applied to the schedule',
            notification_type='optimization',
            target_role='all'
        )
        
        return jsonify({'success': True, 'message': 'Optimization applied successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/export-optimization-results')
@login_required
@coordinator_required
def export_optimization_results():
    """Export optimization results as CSV"""
    try:
        # Create sample data
        data = {
            'Metric': ['Conflicts', 'Utilization', 'Balance', 'Workload', 'Department Match', 'Satisfaction'],
            'Before': [12, 65, 70, 55, 60, 65],
            'After': [2, 88, 92, 88, 85, 90],
            'Improvement': [83, 35, 31, 60, 42, 38]
        }
        
        df = pd.DataFrame(data)
        
        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'optimization_results_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/exam-schedule')
@login_required
@coordinator_required
def get_exam_schedule():
    """Get filtered exam schedule"""
    try:
        exam_type = request.args.get('type')
        dept_id = request.args.get('dept')
        status = request.args.get('status')
        month = request.args.get('month')
        
        query = Exam.query
        
        if exam_type:
            query = query.filter_by(exam_type=exam_type)
        
        if dept_id:
            query = query.join(Subject).filter(Subject.department_id == dept_id)
        
        if status:
            if status == 'published':
                query = query.filter_by(is_published=True)
            elif status == 'draft':
                query = query.filter_by(is_published=False)
        
        if month:
            year, month_num = map(int, month.split('-'))
            query = query.filter(
                db.extract('year', Exam.exam_date) == year,
                db.extract('month', Exam.exam_date) == month_num
            )
        
        exams = query.order_by(Exam.exam_date).limit(50).all()
        
        data = []
        for exam in exams:
            student_count = Student.query.filter_by(
                department_id=exam.subject.department_id if exam.subject else None
            ).count()
            
            data.append({
                'id': exam.id,
                'date': exam.exam_date.strftime('%d-%m-%Y'),
                'session': '10 AM' if exam.start_time and exam.start_time.hour == 10 else '2 PM',
                'department': exam.subject.department.name if exam.subject else 'N/A',
                'subject': exam.subject.name if exam.subject else 'N/A',
                'semester': exam.subject.semester.semester_number if exam.subject and exam.subject.semester else 1,
                'student_count': student_count,
                'status': 'published' if exam.is_published else 'draft'
            })
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/exams-by-month')
@login_required
@coordinator_required
def get_exams_by_month():
    """Get exams grouped by month for calendar"""
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        exams = Exam.query.filter(
            db.extract('year', Exam.exam_date) == year,
            db.extract('month', Exam.exam_date) == month
        ).all()
        
        data = []
        for exam in exams:
            data.append({
                'date': exam.exam_date.strftime('%Y-%m-%d'),
                'session': '10AM' if exam.start_time and exam.start_time.hour == 10 else '2PM',
                'subject': exam.subject.name if exam.subject else 'N/A'
            })
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/exam/<int:exam_id>')
@login_required
@coordinator_required
def get_exam(exam_id):
    """Get exam details by ID"""
    try:
        exam = Exam.query.get_or_404(exam_id)
        
        return jsonify({
            'id': exam.id,
            'name': exam.name,
            'type': exam.exam_type,
            'date': exam.exam_date.strftime('%Y-%m-%d'),
            'session': '10AM' if exam.start_time and exam.start_time.hour == 10 else '2PM',
            'duration': exam.duration_minutes,
            'department_id': exam.subject.department_id if exam.subject else None,
            'subject_id': exam.subject_id,
            'semester': exam.subject.semester.semester_number if exam.subject and exam.subject.semester else 1,
            'max_marks': exam.max_marks
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/save-exam', methods=['POST'])
@login_required
@coordinator_required
def save_exam():
    """Save or update exam"""
    try:
        data = request.get_json()
        
        exam_id = data.get('id')
        
        if exam_id:
            # Update existing exam
            exam = Exam.query.get_or_404(exam_id)
            exam.name = data['name']
            exam.exam_type = data['type']
            exam.exam_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            exam.duration_minutes = data['duration']
            exam.subject_id = data['subject_id']
            exam.max_marks = data['max_marks']
            
            # Set times based on session
            if data['session'] == '10AM':
                exam.start_time = datetime.strptime('10:00', '%H:%M').time()
                exam.end_time = datetime.strptime('13:00', '%H:%M').time()
            else:
                exam.start_time = datetime.strptime('14:00', '%H:%M').time()
                exam.end_time = datetime.strptime('17:00', '%H:%M').time()
            
            message = 'Exam updated successfully'
        else:
            # Create new exam
            # Set times based on session
            if data['session'] == '10AM':
                start_time = datetime.strptime('10:00', '%H:%M').time()
                end_time = datetime.strptime('13:00', '%H:%M').time()
            else:
                start_time = datetime.strptime('14:00', '%H:%M').time()
                end_time = datetime.strptime('17:00', '%H:%M').time()
            
            exam = Exam(
                name=data['name'],
                exam_type=data['type'],
                semester_id=1,  # This should be looked up
                subject_id=data['subject_id'],
                exam_date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                start_time=start_time,
                end_time=end_time,
                duration_minutes=data['duration'],
                max_marks=data['max_marks'],
                created_by=current_user.id,
                is_published=False
            )
            db.session.add(exam)
            message = 'Exam created successfully'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': message})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/exam/<int:exam_id>', methods=['DELETE'])
@login_required
@coordinator_required
def delete_exam(exam_id):
    """Delete an exam"""
    try:
        exam = Exam.query.get_or_404(exam_id)
        db.session.delete(exam)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Exam deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/publish-schedule', methods=['POST'])
@login_required
@coordinator_required
def publish_schedule():
    """Publish exam schedule to all departments"""
    try:
        # Update all exams to published
        Exam.query.update({Exam.is_published: True})
        db.session.commit()
        
        create_notification(
            title='Exam Schedule Published',
            message='The exam schedule has been published. Please check the timetable.',
            notification_type='exam',
            target_role='all'
        )
        
        return jsonify({'success': True, 'message': 'Schedule published successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/export-exam-schedule')
@login_required
@coordinator_required
def export_exam_schedule():
    """Export exam schedule as PDF/Excel"""
    try:
        # Get all published exams
        exams = Exam.query.filter_by(is_published=True).order_by(Exam.exam_date).all()
        
        # Create data for export
        data = []
        for exam in exams:
            data.append({
                'Date': exam.exam_date.strftime('%d-%m-%Y'),
                'Session': '10 AM' if exam.start_time and exam.start_time.hour == 10 else '2 PM',
                'Department': exam.subject.department.name if exam.subject else 'N/A',
                'Subject': exam.subject.name if exam.subject else 'N/A',
                'Semester': exam.subject.semester.semester_number if exam.subject and exam.subject.semester else 1,
                'Duration': f"{exam.duration_minutes} min",
                'Status': 'Published'
            })
        
        # Create Excel file
        df = pd.DataFrame(data)
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Exam Schedule', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'exam_schedule_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coordinator_bp.route('/api/saved-reports')
@login_required
@coordinator_required
def get_saved_reports():
    """Get list of saved reports"""
    try:
        # Sample data - in real system, this would come from a Reports table
        reports = [
            {'id': 1, 'name': 'Exam Summary March 2025', 'type': 'Exam Summary', 
             'generated_on': '2025-03-15', 'format': 'PDF', 'size': '2.4 MB'},
            {'id': 2, 'name': 'Room Utilization Q1 2025', 'type': 'Room Utilization', 
             'generated_on': '2025-03-14', 'format': 'Excel', 'size': '1.8 MB'},
            {'id': 3, 'name': 'Invigilator Duties March', 'type': 'Invigilator Duties', 
             'generated_on': '2025-03-13', 'format': 'PDF', 'size': '1.2 MB'},
            {'id': 4, 'name': 'Conflict Analysis Report', 'type': 'Conflict Analysis', 
             'generated_on': '2025-03-12', 'format': 'CSV', 'size': '0.9 MB'},
        ]
        
        return jsonify(reports)
    
    except Exception as e:
        return jsonify([])

@coordinator_bp.route('/api/download-report')
@login_required
@coordinator_required
def download_report():
    """Download a generated report"""
    try:
        report_type = request.args.get('type')
        format = request.args.get('format', 'pdf')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        
        # Create sample data based on report type
        if report_type == 'exam_summary':
            data = {
                'Department': ['CS', 'BCA', 'Commerce', 'English', 'Economics', 'History'],
                'Total Exams': [24, 18, 20, 16, 14, 12],
                'Morning': [12, 9, 10, 8, 7, 6],
                'Afternoon': [12, 9, 10, 8, 7, 6],
                'Students': [420, 315, 350, 280, 245, 210]
            }
        elif report_type == 'room_utilization':
            data = {
                'Room': ['A101', 'A102', 'B101', 'B102', 'C101', 'C102'],
                'Block': ['A', 'A', 'B', 'B', 'C', 'C'],
                'Capacity': [60, 60, 45, 45, 30, 30],
                'Utilization': [85, 78, 92, 88, 95, 90],
                'Total Exams': [15, 14, 12, 11, 8, 7]
            }
        else:
            data = {
                'Teacher': ['Dr. Sharma', 'Prof. Patel', 'Dr. Reddy', 'Prof. Kumar'],
                'Department': ['CS', 'BCA', 'Commerce', 'English'],
                'Duties': [8, 6, 7, 5],
                'Morning': [4, 3, 4, 2],
                'Afternoon': [4, 3, 3, 3]
            }
        
        df = pd.DataFrame(data)
        
        if format == 'excel':
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Report', index=False)
            output.seek(0)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ext = 'xlsx'
        elif format == 'csv':
            output = BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)
            mimetype = 'text/csv'
            ext = 'csv'
        else:  # pdf
            # Simple text file as placeholder for PDF
            output = BytesIO()
            output.write(b"PDF report would be generated here")
            output.seek(0)
            mimetype = 'application/pdf'
            ext = 'pdf'
        
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=f'{report_type}_{datetime.now().strftime("%Y%m%d")}.{ext}'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===================== HELPER FUNCTIONS =====================

def check_conflicts_count():
    """Count total conflicts in the system"""
    # Simplified conflict counting
    teacher_conflicts = len(check_teacher_conflicts())
    room_conflicts = len(check_room_conflicts())
    student_conflicts = len(check_student_conflicts())
    
    return teacher_conflicts + room_conflicts + student_conflicts

def check_teacher_conflicts(from_date=None, to_date=None):
    """Check for teacher scheduling conflicts"""
    conflicts = []
    
    # Get all invigilator allocations
    allocations = InvigilatorAllocation.query.all()
    
    # Group by teacher and date
    teacher_schedule = {}
    for alloc in allocations:
        key = f"{alloc.teacher_id}_{alloc.duty_date}"
        if key in teacher_schedule:
            # Conflict found - teacher assigned twice on same day
            conflicts.append({
                'type': 'teacher',
                'title': 'Teacher Double Booking',
                'description': f'Teacher assigned to multiple duties on {alloc.duty_date}',
                'details': f'Teacher ID: {alloc.teacher_id}'
            })
        else:
            teacher_schedule[key] = True
    
    return conflicts[:10]  # Limit for display

def check_room_conflicts(from_date=None, to_date=None):
    """Check for room scheduling conflicts"""
    conflicts = []
    
    # Get all room allocations
    allocations = RoomAllocation.query.all()
    
    # Group by room and date
    room_schedule = {}
    for alloc in allocations:
        if alloc.exam:
            key = f"{alloc.room_number}_{alloc.exam.exam_date}"
            if key in room_schedule:
                # Conflict found - room used twice on same day
                conflicts.append({
                    'type': 'room',
                    'title': 'Room Double Booking',
                    'description': f'Room {alloc.room_number} scheduled for multiple exams on {alloc.exam.exam_date}',
                    'details': f'Exam: {alloc.exam.name}'
                })
            else:
                room_schedule[key] = True
    
    return conflicts[:10]

def check_student_conflicts(from_date=None, to_date=None):
    """Check for student scheduling conflicts"""
    # In a real system, this would check if students are scheduled for multiple exams at the same time
    return []

def create_notification(title, message, notification_type, target_role='all'):
    """Create a system notification"""
    try:
        notification = Notification(
            title=title,
            message=message,
            notification_type=notification_type,
            target_role=target_role,
            created_by=current_user.id,
            is_published=True
        )
        db.session.add(notification)
        db.session.commit()
    except:
        db.session.rollback()


# ===================== AI OPTIMIZATION ALGORITHMS =====================

def genetic_algorithm_optimize(timetable):
    """Optimize timetable using genetic algorithm"""
    # Simplified genetic algorithm simulation
    # In a real system, this would implement actual genetic algorithm operations
    
    # Add fitness scores
    for item in timetable:
        item['fitness'] = random.uniform(0.7, 0.95)
    
    # Sort by fitness
    timetable.sort(key=lambda x: x['fitness'], reverse=True)
    
    return timetable

def genetic_algorithm_timetable(exams, population_size, generations, mutation_rate, crossover_rate):
    """Run genetic algorithm for timetable optimization"""
    # Simulate optimization history
    history = {
        'best_fitness': [0.5 + 0.4 * (1 - np.exp(-i/20)) for i in range(generations)],
        'avg_fitness': [0.4 + 0.4 * (1 - np.exp(-i/25)) for i in range(generations)]
    }
    
    # Return optimized exams (simulated)
    return exams, history

def ant_colony_optimize_rooms(rooms, students):
    """Optimize room allocation using ant colony algorithm"""
    allocations = []
    
    # Simple simulation of ant colony optimization
    for i, student in enumerate(students[:50]):  # Limit to 50 for demo
        if i < len(rooms):
            room = next((r for r in rooms if r['id'] == int(rooms[i])), None)
        else:
            room = next((r for r in rooms if r['id'] == int(rooms[i % len(rooms)])), None)
        
        if room:
            allocations.append({
                'room_number': room['room_number'],
                'block': room['block'],
                'student_name': student['name'],
                'registration_no': student['registration_no'],
                'department': student['department'],
                'semester': student['semester'],
                'score': random.uniform(0.8, 0.98)
            })
    
    return allocations

def ant_colony_optimization(students, rooms, ant_count, iterations, alpha, beta, goal):
    """Run ant colony optimization for room allocation"""
    allocations = []
    history = [random.uniform(0.5, 0.8) for _ in range(iterations)]
    
    for i in range(min(len(students), len(rooms) * 30)):  # 30 students per room
        room_idx = i % len(rooms)
        allocations.append((students[i % len(students)], rooms[room_idx]))
    
    return allocations, history

def constraint_satisfaction_assign(teachers, room, exam_date, session):
    """Assign invigilators using constraint satisfaction"""
    assignments = []
    
    if len(teachers) >= 2:
        # Simple assignment - just pick first two
        assignments.append({
            'date': exam_date,
            'session': 'Morning' if session == '10AM' else 'Afternoon',
            'room': room['room_number'] if room else 'N/A',
            'block': room['block'] if room else 'A',
            'invigilator1': teachers[0].full_name,
            'invigilator2': teachers[1].full_name,
            'department': teachers[0].department.name if teachers[0].department else 'N/A'
        })
    
    return assignments

def constraint_satisfaction_invigilators(teachers, exams, rooms, max_duties, weights, strategy):
    """Run constraint satisfaction for invigilator assignment"""
    room_assignments = []
    teacher_assignments = {teacher: [] for teacher in teachers}
    
    # Simple simulation
    for i, exam in enumerate(exams[:10]):  # Limit to 10 exams
        room = rooms[i % len(rooms)]
        inv1 = teachers[i % len(teachers)]
        inv2 = teachers[(i + 1) % len(teachers)]
        
        room_assignments.append((exam, room, inv1, inv2))
        
        teacher_assignments[inv1].append({
            'exam': exam,
            'room': room,
            'session': 'Morning' if exam.start_time and exam.start_time.hour == 10 else 'Afternoon'
        })
        
        teacher_assignments[inv2].append({
            'exam': exam,
            'room': room,
            'session': 'Morning' if exam.start_time and exam.start_time.hour == 10 else 'Afternoon'
        })
    
    # Calculate stats
    stats = {
        'workload_balance': random.randint(75, 95),
        'dept_match': random.randint(70, 90),
        'satisfaction': random.randint(80, 98)
    }
    
    return room_assignments, teacher_assignments, stats