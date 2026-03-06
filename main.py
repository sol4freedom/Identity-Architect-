from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import os
import logging

app = FastAPI()
logger = logging.getLogger("uvicorn")

# THE CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# THE ORACLE CLIENT
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.post("/ask-oracle")
async def ask_oracle(request: Request):
    d = await request.json()
    user_question = d.get("question")
    
    try:
        # Uploads your Master Reference Book
        oracle_document = client.files.upload(file="Integrated_Self_Reference.pdf")
        
        # Generates the personalized response
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[oracle_document, "You are the Oracle for The Integrated Self. Answer using the provided PDF.", user_question]
        )
        return {"answer": response.text}
    except Exception as e:
        logger.error(f"Oracle Error: {e}")
        return {"answer": "The Oracle is currently recalibrating. Please try again in a moment."}


