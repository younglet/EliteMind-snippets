# EliteMind-snippets

EliteMind (ESP32-S3) 设备的 Python 示例代码合集（MicroPython / `em_*` 模块）。

## 目录

```
EliteMind_snippets/
├── demo/     # 官方示例
│   ├── demo_dsiplay.py     # 屏幕显示：画布、颜色、文字、中文
│   ├── demo_follow_face.py # 人脸跟随：视觉 + 麦轮
│   ├── demo_gripper.py     # 夹爪开合
│   ├── demo_led.py         # LED 灯带 / 灯效
│   ├── demo_mecanum_rc.py  # 麦轮遥控小车 + 夹爪 + 转向灯
│   └── demo_movement.py    # 四轮电机运动
└── debug/    # 调试脚本
    └── debug_btremote_key.py # 读取蓝牙遥控器按键
```

## 上传到设备

USB 直连电脑后，mpremote 会自动识别设备，把 `demo/` 和 `debug/` 下所有 `.py` 传到设备根目录 `/`：

```bash
mpremote cp -r demo/* debug/* :
```

没被自动识别时，指定端口再传：

```bash
mpremote connect COMxx cp -r demo/* debug/* :
```

> `demo/*`、`debug/*` 由 shell 展开：Git Bash / WSL / Linux / macOS 可直接用；
> cmd 不支持通配符，用
> `for %f in (demo\*.py debug\*.py) do mpremote cp -r %f :`
