"""
CLI script to create an administrator or user account.

Usage:
    python backend/scripts/create_user.py --username admin --password MySecurePassword123!
    python backend/scripts/create_user.py --username admin   # Prompts securely for password
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

# Add backend directory and repo root to sys.path
_backend_dir = str(Path(__file__).resolve().parents[1])
_repo_root = str(Path(__file__).resolve().parents[2])
for path in [_backend_dir, _repo_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

from app.core.exceptions import AppError
from app.db.session import SessionLocal
from app.services.auth_service import AuthService


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a user or admin account.")
    parser.add_argument("--username", "-u", help="Username for the new account")
    parser.add_argument("--password", "-p", help="Password for the new account (optional, prompted securely if omitted)")
    parser.add_argument("--inactive", action="store_true", help="Set user status as inactive (default: active)")

    args = parser.parse_args()

    username = args.username or os.getenv("INITIAL_ADMIN_USERNAME")
    if not username:
        try:
            username = input("Enter username: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.", file=sys.stderr)
            sys.exit(1)

    password = args.password or os.getenv("INITIAL_ADMIN_PASSWORD")
    if not password:
        try:
            password = getpass.getpass("Enter password (min 8 chars): ").strip()
            confirm = getpass.getpass("Confirm password: ").strip()
            if password != confirm:
                print("Error: Passwords do not match.", file=sys.stderr)
                sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.", file=sys.stderr)
            sys.exit(1)

    is_active = not args.inactive

    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        user = auth_service.create_user(
            username=username,
            password=password,
            is_active=is_active,
        )
        print(f"Success: User '{user.username}' created successfully (ID: {user.id}, Active: {user.is_active}).")
    except AppError as exc:
        print(f"Error ({exc.code}): {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
