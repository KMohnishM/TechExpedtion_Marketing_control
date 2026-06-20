import Chart from 'chart.js/auto';
import './style.css';

// Base API Configuration
const API_URL = 'http://localhost:8000/api';

// Application State
let campaigns = [];
let anomalies = [];
let logs = [];
let activeAgent = 'Supervisor';
let chatHistory = [];
let chartInstance = null;
let currentEditingCampaignId = null;

// DOM Elements Cache
const campaignsContainer = document.getElementById('campaigns-container');
const anomaliesContainer = document.getElementById('anomalies-container');
const logsContainer = document.getElementById('logs-container');
const chatMessagesContainer = document.getElementById('chat-messages-container');
const chatInputForm = document.getElementById('chat-input-form');
const chatInputField = document.getElementById('chat-input-field');
const chatSendBtn = document.getElementById('chat-send-btn');
const quickPromptsContainer = document.getElementById('quick-prompts-container');
const systemHealthText = document.getElementById('system-health-text');
const globalRoi = document.getElementById('global-roi');
const globalBudgetRatio = document.getElementById('global-budget-ratio');
const globalAlerts = document.getElementById('global-alerts');
const alertsCountCard = document.getElementById('alerts-count-card');
const traceFlowStatus = document.getElementById('trace-flow-status');

// Budget Modal Elements
const budgetModal = document.getElementById('budget-modal');
const modalCampaignName = document.getElementById('modal-campaign-name');
const budgetInput = document.getElementById('budget-input');
const closeBudgetModalBtn = document.getElementById('close-budget-modal');
const cancelBudgetBtn = document.getElementById('cancel-budget-btn');
const saveBudgetBtn = document.getElementById('save-budget-btn');
const triggerAnomalyDemoBtn = document.getElementById('trigger-anomaly-demo-btn');

/* ==========================================
   INITIALIZATION & API CALLS
   ========================================== */
window.addEventListener('DOMContentLoaded', () => {
  initializeChart();
  fetchDashboardData();
  
  // Periodic polling for real-time metrics simulation
  setInterval(fetchDashboardData, 3000);
  
  setupEventListeners();
});

function setupEventListeners() {
  // Chat submit
  chatInputForm.addEventListener('submit', handleChatSubmit);
  
  // Quick prompts
  quickPromptsContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (btn && btn.dataset.query) {
      chatInputField.value = btn.dataset.query;
      handleChatSubmit(e);
    }
  });

  // Chat intro inline suggested questions
  chatMessagesContainer.addEventListener('click', (e) => {
    const li = e.target.closest('ul.chat-intro-list li');
    if (li) {
      const text = li.innerText.replace(/"/g, '');
      chatInputField.value = text;
      handleChatSubmit(e);
    }
  });

  // Modal event listeners
  closeBudgetModalBtn.addEventListener('click', hideBudgetModal);
  cancelBudgetBtn.addEventListener('click', hideBudgetModal);
  saveBudgetBtn.addEventListener('click', submitBudgetChange);
  
  // Demo infect button
  triggerAnomalyDemoBtn.addEventListener('click', triggerAnomalyDemo);
}

// Fetch dashboard stats, campaigns, anomalies and audit logs
async function fetchDashboardData() {
  try {
    const response = await fetch(`${API_URL}/dashboard`);
    if (!response.ok) throw new Error('API server unreachable');
    
    const data = await response.json();
    
    // Update local states
    campaigns = data.campaigns;
    anomalies = data.anomalies;
    logs = data.logs;
    
    // Refresh UI Components
    updateHeaderStats();
    renderCampaigns();
    renderAnomalies();
    renderLogs();
    updateChart(data.history);
    updateAgentPills(data.agent_statuses);
    
    systemHealthText.innerText = 'Online';
    systemHealthText.parentElement.querySelector('.status-dot').className = 'status-dot pulsing-green';
  } catch (error) {
    console.error('Error fetching dashboard:', error);
    systemHealthText.innerText = 'Unreachable';
    systemHealthText.parentElement.querySelector('.status-dot').className = 'status-dot';
  }
}

