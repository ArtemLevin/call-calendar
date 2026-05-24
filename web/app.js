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

const availableSlots = {
  '2026-04-07': ['21:00', '21:30', '22:00', '22:30', '23:00', '23:30'],
  '2026-04-08': ['19:00', '19:30'],
};

let currentMonth = new Date(2026, 3, 1);
let selectedDate = '2026-04-07';
let selectedTime = null;
let timeFormat = '24h';

function ymd(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function formatSlot(time24) {
  if (timeFormat === '24h') return time24;
  const [h, m] = time24.split(':').map(Number);
  const suffix = h >= 12 ? 'PM' : 'AM';
  const hour12 = ((h + 11) % 12) + 1;
  return `${hour12}:${String(m).padStart(2, '0')} ${suffix}`;
}

function renderSlots() {
  const slots = availableSlots[selectedDate] ?? [];
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
    const blank = document.createElement('div');
    calendarGrid.appendChild(blank);
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = new Date(y, m, day);
    const key = ymd(date);
    const available = Object.hasOwn(availableSlots, key);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'day-cell';
    btn.textContent = String(day);
    btn.setAttribute('role', 'gridcell');
    btn.setAttribute('aria-selected', String(selectedDate === key));
    if (available) btn.classList.add('available');
    if (selectedDate === key) btn.classList.add('selected');
    if (!available) btn.disabled = true;

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

prevMonth?.addEventListener('click', () => {
  currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
  const inMonth = selectedDate.startsWith(`${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-`);
  if (!inMonth) selectedDate = ymd(new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1));
  selectedTime = null;
  renderCalendar();
  renderSelectedDateLabel();
  renderSlots();
});

nextMonth?.addEventListener('click', () => {
  currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
  const inMonth = selectedDate.startsWith(`${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-`);
  if (!inMonth) selectedDate = ymd(new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1));
  selectedTime = null;
  renderCalendar();
  renderSelectedDateLabel();
  renderSlots();
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

renderCalendar();
renderSelectedDateLabel();
renderSlots();
