// ===========================
// Application State
// ===========================
const state = {
    apiUrl: 'http://localhost:8080',
    selectedDomain: 'general',
    conversationHistory: [],
    currentResults: null,
    isLoading: false,
    conversationId: generateId()
};

// ===========================
// Utility Functions
// ===========================
function generateId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function getCurrentTime() {
    return new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===========================
// DOM Elements
// ===========================
const elements = {
    messagesContainer: document.getElementById('messages'),
    queryInput: document.getElementById('query-input'),
    sendBtn: document.getElementById('send-btn'),
    clearChatBtn: document.getElementById('clear-chat'),
    apiUrlInput: document.getElementById('api-url'),
    connectionStatus: document.getElementById('connection-status'),
    resultsContent: document.getElementById('results-content'),
    toggleViewBtn: document.getElementById('toggle-view'),
    exportBtn: document.getElementById('export-btn'),
    domainBtns: document.querySelectorAll('.domain-btn'),
    exampleItems: document.querySelectorAll('.example-item')
};

// ===========================
// API Functions
// ===========================
async function checkApiConnection() {
    try {
        const response = await fetch(`${state.apiUrl}/health`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            updateConnectionStatus(true);
            return true;
        }
        throw new Error('API not healthy');
    } catch (error) {
        console.error('API connection failed:', error);
        updateConnectionStatus(false);
        return false;
    }
}

async function sendQuery(query) {
    try {
        const response = await fetch(`${state.apiUrl}/api/v1/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                domain: state.selectedDomain,
                conversation_id: state.conversationId,
                conversation_history: state.conversationHistory
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Query failed:', error);
        throw error;
    }
}

// ===========================
// UI Update Functions
// ===========================
function updateConnectionStatus(connected) {
    const statusIndicator = elements.connectionStatus.parentElement;
    if (connected) {
        statusIndicator.classList.add('connected');
        elements.connectionStatus.textContent = 'Connected';
    } else {
        statusIndicator.classList.remove('connected');
        elements.connectionStatus.textContent = 'Disconnected';
    }
}

function addMessage(content, type = 'user', options = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Render as Markdown if marked library is available, otherwise fallback to escaped text
    if (typeof marked !== 'undefined') {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }

    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'message-timestamp';
    timestampDiv.textContent = getCurrentTime();

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timestampDiv);

    // Add SQL block if present
    if (options.sql) {
        const sqlBlock = createSqlBlock(options.sql);
        messageDiv.appendChild(sqlBlock);
    }

    // Remove welcome message if exists
    const welcomeMsg = elements.messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    elements.messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;

    return messageDiv;
}

function createSqlBlock(sql) {
    const sqlBlock = document.createElement('div');
    sqlBlock.className = 'sql-block';

    sqlBlock.innerHTML = `
        <div class="sql-header">
            <span class="sql-label">Generated SQL</span>
            <button class="copy-btn" onclick="copySqlToClipboard(this)">Copy</button>
        </div>
        <pre class="sql-code">${escapeHtml(sql)}</pre>
    `;

    return sqlBlock;
}

function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-indicator';
    loadingDiv.id = 'loading-indicator';

    loadingDiv.innerHTML = `
        <span>Thinking</span>
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;

    elements.messagesContainer.appendChild(loadingDiv);
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

function hideLoading() {
    const loadingDiv = document.getElementById('loading-indicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function displayResults(results, sql, visConfig) {
    if (!results || results.length === 0) {
        elements.resultsContent.innerHTML = `
            <div class="empty-state">
                <h3>No Data Found</h3>
                <p>The query returned no results</p>
            </div>
        `;
        return;
    }

    state.currentResults = results;
    state.currentVisConfig = visConfig; // Store for switching

    // Clear previous content
    elements.resultsContent.innerHTML = '';

    // Create Visualization Toolbar
    const toolbar = createVizToolbar(visConfig);
    elements.resultsContent.appendChild(toolbar);

    // Create container for visualization (chart or table)
    const vizContainer = document.createElement('div');
    vizContainer.id = 'viz-container';
    elements.resultsContent.appendChild(vizContainer);

    // Default to Table view, but if recommendation is stronf, maybe user wants to see it?
    // User said: "user will select". So let's show Table by default but make the recommendation obvious.
    renderVisualization('table');
}

function createVizToolbar(visConfig) {
    const toolbar = document.createElement('div');
    toolbar.className = 'viz-toolbar';

    const label = document.createElement('span');
    label.className = 'viz-label';
    label.textContent = 'View As:';
    toolbar.appendChild(label);

    const recommendedType = visConfig?.chart_type || 'table';

    // Define available types
    const types = [
        { id: 'table', icon: '📋', label: 'Table' },
        { id: 'bar', icon: '📊', label: 'Bar' },
        { id: 'line', icon: '📈', label: 'Line' },
        { id: 'pie', icon: '🥧', label: 'Pie' }
    ];

    types.forEach(type => {
        const btn = document.createElement('button');
        btn.className = 'viz-btn';
        btn.dataset.type = type.id;

        let labelHtml = `<span class="viz-icon">${type.icon}</span> ${type.label}`;

        // Add recommendation badge if matches
        if (recommendedType === type.id && type.id !== 'table') {
            btn.classList.add('recommended');
            labelHtml += ` <span class="viz-badge">Recommended</span>`;
        }

        btn.innerHTML = labelHtml;

        btn.onclick = () => {
            // Update active state
            toolbar.querySelectorAll('.viz-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderVisualization(type.id);
        };

        // Set Table as active initially
        if (type.id === 'table') {
            btn.classList.add('active');
        }

        toolbar.appendChild(btn);
    });

    return toolbar;
}

function renderVisualization(type) {
    const container = document.getElementById('viz-container');
    container.innerHTML = '';

    if (type === 'table') {
        const table = createDataTable(state.currentResults);
        container.appendChild(table);
    } else {
        // Create config override for the selected type
        let config = state.currentVisConfig;

        // If switching to a type different from recommendation, we need to adapt
        if (!config || config.chart_type !== type) {
            // Heuristic adaptation
            const columns = Object.keys(state.currentResults[0]);
            const numericColumns = columns.filter(col => {
                return state.currentResults.every(row => !isNaN(parseFloat(row[col])));
            });
            const labelColumn = columns.find(col => !numericColumns.includes(col)) || columns[0];

            config = {
                chart_type: type,
                x_axis_key: config?.x_axis_key || labelColumn,
                y_axis_key: config?.y_axis_key || numericColumns[0],
                title: config?.title || 'Data Visualization'
            };
        }

        const chart = createChart(state.currentResults, config);
        if (chart) {
            container.appendChild(chart);
        } else {
            container.innerHTML = '<div class="empty-state"><p>Cannot generate this chart with current data</p></div>';
        }
    }
}

function createDataTable(data) {
    const container = document.createElement('div');
    container.className = 'data-table-container';

    const table = document.createElement('table');
    table.className = 'data-table';

    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    const columns = Object.keys(data[0]);
    columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create body
    const tbody = document.createElement('tbody');
    data.forEach(row => {
        const tr = document.createElement('tr');
        columns.forEach(col => {
            const td = document.createElement('td');
            td.textContent = row[col] ?? 'N/A';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);

    return container;
}

function createChart(data, config) {
    if (data.length === 0) return null;

    // If explicit config says "table", don't show chart
    if (config && config.chart_type === 'table') return null;

    let chartType, xKey, yKeys, title;

    if (config) {
        // Use intelligent configuration from backend
        chartType = config.chart_type;
        xKey = config.x_axis_key;

        // Handle Y keys (could be string or array)
        if (Array.isArray(config.y_axis_key)) {
            yKeys = config.y_axis_key;
        } else {
            yKeys = [config.y_axis_key];
        }

        title = config.title;

        // Verify keys exist in data
        if (!data[0].hasOwnProperty(xKey)) {
            console.warn(`Chart X-axis key '${xKey}' not found in data. Falling back.`);
            config = null; // Fallback to auto-detection
        }
    }

    // Fallback Auto-Detection (if no config or invalid config)
    if (!config) {
        const columns = Object.keys(data[0]);
        const numericColumns = columns.filter(col => {
            return data.every(row => !isNaN(parseFloat(row[col])));
        });

        const labelColumn = columns.find(col => !numericColumns.includes(col)) || columns[0];

        if (numericColumns.length === 0 || data.length > 50) {
            return null;
        }

        chartType = data.length <= 10 ? 'bar' : 'line';
        xKey = labelColumn;
        yKeys = numericColumns.slice(0, 3); // Take top 3 numeric cols
        title = 'Data Visualization';
    }

    const container = document.createElement('div');
    container.className = 'chart-container';

    const titleDiv = document.createElement('div');
    titleDiv.className = 'chart-title';
    titleDiv.textContent = title || 'Data Visualization';
    container.appendChild(titleDiv);

    const canvas = document.createElement('canvas');
    canvas.className = 'chart-canvas';
    container.appendChild(canvas);

    // Prepare chart data
    const labels = data.map(row => row[xKey]);

    const datasets = yKeys.map((key, index) => {
        const colors = [
            { bg: 'rgba(99, 102, 241, 0.6)', border: 'rgb(99, 102, 241)' },
            { bg: 'rgba(139, 92, 246, 0.6)', border: 'rgb(139, 92, 246)' },
            { bg: 'rgba(236, 72, 153, 0.6)', border: 'rgb(236, 72, 153)' },
            { bg: 'rgba(16, 185, 129, 0.6)', border: 'rgb(16, 185, 129)' }, // Emerald
            { bg: 'rgba(245, 158, 11, 0.6)', border: 'rgb(245, 158, 11)' }  // Amber
        ];

        // Cycle colors if more datasets than colors
        const color = colors[index % colors.length];

        return {
            label: key,
            data: data.map(row => parseFloat(row[key]) || 0),
            backgroundColor: color.bg,
            borderColor: color.border,
            borderWidth: 2,
            tension: 0.4,
            fill: chartType === 'area' // Fill if it's an area chart
        };
    });

    // Map backend chart types to Chart.js types
    const chartJsMap = {
        'bar': 'bar',
        'line': 'line',
        'pie': 'pie',
        'doughnut': 'doughnut',
        'scatter': 'scatter',
        'area': 'line' // Area is line with fill
    };

    const finalType = chartJsMap[chartType] || 'bar';

    // Create chart
    new Chart(canvas, {
        type: finalType,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: yKeys.length > 0,
                    position: 'top',
                    labels: {
                        color: '#e0e0e8',
                        font: { family: 'Inter', size: 12 }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(20, 20, 31, 0.95)',
                    titleColor: '#e0e0e8',
                    bodyColor: '#a0a0b0',
                    borderColor: 'rgba(99, 102, 241, 0.5)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(99, 102, 241, 0.1)' },
                    ticks: {
                        color: '#a0a0b0',
                        font: { family: 'Inter', size: 11 }
                    },
                    display: !['pie', 'doughnut'].includes(finalType)
                },
                y: {
                    grid: { color: 'rgba(99, 102, 241, 0.1)' },
                    ticks: {
                        color: '#a0a0b0',
                        font: { family: 'Inter', size: 11 }
                    },
                    display: !['pie', 'doughnut'].includes(finalType)
                }
            }
        }
    });

    return container;
}

function showError(message) {
    addMessage(`❌ Error: ${message}`, 'assistant');
}

// ===========================
// Event Handlers
// ===========================
async function handleSendMessage() {
    const query = elements.queryInput.value.trim();

    if (!query || state.isLoading) return;

    // Add user message
    addMessage(query, 'user');

    // Update conversation history
    state.conversationHistory.push({
        role: 'user',
        content: query
    });

    // Clear input
    elements.queryInput.value = '';
    elements.queryInput.style.height = 'auto';

    // Set loading state
    state.isLoading = true;
    elements.sendBtn.disabled = true;
    showLoading();

    try {
        // Send query to API
        const response = await sendQuery(query);

        hideLoading();

        // Handle different response statuses
        if (response.status === 'needs_clarification') {
            addMessage(response.clarification_question, 'assistant');
            state.conversationHistory.push({
                role: 'assistant',
                content: response.clarification_question
            });
        } else if (response.status === 'success') {
            const resultMessage = `✅ Query executed successfully! Found ${response.results?.length || 0} results.`;
            addMessage(resultMessage, 'assistant', { sql: response.sql });

            state.conversationHistory.push({
                role: 'assistant',
                content: resultMessage
            });

            // Display results
            displayResults(response.results, response.sql, response.visualization_config);
        } else if (response.status === 'failed') {
            showError(response.error || 'Query execution failed');
            if (response.sql) {
                const lastMessage = elements.messagesContainer.lastElementChild;
                const sqlBlock = createSqlBlock(response.sql);
                lastMessage.appendChild(sqlBlock);
            }
        } else {
            showError('Unexpected response from server');
        }
    } catch (error) {
        hideLoading();
        showError(error.message || 'Failed to connect to the API. Please make sure the server is running.');
    } finally {
        state.isLoading = false;
        elements.sendBtn.disabled = false;
    }
}

function handleClearChat() {
    state.conversationHistory = [];
    state.conversationId = generateId();

    elements.messagesContainer.innerHTML = `
        <div class="welcome-message">
            <h2>👋 Welcome to DerivInsight</h2>
            <p>Ask me anything about your data in natural language. I'll convert it to SQL and show you the results!</p>
            <div class="welcome-features">
                <div class="feature">
                    <span class="feature-icon">🤖</span>
                    <span>AI-Powered Queries</span>
                </div>
                <div class="feature">
                    <span class="feature-icon">📊</span>
                    <span>Visual Analytics</span>
                </div>
                <div class="feature">
                    <span class="feature-icon">⚡</span>
                    <span>Real-time Results</span>
                </div>
            </div>
        </div>
    `;

    elements.resultsContent.innerHTML = `
        <div class="empty-state">
            <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
                <circle cx="60" cy="60" r="50" stroke="url(#emptyGradient)" stroke-width="2" opacity="0.3"/>
                <path d="M60 40v40M40 60h40" stroke="url(#emptyGradient)" stroke-width="2" stroke-linecap="round"/>
                <defs>
                    <linearGradient id="emptyGradient" x1="0" y1="0" x2="120" y2="120">
                        <stop offset="0%" stop-color="#6366f1"/>
                        <stop offset="100%" stop-color="#8b5cf6"/>
                    </linearGradient>
                </defs>
            </svg>
            <h3>No Results Yet</h3>
            <p>Run a query to see data visualizations and tables here</p>
        </div>
    `;
}

function handleDomainChange(domain) {
    state.selectedDomain = domain;

    // Update UI
    elements.domainBtns.forEach(btn => {
        if (btn.dataset.domain === domain) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function handleExampleClick(query) {
    elements.queryInput.value = query;
    elements.queryInput.focus();

    // Auto-adjust textarea height
    elements.queryInput.style.height = 'auto';
    elements.queryInput.style.height = elements.queryInput.scrollHeight + 'px';
}

function handleExport() {
    if (!state.currentResults || state.currentResults.length === 0) {
        alert('No data to export');
        return;
    }

    // Convert to CSV
    const columns = Object.keys(state.currentResults[0]);
    const csv = [
        columns.join(','),
        ...state.currentResults.map(row =>
            columns.map(col => {
                const value = row[col] ?? '';
                // Escape quotes and wrap in quotes if contains comma
                return typeof value === 'string' && value.includes(',')
                    ? `"${value.replace(/"/g, '""')}"`
                    : value;
            }).join(',')
        )
    ].join('\n');

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query-results-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

// ===========================
// Global Functions (for inline handlers)
// ===========================
window.copySqlToClipboard = function (btn) {
    const sqlBlock = btn.closest('.sql-block');
    const sqlCode = sqlBlock.querySelector('.sql-code').textContent;

    navigator.clipboard.writeText(sqlCode).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => {
            btn.textContent = 'Copy';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    });
};

// ===========================
// Event Listeners
// ===========================
elements.sendBtn.addEventListener('click', handleSendMessage);

elements.queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
});

// Auto-resize textarea
elements.queryInput.addEventListener('input', (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = e.target.scrollHeight + 'px';
});

elements.clearChatBtn.addEventListener('click', handleClearChat);

elements.apiUrlInput.addEventListener('change', (e) => {
    state.apiUrl = e.target.value.trim();
    checkApiConnection();
});

elements.domainBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        handleDomainChange(btn.dataset.domain);
    });
});

elements.exampleItems.forEach(item => {
    item.addEventListener('click', () => {
        handleExampleClick(item.dataset.query);
    });
});

elements.exportBtn.addEventListener('click', handleExport);

// ===========================
// Initialization
// ===========================
async function initialize() {
    console.log('🚀 Initializing DerivInsight Frontend...');

    // Check API connection
    await checkApiConnection();

    // Set initial domain
    handleDomainChange('general');

    // Focus input
    elements.queryInput.focus();

    console.log('✅ Initialization complete');
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}
