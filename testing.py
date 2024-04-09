from pyfirmata import Arduino, util
import time

# Specify the port and board model
port = 'COM10'
board = Arduino(port)

# Start an iterator thread so that serial buffer doesn't overflow
it = util.Iterator(board)
it.start()

# Define the digital pin to be read (digital pin 10 in this case)
pin = board.get_pin('d:10:i')  # d for digital, 10 for pin number, i for input

try:
    while True:
        pin_value = pin.read()  # Read the pin value
        if pin_value is not None:
            print(f"Pin 10 value: {'HIGH' if pin_value else 'LOW'}")
        else:
            print("Reading error or pin not initialized")
        
        time.sleep(1)  # Wait for 1 second before the next read

except KeyboardInterrupt:
    # Clean up and close the connection on Ctrl+C
    print("Exiting...")
    board.exit()