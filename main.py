import os
import json
from urllib.request import Request
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from auth.router import auth_router
from victron.data.router import data_router
from victron.router import ve_router
from dotenv import load_dotenv
from pathlib import Path

# from data.np_data_fetch import parse_nord_pool_data


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

def include_routers(app):
    app.include_router(auth_router)
    app.include_router(data_router)
    app.include_router(ve_router)

def start_application():
    app = FastAPI(title=os.getenv("APP_NAME"), version=os.getenv("APP_VERSION"))
    include_routers(app)
    return app

app = start_application()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.route("/main")
def main_route(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.route("/profile")
def main_route(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.route("/login")
def main_route(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.route("/register")
def main_route(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.route("/table")
def main_route(request: Request):
    return templates.TemplateResponse("table.html", {"request": request})