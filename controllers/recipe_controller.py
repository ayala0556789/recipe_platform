import os

import uuid
from PIL import Image



def process_recipe_images(image_file, upload_folder):
    """טיפול בתמונות באמצעות ספריית Pillow """
    # יצירת שם ייחודי כדי למנוע דריסת קבצים (UUID)
    ext = os.path.splitext(image_file.filename)[1]
    unique_name = str(uuid.uuid4())

    # 1. שמירת התמונה המקורית
    original_filename = f"{unique_name}_original{ext}"
    original_path = os.path.join(upload_folder, original_filename)
    image_file.save(original_path)

    # פתיחת התמונה לעיבוד
    img = Image.open(original_path)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")  # המרה אם יש שקיפות

    variations = []

    # וריאציה 1: שחור-לבן
    bw_name = f"{unique_name}_bw{ext}"
    img.convert('L').save(os.path.join(upload_folder, bw_name))
    variations.append(f"uploads/{bw_name}")

    # וריאציה 2: סיבוב ב-90 מעלות
    rot_name = f"{unique_name}_rotated{ext}"
    img.rotate(90).save(os.path.join(upload_folder, rot_name))
    variations.append(f"uploads/{rot_name}")

    # וריאציה 3: תמונה ממוזערת (Thumbnail)
    thumb_name = f"{unique_name}_thumb{ext}"
    thumb_img = img.copy()
    thumb_img.thumbnail((100, 100))
    thumb_img.save(os.path.join(upload_folder, thumb_name))
    variations.append(f"uploads/{thumb_name}")

    return f"uploads/{original_filename}", variations


def search_algorithm(user_ingredients_str, all_recipes):
    """אלגוריתם חיפוש לפי רכיבים (שימוש ב-Set Intersection)"""
    # ניקוי הקלט של המשתמש והפיכתו ל-Set
    user_set = {i.strip().lower() for i in user_ingredients_str.split(',') if i.strip()}
    results = []

    for recipe in all_recipes:
        # יצירת Set של רכיבי המתכון הנוכחי
        recipe_set = {ing.product.lower() for ing in recipe.ingredients}
        if not recipe_set: continue

        # חישוב חיתוך (Intersection) - מה שיש למשתמש וגם במתכון
        common = user_set.intersection(recipe_set)

        # חישוב ציון התאמה (Matching Score)
        score = (len(common) / len(recipe_set)) * 100

        print(f"💙💙score{score}")


        # סינון לפי אחוז מינימלי (20%)
        if score >= 20:
            results.append({
                'recipe': recipe,
                'score': round(score, 1)
            })
    # # 4. שליחת המשתנה בשם 'results' כדי שיתאים ל- {% for item in results %} ב-HTML
    #     return render_template('search.html', results=results, searched_for=searched_for)
    # מיון התוצאות מהציון הגבוה לנמוך
    return sorted(results, key=lambda x: x['score'], reverse=True)

