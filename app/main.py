from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

app = FastAPI(title="VitalPulse AI Engine", version="1.0.0")

templates = Jinja2Templates(directory="app/templates")

USER_DB: Dict[str, dict] = {}
MEMORY_LOG: List[str] = []

class ProfileInput(BaseModel):
    user_id: str = Field(default="default_user")
    age: int = Field(gt=0, lt=120)
    sex: str
    weight_kg: float = Field(gt=0)
    height_cm: float = Field(gt=0)
    activity_level: str
    goal: str
    dietary_preference: Optional[str] = "Omnivore"
    notes: Optional[str] = ""

class ChatInput(BaseModel):
    user_id: str = Field(default="default_user")
    message: str

def calculate_metrics(profile: ProfileInput) -> dict:
    if profile.sex.lower() == "male":
        bmr = (10 * profile.weight_kg) + (6.25 * profile.height_cm) - (5 * profile.age) + 5
    else:
        bmr = (10 * profile.weight_kg) + (6.25 * profile.height_cm) - (5 * profile.age) - 161

    multipliers = {"sedentary": 1.2, "moderate": 1.55, "active": 1.725}
    tdee = bmr * multipliers.get(profile.activity_level.lower(), 1.2)

    if profile.goal == "gain":
        target_calories = tdee + 400
    elif profile.goal == "lose":
        target_calories = tdee - 400
    else:
        target_calories = tdee

    protein_g = (target_calories * 0.20) / 4
    carbs_g = (target_calories * 0.50) / 4
    fat_g = (target_calories * 0.30) / 9

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "target_calories": round(target_calories, 1),
        "protein_g": round(protein_g, 1),
        "carbs_g": round(carbs_g, 1),
        "fat_g": round(fat_g, 1)
    }

@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/profile")
async def update_profile(profile: ProfileInput):
    metrics = calculate_metrics(profile)
    USER_DB[profile.user_id] = {
        "profile": profile.model_dump(),
        "metrics": metrics
    }
    
    if profile.notes:
        MEMORY_LOG.append(f"Preference note: {profile.notes}")
    if profile.dietary_preference:
        MEMORY_LOG.append(f"Diet type: {profile.dietary_preference}")

    return {
        "status": "success",
        "metrics": metrics,
        "active_memories": MEMORY_LOG
    }

@app.post("/api/chat")
async def chat_endpoint(chat: ChatInput):
    user_data = USER_DB.get(chat.user_id)
    user_msg = chat.message.lower()

    if not user_data:
        return {"response": "Please configure your body profile metrics first so I can calculate accurate targets for you."}

    metrics = user_data["metrics"]
    profile = user_data["profile"]

    if "calor" in user_msg or "target" in user_msg:
        reply = (f"Based on your profile ({profile['age']}yo, {profile['weight_kg']}kg, {profile['goal']} goal), "
                 f"your daily target is {metrics['target_calories']} kcal/day.")
    elif "protein" in user_msg or "macro" in user_msg:
        reply = (f"Your daily macro targets are: Protein: {metrics['protein_g']}g, "
                 f"Carbs: {metrics['carbs_g']}g, Fats: {metrics['fat_g']}g.")
    elif "milk" in user_msg or "iron" in user_msg:
        reply = ("Remember: Consuming high amounts of dairy (calcium) alongside plant-based iron sources "
                 "can block iron absorption. Keep dairy separate from iron-heavy meals!")
    else:
        mem_str = ", ".join(MEMORY_LOG) if MEMORY_LOG else "None"
        reply = (f"Got it! I am tracking your daily goal of {metrics['target_calories']} kcal. "
                 f"Stored Context Memories: [{mem_str}]. How can I assist your workout or nutrition plan?")

    return {"response": reply}
