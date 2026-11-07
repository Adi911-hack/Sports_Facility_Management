USE arena_sports;

CREATE OR REPLACE VIEW vw_booking_details AS
SELECT
    b.booking_id,
    u.user_id,
    u.full_name AS student_name,
    s.sport_name,
    f.facility_id,
    f.facility_name,
    b.booking_date,
    b.start_time,
    b.end_time,
    b.status
FROM bookings b
JOIN users u
    ON b.user_id = u.user_id
JOIN facilities f
    ON b.facility_id = f.facility_id
JOIN sports s
    ON f.sport_id = s.sport_id;






SELECT * FROM vw_booking_details;




CREATE OR REPLACE VIEW vw_facility_statistics AS
SELECT
    f.facility_id,
    f.facility_name,
    s.sport_name,
    f.location,
    f.capacity,
    f.status AS facility_status,
    COUNT(b.booking_id) AS total_bookings,
    COALESCE(SUM(
        CASE
            WHEN b.status = 'CONFIRMED'
            THEN 1 ELSE 0
        END
    ), 0) AS confirmed_bookings,
    COALESCE(SUM(
        CASE
            WHEN b.status = 'COMPLETED'
            THEN 1 ELSE 0
        END
    ), 0) AS completed_bookings
FROM facilities f
JOIN sports s
    ON f.sport_id = s.sport_id
LEFT JOIN bookings b
    ON f.facility_id = b.facility_id
GROUP BY
    f.facility_id,
    f.facility_name,
    s.sport_name,
    f.location,
    f.capacity,
    f.status;




SELECT * FROM vw_facility_statistics;




SHOW FULL TABLES
FROM arena_sports
WHERE Table_type = 'VIEW';
