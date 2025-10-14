# 🐳 Excel DataFrame Processor - Docker Setup

Run the Excel DataFrame Processor CLI in a containerized environment with easy database directory mounting.

## 🚀 Quick Start

### 1. Build and Run CLI
```bash
# Build image and run CLI interactively
./docker-run.sh run

# Or with custom database directory
./docker-run.sh run --db-dir /path/to/your/excel/files
```

### 2. Start Jupyter Notebook
```bash
# Start notebook server on port 8888
./docker-run.sh notebook

# Access at: http://localhost:8888
```

### 3. Execute Single Query
```bash
# Execute a SQL query directly
./docker-run.sh exec "SELECT * FROM employees.staff WHERE salary > 70000"
```

## 📋 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `build` | Build Docker image | `./docker-run.sh build` |
| `run` | Start interactive CLI | `./docker-run.sh run --db-dir ./data` |
| `notebook` | Start Jupyter server | `./docker-run.sh notebook --port 8888` |
| `exec` | Execute single query | `./docker-run.sh exec "SHOW DB"` |
| `stop` | Stop all containers | `./docker-run.sh stop` |
| `clean` | Remove containers/images | `./docker-run.sh clean` |
| `logs` | Show container logs | `./docker-run.sh logs` |

## 🔧 Manual Docker Commands

### Build Image
```bash
docker build -t excel-dataframe-processor .
```

### Run CLI with Volume Mount
```bash
docker run -it --rm \
  -v /path/to/excel/files:/data:ro \
  -v ./logs:/app/logs \
  excel-dataframe-processor
```

### Run Jupyter Notebook
```bash
docker run -d \
  --name excel-notebook \
  -p 8888:8888 \
  -v /path/to/excel/files:/data:ro \
  -v ./notebooks:/app/notebooks \
  excel-dataframe-processor \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

## 📁 Directory Structure

```
your-project/
├── excel-files/          # Your Excel/CSV files (mounted to /data)
├── logs/                 # Application logs (optional)
├── notebooks/            # Jupyter notebooks (optional)
├── Dockerfile            # Main CLI image
├── Dockerfile.notebook   # Jupyter image
├── docker-compose.yml    # Multi-service setup
└── docker-run.sh         # Convenience script
```

## 🐳 Docker Compose

For a complete setup with both CLI and notebook services:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔒 Security Features

- **Non-root user**: Runs as `exceluser` for security
- **Read-only mounts**: Database directory mounted read-only
- **Health checks**: Built-in container health monitoring
- **Minimal base**: Uses Python slim image for smaller attack surface

## 📊 Usage Examples

### Interactive CLI Session
```bash
./docker-run.sh run --db-dir ./sample_data

# Inside container:
excel> SHOW DB
excel> SELECT * FROM employees.staff WHERE salary > 70000
excel> SELECT department, COUNT(*) FROM employees.staff GROUP BY department
excel> EXIT
```

### Jupyter Notebook
```bash
./docker-run.sh notebook

# Open browser to http://localhost:8888
# Run the demo notebook: Excel_DataFrame_Processor_Demo_Fixed.ipynb
```

### Batch Processing
```bash
# Execute multiple queries
./docker-run.sh exec "LOAD DB"
./docker-run.sh exec "SELECT COUNT(*) FROM employees.staff"
./docker-run.sh exec "SELECT * FROM employees.staff > /app/logs/export.csv"
```

## 🛠️ Customization

### Environment Variables
- `EXCEL_DB_DIR`: Database directory path (default: `/data`)
- `PYTHONUNBUFFERED`: Python output buffering (default: `1`)

### Volume Mounts
- `/data`: Excel/CSV files directory (read-only recommended)
- `/app/logs`: Application logs directory
- `/app/notebooks`: Jupyter notebooks directory

### Port Configuration
- `8888`: Jupyter Lab server (configurable)
- `8080`: Reserved for future web interface

## 🔍 Troubleshooting

### Container Won't Start
```bash
# Check logs
./docker-run.sh logs

# Verify image
docker images | grep excel-dataframe-processor
```

### Permission Issues
```bash
# Ensure directories exist and are readable
ls -la /path/to/excel/files
chmod -R 755 /path/to/excel/files
```

### Memory Issues
```bash
# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory
```

## 🎯 Production Deployment

For production use, consider:

1. **Resource Limits**:
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

2. **Persistent Volumes**:
```yaml
volumes:
  excel_data:
    driver: local
```

3. **Security Scanning**:
```bash
docker scan excel-dataframe-processor
```

4. **Multi-stage Build** (for smaller images):
```dockerfile
FROM python:3.11-slim as builder
# ... build dependencies
FROM python:3.11-slim as runtime
# ... runtime only
```

## 📈 Performance Tips

- **Memory**: Allocate sufficient memory for large Excel files
- **CPU**: Multi-core helps with complex queries
- **Storage**: Use SSD for better I/O performance
- **Network**: Local volumes perform better than network mounts

Ready to analyze your Excel data with SQL in Docker! 🚀📊