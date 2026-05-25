"""VisePanda LLM Prompt Engine — System Prompt + 主动提问 + 知识注入"""
import json
from data.knowledge.cities import CITIES
from data.knowledge.food import FOOD
from data.knowledge.tips import TIPS

# ── 知识摘要（放 system prompt 里太大，压缩为精简版） ──
def _city_overview():
    """返回城市名列表+关键词"""
    lines = []
    for key, city in CITIES.items():
        lines.append(f"- {city['name_zh']}({city['name_en']}): {city['vibe']} | {city['days_min']}-{city['days_max']}天 | 最佳{', '.join(city['keywords'][:4])}")
    return '\n'.join(lines)

def _food_cities():
    """返回有美食数据的城市"""
    return ', '.join(sorted(FOOD.keys()))

# ── System Prompt ──
SYSTEM_PROMPT = f"""你是 VisePanda (熊猫行)，一个专业的 AI 中国旅行规划助手。

## 核心行为

### 1. 先问清楚再规划
每次对话开始时，主动询问用户的偏好（如果用户没有一次性提供足够信息）：
- **目的地**：想去哪个城市/地区？
- **天数**：玩几天？
- **预算**：穷游/中等/豪华？
- **风格/兴趣**：美食/历史/自然/购物/休闲？
- **人群**：独行/情侣/家庭/朋友？
- **季节/时间**：什么时候去？

如果用户提供的信息足够详细，直接给出行程；如果信息不充分，先提问1-2个最关键的问题，不要一口气问所有问题。

### 2. 输出格式
回复分成两段：
- **第一段**：规划/建议的文字内容
- **第二段（可选）**：用划线列表提供3-4个"你可以接着问"的选项，以 ---SUGGESTIONS--- 分隔

### 3. 知识集成
你拥有以下中国旅行知识，每次回答时基于这些知识提供建议：

**城市概览：**
{_city_overview()}

**美食数据覆盖城市：** {_food_cities()}

**旅行贴士涵盖：** 交通 | 住宿 | 通讯(VPN) | 季节性建议 | 支付 | 安全 | 礼仪 | 语言 | 打包

### 4. 回答风格
- 中文优先，用户用英文则英文回复
- 给出具体的景点名（中文+英文）、价格范围、时间建议
- 有据可查，不编造数据
- 对预算敏感用户给出省钱技巧
- 推荐当地特色美食和餐厅
- 对带小孩/老人的行程额外注意体力安排
- 对短期行程（1-2天）建议紧凑但合理
- 对长期行程（5天+）留出休息日

### 5. 主动提问与深度探测
每次回答时，根据上下文主动提及以下事项之一：
- 签证要求（外籍用户）
- VPN/网络访问（外籍用户）
- 当地天气提醒
- 交通建议（高铁vs飞机）
- 支付方式提示
- 景区预约/排队信息
- 行李建议
- **外籍专享**：144h过境免签 / 海南免签 / SIM卡 / 支付宝绑定 / VPN

**渐进式探测**：不要一次性问完所有问题。先回答用户当前的问题，然后自然地问1个后续问题。
**反悔处理**：如果用户说「刚才说的不算」「换个想法」，回溯到修改点重新规划，而不是从头开始。
**隐性需求**：从用户语言推断（「便宜」→预算敏感，「慢」→休闲向，「带孩子」→亲子推荐，「拍照」→出片优先）

### 6. 行程迭代 & 对比
- **多轮修改**：如果用户说「太赶了」「换个酒店」「加一天」，只修改受影响的部分，不要重新生成全部
- **行程对比**：当用户说「给几个方案」时，同时给出 2-3 个不同风格（紧凑/休闲/深度/预算不同）
- **天气自适应**：如果知道用户出行时间，主动考虑该季节/月份的气候特点

### 7. 行程结构
当日程安排时，按天输出：
**Day 1: [主题]**
- 上午：[具体安排]
- 下午：[具体安排]
- 晚上：[具体安排]
- 🍽️ 推荐美食：[具体餐厅/菜品]
- 💰 当日预算：[估算]
- 📌 Tips：[小贴士]

## 限制
- 只回答中国旅行相关问题
- 不提供医疗/法律建议
- 不确定的信息标注"建议自行确认"
- 尊重用户的所有偏好设定"""

def get_system_prompt(user_context: dict = None) -> str:
    """返回 system prompt，可附加用户上下文"""
    if not user_context:
        return SYSTEM_PROMPT

    context_parts = []
    if user_context.get("preferences"):
        context_parts.append(f"用户已知偏好：{json.dumps(user_context['preferences'], ensure_ascii=False)}")
    if user_context.get("current_trip"):
        context_parts.append(f"当前行程：{json.dumps(user_context['current_trip'], ensure_ascii=False)}")

    if context_parts:
        return SYSTEM_PROMPT + "\n\n## 用户上下文\n" + "\n".join(context_parts)
    return SYSTEM_PROMPT

def get_proactive_questions(missing_info: list) -> list:
    """根据缺失信息生成主动提问"""
    q_map = {
        "destination": ["想去哪个城市？北京、上海、成都、西安还是其他地方？", "你有想去的城市吗？"],
        "days": ["计划玩几天？", "大概有多少天的时间？"],
        "budget": ["预算大概是多少？穷游（每天¥300以下）、中等（¥500-1000）、还是豪华（¥1500+）？"],
        "style": ["你喜欢什么类型的旅行？美食/历史/自然风光/都市购物/还是混合？"],
        "people": ["自己一个人还是和家人/朋友一起？"],
        "season": ["打算什么时候去？不同季节体验差别很大"],
    }
    return q_map.get(missing_info[0], ["还有什么我可以帮你规划的？"]) if missing_info else []


def validate_itinerary(itinerary: dict) -> list[str]:
    """Check an itinerary for potential issues. Returns list of warnings."""
    warnings = []
    days = itinerary.get("itinerary", itinerary.get("days", []))
    if not days:
        warnings.append("行程中没有日程信息")
        return warnings

    city_name = itinerary.get("city", "")

    for day in days:
        day_num = day.get("day", 0)
        activities = day.get("activities", day.get("items", []))

        # Count activities for pacing
        act_count = len(activities)
        if act_count > 8:
            warnings.append(f"Day {day_num}: 安排了 {act_count} 项活动，可能太紧凑")
        elif act_count == 0:
            warnings.append(f"Day {day_num}: 没有安排任何活动")

        # Check for unrealistic meal times
        for act in activities:
            time_str = act.get("time", "")
            name = act.get("name", "")
            if "吃" in time_str or "餐" in time_str or "饭" in time_str:
                if any(h in time_str for h in ["22:", "23:", "00:", "01:", "02:"]):
                    warnings.append(f"Day {day_num}: '{name}' 安排在深夜 {time_str}，可能不合理")
            if "起" in time_str or "出发" in time_str:
                try:
                    hour = int(time_str.split(":")[0])
                    if hour < 5:
                        warnings.append(f"Day {day_num}: '{name}' 出发时间 {time_str} 过早")
                except (ValueError, IndexError):
                    pass

    # Check if restaurants are mentioned but no meal breaks
    food_keywords = ["餐厅", "美食", "吃饭", "午餐", "晚餐", "早茶", "火锅", "烤"]
    for day in days:
        day_num = day.get("day", 0)
        activities = day.get("activities", day.get("items", []))
        all_text = " ".join(act.get("name", "") + act.get("time", "") for act in activities)
        has_food_mention = any(k in all_text for k in food_keywords)
        if not has_food_mention and activities:
            warnings.append(f"Day {day_num}: 未提及餐饮安排")

    return warnings
