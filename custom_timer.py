class Timer:
    def __init__(self):
        self.reset()
    def reset(self):
        self.time = 0
        self.running = False
    def start(self):
        self.running = True
    def update(self, dt):
        if self.running:
            self.time += dt 