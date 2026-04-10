from fastapi import FastAPI

from app.api.v1.payments import router as payments_router

app = FastAPI(title="Luna Payment Service")
app.include_router(payments_router)
