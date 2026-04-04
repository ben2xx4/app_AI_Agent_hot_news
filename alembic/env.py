from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from alembic.script import ScriptDirectory
from sqlalchemy import engine_from_config, inspect, pool, text
from sqlalchemy.engine import Connection

from app.core.settings import get_settings
from app.db.base import Base
from app.db.session import resolve_database_url
from app.models import *  # noqa: F401,F403


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", resolve_database_url(settings))
target_metadata = Base.metadata
script_directory = ScriptDirectory.from_config(config)
head_revision = script_directory.get_current_head()
expected_tables = set(target_metadata.tables.keys())


def _should_stamp_existing_sqlite_schema(connection: Connection) -> bool:
    if connection.dialect.name != "sqlite":
        return False

    table_names = set(inspect(connection).get_table_names())
    if not expected_tables.issubset(table_names):
        return False

    if "alembic_version" not in table_names:
        return True

    version = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one_or_none()
    return version is None


def _stamp_existing_sqlite_schema(connection: Connection) -> None:
    table_names = set(inspect(connection).get_table_names())
    if "alembic_version" not in table_names:
        connection.execute(
            text(
                """
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
                """
            )
        )

    connection.execute(text("DELETE FROM alembic_version"))
    connection.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:version_num)"),
        {"version_num": head_revision},
    )
    connection.commit()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        if _should_stamp_existing_sqlite_schema(connection):
            _stamp_existing_sqlite_schema(connection)
            return

        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
