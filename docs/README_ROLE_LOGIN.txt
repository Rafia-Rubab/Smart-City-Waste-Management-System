SMART CITY WASTE MANAGEMENT - ROLE BASED LOGIN

AI Assistant module removed.

Oracle connection set in SmartCityWaste/config.py:
Host: localhost
Port: 1521
Service: xepdb1
Username: system
Password: write your Oracle SYSTEM password in DB_PASSWORD

Important:
The project cannot know your Oracle password automatically. Open SmartCityWaste/config.py and set:
DB_PASSWORD = "your_password"

Demo users after running seed_sample_data.py:
Admin:   admin / admin123
Citizen: citizen / citizen123
Worker:  worker / worker123

Run steps:
1. Open folder in VS Code.
2. cd SmartCityWaste
3. python -m venv venv
4. venv\Scripts\activate
5. pip install -r ..\requirements.txt
6. Run database/schema.sql in Oracle SQL Developer.
7. python seed_sample_data.py
8. python app.py
9. Open http://127.0.0.1:5000
