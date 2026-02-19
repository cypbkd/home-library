"""
Background tasks for AWS Lambda using SQS for async processing.
Replaces threading with SQS message queue.
"""
import requests
import json
import os
import boto3
from dynamodb_models import DynamoDBBook, DynamoDBUserBook

# Initialize SQS client
sqs = boto3.client('sqs', region_name=os.environ.get('AWS_REGION'))
QUEUE_URL = os.environ.get('METADATA_QUEUE_URL')

GOOGLE_BOOKS_API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY')


def fetch_book_metadata_async(user_book_id):
    """
    Queue a metadata fetch task by sending message to SQS.
    This is called from the main Lambda function.
    """
    if not QUEUE_URL:
        print("[Warning] METADATA_QUEUE_URL not set. Skipping async metadata fetch.")
        return
    
    message = {
        'user_book_id': user_book_id
    }
    
    try:
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        print(f"[SQS] Queued metadata fetch for user_book_id: {user_book_id}")
    except Exception as e:
        print(f"[SQS Error] Failed to queue metadata fetch: {e}")


def process_metadata_fetch(event, context):
    """
    Lambda handler for processing SQS messages.
    This function is triggered by SQS and fetches book metadata.
    """
    for record in event['Records']:
        try:
            message_body = json.loads(record['body'])
            user_book_id = message_body['user_book_id']
            
            print(f"[Metadata Worker] Processing user_book_id: {user_book_id}")
            
            # Get user book and book details
            user_book = DynamoDBUserBook.get_by_id(user_book_id)
            if not user_book:
                print(f"[Metadata Worker] UserBook {user_book_id} not found")
                continue
            
            book = DynamoDBBook.get_by_id(user_book['book_id'])
            if not book:
                print(f"[Metadata Worker] Book {user_book['book_id']} not found")
                continue
            
            isbn = book['isbn']
            print(f"[Metadata Worker] Fetching metadata for ISBN: {isbn}")
            
            # Fetch from Google Books API
            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and 'items' in data:
                volume_info = data['items'][0]['volumeInfo']
                
                # Update book with metadata
                DynamoDBBook.update(
                    book['book_id'],
                    title=volume_info.get('title', book['title']),
                    author=', '.join(volume_info.get('authors', [book['author']])),
                    description=volume_info.get('description', 'No description available.'),
                    cover_image_url=volume_info.get('imageLinks', {}).get('thumbnail') or 
                                   "https://www.press.uillinois.edu/books/images/no_cover_lg.jpg",
                    genre=volume_info.get('categories', ['Uncategorized'])[0] if volume_info.get('categories') else book.get('genre', 'Unknown')
                )
                
                # Update sync status
                DynamoDBUserBook.update(user_book_id, sync_status='SYNCED')
                print(f"[Metadata Worker] Successfully updated metadata for ISBN: {isbn}")
            else:
                print(f"[Metadata Worker] No metadata found for ISBN: {isbn}")
                updates = {}
                if book.get('title') == 'Fetching Title...':
                    updates['title'] = 'Unknown'
                if book.get('author') == 'Fetching Author...':
                    updates['author'] = 'Unknown'
                if updates:
                    DynamoDBBook.update(book['book_id'], **updates)
                DynamoDBUserBook.update(user_book_id, sync_status='FAILED')
        
        except requests.exceptions.RequestException as e:
            print(f"[Metadata Worker] Request error: {e}")
            if 'user_book_id' in locals():
                if 'book' in locals():
                    updates = {}
                    if book.get('title') == 'Fetching Title...':
                        updates['title'] = 'Unknown'
                    if book.get('author') == 'Fetching Author...':
                        updates['author'] = 'Unknown'
                    if updates:
                        DynamoDBBook.update(book['book_id'], **updates)
                DynamoDBUserBook.update(user_book_id, sync_status='FAILED')
        except Exception as e:
            print(f"[Metadata Worker] Unexpected error: {e}")
            if 'user_book_id' in locals():
                if 'book' in locals():
                    updates = {}
                    if book.get('title') == 'Fetching Title...':
                        updates['title'] = 'Unknown'
                    if book.get('author') == 'Fetching Author...':
                        updates['author'] = 'Unknown'
                    if updates:
                        DynamoDBBook.update(book['book_id'], **updates)
                DynamoDBUserBook.update(user_book_id, sync_status='FAILED')
    
    return {
        'statusCode': 200,
        'body': json.dumps('Metadata processing complete')
    }
