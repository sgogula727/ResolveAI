from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine #created a DB engine that works with async I/O
#async_sessionmaker is a factory for creating async sessions, AsyncSession is the session type used in routed
from .config import settings
from .models import Base #Base is the SQLAlchemy model from models.py, contains all my mdoels


#settings.database_url comes from backend/config.py, future=True uses SQLAclhemy 2.0 style, echo= False mean no SQL logging by default
engine = create_async_engine(settings.database_url, future=True, echo=False)
#creates the session maker, expire_on_commit=False means that objects won't be expired after commit, class_=AsyncSession makes sure async sessions are created
#this is what fastapi routes will use to interact with the database
async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

#creates all tables defined in models.py, call it once on startup, replace with Alembic migrations in production
async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all) #creates all the tables

#lets FastAPI iject a DB session via Depends(get_session), guarentees session closes after request
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
