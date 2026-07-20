

import os
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Recipe, IngredientEntry  # ייבוא מחלקות ה-ORM
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session # הוספנו session
from PIL import Image,ImageOps
import json
import uuid

# 1. הגדרת נתיב הבסיס (איפה ש-app.py נמצא)
# basedir = os.path.abspath(os.path.dirname(__file__))

# # 2.  נתיבי המערכת לייבוא מודלים
# sys.path.append(basedir)
# sys.path.append(os.path.abspath(os.path.join(basedir, '..')))
# 3. הגדרת האפליקציה עם נתיבים גמישים
# אם app.py כבר בתוך recipe_platform, אנחנו לא צריכים להוסיף את השם שוב לנתיב התיקיות
# template_dir = os.path.join(basedir, 'templates')
# static_dir = os.path.join(basedir, 'static')
# # בדיקה: אם התיקיות לא שם, אולי הן בתיקייה פנימית יותר?
# if not os.path.exists(template_dir):
#     template_dir = os.path.join(basedir, 'recipe_platform', 'templates')
#     static_dir = os.path.join(basedir, 'recipe_platform', 'static')



#למה? ב-Flask, קבצים שמוגשים לדפדפן (כמו תמונות) חייבים להיות בתיקיית static.
# 1. טעינת משתני סביבה מהקובץ .env (כמו SECRET_KEY)
load_dotenv()

# 2. הגדרת אפליקציית Flask
app = Flask(__name__) #, template_folder=template_dir, static_folder=static_dir)

# 3. הגדרות קונפיגורציה
# המפתח הסודי משמש לאבטחת המידע שעובר בין השרת לדפדפן
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key_123')

# הגדרת נתיב למסד הנתונים
#create_engine(...):
# זו פונקציה שמספקת SQLAlchemy ליצירת אובייקט engine.
# היא מקבלת כארגומנט את כתובת ה-URL של בסיס הנתונים

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///recipe_platform.db')
engine = create_engine(DATABASE_URL)

# יצירת מחלקה לניהול סשנים (תקשורת) מול ה-DB
#
Session = sessionmaker(bind=engine)

# 4. הגדרת תיקיית העלאת תמונות
# app.config['UPLOAD_FOLDER'] = os.path.join(static_dir, 'uploads')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# 5. פונקציה לאתחול מסד הנתונים
def init_db():
    """יוצרת את הטבלאות ב-DB לפי המודלים שהגדרנו ב-models.py"""
    Base.metadata.create_all(engine)
    print("Database initialized and tables created.")


# הרצת האתחול בתוך ה-Context של פלאסק
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
# 6. נתיבי אפליקציה (Routes)
# ------------------------------------

@app.route('/')
def home():
    """מציג את דף הבית עם רשימת כל המתכונים"""
    # פתיחת סשן (חיבור זמני) למסד הנתונים
    session = Session()

    # שליפת כל האובייקטים מסוג Recipe (מתכון)
    all_recipes = session.query(Recipe).all()
    # --- קוד בדיקה זמני: הדפסת רכיבים לטרמינל ---
    print("\n--- בדיקת מסד נתונים ---")
    for r in all_recipes:
        print(f"מתכון: {r.title}")
        for ing in r.ingredients:
            print(f"  - רכיב: {ing.amount} {ing.unit} {ing.product}")
    print("--------------------------\n")
    # --- סוף קוד בדיקה ---
    # סגירת הסשן בסיום הפעולה
    session.close()

    # שליחת הנתונים לדף index.html
    return render_template('index.html', recipes=all_recipes)


# ------------------------------------
# 7. הפעלת השרת
# ------------------------------------
#עלינו להגיד לשרת מה לעשות כשמישהו נכנס לכתובת /register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # שליפת הנתונים מהטופס שהמשתמש מילא
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        ## generate_password_hash:
        # הצפנת הסיסמה לפני השמירה (אבטחה!)
        #זוהי פונקציה שמיובאת מ app.py
        # היא לוקחת את הסיסמה (למשל "123") והופכת אותה לרצף אותיות ארוך ובלתי קריא. זה קריטי לאבטחה!
        hashed_pw = generate_password_hash(password)

        # יצירת מופע חדש של משתמש
        new_user = User(email=email, password_hash=hashed_pw, role=role)

        # שמירה למסד הנתונים
        session = Session()
        try:
            # new_user.save(session):
            # כאן  משתמשים בפונקציה שכתובה ב-models.py.
            # היא לוקחת את אובייקט הפייתון שיצרנו והופכת אותו לשורה חדשה בטבלת המשתמשים ב-DB
            new_user.save(session)
            print(f"User {email} registered successfully!")
            return redirect(url_for('home')) # חזרה לדף הבית אחרי הצלחה
        except Exception as e:
            print(f"Error during registration: {e}")
            return "חלה שגיאה (ייתכן שהמייל כבר קיים במערכת)"
        finally:
            session.close()

    # אם זה GET (כלומר המשתמש רק נכנס לדף) - נציג לו את הקובץ שיצרנו
    return render_template('register.html')

