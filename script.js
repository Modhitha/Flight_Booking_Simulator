const API = "";
document.getElementById("search-btn").addEventListener("click", searchFlights);
document.getElementById("lookup-btn").addEventListener("click", lookupPNR);
document.getElementById("cancel-btn").addEventListener("click", cancelPNR);
let selectedFlight = null;

function el(tag, inner, cls) {
  const d = document.createElement(tag);
  if (inner) d.innerHTML = inner;
  if (cls) d.className = cls;
  return d;
}

async function searchFlights() {
  const origin = document.getElementById("origin").value;
  const destination = document.getElementById("destination").value;
  const date = document.getElementById("date").value;
  const sort_by = document.getElementById("sort_by").value;
  if (!origin || !destination || !date) { alert("fill origin, destination and date"); return; }
  try {
    const res = await fetch(`${API}/search?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&date=${encodeURIComponent(date)}&sort_by=${encodeURIComponent(sort_by)}`);
    if (!res.ok) throw res;
    const data = await res.json();
    renderFlights(data.search_results);
  } catch (e) {
    document.getElementById("flights").innerHTML = "<div class='card'>No flights found</div>";
  }
}

function renderFlights(list) {
  const container = document.getElementById("flights");
  container.innerHTML = "";
  list.forEach(f => {
    const card = el("div", "", "flight-card");
    card.innerHTML = `<b>${f.flight_no}</b> <span class="small">(${f.airline_name || ""})</span><br>
      ${f.origin} → ${f.destination}<br>
      Departure: ${new Date(f.departure).toLocaleString()} | Arrival: ${new Date(f.arrival).toLocaleString()}<br>
      Price: ₹${f.dynamic_price.toFixed(2)} | Seats Available: ${f.seats_available}<br>`;
    const bookBtn = el("button", "Book");
    bookBtn.onclick = () => startBooking(f);
    card.appendChild(bookBtn);
    container.appendChild(card);
  });
}

function startBooking(flight) {
  selectedFlight = flight;
  document.getElementById("p-name").value = "";
  document.getElementById("p-phone").value = "";
  document.getElementById("p-email").value = "";
  document.getElementById("p-city").value = "";
  document.getElementById("passenger-modal").classList.remove("hidden");
  document.getElementById("pay-btn").onclick = simulatePaymentAndBook;
  document.getElementById("cancel-pass").onclick = () => document.getElementById("passenger-modal").classList.add("hidden");
}

async function simulatePaymentAndBook() {
  const name = document.getElementById("p-name").value.trim();
  const phone = document.getElementById("p-phone").value.trim();
  const email = document.getElementById("p-email").value.trim();
  const city = document.getElementById("p-city").value.trim();
  if (!name || !phone || !email || !city) { alert("Fill passenger info"); return; }
  const booking = {
    flight_id: selectedFlight.flight_id,
    passenger: { full_name: name, contact_number: phone, email: email, city: city },
    seat_no: "Auto"
  };
  document.getElementById("passenger-modal").classList.add("hidden");
  const payOK = Math.random() < 0.9;
  if (!payOK) { alert("Payment failed (simulated). Try again."); return; }
  try {
    const res = await fetch("/book", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(booking) });
    const data = await res.json();
    if (!res.ok) { alert(data.detail || "Booking failed"); return; }
    showReceipt(data.PNR);
  } catch (e) {
    alert("Booking error");
  }
}

async function showReceipt(pnr) {
  try {
    const res = await fetch(`/receipt/${pnr}`);
    if (!res.ok) throw res;
    const r = await res.json();
    const area = document.getElementById("receipt-area");
    area.innerHTML = `<div class="card"><b>Booking Confirmed</b><br>PNR: ${r.PNR}<br>Flight: ${r.flight_no}<br>${r.origin} → ${r.destination}<br>Departure: ${r.departure}<br>Price: ₹${r.price}<br><button id="download-json">Download Receipt (JSON)</button></div>`;
    document.getElementById("download-json").onclick = () => downloadJSON(r);
  } catch (e) {
    alert("Unable to fetch receipt");
  }
}

function downloadJSON(obj) {
  const data = JSON.stringify(obj, null, 2);
  const blob = new Blob([data], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `receipt_${obj.PNR}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function lookupPNR() {
  const pnr = document.getElementById("lookup-pnr").value.trim();
  if (!pnr) return alert("enter pnr");
  try {
    const res = await fetch(`/booking/${pnr}`);
    if (!res.ok) throw res;
    const data = await res.json();
    document.getElementById("lookup-result").textContent = JSON.stringify(data.booking, null, 2);
  } catch (e) {
    document.getElementById("lookup-result").textContent = "Not found";
  }
}

async function cancelPNR() {
  const pnr = document.getElementById("cancel-pnr").value.trim();
  if (!pnr) return alert("enter pnr to cancel");
  try {
    const res = await fetch(`/cancel/${pnr}`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw data;
    alert("Cancelled: " + data.PNR);
  } catch (e) {
    alert("Cancel failed");
  }
}
