#Milestone:2,3
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
import random, threading, mysql.connector

app = FastAPI(title="Flight Booking System")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="flight_booking"
    )

demand_levels = {"high": 1.5, "medium": 1.2, "low": 1.0}

class PassengerInfo(BaseModel):
    full_name: str
    contact_number: str
    email: str
    city: str

class BookingRequest(BaseModel):
    flight_id: int
    passenger: PassengerInfo
    seat_no: str

def calculate_dynamic_price(base_fare, seats_available, total_seats, departure_time):
    remaining_percentage = seats_available / total_seats
    time_diff = (departure_time - datetime.now()).total_seconds() / 3600
    demand = random.choice(list(demand_levels.values()))
    seat_factor = 1.5 if remaining_percentage < 0.3 else 1.2 if remaining_percentage < 0.5 else 1.0
    time_factor = 1.5 if time_diff < 6 else 1.2 if time_diff < 12 else 1.0
    return round(base_fare * seat_factor * time_factor * demand, 2)

@app.get("/flights")
def get_all_flights(sort_by: str = Query(None, pattern="^(price|duration)$")):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flights")
    flights = cursor.fetchall()
    for f in flights:
        f["dynamic_price"] = calculate_dynamic_price(f["base_fare"], f["seats_available"], f["total_seats"], f["departure"])
    if sort_by == "price":
        flights.sort(key=lambda x: x["dynamic_price"])
    elif sort_by == "duration":
        flights.sort(key=lambda x: (datetime.fromisoformat(str(x["arrival"])) - datetime.fromisoformat(str(x["departure"]))).seconds)
    cursor.close()
    conn.close()
    return {"flights": flights}

@app.get("/search")
def search_flights(origin: str, destination: str, date: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flights WHERE origin=%s AND destination=%s AND DATE(departure)=%s", (origin, destination, date))
    results = cursor.fetchall()
    if not results:
        raise HTTPException(status_code=404, detail="No flights found")
    for r in results:
        r["dynamic_price"] = calculate_dynamic_price(r["base_fare"], r["seats_available"], r["total_seats"], r["departure"])
    cursor.close()
    conn.close()
    return {"search_results": results}

@app.post("/book")
def book_flight(booking: BookingRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flights WHERE flight_id=%s", (booking.flight_id,))
    flight = cursor.fetchone()
    if not flight or flight["seats_available"] <= 0:
        raise HTTPException(status_code=400, detail="Flight unavailable")
    cursor.execute("INSERT INTO passengers (full_name, contact_number, email, city) VALUES (%s,%s,%s,%s)",
                   (booking.passenger.full_name, booking.passenger.contact_number, booking.passenger.email, booking.passenger.city))
    passenger_id = cursor.lastrowid
    pnr = "PNR" + str(random.randint(100000, 999999))
    price = calculate_dynamic_price(flight["base_fare"], flight["seats_available"], flight["total_seats"], flight["departure"])
    cursor.execute("INSERT INTO bookings (flight_id, passenger_id, seat_no, status, price, pnr) VALUES (%s,%s,%s,%s,%s,%s)",
                   (booking.flight_id, passenger_id, booking.seat_no, "CONFIRMED", price, pnr))
    booking_id = cursor.lastrowid
    cursor.execute("INSERT INTO payments (booking_id, amount, payment_status, payment_date) VALUES (%s,%s,%s,%s)",
                   (booking_id, price, random.choice(["SUCCESS", "FAILED"]), datetime.now()))
    cursor.execute("UPDATE flights SET seats_available=seats_available-1 WHERE flight_id=%s", (booking.flight_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"PNR": pnr, "price": price}

@app.get("/booking/{pnr}")
def get_booking(pnr: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT b.*, f.flight_no, f.origin, f.destination, f.departure, f.arrival, p.full_name FROM bookings b JOIN flights f ON b.flight_id=f.flight_id JOIN passengers p ON b.passenger_id=p.passenger_id WHERE b.pnr=%s", (pnr,))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"booking": booking}

@app.post("/cancel/{pnr}")
def cancel_booking(pnr: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bookings WHERE pnr=%s", (pnr,))
    booking = cursor.fetchone()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["status"] == "CANCELLED":
        raise HTTPException(status_code=400, detail="Already cancelled")
    cursor.execute("UPDATE bookings SET status='CANCELLED' WHERE pnr=%s", (pnr,))
    cursor.execute("UPDATE flights SET seats_available=seats_available+1 WHERE flight_id=%s", (booking["flight_id"],))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Cancelled", "PNR": pnr}

def simulate_demand():
    while True:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM flights")
        flights = cursor.fetchall()
        for f in flights:
            if random.random() < 0.3 and f["seats_available"] > 0:
                cursor.execute("UPDATE flights SET seats_available=seats_available-1 WHERE flight_id=%s", (f["flight_id"],))
        conn.commit()
        cursor.close()
        conn.close()
        threading.Event().wait(60)

threading.Thread(target=simulate_demand, daemon=True).start()
