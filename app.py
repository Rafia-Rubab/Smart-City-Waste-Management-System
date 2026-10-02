from functools import wraps
from datetime import datetime, date
import oracledb
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from config import DB_HOST, DB_PASSWORD, DB_PORT, DB_SERVICE, DB_USER, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY


def get_db():
    return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}")


def rows_to_dicts(cursor):
    cols = [d[0].lower() for d in cursor.description]
    data = []
    for row in cursor.fetchall():
        item = {}
        for col, val in zip(cols, row):
            if hasattr(val, 'read'):
                val = val.read()
            item[col] = val
        data.append(item)
    return data


def execute(sql, params=None, fetch=False, one=False):
    db = get_db(); cur = db.cursor(); cur.execute(sql, params or {})
    result = None
    if fetch:
        result = rows_to_dicts(cur)
    elif one:
        result = cur.fetchone()
    else:
        db.commit()
    db.close(); return result

def to_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def is_today_or_future(date_text):
    try:
        selected_date = datetime.strptime(date_text, '%Y-%m-%d').date()
        return selected_date >= date.today()
    except (TypeError, ValueError):
        return False

def validate_staff_form(form, editing=False):
    errors = []

    staff_type = form.get('staff_type')
    full_name = (form.get('full_name') or '').strip()
    contact = (form.get('contact') or '').strip()
    employee_id_text = (form.get('employee_id') or '').strip()
    salary_text = (form.get('salary') or '').strip()

    if not full_name:
        errors.append('Full name is required.')

    if not contact:
        errors.append('Contact number is required.')

    if not employee_id_text:
        errors.append('Employee ID is required.')
    else:
        try:
            employee_id = int(employee_id_text)
            if employee_id <= 0:
                errors.append('Employee ID must be a positive number.')
        except ValueError:
            errors.append('Employee ID must contain numbers only.')

    if not salary_text:
        errors.append('Salary is required.')
    else:
        try:
            salary = float(salary_text)
            if salary < 1000:
                errors.append('Salary must be 1000 or greater.')
        except ValueError:
            errors.append('Salary must be a valid number.')

    if staff_type == 'Driver':
        license_number = (form.get('license_number') or '').strip()
        vehicle_type = (form.get('vehicle_type') or '').strip()
        vehicle_capacity_text = (form.get('vehicle_capacity') or '').strip()
        fuel_type = (form.get('fuel_type') or '').strip()

        if not license_number:
            errors.append('License number is required for drivers.')

        if not vehicle_type:
            errors.append('Vehicle type is required for drivers.')

        if not vehicle_capacity_text:
            errors.append('Vehicle capacity is required for drivers.')
        else:
            try:
                vehicle_capacity = float(vehicle_capacity_text)
                if vehicle_capacity < 0:
                    errors.append('Vehicle capacity cannot be negative.')
            except ValueError:
                errors.append('Vehicle capacity must be a valid number.')

        if not fuel_type:
            errors.append('Fuel type is required for drivers.')

    elif staff_type == 'Collector':
        pass

    elif staff_type == 'Supervisor':
        department = (form.get('department') or '').strip()
        if not department:
            errors.append('Department is required for supervisors.')

    else:
        errors.append('Please select a valid staff type.')

    return errors

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in allowed_roles:
                flash('You do not have permission to access this page.')
                return redirect(url_for('home'))
            return view_func(*args, **kwargs)
        return wrapper
    return decorator


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapper


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        db = get_db(); cur = db.cursor()
        cur.execute("""SELECT user_id, username, password_hash, role, citizen_id, staff_id
                       FROM APP_USER WHERE username=:username AND is_active='Y'""", {'username': username})
        user = cur.fetchone(); db.close()
        if user and check_password_hash(user[2], password):
            session.clear()
            session.update({'user_id': user[0], 'username': user[1], 'role': user[3], 'citizen_id': user[4], 'staff_id': user[5]})
            return redirect(url_for('home'))
        flash('Invalid username or password.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))


@app.route('/')
@login_required
def home():
    return redirect(url_for({'Admin':'admin_dashboard','Citizen':'citizen_dashboard','Driver':'worker_dashboard','Collector':'worker_dashboard','Supervisor':'worker_dashboard','Worker':'worker_dashboard'}.get(session.get('role'), 'login')))


@app.route('/admin/dashboard')
@role_required('Admin')
def admin_dashboard():
    db = get_db(); cur = db.cursor()
    def count(sql): cur.execute(sql); return cur.fetchone()[0]
    stats = {
        'open_complaints': count("SELECT COUNT(*) FROM COMPLAINT WHERE status='Open'"),
        'overflow_bins': count('SELECT COUNT(*) FROM WASTE_BIN WHERE fill_level > 80'),
        'pending': count("SELECT COUNT(*) FROM DAILY_SCHEDULE WHERE status='Pending'"),
        'staff_count': count('SELECT COUNT(*) FROM STAFF'),
        'areas': count('SELECT COUNT(*) FROM AREA'),
        'routes': count('SELECT COUNT(*) FROM ROUTE'),
        'recycling_centers': count('SELECT COUNT(*) FROM RECYCLING_CENTER'),
        'dumping_places': count('SELECT COUNT(*) FROM DUMPING_PLACE'),
    }
    db.close(); return render_template('admin_dashboard.html', **stats)


@app.route('/areas', methods=['GET','POST'])
@role_required('Admin')
def areas():
    if request.method == 'POST':
        execute("INSERT INTO AREA(area_name, city_zone, postal_code) VALUES(:name,:zone,:postal)",
                {'name':request.form['area_name'], 'zone':request.form.get('city_zone'), 'postal':request.form.get('postal_code')})
        flash('Area added successfully.'); return redirect(url_for('areas'))
    data = execute('SELECT area_id, area_name, city_zone, postal_code FROM AREA ORDER BY area_id', fetch=True)
    return render_template('areas.html', areas=data)


@app.route('/areas/<int:id>/delete', methods=['POST'])
@role_required('Admin')
def delete_area(id):
    try:
        execute('DELETE FROM AREA WHERE area_id=:id', {'id':id}); flash('Area deleted successfully.')
    except Exception:
        flash('Area cannot be deleted because it is used in other records.')
    return redirect(url_for('areas'))


@app.route('/complaints')
@role_required('Admin')
def complaints():
    data = execute("""SELECT c.complaint_id, ci.full_name, a.area_name, c.location, c.complaint_type,
                  TO_CHAR(c.description) AS description, c.priority, c.status, c.complaint_date
                  FROM COMPLAINT c JOIN CITIZEN ci ON c.citizen_id=ci.citizen_id
                  JOIN AREA a ON c.area_id=a.area_id ORDER BY c.complaint_date DESC""", fetch=True)
    return render_template('complaints.html', complaints=data)


@app.route('/complaints/<int:complaint_id>/status', methods=['POST'])
@role_required('Admin', 'Driver', 'Collector', 'Supervisor', 'Worker')
def update_complaint_status(complaint_id):

    status = request.form.get('status')

    if status not in ['Open', 'In Progress', 'Resolved']:
        flash('Invalid complaint status.')
        return redirect(request.referrer or url_for('home'))

    db = get_db()
    cur = db.cursor()

    try:

 
        cur.callproc(
            "SP_UPDATE_COMPLAINT_STATUS",
            [complaint_id, status]
        )

        db.commit()

        flash('Complaint status updated successfully using stored procedure.')

    except Exception as exc:

        db.rollback()

        flash(f'Error: {exc}')

    finally:

        db.close()

    return redirect(request.referrer or url_for('home'))


@app.route('/bins', methods=['GET','POST'])
@role_required('Admin')
def bins():
    if request.method == 'POST':
        execute("INSERT INTO WASTE_BIN(area_id, location, fill_level, waste_type) VALUES(:area,:loc,:fill,:type)",
                {'area':request.form['area_id'], 'loc':request.form.get('location'), 'fill':request.form.get('fill_level') or 0, 'type':request.form.get('waste_type')})
        flash('Waste bin added successfully.'); return redirect(url_for('bins'))
    data = execute("""SELECT b.bin_id, a.area_name, b.location, b.fill_level, b.waste_type
                    FROM WASTE_BIN b JOIN AREA a ON b.area_id=a.area_id ORDER BY b.fill_level DESC""", fetch=True)
    area_list = execute('SELECT area_id, area_name FROM AREA ORDER BY area_name', fetch=True)
    return render_template('bins.html', bins=data, areas=area_list)


@app.route('/bins/<int:id>/update', methods=['POST'])
@role_required('Admin')
def update_bin(id):
    execute('UPDATE WASTE_BIN SET fill_level=:fill WHERE bin_id=:id', {'fill':request.form.get('fill_level') or 0,'id':id})
    flash('Bin fill level updated successfully.'); return redirect(url_for('bins'))
@app.route('/staff', methods=['GET','POST'])
@role_required('Admin')
def staff():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()

        stype = request.form['staff_type']
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        employee_id = request.form.get('employee_id')
        salary = request.form.get('salary') or 0
        vehicle_capacity = request.form.get('vehicle_capacity') or 0

        if not username or not password:
            db.close()
            flash('Username and password are required for every staff member.')
            return redirect(url_for('staff'))

        if password != confirm_password:
            db.close()
            flash('Password and confirm password do not match.')
            return redirect(url_for('staff'))

        try:
            employee_id_int = int(employee_id)
            if employee_id_int <= 0:
                flash('Employee ID must be a positive number.')
                db.close()
                return redirect(url_for('staff'))
        except:
            flash('Employee ID must contain numbers only.')
            db.close()
            return redirect(url_for('staff'))

        try:
            salary_value = float(salary)
            if salary_value < 1000:
                flash('Salary must be 1000 or greater.')
                db.close()
                return redirect(url_for('staff'))
        except:
            flash('Salary must be a valid number.')
            db.close()
            return redirect(url_for('staff'))

        if stype == 'Driver':
            if not request.form.get('license_number'):
                flash('License number is required for drivers.')
                db.close()
                return redirect(url_for('staff'))

            if not request.form.get('vehicle_type'):
                flash('Vehicle type is required for drivers.')
                db.close()
                return redirect(url_for('staff'))

            try:
                capacity_value = float(vehicle_capacity)
                if capacity_value < 0:
                    flash('Vehicle capacity cannot be negative.')
                    db.close()
                    return redirect(url_for('staff'))
            except:
                flash('Vehicle capacity must be a valid number.')
                db.close()
                return redirect(url_for('staff'))

        if stype == 'Supervisor' and not request.form.get('department'):
            flash('Department is required for supervisors.')
            db.close()
            return redirect(url_for('staff'))

        try:
            cur.execute("""
                INSERT INTO STAFF(employee_id, full_name, contact, salary, staff_type)
                VALUES(:emp, :n, :c, :s, :t)
            """, {
                'emp': employee_id_int,
                'n': request.form['full_name'],
                'c': request.form.get('contact'),
                's': salary_value,
                't': stype
            })

            cur.execute('SELECT staff_id FROM STAFF WHERE employee_id=:emp', {'emp': employee_id_int})
            sid = cur.fetchone()[0]

            if stype == 'Driver':
                cur.execute("""
                    INSERT INTO DRIVER(staff_id, license_number)
                    VALUES(:sid, :x)
                """, {
                    'sid': sid,
                    'x': request.form.get('license_number')
                })

                cur.execute("""
                    INSERT INTO VEHICLE(driver_staff_id, vehicle_type, capacity, fuel_type)
                    VALUES(:sid, :vehicle_type, :capacity, :fuel_type)
                """, {
                    'sid': sid,
                    'vehicle_type': request.form.get('vehicle_type'),
                    'capacity': vehicle_capacity,
                    'fuel_type': request.form.get('fuel_type') or 'Diesel'
                })

            elif stype == 'Collector':
                cur.execute("""
                    INSERT INTO COLLECTOR(staff_id)
                    VALUES(:sid)
                """, {
                    'sid': sid
                })

            elif stype == 'Supervisor':
                cur.execute("""
                    INSERT INTO SUPERVISOR(staff_id, department)
                    VALUES(:sid, :x)
                """, {
                    'sid': sid,
                    'x': request.form.get('department')
                })

            cur.execute("""
                INSERT INTO APP_USER(username, password_hash, role, staff_id)
                VALUES(:u, :p, :role, :sid)
            """, {
                'u': username,
                'p': generate_password_hash(password),
                'role': stype,
                'sid': sid
            })

            db.commit()
            flash('Staff member and login account created successfully.')

        except Exception as exc:
            db.rollback()
            flash(f'Staff member could not be created. Error: {exc}')

        finally:
            db.close()

        return redirect(url_for('staff'))

    data = execute("""
        SELECT s.staff_id,
               s.employee_id,
               s.full_name,
               s.contact,
               s.salary,
               s.staff_type,
               d.license_number,
               sp.department,
               v.vehicle_id,
               v.vehicle_type,
               v.capacity AS vehicle_capacity,
               v.fuel_type,
               u.user_id,
               u.username,
               u.role AS login_role,
               u.is_active
        FROM STAFF s
        LEFT JOIN DRIVER d ON s.staff_id = d.staff_id
        LEFT JOIN COLLECTOR c ON s.staff_id = c.staff_id
        LEFT JOIN SUPERVISOR sp ON s.staff_id = sp.staff_id
        LEFT JOIN VEHICLE v ON s.staff_id = v.driver_staff_id
        LEFT JOIN APP_USER u ON s.staff_id = u.staff_id
        ORDER BY s.staff_id
    """, fetch=True)

    schedules_list = execute("""
        SELECT cs.schedule_id, r.route_name, cs.frequency, cs.waste_type, cs.schedule_type
        FROM COLLECTION_SCHEDULE cs
        JOIN ROUTE r ON cs.route_id = r.route_id
        ORDER BY cs.schedule_id DESC
    """, fetch=True)

    assignments = execute("""
        SELECT sa.assignment_id, sa.staff_id, sa.schedule_id, sa.role,
               r.route_name, cs.frequency, cs.waste_type
        FROM STAFF_ASSIGNMENT sa
        JOIN COLLECTION_SCHEDULE cs ON sa.schedule_id = cs.schedule_id
        JOIN ROUTE r ON cs.route_id = r.route_id
        ORDER BY sa.assignment_id DESC
    """, fetch=True)

    return render_template('staff.html', staff=data, schedules=schedules_list, assignments=assignments)

@app.route('/staff/<int:staff_id>/edit', methods=['POST'])
@role_required('Admin')
def edit_staff(staff_id):
    db = get_db()
    cur = db.cursor()

    new_type = request.form.get('staff_type')
    employee_id = request.form.get('employee_id')
    salary = request.form.get('salary') or 0
    vehicle_capacity = request.form.get('vehicle_capacity') or 0

    try:
        employee_id_int = int(employee_id)
        if employee_id_int <= 0:
            flash('Employee ID must be a positive number.')
            db.close()
            return redirect(url_for('staff'))
    except:
        flash('Employee ID must contain numbers only.')
        db.close()
        return redirect(url_for('staff'))

    try:
        salary_value = float(salary)
        if salary_value < 1000:
            flash('Salary must be 1000 or greater.')
            db.close()
            return redirect(url_for('staff'))
    except:
        flash('Salary must be a valid number.')
        db.close()
        return redirect(url_for('staff'))

    if new_type == 'Driver':
        if not request.form.get('license_number'):
            flash('License number is required for drivers.')
            db.close()
            return redirect(url_for('staff'))

        if not request.form.get('vehicle_type'):
            flash('Vehicle type is required for drivers.')
            db.close()
            return redirect(url_for('staff'))

        try:
            capacity_value = float(vehicle_capacity)
            if capacity_value < 0:
                flash('Vehicle capacity cannot be negative.')
                db.close()
                return redirect(url_for('staff'))
        except:
            flash('Vehicle capacity must be a valid number.')
            db.close()
            return redirect(url_for('staff'))

    if new_type == 'Supervisor' and not request.form.get('department'):
        flash('Department is required for supervisors.')
        db.close()
        return redirect(url_for('staff'))

    try:
        cur.execute('SELECT staff_type FROM STAFF WHERE staff_id=:id', {'id': staff_id})
        row = cur.fetchone()

        if not row:
            flash('Staff member not found.')
            db.close()
            return redirect(url_for('staff'))

        old_type = row[0]

        cur.execute("""
            UPDATE STAFF
            SET employee_id=:emp,
                full_name=:n,
                contact=:c,
                salary=:s,
                staff_type=:t
            WHERE staff_id=:id
        """, {
            'emp': employee_id_int,
            'n': request.form.get('full_name'),
            'c': request.form.get('contact'),
            's': salary_value,
            't': new_type,
            'id': staff_id
        })

        if old_type != new_type:
            cur.execute('DELETE FROM VEHICLE WHERE driver_staff_id=:id', {'id': staff_id})
            cur.execute('DELETE FROM DRIVER WHERE staff_id=:id', {'id': staff_id})
            cur.execute('DELETE FROM COLLECTOR WHERE staff_id=:id', {'id': staff_id})
            cur.execute('DELETE FROM SUPERVISOR WHERE staff_id=:id', {'id': staff_id})

        if new_type == 'Driver':
            cur.execute('SELECT COUNT(*) FROM DRIVER WHERE staff_id=:id', {'id': staff_id})
            if cur.fetchone()[0]:
                cur.execute("""
                    UPDATE DRIVER
                    SET license_number=:x
                    WHERE staff_id=:id
                """, {
                    'x': request.form.get('license_number'),
                    'id': staff_id
                })
            else:
                cur.execute("""
                    INSERT INTO DRIVER(staff_id, license_number)
                    VALUES(:id, :x)
                """, {
                    'id': staff_id,
                    'x': request.form.get('license_number')
                })

            cur.execute('SELECT COUNT(*) FROM VEHICLE WHERE driver_staff_id=:id', {'id': staff_id})
            vehicle_exists = cur.fetchone()[0]

            if vehicle_exists:
                cur.execute("""
                    UPDATE VEHICLE
                    SET vehicle_type=:vehicle_type,
                        capacity=:capacity,
                        fuel_type=:fuel_type
                    WHERE driver_staff_id=:id
                """, {
                    'vehicle_type': request.form.get('vehicle_type'),
                    'capacity': vehicle_capacity,
                    'fuel_type': request.form.get('fuel_type') or 'Diesel',
                    'id': staff_id
                })
            else:
                cur.execute("""
                    INSERT INTO VEHICLE(driver_staff_id, vehicle_type, capacity, fuel_type)
                    VALUES(:id, :vehicle_type, :capacity, :fuel_type)
                """, {
                    'id': staff_id,
                    'vehicle_type': request.form.get('vehicle_type'),
                    'capacity': vehicle_capacity,
                    'fuel_type': request.form.get('fuel_type') or 'Diesel'
                })

        elif new_type == 'Collector':
            cur.execute(
                'SELECT COUNT(*) FROM COLLECTOR WHERE staff_id=:id',
                {'id': staff_id}
            )

            if not cur.fetchone()[0]:
                cur.execute(
                    'INSERT INTO COLLECTOR(staff_id) VALUES(:id)',
                    {'id': staff_id}
                )

        elif new_type == 'Supervisor':
            cur.execute('SELECT COUNT(*) FROM SUPERVISOR WHERE staff_id=:id', {'id': staff_id})
            if cur.fetchone()[0]:
                cur.execute("""
                    UPDATE SUPERVISOR
                    SET department=:x
                    WHERE staff_id=:id
                """, {
                    'x': request.form.get('department'),
                    'id': staff_id
                })
            else:
                cur.execute("""
                    INSERT INTO SUPERVISOR(staff_id, department)
                    VALUES(:id, :x)
                """, {
                    'id': staff_id,
                    'x': request.form.get('department')
                })

        cur.execute("""
            UPDATE APP_USER
            SET role=:role
            WHERE staff_id=:id
        """, {
            'role': new_type,
            'id': staff_id
        })

        db.commit()
        flash('Staff information updated successfully.')

    except Exception as exc:
        db.rollback()
        flash(f'Staff information could not be updated. Error: {exc}')

    finally:
        db.close()

    return redirect(url_for('staff'))

@app.route('/staff/<int:staff_id>/username', methods=['POST'])
@role_required('Admin')
def change_staff_username(staff_id):
    username = (request.form.get('username') or '').strip()
    if not username:
        flash('Username cannot be empty.')
        return redirect(url_for('staff'))
    try:
        execute('UPDATE APP_USER SET username=:u WHERE staff_id=:id', {'u': username, 'id': staff_id})
        flash('Username changed successfully.')
    except Exception as exc:
        flash(f'Username could not be changed. It may already be used. Error: {exc}')
    return redirect(url_for('staff'))


@app.route('/staff/<int:staff_id>/password', methods=['POST'])
@role_required('Admin')
def reset_staff_password(staff_id):
    password = request.form.get('password') or ''
    confirm_password = request.form.get('confirm_password') or ''
    if not password or password != confirm_password:
        flash('Password and confirm password are required and must match.')
        return redirect(url_for('staff'))
    execute('UPDATE APP_USER SET password_hash=:p WHERE staff_id=:id',
            {'p': generate_password_hash(password), 'id': staff_id})
    flash('Password reset successfully.')
    return redirect(url_for('staff'))


@app.route('/staff/<int:staff_id>/login-status', methods=['POST'])
@role_required('Admin')
def staff_login_status(staff_id):
    status = request.form.get('is_active')
    if status in ['Y', 'N']:
        execute('UPDATE APP_USER SET is_active=:s WHERE staff_id=:id', {'s': status, 'id': staff_id})
        flash('Login status updated successfully.')
    return redirect(url_for('staff'))


@app.route('/staff/<int:staff_id>/assign-schedule', methods=['POST'])
@role_required('Admin')
def assign_staff_schedule(staff_id):
    schedule_id = request.form.get('schedule_id')
    role = request.form.get('role')
    if not schedule_id:
        flash('Please select a schedule.')
        return redirect(url_for('staff'))
    try:
        execute('INSERT INTO STAFF_ASSIGNMENT(staff_id, schedule_id, role) VALUES(:staff,:schedule,:role)',
                {'staff': staff_id, 'schedule': schedule_id, 'role': role})
        flash('Schedule assigned successfully.')
    except Exception as exc:
        flash(f'Schedule could not be assigned. Error: {exc}')
    return redirect(url_for('staff'))


@app.route('/staff/assignments/<int:assignment_id>/delete', methods=['POST'])
@role_required('Admin')
def delete_staff_assignment(assignment_id):
    execute('DELETE FROM STAFF_ASSIGNMENT WHERE assignment_id=:id', {'id': assignment_id})
    flash('Schedule assignment removed successfully.')
    return redirect(url_for('staff'))

@app.route('/staff/<int:staff_id>/delete', methods=['POST'])
@role_required('Admin')
def delete_staff(staff_id):
    db = get_db()
    cur = db.cursor()

    try:
        cur.execute('DELETE FROM SCHEDULE_UPDATE WHERE staff_id=:id', {'id': staff_id})
        cur.execute('DELETE FROM RESERVED_STAFF WHERE staff_id=:id', {'id': staff_id})
        cur.execute('DELETE FROM STAFF_ASSIGNMENT WHERE staff_id=:id', {'id': staff_id})
        cur.execute('DELETE FROM APP_USER WHERE staff_id=:id', {'id': staff_id})
        cur.execute('DELETE FROM VEHICLE WHERE driver_staff_id=:id', {'id': staff_id})
        cur.execute('DELETE FROM DRIVER WHERE staff_id=:id', {'id': staff_id})
        cur.execute('DELETE FROM COLLECTOR WHERE staff_id=:id', {'id': staff_id})
        cur.execute('DELETE FROM SUPERVISOR WHERE staff_id=:id', {'id': staff_id})
        cur.execute('DELETE FROM STAFF WHERE staff_id=:id', {'id': staff_id})

        db.commit()
        flash('Staff member and related records deleted successfully.')

    except Exception as exc:
        db.rollback()
        flash(f'Staff member could not be deleted. Error: {exc}')

    finally:
        db.close()

    return redirect(url_for('staff'))

@app.route('/routes', methods=['GET','POST'])
@role_required('Admin')
def routes():
    if request.method == 'POST':
        distance_km = request.form.get('distance_km') or 0
        est_time_hr = request.form.get('est_time_hr') or 0
        fuel_cost = request.form.get('fuel_cost') or 0

        try:
            distance_km = float(distance_km)
            est_time_hr = float(est_time_hr)
            fuel_cost = float(fuel_cost)
        except ValueError:
            flash('Distance, estimated time, and fuel cost must be valid numbers.')
            return redirect(url_for('routes'))

        if distance_km < 0:
            flash('Distance cannot be negative.')
            return redirect(url_for('routes'))

        if est_time_hr < 0:
            flash('Estimated time cannot be negative.')
            return redirect(url_for('routes'))

        if fuel_cost < 0:
            flash('Fuel cost cannot be negative.')
            return redirect(url_for('routes'))

        execute("""
            INSERT INTO ROUTE(route_name, areas_covered, distance_km, est_time_hr, traffic_level, fuel_cost)
            VALUES(:n,:a,:d,:t,:l,:f)
        """, {
            'n': request.form['route_name'],
            'a': request.form.get('areas_covered'),
            'd': distance_km,
            't': est_time_hr,
            'l': request.form.get('traffic_level'),
            'f': fuel_cost
        })

        flash('Route added successfully.')
        return redirect(url_for('routes'))

    data = execute("""
        SELECT route_id,
               route_name,
               TO_CHAR(areas_covered) AS areas_covered,
               distance_km,
               est_time_hr,
               traffic_level,
               fuel_cost
        FROM ROUTE
        ORDER BY route_id
    """, fetch=True)

    return render_template('routes.html', routes=data)

@app.route('/schedules', methods=['GET', 'POST'])
@role_required('Admin')
def schedules():
    if request.method == 'POST':
        collection_date = request.form.get('collection_date')

        if not is_today_or_future(collection_date):
            flash('Collection date cannot be in the past. Please select today or a future date.')
            return redirect(url_for('schedules'))

        db = get_db()
        cur = db.cursor()

        try:
            cur.execute("""
                INSERT INTO COLLECTION_SCHEDULE
                (route_id, frequency, waste_type, schedule_type, last_updated)
                VALUES(:r, :f, :w, :t, SYSDATE)
            """, {
                'r': request.form['route_id'],
                'f': request.form['frequency'],
                'w': request.form['waste_type'],
                't': request.form['schedule_type']
            })

            cur.execute('SELECT MAX(schedule_id) FROM COLLECTION_SCHEDULE')
            sid = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO DAILY_SCHEDULE
                (schedule_id, collection_date, time_slot, status)
                VALUES(:sid, TO_DATE(:dt, 'YYYY-MM-DD'), :slot, 'Pending')
            """, {
                'sid': sid,
                'dt': collection_date,
                'slot': request.form.get('time_slot')
            })

            if request.form.get('staff_id'):
                cur.execute("""
                    SELECT staff_type
                    FROM STAFF
                    WHERE staff_id=:sid
                """, {'sid': request.form['staff_id']})

                staff_type_row = cur.fetchone()
                assignment_role = staff_type_row[0] if staff_type_row else request.form.get('role')

                cur.execute("""
                    INSERT INTO STAFF_ASSIGNMENT(staff_id, schedule_id, role)
                    VALUES(:staff, :sid, :role)
                """, {
                    'staff': request.form['staff_id'],
                    'sid': sid,
                    'role': assignment_role
                })

            db.commit()
            flash('Schedule created successfully.')

        except Exception as exc:
            db.rollback()
            flash(f'Schedule could not be created. Error: {exc}')

        finally:
            db.close()

        return redirect(url_for('schedules'))

    data = execute("""
        SELECT ds.daily_id,
               ds.collection_date,
               ds.time_slot,
               ds.status,
               cs.schedule_id,
               cs.frequency,
               cs.waste_type,
               cs.schedule_type,
               r.route_name
        FROM DAILY_SCHEDULE ds
        JOIN COLLECTION_SCHEDULE cs ON ds.schedule_id = cs.schedule_id
        JOIN ROUTE r ON cs.route_id = r.route_id
        ORDER BY ds.collection_date DESC
    """, fetch=True)

    routes_list = execute("""
        SELECT route_id, route_name
        FROM ROUTE
        ORDER BY route_name
    """, fetch=True)

    staff_list = execute("""
        SELECT staff_id, full_name, staff_type
        FROM STAFF
        ORDER BY full_name
    """, fetch=True)

    return render_template(
        'schedules.html',
        schedules=data,
        routes=routes_list,
        staff=staff_list,
        today=date.today().isoformat()
    )

@app.route('/schedules/<int:daily_id>/status', methods=['POST'])
@role_required('Admin', 'Driver', 'Collector', 'Supervisor', 'Worker')
def update_schedule_status(daily_id):
    status=request.form.get('status')
    if status in ['Pending','Completed','Cancelled']:
        execute('UPDATE DAILY_SCHEDULE SET status=:s WHERE daily_id=:id', {'s':status,'id':daily_id})
        flash('Schedule status updated successfully.')
    return redirect(request.referrer or url_for('schedules'))

@app.route('/schedule-updates', methods=['GET', 'POST'])
@role_required('Admin', 'Driver', 'Collector')
def schedule_updates():
    staff_id = session.get('staff_id')
    user_role = session.get('role')

    if request.method == 'POST':
        daily_id = request.form.get('daily_id')
        update_reason = request.form.get('update_reason')
        new_time_slot = request.form.get('new_time_slot')
        new_date = request.form.get('new_collection_date')
        remarks = request.form.get('remarks')

        if not daily_id:
            flash('Please select a schedule.')
            return redirect(url_for('schedule_updates'))

        if not new_time_slot:
            flash('New time slot is required.')
            return redirect(url_for('schedule_updates'))

        if not update_reason:
            flash('Update reason is required.')
            return redirect(url_for('schedule_updates'))

        if new_date and not is_today_or_future(new_date):
            flash('Updated collection date cannot be in the past.')
            return redirect(url_for('schedule_updates'))

        if user_role != 'Admin':
            allowed = execute("""
                SELECT COUNT(*)
                FROM DAILY_SCHEDULE ds
                JOIN STAFF_ASSIGNMENT sa ON ds.schedule_id = sa.schedule_id
                WHERE ds.daily_id = :daily_id
                AND sa.staff_id = :staff_id
            """, {
                'daily_id': daily_id,
                'staff_id': staff_id
            }, one=True)[0]

            if not allowed:
                flash('You can only request updates for schedules assigned to you.')
                return redirect(url_for('schedule_updates'))

        db = get_db()
        cur = db.cursor()

        try:
            if user_role == 'Admin':
                if new_date:
                    cur.execute("""
                        UPDATE DAILY_SCHEDULE
                        SET collection_date = TO_DATE(:new_date, 'YYYY-MM-DD'),
                            time_slot = :new_time_slot
                        WHERE daily_id = :daily_id
                    """, {
                        'new_date': new_date,
                        'new_time_slot': new_time_slot,
                        'daily_id': daily_id
                    })
                else:
                    cur.execute("""
                        UPDATE DAILY_SCHEDULE
                        SET time_slot = :new_time_slot
                        WHERE daily_id = :daily_id
                    """, {
                        'new_time_slot': new_time_slot,
                        'daily_id': daily_id
                    })

                cur.execute("""
                    INSERT INTO SCHEDULE_UPDATE
                    (daily_id, staff_id, update_reason, update_date, new_time_slot, remarks)
                    VALUES
                    (:daily_id, NULL, :reason, SYSDATE, :new_time_slot, :remarks)
                """, {
                    'daily_id': daily_id,
                    'reason': update_reason,
                    'new_time_slot': new_time_slot,
                    'remarks': remarks
                })

                flash('Schedule updated successfully.')

            else:
                cur.execute("""
                    INSERT INTO SCHEDULE_UPDATE
                    (daily_id, staff_id, update_reason, update_date, new_time_slot, remarks)
                    VALUES
                    (:daily_id, :staff_id, :reason, SYSDATE, :new_time_slot, :remarks)
                """, {
                    'daily_id': daily_id,
                    'staff_id': staff_id,
                    'reason': update_reason,
                    'new_time_slot': new_time_slot,
                    'remarks': remarks
                })

                flash('Schedule update request submitted successfully.')

            db.commit()

        except Exception as exc:
            db.rollback()
            flash(f'Schedule update could not be saved. Error: {exc}')

        finally:
            db.close()

        return redirect(url_for('schedule_updates'))

    if user_role == 'Admin':
        assigned_daily = execute("""
            SELECT ds.daily_id,
                   ds.collection_date,
                   ds.time_slot,
                   r.route_name
            FROM DAILY_SCHEDULE ds
            JOIN COLLECTION_SCHEDULE cs ON ds.schedule_id = cs.schedule_id
            JOIN ROUTE r ON cs.route_id = r.route_id
            ORDER BY ds.collection_date DESC
        """, fetch=True)

        updates = execute("""
            SELECT su.update_id,
                   su.daily_id,
                   ds.collection_date,
                   ds.time_slot AS current_time_slot,
                   r.route_name,
                   NVL(s.full_name, 'Admin') AS updated_by,
                   NVL(s.staff_type, 'Admin') AS staff_type,
                   TO_CHAR(su.update_reason) AS update_reason,
                   su.update_date,
                   su.new_time_slot,
                   TO_CHAR(su.remarks) AS remarks
            FROM SCHEDULE_UPDATE su
            JOIN DAILY_SCHEDULE ds ON su.daily_id = ds.daily_id
            JOIN COLLECTION_SCHEDULE cs ON ds.schedule_id = cs.schedule_id
            JOIN ROUTE r ON cs.route_id = r.route_id
            LEFT JOIN STAFF s ON su.staff_id = s.staff_id
            ORDER BY su.update_date DESC, su.update_id DESC
        """, fetch=True)

    else:
        assigned_daily = execute("""
            SELECT ds.daily_id,
                   ds.collection_date,
                   ds.time_slot,
                   r.route_name
            FROM DAILY_SCHEDULE ds
            JOIN COLLECTION_SCHEDULE cs ON ds.schedule_id = cs.schedule_id
            JOIN ROUTE r ON cs.route_id = r.route_id
            JOIN STAFF_ASSIGNMENT sa ON cs.schedule_id = sa.schedule_id
            WHERE sa.staff_id = :staff_id
            ORDER BY ds.collection_date DESC
        """, {'staff_id': staff_id}, fetch=True)

        updates = execute("""
            SELECT su.update_id,
                   su.daily_id,
                   ds.collection_date,
                   ds.time_slot AS current_time_slot,
                   r.route_name,
                   NVL(s.full_name, 'Admin') AS updated_by,
                   NVL(s.staff_type, 'Admin') AS staff_type,
                   TO_CHAR(su.update_reason) AS update_reason,
                   su.update_date,
                   su.new_time_slot,
                   TO_CHAR(su.remarks) AS remarks
            FROM SCHEDULE_UPDATE su
            JOIN DAILY_SCHEDULE ds ON su.daily_id = ds.daily_id
            JOIN COLLECTION_SCHEDULE cs ON ds.schedule_id = cs.schedule_id
            JOIN ROUTE r ON cs.route_id = r.route_id
            LEFT JOIN STAFF s ON su.staff_id = s.staff_id
            JOIN STAFF_ASSIGNMENT sa ON ds.schedule_id = sa.schedule_id
            WHERE sa.staff_id = :staff_id
            ORDER BY su.update_date DESC, su.update_id DESC
        """, {'staff_id': staff_id}, fetch=True)

    return render_template(
        'schedule_updates.html',
        updates=updates,
        assigned_daily=assigned_daily,
        today=date.today().isoformat()
    )
@app.route('/reserved-staff', methods=['GET','POST'])
@role_required('Admin')
def reserved_staff():
    if request.method=='POST':
        execute("INSERT INTO RESERVED_STAFF(staff_id, availability_date, occasion_type) VALUES(:s, TO_DATE(:d,'YYYY-MM-DD'), :o)",
                {'s':request.form['staff_id'],'d':request.form['availability_date'],'o':request.form['occasion_type']})
        flash('Reserved staff record added successfully.'); return redirect(url_for('reserved_staff'))
    data=execute("""SELECT r.reserved_id, s.full_name, r.availability_date, r.occasion_type
                   FROM RESERVED_STAFF r JOIN STAFF s ON r.staff_id=s.staff_id ORDER BY r.availability_date DESC""", fetch=True)
    staff_list=execute('SELECT staff_id, full_name FROM STAFF ORDER BY full_name', fetch=True)
    return render_template('reserved_staff.html', records=data, staff=staff_list)


@app.route('/facilities', methods=['GET','POST'])
@role_required('Admin')
def facilities():
    if request.method=='POST':
        kind=request.form['kind']
        if kind=='recycling':
            execute('INSERT INTO RECYCLING_CENTER(location, accepted_waste_types, capacity) VALUES(:l,:w,:c)', {'l':request.form.get('location'),'w':request.form.get('waste_types'),'c':request.form.get('capacity') or 0})
            flash('Recycling center added successfully.')
        else:
            execute('INSERT INTO DUMPING_PLACE(location, capacity, waste_categories, status, area_served) VALUES(:l,:c,:w,:s,:a)', {'l':request.form.get('location'),'c':request.form.get('capacity') or 0,'w':request.form.get('waste_types'),'s':request.form.get('status'),'a':request.form.get('area_served')})
            flash('Dumping place added successfully.')
        return redirect(url_for('facilities'))
    recycling=execute('SELECT centre_id, location, accepted_waste_types, capacity FROM RECYCLING_CENTER ORDER BY centre_id', fetch=True)
    dumping=execute('SELECT dump_id, location, capacity, waste_categories, status, area_served FROM DUMPING_PLACE ORDER BY dump_id', fetch=True)
    return render_template('facilities.html', recycling=recycling, dumping=dumping)


@app.route('/collection-records', methods=['GET','POST'])
@role_required('Admin')
def collection_records():
    if request.method=='POST':
        execute("""INSERT INTO COLLECTION_RECORD(daily_id, recycling_centre_id, dump_id, collection_date, waste_type, quantity_kg, destination_type)
                  VALUES(:d, :rc, :dp, SYSDATE, :w, :q, :dest)""",
                {'d':request.form['daily_id'],'rc':request.form.get('recycling_centre_id') or None,'dp':request.form.get('dump_id') or None,'w':request.form.get('waste_type'),'q':request.form.get('quantity_kg') or 0,'dest':request.form.get('destination_type')})
        flash('Collection record added successfully.'); return redirect(url_for('collection_records'))
    records=execute("""SELECT cr.collection_id, cr.daily_id, cr.collection_date, cr.waste_type, cr.quantity_kg, cr.destination_type,
                     rc.location AS recycling_location, dp.location AS dumping_location
                     FROM COLLECTION_RECORD cr LEFT JOIN RECYCLING_CENTER rc ON cr.recycling_centre_id=rc.centre_id
                     LEFT JOIN DUMPING_PLACE dp ON cr.dump_id=dp.dump_id ORDER BY cr.collection_id DESC""", fetch=True)
    daily=execute('SELECT daily_id, collection_date, time_slot FROM DAILY_SCHEDULE ORDER BY daily_id DESC', fetch=True)
    recycling=execute('SELECT centre_id, location FROM RECYCLING_CENTER ORDER BY centre_id', fetch=True)
    dumping=execute('SELECT dump_id, location FROM DUMPING_PLACE ORDER BY dump_id', fetch=True)
    return render_template('collection_records.html', records=records, daily=daily, recycling=recycling, dumping=dumping)


@app.route('/reports')
@role_required('Admin')
def reports():
    report = {
        'complaints_by_status': execute('SELECT status, COUNT(*) AS total FROM COMPLAINT GROUP BY status ORDER BY status', fetch=True),
        'bins_by_type': execute('SELECT waste_type, COUNT(*) AS total, ROUND(AVG(fill_level),2) AS avg_fill FROM WASTE_BIN GROUP BY waste_type ORDER BY waste_type', fetch=True),
        'staff_by_type': execute('SELECT staff_type, COUNT(*) AS total FROM STAFF GROUP BY staff_type ORDER BY staff_type', fetch=True),
        'collections_by_destination': execute('SELECT destination_type, COUNT(*) AS total, NVL(SUM(quantity_kg),0) AS quantity FROM COLLECTION_RECORD GROUP BY destination_type ORDER BY destination_type', fetch=True),
    }
    return render_template('reports.html', **report)


@app.route('/citizen/dashboard', methods=['GET', 'POST'])
@role_required('Citizen')
def citizen_dashboard():
    citizen_id = session.get('citizen_id')

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        area_id = request.form.get('area_id')
        location = request.form.get('location', '').strip()
        complaint_type = request.form.get('complaint_type')
        description = request.form.get('description')
        priority = request.form.get('priority') or 'Medium'

        if not full_name:
            flash('Please enter your full name.')
            return redirect(url_for('citizen_dashboard'))

        if not area_id or not location:
            flash('Please select an area and enter the exact complaint location.')
            return redirect(url_for('citizen_dashboard'))

        execute("""
            UPDATE CITIZEN
            SET full_name = :full_name
            WHERE citizen_id = :citizen_id
        """, {
            'full_name': full_name,
            'citizen_id': citizen_id
        })

        execute("""
            INSERT INTO COMPLAINT
            (citizen_id, area_id, location, complaint_type, description, priority, status, complaint_date)
            VALUES
            (:citizen_id, :area_id, :location, :ctype, :description, :priority, 'Open', SYSDATE)
        """, {
            'citizen_id': citizen_id,
            'area_id': area_id,
            'location': location,
            'ctype': complaint_type,
            'description': description,
            'priority': priority
        })

        flash('Complaint submitted successfully.')
        return redirect(url_for('citizen_dashboard'))

    citizen = execute("""
        SELECT citizen_id, full_name
        FROM CITIZEN
        WHERE citizen_id = :cid
    """, {'cid': citizen_id}, fetch=True)

    citizen = citizen[0] if citizen else {}

    areas = execute("""
        SELECT area_id, area_name, city_zone
        FROM AREA
        ORDER BY area_name
    """, fetch=True)

    my_complaints = execute("""
        SELECT c.complaint_id,
               ci.full_name,
               a.area_name,
               c.location,
               c.complaint_type,
               c.priority,
               c.status,
               c.complaint_date,
               TO_CHAR(c.description) AS description
        FROM COMPLAINT c
        JOIN CITIZEN ci ON c.citizen_id = ci.citizen_id
        JOIN AREA a ON c.area_id = a.area_id
        WHERE c.citizen_id = :cid
        ORDER BY c.complaint_date DESC
    """, {'cid': citizen_id}, fetch=True)

    return render_template(
        'citizen_dashboard.html',
        complaints=my_complaints,
        areas=areas,
        citizen=citizen
    )

@app.route('/worker/dashboard')
@role_required('Driver', 'Collector', 'Supervisor', 'Worker')
def worker_dashboard():
    staff_id = session.get('staff_id')

    profile = execute("""
        SELECT s.staff_id,
               s.full_name,
               s.contact,
               s.salary,
               s.staff_type,
               d.license_number,
               sp.department,
               v.vehicle_id,
               v.vehicle_type,
               v.capacity AS vehicle_capacity,
               v.fuel_type
        FROM STAFF s
        LEFT JOIN DRIVER d ON s.staff_id = d.staff_id
        LEFT JOIN COLLECTOR c ON s.staff_id = c.staff_id
        LEFT JOIN SUPERVISOR sp ON s.staff_id = sp.staff_id
        LEFT JOIN VEHICLE v ON s.staff_id = v.driver_staff_id
        WHERE s.staff_id = :sid
    """, {'sid': staff_id}, fetch=True)

    profile = profile[0] if profile else {}

    tasks = execute("""
        SELECT ds.daily_id,
               ds.collection_date,
               ds.time_slot,
               ds.status,
               cs.schedule_id,
               cs.frequency,
               cs.waste_type,
               cs.schedule_type,
               r.route_name,
               TO_CHAR(r.areas_covered) AS areas_covered,
               r.distance_km,
               r.est_time_hr,
               r.traffic_level,
               sa.role
        FROM STAFF_ASSIGNMENT sa
        JOIN COLLECTION_SCHEDULE cs ON sa.schedule_id = cs.schedule_id
        JOIN DAILY_SCHEDULE ds ON cs.schedule_id = ds.schedule_id
        JOIN ROUTE r ON cs.route_id = r.route_id
        WHERE sa.staff_id = :sid
        ORDER BY ds.collection_date DESC
    """, {'sid': staff_id}, fetch=True)

    if profile.get('staff_type') == 'Driver':
        return render_template(
            'driver_dashboard.html',
            profile=profile,
            tasks=tasks
        )

    if profile.get('staff_type') == 'Supervisor':
        all_tasks = execute("""
            SELECT ds.daily_id,
                   ds.collection_date,
                   ds.time_slot,
                   ds.status,
                   cs.waste_type,
                   r.route_name,
                   TO_CHAR(r.areas_covered) AS areas_covered,
                   s.full_name AS assigned_staff,
                   sa.role
            FROM DAILY_SCHEDULE ds
            JOIN COLLECTION_SCHEDULE cs ON ds.schedule_id = cs.schedule_id
            JOIN ROUTE r ON cs.route_id = r.route_id
            LEFT JOIN STAFF_ASSIGNMENT sa ON cs.schedule_id = sa.schedule_id
            LEFT JOIN STAFF s ON sa.staff_id = s.staff_id
            ORDER BY ds.collection_date DESC
        """, fetch=True)

        complaints = execute("""
            SELECT c.complaint_id,
                   ci.full_name,
                   a.area_name,
                   c.location,
                   c.complaint_type,
                   TO_CHAR(c.description) AS description,
                   c.priority,
                   c.status,
                   c.complaint_date
            FROM COMPLAINT c
            JOIN CITIZEN ci ON c.citizen_id = ci.citizen_id
            JOIN AREA a ON c.area_id = a.area_id
            ORDER BY c.complaint_date DESC
        """, fetch=True)

        stats = {
            'open_complaints': execute(
                "SELECT COUNT(*) FROM COMPLAINT WHERE status='Open'",
                one=True
            )[0],
            'pending_tasks': execute(
                "SELECT COUNT(*) FROM DAILY_SCHEDULE WHERE status='Pending'",
                one=True
            )[0],
            'completed_tasks': execute(
                "SELECT COUNT(*) FROM DAILY_SCHEDULE WHERE status='Completed'",
                one=True
            )[0],
            'staff_count': execute(
                "SELECT COUNT(*) FROM STAFF",
                one=True
            )[0],
        }

        schedule_updates_list = execute("""
            SELECT su.update_id,
                   su.daily_id,
                   ds.collection_date,
                   r.route_name,
                   NVL(s.full_name, 'Admin') AS updated_by,
                   NVL(s.staff_type, 'Admin') AS staff_type,
                   TO_CHAR(su.update_reason) AS update_reason,
                   su.update_date,
                   su.new_time_slot,
                   TO_CHAR(su.remarks) AS remarks
            FROM SCHEDULE_UPDATE su
            JOIN DAILY_SCHEDULE ds ON su.daily_id = ds.daily_id
            JOIN COLLECTION_SCHEDULE cs ON ds.schedule_id = cs.schedule_id
            JOIN ROUTE r ON cs.route_id = r.route_id
            LEFT JOIN STAFF s ON su.staff_id = s.staff_id
            ORDER BY su.update_date DESC, su.update_id DESC
        """, fetch=True)

        return render_template(
            'supervisor_dashboard.html',
            profile=profile,
            tasks=all_tasks,
            complaints=complaints,
            schedule_updates=schedule_updates_list,
            **stats
        )

    recycling = execute("""
        SELECT centre_id, location
        FROM RECYCLING_CENTER
        ORDER BY location
    """, fetch=True)

    dumping = execute("""
        SELECT dump_id, location
        FROM DUMPING_PLACE
        ORDER BY location
    """, fetch=True)

    records = execute("""
        SELECT cr.collection_id,
               cr.daily_id,
               cr.collection_date,
               cr.waste_type,
               cr.quantity_kg,
               cr.destination_type,
               rc.location AS recycling_location,
               dp.location AS dumping_location
        FROM COLLECTION_RECORD cr
        LEFT JOIN RECYCLING_CENTER rc ON cr.recycling_centre_id = rc.centre_id
        LEFT JOIN DUMPING_PLACE dp ON cr.dump_id = dp.dump_id
        WHERE cr.daily_id IN (
            SELECT ds.daily_id
            FROM DAILY_SCHEDULE ds
            JOIN STAFF_ASSIGNMENT sa ON ds.schedule_id = sa.schedule_id
            WHERE sa.staff_id = :sid
        )
        ORDER BY cr.collection_id DESC
    """, {'sid': staff_id}, fetch=True)

    return render_template(
        'collector_dashboard.html',
        profile=profile,
        tasks=tasks,
        recycling=recycling,
        dumping=dumping,
        records=records
    )

@app.route('/collector/records/add', methods=['POST'])
@role_required('Driver', 'Collector', 'Supervisor', 'Worker')
def collector_add_record():
    staff_id = session.get('staff_id')
    daily_id = request.form.get('daily_id')
    allowed = execute("""
        SELECT COUNT(*) FROM DAILY_SCHEDULE ds
        JOIN STAFF_ASSIGNMENT sa ON ds.schedule_id = sa.schedule_id
        WHERE ds.daily_id = :d AND sa.staff_id = :s
    """, {'d': daily_id, 's': staff_id}, one=True)[0]
    if not allowed:
        flash('This collection task is not assigned to you.')
        return redirect(url_for('worker_dashboard'))

    destination_type = request.form.get('destination_type')
    recycling_id = request.form.get('recycling_centre_id') or None
    dump_id = request.form.get('dump_id') or None
    if destination_type == 'Recycling':
        dump_id = None
    if destination_type == 'Dumping':
        recycling_id = None

    execute("""
        INSERT INTO COLLECTION_RECORD(daily_id, recycling_centre_id, dump_id, collection_date, waste_type, quantity_kg, destination_type)
        VALUES(:daily_id, :recycling_id, :dump_id, SYSDATE, :waste_type, :quantity, :destination_type)
    """, {'daily_id': daily_id,
           'recycling_id': recycling_id,
           'dump_id': dump_id,
           'waste_type': request.form.get('waste_type'),
           'quantity': request.form.get('quantity_kg') or 0,
           'destination_type': destination_type})
    flash('Collection record submitted successfully.')
    return redirect(url_for('worker_dashboard'))


@app.route('/worker/tasks/<int:daily_id>/status', methods=['POST'])
@role_required('Driver', 'Collector', 'Supervisor', 'Worker')
def update_task_status(daily_id):
    staff_id=session.get('staff_id'); status=request.form.get('status')
    allowed=execute("""SELECT COUNT(*) FROM DAILY_SCHEDULE ds JOIN STAFF_ASSIGNMENT sa ON ds.schedule_id=sa.schedule_id
                    WHERE ds.daily_id=:d AND sa.staff_id=:s""", {'d':daily_id,'s':staff_id}, one=True)[0]
    if allowed and status in ['Pending','Completed','Cancelled']:
        execute('UPDATE DAILY_SCHEDULE SET status=:s WHERE daily_id=:d', {'s':status,'d':daily_id})
        flash('Task status updated successfully.')
    else:
        flash('This task is not assigned to you.')
    return redirect(url_for('worker_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
