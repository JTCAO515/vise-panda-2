"""智能打包清单 — 按目的地/季节/天数/活动生成"""
PACKING_CATEGORIES = {
    "essentials": {"name": "证件/必备", "icon": "🪪", "items": [
        {"name": "护照/身份证", "condition": "always"},
        {"name": "签证/入境文件", "condition": "international"},
        {"name": "酒店预订单(打印件)", "condition": "always"},
        {"name": "机票/火车票(电子/打印)", "condition": "always"},
        {"name": "旅行保险单", "condition": "always"},
        {"name": "银行卡(银联/Visa/Master)", "condition": "always"},
        {"name": "现金(¥500-1000)", "condition": "always"},
        {"name": "手机+充电线", "condition": "always"},
    ]},
    "clothing": {"name": "衣物", "icon": "👕", "items": [
        {"name": "T恤/衬衫 (每日1件)", "condition": "always"},
        {"name": "长裤/短裤", "condition": "always"},
        {"name": "外套/冲锋衣", "condition": "always"},
        {"name": "内衣袜 (每日1套)", "condition": "always"},
        {"name": "舒适步行鞋", "condition": "always"},
        {"name": "凉鞋/拖鞋", "condition": "summer"},
        {"name": "羽绒服/保暖内衣", "condition": "winter"},
        {"name": "防晒衣/帽子", "condition": "summer"},
        {"name": "泳衣", "condition": "beach"},
        {"name": "雨衣/雨伞", "condition": "rainy"},
    ]},
    "toiletries": {"name": "洗漱/药品", "icon": "🧴", "items": [
        {"name": "牙刷/牙膏/洗面奶", "condition": "always"},
        {"name": "洗发水/沐浴露(旅行装)", "condition": "always"},
        {"name": "防晒霜 (SPF50+)", "condition": "summer"},
        {"name": "驱蚊液", "condition": "summer"},
        {"name": "感冒药/肠胃药", "condition": "always"},
        {"name": "创可贴/消毒棉片", "condition": "always"},
        {"name": "晕车药", "condition": "long_trip"},
        {"name": "高反药(红景天)", "condition": "high_altitude"},
        {"name": "隐形眼镜/眼镜", "condition": "always"},
    ]},
    "electronics": {"name": "电子设备", "icon": "🔌", "items": [
        {"name": "充电宝 (≤20000mAh)", "condition": "always"},
        {"name": "转换插头(三孔扁头)", "condition": "always"},
        {"name": "耳机", "condition": "always"},
        {"name": "相机/GoPro", "condition": "optional"},
        {"name": "车载充电器", "condition": "road_trip"},
        {"name": "VPN/上网卡/eSIM", "condition": "international"},
    ]},
    "misc": {"name": "其他", "icon": "📦", "items": [
        {"name": "保温杯", "condition": "always"},
        {"name": "纸巾/湿巾", "condition": "always"},
        {"name": "零食", "condition": "long_trip"},
        {"name": "颈枕/眼罩/耳塞", "condition": "long_trip"},
        {"name": "折叠购物袋", "condition": "always"},
        {"name": "锁(青旅/柜子)", "condition": "hostel"},
        {"name": "晾衣绳/衣架", "condition": "long_trip"},
    ]},
}

def get_packing_list(season: str = "summer", days: int = 3, 
                      activities: list = None, international: bool = False,
                      high_altitude: bool = False, beach: bool = False,
                      road_trip: bool = False, hostel: bool = False) -> str:
    """根据条件生成打包清单文本"""
    conditions = {"always": True, "optional": True}
    conditions[season] = True
    if days >= 5: conditions["long_trip"] = True
    if international: conditions["international"] = True
    if high_altitude: conditions["high_altitude"] = True
    if beach: conditions["beach"] = True
    if road_trip: conditions["road_trip"] = True
    if hostel: conditions["hostel"] = True
    if season in ("summer",): conditions["rainy"] = True

    lines = []
    for cat_key, cat in PACKING_CATEGORIES.items():
        items = [i for i in cat["items"] if conditions.get(i["condition"], False)]
        if not items:
            continue
        lines.append(f"\n**{cat['icon']} {cat['name']}**")
        for item in items:
            lines.append(f"- {item['name']}")
    
    return "\n".join(lines)
