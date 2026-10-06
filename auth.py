"""
Authentication and User Management Module for HICET AI Assistant.
Handles SQLite database operations, password hashing with bcrypt,
and input validation for user registration and login.
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    import bcrypt

    HAS_BCRYPT = True
except ImportError:
    import hashlib
    import secrets

    HAS_BCRYPT = False


# Database configuration
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "users.db"

# Validation patterns
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


def get_db_connection() -> sqlite3.Connection:
    """Create and return a database connection with row factory configured."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the SQLite database and create the users table if not exists."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()


def hash_password(password: str) -> str:
    """Securely hash a plain text password using bcrypt (or salted PBKDF2 as fallback)."""
    if HAS_BCRYPT:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    else:
        # Fallback in case bcrypt is unavailable
        salt = secrets.token_hex(16)
        iterations = 100_000
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return f"pbkdf2${salt}${iterations}${key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    if not password or not password_hash:
        return False

    try:
        if password_hash.startswith("pbkdf2$"):
            _, salt, iterations_str, expected_hex = password_hash.split("$")
            iterations = int(iterations_str)
            computed_key = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            )
            return secrets.compare_digest(computed_key.hex(), expected_hex)
        else:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
    except Exception:
        return False


def register_user(
    full_name: str,
    username: str,
    email: str,
    password: str,
    confirm_password: str,
) -> Tuple[bool, str]:
    """
    Validate inputs and register a new user.

    Returns:
        (success: bool, message: str)
    """
    full_name = (full_name or "").strip()
    username = (username or "").strip()
    email = (email or "").strip().lower()
    password = password or ""
    confirm_password = confirm_password or ""

    # Required fields check
    if not full_name:
        return False, "Please enter your full name."

    if not email:
        return False, "Please enter your email address."

    if not username:
        return False, "Please choose a username."

    if not password:
        return False, "Please enter a password."

    # Email format validation
    if not EMAIL_REGEX.match(email):
        return False, "Please enter a valid email address."

    # Username format validation
    if not USERNAME_REGEX.match(username):
        return (
            False,
            "Username must be 3-30 characters and contain only letters, numbers, or underscores.",
        )

    # Password length validation
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    # Password match check
    if password != confirm_password:
        return False, "Passwords do not match."

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check for existing username (case-insensitive)
            cursor.execute(
                "SELECT id FROM users WHERE LOWER(username) = LOWER(?)",
                (username,),
            )
            if cursor.fetchone():
                return False, "Username already exists."

            # Check for existing email (case-insensitive)
            cursor.execute(
                "SELECT id FROM users WHERE LOWER(email) = LOWER(?)",
                (email,),
            )
            if cursor.fetchone():
                return False, "Email already registered."

            # Hash password and insert
            pwd_hash = hash_password(password)
            cursor.execute(
                """
                INSERT INTO users (full_name, username, email, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (full_name, username, email, pwd_hash),
            )
            conn.commit()

        return True, "Registration successful. Please login."

    except Exception:
        # Graceful handling without exposing database internals
        return False, "Unable to complete registration. Please try again."


def authenticate_user(
    username_or_email: str,
    password: str,
) -> Tuple[Optional[Dict], str]:
    """
    Authenticate a user by username or email and password.

    Returns:
        (user_dict: Optional[Dict], message: str)
    """
    identifier = (username_or_email or "").strip().lower()
    password = password or ""

    if not identifier or not password:
        return None, "Invalid username or password."

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, full_name, username, email, password_hash
                FROM users
                WHERE LOWER(username) = ? OR LOWER(email) = ?
                """,
                (identifier, identifier),
            )
            user_row = cursor.fetchone()

            if not user_row:
                return None, "Invalid username or password."

            if not verify_password(password, user_row["password_hash"]):
                return None, "Invalid username or password."

            user_data = {
                "id": user_row["id"],
                "full_name": user_row["full_name"],
                "username": user_row["username"],
                "email": user_row["email"],
            }
            return user_data, "Login successful."

    except Exception:
        return None, "Authentication error. Please try again."
