
USE arena_sports;

DELIMITER $$

CREATE PROCEDURE sp_create_booking(
    IN p_user_id INT,
    IN p_facility_id INT,
    IN p_booking_date DATE,
    IN p_start_time TIME,
    IN p_end_time TIME,
    OUT p_booking_id INT
)
BEGIN
    DECLARE v_facility_status VARCHAR(20) DEFAULT NULL;
    DECLARE v_user_count INT DEFAULT 0;
    DECLARE v_conflicts INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_booking_id = NULL;

    -- Validate date and time
    IF p_booking_date IS NULL
       OR p_booking_date < CURRENT_DATE()
       OR p_start_time IS NULL
       OR p_end_time IS NULL
       OR p_start_time >= p_end_time THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid booking date or time';
    END IF;

    START TRANSACTION;

    -- Lock this facility to serialize bookings
    SELECT status
    INTO v_facility_status
    FROM facilities
    WHERE facility_id = p_facility_id
    FOR UPDATE;

    IF v_facility_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Facility not found';
    END IF;

    IF v_facility_status <> 'AVAILABLE' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Facility is unavailable';
    END IF;

    -- Validate student
    SELECT COUNT(*)
    INTO v_user_count
    FROM users
    WHERE user_id = p_user_id
      AND role = 'STUDENT';

    IF v_user_count = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Valid student required';
    END IF;

    -- Check overlapping confirmed bookings
    SELECT COUNT(*)
    INTO v_conflicts
    FROM bookings
    WHERE facility_id = p_facility_id
      AND booking_date = p_booking_date
      AND status = 'CONFIRMED'
      AND start_time < p_end_time
      AND end_time > p_start_time;

    IF v_conflicts > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Booking slot already occupied';
    END IF;

    -- Check overlapping tournament matches
    SELECT COUNT(*)
    INTO v_conflicts
    FROM matches
    WHERE facility_id = p_facility_id
      AND match_date = p_booking_date
      AND status IN (
          'SCHEDULED',
          'ONGOING',
          'COMPLETED'
      )
      AND start_time < p_end_time
      AND end_time > p_start_time;

    IF v_conflicts > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Facility reserved for a match';
    END IF;

    -- Create confirmed booking
    INSERT INTO bookings (
        user_id,
        facility_id,
        booking_date,
        start_time,
        end_time,
        status
    )
    VALUES (
        p_user_id,
        p_facility_id,
        p_booking_date,
        p_start_time,
        p_end_time,
        'CONFIRMED'
    );

    SET p_booking_id = LAST_INSERT_ID();

    COMMIT;
END$$

DELIMITER ;
