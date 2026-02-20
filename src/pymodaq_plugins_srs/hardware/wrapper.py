from srsinst.rga import RGA100
from serial.tools.list_ports import comports

class RGAWrapper(RGA100):
    def __init__(self, port, baud_rate=28800, *args, **kwargs):        
        super().__init__('serial', port, baud_rate, *args, **kwargs)

    def get_available_ports():
        """
        Returns a list of available COM ports.
        """
        return [comport.name for comport in comports()]