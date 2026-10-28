import em_sensor as sensor
import em_mecanum as mecanum
import em_gripper as gripper
import em_led as led
import time
import math

# ============================================================================
# 麦轮遥控小车 + 夹爪 + 转向灯 + LED 灯带
#
# 遥控器按键布局（bit 掩码）：
#        1                16
#   2         8      128      32
#      4                   64
#
#   左簇 4 键 (1/2/4/8)    -> 调亮度 + 调颜色
#   右簇 4 键 (16/64/32/128) -> 灯效：16爆闪 64呼吸灯 32滚动流动 128逆向跑马
#   16384 常亮 / 32768 彩虹
#   256 / 512 左右转向灯    1024 / 2048 夹爪开/关
#
# 灯光统一逻辑（与转向灯一致）：
#   点一下 -> 开；再点一下 -> 关；点另一个灯效键 -> 直接切过去
#
# 灯带 API 参考 demo_led.py：
#   关灯            -> led.set_mask(ALL_MASK, 0x000000)
#   灯效            -> led.set_effect(EFFECT_xxx, 颜色, speed=5, brightness=xx)
#   停掉原生效果    -> led.set_effect(EFFECT_NONE, 0x000000)
#   首尾灯/转向灯   -> led.set_mask(mask, 颜色, brightness=xx)
# ============================================================================

# ===== 摇杆参数 =====
CENTER = 100
DEADZONE = 8
MAX_SPEED = 300  # 最高速度

# ===== 按键位掩码 =====
KEY_LEFT_SIGNAL = 256  # 左转向灯
KEY_RIGHT_SIGNAL = 512  # 右转向灯
KEY_GRIPPER_OPEN = 1024  # 夹爪打开
KEY_GRIPPER_CLOSE = 2048  # 夹爪关闭

KEY_LEFT_UP = 1  # 左簇-上   亮度 +
KEY_LEFT_DOWN = 4  # 左簇-下   亮度 -
KEY_LEFT_LEFT = 2  # 左簇-左   色调 -
KEY_LEFT_RIGHT = 8  # 左簇-右   色调 +
LEFT_KEYS = (KEY_LEFT_UP, KEY_LEFT_DOWN, KEY_LEFT_LEFT, KEY_LEFT_RIGHT)

KEY_RIGHT_UP = 16  # 右簇-上   爆闪
KEY_RIGHT_LEFT = 64  # 右簇-左   呼吸灯
KEY_RIGHT_RIGHT = 32  # 右簇-右   滚动流动
KEY_RIGHT_DOWN = 128  # 右簇-下   逆向跑马
RIGHT_KEYS = (KEY_RIGHT_UP, KEY_RIGHT_LEFT, KEY_RIGHT_RIGHT, KEY_RIGHT_DOWN)

# ===== 灯光按键（所有灯光按钮同一套逻辑：再按一次关闭，可直接切到其它模式）=====
KEY_LIGHT_ON = 16384  # 常亮
KEY_LIGHT_RAINBOW = 32768  # 彩虹（原“关闭”键改成彩虹，不再有单独关灯键）
LIGHT_MODE_MASK = KEY_LIGHT_ON | KEY_LIGHT_RAINBOW

# ===== 灯带参数 =====
NUM_LEDS = 8
ALL_MASK = (1 << NUM_LEDS) - 1
LED_LEFT_INDEX = 0  # 第1颗灯 = 左转向灯
LED_RIGHT_INDEX = 7  # 第8颗灯 = 右转向灯
LED_BRIGHTNESS = 128
TURN_COLOR = 0xFF8000  # 转向灯颜色（琥珀色）
OFF_COLOR = 0x000000
BLINK_MS = 400  # 转向灯闪烁半周期
EFFECT_SPEED = 5  # 原生灯效速度
STROBE_MS = 100  # 爆闪半周期（亮/灭各 100ms）
TURN_OFF_THRESHOLD = 20  # 反向平移/旋转偏移超过该值时，对应转向灯自动熄灭
# 方向判定：+1 = 摇杆偏移为正时车辆实际向右（右移/右转）；若实车方向相反，改成 -1
DIR_RIGHT_SIGN = 1

# ===== 颜色 / 亮度 =====
HUE_STEP = 30  # 每次调色的色相步进（度）
HUE_MAX = 360
BRIGHT_STEP = 32  # 每次调亮度的步进
BRIGHT_MAX = 255
BRIGHT_MIN = 33  # 最低亮度（不能全黑）
SATURATION = 1.0  # 饱和度（1.0 = 纯色）


