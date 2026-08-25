from fastapi import APIRouter

from app.api.routes import agent_runtime, agents, crawls, customer_service, data_analyst, document_intelligence, documents, health, knowledge_bases, rag, users, workspaces

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(workspaces.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(agents.router)
api_router.include_router(documents.router)
api_router.include_router(crawls.router)
api_router.include_router(rag.router)
api_router.include_router(agent_runtime.router)
api_router.include_router(data_analyst.router)
api_router.include_router(customer_service.router)
api_router.include_router(document_intelligence.router)
