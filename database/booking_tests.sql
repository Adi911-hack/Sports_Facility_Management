
USE arena_sports;

SET @student_id = (
    SELECT user_id
    FROM users
    WHERE email = 'rahul@arena.test'
);

SET @court_id = (
    SELECT facility_id
    FROM facilities
    WHERE facility_name = 'Badminton Court 1'
);

SELECT @student_id, @court_id;





CALL sp_create_booking(
    @student_id,
    @court_id,
    '2027-02-15',
    '10:00:00',
    '11:00:00',
    @new_booking_id
);

SELECT @new_booking_id AS booking_id;





CALL sp_create_booking(
    @student_id,
    @court_id,
    '2027-02-15',
    '10:30:00',
    '11:30:00',
    @conflicting_booking_id
);






CALL sp_create_booking(
    @student_id,
    @court_id,
    '2027-02-15',
    '11:00:00',
    '12:00:00',
    @second_booking_id
);

SELECT @second_booking_id AS booking_id;





CALL sp_create_booking(
    @student_id,
    @court_id,
    '2026-11-20',
    '10:30:00',
    '11:00:00',
    @match_conflict_id
);





SELECT
    booking_id,
    user_id,
    facility_id,
    booking_date,
    start_time,
    end_time,
    status
FROM bookings
WHERE facility_id = @court_id
  AND booking_date = '2027-02-15'
ORDER BY start_time;