def hsv_to_rgb(h, s, v):
    """色相/饱和度/明度 -> (r,g,b)"""
    h = h % 360
    c = v * s
    x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0.0
    elif h < 120:
        r, g, b = x, c, 0.0
    elif h < 180:
        r, g, b = 0.0, c, x
    elif h < 240:
        r, g, b = 0.0, x, c
    elif h < 300:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x
    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


def pack_color(rgb):
    """(r,g,b) -> 0xRRGGBB"""
    r, g, b = rgb
    return ((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF)


def fx_strobe(t):
    """爆闪：整条灯带亮/灭交替（原生没有爆闪效果，这个自己画）"""
    on = ((t // STROBE_MS) % 2) == 0
    return (ALL_MASK, None) if on else (0, None)


def build_effects():
    """右簇 4 键 -> 灯效（原生效果用法参考 demo_led.py）"""
    n_run = getattr(led, "EFFECT_RUNNING", None)
    n_breath = getattr(led, "EFFECT_BREATHING", None)
    n_marquee = getattr(led, "EFFECT_MARQUEE", None)
    d_fwd = getattr(led, "DIR_FORWARD", None)
    d_bwd = getattr(led, "DIR_BACKWARD", None)
    return [
        # (按键, 名称, 类型, 参数, 方向)
        (KEY_RIGHT_UP, "爆闪", "soft", fx_strobe, None),
        (KEY_RIGHT_LEFT, "呼吸灯", "native", n_breath, None),
        (KEY_RIGHT_RIGHT, "滚动流动", "native", n_marquee, d_fwd),
        (KEY_RIGHT_DOWN, "逆向跑马", "native", n_run, d_bwd),
    ]


def send_effect(eff, color, bright, direction=None):
    """下发原生灯效"""
    if eff is None:
        return False
    try:
        if direction is None:
            led.set_effect(eff, color, speed=EFFECT_SPEED, brightness=bright)
        else:
            led.set_effect(eff, color, direction=direction, speed=EFFECT_SPEED, brightness=bright)
        return True
    except Exception as e:
        print("[WARN] 灯效下发失败:", e)
        return False


def stop_effect():
    """停掉设备上的原生效果"""
    try:
        led.set_effect(led.EFFECT_NONE, 0x000000)
    except Exception:
        pass


def lights_off(cover_rainbow=False):
    """彻底关闭：停原生效果 + 整条清黑（参考 demo_led.py）
       cover_rainbow=True 时先用静态黑覆盖，防止彩虹停不掉
    """
    if cover_rainbow:
        try:
            led.set_effect(
                led.EFFECT_STATIC, 0x000000,
                speed=EFFECT_SPEED, brightness=BRIGHT_MIN,
            )
        except Exception:
            pass
    stop_effect()
    try:
        led.set_mask(ALL_MASK, OFF_COLOR)
    except Exception as e:
        print("[WARN] 关灯失败:", e)


def show_turn(mask):
    """转向灯：mask 点亮第1/第8颗；mask=0 时整条熄灭"""
    try:
        if mask:
            led.set_mask(mask, TURN_COLOR, brightness=LED_BRIGHTNESS)
        else:
            led.set_mask(ALL_MASK, OFF_COLOR)
    except Exception as e:
        print("[WARN] 转向灯下发失败:", e)


class KeyRepeat:
    """左簇按键：沿触发 + 长按连发（只管亮度/色调 4 个键）"""

    def __init__(self):
        self.state = {}

    def fired(self, keys, now):
        """返回本次需要响应的按键列表"""
        out = []
        for bit in LEFT_KEYS:
            if keys & bit:
                st = self.state.get(bit)
                if st is None:
                    self.state[bit] = {"since": now, "next": now + 400}
                    out.append(bit)
                elif time.ticks_diff(now, st["next"]) >= 0:
                    st["next"] = now + 150
                    out.append(bit)
            else:
                self.state.pop(bit, None)
        return out


def joystick_offset(v):
    """读取摇杆并返回相对中心的偏移量；无数据(None)按 0 处理"""
    if v is None:
        return 0
    return v - CENTER


def deadzone(v):
    """死区处理"""
    return 0 if abs(v) < DEADZONE else v


def main():
    try:
        led_ok = led.is_online()
    except Exception as e:
        print("[WARN] LED 设备检测失败:", e)
        led_ok = False
    if not led_ok:
        print("[WARN] LED 设备不在线，灯效/转向灯不可用")

    EFFECTS = build_effects()
    # 灯效状态名 -> 灯效规格（名称, 类型, 参数, 方向）
    FX = {
        "fx_strobe": EFFECTS[0],
        "fx_breath": EFFECTS[1],
        "fx_marquee": EFFECTS[2],
        "fx_run_back": EFFECTS[3],
    }
    # 所有灯光按钮 -> 目标状态（同一套逻辑：再按一次关闭，点别的直接切过去）
    LIGHT_BUTTONS = [
        (KEY_LEFT_SIGNAL, "turn_left"),
        (KEY_RIGHT_SIGNAL, "turn_right"),
        (KEY_RIGHT_UP, "fx_strobe"),
        (KEY_RIGHT_LEFT, "fx_breath"),
        (KEY_RIGHT_RIGHT, "fx_marquee"),
        (KEY_RIGHT_DOWN, "fx_run_back"),
        (KEY_LIGHT_ON, "steady"),
        (KEY_LIGHT_RAINBOW, "rainbow"),
    ]
    LIGHT_NAME = {
        "off": "关闭",
        "steady": "常亮",
        "rainbow": "彩虹",
        "turn_left": "左转向灯",
        "turn_right": "右转向灯",
        "fx_strobe": EFFECTS[0][1],
        "fx_breath": EFFECTS[1][1],
        "fx_marquee": EFFECTS[2][1],
        "fx_run_back": EFFECTS[3][1],
    }

    # ===== 灯光状态机（单一状态源）=====
    # off / steady / rainbow / turn_left / turn_right / fx_xxx
    light = "off"
    cmd = None  # 已下发的命令标识，避免重复下发

    hue = 180  # 色相 0~359，默认 180 = 青色(0x00FFFF)
    bright = 200  # 亮度 33~255
    turn = {"blink_on": True, "next_toggle": 0}
    keys = KeyRepeat()
    prev_keys = 0
    remote_lost = False

    print("=== 麦轮遥控 + 灯效 ===")
    print("摇杆: 运动   1024/2048: 夹爪开/关")
    print("灯光按钮统一逻辑: 点一下开, 再点一下关, 点另一个直接切过去")
    print("16384 常亮  32768 彩虹  256/512 左右转向灯")
    print("右簇 16/64/32/128 = 爆闪/呼吸灯/滚动流动/逆向跑马")
    print("左簇 1/4=亮度+/- 2/8=色调-/+   默认青色(0x00FFFF) 转向灯琥珀色(0xFF8000)")

    while True:
        keys_now = 0
        try:
            now = time.ticks_ms()
            keys_now = sensor.get_bt_remote(0) or 0

            # ===== 摇杆：底盘运动 =====
            ly = sensor.get_bt_remote(1)  # 左摇杆前后
            lx = sensor.get_bt_remote(2)  # 左摇杆左右
            rx = sensor.get_bt_remote(4)  # 右摇杆左右

            forward_raw = joystick_offset(ly)
            strafe_raw = joystick_offset(lx)
            rotate_raw = joystick_offset(rx)

            if ly is None and lx is None and rx is None:
                mecanum.set_wheels(0, 0, 0, 0)  # 遥控器无数据：停车
                if not remote_lost:
                    remote_lost = True
                    print("[WARN] 遥控器无数据，已停车")
            else:
                remote_lost = False
                forward = deadzone(forward_raw)
                strafe = deadzone(strafe_raw)
                rotate = deadzone(rotate_raw)

                # 麦轮混控：左前、右前、左后、右后
                lf = forward + strafe + rotate
                rf = forward - strafe - rotate
                lb = forward - strafe + rotate
                rb = forward + strafe - rotate

                # 按最高速度缩放，保留各轮之间的比例
                max_value = max(abs(lf), abs(rf), abs(lb), abs(rb), CENTER)
                mecanum.set_wheels(
                    int(lf * MAX_SPEED / max_value),
                    int(rf * MAX_SPEED / max_value),
                    int(lb * MAX_SPEED / max_value),
                    int(rb * MAX_SPEED / max_value),
                )

            # ===== 夹爪：按键沿触发 =====
            if keys_now & KEY_GRIPPER_OPEN and not (prev_keys & KEY_GRIPPER_OPEN):
                gripper.open(0)
                print("夹爪打开")
            if keys_now & KEY_GRIPPER_CLOSE and not (prev_keys & KEY_GRIPPER_CLOSE):
                gripper.close(0)
                print("夹爪关闭")

            # ===== 灯光按钮（统一逻辑：再按一次关闭，点别的直接切过去）=====
            # 不 break：同一帧多个灯键同时按下时，按列表顺序依次处理，后面的生效
            for bit, target in LIGHT_BUTTONS:
                if keys_now & bit and not (prev_keys & bit):
                    if light == target:
                        light = "off"  # 再按一次 = 关闭
                        print("灯光: 关闭")
                    else:
                        light = target  # 直接切到其它模式
                        print("灯光:", LIGHT_NAME.get(target, target))

            # ===== 转向灯：反向运动自动熄灭 =====
            strafe_right = strafe_raw * DIR_RIGHT_SIGN
            rotate_right = rotate_raw * DIR_RIGHT_SIGN
            if light == "turn_left" and (
                strafe_right > TURN_OFF_THRESHOLD or rotate_right > TURN_OFF_THRESHOLD
            ):
                light = "off"
                print("左转向灯: 关（反向运动，自动熄灭）")
            elif light == "turn_right" and (
                strafe_right < -TURN_OFF_THRESHOLD or rotate_right < -TURN_OFF_THRESHOLD
            ):
                light = "off"
                print("右转向灯: 关（反向运动，自动熄灭）")

            # ===== 左簇调色/亮度 =====
            for bit in keys.fired(keys_now, now):
                if bit == KEY_LEFT_UP:
                    bright = min(BRIGHT_MAX, bright + BRIGHT_STEP)
                    print("亮度:", bright)
                elif bit == KEY_LEFT_DOWN:
                    bright = max(BRIGHT_MIN, bright - BRIGHT_STEP)
                    print("亮度:", bright)
                elif bit == KEY_LEFT_RIGHT:
                    hue = (hue + HUE_STEP) % HUE_MAX
                    print("色调:", hue)
                elif bit == KEY_LEFT_LEFT:
                    hue = (hue - HUE_STEP) % HUE_MAX
                    print("色调:", hue)

            # ===== 灯带下发（状态没变就不发，参考 demo_led.py 的用法）=====
            if led_ok:
                color_now = pack_color(hsv_to_rgb(hue, SATURATION, 1.0))
                if light == "off":
                    if cmd != ("off",):
                        # 彩虹这类原生效果用 EFFECT_NONE 可能停不掉，先用静态黑覆盖
                        lights_off(cover_rainbow=(cmd is not None and cmd[0] == "rainbow"))
                        cmd = ("off",)
                elif light == "steady":
                    # 常亮：一条命令把 8 颗全部点亮为当前颜色
                    key = ("steady", color_now, bright)
                    if cmd != key:
                        try:
                            led.set_mask(ALL_MASK, color_now, brightness=bright)
                            cmd = key
                        except Exception as e:
                            print("[WARN] 常亮下发失败:", e)
                elif light == "rainbow":
                    key = ("rainbow", bright)
                    if cmd != key:
                        if send_effect(getattr(led, "EFFECT_RAINBOW", None), 0xFFFFFF, bright):
                            cmd = key
                elif light in FX:
                    spec = FX[light]
                    if spec[2] == "native":
                        key = ("fx", light, color_now, bright)
                        if cmd != key:
                            if send_effect(spec[3], color_now, bright, spec[4]):
                                cmd = key
                    else:
                        # 自绘效果（爆闪）：按节拍自己下发整条灯带
                        mask, color_override = spec[3](now)
                        c = color_now if color_override is None else pack_color(color_override)
                        key = ("soft", light, mask, c, bright)
                        if cmd != key:
                            try:
                                if mask:
                                    led.set_mask(mask, c, brightness=bright)
                                else:
                                    led.set_mask(ALL_MASK, OFF_COLOR)
                                cmd = key
                            except Exception as e:
                                print("[WARN] 灯效下发失败:", e)
                else:  # turn_left / turn_right 转向灯
                    turn_mask = (1 << LED_LEFT_INDEX) if light == "turn_left" else (1 << LED_RIGHT_INDEX)
                    if cmd is None or cmd[0] != "turn":
                        # 进入转向灯状态：先停掉原生效果，避免和 mask 抢
                        stop_effect()
                        turn["blink_on"] = True
                        turn["next_toggle"] = now + BLINK_MS
                        show_turn(turn_mask)
                        cmd = ("turn", turn_mask, True)
                    elif time.ticks_diff(now, turn["next_toggle"]) >= 0:
                        turn["blink_on"] = not turn["blink_on"]
                        turn["next_toggle"] = now + BLINK_MS
                        show_turn(turn_mask if turn["blink_on"] else 0)
                        cmd = ("turn", turn_mask, turn["blink_on"])

            prev_keys = keys_now
        except Exception as e:
            print("运行异常:", e)
        finally:
            # 无论是否异常都更新按键状态，避免边沿检测错乱
            prev_keys = keys_now

        time.sleep_ms(20)


if __name__ == "__main__":
    main()
