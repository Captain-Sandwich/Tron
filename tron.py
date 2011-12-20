#!/usr/bin/env python3
import curses
import traceback
import random
import time
import threading
import math
import sys
import os
import random
import itertools
from argparse import ArgumentParser

parser = ArgumentParser(description='play tron')

parser.add_argument('players',help='number of players (2 to 4)', metavar='n',type=int,default=2,nargs='?')
parser.add_argument('-t','--timestep',help='set time between steps',metavar='time',default=0.07,type=float)
parser.add_argument('-r',help='use random starting points',action='store_true', default=False)
parser.add_argument('-c',help='use computer opponents',action='store_true', default=False)
parser.add_argument('-d',help='demo mode',action='store_true', default=False)
args = parser.parse_args()
args = vars(args)

#Setup parsed 
timestep = args['timestep']
minstep = 0.05
if timestep < minstep:
    timestep = minstep
random_positions = args['r']
playernum = args['players']
use_ai = args['c']
demo_mode = args['d']
print(use_ai)
if type(playernum) == 'list':
    playernum = playernum[0]
alpha = 0.001 #Growth Factor


keys = [ curses.KEY_UP, curses.KEY_RIGHT, curses.KEY_DOWN, curses.KEY_LEFT,
#Spieler 1, Pfeiltasten
         119,100,115,97, #WDSA
         105,108,107,106, #ILKJ
         56,54,53,52] #numpad, numlock einschalten!!!
    
directions = [(-1,0),(0,1),(1,0),(0,-1)] #oben,rechts,unten,links

def countdown():
    screen.addstr(halfy-4,halfx-2,'  .oooo.  ')
    screen.addstr(halfy-3,halfx-2,'.dP""Y88b ')
    screen.addstr(halfy-2,halfx-2,"      ]8P'")
    screen.addstr(halfy-1,halfx-2,"    <88b. ")
    screen.addstr(halfy,halfx-2,  "     `88b.")
    screen.addstr(halfy+1,halfx-2,'o.   .88P ')
    screen.addstr(halfy+2,halfx-2,"`8bd88P'  ")
    screen.refresh()
    step()
    time.sleep(0.5)
    step()
    time.sleep(0.5)
    screen.addstr(halfy-4,halfx-2,'  .oooo.  ')
    screen.addstr(halfy-3,halfx-2,'.dP""Y88b ')
    screen.addstr(halfy-2,halfx-2,"      ]8P'")
    screen.addstr(halfy-1,halfx-2,"    .d8P' ")
    screen.addstr(halfy,halfx-2,  "  .dP'    ")
    screen.addstr(halfy+1,halfx-2,'.oP     .o')
    screen.addstr(halfy+2,halfx-2,'8888888888')
    screen.refresh()
    step()
    time.sleep(0.5)
    step()
    time.sleep(0.5)
    screen.addstr(halfy-4,halfx-2,'     .o   ')
    screen.addstr(halfy-3,halfx-2,'   o888   ')
    screen.addstr(halfy-2,halfx-2,"    888   ")
    screen.addstr(halfy-1,halfx-2,"    888   ")
    screen.addstr(halfy,halfx-2,  "    888   ")
    screen.addstr(halfy+1,halfx-2,'    888   ')
    screen.addstr(halfy+2,halfx-2,'   o888o  ')
    screen.refresh()
    step()
    time.sleep(1)
    screen.addstr(halfy-4,halfx-2,'          ')
    screen.addstr(halfy-3,halfx-2,'          ')
    screen.addstr(halfy-2,halfx-2,'          ')
    screen.addstr(halfy-1,halfx-2,'          ')
    screen.addstr(halfy,halfx-2,  '          ')
    screen.addstr(halfy+1,halfx-2,'          ')
    screen.addstr(halfy+2,halfx-2,'          ')
    screen.refresh()
    
def debug(*args):
    f = open('log','a')
    for i in args:
        f.write(repr(i))
        f.write(' ')
    f.write('\n')
    f.flush()
    f.close()

def add(t1,t2): #tupel komponentenweise addieren
    return (t1[0]+t2[0],t1[1]+t2[1]) 

class NullDevice():
    def write(self,s):
        pass
#sys.stderr = NullDevice() #faktisch stderr ausschalten

def distance(pos1,pos2):
        return math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)

