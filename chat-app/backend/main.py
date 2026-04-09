import os
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client with NVIDIA base URL
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY", "$NVIDIA_API_KEY") # Replace with your actual key or use env
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "nvidia/nemotron-3-super-120b-a12b"

async def chat_stream_generator(messages: List[Message]):
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b",
            messages=[m.dict() for m in messages],
            temperature=1,
            top_p=0.95,
            max_tokens=16384,
            extra_body={
                "chat_template_kwargs": {"enable_thinking": True},
                "reasoning_budget": 16384
            },
            stream=True
        )

        for chunk in completion:
            if not chunk.choices:
                continue
            
            delta = chunk.choices[0].delta
            
            # Extract reasoning and content
            reasoning = getattr(delta, "reasoning_content", None)
            content = delta.content
            
            payload = {}
            if reasoning:
                payload["reasoning"] = reasoning
            if content is not None:
                payload["content"] = content
                
            if payload:
                yield f"data: {json.dumps(payload)}\n\n"
            
        yield "data: [DONE]\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(chat_stream_generator(request.messages), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
