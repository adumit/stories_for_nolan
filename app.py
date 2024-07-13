import os
import re

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from anthropic import Anthropic
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

app = FastAPI()
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://storiesfornolan.xyz",
        "https://www.storiesfornolan.xyz",
        "http://storiesfornolan.xyz",
        "http://www.storiesfornolan.xyz",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StoryRequest(BaseModel):
    prompt: str
    password: str
    includeMom: bool = False
    includeDad: bool = False


@app.post("/generate_story")
async def generate_story(request: StoryRequest):
    if request.password != os.environ["PASSWORD"]:
        return {"error": "Invalid password"}
    response = get_story(request.prompt, request.includeMom, request.includeDad)
    return {"story": response.strip()}


STORY_SYS_MESSAGE = """
<persona>
You're an expert child's story teller. You write short, heartfelt stories that are perfect for bedtime. They always follow the hero's joruney structure and have a moral at the end. You are adaptable to the prompt that you are given and can include or exclude characters as needed.
</persona>
<task>
Your task is to write a 500-word story for a child based on the given prompt. You may also be asked to include the child's mom or dad in the story and should do so if asked. If not prompted to include the mom or dad, you should not include them in the story.

The hero's journey in your story should include one main problem that the hero faces and overcomes. The story should have a short moral at the end that is appropriate for a child. The story should be quite simple and use straightforward language.
</task>
<response_format>
When you respond, first think through a brief outline of your story in a <thinking> tag. Then, write the story in a <story> tag.

Here is the response format:
<thinking>
Your outline of the story.
</thinking>
<story>
Your story.
</story>
</response_format>
"""

STORY_HUMAN_MESSAGE = """
<prompt>
Write a story based on the following prompt:
{prompt}
</prompt>
"""

def get_story(prompt: str, include_mom: bool, include_dad: bool) -> str:
    sys_message = STORY_SYS_MESSAGE
    human_msg = STORY_HUMAN_MESSAGE.format(prompt=prompt)
    if include_mom:
        human_msg += "<include_mom>You should include the child's mom in the story.</include_mom>"
    if include_dad:
        human_msg += "<include_dad>You should include the child's dad in the story.</include_dad>"
    story_response = get_anthropic_response(sys_message, human_msg)
    try:
        return re.findall(r"<story>(.*?)</story>", story_response, flags=re.DOTALL)[0].strip()
    except IndexError:
        logger.error(f"Anthropic response couldn't extract the story:\n{story_response}")
        return "I'm sorry, I couldn't generate a story for you. Please try again."


def get_anthropic_response(sys_message, human_msg) -> str:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        max_tokens=4000,
        system=sys_message,
        messages=[{"role": "user", "content": human_msg}],
        model=os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
    )
    return message.content[0].text