# הסבר קצר על מה שקורה כאן:
# methods=['GET', 'POST']: דף ההרשמה עובד בשני מצבים.
# GET
# הוא המצב שבו המשתמש רק "מבקש" לראות את הדף.
# POST
# הוא המצב שבו המשתמש "שולח" את הנתונים שלו לשרת



#הוספת נתיב התחברות (/login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        db_session = Session()
        # חיפוש המשתמש לפי המייל שלו
        #filter_by(email=email).first()
        #זו שאילתה בשיטת ORM שמחפשת בטבלת המשתמשים את השורה שבה המייל מתאים למה שהוקלד.
        user = db_session.query(User).filter_by(email=email).first()
        db_session.close()

        # בדיקה: האם המשתמש קיים והאם הסיסמה נכונה?
        if user and check_password_hash(user.password_hash, password):
            #check_password_hash
            #אי אפשר להשוות סיסמה רגילה לסיסמה מוצפנת בעזרת ==. הפונקציה הזו יודעת לקחת את ה-"ג'יבריש" שיש לנו ב-DB ולבדוק אם הוא מתאים לסיסמה שהוקלדה.

            # יצירת "סשן" - השרת זוכר את המשתמש לפי ה-ID שלו
            #בעצם אנחנו בעצם אומרים לשרת: "שים למשתמש הזה צמיד (סשן) ותכתוב עליו את מספר ה-ID שלו".
            session['user_id'] = user.id
            #זה כמו לתת למשתמש "כרטיס כניסה" זמני. מעכשיו, בכל פעם שהדפדפן יפנה לשרת, השרת ידע מי המשתמש בלי לבקש סיסמה שוב.
            session['user_role'] = user.role
            print(f"User {email} logged in!")
            return redirect(url_for('home'))
        else:
            return "מייל או סיסמה לא נכונים. נסה שוב."

    return render_template('login.html')

@app.route('/logout')
def logout():
    """התנתקות מהמערכת"""
    session.clear() # מוחק את נתוני המשתמש מהזיכרון של השרת
    #אנחנו פשוט אומרים לשרת: "גזור את הצמיד (מחק את הסשן), מעכשיו המשתמש הזה שוב זר מבחינתנו".
    return redirect(url_for('home'))

#כתיבת פונקציית העלאת המתכון
#הפונקציה הבאה עושה 3 דברים:
#1. תבדוק אם המשתמש מחובר (בעל הרשאה)
#2. תשמור את התמונה המקורית בתיקיית uploads עם שם ייחודי.
#3. תפתח את התמונה עם Pillow, תייצר את הווריאציות ותשמור אותן ב-DB.


