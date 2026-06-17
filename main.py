import os
import random
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload

# --- DATENBANK SETUP ---
# SQLite ist eine einfache Datei-Datenbank, perfekt für den Start
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/mealplan.db")

# Sicherstellen, dass das Datenverzeichnis existiert (wichtig für Docker Volumes)
db_file_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", "")
db_dir = os.path.dirname(db_file_path)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir)

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definition unserer Tabelle für Lieblingsgerichte
class Dish(Base):
    __tablename__ = "dishes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    # Verknüpfung zum Wochenplan
    planned_meals = relationship("MealPlan", back_populates="dish")
    # Verknüpfung zu den Zutaten (Kaskadierendes Löschen)
    ingredients = relationship("Ingredient", back_populates="dish", cascade="all, delete-orphan")

# Neue Tabelle für Zutaten
class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    amount = Column(String)  # z.B. "200g" oder "1 Bund"
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"))
    
    dish = relationship("Dish", back_populates="ingredients")

# Neue Tabelle für den Wochenplan
class MealPlan(Base):
    __tablename__ = "meal_plan"
    id = Column(Integer, primary_key=True, index=True)
    day = Column(String, unique=True, index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="SET NULL"), nullable=True)
    
    dish = relationship("Dish", back_populates="planned_meals")

# Erstellt die Datenbank-Datei, falls sie noch nicht existiert
Base.metadata.create_all(bind=engine)

# Initialisierung der Wochentage, falls sie noch nicht existieren
def init_db():
    db = SessionLocal()
    days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    for day_name in days:
        existing = db.query(MealPlan).filter(MealPlan.day == day_name).first()
        if not existing:
            new_day = MealPlan(day=day_name)
            db.add(new_day)
    db.commit()
    db.close()

init_db()

# --- APP SETUP ---
app = FastAPI(title="Essensplaner")
templates = Jinja2Templates(directory="templates")

# Hilfsfunktion, um eine Datenbank-Verbindung zu bekommen
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROUTEN (Die Wege im Browser) ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, expand_id: int = None):
    db = SessionLocal()
    # Eager Loading der Zutaten, damit sie im Template verfügbar sind
    dishes = db.query(Dish).options(joinedload(Dish.ingredients)).all()
    # Wochenplan laden (inklusive der verknüpften Gerichte)
    weekly_plan = db.query(MealPlan).all()
    db.close()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "dishes": dishes, 
            "weekly_plan": weekly_plan,
            "expand_id": expand_id
        },
    )

@app.post("/add-ingredient")
async def add_ingredient(dish_id: int = Form(...), name: str = Form(...), amount: str = Form(...)):
    if name:
        db = SessionLocal()
        new_ingredient = Ingredient(name=name, amount=amount, dish_id=dish_id)
        db.add(new_ingredient)
        db.commit()
        db.close()
    return RedirectResponse(url=f"/?expand_id={dish_id}", status_code=303)

@app.post("/delete-ingredient/{ingredient_id}")
async def delete_ingredient(ingredient_id: int, dish_id: int = Form(...)):
    db = SessionLocal()
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if ingredient:
        db.delete(ingredient)
        db.commit()
    db.close()
    return RedirectResponse(url=f"/?expand_id={dish_id}", status_code=303)

@app.post("/update-plan")
async def update_plan(day: str = Form(...), dish_id: str = Form(...)):
    db = SessionLocal()
    # dish_id ist "none" wenn das Feld geleert wurde
    actual_dish_id = int(dish_id) if dish_id != "none" else None
    
    plan_entry = db.query(MealPlan).filter(MealPlan.day == day).first()
    if plan_entry:
        plan_entry.dish_id = actual_dish_id
        db.commit()
    db.close()
    return RedirectResponse(url="/", status_code=303)

@app.post("/add-dish")
async def add_dish(name: str = Form(...)):
    if name:
        db = SessionLocal()
        # Prüfen, ob das Gericht schon existiert
        existing = db.query(Dish).filter(Dish.name == name).first()
        if not existing:
            new_dish = Dish(name=name)
            db.add(new_dish)
            db.commit()
        db.close()
    # Nach dem Speichern leiten wir den User zurück zur Startseite
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete-dish/{dish_id}")
async def delete_dish(dish_id: int):
    db = SessionLocal()
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if dish:
        db.delete(dish)
        db.commit()
    db.close()
    return RedirectResponse(url="/", status_code=303)

@app.get("/random-dish", response_class=HTMLResponse)
async def random_dish(request: Request):
    db = SessionLocal()
    dishes = db.query(Dish).options(joinedload(Dish.ingredients)).all()
    weekly_plan = db.query(MealPlan).all()
    suggestion = random.choice(dishes) if dishes else None
    db.close()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"dishes": dishes, "suggestion": suggestion, "weekly_plan": weekly_plan},
    )
