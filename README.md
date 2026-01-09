# Polling-Based FastAPI + LangGraph Chat Architecture

A production-ready FastAPI application implementing a polling-based LangGraph architecture with MongoDB checkpointing. This system processes user queries through a multi-stage workflow and allows clients to poll for progress updates.

## Features

- **Single State Object Strategy**: All workflow state stored in a simple dictionary structure
- **Polling-based Architecture**: No WebSockets or SSE - simple HTTP polling
- **MongoDB Checkpointing**: Persistent state storage for workflow resumption
- **Background Execution**: Non-blocking workflow processing with `asyncio`
- **Progress Tracking**: Real-time progress updates through UI state
- **Production Ready**: Complete error handling, CORS support, and health checks

## Project Structure

```
polling-api/
├── main.py                          # FastAPI app + router inclusion
├── state.py                         # Single AppState TypedDict
├── controllers/
│   ├── __init__.py
│   └── chat_controller.py           # Single /chat POST endpoint
├── workflow/
│   ├── __init__.py
│   ├── graph.py                     # StateGraph assembly + MongoDBSaver
│   └── nodes/
│       ├── __init__.py
│       ├── orchestrator.py          # Entry point node
│       ├── report_identifier.py     # Report identification logic
│       ├── report_runner.py         # Report processing
│       └── summary_agent.py         # Final summary generation
├── requirements.txt                 # All dependencies
└── README.md                        # This file
```

## Prerequisites

- Python 3.9 or higher
- MongoDB (local or remote instance)

## MongoDB Setup

### Option 1: Docker (Recommended)

```bash
# Start MongoDB using Docker
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:latest
```

### Option 2: Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:latest
    container_name: mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

Start MongoDB:
```bash
docker-compose up -d
```

### Option 3: Local Installation

**macOS (Homebrew):**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Ubuntu/Debian:**
```bash
sudo apt-get install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

## Installation

1. **Clone or navigate to the project directory:**
```bash
cd polling-api
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Running the Application

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The application will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## API Usage

### Endpoint

**POST /chat** - Single endpoint for both creating new workflows and polling existing ones

### 1. Create New Workflow

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze Q4 sales report"}'
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "🚀 Starting analysis...",
  "current_node": "initializing",
  "progress": {"current": 0, "total": 4},
  "data": {},
  "retry_after": 2
}
```

### 2. Poll for Progress (First Poll)

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "🔍 Identifying relevant reports...",
  "current_node": "orchestrator",
  "progress": {"current": 1, "total": 4},
  "data": {"step": "orchestrator_complete", "user_query": "Analyze Q4 sales report"},
  "retry_after": 2
}
```

### 3. Poll for Progress (Second Poll)

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "📊 Processing sales_q4.pdf (1/2)",
  "current_node": "report_runner",
  "progress": {"current": 3, "total": 4},
  "data": {
    "reports": ["sales_q4.pdf", "revenue_q4.xlsx"],
    "step": "reports_identified"
  },
  "retry_after": 2
}
```

### 4. Final Poll (Completed)

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "✅ Q4 sales analysis complete: +23% YoY growth driven by strong product performance and customer acquisition",
  "current_node": "summary_agent",
  "progress": {"current": 4, "total": 4},
  "data": {
    "reports": ["sales_q4.pdf", "revenue_q4.xlsx"],
    "processed_reports": [
      {
        "file": "sales_q4.pdf",
        "type": "sales",
        "metrics": {
          "total_revenue": 2500000,
          "growth_yoy": "23%",
          "top_product": "Product A",
          "top_product_contribution": "60%"
        }
      },
      {
        "file": "revenue_q4.xlsx",
        "type": "revenue",
        "metrics": {
          "total_revenue": 2500000,
          "recurring_revenue": 1800000,
          "new_customers": 450,
          "churn_rate": "3.2%"
        }
      }
    ],
    "summary": "✅ Q4 sales analysis complete: +23% YoY growth driven by strong product performance and customer acquisition",
    "insights": [
      "Sales grew 23% year-over-year",
      "Product A drove 60% of growth",
      "Total revenue reached $2,500,000",
      "Acquired 450 new customers"
    ],
    "step": "completed"
  },
  "retry_after": null
}
```

## Frontend Integration Example

