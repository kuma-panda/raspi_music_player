import RPi.GPIO as GPIO
import time
import threading
import queue

# class GPIOPin:
#     def __init__(self, port):
#         self.__port = port
#         self.__dt = time.time()
#         GPIO.setup(self.__port, GPIO.IN, GPIO.PUD_UP)
#         self.__stat = GPIO.input(self.__port)

#     def get(self):
#         stat = GPIO.input(self.__port)
#         dt = time.time()
#         if stat != self.__stat and dt > self.__dt + 0.01:
#             self.__stat = stat
#             self.__dt = dt
#         return self.__stat        

# ------------------------------------------------------------------------------
class Encoder:
    def __init__(self, pin_a, pin_b):
        self.__pin = {
            'ccw': pin_a,
            'cw' : pin_b
        }
        GPIO.setup(pin_a, GPIO.IN)
        GPIO.setup(pin_b, GPIO.IN)
        self.__state = {
            'ccw': GPIO.input(pin_a),
            'cw' : GPIO.input(pin_b)
        }
        self.__queue = queue.Queue()
        self.__terminated = False
        self.__thread = threading.Thread(target=self.update)
        self.__thread.start()
    
    def quit(self):
        self.__terminated = True
        self.__thread.join()
        print('Encoder: terminate')
        
    def get(self):
        return self.__queue.get() if not self.__queue.empty() else None

    def update(self):
        while not self.__terminated:
            for name, pin in self.__pin.items():
                s = GPIO.input(pin)
                if self.__state[name] != s:
                    self.__queue.put(name)
                    self.__state[name] = s
            time.sleep(0.01)

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    enc = Encoder(17, 27)
    try:
        while True:
            s = enc.get()
            if s:
                print(s)
            time.sleep(0.01)
    except KeyboardInterrupt:
        enc.quit()
        GPIO.cleanup()
