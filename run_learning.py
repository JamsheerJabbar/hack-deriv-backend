import asyncio
from app.modules.learning.trainer import train_all_domains

if __name__ == "__main__":
    asyncio.run(train_all_domains())
