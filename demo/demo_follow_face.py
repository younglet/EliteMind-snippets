import time
import em_vlm as vlm
import em_display as disp
import em_mecanum as mecanum

BLACK = 0x000000  # 黑色

SPEED = 50  # 跟随速度
X_DEAD = 80  # 左右死区：人脸中心 x 与基准的偏差（像素）
W_DEAD = 20  # 前后死区：人脸宽度与基准的偏差（像素）
LOST_MAX = 5  # 目标连续丢失帧数，超过则停车

DIR_NAMES = ["前进", "后退", "左移", "右移"]  # 移动方向

# 初始化绘图层，创建全屏白色容器
disp.init_canvas()
# 创建中文标签
title_label = disp.label_cn(60, 6, "人脸自动跟随", BLACK, False)
status_label = disp.label_cn(10, 30, "状态: 等待标定", BLACK, False)
hint_label = disp.label_cn(10, 50, "人脸正对前方,点击屏幕标定", BLACK, False)
data_label = disp.label_cn(10, 70, "-", BLACK, False)
action_label = disp.label_cn(10, 90, "动作: -", BLACK, False)

# 初始化
if not mecanum.init():
    disp.set_label_text(status_label, "状态: 初始化失败")

# 切换到人脸识别模型
if vlm.set_model(vlm.MODEL_FACE):
    time.sleep(1)  # 等待模型切换完成


# 获取当前检测到的人脸信息
def get_face():
    # 读取已拼装完成的匹配目标列表
    ids = vlm.get_ids()
    if ids:
        # 查询该 ID 的人脸详情，返回 {"id", "x", "y", "w", "h"}
        return vlm.get_face_info(ids[0])
    return None


# 标定基准：目标人脸中心 x 与宽度，标定后保持不变，作为跟随的参考值
target_cx = None  # 记录人脸x坐标
target_w = 0  # 记录人脸宽度
last_pressed = 0  # 上一次触屏状态
last_dir = None  # 上一次运动方向
lost_frames = 0  # 目标连续丢失帧数，检测到人脸后清零

while True:
    # ---- 触屏标定：仅首次点击屏幕时记录基准 ----
    # 读取当前触屏状态
    x, y, pressed = disp.get_touch()
    # target_cx 为 None 表示尚未标定；已标定后忽略后续点击
    if target_cx is None and pressed and not last_pressed:
        face = get_face()
        if face:
            # 以人脸矩形中心 x 作为左右基准，以人脸宽度作为远近基准
            target_cx = face["x"] + face["w"] // 2
            target_w = face["w"]
            lost_frames = 0
            disp.set_label_text(status_label, "状态: 跟随中")
            disp.set_label_text(hint_label, f"基准 x={target_cx} w={target_w}")
        else:
            disp.set_label_text(status_label, "状态: 未检测到人脸")
    last_pressed = pressed  # 保存触摸状态

    # ---- 人脸跟随 ----
    if target_cx is not None:  # 已标定才进入跟随
        face = get_face()
        if face is None:
            # 视觉模块暂时没有返回人脸：累计丢帧，达到阈值且此前正在运动则停车一次
            lost_frames += 1
            if lost_frames >= LOST_MAX and last_dir is not None:
                mecanum.stop()
                last_dir = None
                disp.set_label_text(action_label, "动作: 目标丢失停车")
        else:
            # 目标重新出现
            if lost_frames and last_dir is None:
                disp.set_label_text(action_label, "动作: 停止")
            lost_frames = 0
            # 当前人脸中心 x；w 用于估算与目标的距离
            cx = face["x"] + face["w"] // 2
            disp.set_label_text(data_label, f"当前 x={cx} w={face['w']}")
            # 左右偏差优先，再看远近；偏差都在死区内则停车
            if cx < target_cx - X_DEAD:
                direction = mecanum.DIR_LEFT  # 向左平移
            elif cx > target_cx + X_DEAD:
                direction = mecanum.DIR_RIGHT  # 向右平移
            elif face["w"] < target_w - W_DEAD:
                direction = mecanum.DIR_FORWARD  # 前进
            elif face["w"] > target_w + W_DEAD:
                direction = mecanum.DIR_BACKWARD  # 后退
            else:
                direction = None  # 在死区内，保持不动
            # 仅在方向发生变化时下发命令
            if direction != last_dir:
                if direction is None:
                    mecanum.stop()
                    disp.set_label_text(action_label, "动作: 停止")
                else:
                    mecanum.move(direction, SPEED)
                    disp.set_label_text(action_label, f"动作: {DIR_NAMES[direction]}")
                last_dir = direction

    time.sleep_ms(50)
