#!/bin/bash
# Generate missing city images using Seedream 5.0
set -euo pipefail

IMG_DIR="/home/ubuntu/projects/vise-panda-2/static/img"
API_KEY="$VOLCENGINE_API_KEY"
API_URL="https://ark.cn-beijing.volces.com/api/v3/images/generations"

declare -A CITIES
CITIES[guiyang]="Guiyang China, city skyline with karst mountains, modern cityscape surrounded by green hills, sunny day"
CITIES[hohhot]="Hohhot Inner Mongolia, traditional Mongolian architecture with modern city skyline, blue sky, grassland landscape"
CITIES[huangshan]="Huangshan Yellow Mountains China, iconic granite peaks emerging from sea of clouds, pine trees, misty sunrise"
CITIES[jiuzhaigou]="Jiuzhaigou National Park China, turquoise blue lakes, colorful autumn forest, waterfalls, snow-capped mountains"
CITIES[lanzhou]="Lanzhou China, Yellow River city view, Zhongshan Bridge, riverside skyline with hills, sunny day"
CITIES[macau]="Macau China, skyline with Macau Tower and historic Portuguese buildings, modern casinos, night harbor view"
CITIES[nanchang]="Nanchang China, Tengwang Pavilion along Gan River, modern city skyline, blue sky"
CITIES[xining]="Xining Qinghai China, Qinghai-Tibet plateau city, traditional Tibetan architecture, clear blue sky, mountain backdrop"
CITIES[yunnan]="Yunnan China, Yuanyang rice terraces landscape, colorful layered fields, misty morning light"
CITIES[zhangjiajie]="Zhangjiajie China, Avatar Hallelujah Mountains, towering quartzite sandstone pillars rising above cloud forest"

for city in "${!CITIES[@]}"; do
    prompt="${CITIES[$city]}"
    outfile="${IMG_DIR}/city-${city}.jpg"
    
    echo "=== Generating $city ==="
    
    response=$(curl -s --max-time 120 -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "{
            \"model\": \"doubao-seedream-5-0-260128\",
            \"prompt\": \"${prompt}\",
            \"n\": 1,
            \"size\": \"1920x1920\"
        }")
    
    url=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['url'])" 2>/dev/null || echo "ERROR")
    
    if [ "$url" = "ERROR" ]; then
        echo "  FAILED: $(echo $response | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('message','unknown'))" 2>/dev/null)"
        continue
    fi
    
    echo "  URL: $url"
    curl -s -o "$outfile" --max-time 60 "$url"
    size=$(stat -c%s "$outfile" 2>/dev/null || stat -f%z "$outfile" 2>/dev/null)
    echo "  Saved: city-${city}.jpg ($size bytes)"
    
    # Rate limit: wait 5 seconds between requests
    sleep 5
done

echo "=== ALL DONE ==="
ls -lh "${IMG_DIR}"/city-*.jpg | wc -l
