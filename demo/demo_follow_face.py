import time
import em_vlm as vlm
import em_mecanum as car
import em_display as disp

# ===== 配置 =====
CENTER_X = 300           # 画面中心 X
DEAD_ZONE = 100          # 死区，小于此偏差不转向
MAX_OFFSET = CENTER_X    # 最大偏差（中心到边缘距离）
MIN_SPEED = 40           # 最小转向 RPM
MAX_SPEED = 60           # 最大转向 RPM
LOOP_MS = 50            # 主循环间隔（ms）

# ===== 屏幕辅助 =====
label_status = None
label_info = None

def show(text):
    print(text)
    if label_status:
        disp.set_label_text(label_status, text)

def show_info(text):
    if label_info:
        disp.set_label_text(label_info, text)


def main():
    global label_status, label_info

    # ===== 初始化屏幕（白底） =====
    disp.init_canvas()
    disp.set_bg_color(0xFFFFFF)
    disp.label_cn(10, 10, "人脸跟随程序", 0x000000)
    label_status = disp.label_cn(10, 40, "初始化中...", 0x333333)
    label_info = disp.draw_label(10, 70, "", 0x555555, 14)

    # ===== 初始化底盘 =====
    show("底盘初始化...")
    car.init()
    car.stop()
    show("底盘就绪")
    time.sleep(0.3)

    # ===== 初始化 K230 摄像头 =====
    show("检查 K230...")
    if not vlm.is_online():
        show("错误: K230 不在线!")
        return

    vlm.set_model(vlm.MODEL_FACE)
    show("切换到人脸识别")
    time.sleep(0.5)

    # ===== 主循环 =====
    show("开始跟随...")
    while True:
        time.sleep_ms(LOOP_MS)

        # 检查模型是否正确
        if vlm.model_type() != vlm.MODEL_FACE:
            vlm.set_model(vlm.MODEL_FACE)
            time.sleep_ms(300)

        # 获取人脸数量
        count = vlm.get_total_num()
        if count is None or count == 0:
            car.stop()
            show("未检测到人脸")
            continue

        # 获取第一个人脸的位置
        ids = vlm.get_ids()
        if not ids:
            car.stop()
            continue

        face = vlm.get_face_info(ids[0])
        if face is None:
            car.stop()
            continue

        face_cx = face["x"] + face["w"] // 2
        offset = face_cx - CENTER_X
        abs_off = abs(offset)

        # 根据偏差线性映射速度：偏差越大越快
        if abs_off <= DEAD_ZONE:
            car.stop()
            show("人脸在中心，停止")
            continue

        ratio = (abs_off - DEAD_ZONE) / (MAX_OFFSET - DEAD_ZONE)
        ratio = max(0.0, min(1.0, ratio))
        turn_speed = int(MIN_SPEED + (MAX_SPEED - MIN_SPEED) * ratio)

        show_info(f"cx={face_cx} off={offset} spd={turn_speed}")

        if offset < 0:
            car.move(car.DIR_ROTATE_LEFT, turn_speed)
            show(f"左转 {turn_speed}")
        else:
            car.move(car.DIR_ROTATE_RIGHT, turn_speed)
            show(f"右转 {turn_speed}")


if __name__ == "__main__":
    main()