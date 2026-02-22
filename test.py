import RPi.GPIO as GPIO
BUSY_PIN = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUSY_PIN, GPIO.IN)
print("正在读取 BUSY 状态...")
print("当前 BUSY 引脚电平:", GPIO.input(BUSY_PIN))
