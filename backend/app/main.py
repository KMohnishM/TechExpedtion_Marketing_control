from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.database import db
from app.agents.graph import agent_graph

app = FastAPI(title="Marketing Control Tower API", version="1.0.0")

# Enable CORS for the frontend Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this. For hackathon, allow all.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Schemas
class StatusUpdate(BaseModel):
    status: str

class BudgetUpdate(BaseModel):
    budget: float

class MitigationRequest(BaseModel):
    mitigation_id: str

class AnomalyTrigger(BaseModel):
    campaign_id: str
    anomaly_type: str

class ChatMessage(BaseModel):
    role: str
    content: str
    sender: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Marketing Control Tower Backend is healthy."}

@app.get("/api/dashboard")
def get_dashboard():
    """
    Returns campaign details, historical chart data, active/resolved anomalies,
    live audit logs, and status information of each agent.
    """
    return db.get_dashboard_data()

@app.post("/api/campaigns/{cid}/status")
def update_campaign_status(cid: str, data: StatusUpdate):
    if data.status not in ["Active", "Paused"]:
        raise HTTPException(status_code=400, detail="Invalid campaign status. Must be 'Active' or 'Paused'")
    success = db.update_campaign_status(cid, data.status)
    if not success:
        raise HTTPException(status_code=404, detail=f"Campaign {cid} not found")
    return {"status": "success", "message": f"Campaign {cid} status updated to {data.status}"}

@app.post("/api/campaigns/{cid}/budget")
def update_campaign_budget(cid: str, data: BudgetUpdate):
    if data.budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be greater than 0")
    success = db.update_campaign_budget(cid, data.budget)
    if not success:
        raise HTTPException(status_code=404, detail=f"Campaign {cid} not found")
    return {"status": "success", "message": f"Campaign {cid} budget updated to ${data.budget:,.2f}"}

@app.post("/api/anomalies/{aid}/resolve")
def resolve_anomaly(aid: str, data: MitigationRequest):
    success = db.resolve_anomaly(aid, data.mitigation_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Anomaly {aid} or Mitigation {data.mitigation_id} not found")
    return {"status": "success", "message": f"Mitigation applied to Anomaly {aid}."}

@app.post("/api/anomalies/trigger")
def trigger_anomaly(data: AnomalyTrigger):
    """
    Endpoint to trigger anomalies dynamically for testing/demonstration.
    """
    aid = db.trigger_anomaly(data.campaign_id, data.anomaly_type)
    return {"status": "success", "anomaly_id": aid, "message": f"Triggered {data.anomaly_type} anomaly on campaign {data.campaign_id}"}

@app.post("/api/chat")
async def chat_with_agents(request: ChatRequest):
    """
    Runs the multi-agent system (LangGraph workflow) on the user's message.
    It passes the current state of campaigns and active anomalies as context.
    """
    user_query = request.message
    
    # Format chat history for LangGraph state
    history_list = []
    for msg in request.history:
        history_list.append({"role": msg.role, "content": msg.content})
        
    # Get current DB snapshot to feed into the agent state context
    dash = db.get_dashboard_data()
    campaigns_snapshot = dash["campaigns"]
    anomalies_snapshot = dash["anomalies"]
    
    # Initialize LangGraph state input
    initial_state = {
        "messages": history_list,
        "user_query": user_query,
        "current_agent": "Supervisor",
        "next_agent": "",
        "campaigns_data": campaigns_snapshot,
        "anomalies": anomalies_snapshot,
        "trace_logs": [f"[Supervisor] Received message: '{user_query}'"],
        "proposed_actions": []
    }
    
    try:
        # Execute the LangGraph compile workflow
        final_state = await agent_graph.ainvoke(initial_state)
        
        # Extract the assistant's final response and sender
        last_message = final_state["messages"][-1]
        response_text = last_message["content"]
        sender = last_message.get("sender", final_state.get("next_agent", "Agent"))
        
        # Log agent response in the database audit logs
        db.add_log(sender, f"Responded to query: '{user_query[:30]}...'")
        
        return {
            "response": response_text,
            "sender": sender,
            "trace_logs": final_state.get("trace_logs", []),
            "proposed_actions": final_state.get("proposed_actions", [])
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        db.add_log("System Error", f"Agent execution failed: {str(e)}")
        # Fallback response
        return {
            "response": f"I encountered an error running the agent workflow: {str(e)}\n\nRunning in local mock mode instead.",
            "sender": "System",
            "trace_logs": [f"[System Error] {str(e)}", error_trace],
            "proposed_actions": []
        }
