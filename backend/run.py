"""
Flipkart Gridlock — Entry Point
One-command startup: python run.py

Creates directories, initializes database, optionally seeds demo data,
and starts the uvicorn server.
"""
import argparse
import sys
from pathlib import Path

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    parser = argparse.ArgumentParser(description="Flipkart Gridlock Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument("--seed", action="store_true", help="Seed demo data")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    args = parser.parse_args()

    # Create required directories
    from config import OUTPUT_DIR, UPLOADS_DIR, EVIDENCE_DIR, MODELS_DIR
    for d in [OUTPUT_DIR, UPLOADS_DIR, EVIDENCE_DIR, MODELS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Initialize database
    from app.database import init_db
    init_db()

    # Initialize zones
    from logic.zone_manager import init_zones
    init_zones()

    # Seed demo data if requested
    if args.seed:
        from utils.demo_seeder import seed_demo_data
        seed_demo_data()

    # Start server
    import uvicorn
    print(f"""
==============================================================
           FLIPKART GRIDLOCK - Traffic Violation             
              Detection System v1.0.0                        
==============================================================
  API Docs:   http://{args.host}:{args.port}/docs                    
  Dashboard:  http://localhost:3000                          
  WebSocket:  ws://{args.host}:{args.port}/ws/stream                 
==============================================================
    """)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info",
    )


if __name__ == "__main__":
    main()
