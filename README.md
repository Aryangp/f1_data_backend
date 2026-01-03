# F1 Race Telemetry Backend

A high-performance FastAPI backend for processing and serving Formula 1 race telemetry data. This application integrates with `fastf1` to provide real-time race data, utilizing efficient caching and WebSocket streaming for a seamless user experience.

## Features

-   ✅ **FastAPI**: Modern, fast (high-performance), web framework for building APIs with Python.
-   ✅ **F1 Telemetry**: Real-time integration with `fastf1` to fetch and process race data.
-   ✅ **WebSocket Support**: Real-time progress updates for long-running telemetry processing tasks.
-   ✅ **Efficient Data Handling**:
    -   Using `orjson` for fast JSON serialization.
    -   Gzip compression for optimized network transfer.
    -   NumPy integration for high-performance numerical operations.
-   ✅ **Smart Caching**: Local caching system to minimize redundant computations and external API calls.
-   ✅ **S3 Integration**: Capability to upload processed telemetry to AWS S3.
-   ✅ **Docker Ready**: containerized for easy deployment and scalability.
-   ✅ **Type Safety**: Comprehensive type hints using Pydantic schemas.

## Project Structure

```
.
├── app/
│   ├── main.py              # Main FastAPI application entry point
│   ├── config.py            # Application settings and configuration
│   ├── routers/             # API route definitions
│   │   ├── f1.py            # F1 telemetry endpoints (HTTP & WS)
│   │   ├── health.py        # Health check endpoints
│   │   └── api.py           # Example API endpoints
│   ├── services/            # Business logic and external integrations
│   │   ├── f1_telemetry.py  # Core telemetry processing logic
│   │   ├── f1_s3_bucket.py  # S3 upload functionality
│   │   └── ...
│   ├── schemas/             # Pydantic models for data validation
│   └── utils/               # Helper utilities
├── computed_data/           # Directory for local cached telemetry files
├── .fastf1-cache/           # FastF1 internal cache
├── Dockerfile               # Docker build instructions
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

## Setup & Installation

### Local Development

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file (copy from `.env.example` if available) or set via shell.

4.  **Run the application:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be accessible at `http://localhost:8000`.

### Docker

1.  **Build the image:**
    ```bash
    docker build -t f1-race-backend .
    ```

2.  **Run the container:**
    ```bash
    docker run -p 8000:8000 f1-race-backend
    ```

### AWS Deployment (Automated)

This project uses Terraform for infrastructure provisioning and GitHub Actions for CI/CD.

#### 1. Resource Provisioning (One-time)
1.  Navigate to the `terraform/` directory.
2.  Initialize and apply Terraform:
    ```bash
    terraform init
    terraform apply
    ```
    Confirm with `yes`.
3.  **IMPORTANT:** Note the outputs:
    -   `instance_public_ip`: IP of your backend.
    -   `ecr_repository_url`: Your Docker registry.
    -   `private_key_pem`: Save this content to a file (e.g., `f1-key.pem`) to SSH into your instance if needed.

#### 2. GitHub Secrets Configuration
Go to your repository Settings > Secrets and variables > Actions, and add:
-   `AWS_ACCESS_KEY_ID`: Your AWS Access Key.
-   `AWS_SECRET_ACCESS_KEY`: Your AWS Secret Key.
-   `AWS_REGION`: `us-east-1` (or your chosen region).
-   `EC2_HOST`: The `instance_public_ip` from Terraform.
-   `EC2_SSH_KEY`: The content of `private_key_pem` from Terraform.

#### 3. Deploy
Push to the `main` branch. GitHub Actions will build the container, push to ECR, and auto-deploy to your EC2 instance.

## API Documentation

Interactive API documentation is available at:
-   **Swagger UI**: http://localhost:8000/docs
-   **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### F1 Telemetry

-   **Get Race Telemetry (GET)**
    `GET /f1/race-telemetry/{year}/{round_number}`
    Fetches processed telemetry for a specific race. Supports `frame_skip` and `compress` parameters for optimization.

-   **Get Race Telemetry (POST)**
    `POST /f1/race-telemetry`
    Alternative to GET, allowing complex request bodies.

-   **Process Telemetry (WebSocket)**
    `WS /f1/process-telemetry/{year}/{round_number}`
    Connect to this endpoint to trigger telemetry processing and receive real-time progress updates (0-100%).
    
    **Messages:**
    -   `{"type": "progress", "progress": 50.0, "message": "..."}`
    -   `{"type": "complete", "data": {...}}`
    -   `{"type": "error", "message": "..."}`

-   **Get Available Sessions**
    `GET /f1/sessions/{year}`
    Returns a list of all race events for the specified season.

#### Health

-   `GET /health/` - Service health status
-   `GET /health/live` - Liveness probe
-   `GET /health/ready` - Readiness probe

## Development

### Running tests
(Add test instructions if pytest is configured)
```bash
pytest
```

## License

MIT
