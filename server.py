import uvicorn
import sys

def run_server():
    """Run the FastAPI server."""
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()