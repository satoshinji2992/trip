"""道路图模型 - 用于路线规划，边数不少于200条"""
from datetime import datetime
from app import db


class GraphNode(db.Model):
    """道路图节点"""
    __tablename__ = 'graph_nodes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scenic_id = db.Column(db.Integer, db.ForeignKey('scenics.id'), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    # 节点类型: intersection=路口, building=建筑入口, gate=大门, station=站点, spot=景点
    node_type = db.Column(db.String(32), default='intersection')
    latitude = db.Column(db.Float, default=0.0)
    longitude = db.Column(db.Float, default=0.0)
    # 相对坐标（用于地图展示）
    x = db.Column(db.Float, default=0.0)
    y = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'scenic_id': self.scenic_id,
            'name': self.name,
            'node_type': self.node_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'x': self.x,
            'y': self.y,
        }


class GraphEdge(db.Model):
    """道路图边 - 不少于200条"""
    __tablename__ = 'graph_edges'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scenic_id = db.Column(db.Integer, db.ForeignKey('scenics.id'), nullable=False, index=True)
    from_node_id = db.Column(db.Integer, db.ForeignKey('graph_nodes.id'), nullable=False)
    to_node_id = db.Column(db.Integer, db.ForeignKey('graph_nodes.id'), nullable=False)
    # 距离（米）
    distance = db.Column(db.Float, nullable=False, default=100.0)
    # 道路名称
    road_name = db.Column(db.String(64), default='')
    # 是否双向
    bidirectional = db.Column(db.Boolean, default=True)
    # 拥挤度 0.0-1.0，0为空闲，1为拥挤
    congestion = db.Column(db.Float, default=0.3)
    # 道路类型: main=主路, branch=支路, path=小路, indoor=室内通道
    road_type = db.Column(db.String(32), default='main')
    # 允许的交通工具: walk=步行, bike=自行车, cart=电瓶车, all=所有
    transport_allowed = db.Column(db.String(32), default='all')
    # 理想速度（km/h）
    ideal_speed = db.Column(db.Float, default=5.0)

    from_node = db.relationship('GraphNode', foreign_keys=[from_node_id], backref='edges_from')
    to_node = db.relationship('GraphNode', foreign_keys=[to_node_id], backref='edges_to')

    def get_actual_speed(self):
        """根据拥挤度计算实际速度: 实际速度 = 拥挤度 * 理想速度"""
        # 拥挤度为小于等于1的正数，实际速度 = (1 - congestion + 0.1) * ideal_speed
        # 确保最低速度不为0
        factor = max(0.1, 1.0 - self.congestion)
        return factor * self.ideal_speed

    def get_time_cost(self):
        """获取通过该边的时间成本（分钟）"""
        speed = self.get_actual_speed()
        if speed <= 0:
            return float('inf')
        # distance是米，speed是km/h，转换为分钟
        return (self.distance / 1000.0) / speed * 60.0

    def to_dict(self):
        return {
            'id': self.id,
            'scenic_id': self.scenic_id,
            'from_node_id': self.from_node_id,
            'to_node_id': self.to_node_id,
            'distance': self.distance,
            'road_name': self.road_name,
            'bidirectional': self.bidirectional,
            'congestion': self.congestion,
            'road_type': self.road_type,
            'transport_allowed': self.transport_allowed,
            'ideal_speed': self.ideal_speed,
            'actual_speed': self.get_actual_speed(),
            'time_cost': self.get_time_cost(),
        }
