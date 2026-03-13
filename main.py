from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

try:
    oracle_document = client.files.upload(file="Integrated_Self_Reference.pdf")
    print("Oracle Manual Loaded Successfully")
except Exception as e:
    print(f"Manual Load Error: {e}")
    oracle_document = None

@app.post("/ask-oracle")
async def ask_oracle(request: Request):
    d = await request.json()
    user_question = d.get("question")
    
    if not oracle_document:
        return {"answer": "The Oracle manual failed to load. Please check GitHub."}
    
    try:
        # We are turning off strict filters so the Oracle can speak freely
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[oracle_document, "You are the Oracle. Use the manual to give a brief, mystical answer.", user_question],
            config=types.GenerateContentConfig(
                safety_settings=[types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_NONE",
                )]
            )
        )
        return {"answer": response.text}
    except Exception as e:
        print(f"AI Error: {e}")
        return {"answer": "The Oracle is currently recalibrating."}
