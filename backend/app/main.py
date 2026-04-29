import os
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import delete, desc, func, insert, select, update

from .database import (
    get_database_url,
    get_engine,
    init_db,
    report_differences,
    reports,
    table_for_type,
)


MaterialType = Literal["gas", "vapor"]

app = FastAPI(title="Ceye Qx Inventory API")

frontend_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MaterialPayload(BaseModel):
    id: str | None = None
    name: str = Field(min_length=1)
    existing: int = 0
    counted: int = 0
    description: str = ""


class ReportDifferencePayload(BaseModel):
    material_id: str | None = None
    material_name: str | None = None
    existing_count: int | None = None
    counted_count: int | None = None
    id: str | None = None
    name: str | None = None
    existing: int | None = None
    counted: int | None = None
    room_count: int = 0
    process_count: int = 0
    difference: int | None = None


class ReportPayload(BaseModel):
    id: str | None = None
    type: MaterialType
    user_name: str = Field(min_length=1)
    shift: str = Field(min_length=1)
    differences: list[ReportDifferencePayload] = []


@app.on_event("startup")
def startup() -> None:
    init_db()


def row_to_dict(row) -> dict:
    return dict(row._mapping) if hasattr(row, "_mapping") else dict(row)


def normalize_material(row) -> dict:
    material = row_to_dict(row)
    return {
        "id": material["id"],
        "name": material["name"],
        "existing": material["existing"],
        "counted": material["counted"],
        "description": material["description"] or "",
        "created_at": material.get("created_at"),
        "updated_at": material.get("updated_at"),
    }


def normalize_difference(row) -> dict:
    diff = row_to_dict(row)
    return {
        "id": diff["material_id"],
        "name": diff["material_name"],
        "existing": diff["existing"],
        "counted": diff["counted"],
        "room_count": diff["room_count"],
        "process_count": diff["process_count"],
        "difference": diff["difference"],
        "description": "",
    }


def normalize_payload_differences(payload: ReportPayload) -> list[dict]:
    normalized = []
    for diff in payload.differences:
        material_id = diff.material_id or diff.id
        if not material_id:
            raise HTTPException(status_code=400, detail="Each difference needs a material id")

        existing = diff.existing_count if diff.existing_count is not None else diff.existing or 0
        counted = diff.counted_count if diff.counted_count is not None else diff.counted or 0
        difference = diff.difference if diff.difference is not None else counted - existing
        normalized.append(
            {
                "id": str(uuid4()),
                "material_id": material_id,
                "material_name": diff.material_name or diff.name or "",
                "existing": existing,
                "counted": counted,
                "room_count": diff.room_count,
                "process_count": diff.process_count,
                "difference": difference,
            }
        )
    return normalized


def build_report_response(report_row, differences: list[dict]) -> dict:
    report = row_to_dict(report_row)
    return {
        **report,
        "differences": differences,
    }


@app.get("/health")
def health() -> dict:
    database_kind = "PostgreSQL" if get_database_url().startswith("postgresql") else "SQLite"
    return {"status": "ok", "database": database_kind}


@app.get("/api/materials/{material_type}")
def get_materials(material_type: MaterialType) -> list[dict]:
    table = table_for_type(material_type)
    with get_engine().begin() as connection:
        rows = connection.execute(select(table).order_by(table.c.created_at)).fetchall()
    return [normalize_material(row) for row in rows]


