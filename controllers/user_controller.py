from werkzeug.security import generate_password_hash, check_password_hash
from recipe_platform.models.database import User


def register_user(db_session, email, password, role):
    """לוגיקה לרישום משתמש חדש עם הצפנת סיסמה"""
    # בדיקה אם המשתמש כבר קיים
    existing_user = db_session.query(User).filter_by(email=email).first()
    if existing_user:
        return False, "המייל כבר קיים במערכת"

    # יצירת המשתמש החדש (הצפנת הסיסמה  )
    hashed_pw = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed_pw, role=role)

    # במידה והוא נרשם כ-Reader, הוא מאושר אוטומטית (כי הוא לא מעלה כלום)
    if role == 'Reader':
        new_user.is_approved_uploader = True

    new_user.save(db_session)
    return True, "ההרשמה בוצעה בהצלחה"


def login_user(db_session, email, password):
    """אימות פרטי התחברות"""
    # זו שאילתה בשיטת ORM שמחפשת בטבלת המשתמשים את השורה שבה המייל מתאים למה שהוקלד.
    user = db_session.query(User).filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    return None


def get_pending_users(db_session):
    """שליפת כל המשתמשים שממתינים לאישור מנהל """
    return db_session.query(User).filter_by(role='Uploader', is_approved_uploader=False).all()