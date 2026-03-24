"""建筑物模型"""
from datetime import datetime
from app import db


class Building(db.Model):
    """建筑物表 - 景点、教学楼、办公楼、宿舍楼等，至少20个"""
    __tablename__ = 'buildings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scenic_id = db.Column(db.Integer, db.ForeignKey('scenics.id'), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    # 类型: attraction=景点, teaching=教学楼, office=办公楼, dormitory=宿舍楼, library=图书馆, museum=博物馆, other=其他
    type = db.Column(db.String(32), nullable=False, default='attraction')
    description = db.Column(db.Text, default='')
    # 楼层数（用于室内导航）
    floors = db.Column(db.Integer, default=1)
    # 是否有电梯
    has_elevator = db.Column(db.Boolean, default=False)
    latitude = db.Column(db.Float, default=0.0)
    longitude = db.Column(db.Float, default=0.0)
    # 封面图片
    cover_image = db.Column(db.String(256), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系 - 室内导航节点
    indoor_nodes = db.relationship('IndoorNode', backref='building', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'scenic_id': self.scenic_id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'floors': self.floors,
            'has_elevator': self.has_elevator,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'cover_image': self.cover_image,
        }


class IndoorNode(db.Model):
    """室内导航节点 - 用于室内导航"""
    __tablename__ = 'indoor_nodes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    # 节点类型: entrance=入口, elevator=电梯, stair=楼梯, room=房间, corridor=走廊, exit=出口
    node_type = db.Column(db.String(32), nullable=False, default='room')
    floor = db.Column(db.Integer, default=1)
    # 相对坐标（建筑内部）
    x = db.Column(db.Float, default=0.0)
    y = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'building_id': self.building_id,
            'name': self.name,
            'node_type': self.node_type,
            'floor': self.floor,
            'x': self.x,
            'y': self.y,
        }


class IndoorEdge(db.Model):
    """室内导航边 - 室内节点之间的连接"""
    __tablename__ = 'indoor_edges'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), nullable=False, index=True)
    from_node_id = db.Column(db.Integer, db.ForeignKey('indoor_nodes.id'), nullable=False)
    to_node_id = db.Column(db.Integer, db.ForeignKey('indoor_nodes.id'), nullable=False)
    # 距离（米）
    distance = db.Column(db.Float, nullable=False, default=1.0)
    # 是否双向
    bidirectional = db.Column(db.Boolean, default=True)
    # 类型: corridor=走廊, elevator=电梯, stair=楼梯
    edge_type = db.Column(db.String(32), default='corridor')

    from_node = db.relationship('IndoorNode', foreign_keys=[from_node_id])
    to_node = db.relationship('IndoorNode', foreign_keys=[to_node_id])

    def to_dict(self):
        return {
            'id': self.id,
            'building_id': self.building_id,
            'from_node_id': self.from_node_id,
            'to_node_id': self.to_node_id,
            'distance': self.distance,
            'bidirectional': self.bidirectional,
            'edge_type': self.edge_type,
        }
