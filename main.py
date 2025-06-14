from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import base64
import json
import os

from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Load fake data
DATA_PATH = "../data/all_data.json"
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"{DATA_PATH} not found!")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    DATA = json.load(f)

# FastAPI app
app = FastAPI(
    title="TDS Virtual TA",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

class Link(BaseModel):
    url: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    links: List[Link]

def search_data(question: str):
    question_lower = question.lower()
    matches = []

    for item in DATA:
        text = item.get("text") or item.get("body") or ""
        if any(word in text.lower() for word in question_lower.split()):
            matches.append(item)

    matches = sorted(matches, key=lambda x: len(x.get("text", "")), reverse=True)
    top = matches[:2]

    if not top:
        return "Sorry, I don't have an answer for that yet.", []

    answer = top[0].get("text", "")[:500] + "..."

    links = []
    for m in top:
        links.append({
            "url": m.get("source") or m.get("url"),
            "text": m.get("title", "")[:80]
        })

    return answer, links

@app.post("/", response_model=AnswerResponse)
async def get_answer(req: QuestionRequest):
    if not req.question:
        raise HTTPException(status_code=400, detail="Missing question.")

    if req.image:
        try:
            base64.b64decode(req.image)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image.")

    answer_text, link_objs = search_data(req.question)
    return AnswerResponse(answer=answer_text, links=link_objs)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