/* ==========================================
   UI RENDERING FUNCTIONS
   ========================================== */
function updateHeaderStats() {
  if (campaigns.length === 0) return;
  
  // Calculate average ROI for active campaigns
  const activeCamps = campaigns.filter(c => c.status === 'Active');
  const avgRoiValue = activeCamps.length > 0 
    ? (activeCamps.reduce((acc, c) => acc + c.roi, 0) / activeCamps.length).toFixed(1) + 'x'
    : 'N/A';
  globalRoi.innerText = avgRoiValue;
  
  // Calculate spent vs total budget
  const totalBudget = campaigns.reduce((acc, c) => acc + c.budget, 0);
  const totalSpent = campaigns.reduce((acc, c) => acc + c.spent, 0);
  globalBudgetRatio.innerText = `$${(totalSpent/1000).toFixed(1)}k / $${(totalBudget/1000).toFixed(0)}k`;
  
  // Count active anomalies
  const activeAlerts = anomalies.filter(a => a.status === 'Active').length;
  globalAlerts.innerText = activeAlerts;
  
  if (activeAlerts > 0) {
    alertsCountCard.classList.add('critical-glow');
  } else {
    alertsCountCard.classList.remove('critical-glow');
  }
}

function renderCampaigns() {
  campaignsContainer.innerHTML = '';
  
  campaigns.forEach(c => {
    const isUnderperforming = c.roi < 1.5 && c.status === 'Active';
    const percentSpent = Math.min(100, (c.spent / c.budget) * 100).toFixed(0);
    const hasAnomaly = anomalies.some(a => a.campaign_id === c.id && a.status === 'Active');
    
    const card = document.createElement('div');
    card.className = `campaign-card ${hasAnomaly ? 'has-active-anomaly' : ''}`;
    
    card.innerHTML = `
      <div class="camp-header">
        <div class="camp-name-container">
          <span class="camp-name" title="${c.name}">${c.name}</span>
          <span class="camp-channel">${c.channel}</span>
        </div>
        <span class="status-badge ${c.status.toLowerCase()}" data-id="${c.id}">${c.status}</span>
      </div>
      
      <div class="camp-progress-container">
        <div class="camp-progress-bar">
          <div class="camp-progress-fill" style="width: ${percentSpent}%"></div>
        </div>
        <div class="camp-budget-label">
          <span>Spent: $${c.spent.toLocaleString(undefined, {maximumFractionDigits:0})}</span>
          <span>Budget: $${c.budget.toLocaleString(undefined, {maximumFractionDigits:0})}</span>
        </div>
      </div>
      
      <div class="camp-metrics-grid">
        <div class="camp-metric">
          <span class="metric-label">CTR</span>
          <span class="metric-value ${hasAnomaly && c.id === 'C1' ? 'text-pink' : ''}">${c.ctr}%</span>
        </div>
        <div class="camp-metric">
          <span class="metric-label">ROI</span>
          <span class="metric-value ${isUnderperforming ? 'text-pink' : 'text-teal'}">${c.roi}x</span>
        </div>
      </div>
    `;
    
    // Add click handler to toggle status or open edit modal
    card.querySelector('.status-badge').addEventListener('click', (e) => {
      e.stopPropagation();
      toggleCampaignStatus(c.id, c.status);
    });
    
    card.addEventListener('click', () => {
      showBudgetModal(c.id, c.name, c.budget);
    });
    
    campaignsContainer.appendChild(card);
  });
}

