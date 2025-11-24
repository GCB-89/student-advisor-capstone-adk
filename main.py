#!/usr/bin/env python3
"""
Bates Agent Launch Script

This script launches the Bates Technical College advisor agent using the Google ADK web interface.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def main():
    """Main function to launch the Bates agent web interface."""
    # Load environment variables from .env file
    load_dotenv("bates_agent/.env")
    
    # Verify that required environment variables are set
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        print("Please check your .env file in the bates_agent directory.")
        return 1
    
    # Get the current directory (should be the Bates Agent directory)
    current_dir = Path.cwd()
    venv_path = current_dir / ".venv" / "Scripts" / "adk.exe"
    
    if not venv_path.exists():
        print(f"❌ Error: ADK executable not found at {venv_path}")
        print("Please ensure the virtual environment is properly set up.")
        return 1
    
    print("🎓 Starting Bates Technical College Advisor Agent...")
    print("🌐 Launching web interface...")
    print("\n📝 The web interface will open automatically in your browser.")
    print("💡 You can ask about programs, courses, admissions, financial aid, and more!")
    print("\n⏹️  Press Ctrl+C to stop the server when you're done.\n")
    
    try:
        # Launch the ADK web interface
        # The current directory contains the bates_agent folder, which is our agent
        cmd = [
            str(venv_path),
            "web",
            ".",  # Current directory as the agents directory
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"  # Enable auto-reload for development
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        print("🌐 Opening web interface at: http://127.0.0.1:8000\n")
        
        # Run the command
        result = subprocess.run(cmd, cwd=current_dir)
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Thanks for using the Bates Agent!")
        return 0
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())