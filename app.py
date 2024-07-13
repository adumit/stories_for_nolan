from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from anthropic import Anthropic

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://6691ded0dc51f382e99bc852--stories-for-nolan.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StoryRequest(BaseModel):
    prompt: str
    password: str


@app.post("/generate_story")
async def generate_story(request: StoryRequest):
    if request.password != os.environ["PASSWORD"]:
        return {"error": "Invalid password"}
    response = get_story(request.prompt)
    return {"story": response.strip()}



def get_story(prompt: str) -> str:
    return "This is a test story."


def get_anthropic_response(sys_message, human_msg, model) -> str:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        max_tokens=4000,
        system=sys_message.content,
        messages=[{"role": "user", "content": human_msg.content}],
        model=model,
    )
    return message.content[0].text
