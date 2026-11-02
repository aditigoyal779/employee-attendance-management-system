from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlmodel.ext.asyncio.session import AsyncSession

MYSQL_CONNECTION_STRING = "mysql+aiomysql://root:@localhost:3306/employee_management"

# Create the async engine
engine = create_async_engine(
    MYSQL_CONNECTION_STRING,
    pool_pre_ping=True,  # Tests connection health before use
    pool_size=10,  # Number of permanent connections to keep
    max_overflow=20  # Extra connections allowed during high traffic
)

# Create base class for database models
Base = declarative_base()

# Create the async session factory
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
    class_=AsyncSession
)


# Dependency for FastAPI routes
async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
