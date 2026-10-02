-- FINAL DATABASE SCRIPT
-- Smart City Waste Management System

-- AREA
CREATE TABLE AREA (
  area_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  area_name   VARCHAR2(100) NOT NULL,
  city_zone   VARCHAR2(50),
  postal_code VARCHAR2(20)
);

-- CITIZEN
CREATE TABLE CITIZEN (
  citizen_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  full_name  VARCHAR2(100) NOT NULL,
  email      VARCHAR2(100) UNIQUE,
  phone      VARCHAR2(20),
  address    VARCHAR2(200),
  area_id    NUMBER NOT NULL,
  FOREIGN KEY (area_id) REFERENCES AREA(area_id)
);

-- COMPLAINT
CREATE TABLE COMPLAINT (
  complaint_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  citizen_id     NUMBER NOT NULL,
  area_id        NUMBER NOT NULL,
  location       VARCHAR2(200) NOT NULL,
  complaint_type VARCHAR2(50) NOT NULL CONSTRAINT chk_complaint_type CHECK (complaint_type IN ('Missed Collection','Overflowing Bin','Illegal Dumping')),
  description    CLOB NOT NULL,
  priority       VARCHAR2(10) DEFAULT 'Medium' NOT NULL CONSTRAINT chk_complaint_priority CHECK (priority IN ('Low','Medium','High')),
  status         VARCHAR2(20) DEFAULT 'Open' NOT NULL CONSTRAINT chk_complaint_status CHECK (status IN ('Open','In Progress','Resolved')),
  complaint_date DATE DEFAULT SYSDATE NOT NULL,
  FOREIGN KEY (citizen_id) REFERENCES CITIZEN(citizen_id),
  FOREIGN KEY (area_id) REFERENCES AREA(area_id)
);

-- ROUTE
CREATE TABLE ROUTE (
  route_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  route_name    VARCHAR2(100) NOT NULL,
  areas_covered CLOB NOT NULL,
  distance_km   NUMBER(8,2) CONSTRAINT chk_route_distance CHECK (distance_km >= 0),
  est_time_hr   NUMBER(5,2) CONSTRAINT chk_route_time CHECK (est_time_hr >= 0),
  traffic_level VARCHAR2(10) CONSTRAINT chk_route_traffic CHECK (traffic_level IN ('Low','Medium','High')),
  fuel_cost     NUMBER(10,2) CONSTRAINT chk_route_fuel CHECK (fuel_cost >= 0)
);

-- WASTE_BIN
CREATE TABLE WASTE_BIN (
  bin_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  area_id    NUMBER NOT NULL,
  location   VARCHAR2(200) NOT NULL,
  fill_level NUMBER(5,2) DEFAULT 0 NOT NULL CONSTRAINT chk_bin_fill CHECK (fill_level BETWEEN 0 AND 100),
  waste_type VARCHAR2(20) NOT NULL CHECK (waste_type IN ('Organic','Plastic','Hazardous')),
  FOREIGN KEY (area_id) REFERENCES AREA(area_id)
);

-- COLLECTION_SCHEDULE
CREATE TABLE COLLECTION_SCHEDULE (
  schedule_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  route_id      NUMBER NOT NULL,
  frequency     VARCHAR2(20) NOT NULL CHECK (frequency IN ('Daily','Weekly','Bi-Weekly','Monthly')),
  waste_type    VARCHAR2(20) NOT NULL CHECK (waste_type IN ('Organic','Plastic','Hazardous','All')),
  schedule_type VARCHAR2(20) DEFAULT 'Regular' NOT NULL CHECK (schedule_type IN ('Regular','Emergency')),
  last_updated  DATE,
  FOREIGN KEY (route_id) REFERENCES ROUTE(route_id)
);

-- SCHEDULE_BIN
CREATE TABLE SCHEDULE_BIN (
  schedule_id NUMBER NOT NULL,
  bin_id      NUMBER NOT NULL,
  PRIMARY KEY (schedule_id, bin_id),
  FOREIGN KEY (schedule_id) REFERENCES COLLECTION_SCHEDULE(schedule_id),
  FOREIGN KEY (bin_id) REFERENCES WASTE_BIN(bin_id)
);

