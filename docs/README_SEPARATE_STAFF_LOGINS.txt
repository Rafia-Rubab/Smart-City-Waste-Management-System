Separate Staff Login Update

This version uses separate login roles for:
- Admin
- Citizen
- Driver
- Collector
- Supervisor

Driver, Collector, and Supervisor are not stored as Worker role anymore.
They are stored directly in APP_USER.role.

Fresh database setup:
1. Run database/schema.sql in Oracle SQL Developer with F5.
2. Run python seed_sample_data.py.
3. Run python app.py.

Existing old database update:
1. Run database/migration_separate_staff_logins.sql in Oracle SQL Developer with F5.
2. Run python seed_sample_data.py again.
3. Run python app.py.

Sample logins:
admin / admin123
citizen / citizen123
driver / driver123
collector / collector123
supervisor / supervisor123

When Admin adds a staff member and enters login username/password:
- Driver staff creates Driver login role.
- Collector staff creates Collector login role.
- Supervisor staff creates Supervisor login role.
