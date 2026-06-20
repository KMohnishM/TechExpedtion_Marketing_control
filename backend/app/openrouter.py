import os
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct:free")

logger = logging.getLogger("openrouter")

async def generate_chat_response(messages: list, model: str = None) -> str:
    """
    Sends a chat completion request to OpenRouter.
    If no key is configured, falls back to a smart mock agent response.
    """
    if not model:
        model = OPENROUTER_MODEL
        
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY is not set. Falling back to Smart Mock Agent Mode.")
        return await _generate_mock_response(messages)
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173", # Standard local Vite dev port
        "X-Title": "Marketing Control Tower"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenRouter API error: Status {response.status_code} - {response.text}")
                # Fallback on HTTP error
                return f"[API Error - Falling back to Smart Mock Response]\n\n" + await _generate_mock_response(messages)
    except Exception as e:
        logger.error(f"Exception calling OpenRouter: {e}")
        return f"[Connection Error - Falling back to Smart Mock Response]\n\n" + await _generate_mock_response(messages)

async def _generate_mock_response(messages: list) -> str:
    """
    Generates intelligent simulated agent responses based on keywords in the prompt.
    """
    # Extract the last user message
    user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_msg = msg.get("content", "").lower()
            break
            
    if not user_msg:
        return "Hello! I am the Marketing Control Tower agent system. How can I help you optimize your campaigns today?"

    # Campaign optimization or status
    if "status" in user_msg or "campaigns" in user_msg or "active" in user_msg or "list" in user_msg:
        return (
            "### Current Campaign Status Overview\n\n"
            "I've fetched the latest performance metrics for our active campaigns:\n\n"
            "1. **Summer Promo - Apparel (Instagram Ads)**: Active | Spend: $18,450 / $50,000 | CTR: 1.8% | Conversions: 1,476 | ROI: 2.1x\n"
            "2. **Fall Launch - Electronics (Google Search)**: Active | Spend: $89,400 / $120,000 | CTR: 3.2% | Conversions: 3,725 | ROI: 2.8x\n"
            "3. **Re-engagement - Cart Abandonment (GDN)**: Active | Spend: $29,800 / $30,000 | CTR: 0.5% | Conversions: 662 | ROI: 0.9x\n"
            "4. **B2B Enterprise Outreach (LinkedIn)**: Paused | Spend: $12,000 / $75,000 | CTR: 0.8% | Conversions: 80 | ROI: 1.4x\n\n"
            "**Recommendations:**\n"
            "- **Re-engagement**: This campaign is nearing its budget limit and has a sub-1.0x ROI. I suggest pausing or reallocating budget to **Fall Launch**, which has a strong 2.8x ROI.\n"
            "- **B2B Outreach**: Currently paused. We should review the targeting criteria before resuming, as CPC is high ($4.50)."
        )
        
    if "budget" in user_msg or "increase" in user_msg or "optimize" in user_msg:
        return (
            "### Campaign Budget Optimization Strategy\n\n"
            "Based on ROI trends, the **Analytics Agent** and **Campaign Agent** propose the following reallocations:\n\n"
            "1. **Increase Budget on Fall Launch - Electronics**:\n"
            "   - Current Budget: **$120,000**\n"
            "   - Proposed Budget: **$140,000** (+ $20,000)\n"
            "   - Justification: Excellent performance with a 2.8x ROI and high conversion rate (5.0%). Projected to yield ~800 additional conversions.\n\n"
            "2. **Deallocate Budget from Re-engagement**:\n"
            "   - Current Budget: **$30,000**\n"
            "   - Proposed Budget: **$30,000** (Keep capped, do not increase spend)\n"
            "   - Justification: ROI is poor (0.9x). Retargeting ads have hit audience fatigue.\n\n"
            "3. **Resume B2B Outreach Campaign**:\n"
            "   - Current Budget: **$75,000** (Active budget: $12,000 spent)\n"
            "   - Recommendation: Resume with narrowed job-title exclusions to decrease waste CPC."
        )

    # Anomaly or click farm / pixel issues
    if "anomaly" in user_msg or "fraud" in user_msg or "click farm" in user_msg or "pixel" in user_msg or "alert" in user_msg:
        return (
            "### Observability Incident Report\n\n"
            "The **Anomaly Agent** is tracking **1 Active Anomaly**:\n\n"
            "#### 🚨 Incident A1: Ad Fraud / Click Farm on 'Summer Promo - Apparel'\n"
            "- **Symptom**: CTR jumped suddenly from 1.8% to 14.5% with 0 conversions. Clicks are originating from a single subnet region.\n"
            "- **Impact**: High click costs without business value. Budget is being depleted by bots.\n"
            "- **Recommended Fix**: Deploy the IP Subnet Blocklist. This will filter out bad bot traffic while preserving organic Instagram clicks.\n\n"
            "You can resolve this incident immediately from the **Active Anomalies** panel by clicking **Deploy IP Subnet Blocklist**."
        )

    # Audience or demographics
    if "audience" in user_msg or "demographics" in user_msg or "gen-z" in user_msg or "targeting" in user_msg:
        return (
            "### Audience Targeting Analysis\n\n"
            "The **Audience Agent** has analyzed demographics across our campaigns:\n\n"
            "- **Summer Promo - Apparel**: High resonance with **18-24 year-olds** on Instagram. CTR is 2.4% (above the 1.8% average). Conversions are strong. However, we are seeing ad fatigue in the 25-34 segment.\n"
            "- **Fall Launch - Electronics**: Google Search targeting is highly effective for terms like 'buy high-end laptop' and 'best noise cancelling headphones'. High purchase intent, primarily ages **25-44**.\n\n"
            "**Suggested Expansion:**\n"
            "I recommend setting up a **Lookalike Audience (1% match)** on Instagram based on our top converters. This will help discover new apparel buyers with a projected 20% lower CAC."
        )

    # General help response
    return (
        "### Marketing Control Tower - Assistant Command Center\n\n"
        "I am the central coordinator for your marketing agents:\n"
        "- 📈 **Analytics Agent**: Analyzes ROI, CTR, conversions, and CPA.\n"
        "- 🎯 **Audience Agent**: Reviews targeting, segments, and suggests expansions.\n"
        "- ⚙️ **Campaign Agent**: Modifies status, updates budgets, and optimizes ads.\n"
        "- 🚨 **Anomaly Agent**: Monitors system health, flags fraud, and handles pixel failures.\n\n"
        "**Try asking me:**\n"
        "- *'Are there any anomalies?'*\n"
        "- *'Show me campaign budgets and performance.'*\n"
        "- *'How can we optimize our audience targeting?'*\n"
        "- *'Recommend a budget shift for Fall Launch.'*"
    )
