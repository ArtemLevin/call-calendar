const config = window.APP_CONFIG ?? { API_BASE_URL: '/api' };

const overlayToggle = document.getElementById('overlay-toggle');
const settingsButton = document.getElementById('settings-button');
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
const meetingTitle = document.getElementById('meeting-title');
const meetingDurationSelect = document.getElementById('meeting-duration-select');
const meetingProviderSelect = document.getElementById('meeting-provider-select');
const meetingTimezoneSelect = document.getElementById('meeting-timezone-select');
const colleagueSelect = document.getElementById('colleague-select');
const colleagueAvatar = document.getElementById('colleague-avatar');

let currentMonth = new Date();
let selectedDate = null;
let selectedTime = null;
let timeFormat = '24h';
let availableSlots = {};
let colleagues = [];
let selectedColleague = null;
let meetingSettings = {
  meeting_provider: 'google_meet',
  meeting_timezone: 'Asia/Yekaterinburg',
  meeting_duration_minutes: 30,
};

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

function toMeetingTitle(duration) {
  return `${duration} Min Meeting`;
}

function providerLabel(provider) {
  return provider.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function populateSelect(select, values, selectedValue, formatter = (value) => String(value)) {
  if (!select) return;
  select.innerHTML = '';
  for (const value of values) {
    const option = document.createElement('option');
    option.value = String(value);
    option.textContent = formatter(value);
    option.selected = String(value) === String(selectedValue);
    select.appendChild(option);
  }
}

function renderMeetingSettings() {
  if (meetingTitle) {
    meetingTitle.textContent = toMeetingTitle(meetingSettings.meeting_duration_minutes);
  }
}

async function loadGlobalMeetingSettings() {
  const [optionsResponse, settingsResponse] = await Promise.all([
    fetch(`${config.API_BASE_URL}/meeting-metadata/options`),
    fetch(`${config.API_BASE_URL}/meeting-settings`),
  ]);
  const optionsPayload = await parseJsonSafe(optionsResponse);
  const settingsPayload = await parseJsonSafe(settingsResponse);
  if (!optionsResponse.ok) throw new Error(formatErrorMessage(optionsResponse, optionsPayload));
  if (!settingsResponse.ok) throw new Error(formatErrorMessage(settingsResponse, settingsPayload));

  meetingSettings = settingsPayload;
  populateSelect(meetingTimezoneSelect, optionsPayload.meeting_timezone_options, settingsPayload.meeting_timezone);
  populateSelect(
    meetingDurationSelect,
    optionsPayload.meeting_duration_minutes_options,
    settingsPayload.meeting_duration_minutes,
    (value) => `${value}m`,
  );
  renderMeetingSettings();
}

function applyColleagueToMeetingSettings() {
  if (!selectedColleague) return;
  meetingSettings = {
    ...meetingSettings,
    meeting_provider: selectedColleague.default_meeting_provider,
    meeting_timezone: selectedColleague.timezone,
    meeting_duration_minutes: selectedColleague.meeting_duration_minutes,
  };
  populateSelect(
    meetingProviderSelect,
    selectedColleague.contact_options,
    meetingSettings.meeting_provider,
    providerLabel,
  );
  populateSelect(meetingTimezoneSelect, [selectedColleague.timezone], meetingSettings.meeting_timezone);
  populateSelect(
    meetingDurationSelect,
    [selectedColleague.meeting_duration_minutes],
    meetingSettings.meeting_duration_minutes,
    (value) => `${value}m`,
  );
  renderMeetingSettings();
}

async function loadColleagues() {
  const response = await fetch(`${config.API_BASE_URL}/colleagues/`);
  const payload = await parseJsonSafe(response);
  if (!response.ok) throw new Error(formatErrorMessage(response, payload));
  colleagues = payload;
  if (colleagues.length === 0) throw new Error('No colleagues available for booking.');

  const selectedId = selectedColleague?.id ?? colleagues[0].id;
  selectedColleague = colleagues.find((item) => item.id === selectedId) ?? colleagues[0];

  populateSelect(colleagueSelect, colleagues.map((item) => item.id), selectedColleague.id, (value) => {
    const colleague = colleagues.find((item) => item.id === Number(value));
    return colleague ? colleague.name : String(value);
  });
  if (colleagueAvatar && selectedColleague.name.length > 0) {
    colleagueAvatar.textContent = selectedColleague.name[0].toUpperCase();
  }
  applyColleagueToMeetingSettings();
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

async function loadAvailability() {
  if (!selectedColleague) return;
  const monthStart = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1, 0, 0, 0);
  const monthEnd = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1, 0, 0, 0);
  const response = await fetch(
    `${config.API_BASE_URL}/colleagues/${selectedColleague.id}/availability?from_ts=${encodeURIComponent(monthStart.toISOString().slice(0, 19))}&to_ts=${encodeURIComponent(monthEnd.toISOString().slice(0, 19))}`,
  );
  const payload = await parseJsonSafe(response);
  if (!response.ok) throw new Error(formatErrorMessage(response, payload));

  availableSlots = {};
  for (const slot of payload.slots) {
    const [datePart, timePart] = slot.slot_start.split('T');
    const slotTime = (timePart ?? '').slice(0, 5);
    if (!datePart || !slotTime) continue;
    if (!availableSlots[datePart]) availableSlots[datePart] = [];
    availableSlots[datePart].push(slotTime);
  }

  for (const dateKey of Object.keys(availableSlots)) {
    availableSlots[dateKey].sort();
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
  if (!selectedDate || !selectedTime || !selectedColleague) {
    bookingResult.textContent = 'Select colleague, date, and time first.';
    return;
  }

  const body = {
    slot_start: toIsoLocal(selectedDate, selectedTime),
    customer_name: document.getElementById('customer_name').value,
    customer_email: document.getElementById('customer_email').value,
    meeting_provider: meetingSettings.meeting_provider,
    meeting_timezone: meetingSettings.meeting_timezone,
    meeting_duration_minutes: meetingSettings.meeting_duration_minutes,
    colleague_id: selectedColleague.id,
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
  await loadAvailability();
});

colleagueSelect?.addEventListener('change', async () => {
  const selectedId = Number(colleagueSelect.value);
  selectedColleague = colleagues.find((item) => item.id === selectedId) ?? null;
  if (!selectedColleague) {
    bookingResult.textContent = 'Selected colleague is unavailable.';
    return;
  }
  if (colleagueAvatar && selectedColleague.name.length > 0) {
    colleagueAvatar.textContent = selectedColleague.name[0].toUpperCase();
  }
  selectedTime = null;
  selectedDate = null;
  applyColleagueToMeetingSettings();
  try {
    await loadAvailability();
  } catch (error) {
    bookingResult.textContent = error.message;
  }
});

overlayToggle?.addEventListener('click', () => {
  const on = overlayToggle.getAttribute('aria-checked') === 'true';
  overlayToggle.setAttribute('aria-checked', String(!on));
});

settingsButton?.addEventListener('click', () => {
  colleagueSelect?.focus();
});

viewButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    viewButtons.forEach((item) => item.classList.remove('is-active'));
    btn.classList.add('is-active');
  });
});

prevMonth?.addEventListener('click', async () => {
  currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
  await loadAvailability();
});

nextMonth?.addEventListener('click', async () => {
  currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
  await loadAvailability();
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

Promise.all([loadGlobalMeetingSettings(), loadColleagues()])
  .then(() => loadAvailability())
  .catch((error) => {
    bookingResult.textContent = error.message;
  })
  .finally(() => {
    renderCalendar();
    renderSelectedDateLabel();
    renderSlots();
    renderMeetingSettings();
  });