def randomstarts(num):
    mindistance = int(math.sqrt(size[0]*size[1]) / 5) #recht willkuerlich
    a = max(5,playernum)
    mindistedge = int(math.sqrt(size[0]*size[1]) / a) # auch recht willkuerlich
    ok = False
    while not ok:
        positions = []
        #koordinaten generieren
        for i in range(num):
            y = random.randint(mindistedge+1,size[0]-mindistedge)
            x = random.randint(mindistedge+1,size[1]-mindistedge)
            positions.append((y,x))
        #koordinaten ueberpruefen
        if num == 1:
            ok = True
        for i,j in itertools.combinations(positions,2):
            if distance(i,j) < mindistance:
                ok = False
                break
            else:
                ok = True
    dirs = [directions[random.randint(0,3)] for i in range(num)]
    return positions,dirs

    
def playersetup(num):
    spieler = []
    if random_positions:
        pos,dirs = randomstarts(num)
        for i in range(num):
            if (use_ai and i > 0) or demo_mode:
                spieler.append(Survivor(pos[i],dirs[i],i+1,5))
            else:
                spieler.append(Spieler(pos[i],dirs[i],i+1))
        return spieler
    else:
        xpadding = int(size[1]/10)
        ypadding = int(size[0]/10)
        if num >= 2:
            spieler.append(Spieler((halfy,xpadding),(0,1),1)) #richtung rechts, blau
            spieler.append(Spieler((halfy,size[1]-xpadding-1),(0,-1),2)) #richtung links, rot
        if num >= 3:
            spieler.append(Spieler((ypadding,halfx),(1,0),3))
        if num >= 4:
            spieler.append(Spieler((size[0]-ypadding-1,halfx),(-1,0),4))
        return spieler
        
def status():
    if playernum <= 4:
        quarterx = int(halfx/2)
        pos = 0
        counter = 1
        statusline.erase()
        for i in spieler:
            statusline.addstr(0,pos,'Spieler %d:    %4d' % (counter,score[counter-1]),curses.color_pair(i.color))
            statusline.refresh()
            counter +=1
            pos += quarterx
        
def init(stdscr):
    global size
    global screen
    global statusline
    global stepper
    global halfx
    global halfy
    global score
    try:
        score = [0]*playernum
    except IndexError:
        score = [0,0]
    size = os.popen('stty size', 'r').read().split()
    size[0] = int(size[0])
    size[1] = int(size[1])
    halfx = int(size[1]/2)
    halfy = int(size[0]/2)
    if size[0] < 30 or size[1] < 30:
        raise Exception
    statusline = stdscr.subwin(1,size[1],0,0)
    #screen = stdscr.subwin(size[0]-1,size[1],1,0)
    screen = stdscr.subwin(size[0]-1,size[1],1,0)

def handle_key(key):
    if key == 113: #q 'QUIT'
        stepper.stop()
        raise Exception
    if key == 110 : #n 'Neues Spiel'
        stepper.stop()
        main() 
    if key in keys:
        index = keys.index(key)
        player = spieler[int(index/4)] #integer division; 4 tasten pro spieler
        player.changedir(directions[index%4]) #neue Richtung setzen

def main():
    global besetzt
    global stepper
    global spieler
    stepper = Stepper()
    screen.erase()
    screen.box()
    screen.refresh()
    try:
        spieler = playersetup(playernum)
    except IndexError:
        spieler = playersetup(2)
    status()
    besetzt = set([])
    #for i in range(3):
    #    step()
    countdown()
    stepper.start()
    c = ''
    while c != 113: #113 ist q
        c = stdscr.getch()
        handle_key(c)

def step():
    global stepper
    global spieler
    global besetzt
    #lebende weiterlaufen lassen
    for i in spieler:
        i.step()
    #als erstes alle umbringen die in einer mauer sitzen
#    for i in spieler:
#        if i.collision(i.pos):
#            i.alive = False #Spieler stirbt
#            pass
    #sieger checken
    alive = 0 #lebende Spieler checken
    for i in spieler:
        if i.alive:
            alive += 1
    if alive == 1 and not demo_mode:
        winner =  [i.alive for i in spieler].index(True)
        statusline.erase()
        statusline.addstr(0,0,'Spieler %s hat gewonnen' % str(winner+1), curses.color_pair(spieler[winner].color))
        statusline.refresh()
        spieler[winner].alive = False
        score[winner] += 1
        stepper.stop()
    elif demo_mode:
        if alive == 1 and playernum> 1:
            stepper.stop()
            main()
        elif alive == 0 and playernum==1:
            stepper.stop()
            #main()
    elif alive == 0:
        statusline.erase()
        statusline.addstr(0,0,'Unentschieden')
        statusline.refresh()
        stepper.stop()
    screen.refresh()

