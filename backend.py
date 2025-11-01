#Milestone-2,3
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, EmailStr, constr
from datetime import datetime, timedelta
import random, threading, os, mysql.connector, time

app = FastAPI(title="Flight Booking System")
app.mount("/static", StaticFiles(directory=os.path.dirname(__file__)), name="static")

@app.get("/")
def serve_homepage():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root@123",
        database="flight_booking",
        autocommit=False
    )

demand_levels = {"high": 1.5, "medium": 1.2, "low": 1.0}

class PassengerInfo(BaseModel):
    full_name: constr(min_length=2)
    contact_number: constr(min_length=7)
    email: EmailStr
    city: constr(min_length=2)

class BookingRequest(BaseModel):
    flight_id: int
    passenger: PassengerInfo

def calculate_dynamic_price(base_fare, seats_available, total_seats, departure_time):
    base_fare = float(base_fare)
    try:
        remaining_percentage = seats_available / total_seats
    except Exception:
        remaining_percentage = 1.0
    time_diff_hours = max(((departure_time - datetime.now()).total_seconds() / 3600), 0)
    demand = random.choice(list(demand_levels.values()))
    if remaining_percentage < 0.15:
        seat_factor = 2.0
    elif remaining_percentage < 0.3:
        seat_factor = 1.5
    elif remaining_percentage < 0.5:
        seat_factor = 1.2
    else:
        seat_factor = 1.0
    if time_diff_hours < 3:
        time_factor = 2.0
    elif time_diff_hours < 6:
        time_factor = 1.5
    elif time_diff_hours < 24:
        time_factor = 1.2
    else:
        time_factor = 1.0
    final = base_fare * seat_factor * time_factor * demand
    return round(final, 2)

@app.get("/flights")
def get_all_flights(sort_by: str = Query(None, regex="^(price|duration)$")):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flights")
    flights = cursor.fetchall()
    for f in flights:
        f["dynamic_price"] = calculate_dynamic_price(f["base_fare"], f["seats_available"], f["total_seats"], f["departure"])
        f["duration_seconds"] = int((f["arrival"] - f["departure"]).total_seconds())
    if sort_by == "price":
        flights.sort(key=lambda x: x["dynamic_price"])
    elif sort_by == "duration":
        flights.sort(key=lambda x: x["duration_seconds"])
    cursor.close()
    conn.close()
    return {"flights": flights}

@app.get("/search")
def search_flights(origin: str, destination: str, date: str, sort_by: str = Query(None, regex="^(price|duration)$")):
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except Exception:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flights WHERE origin=%s AND destination=%s AND DATE(departure)=%s",
                   (origin, destination, date))
    results = cursor.fetchall()
    if not results:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="No flights found")
    for r in results:
        r["dynamic_price"] = calculate_dynamic_price(r["base_fare"], r["seats_available"], r["total_seats"], r["departure"])
        r["duration_seconds"] = int((r["arrival"] - r["departure"]).total_seconds())
    if sort_by == "price":
        results.sort(key=lambda x: x["dynamic_price"])
    elif sort_by == "duration":
        results.sort(key=lambda x: x["duration_seconds"])
    cursor.close()
    conn.close()
    return {"search_results": results}

@app.post("/book")
def book_flight(booking: BookingRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM flights WHERE flight_id=%s FOR UPDATE", (booking.flight_id,))
        flight = cursor.fetchone()
        if not flight:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Flight not found")
        if flight["seats_available"] <= 0:
            conn.rollback()
            raise HTTPException(status_code=400, detail="No seats available")

        cursor.execute(
            "INSERT INTO passengers (full_name, contact_number, email, city) VALUES (%s,%s,%s,%s)",
            (booking.passenger.full_name, booking.passenger.contact_number, booking.passenger.email, booking.passenger.city)
        )
        passenger_id = cursor.lastrowid

        pnr = None
        for _ in range(5):
            candidate = "PNR" + str(random.randint(100000, 999999))
            cursor.execute("SELECT 1 FROM bookings WHERE pnr=%s", (candidate,))
            if not cursor.fetchone():
                pnr = candidate
                break
        if not pnr:
            conn.rollback()
            raise HTTPException(status_code=500, detail="Failed to generate unique PNR")

        price = calculate_dynamic_price(flight["base_fare"], flight["seats_available"], flight["total_seats"], flight["departure"])
        payment_status = "SUCCESS"  # ✅ always success

        cursor.execute(
            "INSERT INTO bookings (flight_id, passenger_id, seat_no, status, price, pnr) VALUES (%s,%s,%s,%s,%s,%s)",
            (booking.flight_id, passenger_id, "any", "CONFIRMED", price, pnr)
        )
        booking_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO payments (booking_id, amount, payment_status, payment_date) VALUES (%s,%s,%s,%s)",
            (booking_id, price, payment_status, datetime.now())
        )
        cursor.execute("UPDATE flights SET seats_available=seats_available-1 WHERE flight_id=%s", (booking.flight_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"PNR": pnr, "price": price}
    except mysql.connector.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/booking/{pnr}")
def get_booking(pnr: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, f.flight_no, f.origin, f.destination, f.departure, f.arrival, p.full_name, p.email, p.contact_number
        FROM bookings b
        JOIN flights f ON b.flight_id=f.flight_id
        JOIN passengers p ON b.passenger_id=p.passenger_id
        WHERE b.pnr=%s
    """, (pnr,))
    booking = cursor.fetchone()
    cursor.execute("SELECT * FROM payments WHERE booking_id=%s", (booking["booking_id"],))
    payment = cursor.fetchone()
    cursor.close()
    conn.close()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking["payment"] = payment
    return {"booking": booking}

@app.post("/cancel/{pnr}")
def cancel_booking(pnr: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bookings WHERE pnr=%s FOR UPDATE", (pnr,))
    booking = cursor.fetchone()
    if not booking:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["status"] == "CANCELLED":
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Already cancelled")
    cursor.execute("UPDATE bookings SET status='CANCELLED' WHERE pnr=%s", (pnr,))
    cursor.execute("UPDATE flights SET seats_available=seats_available+1 WHERE flight_id=%s", (booking["flight_id"],))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "CANCELLED", "PNR": pnr}

@app.get("/receipt/{pnr}")
def receipt(pnr: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, f.flight_no, f.origin, f.destination, f.departure, f.arrival,
                   p.full_name, p.email, p.contact_number
            FROM bookings b
            JOIN flights f ON b.flight_id = f.flight_id
            JOIN passengers p ON b.passenger_id = p.passenger_id
            WHERE b.pnr = %s
        """, (pnr,))
        booking = cursor.fetchone()
        cursor.close()
        conn.close()

        if not booking:
            return JSONResponse(status_code=404, content={"detail": f"PNR {pnr} not found"})

        receipt = {
            "PNR": booking.get("pnr"),
            "passenger": {
                "name": booking.get("full_name"),
                "email": booking.get("email"),
                "phone": booking.get("contact_number")
            },
            "flight_no": booking.get("flight_no"),
            "origin": booking.get("origin"),
            "destination": booking.get("destination"),
            "departure": booking.get("departure").isoformat() if isinstance(booking.get("departure"), datetime) else booking.get("departure"),
            "arrival": booking.get("arrival").isoformat() if isinstance(booking.get("arrival"), datetime) else booking.get("arrival"),
            "price": float(booking.get("price")),
            "status": booking.get("status")
        }

        return JSONResponse(content=receipt)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Error fetching receipt: {str(e)}"})

