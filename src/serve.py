#!/usr/bin/python3
"""serve.py

Handy script for running development server.

usage:
    ./serve.py
    python3 serve.py

"""
import uvicorn
from config import settings

if __name__ in '__main__':
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT,
                reload=settings.DEBUG, log_level=settings.LOG_LEVEL)