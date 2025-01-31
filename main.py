from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from src.services.limiter import limiter

# Імпортуємо маршрути
from src.api import contacts, utils, auth, users

app = FastAPI()

origins = ["*"]
# Додаємо CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Дозволяємо запити з цього домену
    allow_credentials=True,
    allow_methods=["*"],  # Дозволяємо всі методи (GET, POST, PUT, DELETE тощо)
    allow_headers=["*"],  # Дозволяємо всі заголовки
)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
    )

# Підключаємо маршрути
app.include_router(contacts.router, prefix="/api")
app.include_router(utils.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")

# Функція для застосування міграцій
async def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

# Запуск міграцій при старті додатка
@app.on_event("startup")
async def startup_event():
    await run_migrations()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)