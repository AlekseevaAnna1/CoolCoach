from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.stats import StatsRead
from app.services.auth import get_current_user
from app.services.stats import get_user_stats

router = APIRouter()


# Календарь тренировок и краткая справка о прогрессе.
@router.get("", response_model=StatsRead)
async def read_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StatsRead:
    return await get_user_stats(db, current_user)
