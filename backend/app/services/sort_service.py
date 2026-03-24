"""
排序算法服务 - 核心算法，自实现
包含：推荐排序（热度+评价+兴趣）、Top-K排序（不完全排序）、多维度排序
所有排序算法基于自设计的数据结构，自己编程实现
"""


class SortableItem:
    """可排序项 - 自定义数据结构"""
    __slots__ = ['data', 'score', 'key']

    def __init__(self, data, score=0.0, key=None):
        self.data = data
        self.score = score
        self.key = key

    def __lt__(self, other):
        return self.score < other.score

    def __gt__(self, other):
        return self.score > other.score

    def __eq__(self, other):
        return self.score == other.score


class MaxHeap:
    """最大堆 - 用于Top-K排序，自实现数据结构"""

    def __init__(self):
        self._data = []
        self._size = 0

    @property
    def size(self):
        return self._size

    def peek(self):
        if self._size == 0:
            return None
        return self._data[0]

    def push(self, item):
        """插入元素"""
        self._data.append(item)
        self._size += 1
        self._sift_up(self._size - 1)

    def pop(self):
        """弹出最大元素"""
        if self._size == 0:
            raise IndexError("堆为空")
        max_item = self._data[0]
        self._size -= 1
        if self._size > 0:
            self._data[0] = self._data[self._size]
            self._data.pop()
            self._sift_down(0)
        else:
            self._data.pop()
        return max_item

    def _sift_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if self._data[index].score > self._data[parent].score:
                self._data[index], self._data[parent] = self._data[parent], self._data[index]
                index = parent
            else:
                break

    def _sift_down(self, index):
        while True:
            largest = index
            left = 2 * index + 1
            right = 2 * index + 2
            if left < self._size and self._data[left].score > self._data[largest].score:
                largest = left
            if right < self._size and self._data[right].score > self._data[largest].score:
                largest = right
            if largest != index:
                self._data[index], self._data[largest] = self._data[largest], self._data[index]
                index = largest
            else:
                break


class MinHeapForTopK:
    """最小堆 - 用于维护Top-K元素，自实现数据结构
    
    核心思路：维护一个大小为K的最小堆，堆顶是当前Top-K中最小的元素。
    新元素如果比堆顶大则替换堆顶，保证堆中始终是最大的K个元素。
    时间复杂度：O(N * log K)，优于完全排序的 O(N * log N)
    """

    def __init__(self, capacity):
        self._data = []
        self._size = 0
        self._capacity = capacity

    @property
    def size(self):
        return self._size

    def peek(self):
        if self._size == 0:
            return None
        return self._data[0]

    def push(self, item):
        """插入元素，如果堆未满直接插入，否则和堆顶比较"""
        if self._size < self._capacity:
            self._data.append(item)
            self._size += 1
            self._sift_up(self._size - 1)
        elif item.score > self._data[0].score:
            self._data[0] = item
            self._sift_down(0)

    def pop(self):
        if self._size == 0:
            raise IndexError("堆为空")
        min_item = self._data[0]
        self._size -= 1
        if self._size > 0:
            self._data[0] = self._data[self._size]
            self._data.pop()
            self._sift_down(0)
        else:
            self._data.pop()
        return min_item

    def get_sorted_desc(self):
        """获取所有元素并按分数降序排列"""
        result = []
        while self._size > 0:
            result.append(self.pop())
        result.reverse()
        return result

    def _sift_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if self._data[index].score < self._data[parent].score:
                self._data[index], self._data[parent] = self._data[parent], self._data[index]
                index = parent
            else:
                break

    def _sift_down(self, index):
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2
            if left < self._size and self._data[left].score < self._data[smallest].score:
                smallest = left
            if right < self._size and self._data[right].score < self._data[smallest].score:
                smallest = right
            if smallest != index:
                self._data[index], self._data[smallest] = self._data[smallest], self._data[index]
                index = smallest
            else:
                break


def top_k_sort(items, k=10):
    """
    Top-K排序算法 - 核心算法
    不需要完全排序，只需要找出前K个最大元素
    使用最小堆实现，时间复杂度 O(N * log K)
    
    参数:
        items: SortableItem列表
        k: 返回前K个
    
    返回:
        前K个元素（按分数降序）
    """
    if not items:
        return []
    k = min(k, len(items))
    heap = MinHeapForTopK(k)
    for item in items:
        heap.push(item)
    return heap.get_sorted_desc()


def calculate_scenic_score(scenic_data, user_interests=None, sort_by='popularity'):
    """
    计算景区/校园的推荐分数
    
    综合考虑：热度、评价、用户兴趣匹配度
    分数 = w1 * 热度归一化 + w2 * 评价归一化 + w3 * 兴趣匹配度
    
    参数:
        scenic_data: 景区数据字典
        user_interests: 用户兴趣标签列表
        sort_by: 排序依据 - popularity=热度, rating=评价, mixed=综合
    """
    import json

    popularity = scenic_data.get('popularity', 0)
    rating = scenic_data.get('rating', 0)
    tags = scenic_data.get('tags', [])
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []

    if sort_by == 'popularity':
        return float(popularity)
    elif sort_by == 'rating':
        return float(rating) * 1000 + float(popularity)
    else:
        # 综合排序
        # 热度分 (0-100归一化，假设最大热度10000)
        pop_score = min(popularity / 10000.0, 1.0) * 100
        # 评价分 (0-100归一化，评价0-5)
        rating_score = (rating / 5.0) * 100
        # 兴趣匹配分
        interest_score = 0
        if user_interests and tags:
            matched = len(set(user_interests) & set(tags))
            interest_score = (matched / max(len(user_interests), 1)) * 100

        # 加权综合: 热度40% + 评价30% + 兴趣30%
        return pop_score * 0.4 + rating_score * 0.3 + interest_score * 0.3