function renderAnomalies() {
  anomaliesContainer.innerHTML = '';
  
  anomalies.forEach(a => {
    const card = document.createElement('div');
    card.className = `anomaly-alert-card ${a.severity.toLowerCase()} ${a.status.toLowerCase()}`;
    
    const severityBadge = `<span class="severity-tag ${a.severity.toLowerCase()}">${a.severity}</span>`;
    const resolvedBadge = `<span class="severity-tag resolved">RESOLVED</span>`;
    
    let mitigationsHTML = '';
    if (a.status === 'Active') {
      mitigationsHTML = `
        <div class="mitigation-header">Deploy Mitigations</div>
        <div class="mitigations-list">
          ${a.mitigations.map(m => `
            <button class="mitigation-btn" data-aid="${a.id}" data-mid="${m.id}" ${m.status === 'Resolved' ? 'disabled' : ''}>
              <span>${m.text}</span>
              <span class="mitigation-status-icon">&rarr;</span>
            </button>
          `).join('')}
        </div>
      `;
    } else {
      mitigationsHTML = `
        <div class="mitigations-list" style="margin-top: 5px;">
          <div class="mitigation-btn" disabled style="opacity: 0.8; background: rgba(46, 204, 113, 0.05); border-color: rgba(46, 204, 113, 0.2);">
            <span style="color: var(--color-green);">Mitigated successfully</span>
            <span class="mitigation-status-icon resolved">&#10003;</span>
          </div>
        </div>
      `;
    }
    
    card.innerHTML = `
      <div class="anomaly-card-header">
        <span class="anomaly-title">${a.type}</span>
        ${a.status === 'Active' ? severityBadge : resolvedBadge}
      </div>
      <div class="anomaly-meta">Campaign: ${a.campaign_name} | Flagged: ${a.timestamp}</div>
      <div class="anomaly-desc">${a.description}</div>
      ${mitigationsHTML}
    `;
    
    // Mitigations buttons listener
    card.querySelectorAll('.mitigation-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const aid = btn.dataset.aid;
        const mid = btn.dataset.mid;
        applyMitigation(aid, mid);
      });
    });
    
    anomaliesContainer.appendChild(card);
  });
}

function renderLogs() {
  logsContainer.innerHTML = '';
  
  logs.forEach(l => {
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    
    const srcClass = l.source.toLowerCase().replace(/ /g, '-');
    
    entry.innerHTML = `
      <span class="log-time">[${l.timestamp}]</span>
      <span class="log-source ${srcClass}">${l.source}:</span>
      <span class="log-message">${escapeHTML(l.message)}</span>
    `;
    
    logsContainer.appendChild(entry);
  });
  
  // Auto-scroll to bottom of logs
  logsContainer.scrollTop = logsContainer.scrollHeight;
}

function updateAgentPills(statuses) {
  if (!statuses) return;
  const pills = document.querySelectorAll('.agent-pill');
  pills.forEach(pill => {
    const agentName = pill.dataset.agent;
    const status = statuses[agentName];
    if (status === 'Thinking...') {
      pill.className = `agent-pill ${pill.classList[1]} active`;
    } else {
      pill.classList.remove('active');
    }
  });
}

/* ==========================================
   INTERACTION HANDLERS
   ========================================== */
async function toggleCampaignStatus(cid, currentStatus) {
  const nextStatus = currentStatus === 'Active' ? 'Paused' : 'Active';
  try {
    const response = await fetch(`${API_URL}/campaigns/${cid}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: nextStatus })
    });
    if (response.ok) {
      fetchDashboardData();
    }
  } catch (error) {
    console.error('Failed to update status:', error);
  }
}

function showBudgetModal(cid, name, currentBudget) {
  currentEditingCampaignId = cid;
  modalCampaignName.innerText = name;
  budgetInput.value = currentBudget;
  budgetModal.classList.add('show');
}

function hideBudgetModal() {
  budgetModal.classList.remove('show');
  currentEditingCampaignId = null;
}

async function submitBudgetChange() {
  const newBudget = parseFloat(budgetInput.value);
  if (isNaN(newBudget) || newBudget <= 0) {
    alert('Please enter a valid budget.');
    return;
  }
  
  try {
    const response = await fetch(`${API_URL}/campaigns/${currentEditingCampaignId}/budget`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ budget: newBudget })
    });
    if (response.ok) {
      hideBudgetModal();
      fetchDashboardData();
    }
  } catch (error) {
    console.error('Failed to update budget:', error);
  }
}

async function applyMitigation(aid, mid) {
  try {
    const response = await fetch(`${API_URL}/anomalies/${aid}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mitigation_id: mid })
    });
    if (response.ok) {
      fetchDashboardData();
    }
  } catch (error) {
    console.error('Failed to apply mitigation:', error);
  }
}