@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    # 1. בדיקה האם המשתמש בכלל מחובר (בדיקה ראשונית מהסשן)
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 2. בדיקה מול מסד הנתונים - האם המשתמש באמת מאושר?
    db_session = Session()
    user = db_session.query(User).get(session['user_id'])

    # בדיקת הרשאות
    is_allowed = False
    if user:
        if user.role == 'Admin':
            is_allowed = True
        elif user.role == 'Uploader' and user.is_approved_uploader == True:
            is_allowed = True

    if not is_allowed:
        db_session.close()  # סגירת הסשן לפני החסימה
        return "החשבון שלך ממתין לאישור מנהל. לא ניתן להעלות מתכונים עדיין.", 403

    # אם הגענו לכאן, המשתמש מורשה!
    # אנחנו סוגרים את הסשן של הבדיקה כדי לפתוח אחד חדש בתוך ה-POST במידת הצורך
    db_session.close()

    if request.method == 'POST':
        title = request.form.get('title')
        instructions = request.form.get('instructions')
        recipe_type = request.form.get('recipe_type')
        image_file = request.files.get('image')

        if not image_file:
            return "חובה להעלות תמונה", 400

        # עיבוד תמונה ()
        ext = os.path.splitext(image_file.filename)[1]
        unique_name = str(uuid.uuid4())
        original_name = f"{unique_name}_original{ext}"
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_name)
        image_file.save(original_path)

        # variation_paths = []
        # img = Image.open(original_path)
        # if img.mode in ("RGBA", "P"):
        #     img = img.convert("RGB")

        # (כאן מגיעים כל הוריאציות שכתבת - קיצרתי כדי שיהיה ברור)
        # ... (שחור לבן, סיבוב, thumbnail) ...
        # יצירת ווריאציות לתמונה (שחור-לבן, סיבוב, thumbnail)
        img = Image.open(original_path)

        if img.mode in ("RGBA", "P"):  # המרה ל-RGB אם התמונה עם שקיפות
            img = img.convert("RGB")

        variation_paths = []

        # # 1. יצירת תמונה שחור-לבן
        # bw_image = img.convert('L')
        # bw_path = original_path.replace("original", "bw")
        # bw_image.save(bw_path)
        # variation_paths.append(bw_path)
        #
        # # 2. סיבוב התמונה ב-90 מעלות
        # rotated_image = img.rotate(90)
        # rotated_path = original_path.replace("original", "rotated")
        # rotated_image.save(rotated_path)
        # variation_paths.append(rotated_path)
        #
        # # 3. יצירת תמונת thumbnail (מיני-תמונה)
        # thumbnail_image = img.copy()
        # thumbnail_image.thumbnail((100, 100))  # גודל המיני-תמונה 100x100
        # thumbnail_path = original_path.replace("original", "thumbnail")
        # thumbnail_image.save(thumbnail_path)
        # variation_paths.append(thumbnail_path)
        # 1. יצירת תמונה שחור-לבן
        bw_image = img.convert('L')
        bw_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_name}_bw{ext}")
        bw_image.save(bw_path)
        variation_paths.append(f"uploads/{unique_name}_bw{ext}")

        # 2. סיבוב התמונה ב-90 מעלות
        rotated_image = img.rotate(90)
        rotated_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_name}_rotated{ext}")
        rotated_image.save(rotated_path)
        variation_paths.append(f"uploads/{unique_name}_rotated{ext}")

        # 3. יצירת תמונת thumbnail
        thumbnail_image = img.copy()
        thumbnail_image.thumbnail((100, 100))  # גודל המיני-תמונה 100x100
        thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_name}_thumbnail{ext}")
        thumbnail_image.save(thumbnail_path)
        variation_paths.append(f"uploads/{unique_name}_thumbnail{ext}")

        # שמירה למסד הנתונים
        new_db_session = Session()
        try:
            new_recipe = Recipe(
                title=title,
                instructions=instructions,
                recipe_type=recipe_type,
                image_path=f"uploads/{original_name}",
                user_id=session['user_id']
            )
            # אם יש לך את הפונקציות וריאציות, תוסיפי אותן כאן
            new_recipe.set_variation_paths(variation_paths)

            ingredients_text = request.form.get('ingredients_list')
            if ingredients_text:
                lines = ingredients_text.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) == 3:
                            new_ingredient = IngredientEntry(
                                amount=float(parts[0].strip()),
                                unit=parts[1].strip(),
                                product=parts[2].strip(),
                                recipe=new_recipe
                            )
                            new_db_session.add(new_ingredient)

            new_recipe.save(new_db_session)
            return redirect(url_for('home'))
        except Exception as e:
            new_db_session.rollback()
            return f"שגיאה: {e}"
        finally:
            new_db_session.close()

    return render_template('add_recipe.html')

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    db_session = Session()
    try:
        # שליפת המתכון
        recipe = db_session.query(Recipe).filter_by(id=recipe_id).first()

        if not recipe:
            return "המתכון לא נמצא", 404

        # כאן אנחנו "מכריחים" את פייתון לטעון את הרכיבים עכשיו, כשהסשן פתוח
        # פשוט על ידי גישה אליהם
        temp_ingredients = recipe.ingredients

        variations = recipe.get_variation_paths()

        # אנחנו מעבירים את הנתונים לדף כשהסשן עדיין פתוח
        return render_template('view_recipe.html', recipe=recipe, variations=variations)

    finally:
        # הסשן ייסגר רק אחרי שהדף נוצר (או אם הייתה שגיאה)
        db_session.close()


