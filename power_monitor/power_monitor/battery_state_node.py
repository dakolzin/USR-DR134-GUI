import time
import socket

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState

HOST, PORT = "192.168.3.50", 5020  # тот же IP/порт, что в power.py

def crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])

def voltage_to_soc(voltage: float) -> float:
    """
    Приблизительный SOC для 6S Li-ion по напряжению (0..1).
    Таблица точек + линейная интерполяция.
    """
    points = [
        (25.2, 1.00),
        (24.3, 0.90),
        (23.7, 0.80),
        (23.1, 0.70),
        (22.8, 0.60),
        (22.5, 0.50),
        (22.2, 0.40),
        (21.9, 0.30),
        (21.3, 0.20),
        (20.7, 0.10),
        (19.8, 0.00),
    ]

    if voltage >= points[0][0]:
        return 1.0
    if voltage <= points[-1][0]:
        return 0.0

    for i in range(len(points) - 1):
        v1, s1 = points[i]
        v2, s2 = points[i + 1]
        if v1 >= voltage >= v2:
            # линейная интерполяция между v1 и v2
            k = (v1 - voltage) / (v1 - v2)
            return s1 + (s2 - s1) * k

    return 0.0

def make_req(addr: int) -> bytes:
    # slave = 1, func = 0x04, count = 1
    pdu = bytes([
        0x01, 0x04,
        (addr >> 8) & 0xFF, addr & 0xFF,
        0x00, 0x01
    ])
    return pdu + crc16(pdu)

def read_reg(addr: int) -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(2)
    s.connect((HOST, PORT))

    try:
        s.sendall(make_req(addr))
        time.sleep(0.05)
        resp = s.recv(256)
    finally:
        s.close()

    if len(resp) < 5 or (resp[1] & 0x80):
        raise RuntimeError(f"Modbus error for 0x{addr:04X}: {resp.hex(' ').upper()}")

    return (resp[3] << 8) | resp[4]

class BatteryMonitor(Node):
    def __init__(self):
        super().__init__("battery_monitor")
        self.pub = self.create_publisher(BatteryState, "battery_state", 10)
        self.timer = self.create_timer(2.0, self.update)

    def update(self):
        try:
            # Напряжение
            voltage_mv = read_reg(0x000E)
            voltage = voltage_mv / 1000.0

            # Ток
            current_raw = read_reg(0x000F)
            if current_raw >= 0x8000:
                current_raw -= 0x10000
            current_a = current_raw / 1000.0

            # Можем читать сырой SOC, но только для логов (не для процента)
            # soc_raw = read_reg(0x0012)
            # soc_reg = soc_raw / 10.0

            # Оценка SOC по напряжению
            soc_est = voltage_to_soc(voltage)  # 0..1

            msg = BatteryState()
            msg.voltage = voltage
            msg.current = current_a
            msg.percentage = soc_est       # <-- используем только по напряжению
            msg.present = True

            self.pub.publish(msg)

            # можно логировать, если нужно
            # self.get_logger().info(
            #     f"U={voltage:.3f} V, I={current_a:.3f} A, SOC≈{soc_est*100:.1f}%"
            # )

            # порог по напряжению
            if msg.voltage < 21.0:
                self.get_logger().warn(f"LOW BATTERY: {msg.voltage:.2f} V")

        except Exception as e:
            self.get_logger().error(f"Battery read error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = BatteryMonitor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
