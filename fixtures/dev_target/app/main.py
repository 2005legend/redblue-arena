from fastapi import FastAPI

from app.routes import admin, auth, files, invoices

app = FastAPI(title="Mini Shop API")
app.include_router(auth.router)
app.include_router(invoices.router)
app.include_router(admin.router)
app.include_router(files.router)
