from fastapi import FastAPI

from app.routes import admin, auth, calc, debug, files, invoices, profile, ui

app = FastAPI(title="Mini Shop API")
app.include_router(auth.router)
app.include_router(invoices.router)
app.include_router(admin.router)
app.include_router(files.router)
app.include_router(profile.router)
app.include_router(debug.router)
app.include_router(calc.router)
app.include_router(ui.router)
