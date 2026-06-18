"""旅游日记路由 - 日记管理、交流、全文搜索、压缩存储"""
import json
import os
import uuid
import requests
from flask import Blueprint, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.diary import Diary, DiaryComment, DiaryImage
from app.models.scenic import Scenic
from app.services.sort_service import recommend_diaries
from app.services.search_service import (
    fuzzy_search, fulltext_search_diaries, index_diary, rebuild_diary_index
)
from app.utils.response import success, error

diary_bp = Blueprint('diary', __name__)


@diary_bp.route('/create', methods=['POST'])
@login_required
def create_diary():
    """
    创建旅游日记
    内容使用zlib无损压缩存储（核心算法为无损压缩）
    """
    data = request.get_json()
    if not data:
        return error('请求数据为空')

    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    scenic_id = data.get('scenic_id')
    destination = data.get('destination', '').strip()
    tags = data.get('tags', [])
    is_public = data.get('is_public', True)

    if not title:
        return error('日记标题不能为空')
    if not content:
        return error('日记内容不能为空')

    # 如果提供了scenic_id，自动获取destination
    if scenic_id and not destination:
        scenic = Scenic.query.get(scenic_id)
        if scenic:
            destination = scenic.name

    diary = Diary(
        user_id=current_user.id,
        title=title,
        scenic_id=scenic_id,
        destination=destination,
        tags=json.dumps(tags, ensure_ascii=False),
        is_public=is_public,
    )
    # 使用zlib无损压缩存储内容
    diary.set_content(content)

    try:
        db.session.add(diary)
        db.session.commit()

        # 索引到全文搜索
        try:
            index_dir = current_app.config.get('WHOOSH_INDEX_DIR', 'whoosh_index')
            index_diary(diary.to_dict(include_content=True), index_dir)
        except Exception as e:
            current_app.logger.warning(f'全文索引更新失败: {e}')

        return success(diary.to_dict(), '日记创建成功')
    except Exception as e:
        db.session.rollback()
        return error(f'创建失败: {str(e)}')


@diary_bp.route('/update/<int:diary_id>', methods=['PUT'])
@login_required
def update_diary(diary_id):
    """更新日记"""
    diary = Diary.query.get(diary_id)
    if not diary:
        return error('日记不存在', 404)
    if diary.user_id != current_user.id:
        return error('无权修改此日记', 403)

    data = request.get_json()
    if not data:
        return error('请求数据为空')

    if 'title' in data:
        diary.title = data['title']
    if 'content' in data:
        diary.set_content(data['content'])  # 压缩存储
    if 'scenic_id' in data:
        diary.scenic_id = data['scenic_id']
    if 'destination' in data:
        diary.destination = data['destination']
    if 'tags' in data:
        diary.tags = json.dumps(data['tags'], ensure_ascii=False)
    if 'is_public' in data:
        diary.is_public = data['is_public']

    try:
        db.session.commit()
        # 更新全文索引
        try:
            index_dir = current_app.config.get('WHOOSH_INDEX_DIR', 'whoosh_index')
            index_diary(diary.to_dict(include_content=True), index_dir)
        except Exception as e:
            current_app.logger.warning(f'全文索引更新失败: {e}')
        return success(diary.to_dict(), '更新成功')
    except Exception as e:
        db.session.rollback()
        return error(f'更新失败: {str(e)}')


@diary_bp.route('/delete/<int:diary_id>', methods=['DELETE'])
@login_required
def delete_diary(diary_id):
    """删除日记"""
    diary = Diary.query.get(diary_id)
    if not diary:
        return error('日记不存在', 404)
    if diary.user_id != current_user.id:
        return error('无权删除此日记', 403)

    try:
        db.session.delete(diary)
        db.session.commit()
        return success(message='删除成功')
    except Exception as e:
        db.session.rollback()
        return error(f'删除失败: {str(e)}')


@diary_bp.route('/<int:diary_id>', methods=['GET'])
def get_diary(diary_id):
    """
    获取日记详情
    每次浏览增加浏览量（热度）
    """
    diary = Diary.query.get(diary_id)
    if not diary:
        return error('日记不存在', 404)

    # 增加浏览量
    diary.view_count += 1
    db.session.commit()

    data = diary.to_dict(include_content=True)
    # 附加图片
    data['images'] = [img.to_dict() for img in diary.images.all()]
    data['videos'] = _list_diary_animation_videos(diary_id)
    # 附加评论
    data['comments'] = [c.to_dict() for c in diary.comments.order_by(DiaryComment.created_at.desc()).all()]

    return success(data)


