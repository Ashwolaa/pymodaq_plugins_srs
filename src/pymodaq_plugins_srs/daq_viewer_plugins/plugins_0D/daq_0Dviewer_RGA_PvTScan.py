import numpy as np

from pymodaq_utils.utils import ThreadCommand
from pymodaq_data.data import DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins

from pymodaq_plugins_srs.hardware.wrapper import RGAWrapper

class DAQ_0DViewer_RGA_PvTScan(DAQ_Viewer_base):
    """ Instrument plugin class for a OD viewer.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Viewer module through inheritance via
    DAQ_Viewer_base. It makes a bridge between the DAQ_Viewer module and the Python wrapper of a particular instrument.

    TODO Complete the docstring of your plugin with:
        * The set of instruments that should be compatible with this instrument plugin.
        * With which instrument it has actually been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    # TODO add your particular attributes here if any

    """
    params = comon_parameters+[
        {'title': 'COM:', 'name': 'com_port', 'type': 'list',
         'limits': RGAWrapper.get_available_ports()},        
        {'title': 'Filament:', 'name': 'filament', 'type': 'float', 'value': 0,
         'default': 0, 'min': 0, 'max': 3.5,},        
        {'title': 'CEM:', 'name': 'cem', 'type': 'float', 'value': 0,
         'default': 0, 'min': 0, 'max': 2000,},      
        {'title': 'Scan Speed:', 'name': 'scan_speed', 'type': 'int', 'value': 0,
         'default': 3, 'min': 0, 'max': 9,},
        {'title': 'Units:', 'name': 'units', 'type': 'list', 'limits': ['fA', 'torr']},
        {'title': 'Scan resolution (steps per amu):', 'name': 'scan_resolution', 'type': 'float', 'value': 0,
         'default': 10, 'min': 10, 'max': 25,}, # UH
        {'title': 'Masses to measure:', 'name': 'masses_to_measure', 'type': 'str', 'value': '2, 18, 44',
         'tip': 'Enter masses separated by commas (e.g. 2, 18, 44). Max mass: 300',},    # UH  
        ]

    def ini_attributes(self):
        self.controller: RGAWrapper = None

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        
        if param.name() == "filament":
           self.controller.ionizer.emission_current = param.value()  
        elif param.name() == "cem":
           self.controller.cem.voltage = param.value() 
        elif param.name() == "scan_speed":
           self.controller.scan.scan.speed = param.value()  
        elif param.name() == "scan_resolution":
           self.controller.scan.resolution = param.value() # UH
        elif param.name() == "masses_to_measure":
           if hasattr(self, 'controller') and self.controller is not None:               
               self.masses_to_measure = self.get_masses_to_measure()  # Update the masses_to_measure attribute with the new value
        elif param.name() == "units":
            self.conversion_factor = self.get_conversion_factor()
            
            #    try:
            #     raw_value = param.value()
            #     parsed_masses = [int(m.strip()) for m in raw_value.split(',') if m.strip()]
            #     max_allowed = 300
            #     mass_list = [m for m in parsed_masses if m <= max_allowed]
                
            #     if len(mass_list) < len(parsed_masses):
            #         discarded = [m for m in parsed_masses if m > max_allowed]
            #         print(f"Warning: The following masses were discarded (Max {max_allowed}): {discarded}")

            #     # self.controller.scan.masses_to_measure = mass_list
            #    except ValueError:
            #     print("Error: Please enter a valid list of numbers separated by commas.")
    def get_conversion_factor(self):
        self.selected_unit = self.settings.child('units').value()
        if self.selected_unit == 'fA':
            return 0.1
        elif self.selected_unit == 'torr':
            return self.controller.pressure.get_partial_pressure_sensitivity_in_torr()
        else:
            raise ValueError(f"Unsupported unit: {self.selected_unit}")

    def get_masses_to_measure(self):
        mass_list = []
        try:
            param_masses = self.settings.child('masses_to_measure').value()
            parsed_masses = [int(m.strip()) for m in param_masses.split(',') if m.strip()]
            max_allowed = 300
            mass_list = [m for m in parsed_masses if m <= max_allowed]
            
            if len(mass_list) < len(parsed_masses):
                discarded = [m for m in parsed_masses if m > max_allowed]
                print(f"Warning: The following masses were discarded (Max {max_allowed}): {discarded}")        
        except ValueError:
                print("Error: Please enter a valid list of numbers separated by commas.")            

        return mass_list

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        self.ini_detector_init(controller)  
        if self.is_master:
            self.controller = RGAWrapper(port=self.settings.child('com_port').value()) 
            # self.controller.filament.turn_on() 

            # self.controller.open_communication() # call eventual methods
            initialized = self.controller.is_connected() 
        else:
            self.controller = controller
            initialized = True

        self.dte_signal_temp.emit(DataToExport(name='Scan pressure RGA',
                                               data=[DataFromPlugins(name='Masses',
                                                                    data=[np.array([0]), np.array([0])], # UH
                                                                    dim='Data0D',
                                                                    labels=['2', '4'])]))
        self.masses_to_measure = self.get_masses_to_measure()  # Update the masses_to_measure attribute with the new value
        self.conversion_factor = self.get_conversion_factor()  # Update the conversion factor based on the selected unit
        info = "PvT Scan RGA"
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        self.controller.filament.turn_off()
        self.controller.cem.voltage = 0
        if self.is_master:
            self.controller.disconnect()

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        masses_of_choice = self.masses_to_measure
        names = [f'{mass} amu' for mass in masses_of_choice]
        data_tot = self.controller.scan.get_multiple_mass_scan(masses_of_choice)
        data_tot *= self.conversion_factor

        data_channels = []
        for i, name in enumerate(names):
            data_channels.append(np.array([data_tot[i]]))

        self.dte_signal.emit(
            DataToExport(name='PvT Scan RGA',
                        data=[
                            DataFromPlugins(name=self.selected_unit,
                                            data=data_channels,
                                            dim='Data0D',
                                            labels=names)
                            ]))


    def callback(self):
        """optional asynchrone method called when the detector has finished its acquisition of data"""
        data_tot = self.controller.your_method_to_get_data_from_buffer()
        self.dte_signal.emit(DataToExport(name='PvT Scan RGA',
                                          data=[DataFromPlugins(name='Callback', data=data_tot,
                                                                dim='Data0D', labels=['dat0', 'data1'])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        # self.controller.stop()  
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))
        return ''


if __name__ == '__main__':
    main(__file__)
