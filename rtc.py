import smbus
import threading
import datetime
import time

class RTC:
    I2C_CHAN   = 1
    I2C_ADDR   = 0x51
    REG_SECOND = 0x04
    REG_MINUTE = 0x05
    REG_HOUR   = 0x06
    REG_DAY    = 0x07
    REG_WEEK   = 0x08   # 日曜日が0、土曜日が6
    REG_MONTH  = 0x09
    REG_YEAR   = 0x0A

    def __init__(self):
        self.__bus = smbus.SMBus(RTC.I2C_CHAN)
        self.__lock = threading.Lock()
        self.__time = datetime.datetime.now()
        
        self.__thread = threading.Thread(target=self.update)
        self.__terminated = False
        self.__thread.start()

    def quit(self):
        self.__terminated = True
        self.__thread.join()
        print('RTC: terminate')

    @property
    def time(self):
        self.__lock.acquire()
        t = self.__time
        self.__lock.release()
        return t

    def update(self):
        tick = 0
        while not self.__terminated:
            time.sleep(0.1)
            tick += 1
            if tick < 5:
                continue
            r = [int('{:02x}'.format(r)) for r in self.__bus.read_i2c_block_data(RTC.I2C_ADDR, RTC.REG_SECOND, 7)]
            self.__lock.acquire()
            self.__time = datetime.datetime(2000+r[6], r[5], r[3], r[2], r[1], r[0])
            self.__lock.release()            
            tick = 0

if __name__ == '__main__':
    rtc = RTC()
    time.sleep(2)
    print('{:%Y/%m/%d %H:%M:%S}'.format(rtc.time))
    rtc.quit()
