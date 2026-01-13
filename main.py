# 1. IMPORTS: Bringing in the necessary tools
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # <--- CRITICAL: The Security Pass
from pydantic import BaseModel, validator
from typing import Union, Optional

# 2. APP SETUP: Starting the server
app = FastAPI()

# 3. SECURITY (CORS): This unlocks the door for Wix
# Without this, the browser blocks the connection and says "Failed to Fetch"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # "*" means "Let anyone in" (Wix, Google, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Allow POST, GET, etc.
    allow_headers=["*"],
)

# 4. DATA MODEL: This is the "Shape" of the data we expect from Wix
class UserInput(BaseModel):
    name: str
    date: str
    time: str
    city: str
    struggle: str
    # "Union" means: We accept a Number, a Decimal, OR Text. We don't care.
    tz: Union[float, int, str, None] = None 

    # 5. DATA CLEANER: The "Timezone Fixer"
    # This runs BEFORE the code tries to do any math.
    @validator('tz', pre=True)
    def parse_timezone(cls, v):
        if v is None: return 0 # If empty, default to 0
        try:
            # Force it to be a simple Integer (removes decimals, quotes, etc.)
            return int(float(v)) 
        except:
            return 0 # If garbage, default to 0

    # 6. DATA CLEANER: The "Date Fixer"
    # Fixes "1976-05-30T00:00:00" -> "1976-05-30"
    @validator('date', pre=True)
    def clean_date(cls, v):
        if "T" in v:
            return v.split("T")[0]
        return v

# 7. HEALTH CHECK: Verifies the server is alive
@app.get("/")
def home():
    return {"message": "Server is Online"}

# 8. THE CALCULATOR: Receiving the POST request from Wix
@app.post("/calculate")
def generate_reading(data: UserInput):
    print(f"Received Data: {data}") # Logs the clean data

    # 9. SUCCESS RESPONSE
    return {
        "report": f"SUCCESS! Connection Established.\nUser: {data.name}\nDate: {data.date}\nTimezone: {data.tz}\nTheme: {data.struggle}"
    }
