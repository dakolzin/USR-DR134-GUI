from setuptools import find_packages, setup

package_name = 'power_monitor'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/battery_monitor.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='dood',
    maintainer_email='podkolzindanil@yandex.ru',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'battery_state_node = power_monitor.battery_state_node:main',
            'battery_tui = power_monitor.battery_tui:main',
        ],
    },
)
