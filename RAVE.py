#!/bin/python

import os
import codecs
import tempfile
import time
import struct
import sys
import signal
import time
import traceback
import threading
import math
import numpy as np
import statistics
import serial
from scipy.signal import butter, lfilter, freqz

milli_time = lambda: int(round(time.time() * 1000))


import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *


ser = serial.Serial("/dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00", 9600, timeout = 1)


enerd = 1


def ser_write():
    global enerd 
    while True:
    
        inp = ser.readline()

        if inp == b'x\r\n':
            print("Got magic bytes, sending...")
        else:
            continue
        

        print("Enerd: "+str(enerd))

        if (enerd > 1):
            enerd = 1


        out = int(enerd*255)
        print("RAW SAUCE: "+str(out))

        out = out.to_bytes(1, 'little')
        ser.write(out)
        print("Wrote to ser: "+str(out))
        

    return



#pygame.init()
maxx = 1024
maxy = 1024
#screen = pygame.display.set_mode((maxx, maxy))

x = 0
y = 0

fifo = open("/tmp/mpd.fifo", "rb")

#clock = pygame.time.Clock()

running = True

def input(events): 
    for event in events: 
        if event.type == pygame.QUIT: 
            running = False
        else: 
            #print(event)
            pass


def SHUTITDOWN():
    pygame.display.quit()
    ser.close()
    traceback.print_exc(file=sys.stdout)
    os.kill(os.getpid(), signal.SIGKILL)


end = 0

normies = [] 
rawxd = []
peaks = []

for i in range(0, maxx+1):
    normies.append(0)
    rawxd.append(0)
    peaks.append(0)


def clout_getter():
    while True:
        for i in range(0, maxx-1):
            #num = fifo.read(2)
            num = fifo.read(2)
            value = int.from_bytes(num, byteorder="little", signed=True)
            rawxd[i] = value

            #print(value)

            # Min Max Normalisation
            value = (value+32767)/(65535)
            value = value*maxy

            value = int(value)


            if value > maxy or value < 0:
                value = 254*maxy
            normies[i] = value

def possed_m(data):
    total = 0
    count = 0
    for i in data:
        total = total+abs(i)
        count = count+1

    total = total/count

    return total/32768 # Taking absolute value of signed int16 means
                       # we won't exceed more than half


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


def max(data): #TODO: FINISH
    pass

def thresholding_algo(y, lag, threshold, influence):
    signals = np.zeros(len(y), dtype=np.int8)
    filteredY = np.array(y)
    avgFilter = [0]*len(y)
    stdFilter = [0]*len(y)
    avgFilter[lag - 1] = np.mean(y[0:lag])
    stdFilter[lag - 1] = np.std(y[0:lag])
    for i in range(lag, len(y)):
        if abs(y[i] - avgFilter[i-1]) > threshold * stdFilter [i-1]:
            if y[i] > avgFilter[i-1]:
                signals[i] = 1
            else:
                signals[i] = -1

            filteredY[i] = influence * y[i] + (1 - influence) * filteredY[i-1]
            avgFilter[i] = np.mean(filteredY[(i-lag):i])
            stdFilter[i] = np.std(filteredY[(i-lag):i])
        else:
            signals[i] = 0
            ilteredY[i] = y[i]
            avgFilter[i] = np.mean(filteredY[(i-lag):i])
            stdFilter[i] = np.std(filteredY[(i-lag):i])

    return np.asarray(signals)

def big_peak(data, x):
    std = statistics.stdev(data)
    mean = statistics.mean(data)

    #print("The mean: "+str(mean))
    #print("Us: "+str(data[-1]))
    if data[x] > std*2+mean:
        return 1
    return 0



def last_x(array, pos, x):
    
    length = len(array)

    start = pos-x
    if start < 0:
        start = 0
    out = array[start:pos]

    remain = x-len(out)
    if remain > 0:
        start = length-remain
        out = array[start:length] + out 

    return out

def peak_anal(data):
    # Peak anal
    amount = 1
    total = 0
    last_pos = 0
    pos = 0
    for peak in data:
        pos += 1
        if peak is 1:
            amount += 1
            total += (pos-last_pos)
            last_pos = pos

    avg_peak_dist = total/amount

    return avg_peak_dist
    


get_thread = threading.Thread(target=clout_getter)
ser_thread = threading.Thread(target=ser_write)
get_thread.start()
ser_thread.start()


last_draw = normies


bufsize = maxx
means = []
mpeaks = []
for i in range(0, bufsize*2):
    means.append(0)
    mpeaks.append(0)

order = 6
fs = 44100.0       # sample rate, Hz
cutoff = 500.0  # desired cutoff frequency of the filter, Hz

threshold = 8
lag = 2
influence = 0.8



colors = (
    (1,0,0),
    (0,1,0),
    (0,0,1),
    (0,1,0),
    (1,1,1),
    (0,1,1),
    (1,0,0),
    (0,1,0),
    (0,0,1),
    (1,0,0),
    (1,1,1),
    (0,1,1),
    )

surfaces = (
    (0,1,2,3),
    (3,2,7,6),
    (6,7,5,4),
    (4,5,1,0),
    (1,5,7,2),
    (4,0,3,6)
    )


