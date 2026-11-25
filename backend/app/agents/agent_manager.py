import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import WebSocket
from sqlalchemy.orm import Session
from app.models.agent import Agent

logger = logging.getLogger("querylens.agent_manager")

class AgentConnectionManager:
    def __init__(self):
        # agent_id -> WebSocket
        self.active_sockets: Dict[str, WebSocket] = {}
        # correlation_id -> asyncio.Future
        self.pending_requests: Dict[str, asyncio.Future] = {}

    def is_agent_online(self, agent_id: str) -> bool:
        return agent_id in self.active_sockets

    async def register_socket(self, agent_id: str, websocket: WebSocket):
        self.active_sockets[agent_id] = websocket
        logger.info(f"Agent {agent_id} connected via WebSocket.")

    def unregister_socket(self, agent_id: str):
        if agent_id in self.active_sockets:
            del self.active_sockets[agent_id]
            logger.info(f"Agent {agent_id} disconnected.")

    async def handle_incoming_message(self, agent_id: str, message_str: str, db: Session):
        try:
            data = json.loads(message_str)
            msg_type = data.get("type")
            correlation_id = data.get("correlation_id")

            if msg_type == "heartbeat":
                # Update heartbeat in DB
                agent = db.query(Agent).filter(Agent.id == agent_id).first()
                if agent:
                    agent.last_heartbeat = datetime.now(timezone.utc)
                    agent.status = "online"
                    db.commit()
                # Send heartbeat ack
                if agent_id in self.active_sockets:
                    await self.active_sockets[agent_id].send_text(json.dumps({"type": "heartbeat_ack"}))
                return

            if correlation_id and correlation_id in self.pending_requests:
                future = self.pending_requests[correlation_id]
                if not future.done():
                    future.set_result(data.get("payload"))

        except Exception as e:
            logger.error(f"Error handling message from agent {agent_id}: {e}")

    async def dispatch_command(self, agent_id: str, command_type: str, payload: Dict[str, Any], timeout: float = 35.0) -> Dict[str, Any]:
        if agent_id not in self.active_sockets:
            raise ConnectionError(f"Connector Agent '{agent_id}' is currently offline.")

        ws = self.active_sockets[agent_id]
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_requests[correlation_id] = future

        msg = {
            "type": command_type,
            "correlation_id": correlation_id,
            "payload": payload,
        }

        try:
            await ws.send_text(json.dumps(msg))
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Agent '{agent_id}' did not respond within {timeout}s.")
        finally:
            if correlation_id in self.pending_requests:
                del self.pending_requests[correlation_id]

agent_manager = AgentConnectionManager()
