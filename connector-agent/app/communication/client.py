import asyncio
import json
import logging
import websockets
from app.config import agent_settings
from app.database.executor import LocalDatabaseExecutor

logger = logging.getLogger("querylens.agent.client")

class AgentClient:
    def __init__(self):
        self.executor = LocalDatabaseExecutor()
        self.running = True

    async def start(self):
        ws_url = f"{agent_settings.CLOUD_WS_URL.rstrip('/')}/{agent_settings.AGENT_TOKEN}"
        logger.info(f"Starting QueryLens Connector Agent '{agent_settings.AGENT_NAME}'...")
        logger.info(f"Target Cloud WebSocket URL: {ws_url}")

        retry_delay = 2
        max_retry_delay = 30

        while self.running:
            try:
                logger.info("Attempting outbound connection to QueryLens Cloud...")
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as ws:
                    logger.info("Connected successfully to QueryLens Cloud.")
                    retry_delay = 2  # Reset backoff on successful connection

                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))
                    receiver_task = asyncio.create_task(self._receiver_loop(ws))

                    done, pending = await asyncio.wait(
                        [heartbeat_task, receiver_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    for task in pending:
                        task.cancel()

            except (websockets.exceptions.ConnectionClosed, OSError) as e:
                logger.warning(f"Connection lost ({e}). Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
            except Exception as e:
                logger.error(f"Unexpected agent error: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)

    async def _heartbeat_loop(self, ws):
        while self.running:
            try:
                await ws.send(json.dumps({"type": "heartbeat"}))
                await asyncio.sleep(agent_settings.HEARTBEAT_INTERVAL_SECONDS)
            except Exception:
                break

    async def _receiver_loop(self, ws):
        while self.running:
            message_str = await ws.recv()
            try:
                msg = json.loads(message_str)
                msg_type = msg.get("type")
                correlation_id = msg.get("correlation_id")
                payload = msg.get("payload", {})

                if msg_type == "execute_sql":
                    sql = payload.get("sql", "")
                    limit = payload.get("limit", 500)
                    logger.info(f"Executing query [correlation_id={correlation_id}]")
                    res = self.executor.execute_query(sql, limit=limit)
                    await ws.send(json.dumps({
                        "type": "query_result",
                        "correlation_id": correlation_id,
                        "payload": res,
                    }))

                elif msg_type == "introspect_schema":
                    logger.info(f"Introspecting schema [correlation_id={correlation_id}]")
                    res = self.executor.introspect_schema()
                    await ws.send(json.dumps({
                        "type": "schema_result",
                        "correlation_id": correlation_id,
                        "payload": res,
                    }))

            except Exception as e:
                logger.error(f"Error processing command: {e}")

    def stop(self):
        self.running = False
