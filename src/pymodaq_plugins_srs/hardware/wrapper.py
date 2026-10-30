from srsinst.rga import RGA100
from serial.tools.list_ports import comports
import platform

os_name = platform.system()
if os_name == "Windows":
    print("Running on Windows")
elif os_name == "Linux":
    print("Running on Linux")
else:
    print(f"Running on {os_name}")

class RGAWrapper(RGA100):
    def __init__(self, port, baud_rate=28800, *args, **kwargs):
        super().__init__('serial', port, baud_rate, True, *args, **kwargs)

    def get_available_ports():
        """
        Returns a list of available COM ports.
        """
        ports = comports()
        if os_name == "Windows":
            return [comport.name for comport in ports]

        elif os_name == "Linux":            
            return [port.device for port in ports if 'ttyUSB' in port.device]


# R = RGAWrapper("/dev/ttyUSB0")
# R = RGAWrapper("/dev/srs_rga100")

# R.disconnect()