import sys
import socket
import select
import pygame
import time

# autopilot
def getDepth():
    global INITDEPTH
    global depthHistory
    # averages the value over the past 5 readings
    depthHistory.append(depthSensor.getDepth())
    if len(depthHistory) > 5:
        depthHistory.pop(0)
    return (sum(depthHistory) / len(depthHistory)) - INITDEPTH

autopilotOn = False
import depthSensor

tmp = []
for _ in range(10):
    tmp.append(depthSensor.getDepth())
    time.sleep(0.05)
INITDEPTH = sum(tmp) / len(tmp) # in cm, intial above water reading
print(tmp)
depthHistory = tmp[-5:] # past 5 readings
del tmp

desiredDepth = 0 # in cm, relative to INITDEPTH

def autopilot():
    currDepth = getDepth()
    deltaDepth = desiredDepth - currDepth


port = '/dev/ttyACM0'

import pyfirmata

#setup pyFirmata
board =  pyfirmata.Arduino(port)

#setup an iterator for safety
iter8 = pyfirmata.util.Iterator(board)
iter8.start()

#locate pins
pin2 = board.get_pin('d:2:s') #motor 2
pin3 = board.get_pin('d:3:s') #motor 3
pin4 = board.get_pin('d:4:s') #motor 4
pin5 = board.get_pin('d:5:s') #motor 5
pin6 = board.get_pin('d:6:s') #motor 6
pin7 = board.get_pin('d:7:s') #motor 7
pin8 = board.get_pin('d:8:s') #motor 8
pin9 = board.get_pin('d:9:s') #motor 9
pin10 = board.get_pin('d:10:s') #motor 10
pin12 = board.get_pin('d:12:s') #motor 12

def move2(a):
    pin2.write(a) # motor

def move3(a):
    pin3.write(a) # motor

def move4(a):
    pin4.write(a) # motor

def move5(a):
    pin5.write(a) # motor

def move6(a):
    pin6.write(a) # vertical thruster

def move7(a):
    pin7.write(a) # vertial thruster

def move8(a):
    pin8.write(a) # claw

def move9(a):
    pin9.write(a)

def move10(a):
    pin10.write(a)

def move12(a):
    pin12.write(a)

trimUp = {
    'left': 0.0,
    'right': 0.0
}

justPressed1 = {
    'A': False, # claw
    'B': False, # claw
    'X': False, # shift
    'Y': False, #
    'LB': False, # trim up
    'RB': False # trim down
}

justPressed2 = {
    'A': False,
    'B': False,
    'X': False,
    'Y': False,
    'LB': False,
    'RB': False
}

def buttonPressed(button, num):
    global trimUp
    if num == 1:
        if button == 'LB':
            trimUp['left'] += 1
            trimUp['right'] += 1
        elif button == 'RB':
            trimUp['left'] -= 1
            trimUp['right'] -= 1

