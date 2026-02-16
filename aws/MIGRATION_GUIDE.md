# Migration Guide: SQLite to DynamoDB

This guide helps you migrate existing data from your local SQLite database to AWS DynamoDB.

## Overview

The migration involves:
1. Exporting data from SQLite
2. Transforming data to DynamoDB format
3. Importing data to DynamoDB tables
4. Verifying the migration

## Prerequisites

- Local SQLite database with existing data
- AWS CLI configured
- Python 3.11+ with boto3 installed
- DynamoDB tables already created (run `./deploy.sh dev` first)

## Migration Script

Save this as `migrate_to_dynamodb.py` in the `aws` directory:

```python
#!/usr/bin/env python3
"""
Migration script to move data from SQLite to DynamoDB.
Usage: python migrate_to_dynamodb.py
"""
import sqlite3
import boto3
import uuid
import sys
import os
from datetime import datetime, timezone
from decimal import Decimal

# Configuration
SQLITE_DB_PATH = '../instance/site.db'  # Adjust path as needed
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

# DynamoDB table names
USERS_TABLE = f'BookLibrary-Users-{ENVIRONMENT}'
BOOKS_TABLE = f'BookLibrary-Books-{ENVIRONMENT}'
USER_BOOKS_TABLE = f'BookLibrary-UserBooks-{ENVIRONMENT}'

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)


def migrate_users():
    """Migrate users from SQLite to DynamoDB"""
    print("Migrating users...")
    
    # Connect to SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    
    # DynamoDB table
    table = dynamodb.Table(USERS_TABLE)
    
    # Map old IDs to new UUIDs
    user_id_map = {}
    
    for user in users:
        old_id = user['id']
        new_id = str(uuid.uuid4())
        user_id_map[old_id] = new_id
        
        item = {
            'user_id': new_id,
            'username': user['username'],
            'email': user['email'],
            'password_hash': user['password_hash'],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        table.put_item(Item=item)
        print(f"  Migrated user: {user['username']} (ID: {old_id} -> {new_id})")
    
    conn.close()
    print(f"✓ Migrated {len(users)} users")
    return user_id_map


def migrate_books():
    """Migrate books from SQLite to DynamoDB"""
    print("\nMigrating books...")
    
    # Connect to SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all books
    cursor.execute("SELECT * FROM book")
    books = cursor.fetchall()
    
    # DynamoDB table
    table = dynamodb.Table(BOOKS_TABLE)
    
    # Map old IDs to new UUIDs
    book_id_map = {}
    
    for book in books:
        old_id = book['id']
        new_id = str(uuid.uuid4())
        book_id_map[old_id] = new_id
        
        item = {
            'book_id': new_id,
            'isbn': book['isbn'],
            'title': book['title'],
            'author': book['author'],
            'genre': book['genre'] or 'Unknown',
            'cover_image_url': book['cover_image_url'],
            'description': book['description'],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        table.put_item(Item=item)
        print(f"  Migrated book: {book['title']} (ID: {old_id} -> {new_id})")
    
    conn.close()
    print(f"✓ Migrated {len(books)} books")
    return book_id_map


def migrate_user_books(user_id_map, book_id_map):
    """Migrate user-book relationships from SQLite to DynamoDB"""
    print("\nMigrating user-book relationships...")
    
    # Connect to SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all user-book relationships
    cursor.execute("SELECT * FROM user_book")
    user_books = cursor.fetchall()
    
    # DynamoDB table
    table = dynamodb.Table(USER_BOOKS_TABLE)
    
    for ub in user_books:
        old_user_id = ub['user_id']
        old_book_id = ub['book_id']
        
        # Skip if user or book wasn't migrated
        if old_user_id not in user_id_map or old_book_id not in book_id_map:
            print(f"  Skipping relationship: user {old_user_id}, book {old_book_id} (not found)")
            continue
        
        new_user_id = user_id_map[old_user_id]
        new_book_id = book_id_map[old_book_id]
        user_book_id = str(uuid.uuid4())
        
        item = {
            'user_book_id': user_book_id,
            'user_id': new_user_id,
            'book_id': new_book_id,
            'status': ub['status'],
            'rating': Decimal(str(ub['rating'])) if ub['rating'] else None,
            'sync_status': ub['sync_status'],
            'date_added': ub['date_added'] or datetime.now(timezone.utc).isoformat()
        }
        
        table.put_item(Item=item)
        print(f"  Migrated relationship: user {old_user_id} -> book {old_book_id}")
    
    conn.close()
    print(f"✓ Migrated {len(user_books)} user-book relationships")


def verify_migration():
    """Verify the migration was successful"""
    print("\nVerifying migration...")
    
    users_table = dynamodb.Table(USERS_TABLE)
    books_table = dynamodb.Table(BOOKS_TABLE)
    user_books_table = dynamodb.Table(USER_BOOKS_TABLE)
    
    # Count items
    users_count = users_table.scan(Select='COUNT')['Count']
    books_count = books_table.scan(Select='COUNT')['Count']
    user_books_count = user_books_table.scan(Select='COUNT')['Count']
    
    print(f"\nDynamoDB Tables:")
    print(f"  Users: {users_count}")
    print(f"  Books: {books_count}")
    print(f"  UserBooks: {user_books_count}")
    
    # Compare with SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM user")
    sqlite_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM book")
    sqlite_books = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_book")
    sqlite_user_books = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\nSQLite Database:")
    print(f"  Users: {sqlite_users}")
    print(f"  Books: {sqlite_books}")
    print(f"  UserBooks: {sqlite_user_books}")
    
    # Check if counts match
    if users_count == sqlite_users and books_count == sqlite_books and user_books_count == sqlite_user_books:
        print("\n✓ Migration verified successfully!")
        return True
    else:
        print("\n⚠ Warning: Counts don't match. Please review the migration.")
        return False


def main():
    """Main migration function"""
    print("=" * 60)
    print("SQLite to DynamoDB Migration")
    print("=" * 60)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {AWS_REGION}")
    print(f"SQLite DB: {SQLITE_DB_PATH}")
    print("=" * 60)
    
    # Check if SQLite database exists
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Error: SQLite database not found at {SQLITE_DB_PATH}")
        sys.exit(1)
    
    # Confirm migration
    response = input("\nThis will migrate data to DynamoDB. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)
    
    try:
        # Migrate data
        user_id_map = migrate_users()
        book_id_map = migrate_books()
        migrate_user_books(user_id_map, book_id_map)
        
        # Verify migration
        verify_migration()
        
        print("\n" + "=" * 60)
        print("Migration complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
```

