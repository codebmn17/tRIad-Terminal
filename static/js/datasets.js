/**
 * Dataset Management JavaScript
 * Handles real-time updates via SSE and user interactions
 */

class DatasetManager {
    constructor() {
        this.eventSource = null;
        this.datasets = new Map();
        this.searchEnabled = false;

        this.init();
    }

    init() {
        this.bindEventListeners();
        this.connectToSSE();
        this.loadDatasets();
        this.checkSearchAvailability();
    }

    bindEventListeners() {
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadDatasets();
        });

        // Ingest all button
        document.getElementById('ingest-all-btn').addEventListener('click', () => {
            this.ingestAllDatasets();
        });

        // Clear logs button
        document.getElementById('clear-logs-btn').addEventListener('click', () => {
            this.clearLogs();
        });

        // Search functionality
        document.getElementById('search-btn').addEventListener('click', () => {
            this.performSearch();
        });

        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
    }

    async loadDatasets() {
        try {
            const response = await fetch('/datasets/list');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const datasets = await response.json();
            this.updateDatasetTable(datasets);

            // Store datasets in map
            this.datasets.clear();
            datasets.forEach(dataset => {
                this.datasets.set(dataset.id, dataset);
            });

            this.addLogEntry('info', `Loaded ${datasets.length} datasets`);

        } catch (error) {
            this.addLogEntry('error', `Failed to load datasets: ${error.message}`);
        }
    }

    updateDatasetTable(datasets) {
        const tbody = document.getElementById('dataset-list');
        tbody.innerHTML = '';

        datasets.forEach(dataset => {
            const row = this.createDatasetRow(dataset);
            tbody.appendChild(row);
        });
    }

    createDatasetRow(dataset) {
        const row = document.createElement('tr');
        row.setAttribute('data-dataset-id', dataset.id);

        // Dataset info
        const infoCell = document.createElement('td');
        infoCell.innerHTML = `
            <strong>${dataset.name}</strong><br>
            <small style="color: #888;">${dataset.description}</small>
        `;

        // Category
        const categoryCell = document.createElement('td');
        const categoryBadge = document.createElement('span');
        categoryBadge.className = `category-badge category-${dataset.category}`;
        categoryBadge.textContent = dataset.category;
        categoryCell.appendChild(categoryBadge);

        // Status
        const statusCell = document.createElement('td');
        const readyIndicator = dataset.ready ? '✅' : '⏳';
        statusCell.innerHTML = `${readyIndicator} ${dataset.ready ? 'Ready' : 'Processing'}`;
        if (dataset.error_message) {
            statusCell.innerHTML += `<br><small style="color: #ff4444;">${dataset.error_message}</small>`;
        }

        // Progress
        const progressCell = document.createElement('td');
        progressCell.innerHTML = this.createProgressBars(dataset.phases);

        // Actions
        const actionsCell = document.createElement('td');
        const ingestBtn = document.createElement('button');
        ingestBtn.className = 'btn';
        ingestBtn.textContent = 'Ingest';
        ingestBtn.style.fontSize = '12px';
        ingestBtn.style.padding = '4px 8px';
        ingestBtn.onclick = () => this.ingestDataset(dataset.id);
        actionsCell.appendChild(ingestBtn);

        row.appendChild(infoCell);
        row.appendChild(categoryCell);
        row.appendChild(statusCell);
        row.appendChild(progressCell);
        row.appendChild(actionsCell);

        return row;
    }

    createProgressBars(phases) {
        const phasesOrder = ['download', 'normalize', 'embed'];
        let html = '';

        phasesOrder.forEach(phase => {
            const status = phases[phase] || 'pending';
            const percentage = this.getPhaseProgress(status);

            html += `
                <div style="margin: 2px 0; font-size: 11px;">
                    <span style="display: inline-block; width: 70px;">${phase}:</span>
                    <span class="phase-status phase-${status}">${status}</span>
                    <div class="progress-bar" style="width: 100px; display: inline-block; margin-left: 8px;">
                        <div class="progress-fill progress-${status}" style="width: ${percentage}%"></div>
                    </div>
                </div>
            `;
        });

        return html;
    }

    getPhaseProgress(status) {
        switch (status) {
            case 'pending': return 0;
            case 'running': return 50;
            case 'completed': return 100;
            case 'error': return 100;
            case 'skipped': return 100;
            default: return 0;
        }
    }

    async ingestDataset(datasetId, force = false) {
        try {
            const response = await fetch('/datasets/ingest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dataset_id: datasetId,
                    force: force
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            this.addLogEntry('success', result.message);

        } catch (error) {
            this.addLogEntry('error', `Failed to start ingestion for ${datasetId}: ${error.message}`);
        }
    }

    async ingestAllDatasets() {
        try {
            const datasetIds = Array.from(this.datasets.keys());

            const response = await fetch('/datasets/ingest/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dataset_ids: datasetIds,
                    force: false
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            this.addLogEntry('success', result.message);

        } catch (error) {
            this.addLogEntry('error', `Failed to start batch ingestion: ${error.message}`);
        }
    }

    async checkSearchAvailability() {
        try {
            const response = await fetch('/datasets/embeddings/status');
            if (response.ok) {
                const status = await response.json();
                this.searchEnabled = status.enabled;

                if (this.searchEnabled) {
                    document.getElementById('search-section').style.display = 'block';
                    this.addLogEntry('info', `Search enabled with ${status.backend} (${status.model})`);
                } else {
                    this.addLogEntry('info', 'Search disabled - set ENABLE_EMBEDDINGS=1 to enable');
                }
            }
        } catch (error) {
            this.addLogEntry('warning', `Could not check search status: ${error.message}`);
        }
    }

    async performSearch() {
        if (!this.searchEnabled) {
            this.addLogEntry('warning', 'Search is not enabled');
            return;
        }

        const query = document.getElementById('search-input').value.trim();
        if (!query) return;

        try {
            const response = await fetch('/datasets/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    limit: 10
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            this.displaySearchResults(result);

        } catch (error) {
            this.addLogEntry('error', `Search failed: ${error.message}`);
        }
    }

    displaySearchResults(result) {
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.innerHTML = '';

        if (result.results.length === 0) {
            resultsDiv.innerHTML = '<div style="color: #888; padding: 10px;">No results found</div>';
            return;
        }

        result.results.forEach(item => {
            const resultDiv = document.createElement('div');
            resultDiv.className = 'search-result';
            resultDiv.innerHTML = `
                <div class="search-result-score">Score: ${item.score.toFixed(3)}</div>
                <div><strong>Dataset:</strong> ${item.dataset_id}</div>
                <div class="search-result-content">${item.content}</div>
            `;
            resultsDiv.appendChild(resultDiv);
        });

        this.addLogEntry('info', `Found ${result.total} results in ${result.took_ms.toFixed(1)}ms`);
    }

    connectToSSE() {
        if (this.eventSource) {
            this.eventSource.close();
        }

        this.eventSource = new EventSource('/datasets/stream');

        this.eventSource.addEventListener('open', () => {
            this.updateConnectionStatus('connected');
            this.addLogEntry('info', 'Connected to real-time updates');
        });

        this.eventSource.addEventListener('dataset-event', (event) => {
            const data = JSON.parse(event.data);
            this.handleDatasetEvent(data);
        });

        this.eventSource.addEventListener('error', () => {
            this.updateConnectionStatus('disconnected');
            this.addLogEntry('warning', 'Connection to real-time updates lost, attempting to reconnect...');

            // Attempt to reconnect after a delay
            setTimeout(() => {
                if (this.eventSource.readyState === EventSource.CLOSED) {
                    this.connectToSSE();
                }
            }, 5000);
        });

        this.updateConnectionStatus('connecting');
    }

    handleDatasetEvent(event) {
        const { type, data } = event;

        switch (type) {
            case 'ingestion_started':
                this.addLogEntry('info', `Started ingestion for ${data.dataset_id}`);
                break;

            case 'phase_started':
                this.addLogEntry('info', `${data.dataset_id}: Started ${data.phase} phase`);
                this.updateDatasetPhase(data.dataset_id, data.phase, 'running');
                break;

            case 'phase_completed':
                this.addLogEntry('success', `${data.dataset_id}: Completed ${data.phase} phase`);
                this.updateDatasetPhase(data.dataset_id, data.phase, 'completed');
                break;

            case 'phase_error':
                this.addLogEntry('error', `${data.dataset_id}: Error in ${data.phase} phase - ${data.error}`);
                this.updateDatasetPhase(data.dataset_id, data.phase, 'error');
                break;

            case 'ingestion_completed':
                this.addLogEntry('success', `Completed ingestion for ${data.dataset_id} (Ready: ${data.ready})`);
                // Refresh dataset info
                this.loadDatasets();
                break;

            case 'ingestion_error':
                this.addLogEntry('error', `Ingestion error for ${data.dataset_id}: ${data.error}`);
                break;
        }
    }

    updateDatasetPhase(datasetId, phase, status) {
        const row = document.querySelector(`tr[data-dataset-id="${datasetId}"]`);
        if (!row) return;

        // Update the progress bars in the row
        const progressCell = row.querySelector('td:nth-child(4)');
        if (progressCell) {
            // Update the dataset in memory
            if (this.datasets.has(datasetId)) {
                const dataset = this.datasets.get(datasetId);
                dataset.phases[phase] = status;

                // Regenerate progress bars
                progressCell.innerHTML = this.createProgressBars(dataset.phases);
            }
        }
    }

    updateConnectionStatus(status) {
        const statusSpan = document.getElementById('connection-status');
        const indicator = document.getElementById('status-indicator');

        statusSpan.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        indicator.className = `status-indicator status-${status}`;
    }

    addLogEntry(type, message) {
        const logArea = document.getElementById('log-area');
        const entry = document.createElement('div');
        entry.className = `log-entry log-${type}`;

        const timestamp = new Date().toLocaleTimeString();
        entry.textContent = `[${timestamp}] ${message}`;

        logArea.appendChild(entry);
        logArea.scrollTop = logArea.scrollHeight;

        // Keep only last 100 log entries
        const entries = logArea.querySelectorAll('.log-entry');
        if (entries.length > 100) {
            entries[0].remove();
        }
    }

    clearLogs() {
        const logArea = document.getElementById('log-area');
        logArea.innerHTML = '<div class="log-entry log-info">Logs cleared</div>';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.datasetManager = new DatasetManager();
});
