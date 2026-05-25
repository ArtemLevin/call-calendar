const config = window.APP_CONFIG ?? { API_BASE_URL: '/api' };

const overlayToggle = document.getElementById('overlay-toggle');
const viewButtons = Array.from(document.querySelectorAll('.icon-btn[data-view]'));
const monthLabel = document.getElementById('month-label');
const prevMonth = document.getElementById('prev-month');
const nextMonth = document.getElementById('next-month');
const calendarGrid = document.getElementById('calendar-grid');
const selectedDateLabel = document.getElementById('selected-date-label');
const slotList = document.getElementById('slot-list');
const slotEmpty = document.getElementById('slot-empty');
const format12h = document.getElementById('format-12h');
const format24h = document.getElementById('format-24h');
const bookingForm = document.getElementById('booking-form');
const bookingResult = document.getElementById('booking-result');

let currentMonth = new Date();
let selectedDate = null;
let selectedTime = null;
let timeFormat = '24h';
let availableSlots = {};
const WORKDAY_START_HOUR = 9;
const WORKDAY_END_HOUR = 18;

function ymd(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function parseJsonSafe(response) {
  return response.json().catch(() => ({ detail: 'Unreadable server response.' }));
}

function formatErrorMessage(response, payload) {
  if (response.status === 409) return payload?.detail ?? 'Slot is already booked.';
  if (response.status === 422) return 'Invalid data. Check selected slot, name, and email.';
  return payload?.detail ?? `Unexpected error (${response.status})`;
}

function formatSlot(time24) {
  if (timeFormat === '24h') return time24;
  const [h, m] = time24.split(':').map(Number);
  const suffix = h >= 12 ? 'PM' : 'AM';
  const hour12 = ((h + 11) % 12) + 1;
  return `${hour12}:${String(m).padStart(2, '0')} ${suffix}`;
}

function slotsForDate(dateKey) {
  return availableSlots[dateKey] ?? [];
}

function enumerateBookableSlotsInMonth(monthDate) {
  const y = monthDate.getFullYear();
  const m = monthDate.getMonth();
  const daysInMonth = new Date(y, m + 1, 0).getDate();
  const slotsByDate = {};

  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = new Date(y, m, day);
    const isWeekend = date.getDay() === 0 || date.getDay() === 6;
    if (isWeekend) continue;

    const key = ymd(date);
    slotsByDate[key] = [];

    for (let hour = WORKDAY_START_HOUR; hour < WORKDAY_END_HOUR; hour += 1) {
      slotsByDate[key].push(`${String(hour).padStart(2, '0')}:00`);
      slotsByDate[key].push(`${String(hour).padStart(2, '0')}:30`);
    }
  }

  return slotsByDate;
}

function renderSlots() {
  const slots = selectedDate ? slotsForDate(selectedDate) : [];
  slotList.innerHTML = '';
  slotEmpty.hidden = slots.length > 0;

  for (const slot of slots) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'slot-button';
    btn.setAttribute('aria-pressed', String(selectedTime === slot));
    if (selectedTime === slot) btn.classList.add('selected');
    btn.innerHTML = `<span class="slot-dot" aria-hidden="true"></span><span>${formatSlot(slot)}</span>`;
    btn.addEventListener('click', () => {
      selectedTime = slot;
      renderSlots();
    });
    slotList.appendChild(btn);
  }
}

function renderSelectedDateLabel() {
  if (!selectedDate) {
    selectedDateLabel.textContent = 'Select date';
    return;
  }
  const d = new Date(`${selectedDate}T00:00:00`);
  selectedDateLabel.textContent = d.toLocaleDateString('en-US', { weekday: 'short', day: '2-digit' });
}

function renderCalendar() {
  const y = currentMonth.getFullYear();
  const m = currentMonth.getMonth();
  monthLabel.textContent = currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  const first = new Date(y, m, 1);
  const firstWeekdayMonBased = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(y, m + 1, 0).getDate();

  calendarGrid.innerHTML = '';
  for (let i = 0; i < firstWeekdayMonBased; i += 1) {
    calendarGrid.appendChild(document.createElement('div'));
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = new Date(y, m, day);
    const key = ymd(date);
    const slots = slotsForDate(key);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'day-cell';
    btn.textContent = String(day);
    btn.setAttribute('role', 'gridcell');
    btn.setAttribute('aria-selected', String(selectedDate === key));
    if (slots.length > 0) btn.classList.add('available');
    if (selectedDate === key) btn.classList.add('selected');
    if (slots.length === 0) btn.disabled = true;

    btn.addEventListener('click', () => {
      selectedDate = key;
      selectedTime = null;
      renderCalendar();
      renderSelectedDateLabel();
      renderSlots();
    });

    calendarGrid.appendChild(btn);
  }
}

