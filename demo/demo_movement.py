import time
import em_motor as motor

SPEED = 120  # RPM
DURATION = 3  # 秒

def get_all_ids():
    """返回 {轮位: can_id} 字典"""
    mapping = {}
    for dev in motor.list():
        w = dev.get("wheel")
        if w in (motor.WHEEL_FL, motor.WHEEL_FR, motor.WHEEL_RL, motor.WHEEL_RR):
            mapping[w] = dev["can_id"]
    return mapping

def drive_all(fl, fr, rl, rr, duration=DURATION):
    """同时给四个轮子发速度指令"""
    ids = get_all_ids()
    if len(ids) < 4:
        print("[WARN] 未检测到全部四个轮子，当前在线:", list(ids.keys()))
        return False
    motor.set_speed(ids[motor.WHEEL_FL], fl, duration)
    motor.set_speed(ids[motor.WHEEL_FR], fr, duration)
    motor.set_speed(ids[motor.WHEEL_RL], rl, duration)
    motor.set_speed(ids[motor.WHEEL_RR], rr, duration)
    return True

def main():
    print("在线电机数:", motor.count())
    ids = get_all_ids()
    if len(ids) < 4:
        print("需要四个轮子都在线才能演示全向移动")
        return

    print("\n=== 1. 前进 ===")
    # 四轮同向同速
    drive_all(SPEED, SPEED, SPEED, SPEED)
    time.sleep(DURATION + 0.5)

    print("\n=== 2. 后退 ===")
    drive_all(-SPEED, -SPEED, -SPEED, -SPEED)
    time.sleep(DURATION + 0.5)

    print("\n=== 3. 左平移（蟹行）=== ")
    # 左前+右后反转，右前+左后正转
    drive_all(-SPEED, SPEED, SPEED, -SPEED)
    time.sleep(DURATION + 0.5)

    print("\n=== 4. 右平移（蟹行）=== ")
    drive_all(SPEED, -SPEED, -SPEED, SPEED)
    time.sleep(DURATION + 0.5)

    print("\n=== 5. 原地逆时针旋转 ===")
    # 左侧反转，右侧正转
    drive_all(-SPEED, SPEED, -SPEED, SPEED)
    time.sleep(DURATION + 0.5)

    print("\n=== 6. 原地顺时针旋转 ===")
    drive_all(SPEED, -SPEED, SPEED, -SPEED)
    time.sleep(DURATION + 0.5)

    print("\n=== 7. 左前斜向 ===")
    # 左前停，右后停，右前+左后正转
    drive_all(0, SPEED, SPEED, 0)
    time.sleep(DURATION + 0.5)

    print("\n=== 8. 右前斜向 ===")
    drive_all(SPEED, 0, 0, SPEED)
    time.sleep(DURATION + 0.5)

    print("\n全部停止")
    motor.stop()

if __name__ == "__main__":
    main()