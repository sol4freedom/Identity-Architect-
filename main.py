from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 1. PRE-LOAD THE BOOK (Do this outside the function)
# This ensures the Oracle already has the manual open before the question arrives
try:
    oracle_document = client.files.upload(file="Integrated_Self_Reference.pdf")
    print("Oracle Manual Loaded Successfully")
except Exception as e:
    print(f"Error loading manual: {e}")
    oracle_document = None

@app.post("/ask-oracle")
async def ask_oracle(request: Request):
    d = await request.json()
    user_question = d.get("question")
    
    if not oracle_document:
        return {"answer": "The Oracle cannot find its reference manual. Check GitHub for the PDF."}
    
    try:
        # 2. GENERATE RESPONSE (The actual brain work)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[oracle_document, "You are the Oracle for The Integrated Self. Use the provided PDF to answer profoundly.", user_question]
        )
        return {"answer": response.text}
    except Exception as e:
        # This will now tell us the REAL error in the Render logs
        print(f"Generation Error: {e}")
        return {"answer": "The Oracle is currently recalibrating."}