## Step-by-Step Migration

### Step 1: Backup Your SQLite Database

```bash
# Create a backup
cp home-library/instance/site.db home-library/instance/site.db.backup
```

### Step 2: Deploy DynamoDB Tables

```bash
cd home-library/aws
./deploy.sh dev
```

Wait for deployment to complete.

### Step 3: Install Required Python Packages

```bash
pip install boto3
```

### Step 4: Set Environment Variables

```bash
export AWS_REGION=us-east-1
export ENVIRONMENT=dev
```

### Step 5: Run Migration Script

```bash
python migrate_to_dynamodb.py
```

The script will:
- Read all users from SQLite
- Create new UUIDs for each user
- Insert users into DynamoDB
- Repeat for books and user-book relationships
- Verify counts match

### Step 6: Verify Migration

```bash
# Check DynamoDB tables
aws dynamodb scan --table-name BookLibrary-Users-dev --max-items 5
aws dynamodb scan --table-name BookLibrary-Books-dev --max-items 5
aws dynamodb scan --table-name BookLibrary-UserBooks-dev --max-items 5
```

### Step 7: Test the Application

```bash
# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name BookLibrary-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Test login with existing user
curl -X POST ${API_ENDPOINT}/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=your-email@example.com&password=your-password"
```

## Important Notes

### ID Mapping
- SQLite uses integer IDs (1, 2, 3...)
- DynamoDB uses UUIDs (550e8400-e29b-41d4-a716-446655440000)
- The migration script creates a mapping between old and new IDs

### Password Hashes
- Password hashes are migrated as-is
- Users can log in with their existing passwords
- No need to reset passwords

### Timestamps
- SQLite timestamps are converted to ISO 8601 format
- DynamoDB stores timestamps as strings

### Ratings
- SQLite stores ratings as integers
- DynamoDB stores ratings as Decimal (required for numbers)
- The migration script handles this conversion

## Rollback Plan

If migration fails or you need to rollback:

### Option 1: Restore SQLite Backup
```bash
cp home-library/instance/site.db.backup home-library/instance/site.db
```

### Option 2: Clear DynamoDB Tables
```bash
# Delete all items (be careful!)
aws dynamodb scan --table-name BookLibrary-Users-dev \
  --attributes-to-get user_id \
  --query 'Items[*].user_id.S' \
  --output text | \
  xargs -I {} aws dynamodb delete-item \
    --table-name BookLibrary-Users-dev \
    --key '{"user_id":{"S":"{}"}}'
```

## Troubleshooting

### Error: "Table does not exist"
**Solution**: Deploy CloudFormation stack first: `./deploy.sh dev`

### Error: "Unable to locate credentials"
**Solution**: Run `aws configure` to set up AWS credentials

### Error: "Access Denied"
**Solution**: Ensure your AWS user has DynamoDB permissions

### Error: "Duplicate key"
**Solution**: Clear DynamoDB tables before re-running migration

### Warning: "Counts don't match"
**Solution**: Check CloudWatch logs for errors, verify all relationships migrated

## Post-Migration

After successful migration:

1. ✅ Test all application features
2. ✅ Verify user login works
3. ✅ Verify book operations work
4. ✅ Check metadata sync is working
5. ✅ Monitor CloudWatch logs for errors
6. ✅ Keep SQLite backup for 30 days
7. ✅ Update documentation with new architecture

## Data Consistency

### During Migration
- Stop the local Flask application
- Don't allow new user registrations
- Migration should take < 5 minutes for most databases

### After Migration
- All new data goes to DynamoDB
- SQLite database is no longer used
- Keep SQLite backup for reference

## Performance Comparison

| Operation | SQLite | DynamoDB |
|-----------|--------|----------|
| Read user | ~1ms | ~10ms |
| Write user | ~1ms | ~10ms |
| Query books | ~5ms | ~15ms |
| Scalability | Limited | Unlimited |
| Concurrent users | ~100 | Thousands |

DynamoDB has slightly higher latency but scales infinitely.

## Cost Impact

- SQLite: Free (local storage)
- DynamoDB: ~$2-5/month for low usage
- Free tier covers most development usage

---

**Need Help?** Check CloudWatch Logs or AWS DynamoDB console for detailed error messages.
