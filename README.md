Project: Flight Booking Simulator with Dynamic Pricing
Overview:
This project simulates a real-world flight booking system that integrates dynamic pricing, seat management, and a complete booking workflow. The system provides RESTful APIs built using FastAPI, connected to a MySQL database, and an interactive frontend developed with HTML, CSS, and JavaScript.
Features Implemented

Backend (FastAPI) --
Flight Retrieval APIs:
Retrieve all flights.
Search flights by origin, destination, and optional date.
Sort search results by price or duration.
Dynamic Pricing Engine:
Adjusts fares based on:
Remaining seat percentage
Time left until departure
Simulated demand level
Base fare and pricing tiers
Seat Availability Simulation:
Background process dynamically updates seat availability to mimic real-time bookings and cancellations.
Booking Workflow:
Flight & seat selection
Passenger registration
Simulated payment (success/failure)
PNR generation
Concurrency-safe seat reservation
Booking storage and retrieval
Booking Management:
Cancel bookings
Retrieve booking history using PNR

Frontend (HTML, CSS, JavaScript)--
Developed an interactive user interface for:
Searching and displaying flights dynamically using backend APIs.
Selecting flights and entering passenger details.
Simulating payments and viewing booking confirmations.
Checking booking history and cancellation.
Designed a clean, responsive layout using CSS Flexbox/Grid and JavaScript for asynchronous API calls (fetch()).

Database Design (MySQL)--
flights – Stores flight details: flight number, airline, origin, destination, departure/arrival times, total seats, available seats, and base fare.
passengers – Contains passenger information: full name, contact number, email, and city.
bookings – Tracks bookings with fields for flight ID, passenger ID, seat number, PNR, status, and final ticket price.
payments – Records payment details linked to each booking, including amount, status, and payment date.

Technologies Used--
Backend: FastAPI (Python)
Frontend: HTML, CSS, JavaScript
Database: MySQL
Tools: Uvicorn, Pydantic, MySQL Connector, Virtual Environment (venv).