class Stepper(threading.Thread):
    def __init__(self):
        self.stopped = False
        self.timestep = timestep
        self.alpha = alpha
        self.starttime = time.time()
        self.counter = 0
        super(Stepper, self).__init__()

    def stop(self):
        self.stopped = True

    def run(self):
        while not self.stopped:
            if self.timestep > minstep:
                self.timestep = timestep - alpha*(time.time()-self.starttime)
            step()
            time.sleep(self.timestep)
            self.counter += 1

class Spieler():
    def __init__(self,pos,direction,color):
        self.pos = pos
        self.direction = direction
        self.color = color
        self.char = '\u2588'
        self.alive = True
        self.block = False

    def step(self):
        global besetzt
        if self.alive:
            self.pos = add(self.pos, self.direction)
            screen.addstr(self.pos[0],self.pos[1], self.char,curses.color_pair(self.color))
            if self.collision(self.pos):
                self.alive = False
            besetzt.add(self.pos) # wachsen
            self.block = False # eine Aktion pro Step

    def collision(self,position):
        global besetzt
        if position[0] == 0 or position[0] == size[0]-2:
            return True
        elif position[1] == 0 or position[1] == size[1]-1:
            return True
        elif position in besetzt:
            return True

    def changedir(self,direction):
        if not self.block:
            #umdrehen nicht erlauben
            if self.direction[0] == -direction[0]:
                return False
            elif self.direction[1] == -direction[1]:
                return False
            else:
                self.direction = direction
                self.block = True

class Survivor(Spieler):
    def __init__(self,pos,direction,color,difficulty):
        super(Survivor,self).__init__(pos,direction,color)
        self.diff = difficulty
        self.counter = 0
        self.randmove = int(random.gauss(25,10))
        self.color = 5

    def turn(self):
        if self.block:
            return True
        index = directions.index(self.direction)
        a = random.choice([-1,1])
        newindex = (index +a) % 4
        newdir = directions[newindex]
        futurepos = add(self.pos,newdir)
        if self.collision(futurepos):
            a = -a
            newindex = (index +a) % 4
            newdir = directions[newindex]

        self.changedir(newdir)
        self.block = True

    def debug(self,*args):
        if spieler.index(self) == 0:
            debug(*args)

    def lookahead(self,pos,distance,direction):
        distance = distance+1
        for i in range(1,distance):
            vector = (direction[0]*i,direction[1]*i)
            target = add(pos,vector)
            if self.collision(target):
                return True
                break
            else:
                return False

    def step(self):
        super(Survivor,self).step()
        self.counter += 1
        if self.lookahead(self.pos,self.diff,self.direction):
            self.turn()
        if not self.block:
            if self.counter == self.randmove:
                if random.getrandbits(1):
                    self.turn()
                self.counter = 0
                self.randmove = int(random.gauss(25,10))
        else:
            self.block = False



if __name__=='__main__':
  try:
      # Initialize curses
      stdscr=curses.initscr()
      # Turn off echoing of keys, and enter cbreak mode,
      # where no buffering is performed on keyboard input
      curses.noecho()
      curses.cbreak()
      curses.curs_set(0)
      

      #add color:
      curses.start_color()
      curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
      curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
      curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
      curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
      curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
      

      # In keypad mode, escape sequences for special keys
      # (like the cursor keys) will be interpreted and
      # a special value like curses.KEY_LEFT will be returned
      stdscr.keypad(1)
      init(stdscr)                    # Enter the main loop
      main()
      # Set everything back to normal
      stdscr.keypad(0)
      curses.echo()
      curses.curs_set(1)
      curses.nocbreak()
      curses.endwin()                 # Terminate curses
  except:
      # In event of error, restore terminal to sane state.
      stdscr.keypad(0)
      curses.echo()
      curses.nocbreak()
      curses.endwin()
      curses.curs_set(1)
      traceback.print_exc()           # Print the exception
