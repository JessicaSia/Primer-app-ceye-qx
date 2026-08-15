import os
import hashlib
import re
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import and_, delete, desc, func, insert, select, text, update

from .database import (
    areas,
    custom_materials,
    get_database_url,
    get_engine,
    init_db,
    material_lists,
    organizations,
    report_differences,
    reports,
    table_for_type,
    user_sessions,
    users,
)


MaterialType = Literal["gas", "vapor"]
UserRole = Literal["admin", "nurse", "supervisor", "readonly"]
ROLE_LABELS = {
    "admin": "Administrador",
    "nurse": "Enfermeria",
    "supervisor": "Supervisor/jefatura",
    "readonly": "Solo lectura",
}
ALL_ROLES = set(ROLE_LABELS)

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


class MaterialTypeChangePayload(MaterialPayload):
    type: MaterialType


class MaterialOrderPayload(BaseModel):
    ids: list[str]


class MaterialListPayload(BaseModel):
    name: str = Field(min_length=1)


class AreaPayload(BaseModel):
    name: str = Field(min_length=1)


class CustomMaterialMovePayload(MaterialPayload):
    target_list_id: str = Field(min_length=1)


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
    type: str = Field(min_length=1)
    user_name: str = Field(min_length=1)
    shift: str = Field(min_length=1)
    duration_seconds: int = 0
    differences: list[ReportDifferencePayload] = []


class LoginPayload(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=1)


class UserPayload(BaseModel):
    name: str = Field(min_length=1)
    username: str = Field(min_length=3)
    password: str = Field(min_length=6)
    role: UserRole
    area_id: str | None = None


class UserUpdatePayload(BaseModel):
    name: str | None = None
    username: str | None = None
    password: str | None = None
    role: UserRole | None = None
    area_id: str | None = None


@app.on_event("startup")
def startup() -> None:
    init_db()


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    return secrets.compare_digest(hash_password(password, salt), password_hash)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalize_username(value: str) -> str:
    username = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+", username):
        raise HTTPException(
            status_code=400,
            detail="El nombre de usuario solo puede usar letras y numeros",
        )
    return username


def local_email_for_username(username: str) -> str:
    return f"{username}@ceye.local"


