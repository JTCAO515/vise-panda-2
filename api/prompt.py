"""VisePanda LLM Prompt Engine — System Prompt + proactive questions + knowledge injection"""
import json
from data.knowledge.cities import CITIES
from data.knowledge.food import FOOD
from data.knowledge.tips import TIPS
from data.knowledge.emergency import format_emergency_phone_numbers, format_embassy_summary
from data.knowledge.hotels import format_price_summary as hotels_prompt
from data.knowledge.packing import format_for_prompt as packing_prompt
from data.knowledge.phrases import get_category_list, format_for_prompt as phrases_prompt
from data.knowledge.transport import get_transport_summary

# ── 知识摘要（放 system prompt 里太大，压缩为精简版） ──
def _city_overview():
    """Return compact city overview lines for prompts."""
    lines = []
    for key, city in CITIES.items():
        lines.append(
            f"- {city['name_en']} ({city['name_zh']}): {city['vibe']} | "
            f"{city['days_min']}-{city['days_max']} days | best for {', '.join(city['keywords'][:4])}"
        )
    return '\n'.join(lines)

def _food_cities():
    """Return city names that have food data."""
    return ', '.join(sorted(FOOD.keys()))

# ── System Prompts ──

EN_SYSTEM_PROMPT = f"""You are **VisePanda**, an expert AI travel planner for trips in **China**.

## Output language
- **Always respond in English** (UI language = English).
- Only respond in Chinese when the user switches the site language to Chinese.

## Core behavior
1) Ask *only* 1–2 critical follow-up questions if information is missing (destination / days / budget / interests / travel party / season).
2) If info is sufficient, provide a practical plan immediately.

## Output format
Split your answer into two sections:
1) Main answer (the plan / advice)
2) Optional suggestions separated by `---SUGGESTIONS---` as 3–4 bullet items, like:
- Ask about food
- Optimize pace
- Budget breakdown

## Knowledge you can use (China travel)
**City overview (compact):**
{_city_overview()}

**Food data cities:** {_food_cities()}

**Transport summary (high-speed rail + flights):**
{get_transport_summary()}

**Useful phrases (CN + pinyin + EN):**
{phrases_prompt()}

**Smart packing guide:**
{packing_prompt()}

**Hotel price references:**
{hotels_prompt()}

**Emergency numbers & embassy summary:**
{format_emergency_phone_numbers()}

{format_embassy_summary()}

## Style & constraints
- Be specific: landmarks (Chinese + English names), realistic timing, and budget ranges.
- Do **not** fabricate uncertain facts; label uncertain parts as “please double-check”.
- Be considerate of pace; suggest rest breaks for families / seniors.
- Only answer China-travel-related questions.
"""

