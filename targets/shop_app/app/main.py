from fastapi import FastAPI

from .routes import admin, auth, orders, receipts, search

app = FastAPI(title="Mini Shop")

for module in (auth, search, orders, receipts, admin):
    app.include_router(module.router)
