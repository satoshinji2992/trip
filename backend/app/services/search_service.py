"""
搜索服务 - 核心算法
包含：查找算法、模糊查找算法、全文搜索（Whoosh）、文本搜索
所有核心算法基于自设计的数据结构，自己编程实现
"""
import os
import re
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, NUMERIC, KEYWORD
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.analysis import RegexTokenizer, LowercaseFilter
from whoosh import scoring


# ==================== 自实现查找算法 ====================

class TrieNode:
    """Trie树节点 - 自定义数据结构，用于高效前缀匹配和模糊查找"""
    __slots__ = ['children', 'is_end', 'data_ids']

    def __init__(self):
        self.children = {}
        self.is_end = False
        self.data_ids = []  # 存储匹配到该节点的数据ID列表


class Trie:
    """
    Trie树（字典树）- 自实现数据结构
    用于高效的字符串前缀查找和模糊匹配
    时间复杂度：插入 O(L)，查找 O(L)，其中L为字符串长度
    """

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, data_id):
        """插入单词及关联数据ID"""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.data_ids.append(data_id)  # 每个前缀节点都记录
        node.is_end = True

    def search_prefix(self, prefix):
        """前缀查找 - 返回所有以prefix为前缀的数据ID"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        return list(set(node.data_ids))

    def exact_search(self, word):
        """精确查找"""
        node = self.root
        for char in word:
            if char not in node.children:
                return []
            node = node.children[char]
        if node.is_end:
            return list(set(node.data_ids))
        return []


def fuzzy_match(pattern, text, max_distance=2):
    """
    模糊匹配算法 - 基于编辑距离（Levenshtein距离）
    自实现动态规划算法
    
    参数:
        pattern: 搜索模式
        text: 目标文本
        max_distance: 最大允许编辑距离
    
    返回:
        (is_match, edit_distance)
    """
    m, n = len(pattern), len(text)

    # 优化：如果长度差超过max_distance，直接返回不匹配
    if abs(m - n) > max_distance:
        return False, abs(m - n)

    # DP表：dp[i][j] = pattern[:i] 和 text[:j] 的编辑距离
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if pattern[i - 1] == text[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # 删除
                    dp[i][j - 1],      # 插入
                    dp[i - 1][j - 1]   # 替换
                )

    distance = dp[m][n]
    return distance <= max_distance, distance


def fuzzy_search(query, items, fields, max_distance=2):
    """
    模糊搜索 - 在多个字段中进行模糊匹配
    核心算法为模糊查找算法
    
    参数:
        query: 搜索关键词
        items: 数据字典列表
        fields: 要搜索的字段名列表
        max_distance: 最大编辑距离
    
    返回:
        匹配的项列表，按匹配度排序
    """
    if not query or not items:
        return items

    query_lower = query.lower()
    results = []

    for item in items:
        best_distance = float('inf')
        matched = False

        for field in fields:
            value = str(item.get(field, '')).lower()
            if not value:
                continue

            # 1. 完全包含匹配（优先级最高）
            if query_lower in value:
                matched = True
                best_distance = 0
                break

            # 2. 分词后逐词匹配
            words = re.split(r'[\s,，。.、/\\]+', value)
            for word in words:
                if not word:
                    continue
                is_match, dist = fuzzy_match(query_lower, word, max_distance)
                if is_match and dist < best_distance:
                    best_distance = dist
                    matched = True

            # 3. 对整个值进行子串模糊匹配
            if not matched and len(query_lower) <= len(value):
                for start in range(len(value) - len(query_lower) + 1):
                    substr = value[start:start + len(query_lower)]
                    is_match, dist = fuzzy_match(query_lower, substr, max_distance)
                    if is_match and dist < best_distance:
                        best_distance = dist
                        matched = True

        if matched:
            item_copy = dict(item)
            item_copy['_match_distance'] = best_distance
            results.append(item_copy)

    # 按匹配距离排序（距离越小越匹配）
    results.sort(key=lambda x: x.get('_match_distance', float('inf')))
    return results


# ==================== Whoosh全文搜索 ====================

# 日记全文搜索Schema
diary_schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True, analyzer=RegexTokenizer() | LowercaseFilter()),
    content=TEXT(stored=True, analyzer=RegexTokenizer() | LowercaseFilter()),
    destination=TEXT(stored=True),
    tags=KEYWORD(stored=True, commas=True),
    user_id=ID(stored=True),
)


def get_or_create_diary_index(index_dir):
    """获取或创建日记全文搜索索引"""
    if not os.path.exists(index_dir):
        os.makedirs(index_dir, exist_ok=True)
    if exists_in(index_dir, indexname='diary'):
        return open_dir(index_dir, indexname='diary')
    return create_in(index_dir, diary_schema, indexname='diary')


def index_diary(diary_data, index_dir):
    """索引一篇日记到Whoosh"""
    ix = get_or_create_diary_index(index_dir)
    writer = ix.writer()
    writer.update_document(
        id=str(diary_data['id']),
        title=diary_data.get('title', ''),
        content=diary_data.get('content', ''),
        destination=diary_data.get('destination', ''),
        tags=','.join(diary_data.get('tags', [])) if isinstance(diary_data.get('tags'), list) else '',
        user_id=str(diary_data.get('user_id', '')),
    )
    writer.commit()


def fulltext_search_diaries(query_str, index_dir, limit=50):
    """
    日记全文搜索 - 核心算法为文本搜索
    使用Whoosh实现高效全文检索
    
    参数:
        query_str: 搜索关键词
        index_dir: 索引目录
        limit: 返回结果数限制
    
    返回:
        匹配的日记ID列表及分数
    """
    ix = get_or_create_diary_index(index_dir)
    results_list = []

    with ix.searcher(weighting=scoring.BM25F()) as searcher:
        parser = MultifieldParser(['title', 'content', 'destination', 'tags'], ix.schema, group=OrGroup)
        query = parser.parse(query_str)
        results = searcher.search(query, limit=limit)

        for hit in results:
            results_list.append({
                'diary_id': int(hit['id']),
                'score': hit.score,
                'title': hit.get('title', ''),
            })

    return results_list


def rebuild_diary_index(index_dir):
    """重建日记全文搜索索引"""
    from app.models.diary import Diary

    ix = get_or_create_diary_index(index_dir)
    writer = ix.writer()

    diaries = Diary.query.filter_by(is_public=True).all()
    for diary in diaries:
        import json
        tags = json.loads(diary.tags) if diary.tags else []
        writer.update_document(
            id=str(diary.id),
            title=diary.title or '',
            content=diary.get_content() or '',
            destination=diary.destination or '',
            tags=','.join(tags) if isinstance(tags, list) else '',
            user_id=str(diary.user_id),
        )
    writer.commit()
    return len(diaries)
