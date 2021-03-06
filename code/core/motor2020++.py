#!/usr/bin/env python3.4

from sys import version
if version[0] != '3':
    raise Exception('This is Python3 code')

import webSocketClient
import json


axis = ['xLeft', 'yLeft', 'triggerLeft', 'xRight', 'yRight', 'triggerRight']
buttons = ['A', 'B', 'X', 'Y', 'LB', 'RB']

PORT = '/dev/ttyACM0'

trimUp = {
    'left': 0.0,
    'right': 0.0
}

justPressed = [
    {
        'A': False,
        'B': False,
        'X': False,
        'Y': False,
        'LB': False,
        'RB': False
    },
    {
        'A': False,
        'B': False,
        'X': False,
        'Y': False,
        'LB': False,
        'RB': False
    }
]

emergencyPower = False

currentPower = {
    'left': 93.0,
    'right': 93.0
}

import pyfirmata

#setup pyFirmata
BOARD =  pyfirmata.Arduino(PORT)

#setup an iterator for safety
iter8 = pyfirmata.util.Iterator(BOARD)
iter8.start()

#locate pins
pins = [
    None, # no pin 0
    None, # no pin 1
    BOARD.get_pin('d:2:s'), #motor 2
    BOARD.get_pin('d:3:s'), #motor 3
    BOARD.get_pin('d:4:s'), #motor 4
    BOARD.get_pin('d:5:s'), #motor 5
    BOARD.get_pin('d:6:s'), #motor 6 - vertical thruster
    BOARD.get_pin('d:7:s'), #motor 7 - vertical thruster
    BOARD.get_pin('d:8:s'), #motor 8 - claw
    BOARD.get_pin('d:9:s'), #motor 9
    BOARD.get_pin('d:10:s'), #motor 10
    None, # no pin 11
    BOARD.get_pin('d:12:s'), #motor 12
]

# example: pins[8].write(150)

def buttonPressed(button, num):
    global trimUp, emergencyPower
    # num is zero or one
    if num == 0:
        if button == 'LB':
            trimUp['left'] += 1
            trimUp['right'] += 1
        elif button == 'RB':
            trimUp['left'] -= 1
            trimUp['right'] -= 1
        elif button == 'X':
            emergencyPower = True
        elif button == 'Y':
            emergencyPower = False


def process(data):
    global emergencyPower, justPressed

    joysticks = json.loads(data)
    assert len(joysticks) == 24

    joystick1 = dict(zip(axis + buttons, joysticks[:12]))
    joystick2 = dict(zip(axis + buttons, joysticks[12:]))

    old = [] # for debugging

    del data

    stickNum = 0
    for stick, jPressed in zip((joystick1, joystick2), justPressed):
        for k in stick:
            if k not in buttons:
                continue

            v = stick[k]
            if v == 1 and not jPressed[k]:
                # just pressed
                buttonPressed(k, stickNum)
                jPressed[k] = True
            elif v == 0 and jPressed[k]:
                # just released
                jPressed[k] = False
            elif v not in [1, 0]:
                raise ValueError('Got {0}, expected 0 or 1'.format(v))
            else:
                pass

        stickNum += 1

    del stickNum

    motor_claw = 90

    #print(joystick1)
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
    #      \d\     /c/
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
    xLeft = 60 * joystick1['xLeft'] # should be strafe
    yRight = 60 * joystick1['yRight']

    spin = 0

    joystick1['triggerRight'] = (joystick1['triggerRight'] + 1) / 2
    joystick1['triggerLeft'] = (joystick1['triggerLeft'] + 1) / 2

    joystick2['triggerRight'] = (joystick2['triggerRight'] + 1) / 2
    joystick2['triggerLeft'] = (joystick2['triggerLeft'] + 1) / 2

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

    neutral_up = 93
    motor_up_left  = neutral_up - (trimUp['left'] + yRight)
    motor_up_right = neutral_up - (trimUp['right'] + yRight) # thrusters reversed

    def bounds(x):
        if x < 30:
            return 30
        if x > 150:
            return 150
        return round(x, 3)

    def specialBounds(x):
        if x < 20:
            return 20
        if x > 210:
            return 210
        return round(x, 3)

    motor_a = bounds(motor_a)
    motor_b = bounds(motor_b)
    motor_c = bounds(180 - motor_c) # reverse # de reverse
    motor_d = bounds(motor_d)

    motor_up_left  = specialBounds(motor_up_left)
    motor_up_right = specialBounds(motor_up_right)

    step = 5

    if emergencyPower:
        currentPower['left'] = motor_up_left
        currentPower['right'] = motor_up_right
    else:
        if neutral_up == motor_up_left:
            currentPower['left'] = motor_up_left
        else:
            if currentPower['left'] < motor_up_left: # less than desired
                currentPower['left'] += step
                if currentPower['left'] > motor_up_left:
                    currentPower['left'] = motor_up_left

            if currentPower['left'] > motor_up_left: # more than desired
                currentPower['left'] -= step
                if currentPower['left'] < motor_up_left:
                    currentPower['left'] = motor_up_left
        
        if neutral_up == motor_up_right:
            currentPower['right'] = motor_up_right
        else:
            if currentPower['right'] < motor_up_right: # less than desired
                currentPower['right'] += step
                if currentPower['right'] > motor_up_right:
                    currentPower['right'] = motor_up_right

            if currentPower['right'] > motor_up_right: # more than desired
                currentPower['right'] -= step
                if currentPower['right'] < motor_up_right:
                    currentPower['right'] = motor_up_right

    #'''
    # right
    pins[4].write(motor_a)
    pins[2].write(motor_b)
    pins[3].write(motor_c)
    pins[5].write(motor_d)

    # 150 down up, 30 move up
    pins[6].write(currentPower['right'])  #motor_up_right) # stop on 93
    pins[7].write(currentPower['left'])  #motor_up_left) # stop on 93

    pins[8].write(motor_claw)
    #'''

    # print datalist
    for i in range(30):
        print('\r\033[A\033[K', end='')

    print('Trim: [{0}, {1}]'.format(trimUp['left'], trimUp['right']))
    print(joystick1)
    print(joystick2)
    print(motor_a, motor_b)
    print(180-motor_c, motor_d)
    print()
    print(currentPower['left'], currentPower['right'])
    print(motor_claw)
    #global emergencyPower
    if emergencyPower:
        print('-----------------------')
        print('-- MAX POWER ENABLED --')
        print('-----------------------')

    index = 0
    for i in old:
        print(index, i)
        index += 1

webSocketClient.start('motor', process, ip="192.168.1.2")
