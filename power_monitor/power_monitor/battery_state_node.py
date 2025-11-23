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
            voltage_mv = read_reg(0x000E)

            current_raw = read_reg(0x000F)
            if current_raw >= 0x8000:
                current_raw -= 0x10000

            soc_raw = read_reg(0x0012)
            soc = soc_raw / 10.0

            msg = BatteryState()
            msg.voltage = voltage_mv / 1000.0
            msg.current = current_raw / 1000.0   # A
            msg.percentage = min(soc / 100.0, 1.0)  # 0..1
            msg.present = True

            # msg.design_capacity = 20.0

            self.pub.publish(msg)

            #self.get_logger().info(f"Voltage: {msg.voltage:.3f} V, Current: {msg.current:.3f} A")

            # простое оповещение по порогу 18 В
            if msg.voltage < 18.0:
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
