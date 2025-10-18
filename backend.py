from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import random
import asyncio
import mysql.connector

app = FastAPI()

#  Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="flight_booking_system"
    )

# Pydantic Models
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

# Dynamic Pricing Function
def calculate_dynamic_price(base_fare: float, total_seats: int, seats_available: int, departure_time: datetime) -> float:
    
    seat_percentage = (total_seats - seats_available) / total_seats
    seat_factor = 0.25 * seat_percentage  

    hours_until_departure = (departure_time - datetime.now()).total_seconds() / 3600
    if hours_until_departure <= 0:
        hours_until_departure = 1
    
    time_factor = 0.0
    if hours_until_departure <= 24:
        time_factor = 0.4 
    else:
        time_factor = min(0.2, 0.2 * (24 / hours_until_departure))

    
    demand_level = random.uniform(0.0, 1.0)  
    demand_factor = 0.3 * demand_level 

    
    if base_fare >= 8000:
        tier_factor = 0.15  
    elif base_fare >= 5000:
        tier_factor = 0.08  
    else:
        tier_factor = 0.03  

    
    volatility = random.uniform(-0.02, 0.05)

    
    multiplier = 1 + seat_factor + time_factor + demand_factor + tier_factor + volatility
    dynamic_price = base_fare * multiplier
    return round(dynamic_price, 2)

# Build REST APIs - Retrieving all flights
@app.get("/flights", response_model=List[FlightResponse])
def get_all_flights(sort_by: Optional[str] = Query(None, regex="^(price|duration)$")):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flights")
    flights = cursor.fetchall()
    result = []
    for f in flights:
        dynamic_price = calculate_dynamic_price(
            float(f['base_fare']),
            int(f['total_seats']),
            int(f['seats_available']),
            f['departure']
        )
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
    # Sorting
    if sort_by == "price":
        result.sort(key=lambda x: x["dynamic_price"])
    elif sort_by == "duration":
        result.sort(key=lambda x: (
            datetime.strptime(x["arrival"], "%Y-%m-%d %H:%M:%S") -
            datetime.strptime(x["departure"], "%Y-%m-%d %H:%M:%S")
        ).total_seconds())
    cursor.close()
    conn.close()
    return result

#  Search API with Dynamic Pricing Integration
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
        dynamic_price = calculate_dynamic_price(
            float(f['base_fare']),
            int(f['total_seats']),
            int(f['seats_available']),
            f['departure']
        )
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

#  Simulate external airline schedule APIs
@app.get("/external/schedule")
def simulate_external_api():
    sample_flights = [
        {"flight_no": "QF789", "origin": "Delhi", "destination": "Singapore", "departure": "2025-03-05 09:00:00"},
        {"flight_no": "EK555", "origin": "Mumbai", "destination": "Dubai", "departure": "2025-03-06 07:30:00"}
    ]
    return {"external_flights": sample_flights}

#  Background process to simulate demand/availability changes
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