@app.route('/search', methods=['GET', 'POST'])
def search_recipes():
    results = []
    if request.method == 'POST':
        # 1. קבלת הרכיבים מהמשתמש והפיכתם ל-Set (שלב 1 באפיון)
        #למה Set?
        # בגלל שזהו מבנה נתונים שמאפשר לבצע פעולות מתמטיות כמו "חיתוך" בקלות ובמהירות רבה.
        # במקום לעשות לולאה בתוך לולאה, אנחנו משתמשים בפונקציה intersection.
        user_input = request.form.get('user_ingredients', '')
        user_set = {i.strip() for i in user_input.split(',') if i.strip()}

        db_session = Session()
        all_recipes = db_session.query(Recipe).all()

        for recipe in all_recipes:
            # 2. יצירת Set של רכיבי המתכון מה-DB
            recipe_ingredients = {ing.product for ing in recipe.ingredients}

            if not recipe_ingredients:
                continue

            # 3. חישוב רכיבים משותפים (Intersection - שלב 2 באפיון)
            common_ingredients = user_set.intersection(recipe_ingredients)

            # 4. חישוב ציון ההתאמה (Score - שלב 3 באפיון)
            # נוסחה: (כמות משותפת / סה"כ רכיבים במתכון) * 100
            score = (len(common_ingredients) / len(recipe_ingredients)) * 100

            # סינון - רק מתכונים עם מעל 20% התאמה (שלב 4 באפיון)
            if score >= 20:
                results.append({
                    'recipe': recipe,
                    'score': round(score, 1)
                })

        # 5. מיון התוצאות לפי הציון בסדר יורד
        results.sort(key=lambda x: x['score'], reverse=True)
        db_session.close()

    return render_template('search.html', results=results)


@app.route('/admin/dashboard')
def admin_dashboard():
    # בדיקת אבטחה: רק Admin יכול להיכנס
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        return "גישה נדחתה: דף זה מיועד למנהלים בלבד", 403

    db_session = Session()
    # שליפת כל המשתמשים שביקשו להיות Uploader ועדיין לא מאושרים
    pending_users = db_session.query(User).filter_by(role='Uploader', is_approved_uploader=False).all()
    pending_recipie = db_session.query(User).filter_by(role='Uploader', is_approved_uploader=False).all()


    db_session.close()
    return render_template('admin_dashboard.html', users=pending_users)


@app.route('/admin/approve/<int:user_id>')
def approve_user(user_id):
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        return "גישה נדחתה", 403

    db_session = Session()
    user = db_session.query(User).filter_by(id=user_id).first()

    if user:
        user.is_approved_uploader = True  # שינוי הסטטוס למאושר
        db_session.commit()

    db_session.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete_recipe/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    # בדיקה שהמשתמש הוא מנהל
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        return "גישה נדחתה: דף זה מיועד למנהלים בלבד", 403

    # פתיחת סשן למסד נתונים
    db_session = Session()

    try:
        # שליפת המתכון מהמסד
        recipe = db_session.query(Recipe).filter_by(id=recipe_id).first()

        if not recipe:
            return "המתכון לא נמצא", 404

        # מחיקת המתכון
        db_session.delete(recipe)
        db_session.commit()

        return redirect(url_for('admin_dashboard'))  # חזרה לדף הניהול של המנהל

    except Exception as e:
        db_session.rollback()
        return f"שגיאה במחיקת המתכון: {e}"

    finally:
        db_session.close()


#למה כתבנו את זה ככה?
#session.get('user_role'):
# האפיון דרש שרק משתמשים מאושרים (Admin או Uploader)
# יוכלו להעלות מתכונים.
# זה שלב האבטחה שלנו.
#uuid.uuid4():
# זהו "מזהה ייחודי גלובלי".
# אם שני אנשים יעלו תמונה בשם pizza.jpg,
# ה-UUID יבטיח שאחד יהיה a1-pizza.jpg והשני b2-pizza.jpg.
#json.dumps (דרך set_variation_paths):
# כפי שציינת ב-models, ה-DB לא יודע לשמור רשימות.
# לכן אנחנו הופכים את רשימת נתיבי התמונות לטקסט ארוך.


if __name__ == '__main__':
    # הרצת השרת במצב debug שמאפשר לראות שגיאות בזמן אמת
    app.run(debug=True)

# . הסבר קצר על מה שיצרת (למה זה עובד?)
# Base.metadata.create_all(engine):
# הפקודה הזו בודקת את כל המחלקות שיורשות מ-Base בתוך models.py.
# היא רואה את User, Recipe ו-IngredientEntry
# ויוצרת בתוך ה-SQLite טבלאות עם עמודות שמתאימות בדיוק להגדרות שלך (Integer, String וכו').
#
# הורשה מ-BaseModel:
# בגלל שכל המחלקות שלך יורשות מ-BaseModel,
# לכולן יש עכשיו עמודת id ו-created_at באופן אוטומטי,
# וגם את הפונקציות save() ו-delete() שבנית.
