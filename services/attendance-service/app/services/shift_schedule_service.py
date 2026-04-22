import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_schedule import ShiftSchedule
from app.repositories.shift_schedule_repository import ShiftScheduleRepository
from app.repositories.geofence_repository import GeofenceRepository
from app.schemas.shift_schedule import ShiftScheduleCreate, ShiftScheduleUpdate

logger = logging.getLogger(__name__)


class ShiftScheduleService:
    def __init__(self, db: AsyncSession):
        self.repo = ShiftScheduleRepository(db)
        self.geofence_repo = GeofenceRepository(db)

    @staticmethod
    def _uuid_list(values):
        return [str(v) for v in values or []]

    async def _validate_references(self, shift_type_id: UUID, clock_in_ids: list, clock_out_ids: list) -> None:
        if not await self.repo.exists_shift_type(shift_type_id):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="shift_type_id must reference an active shift type")
        requested = {UUID(str(v)) for v in (clock_in_ids or [])} | {UUID(str(v)) for v in (clock_out_ids or [])}
        found = await self.geofence_repo.get_by_ids(list(requested))
        found_ids = {g.id for g in found}
        missing = requested - found_ids
        if missing:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown or inactive location id(s): {', '.join(str(x) for x in missing)}",
            )

    async def create(self, data: ShiftScheduleCreate) -> ShiftSchedule:
        if await self.repo.get_by_name(data.name):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Shift schedule '{data.name}' already exists")
        await self._validate_references(data.shift_type_id, data.allowed_clock_in_location_ids, data.allowed_clock_out_location_ids)
        schedule = ShiftSchedule(
            name=data.name,
            description=data.description,
            shift_type_id=data.shift_type_id,
            clock_in_start_time=data.clock_in_start_time,
            clock_in_end_time=data.clock_in_end_time,
            clock_out_start_time=data.clock_out_start_time,
            clock_out_end_time=data.clock_out_end_time,
            auto_clock_out_enabled=data.auto_clock_out_enabled,
            auto_clock_out_time=data.auto_clock_out_time,
            tasks_mandatory=data.tasks_mandatory,
            allowed_clock_in_location_ids=self._uuid_list(data.allowed_clock_in_location_ids),
            allowed_clock_out_location_ids=self._uuid_list(data.allowed_clock_out_location_ids),
            effective_from=data.effective_from,
            effective_to=data.effective_to,
        )
        result = await self.repo.create(schedule)
        logger.info("ShiftSchedule created: %s", result.id)
        return result

    async def get(self, schedule_id: UUID) -> ShiftSchedule:
        obj = await self.repo.get_by_id(schedule_id)
        if not obj:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Shift schedule {schedule_id} not found")
        return obj

    async def list_all(self, include_inactive: bool = False):
        return await self.repo.get_all(include_inactive=include_inactive)

    async def update(self, schedule_id: UUID, data: ShiftScheduleUpdate) -> ShiftSchedule:
        obj = await self.get(schedule_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != schedule_id:
                raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Shift schedule '{update_data['name']}' already exists")
        shift_type_id = update_data.get("shift_type_id", obj.shift_type_id)
        clock_in_ids = update_data.get("allowed_clock_in_location_ids", obj.allowed_clock_in_location_ids)
        clock_out_ids = update_data.get("allowed_clock_out_location_ids", obj.allowed_clock_out_location_ids)
        if "shift_type_id" in update_data or "allowed_clock_in_location_ids" in update_data or "allowed_clock_out_location_ids" in update_data:
            await self._validate_references(shift_type_id, clock_in_ids, clock_out_ids)
        if "allowed_clock_in_location_ids" in update_data:
            update_data["allowed_clock_in_location_ids"] = self._uuid_list(update_data["allowed_clock_in_location_ids"])
        if "allowed_clock_out_location_ids" in update_data:
            update_data["allowed_clock_out_location_ids"] = self._uuid_list(update_data["allowed_clock_out_location_ids"])
        return await self.repo.update(obj, update_data)

    async def soft_delete(self, schedule_id: UUID) -> ShiftSchedule:
        obj = await self.get(schedule_id)
        return await self.repo.update(obj, {"is_active": 0})
