"""Language Emergency Cards — Chinese-English phrase book for travelers"""

PHRASE_CATEGORIES = {
    "taxi": {
        "title_zh": "🚕 Taxi / Ride-hailing (打车)",
        "title_en": "Taxi / Ride-hailing",
        "icon": "🚕",
        "phrases": [
            ("请带我去这个地址", "qǐng dài wǒ qù zhè ge dì zhǐ", "Please take me to this address"),
            ("打表吗？", "dǎ biǎo ma?", "Do you use the meter?"),
            ("前面路口停就可以了", "qián miàn lù kǒu tíng jiù kě yǐ le", "You can stop at the intersection ahead"),
            ("我要去机场/火车站", "wǒ yào qù jī chǎng / huǒ chē zhàn", "I need to go to the airport / train station"),
            ("多少钱？", "duō shǎo qián?", "How much is it?"),
            ("可以用支付宝/微信支付吗？", "kě yǐ yòng zhī fù bǎo / wēi xìn zhī fù ma?", "Can I pay with Alipay / WeChat Pay?"),
            ("请开一下后备箱", "qǐng kāi yī xià hòu bèi xiāng", "Please open the trunk"),
            ("我赶时间，能开快一点吗？", "wǒ gǎn shí jiān, néng kāi kuài yī diǎn ma?", "I'm in a hurry, can you drive faster?"),
        ]
    },
    "dining": {
        "title_zh": "🍜 Ordering Food (点餐)",
        "title_en": "Ordering Food",
        "icon": "🍜",
        "phrases": [
            ("有英文菜单吗？", "yǒu yīng wén cài dān ma?", "Do you have an English menu?"),
            ("有什么推荐的？", "yǒu shén me tuī jiàn de?", "What do you recommend?"),
            ("我不要辣的", "wǒ bù yào là de", "I don't want it spicy"),
            ("我对花生/海鲜过敏", "wǒ duì huā shēng / hǎi xiān guò mǐn", "I'm allergic to peanuts / seafood"),
            ("请给我一双筷子", "qǐng gěi wǒ yī shuāng kuài zi", "Please give me a pair of chopsticks"),
            ("买单 / 结账", "mǎi dān / jié zhàng", "Check, please"),
            ("打包", "dǎ bāo", "Takeaway / To go"),
            ("分开付", "fēn kāi fù", "Separate checks, please"),
        ]
    },
    "directions": {
        "title_zh": "🗺️ Asking Directions (问路)",
        "title_en": "Asking Directions",
        "icon": "🗺️",
        "phrases": [
            ("请问这里怎么走？", "qǐng wèn zhè lǐ zěn me zǒu?", "How do I get here?"),
            ("附近有地铁站吗？", "fù jìn yǒu dì tiě zhàn ma?", "Is there a subway station nearby?"),
            ("步行过去要多久？", "bù xíng guò qù yào duō jiǔ?", "How long does it take to walk there?"),
            ("坐几路公交？", "zuò jǐ lù gōng jiāo?", "Which bus number should I take?"),
            ("我能用导航吗？", "wǒ néng yòng dǎo háng ma?", "Can I use navigation here? (Google Maps is blocked in China)"),
            ("请在地图上指给我看", "qǐng zài dì tú shàng zhǐ gěi wǒ kàn", "Please show me on the map"),
            ("直走然后左转", "zhí zǒu rán hòu zuǒ zhuǎn", "Go straight then turn left"),
            ("在这个路口右转", "zài zhè ge lù kǒu yòu zhuǎn", "Turn right at this intersection"),
        ]
    },
    "medical": {
        "title_zh": "🏥 Medical / Emergency (就医)",
        "title_en": "Medical / Emergency",
        "icon": "🏥",
        "phrases": [
            ("我不舒服，需要看医生", "wǒ bù shū fu, xū yào kàn yī shēng", "I feel unwell, I need to see a doctor"),
            ("最近的医院在哪里？", "zuì jìn de yī yuàn zài nǎ lǐ?", "Where is the nearest hospital?"),
            ("我发烧了", "wǒ fā shāo le", "I have a fever"),
            ("我肚子疼", "wǒ dù zi téng", "I have a stomachache"),
            ("我有保险", "wǒ yǒu bǎo xiǎn", "I have insurance"),
            ("请帮我叫救护车", "qǐng bāng wǒ jiào jiù hù chē", "Please call an ambulance"),
            ("我需要翻译", "wǒ xū yào fān yì", "I need an interpreter"),
            ("我受伤了", "wǒ shòu shāng le", "I'm injured"),
        ]
    },
    "shopping": {
        "title_zh": "🛍️ Shopping (购物)",
        "title_en": "Shopping",
        "icon": "🛍️",
        "phrases": [
            ("这个多少钱？", "zhè ge duō shǎo qián?", "How much is this?"),
            ("可以便宜一点吗？", "kě yǐ pián yí yī diǎn ma?", "Can you make it cheaper?"),
            ("可以试穿吗？", "kě yǐ shì chuān ma?", "Can I try it on?"),
            ("有更大/小号的吗？", "yǒu gèng dà / xiǎo hào de ma?", "Do you have a larger / smaller size?"),
            ("能退税吗？", "néng tuì shuì ma?", "Can I get a tax refund?"),
            ("我可以用信用卡吗？", "wǒ kě yǐ yòng xìn yòng kǎ ma?", "Can I use a credit card?"),
            ("我要这个", "wǒ yào zhè ge", "I'll take this one"),
            ("能帮忙包装成礼物吗？", "néng bāng máng bāo zhuāng chéng lǐ wù ma?", "Can you gift wrap it?"),
        ]
    },
    "hotel": {
        "title_zh": "🏨 Hotel (酒店)",
        "title_en": "Hotel",
        "icon": "🏨",
        "phrases": [
            ("我预订了房间", "wǒ yù dìng le fáng jiān", "I have a reservation"),
            ("办理入住", "bàn lǐ rù zhù", "Check-in, please"),
            ("有Wi-Fi吗？密码是多少？", "yǒu wi-fi ma? mì mǎ shì duō shǎo?", "Is there Wi-Fi? What's the password?"),
            ("早餐几点开始？", "zǎo cān jǐ diǎn kāi shǐ?", "What time does breakfast start?"),
            ("可以延迟退房吗？", "kě yǐ yán chí tuì fáng ma?", "Can I do a late checkout?"),
            ("房间没有热水", "fáng jiān méi yǒu rè shuǐ", "There's no hot water in the room"),
            ("能帮我叫出租车吗？", "néng bāng wǒ jiào chū zū chē ma?", "Can you call a taxi for me?"),
            ("我需要多一条毛巾", "wǒ xū yào duō yī tiáo máo jīn", "I need one more towel"),
        ]
    },
    "emergency": {
        "title_zh": "🆘 Emergency Help (紧急求助)",
        "title_en": "Emergency Help",
        "icon": "🆘",
        "phrases": [
            ("救命！", "jiù mìng!", "Help!"),
            ("报警电话是多少？", "bào jǐng diàn huà shì duō shǎo?", "What's the police number?"),
            ("拨打110 / 119 / 120", "bō dǎ yī yī líng / yī yāo jiǔ / yī èr líng", "Call 110 (police) / 119 (fire) / 120 (ambulance)"),
            ("我的护照丢了", "wǒ de hù zhào diū le", "I lost my passport"),
            ("我迷路了", "wǒ mí lù le", "I'm lost"),
            ("请帮我联系我的大使馆", "qǐng bāng wǒ lián xì wǒ de dà shǐ guǎn", "Please contact my embassy"),
            ("我被偷了", "wǒ bèi tōu le", "I've been robbed"),
            ("我遇到了麻烦", "wǒ yù dào le má fan", "I'm in trouble"),
        ]
    },
    "transit": {
        "title_zh": "🚇 Public Transit (公共交通)",
        "title_en": "Public Transit",
        "icon": "🚇",
        "phrases": [
            ("地铁票怎么买？", "dì tiě piào zěn me mǎi?", "How do I buy a subway ticket?"),
            ("到...多少钱？", "dào ... duō shǎo qián?", "How much to go to ...?"),
            ("在哪一站下车？", "zài nǎ yī zhàn xià chē?", "Which stop should I get off at?"),
            ("换乘站在哪里？", "huàn chéng zhàn zài nǎ lǐ?", "Where is the transfer station?"),
            ("末班车是几点？", "mò bān chē shì jǐ diǎn?", "What time is the last train?"),
            ("这个座位有人吗？", "zhè ge zuò wèi yǒu rén ma?", "Is this seat taken?"),
            ("可以用交通卡吗？", "kě yǐ yòng jiāo tōng kǎ ma?", "Can I use a transit card?"),
            ("我要充值交通卡", "wǒ yào chōng zhí jiāo tōng kǎ", "I need to top up my transit card"),
        ]
    },
}


