from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import os

app = FastAPI()

# THE CORS FIX - Allows Wix to communicate with Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# THE BRAIN - Authenticates with your API key
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.post("/ask-oracle")
async def ask_oracle(request: Request):
    d = await request.json()
    user_question = d.get("question")
    
    try:
        # Uploads your Master Reference Book
        oracle_document = client.files.upload(file="Integrated_Self_Reference.pdf")
        
        # Personalized response generation
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[oracle_document, "You are the Oracle for The Integrated Self.", user_question]
        )
        return {"answer": response.text}
    except Exception as e:
        return {"answer": "The Oracle is currently recalibrating."}