def recommend_scenics(scenics_data, user_interests=None, sort_by='mixed', top_k=10):
    """
    景区推荐排序 - 核心功能
    使用Top-K排序算法，不经过完全排序即可排好前10个
    
    参数:
        scenics_data: 景区数据字典列表
        user_interests: 用户兴趣
        sort_by: 排序方式
        top_k: 返回前K个
    
    返回:
        排序后的景区列表
    """
    items = []
    for scenic in scenics_data:
        score = calculate_scenic_score(scenic, user_interests, sort_by)
        items.append(SortableItem(data=scenic, score=score))

    sorted_items = top_k_sort(items, k=top_k)
    return [item.data for item in sorted_items]


def calculate_diary_score(diary_data, user_interests=None, sort_by='mixed'):
    """
    计算日记推荐分数
    综合考虑：热度（浏览量）、评价、用户兴趣匹配度
    """
    import json

    view_count = diary_data.get('view_count', 0)
    avg_rating = diary_data.get('average_rating', 0)
    tags = diary_data.get('tags', [])
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []

    if sort_by == 'popularity':
        return float(view_count)
    elif sort_by == 'rating':
        return float(avg_rating) * 10000 + float(view_count)
    else:
        pop_score = min(view_count / 1000.0, 1.0) * 100
        rating_score = (avg_rating / 5.0) * 100
        interest_score = 0
        if user_interests and tags:
            matched = len(set(user_interests) & set(tags))
            interest_score = (matched / max(len(user_interests), 1)) * 100
        return pop_score * 0.4 + rating_score * 0.3 + interest_score * 0.3


def recommend_diaries(diaries_data, user_interests=None, sort_by='mixed', top_k=10):
    """日记推荐排序"""
    items = []
    for diary in diaries_data:
        score = calculate_diary_score(diary, user_interests, sort_by)
        items.append(SortableItem(data=diary, score=score))
    sorted_items = top_k_sort(items, k=top_k)
    return [item.data for item in sorted_items]


def calculate_food_score(food_data, user_preferences=None, sort_by='mixed', user_location=None):
    """
    计算美食推荐分数
    综合考虑：热度、评价、距离（如果有用户位置）
    """
    popularity = food_data.get('popularity', 0)
    rating = food_data.get('rating', 0)
    distance = food_data.get('distance', 0)

    if sort_by == 'popularity':
        return float(popularity)
    elif sort_by == 'rating':
        return float(rating) * 10000 + float(popularity)
    elif sort_by == 'distance':
        # 距离越近分数越高
        return 1000000.0 / max(distance, 1.0)
    else:
        pop_score = min(popularity / 1000.0, 1.0) * 100
        rating_score = (rating / 5.0) * 100
        dist_score = max(0, 100 - distance / 10.0) if distance else 50
        return pop_score * 0.3 + rating_score * 0.4 + dist_score * 0.3


def recommend_foods(foods_data, sort_by='mixed', top_k=10):
    """美食推荐排序"""
    items = []
    for food in foods_data:
        score = calculate_food_score(food, sort_by=sort_by)
        items.append(SortableItem(data=food, score=score))
    sorted_items = top_k_sort(items, k=top_k)
    return [item.data for item in sorted_items]


def sort_by_path_distance(items, graph, source_node_id, node_id_key='graph_node_id'):
    """
    按路径距离排序 - 核心算法
    使用Dijkstra计算从源点到各目标的实际路径距离（非直线距离），再排序
    
    参数:
        items: 数据字典列表，每个须包含 graph_node_id
        graph: Graph对象
        source_node_id: 源节点ID
        node_id_key: 节点ID字段名
    
    返回:
        按路径距离排序的列表，每项附加 distance 字段
    """
    from app.services.graph_service import dijkstra

    if not items or source_node_id is None:
        return items

    # 一次Dijkstra计算从源点到所有节点的最短距离
    distances, _ = dijkstra(graph, source_node_id, weight_type='distance')

    for item in items:
        node_id = item.get(node_id_key)
        if node_id and node_id in distances:
            item['distance'] = distances[node_id]
        else:
            item['distance'] = float('inf')

    # 按距离排序
    sortable = [SortableItem(data=item, score=-item['distance']) for item in items]
    # score取负是因为Top-K返回分数最大的，而我们要距离最小的
    sorted_items = top_k_sort(sortable, k=len(sortable))
    # 反转因为分数为负
    result = [item.data for item in sorted_items]
    result.reverse()
    return result
