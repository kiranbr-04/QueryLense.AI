import asyncio
import logging
import signal
import sys
from app.communication.client import AgentClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] QueryLensAgent: %(message)s",
)
logger = logging.getLogger("querylens.agent")

def main():
    client = AgentClient()

    def signal_handler(sig, frame):
        logger.info("Termination signal received. Shutting down agent gracefully...")
        client.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        logger.info("Agent stopped by user.")

if __name__ == "__main__":
    main()