def get_category(cat: str) -> dict | None:
    """Get a single category by key"""
    return PHRASE_CATEGORIES.get(cat)


def get_all_categories() -> dict:
    """Get all categories (overview only, no phrases for brevity)"""
    return {
        k: {
            "title_zh": v["title_zh"],
            "title_en": v["title_en"],
            "icon": v["icon"],
            "count": len(v["phrases"]),
        }
        for k, v in PHRASE_CATEGORIES.items()
    }


def get_category_list() -> list[dict]:
    """Return categories as a list"""
    cats = []
    for k, v in PHRASE_CATEGORIES.items():
        cats.append({
            "id": k,
            "title_zh": v["title_zh"],
            "title_en": v["title_en"],
            "icon": v["icon"],
            "count": len(v["phrases"]),
        })
    return cats


def format_for_prompt() -> str:
    """Compact format for LLM system prompt"""
    lines = [
        "## Language Emergency Cards (语言急救卡)",
        "You can generate Chinese-English phrase cards for foreign travelers in these scenarios:",
    ]
    for k, v in PHRASE_CATEGORIES.items():
        lines.append(f"- {v['icon']} **{k}**: {v['title_en']} / {v['title_zh']} ({len(v['phrases'])} phrases)")
    lines.append("\n用户请求时，用格式化卡片展示中文+拼音+英文对照，方便截图保存。")
    return "\n".join(lines)
