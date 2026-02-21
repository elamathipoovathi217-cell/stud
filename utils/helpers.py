import random
import string
from datetime import datetime

# Department -> semester -> subjects
DEPARTMENTS = {
    'CSE': {
        '1': ['Mathematics I', 'Programming in C', 'Digital Logic'],
        '2': ['Data Structures', 'Computer Organization', 'Discrete Mathematics'],
        '3': ['DBMS', 'Operating Systems', 'Computer Networks'],
        '4': ['Software Engineering', 'Web Technology', 'Theory of Computation'],
    },
    'ECE': {
        '1': ['Engineering Physics', 'Basic Electronics', 'Mathematics I'],
        '2': ['Signals and Systems', 'Network Theory', 'Electronic Devices'],
    },
    'EEE': {
        '1': ['Basic Electrical Engineering', 'Engineering Mechanics', 'Mathematics I'],
        '2': ['Electrical Machines I', 'Power Systems I', 'Control Systems'],
    },
    'MECH': {
        '1': ['Engineering Graphics', 'Thermodynamics', 'Mathematics I'],
        '2': ['Fluid Mechanics', 'Manufacturing Process', 'Strength of Materials'],
    },
    'CIVIL': {
        '1': ['Engineering Geology', 'Surveying', 'Mathematics I'],
        '2': ['Structural Analysis', 'Concrete Technology', 'Fluid Mechanics'],
    },
    'IT': {
        '1': ['Mathematics I', 'Problem Solving', 'Digital Fundamentals'],
        '2': ['Python Programming', 'Data Structures', 'Database Fundamentals'],
    },
}


def _rand(n=4):
    return ''.join(random.choices(string.digits, k=n))


def generate_registration_number(department_code='GEN'):
    year = datetime.now().year
    return f"{department_code}{year}{_rand(4)}"


def generate_student_id(prefix='STU'):
    return f"{prefix}-{_rand(6)}"
