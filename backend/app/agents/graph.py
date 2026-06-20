from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes import (
    supervisor_node,
    analytics_agent_node,
    campaign_agent_node,
    audience_agent_node,
    anomaly_agent_node
)

def build_agent_graph():
    # Initialize the graph with state schema
    workflow = StateGraph(AgentState)
    
    # Register nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("analytics_agent", analytics_agent_node)
    workflow.add_node("campaign_agent", campaign_agent_node)
    workflow.add_node("audience_agent", audience_agent_node)
    workflow.add_node("anomaly_agent", anomaly_agent_node)
    
    # Set the starting node
    workflow.set_entry_point("supervisor")
    
    # Map out the conditional routing from supervisor
    def route_from_supervisor(state: AgentState):
        next_agent = state.get("next_agent")
        if next_agent == "Analytics Agent":
            return "analytics_agent"
        elif next_agent == "Campaign Agent":
            return "campaign_agent"
        elif next_agent == "Audience Agent":
            return "audience_agent"
        elif next_agent == "Anomaly Agent":
            return "anomaly_agent"
        return "analytics_agent" # fallback
        
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "analytics_agent": "analytics_agent",
            "campaign_agent": "campaign_agent",
            "audience_agent": "audience_agent",
            "anomaly_agent": "anomaly_agent"
        }
    )
    
    # Once a specialist agent finishes, they yield control back to the user
    workflow.add_edge("analytics_agent", END)
    workflow.add_edge("campaign_agent", END)
    workflow.add_edge("audience_agent", END)
    workflow.add_edge("anomaly_agent", END)
    
    # Compile the graph
    return workflow.compile()

# Instantiated agent graph
agent_graph = build_agent_graph()