### JavaScript Fetch API

```javascript
async function analyzeReport(message) {
  // 1. Initiate workflow
  const initResponse = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });

  const { thread_id } = await initResponse.json();

  // 2. Poll for results
  while (true) {
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds

    const pollResponse = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id })
    });

    const result = await pollResponse.json();

    // Update UI with progress
    console.log(`${result.message} [${result.progress.current}/${result.progress.total}]`);

    if (result.status === 'completed' || result.status === 'failed') {
      return result;
    }
  }
}

// Usage
analyzeReport('Analyze Q4 sales report')
  .then(result => console.log('Final result:', result))
  .catch(error => console.error('Error:', error));
```

### React Example

```jsx
import { useState, useEffect } from 'react';

function ChatComponent() {
  const [threadId, setThreadId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState({ current: 0, total: 4 });
  const [data, setData] = useState({});

  const startWorkflow = async (userMessage) => {
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage })
    });

    const result = await response.json();
    setThreadId(result.thread_id);
    setStatus(result.status);
    setMessage(result.message);
    setProgress(result.progress);
  };

  useEffect(() => {
    if (!threadId || status === 'completed' || status === 'failed') return;

    const interval = setInterval(async () => {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId })
      });

      const result = await response.json();
      setStatus(result.status);
      setMessage(result.message);
      setProgress(result.progress);
      setData(result.data);

      if (result.status === 'completed' || result.status === 'failed') {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [threadId, status]);

  return (
    <div>
      <button onClick={() => startWorkflow('Analyze Q4 sales report')}>
        Start Analysis
      </button>
      <div>Status: {message}</div>
      <div>Progress: {progress.current}/{progress.total}</div>
      {status === 'completed' && (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      )}
    </div>
  );
}
```

## Workflow Stages

The application processes requests through four sequential stages:

1. **Orchestrator** - Initializes workflow and prepares for analysis
2. **Report Identifier** - Identifies relevant reports based on user query
3. **Report Runner** - Processes each identified report and extracts data
4. **Summary Agent** - Generates final summary and insights

## State Structure

All workflow data is stored in a single dictionary:

```python
{
  "state": {
    "message": "user input message",
    "ui": {
      "message": "Human readable status for UI",
      "current_node": "orchestrator|report_identifier|report_runner|summary_agent",
      "status": "running|completed|failed",
      "progress": {"current": 1, "total": 4}
    },
    "data": {
      "reports": ["sales_q4.pdf", "revenue_q4.xlsx"],
      "processed_reports": [...],
      "summary": "...",
      "insights": [...]
    }
  }
}
```

## Error Handling

The application includes comprehensive error handling:

- **400 Bad Request**: Neither `message` nor `thread_id` provided
- **404 Not Found**: Specified `thread_id` doesn't exist
- **500 Internal Server Error**: Graph execution or state retrieval errors

Failed workflows set `status: "failed"` with error details in the response.

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest
```

### Code Structure

- **Single State Strategy**: All data in one dictionary for minimal checkpoints
- **Background Execution**: Uses `asyncio.create_task()` for non-blocking processing
- **Idempotent Polling**: Safe to poll same `thread_id` multiple times
- **MongoDB Persistence**: Automatic checkpoint saving via LangGraph

## Production Considerations

1. **MongoDB Configuration**: Update connection string in `workflow/graph.py` for production MongoDB instance
2. **CORS Settings**: Configure `allow_origins` in `main.py` for specific domains
3. **Environment Variables**: Use `.env` file for sensitive configuration
4. **Logging**: Add structured logging for production monitoring
5. **Rate Limiting**: Implement rate limiting for the `/chat` endpoint
6. **Authentication**: Add authentication/authorization as needed

## Troubleshooting

### MongoDB Connection Issues

If you see "MongoDB connection failed" warnings:
1. Ensure MongoDB is running: `docker ps` or `brew services list`
2. Check connection string in `workflow/graph.py`
3. Verify network connectivity to MongoDB

### Import Errors

If you encounter import errors:
```bash
pip install --upgrade -r requirements.txt
```

### Port Already in Use

If port 8000 is already in use:
```bash
uvicorn main:app --reload --port 8001
```

## License

MIT

## Support

For issues and questions, please open an issue in the project repository.