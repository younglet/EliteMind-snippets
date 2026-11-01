import time
import em_sensor as sensor
import em_display as disp

BLACK = 0x000000  # 黑色

LDR_MAX = 120  # 光敏传感器实际测量到环境中的最强光线数值
MIN_BRIGHT = 10  # 最低屏幕亮度

# 初始化绘图层，创建全屏白色容器
disp.init_canvas()

# 创建中文标签
title_lbl = disp.label_cn(60, 30, "屏幕亮度自动调节", BLACK, False)
light_lbl = disp.label_cn(10, 80, "光敏数值: -", BLACK, False)
bright_lbl = disp.label_cn(10, 120, "屏幕亮度: -", BLACK, False)
status_lbl = disp.label_cn(10, 160, "状态: 等待传感器...", BLACK, False)

while True:
    light = sensor.get_ldr_light()  # 读取光敏传感器数值，无数据返回 None

    if light is None:
        disp.set_label_text(light_lbl, "光敏数值: 无数据")
        disp.set_label_text(status_lbl, "状态: 传感器离线")
    else:
        # 将光敏数值(0~LDR_MAX)线性映射为亮度(MIN_BRIGHT~100)
        if light > LDR_MAX:
            light = LDR_MAX
        bright = MIN_BRIGHT + (100 - MIN_BRIGHT) * light // LDR_MAX

        disp.set_backlight(bright)  # 调整屏幕背光亮度

        # 实时显示数值
        disp.set_label_text(light_lbl, f"光敏数值: {light}")
        disp.set_label_text(bright_lbl, f"屏幕亮度: {bright}%")
        disp.set_label_text(status_lbl, "状态: 运行中")

    time.sleep(0.2)
