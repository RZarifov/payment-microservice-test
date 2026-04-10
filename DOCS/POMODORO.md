# 26y-04m-10d: 

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
Splitting README into multiple files.
Refining README.md.

##### 11th session (25m)
Continuing with readme.
Explaining architecture.

##### 12th session (25m)
Continuing with architecture.
