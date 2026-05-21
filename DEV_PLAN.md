# План реализации минимально жизнеспособного каркаса booking‑сервиса

## 1. Scope (что именно делаем)

Создаём минимально жизнеспособный каркас booking‑сервиса (без auth и внешних интеграций), чтобы:

* появилась реальная структура `app/`, `tests/`, `alembic/`;
* заработал базовый API для слотов/бронирований;
* соблюдалась архитектура **Endpoint → Service → Repository → Database**;
* были первичные тесты (happy path + ошибки);
* проходили команды: `make test`, `make lint`, `make typecheck`.

Это соответствует целевому описанию проекта и DoD в `AGENTS.md`.

## 2. Архитектурные границы (жёсткие правила)

При реализации держим следующие инварианты (следует из `docs/architecture-boundaries.md`):

* **Endpoint**: только HTTP/валидация/маппинг ошибок.
* **Service**: все бизнес‑правила (30‑минутные слоты, конфликт брони, валидация бизнес‑ограничений).
* **Repository**: только доступ к данным.
* **Model**: без сетевого I/O и бизнес‑оркестрации.


## 3. Пошаговый план реализации

### Шаг A. Инициализация структуры

Создать:
* `app/main.py` (FastAPI app + healthcheck + router include);
* `app/api/endpoints/bookings.py`;
* `app/services/booking_service.py`;
* `app/db/models/booking.py`;
* `app/db/repositories/booking_repository.py`;
* `app/db/session.py`;
* `app/schemas/booking.py`;
* `app/exceptions.py`;
* `tests/api/test_bookings.py`;
* `tests/services/test_booking_service.py`;
* `tests/db/test_booking_repository.py`;
* `alembic/` (+ `env.py`, `versions/` — initial migration).

Ориентир берём из «Reference Files / TODO to create».

### Шаг B. Доменная модель и контракты

Ввести:
* `BookingStatus` enum (`pending|confirmed|cancelled|completed`);
* SQLAlchemy‑модель `Booking` (`id`, `slot_start`, `customer_name`, `customer_email`, `status`, `created_at`);
* Pydantic‑схемы:
    * `BookingCreate`;
    * `BookingResponse`;
    * при необходимости `BookingListResponse`.


**Правила:**
* типизация везде обязательна;
* `EmailStr`, ограничения на имя, `slot datetime`;
* без `Any` без причины.

### Шаг C. Repository слой

Минимальные методы:
* `create(data: BookingCreate) -> Booking`;
* `get_by_id(booking_id: int) -> Booking | None`;
* `list_upcoming(now: datetime) -> list[Booking]`;
* `is_slot_available(slot_start: datetime) -> bool`.

**Важно:**
* доступ к БД только здесь;
* в `is_slot_available` учитывать, что `cancelled` не блокирует слот.

### Шаг D. Service слой

`BookingService`:
* `create_booking(data)`:
    * проверка `slot` на 30‑минутную сетку;
    * проверка «в будущем»;
    * проверка доступности слота;
    * создание брони.
* `get_booking(id)`;
* `list_upcoming_bookings()`.

Ошибки — через доменные exception‑классы (например, `SlotNotAvailableError`, `BookingNotFoundError`, `InvalidSlotError`).

### Шаг E. Endpoint слой

Минимальные HTTP‑ручки:
* `POST /api/bookings` — создать бронь;
* `GET /api/bookings/{id}` — получить бронь;
* `GET /api/bookings/upcoming` — список предстоящих.

**Endpoint делает только:**
* приём/валидацию входа через Pydantic;
* вызов service;
* трансляцию доменных ошибок в HTTP‑коды (`409`, `404`, `422` и т. д.).

### Шаг F. Миграции
* инициализировать Alembic;
* создать initial migration для таблицы `bookings`;
* проверить `upgrade/downgrade` на локальной БД (без destructive действий и без удаления данных).

### Шаг G. Тесты (обязательный минимум)

**Service tests** (`tests/services`):
* happy path create;
* slot already taken → `SlotNotAvailableError`;
* invalid 30‑min slot;
* past slot rejection.

**API tests** (`tests/api`):
* `POST /bookings` success (`201`);
* conflict (`409`);
* invalid payload (`422`);
* get not found (`404`).

**Repository tests** (`tests/db`):
* create/get/list;
* availability logic учитывает статус `cancelled`.

Требования: AAA‑паттерн и покрытие изменённого кода ≥ 80 %.

## 4. Риски и как их заранее закрыть

* **Несоответствие Pydantic v1/v2**: зафиксировать стиль (`model_validate`/`model_dump`) и привести весь код к одной версии.
* **Timezone/naive datetime**: сразу определить policy (`UTC‑aware` preferred), явно задокументировать.
* **Гонки при бронировании**:
    * минимум: уникальный индекс/constraint на `slot_start` для активных статусов или транзакционная проверка;
    * тест на конфликтный сценарий на уровне сервиса.
* **Разрыв архитектурных границ**: code review по чек‑листу boundaries перед merge.

## 5. Verify‑план (строго по договорённостям)

После каждого небольшого инкремента:
* `make test`;
* `make lint`;
* `make typecheck`.

Перед финалом: проверить DoD чек‑лист из `AGENTS.md`.

## 6. Предлагаемый порядок коммитов (мелкими шагами)

1. `chore: scaffold app/tests/alembic structure`.
2. `feat: add booking model schemas and base exceptions`.
3. `feat: implement booking repository and service`.
4. `feat: add booking API endpoints and error mapping`.
5. `test: add service/api/repository tests`.
6. `chore: add initial alembic migration and finalize checks`.