@diary_bp.route('/my', methods=['GET'])
@login_required
def my_diaries():
    """获取我的日记列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Diary.query.filter_by(user_id=current_user.id).order_by(Diary.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success({
        'items': [d.to_dict(include_content=False) for d in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
    })


@diary_bp.route('/public', methods=['GET'])
def public_diaries():
    """
    浏览所有公开日记 - 支持推荐排序
    核心算法：排序算法，按热度、评价、兴趣推荐
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'mixed')
    top_k = request.args.get('top_k', 10, type=int)

    all_diaries = Diary.query.filter_by(is_public=True).all()
    diaries_data = [d.to_dict(include_content=False) for d in all_diaries]

    # 获取用户兴趣
    user_interests = None
    if current_user.is_authenticated:
        try:
            user_interests = json.loads(current_user.interests) if current_user.interests else None
        except Exception:
            user_interests = None

    # 推荐排序
    sorted_data = recommend_diaries(diaries_data, user_interests, sort_by, top_k=len(diaries_data))

    # 分页
    start = (page - 1) * per_page
    end = start + per_page
    paged_data = sorted_data[start:end]

    return success({
        'items': paged_data,
        'total': len(sorted_data),
        'page': page,
        'per_page': per_page,
    })


@diary_bp.route('/by-destination', methods=['GET'])
def diaries_by_destination():
    """
    按目的地查找日记 - 核心算法为查找算法和排序算法
    输入旅游目的地，对目的地相关日记按热度和评分排序
    """
    destination = request.args.get('destination', '').strip()
    sort_by = request.args.get('sort_by', 'mixed')

    if not destination:
        return error('目的地不能为空')

    all_diaries = Diary.query.filter_by(is_public=True).all()
    diaries_data = [d.to_dict(include_content=False) for d in all_diaries]

    # 按目的地模糊查找
    matched = fuzzy_search(destination, diaries_data, fields=['destination', 'title', 'tags'])

    # 排序
    user_interests = None
    if current_user.is_authenticated:
        try:
            user_interests = json.loads(current_user.interests) if current_user.interests else None
        except Exception:
            user_interests = None

    sorted_data = recommend_diaries(matched, user_interests, sort_by, top_k=len(matched))

    return success({
        'items': sorted_data,
        'total': len(sorted_data),
        'destination': destination,
    })


@diary_bp.route('/search', methods=['GET'])
def search_diaries():
    """
    日记搜索 - 支持精确查找和模糊查找
    核心算法：查找算法（考虑日记数量较大，变化非常快的情况下进行高效查找）
    使用Trie树进行高效前缀匹配
    """
    query_str = request.args.get('q', '').strip()
    sort_by = request.args.get('sort_by', 'mixed')

    if not query_str:
        return error('搜索关键词不能为空')

    all_diaries = Diary.query.filter_by(is_public=True).all()
    diaries_data = [d.to_dict(include_content=False) for d in all_diaries]

    # 模糊查找
    matched = fuzzy_search(query_str, diaries_data, fields=['title', 'destination', 'author_name'])

    # 排序
    sorted_data = recommend_diaries(matched, sort_by=sort_by, top_k=len(matched))

    return success({
        'items': sorted_data,
        'total': len(sorted_data),
        'query': query_str,
    })


@diary_bp.route('/fulltext-search', methods=['GET'])
def fulltext_search():
    """
    日记全文搜索 - 核心算法为文本搜索
    按日记内容进行全文检索，使用Whoosh实现BM25F评分
    """
    query_str = request.args.get('q', '').strip()
    limit = request.args.get('limit', 50, type=int)

    if not query_str:
        return error('搜索关键词不能为空')

    index_dir = current_app.config.get('WHOOSH_INDEX_DIR', 'whoosh_index')

    try:
        results = fulltext_search_diaries(query_str, index_dir, limit)

        # 获取完整日记数据
        diary_ids = [r['diary_id'] for r in results]
        diaries = Diary.query.filter(Diary.id.in_(diary_ids)).all()
        diary_map = {d.id: d.to_dict(include_content=False) for d in diaries}

        enriched_results = []
        for r in results:
            diary_data = diary_map.get(r['diary_id'])
            if diary_data:
                diary_data['search_score'] = r['score']
                enriched_results.append(diary_data)

        if len(enriched_results) < limit:
            existing_ids = {item['id'] for item in enriched_results}
            fallback_diaries = Diary.query.filter_by(is_public=True).all()
            for diary in fallback_diaries:
                if diary.id in existing_ids:
                    continue
                searchable = ' '.join([
                    diary.title or '',
                    diary.destination or '',
                    diary.tags or '',
                    diary.get_content() or '',
                ])
                if query_str in searchable:
                    diary_data = diary.to_dict(include_content=False)
                    diary_data['search_score'] = 0.1
                    enriched_results.append(diary_data)
                    existing_ids.add(diary.id)
                    if len(enriched_results) >= limit:
                        break

        return success({
            'items': enriched_results,
            'total': len(enriched_results),
            'query': query_str,
        })
    except Exception as e:
        return error(f'全文搜索失败: {str(e)}')


