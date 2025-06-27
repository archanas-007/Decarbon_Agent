#!/usr/bin/env python3
"""
Helper script to set up environment variables for the Decarbon AI system.
"""

import os
import sys

def setup_environment():
    """Set up environment variables."""
    print("🧠 Decarbon AI Master Brain - Environment Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ Found existing {env_file} file")
        with open(env_file, 'r') as f:
            content = f.read()
            if 'GEMINI_API_KEY' in content:
                print("✅ Gemini API key is already configured")
                return
    else:
        print(f"📝 Creating new {env_file} file")
    
    # Get API key from user
    print("\n🔑 To enable full AI functionality, you need a Gemini API key.")
    print("   Get one from: https://makersuite.google.com/app/apikey")
    print()
    
    api_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("\n⚠️  No API key provided. System will run in demo mode.")
        api_key = "your_gemini_api_key_here"
    
    # Write .env file
    env_content = f"""# Gemini API Configuration
GEMINI_API_KEY={api_key}

# System Configuration
LOG_LEVEL=INFO
SIMULATION_SPEED=1.0
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ {env_file} file created successfully!")
        
        if api_key != "your_gemini_api_key_here":
            print("🎉 Full AI functionality is now enabled!")
            print("   Restart your Streamlit applications to see the changes.")
        else:
            print("📝 To enable AI later, edit the .env file and add your API key.")
            
    except Exception as e:
        print(f"❌ Error creating {env_file}: {e}")
        print("   Please create the file manually with your API key.")

def check_environment():
    """Check if environment is properly set up."""
    print("\n🔍 Environment Check")
    print("=" * 30)
    
    # Check .env file
    if os.path.exists(".env"):
        print("✅ .env file exists")
        with open(".env", 'r') as f:
            content = f.read()
            if 'GEMINI_API_KEY' in content and 'your_gemini_api_key_here' not in content:
                print("✅ Gemini API key is configured")
                return True
            else:
                print("⚠️  Gemini API key not configured (demo mode)")
                return False
    else:
        print("❌ .env file not found")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_environment()
    else:
        setup_environment() 