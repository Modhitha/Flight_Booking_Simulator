CREATE DATABASE flight_booking_system;
USE flight_booking_system;

CREATE TABLE flights (
    flight_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_no VARCHAR(10) NOT NULL,
    origin VARCHAR(50) NOT NULL,
    destination VARCHAR(50) NOT NULL,
    departure DATETIME NOT NULL,
    arrival DATETIME NOT NULL,
    base_fare DECIMAL(10,2) NOT NULL,
    total_seats INT NOT NULL,
    seats_available INT NOT NULL,
    airline_name VARCHAR(30)
);

INSERT INTO flights (flight_no, origin, destination, departure, arrival, base_fare, total_seats, seats_available, airline_name)
VALUES 
('AI101', 'Delhi', 'Mumbai', '2025-03-01 08:00:00', '2025-03-01 10:00:00', 7500.00, 180, 160, 'Air India'),
('6E202', 'Mumbai', 'Chennai', '2025-03-01 11:30:00', '2025-03-01 13:45:00', 6800.00, 200, 180, 'IndiGo'),
('SG303', 'Bangalore', 'Delhi', '2025-03-01 09:15:00', '2025-03-01 11:45:00', 8200.00, 220, 210, 'SpiceJet'),
('UK404', 'Chennai', 'Kolkata', '2025-03-01 14:30:00', '2025-03-01 17:00:00', 7000.00, 190, 190, 'Vistara');

CREATE TABLE passengers (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(50) NOT NULL,
    contact_no VARCHAR(15),
    email VARCHAR(50),
    city VARCHAR(40)
);

INSERT INTO passengers (full_name, contact_no, email, city)
VALUES
('Rahul Verma', '9876543210', 'rahul.verma@mail.com', 'Delhi'),
('Ananya Iyer', '9123456780', 'ananya.iyer@mail.com', 'Chennai'),
('Arjun Mehta', '9988776655', 'arjun.mehta@mail.com', 'Mumbai'),
('Sneha Das', '9090909090', 'sneha.das@mail.com', 'Kolkata');

CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT,
    passenger_id INT,
    seat_no INT,
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id),
    FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id)
);

INSERT INTO bookings (flight_id, passenger_id, seat_no)
VALUES
(1, 1, 12),
(2, 3, 22),
(3, 2, 5),
(4, 4, 17);

CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT,
    amount DECIMAL(10,2),
    payment_status VARCHAR(20),
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
);

INSERT INTO payments (booking_id, amount, payment_status)
VALUES
(1, 7500.00, 'Paid'),
(2, 6800.00, 'Paid'),
(3, 8200.00, 'Pending'),
(4, 7000.00, 'Paid');

SELECT * FROM flights;
SELECT full_name, city FROM passengers;

SELECT f.flight_no, p.full_name, b.seat_no
FROM bookings b
JOIN flights f ON b.flight_id = f.flight_id
JOIN passengers p ON b.passenger_id = p.passenger_id;

UPDATE flights
SET seats_available = seats_available - 1
WHERE flight_id = 1;

UPDATE flights
SET base_fare = base_fare * 1.10
WHERE seats_available < 50;

START TRANSACTION;
UPDATE flights
SET seats_available = seats_available - 1
WHERE flight_id = 2;

INSERT INTO bookings (flight_id, passenger_id, seat_no)
VALUES (2, 1, 18);

INSERT INTO payments (booking_id, amount, payment_status)
VALUES (LAST_INSERT_ID(), 6800.00, 'Paid');
COMMIT;

SELECT origin, COUNT(*) AS total_flights, AVG(base_fare) AS avg_fare
FROM flights
GROUP BY origin;