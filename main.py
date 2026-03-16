from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import os

app = FastAPI()

# Allows Wix to talk to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the AI Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# PRE-LOAD THE MANUAL (The step that makes it "Integrated Self")
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
        return {"answer": "The Oracle manual is missing. Check your GitHub files."}
    
    try:
        # Simple, working generation logic
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                oracle_document, 
                "You are the Oracle for The Integrated Self. Use the provided manual to answer the user's question with depth and clarity.", 
                user_question
            ]
        )
        return {"answer": response.text}
    except Exception as e:
        print(f"AI Error: {e}")
        return {"answer": "The Oracle is currently recalibrating."}

