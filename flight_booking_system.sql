#Used mysql Workbench
CREATE DATABASE IF NOT EXISTS flight_booking;
USE flight_booking;

CREATE TABLE flights (
    flight_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_no VARCHAR(20),
    origin VARCHAR(50),
    destination VARCHAR(50),
    departure DATETIME,
    arrival DATETIME,
    base_fare DECIMAL(10,2),
    seats_available INT,
    total_seats INT
);

CREATE TABLE passengers (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    contact_number VARCHAR(15),
    email VARCHAR(100),
    city VARCHAR(50)
);

CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT,
    passenger_id INT,
    seat_no VARCHAR(10),
    status VARCHAR(20),
    price DECIMAL(10,2),
    pnr VARCHAR(20),
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id),
    FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id)
);

CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT,
    amount DECIMAL(10,2),
    payment_status VARCHAR(20),
    payment_date DATETIME,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
);

INSERT INTO flights (flight_no, origin, destination, departure, arrival, base_fare, seats_available, total_seats)
VALUES
('AI101', 'Mumbai', 'Delhi', '2025-11-02 08:00:00', '2025-11-02 10:00:00', 5500, 30, 60),
('6E202', 'Chennai', 'Hyderabad', '2025-11-02 09:00:00', '2025-11-02 10:15:00', 4000, 40, 60),
('UK303', 'Delhi', 'Bangalore', '2025-11-02 14:00:00', '2025-11-02 17:30:00', 7000, 25, 60);11-02 14:00:00', '2025-11-02 17:30:00', 7000, 25, 60);
