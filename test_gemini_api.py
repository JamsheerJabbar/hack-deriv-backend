import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file")
    exit(1)

print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")

# Configure Gemini
try:
    genai.configure(api_key=api_key)
    print("✓ Gemini configured successfully")
except Exception as e:
    print(f"❌ Failed to configure Gemini: {e}")
    exit(1)

# Test with a simple prompt
try:
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    print("✓ Model initialized")
    
    response = model.generate_content("Say 'Hello World' and nothing else.")
    print(f"\n✅ API Test Successful!")
    print(f"Response: {response.text}")
    
except Exception as e:
    error_msg = str(e)
    print(f"\n❌ API Test Failed!")
    print(f"Error: {error_msg}")
    
    if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
        print("\n⚠️  DIAGNOSIS: Rate Limit / Quota Exceeded")
        print("   - Your API key has exceeded its request quota")
        print("   - Wait for quota reset (usually daily)")
        print("   - Or use a different API key")
        print("   - Or upgrade your API plan")
    elif "401" in error_msg or "403" in error_msg or "invalid" in error_msg.lower():
        print("\n⚠️  DIAGNOSIS: Invalid API Key")
        print("   - Check if the API key is correct")
        print("   - Verify the key is enabled in Google AI Studio")
    else:
        print("\n⚠️  DIAGNOSIS: Unknown Error")
        print("   - Check Google AI Studio status")
        print("   - Verify your API key permissions")
