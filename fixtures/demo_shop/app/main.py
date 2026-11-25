from fastapi import FastAPI

from app.routes import account, admin, attachments, auth, debug, downloads, orders, products, tickets, ui, widgets

app = FastAPI(title="Lumen Goods API")
for router in (auth, products, orders, tickets, admin, downloads, attachments, account, debug, widgets, ui):
    app.include_router(router.router)
