import asyncio
from app.modules.learning import learning_service

async def update_all_domains():
    domains = ['compliance', 'risk', 'operations', 'security', 'general']
    for domain in domains:
        print(f"Updating {domain}...")
        await learning_service.discover_and_learn(domain)
        print(f"Done {domain}.")

if __name__ == "__main__":
    asyncio.run(update_all_domains())