verticies = (
    (1, -1, -1),
    (1, 1, -1),
    (-1, 1, -1),
    (-1, -1, -1),
    (1, -1, 1),
    (1, 1, 1),
    (-1, -1, 1),
    (-1, 1, 1)
    )

edges = (
    (0,1),
    (0,3),
    (0,4),
    (2,1),
    (2,3),
    (2,7),
    (6,3),
    (6,4),
    (6,7),
    (5,1),
    (5,4),
    (5,7)
    )


def Cube(x, y, z, s):
    
    if s == 0.0:
        s = 1
    
    
#    glBegin(GL_QUADS)
#    for surface in surfaces:
#        x = 0
#        for vertex in surface:
#            x+=1
#            glColor3fv(colors[x])
#            nu = verticies[vertex]
#            nu = (nu[0]*s+x, nu[1]*s+y, nu[2]*s+z)
#            glVertex3fv(nu)
#    glEnd()
    
    
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            nu = verticies[vertex]
            nu = (nu[0]*s+x, nu[1]*s+y, nu[2]*s+z)
            glVertex3fv(nu)
    glEnd()


pygame.init()
display = (1366,768)
pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)

glTranslatef(0.0,0.0, -5)





bs = 0
try:
    while running is True:
 #       if (milli_time() - end < 16):
 #           continue
        
        bs = bs+1
        if bs > bufsize-2:
            bs = 0
        
 #       screen.fill((0,0,0))
    
        input(pygame.event.get()) 


        #nshot = np.fft.fft(normies)
        nshot = np.array(normies)
        lshot = butter_lowpass_filter(nshot, cutoff, fs, order)
        mean = int(maxy/2-(possed_m(rawxd))*(maxy/2))
        enerd = possed_m(rawxd)*2
        #print("Mean: "+str(possed_m(rawxd)/32767))
        means[bs] = enerd
        #print("Enerd: "+str(possed_m(rawxd)/32767))

       
        hot = big_peak(means, bs)

        #print("Hot?: "+str(hot))
    

        # THE MAGIC
        glRotatef(1, 3, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        if hot is 0:
            Cube(0, 0, 0, enerd)
        else:
            Cube(+1, -1, 0, enerd)
            Cube(-1, -1, 0, enerd)
            Cube(+1, +1, 0, enerd)
            Cube(-1, +1, 0, enerd)






        


        #speaks = thresholding_algo(lshot, lag, threshold, influence)
        #
        #print(speaks)

        color = (50, 50, 50)
  #      pygame.draw.line(screen, color, (0, mean), (maxx, mean), 1) # Mean line
  #      pygame.draw.line(screen, color, (0, maxy/2), (maxx, maxy/2), 1) # Middle line
        
        
        #print(bs)
        #pygame.draw.line(screen, color, (bs, maxy-maxy/6), (bs, maxy), 1) # Mean BS line
        for pos in range(100, maxx-100):
            if pos%1 is 0:

                spot = int(lshot[pos]) #### USE LIVE DATA FOR DRAW
                last_spot = last_draw[pos]
                
                col = int((spot/maxy)*255)
                if col > 254 or col < 0:
                    continue
                color = (255, col, 0)
                color2 = (255, 0, col)



                #print(spot)


         #       if speaks[pos] != 0:
          #          pygame.draw.circle(screen, (255, 255, 255), (pos,  int(maxy-means[pos])), 2)
           #         print(speaks[pos])


                # Shit unfiltered peak detection
                #if lshot[pos] > lshot[pos-1] and lshot[pos] > lshot[pos+1] or \
                #   lshot[pos] < lshot[pos-1] and lshot[pos] < lshot[pos+1]:
                #    peaks[pos] = 1
                #else:
                #    peaks[pos] = 0

                # Same shit on the means
                #if means[pos] > means[pos-1] and means[pos] > means[pos+1] or \
                #   means[pos] < means[pos-1] and means[pos] < means[pos+1]:
                #    mpeaks[pos] = 1
                #else:
                #    mpeaks[pos] = 0



            #    if big_peak(means[pos-100]) is 1:
            #        pygame.draw.circle(screen, (255, 255, 255), (pos,  int(maxy-means[pos])), 2)


                spot = int(spot)

                #dist = math.sqrt(pow(spot-last_draw[pos-1], 2))
                #if dist > maxy/2:
                #    continue

                #pygame.draw.circle(screen, color, (pos, spot), 1, 1)
                if pos > 1:
   #                 pygame.draw.line(screen, color, (pos-1, nshot[pos-1]), (pos, nshot[pos]), 1) # FREQLINE
   #                 pygame.draw.line(screen, color2, (pos-1, last_draw[pos-1]), (pos, spot), 1) # BASSLINE
                    color = (255, 0, int(abs(means[pos])/(maxy/6)*255))
   #                 pygame.draw.line(screen, color, (pos-1, maxy-+means[pos-1]), (pos, maxy-+means[pos]), 1) # MEANLINE

    

                last_draw[pos] = spot

                
        #print("Avg. Mean Peaks Dist: " + str(peak_anal(mpeaks)))
        #print("Avg. Peak Dist: " + str(peak_anal(peaks)))




        pygame.display.flip()
        pygame.time.wait(10)



    #    pygame.display.flip()



     #   end = milli_time()
except:
    print("IS ALL OVER NAO")
    SHUTITDOWN()

SHUTITDOWN()



main()