async function triggerAnomalyDemo() {
  try {
    const response = await fetch(`${API_URL}/anomalies/trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ campaign_id: 'C1', anomaly_type: 'click_farm' })
    });
    if (response.ok) {
      fetchDashboardData();
    }
  } catch (error) {
    console.error('Failed to infect demo:', error);
  }
}

/* ==========================================
   AGENT CHAT WORKSPACE
   ========================================== */
async function handleChatSubmit(e) {
  e.preventDefault();
  const text = chatInputField.value.trim();
  if (!text) return;
  
  // Add user bubble
  appendChatBubble('user', text);
  chatInputField.value = '';
  
  // Set thinking state
  setWorkspaceLoading(true);
  
  // Animate LangGraph Flow
  updateTraceFlow('Routing request...', 'supervisor');
  
  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        history: chatHistory
      })
    });
    
    if (!response.ok) throw new Error('API server returned error');
    
    const data = await response.json();
    
    // Complete LangGraph Flow
    const agentSender = data.sender;
    const senderSlug = agentSender.toLowerCase().replace(/ agent/g, '');
    updateTraceFlow(`Processing with ${agentSender}`, senderSlug, true);
    
    // Add agent response bubble
    setTimeout(() => {
      appendChatBubble(senderSlug, data.response, data.proposed_actions);
      setWorkspaceLoading(false);
      updateTraceFlow('Idle', 'idle');
      fetchDashboardData(); // Refresh metrics in case actions happened
    }, 1000);
    
  } catch (error) {
    console.error('Chat error:', error);
    appendChatBubble('system', 'Sorry, I encountered an error communicating with the agent cluster. Please make sure the FastAPI backend is running.');
    setWorkspaceLoading(false);
    updateTraceFlow('Error', 'error');
  }
}

function appendChatBubble(sender, text, proposedActions = []) {
  const bubble = document.createElement('div');
  
  let senderName = 'USER';
  let avatarText = 'USR';
  
  if (sender === 'system') {
    bubble.className = 'chat-message system-msg';
    senderName = 'System';
    avatarText = 'SYS';
  } else if (sender === 'user') {
    bubble.className = 'chat-message user';
  } else {
    // Agent sender
    bubble.className = `chat-message agent-msg agent-${sender}`;
    avatarText = sender.substring(0, 3).toUpperCase();
    
    if (sender === 'supervisor') senderName = 'Supervisor';
    else if (sender === 'analytics') senderName = 'Analytics Agent';
    else if (sender === 'campaign') senderName = 'Campaign Agent';
    else if (sender === 'audience') senderName = 'Audience Agent';
    else if (sender === 'anomaly') senderName = 'Anomaly Agent';
  }
  
  // Convert simple markdown elements (tables, headers)
  let formattedText = parseSimpleMarkdown(text);
  
  let actionsHTML = '';
  if (proposedActions && proposedActions.length > 0) {
    actionsHTML = `
      <div class="proposal-card">
        <div class="proposal-header">
          <span>⚙️ Proposal Recommendation</span>
        </div>
        <div class="proposal-details">
          ${proposedActions.map(action => {
            if (action.type === 'budget_change') {
              return `Modify budget for <strong>${action.campaign_name}</strong> to $${action.proposed_value.toLocaleString()}`;
            } else if (action.type === 'pause') {
              return `Pause Campaign: <strong>${action.campaign_name}</strong>`;
            }
            return 'Apply optimization change';
          }).join('<br>')}
        </div>
        <div class="proposal-actions-row">
          ${proposedActions.map(action => {
            if (action.type === 'budget_change') {
              return `<button class="btn btn-xs btn-primary action-execute-btn" data-type="budget" data-cid="${action.campaign_id}" data-val="${action.proposed_value}">Approve & Apply</button>`;
            } else if (action.type === 'pause') {
              return `<button class="btn btn-xs btn-primary action-execute-btn" data-type="status" data-cid="${action.campaign_id}" data-val="Paused">Approve & Pause</button>`;
            }
            return '';
          }).join('')}
          <button class="btn btn-xs btn-outline action-reject-btn">Dismiss</button>
        </div>
      </div>
    `;
  }
  
  bubble.innerHTML = `
    ${sender !== 'user' ? `<div class="msg-avatar agent-${sender}">${avatarText}</div>` : ''}
    <div class="msg-body">
      ${formattedText}
      ${actionsHTML}
    </div>
    ${sender === 'user' ? `<div class="msg-avatar user">${avatarText}</div>` : ''}
  `;
  
  // Listeners for action buttons inside proposal card
  bubble.querySelectorAll('.action-execute-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const type = btn.dataset.type;
      const cid = btn.dataset.cid;
      const val = btn.dataset.val;
      
      try {
        let res;
        if (type === 'budget') {
          res = await fetch(`${API_URL}/campaigns/${cid}/budget`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ budget: parseFloat(val) })
          });
        } else if (type === 'status') {
          res = await fetch(`${API_URL}/campaigns/${cid}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: val })
          });
        }
        
        if (res && res.ok) {
          btn.closest('.proposal-card').innerHTML = `
            <div style="color: var(--color-green); font-size: 0.75rem; font-weight: bold; display: flex; align-items: center; gap: 0.4rem;">
              <span>&#10003; Recommendation Approved & Executed</span>
            </div>
          `;
          fetchDashboardData();
        }
      } catch (e) {
        console.error('Failed executing proposed action:', e);
      }
    });
  });
  
  bubble.querySelectorAll('.action-reject-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.proposal-card').remove();
    });
  });
  
  chatMessagesContainer.appendChild(bubble);
  chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
  
  // Add to local log history
  if (sender !== 'system') {
    chatHistory.push({
      role: sender === 'user' ? 'user' : 'assistant',
      content: text,
      sender: senderName
    });
    // Cap history
    if (chatHistory.length > 20) chatHistory.shift();
  }
}

