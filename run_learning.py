import asyncio
import json
from app.modules.domain_adapter import domain_adapter

async def main():
    domains = ["general", "security", "compliance", "risk", "operations"]
    
    print(f"🚀 Starting Autonomous Discovery for {len(domains)} domains...")
    
    for domain in domains:
        print(f"\n[{domain.upper()}] Discovering...")
        try:
            success, message = await domain_adapter.discover_and_learn(domain)
            if success:
                print(f"✅ Learned {domain}: {message}")
            else:
                print(f"❌ Failed {domain}: {message}")
        except Exception as e:
            print(f"❌ Error {domain}: {e}")

    print("\n✨ All domains updated! Check app/data/domains/ folder.")

if __name__ == "__main__":
    asyncio.run(main())
