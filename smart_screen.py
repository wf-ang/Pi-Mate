import epd4in2
import time
import requests
import sxtwl
import json
import os
from PIL import Image, ImageDraw, ImageFont
import datetime

# 字体路径
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
# 缓存文件路径
STATE_FILE = "/tmp/smart_screen_state.json"

def load_state():
    """读取本地缓存名言"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"lines": [], "footer": "", "timestamp": 0}

def save_state(lines, footer, timestamp):
    """保存名言到本地缓存"""
    with open(STATE_FILE, "w") as f:
        json.dump({"lines": lines, "footer": footer, "timestamp": timestamp}, f)

def get_quote_that_fits(draw, font_quote, max_width=360, max_lines=4):
    """获取名言：带有严格的像素宽度测量和自动重试机制"""
    for attempt in range(1, 6): # 最多重试 5 次
        try:
            url = "https://v1.hitokoto.cn/?c=d&c=k&c=i"
            r = requests.get(url, timeout=5)
            data = r.json()
            
            quote = data.get('hitokoto', '')
            author = data.get('from_who')
            source = data.get('from')
            
            # 智能拼接 “作者 · 作品”
            if author and source and author != source:
                footer = f"—— {author} · {source}"
            elif author:
                footer = f"—— {author}"
            elif source:
                footer = f"—— {source}"
            else:
                footer = "—— 佚名"

            # 测量文字宽度并自动换行
            lines = []
            current_line = ""
            for char in quote:
                bbox = draw.textbbox((0, 0), current_line + char, font=font_quote)
                w = bbox[2] - bbox[0]
                if w <= max_width:
                    current_line += char
                else:
                    lines.append(current_line)
                    current_line = char
            if current_line:
                lines.append(current_line)
            
            # 判断行数是否符合要求
            if len(lines) <= max_lines:
                return lines, footer
            else:
                print(f"[重试机制] 第 {attempt} 次获取的名言过长 ({len(lines)}行)，正在重新请求...")
                time.sleep(1)
                
        except Exception as e:
            print(f"[API请求失败] {e}，将在 1 秒后重试...")
            time.sleep(1)
            
    # 如果 5 次重试都失败，返回默认文本
    return ["大多数人如果能给更多事情一个机", "会的话，他们的问题都能解决。"], "—— 岛上书店"

def get_lunar():
    """获取农历，去掉了前面的'农历'二字"""
    now = datetime.datetime.now()
    lunar_day = sxtwl.fromSolar(now.year, now.month, now.day)
    ymc = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "腊"]
    rmc = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十", 
           "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十", 
           "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"]
    month = lunar_day.getLunarMonth()
    day = lunar_day.getLunarDay()
    
    # 【修改点】删除了前面的 f"农历..."
    return f"{ymc[month-1]}月{rmc[day-1]}"

def main():
    try:
        epd = epd4in2.EPD()
        epd.init()

        # 使用 L 模式绘制以获取抗锯齿边缘
        image_gray = Image.new('L', (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(image_gray)
        
        # ==========================================
        # 字体统一配置区
        # ==========================================
        font_time = ImageFont.truetype(FONT_PATH, 90)
        font_date = ImageFont.truetype(FONT_PATH, 22)   # 副栏字体设为 22
        font_quote = ImageFont.truetype(FONT_PATH, 22)  # 名言字体同样设为 22
        font_author = ImageFont.truetype(FONT_PATH, 18)

        now_dt = datetime.datetime.now()
        current_timestamp = time.time()
        
        # 缓存机制：每 10 分钟 (600秒) 更新一次名言
        state = load_state()
        if current_timestamp - state['timestamp'] >= 600 or not state['lines']:
            print("\n>>> 触发 10 分钟节点，正在抓取新名言...")
            lines, footer = get_quote_that_fits(draw, font_quote)
            save_state(lines, footer, current_timestamp)
            # 只有在换名言的时候，才执行一次深度清屏防止残影
            epd.Clear() 
        else:
            lines = state['lines']
            footer = state['footer']
            time_left = 600 - int(current_timestamp - state['timestamp'])
            print(f"\n>>> 从本地缓存加载名言 (距下次换句还有 {time_left} 秒)")

        # --- 1. 顶部区域：时间 ---
        time_str = now_dt.strftime('%H:%M')
        bbox_time = draw.textbbox((0, 0), time_str, font=font_time)
        w_time = bbox_time[2] - bbox_time[0]
        draw.text(((400 - w_time) / 2, 10), time_str, font=font_time, fill=0)

        draw.line((20, 115, 380, 115), fill=0, width=2)

        # --- 2. 中部区域：日期 ---
        date_str = now_dt.strftime('%Y-%m-%d')
        weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now_dt.weekday()]
        lunar_str = get_lunar()
        
        middle_str = f"{date_str}    {weekday}    {lunar_str}"
        bbox_mid = draw.textbbox((0, 0), middle_str, font=font_date)
        w_mid = bbox_mid[2] - bbox_mid[0]
        draw.text(((400 - w_mid) / 2, 135), middle_str, font=font_date, fill=0)

        draw.line((20, 175, 380, 175), fill=0, width=2)

        # --- 3. 底部区域：名言与出处 ---
        y_offset = 195
        for line in lines:
            draw.text((20, y_offset), line, font=font_quote, fill=0)
            y_offset += 32 # 行距
            
        bbox_author = draw.textbbox((0, 0), footer, font=font_author)
        w_author = bbox_author[2] - bbox_author[0]
        draw.text((380 - w_author, 270), footer, font=font_author, fill=0)

        # ==========================================
        # 终端回显：实时监控当前屏幕内容
        # ==========================================
        print("\n" + "="*45)
        print(" 终端回显：当前墨水屏内容")
        print("="*45)
        print(f"【时 间】 {time_str}")
        print(f"【副 栏】 {middle_str}")
        print(f"【名 言】")
        for idx, line in enumerate(lines):
            print(f"          {line}")
        print(f"【出 处】 {footer}")
        print("="*45 + "\n")

        # --- 4. 图像二值化魔法 ---
        THRESHOLD = 160 
        lut = [255 if x > THRESHOLD else 0 for x in range(256)]
        image_bw = image_gray.point(lut, '1')

        print("正在推送至墨水屏...")
        epd.display(epd.getbuffer(image_bw))
        epd.sleep()
        print("推送成功，屏幕已休眠。\n")

    except Exception as e:
        print(f"运行出错: {e}")

if __name__ == "__main__":
    main()