function setWorkspaceLoading(isLoading) {
  chatInputField.disabled = isLoading;
  chatSendBtn.disabled = isLoading;
  
  const loaderId = 'chat-workspace-spinner';
  let loader = document.getElementById(loaderId);
  
  if (isLoading) {
    chatSendBtn.innerHTML = `<span>Thinking</span><span class="pulsing-dot">...</span>`;
  } else {
    chatSendBtn.innerHTML = `
      <span>Send</span>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
    `;
  }
}

/* ==========================================
   LANGGRAPH WORKFLOW STEP VISUALIZER
   ========================================== */
function updateTraceFlow(statusText, nodeSlug, isDone = false) {
  traceFlowStatus.innerText = statusText;
  
  const nodes = {
    user: document.getElementById('node-user'),
    supervisor: document.getElementById('node-supervisor'),
    specialist: document.getElementById('node-specialist'),
    output: document.getElementById('node-output')
  };
  
  // Reset nodes classes
  Object.values(nodes).forEach(n => {
    n.className = 'trace-node';
  });
  
  if (nodeSlug === 'idle') {
    nodes.user.className = 'trace-node completed';
    nodes.supervisor.className = 'trace-node completed';
    nodes.specialist.className = 'trace-node completed';
    nodes.output.className = 'trace-node completed';
    return;
  }
  
  if (nodeSlug === 'error') {
    Object.values(nodes).forEach(n => {
      n.className = 'trace-node';
    });
    return;
  }
  
  if (nodeSlug === 'supervisor') {
    nodes.user.className = 'trace-node completed';
    nodes.supervisor.className = 'trace-node active';
  } else if (['analytics', 'campaign', 'audience', 'anomaly'].includes(nodeSlug)) {
    nodes.user.className = 'trace-node completed';
    nodes.supervisor.className = 'trace-node completed';
    
    // Customize text on specialist node dynamically
    nodes.specialist.innerText = nodeSlug.charAt(0).toUpperCase() + nodeSlug.slice(1) + ' Agent';
    
    if (isDone) {
      nodes.specialist.className = 'trace-node completed';
      nodes.output.className = 'trace-node active';
    } else {
      nodes.specialist.className = 'trace-node active';
    }
  }
}

