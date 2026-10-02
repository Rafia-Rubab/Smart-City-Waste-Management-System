import oracledb
from werkzeug.security import generate_password_hash
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_SERVICE, DB_PORT


def get_db():
    return oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    )


def scalar(cur, sql, params=None):
    cur.execute(sql, params or {})
    row = cur.fetchone()
    return row[0] if row else None


def ensure_user(cur, username, password, role, citizen_id=None, staff_id=None):
    if scalar(cur, 'SELECT COUNT(*) FROM APP_USER WHERE username=:u', {'u': username}) == 0:
        cur.execute("""
            INSERT INTO APP_USER(username, password_hash, role, citizen_id, staff_id)
            VALUES(:u, :p, :r, :c, :s)
        """, {
            'u': username,
            'p': generate_password_hash(password),
            'r': role,
            'c': citizen_id,
            's': staff_id
        })


def main():
    db = get_db()
    cur = db.cursor()

    # Backward-compatible migration for older project databases.
    if scalar(cur, """
        SELECT COUNT(*)
        FROM user_tab_columns
        WHERE table_name='COMPLAINT'
        AND column_name='LOCATION'
    """) == 0:
        cur.execute('ALTER TABLE COMPLAINT ADD location VARCHAR2(200)')
        cur.execute("UPDATE COMPLAINT SET location='Not specified' WHERE location IS NULL")
        db.commit()

    # Areas
    areas = [
        ('Taxila City', 'Zone A', '47080'),
        ('Wah Cantt', 'Zone B', '47040'),
        ('HIT Area', 'Zone C', '47070')
    ]

    for name, zone, postal in areas:
        if scalar(cur, 'SELECT COUNT(*) FROM AREA WHERE area_name=:n', {'n': name}) == 0:
            cur.execute("""
                INSERT INTO AREA(area_name, city_zone, postal_code)
                VALUES(:n, :z, :p)
            """, {
                'n': name,
                'z': zone,
                'p': postal
            })

    area_id = scalar(cur, "SELECT area_id FROM AREA WHERE area_name='Taxila City'")

    # Citizen
    if scalar(cur, "SELECT COUNT(*) FROM CITIZEN WHERE email='citizen@example.com'") == 0:
        cur.execute("""
            INSERT INTO CITIZEN(full_name, email, phone, address, area_id)
            VALUES('Demo Citizen', 'citizen@example.com', '03000000000', 'Street 1, Taxila', :a)
        """, {'a': area_id})

    citizen_id = scalar(cur, "SELECT citizen_id FROM CITIZEN WHERE email='citizen@example.com'")

    # Staff
    staff_defs = [
        (101, 'Demo Collector', '03111111111', 45000, 'Collector'),
        (102, 'Ali Driver', '03222222222', 55000, 'Driver'),
        (103, 'Sara Supervisor', '03333333333', 65000, 'Supervisor')
    ]

    staff_ids = []

    for employee_id, name, contact, salary, stype in staff_defs:
        sid = scalar(cur, 'SELECT staff_id FROM STAFF WHERE employee_id=:emp', {'emp': employee_id})

        if not sid:
            cur.execute("""
                INSERT INTO STAFF(employee_id, full_name, contact, salary, staff_type)
                VALUES(:emp, :n, :c, :s, :t)
            """, {
                'emp': employee_id,
                'n': name,
                'c': contact,
                's': salary,
                't': stype
            })

            sid = scalar(cur, 'SELECT staff_id FROM STAFF WHERE employee_id=:emp', {'emp': employee_id})

            if stype == 'Collector':
                cur.execute("""
                    INSERT INTO COLLECTOR(staff_id)
                    VALUES(:s)
                """, {'s': sid})

            elif stype == 'Driver':
                cur.execute("""
                    INSERT INTO DRIVER(staff_id, license_number)
                    VALUES(:s, :e)
                """, {
                    's': sid,
                    'e': f'LIC-{sid:03d}'
                })

                cur.execute("""
                    INSERT INTO VEHICLE(driver_staff_id, vehicle_type, capacity, fuel_type)
                    VALUES(:s, 'Garbage Truck', 5, 'Diesel')
                """, {'s': sid})

            elif stype == 'Supervisor':
                cur.execute("""
                    INSERT INTO SUPERVISOR(staff_id, department)
                    VALUES(:s, 'Waste Operations')
                """, {'s': sid})

        staff_ids.append(sid)

    collector_id = staff_ids[0]
    driver_id = staff_ids[1]
    supervisor_id = staff_ids[2]

    # Route
    route_id = scalar(cur, "SELECT route_id FROM ROUTE WHERE route_name='Route A'")

    if not route_id:
        cur.execute("""
            INSERT INTO ROUTE(route_name, areas_covered, distance_km, est_time_hr, traffic_level, fuel_cost)
            VALUES('Route A', 'Taxila City, Main Market, Station Road', 8.5, 1.25, 'Medium', 2500)
        """)
        route_id = scalar(cur, "SELECT route_id FROM ROUTE WHERE route_name='Route A'")

    if scalar(cur, "SELECT COUNT(*) FROM ROUTE WHERE route_name='Route B'") == 0:
        cur.execute("""
            INSERT INTO ROUTE(route_name, areas_covered, distance_km, est_time_hr, traffic_level, fuel_cost)
            VALUES('Route B', 'Wah Cantt, Mall Road', 12, 1.75, 'Low', 3200)
        """)

    # Waste bins
    bins = [
        ('Main Market', 85, 'Organic'),
        ('Station Road', 60, 'Plastic'),
        ('Industrial Road', 92, 'Hazardous')
    ]

    for loc, fill, wtype in bins:
        if scalar(cur, 'SELECT COUNT(*) FROM WASTE_BIN WHERE location=:l', {'l': loc}) == 0:
            cur.execute("""
                INSERT INTO WASTE_BIN(area_id, location, fill_level, waste_type)
                VALUES(:a, :l, :f, :w)
            """, {
                'a': area_id,
                'l': loc,
                'f': fill,
                'w': wtype
            })

    bin_id = scalar(cur, "SELECT bin_id FROM WASTE_BIN WHERE location='Main Market'")

    # Schedule
    schedule_id = scalar(
        cur,
        'SELECT schedule_id FROM COLLECTION_SCHEDULE WHERE route_id=:r FETCH FIRST 1 ROWS ONLY',
        {'r': route_id}
    )

    if not schedule_id:
        cur.execute("""
            INSERT INTO COLLECTION_SCHEDULE(route_id, frequency, waste_type, schedule_type, last_updated)
            VALUES(:r, 'Daily', 'Organic', 'Regular', SYSDATE)
        """, {'r': route_id})

        schedule_id = scalar(cur, 'SELECT MAX(schedule_id) FROM COLLECTION_SCHEDULE')

        cur.execute("""
            INSERT INTO SCHEDULE_BIN(schedule_id, bin_id)
            VALUES(:s, :b)
        """, {
            's': schedule_id,
            'b': bin_id
        })

    if scalar(cur, 'SELECT COUNT(*) FROM DAILY_SCHEDULE WHERE schedule_id=:s', {'s': schedule_id}) == 0:
        cur.execute("""
            INSERT INTO DAILY_SCHEDULE(schedule_id, collection_date, time_slot, status)
            VALUES(:s, TRUNC(SYSDATE), '09:00 AM - 11:00 AM', 'Pending')
        """, {'s': schedule_id})

    daily_id = scalar(
        cur,
        'SELECT daily_id FROM DAILY_SCHEDULE WHERE schedule_id=:s FETCH FIRST 1 ROWS ONLY',
        {'s': schedule_id}
    )

    # Staff assignments
    for sid, role in [
        (collector_id, 'Collector'),
        (driver_id, 'Driver'),
        (supervisor_id, 'Supervisor')
    ]:
        if scalar(
            cur,
            'SELECT COUNT(*) FROM STAFF_ASSIGNMENT WHERE staff_id=:sid AND schedule_id=:sch',
            {'sid': sid, 'sch': schedule_id}
        ) == 0:
            cur.execute("""
                INSERT INTO STAFF_ASSIGNMENT(staff_id, schedule_id, role)
                VALUES(:sid, :sch, :role)
            """, {
                'sid': sid,
                'sch': schedule_id,
                'role': role
            })

    # Complaint
    if scalar(cur, 'SELECT COUNT(*) FROM COMPLAINT') == 0:
        cur.execute("""
            INSERT INTO COMPLAINT(citizen_id, area_id, location, complaint_type, description, priority, status, complaint_date)
            VALUES(:c, :a, 'Main Market near Gate 2', 'Overflowing Bin',
                   'Main market bin is full and needs urgent collection.',
                   'High', 'Open', SYSDATE)
        """, {
            'c': citizen_id,
            'a': area_id
        })

    # Recycling center
    if scalar(cur, 'SELECT COUNT(*) FROM RECYCLING_CENTER') == 0:
        cur.execute("""
            INSERT INTO RECYCLING_CENTER(location, accepted_waste_types, capacity)
            VALUES('Taxila Recycling Unit', 'Plastic, Organic', 2000)
        """)

    # Dumping place
    if scalar(cur, 'SELECT COUNT(*) FROM DUMPING_PLACE') == 0:
        cur.execute("""
            INSERT INTO DUMPING_PLACE(location, capacity, waste_categories, status, area_served)
            VALUES('Municipal Dumping Site', 5000, 'Organic, Hazardous', 'Active', 'Taxila City')
        """)

    rc = scalar(cur, 'SELECT centre_id FROM RECYCLING_CENTER FETCH FIRST 1 ROWS ONLY')

    # Collection record
    if scalar(cur, 'SELECT COUNT(*) FROM COLLECTION_RECORD') == 0:
        cur.execute("""
            INSERT INTO COLLECTION_RECORD(daily_id, recycling_centre_id, collection_date, waste_type, quantity_kg, destination_type)
            VALUES(:d, :r, SYSDATE, 'Organic', 450, 'Recycling')
        """, {
            'd': daily_id,
            'r': rc
        })

    # Reserved staff
    if scalar(cur, 'SELECT COUNT(*) FROM RESERVED_STAFF') == 0:
        cur.execute("""
            INSERT INTO RESERVED_STAFF(staff_id, availability_date, occasion_type)
            VALUES(:s, TRUNC(SYSDATE) + 1, 'Emergency')
        """, {'s': collector_id})

    # Schedule update
    if scalar(cur, 'SELECT COUNT(*) FROM SCHEDULE_UPDATE') == 0:
        cur.execute("""
            INSERT INTO SCHEDULE_UPDATE(daily_id, staff_id, update_reason, update_date, new_time_slot, remarks)
            VALUES(:d, :s, 'Traffic delay on the assigned route.', SYSDATE,
                   '11:00 AM - 01:00 PM', 'Sample schedule update request.')
        """, {
            'd': daily_id,
            's': driver_id
        })

    # Login users
    ensure_user(cur, 'admin', 'admin123', 'Admin')
    ensure_user(cur, 'citizen', 'citizen123', 'Citizen', citizen_id=citizen_id)
    ensure_user(cur, 'collector', 'collector123', 'Collector', staff_id=collector_id)
    ensure_user(cur, 'driver', 'driver123', 'Driver', staff_id=driver_id)
    ensure_user(cur, 'supervisor', 'supervisor123', 'Supervisor', staff_id=supervisor_id)

    db.commit()
    db.close()

    print('Sample data and role users created successfully.')
    print('Admin: admin/admin123')
    print('Citizen: citizen/citizen123')
    print('Collector: collector/collector123')
    print('Driver: driver/driver123')
    print('Supervisor: supervisor/supervisor123')


if __name__ == '__main__':
    main()