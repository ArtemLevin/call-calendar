const config = window.APP_CONFIG ?? { API_BASE_URL: '/api' };

const bookingForm = document.getElementById('booking-form');
const createResult = document.getElementById('create-result');
const upcomingList = document.getElementById('upcoming-list');
const refreshButton = document.getElementById('refresh-upcoming');

function formatErrorMessage(response, payload) {
  if (response.status === 409) {
    return payload?.detail ?? 'Slot is already booked.';
  }

  if (response.status === 422) {
    return 'Invalid input. Please check datetime/email format.';
  }

  return payload?.detail ?? `Unexpected error (${response.status})`;
}

async function loadUpcoming() {
  const fromTs = new Date().toISOString().slice(0, 19);
  const url = `${config.API_BASE_URL}/bookings/upcoming?from_ts=${encodeURIComponent(fromTs)}&limit=20&offset=0`;
  const response = await fetch(url);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(formatErrorMessage(response, payload));
  }

  upcomingList.innerHTML = '';
  for (const booking of payload) {
    const item = document.createElement('li');
    item.textContent = `${booking.slot_start} — ${booking.customer_name} (${booking.customer_email})`;
    upcomingList.appendChild(item);
  }
}

bookingForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const body = {
    slot_start: document.getElementById('slot_start').value,
    customer_name: document.getElementById('customer_name').value,
    customer_email: document.getElementById('customer_email').value,
  };

  createResult.textContent = '';

  const response = await fetch(`${config.API_BASE_URL}/bookings/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const payload = await response.json();
  if (!response.ok) {
    createResult.textContent = formatErrorMessage(response, payload);
    return;
  }

  // Why: immediately reloading the upcoming list keeps UI state aligned with
  // backend ordering and conflict rules instead of duplicating list logic client-side.
  createResult.textContent = `Booking #${payload.id} created.`;
  await loadUpcoming();
});

refreshButton.addEventListener('click', async () => {
  try {
    await loadUpcoming();
  } catch (error) {
    createResult.textContent = error.message;
  }
});

loadUpcoming().catch((error) => {
  createResult.textContent = error.message;
});
