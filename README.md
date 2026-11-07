# ARENA — Sports Facility Management System

## Project Overview

ARENA is a database-driven sports facility management application developed as a DBMS mini-project.

The system is designed to help students book sports facilities, create teams, participate in tournaments, and view match results. Administrators will be able to manage facilities, bookings, tournaments, teams, and match schedules.

**Technology Stack**
- Database: MySQL 8.x
- Backend: Python Flask
- Database Connector: mysql-connector-python
- Frontend: HTML, CSS, JavaScript
- Development: VS Code and MySQL Workbench

## Database Design

The project contains 10 interconnected SQL tables:

1. users
2. sports
3. facilities
4. bookings
5. tournaments
6. teams
7. team_members
8. tournament_registrations
9. matches
10. match_results

The database demonstrates primary keys, foreign keys, relationships, constraints, normalization, DDL, DML, joins, subqueries, aggregate queries, views, stored procedures, and transactions.

## Work Completed

- MySQL database `arena_sports` created
- All 10 relational tables implemented
- ER diagram generated and saved
- Relational schema documented
- DDL script exported
- Sample data inserted into all tables
- Advanced SQL queries implemented
- Two database views created
- Booking creation procedure implemented and tested
- Booking cancellation logic developed
- Basic booking conflict checks tested
- Concurrency testing started
- Python virtual environment created
- Flask and other Python dependencies installed
- Complete MySQL database backup exported

**Note:** The existing SQL procedures, triggers, and concurrency safeguards require final review and testing during integration.

## Installation on a New Laptop

### 1. Clone the repository

```powershell
git clone https://github.com/Adi911-hack/Sports_Facility_Management.git
cd Sports_Facility_Management
```

### 2. Install the software

Install Python, MySQL Server, MySQL Workbench, and VS Code.

### 3. Restore the database

Open MySQL Workbench and connect to the local server.

Use **Server → Data Import → Import from Self-Contained File** to import:

`database/arena_full_backup.sql`

Check that the database, tables, views, and procedures were restored successfully.

Do not rerun all seed SQL scripts after importing the full backup.

### 4. Set up Python

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 5. Configure the database connection

Create a local `.env` file with the MySQL connection details. Never commit actual credentials.

### 6. Run the Flask application

Once `backend/app.py` has been created and configured:

```powershell
.\.venv\Scripts\python.exe backend\app.py
```

The local development server will normally be accessible at:

`http://127.0.0.1:5000/`

## Remaining Development

### Backend
- Establish Flask–MySQL connection
- Implement registration, login, and logout
- Implement dynamic court bookings and cancellations
- Implement team creation and membership management
- Implement tournament registration
- Implement match scheduling and results
- Implement admin functionality
- Finalize database constraints and concurrency handling

### Frontend
- Design the landing page
- Create login and registration pages
- Create student dashboard
- Create facility browsing and booking pages
- Create teams and tournaments pages
- Create admin dashboard
- Add responsive styling and error messages

### Testing and Documentation
- Test all database operations
- Validate booking conflicts and user permissions
- Verify tournament and match operations
- Test the complete application
- Prepare screenshots, report, and demonstration

## Handoff Status

The database foundation has been developed. The Flask application and user interface still need to be implemented and integrated with MySQL.

The next developer should begin by restoring the database and verifying the existing SQL procedures before starting backend development.

## Security

Use only fictional demonstration accounts and disposable test passwords.

Do not commit real database credentials, `.env` files, or the Python virtual environment.

---

**Project:** ARENA — Sports Facility Management System
**Course:** Database Management Systems Mini-Project