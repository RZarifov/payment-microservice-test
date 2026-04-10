# Async payment service test task
Тестовое задание.  

Микросервис для асинхронной обработки платежей. Сервис
принимает запросы на оплату, обрабатывает их через внешний платежный шлюз
(эмуляцию) и уведомляет клиента о результате через webhook.

---

## Сущности

### Платёж (Payment)

- ID платежа (уникальный идентификатор)
- Сумма (decimal)
- Валюта (RUB, USD, EUR)
- Описание (строка)
- Метаданные (JSON поле для дополнительной информации)
- Статус (pending, succeeded, failed)
- Idempotency key (уникальный ключ для защиты от дублей)
- Webhook URL (для уведомления о результате)
- Даты создания и обработки

---

## Функционал API

### Создание платежа

**POST /api/v1/payments**

- Заголовок: Idempotency-Key (обязательный)
- Body: сумма, валюта, описание, метаданные, webhook_url
- Ответ: 202 Accepted, payment_id, статус, crea

### Получение информации о платеже

**GET /api/v1/payments/{payment_id}**

- Ответ: детальная информация о платеже.

---

## Технические требования:

### Брокер сообщений

- При создании платежа публикуется событие в очередь payments.new

- Один consumer:
  - Получает сообщение из очереди
  - Эмулирует обработку платежа (2-5 сек, 90% успех, 10% ошибка)
  - Обновляет статус в БД
  - Отправляет webhook уведомление на указанный URL
  - Реализует повторные попытки при ошибках отправки

- Гарантии доставки
  - Outbox pattern для гарантированной публикации событий
  - Idempotency key для защиты от дублей
  - Dead Letter Queue для сообщений, не обработанных после 3 попыто

---

## Auth

Статический api ключ в заголовке X-API-Key для всех эндпоинтов.

---

## Tech Stack

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (асинхронный режим)
- PostgreSQL
- RabbitMQ (FastStream)
- Alembic (миграции)
- Docker + docker-compose

---

## Требования к результату

1. Модели и миграции: таблицы payments и outbox
2. API эндпоинты: создание и получение платежа
3. Consumer: один обработчик, делающий всё
4. Outbox pattern: гарантированная доставка событий
5. Retry: 3 попытки с экспоненциальной задержкой
6. Dead Letter Queue: для окончательно упавших сообщений
7. Docker: compose файл с postgres, rabbitmq, api, consumer
8. Документация: README с запуском и примерами

---

## Критерии оценки:

- Архитектура и чистота кода
- Корректная реализация Outbox pattern
- Работа с RabbitMQ (очереди, обменники, DLQ)
- Идемпотентность
- Обработка ошибок и retry логика
- Работоспособность Docker-окружения

---

## DATABASE INIT AND INITIAL LAUNCH
```
# INITIATES AND PRIMES DOCKER
make up

# MAKES MIGRATIONS FOR ALEMBIC
make migrate

# MAKES REVISION FOR ALEMBIC
make revision m="create payments and outbox"

# LAUNCH THE APP THEN TEST THROUGH CURL
make run
```

---

## TEST CURL

##### Create payment
```
curl -i -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: luna_test" \
  -H "Idempotency-Key: test-001" \
  -d '{
    "amount": "100.00",
    "currency": "RUB",
    "description": "test payment",
    "webhook_url": "http://localhost:9999/webhook"
  }'
```

##### Fetch payment
```
PAYMENT_ID=<<<YOUR PAYMENT ID HERE>>>
curl -i http://localhost:8000/api/v1/payments/$PAYMENT_ID \
  -H "X-API-Key: luna_test"
```

---

## Pomodoro execution: 

##### First session (25m)
Project init; test task familiarization; README.md formatting.  

##### Second session (25m)
- Decided to put outbox poller within the async app itself. Queries every N seconds and makes a publish. Later can be moved away from app async loop if necessary.  
  
Doing initial docker compose and docker preparation.  

Doing dependencies besides services.

##### Third session (25m)
Move to .env
Make database and models

##### 4th session (25m)
Alembic and project structure tweaking
Docker debug. Ports and pull failure.

##### 5th session (25m)
Core app endpoints, schemas, services.
Makefile.
`__init__.py` files.
Test curl.
Add necessary instructions to README.md

##### 6th session (25m)
Manually testing endpoints.
Tweaking schemas, endpoints.

##### 7th session (25m)
Creating pytest tests.
Creating environment for tests.

##### 8th session (25m)
Changing the strategy for tests: deny everything then allow specific.
Outbox worker.

##### 9th session (25m)
Consumer:
- Webhook.
- Entry point.
- Tests

##### 10th session (25m)
Scrutinizing over consumer.

---

## TODO:

- [ ] CRITICAL: Move secrets to vault.
  - Postgres
  - RabbitMQ
- [ ] CRITICAL: Remove postgres port out of scope.
- [ ] If necessary move python into separate container for encapsulation.
- [x] .env file with necessary keys.  
  - [x] pydantic-settings since they moved it to other crate.
- [ ] Alembic and models in app/db. Make sure it won't cause any problems.
- [ ] Think critically about outbox, move if necessary.
- [ ] Check deprecation warnings.
- [x] Make test database creation automatic.
- [ ] Pytest fails to get loop scope from toml config. Fix.
- [x] Fix ugly hack for session fixture in tests and replace it with context manager.
