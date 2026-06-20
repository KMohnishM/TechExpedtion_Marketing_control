from typing import List, Dict, Any, TypedDict, Annotated
import operator

class AgentState(TypedDict):
    # Standard conversation messages
    messages: Annotated[List[Dict[str, Any]], operator.add]
    
    # Original user query
    user_query: str
    
    # Current active agent
    current_agent: str
    
    # Next agent to route to
    next_agent: str
    
    # Snapshots of data for reference
    campaigns_data: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    
    # Execution logs / trace of agent thoughts
    trace_logs: Annotated[List[str], operator.add]
    
    # Actions proposed by agents that require user confirmation (e.g. pause campaigns, raise budgets)
    proposed_actions: List[Dict[str, Any]]
