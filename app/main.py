import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="VitalPulse")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

class ProfileData(BaseModel):
    user_id: str
    age: int
    sex: str
    weight_kg: float
    height_cm: float
    activity_level: str
    goal: str
    notes: str | None = None

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/profile")
async def calculate_profile(data: ProfileData):
    if data.sex.lower() == "male":
        bmr = 88.362 + (13.397 * data.weight_kg) + (4.799 * data.height_cm) - (5.677 * data.age)
    else:
        bmr = 447.593 + (9.247 * data.weight_kg) + (3.098 * data.height_cm) - (4.330 * data.age)

    activity_multipliers = {
        "sedentary": 1.2,
        "moderate": 1.55,
        "active": 1.725
    }
    tdee = bmr * activity_multipliers.get(data.activity_level, 1.2)

    if data.goal == "gain":
        target_calories = round(tdee + 400)
    elif data.goal == "lose":
        target_calories = round(tdee - 400)
    else:
        target_calories = round(tdee)

    protein_g = round(data.weight_kg * 2.0)
    carbs_g = round((target_calories * 0.5) / 4)

    return {
        "status": "success",
        "metrics": {
            "bmr": round(bmr),
            "target_calories": target_calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g
        }
    }

@app.post("/api/chat")
async def chat_endpoint(data: ChatRequest):
    return {
        "response": f"VitalPulse Assistant received your message: '{data.message}'. Update your body metrics to keep targets synchronized!"
    }
