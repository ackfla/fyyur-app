"""empty message

Revision ID: f5c3e4f22a7c
Revises: 5787a70a193d
Create Date: 2021-06-03 12:27:44.310952

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5c3e4f22a7c'
down_revision = '5787a70a193d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('city',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('city', sa.String(length=120), nullable=True),
    sa.Column('state', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('venue', sa.Column('cityid', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'venue', 'city', ['cityid'], ['id'])
    op.drop_column('venue', 'state')
    op.drop_column('venue', 'city')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venue', sa.Column('city', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
    op.add_column('venue', sa.Column('state', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'venue', type_='foreignkey')
    op.drop_column('venue', 'cityid')
    op.drop_table('city')
    # ### end Alembic commands ###