/* ==========================================
   REAL-TIME CTR CHART (CHART.JS)
   ========================================== */
function initializeChart() {
  const ctx = document.getElementById('ctrChart').getContext('2d');
  
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Summer Promo',
          borderColor: '#00f2fe',
          backgroundColor: 'rgba(0, 242, 254, 0.05)',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          fill: true,
          data: []
        },
        {
          label: 'Fall Launch',
          borderColor: '#9b51e0',
          backgroundColor: 'rgba(155, 81, 224, 0.05)',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          fill: true,
          data: []
        },
        {
          label: 'Re-engagement',
          borderColor: '#ff007a',
          backgroundColor: 'rgba(255, 0, 122, 0.05)',
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.3,
          fill: true,
          data: []
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            boxWidth: 8,
            boxHeight: 8,
            color: '#94a3b8',
            font: {
              family: 'Outfit',
              size: 9
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 8, family: 'JetBrains Mono' },
            maxRotation: 0
          }
        },
        y: {
          min: 0,
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: {
            color: '#64748b',
            font: { size: 8, family: 'JetBrains Mono' },
            callback: (v) => v + '%'
          }
        }
      }
    }
  });
}

function updateChart(history) {
  if (!history || !chartInstance) return;
  
  chartInstance.data.labels = history.timestamps;
  
  chartInstance.data.datasets[0].data = history.CTR.C1;
  chartInstance.data.datasets[1].data = history.CTR.C2;
  chartInstance.data.datasets[2].data = history.CTR.C3;
  
  chartInstance.update('none'); // Update without full layout recalculations for speed
}

/* ==========================================
   HELPER UTILITIES
   ========================================== */
function parseSimpleMarkdown(markdown) {
  if (!markdown) return '';
  
  let html = markdown;
  
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h4>$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2>$1</h2>');
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  
  // Unordered list
  html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
  // Combine consecutive <ul> tags
  html = html.replace(/<\/ul>\s*<ul>/gim, '');
  
  // Table parser
  const lines = html.split('\n');
  let inTable = false;
  let tableHTML = '';
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith('|') && line.endsWith('|')) {
      if (!inTable) {
        inTable = true;
        tableHTML = '<table>';
      }
      
      const cells = line.split('|').map(c => c.trim()).filter((c, index, arr) => index > 0 && index < arr.length - 1);
      
      // Skip alignment line e.g. |---|---|
      if (cells.every(c => c.match(/^:?-+:?$/))) {
        continue;
      }
      
      const cellTag = tableHTML.includes('</th>') ? 'td' : 'th';
      tableHTML += '<tr>' + cells.map(c => `<${cellTag}>${c}</${cellTag}>`).join('') + '</tr>';
    } else {
      if (inTable) {
        inTable = false;
        tableHTML += '</table>';
        // Replace previous table lines in html
        lines[i - 1] = tableHTML;
        tableHTML = '';
      }
    }
  }
  
  html = lines.join('\n');
  
  // Linebreaks
  html = html.replace(/\n/g, '<br>');
  // clean up extra br tags inside lists/tables
  html = html.replace(/<br><\/tr>/g, '</tr>');
  html = html.replace(/<br><tr>/g, '<tr>');
  html = html.replace(/<br><ul>/g, '<ul>');
  html = html.replace(/<br><li>/g, '<li>');
  html = html.replace(/<\/ul><br>/g, '</ul>');
  
  // Remove trailing PROPOSE_ACTION metadata from output so the user doesn't see raw JSON
  html = html.replace(/PROPOSE_ACTION:\s*\{.*?\}<br>?/gi, '');
  html = html.replace(/PROPOSE_ACTION:\s*\{.*?\}/gi, '');
  
  return html;
}

function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}
