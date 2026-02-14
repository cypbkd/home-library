import requests
import json
import time
import os

# Placeholder for a real API key if needed
GOOGLE_BOOKS_API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY') 

def fetch_book_metadata(isbn):
    print(f"[Background Task] Fetching metadata for ISBN: {isbn}")
    # Simulate a network delay
    time.sleep(5)

    book_data = None
    # Example: Google Books API (replace with actual API call)
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    # if GOOGLE_BOOKS_API_KEY:
    #     url += f"&key={GOOGLE_BOOKS_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        if data and 'items' in data:
            volume_info = data['items'][0]['volumeInfo']
            book_data = {
                'title': volume_info.get('title'),
                'author': ', '.join(volume_info.get('authors', ['Unknown'])),
                'description': volume_info.get('description', 'No description available.'),
                'cover_image_url': volume_info.get('imageLinks', {}).get('thumbnail'),
                'genre': volume_info.get('categories', ['Uncategorized'])[0]
            }
            print(f"[Background Task] Successfully fetched metadata for {isbn}: {book_data.get('title')}")
        else:
            print(f"[Background Task] No metadata found for ISBN: {isbn}")

    except requests.exceptions.RequestException as e:
        print(f"[Background Task] Error fetching metadata for ISBN {isbn}: {e}")
    except json.JSONDecodeError:
        print(f"[Background Task] Error decoding JSON for ISBN {isbn}")
    except Exception as e:
        print(f"[Background Task] An unexpected error occurred for ISBN {isbn}: {e}")

    return book_data


if __name__ == '__main__':
    # Example usage (for testing the task independently)
    test_isbn = "9780321765723"
    metadata = fetch_book_metadata(test_isbn)
    print(f"Finished testing. Metadata: {metadata}")

    test_isbn_no_result = "9780000000000"
    metadata_no_result = fetch_book_metadata(test_isbn_no_result)
    print(f"Finished testing. Metadata (no result): {metadata_no_result}")
