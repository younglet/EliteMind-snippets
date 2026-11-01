import time
import em_sensor as sensor
import em_mecanum as mecanum
import em_display as disp

BLACK = 0x000000  # 黑色

# 目标距离与容差（单位：mm）
TARGET_DIST = 150  # 保持与物体的距离
TOLERANCE = 20  # 死区 ±20，减少抖动
LOST_DIST = 350  # 超过该距离视为目标丢失
SPEED = 50  # 移动速度

# 初始化绘图层，创建全屏白色容器
disp.init_canvas()

# 创建中文标签
title_lbl = disp.label_cn(90, 6, "TOF 跟随", BLACK, False)
status_lbl = disp.label_cn(10, 30, "-", BLACK, False)
count_lbl = disp.label_cn(10, 50, "-", BLACK, False)
dist_lbl = disp.label_cn(10, 70, "-", BLACK, False)
action_lbl = disp.label_cn(10, 90, "-", BLACK, False)

disp.set_label_text(status_lbl, f"TOF状态: {sensor.is_online(sensor.DEV_TOF, 0)}")
disp.set_label_text(count_lbl, f"TOF数量: {sensor.count(sensor.DEV_TOF)}")

# 初始化底盘
mecanum.init()

# 记录上一次动作，避免重复发送相同命令
last_action = None

while True:
    # 读取 TOF 传感器的值（mm）
    dist = sensor.get_tof_distance(0)
    disp.set_label_text(dist_lbl, f"距离: {dist}")

    if dist is None:
        # 无有效读数，停车
        action = "stop"
        mecanum.stop()
    elif dist > LOST_DIST:
        # 距离过远，视为目标丢失，停车
        action = "lost"
        mecanum.stop()
    else:
        offset = dist - TARGET_DIST  # 正值=太远需前进，负值=太近需后退
        if offset > TOLERANCE:
            # 距离过远，前进
            action = "forward"
            mecanum.move(mecanum.DIR_FORWARD, SPEED)
        elif offset < -TOLERANCE:
            # 距离过近，后退
            action = "backward"
            mecanum.move(mecanum.DIR_BACKWARD, SPEED)
        else:
            # 在目标范围内，停止
            action = "stop"
            mecanum.stop()

    # 显示当前动作
    if action != last_action:
        disp.set_label_text(action_lbl, f"动作: {action}")
        last_action = action

    time.sleep_ms(100)
