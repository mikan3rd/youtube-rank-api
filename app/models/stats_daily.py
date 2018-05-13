from logging import getLogger

from sqlalchemy import Column, ForeignKeyConstraint, Index, tuple_
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR
from sqlalchemy.orm import relationship

from . import Base, ModelMixin


log = getLogger(__name__)


class CampaignArea(Base, ModelMixin):
    __tablename__ = 'stats_daily'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    target_area = Column(VARCHAR(length=255), nullable=False)
    area = Column(VARCHAR(length=255), nullable=False, index=True)
    keyword = Column(VARCHAR(length=255), nullable=False)
    article = relationship('Article', uselist=False)