-- DAILY_SCHEDULE
CREATE TABLE DAILY_SCHEDULE (
  daily_id        NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  schedule_id     NUMBER NOT NULL,
  collection_date DATE NOT NULL,
  time_slot       VARCHAR2(50) NOT NULL,
  status          VARCHAR2(20) DEFAULT 'Pending' NOT NULL CHECK (status IN ('Pending','Completed','Cancelled')),
  FOREIGN KEY (schedule_id) REFERENCES COLLECTION_SCHEDULE(schedule_id)
);

-- STAFF
CREATE TABLE STAFF (
  staff_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  full_name  VARCHAR2(100) NOT NULL,
  contact    VARCHAR2(20) NOT NULL,
  salary     NUMBER(10,2) NOT NULL CONSTRAINT chk_staff_salary CHECK (salary > 0),
  staff_type VARCHAR2(20) NOT NULL CHECK (staff_type IN ('Driver','Collector','Supervisor'))
);

-- DRIVER
CREATE TABLE DRIVER (
  staff_id       NUMBER PRIMARY KEY,
  license_number VARCHAR2(50) NOT NULL UNIQUE,
  FOREIGN KEY (staff_id) REFERENCES STAFF(staff_id) ON DELETE CASCADE
);

-- COLLECTOR
CREATE TABLE COLLECTOR (
  staff_id        NUMBER PRIMARY KEY,
  employee_number VARCHAR2(50) NOT NULL UNIQUE,
  FOREIGN KEY (staff_id) REFERENCES STAFF(staff_id) ON DELETE CASCADE
);

-- SUPERVISOR
CREATE TABLE SUPERVISOR (
  staff_id   NUMBER PRIMARY KEY,
  department VARCHAR2(100) NOT NULL,
  FOREIGN KEY (staff_id) REFERENCES STAFF(staff_id) ON DELETE CASCADE
);

-- VEHICLE
CREATE TABLE VEHICLE (
  vehicle_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  driver_staff_id NUMBER UNIQUE,
  vehicle_type    VARCHAR2(50) NOT NULL,
  capacity        NUMBER(10,2) NOT NULL CONSTRAINT chk_vehicle_capacity CHECK (capacity > 0),
  fuel_type       VARCHAR2(20) NOT NULL CHECK (fuel_type IN ('Diesel','CNG','Electric')),
  status          VARCHAR2(20) DEFAULT 'Active' CHECK (status IN ('Active','Maintenance','Retired')),
  FOREIGN KEY (driver_staff_id) REFERENCES DRIVER(staff_id)
);

-- RESERVED_STAFF
CREATE TABLE RESERVED_STAFF (
  reserved_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  staff_id          NUMBER NOT NULL,
  availability_date DATE NOT NULL,
  occasion_type     VARCHAR2(30) NOT NULL CHECK (occasion_type IN ('Festival','Public Holiday','Natural Disaster','Emergency')),
  FOREIGN KEY (staff_id) REFERENCES STAFF(staff_id)
);

-- STAFF_ASSIGNMENT
CREATE TABLE STAFF_ASSIGNMENT (
  assignment_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  staff_id      NUMBER NOT NULL,
  schedule_id   NUMBER NOT NULL,
  role          VARCHAR2(100) NOT NULL CHECK (role IN ('Driver','Collector','Supervisor')),
  FOREIGN KEY (staff_id) REFERENCES STAFF(staff_id),
  FOREIGN KEY (schedule_id) REFERENCES COLLECTION_SCHEDULE(schedule_id)
);

-- SCHEDULE_UPDATE
CREATE TABLE SCHEDULE_UPDATE (
  update_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  daily_id      NUMBER NOT NULL,
  staff_id      NUMBER NOT NULL,
  update_reason CLOB NOT NULL,
  update_date   DATE DEFAULT SYSDATE NOT NULL,
  new_time_slot VARCHAR2(50) NOT NULL,
  remarks       CLOB,
  FOREIGN KEY (daily_id) REFERENCES DAILY_SCHEDULE(daily_id),
  FOREIGN KEY (staff_id) REFERENCES STAFF(staff_id)
);

