from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, mail
from models import User, Student, Department, Course, Subject, Semester, AcademicYear, TeacherSubject
from utils.validators import validate_email, validate_phone, validate_password
from utils.helpers import generate_registration_number, generate_student_id, DEPARTMENTS
from flask_mail import Message
from datetime import datetime, date
import secrets
import os
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        department_name = request.form.get('department', '').strip()
        remember = True if request.form.get('remember') else False

        # Find user by username/email, or by student registration number + department
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        if not user:
            student_query = Student.query.filter_by(registration_number=username)
            if department_name:
                student_query = student_query.join(Department).filter(Department.name == department_name)
            student = student_query.first()
            user = student.user_account if student else None
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account is deactivated. Contact administrator.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect based on role
            return redirect(url_for('auth.dashboard_redirect'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))
    
    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.form.get('full_name', '').strip()
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            phone = request.form.get('phone', '').strip()
            role = request.form.get('role', '')
            department_id = request.form.get('department_id')
            
            # Validation
            if not all([full_name, username, email, password, role]):
                flash('All fields are required', 'danger')
                return redirect(url_for('auth.register'))
            
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('auth.register'))
            
            is_valid, msg = validate_password(password)
            if not is_valid:
                flash(msg, 'danger')
                return redirect(url_for('auth.register'))
            
            if not validate_email(email):
                flash('Invalid email format', 'danger')
                return redirect(url_for('auth.register'))
            
            if phone and not validate_phone(phone):
                flash('Invalid phone number (10 digits required)', 'danger')
                return redirect(url_for('auth.register'))
            
            # Check if user exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'danger')
                return redirect(url_for('auth.register'))
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('auth.register'))
            
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                full_name=full_name,
                phone=phone,
                role=role,
                department_id=department_id if department_id else None,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # If student, create student record
            if role == 'student':
                registration_number = request.form.get('registration_number')
                student_id = request.form.get('student_id')
                course_id = request.form.get('course_id')
                batch_year = request.form.get('batch_year')
                
                if not all([registration_number, student_id, course_id, batch_year]):
                    flash('Student details are required', 'danger')
                    db.session.rollback()
                    return redirect(url_for('auth.register'))
                
                student = Student(
                    registration_number=registration_number,
                    student_id=student_id,
                    name=full_name,
                    email=email,
                    phone=phone,
                    user_id=user.id,
                    course_id=course_id,
                    department_id=department_id,
                    current_semester=1,
                    batch_year=int(batch_year),
                    admission_date=date.today(),
                    is_active=True
                )
                db.session.add(student)
            
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except IntegrityError:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    # Get departments for dropdown
    departments = Department.query.all()
    courses = Course.query.all()
    
    return render_template('register.html', departments=departments, courses=courses)

