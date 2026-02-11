from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base

# Import all models so that Base.metadata is fully populated for autogenerate.
from app.models.user import User  # noqa: F401
from app.models.company import Company  # noqa: F401
from app.models.engineer import Engineer, engineer_skills  # noqa: F401
from app.models.project import Project, project_required_skills  # noqa: F401
from app.models.quotation import Quotation  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.contract import Contract  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.skill_tag import SkillTag  # noqa: F401
from app.models.matching import MatchingResult  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.automation import (  # noqa: F401
    RoutingRule,
    ExcelTemplate,
    ProcessingJob,
    ProcessingLog,
    WebSystemCredential,
    SlackChannel,
    ReportSchedule,
)

config = context.config

# Override sqlalchemy.url from application settings (DATABASE_URL env var).
# This ensures the URL in alembic.ini is just a placeholder.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without requiring a live database connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an engine and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
