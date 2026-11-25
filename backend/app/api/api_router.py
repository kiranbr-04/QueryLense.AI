from fastapi import APIRouter
from app.api.v1 import (
    auth,
    organizations,
    connections,
    schema,
    query,
    history,
    agents,
    audit,
    api_connectors,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(connections.router)
api_router.include_router(schema.router)
api_router.include_router(query.router)
api_router.include_router(history.router)
api_router.include_router(agents.router)
api_router.include_router(audit.router)
api_router.include_router(api_connectors.router)
