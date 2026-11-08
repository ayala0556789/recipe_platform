# Recipe Platform — Recipe Sharing and Search by Your Ingredients

A recipe sharing platform built with Flask and SQLAlchemy. Users upload recipes, search for recipes by the ingredients they already have, and upload permissions are managed by an administrator.

<!-- Add a screenshot or short GIF here -->
<!-- ![Recipe Platform demo](docs/demo.gif) -->

## Key Ideas

The app solves the "what can I cook with what's in my fridge?" problem:

- **Set-intersection search:** instead of relying on text matching, the user's ingredients and each recipe's ingredients are converted to Python sets. The app computes the overlap percentage and filters out recipes below a 20% match.
- **On-the-fly image processing:** every uploaded image is processed automatically with Pillow, producing three variations (grayscale, rotated, thumbnail) for use in different views.

## Architecture

- `models`: data layer (`BaseModel`, `User`, `Recipe`, `IngredientEntry`) using SQLAlchemy.
- `controllers`: business logic (`user_controller` for registration and permissions, `recipe_controller` for search and image processing).
- `templates`: server-rendered dynamic HTML pages (Jinja2).
- `static`: styling and the user-uploaded images.
- `app.py`: the entry point that defines the routes and wires everything together.

## Key Features

- **Smart ingredient search:** the user enters available ingredients and recipes are ranked by match percentage.
- **Recipe gallery and filtering:** browse by type (dairy / meat / pareve).
- **Role-based access control (RBAC):** three roles: Reader (view and search), Uploader (upload recipes), Admin (full management).
- **Approval workflow:** new users who request upload rights start with a "pending" status and can upload only after an Admin approves them.
- **Admin panel:** approve users and delete recipes from a dedicated dashboard.
- **Automatic image handling:** UUIDs prevent filename collisions, and design variations are created for each recipe.

## Tech Stack

| Area | Technology |
|---|---|
| Backend / web framework | Python, Flask |
| Database and ORM | SQLite, SQLAlchemy |
| Image processing | Pillow (PIL) |
| Security | Werkzeug Security |
| Frontend (server-side) | Jinja2 (HTML), CSS |
| Environment | python-dotenv |

## Getting Started

1. Clone the project: `git clone <repository-url>` and `cd recipe_platform`.
2. Create and activate a virtual environment: `python -m venv venv`, then `source venv/bin/activate` (or `venv\Scripts\activate` on Windows).
3. Install dependencies: `pip install -r requirements.txt`.
4. Create a `.env` file in the project root with: `SECRET_KEY=your_secret_key_here`.
5. Run the app: `python app.py`. The `recipe_platform.db` database is created automatically on first run. The server runs at `http://127.0.0.1:5000`.

## Demo Account

To explore the admin panel and the full feature set, log in with this **demo-only** Admin account:

- Email: `admin@gmail.com`
- Password: `123456`

## Security Notes

- **Secrets separation:** `SECRET_KEY` is loaded from a `.env` file excluded from Git via `.gitignore`.
- **User content protection:** `static/uploads/` and the database file are also excluded in `.gitignore` to prevent data leaks and repository bloat.
- **Route protection:** sensitive actions (upload, delete, user management) require authentication and a matching role.


