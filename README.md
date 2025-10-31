Project : Flight Booking Simulator with Dynamic Pricing

Steps Completed (Up to Now):
Built REST APIs using FastAPI for:
Retrieving all flights
Searching flights by origin, destination, and optional date
Implemented input validation and sorting by price or duration.
Designed a dynamic pricing engine considering:
Remaining seat percentage
Time until departure
Simulated demand level
Base fare & pricing tiers
Integrated dynamic pricing into flight search API.
Implemented background process to simulate seat availability changes over time.
Developed booking workflow:
Flight & seat selection
Passenger info registration
Simulated payment (success/fail)
PNR generation and booking storage
Concurrency-safe seat reservation
Implemented booking cancellation and history retrieval by PNR.

Technologies Used:
Backend: FastAPI (Python)
Database: MySQL
Frontend: HTML, CSS, JavaScript

Database Schema:
flights – Flight details including departure, arrival, total seats, available seats, base fare, and airline.
passengers – Stores passenger information such as full name, contact number, email, and city.
bookings – Booking records including flight ID, passenger ID, seat number, PNR, status, and price.
payments – Payment records linked to bookings, including amount, payment status, and payment date.


Fully integrate the frontend (HTML, CSS, JS) with backend APIs for interactive booking.

