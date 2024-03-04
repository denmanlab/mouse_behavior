from pyfirmata import ArduinoMega, util, INPUT, SERVO, OUTPUT
class ArduinoController():
    def __init__(self,board_string,horizontal=0,vertical=1,digital_channels=[53,51,49,47,45,43],food_reward_pin=8):
        self.board =  ArduinoMega(board_string)
        self.horizontal_channel = horizontal
        self.vertical_channel = vertical
        self.digital_channels = digital_channels
        self.food_reward_pin = food_reward_pin
        self.water_reward_pin = 7
        self.lick_opto_pin_low_when_licked = 31
        self.lick_opto_pin_high_when_licked = 35
        self.lick_opto_pin = self.lick_opto_pin_low_when_licked

        #set up reward delivery====================================================================
        # try:
        import sys
        sys.path.append('C:\github\syringe_pump') # https://github.com/dougollerenshaw/syringe_pump
        from stepper import Stepper
        self.s = Stepper(mode='arduino',port='COM4',syringe='3mL',board=self .board)
        # s.enable()
        # except:
        #     print("Error:", sys.exc_info()[0])
        #     print('WARNING: no reward hardware set up')
        REWARD_VOLUME=50#in µL
        REWARD_WINDOW=0.5#in seconds

        self.init()

    def init(self):
        it = util.Iterator(self.board)
        it.start()
        self.board.analog[self.horizontal_channel].enable_reporting()#horizontal
        self.board.analog[self.vertical_channel].enable_reporting()#vertical

        # for channel in self.digital_channels:
        #     self.board.digital[channel].mode=INPUT

        #set up servo motor ouput
        # set up pin D9 as Servo Output
        self.reward_food_pin = self.board.digital[self.food_reward_pin]
        self.reward_food_pin.mode = SERVO
  
        self.board.digital[self.water_reward_pin].mode=OUTPUT
        self.board.digital[43].mode=OUTPUT
        self.board.digital[44].mode=OUTPUT

        self.board.digital[self.lick_opto_pin_low_when_licked].mode=INPUT
        self.board.digital[self.lick_opto_pin_high_when_licked].mode=INPUT
        # self.board.analog[self.].enable_reporting()


    # joystick 
    def start_joystick(self):
        #make an infinite loop
        print('ready to listen to joystick')
        while True:
            pass
            h = self.board.analog[0].read()
            v = self.board.analog[1].read()
            if h == None or v==None :pass
            else:
                if h < 0.4: #went left
                    self.left()
                if h > 0.6: #went right
                    self.right()
                if v < 0.4: #went up
                    self.up()
                if v > 0.6: #went down
                    self.down()


    # reward spout motor
    def move_spout(self,a):
        self.reward_food_pin.write(a)


    #reward delivery motor

    def button_state(self,channel):
        return self.board.digital[channel].read()
        #     print('down')
        # if self.board.digital[channel].read():
        #     print('up')

    def left(self):
        print('left')
    def right(self):
        print('right')
    def up(self):
        print('up')
    def down(self):
        print('down')
#==============================