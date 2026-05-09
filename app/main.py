from dotenv import load_dotenv
load_dotenv()  # must run before any module that reads os.getenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, Base
from app.routes import auth
from app.routes import query
from app.models import user, product, order  # registers tables with SQLAlchemy
from app.routes import user as user_routes
from app.routes import product as product_routes
from app.routes import order as order_routes

app = FastAPI(title="Analtix")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to your frontend URL before real production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(user_routes.router)
app.include_router(product_routes.router)
app.include_router(order_routes.router)
app.include_router(auth.router)
app.include_router(query.router)


@app.get("/")
def root():
    return {"message": "Analtix API is running", "docs": "/docs"}
