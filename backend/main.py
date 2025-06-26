from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    # "http://localhost:5137",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    with open(f"./uploads/{file.filename}", "wb") as f:
        f.write(contents)
    return JSONResponse(content={"filename": file.filename})

@app.post("/api/start")
async def start():
    from engine import run_match
    try:
        results = run_match()
        return JSONResponse(content={"status": "Match started successfully",
                                     "response": results})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})