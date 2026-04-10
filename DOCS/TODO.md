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
- [ ] Заменить поллер в виде таска на Debezium.  
  - [ ] Убрать заметку из файла ARCHITECTURE.md  
- [ ] Различные конфиги для DEV и PROD, чтобы можно было менять одним параметром в .env
- [ ] Генерация API-KEY и сессии.  
- [ ] Заменить параметры в докере на переменные среды.
