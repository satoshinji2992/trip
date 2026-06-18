"""数据模型包"""
from app.models.user import User
from app.models.scenic import Scenic
from app.models.building import Building
from app.models.facility import Facility
from app.models.graph import GraphNode, GraphEdge
from app.models.diary import Diary, DiaryComment, DiaryImage
from app.models.food import Food, Restaurant

__all__ = [
    'User', 'Scenic', 'Building', 'Facility',
    'GraphNode', 'GraphEdge',
    'Diary', 'DiaryComment', 'DiaryImage',
    'Food', 'Restaurant',
]
