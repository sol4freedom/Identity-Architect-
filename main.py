from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Union, Optional

app = FastAPI()

# --- THE DATA SHAPE ---
# This acts like a "Universal Adapter"
# It accepts text, numbers, or decimals for timezone without crashing
class UserInput(BaseModel):
    name: str
    date: str
    time: str
    city: str
    struggle: str
    # Accept anything for timezone initially
    tz: Union[float, int, str, None] = None

    # Validator 1: Clean the Timezone
    # This specifically fixes the "invalid literal for int()" error
    @validator('tz', pre=True)
    def parse_timezone(cls, v):
        if v is None: 
            return 0
        try:
            # The magic fix: Turn "-3.0" (string) -> -3.0 (float) -> -3 (int)
            return int(float(v)) 
        except:
            return 0 # Default to 0 if garbage data arrives

    # Validator 2: Clean the Date
    @validator('date', pre=True)
    def clean_date(cls, v):
        # Turns "1976-05-30T00:00:00" into "1976-05-30"
        if "T" in v:
            return v.split("T")[0]
        return v

@app.get("/")
def home():
    return {"message": "Server is awake and healthy!"}

@app.post("/calculate")
def generate_reading(data: UserInput):
    print(f"Received Data: {data}") 

    try:
        # THE REPORT GENERATOR
        # This proves the plumbing works.
        report_text = f"""
        **INTEGRATED SELF REPORT FOR {data.name.upper()}**
        
        **Theme:** {data.struggle}
        **Birth Data:** {data.date} at {data.time}
        **Timezone Used:** {data.tz}
        
        SUCCESS! The server accepted your data without crashing.
        We are now ready to install the Astrology Engine.
        """
        
        return {"report": report_text}

    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
