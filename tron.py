#!usr/bin/python3
import curses,traceback
import random
import time
import threading
import math
import sys
import os


size = (30,79) #(y,x)
timestep = 0.07
minstep = 0.05
alpha = 0.001 #Growth Factor
keys = [ curses.KEY_UP, curses.KEY_RIGHT, curses.KEY_DOWN, curses.KEY_LEFT,
#Spieler 1, Pfeiltasten
         119,100,115,97, #WDSA
         105,108,107,106, #ILKJ
         56,54,53,52] #numpad, numlock einschalten!!!

def countdown():
    screen.addstr(halfy-3,halfx-2,'333333 ')
    screen.addstr(halfy-2,halfx-2,'   3333')
    screen.addstr(halfy-1,halfx-2,'  3333 ')
    screen.addstr(halfy,halfx-2,'    333')
    screen.addstr(halfy+1,halfx-2,'333333 ')
    screen.refresh()
    time.sleep(1)
    screen.addstr(halfy-3,halfx-2,' 2222  ')
    screen.addstr(halfy-2,halfx-2,'222222 ')
    screen.addstr(halfy-1,halfx-2,'    222')
    screen.addstr(halfy,halfx-2,' 2222  ')
    screen.addstr(halfy+1,halfx-2,'2222222')
    screen.refresh()
    time.sleep(1)
    screen.addstr(halfy-3,halfx-2,'   1   ')
    screen.addstr(halfy-2,halfx-2,'  111  ')
    screen.addstr(halfy-1,halfx-2,'   11  ')
    screen.addstr(halfy,halfx-2,'   11  ')
    screen.addstr(halfy+1,halfx-2,'  111  ')
    screen.refresh()
    time.sleep(1)
    screen.addstr(halfy-3,halfx-2,'       ')
    screen.addstr(halfy-2,halfx-2,'       ')
    screen.addstr(halfy-1,halfx-2,'       ')
    screen.addstr(halfy,halfx-2,'       ')
    screen.addstr(halfy+1,halfx-2,'       ')
    screen.refresh()
    



def add(t1,t2): #tupel komponentenweise addieren
    return (t1[0]+t2[0],t1[1]+t2[1]) 

class Spieler():
    def __init__(self,pos,direction,color):
        self.pos = pos
        self.direction = direction
        self.wall = []
        self.wall.append(self.pos)
        self.color = color
        self.char = '\u2588'
        self.alive = True
        self.block = False

    def step(self):
        if self.alive:
            self.pos = add(self.pos, self.direction)
            self.wall.append(self.pos) # wachsen
            self.block = False # eine Aktion pro Step
            #danach collision tests

    def draw(self):
        #TODO eigentlich muss nur das neueste gemalt werden
        #for i in self.wall:
        #    screen.addstr(i[0],i[1], self.char,curses.color_pair(self.color))
        i = self.wall[-1]
        screen.addstr(i[0],i[1], self.char,curses.color_pair(self.color))
        

    def collision(self,besetzt):
        if self.pos[0] == 0 or self.pos[0] == size[0]-1:
            return True
        elif self.pos[1] == 0 or self.pos[1] == size[1]-1:
            return True
        elif self.pos in besetzt:
            if besetzt.count(self.pos) > 1:
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


def playersetup(num):
    spieler = []
    if num >= 2:
        spieler.append(Spieler((halfy,4),(0,1),1)) #richtung rechts, blau
        spieler.append(Spieler((halfy,size[1]-5),(0,-1),2)) #richtung links, rot
    if num >= 3:
        spieler.append(Spieler((4,halfx),(1,0),3))
    if num >= 4:
        spieler.append(Spieler((size[0]-5,halfx),(-1,0),4))
    return spieler
        
def status():
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
        score = [0]*int(sys.argv[1])
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
    directions = [(-1,0),(0,1),(1,0),(0,-1)] #oben,rechts,unten,links
    if key == 113: #q 'QUIT'
        stepper.stop()
        raise Exception
    if key == 110 : #n 'Neues Spiel'
        main() 
    if key in keys:
        index = keys.index(key)
        player = spieler[int(index/4)] #integer division; 4 tasten pro spieler
        player.changedir(directions[index%4]) #neue Richtung setzen

def main():
    global stepper
    global spieler
    screen.erase()
    screen.box()
    screen.refresh()
    try:
        spieler = playersetup(int(sys.argv[1]))
    except IndexError:
        spieler = playersetup(2)
    status()
    for i in range(3):
        step()
    countdown()
    stepper = Stepper()
    stepper.start()
    c = ''
    while c != 113: #113 ist q
        c = stdscr.getch()
        handle_key(c)

def step():
    global stepper
    global spieler
    #lebende weiterlaufen lassen
    for i in spieler:
        i.step()
    #als erstes alle umbringen die in einer mauer sitzen
    besetzt = []
    for i in spieler:
        besetzt.extend(i.wall)
    for i in spieler:
        if i.collision(besetzt):
            i.alive = False #Spieler stirbt
            pass
    #sieger checken
    alive = 0 #lebende Spieler checken
    for i in spieler:
        if i.alive:
            alive += 1
    if alive == 1:
        winner =  [i.alive for i in spieler].index(True)
        statusline.erase()
        statusline.addstr(0,0,'Spieler %s hat gewonnen' % str(winner+1), curses.color_pair(spieler[winner].color))
        statusline.refresh()
        spieler[winner].alive = False
        score[winner] += 1
        stepper.stop()
    elif alive == 0:
        statusline.erase()
        statusline.addstr(0,0,'Unentschieden')
        statusline.refresh()
        stepper.stop()

    for i in spieler:
        i.draw()
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

    
if __name__=='__main__':
  try:
      # Initialize curses
      stdscr=curses.initscr()
      # Turn off echoing of keys, and enter cbreak mode,
      # where no buffering is performed on keyboard input
      curses.noecho()
      curses.cbreak()
      #curses.curs_set(0)
      

      #add color:
      curses.start_color()
      curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
      curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
      curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
      curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
      

      # In keypad mode, escape sequences for special keys
      # (like the cursor keys) will be interpreted and
      # a special value like curses.KEY_LEFT will be returned
      stdscr.keypad(1)
      init(stdscr)                    # Enter the main loop
      main()
      # Set everything back to normal
      stdscr.keypad(0)
      curses.echo()
      #curses.curs_set(1)
      curses.nocbreak()
      curses.endwin()                 # Terminate curses
  except:
      # In event of error, restore terminal to sane state.
      stdscr.keypad(0)
      curses.echo()
      curses.nocbreak()
      curses.endwin()
      traceback.print_exc()           # Print the exception
