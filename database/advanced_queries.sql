
SELECT
    b.booking_id,
    u.full_name AS student,
    s.sport_name,
    f.facility_name,
    b.booking_date,
    b.start_time,
    b.end_time,
    b.status
FROM bookings b
JOIN users u ON b.user_id = u.user_id
JOIN facilities f ON b.facility_id = f.facility_id
JOIN sports s ON f.sport_id = s.sport_id
ORDER BY b.booking_date, b.start_time;






SELECT
    f.facility_name,
    s.sport_name,
    COUNT(b.booking_id) AS total_bookings
FROM facilities f
JOIN sports s ON f.sport_id = s.sport_id
LEFT JOIN bookings b
    ON f.facility_id = b.facility_id
    AND b.status IN ('CONFIRMED', 'COMPLETED')
GROUP BY
    f.facility_id,
    f.facility_name,
    s.sport_name
ORDER BY total_bookings DESC, f.facility_name;





SELECT
    u.user_id,
    u.full_name,
    COUNT(b.booking_id) AS booking_count
FROM users u
JOIN bookings b ON u.user_id = b.user_id
WHERE b.status <> 'CANCELLED'
GROUP BY u.user_id, u.full_name
HAVING COUNT(b.booking_id) >= 2
ORDER BY booking_count DESC;




SELECT
    tr.tournament_name,
    s.sport_name,
    t.team_name,
    u.full_name AS captain,
    r.status AS registration_status
FROM tournament_registrations r
JOIN tournaments tr
    ON r.tournament_id = tr.tournament_id
JOIN sports s
    ON tr.sport_id = s.sport_id
JOIN teams t
    ON r.team_id = t.team_id
JOIN users u
    ON t.captain_id = u.user_id
ORDER BY tr.tournament_name, t.team_name;





SELECT
    f.facility_id,
    f.facility_name,
    f.location
FROM facilities f
WHERE f.status = 'AVAILABLE'
AND NOT EXISTS (
    SELECT 1
    FROM bookings b
    WHERE b.facility_id = f.facility_id
      AND b.status = 'CONFIRMED'
);






SELECT
    tr.tournament_name,
    t1.team_name AS team_1,
    mr.team1_score,
    t2.team_name AS team_2,
    mr.team2_score,
    w.team_name AS winner
FROM match_results mr
JOIN matches m ON mr.match_id = m.match_id
JOIN tournaments tr ON m.tournament_id = tr.tournament_id
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
LEFT JOIN teams w ON mr.winner_team_id = w.team_id;
