import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

# הגדרת בסיס לכל המחלקות שיורשות ממנו
Base = declarative_base()


class BaseModel(Base):
    """מודל בסיס המספק תכונות משותפות לכל הטבלאות (הורשה)"""
    __abstract__ = True  # מציין ל-SQLAlchemy לא ליצור טבלה עבור המחלקה הזו עצמה
    id = Column(Integer, primary_key=True)
    # יצירת חותמת זמן אוטומטית לכל רשומה
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def save(self, session):
        """מתודה לשמירת האובייקט הנוכחי ב-DB"""
        session.add(self)
        session.commit()  # שלב קריטי: ביצוע השינויים בפועל בבסיס הנתונים


class User(BaseModel):
    """מודל משתמש עם רמות הרשאה (Admin, Uploader, Reader)"""
    __tablename__ = 'users'
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)  # סיסמה מוצפנת
    role = Column(String(20), default='Reader')
    is_approved_uploader = Column(Boolean, default=False)  # הרשאה מיוחדת מהמנהל
    # קשר יחיד-לרבים: משתמש אחד יכול להעלות הרבה מתכונים
    recipes = relationship("Recipe", back_populates="uploader")


class Recipe(BaseModel):
    """מודל המתכון הראשי"""
    __tablename__ = 'recipes'
    title = Column(String(255), nullable=False)
    instructions = Column(String)
    image_path = Column(String)  # נתיב לתמונה המקורית
    variation_paths = Column(String)  # נתיבי 3 הווריאציות (נשמר כמחרוזת JSON)
    recipe_type = Column(String(20), default='Parve')  # סוג המתכון לסינון

    # קישור למשתמש שהעלה (ForeignKey)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # קשרים וניהול מחיקה (Cascade) - אם נמחק מתכון, נמחקים גם הרכיבים שלו
    ingredients = relationship("IngredientEntry", back_populates="recipe", cascade="all, delete-orphan")
    uploader = relationship("User", back_populates="recipes")

    def get_variation_paths(self):
        """המרת מחרוזת ה-JSON מה-DB חזרה לרשימת פייתון לשימוש בגלריה"""
        if self.variation_paths:
            return json.loads(self.variation_paths)
        return []

    def set_variation_paths(self, paths_list):
        """המרה של רשימת נתיבים למחרוזת JSON לצורך שמירה ב-DB"""
        self.variation_paths = json.dumps(paths_list)


class IngredientEntry(BaseModel):
    """מודל לרכיבים בתוך מתכון (One-to-Many)"""
    __tablename__ = 'ingredients'
    amount = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    product = Column(String(100), nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    recipe = relationship("Recipe", back_populates="ingredients")