-- RECYCLING_CENTER
CREATE TABLE RECYCLING_CENTER (
  centre_id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  location             VARCHAR2(200) NOT NULL,
  accepted_waste_types VARCHAR2(200) NOT NULL,
  capacity             NUMBER(12,2) NOT NULL CONSTRAINT chk_recycling_capacity CHECK (capacity > 0)
);

-- DUMPING_PLACE
CREATE TABLE DUMPING_PLACE (
  dump_id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  location         VARCHAR2(200) NOT NULL,
  capacity         NUMBER(12,2) NOT NULL CONSTRAINT chk_dump_capacity CHECK (capacity > 0),
  waste_categories VARCHAR2(200) NOT NULL,
  status           VARCHAR2(10) DEFAULT 'Active' NOT NULL CHECK (status IN ('Active','Full','Closed')),
  area_served      VARCHAR2(200)
);

-- COLLECTION_RECORD
CREATE TABLE COLLECTION_RECORD (
  collection_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  daily_id            NUMBER NOT NULL,
  recycling_centre_id NUMBER,
  dump_id             NUMBER,
  collection_date     DATE DEFAULT SYSDATE NOT NULL,
  waste_type          VARCHAR2(20) NOT NULL CHECK (waste_type IN ('Organic','Plastic','Hazardous')),
  quantity_kg         NUMBER(10,2) NOT NULL CONSTRAINT chk_collection_qty CHECK (quantity_kg > 0),
  destination_type    VARCHAR2(20) NOT NULL CHECK (destination_type IN ('Recycling','Dumping')),
  CONSTRAINT chk_collection_destination CHECK (
    (destination_type = 'Recycling' AND recycling_centre_id IS NOT NULL AND dump_id IS NULL) OR
    (destination_type = 'Dumping' AND dump_id IS NOT NULL AND recycling_centre_id IS NULL)
  ),
  FOREIGN KEY (daily_id) REFERENCES DAILY_SCHEDULE(daily_id),
  FOREIGN KEY (recycling_centre_id) REFERENCES RECYCLING_CENTER(centre_id),
  FOREIGN KEY (dump_id) REFERENCES DUMPING_PLACE(dump_id)
);

-- MUNICIPAL_AUTHORITY
CREATE TABLE MUNICIPAL_AUTHORITY (
  authority_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  authority_name VARCHAR2(100) NOT NULL,
  department     VARCHAR2(100) NOT NULL,
  contact        VARCHAR2(20) NOT NULL,
  email          VARCHAR2(100)
);

-- ROLE BASED LOGIN USERS
CREATE TABLE APP_USER (
  user_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username      VARCHAR2(50) UNIQUE NOT NULL,
  password_hash VARCHAR2(255) NOT NULL,
  role          VARCHAR2(20) NOT NULL CHECK (role IN ('Admin','Citizen','Driver','Collector','Supervisor')),
  citizen_id    NUMBER,
  staff_id      NUMBER,
  is_active     CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y','N')),
  created_at    DATE DEFAULT SYSDATE,
  FOREIGN KEY (citizen_id) REFERENCES CITIZEN(citizen_id),
  FOREIGN KEY (staff_id) REFERENCES STAFF(staff_id),
  CHECK (
    (role = 'Admin' AND citizen_id IS NULL AND staff_id IS NULL) OR
    (role = 'Citizen' AND citizen_id IS NOT NULL AND staff_id IS NULL) OR
    (role IN ('Driver','Collector','Supervisor') AND staff_id IS NOT NULL AND citizen_id IS NULL)
  )
);

-- -----------------------------
-- VIEWS
-- -----------------------------
CREATE OR REPLACE VIEW VW_COMPLAINT_DETAILS AS
SELECT
    c.complaint_id,
    ct.full_name AS citizen_name,
    ct.email AS citizen_email,
    a.area_name,
    c.location,
    c.complaint_type,
    DBMS_LOB.SUBSTR(c.description, 1000, 1) AS description_text,
    c.priority,
    c.status,
    c.complaint_date
FROM COMPLAINT c
JOIN CITIZEN ct ON c.citizen_id = ct.citizen_id
JOIN AREA a ON c.area_id = a.area_id;

CREATE OR REPLACE VIEW VW_STAFF_LOGIN_DETAILS AS
SELECT
    s.staff_id,
    s.full_name,
    s.contact,
    s.salary,
    s.staff_type,
    u.username,
    u.role,
    u.is_active,
    u.created_at
