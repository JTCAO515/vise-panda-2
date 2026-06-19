"""Emergency assistance info for foreign travelers in China"""

EMERGENCY = {
    "phone": {
        "police": {"number": "110", "description": "Police (报警) — theft, assault, robbery"},
        "fire": {"number": "119", "description": "Fire Department (火警)"},
        "ambulance": {"number": "120", "description": "Ambulance / Medical Emergency (急救)"},
        "traffic": {"number": "122", "description": "Traffic Accident (交通事故)"},
        "directory": {"number": "114", "description": "Directory Assistance (查号台)"},
    },
    "common_emergencies": {
        "lost_passport": {
            "title": "Lost Passport (护照丢失)",
            "steps": [
                "1. Report to the nearest police station immediately — get a Police Report Receipt (护照遗失报案回执)",
                "2. Go to your country's embassy/consulate to apply for an Emergency Travel Document (旅行证)",
                "3. Visit the Exit-Entry Administration Bureau to process visa re-issuance",
                "4. In urgent cases, the Emergency Travel Document can replace your passport for departure",
            ],
            "tip": "Keep a photocopy or photo of your passport on your phone — it helps with the re-issue process (建议随身带护照复印件或存在手机里)"
        },
        "medical_emergency": {
            "title": "Medical Emergency (医疗急救)",
            "steps": [
                "1. Dial 120 for an ambulance (free emergency number)",
                "2. Tell the operator your location and symptoms — simple English usually works",
                "3. Major Grade-A tertiary hospitals (三甲医院) have international departments / foreign patient clinics",
                "4. Take your passport to the ER — treatment first, payment later",
                "5. Contact your travel insurance company",
            ],
            "tip": "Beijing Union Hospital International (北京协和医院国际部), Shanghai Huashan Hospital (上海华山医院), and Guangzhou First Affiliated Hospital (广州中山一院) all offer English service"
        },
        "arrested": {
            "title": "Arrested / Detained (被拘留/被捕)",
            "steps": [
                "1. You have the right to contact your embassy — demand to notify them",
                "2. Do NOT sign any Chinese document you don't understand",
                "3. Request a translator — Chinese law requires one to be provided",
                "4. Contact your travel insurance and legal aid",
            ],
            "tip": "China visa rules: all foreigners in China must abide by Chinese law — 'I didn't know' is not an excuse (不知道法律不是借口)"
        },
        "natural_disaster": {
            "title": "Natural Disaster (自然灾害)",
            "steps": [
                "1. Follow instructions from local authorities and attraction staff",
                "2. Monitor China Earthquake Networks Center (中国地震台网) or local weather alerts",
                "3. Contact your embassy to register your location",
                "4. Keep your phone charged and use offline maps",
            ],
            "tip": "Japanese/Taiwanese travellers most commonly encounter typhoons/earthquakes in mainland China — check forecasts before travelling (日本/台湾游客来大陆最常遇到台风/地震)"
        }
    },
    "embassies": {
        "us": {
            "country": "United States (美国)",
            "phone": "010-8531-3000",
            "emergency": "010-8531-4000 (after hours)",
            "address": "No. 55 An Jia Lou Road, Chaoyang, Beijing (北京朝阳区安家楼路55号)",
            "website": "https://china.usembassy-china.org.cn",
            "cities": ["Beijing (北京)", "Shanghai (上海)", "Guangzhou (广州)", "Chengdu (成都)", "Shenyang (沈阳)", "Wuhan (武汉)"]
        },
        "uk": {
            "country": "United Kingdom (英国)",
            "phone": "010-8529-6600",
            "emergency": "010-8529-6600 (24h)",
            "address": "11 Guang Hua Lu, Jian Guo Men Wai, Chaoyang, Beijing (北京朝阳区建国门外光华路11号)",
            "website": "https://www.gov.uk/world/china",
            "cities": ["Beijing (北京)", "Shanghai (上海)", "Guangzhou (广州)", "Chongqing (重庆)", "Wuhan (武汉)"]
        },
        "au": {
            "country": "Australia (澳大利亚)",
            "phone": "010-5140-4111",
            "emergency": "010-5140-4248",
            "address": "Tayuan Diplomatic Office Building, Liangmahe Nan Lu, Chaoyang, Beijing (北京朝阳区亮马河南路14号塔园外交办公楼)",
            "website": "https://china.embassy.gov.au",
            "cities": ["Beijing (北京)", "Shanghai (上海)", "Guangzhou (广州)", "Chengdu (成都)"]
        },
        "ca": {
            "country": "Canada (加拿大)",
            "phone": "010-5139-4000",
            "emergency": "010-5139-4000",
            "address": "10 Liangma Qiao Road, Chaoyang, Beijing (北京朝阳区亮马桥路10号)",
            "website": "https://www.international.gc.ca/china",
            "cities": ["Beijing (北京)", "Shanghai (上海)", "Guangzhou (广州)", "Chongqing (重庆)"]
        },
        "sg": {
            "country": "Singapore (新加坡)",
            "phone": "010-6532-1115",
            "emergency": "010-6532-1115",
            "address": "42 Liangma Qiao Road, Chaoyang, Beijing (北京朝阳区亮马桥路42号)",
            "website": "https://www.mfa.gov.sg/beijing",
            "cities": ["Beijing (北京)", "Shanghai (上海)", "Guangzhou (广州)", "Xiamen (厦门)", "Chengdu (成都)"]
        },
        "de": {
            "country": "Germany (德国)",
            "phone": "010-8532-9000",
            "emergency": "010-8532-9000",
            "address": "52 Liangma Qiao Road, Chaoyang, Beijing (北京朝阳区亮马桥路52号)",
            "website": "https://china.diplo.de",
            "cities": ["Beijing (北京)", "Shanghai (上海)", "Guangzhou (广州)", "Chengdu (成都)"]
        },
        "fr": {
            "country": "France (法国)",
            "phone": "010-8531-2000",
            "emergency": "010-8531-2000",
            "address": "47 Liangma Qiao Road, Chaoyang, Beijing (北京朝阳区亮马桥路47号)",
            "website": "https://cn.ambafrance.org",
            "cities": ["Beijing (北京)", "Shanghai (上海)", "Guangzhou (广州)", "Chengdu (成都)"]
        },
        "jp": {
            "country": "Japan (日本)",
            "phone": "010-6532-2361",
            "emergency": "010-6532-2361",
            "address": "1 Liangma Qiao Road, Chaoyang, Beijing (北京朝阳区亮马桥路1号)",
            "website": "https://www.cn.emb-japan.go.jp",
            "cities": ["Beijing (北京)", "Shanghai (上海)", "Guangzhou (广州)", "Qingdao (青岛)", "Chongqing (重庆)", "Shenyang (沈阳)"]
        },
        "kr": {
            "country": "South Korea (韩国)",
            "phone": "010-8531-0700",
            "emergency": "010-8531-0700",
            "address": "26 Liangma Qiao Road, Chaoyang, Beijing (北京朝阳区亮马桥路26号)",
            "website": "https://overseas.mofa.go.kr/cn-zh",
            "cities": ["Beijing (北京)", "Shanghai (上海)", "Guangzhou (广州)", "Qingdao (青岛)", "Chengdu (成都)", "Xi'an (西安)"]
        },
    },
}


def format_emergency_phone_numbers() -> str:
    """Format emergency phone numbers for system prompt"""
    lines = ["## Emergency Numbers in China (紧急电话)", ""]
    for key, info in EMERGENCY["phone"].items():
        lines.append(f"- {info['number']}: {info['description']}")
    lines.append("")
    lines.append("All numbers are free to call. Operators may speak only Chinese, but saying 'Speak English please' usually connects you to an English-speaking operator. (所有电话免费拨打，接线员可能只说中文)")
    return "\n".join(lines)


def get_embassy(country_code: str) -> dict | None:
    """Get embassy info by country code (us, uk, au, etc.)"""
    return EMERGENCY["embassies"].get(country_code.lower())


def format_embassy_summary() -> str:
    """Compact embassy list for system prompt"""
    lines = ["## Major Embassies & Consulates in China (主要国家驻华大使馆/领事馆)"]
    for code, emb in EMERGENCY["embassies"].items():
        cities = "、".join(emb["cities"])
        lines.append(f"- {emb['country']}: {emb['phone']} ({cities})")
    return "\n".join(lines)