@app.post("/api/materials/{material_type}", status_code=201)
def create_material(material_type: MaterialType, payload: MaterialPayload) -> dict:
    table = table_for_type(material_type)
    material_id = payload.id or str(uuid4())
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Material name is required")

    with get_engine().begin() as connection:
        try:
            connection.execute(
                insert(table).values(
                    id=material_id,
                    name=name,
                    existing=payload.existing,
                    counted=payload.counted,
                    description=payload.description,
                )
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        row = connection.execute(select(table).where(table.c.id == material_id)).first()

    return normalize_material(row)


@app.put("/api/materials/{material_type}/{material_id}")
def update_material(material_type: MaterialType, material_id: str, payload: MaterialPayload) -> dict:
    table = table_for_type(material_type)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Material name is required")

    with get_engine().begin() as connection:
        result = connection.execute(
            update(table)
            .where(table.c.id == material_id)
            .values(
                name=name,
                existing=payload.existing,
                counted=payload.counted,
                description=payload.description,
                updated_at=func.now(),
            )
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Material not found")

        row = connection.execute(select(table).where(table.c.id == material_id)).first()

    return normalize_material(row)


@app.delete("/api/materials/{material_type}/{material_id}")
def delete_material(material_type: MaterialType, material_id: str) -> dict:
    table = table_for_type(material_type)
    with get_engine().begin() as connection:
        result = connection.execute(delete(table).where(table.c.id == material_id))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Material not found")

    return {"message": "Deleted", "id": material_id}


@app.get("/api/reports")
def get_reports() -> list[dict]:
    result = []
    with get_engine().begin() as connection:
        report_rows = connection.execute(
            select(reports).order_by(desc(reports.c.created_at))
        ).fetchall()
        for report in report_rows:
            differences = connection.execute(
                select(report_differences)
                .where(report_differences.c.report_id == report._mapping["id"])
                .order_by(report_differences.c.created_at)
            ).fetchall()
            result.append(
                build_report_response(
                    report,
                    [normalize_difference(diff) for diff in differences],
                )
            )
    return result


@app.post("/api/reports", status_code=201)
def create_report(payload: ReportPayload) -> dict:
    report_id = payload.id or str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    user_name = payload.user_name.strip()
    shift = payload.shift.strip()
    if not user_name or not shift:
        raise HTTPException(status_code=400, detail="User name and shift are required")

    normalized = normalize_payload_differences(payload)

    with get_engine().begin() as connection:
        connection.execute(
            insert(reports).values(
                id=report_id,
                type=payload.type,
                user_name=user_name,
                shift=shift,
                timestamp=timestamp,
            )
        )
        if normalized:
            connection.execute(
                insert(report_differences),
                [{**diff, "report_id": report_id} for diff in normalized],
            )

    return {
        "id": report_id,
        "type": payload.type,
        "user_name": user_name,
        "shift": shift,
        "timestamp": timestamp,
        "differences": [
            {
                "id": diff["material_id"],
                "name": diff["material_name"],
                "existing": diff["existing"],
                "counted": diff["counted"],
                "room_count": diff["room_count"],
                "process_count": diff["process_count"],
                "difference": diff["difference"],
                "description": "",
            }
            for diff in normalized
        ],
    }


@app.put("/api/reports/{report_id}")
def update_report(report_id: str, payload: ReportPayload) -> dict:
    user_name = payload.user_name.strip()
    shift = payload.shift.strip()
    if not user_name or not shift:
        raise HTTPException(status_code=400, detail="User name and shift are required")

    normalized = normalize_payload_differences(payload)

    with get_engine().begin() as connection:
        result = connection.execute(
            update(reports)
            .where(reports.c.id == report_id)
            .values(type=payload.type, user_name=user_name, shift=shift)
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Report not found")

        connection.execute(delete(report_differences).where(report_differences.c.report_id == report_id))
        if normalized:
            connection.execute(
                insert(report_differences),
                [{**diff, "report_id": report_id} for diff in normalized],
            )
        report = connection.execute(select(reports).where(reports.c.id == report_id)).first()

    return build_report_response(
        report,
        [
            {
                "id": diff["material_id"],
                "name": diff["material_name"],
                "existing": diff["existing"],
                "counted": diff["counted"],
                "room_count": diff["room_count"],
                "process_count": diff["process_count"],
                "difference": diff["difference"],
                "description": "",
            }
            for diff in normalized
        ],
    )
