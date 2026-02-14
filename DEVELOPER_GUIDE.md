# Developer Guide: Book Library App

This guide provides an overview for developers working on the Book Library application.

## 1. Project Overview

The Book Library App is a Flask-based web application designed to help users manage their personal book collections. It allows users to add, view, edit, and delete books, track their reading status, and rate books. The application integrates with external APIs for book metadata (e.g., cover images, descriptions, authors based on ISBN).

## 2. Setup

To get the project up and running on your local machine:

### Prerequisites

*   Python 3.8+
*   pip (Python package installer)

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd book_library_app
    ```
    (Note: Replace `<repository_url>` with the actual repository URL if this were a real git project.)

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the virtual environment:**
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set up environment variables:**
    Create a `.env` file in the root directory (or set them directly in your shell) with necessary configurations. For example:
    ```
    FLASK_APP=app.py
    FLASK_ENV=development
    SECRET_KEY='your_secret_key_here'
    # Add any API keys for external book services if applicable
    # OPEN_LIBRARY_API_KEY='your_open_library_key'
    ```

6.  **Initialize and migrate the database:**
    ```bash
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```

7.  **Run the application:**
    ```bash
    flask run
    ```
    The application should now be accessible at `http://127.0.0.1:5000/`.

## 3. Project Structure

Here's an overview of the key directories and files:

```
book_library_app/
├── app.py                  # Main Flask application file, defines routes and views.
├── config.py               # Configuration settings for the app.
├── extensions.py           # Initializes Flask extensions (e.g., SQLAlchemy, Migrate).
├── models.py               # Defines database models using Flask-SQLAlchemy.
├── requirements.txt        # Lists all Python dependencies.
├── setup.py                # Package setup file.
├── tasks.py                # Background tasks (e.g., book syncing).
├── templates/              # Contains Jinja2 HTML templates.
│   ├── base.html           # Base template for common layout.
│   ├── books.html          # Displays the user's book collection.
│   ├── add_book.html       # Form for adding a new book.
│   ├── edit_book.html      # Form for editing an existing book.
│   ├── home.html           # Landing page.
│   ├── login.html          # User login page.
│   └── register.html       # User registration page.
├── static/                 # (Assumed, for CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── img/
├── migrations/             # Alembic migration scripts for database schema changes.
├── instance/               # Instance-specific files, e.g., the SQLite database.
└── tests/                  # Unit and integration tests.
```

## 4. Key Features

*   **User Authentication:** Register, Login, Logout (Flask-Login).
*   **Book Management:** CRUD operations for books (Add, View, Edit, Delete).
*   **Reading Status & Rating:** Track "to-read", "reading", "read" status and assign ratings.
*   **External API Integration:** Fetches book metadata (cover, author, description) based on ISBN.
*   **Database Migrations:** Managed with Flask-Migrate (Alembic).
*   **Background Syncing:** Placeholder for potential background tasks using `tasks.py`.

## 5. Database

The application uses `Flask-SQLAlchemy` for database interaction and `Flask-Migrate` (which wraps Alembic) for database migrations.

*   **Models:** Defined in `models.py`.
*   **Migrations:**
    *   To create a new migration after model changes: `flask db migrate -m "Description of changes"`
    *   To apply migrations: `flask db upgrade`
    *   To revert migrations: `flask db downgrade`

## 6. Templates

HTML templates are located in the `templates/` directory and use Jinja2 templating engine. `base.html` serves as the main layout, extended by other specific page templates.

## 7. Running Tests

Tests are located in the `tests/` directory. To run them:

1.  Activate your virtual environment.
2.  Navigate to the project root.
3.  Run pytest:
    ```bash
    pytest
    ```

## 8. Contributing

*   Follow the existing code style.
*   Write clear commit messages.
*   Ensure tests pass and add new tests for new features/bug fixes.
*   Open an issue first for major changes or new features to discuss.
