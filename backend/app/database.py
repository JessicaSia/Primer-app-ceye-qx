import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    inspect,
    text,
)
from sqlalchemy.engine import Engine


load_dotenv()

metadata = MetaData()

materials_gas = Table(
    "materials_gas",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("existing", Integer, nullable=False, server_default="0"),
    Column("counted", Integer, nullable=False, server_default="0"),
    Column("description", String, nullable=False, server_default=""),
    Column("order_index", Integer, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

materials_vapor = Table(
    "materials_vapor",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("existing", Integer, nullable=False, server_default="0"),
    Column("counted", Integer, nullable=False, server_default="0"),
    Column("description", String, nullable=False, server_default=""),
    Column("order_index", Integer, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

material_lists = Table(
    "material_lists",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

custom_materials = Table(
    "custom_materials",
    metadata,
    Column("id", String, primary_key=True),
    Column("list_id", String, ForeignKey("material_lists.id", ondelete="CASCADE"), nullable=False),
    Column("name", String, nullable=False),
    Column("existing", Integer, nullable=False, server_default="0"),
    Column("counted", Integer, nullable=False, server_default="0"),
    Column("description", String, nullable=False, server_default=""),
    Column("order_index", Integer, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

reports = Table(
    "reports",
    metadata,
    Column("id", String, primary_key=True),
    Column("type", String, nullable=False),
    Column("user_name", String, nullable=False, server_default=""),
    Column("shift", String, nullable=False, server_default=""),
    Column("timestamp", String, nullable=False, server_default=func.now()),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

report_differences = Table(
    "report_differences",
    metadata,
    Column("id", String, primary_key=True),
    Column("report_id", String, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
    Column("material_id", String, nullable=False),
    Column("material_name", String, nullable=False, server_default=""),
    Column("existing", Integer, nullable=False, server_default="0"),
    Column("counted", Integer, nullable=False, server_default="0"),
    Column("room_count", Integer, nullable=False, server_default="0"),
    Column("process_count", Integer, nullable=False, server_default="0"),
    Column("difference", Integer, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


def normalize_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)
    if raw_url.startswith("postgresql://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return normalize_database_url(database_url)

    sqlite_path = Path(os.getenv("SQLITE_DB_PATH", "/data/inventory.db"))
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path}"


engine = create_engine(get_database_url(), pool_pre_ping=True)


def get_engine() -> Engine:
    return engine


def table_for_type(material_type: str) -> Table:
    return materials_gas if material_type == "gas" else materials_vapor


def init_db() -> None:
    metadata.create_all(engine)
    migrate_existing_tables()
    seed_data()


def migrate_existing_tables() -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        if "reports" in inspector.get_table_names():
            report_columns = {column["name"] for column in inspector.get_columns("reports")}
            if "user_name" not in report_columns:
                connection.execute(
                    text("ALTER TABLE reports ADD COLUMN user_name VARCHAR NOT NULL DEFAULT ''")
                )
            if "shift" not in report_columns:
                connection.execute(
                    text("ALTER TABLE reports ADD COLUMN shift VARCHAR NOT NULL DEFAULT ''")
                )
            remove_reports_type_check(connection)

        for table_name in ("materials_gas", "materials_vapor"):
            if table_name in inspector.get_table_names():
                material_columns = {
                    column["name"] for column in inspector.get_columns(table_name)
                }
                if "order_index" not in material_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            "ADD COLUMN order_index INTEGER NOT NULL DEFAULT 0"
                        )
                    )
                    rows = connection.execute(
                        text(f"SELECT id FROM {table_name} ORDER BY created_at")
                    ).fetchall()
                    for index, row in enumerate(rows):
                        connection.execute(
                            text(f"UPDATE {table_name} SET order_index = :order_index WHERE id = :id"),
                            {"order_index": index, "id": row._mapping["id"]},
                        )

        if "report_differences" in inspector.get_table_names():
            difference_columns = {
                column["name"] for column in inspector.get_columns("report_differences")
            }
            if "room_count" not in difference_columns:
                connection.execute(
                    text(
                        "ALTER TABLE report_differences "
                        "ADD COLUMN room_count INTEGER NOT NULL DEFAULT 0"
                    )
                )
            if "process_count" not in difference_columns:
                connection.execute(
                    text(
                        "ALTER TABLE report_differences "
                        "ADD COLUMN process_count INTEGER NOT NULL DEFAULT 0"
                    )
                )


def remove_reports_type_check(connection) -> None:
    if engine.dialect.name == "postgresql":
        connection.execute(text("ALTER TABLE reports DROP CONSTRAINT IF EXISTS reports_type_check"))
        return

    if engine.dialect.name != "sqlite":
        return

    create_sql = connection.execute(
        text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'reports'")
    ).scalar()
    if not create_sql or "reports_type_check" not in create_sql:
        return

    connection.execute(text("PRAGMA foreign_keys=OFF"))
    connection.execute(
        text(
            """
            CREATE TABLE reports_new (
                id VARCHAR NOT NULL,
                type VARCHAR NOT NULL,
                user_name VARCHAR NOT NULL DEFAULT '',
                shift VARCHAR NOT NULL DEFAULT '',
                timestamp VARCHAR NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            )
            """
        )
    )
    connection.execute(
        text(
            """
            INSERT INTO reports_new (id, type, user_name, shift, timestamp, created_at)
            SELECT id, type, user_name, shift, timestamp, created_at FROM reports
            """
        )
    )
    connection.execute(text("DROP TABLE reports"))
    connection.execute(text("ALTER TABLE reports_new RENAME TO reports"))
    connection.execute(text("PRAGMA foreign_keys=ON"))


def seed_data() -> None:
    with engine.begin() as connection:
        existing_rows = connection.execute(
            text("SELECT COUNT(*) FROM materials_gas")
        ).scalar_one()
        if existing_rows > 0:
            return

        connection.execute(
            materials_gas.insert(),
            [
                {
                    "id": "gas-1",
                    "name": "Oxigeno",
                    "existing": 100,
                    "description": "Gas medico para respiracion asistida",
                    "order_index": 0,
                },
                {
                    "id": "gas-2",
                    "name": "Nitrogeno",
                    "existing": 50,
                    "description": "Gas para sistemas de enfriamiento",
                    "order_index": 1,
                },
            ],
        )
        connection.execute(
            materials_vapor.insert(),
            [
                {
                    "id": "vapor-1",
                    "name": "Vapor 1",
                    "existing": 20,
                    "description": "Vapor utilizado en esterilizacion",
                    "order_index": 0,
                },
                {
                    "id": "vapor-2",
                    "name": "Vapor 2",
                    "existing": 30,
                    "description": "Vapor para limpieza de equipo",
                    "order_index": 1,
                },
            ],
        )
