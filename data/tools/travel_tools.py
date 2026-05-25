"""旅行决策工具集：决策树 + 文案生成 + 游记"""
import random

DECISION_QUESTIONS = [
    {"q": "你更喜欢哪种旅行节奏？", "options": {"a": "悠闲慢游", "b": "紧凑打卡"}},
    {"q": "最看重什么？", "options": {"a": "美食", "b": "历史", "c": "自然", "d": "都市"}},
    {"q": "预算大概？", "options": {"a": "穷游 ¥2000内", "b": "中等 ¥5000", "c": "豪华 ¥1万+"}},
    {"q": "几个人去？", "options": {"a": "独行", "b": "情侣", "c": "家庭/朋友"}},
    {"q": "什么时候去？", "options": {"a": "最近就去", "b": "计划中"}},
]

def recommend_destination(answers: dict) -> str:
    """根据5个答案推荐目的地"""
    prefs = []
    if answers.get("q2") == "a":
        prefs.extend(["成都", "广州", "长沙", "重庆"])
    elif answers.get("q2") == "b":
        prefs.extend(["北京", "西安", "南京", "洛阳"])
    elif answers.get("q2") == "c":
        prefs.extend(["云南", "桂林", "张家界", "九寨沟"])
    else:
        prefs.extend(["上海", "深圳", "杭州", "成都"])
    
    if answers.get("q1") == "a":
        prefs = [c for c in prefs if c not in ["上海", "深圳", "重庆"]]
    if answers.get("q3") == "a":
        prefs = [c for c in prefs if c not in ["上海", "深圳", "杭州"]]
    if answers.get("q4") == "b":
        prefs = [c for c in prefs if c in ["成都", "大理", "丽江", "厦门", "杭州"]]
    
    return random.choice(prefs) if prefs else random.choice(["成都", "西安", "云南", "桂林"])

SOCIAL_TEMPLATES = {
    "instagram": [
        "📸 {city}的{place}，{adj}到词穷。{emoji}\n\n#travel #china #{city_tag}",
        "{city}的{adj}，都在这一口{food}里了。{emoji}\n\n#foodie #{city_tag}",
    ],
    "wechat": [
        "在{city}的第{days}天，{feeling}。\n{tip}\n📍{place}",
        "来{city}一定要{action}！{reason}🥹\n#旅行日记",
    ],
    "xiaohongshu": [
        "{city}三天两晚攻略❗{highlights}\n{emoji} 人均仅{price}元\n✨ 详细路线看👇",
    ]
}

def generate_caption(platform: str, city: str, place: str = "",
                      food: str = "", days: int = 3, price: int = 2000) -> str:
    """生成朋友圈/社交文案"""
    import random
    adj_map = {"成都": "巴适", "重庆": "魔幻", "西安": "震撼", "北京": "大气",
               "上海": "摩登", "云南": "治愈", "桂林": "绝美", "广州": "好食"}
    adj = adj_map.get(city, "好看")
    feeling = random.choice(["慢下来才发现好多美好", "又解锁一个新城市", "快乐就这么简单"])
    tip = random.choice(["推荐早上来没人", "本地人带路才找到的", "一定要提前预约"])
    action = random.choice(["吃一顿地道早餐", "去这个机位拍照", "感受当地人的生活"])
    reason = random.choice(["太绝了", "谁懂啊", "真的好爱"])
    highlights = random.choice(["景点+美食全攻略", "小众路线推荐", "拍照机位分享"])
    emoji = random.choice(["✨", "🥹", "🔥", "💯", "😭"])
    city_tag = city.lower()
    
    tmpl = random.choice(SOCIAL_TEMPLATES.get(platform, SOCIAL_TEMPLATES["wechat"]))
    return tmpl.format(city=city, place=place, adj=adj, emoji=emoji, 
                       city_tag=city_tag, days=days, food=food or "当地美食",
                       feeling=feeling, tip=tip, action=action, reason=reason,
                       highlights=highlights, price=price)
