from fastapi import APIRouter

from app.api.routes import assets, auth, blockchain, health, notes, steganography, system

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(steganography.router, prefix="/steganography", tags=["steganography"])
api_router.include_router(blockchain.router, prefix="/blockchain", tags=["blockchain"])