########Multiple clients connect to a server than send and receive data to all clients
def chat_client(host='192.168.1.2', port=9009):
    m10 = 90
    m12 = 0
    global buffer
    if (host == None or port == None):
        if(len(sys.argv) < 3):
            print('Usage: python chat_client.py 192.168.1.__ 9009')
            sys.exit()

        host = sys.argv[1]
        port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    # connect to remote host
    try:
        s.connect((host, port))
    except:
        print('Unable to connect')
        sys.exit()

    print('Connected to remote host. You can start sending messages')
    sys.stdout.write('[Me] '); sys.stdout.flush()

    while True:
        socket_list = [sys.stdin, s]

        # Get the list sockets which are readable
        ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])

        for sock in ready_to_read:
        # print ("sock " +str(sock))
        #print ("s "+str(s))

            if sock == sock:
                data = s.recv(4096)
                print(data)

                if not data:
                    print('\nDisconnected from chat server')
                    sys.exit()
                else:
                    #print data
                    # sys.stdout.write(data)
                    datalist = [float(i) for i in data.split()[2:]]

                    for i in range(len(datalist)):
                        if abs(datalist[i]) < 0.1:
                            datalist[i] = 0.0

                    assert len(datalist) == 24

                    axis = ['xLeft', 'yLeft', 'triggerLeft', 'xRight', 'yRight', 'triggerRight']
                    buttons = ['A', 'B', 'X', 'Y', 'LB', 'RB']

                    joystick1 = dict(zip(axis + buttons, datalist[:12]))
                    joystick2 = dict(zip(axis + buttons, datalist[12:]))

                    global justPressed1, justPressed2

                    for k in joystick1:
                        if k not in buttons:
                            continue
                        v = joystick1[k]
                        if v == 1 and not justPressed1[k]:
                            # just pressed
                            buttonPressed(k, 1)
                            justPressed1[k] = True
                        elif v == 0 and justPressed1[k]:
                            # just released
                            justPressed1[k] = False
                        elif v not in [1, 0]:
                            raise ValueError('Got {0}, expected 0 or 1'.format(v))
                        else:
                            pass

                    for k in joystick2:
                        if k not in buttons:
                            continue
                        v = joystick2[k]
                        if v == 1 and not justPressed2[k]:
                            # just pressed
                            buttonPressed(k, 2)
                            justPressed2[k] = True
                        elif v == 0 and justPressed2[k]:
                            # just released
                            justPressed2[k] = False
                        elif v not in [1, 0]:
                            raise ValueError('Got {0}, expected 0 or 1'.format(v))
                        else:
                            pass

                    motor_claw = 90

                    if joystick1['A'] and joystick1['B']:
                        pass # do nothing cause both are pressed
                    elif joystick1['A']:
                        motor_claw = 150
                    elif joystick1['B']:
                        motor_claw = 30



                    #       150    150
                    #       /a/    \b\
                    #  4  /////    \\\\\  2
                    #
                    #               150
                    #  5  \\\\\    /////  3
                    #      \c\     /d/
                    #      150
                    # ______________a_b_c_d
                    # Back          - - + +
                    # Front         + + - -
                    # Strafe Left   - + - +
                    # Strafe Right  + - + -
                    # Rotate Left   - + + -
                    # Rotate Right  + - - +
                    #

                    yLeft = 60 * joystick1['yLeft']
                    xLeft = 60 * joystick1['xLeft']
                    yRight = 60 * joystick1['yRight']

                    spin = 0

                    joystick1['triggerRight'] = (joystick1['triggerRight'] + 1) / 2

                    joystick1['triggerLeft'] = (joystick1['triggerLeft'] + 1) / 2

                    if joystick1['triggerRight'] >= 0.1 and joystick1['triggerLeft'] >= 0.1:
                        pass # do nothing cause both are pressed
                    else:
                        if joystick1['triggerRight'] > 0.1:
                            # spin right
                            spin = joystick1['triggerRight'] * 60

                        if joystick1['triggerLeft'] > 0.1:
                            # spin left
                            spin = -joystick1['triggerLeft'] * 60


                    motor_a = 90 + yLeft - xLeft - spin

                    motor_b = 90 + yLeft + xLeft + spin

                    motor_c = 90 - yLeft + xLeft - spin

                    motor_d = 90 - yLeft - xLeft + spin

                    #mixing
                    #m1 = 90+forwardval+strafeval+turnval
                    #m2 = 90+forwardval-strafeval-turnval
                    #m3 = 90-forwardval+strafeval
                    #m4 = 90-forwardval-strafeval

                    global trimUp

                    motor_up_left  = 93 + trimUp['left'] + yRight
                    motor_up_right = 93 + trimUp['right'] + yRight

                    def bounds(x):
                        if x < 30:
                            return 30
                        if x > 150:
                            return 150
                        return x

                    motor_a = bounds(motor_a)
                    motor_b = bounds(motor_b)
                    motor_c = bounds(180 - motor_c) # reverse
                    motor_d = bounds(motor_d)

                    motor_up_left  = bounds(motor_up_left)
                    motor_up_right = bounds(motor_up_right)


                    # right

                    move4(motor_a)
                    move2(motor_b)
                    move3(motor_c)
                    move5(motor_d)

                    # 150 down up, 30 move up
                    move6(motor_up_right) # stop on 93
                    move7(motor_up_left) # stop on 93

                    move8(motor_claw)








                #print(str(m1) +' '+str(m2)+' '+str(m3)+' '+str(m4)+' '+str(m6)+' '+str(m7)+' '+str(m12)+' '+str(m10))

                # print datalist
                for i in range(30):
                    print '\r\033[A\033[K',

                print('Trim: [{0}, {1}]'.format(trimUp['left'], trimUp['right']))
                print(joystick1)
                print(joystick2)
                print(motor_a, motor_b)
                print(motor_c, motor_d)
                print ''
                print(motor_up_left, motor_up_right)
                print(motor_claw)


                # else:
                # user entered a message
                # s.send(msg)
                # sys.stdout.write (msg + '\n[Me]'); sys.stdout.flush()

if __name__ == "__main__":
    chat_client()
    print('Done')
