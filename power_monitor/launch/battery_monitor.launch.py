from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        
        # Нода чтения батареи (Modbus over TCP)
        Node(
            package="power_monitor",
            executable="battery_state_node",
            name="battery_state_node",
            output="screen"
        ),

        # Интерфейс (TUI) зарядки
        Node(
            package="power_monitor",
            executable="battery_tui",
            name="battery_tui",
            output="screen"
        )
    ])
