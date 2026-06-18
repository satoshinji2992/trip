"""统一响应格式"""
from flask import jsonify


def success(data=None, message='操作成功', code=200):
    """成功响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data,
    }), code


def error(message='操作失败', code=400, data=None):
    """错误响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data,
    }), code


def paginate(query, page=1, per_page=20):
    """分页辅助函数"""
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
    }
