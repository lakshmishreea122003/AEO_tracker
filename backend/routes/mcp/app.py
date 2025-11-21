# app/main.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from anthropic import AsyncAnthropic

from routes.mcp.models import ChatRequest, ChatResponse

from claude import TOOLS, TOOL_IMPLS

app = FastAPI()
client = AsyncAnthropic(api_key="")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    user_msg = req.message
    
    # Initialize conversation history
    if req.conversation_history is None:
        messages = []
    else:
        # Filter out any system messages
        messages = [msg for msg in req.conversation_history if msg.get("role") != "system"]
    
    # Add user message
    messages.append({"role": "user", "content": user_msg})
    
    # System prompt (separate parameter, not in messages!)
    system_prompt = (
        "You are a helpful assistant. "
        "You can call tools to search the web or scrape pages. "
        "Use `serp` for Google/SERP/fresh web info. "
        "Use `web_page_results` when the user gives a URL or asks to read/scrape a page."
    )
    
    print(f"\n{'='*60}")
    print(f"💬 User: {user_msg}")
    print(f"🛠️  Available tools: {[t['name'] for t in TOOLS]}")
    
    # First call with tools
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",  # Using latest model
        max_tokens=4096,
        system=system_prompt,  # ✅ System as separate parameter
        tools=TOOLS,
        messages=messages
    )
    
    # Handle tool calls in a loop (agentic behavior)
    iteration = 0
    while response.stop_reason == "tool_use":
        iteration += 1
        print(f"\n🔄 Iteration {iteration}: Claude wants to use tools")
        
        # Add assistant's response (with tool_use blocks) to history
        messages.append({
            "role": "assistant",
            "content": response.content
        })
        
        # Execute all tool calls
        tool_results = []
        for content_block in response.content:
            if hasattr(content_block, "type") and content_block.type == "tool_use":
                tool_name = content_block.name
                tool_args = content_block.input
                tool_use_id = content_block.id
                
                print(f"  🔧 Tool: {tool_name}")
                print(f"  📝 Input: {tool_args}")
                
                # Execute the tool
                tool_fn = TOOL_IMPLS.get(tool_name)
                if tool_fn is None:
                    result = {"error": f"Unknown tool: {tool_name}"}
                else:
                    try:
                        result = await tool_fn(**tool_args)
                    except Exception as e:
                        result = {"error": str(e)}
                
                print(f"  ✅ Result: {str(result)[:200]}...")
                
                # Add tool result
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": str(result)  # Convert to string for API
                })
        
        # Add tool results to messages (as user role!)
        messages.append({
            "role": "user",  # ✅ Tool results go as "user" role
            "content": tool_results
        })
        
        # Continue conversation with tool results
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages
        )
    
    # Extract final text response
    final_text = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            final_text += block.text
    
    print(f"\n🤖 Claude: {final_text}")
    print(f"{'='*60}\n")
    
    return ChatResponse(
        answer=final_text,
        tool_calls_made=iteration,
        conversation_history=messages
    )

@app.get("/")
async def root():
    return {
        "message": "Claude Tool Calling API",
        "available_tools": [tool["name"] for tool in TOOLS]
    }

@app.get("/tools")
async def list_tools():
    return {"tools": TOOLS}
