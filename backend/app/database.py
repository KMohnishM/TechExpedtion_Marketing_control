import random
from datetime import datetime, timedelta
import threading
import time

class MarketingDatabase:
    def __init__(self):
        self.lock = threading.Lock()
        
        # In-memory campaign store
        self.campaigns = {
            "C1": {
                "id": "C1",
                "name": "Summer Promo - Apparel",
                "channel": "Instagram Ads",
                "budget": 50000.0,
                "spent": 18450.0,
                "status": "Active",
                "ctr": 1.8,  # percentage
                "cpc": 0.45, # dollars
                "conversions": 1476,
                "roi": 2.1,   # multiplier
                "demographics": "Gen-Z & Millennials, age 18-34, interest: fashion, retail",
                "impressions": 1025000,
                "clicks": 18450
            },
            "C2": {
                "id": "C2",
                "name": "Fall Launch - Electronics",
                "channel": "Google Search",
                "budget": 120000.0,
                "spent": 89400.0,
                "status": "Active",
                "ctr": 3.2,
                "cpc": 1.20,
                "conversions": 3725,
                "roi": 2.8,
                "demographics": "Tech Enthusiasts, age 25-54, high purchase intent",
                "impressions": 2328125,
                "clicks": 74500
            },
            "C3": {
                "id": "C3",
                "name": "Re-engagement - Cart Abandonment",
                "channel": "GDN Retargeting",
                "budget": 30000.0,
                "spent": 29800.0,
                "status": "Active",
                "ctr": 0.5,
                "cpc": 0.15,
                "conversions": 662,
                "roi": 0.9,
                "demographics": "Previous visitors, cart abandoners (last 30 days)",
                "impressions": 3973300,
                "clicks": 19866
            },
            "C4": {
                "id": "C4",
                "name": "B2B Enterprise Outreach",
                "channel": "LinkedIn Ads",
                "budget": 75000.0,
                "spent": 12000.0,
                "status": "Paused",
                "ctr": 0.8,
                "cpc": 4.50,
                "conversions": 80,
                "roi": 1.4,
                "demographics": "IT Decision Makers, CTOs, VPs of Engineering, Company Size 200+",
                "impressions": 333333,
                "clicks": 2666
            }
        }
        
        # Historical metrics for charting (last 10 minutes, sampled every 10 seconds)
        self.history = {
            "timestamps": [],
            "CTR": { "C1": [], "C2": [], "C3": [], "C4": [] },
            "Conversions": { "C1": [], "C2": [], "C3": [], "C4": [] },
            "Spend": { "C1": [], "C2": [], "C3": [], "C4": [] }
        }
        
        # Initialize some historical data
        now = datetime.now()
        for i in range(20):
            t = now - timedelta(seconds=(20-i)*10)
            self.history["timestamps"].append(t.strftime("%H:%M:%S"))
            for cid, camp in self.campaigns.items():
                self.history["CTR"][cid].append(camp["ctr"] + random.uniform(-0.1, 0.1) if camp["status"] == "Active" else 0)
                self.history["Conversions"][cid].append(camp["conversions"] - (20-i) * random.randint(2, 5) if camp["status"] == "Active" else camp["conversions"])
                self.history["Spend"][cid].append(camp["spent"] - (20-i) * random.uniform(10, 30) if camp["status"] == "Active" else camp["spent"])

        # Anomalies tracking
        self.anomalies = {
            "A1": {
                "id": "A1",
                "campaign_id": "C1",
                "campaign_name": "Summer Promo - Apparel",
                "type": "Ad Fraud / Click Farm",
                "severity": "Critical",
                "description": "Sudden 8x spike in click rate (CTR) detected from a concentrated IP subnet in Southeast Asia. Conversions remain completely flat. High probability of click farm bot activity.",
                "status": "Active",
                "timestamp": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                "mitigations": [
                    {"id": "M1", "text": "Deploy IP Subnet Blocklist (Auto-Exclude)", "status": "Available"},
                    {"id": "M2", "text": "Temporarily Pause Summer Promo Campaign", "status": "Available"},
                    {"id": "M3", "text": "Enable Recaptcha on Checkout Page", "status": "Available"}
                ]
            },
            "A2": {
                "id": "A2",
                "campaign_id": "C2",
                "campaign_name": "Fall Launch - Electronics",
                "type": "Tracking Pixel Outage",
                "severity": "Warning",
                "description": "Conversion counts dropped to zero starting at 18:30, despite stable click traffic. Verify container tag settings and thank-you page pixel code.",
                "status": "Resolved",
                "timestamp": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "mitigations": [
                    {"id": "M4", "text": "Rollback GTM Workspace Version", "status": "Resolved"},
                    {"id": "M5", "text": "Manual Pixel Verification Ping", "status": "Resolved"}
                ]
            }
        }
        
        # Operation logs / Audit logs
        self.logs = [
            {"timestamp": (datetime.now() - timedelta(minutes=15)).strftime("%H:%M:%S"), "source": "System", "message": "Campaign database loaded. Monitoring engine initialized."},
            {"timestamp": (datetime.now() - timedelta(minutes=10)).strftime("%H:%M:%S"), "source": "Anomaly Agent", "message": "Scanned all campaign parameters. Healthy metrics checked."},
            {"timestamp": (datetime.now() - timedelta(minutes=5)).strftime("%H:%M:%S"), "source": "Anomaly Agent", "message": "ALERT: High CTR variance detected on Summer Promo - Apparel. Flagged as A1 (Click Farm)."}
        ]
        
        # Agent status tracking
        self.agent_statuses = {
            "Campaign Agent": "Idle",
            "Audience Agent": "Idle",
            "Analytics Agent": "Idle",
            "Anomaly Agent": "Monitoring"
        }

        # Simulation loop thread
        self.stop_simulation = False
        self.sim_thread = threading.Thread(target=self._run_simulation, daemon=True)
        self.sim_thread.start()

    def add_log(self, source: str, message: str):
        with self.lock:
            self.logs.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "source": source,
                "message": message
            })
            # Keep logs capped
            if len(self.logs) > 50:
                self.logs.pop(0)

    def set_agent_status(self, agent: str, status: str):
        with self.lock:
            self.agent_statuses[agent] = status

    def get_dashboard_data(self):
        with self.lock:
            return {
                "campaigns": list(self.campaigns.values()),
                "history": self.history,
                "anomalies": list(self.anomalies.values()),
                "logs": self.logs,
                "agent_statuses": self.agent_statuses
            }

    def update_campaign_status(self, cid: str, status: str):
        with self.lock:
            if cid in self.campaigns:
                self.campaigns[cid]["status"] = status
                self.add_log("Campaign Agent", f"Updated status of campaign {self.campaigns[cid]['name']} to {status}")
                return True
            return False

    def update_campaign_budget(self, cid: str, budget: float):
        with self.lock:
            if cid in self.campaigns:
                old_budget = self.campaigns[cid]["budget"]
                self.campaigns[cid]["budget"] = budget
                self.add_log("Campaign Agent", f"Adjusted budget of {self.campaigns[cid]['name']} from ${old_budget:,.2f} to ${budget:,.2f}")
                return True
            return False

    def resolve_anomaly(self, aid: str, mitigation_id: str):
        with self.lock:
            if aid in self.anomalies:
                anomaly = self.anomalies[aid]
                anomaly["status"] = "Resolved"
                for mit in anomaly["mitigations"]:
                    if mit["id"] == mitigation_id:
                        mit["status"] = "Resolved"
                
                self.add_log("Anomaly Agent", f"Anomaly {anomaly['type']} resolved via mitigation: {[m['text'] for m in anomaly['mitigations'] if m['id'] == mitigation_id][0]}")
                
                # If resolving fraud on C1, recover metrics
                if anomaly["campaign_id"] == "C1":
                    c = self.campaigns["C1"]
                    c["ctr"] = 1.8
                    c["cpc"] = 0.45
                    self.add_log("Campaign Agent", f"Traffic filters deployed. Summer Promo - Apparel CTR reverted to normal baseline (1.8%).")
                return True
            return False

    def trigger_anomaly(self, campaign_id: str, anomaly_type: str):
        with self.lock:
            # Helper to programmatically inject an anomaly for demo purposes
            aid = f"A{len(self.anomalies) + 1}"
            campaign_name = self.campaigns[campaign_id]["name"] if campaign_id in self.campaigns else "Unknown"
            
            if anomaly_type == "click_farm":
                self.anomalies[aid] = {
                    "id": aid,
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "type": "Ad Fraud / Click Farm",
                    "severity": "Critical",
                    "description": f"Abnormal CTR jump detected on {campaign_name}. IP behavior indicates bots.",
                    "status": "Active",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "mitigations": [
                        {"id": f"M_{aid}_1", "text": "Deploy IP Blocklist", "status": "Available"},
                        {"id": f"M_{aid}_2", "text": "Pause Campaign", "status": "Available"}
                    ]
                }
                # spike campaign metrics
                if campaign_id in self.campaigns:
                    self.campaigns[campaign_id]["ctr"] = 14.5
                    self.campaigns[campaign_id]["cpc"] = 0.08
            
            self.add_log("Anomaly Agent", f"ALERT: New anomaly {anomaly_type} injected on campaign {campaign_name}.")
            return aid

    def _run_simulation(self):
        while not self.stop_simulation:
            time.sleep(10)
            with self.lock:
                now_str = datetime.now().strftime("%H:%M:%S")
                self.history["timestamps"].append(now_str)
                if len(self.history["timestamps"]) > 30:
                    self.history["timestamps"].pop(0)

                for cid, camp in self.campaigns.items():
                    if camp["status"] != "Active":
                        # Log static values
                        self.history["CTR"][cid].append(0.0)
                        self.history["Conversions"][cid].append(camp["conversions"])
                        self.history["Spend"][cid].append(camp["spent"])
                        continue

                    # If active, spent goes up
                    # LinkedIn goes up faster, Retargeting slower, Search Ads moderate
                    cost_per_tick = 0.0
                    if camp["channel"] == "Instagram Ads":
                        cost_per_tick = random.uniform(5.0, 15.0)
                    elif camp["channel"] == "Google Search":
                        cost_per_tick = random.uniform(15.0, 45.0)
                    elif camp["channel"] == "GDN Retargeting":
                        cost_per_tick = random.uniform(2.0, 8.0)
                    elif camp["channel"] == "LinkedIn Ads":
                        cost_per_tick = random.uniform(30.0, 80.0)

                    # Check if budget exhausted
                    if camp["spent"] + cost_per_tick >= camp["budget"]:
                        camp["spent"] = camp["budget"]
                        camp["status"] = "Paused"
                        self.logs.append({
                            "timestamp": now_str,
                            "source": "Campaign Agent",
                            "message": f"Campaign {camp['name']} auto-paused. Budget cap reached."
                        })
                        continue

                    camp["spent"] += cost_per_tick
                    camp["impressions"] += int(cost_per_tick / (camp["cpc"] if camp["cpc"] > 0 else 0.5) * 50)
                    
                    # Click calculations
                    has_click_fraud = any(a["status"] == "Active" and a["campaign_id"] == cid and a["type"] == "Ad Fraud / Click Farm" for a in self.anomalies.values())
                    
                    if has_click_fraud:
                        # Massive clicks, no conversions
                        camp["ctr"] = round(random.uniform(12.0, 16.0), 2)
                        camp["cpc"] = round(random.uniform(0.05, 0.10), 2)
                        new_clicks = int(cost_per_tick / camp["cpc"])
                        camp["clicks"] += new_clicks
                        # Conversions do not increase
                        new_convs = 0
                    else:
                        # Normal behavior
                        # slight noise
                        camp["ctr"] = round(max(0.1, camp["ctr"] + random.uniform(-0.05, 0.05)), 2)
                        new_clicks = int(cost_per_tick / camp["cpc"])
                        camp["clicks"] += new_clicks
                        
                        # Conversions
                        conversion_rate = 0.08  # apparel
                        if cid == "C2": conversion_rate = 0.05  # electronics
                        elif cid == "C3": conversion_rate = 0.03 # retargeting
                        elif cid == "C4": conversion_rate = 0.03 # linkedin
                        
                        # Check pixel outage anomaly
                        has_pixel_outage = any(a["status"] == "Active" and a["campaign_id"] == cid and a["type"] == "Tracking Pixel Outage" for a in self.anomalies.values())
                        if has_pixel_outage:
                            new_convs = 0
                        else:
                            new_convs = int(new_clicks * conversion_rate * random.uniform(0.8, 1.2))
                        
                        camp["conversions"] += new_convs

                    # ROI calculation
                    # Value generated = conversions * average sale value
                    avg_sale = 45.0
                    if cid == "C2": avg_sale = 150.0
                    elif cid == "C3": avg_sale = 55.0
                    elif cid == "C4": avg_sale = 2500.0 # enterprise
                    
                    revenue = camp["conversions"] * avg_sale
                    camp["roi"] = round(revenue / camp["spent"], 2) if camp["spent"] > 0 else 0.0
                    
                    # Update charts history
                    self.history["CTR"][cid].append(camp["ctr"])
                    self.history["Conversions"][cid].append(camp["conversions"])
                    self.history["Spend"][cid].append(camp["spent"])
                    
                    # Capping historical data size
                    if len(self.history["CTR"][cid]) > 30:
                        self.history["CTR"][cid].pop(0)
                        self.history["Conversions"][cid].pop(0)
                        self.history["Spend"][cid].pop(0)

# Global database instance
db = MarketingDatabase()
