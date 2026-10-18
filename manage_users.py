#!/usr/bin/env python3
"""
Scout Inventory — User Manager
================================
Manage who can access the Scout Inventory app by maintaining
the allowedUsers collection in Firestore.

SETUP
-----
1.  pip install firebase-admin
2.  Place serviceAccountKey.json in the same folder as this script
3.  Run one of the commands below

COMMANDS
--------
  List all current users:
    python manage_users.py --list

  Add a single user:
    python manage_users.py --add leader@gmail.com

  Add multiple users at once:
    python manage_users.py --add leader1@gmail.com leader2@scouts.org leader3@gmail.com

  Add from a text file (one email per line):
    python manage_users.py --add-file users.txt

  Remove a user:
    python manage_users.py --remove leader@gmail.com

  Remove multiple users:
    python manage_users.py --remove leader1@gmail.com leader2@gmail.com
"""

import argparse
import sys
import os
import re

def valid_email(email):
    return re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email) is not None

def connect():
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        print("ERROR: firebase-admin not installed. Run: pip install firebase-admin")
        sys.exit(1)

    key_path = 'serviceAccountKey.json'
    if not os.path.exists(key_path):
        print(f"ERROR: serviceAccountKey.json not found in current folder.")
        print("Download it from Firebase console → Project Settings → Service accounts → Generate new private key")
        sys.exit(1)

    if not firebase_admin._apps:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)

    return firestore.client()

def list_users(db):
    users = db.collection('allowedUsers').stream()
    user_list = sorted([doc.id for doc in users])
    if not user_list:
        print("No users in the allowed list.")
        return
    print(f"\n{'─'*45}")
    print(f"  {'#':<4} {'Email'}")
    print(f"{'─'*45}")
    for i, email in enumerate(user_list, 1):
        print(f"  {i:<4} {email}")
    print(f"{'─'*45}")
    print(f"  {len(user_list)} user(s) total\n")

def add_users(db, emails):
    # Validate
    valid = []
    for email in emails:
        email = email.strip().lower()
        if not email:
            continue
        if not valid_email(email):
            print(f"  ⚠  Skipping invalid email: {email}")
            continue
        valid.append(email)

    if not valid:
        print("No valid email addresses to add.")
        return

    # Check existing
    existing = {doc.id for doc in db.collection('allowedUsers').stream()}
    to_add = [e for e in valid if e not in existing]
    dupes  = [e for e in valid if e in existing]

    if dupes:
        print(f"\n  Already in allowed list (skipped):")
        for e in dupes:
            print(f"    · {e}")

    if not to_add:
        print("\nNothing new to add.")
        return

    print(f"\n  Adding {len(to_add)} user(s)…")
    added = 0
    for email in to_add:
        try:
            db.collection('allowedUsers').document(email).set({'email': email})
            print(f"  ✓  {email}")
            added += 1
        except Exception as e:
            print(f"  ✗  {email} — ERROR: {e}")

    print(f"\n  Done — {added} user(s) added.\n")

def remove_users(db, emails):
    existing = {doc.id for doc in db.collection('allowedUsers').stream()}
    to_remove = []
    for email in emails:
        email = email.strip().lower()
        if email not in existing:
            print(f"  ⚠  Not found in allowed list: {email}")
        else:
            to_remove.append(email)

    if not to_remove:
        print("Nothing to remove.")
        return

    print(f"\n  Removing {len(to_remove)} user(s):")
    for email in to_remove:
        print(f"    · {email}")

    confirm = input("\n  Are you sure? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("  Cancelled.")
        return

    removed = 0
    for email in to_remove:
        try:
            db.collection('allowedUsers').document(email).delete()
            print(f"  ✓  Removed {email}")
            removed += 1
        except Exception as e:
            print(f"  ✗  {email} — ERROR: {e}")

    print(f"\n  Done — {removed} user(s) removed.\n")

def add_from_file(db, filepath):
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)
    with open(filepath, 'r') as f:
        emails = [line.strip() for line in f if line.strip()]
    print(f"  Read {len(emails)} line(s) from {filepath}")
    add_users(db, emails)

def main():
    parser = argparse.ArgumentParser(
        description='Manage Scout Inventory allowed users in Firestore',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_users.py --list
  python manage_users.py --add leader@gmail.com
  python manage_users.py --add leader1@gmail.com leader2@gmail.com
  python manage_users.py --add-file users.txt
  python manage_users.py --remove leader@gmail.com
        """
    )
    parser.add_argument('--list',      action='store_true',  help='List all allowed users')
    parser.add_argument('--add',       nargs='+',            help='Add one or more email addresses')
    parser.add_argument('--add-file',  metavar='FILE',       help='Add emails from a text file (one per line)')
    parser.add_argument('--remove',    nargs='+',            help='Remove one or more email addresses')

    args = parser.parse_args()

    if not any([args.list, args.add, args.add_file, args.remove]):
        parser.print_help()
        sys.exit(0)

    print("\n🔑 Connecting to Firebase…")
    db = connect()
    print("✓  Connected\n")

    if args.list:
        list_users(db)

    if args.add:
        add_users(db, args.add)

    if args.add_file:
        add_from_file(db, args.add_file)

    if args.remove:
        remove_users(db, args.remove)

if __name__ == '__main__':
    main()