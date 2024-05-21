
from pyfirmata import Arduino, util
import time
class ArduinoController:
    def __init__(self, port, sol1_pin=2, sol2_pin=3, 
                 servo_pin=6,
                 ir_pin = 10,
                 estim_pin = 7,
                 spout_charge_pin = 5):
        self.board = Arduino(port)
        it = util.Iterator(self.board)
        it.start()
        
        self.sol1_pin = self.board.get_pin(f'd:{sol1_pin}:o')  # Pin for IN1 as output
        self.sol2_pin = self.board.get_pin(f'd:{sol2_pin}:o')  # Pin for IN2 as output
        self.ir_pin = self.board.get_pin(f'd:{ir_pin}:i')  # IR beam input
        self.estim_pin = self.board.get_pin(f'd:{estim_pin}:i') # ESTIM digital copy from stimulator
        # Setting up a servo on pin 6
        self.servo_pin = self.board.get_pin(f'd:{servo_pin}:o')
        self.board.servo_config(servo_pin)  # Configure pin for servo mode
        self.spout_charge_pin = self.board.get_pin(f'd:{spout_charge_pin}:o')


        self.buzzer_pin = self.board.get_pin('d:11:p')  # 'p' for PWM

    def buzz(self, frequency = 5000, duration = 0.1, volume = 0.05):

        """Generate a tone with a given frequency and duration."""
        period = 1.0 / frequency  # Calculate the period
        half_period = period / 2  # Half period needed for square wave
        
        start_time = time.time()
        while time.time() - start_time < duration:  # Generate tone for the duration
            self.buzzer_pin.write(volume)
            time.sleep(half_period)
            self.buzzer_pin.write(0)
            time.sleep(half_period)

    def move_spout(self, angle):
        self.servo_pin.write(angle)

    def activate_solenoid(self):
        """Activates the solenoid by setting IN1 high and IN2 low."""
        self.sol1_pin.write(1)
        self.sol2_pin.write(0)

    def deactivate_solenoid(self):
        """Deactivates the solenoid by setting both IN1 and IN2 low."""
        self.sol1_pin.write(0)
        self.sol2_pin.write(0)

    def droplet(self, dur):
        """Creates a droplet by activating the solenoid for a specified duration, then deactivates it."""
        self.activate_solenoid()
        self.board.pass_time(dur)
        self.deactivate_solenoid()
    

