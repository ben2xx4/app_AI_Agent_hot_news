from fastapi import APIRouter

from app.api.routes import chat, health, news, policies, prices, traffic, weather

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(news.router, tags=["news"])
api_router.include_router(prices.router, tags=["prices"])
api_router.include_router(weather.router, tags=["weather"])
api_router.include_router(policies.router, tags=["policies"])
api_router.include_router(traffic.router, tags=["traffic"])
api_router.include_router(chat.router, tags=["chat"])
