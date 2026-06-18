"""美食推荐模型"""
from datetime import datetime
from app import db


class Restaurant(db.Model):
    """餐厅/饭店表"""
    __tablename__ = 'restaurants'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scenic_id = db.Column(db.Integer, db.ForeignKey('scenics.id'), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    # 菜系: chinese=中餐, western=西餐, japanese=日料, korean=韩餐, fast_food=快餐, snack=小吃, cafe=咖啡甜品, other=其他
    cuisine = db.Column(db.String(32), default='chinese')
    description = db.Column(db.Text, default='')
    address = db.Column(db.String(256), default='')
    latitude = db.Column(db.Float, default=0.0)
    longitude = db.Column(db.Float, default=0.0)
    graph_node_id = db.Column(db.Integer, db.ForeignKey('graph_nodes.id'), nullable=True)
    # 人均价格
    avg_price = db.Column(db.Float, default=30.0)
    rating = db.Column(db.Float, default=4.0)
    rating_count = db.Column(db.Integer, default=0)
    popularity = db.Column(db.Integer, default=0)
    open_time = db.Column(db.String(64), default='08:00-22:00')
    cover_image = db.Column(db.String(256), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scenic = db.relationship('Scenic', backref='restaurants')
    graph_node = db.relationship('GraphNode', backref='restaurants_at_node')
    foods = db.relationship('Food', backref='restaurant', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'scenic_id': self.scenic_id,
            'name': self.name,
            'cuisine': self.cuisine,
            'description': self.description,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'graph_node_id': self.graph_node_id,
            'avg_price': self.avg_price,
            'rating': self.rating,
            'rating_count': self.rating_count,
            'popularity': self.popularity,
            'open_time': self.open_time,
            'cover_image': self.cover_image,
        }


class Food(db.Model):
    """美食/菜品表"""
    __tablename__ = 'foods'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    # 菜系
    cuisine = db.Column(db.String(32), default='chinese')
    description = db.Column(db.Text, default='')
    price = db.Column(db.Float, default=0.0)
    rating = db.Column(db.Float, default=4.0)
    popularity = db.Column(db.Integer, default=0)
    cover_image = db.Column(db.String(256), default='')
    # 标签
    tags = db.Column(db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'restaurant_name': self.restaurant.name if self.restaurant else '',
            'name': self.name,
            'cuisine': self.cuisine,
            'description': self.description,
            'price': self.price,
            'rating': self.rating,
            'popularity': self.popularity,
            'cover_image': self.cover_image,
            'tags': json.loads(self.tags) if self.tags else [],
        }
