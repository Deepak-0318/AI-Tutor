"""Initial migration

Revision ID: bf53228cf4bf
Revises: 
Create Date: 2025-04-03 22:47:02.501251

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf53228cf4bf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=128), nullable=False))
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=80),
               existing_nullable=False)
        batch_op.alter_column('progress',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.Text(),
               existing_nullable=True)
        batch_op.drop_column('password')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password', sa.VARCHAR(length=50), nullable=False))
        batch_op.alter_column('progress',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
        batch_op.alter_column('username',
               existing_type=sa.String(length=80),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)
        batch_op.drop_column('password_hash')

    # ### end Alembic commands ###
