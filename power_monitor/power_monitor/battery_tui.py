import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState

BAR_WIDTH = 30

def make_bar(perc: float) -> str:
    p = max(0.0, min(1.0, perc))
    filled = int(p * BAR_WIDTH)
    empty = BAR_WIDTH - filled
    return "[" + "#" * filled + "-" * empty + "]"

class BatteryTUI(Node):
    def __init__(self):
        super().__init__("battery_tui")
        self.sub = self.create_subscription(
            BatteryState,
            "battery_state",
            self.cb,
            10
        )
        self.last_msg = None
        self.timer = self.create_timer(1.0, self.redraw)

    def cb(self, msg: BatteryState):
        self.last_msg = msg

    def redraw(self):
        if self.last_msg is None:
            return

        v = self.last_msg.voltage
        i = self.last_msg.current
        perc = self.last_msg.percentage  # 0..1
        bar = make_bar(perc)
        p100 = perc * 100.0

        if p100 >= 50:
            color = "\033[92m"   # зелёный
        elif p100 >= 20:
            color = "\033[93m"   # жёлтый
        else:
            color = "\033[91m"   # красный
        reset = "\033[0m"

        print(
            f"{color}{bar} {p100:5.1f}%  "
            f"U={v:5.2f} V  I={i:6.3f} A{reset}",
            flush=True
        )

def main(args=None):
    rclpy.init(args=args)
    node = BatteryTUI()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
