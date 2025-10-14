#!/bin/bash

# Excel DataFrame Processor - Docker Run Script
# This script provides easy commands to run the Excel processor in Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DB_DIR="./sample_data"
IMAGE_NAME="excel-dataframe-processor"
CONTAINER_NAME="excel-processor"

# Help function
show_help() {
    echo -e "${BLUE}Excel DataFrame Processor - Docker Runner${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build                 Build the Docker image"
    echo "  run                   Run the CLI interactively"
    echo "  notebook              Start Jupyter notebook server"
    echo "  exec                  Execute a command in running container"
    echo "  stop                  Stop running containers"
    echo "  clean                 Remove containers and images"
    echo "  logs                  Show container logs"
    echo ""
    echo "Options:"
    echo "  --db-dir DIR          Database directory to mount (default: ./sample_data)"
    echo "  --port PORT           Port for notebook server (default: 8888)"
    echo "  --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build                                    # Build the image"
    echo "  $0 run                                      # Run CLI with default data dir"
    echo "  $0 run --db-dir /path/to/excel/files       # Run CLI with custom data dir"
    echo "  $0 notebook                                 # Start Jupyter notebook"
    echo "  $0 exec 'SELECT * FROM employees.staff'    # Execute SQL query"
    echo "  $0 logs                                     # Show logs"
}

# Build Docker image
build_image() {
    echo -e "${BLUE}Building Excel DataFrame Processor Docker image...${NC}"
    docker build -t $IMAGE_NAME .
    echo -e "${GREEN}✅ Image built successfully!${NC}"
}

# Run CLI interactively
run_cli() {
    echo -e "${BLUE}Starting Excel DataFrame Processor CLI...${NC}"
    echo -e "${YELLOW}Database directory: $DB_DIR${NC}"
    echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
    echo ""
    
    docker run -it --rm \
        --name $CONTAINER_NAME \
        -v "$(realpath $DB_DIR)":/data:ro \
        -v "$(pwd)/logs":/app/logs \
        $IMAGE_NAME
}

# Start Jupyter notebook
run_notebook() {
    local port=${1:-8888}
    echo -e "${BLUE}Starting Jupyter Notebook server...${NC}"
    echo -e "${YELLOW}Database directory: $DB_DIR${NC}"
    echo -e "${YELLOW}Notebook URL: http://localhost:$port${NC}"
    echo ""
    
    docker run -d \
        --name excel-notebook \
        -p $port:8888 \
        -v "$(realpath $DB_DIR)":/data:ro \
        -v "$(pwd)/notebooks":/app/notebooks \
        -v "$(pwd)/logs":/app/logs \
        -e JUPYTER_ENABLE_LAB=yes \
        excel-dataframe-processor \
        bash -c "pip install jupyter jupyterlab && jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"
    
    echo -e "${GREEN}✅ Notebook server started!${NC}"
    echo -e "${BLUE}Access at: http://localhost:$port${NC}"
}

# Execute command in container
exec_command() {
    local cmd="$1"
    echo -e "${BLUE}Executing command in container...${NC}"
    
    docker run --rm \
        -v "$(realpath $DB_DIR)":/data:ro \
        $IMAGE_NAME \
        python -c "
from excel_processor.notebook import ExcelProcessor
processor = ExcelProcessor('/data')
result = processor.query('$cmd')
print(result)
"
}

# Stop containers
stop_containers() {
    echo -e "${BLUE}Stopping Excel DataFrame Processor containers...${NC}"
    docker stop $CONTAINER_NAME excel-notebook 2>/dev/null || true
    docker rm $CONTAINER_NAME excel-notebook 2>/dev/null || true
    echo -e "${GREEN}✅ Containers stopped${NC}"
}

# Clean up
clean_up() {
    echo -e "${BLUE}Cleaning up Docker resources...${NC}"
    stop_containers
    docker rmi $IMAGE_NAME 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Show logs
show_logs() {
    local container=${1:-$CONTAINER_NAME}
    echo -e "${BLUE}Showing logs for $container...${NC}"
    docker logs -f $container
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --db-dir)
            DB_DIR="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        build)
            COMMAND="build"
            shift
            ;;
        run)
            COMMAND="run"
            shift
            ;;
        notebook)
            COMMAND="notebook"
            shift
            ;;
        exec)
            COMMAND="exec"
            EXEC_CMD="$2"
            shift 2
            ;;
        stop)
            COMMAND="stop"
            shift
            ;;
        clean)
            COMMAND="clean"
            shift
            ;;
        logs)
            COMMAND="logs"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Execute command
case $COMMAND in
    build)
        build_image
        ;;
    run)
        build_image
        run_cli
        ;;
    notebook)
        build_image
        run_notebook $PORT
        ;;
    exec)
        exec_command "$EXEC_CMD"
        ;;
    stop)
        stop_containers
        ;;
    clean)
        clean_up
        ;;
    logs)
        show_logs
        ;;
    *)
        echo -e "${RED}No command specified${NC}"
        show_help
        exit 1
        ;;
esac