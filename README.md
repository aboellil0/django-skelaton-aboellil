# Django Project Skeleton

This is a Django project skeleton ready to be integrated into your main project.

## Project Structure

- **project_skeleton/**: Main Django project settings
- **core/**: Sample Django app
- **static/**: Static files (CSS, JS, images)
- **media/**: User-uploaded media files
- **templates/**: HTML templates

## Setup Instructions

1. Create a virtual environment:
   ```
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

## Ready to Transfer

This skeleton is ready to be copied into your main project when it's ready!
