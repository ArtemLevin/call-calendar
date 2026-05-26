from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.colleague import Colleague


class ColleagueRepository:
    DEFAULT_COLLEAGUE_ID = 1

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[Colleague]:
        stmt: Select[tuple[Colleague]] = select(Colleague).order_by(Colleague.id.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, colleague_id: int) -> Colleague | None:
        stmt: Select[tuple[Colleague]] = select(Colleague).where(Colleague.id == colleague_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
