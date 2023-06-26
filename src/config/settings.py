"""config/settings.py

This file holds the global server settings for the VioletHawk server.
"""
import os
import hashlib
from datetime import timezone
from drivers.storage.storage import StorageDriver
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from neo4j import GraphDatabase

# Main Application Settings
APP_NAME = "VioletHawk"
DESCRIPTION = "Open-source Reddit alternative"
VERSION = "1.0.0"
DOCS_URL = "/docs"
REDOC_URL = "/redoc"
DEBUG = True
HOST = "0.0.0.0"
PORT = 8000
TIMEZONE = timezone.utc
LOG_LEVEL = "info"

# Security
FORCE_SSL = False
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "3zitWEiWeX8YyD2pYjnF9OJAxfkM_vJ_1ot6LMYKS0MNn06u2T3w6I4hXt0NWgE7hCg")
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]

# CORS Settings
CORS_ENABLED = True
CORS_MAX_AGE = 600  # Time in seconds to cache CORS requests
ALLOW_CREDENTIALS = True
ALLOWED_ORIGINS = [
    f"http://{HOST}:{PORT}",
    f"https://{HOST}:{PORT}"
]

# What methods are allowed
ALLOW_METHODS = ["GET", "POST", "PUT"]

# Response Headers
ALLOW_HEADERS = ["*"]

# Password Settings
FORCE_COMPLEX = True
PASSWORD_SCHEMES = ["bcrypt"]
PASSWORD_SCHEMES_DEPRECATED = "auto"
SALT_SIZE = 32
PWD_CONTEXT = CryptContext(schemes=PASSWORD_SCHEMES,
                           deprecated=PASSWORD_SCHEMES_DEPRECATED)
# Password complexity
# Must have:
#   8 chars, 1 Uppercase, 1 Lowercase, 1 Number, 1 Special Char
PASSWORD_COMPLEXITY_PATTERN = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
# RFC 5322 Regex Email Pattern
EMAIL_VALIDATE_PATTERN = "(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21\\x23-\\x5b\\x5d-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21-\\x5a\\x53-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])+)\\])"

# Auth Settings
AUTH_ENDPOINT = "/auth"
TOKEN_ENDPOINT = AUTH_ENDPOINT + "/token"
JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME_MINUTES = 15
ENABLE_ACCOUNT_CREATION = True
ENABLE_BEARER_AUTH = True
OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl=TOKEN_ENDPOINT,
                                     auto_error=False)

# Database Settings
DATABASE_URL = os.environ.get("DATABASE_URL", "neo4j://localhost:7687")
DATABASE_USER = os.environ.get("DATABASE_USER", "neo4j")
DATABASE_PASS = os.environ.get("DATABASE_PASS", "password")

# Used to filter out dangerous query parameters
BASE_PROPERTIES = ["User"]

# Static File Handling
STATIC_ROUTE = "/static"
STATIC_DIR = "static"

# Templating
TEMPLATE_DIR = "templates"
TEMPLATES = Jinja2Templates(directory=TEMPLATE_DIR)

# Storage Settings
HASH_FILES = False
HASH_FUNC = hashlib.sha256
UPLOAD_DIR = "uploads"
STORAGE_DRIVER = StorageDriver(UPLOAD_DIR)

# App Middleware
MIDDLEWARE = [{
    "root": TrustedHostMiddleware,
    "allowed_hosts": ALLOWED_HOSTS
},
    {
        "root": GZipMiddleware,
        "minimum_size": 500
}
]

if CORS_ENABLED:
    MIDDLEWARE.append({
        "root": CORSMiddleware,
        "allow_origins": ALLOWED_ORIGINS,
        "allow_credentials": ALLOW_CREDENTIALS,
        "allow_methods": ALLOW_METHODS,
        "allow_headers": ALLOW_HEADERS
    })

if FORCE_SSL:
    MIDDLEWARE.append({"root": HTTPSRedirectMiddleware})

# Neo4j Database Driver for convenience
DB = GraphDatabase.driver(DATABASE_URL,
                          auth=(DATABASE_USER,
                                DATABASE_PASS))