def normalize_user(row) -> dict:
    user = row_to_dict(row)
    return {
        "id": user["id"],
        "organization_id": user.get("organization_id"),
        "area_id": user.get("area_id"),
        "name": user["name"],
        "username": user.get("username") or (user["email"] or "").split("@")[0],
        "email": user["email"],
        "role": user["role"],
        "role_label": ROLE_LABELS.get(user["role"], user["role"]),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


def normalize_organization(row) -> dict:
    item = row_to_dict(row)
    return {
        "id": item["id"],
        "name": item["name"],
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def normalize_area(row) -> dict:
    item = row_to_dict(row)
    return {
        "id": item["id"],
        "organization_id": item["organization_id"],
        "name": item["name"],
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def can_access_all_areas(user: dict) -> bool:
    return user["role"] in {"admin", "supervisor"}


def scope_condition(table, user: dict):
    conditions = [table.c.organization_id == user["organization_id"]]
    if not can_access_all_areas(user):
        conditions.append(table.c.area_id == user["area_id"])
    return and_(*conditions)


def scope_values(user: dict) -> dict:
    return {
        "organization_id": user["organization_id"],
        "area_id": user["area_id"],
    }


def set_rls_context(connection, user: dict) -> None:
    if get_database_url().startswith("postgresql"):
        connection.execute(text("SELECT set_config('app.user_id', :value, true)"), {"value": user["id"]})
        connection.execute(text("SELECT set_config('app.role', :value, true)"), {"value": user["role"]})
        connection.execute(
            text("SELECT set_config('app.organization_id', :value, true)"),
            {"value": user["organization_id"] or ""},
        )
        connection.execute(text("SELECT set_config('app.area_id', :value, true)"), {"value": user["area_id"] or ""})


def validate_area_for_user(connection, user: dict, area_id: str | None) -> str:
    selected_area_id = area_id or user["area_id"]
    row = connection.execute(
        select(areas)
        .where(areas.c.id == selected_area_id)
        .where(areas.c.organization_id == user["organization_id"])
    ).first()
    if not row:
        raise HTTPException(status_code=400, detail="Area no valida para este hospital")
    return selected_area_id


@contextmanager
def scoped_connection(request: Request):
    user = current_user(request)
    with get_engine().begin() as connection:
        set_rls_context(connection, user)
        yield connection, user


def is_expired(value) -> bool:
    expires_at = parse_datetime(value)
    if not expires_at:
        return True
    return expires_at <= datetime.now(timezone.utc)


def parse_datetime(value) -> datetime | None:
    if not value:
        return None
    parsed = value
    if isinstance(parsed, str):
        try:
            parsed = datetime.fromisoformat(parsed.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(parsed, datetime):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def report_is_in_nurse_edit_window(report_row) -> bool:
    report = row_to_dict(report_row)
    report_time = parse_datetime(report.get("created_at")) or parse_datetime(report.get("timestamp"))
    if not report_time:
        return False
    age = datetime.now(timezone.utc) - report_time
    return timedelta(0) <= age <= timedelta(hours=12)


def require_report_edit_permission(request: Request, report_row) -> dict:
    user = current_user(request)
    if user["role"] in {"admin", "supervisor"}:
        return user
    if user["role"] == "nurse" and report_is_in_nurse_edit_window(report_row):
        return user
    raise HTTPException(
        status_code=403,
        detail="Enfermeria solo puede editar reportes durante las primeras 12 horas",
    )


def authenticate_token(authorization: str | None) -> dict | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    token_hash = hash_token(token)
    with get_engine().begin() as connection:
        session_row = connection.execute(
            select(user_sessions).where(user_sessions.c.token_hash == token_hash)
        ).first()
        if not session_row:
            return None

        session = row_to_dict(session_row)
        if is_expired(session["expires_at"]):
            connection.execute(delete(user_sessions).where(user_sessions.c.token_hash == token_hash))
            return None

        user_row = connection.execute(select(users).where(users.c.id == session["user_id"])).first()
        return normalize_user(user_row) if user_row else None


@app.middleware("http")
async def require_api_auth(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    public_paths = {"/api/auth/login"}
    if path.startswith("/api/") and path not in public_paths:
        user = authenticate_token(request.headers.get("authorization"))
        if not user:
            return JSONResponse(
                {"detail": "Sesion requerida"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        request.state.user = user

    return await call_next(request)


def current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Sesion requerida")
    return user


def require_role(request: Request, *roles: UserRole) -> dict:
    user = current_user(request)
    if user["role"] not in roles:
        raise HTTPException(status_code=403, detail="No tienes permiso para esta accion")
    return user


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
        "order_index": material.get("order_index", 0),
        "created_at": material.get("created_at"),
        "updated_at": material.get("updated_at"),
    }


def normalize_material_list(row, materials: list[dict] | None = None) -> dict:
    item = row_to_dict(row)
    return {
        "id": item["id"],
        "name": item["name"],
        "materials": materials or [],
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
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


def merge_order_ids(requested_ids: list[str], existing_ids: list[str]) -> list[str]:
    requested_set = set(requested_ids)
    existing_set = set(existing_ids)

    if len(requested_ids) != len(requested_set):
        raise HTTPException(status_code=400, detail="Material order contains duplicate ids")

    unknown_ids = requested_set - existing_set
    if unknown_ids:
        raise HTTPException(status_code=400, detail="Material order contains materials that no longer exist")

    return requested_ids + [material_id for material_id in existing_ids if material_id not in requested_set]


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


@app.post("/api/auth/login")
def login(payload: LoginPayload) -> dict:
    username = normalize_username(payload.username)
    with get_engine().begin() as connection:
        user_row = connection.execute(select(users).where(users.c.username == username)).first()
        if not user_row:
            raise HTTPException(status_code=401, detail="Usuario o contrasena incorrectos")

        user_data = row_to_dict(user_row)
        if not verify_password(payload.password, user_data["password_salt"], user_data["password_hash"]):
            raise HTTPException(status_code=401, detail="Usuario o contrasena incorrectos")

        token = secrets.token_urlsafe(32)
        connection.execute(
            insert(user_sessions).values(
                token_hash=hash_token(token),
                user_id=user_data["id"],
                expires_at=datetime.now(timezone.utc) + timedelta(days=14),
            )
        )

    return {"token": token, "user": normalize_user(user_row)}


@app.get("/api/auth/me")
def get_me(request: Request) -> dict:
    return current_user(request)


@app.post("/api/auth/logout")
def logout(request: Request) -> dict:
    authorization = request.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        with get_engine().begin() as connection:
            connection.execute(delete(user_sessions).where(user_sessions.c.token_hash == hash_token(token)))
    return {"message": "Sesion cerrada"}


@app.get("/api/users")
def get_users(request: Request) -> list[dict]:
    with scoped_connection(request) as (connection, user):
        require_role(request, "admin")
        rows = connection.execute(
            select(users)
            .where(users.c.organization_id == user["organization_id"])
            .order_by(users.c.created_at)
        ).fetchall()
    return [normalize_user(row) for row in rows]


@app.post("/api/users", status_code=201)
def create_user(request: Request, payload: UserPayload) -> dict:
    actor = require_role(request, "admin")
    username = normalize_username(payload.username)
    email = local_email_for_username(username)
    name = payload.name.strip()
    if payload.role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail="Rol invalido")

    salt = secrets.token_hex(16)
    user_id = str(uuid4())
    with scoped_connection(request) as (connection, user):
        area_id = validate_area_for_user(connection, user, payload.area_id)
        duplicate = connection.execute(
            select(users.c.id)
            .where(users.c.organization_id == actor["organization_id"])
            .where(users.c.username == username)
        ).first()
        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="Nombre de usuario ya existente, por favor elige otro",
            )
        connection.execute(
            insert(users).values(
                id=user_id,
                organization_id=actor["organization_id"],
                area_id=area_id,
                name=name,
                username=username,
                email=email,
                password_hash=hash_password(payload.password, salt),
                password_salt=salt,
                role=payload.role,
            )
        )
        row = connection.execute(select(users).where(users.c.id == user_id)).first()
    return normalize_user(row)


@app.put("/api/users/{user_id}")
def update_user(request: Request, user_id: str, payload: UserUpdatePayload) -> dict:
    actor = require_role(request, "admin")
    values = {}
    if payload.name is not None:
        values["name"] = payload.name.strip()
    if payload.username is not None:
        username = normalize_username(payload.username)
        values["username"] = username
        values["email"] = local_email_for_username(username)
    if payload.role is not None:
        values["role"] = payload.role
    if payload.area_id is not None:
        values["area_id"] = payload.area_id
    if payload.password:
        salt = secrets.token_hex(16)
        values["password_salt"] = salt
        values["password_hash"] = hash_password(payload.password, salt)
    if not values:
        raise HTTPException(status_code=400, detail="No hay cambios para guardar")
    values["updated_at"] = func.now()

    with scoped_connection(request) as (connection, user):
        if "area_id" in values:
            values["area_id"] = validate_area_for_user(connection, user, values["area_id"])
        if "username" in values:
            duplicate = connection.execute(
                select(users.c.id)
                .where(users.c.organization_id == actor["organization_id"])
                .where(users.c.username == values["username"])
                .where(users.c.id != user_id)
            ).first()
            if duplicate:
                raise HTTPException(
                    status_code=400,
                    detail="Nombre de usuario ya existente, por favor elige otro",
                )
        result = connection.execute(
            update(users)
            .where(users.c.id == user_id)
            .where(users.c.organization_id == actor["organization_id"])
            .values(**values)
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        row = connection.execute(select(users).where(users.c.id == user_id)).first()
    return normalize_user(row)


@app.delete("/api/users/{user_id}")
def delete_user(request: Request, user_id: str) -> dict:
    actor = require_role(request, "admin")
    if actor["id"] == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta activa")
    with scoped_connection(request) as (connection, user):
        connection.execute(delete(user_sessions).where(user_sessions.c.user_id == user_id))
        result = connection.execute(
            delete(users)
            .where(users.c.id == user_id)
            .where(users.c.organization_id == actor["organization_id"])
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Deleted", "id": user_id}


@app.get("/api/organizations")
def get_organizations(request: Request) -> list[dict]:
    with scoped_connection(request) as (connection, user):
        row = connection.execute(
            select(organizations).where(organizations.c.id == user["organization_id"])
        ).first()
    return [normalize_organization(row)] if row else []


@app.get("/api/areas")
def get_areas(request: Request) -> list[dict]:
    with scoped_connection(request) as (connection, user):
        rows = connection.execute(
            select(areas)
            .where(areas.c.organization_id == user["organization_id"])
            .order_by(areas.c.name)
        ).fetchall()
    return [normalize_area(row) for row in rows]


@app.post("/api/areas", status_code=201)
def create_area(request: Request, payload: AreaPayload) -> dict:
    user = require_role(request, "admin")
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre del area es requerido")

    with scoped_connection(request) as (connection, _user):
        duplicate = connection.execute(
            select(areas.c.id)
            .where(areas.c.organization_id == user["organization_id"])
            .where(func.lower(areas.c.name) == name.lower())
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Ya existe un area con ese nombre")
        area_id = str(uuid4())
        connection.execute(
            insert(areas).values(id=area_id, organization_id=user["organization_id"], name=name)
        )
        row = connection.execute(select(areas).where(areas.c.id == area_id)).first()
    return normalize_area(row)


@app.get("/api/materials/{material_type}")
def get_materials(request: Request, material_type: MaterialType) -> list[dict]:
    table = table_for_type(material_type)
    with scoped_connection(request) as (connection, user):
        rows = connection.execute(
            select(table)
            .where(scope_condition(table, user))
            .order_by(table.c.order_index, table.c.created_at)
        ).fetchall()
    return [normalize_material(row) for row in rows]


@app.get("/api/material-lists")
def get_material_lists(request: Request) -> list[dict]:
    result = []
    with scoped_connection(request) as (connection, user):
        list_rows = connection.execute(
            select(material_lists)
            .where(scope_condition(material_lists, user))
            .order_by(material_lists.c.created_at)
        ).fetchall()
        for item in list_rows:
            rows = connection.execute(
                select(custom_materials)
                .where(custom_materials.c.list_id == item._mapping["id"])
                .where(scope_condition(custom_materials, user))
                .order_by(custom_materials.c.order_index, custom_materials.c.created_at)
            ).fetchall()
            result.append(normalize_material_list(item, [normalize_material(row) for row in rows]))
    return result


@app.post("/api/material-lists", status_code=201)
def create_material_list(request: Request, payload: MaterialListPayload) -> dict:
    user = require_role(request, "admin", "supervisor")
    list_id = str(uuid4())
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="List name is required")
    if name.lower() in {"gas", "vapor"}:
        raise HTTPException(status_code=400, detail="Gas and Vapor are system lists")

    with scoped_connection(request) as (connection, scoped_user):
        duplicate = connection.execute(
            select(material_lists.c.id)
            .where(material_lists.c.organization_id == scoped_user["organization_id"])
            .where(material_lists.c.area_id == scoped_user["area_id"])
            .where(func.lower(material_lists.c.name) == name.lower())
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="A list with this name already exists")
        connection.execute(insert(material_lists).values(id=list_id, name=name, **scope_values(user)))
        row = connection.execute(select(material_lists).where(material_lists.c.id == list_id)).first()

    return normalize_material_list(row)


@app.delete("/api/material-lists/{list_id}")
def delete_material_list(request: Request, list_id: str) -> dict:
    user = require_role(request, "admin")
    with scoped_connection(request) as (connection, _user):
        connection.execute(delete(custom_materials).where(custom_materials.c.list_id == list_id))
        result = connection.execute(
            delete(material_lists)
            .where(material_lists.c.id == list_id)
            .where(material_lists.c.organization_id == user["organization_id"])
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="List not found")
    return {"message": "Deleted", "id": list_id}


@app.post("/api/material-lists/{list_id}/materials", status_code=201)
def create_custom_material(request: Request, list_id: str, payload: MaterialPayload) -> dict:
    user = require_role(request, "admin", "supervisor")
    material_id = payload.id or str(uuid4())
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Material name is required")

    with scoped_connection(request) as (connection, scoped_user):
        if not connection.execute(
            select(material_lists.c.id)
            .where(material_lists.c.id == list_id)
            .where(scope_condition(material_lists, scoped_user))
        ).first():
            raise HTTPException(status_code=404, detail="List not found")
        next_order = connection.execute(
            select(func.coalesce(func.max(custom_materials.c.order_index), -1) + 1)
            .where(custom_materials.c.list_id == list_id)
        ).scalar_one()
        connection.execute(
            insert(custom_materials).values(
                id=material_id,
                **scope_values(user),
                list_id=list_id,
                name=name,
                existing=payload.existing,
                counted=payload.counted,
                description=payload.description,
                order_index=next_order,
            )
        )
        row = connection.execute(select(custom_materials).where(custom_materials.c.id == material_id)).first()
    return normalize_material(row)


@app.put("/api/material-lists/{list_id}/materials/order")
def update_custom_material_order(request: Request, list_id: str, payload: MaterialOrderPayload) -> list[dict]:
    require_role(request, "admin", "supervisor")
    with scoped_connection(request) as (connection, user):
        existing_ids = [
            row._mapping["id"]
            for row in connection.execute(
                select(custom_materials.c.id)
                .where(custom_materials.c.list_id == list_id)
                .where(scope_condition(custom_materials, user))
                .order_by(custom_materials.c.order_index, custom_materials.c.created_at)
            ).fetchall()
        ]
        merged_ids = merge_order_ids(payload.ids, existing_ids)

        for order_index, material_id in enumerate(merged_ids):
            connection.execute(
                update(custom_materials)
                .where(custom_materials.c.id == material_id)
                .where(custom_materials.c.list_id == list_id)
                .where(scope_condition(custom_materials, user))
                .values(order_index=order_index, updated_at=func.now())
            )
        rows = connection.execute(
            select(custom_materials)
            .where(custom_materials.c.list_id == list_id)
            .where(scope_condition(custom_materials, user))
            .order_by(custom_materials.c.order_index, custom_materials.c.created_at)
        ).fetchall()
    return [normalize_material(row) for row in rows]


@app.put("/api/material-lists/{list_id}/materials/{material_id}")
def update_custom_material(request: Request, list_id: str, material_id: str, payload: MaterialPayload) -> dict:
    require_role(request, "admin", "supervisor")
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Material name is required")

    with scoped_connection(request) as (connection, user):
        result = connection.execute(
            update(custom_materials)
            .where(custom_materials.c.id == material_id)
            .where(custom_materials.c.list_id == list_id)
            .where(scope_condition(custom_materials, user))
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
        row = connection.execute(select(custom_materials).where(custom_materials.c.id == material_id)).first()
    return normalize_material(row)


@app.put("/api/material-lists/{list_id}/materials/{material_id}/list")
def move_custom_material(request: Request, list_id: str, material_id: str, payload: CustomMaterialMovePayload) -> dict:
    require_role(request, "admin", "supervisor")
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Material name is required")

    with scoped_connection(request) as (connection, user):
        if not connection.execute(
            select(material_lists.c.id)
            .where(material_lists.c.id == payload.target_list_id)
            .where(scope_condition(material_lists, user))
        ).first():
            raise HTTPException(status_code=404, detail="Target list not found")

        next_order = connection.execute(
            select(func.coalesce(func.max(custom_materials.c.order_index), -1) + 1)
            .where(custom_materials.c.list_id == payload.target_list_id)
        ).scalar_one()
        result = connection.execute(
            update(custom_materials)
            .where(custom_materials.c.id == material_id)
            .where(custom_materials.c.list_id == list_id)
            .where(scope_condition(custom_materials, user))
            .values(
                list_id=payload.target_list_id,
                name=name,
                existing=payload.existing,
                counted=payload.counted,
                description=payload.description,
                order_index=next_order,
                updated_at=func.now(),
            )
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Material not found")
        row = connection.execute(select(custom_materials).where(custom_materials.c.id == material_id)).first()
    return normalize_material(row)


@app.delete("/api/material-lists/{list_id}/materials/{material_id}")
def delete_custom_material(request: Request, list_id: str, material_id: str) -> dict:
    require_role(request, "admin")
    with scoped_connection(request) as (connection, user):
        result = connection.execute(
            delete(custom_materials)
            .where(custom_materials.c.id == material_id)
            .where(custom_materials.c.list_id == list_id)
            .where(scope_condition(custom_materials, user))
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Material not found")
    return {"message": "Deleted", "id": material_id}


@app.post("/api/materials/{material_type}", status_code=201)
def create_material(request: Request, material_type: MaterialType, payload: MaterialPayload) -> dict:
    user = require_role(request, "admin", "supervisor")
    table = table_for_type(material_type)
    material_id = payload.id or str(uuid4())
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Material name is required")

    with scoped_connection(request) as (connection, _user):
        next_order = connection.execute(
            select(func.coalesce(func.max(table.c.order_index), -1) + 1)
            .where(table.c.organization_id == user["organization_id"])
            .where(table.c.area_id == user["area_id"])
        ).scalar_one()
        try:
            connection.execute(
                insert(table).values(
                    id=material_id,
                    **scope_values(user),
                    name=name,
                    existing=payload.existing,
                    counted=payload.counted,
                    description=payload.description,
                    order_index=next_order,
                )
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        row = connection.execute(select(table).where(table.c.id == material_id)).first()

    return normalize_material(row)


@app.put("/api/materials/{material_type}/order")
def update_material_order(request: Request, material_type: MaterialType, payload: MaterialOrderPayload) -> list[dict]:
    require_role(request, "admin", "supervisor")
    table = table_for_type(material_type)
    with scoped_connection(request) as (connection, user):
        existing_ids = [
            row._mapping["id"]
            for row in connection.execute(
                select(table.c.id)
                .where(scope_condition(table, user))
                .order_by(table.c.order_index, table.c.created_at)
            ).fetchall()
        ]
        merged_ids = merge_order_ids(payload.ids, existing_ids)

        for order_index, material_id in enumerate(merged_ids):
            connection.execute(
                update(table)
                .where(table.c.id == material_id)
                .where(scope_condition(table, user))
                .values(order_index=order_index, updated_at=func.now())
            )

        rows = connection.execute(
            select(table).where(scope_condition(table, user)).order_by(table.c.order_index, table.c.created_at)
        ).fetchall()

    return [normalize_material(row) for row in rows]


@app.put("/api/materials/{material_type}/{material_id}")
def update_material(request: Request, material_type: MaterialType, material_id: str, payload: MaterialPayload) -> dict:
    require_role(request, "admin", "supervisor")
    table = table_for_type(material_type)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Material name is required")

    with scoped_connection(request) as (connection, user):
        result = connection.execute(
            update(table)
            .where(table.c.id == material_id)
            .where(scope_condition(table, user))
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


@app.put("/api/materials/{material_type}/{material_id}/type")
def change_material_type(
    request: Request,
    material_type: MaterialType,
    material_id: str,
    payload: MaterialTypeChangePayload,
) -> dict:
    require_role(request, "admin", "supervisor")
    source_table = table_for_type(material_type)
    target_table = table_for_type(payload.type)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Material name is required")

    if payload.type == material_type:
        return update_material(request, material_type, material_id, payload)

    with scoped_connection(request) as (connection, user):
        source_row = connection.execute(
            select(source_table).where(source_table.c.id == material_id)
            .where(scope_condition(source_table, user))
        ).first()
        if not source_row:
            raise HTTPException(status_code=404, detail="Material not found")

        duplicate = connection.execute(
            select(target_table.c.id).where(target_table.c.id == material_id)
            .where(scope_condition(target_table, user))
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Material already exists in target type")

        next_order = connection.execute(
            select(func.coalesce(func.max(target_table.c.order_index), -1) + 1)
            .where(target_table.c.organization_id == user["organization_id"])
            .where(target_table.c.area_id == user["area_id"])
        ).scalar_one()

        connection.execute(
            insert(target_table).values(
                id=material_id,
                **scope_values(user),
                name=name,
                existing=payload.existing,
                counted=payload.counted,
                description=payload.description,
                order_index=next_order,
            )
        )
        connection.execute(delete(source_table).where(source_table.c.id == material_id).where(scope_condition(source_table, user)))
        row = connection.execute(select(target_table).where(target_table.c.id == material_id)).first()

    return normalize_material(row)


@app.delete("/api/materials/{material_type}/{material_id}")
def delete_material(request: Request, material_type: MaterialType, material_id: str) -> dict:
    require_role(request, "admin")
    table = table_for_type(material_type)
    with scoped_connection(request) as (connection, user):
        result = connection.execute(delete(table).where(table.c.id == material_id).where(scope_condition(table, user)))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Material not found")

    return {"message": "Deleted", "id": material_id}


@app.get("/api/reports")
def get_reports(request: Request) -> list[dict]:
    result = []
    with scoped_connection(request) as (connection, user):
        report_rows = connection.execute(
            select(reports).where(scope_condition(reports, user)).order_by(desc(reports.c.created_at))
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
def create_report(request: Request, payload: ReportPayload) -> dict:
    user = require_role(request, "admin", "supervisor", "nurse")
    report_id = payload.id or str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    user_name = payload.user_name.strip()
    shift = payload.shift.strip()
    duration_seconds = max(0, payload.duration_seconds or 0)
    if not user_name or not shift:
        raise HTTPException(status_code=400, detail="User name and shift are required")

    normalized = normalize_payload_differences(payload)

    with scoped_connection(request) as (connection, _user):
        connection.execute(
            insert(reports).values(
                id=report_id,
                **scope_values(user),
                type=payload.type,
                user_name=user_name,
                shift=shift,
                timestamp=timestamp,
                duration_seconds=duration_seconds,
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
        "duration_seconds": duration_seconds,
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
def update_report(request: Request, report_id: str, payload: ReportPayload) -> dict:
    user_name = payload.user_name.strip()
    shift = payload.shift.strip()
    duration_seconds = max(0, payload.duration_seconds or 0)
    if not user_name or not shift:
        raise HTTPException(status_code=400, detail="User name and shift are required")

    normalized = normalize_payload_differences(payload)

    with scoped_connection(request) as (connection, user):
        existing_report = connection.execute(
            select(reports)
            .where(reports.c.id == report_id)
            .where(scope_condition(reports, user))
        ).first()
        if not existing_report:
            raise HTTPException(status_code=404, detail="Report not found")

        require_report_edit_permission(request, existing_report)

        result = connection.execute(
            update(reports)
            .where(reports.c.id == report_id)
            .where(scope_condition(reports, user))
            .values(
                type=payload.type,
                user_name=user_name,
                shift=shift,
                duration_seconds=duration_seconds,
            )
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
