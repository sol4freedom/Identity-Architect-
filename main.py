from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import os

app = FastAPI()

# This is the "Security Guard" that lets Wix talk to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connects to your NEW Gemini API Key (Make sure to update this in Render!)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# PRE-LOAD YOUR PDF
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
        return {"answer": "The Oracle cannot find its manual. Please check the PDF on GitHub."}
    
    try:
        # The simple prompt your buddy suggested
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                oracle_document, 
                "You are the Oracle for 'The Integrated Self'. Use the provided manual to answer the user's question profoundly and practically.", 
                user_question
            ]
        )
        return {"answer": response.text}
    except Exception as e:
        print(f"AI Error: {e}")
        return {"answer": "The Oracle is currently recalibrating."}