FROM STAFF s
LEFT JOIN APP_USER u ON s.staff_id = u.staff_id;

CREATE OR REPLACE VIEW VW_SCHEDULE_ASSIGNMENTS AS
SELECT
    sa.assignment_id,
    s.staff_id,
    s.full_name AS staff_name,
    s.staff_type,
    sa.role AS assignment_role,
    cs.schedule_id,
    cs.frequency,
    cs.waste_type,
    cs.schedule_type,
    r.route_name,
    DBMS_LOB.SUBSTR(r.areas_covered, 1000, 1) AS areas_covered_text,
    ds.daily_id,
    ds.collection_date,
    ds.time_slot,
    ds.status AS daily_status
FROM STAFF_ASSIGNMENT sa
JOIN STAFF s ON sa.staff_id = s.staff_id
JOIN COLLECTION_SCHEDULE cs ON sa.schedule_id = cs.schedule_id
JOIN ROUTE r ON cs.route_id = r.route_id
LEFT JOIN DAILY_SCHEDULE ds ON cs.schedule_id = ds.schedule_id;

CREATE OR REPLACE VIEW VW_COLLECTION_SUMMARY AS
SELECT
    cr.collection_id,
    cr.collection_date,
    cr.waste_type,
    cr.quantity_kg,
    cr.destination_type,
    ds.daily_id,
    ds.status AS daily_status,
    rc.location AS recycling_center_location,
    dp.location AS dumping_place_location
FROM COLLECTION_RECORD cr
JOIN DAILY_SCHEDULE ds ON cr.daily_id = ds.daily_id
LEFT JOIN RECYCLING_CENTER rc ON cr.recycling_centre_id = rc.centre_id
LEFT JOIN DUMPING_PLACE dp ON cr.dump_id = dp.dump_id;

-- -----------------------------
-- TRIGGERS
-- -----------------------------
CREATE OR REPLACE TRIGGER TRG_COMPLAINT_DEFAULTS
BEFORE INSERT ON COMPLAINT
FOR EACH ROW
BEGIN
    IF :NEW.complaint_date IS NULL THEN
        :NEW.complaint_date := SYSDATE;
    END IF;

    IF :NEW.status IS NULL THEN
        :NEW.status := 'Open';
    END IF;

    IF :NEW.priority IS NULL THEN
        :NEW.priority := 'Medium';
    END IF;
END;
/

CREATE OR REPLACE TRIGGER TRG_APP_USER_DEFAULTS
BEFORE INSERT ON APP_USER
FOR EACH ROW
BEGIN
    IF :NEW.created_at IS NULL THEN
        :NEW.created_at := SYSDATE;
    END IF;

    IF :NEW.is_active IS NULL THEN
        :NEW.is_active := 'Y';
    END IF;
END;
/

CREATE OR REPLACE TRIGGER TRG_COLLECTION_SCHEDULE_UPDATED
BEFORE INSERT OR UPDATE ON COLLECTION_SCHEDULE
FOR EACH ROW
BEGIN
    :NEW.last_updated := SYSDATE;
END;
/

CREATE OR REPLACE TRIGGER TRG_STAFF_ASSIGNMENT_ROLE
BEFORE INSERT OR UPDATE ON STAFF_ASSIGNMENT
FOR EACH ROW
DECLARE
    v_staff_type STAFF.staff_type%TYPE;
BEGIN
    SELECT staff_type INTO v_staff_type
    FROM STAFF
    WHERE staff_id = :NEW.staff_id;

    IF :NEW.role IS NULL THEN
        :NEW.role := v_staff_type;
    END IF;

    IF :NEW.role <> v_staff_type THEN
        RAISE_APPLICATION_ERROR(-20006, 'Staff assignment role must match staff type.');
    END IF;
END;
/

CREATE OR REPLACE TRIGGER TRG_STAFF_LOGIN_ROLE_MATCH
BEFORE INSERT OR UPDATE ON APP_USER
FOR EACH ROW
DECLARE
    v_staff_type STAFF.staff_type%TYPE;
