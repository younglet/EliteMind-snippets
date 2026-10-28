import em_sensor as sensor
import em_mecanum as mecanum
import time

while True:
    try:
        key= sensor.get_bt_remote(1)  # 非摇杆按键
        print("key:", key)
    except Exception as e:
        pass
    time.sleep_ms(100)