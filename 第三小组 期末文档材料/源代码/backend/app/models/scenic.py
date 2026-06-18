"""景区/校园模型"""
from datetime import datetime
from app import db


class Scenic(db.Model):
    """景区/校园表 - 至少200个"""
    __tablename__ = 'scenics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    # 类型: scenic=景区, campus=校园
    type = db.Column(db.String(20), nullable=False, default='scenic')
    # 分类标签: 自然风光、历史文化、主题乐园、科技馆、博物馆、大学等
    category = db.Column(db.String(64), default='')
    description = db.Column(db.Text, default='')
    address = db.Column(db.String(256), default='')
    # 经纬度
    latitude = db.Column(db.Float, default=0.0)
    longitude = db.Column(db.Float, default=0.0)
    # 热度（浏览量/访问量）
    popularity = db.Column(db.Integer, default=0)
    # 评价分数 1-5
    rating = db.Column(db.Float, default=4.0)
    # 评价人数
    rating_count = db.Column(db.Integer, default=0)
    # 门票价格
    ticket_price = db.Column(db.Float, default=0.0)
    # 开放时间
    open_time = db.Column(db.String(64), default='08:00-18:00')
    # 封面图片
    cover_image = db.Column(db.String(256), default='')
    # 标签，JSON数组
    tags = db.Column(db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    buildings = db.relationship('Building', backref='scenic', lazy='dynamic')
    facilities = db.relationship('Facility', backref='scenic', lazy='dynamic')
    graph_nodes = db.relationship('GraphNode', backref='scenic', lazy='dynamic')

    def to_dict(self):
        """序列化"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'category': self.category,
            'description': self.description,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'popularity': self.popularity,
            'rating': self.rating,
            'rating_count': self.rating_count,
            'ticket_price': self.ticket_price,
            'open_time': self.open_time,
            'cover_image': self.cover_image,
            'tags': json.loads(self.tags) if self.tags else [],
            'building_count': self.buildings.count() if self.buildings else 0,
            'facility_count': self.facilities.count() if self.facilities else 0,
        }
