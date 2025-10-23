# Milestone 2: Flight Search & Dynamic Pricing
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import random
import asyncio
import mysql.connector
import string

app = FastAPI()

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="flight_booking_system"
    )

class FlightResponse(BaseModel):
    flight_id: int
    flight_no: str
    origin: str
    destination: str
    departure: str
    arrival: str
    base_fare: float
    dynamic_price: float
    total_seats: int
    seats_available: int
    airline_name: str

def calculate_dynamic_price(base_fare: float, total_seats: int, seats_available: int, departure_time: datetime) -> float:
    seat_percentage = (total_seats - seats_available) / total_seats
    seat_factor = 0.25 * seat_percentage
    hours_until_departure = (departure_time - datetime.now()).total_seconds() / 3600
    if hours_until_departure <= 0:
        hours_until_departure = 1
    time_factor = 0.4 if hours_until_departure <= 24 else min(0.2, 0.2 * (24 / hours_until_departure))
    demand_level = random.uniform(0.0, 1.0)
    demand_factor = 0.3 * demand_level
    tier_factor = 0.15 if base_fare >= 8000 else 0.08 if base_fare >= 5000 else 0.03
    volatility = random.uniform(-0.02, 0.05)
    multiplier = 1 + seat_factor + time_factor + demand_factor + tier_factor + volatility
    return round(base_fare * multiplier, 2)

@app.get("/flights", response_model=List[FlightResponse])
def get_all_flights(sort_by: Optional[str] = Query(None, regex="^(price|duration)$")):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flights")
    flights = cursor.fetchall()
    result = []
    for f in flights:
        dynamic_price = calculate_dynamic_price(float(f['base_fare']), int(f['total_seats']), int(f['seats_available']), f['departure'])
        result.append({
            "flight_id": f["flight_id"],
            "flight_no": f["flight_no"],
            "origin": f["origin"],
            "destination": f["destination"],
            "departure": f["departure"].strftime("%Y-%m-%d %H:%M:%S"),
            "arrival": f["arrival"].strftime("%Y-%m-%d %H:%M:%S"),
            "base_fare": float(f["base_fare"]),
            "dynamic_price": dynamic_price,
            "total_seats": f["total_seats"],
            "seats_available": f["seats_available"],
            "airline_name": f["airline_name"]
        })
    if sort_by == "price":
        result.sort(key=lambda x: x["dynamic_price"])
    elif sort_by == "duration":
        result.sort(key=lambda x: (datetime.strptime(x["arrival"], "%Y-%m-%d %H:%M:%S") - datetime.strptime(x["departure"], "%Y-%m-%d %H:%M:%S")).total_seconds())
    cursor.close()
    conn.close()
    return result

@app.get("/search", response_model=List[FlightResponse])
def search_flights(origin: str, destination: str, date: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM flights WHERE origin=%s AND destination=%s"
    params = [origin, destination]
    if date:
        query += " AND DATE(departure)= %s"
        params.append(date)
    cursor.execute(query, tuple(params))
    flights = cursor.fetchall()
    result = []
    for f in flights:
        dynamic_price = calculate_dynamic_price(float(f['base_fare']), int(f['total_seats']), int(f['seats_available']), f['departure'])
        result.append({
            "flight_id": f["flight_id"],
            "flight_no": f["flight_no"],
            "origin": f["origin"],
            "destination": f["destination"],
            "departure": f["departure"].strftime("%Y-%m-%d %H:%M:%S"),
            "arrival": f["arrival"].strftime("%Y-%m-%d %H:%M:%S"),
            "base_fare": float(f["base_fare"]),
            "dynamic_price": dynamic_price,
            "total_seats": f["total_seats"],
            "seats_available": f["seats_available"],
            "airline_name": f["airline_name"]
        })
    cursor.close()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="No flights found")
    return result

@app.get("/external/schedule")
def simulate_external_api():
    sample_flights = [
        {"flight_no": "QF789", "origin": "Delhi", "destination": "Singapore", "departure": "2025-03-05 09:00:00"},
        {"flight_no": "EK555", "origin": "Mumbai", "destination": "Dubai", "departure": "2025-03-06 07:30:00"}
    ]
    return {"external_flights": sample_flights}

async def simulate_market_step():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT flight_id, seats_available, total_seats FROM flights")
    flights = cursor.fetchall()
    for f in flights:
        change = random.randint(-3, 3)
        new_seats = max(0, min(f['total_seats'], f['seats_available'] + change))
        cursor.execute("UPDATE flights SET seats_available=%s WHERE flight_id=%s", (new_seats, f['flight_id']))
    conn.commit()
    cursor.close()
    conn.close()

