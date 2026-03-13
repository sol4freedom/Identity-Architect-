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

# Initialize the client with the key
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# PRE-LOAD THE MANUAL
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
        return {"answer": "The Oracle cannot find its manual. Check the PDF on GitHub."}
    
    try:
        # We are using a very simple prompt to avoid AI crashes
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                oracle_document, 
                "You are the Oracle for The Integrated Self. Use the manual to give a brief, mystical answer.", 
                user_question
            ]
        )
        return {"answer": response.text}
    except Exception as e:
        # If this fails, the error will show in your Render Logs!
        print(f"AI Error: {e}")
        return {"answer": "The Oracle is currently recalibrating."}
