import os
import sys

from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
from sqlalchemy import or_, func

# ייבוא
try:
    from models.database import Base, User, Recipe, IngredientEntry
    from controllers.recipe_controller import process_recipe_images, search_algorithm
    from controllers.user_controller import register_user, login_user, get_pending_users
except ImportError as e:
    print(f"Import Error: {e}")



#  טעינת משתני סביבה מהקובץ .env (כמו SECRET_KEY)
load_dotenv()

#  הגדרת אפליקציית Flask
app = Flask(__name__)

#  הגדרת תיקיית העלאת תמונות
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#  הגדרות קונפיגורציה
# המפתח הסודי משמש לאבטחת המידע שעובר בין השרת לדפדפן
app.config['SECRET_KEY'] = 'dev_secret_key'


#  חיבור למסד הנתונים :
#  הגדרת נתיב הבסיס (איפה ש-app.py נמצא)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'recipe_platform.db')
engine = create_engine(f'sqlite:///{db_path}')


# יצירת מחלקה לניהול סשנים (תקשורת) מול ה-DB
Session = sessionmaker(bind=engine)

def init_db():
    """יוצרת את הטבלאות ב-DB לפי המודלים המוגדרים ב-models"""
    Base.metadata.create_all(engine)
    print(f"✅ Database connected at: {db_path}")

# יצירת הטבלאות
# עי הרצת האתחול בתוך ה-Context של פלאסק
with app.app_context():
   init_db()

#הרצנו פעם אחת כדי ליצור מנהל
# with app.app_context():
#     init_db()
#     # קוד זמני ליצירת מנהל
#     db_session = Session()
#     admin = db_session.query(User).filter_by(email="admin@gmail.com").first()
#     if not admin:
#         from werkzeug.security import generate_password_hash
#         new_admin = User(
#             email="admin@gmail.com",
#             password_hash=generate_password_hash("123456"),
#             role="Admin",
#             is_approved_uploader=True
#         )
#         db_session.add(new_admin)
#         db_session.commit()
#     db_session.close()

# ------------------------------------
# נתיבים (Routes)
# ------------------------------------

@app.route('/')
def home():
    """מציג את דף הבית עם רשימת כל המתכונים"""
    # פתיחת סשן (חיבור זמני) למסד הנתונים
    db_session = Session()
    # שליפת כל האובייקטים מסוג Recipe (מתכון)
    recipes = db_session.query(Recipe).all()
    db_session.close()
    return render_template('index.html', recipes=recipes)

# methods=['GET', 'POST']: דף ההרשמה עובד בשני מצבים.
# GET
# הוא המצב שבו המשתמש רק "מבקש" לראות את הדף.
# POST
# הוא המצב שבו המשתמש "שולח" את הנתונים שלו לשרת

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db_session = Session()
        # שליחת הנתונים ל-user_controller לביצוע הרישום
        success, message = register_user(
            db_session,
            request.form.get('email'),
            request.form.get('password'),
            request.form.get('role')
        )
        db_session.close()
        if success:
            return redirect(url_for('login'))
        return message
    # אם זה GET (כלומר המשתמש רק נכנס לדף) - נציג לו את הקובץ
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db_session = Session()
        # אימות משתמש דרך ה-Controller
        user = login_user(db_session, request.form.get('email'), request.form.get('password'))
        db_session.close()

        if user:
            # יצירת "סשן" - השרת זוכר את המשתמש לפי ה-ID שלו
            # בעצם אנחנו בעצם אומרים לשרת: "שים למשתמש הזה צמיד (סשן) ותכתוב עליו את מספר ה-ID שלו".
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['is_approved_uploader'] = user.is_approved_uploader
            return redirect(url_for('home'))
        return "אימייל או סיסמה שגויים"
    return render_template('login.html')


@app.route('/logout')
def logout():
    """התנתקות מהמערכת"""
    session.clear()
    return redirect(url_for('home'))


@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    db_session = Session()
    try:
        # טעינה של המתכון עם הרכיבים
        recipe = db_session.query(Recipe).options(joinedload(Recipe.ingredients)).filter_by(id=recipe_id).first()

        if not recipe:
            db_session.close()
            return "המתכון לא נמצא", 404

        #  שימוש בפונקציה הנכונה שקיימת במודל
        variations = recipe.get_variation_paths()
        return render_template('view_recipe.html', recipe=recipe, variations=variations)

    finally:
        # הסשן ייסגר רק אחרי שהדף נוצר (או אם הייתה שגיאה)
        db_session.close()




