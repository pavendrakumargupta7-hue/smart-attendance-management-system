# Smart Attendance Management System (SAMS)

## Overview
SAMS is a Python-based web application built with Streamlit to manage students, teachers, and attendance records.

## Features
- Student registration and management
- Separate admin and teacher login
- Attendance record management and search
- Geolocation-based attendance verification
- Face verification for attendance
- Teacher management
- Password reset functionality
- Attendance dashboard

## Technologies
- Python
- Streamlit
- SQLite
- Face recognition and image processing libraries
- Geolocation

## Installation
1. Install Python.
2. Clone this repository and open its folder.
3. Install dependencies using:
   py -m pip install -r requirements.txt
4. Configure required credentials locally. Never upload secrets.
5. Run the application using:
   py -m streamlit run app.py

## Security
- Do not upload database files or real student data.
- Keep .streamlit/secrets.toml and .env files private.
- Never publish passwords, email app passwords, or API keys.
