"""旅游日记模型"""
import zlib
import base64
from datetime import datetime
from app import db


class Diary(db.Model):
    """旅游日记表"""
    __tablename__ = 'diaries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(256), nullable=False, index=True)
    # 内容使用zlib无损压缩存储
    content_compressed = db.Column(db.LargeBinary, nullable=True)
    # 关联的景区/校园
    scenic_id = db.Column(db.Integer, db.ForeignKey('scenics.id'), nullable=True)
    # 目的地名称（冗余字段，便于搜索）
    destination = db.Column(db.String(128), default='', index=True)
    # 热度（浏览量）
    view_count = db.Column(db.Integer, default=0)
    # 评分总分
    rating_sum = db.Column(db.Float, default=0.0)
    # 评分人数
    rating_count = db.Column(db.Integer, default=0)
    # 标签，JSON数组
    tags = db.Column(db.Text, default='[]')
    # 是否公开
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    images = db.relationship('DiaryImage', backref='diary', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('DiaryComment', backref='diary', lazy='dynamic', cascade='all, delete-orphan')
    scenic = db.relationship('Scenic', backref='diaries')

    def set_content(self, text):
        """使用zlib无损压缩存储内容"""
        if text:
            compressed = zlib.compress(text.encode('utf-8'), level=9)
            self.content_compressed = compressed

    def get_content(self):
        """解压缩获取内容"""
        if self.content_compressed:
            try:
                return zlib.decompress(self.content_compressed).decode('utf-8')
            except Exception:
                return ''
        return ''

    @property
    def average_rating(self):
        """计算平均评分"""
        if self.rating_count == 0:
            return 0.0
        return round(self.rating_sum / self.rating_count, 1)

    def to_dict(self, include_content=True):
        """序列化"""
        import json
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'author_name': self.author.nickname or self.author.username if self.author else '',
            'title': self.title,
            'scenic_id': self.scenic_id,
            'destination': self.destination,
            'view_count': self.view_count,
            'average_rating': self.average_rating,
            'rating_count': self.rating_count,
            'tags': json.loads(self.tags) if self.tags else [],
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'image_count': self.images.count() if self.images else 0,
            'comment_count': self.comments.count() if self.comments else 0,
        }
        if include_content:
            result['content'] = self.get_content()
            # 计算压缩率
            content = self.get_content()
            if content and self.content_compressed:
                original_size = len(content.encode('utf-8'))
                compressed_size = len(self.content_compressed)
                result['compression_ratio'] = round(compressed_size / original_size, 4) if original_size > 0 else 1.0
        return result


class DiaryImage(db.Model):
    """日记图片表"""
    __tablename__ = 'diary_images'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    diary_id = db.Column(db.Integer, db.ForeignKey('diaries.id'), nullable=False, index=True)
    image_path = db.Column(db.String(256), nullable=False)
    description = db.Column(db.String(256), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'diary_id': self.diary_id,
            'image_path': self.image_path,
            'description': self.description,
        }


class DiaryComment(db.Model):
    """日记评论/评分表"""
    __tablename__ = 'diary_comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    diary_id = db.Column(db.Integer, db.ForeignKey('diaries.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, default='')
    # 评分 1-5
    rating = db.Column(db.Float, default=5.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='diary_comments')

    def to_dict(self):
        return {
            'id': self.id,
            'diary_id': self.diary_id,
            'user_id': self.user_id,
            'user_name': self.user.nickname or self.user.username if self.user else '',
            'content': self.content,
            'rating': self.rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
