# Тестовое задание для обработчика платежей

Микросервис для асинхронной обработки платежей.

Принимает запросы на оплату, обрабатывает их через эмулированный платёжный шлюз и уведомляет клиента о результате через webhook.

---

## Быстрый старт

##### База данных и миграция:
```bash
make up        # поднимает postgres и rabbitmq
make migrate   # применяет миграции
```

##### Создание новой миграции:
```bash
make revision m="Description for new migration"
```

##### Запуск консьюмера и приложения в отдельных терминалах:
**Первый:**
```bash
make run
```

**Второй:**
```bash
make consumer  # запускает обработчик очереди (отдельный терминал)
```

##### Запустить сразу и консьюмер поверх RMQ и сам микросервис:
```bash
make run_both
```
**NOTE:** По умолчанию запускается на порту 8000.

---

## Архитектура

**ОПИСАНА ПОДРОБНО В DOCS/ARCHITECTURE.md**

---

## Конфигурация

## Конфигурация

Все параметры задаются через `.env`. Пример в `.env.example`.

`ENV` — окружение, `DEV` или `PROD`
`POSTGRES_HOST` — хост PostgreSQL
`POSTGRES_PORT` — порт PostgreSQL (По умолчанию: 5432)
`POSTGRES_DB` — имя базы данных
`POSTGRES_USER` — пользователь БД
`POSTGRES_PASSWORD` — пароль БД
`RABBITMQ_HOST` — хост RabbitMQ
`RABBITMQ_PORT` — порт RabbitMQ (По умолчанию: 5672)
`RABBITMQ_USER` — пользователь RabbitMQ
`RABBITMQ_PASSWORD` — пароль RabbitMQ
`API_KEY` — статический ключ авторизации
`SERVICE_TITLE` — название сервиса
`OUTBOX_POLL_INTERVAL` — интервал поллинга outbox в секундах (По умолчанию: 1 секунда)
`WEBHOOK_RETRY_ATTEMPTS` — количество попыток доставки webhook (По умолчанию: 5)
`WEBHOOK_RETRY_BASE_DELAY` — начальная задержка retry в секундах (По умолчанию: 1 секунда)
`WEBHOOK_TIMEOUT` - время ожидания outbox вебхука. (По умолчанию: 10 секунд)
`LOG_LEVEL` — уровень логирования (По умолчанию: INFO)

---

## API

Все эндпоинты требуют заголовок `X-API-Key`.

### POST /api/v1/payments

Создание платежа.

Заголовки:
- `X-API-Key: <key>` — обязательный
- `Idempotency-Key: <key>` — обязательный, уникальная строка

Тело запроса:
```json
{
  "amount": "100.00",
  "currency": "RUB",
  "description": "оплата заказа номер 100500",
  "metadata": {"order_id": "100500"},
  "webhook_url": "https://example.com/webhook"
}
```

Ответ `202 Accepted`:
```json
{
  "id": "uuid",
  "status": "pending",
  "amount": "100.00",
  "currency": "RUB",
  "description": "оплата заказа номер 100500",
  "metadata": {"order_id": "100500"},
  "webhook_url": "https://example.com/webhook",
  "created_at": "2026-01-01T00:00:00Z",
  "processed_at": null
}
```

### GET /api/v1/payments/{payment_id}

Получение информации о платеже.

Ответ `200 OK` — то же тело что при создании, с актуальным `status` и `processed_at`.

---

## Примеры curl

```bash
# создание платежа
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

# получение платежа
PAYMENT_ID=your-payment-id-here
curl -i http://localhost:8000/api/v1/payments/$PAYMENT_ID \
  -H "X-API-Key: luna_test"
```

### Polling статуса платежа

Поскольку платёж обрабатывается асинхронно, сразу после создания он находится в статусе `pending`. Для получения финального статуса необходимо периодически опрашивать GET эндпоинт:

```bash
PAYMENT_ID=your-payment-id-here

while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/payments/$PAYMENT_ID \
    -H "X-API-Key: luna_test" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "status: $STATUS"
  if [ "$STATUS" != "pending" ]; then
    break
  fi
  sleep 2
done
```

Ждёт пока статус сменится с `pending` на `succeeded` или `failed`.

---

## Тесты

```bash
make test
```

Тестовая БД создаётся автоматически при первом запуске тестов.

---

## Tech Stack

- Python 3.14
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async)
- PostgreSQL 17
- RabbitMQ 3.12 (with FastStream)
- Alembic
- Docker + docker-compose