BEGIN
    IF :NEW.role IN ('Driver', 'Collector', 'Supervisor') THEN
        IF :NEW.staff_id IS NULL THEN
            RAISE_APPLICATION_ERROR(-20007, 'Staff login must be linked with staff_id.');
        END IF;

        SELECT staff_type INTO v_staff_type
        FROM STAFF
        WHERE staff_id = :NEW.staff_id;

        IF :NEW.role <> v_staff_type THEN
            RAISE_APPLICATION_ERROR(-20008, 'Login role must match staff type.');
        END IF;
    END IF;
END;
/

-- stored procedure
CREATE OR REPLACE PROCEDURE SP_RESOLVE_COMPLAINT (
    p_complaint_id IN NUMBER
)
AS
    v_count NUMBER;
BEGIN

    SELECT COUNT(*)
    INTO v_count
    FROM COMPLAINT
    WHERE complaint_id = p_complaint_id;

    IF v_count = 0 THEN
        RAISE_APPLICATION_ERROR(-20050,
        'Complaint does not exist.');
    END IF;

    UPDATE COMPLAINT
    SET status = 'Resolved'
    WHERE complaint_id = p_complaint_id;

    COMMIT;

END;
/

-- =========================================================
-- SAMPLE DATA
-- =========================================================

-- Areas
INSERT INTO AREA(area_name, city_zone, postal_code) VALUES('Taxila City','Zone A','47080');
INSERT INTO AREA(area_name, city_zone, postal_code) VALUES('Wah Cantt','Zone B','47040');
INSERT INTO AREA(area_name, city_zone, postal_code) VALUES('HIT Area','Zone C','47070');

-- Citizen
INSERT INTO CITIZEN(full_name,email,phone,address,area_id)
VALUES('Demo Citizen','citizen@example.com','03000000000','Street 1, Taxila', (SELECT area_id FROM AREA WHERE area_name='Taxila City'));

-- Staff
INSERT INTO STAFF(full_name,contact,salary,staff_type) VALUES('Demo Collector','03111111111',45000,'Collector');
INSERT INTO STAFF(full_name,contact,salary,staff_type) VALUES('Ali Driver','03222222222',55000,'Driver');
INSERT INTO STAFF(full_name,contact,salary,staff_type) VALUES('Sara Supervisor','03333333333',65000,'Supervisor');

-- Staff subtype records
INSERT INTO COLLECTOR(staff_id, employee_number)
VALUES((SELECT staff_id FROM STAFF WHERE full_name='Demo Collector'), 'EMP-001');

INSERT INTO DRIVER(staff_id, license_number)
VALUES((SELECT staff_id FROM STAFF WHERE full_name='Ali Driver'), 'LIC-001');

INSERT INTO SUPERVISOR(staff_id, department)
VALUES((SELECT staff_id FROM STAFF WHERE full_name='Sara Supervisor'), 'Waste Operations');

-- Vehicle
INSERT INTO VEHICLE(driver_staff_id, vehicle_type, capacity, fuel_type, status)
VALUES((SELECT staff_id FROM STAFF WHERE full_name='Ali Driver'), 'Garbage Truck', 5, 'Diesel', 'Active');

-- Routes
INSERT INTO ROUTE(route_name, areas_covered, distance_km, est_time_hr, traffic_level, fuel_cost)
VALUES('Route A', 'Taxila City, Main Market, Station Road', 8.5, 1.25, 'Medium', 2500);

INSERT INTO ROUTE(route_name, areas_covered, distance_km, est_time_hr, traffic_level, fuel_cost)
VALUES('Route B', 'Wah Cantt, Mall Road', 12, 1.75, 'Low', 3200);

-- Waste bins
INSERT INTO WASTE_BIN(area_id, location, fill_level, waste_type)
VALUES((SELECT area_id FROM AREA WHERE area_name='Taxila City'), 'Main Market', 85, 'Organic');

INSERT INTO WASTE_BIN(area_id, location, fill_level, waste_type)
VALUES((SELECT area_id FROM AREA WHERE area_name='Taxila City'), 'Station Road', 60, 'Plastic');

INSERT INTO WASTE_BIN(area_id, location, fill_level, waste_type)
VALUES((SELECT area_id FROM AREA WHERE area_name='Taxila City'), 'Industrial Road', 92, 'Hazardous');

