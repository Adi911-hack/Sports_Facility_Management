
USE arena_sports;

WITH FacilityBookingStats AS (
    SELECT
        f.facility_id,
        f.facility_name,
        s.sport_name,
        COUNT(b.booking_id) AS total_bookings,
        SUM(
            CASE
                WHEN b.status = 'CONFIRMED'
                THEN 1
                ELSE 0
            END
        ) AS confirmed_bookings
    FROM facilities AS f
    JOIN sports AS s
        ON f.sport_id = s.sport_id
    LEFT JOIN bookings AS b
        ON f.facility_id = b.facility_id
    GROUP BY
        f.facility_id,
        f.facility_name,
        s.sport_name
)
SELECT
    facility_id,
    facility_name,
    sport_name,
    total_bookings,
    confirmed_bookings
FROM FacilityBookingStats
ORDER BY total_bookings DESC, facility_id;




USE arena_sports;

-- NESTED QUERY:
-- Students who have made at least one booking

SELECT
    u.user_id,
    u.full_name,
    u.email
FROM users AS u
WHERE u.role = 'STUDENT'
  AND u.user_id IN (
      SELECT DISTINCT b.user_id
      FROM bookings AS b
  )
ORDER BY u.user_id;




USE arena_sports;

-- CORRELATED QUERY:
-- Facilities with more bookings than
-- the average facility booking count

SELECT
    f.facility_id,
    f.facility_name,
    (
        SELECT COUNT(*)
        FROM bookings AS b
        WHERE b.facility_id = f.facility_id
    ) AS total_bookings
FROM facilities AS f
WHERE (
    SELECT COUNT(*)
    FROM bookings AS b
    WHERE b.facility_id = f.facility_id
) > (
    SELECT AVG(facility_booking_count)
    FROM (
        SELECT
            f2.facility_id,
            COUNT(b2.booking_id) AS facility_booking_count
        FROM facilities AS f2
        LEFT JOIN bookings AS b2
            ON b2.facility_id = f2.facility_id
        GROUP BY f2.facility_id
    ) AS facility_counts
)
ORDER BY total_bookings DESC;
