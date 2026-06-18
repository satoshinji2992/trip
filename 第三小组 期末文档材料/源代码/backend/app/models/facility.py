"""服务设施模型"""
from datetime import datetime
from app import db


class Facility(db.Model):
    """服务设施表 - 商店、饭店、洗手间、图书馆、食堂、超市、咖啡馆等，至少50个"""
    __tablename__ = 'facilities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scenic_id = db.Column(db.Integer, db.ForeignKey('scenics.id'), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    # 类型: shop=商店, restaurant=饭店, restroom=洗手间, library=图书馆,
    # canteen=食堂, supermarket=超市, cafe=咖啡馆, hospital=医务室, atm=ATM, parking=停车场
    type = db.Column(db.String(32), nullable=False, default='shop')
    category = db.Column(db.String(64), default='')
    description = db.Column(db.Text, default='')
    latitude = db.Column(db.Float, default=0.0)
    longitude = db.Column(db.Float, default=0.0)
    # 关联到道路图节点，用于路径距离计算
    graph_node_id = db.Column(db.Integer, db.ForeignKey('graph_nodes.id'), nullable=True)
    # 营业时间
    open_time = db.Column(db.String(64), default='08:00-22:00')
    # 评分
    rating = db.Column(db.Float, default=4.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    graph_node = db.relationship('GraphNode', backref='facilities_at_node')

    def to_dict(self):
        return {
            'id': self.id,
            'scenic_id': self.scenic_id,
            'name': self.name,
            'type': self.type,
            'category': self.category,
            'description': self.description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'graph_node_id': self.graph_node_id,
            'open_time': self.open_time,
            'rating': self.rating,
        }
