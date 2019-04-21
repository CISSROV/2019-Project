
# pip3 install ms5803py
# sudo apt-get install -y python-smbus
# sudo apt-get install -y i2c-tools

# python2

import ms5803py
import time

s = ms5803py.Sensor()
surface = 0 # 1007   # 1013.25 mBar

surface = getDepth()

def getDepth():
    ave_pressure = 0.0
    ave_temp = 0.0
    ave_depth = 0.0
    for i in range(30):
        press, temp = s.read()
        press = press * 10.0
        rho = 1000*(1 - (temp+288.9414)/(508929.2*(temp+68.12963))*(temp-3.9863)**2)  #freshwater density
        depth =  (1000*( (100.0*(press-surface)) / (rho*9.81) ))
        ave_pressure += press
        ave_temp += temp
        ave_depth += depth
        time.sleep(0.03)
    #print("pressure=%6.2f mBar, temp=%4.2f C, depth=%4.1f cm"% (ave_pressure/30.0, ave_temp/30.0, ave_depth/30.0))
    return ave_depth/30.0
