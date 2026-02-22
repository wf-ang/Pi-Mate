import epd4in2
import time
import requests
import sxtwl
from PIL import Image, ImageDraw, ImageFont
import datetime
import os

# 字体路径（确保已安装 fonts-wqy-microhei）
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

def get_quote():
    """获取名言：d文学、i哲学、h诗词"""
    try:
        # c=d:文学, c=i:哲学, c=h:诗词
        url = "https://v1.hitokoto.cn/?c=d&c=i&c=h"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data['hitokoto'], f"—— {data['from']}"
    except Exception as e:
        print(f"API请求失败: {e}")
        return "众里寻他千百度，蓦然回首，那人却在，灯火阑珊处。", "—— 辛弃疾"

def get_lunar():
    """获取农历"""
    now = datetime.datetime.now()
    lunar = sxtwl.fromSolar(now.year, now.month, now.day)
    ymc = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "腊"]
    rmc = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十", 
           "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十", 
           "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"]
    return f"农历{ymc[lunar.getMonth()-1]}月{rmc[lunar.getDay()-1]}"

def main():
    try:
        epd = epd4in2.EPD()
        
        # 1. 全局刷新逻辑：每次启动都会执行 init 和 Clear
        print("开始全局刷新...")
        epd.init()
        epd.Clear() # 屏幕会闪烁几次，这能有效清除残影

        image = Image.new('1', (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(image)
        
        # 加载字体
        font_time = ImageFont.truetype(FONT_PATH, 70)
        font_date = ImageFont.truetype(FONT_PATH, 22)
        font_quote = ImageFont.truetype(FONT_PATH, 24)
        font_author = ImageFont.truetype(FONT_PATH, 18)

        # 1. 绘制时间与日期
        now = datetime.datetime.now()
        time_str = now.strftime('%H:%M')
        date_str = now.strftime('%Y年%m月%d日')
        weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
        
        draw.text((20, 10), time_str, font=font_time, fill=0)
        draw.text((220, 25), date_str, font=font_date, fill=0)
        draw.text((220, 55), f"{weekday} | {get_lunar()}", font=font_date, fill=0)

        draw.line((20, 95, 380, 95), fill=0, width=2)

        # 2. 绘制名言（文学、哲学、诗词）
        quote, author = get_quote()
        
        # 简单的自动换行逻辑（每行约15个汉字）
        line_length = 15
        lines = [quote[i:i+line_length] for i in range(0, len(quote), line_length)]
        
        y_offset = 120
        for line in lines[:3]: # 最多显示3行，防止重叠
            draw.text((40, y_offset), line, font=font_quote, fill=0)
            y_offset += 35
            
        draw.text((240, 260), author, font=font_author, fill=0)

        # 3. 推送显示并进入睡眠
        epd.display(epd.getbuffer(image))
        print("显示更新完成。")
        epd.sleep()

    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
