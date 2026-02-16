import requests
import json
import os
from flask import current_app

# Placeholder for a real API key if needed
GOOGLE_BOOKS_API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY')

def fetch_book_metadata(app, user_book_id):
    from extensions import db
    from models import Book, UserBook

    with app.app_context():
        user_book = db.session.get(UserBook, user_book_id)
        if not user_book:
            current_app.logger.info(f"[Background Task] UserBook with ID {user_book_id} not found.")
            return

        book = db.session.get(Book, user_book.book_id)
        if not book:
            current_app.logger.info(f"[Background Task] Book with ID {user_book.book_id} not found.")
            return

        isbn = book.isbn
        current_app.logger.info(f"[Background Task] Fetching metadata for ISBN: {isbn}")

        book_data = None
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        # if GOOGLE_BOOKS_API_KEY:
        #     url += f"&key={GOOGLE_BOOKS_API_KEY}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data and 'items' in data:
                volume_info = data['items'][0]['volumeInfo']
                book.title = volume_info.get('title')
                book.author = ', '.join(volume_info.get('authors', ['Unknown']))
                book.description = volume_info.get('description', 'No description available.')
                book.cover_image_url = volume_info.get('imageLinks', {}).get('thumbnail') or "https://www.press.uillinois.edu/books/images/no_cover_lg.jpg"
                book.genre = volume_info.get('categories', ['Uncategorized'])[0]
                user_book.sync_status = 'SYNCED'
                db.session.commit()
                current_app.logger.info(f"[Background Task] Successfully fetched and updated metadata for {isbn}: {book.title}")
            else:
                current_app.logger.info(f"[Background Task] No metadata found for ISBN: {isbn}")
                user_book.sync_status = 'FAILED'
                db.session.commit()

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"[Background Task] Error fetching metadata for ISBN {isbn}: {e}")
            user_book.sync_status = 'FAILED'
            db.session.commit()
        except json.JSONDecodeError:
            current_app.logger.error(f"[Background Task] Error decoding JSON for ISBN {isbn}")
            user_book.sync_status = 'FAILED'
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"[Background Task] An unexpected error occurred for ISBN {isbn}: {e}")
            user_book.sync_status = 'FAILED'
            db.session.commit()
if __name__ == '__main__':
    # Example usage (for testing the task independently)
    # This part needs a Flask app context to run, so it's not directly runnable here without setting up a test app.
    # For now, commenting it out or simplifying for independent testing if possible.
    print("This task is designed to be run within a Flask application context.")
    print("To test, you would typically use a test client or run a small Flask app.")
