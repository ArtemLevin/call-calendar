# План дальнейшего расширения функционала (feature-safe)

## 0. Контекст и цель

Текущая база проекта уже содержит:
- стабильный слой API/Service/Repository;
- доменные инварианты времени и слота;
- migration smoke + drift-check;
- базовый frontend для бронирования.

Цель этого плана — расширять продуктовые возможности **инкрементально и безопасно**, без нарушения архитектуры:

`Endpoint → Service → Repository → Database`

и без слома текущих контрактов.

---

## 1. Границы и правила выполнения

### Обязательные инварианты

1. Бизнес-логика только в `app/services/*`.
2. Endpoint-слой только для HTTP concerns (валидация/маппинг ошибок/response model).
3. Repository-слой только для доступа к данным и транзакционной персистенции.
4. Любое изменение схемы БД — только через Alembic revision.
5. Любое расширение API — с контрактными тестами и обновлением документации.

### Quality gate для каждого PR

- `make lint`
- `make typecheck`
- `make test`
- `make migrate-smoke`
- `make migration-drift-check`

---

## 2. План-эпики и порядок реализации

## Эпик A — Статусы (доработка до production-ready)

### Цель

Сделать управление статусами полностью предсказуемым и тестируемым для owner-сценариев.

### Scope

- `app/schemas/booking.py`
- `app/services/booking_service.py`
- `app/db/repositories/booking_repository.py`
- `app/api/endpoints/bookings.py`
- `tests/services/test_booking_service.py`
- `tests/api/test_bookings.py`

### Задачи

1. Зафиксировать публичный контракт смены статуса (request/response/errors).
2. Довести transition-policy в сервисе до полного покрытия edge-cases:
   - idempotent update;
   - terminal statuses;
   - not found;
   - invalid transition conflict.
3. Добавить owner-фильтрацию по статусу в read endpoint (без breaking changes).

### Критерий готовности

- все переходы статусов покрыты service + API tests;
- endpoint остаётся thin;
- нет дублирования transition-логики в repository/API.

---

## Эпик B — Owner Views (безопасное расширение read-модели)

### Цель

Добавить owner-ориентированные сценарии просмотра бронирований, не ломая существующий `/api/bookings/upcoming`.

### Scope

- `app/schemas/booking.py`
- `app/services/booking_service.py`
- `app/db/repositories/booking_repository.py`
- `app/api/endpoints/bookings.py`
- `tests/api/test_bookings.py`
- `tests/services/test_booking_service.py`
- `README.md` / `docs/architecture-boundaries.md`

### Задачи

1. Добавить owner-read use-case с явными фильтрами:
   - `status` (optional),
   - `from_ts` / `to_ts` (где применимо),
   - `limit/offset`.
2. Сохранить стабильную сортировку (`slot_start`, затем `id`) как контракт.
3. Документировать поведение пагинации и фильтров.

### Критерий готовности

- owner-view сценарий покрыт API-тестами;
- текущие booking endpoints не имеют breaking changes;
- контракты обновлены в docs.

---

## Эпик C — Pagination UX (инкрементально)

### Цель

Улучшить UX пагинации без мгновенного перехода на cursor-only модель.

### Scope

- `app/schemas/booking.py`
- `app/api/endpoints/bookings.py`
- `app/services/booking_service.py`
- `app/db/repositories/booking_repository.py`
- `web/app.js`
- `tests/api/test_bookings.py`

### Задачи

1. Расширить read-response метаданными пагинации (`has_more` или эквивалент).
2. Обновить frontend-controls для next/prev без изменения базового API path.
3. Добавить targeted tests для boundary условий:
   - последняя страница;
   - offset за пределами данных;
   - стабильный порядок при одинаковом `slot_start`.

### Критерий готовности

- UX навигации работает без прокрутки страницы/хаотичного пересортирования;
- API и UI согласованы по pagination-контракту;
- регрессий по существующим endpoint tests нет.

---

## Эпик D — Availability API (по готовности)

### Цель

Убрать дублирование вычисления доступных слотов во frontend и централизовать логику доступности на backend.

### Scope

- `app/schemas/booking.py`
- `app/services/booking_service.py`
- `app/db/repositories/booking_repository.py`
- `app/api/endpoints/bookings.py` (или новый endpoint-файл)
- `web/app.js`
- `tests/services/*`
- `tests/api/*`

### Задачи

1. Ввести read-only endpoint доступности слотов (без удаления текущего потока сразу).
2. Перенести правила генерации/фильтрации слотов в service.
3. Постепенно переключить frontend на новый endpoint.

### Критерий готовности

- единый источник истины для availability;
- frontend не дублирует бизнес-правила;
- старый контракт либо сохранён, либо аккуратно deprecate-нут с документацией.

---

## 3. Риски и ограничения

1. **Creeping scope** — не объединять эпики A/B/C/D в один PR.
2. **Контрактные регрессии** — любое изменение response shape только с тестами и docs update.
3. **CI длительность** — миграционные проверки обязательны, но запускать targeted tests по изменённому scope.
4. **Timezone edge cases** — все новые datetime-поля нормализовать на service boundary.

---

## 4. Рекомендуемая нарезка задач (issue breakdown)

### Iteration 1 (рекомендуем начать)
- Статус-фильтрация owner read + API tests.

### Iteration 2
- Документирование owner-contract + расширение service tests на status/read сочетания.

### Iteration 3
- Pagination metadata + frontend pagination controls.

### Iteration 4
- Availability endpoint (опционально, после стабилизации owner/pagination).

---

## 5. Definition of Done для каждого feature PR

PR считается завершённым только если:

1. Scope ограничен одним use-case.
2. Слои не нарушены.
3. Добавлены/обновлены targeted tests (happy + edge + error).
4. Пройдены `lint`, `typecheck`, `test`, `migrate-smoke`, `migration-drift-check`.
5. Обновлены docs при изменении API/поведения.
