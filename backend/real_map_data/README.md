# 真实地图导入说明

`init_data_graph.py` 现在支持三种道路图来源，优先级如下：

1. `backend/real_map_data/manifest.json` 中声明的本地 `GeoJSON`
2. 按景区中心点从 `OpenStreetMap / Overpass` 拉取真实道路
3. 如果以上失败，自动回退到原有模拟道路图

## 1. 使用本地 GeoJSON

在本目录放置 GeoJSON 文件，然后新建 `manifest.json`，格式如下：

```json
{
  "故宫博物院": {
    "source": "geojson",
    "file": "gugong.geojson"
  },
  "北京大学": {
    "source": "geojson",
    "file": "pku.geojson"
  }
}
```

要求：

- 文件内容为 `FeatureCollection`
- 几何类型支持 `LineString` 和 `MultiLineString`
- `properties` 可选字段：`name`、`highway`、`oneway`、`surface`

## 2. 直接拉取 OpenStreetMap

如果不提供 `manifest.json`，可以通过环境变量指定要拉取真实地图的景区：

```bash
export REAL_MAP_SCENICS="故宫博物院,北京大学"
python init_data.py
```

可选环境变量：

- `REAL_MAP_RADIUS=900`
  以景区中心点为圆心抓取多少米范围内的道路
- `REAL_MAP_FETCH_ALL=1`
  对初始化覆盖到的全部景区/校园都尝试真实地图
- `OVERPASS_URL=https://overpass-api.de/api/interpreter`
  自定义 Overpass 服务地址

## 3. 说明

- 真实地图抓取依赖外网访问 Overpass API
- 如果接口超时、区域无有效道路、或数据解析失败，初始化脚本会自动改用模拟图，不会中断整次初始化
- 设施和餐厅初始化会优先落在真实道路节点上，避免点位漂移
