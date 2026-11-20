"""${message}

Revision ID: ${up_revision}
Revises:${" " + down_revision if down_revision else ""}
Create Date: ${create_date}

"""

from collections.abc import Sequence

import sqlalchemy as sa
${(imports.strip() + "\n") if imports else ""}
from alembic import op

# revision identifiers, used by Alembic.
revision: str = ${'"' + up_revision + '"'}
down_revision: str | None = ${'"' + down_revision + '"' if down_revision else "None"}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
