Smart City Waste Management System - Updated Version

New changes in this version:
1. Citizen complaints now require the citizen to select an area and enter the exact complaint location manually.
2. Complaint IDs, citizen IDs, area IDs, staff IDs, schedule IDs, etc. are still generated automatically by Oracle identity columns. Users do not enter IDs manually.
3. Schedule Updates module has been added.
   - Workers can submit a schedule update request for assigned schedules.
   - Admin can view all schedule update history.
   - Supervisor dashboard also shows schedule update history.
4. Sample data includes a sample schedule update request.
5. A migration script is included for old databases:
   database/migration_add_location_and_schedule_updates.sql

Fresh setup:
1. Run database/schema.sql in Oracle SQL Developer using F5.
2. Run: python seed_sample_data.py
3. Run: python app.py

If you already created the old database schema:
1. Run database/migration_add_location_and_schedule_updates.sql in SQL Developer using F5.
2. Run: python seed_sample_data.py
3. Run: python app.py

Sample logins:
Admin: admin / admin123
Citizen: citizen / citizen123
Collector: collector / collector123
Driver: driver / driver123
Supervisor: supervisor / supervisor123
