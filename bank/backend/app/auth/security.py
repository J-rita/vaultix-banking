from flask_bcrypt import Bcrypt

# Initialize Bcrypt - we'll link it to the app in main.py
bcrypt = Bcrypt()

def get_password_hash(password):
    """
    Generates a secure bcrypt hash for the given password.
    """
    # decode('utf-8') to return a string for database storage
    return bcrypt.generate_password_hash(password).decode('utf-8')

def verify_password(password, hashed_password):
    """
    Verifies a password against a stored bcrypt hash.
    """
    return bcrypt.check_password_hash(hashed_password, password)

# Note: JWT creation and verification are now handled directly 
# by flask-jwt-extended in the route files.
