"""Create Message model

Revision ID: 932566e91a7c
Revises: 
Create Date: 2024-02-24 16:51:18.267608

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '932566e91a7c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password',
               existing_type=mysql.VARCHAR(length=14),
               type_=sa.String(length=60),
               existing_nullable=False)
        batch_op.alter_column('date_of_birth',
               existing_type=sa.DATE(),
               type_=sa.String(length=50),
               existing_nullable=False)
        batch_op.drop_column('bio')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bio', mysql.TEXT(), nullable=False))
        batch_op.alter_column('date_of_birth',
               existing_type=sa.String(length=50),
               type_=sa.DATE(),
               existing_nullable=False)
        batch_op.alter_column('password',
               existing_type=sa.String(length=60),
               type_=mysql.VARCHAR(length=14),
               existing_nullable=False)

    op.drop_table('message')
    # ### end Alembic commands ###