-- Collection schedule
INSERT INTO COLLECTION_SCHEDULE(route_id, frequency, waste_type, schedule_type)
VALUES((SELECT route_id FROM ROUTE WHERE route_name='Route A'), 'Daily', 'Organic', 'Regular');

INSERT INTO SCHEDULE_BIN(schedule_id, bin_id)
VALUES((SELECT schedule_id FROM COLLECTION_SCHEDULE WHERE route_id=(SELECT route_id FROM ROUTE WHERE route_name='Route A') AND ROWNUM=1),
       (SELECT bin_id FROM WASTE_BIN WHERE location='Main Market'));

INSERT INTO DAILY_SCHEDULE(schedule_id, collection_date, time_slot, status)
VALUES((SELECT schedule_id FROM COLLECTION_SCHEDULE WHERE route_id=(SELECT route_id FROM ROUTE WHERE route_name='Route A') AND ROWNUM=1), SYSDATE, '09:00 AM - 11:00 AM', 'Pending');

-- Staff assignments
INSERT INTO STAFF_ASSIGNMENT(staff_id, schedule_id, role)
VALUES((SELECT staff_id FROM STAFF WHERE full_name='Demo Collector'),
       (SELECT schedule_id FROM COLLECTION_SCHEDULE WHERE route_id=(SELECT route_id FROM ROUTE WHERE route_name='Route A') AND ROWNUM=1),
       'Collector');

INSERT INTO STAFF_ASSIGNMENT(staff_id, schedule_id, role)
VALUES((SELECT staff_id FROM STAFF WHERE full_name='Ali Driver'),
       (SELECT schedule_id FROM COLLECTION_SCHEDULE WHERE route_id=(SELECT route_id FROM ROUTE WHERE route_name='Route A') AND ROWNUM=1),
       'Driver');

INSERT INTO STAFF_ASSIGNMENT(staff_id, schedule_id, role)
VALUES((SELECT staff_id FROM STAFF WHERE full_name='Sara Supervisor'),
       (SELECT schedule_id FROM COLLECTION_SCHEDULE WHERE route_id=(SELECT route_id FROM ROUTE WHERE route_name='Route A') AND ROWNUM=1),
       'Supervisor');

-- Complaint
INSERT INTO COMPLAINT(citizen_id, area_id, location, complaint_type, description, priority, status)
VALUES((SELECT citizen_id FROM CITIZEN WHERE email='citizen@example.com'),
       (SELECT area_id FROM AREA WHERE area_name='Taxila City'),
       'Main Market near Gate 2',
       'Overflowing Bin',
       'Main market bin is full and needs urgent collection.',
       'High',
       'Open');

-- Facilities
INSERT INTO RECYCLING_CENTER(location, accepted_waste_types, capacity)
VALUES('Taxila Recycling Unit', 'Plastic, Organic', 2000);

INSERT INTO DUMPING_PLACE(location, capacity, waste_categories, status, area_served)
VALUES('Municipal Dumping Site', 5000, 'Organic, Hazardous', 'Active', 'Taxila City');

-- Collection record
INSERT INTO COLLECTION_RECORD(daily_id, recycling_centre_id, collection_date, waste_type, quantity_kg, destination_type)
VALUES((SELECT daily_id FROM DAILY_SCHEDULE WHERE ROWNUM=1),
       (SELECT centre_id FROM RECYCLING_CENTER WHERE ROWNUM=1),
       SYSDATE,
       'Organic',
       450,
       'Recycling');

-- Reserved staff
INSERT INTO RESERVED_STAFF(staff_id, availability_date, occasion_type)
VALUES((SELECT staff_id FROM STAFF WHERE full_name='Demo Collector'), SYSDATE+1, 'Emergency');

-- Schedule update
INSERT INTO SCHEDULE_UPDATE(daily_id, staff_id, update_reason, new_time_slot, remarks)
VALUES((SELECT daily_id FROM DAILY_SCHEDULE WHERE ROWNUM=1),
       (SELECT staff_id FROM STAFF WHERE full_name='Ali Driver'),
       'Traffic delay on the assigned route.',
       '11:00 AM - 01:00 PM',
       'Sample schedule update request.');


