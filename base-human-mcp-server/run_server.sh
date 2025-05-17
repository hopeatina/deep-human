#!/bin/bash
# Script to run the human MCP server with different configurations

# Default values
CONFIG_FILE="base-human-mcp-server/hope_config.yaml"
TRANSPORT="http"
PORT="8000"
HOST="127.0.0.1"

# Help function
function show_help {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --config FILEPATH    Configuration file path (default: $CONFIG_FILE)"
    echo "  -t, --transport TYPE     Transport type: stdio, http, sse (default: $TRANSPORT)"
    echo "  -p, --port PORT          Port number for HTTP/SSE (default: $PORT)"
    echo "  -h, --host HOST          Host for HTTP/SSE (default: $HOST)"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --config base-human-mcp-server/hope_config.yaml --transport http --port 9000"
    echo "  $0 --config base-human-mcp-server/hanna_config.yaml --transport sse --port 9001"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -c|--config)
            CONFIG_FILE="$2"
            shift
            shift
            ;;
        -t|--transport)
            TRANSPORT="$2"
            shift
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift
            shift
            ;;
        -h|--host)
            HOST="$2"
            shift
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $key"
            show_help
            exit 1
            ;;
    esac
done

# Run the server with the specified options
echo "Starting server with config: $CONFIG_FILE"
echo "Transport: $TRANSPORT, Host: $HOST, Port: $PORT"

# Special handling for port 9001
if [ "$PORT" == "9001" ] && [ "$TRANSPORT" == "http" ]; then
    echo "Port 9001 detected with HTTP transport, switching to SSE transport"
    TRANSPORT="sse"
fi

# Activate virtual environment if needed
# source .venv/bin/activate

# Run the server
python base-human-mcp-server/server.py --config "$CONFIG_FILE" --transport "$TRANSPORT" --host "$HOST" --port "$PORT" 