@diary_bp.route('/<int:diary_id>/comment', methods=['POST'])
@login_required
def add_comment(diary_id):
    """
    添加评论和评分
    每位同学浏览完可以对旅游日记进行评分
    """
    diary = Diary.query.get(diary_id)
    if not diary:
        return error('日记不存在', 404)

    data = request.get_json()
    if not data:
        return error('请求数据为空')

    content = data.get('content', '').strip()
    rating = data.get('rating', 5.0)

    if not content:
        return error('评论内容不能为空')
    if rating < 1 or rating > 5:
        return error('评分范围为1-5')

    # 检查是否已经评论过
    existing = DiaryComment.query.filter_by(
        diary_id=diary_id, user_id=current_user.id
    ).first()
    if existing:
        return error('您已经评论过该日记')

    comment = DiaryComment(
        diary_id=diary_id,
        user_id=current_user.id,
        content=content,
        rating=rating,
    )

    # 更新日记评分
    diary.rating_sum += rating
    diary.rating_count += 1

    try:
        db.session.add(comment)
        db.session.commit()
        return success(comment.to_dict(), '评论成功')
    except Exception as e:
        db.session.rollback()
        return error(f'评论失败: {str(e)}')


@diary_bp.route('/<int:diary_id>/upload-image', methods=['POST'])
@login_required
def upload_diary_image(diary_id):
    """上传日记图片"""
    diary = Diary.query.get(diary_id)
    if not diary:
        return error('日记不存在', 404)
    if diary.user_id != current_user.id:
        return error('无权操作', 403)

    if 'image' not in request.files:
        return error('未上传图片')

    file = request.files['image']
    if file.filename == '':
        return error('文件名为空')

    # 保存文件
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'diary', str(diary_id))
    os.makedirs(upload_dir, exist_ok=True)

    from werkzeug.utils import secure_filename
    import uuid
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
    filename = f'{uuid.uuid4().hex}.{ext}'
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    relative_path = f'/uploads/diary/{diary_id}/{filename}'
    description = request.form.get('description', '')

    image = DiaryImage(
        diary_id=diary_id,
        image_path=relative_path,
        description=description,
    )

    try:
        db.session.add(image)
        db.session.commit()
        return success(image.to_dict(), '图片上传成功')
    except Exception as e:
        db.session.rollback()
        return error(f'上传失败: {str(e)}')


@diary_bp.route('/<int:diary_id>/image/<int:image_id>', methods=['DELETE'])
@login_required
def delete_diary_image(diary_id, image_id):
    """删除日记图片"""
    diary = Diary.query.get(diary_id)
    if not diary:
        return error('日记不存在', 404)
    if diary.user_id != current_user.id:
        return error('无权操作', 403)

    image = DiaryImage.query.filter_by(id=image_id, diary_id=diary_id).first()
    if not image:
        return error('图片不存在', 404)

    image_path = _resolve_upload_path(image.image_path)
    try:
        db.session.delete(image)
        db.session.commit()
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
        return success(message='图片删除成功')
    except Exception as e:
        db.session.rollback()
        return error(f'删除失败: {str(e)}')


