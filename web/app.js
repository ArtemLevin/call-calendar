const config = window.APP_CONFIG ?? { API_BASE_URL: '/api' };

const bookingForm = document.getElementById('booking-form');
const createResult = document.getElementById('create-result');
const upcomingList = document.getElementById('upcoming-list');
const refreshButton = document.getElementById('refresh-upcoming');
const pageSizeSelect = document.getElementById('page-size');
const prevPageButton = document.getElementById('prev-page');
const nextPageButton = document.getElementById('next-page');
const pageInfo = document.getElementById('page-info');
const slotStartInput = document.getElementById('slot_start');

let pageSize = Number(pageSizeSelect.value);
let currentPage = 0;
let lastPageReached = false;

function formatErrorMessage(response, payload) {
  if (response.status === 409) {
    return payload?.detail ?? 'Slot is already booked.';
  }

  if (response.status === 422) {
    return 'Invalid input. Please check datetime/email format.';
  }

  return payload?.detail ?? `Unexpected error (${response.status})`;
}

function parseJsonSafe(response) {
  return response
    .json()
    .catch(() => ({ detail: 'Server returned an unreadable response.' }));
}

function toApiLocalNaiveDateTime(value) {
  if (!value) {
    return '';
  }

  // Why: backend persists naive datetime values, so we keep local wall-clock
  // format without timezone suffix to avoid accidental client-side UTC shifts.
  return `${value}:00`;
}

function updatePaginationControls(resultCount) {
  pageInfo.textContent = `Page ${currentPage + 1}`;
  prevPageButton.disabled = currentPage === 0;
  nextPageButton.disabled = resultCount < pageSize || lastPageReached;
}

async function loadUpcoming() {
  const offset = currentPage * pageSize;
  const fromTs = toApiLocalNaiveDateTime(slotStartInput.value) || new Date().toISOString().slice(0, 19);
  const url = `${config.API_BASE_URL}/bookings/upcoming?from_ts=${encodeURIComponent(fromTs)}&limit=${pageSize}&offset=${offset}`;
  const response = await fetch(url);
  const payload = await parseJsonSafe(response);

  if (!response.ok) {
    throw new Error(formatErrorMessage(response, payload));
  }

  upcomingList.innerHTML = '';
  for (const booking of payload) {
    const item = document.createElement('li');
    item.textContent = `${booking.slot_start} — ${booking.customer_name} (${booking.customer_email})`;
    upcomingList.appendChild(item);
  }

  lastPageReached = payload.length < pageSize;
  updatePaginationControls(payload.length);
}

bookingForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const body = {
    slot_start: toApiLocalNaiveDateTime(slotStartInput.value),
    customer_name: document.getElementById('customer_name').value,
    customer_email: document.getElementById('customer_email').value,
  };

  createResult.textContent = '';

  try {
    const response = await fetch(`${config.API_BASE_URL}/bookings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const payload = await parseJsonSafe(response);
    if (!response.ok) {
      createResult.textContent = formatErrorMessage(response, payload);
      return;
    }

    // Why: reloading page 1 after successful create keeps pagination stable and
    // surfaces the new slot according to backend sorting rules.
    currentPage = 0;
    createResult.textContent = `Booking #${payload.id} created.`;
    await loadUpcoming();
  } catch (_error) {
    createResult.textContent = 'Network error. Please retry.';
  }
});

refreshButton.addEventListener('click', async () => {
  try {
    await loadUpcoming();
  } catch (error) {
    createResult.textContent = error.message;
  }
});

pageSizeSelect.addEventListener('change', async () => {
  pageSize = Number(pageSizeSelect.value);
  currentPage = 0;

  try {
    await loadUpcoming();
  } catch (error) {
    createResult.textContent = error.message;
  }
});

prevPageButton.addEventListener('click', async () => {
  if (currentPage === 0) {
    return;
  }

  currentPage -= 1;
  try {
    await loadUpcoming();
  } catch (error) {
    createResult.textContent = error.message;
  }
});

nextPageButton.addEventListener('click', async () => {
  if (lastPageReached) {
    return;
  }

  currentPage += 1;
  try {
    await loadUpcoming();
  } catch (error) {
    createResult.textContent = error.message;
  }
});

loadUpcoming().catch((error) => {
  createResult.textContent = error.message;
});
