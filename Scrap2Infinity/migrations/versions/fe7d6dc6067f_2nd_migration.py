"""2nd migration

Revision ID: fe7d6dc6067f
Revises: 
Create Date: 2022-03-26 10:28:20.735200

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe7d6dc6067f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('upload_data',
    sa.Column('filename', sa.String(length=200), nullable=False),
    sa.Column('file', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('filename')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('upload_data')
    # ### end Alembic commands ###
