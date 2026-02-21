import re


def validate_email(email):
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email or ''))


def validate_phone(phone):
    return bool(re.match(r'^\d{10}$', (phone or '').strip()))


def validate_password(password):
    password = password or ''
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long.'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must include at least one uppercase letter.'
    if not re.search(r'[a-z]', password):
        return False, 'Password must include at least one lowercase letter.'
    if not re.search(r'\d', password):
        return False, 'Password must include at least one number.'
    return True, 'Valid password.'
