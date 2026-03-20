from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import os

app = FastAPI()

# SECURITY: This allows your Wix site to talk to this Render server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Gemini Client using the key from your Render Environment
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# --- PRE-LOAD THE MANUAL (The "Direct Path" Fix) ---
try:
    # This finds the exact folder on Render where your files are stored
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "Integrated_Self_Reference.pdf")
    
    print(f"Searching for manual at: {file_path}")
    
    if os.path.exists(file_path):
        # Changed 'path' to 'file' to match the new library requirements
        oracle_document = client.files.upload(file=file_path)
        print("Oracle Manual Loaded Successfully")
    else:
        print(f"CRITICAL: File not found at {file_path}")
        oracle_document = None
except Exception as e:
    print(f"Manual Load Error: {e}")
    oracle_document = None

@app.post("/ask-oracle")
async def ask_oracle(request: Request):
    d = await request.json()
    user_question = d.get("question")
    
    # Safety check: if the manual didn't load, tell the user why
    if not oracle_document:
        return {"answer": "The Oracle cannot find its manual. Check the Render logs for the file path."}
    
    try:
        # Generate the response using your PDF as the only source of truth
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                oracle_document, 
                "You are the Oracle for 'The Integrated Self'. Use the manual to give a profound, mystical, and direct answer.", 
                user_question
            ]
        )
        return {"answer": response.text}
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return {"answer": "The Oracle is currently recalibrating."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
