# Smart City Waste Management System

A role-based web application designed to manage and streamline waste collection operations through a centralized database-driven system. The project provides separate portals for Admin, Citizen, Driver, Collector, and Supervisor, enabling efficient management of waste collection, complaints, routes, schedules, staff, and collection records.

## Project Overview

The **Smart City Waste Management System** was developed to provide an organized and efficient solution for managing waste collection activities in a smart-city environment.

The system implements role-based access, allowing different users to access functionalities according to their responsibilities. Citizens can submit and track complaints, while administrative and operational staff can manage collection activities, routes, schedules, staff, and reports.

The project focuses on applying database concepts in a practical full-stack application and demonstrates how a well-designed database can support real-world operational workflows.

## Key Features

### 👤 Role-Based Access
The system provides separate portals for:

- **Admin** — Manages users, staff, areas, bins, facilities, schedules, routes, complaints, and reports.
- **Citizen** — Submits complaints and interacts with waste-management services.
- **Driver** — Accesses assigned routes and schedules.
- **Collector** — Manages collection-related activities and assigned schedules.
- **Supervisor** — Monitors staff operations and schedule updates.

### 🗑️ Waste Management
- Waste bin management
- Collection records
- Waste collection scheduling
- Route management
- Facility management
- Area management

### 📢 Complaint Management
- Citizens can submit complaints
- Complaint locations and areas can be recorded
- Admin can manage and monitor complaints

### 📅 Schedule Management
- Schedule creation and management
- Staff schedule assignments
- Schedule update requests
- Schedule update history for administrative monitoring

### 👥 Staff Management
- Staff management through the Admin portal
- Separate login roles for Driver, Collector, and Supervisor
- Role-based access to system functionality

### 📊 Reporting
- Collection-related records
- Operational information
- Administrative monitoring and reporting

## Technologies Used

### Frontend
- HTML5
- CSS3

### Backend
- Python
- Flask

### Database
- Oracle Database
- SQL
- PL/SQL

## Database Concepts Implemented

This project demonstrates several important database concepts:

- Entity Relationship Diagram (ERD)
- Relational database design
- Primary Keys
- Foreign Keys
- NOT NULL constraints
- UNIQUE constraints
- CHECK constraints
- Database relationships
- Views
- Stored Procedures
- Triggers
- Identity columns
- Data integrity
- Sample data
- Password hashing

## Project Structure

```text
Smart-City-Waste-Management-System/
│
├── README.md
├── requirements.txt
│
├── database/
│   └── final_database_script.sql
│
├── SmartCityWaste/
│   ├── app.py
│   ├── config.py
│   ├── seed_admin.py
│   ├── seed_sample_data.py
│   │
│   └── templates/
│       ├── admin_dashboard.html
│       ├── citizen_dashboard.html
│       ├── collector_dashboard.html
│       ├── driver_dashboard.html
│       ├── supervisor_dashboard.html
│       └── ...
│
└── docs/
    ├── README_ROLE_LOGIN.txt
    ├── README_SEPARATE_STAFF_LOGINS.txt
    └── README_UPDATED_PROJECT.txt
```

## Database Setup

The complete database setup is provided in:

```text
database/final_database_script.sql
```

The script includes:

- Database object creation
- Tables
- Primary and foreign keys
- Constraints
- Views
- Stored procedures
- Triggers
- Sample data
- Login users

### Steps

1. Open **Oracle SQL Developer**.
2. Open `database/final_database_script.sql`.
3. Execute the script using **F5 (Run Script)**.
4. Verify that the required database objects and sample data have been created.

## Application Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Rafia-Rubab/Smart-City-Waste-Management-System.git
```

### 2. Navigate to the Project

```bash
cd Smart-City-Waste-Management-System/SmartCityWaste
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r ..\requirements.txt
```

### 6. Configure the Oracle Database

Open:

```text
SmartCityWaste/config.py
```

Configure the Oracle database connection according to your local Oracle installation.

**Do not commit real database passwords or other sensitive credentials to GitHub.**

### 7. Run Sample Data Setup

```bash
python seed_sample_data.py
```

### 8. Start the Flask Application

```bash
python app.py
```

### 9. Open the Application

Open the following URL in your browser:

```text
http://127.0.0.1:5000
```

## Sample Login Credentials

The database script provides sample users for testing different roles.

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Citizen | `citizen` | `citizen123` |
| Driver | `driver` | `driver123` |
| Collector | `collector` | `collector123` |
| Supervisor | `supervisor` | `supervisor123` |

> These credentials are intended for local/demo use only and should not be used in a production environment.

## Learning Outcomes

This project provided practical experience in:

- Database design and implementation
- SQL and PL/SQL programming
- Backend development with Flask
- Role-based authentication
- Database-driven application development
- Applying constraints and relationships
- Using triggers, views, and stored procedures
- Connecting a Python application with Oracle Database
- Designing a real-world software solution

## Academic Purpose

This project was developed as an academic database project to demonstrate the practical implementation of database management concepts in a real-world application scenario.

It combines **Oracle Database, SQL, PL/SQL, Python Flask, HTML, and CSS** to create a centralized waste-management platform.

## Future Improvements

Potential future enhancements include:

- Interactive analytics dashboards
- Real-time waste collection tracking
- GPS-based route tracking
- Automated notifications
- Mobile application support
- Advanced waste collection analytics
- Integration with IoT-enabled waste bins

## License

This project is developed for academic and educational purposes.