@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    # 1. בדיקה האם המשתמש בכלל מחובר (בדיקה ראשונית מהסשן)
    if 'user_id' not in session:
        return redirect(url_for('login'))


    # 2. בדיקה מול מסד הנתונים - האם המשתמש באמת מאושר?
    if session.get('user_role') =='Reader':
        return "גישה נדחתה",403
    print(f"💢💢{session.get('is_approved_uploader')}")
    if session.get('is_approved_uploader') != True:
        return "גישה נדחתה, החשבון שלך ממתין לאישור מנהל. לא ניתן להעלות מתכונים עדיין.", 403


    if request.method == 'POST':
        db_session = Session()
        img_file = request.files.get('image')
        orig_path, var_paths = process_recipe_images(img_file, app.config['UPLOAD_FOLDER'])

        new_recipe = Recipe(
            title=request.form.get('title'),
            instructions=request.form.get('instructions'),
            recipe_type=request.form.get('recipe_type'),
            image_path=orig_path,
            user_id=session['user_id']
        )
        new_recipe.set_variation_paths(var_paths)

        ing_text = request.form.get('ingredients_list', '')
        for line in ing_text.strip().split('\n'):
            parts = line.split(',')
            if len(parts) == 3:
                ing = IngredientEntry(
                    amount=float(parts[0].strip()),
                    unit=parts[1].strip(),
                    product=parts[2].strip(),
                    recipe=new_recipe
                )
                db_session.add(ing)

        new_recipe.save(db_session)
        db_session.close()
        return redirect(url_for('home'))
    return render_template('add_recipe.html')




@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []  # נתחיל עם רשימה ריקה
    searched_for = ""
    # user_ingredients_str, all_recipes
    if request.method == 'POST':
        # 1. שליפת הקלט לפי השם שמופיע ב-HTML (user_ingredients)
        ingredients_input = request.form.get('user_ingredients', '').strip()
        searched_for = ingredients_input
        print(f"💥{ingredients_input}")
        # שליפת כל המתכונים
        db_session = Session()
        recipes = db_session.query(Recipe).all()
        print(f"💦💦💦{recipes}")
        results=search_algorithm(ingredients_input,recipes)

    print(f"💨💨{results}")
    # 4. שליחת המשתנה בשם 'results' כדי שיתאים ל- {% for item in results %} ב-HTML
    return render_template('search.html', results=results, searched_for=searched_for)
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('user_role') != 'Admin':
        return "גישה נדחתה: דף זה מיועד למנהלים בלבד", 403

    db_session = Session()
    # שליפת משתמשים הממתינים לאישור
    pending = get_pending_users(db_session)

    # מוסיפים joinedload כדי לטעון את פרטי המעלה מראש
    all_recipes = db_session.query(Recipe).options(joinedload(Recipe.uploader)).all()

    db_session.close()
    return render_template('admin_dashboard.html', users=pending, all_recipes=all_recipes)

@app.route('/admin/approve/<int:user_id>')
def approve_user(user_id):
    if session.get('user_role') != 'Admin':
        return "גישה נדחתה", 403

    db_session = Session()
    # חיפוש המשתמש לפי ה-ID שקיבלנו מהכפתור
    user = db_session.query(User).filter_by(id=user_id).first()

    if user:
        print(f"💜💜{user.is_approved_uploader}")

        user.is_approved_uploader = True  # הפיכתו למאושר
        db_session.commit()
        print(f"💜💜{user.is_approved_uploader}")

    db_session.close()
    # חזרה אוטומטית לדף הניהול כדי לראות שהמשתמש נעלם מרשימת הממתינים
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_recipe/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    if session.get('user_role') != 'Admin':
        return "Unauthorized", 403
    db_session = Session()
    try:
        recipe = db_session.query(Recipe).get(recipe_id)
        if recipe:
            db_session.delete(recipe)
            db_session.commit()
        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        db_session.rollback()
        return f"שגיאה במחיקת המתכון: {e}"

    finally:
        db_session.close()


if __name__ == '__main__':
    # הרצת השרת במצב debug שמאפשר לראות שגיאות בזמן אמת
    app.run(debug=True)





