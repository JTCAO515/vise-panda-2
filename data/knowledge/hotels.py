"""Hotel price ranges for major Chinese cities — budget, mid-range, and luxury"""

HOTELS = {
    "beijing": {
        "name_zh": "北京",
        "name_en": "Beijing",
        "budget": {"range": "¥150-350/晚", "desc": "青年旅舍/如家/汉庭", "areas": "前门/西单/东四"},
        "mid": {"range": "¥400-800/晚", "desc": "全季/亚朵/希尔顿花园", "areas": "王府井/三里屯/国贸"},
        "luxury": {"range": "¥1000-3000+/晚", "desc": "半岛/华尔道夫/四季/王府井文华东方", "areas": "王府井/国贸/金融街"},
        "tip": "建议住二环内（前门/王府井/东四），离景点近"
    },
    "shanghai": {
        "name_zh": "上海",
        "name_en": "Shanghai",
        "budget": {"range": "¥150-350/晚", "desc": "青年旅舍/汉庭/如家", "areas": "人民广场/南京东路"},
        "mid": {"range": "¥400-900/晚", "desc": "全季/亚朵/和颐", "areas": "外滩/静安寺/淮海路"},
        "luxury": {"range": "¥1200-4000+/晚", "desc": "和平饭店/半岛/浦东丽思卡尔顿/W酒店", "areas": "外滩/陆家嘴/静安"},
        "tip": "游客首选人民广场/南京东路；夜景控住外滩或陆家嘴"
    },
    "chengdu": {
        "name_zh": "成都",
        "name_en": "Chengdu",
        "budget": {"range": "¥120-280/晚", "desc": "青年旅舍/汉庭/如家", "areas": "春熙路/天府广场"},
        "mid": {"range": "¥300-600/晚", "desc": "全季/亚朵/锦江宾馆", "areas": "春熙路/宽窄巷子/武侯祠"},
        "luxury": {"range": "¥800-2500+/晚", "desc": "博舍/群光君悦/瑞吉/华尔道夫", "areas": "太古里/春熙路"},
        "tip": "住春熙路附近最方便，去景点都近。博舍是必住精品酒店"
    },
    "xian": {
        "name_zh": "西安",
        "name_en": "Xi'an",
        "budget": {"range": "¥100-250/晚", "desc": "青年旅舍/汉庭/如家", "areas": "钟楼/南门"},
        "mid": {"range": "¥250-600/晚", "desc": "全季/亚朵/美居", "areas": "钟楼/大雁塔/南门"},
        "luxury": {"range": "¥700-2000+/晚", "desc": "索菲特传奇/威斯汀/万豪行政公寓", "areas": "钟楼/大雁塔"},
        "tip": "住钟楼或南门城墙内，步行去回民街/城墙。大雁塔附近看喷泉方便"
    },
    "guangzhou": {
        "name_zh": "广州",
        "name_en": "Guangzhou",
        "budget": {"range": "¥120-280/晚", "desc": "汉庭/如家/7天", "areas": "天河/北京路"},
        "mid": {"range": "¥300-700/晚", "desc": "全季/亚朵/凯悦嘉轩", "areas": "天河/珠江新城"},
        "luxury": {"range": "¥900-3500+/晚", "desc": "四季/丽思卡尔顿/文华东方/瑰丽", "areas": "珠江新城/天河"},
        "tip": "珠江新城最方便，广州塔夜景一流"
    },
    "hangzhou": {
        "name_zh": "杭州",
        "name_en": "Hangzhou",
        "budget": {"range": "¥150-300/晚", "desc": "汉庭/如家/布丁", "areas": "西湖区/武林广场"},
        "mid": {"range": "¥350-800/晚", "desc": "全季/亚朵/隐居", "areas": "西湖边/灵隐"},
        "luxury": {"range": "¥1000-4000+/晚", "desc": "西子湖四季/安缦法云/悦榕庄/罗莱夏朵", "areas": "西湖景区/灵隐"},
        "tip": "西湖边的民宿比酒店更有味道；预算够安缦法云必体验"
    },
    "guilin": {
        "name_zh": "桂林",
        "name_en": "Guilin",
        "budget": {"range": "¥80-200/晚", "desc": "青年旅舍/汉庭/7天", "areas": "市中心/两江四湖"},
        "mid": {"range": "¥200-500/晚", "desc": "亚朵/维也纳/民宿", "areas": "市中心/漓江边"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "桂林香格里拉/漓江泊隐/悦榕庄(阳朔)", "areas": "漓江东岸/阳朔"},
        "tip": "阳朔比桂林市区更值得住；遇龙河边的民宿体验绝佳"
    },
    "shenzhen": {
        "name_zh": "深圳",
        "name_en": "Shenzhen",
        "budget": {"range": "¥120-280/晚", "desc": "汉庭/如家/7天", "areas": "罗湖/福田"},
        "mid": {"range": "¥300-700/晚", "desc": "全季/亚朵/万怡", "areas": "福田CBD/南山"},
        "luxury": {"range": "¥900-3000+/晚", "desc": "柏悦/瑞吉/莱佛士/君悦", "areas": "福田/南山/罗湖"},
        "tip": "福田CBD最中心；南山区靠近科技园+华侨城"
    },
    "chongqing": {
        "name_zh": "重庆",
        "name_en": "Chongqing",
        "budget": {"range": "¥100-250/晚", "desc": "汉庭/如家/7天", "areas": "解放碑/观音桥"},
        "mid": {"range": "¥250-550/晚", "desc": "全季/亚朵/维也纳", "areas": "解放碑/江北嘴"},
        "luxury": {"range": "¥700-2500+/晚", "desc": "威斯汀/来福士洲际/尼依格罗/NOVOTEL", "areas": "解放碑/江北嘴/南滨路"},
        "tip": "解放碑最中心；看夜景住南滨路或江北嘴"
    },
    "kunming": {
        "name_zh": "昆明",
        "name_en": "Kunming",
        "budget": {"range": "¥100-200/晚", "desc": "汉庭/如家/青旅", "areas": "翠湖/金马碧鸡坊"},
        "mid": {"range": "¥200-500/晚", "desc": "亚朵/全季/索菲特(老)", "areas": "翠湖/东风广场"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "昆明洲际/索菲特/君乐", "areas": "滇池/翠湖"},
        "tip": "住翠湖周边最有昆明味道，步行去讲武堂/云大"
    },
    "lijiang": {
        "name_zh": "丽江",
        "name_en": "Lijiang",
        "budget": {"range": "¥80-200/晚", "desc": "古城客栈/青旅", "areas": "古城内/束河古镇"},
        "mid": {"range": "¥200-600/晚", "desc": "精品民宿/古城客栈", "areas": "古城内/束河"},
        "luxury": {"range": "¥800-2500+/晚", "desc": "悦榕庄/安缦/古城精品酒店", "areas": "束河/古城边"},
        "tip": "住束河比大研古城安静；古城内石板路拖行李很痛苦，建议民宿老板来接"
    },
    "zhangjiajie": {
        "name_zh": "张家界",
        "name_en": "Zhangjiajie",
        "budget": {"range": "¥80-200/晚", "desc": "客栈/汉庭/7天", "areas": "武陵源/市区"},
        "mid": {"range": "¥200-500/晚", "desc": "亚朵/民宿/维也纳", "areas": "武陵源标志门"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "张家界禾田居/纳百利/皇冠假日", "areas": "武陵源"},
        "tip": "住武陵源标志门附近，进景区最方便，步行可达"
    },
    "suzhou": {
        "name_zh": "苏州",
        "name_en": "Suzhou",
        "budget": {"range": "¥120-250/晚", "desc": "汉庭/如家/7天", "areas": "观前街/火车站"},
        "mid": {"range": "¥250-600/晚", "desc": "亚朵/全季/花间堂", "areas": "观前街/平江路"},
        "luxury": {"range": "¥700-2000+/晚", "desc": "苏州金鸡湖凯宾斯基/柏悦/中茵皇冠", "areas": "金鸡湖/平江路"},
        "tip": "平江路/山塘街的民宿最有江南韵味；金鸡湖边适合商务"
    },
    "lhasa": {
        "name_zh": "拉萨",
        "name_en": "Lhasa",
        "budget": {"range": "¥100-250/晚", "desc": "客栈/青旅/汉庭", "areas": "八廓街/北京路"},
        "mid": {"range": "¥250-600/晚", "desc": "亚朵/客栈/瑞吉(基础)", "areas": "八廓街/布达拉宫"},
        "luxury": {"range": "¥800-2000+/晚", "desc": "拉萨瑞吉/拉萨圣地天堂洲际/拉萨香格里拉", "areas": "八廓街/布达拉宫"},
        "tip": "到拉萨第一晚别洗澡！住八廓街附近转经/去布宫都近。高原反应第一两天少活动"
    },
    "nanjing": {
        "name_zh": "南京",
        "name_en": "Nanjing",
        "budget": {"range": "¥120-250/晚", "desc": "汉庭/如家/7天", "areas": "新街口/夫子庙"},
        "mid": {"range": "¥250-600/晚", "desc": "亚朵/全季/金鹰", "areas": "新街口/玄武湖"},
        "luxury": {"range": "¥800-2500+/晚", "desc": "南京丽思卡尔顿/颐和公馆/威斯汀", "areas": "新街口/颐和路"},
        "tip": "新街口最中心；颐和路公馆区有民国风情住宿"
    },
    "harbin": {
        "name_zh": "哈尔滨",
        "name_en": "Harbin",
        "budget": {"range": "¥100-250/晚", "desc": "汉庭/如家/7天", "areas": "中央大街"},
        "mid": {"range": "¥250-600/晚", "desc": "亚朵/全季/万达嘉华", "areas": "中央大街/松北"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "哈尔滨万达文华/香格里拉/松北融创", "areas": "中央大街/松北"},
        "tip": "中央大街附近最方便，步行到索菲亚教堂/冰雪大世界有班车"
    },
    "wuhan": {
        "name_zh": "武汉", "name_en": "Wuhan",
        "budget": {"range": "¥120-250/晚", "desc": "汉庭/如家/7天", "areas": "江汉路/户部巷"},
        "mid": {"range": "¥250-600/晚", "desc": "亚朵/全季/万达嘉华", "areas": "江汉路/楚河汉街"},
        "luxury": {"range": "¥700-2000+/晚", "desc": "武汉万达瑞华/费尔蒙/泛海喜来登", "areas": "汉口江滩/武昌"},
        "tip": "江汉路最中心，武昌光谷适合学生党"
    },
    "qingdao": {
        "name_zh": "青岛", "name_en": "Qingdao",
        "budget": {"range": "¥100-250/晚", "desc": "汉庭/如家/7天", "areas": "火车站/台东"},
        "mid": {"range": "¥250-600/晚", "desc": "亚朵/全季/威斯汀(基础)", "areas": "五四广场/八大关"},
        "luxury": {"range": "¥800-2500+/晚", "desc": "青岛涵碧楼/海尔洲际/海景花园", "areas": "八大关/崂山"},
        "tip": "八大关附近的德式建筑民宿最有味道；盛夏旺季价格翻倍"
    },
    "xiamen": {
        "name_zh": "厦门", "name_en": "Xiamen",
        "budget": {"range": "¥100-250/晚", "desc": "客栈/汉庭/青旅", "areas": "中山路/曾厝垵"},
        "mid": {"range": "¥250-600/晚", "desc": "亚朵/民宿/全季", "areas": "鼓浪屿/环岛路"},
        "luxury": {"range": "¥700-2000+/晚", "desc": "厦门康莱德/七尚/海悦山庄", "areas": "鼓浪屿/环岛路"},
        "tip": "曾厝垵民宿性价比高；鼓浪屿住一晚很有味道但搬行李痛苦"
    },
    "sanya": {
        "name_zh": "三亚", "name_en": "Sanya",
        "budget": {"range": "¥150-350/晚", "desc": "民宿/汉庭/7天", "areas": "大东海/市区"},
        "mid": {"range": "¥350-800/晚", "desc": "亚朵/希尔顿花园/温德姆", "areas": "三亚湾/亚龙湾"},
        "luxury": {"range": "¥1000-4000+/晚", "desc": "三亚艾迪逊/嘉佩乐/柏悦/悦榕庄", "areas": "海棠湾/亚龙湾"},
        "tip": "亚龙湾沙质最好；海棠湾新酒店多；三亚湾看日落；冬季价格翻倍"
    },
    "changsha": {
        "name_zh": "长沙", "name_en": "Changsha",
        "budget": {"range": "¥100-250/晚", "desc": "汉庭/如家/7天", "areas": "五一广场/太平街"},
        "mid": {"range": "¥250-550/晚", "desc": "亚朵/全季/维也纳", "areas": "五一广场/IFS"},
        "luxury": {"range": "¥700-2000+/晚", "desc": "长沙尼依格罗/瑞吉/君悦/W酒店", "areas": "五一广场/湘江边"},
        "tip": "住五一广场最中心，坡子街/太平街步行可达"
    },
    "lasa": {
        "name_zh": "拉萨", "name_en": "Lhasa",
        "budget": {"range": "¥100-250/晚", "desc": "客栈/青旅/汉庭", "areas": "八廓街/北京路"},
        "mid": {"range": "¥250-600/晚", "desc": "亚朵/客栈/瑞吉(基础)", "areas": "八廓街/布达拉宫"},
        "luxury": {"range": "¥800-2000+/晚", "desc": "拉萨瑞吉/拉萨圣地天堂洲际/香格里拉", "areas": "八廓街/布达拉宫"},
        "tip": "到拉萨第一晚别洗澡！住八廓街附近转经/去布宫都近"
    },
    "fuzhou": {
        "name_zh": "福州", "name_en": "Fuzhou",
        "budget": {"range": "¥120-250/晚", "desc": "汉庭/如家/7天", "areas": "鼓楼/东街口"},
        "mid": {"range": "¥250-550/晚", "desc": "亚朵/全季/凯悦嘉轩", "areas": "鼓楼/三坊七巷"},
        "luxury": {"range": "¥700-1800+/晚", "desc": "福州世茂希尔顿/威斯汀/凯宾斯基", "areas": "鼓楼/闽江北岸"},
        "tip": "三坊七巷的民宿最有福州味道"
    },
    "dunhuang": {
        "name_zh": "敦煌", "name_en": "Dunhuang",
        "budget": {"range": "¥80-200/晚", "desc": "客栈/青旅/汉庭", "areas": "市区/鸣沙山"},
        "mid": {"range": "¥200-500/晚", "desc": "民宿/客栈/丝路怡苑", "areas": "市区"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "敦煌山庄/天河酒店/国际酒店", "areas": "鸣沙山/市区"},
        "tip": "鸣沙山附近的沙漠露营体验值得一试"
    },
    "lanzhou": {
        "name_zh": "兰州", "name_en": "Lanzhou",
        "budget": {"range": "¥100-200/晚", "desc": "汉庭/如家/7天", "areas": "西关/张掖路"},
        "mid": {"range": "¥200-500/晚", "desc": "亚朵/全季/皇冠假日(基础)", "areas": "西关/黄河边"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "兰州皇冠假日/长城建国饭店", "areas": "黄河风情线"},
        "tip": "住西关十字最方便，正宁路夜市步行可达"
    },
    "luoyang": {
        "name_zh": "洛阳", "name_en": "Luoyang",
        "budget": {"range": "¥80-200/晚", "desc": "汉庭/如家/青旅", "areas": "老城区/西工"},
        "mid": {"range": "¥200-500/晚", "desc": "亚朵/全季/牡丹城", "areas": "老城区/洛龙"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "洛阳华阳广场/钼都利豪/万豪", "areas": "洛龙/新区"},
        "tip": "龙门石窟建议住洛龙区；老城区吃水席方便"
    },
    "huangshan": {
        "name_zh": "黄山", "name_en": "Huangshan",
        "budget": {"range": "¥100-250/晚", "desc": "客栈/青旅/汉庭", "areas": "汤口镇/屯溪"},
        "mid": {"range": "¥250-600/晚", "desc": "民宿/亚朵/客栈", "areas": "汤口镇/宏村"},
        "luxury": {"range": "¥700-2000+/晚", "desc": "黄山悦榕庄/涵月楼/昱城皇冠", "areas": "宏村/屯溪"},
        "tip": "爬黄山住汤口镇；看徽派建筑住宏村民宿"
    },
    "guiyang": {
        "name_zh": "贵阳", "name_en": "Guiyang",
        "budget": {"range": "¥100-200/晚", "desc": "汉庭/如家/7天", "areas": "云岩/喷水池"},
        "mid": {"range": "¥200-500/晚", "desc": "亚朵/全季/维也纳", "areas": "云岩/甲秀楼"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "贵阳中天凯悦/索菲特/万丽", "areas": "观山湖/云岩"},
        "tip": "住云岩区或甲秀楼附近，二七路小吃街步行可达"
    },
    "nanchang": {
        "name_zh": "南昌", "name_en": "Nanchang",
        "budget": {"range": "¥80-200/晚", "desc": "汉庭/如家/7天", "areas": "红谷滩/八一广场"},
        "mid": {"range": "¥200-500/晚", "desc": "亚朵/全季/格兰云天", "areas": "红谷滩/滕王阁"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "南昌力高皇冠/前湖迎宾馆/喜来登", "areas": "红谷滩"},
        "tip": "红谷滩新区酒店新；老城区吃拌粉瓦罐汤"
    },
    "xining": {
        "name_zh": "西宁", "name_en": "Xining",
        "budget": {"range": "¥80-200/晚", "desc": "汉庭/如家/青旅", "areas": "城中区/莫家街"},
        "mid": {"range": "¥200-500/晚", "desc": "亚朵/全季/青海宾馆", "areas": "城中区/海湖"},
        "luxury": {"range": "¥600-1800+/晚", "desc": "西宁新华联索菲特/万达嘉华/希尔顿", "areas": "海湖新区"},
        "tip": "住城中区去莫家街方便；去青海湖建议提前一晚住西宁"
    },
    "hohhot": {
        "name_zh": "呼和浩特", "name_en": "Hohhot",
        "budget": {"range": "¥80-200/晚", "desc": "汉庭/如家/7天", "areas": "鼓楼/中山西路"},
        "mid": {"range": "¥200-500/晚", "desc": "亚朵/全季/香格里拉(基础)", "areas": "鼓楼/如意"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "呼和浩特香格里拉/喜来登/万豪", "areas": "如意/新城"},
        "tip": "住鼓楼附近吃蒙餐方便；去草原一般从呼市出发"
    },
    "dali": {
        "name_zh": "大理", "name_en": "Dali",
        "budget": {"range": "¥80-200/晚", "desc": "古城客栈/青旅", "areas": "古城内/才村"},
        "mid": {"range": "¥200-500/晚", "desc": "精品民宿/海景客栈", "areas": "古城/洱海边"},
        "luxury": {"range": "¥600-2000+/晚", "desc": "大理颐和耘熹/明月松间/海纳尔", "areas": "洱海/古城"},
        "tip": "住古城里热闹，住洱海边安静看日出"
    },
    "jiuzhaigou": {
        "name_zh": "九寨沟", "name_en": "Jiuzhaigou",
        "budget": {"range": "¥80-200/晚", "desc": "客栈/青旅/藏家乐", "areas": "沟口/漳扎镇"},
        "mid": {"range": "¥200-500/晚", "desc": "民宿/亚朵/客栈", "areas": "沟口"},
        "luxury": {"range": "¥600-1500+/晚", "desc": "九寨沟悦榕庄/天源豪生/希尔顿", "areas": "沟口"},
        "tip": "住沟口最方便，步行进景区；秋季房价翻倍"
    },
}


def format_price_summary() -> str:
    """Compact edition for LLM system prompt"""
    lines = ["## 酒店价格参考 (Hotel Price Guide)"]
    for key, city in HOTELS.items():
        lines.append(f"- {city['name_zh']}({city['name_en']}): 经济{city['budget']['range']} | 中档{city['mid']['range']} | 豪华{city['luxury']['range']}")
    return "\n".join(lines)


def get_city_hotel(city_key: str) -> dict | None:
    return HOTELS.get(city_key.lower())
