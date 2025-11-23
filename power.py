import socket, time

HOST, PORT = "192.168.3.50", 5020

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])

def make_req(addr):
    # slave=1, func=0x04, count=1
    pdu = bytes([0x01, 0x04,
                 (addr >> 8) & 0xFF, addr & 0xFF,
                 0x00, 0x01])
    return pdu + crc16(pdu)

def read_reg(addr):
    with socket.create_connection((HOST, PORT), timeout=2) as s:
        s.sendall(make_req(addr))
        time.sleep(0.05)
        resp = s.recv(256)
    if len(resp) < 5 or (resp[1] & 0x80):
        raise RuntimeError(f"Modbus error for 0x{addr:04X}: {resp.hex(' ').upper()}")
    return (resp[3] << 8) | resp[4]

# Напряжение (0x000E, mV)
voltage_mv = read_reg(0x000E)

# Ток (0x000F, mA, знаковый)
current_raw = read_reg(0x000F)
if current_raw >= 0x8000:
    current_raw -= 0x10000

# SOC (0x0012, 0.1 %)
soc_raw = read_reg(0x0012)
soc = soc_raw / 10.0

# Остаточная ёмкость (0x0013, mAh) — может быть 0xFFFF
rem_raw = read_reg(0x0013)
remaining_str = f"{rem_raw} mAh" if rem_raw != 0xFFFF else "n/a"

print(f"Voltage: {voltage_mv / 1000:.3f} V")
print(f"Current: {current_raw} mA")
print(f"SOC raw: {soc_raw}  -> {soc:.1f} %")
print(f"Remaining capacity: {remaining_str}")
