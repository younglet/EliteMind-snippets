import em_led as led
import time

NUM_LEDS = 8
BRIGHTNESS = 128
WHITE = 0xFFFFFF
ALL_MASK = (1 << NUM_LEDS) - 1

if not led.is_online():
    print("未检测到LED设备")
else:
    print("LED设备在线")

print("\n=== 逐位检测开始 ===")

# 首尾灯闪烁 3 次白光
for _ in range(3):
    mask = (1 << 0) | (1 << (NUM_LEDS - 1))
    led.set_mask(mask, WHITE, brightness=BRIGHTNESS)
    time.sleep(0.3)
    led.set_mask(ALL_MASK, 0x000000)
    time.sleep(0.3)

# 直接跑马灯效果（替代逐颗点亮）
print(">>> 跑马灯检测")
led.set_effect(led.EFFECT_RUNNING, WHITE, direction=led.DIR_FORWARD, speed=5, brightness=BRIGHTNESS)
time.sleep(3)
led.set_effect(led.EFFECT_NONE, 0x000000)
time.sleep(0.3)

print("=== 逐位检测完成 ===\n")

# ========== 后续灯效 ==========

print(">>> 呼吸灯 - 蓝色")
led.set_effect(led.EFFECT_BREATHING, 0x0000FF, speed=5, brightness=BRIGHTNESS)
time.sleep(6)

print(">>> 跑马灯 - 红色")
led.set_effect(led.EFFECT_RUNNING, 0xFF0000, direction=led.DIR_FORWARD, speed=5, brightness=BRIGHTNESS)
time.sleep(5)

print(">>> 跑马灯反向 - 橙色")
led.set_effect(led.EFFECT_RUNNING, 0xFF6600, direction=led.DIR_BACKWARD, speed=5, brightness=BRIGHTNESS)
time.sleep(5)

print(">>> 彩虹渐变")
led.set_effect(led.EFFECT_RAINBOW, 0xFFFFFF, speed=5, brightness=BRIGHTNESS)
time.sleep(8)

print(">>> 滚动流动 - 绿色")
led.set_effect(led.EFFECT_MARQUEE, 0x00FF00, direction=led.DIR_FORWARD, speed=5, brightness=BRIGHTNESS)
time.sleep(5)

print(">>> 静态常亮 - 白色")
led.set_effect(led.EFFECT_STATIC, WHITE, speed=5, brightness=BRIGHTNESS)
time.sleep(3)

print(">>> 灯光秀结束")
led.set_effect(led.EFFECT_NONE, 0x000000)