@auth_bp.route('/dashboard-redirect')
@login_required
def dashboard_redirect():
    """Redirect user to appropriate dashboard based on role"""
    if current_user.role == 'principal':
        return redirect(url_for('principal.dashboard'))
    elif current_user.role == 'hod':
        return redirect(url_for('hod.dashboard'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher.dashboard'))
    elif current_user.role == 'student':
        return redirect(url_for('student.dashboard'))
    elif current_user.role == 'coordinator':
        return redirect(url_for('coordinator.dashboard'))
    else:
        flash('Invalid user role', 'danger')
        return redirect(url_for('auth.logout'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """View user profile"""
    department_stats = {}
    if current_user.role == 'hod' and current_user.department:
        # Get department statistics
        department_stats['teachers'] = User.query.filter_by(
            department_id=current_user.department_id, 
            role='teacher'
        ).count()
        department_stats['students'] = Student.query.filter_by(
            department_id=current_user.department_id
        ).count()
        department_stats['subjects'] = Subject.query.filter_by(
            department_id=current_user.department_id
        ).count()
    
    return render_template('profile.html', department_stats=department_stats)

@auth_bp.route('/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    try:
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        
        if not full_name or not email:
            flash('Name and email are required', 'danger')
            return redirect(url_for('auth.profile'))
        
        if not validate_email(email):
            flash('Invalid email format', 'danger')
            return redirect(url_for('auth.profile'))
        
        if phone and not validate_phone(phone):
            flash('Invalid phone number', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Check if email already taken by another user
        existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_user:
            flash('Email already in use by another account', 'danger')
            return redirect(url_for('auth.profile'))
        
        current_user.full_name = full_name
        current_user.email = email
        current_user.phone = phone
        
        # Update student record if exists
        if current_user.role == 'student' and current_user.student_record:
            current_user.student_record.name = full_name
            current_user.student_record.email = email
            current_user.student_record.phone = phone
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'danger')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/change-photo', methods=['POST'])
@login_required
def change_photo():
    """Change profile photo"""
    if 'profile_photo' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('auth.profile'))
    
    file = request.files['profile_photo']
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('auth.profile'))
    
    if file and allowed_file(file.filename):
        # Delete old photo if exists
        if current_user.profile_pic:
            old_photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                         'profile_pics', current_user.profile_pic)
            if os.path.exists(old_photo_path):
                os.remove(old_photo_path)
        
        # Save new photo
        filename = secure_filename(f"user_{current_user.id}_{file.filename}")
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_pics', filename)
        file.save(file_path)
        
        current_user.profile_pic = filename
        db.session.commit()
        
        flash('Profile photo updated successfully', 'success')
    else:
        flash('Invalid file type. Allowed: png, jpg, jpeg, gif', 'danger')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('auth.change_password'))
        
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            flash(msg, 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Password changed successfully. Please login again.', 'success')
        logout_user()
        return redirect(url_for('auth.login'))
    
    return render_template('change_password.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            # Store token in database with expiry (you'll need to add these fields)
            # user.reset_token = token
            # user.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            
            # Send email
            try:
                msg = Message('Password Reset Request',
                            sender='noreply@spas.edu',
                            recipients=[email])
                msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_password', token=token, _external=True)}

If you did not make this request, please ignore this email.
'''
                mail.send(msg)
                flash('Password reset link has been sent to your email', 'info')
            except:
                flash('Error sending email. Please try again later.', 'danger')
        else:
            # Don't reveal if email exists or not
            flash('If your email is registered, you will receive a reset link', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    # Find user with valid token
    # user = User.query.filter_by(reset_token=token).first()
    # if not user or user.reset_token_expiry < datetime.utcnow():
    #     flash('Invalid or expired reset link', 'danger')
    #     return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        is_valid, msg = validate_password(password)
        if not is_valid:
            flash(msg, 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        # user.password_hash = generate_password_hash(password)
        # user.reset_token = None
        # user.reset_token_expiry = None
        # db.session.commit()
        
        flash('Password reset successful. Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', token=token)

@auth_bp.route('/notifications')
@login_required
def notifications():
    """View user notifications"""
    return render_template('notifications.html')
@auth_bp.before_app_request
def setup_database():
    """Setup database on first request"""
    from flask import current_app
    with current_app.app_context():
        # Only run if tables are empty AND no users exist
        if Department.query.count() == 0 and User.query.count() == 0:
            init_database()
        else:
            print("Database already has data. Skipping automatic seeding.")
            
@auth_bp.route('/activity-log')
@login_required
def activity_log():
    """View user activity log"""
    return render_template('activity_log.html')

# Initialize database with departments, courses, subjects, and users
def init_database():
    """Initialize database with default data"""
    # Create academic years
    academic_years = [
        AcademicYear(year='2022-2023', start_date=date(2022, 6, 1), end_date=date(2023, 4, 30), is_current=False),
        AcademicYear(year='2023-2024', start_date=date(2023, 6, 1), end_date=date(2024, 4, 30), is_current=False),
        AcademicYear(year='2024-2025', start_date=date(2024, 6, 1), end_date=date(2025, 4, 30), is_current=True),
    ]
    
    for year in academic_years:
        if not AcademicYear.query.filter_by(year=year.year).first():
            db.session.add(year)
    db.session.commit()

    # Create departments
    departments_data = {
        'BSC_CS': 'Computer Science',
        'BCA': 'Computer Applications',
        'BCOM_FIN': 'Commerce (Finance)',
        'BCOM_COOP': 'Commerce (Co-operation)',
        'BA_ENGLISH': 'English',
        'BA_ECONOMICS': 'Economics',
        'BA_HISTORY': 'History'
    }
    
    departments = {}
    for code, name in departments_data.items():
        dept = Department.query.filter_by(code=code).first()
        if not dept:
            dept = Department(code=code, name=name)
            db.session.add(dept)
            db.session.flush()
        departments[code] = dept
    
    db.session.commit()

    # Create courses for each department
    courses = {}
    for dept_code, dept in departments.items():
        course_name = departments_data[dept_code]
        course = Course.query.filter_by(code=dept_code, department_id=dept.id).first()
        if not course:
            course = Course(
                name=course_name,
                code=dept_code,
                duration_years=3 if dept_code in ['BCA', 'BCOM_FIN', 'BCOM_COOP'] else 4,
                department_id=dept.id
            )
            db.session.add(course)
            db.session.flush()
        courses[dept_code] = course
    
    db.session.commit()

    # Create semesters for each course
    current_year = AcademicYear.query.filter_by(is_current=True).first()
    
    for dept_code, course in courses.items():
        duration = course.duration_years
        for sem_num in range(1, duration * 2 + 1):
            semester = Semester.query.filter_by(
                course_id=course.id,
                semester_number=sem_num
            ).first()
            
            if not semester:
                # Calculate semester dates
                if sem_num % 2 == 1:  # Odd semesters (Jun-Dec)
                    start_date = date(2024, 6, 1)
                    end_date = date(2024, 12, 31)
                else:  # Even semesters (Jan-Apr)
                    start_date = date(2025, 1, 1)
                    end_date = date(2025, 4, 30)
                
                semester = Semester(
                    semester_number=sem_num,
                    course_id=course.id,
                    academic_year_id=current_year.id,
                    start_date=start_date,
                    end_date=end_date
                )
                db.session.add(semester)
        db.session.commit()

    # Create subjects for each department and semester
    subject_map = {}
    for dept_code, subjects_dict in DEPARTMENTS.items():
        dept = departments.get(dept_code)
        if not dept:
            continue
            
        course = courses.get(dept_code)
        if not course:
            continue
            
        for sem_num_str, subjects in subjects_dict.items():
            sem_num = int(sem_num_str)
            
            # Find semester
            semester = Semester.query.filter_by(
                course_id=course.id,
                semester_number=sem_num
            ).first()
            
            if not semester:
                continue
                
            for subject_name in subjects:
                subject_code = f"{dept_code}{sem_num:02d}{subjects.index(subject_name)+1:02d}"
                
                subject = Subject.query.filter_by(
                    code=subject_code,
                    department_id=dept.id
                ).first()
                
                if not subject:
                    subject = Subject(
                        name=subject_name,
                        code=subject_code,
                        credits=3,
                        semester_id=semester.id,
                        department_id=dept.id
                    )
                    db.session.add(subject)
                    db.session.flush()
                
                if dept_code not in subject_map:
                    subject_map[dept_code] = {}
                if sem_num not in subject_map[dept_code]:
                    subject_map[dept_code][sem_num] = []
                subject_map[dept_code][sem_num].append(subject)
    
    db.session.commit()

    # Create HODs for each department
    hods = {}
    for dept_code, dept in departments.items():
        hod_username = f"hod_{dept_code.lower()}"
        hod = User.query.filter_by(username=hod_username).first()
        
        if not hod:
            hod = User(
                username=hod_username,
                email=f"hod.{dept_code.lower()}@spas.edu",
                password_hash=generate_password_hash('hod123'),
                full_name=f"HOD of {dept.name}",
                role='hod',
                department_id=dept.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(hod)
            db.session.flush()
        
        dept.hod_id = hod.id
        hods[dept_code] = hod
    
    db.session.commit()

    # Create teachers for each department (5-6 per department)
    teacher_names = [
        ('Dr. A. Sharma', 'asharma'), ('Prof. B. Patel', 'bpatel'), ('Dr. C. Reddy', 'credddy'),
        ('Prof. D. Kumar', 'dkumar'), ('Dr. E. Singh', 'esingh'), ('Prof. F. Nair', 'fnair'),
        ('Dr. G. Menon', 'gmenon'), ('Prof. H. Desai', 'hdesai'), ('Dr. I. Joseph', 'ijoseph'),
        ('Prof. J. Thomas', 'jthomas'), ('Dr. K. George', 'kgeorge'), ('Prof. L. Mathew', 'lmathew')
    ]
    
    teachers = {}
    for dept_code, dept in departments.items():
        dept_teachers = []
        num_teachers = 5 if dept_code in ['BCOM_COOP', 'BA_HISTORY'] else 6
        
        for i in range(num_teachers):
            name, base_username = teacher_names[i % len(teacher_names)]
            username = f"{base_username}_{dept_code.lower()}"
            
            teacher = User.query.filter_by(username=username).first()
            if not teacher:
                teacher = User(
                    username=username,
                    email=f"{base_username}.{dept_code.lower()}@spas.edu",
                    password_hash=generate_password_hash('teacher123'),
                    full_name=f"{name} - {dept.name}",
                    role='teacher',
                    department_id=dept.id,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(teacher)
                db.session.flush()
            
            dept_teachers.append(teacher)
        
        teachers[dept_code] = dept_teachers
    
    db.session.commit()

    # Assign teachers to subjects
    current_year = AcademicYear.query.filter_by(is_current=True).first()
    
    for dept_code, dept in departments.items():
        dept_teachers = teachers.get(dept_code, [])
        if not dept_teachers:
            continue
            
        for sem_num in range(1, 5):  # Current active semesters
            subjects = subject_map.get(dept_code, {}).get(sem_num, [])
            
            for i, subject in enumerate(subjects):
                teacher = dept_teachers[i % len(dept_teachers)]
                
                # Find semester
                semester = Semester.query.filter_by(
                    course_id=courses[dept_code].id,
                    semester_number=sem_num
                ).first()
                
                if not semester:
                    continue
                
                # Check if assignment exists
                assignment = TeacherSubject.query.filter_by(
                    teacher_id=teacher.id,
                    subject_id=subject.id,
                    academic_year_id=current_year.id
                ).first()
                
                if not assignment:
                    assignment = TeacherSubject(
                        teacher_id=teacher.id,
                        subject_id=subject.id,
                        academic_year_id=current_year.id,
                        semester_id=semester.id,
                        is_active=True
                    )
                    db.session.add(assignment)
    
    db.session.commit()

    # Create students (30-40 per class)
    batches = [2022, 2023, 2024, 2025]
    
    for dept_code, dept in departments.items():
        course = courses.get(dept_code)
        if not course:
            continue
        
        for batch in batches:
            # Determine current semester based on batch
            if batch == 2022:
                semesters = [7, 8]  # Final year
            elif batch == 2023:
                semesters = [5, 6]  # Third year
            elif batch == 2024:
                semesters = [3, 4]  # Second year
            else:  # 2025
                semesters = [1, 2]  # First year
            
            for sem_num in semesters:
                # Create 30-40 students per semester
                num_students = 35  # Average
                
                for i in range(1, num_students + 1):
                    reg_number = generate_registration_number(dept_code, batch, i)
                    student_id = generate_student_id(dept_code, i)
                    
                    student = Student.query.filter_by(registration_number=reg_number).first()
                    if not student:
                        # Create user account for student
                        username = f"student_{dept_code.lower()}_{batch}_{i}"
                        email = f"{username}@spas.edu"
                        
                        user = User.query.filter_by(username=username).first()
                        if not user:
                            user = User(
                                username=username,
                                email=email,
                                password_hash=generate_password_hash('student123'),
                                full_name=f"Student {i} - {dept.name}",
                                role='student',
                                department_id=dept.id,
                                is_active=True,
                                created_at=datetime.utcnow()
                            )
                            db.session.add(user)
                            db.session.flush()
                        
                        student = Student(
                            registration_number=reg_number,
                            student_id=student_id,
                            name=f"Student {i} - {dept.name}",
                            email=email,
                            user_id=user.id,
                            course_id=course.id,
                            department_id=dept.id,
                            current_semester=sem_num,
                            batch_year=batch,
                            admission_date=date(batch, 6, 1),
                            is_active=True
                        )
                        db.session.add(student)
    
    db.session.commit()

    # Create coordinator
    coordinator = User.query.filter_by(username='coordinator').first()
    if not coordinator:
        coordinator = User(
            username='coordinator',
            email='coordinator@spas.edu',
            password_hash=generate_password_hash('coord123'),
            full_name='Exam Coordinator',
            role='coordinator',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(coordinator)
    
    # Create principal
    principal = User.query.filter_by(username='principal').first()
    if not principal:
        principal = User(
            username='principal',
            email='principal@spas.edu',
            password_hash=generate_password_hash('admin123'),
            full_name='Dr. Principal Kumar',
            role='principal',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(principal)
    
    db.session.commit()

    print("Database initialized successfully with:")
    print(f"- {Department.query.count()} departments")
    print(f"- {Course.query.count()} courses")
    print(f"- {Semester.query.count()} semesters")
    print(f"- {Subject.query.count()} subjects")
    print(f"- {User.query.filter_by(role='hod').count()} HODs")
    print(f"- {User.query.filter_by(role='teacher').count()} teachers")
    print(f"- {User.query.filter_by(role='student').count()} students")
    print(f"- {Student.query.count()} student records")
    print(f"- {TeacherSubject.query.count()} teacher-subject assignments")

# Call this when app starts
@auth_bp.before_app_request
def setup_database():
    """Setup database on first request"""
    from flask import current_app
    with current_app.app_context():
        # Only run if tables are empty
        if Department.query.count() == 0:
            init_database()