async def scheduler_loop(interval: int):
    while True:
        await simulate_market_step()
        await asyncio.sleep(interval)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scheduler_loop(300))

@app.get("/")
def root():
    return {"message": "Flight Booking Simulator Backend Running"}

# Milestone 3: Booking Workflow & Transaction Management
class PassengerInfo(BaseModel):
    full_name: str
    contact_no: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None

class BookingRequest(BaseModel):
    flight_id: int
    passenger: PassengerInfo
    seat_no: int

def generate_pnr(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.post("/bookings")
def create_booking(request: BookingRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM flights WHERE flight_id=%s FOR UPDATE", (request.flight_id,))
        flight = cursor.fetchone()
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
        if flight['seats_available'] <= 0:
            raise HTTPException(status_code=400, detail="No seats available")
        cursor.execute("INSERT INTO passengers (full_name, contact_no, email, city) VALUES (%s,%s,%s,%s)", (request.passenger.full_name, request.passenger.contact_no, request.passenger.email, request.passenger.city))
        passenger_id = cursor.lastrowid
        cursor.execute("UPDATE flights SET seats_available = seats_available - 1 WHERE flight_id=%s", (request.flight_id,))
        dynamic_price = calculate_dynamic_price(float(flight['base_fare']), int(flight['total_seats']), int(flight['seats_available']) - 1, flight['departure'])
        pnr = generate_pnr()
        cursor.execute("INSERT INTO bookings (flight_id, passenger_id, seat_no) VALUES (%s,%s,%s)", (request.flight_id, passenger_id, request.seat_no))
        booking_id = cursor.lastrowid
        cursor.execute("INSERT INTO payments (booking_id, amount, payment_status) VALUES (%s,%s,'Pending')", (booking_id, dynamic_price))
        conn.commit()
        return {"message": "Booking successful", "pnr": pnr, "flight_no": flight['flight_no'], "price": dynamic_price, "status": "Pending"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/bookings")
def get_all_bookings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.booking_id, b.flight_id, b.seat_no, f.flight_no, f.origin, f.destination, f.departure, f.arrival,
                   p.full_name, p.contact_no, p.email, p.city,
                   pay.amount, pay.payment_status
            FROM bookings b
            JOIN flights f ON b.flight_id = f.flight_id
            JOIN passengers p ON b.passenger_id = p.passenger_id
            JOIN payments pay ON pay.booking_id = b.booking_id
        """)
        bookings = cursor.fetchall()
        return bookings
    finally:
        cursor.close()
        conn.close()

@app.get("/bookings/{pnr}")
def get_booking_by_pnr(pnr: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.booking_id, b.flight_id, b.seat_no, f.flight_no, f.origin, f.destination, f.departure, f.arrival,
                   p.full_name, p.contact_no, p.email, p.city,
                   pay.amount, pay.payment_status
            FROM bookings b
            JOIN flights f ON b.flight_id = f.flight_id
            JOIN passengers p ON b.passenger_id = p.passenger_id
            JOIN payments pay ON pay.booking_id = b.booking_id
            WHERE b.booking_id = %s
        """, (pnr,))
        booking = cursor.fetchone()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
    finally:
        cursor.close()
        conn.close()

@app.delete("/bookings/{pnr}")
def cancel_booking(pnr: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM bookings WHERE booking_id=%s", (pnr,))
        booking = cursor.fetchone()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        cursor.execute("UPDATE flights SET seats_available = seats_available + 1 WHERE flight_id=%s", (booking['flight_id'],))
        cursor.execute("UPDATE payments SET payment_status='Cancelled' WHERE booking_id=%s", (pnr,))
        conn.commit()
        return {"message": f"Booking {pnr} cancelled successfully"}
    finally:
        cursor.close()
        conn.close()

@app.post("/bookings/pay/{pnr}")
def simulate_payment(pnr: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM payments WHERE booking_id=%s", (pnr,))
        payment = cursor.fetchone()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment info not found")
        success = random.choice([True, False])
        if success:
            cursor.execute("UPDATE payments SET payment_status='Paid' WHERE booking_id=%s", (pnr,))
            conn.commit()
            status = "Paid"
            message = f"Payment successful for booking {pnr}"
        else:
            conn.rollback()
            status = "Payment Failed"
            message = f"Payment failed for booking {pnr}, please try again"
        return {"message": message, "status": status}
    finally:
        cursor.close()
        conn.close()
