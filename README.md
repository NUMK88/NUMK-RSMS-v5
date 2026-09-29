# NUMK-RSMS Version 5

Reserve Section Management System for an academic library.

## Version 5 additions
- Role-aware Student, Reserve Desk/Librarian and Management portals
- Role protection for circulation, scanner, reports and management functions
- Excel (.xlsx) transaction export
- PDF transaction report
- Existing CSV export retained
- LCC call-number and physical-copy control retained
- One Reserve copy per student and four-hour loan rule retained

## Setup
1. Create a PostgreSQL database and configure Django settings/environment.
2. Create a virtual environment.
3. `pip install -r requirements.txt`
4. `python manage.py makemigrations core`
5. `python manage.py migrate`
6. Create groups named `Student`, `Librarian`, and `Administrator`, then assign users to the appropriate group.
7. `python manage.py createsuperuser` for the first administrator.
8. `python manage.py runserver`

## Important
Production deployment should use HTTPS, secure environment variables, regular PostgreSQL backups, and controlled media storage for Digital Reserve files.
