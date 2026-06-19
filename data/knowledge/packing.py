"""Smart Packing Lists — by season, scenario, and trip type"""

PACKING = {
    "essentials": {
        "title": "📄 Essential Documents (必备证件)",
        "items": [
            ("护照 (原件+复印件)", "Passport (original + photocopy)", True),
            ("签证 (打印版)", "Visa (printed copy)", True),
            ("酒店预订确认单", "Hotel booking confirmations", True),
            ("机票/火车票电子票", "Flight/train e-tickets", True),
            ("旅行保险单", "Travel insurance policy", False),
            ("护照照片 (2张备用)", "Passport photos (2 spare)", False),
            ("国际驾照翻译件", "International Driving Permit", False),
        ]
    },
    "spring": {
        "title": "🌸 Spring (Mar–May) (春季3-5月)",
        "items": [
            ("薄外套/风衣", "Light jacket / trench coat", True),
            ("长袖T恤+牛仔裤", "Long-sleeve shirts + jeans", True),
            ("舒适运动鞋", "Comfortable walking shoes", True),
            ("雨伞/折叠雨衣", "Umbrella / packable raincoat", True),
            ("薄围巾 (防早晚凉)", "Light scarf (for cool mornings/evenings)", False),
            ("花粉过敏药", "Allergy medication (pollen)", False),
        ]
    },
    "summer": {
        "title": "☀️ Summer (Jun–Aug) (夏季6-8月)",
        "items": [
            ("短袖T恤 (多带几件)", "T-shirts (pack extra — you'll sweat through them)", True),
            ("薄长裤/短裤", "Light pants / shorts", True),
            ("防晒霜 SPF50+", "Sunscreen SPF50+", True),
            ("遮阳帽+太阳镜", "Sun hat + sunglasses", True),
            ("便携小风扇", "Portable mini fan", False),
            ("防蚊液", "Mosquito repellent", True),
            ("速干毛巾", "Quick-dry towel", False),
            ("水壶 (保持补水)", "Reusable water bottle", False),
        ]
    },
    "autumn": {
        "title": "🍂 Autumn (Sep–Nov) (秋季9-11月)",
        "items": [
            ("薄毛衣/卫衣", "Light sweater / hoodie", True),
            ("夹克/冲锋衣", "Jacket / windbreaker", True),
            ("长裤+牛仔裤", "Long pants + jeans", True),
            ("舒适徒步鞋", "Comfortable walking/hiking shoes", True),
            ("围巾", "Scarf", False),
            ("保湿护肤品", "Moisturizer (air gets dry)", False),
        ]
    },
    "winter": {
        "title": "❄️ Winter (Dec–Feb) (冬季12-2月)",
        "items": [
            ("羽绒服/厚大衣", "Down jacket / heavy coat", True),
            ("保暖内衣 (打底)", "Thermal underwear (base layer)", True),
            ("厚毛衣/羊毛衫", "Thick sweater / wool sweater", True),
            ("手套+帽子+围巾", "Gloves + hat + scarf", True),
            ("保暖靴/防滑鞋", "Warm boots / non-slip shoes", True),
            ("暖宝宝贴", "Hand warmers / heat packs", False),
            ("润唇膏+护手霜", "Lip balm + hand cream", True),
            ("保温杯", "Thermos / insulated bottle", False),
        ]
    },
    "beach": {
        "title": "🏖️ Beach Vacation (海边度假)",
        "items": [
            ("泳衣/泳裤", "Swimsuit / trunks", True),
            ("沙滩拖鞋", "Flip-flops / sandals", True),
            ("防晒霜 (防水型)", "Water-resistant sunscreen", True),
            ("防水手机袋", "Waterproof phone pouch", False),
            ("沙滩巾", "Beach towel", False),
            ("墨镜+遮阳帽", "Sunglasses + sun hat", True),
            ("防水包", "Waterproof bag", False),
        ]
    },
    "hiking": {
        "title": "⛰️ Hiking / Mountain Trekking (户外徒步/登山)",
        "items": [
            ("登山鞋 (防滑防水)", "Hiking boots (waterproof, grippy)", True),
            ("冲锋衣/防风外套", "Waterproof jacket / shell", True),
            ("速干衣裤", "Quick-dry shirt + pants", True),
            ("登山杖", "Trekking poles", False),
            ("头灯/手电筒", "Headlamp / flashlight", False),
            ("急救包", "First aid kit", True),
            ("高热量零食 (能量棒)", "High-energy snacks (protein bars)", True),
            ("水袋/大容量水壶", "Hydration pack / large water bottle", True),
        ]
    },
    "business": {
        "title": "💼 Business Travel (商务出行)",
        "items": [
            ("正装/西装 (一套)", "Business suit (one set)", True),
            ("皮鞋", "Formal shoes", True),
            ("熨烫便携器", "Portable steamer/iron", False),
            ("名片 (中英文)", "Business cards (Chinese + English)", False),
            ("笔记本电脑+充电器", "Laptop + charger", True),
            ("转换插头 (中国标准)", "Travel adapter (China: Type A/I, 220V)", True),
            ("备用USB线", "Spare USB cables", False),
        ]
    },
    "tech": {
        "title": "📱 Tech & Electronics (电子产品)",
        "items": [
            ("手机+充电器+数据线", "Phone + charger + cable", True),
            ("移动电源/充电宝(≤20000mAh)", "Power bank (≤20000mAh — flight safe)", True),
            ("转换插头 (中国用)", "Travel adapter for China", True),
            ("耳机/耳塞", "Headphones / earplugs", False),
            ("相机", "Camera (optional)", False),
            ("VPN已安装 (非常重要!)", "VPN installed on phone (essential!)", True),
            ("手机SIM卡槽针", "SIM ejector tool", False),
        ]
    },
    "health": {
        "title": "💊 Medicine / Health (药品/健康)",
        "items": [
            ("常用药: 感冒药+止泻药+止痛药", "Basic meds: cold meds, anti-diarrhea, painkillers", True),
            ("创可贴+消毒棉片", "Band-aids + antiseptic wipes", True),
            ("晕车药 (如需)", "Motion sickness meds (if needed)", False),
            ("个人处方药 (带足量)", "Personal prescription meds (bring enough)", True),
            ("口罩 (备几个)", "Face masks (a few spares)", False),
            ("体温计", "Thermometer", False),
            ("维生素C/泡腾片", "Vitamin C / effervescent tablets", False),
        ]
    },
}


def get_list_for_season(season: str) -> dict | None:
    """Get packing list by season key"""
    return PACKING.get(season)


def get_all_seasons() -> list[str]:
    """Return all available packing list categories"""
    return list(PACKING.keys())


def format_for_prompt() -> str:
    """Compact format for LLM system prompt"""
    lines = [
        "## 智能打包清单 (Smart Packing Lists)",
        "根据目的地+季节+天数+场景生成个性化推荐：",
    ]
    for k, v in PACKING.items():
        essential = sum(1 for i in v["items"] if i[2])
        total = len(v["items"])
        lines.append(f"- {v['title']} ({essential}/{total}建议必带)")
    lines.append("\n用户询问时，结合场景(商务/海滩/徒步等)和季节推荐打包清单。")
    return "\n".join(lines)
