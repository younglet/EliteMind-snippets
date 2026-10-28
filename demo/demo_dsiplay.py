import em_display as disp
import time
import math


def demo_basic():
    """基础画布与文字测试"""
    disp.init_canvas()
    disp.set_bg_color(0xFFFFFF)

    disp.draw_label(10, 10, "Demo: Basic", 0x000000, 18)
    disp.label_cn(10, 40, "基础画布与文字", 0x333333)
    disp.label_cn(10, 70, "背景：白色", 0x555555)

    print("对象数量:", disp.get_obj_count())
    time.sleep(3)


def demo_tv_colorbar():
    """电视彩条信号测试"""
    disp.init_canvas()
    disp.clear_canvas()
    disp.set_bg_color(0x000000)

    disp.draw_label(10, 5, "TV Colorbar Test", 0x00FF00, 16)
    disp.label_cn(10, 25, "电视彩条信号测试", 0xFFFFFF)

    # 顶部8标准彩条
    colors = [
        0xFFFFFF, 0xFFFF00, 0x00FFFF, 0x00FF00,
        0xFF00FF, 0xFF0000, 0x0000FF, 0x000000
    ]
    bar_width = 30
    bar_height = 80
    start_x = 0
    start_y = 50

    for i, c in enumerate(colors):
        disp.draw_rect(start_x + i * bar_width, start_y, bar_width, bar_height, c, c, 0)

    # 中部10个灰度阶跃条
    gray_colors = [
        0x000000, 0x222222, 0x444444, 0x666666, 0x888888,
        0xAAAAAA, 0xCCCCCC, 0xEEEEEE, 0xEEEEEE, 0xFFFFFF,
    ]
    gray_bar_height = 30
    gray_y = start_y + bar_height + 5

    for i, c in enumerate(gray_colors):
        disp.draw_rect(start_x + i * bar_width, gray_y, bar_width, gray_bar_height, c, c, 0)

    time.sleep(5)


def demo_shapes():
    """几何图形绘制测试"""
    disp.init_canvas()
    disp.clear_canvas()
    disp.set_bg_color(0xF5F5F5)

    disp.draw_label(10, 10, "Demo: Shapes", 0x000000, 18)
    disp.label_cn(10, 40, "线段、圆形、矩形", 0x333333)

    disp.draw_line(10, 80, 230, 80, 0xFF0000, 3)
    disp.draw_circle(60, 140, 40, 0x0000FF, 0x000000, 2)
    disp.draw_rect(140, 100, 80, 80, 0x00FF00, 0x000000, 2)

    disp.label_cn(10, 200, "红色线段", 0xFF0000)
    disp.label_cn(10, 230, "蓝色圆形", 0x0000FF)
    disp.label_cn(140, 200, "绿色矩形", 0x00AA00)

    time.sleep(3)


def demo_pendulum():
    """单摆动画 - 增量刷新防闪烁版"""
    disp.init_canvas()
    disp.set_rotation(0)
    disp.clear_canvas()
    disp.set_bg_color(0xFFFFFF)

    disp.draw_label(10, 10, "Demo: Pendulum", 0x000000, 18)
    disp.label_cn(10, 40, "单摆小球动画", 0x333333)

    pivot_x = 120
    pivot_y = 60
    length = 100
    bob_radius = 14
    max_angle = math.pi / 4
    period = 2.0  # 摆动周期2秒
    dt = 0.02     # 帧间隔50FPS

    # 第一帧：创建所有绘图对象
    line_id = disp.draw_line(pivot_x, pivot_y, pivot_x, pivot_y + length, 0x333333, 2)
    bob_id = disp.draw_circle(pivot_x, pivot_y + length, bob_radius, 0xFF3366, 0x333333, 2)
    pivot_id = disp.draw_circle(pivot_x, pivot_y, 4, 0x333333, 0x333333, 0)

    t = 0.0
    frame_count = 0

    while t < 10.0:
        angle = max_angle * math.cos(2 * math.pi * t / period)
        bob_x = int(pivot_x + length * math.sin(angle))
        bob_y = int(pivot_y + length * math.cos(angle))

        # 核心优化：先删除旧线，再画新线，最后移动小球
        # 保证线和球在同一帧内完成更新，杜绝视觉闪烁
        disp.remove(line_id)
        line_id = disp.draw_line(pivot_x, pivot_y, bob_x, bob_y, 0x333333, 2)
        
        try:
            disp.set_pos(bob_id, bob_x - bob_radius, bob_y - bob_radius)
        except TypeError:
            disp.set_pos(bob_id, bob_x - bob_radius)

        # 每10帧更新一次状态（可选，用于调试或显示时间）
        if frame_count % 10 == 0:
            pass 

        t += dt
        frame_count += 1
        time.sleep(dt)

    disp.remove(bob_id)
    disp.remove(line_id)
    disp.remove(pivot_id)


def demo_rotation():
    """旋转测试 - 放在最后执行"""
    for rotation in (0, 90, 180, 270):
        disp.init_canvas()
        disp.set_rotation(rotation)
        disp.clear_canvas()
        disp.set_bg_color(0xFFFFFF)

        disp.draw_label(10, 10, f"Rotation {rotation}", 0x000000, 18)
        disp.label_cn(10, 40, "旋转测试", 0x333333)
        disp.draw_circle(120, 120, 60, 0x0000FF, 0xFF0000, 3)

        time.sleep(2)

    disp.set_rotation(0)


def main():
    demo_basic()
    demo_tv_colorbar()
    demo_shapes()
    demo_pendulum()
    demo_rotation()


main()