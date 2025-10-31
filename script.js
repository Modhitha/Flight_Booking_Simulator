async function searchFlights() {
  const origin = document.getElementById("origin").value;
  const destination = document.getElementById("destination").value;
  const date = document.getElementById("date").value;
  const res = await fetch(`http://127.0.0.1:8000/search?origin=${origin}&destination=${destination}&date=${date}`);
  const data = await res.json();
  const container = document.getElementById("flights");
  container.innerHTML = "";
  if (!data.search_results) { container.innerHTML = "<p>No flights found</p>"; return; }
  data.search_results.forEach(f => {
    const div = document.createElement("div");
    div.className = "flight";
    div.innerHTML = `
      <h3>${f.flight_no}</h3>
      <p>${f.origin} → ${f.destination}</p>
      <p>Departure: ${new Date(f.departure).toLocaleString()}</p>
      <p>Price: ₹${f.dynamic_price}</p>
      <button onclick="bookFlight(${f.flight_id})">Book</button>`;
    container.appendChild(div);
  });
}

async function bookFlight(id) {
  const passenger = {
    full_name: "Test User",
    contact_number: "9999999999",
    email: "test@example.com",
    city: "Mumbai"
  };
  const body = { flight_id: id, passenger, seat_no: "12A" };
  const res = await fetch("http://127.0.0.1:8000/book", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const data = await res.json();
  alert("Booking Successful! PNR: " + data.PNR);
}