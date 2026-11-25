import secrets
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database.session import get_db, SessionLocal
from app.models.agent import Agent
from app.models.user import User
from app.schemas.agent import AgentRegisterRequest, AgentResponse, AgentStatusResponse
from app.api.deps import get_current_user, get_current_admin
from app.agents.agent_manager import agent_manager
from app.security.audit_logger import log_audit_event

router = APIRouter(prefix="/agents", tags=["Connector Agents"])

@router.post("/register", response_model=AgentResponse)
def register_agent(
    data: AgentRegisterRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Generate registration token for an on-premise QueryLens Connector Agent."""
    token = f"qlagent_{secrets.token_urlsafe(32)}"
    agent = Agent(
        organization_id=current_admin.organization_id,
        name=data.name,
        agent_token=token,
        status="offline",
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    log_audit_event(
        db,
        organization_id=current_admin.organization_id,
        action="AGENT_REGISTER",
        resource_type="agent",
        resource_id=agent.id,
        details={"agent_name": agent.name},
        user_id=current_admin.id,
        user_email=current_admin.email,
    )
    return agent

@router.get("", response_model=List[AgentResponse])
def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agents = db.query(Agent).filter(Agent.organization_id == current_user.organization_id).all()
    # Update status dynamically based on active websocket presence
    for a in agents:
        if a.is_revoked:
            a.status = "revoked"
        elif agent_manager.is_agent_online(a.id):
            a.status = "online"
        else:
            a.status = "offline"
    return agents

@router.get("/{agent_id}/status", response_model=AgentStatusResponse)
def get_agent_status(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id, Agent.organization_id == current_user.organization_id)
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    is_online = agent_manager.is_agent_online(agent.id) and not agent.is_revoked
    return AgentStatusResponse(
        id=agent.id,
        name=agent.name,
        status="revoked" if agent.is_revoked else ("online" if is_online else "offline"),
        is_online=is_online,
        last_heartbeat=agent.last_heartbeat,
    )

@router.post("/{agent_id}/revoke")
def revoke_agent(
    agent_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id, Agent.organization_id == current_admin.organization_id)
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    agent.is_revoked = True
    agent.status = "revoked"
    db.commit()

    # Disconnect active socket if any
    if agent_id in agent_manager.active_sockets:
        agent_manager.unregister_socket(agent_id)

    log_audit_event(
        db,
        organization_id=current_admin.organization_id,
        action="AGENT_REVOKE",
        resource_type="agent",
        resource_id=agent.id,
        user_id=current_admin.id,
        user_email=current_admin.email,
    )
    return {"message": "Agent revoked successfully."}

@router.websocket("/connect/{agent_token}")
async def agent_websocket_endpoint(websocket: WebSocket, agent_token: str):
    """
    Secure outbound WebSocket endpoint for QueryLens Connector Agent.
    The on-premise agent establishes an outbound connection to this endpoint.
    """
    await websocket.accept()
    db: Session = SessionLocal()
    agent = None

    try:
        agent = db.query(Agent).filter(Agent.agent_token == agent_token).first()
        if not agent or agent.is_revoked:
            await websocket.close(code=4003, reason="Unauthorized or revoked agent token.")
            return

        agent.status = "online"
        agent.last_heartbeat = datetime.now(timezone.utc)
        if websocket.client:
            agent.ip_address = websocket.client.host
        db.commit()

        await agent_manager.register_socket(agent.id, websocket)

        while True:
            data = await websocket.receive_text()
            await agent_manager.handle_incoming_message(agent.id, data, db)

    except WebSocketDisconnect:
        if agent:
            agent_manager.unregister_socket(agent.id)
            agent.status = "offline"
            db.commit()
    except Exception as e:
        if agent:
            agent_manager.unregister_socket(agent.id)
            agent.status = "offline"
            db.commit()
    finally:
        db.close()