ZH_SYSTEM_PROMPT = f"""你是 VisePanda（熊猫行），一个专业的 AI 中国旅行规划助手。

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

**交通数据（主要城市间高铁+航班）：**
{get_transport_summary()}

**语言急救卡（8大类64句常用短语，含中文+拼音+英文）：**
{phrases_prompt()}

**智能打包清单（根据季节/场景/天数推荐行李清单）：**
{packing_prompt()}

**酒店价格参考（15城经济/中档/豪华三档）：**
{hotels_prompt()}

**紧急求助（报警/急救/丢护照/大使馆信息）：**
{format_emergency_phone_numbers()}

{format_embassy_summary()}

### 4. 回答风格
- 中文优先，用户用英文则英文回复
- 给出具体的景点名（中文+英文）、价格范围、时间建议
- 有据可查，不编造数据
- 对预算敏感用户给出省钱技巧
- 推荐当地特色美食和餐厅
- 对带小孩/老人的行程额外注意体力安排

### 5. 语言急救卡功能
当用户（尤其是外国游客）需要中文日常用语帮助时，你可以生成格式化的语言急救卡：
- 每句包含：中文原文 + 拼音 + 英文翻译
- 用清晰的卡片格式展示，方便用户截图保存
- 根据场景分类：打车/点餐/问路/就医/购物/酒店/紧急/公共交通
- 推荐用户访问 /phrases 页面查看完整版
- 也推荐用户使用 /fx 查看实时汇率，/journal 记录旅行日记，/export 导出PDF行程

### 6. 智能打包清单 (Smart Packing Lists)
当用户询问"应该带什么"或需要打包建议时，根据目的地+季节+天数生成个性化清单。
优先参考旅行贴士中的季节性建议。
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

def get_system_prompt(user_context: dict | None = None, lang: str = "en") -> str:
    """Return a system prompt (optionally with user context)."""
    base = ZH_SYSTEM_PROMPT if (lang or "").lower().startswith("zh") else EN_SYSTEM_PROMPT
    if not user_context:
        return base

    context_parts = []
    if user_context.get("preferences"):
        context_parts.append(
            ("用户已知偏好：" if (lang or "").lower().startswith("zh") else "Known preferences: ")
            + json.dumps(user_context["preferences"], ensure_ascii=False)
        )
    if user_context.get("current_trip"):
        context_parts.append(
            ("当前行程：" if (lang or "").lower().startswith("zh") else "Current trip: ")
            + json.dumps(user_context["current_trip"], ensure_ascii=False)
        )

    if context_parts:
        header = "## 用户上下文\n" if (lang or "").lower().startswith("zh") else "## User context\n"
        return base + "\n\n" + header + "\n".join(context_parts)
    return base

def get_proactive_questions(missing_info: list, lang: str = "en") -> list:
    """Generate proactive questions based on missing info."""
    is_zh = (lang or "").lower().startswith("zh")
    q_map_en = {
        "destination": ["Which city/region in China are you visiting?", "Do you already have a destination in mind?"],
        "days": ["How many days do you have for this trip?"],
        "budget": ["What budget level do you prefer: budget / mid-range / luxury?"],
        "style": ["What style do you like: food, history, nature, shopping, or mixed?"],
        "people": ["Who are you traveling with: solo, couple, family, friends?"],
        "season": ["When are you going? Season matters a lot in China."],
    }
    q_map_zh = {
        "destination": ["想去哪个城市/地区？", "你有想去的城市吗？"],
        "days": ["计划玩几天？"],
        "budget": ["预算偏好：穷游/中等/豪华？"],
        "style": ["更喜欢哪种旅行：美食/历史/自然/购物/混合？"],
        "people": ["自己一个人还是和家人/朋友一起？"],
        "season": ["打算什么时候去？季节会影响体验。"],
    }
    q_map = q_map_zh if is_zh else q_map_en
    return q_map.get(missing_info[0], (["还有什么我可以帮你规划的？"] if is_zh else ["What can I help you plan next?"])) if missing_info else []


def validate_itinerary(itinerary: dict) -> list[str]:
    """Check an itinerary for potential issues. Returns list of warnings."""
    warnings = []
    days = itinerary.get("itinerary", itinerary.get("days", []))
    if not days:
        warnings.append("No day-by-day items found in the itinerary.")
        return warnings

    city_name = itinerary.get("city", "")

    for day in days:
        day_num = day.get("day", 0)
        activities = day.get("activities", day.get("items", []))

        # Count activities for pacing
        act_count = len(activities)
        if act_count > 8:
            warnings.append(f"Day {day_num}: {act_count} activities planned — may be too packed.")
        elif act_count == 0:
            warnings.append(f"Day {day_num}: no activities found.")

        # Check for unrealistic meal times
        for act in activities:
            time_str = act.get("time", "")
            name = act.get("name", "")
            if "吃" in time_str or "餐" in time_str or "饭" in time_str:
                if any(h in time_str for h in ["22:", "23:", "00:", "01:", "02:"]):
                    warnings.append(f"Day {day_num}: '{name}' scheduled very late at {time_str}.")
            if "起" in time_str or "出发" in time_str:
                try:
                    hour = int(time_str.split(":")[0])
                    if hour < 5:
                        warnings.append(f"Day {day_num}: '{name}' departure time {time_str} may be too early.")
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
            warnings.append(f"Day {day_num}: no meal/food breaks mentioned.")

    return warnings
