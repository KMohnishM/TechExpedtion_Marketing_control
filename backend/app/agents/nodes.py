from app.agents.state import AgentState
from app.openrouter import generate_chat_response
from app.database import db
import json

async def run_agent_with_prompt(agent_name: str, system_prompt: str, state: AgentState) -> dict:
    """
    Utility function to query the LLM for a specific agent node,
    enriching the prompt with the current campaign data and anomaly status.
    """
    # Build context string
    campaigns_str = json.dumps(state.get("campaigns_data", []), indent=2)
    anomalies_str = json.dumps(state.get("anomalies", []), indent=2)
    
    context = (
        f"\n\n--- CURRENT SYSTEM DATA ---\n"
        f"CAMPAIGNS:\n{campaigns_str}\n\n"
        f"ACTIVE ANOMALIES:\n{anomalies_str}\n"
        f"---------------------------\n"
    )
    
    # Prepare chat history
    messages = [{"role": "system", "content": system_prompt + context}]
    
    # Add conversation history
    for msg in state.get("messages", []):
        messages.append(msg)
        
    # Add the current user query if it's not already in messages
    user_query = state.get("user_query", "")
    if user_query and not any(m["role"] == "user" and m["content"] == user_query for m in messages):
        messages.append({"role": "user", "content": user_query})
        
    db.set_agent_status(agent_name, "Thinking...")
    response_text = await generate_chat_response(messages)
    db.set_agent_status(agent_name, "Idle")
    
    # Check if this agent proposed any structured actions
    proposed_actions = []
    
    # Simple heuristic to extract actions suggested by the LLM
    # E.g. campaign agent says: PROPOSE_ACTION: PAUSE_CAMPAIGN C1 or PROPOSE_ACTION: ADJUST_BUDGET C2 140000
    if "PROPOSE_ACTION:" in response_text:
        lines = response_text.split("\n")
        for line in lines:
            if "PROPOSE_ACTION:" in line:
                try:
                    action_part = line.split("PROPOSE_ACTION:")[1].strip()
                    # Expecting: {"type": "pause", "campaign_id": "C1"} or similar JSON
                    action_json = json.loads(action_part)
                    proposed_actions.append(action_json)
                except Exception:
                    # Parse text-based commands as fallback
                    if "pause" in line.lower() and "c1" in line.lower():
                        proposed_actions.append({"type": "pause", "campaign_id": "C1", "campaign_name": "Summer Promo"})
                    elif "budget" in line.lower() and "c2" in line.lower():
                        proposed_actions.append({"type": "budget_change", "campaign_id": "C2", "campaign_name": "Fall Launch", "proposed_value": 140000.0, "reason": "High ROI performance"})
    
    return {
        "messages": [{"role": "assistant", "content": response_text, "sender": agent_name}],
        "trace_logs": [f"[{agent_name}] Processed query. Response generated."],
        "proposed_actions": proposed_actions
    }

async def supervisor_node(state: AgentState) -> dict:
    """
    Inspects user query and routes to the appropriate specialist agent.
    """
    user_query = state.get("user_query", "").lower()
    trace = f"[Supervisor] Analyzing user query: '{user_query}'"
    
    next_agent = "Analytics Agent" # default fallback
    
    if any(x in user_query for x in ["anomaly", "anomalies", "pixel", "outage", "fraud", "bot", "click farm", "fake"]):
        next_agent = "Anomaly Agent"
    elif any(x in user_query for x in ["budget", "bid", "pause", "resume", "activate", "change spend", "adjust"]):
        next_agent = "Campaign Agent"
    elif any(x in user_query for x in ["audience", "demographics", "gen-z", "millennials", "interest", "targeting", "segment"]):
        next_agent = "Audience Agent"
    
    db.add_log("Supervisor", f"Routing request to {next_agent}")
    
    return {
        "next_agent": next_agent,
        "trace_logs": [trace, f"[Supervisor] Decided to route request to {next_agent}"]
    }

async def analytics_agent_node(state: AgentState) -> dict:
    prompt = (
        "You are the Analytics Agent. Your job is to analyze campaign performance metrics (CTR, spend, budget, CPM, Conversions, CPC, CPA, ROI).\n"
        "Review the campaigns list provided. Summarize the overall ROI and identify which campaigns are high-performing (ROI > 2.0) and which ones are underperforming (ROI < 1.5).\n"
        "Explain how the CTR and conversions compare across different marketing channels (Instagram Ads, Google Search, LinkedIn Ads, GDN Retargeting).\n"
        "Keep your tone highly professional, analytical, and write clear summaries with markdown tables where applicable."
    )
    return await run_agent_with_prompt("Analytics Agent", prompt, state)

async def campaign_agent_node(state: AgentState) -> dict:
    prompt = (
        "You are the Campaign Agent. Your job is to tune campaigns, manage budgets, adjust bids, and change campaign statuses.\n"
        "Review the current campaigns. If any active campaign has a poor ROI (e.g. C3 Re-engagement has 0.9x ROI), suggest pausing it or shifting budget.\n"
        "If a campaign is performing very well (e.g. C2 Fall Launch has 2.8x ROI), propose increasing its budget.\n"
        "Crucially, if you want to propose a concrete action that the user can click a button to execute, you MUST include a line in this exact format:\n"
        "PROPOSE_ACTION: {\"type\": \"budget_change\", \"campaign_id\": \"C2\", \"campaign_name\": \"Fall Launch - Electronics\", \"proposed_value\": 140000.0, \"reason\": \"Maximize conversion on high ROI channel\"}\n"
        "Or if pausing:\n"
        "PROPOSE_ACTION: {\"type\": \"pause\", \"campaign_id\": \"C3\", \"campaign_name\": \"Re-engagement - Cart Abandonment\"}\n"
        "Use markdown to format your response and explain the rationale behind your suggestions."
    )
    return await run_agent_with_prompt("Campaign Agent", prompt, state)

async def audience_agent_node(state: AgentState) -> dict:
    prompt = (
        "You are the Audience Agent. Your job is to analyze target demographics, interests, and search intents to identify new segments and suggest targeting expansions.\n"
        "Look at the campaigns and their target demographics. Recommend lookalike segments or demographic adjustments.\n"
        "Explain WHY you are suggesting these changes. For example, 'For Instagram ads, our Gen-Z CTR is 2.4%, showing high resonance, while older Millennials have ad fatigue, so we should narrow target age to 18-28 and build a 1% lookalike audience of checkout buyers.'\n"
        "Format your answer with bullet points and clear, easy-to-read sections."
    )
    return await run_agent_with_prompt("Audience Agent", prompt, state)

async def anomaly_agent_node(state: AgentState) -> dict:
    prompt = (
        "You are the Anomaly Agent. Your job is to observe system health, identify active anomalies (click fraud, tracking pixel outages, sudden CTR spikes, budget drains), and provide solutions.\n"
        "Explain the active anomalies (e.g., A1 is click farm fraud on Summer Promo Apparel). Detail what indicators (CTR spike to 14.5% with 0 conversions) led to this conclusion.\n"
        "Suggest mitigations. For example, explain how deploying an IP blocklist will exclude fraud while keeping genuine customer traffic.\n"
        "Structure your response with clear headings: Status, Diagnosis, Impact, and Resolution Plan."
    )
    return await run_agent_with_prompt("Anomaly Agent", prompt, state)
