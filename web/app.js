
const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
const primaryNav = document.getElementById('primary-nav');

if (mobileMenuToggle && primaryNav) {
  mobileMenuToggle.addEventListener('click', () => {
    const expanded = mobileMenuToggle.getAttribute('aria-expanded') === 'true';
    mobileMenuToggle.setAttribute('aria-expanded', String(!expanded));
    primaryNav.classList.toggle('is-open', !expanded);
  });
}

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
const upcomingError = document.getElementById('upcoming-error');

let pageSize = Number(pageSizeSelect.value);
let currentPage = 0;
let lastPageReached = false;
let isLoading = false;

function setMessageState(target, message, variant = "") {
  target.textContent = message;
  target.classList.remove('error', 'success');
  if (variant) {
    target.classList.add(variant);
  }
}

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

function setLoadingState(loading) {
  isLoading = loading;
  bookingForm.querySelector('button[type="submit"]').disabled = loading;
  refreshButton.disabled = loading;
  pageSizeSelect.disabled = loading;
  prevPageButton.disabled = loading || currentPage === 0;
  nextPageButton.disabled = loading || nextPageButton.disabled;
}

async function loadUpcoming() {
  setLoadingState(true);
  upcomingError.textContent = '';
  const offset = currentPage * pageSize;
  const fromTs = toApiLocalNaiveDateTime(slotStartInput.value) || new Date().toISOString().slice(0, 19);
  const url = `${config.API_BASE_URL}/bookings/upcoming?from_ts=${encodeURIComponent(fromTs)}&limit=${pageSize}&offset=${offset}`;
  try {
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
  } finally {
    // Why: centralized loading teardown prevents disabled controls from getting
    // stuck when any network branch throws before normal completion.
    setLoadingState(false);
  }
}

bookingForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const body = {
    slot_start: toApiLocalNaiveDateTime(slotStartInput.value),
    customer_name: document.getElementById('customer_name').value,
    customer_email: document.getElementById('customer_email').value,
  };

  setMessageState(createResult, '');

  try {
    setLoadingState(true);
    const response = await fetch(`${config.API_BASE_URL}/bookings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const payload = await parseJsonSafe(response);
    if (!response.ok) {
      setMessageState(createResult, formatErrorMessage(response, payload), 'error');
      return;
    }

    // Why: reloading page 1 after successful create keeps pagination stable and
    // surfaces the new slot according to backend sorting rules.
    currentPage = 0;
    setMessageState(createResult, `Booking #${payload.id} created.`, 'success');
    await loadUpcoming();
  } catch (_error) {
    setMessageState(createResult, 'Network error. Please retry.', 'error');
  } finally {
    setLoadingState(false);
  }
});

refreshButton.addEventListener('click', async () => {
  if (isLoading) {
    return;
  }
  try {
    await loadUpcoming();
  } catch (error) {
    setMessageState(upcomingError, error.message, 'error');
  }
});

pageSizeSelect.addEventListener('change', async () => {
  pageSize = Number(pageSizeSelect.value);
  currentPage = 0;

  try {
    await loadUpcoming();
  } catch (error) {
    setMessageState(upcomingError, error.message, 'error');
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
    setMessageState(upcomingError, error.message, 'error');
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
    setMessageState(upcomingError, error.message, 'error');
  }
});

loadUpcoming().catch((error) => {
  upcomingError.textContent = error.message;
});