@diary_bp.route('/<int:diary_id>/generate-animation', methods=['POST'])
@login_required
def generate_diary_animation(diary_id):
    """调用局域网Wan视频服务生成旅游动画"""
    diary = Diary.query.get(diary_id)
    if not diary:
        return error('日记不存在', 404)
    if diary.user_id != current_user.id:
        return error('无权操作', 403)

    data = request.get_json(silent=True) or {}
    user_prompt = data.get('prompt', '').strip()
    image_id = data.get('image_id')
    size = data.get('size', '832*480')
    sample_steps = str(data.get('sample_steps', '50'))
    frame_num = str(data.get('frame_num', '121'))
    seed = str(data.get('seed', '-1'))
    selected_image = None
    if image_id:
        selected_image = diary.images.filter_by(id=image_id).first()
    if not selected_image:
        selected_image = diary.images.order_by(DiaryImage.created_at.asc()).first()
    if not selected_image:
        return error('请先上传日记图片，再生成旅游动画')

    prompt = user_prompt or current_app.config.get('AIGC_DEFAULT_PROMPT') or (
        'Create a 5-second cinematic yet realistic travel video of the Forbidden City based on the uploaded photo. '
        'Preserve the palace architecture, roof shape, symmetry, colors, courtyard layout, and original perspective. '
        'Use a slow, stable forward camera movement with subtle parallax. Add natural daylight, gentle atmospheric motion, '
        'and a small amount of realistic visitor movement in the distance. Do not alter the building structure, roof details, '
        'gates, or courtyard geometry. Do not add text, logos, watermarks, fantasy effects, distorted people, warped architecture, '
        'or unrealistic objects. The final video should be clear, elegant, historically respectful, and suitable for a travel diary.'
    )

    image_path = _resolve_upload_path(selected_image.image_path)
    if not image_path or not os.path.exists(image_path):
        return error('日记图片文件不存在，请重新上传图片')

    base_url = current_app.config.get('AIGC_BASE_URL', 'http://10.21.129.82:8000').rstrip('/')
    endpoint = current_app.config.get('AIGC_ENDPOINT', '/generate')
    url = f"{base_url}/{endpoint.lstrip('/')}"

    try:
        with open(image_path, 'rb') as image_file:
            response = requests.post(
                url,
                files={'image': image_file},
                data={
                    'prompt': prompt,
                    'size': size,
                    'sample_steps': sample_steps,
                    'frame_num': frame_num,
                    'seed': seed,
                },
                timeout=None,
            )
        if not response.ok:
            detail = response.text[:500] if response.text else response.reason
            current_app.logger.warning(
                f'AIGC接口调用失败: status={response.status_code}, detail={detail}, '
                f'params={{size:{size}, sample_steps:{sample_steps}, frame_num:{frame_num}, seed:{seed}}}'
            )
            return error(f'AIGC接口调用失败: HTTP {response.status_code} - {detail}')
    except Exception as exc:
        current_app.logger.warning(f'AIGC接口调用失败: {exc}')
        return error(f'AIGC接口调用失败: {str(exc)}')

    video_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'diary', str(diary_id))
    os.makedirs(video_dir, exist_ok=True)
    video_filename = f'animation_{uuid.uuid4().hex}.mp4'
    video_path = os.path.join(video_dir, video_filename)
    with open(video_path, 'wb') as video_file:
        video_file.write(response.content)

    video_url = f'/uploads/diary/{diary_id}/{video_filename}'
    return success({
        'video_url': video_url,
        'prompt': prompt,
        'image_url': selected_image.image_path,
        'service_url': url,
        'params': {
            'size': size,
            'sample_steps': sample_steps,
            'frame_num': frame_num,
            'seed': seed,
        },
    }, '动画生成成功')


def _resolve_upload_path(relative_path):
    """将/uploads开头的访问路径转换为本地上传文件路径"""
    if not relative_path:
        return ''
    prefix = '/uploads/'
    if relative_path.startswith(prefix):
        return os.path.join(current_app.config['UPLOAD_FOLDER'], relative_path[len(prefix):])
    return os.path.join(current_app.config['UPLOAD_FOLDER'], relative_path.lstrip('/'))


def _list_diary_animation_videos(diary_id):
    """读取已生成的日记动画文件，刷新页面后也能展示历史结果"""
    video_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'diary', str(diary_id))
    if not os.path.isdir(video_dir):
        return []
    videos = []
    for filename in sorted(os.listdir(video_dir), reverse=True):
        if not filename.startswith('animation_') or not filename.lower().endswith('.mp4'):
            continue
        file_path = os.path.join(video_dir, filename)
        videos.append({
            'filename': filename,
            'video_url': f'/uploads/diary/{diary_id}/{filename}',
            'created_at': os.path.getmtime(file_path),
        })
    return videos


@diary_bp.route('/rebuild-index', methods=['POST'])
def rebuild_search_index():
    """重建全文搜索索引"""
    index_dir = current_app.config.get('WHOOSH_INDEX_DIR', 'whoosh_index')
    try:
        count = rebuild_diary_index(index_dir)
        return success({'indexed_count': count}, f'索引重建完成，共索引 {count} 篇日记')
    except Exception as e:
        return error(f'索引重建失败: {str(e)}')