function toIsoLocal(slotDate, slotTime) {
  return `${slotDate}T${slotTime}:00`;
}

async function loadUpcoming() {
  const fromTs = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1).toISOString().slice(0, 19);
  const response = await fetch(`${config.API_BASE_URL}/bookings/upcoming?from_ts=${encodeURIComponent(fromTs)}&limit=100&offset=0`);
  const payload = await parseJsonSafe(response);
  if (!response.ok) {
    throw new Error(formatErrorMessage(response, payload));
  }

  const bookedSlots = {};
  for (const booking of payload) {
    const [datePart, timePart] = booking.slot_start.split('T');
    const slotTime = (timePart ?? '').slice(0, 5);
    if (!slotTime) continue;
    if (!bookedSlots[datePart]) {
      bookedSlots[datePart] = [];
    }
    if (!bookedSlots[datePart].includes(slotTime)) {
      bookedSlots[datePart].push(slotTime);
    }
  }

  availableSlots = enumerateBookableSlotsInMonth(currentMonth);

  for (const dateKey of Object.keys(availableSlots)) {
    const dayBooked = new Set(bookedSlots[dateKey] ?? []);
    availableSlots[dateKey] = availableSlots[dateKey].filter((slot) => !dayBooked.has(slot));
    availableSlots[dateKey].sort();

    if (availableSlots[dateKey].length === 0) {
      delete availableSlots[dateKey];
    }
  }

  const firstDate = Object.keys(availableSlots).sort()[0] ?? null;
  if (selectedDate === null || !availableSlots[selectedDate]) {
    selectedDate = firstDate;
    selectedTime = null;
  }

  renderCalendar();
  renderSelectedDateLabel();
  renderSlots();
}

bookingForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  bookingResult.textContent = '';
  if (!selectedDate || !selectedTime) {
    bookingResult.textContent = 'Select date and time first.';
    return;
  }

  const body = {
    slot_start: toIsoLocal(selectedDate, selectedTime),
    customer_name: document.getElementById('customer_name').value,
    customer_email: document.getElementById('customer_email').value,
  };

  const response = await fetch(`${config.API_BASE_URL}/bookings/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const payload = await parseJsonSafe(response);

  if (!response.ok) {
    bookingResult.textContent = formatErrorMessage(response, payload);
    return;
  }

  bookingResult.textContent = `Booking #${payload.id} created.`;
  await loadUpcoming();
});

overlayToggle?.addEventListener('click', () => {
  const on = overlayToggle.getAttribute('aria-checked') === 'true';
  overlayToggle.setAttribute('aria-checked', String(!on));
});

viewButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    viewButtons.forEach((item) => item.classList.remove('is-active'));
    btn.classList.add('is-active');
  });
});

prevMonth?.addEventListener('click', async () => {
  currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
  await loadUpcoming();
});

nextMonth?.addEventListener('click', async () => {
  currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
  await loadUpcoming();
});

format12h?.addEventListener('click', () => {
  timeFormat = '12h';
  format12h.classList.add('is-active');
  format24h.classList.remove('is-active');
  format12h.setAttribute('aria-pressed', 'true');
  format24h.setAttribute('aria-pressed', 'false');
  renderSlots();
});

format24h?.addEventListener('click', () => {
  timeFormat = '24h';
  format24h.classList.add('is-active');
  format12h.classList.remove('is-active');
  format24h.setAttribute('aria-pressed', 'true');
  format12h.setAttribute('aria-pressed', 'false');
  renderSlots();
});

loadUpcoming().catch((error) => {
  bookingResult.textContent = error.message;
  renderCalendar();
  renderSelectedDateLabel();
  renderSlots();
});

renderCalendar();
renderSelectedDateLabel();
renderSlots();
