import oracledb
from werkzeug.security import generate_password_hash
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_SERVICE, DB_PORT


def get_db():
    return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}")


def first_id(cur, table, id_col):
    cur.execute(f"SELECT {id_col} FROM {table} FETCH FIRST 1 ROWS ONLY")
    row = cur.fetchone()
    return row[0] if row else None


def ensure_user(cur, username, password, role, citizen_id=None, staff_id=None):
    cur.execute("SELECT COUNT(*) FROM APP_USER WHERE username = :u", {'u': username})
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO APP_USER (username, password_hash, role, citizen_id, staff_id)
            VALUES (:username, :password_hash, :role, :citizen_id, :staff_id)
        """, {
            'username': username,
            'password_hash': generate_password_hash(password),
            'role': role,
            'citizen_id': citizen_id,
            'staff_id': staff_id
        })


def main():
    db = get_db()
    cur = db.cursor()
    citizen_id = first_id(cur, 'CITIZEN', 'citizen_id')
    staff_id = first_id(cur, 'STAFF', 'staff_id')

    ensure_user(cur, 'admin', 'admin123', 'Admin')
    if citizen_id:
        ensure_user(cur, 'citizen', 'citizen123', 'Citizen', citizen_id=citizen_id)
    else:
        print('Citizen user skipped: CITIZEN table mein koi record nahi mila.')
    if staff_id:
        ensure_user(cur, 'worker', 'worker123', 'Worker', staff_id=staff_id)
    else:
        print('Worker user skipped: STAFF table mein koi record nahi mila.')

    db.commit()
    db.close()
    print('Role users ready: admin/admin123, citizen/citizen123, worker/worker123')


if __name__ == '__main__':
    main()
