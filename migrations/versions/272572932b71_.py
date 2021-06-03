"""empty message

Revision ID: 272572932b71
Revises: 30f8832b3652
Create Date: 2021-06-03 13:49:36.017746

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '272572932b71'
down_revision = '30f8832b3652'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artist', sa.Column('cityid', sa.Integer(), nullable=False))
    op.add_column('artist', sa.Column('website', sa.String(length=120), nullable=True))
    op.add_column('artist', sa.Column('seeking_venue', sa.Boolean(), nullable=True))
    op.add_column('artist', sa.Column('seeking_description', sa.String(length=120), nullable=True))
    op.create_foreign_key(None, 'artist', 'city', ['cityid'], ['id'])
    op.drop_column('artist', 'city')
    op.drop_column('artist', 'state')
    op.drop_column('artist', 'genres')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artist', sa.Column('genres', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
    op.add_column('artist', sa.Column('state', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
    op.add_column('artist', sa.Column('city', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'artist', type_='foreignkey')
    op.drop_column('artist', 'seeking_description')
    op.drop_column('artist', 'seeking_venue')
    op.drop_column('artist', 'website')
    op.drop_column('artist', 'cityid')
    # ### end Alembic commands ###