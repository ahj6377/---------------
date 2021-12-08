import random
import pyglet

from collections import defaultdict

from pyglet.image import load, ImageGrid, Animation
from pyglet.window import key

import cocos.layer
import cocos.sprite
import cocos.collision_model as cm
import cocos.euclid as eu
import cocos.actions as ac
import cocos.tiles
import cocos.particle_systems as ps
import math
import numpy as np
import time
import pygame


##bgm from https://www.chosic.com/download-audio/24995/
raw = pyglet.image.load('resource/watertex1-side.png')
seq = pyglet.image.ImageGrid(raw,1,3)
vorteximage = Animation.from_image_sequence(seq,0.5,True)

pygame.init()

def Truncate(vector, m): # limits vector
    magnitude = abs(vector)
    if magnitude > m:
        vector *= m / magnitude
    return vector


sound = pygame.mixer.Sound("resource/Komiku_-_12_-_Bicycle.mp3")
sound.play(-1)
atksound = pygame.mixer.Sound("resource/shoot.ogg")
boomsound = pygame.mixer.Sound("resource/boom.ogg")
class Actor(cocos.sprite.Sprite):
    def __init__(self, image, x, y):
        super(Actor, self).__init__(image)
        self.position = eu.Vector2(x, y)
        self.cshape = cm.CircleShape(self.position,self.width/2)

    def move(self, offset):
        self.position += offset
        self.cshape.center += offset

    def moveto(self, x,y,t):
        self.move(eu.Vector2((x-self.position[0])/t,(y - self.position[1])/t))
        #self.do(ac.MoveTo((x,y),t))

    def tremble(self):
        self.move(eu.Vector2(random.uniform(-1,1),random.uniform(-1,1)))

    def update(self, elapsed):
        pass

    def collide(self, other):
        pass

class PlayerCannon(Actor):
    KEYS_PRESSED = defaultdict(int)

    def __init__(self, x, y):
        super(PlayerCannon, self).__init__('resource/Cannon.png', x, y)
        self._set_scale(0.5)
        self.speed = eu.Vector2(200, 0)
        self.direction = [1,0]
        self.shootdirection = [1,0]
        self.atkspeed = 1
        self.damage = 1
        self.skillpoint = 0
        self.bomb = 0
        self.shield = 0
        self.bombprice = 3
        self.shieldprice = 3
        self.exp = 0
        self.requireexp = 5

        
        

    def update(self, elapsed):
        pressed = PlayerCannon.KEYS_PRESSED
        space_pressed = pressed[key.SPACE] == 1
        shift_pressed = pressed[key.LSHIFT] == 1
        
        speedfactor = 5    
        if(shift_pressed):
            speedfactor = 1
        x = pressed[key.RIGHT] - pressed[key.LEFT]
        y = pressed[key.UP] - pressed[key.DOWN]
        w = self.width * 0.5
        movement = eu.Vector2(speedfactor*x,speedfactor*y)
        newdirection = [x,y]
        angle = 0
        self.shootangle = 0
        if(newdirection != [0,0]):
            if(newdirection[1] >= 0 ):
                angle = math.acos(np.dot(self.direction, newdirection) / (self.direction[0]**2 + self.direction[1]**2) / (newdirection[0]**2 + newdirection[1]**2))
                angle = math.degrees(angle)
                angle = angle * -1
                self.do(ac.RotateTo(angle,0.001))
            else:
                angle = math.acos(np.dot(self.direction, newdirection) / (self.direction[0]**2 + self.direction[1]**2) / (newdirection[0]**2 + newdirection[1]**2))
                angle = math.degrees(angle)
                self.do(ac.RotateTo(angle,0.001))
            self.shootdirection = [newdirection[0],newdirection[1]]
            self.shootangle = angle     
        self.move(movement)
        
        T = time.time()
        if PlayerShoot.INSTANCE is None and space_pressed and T-self.parent.time >= 0.7:
            self.parent.add(PlayerShoot(self.x + 15*self.shootdirection[0], self.y + 15*self.shootdirection[1]))
            PlayerShoot.INSTANCE.setspeed(200*self.shootdirection[0],200*self.shootdirection[1])
            atksound.play()
            self.parent.time = time.time()


    def collide(self, other):
        return
        if(type(other) == PlayerShoot or type(other) == Shield or type(other) == blackhole):
            return
        if(self.shield == 1):
            self.shield = 0
            self.parent.S.kill()            
            other.kill()
            return
        other.kill()
        self.kill()
        self.parent.respawn_player()

class Shield(Actor):
    def __init__(self,x,y):
        super(Shield, self).__init__('resource/shield_Edit.png',x,y)
        self._set_scale(0.07)
        self.position = pos = eu.Vector2(x, y)
        self.cshape = cm.CircleShape(pos,self.width/2)

    def update(self,dt):
        self.position = self.parent.player.position
        self.cshape.center = self.position

    def collide(self,other):
        return
        '''
        if(type(other) == PlayerShoot or type(other) == PlayerCannon):
            return
        other.kill()
        self.kill()
        '''

class GameLayer(cocos.layer.Layer):
    is_event_handler = True
    key_pressed = defaultdict(int)

    def on_key_press(self, k, _):
        PlayerCannon.KEYS_PRESSED[k] = 1
        self.key_pressed[k] = 1

    def on_key_release(self, k, _):
        PlayerCannon.KEYS_PRESSED[k] = 0
        self.key_pressed[k] = 0

    def on_mouse_release(self,x,y,button,mod):
        #print("mouse_released")
        #print(x,y)
        if(self.onskillwindow == True):
            if(y <= (91/50*x +161/25)) and (y<= (-90/53*x + 76417/53))  and y>=657 and self.player.skillpoint > 0:
                self.player.skillpoint-=1
                self.player.damage +=1
            elif(y <= (23/13)*x - 1402/13) and (y<= -95/54*x + 11986/9) and y >= 519 and self.player.bomb == 0 and self.player.skillpoint >= self.player.bombprice:
                self.player.bomb = 1
                self.player.skillpoint -= self.player.bombprice
                self.player.bombprice+=1
            elif( y<= 94/53*x - 12223/53) and (y <= -94/53*x + 64481/53) and y>= 399 and self.player.shield == 0 and self.player.skillpoint >= self.player.shieldprice:
                self.player.shield = 1
                self.player.skillpoint -= self.player.shieldprice
                self.player.shieldprice+=1
                self.S = Shield(self.player.position[0],self.player.position[1])
                self.add(self.S, z = -1)
            
    



    def makestars(self):

        
        for i in range(100):
            star = NPC(self.width/2, self.height/2)
            dx,dy = random.uniform(-1,1),random.uniform(-1,1)
            norm = np.linalg.norm([dx,dy])
            #dx = -1
            #dy = -1
            dx = dx / norm
            dy = dy / norm
            star.setdirection(dx,dy)
            star.Rotate(dx,dy)
            self.add(star)


    def __init__(self, hud, skillwindow,boom):
        super(GameLayer, self).__init__()
        w, h = cocos.director.director.get_window_size()

        self.hud = hud
        self.skw = skillwindow
        self.Blayer = boom
        self.width = w
        self.height = h
        self.lives = 0
        self.score = 0
        self.time = 2
        self.level = 1
        self.update_score()
        self.create_player()
        cell = 1.25 * 15
        self.count = 1
        self.Isgathering = False
        self.levelchanged = True
        self.gatheringcount = 0
        self.timer10s = 10
        self.onskillwindow = False
        #self.v = virus(50,50)
        #self.b = blackhole(400,600)
        #self.add(self.b)
        #self.add(self.v)
        self.collman = cm.CollisionManagerGrid(0, w, 0, h, 
                                               cell, cell)
        self.schedule(self.update)
        self.bullets = []
        self.timer = 60


    def create_player(self):
        self.player = PlayerCannon(630, 1000)
        self.add(self.player)
        self.hud.update_sp(self.player.skillpoint)

    def update_score(self, score=0):
        self.score += score
        self.hud.update_score(self.score)

    def update_exp(self,score):
        self.player.exp += score
        if(self.player.exp >= self.player.requireexp):
            self.player.skillpoint +=1
            self.player.requireexp +=2
            self.player.exp -= self.player.requireexp

    def update_time(self, dt):
        self.timer -= dt
        self.hud.update_time(self.timer)
    def display_level(self):
        self.hud.update_level(self.level)

    def get_background(self):
        tmx_map = cocos.tiles.load('resource/starry-night-sky.jpg')
        bg = tmx_map[self.tmx_map]
        bg.set_view(0, 0, bg.px_width, bg.px_height)
        return bg
    def gatheringstars(self):
        self.Isgathering = True
        if(self.level == 1):
            for i in range(1):
                S1 = NPC(50 + random.uniform(-20,20) , 50+ random.uniform(-20,20))
                S1.setdirection(self.width/2, self.height/2)
                #S1.Rotate(self.width/2, self.height/2)
                S1.do(ac.RotateTo(-1*45,0.001))
                S1.canmove = False
                self.add(S1)

                S2 = NPC(50 + random.uniform(-20,20), self.height - 50 + random.uniform(-20,20))
                S2.setdirection(self.width/2, self.height/2)
                S2.do(ac.RotateTo(45,0.001))
                S2.canmove = False
                self.add(S2)
                
                S3 = NPC(self.width - 50 + random.uniform(-20,20), 50 + random.uniform(-20,20))
                S3.setdirection(self.width/2, self.height/2)
                S3.do(ac.RotateTo(-1*135,0.001))
                S3.canmove = False
                self.add(S3)

                S4 = NPC(self.width-50+random.uniform(-20,20), self.height-50+random.uniform(-20,20))
                S4.setdirection(self.width/2, self.height/2)
                S4.do(ac.RotateTo(135,0.001))
                S4.canmove = False
                self.add(S4)
                #S1.do(ac.MoveTo((self.width/2, self.height/2)),10)
        elif(self.level == 2):
                randn = random.randint(0,1)
                if(randn == 0):
                    S1 = NPC(50 + random.uniform(-20,20) , 50+ random.uniform(-20,20))
                    S1.setdirection(self.width/2, self.height/2)
                    #S1.Rotate(self.width/2, self.height/2)
                    S1.do(ac.RotateTo(-1*45,0.001))
                    S1.canmove = False
                    self.add(S1)

                    S2 = NPC(50 + random.uniform(-20,20), self.height - 50 + random.uniform(-20,20))
                    S2.setdirection(self.width/2, self.height/2)
                    S2.do(ac.RotateTo(45,0.001))
                    S2.canmove = False
                    self.add(S2)
                elif(randn == 1):
                    S3 = NPC(self.width - 50 + random.uniform(-20,20), 50 + random.uniform(-20,20))
                    S3.setdirection(self.width/2, self.height/2)
                    S3.do(ac.RotateTo(-1*135,0.001))
                    S3.canmove = False
                    self.add(S3)

                    S4 = NPC(self.width-50+random.uniform(-20,20), self.height-50+random.uniform(-20,20))
                    S4.setdirection(self.width/2, self.height/2)
                    S4.do(ac.RotateTo(135,0.001))
                    S4.canmove = False
                    self.add(S4)

                S5 = lv2NPC(self.width/2, self.height - 50)
                S5.setdirection(self.width/2, self.height/2)
                S5.canmove = False
                self.add(S5)

                S6 = lv2NPC(self.width/2, 20)
                S6.setdirection(self.width/2, self.height/2)
                S6.canmove = False
                self.add(S6)

                S7 = lv2NPC(20, self.height/2)
                S7.setdirection(self.width/2, self.height/2)
                S7.canmove=False
                self.add(S7)

                S8 = lv2NPC(self.width-50, self.height/2)
                S8.setdirection(self.width/2, self.height/2)
                S8.canmove = False
                self.add(S8)
        
        elif(self.level == 3):
            S1 = lv3NPC(self.width/2, self.height -50)
            S1.setdirection(self.width/2, self.height*3/4)
            S1.canmove = True
            self.add(S1)
            S2 = lv3NPC(self.width/2, 50)
            S2.setdirection(self.width/2, self.height/4)
            S2.canmove = True
            self.add(S2)
        
        elif(self.level == 4):
            #S1 = lv4NPC(self.width/2,self.height/2)
            S1 = lv4NPC(random.randint(50,self.width-50), random.randint(50,self.height-50))
            self.add(S1)
        


                




    def update(self, dt): 
        
        if(self.key_pressed[key.K] or self.onskillwindow == True):
            self.onskillwindow = True
            
        if(self.onskillwindow == True):
            self.skw.displayskillwindow(self.width/2, self.height/2,self.player.skillpoint, self.player.damage, self.player.bomb, self.player.bombprice, self.player.shield, self.player.shieldprice)
            
            if(self.key_pressed[key.Q]):
                self.onskillwindow=False
                self.skw.quitskillwindow()
                self.skw = skillWindowLayer()
                self.parent.add(self.skw,z=4)
                return

            return
        
        if(self.key_pressed[key.V] and self.player.bomb >0):
            boomsound.play()
            #self.Blayer.explode(self.player.position)
            self.Blayer.boom(self.player.position[0],self.player.position[1])
            for _, node in self.children:
                if(type(node) != PlayerCannon and type(node) != PlayerShoot and type(node) != Shield):

                    distance = (node.position[0] - self.player.position[0])**2 + (node.position[1] - self.player.position[1])**2
                    if(distance <=10000):
                        node.kill()
                
            self.player.bomb = 0


        blackholerandnum = random.randint(0,1000)
        if(blackholerandnum == 1):
            b = blackhole(random.randint(50,self.width-50),random.randint(50,self.height-50))
            self.add(b)
        

        if(self.level >=3):
            num = random.randint(1,100)
            num2 = random.randint(1,10000)
            if(num == 1):
                GHOST = ghost(random.randint(50,self.width-50), random.randint(50,self.height-50))
                self.add(GHOST)
            if(num2 == 1):
                v = virus(random.randint(50,self.width-50), random.randint(50,self.height-50))
                self.add(v)

        self.collman.clear()
        for _, node in self.children:
            self.collman.add(node)
            if not self.collman.knows(node):
                self.remove(node)

        self.update_time(dt)
        self.display_level()
        self.count +=dt
        if(self.timer >=50 and self.count > 0.5):
            self.gatheringstars()
            self.count = 0
            self.Isgathering = True
        elif(self.timer <=45 and self.Isgathering == True):
            
            for _, node in self.children:
                if(type(node) != PlayerShoot and type(node) != PlayerCannon and type(node) != Shield):
                    node.turn()
            self.Isgathering = False

        if(self.timer <= 0):
            self.timer = 60
            self.level+=1

        
        self.collide(self.player)
            
        

        self.collide(PlayerShoot.INSTANCE)
        if(PlayerShoot.INSTANCE is not None):
            t = time.time()
            self.player.ondelay = True
            if(t - self.time > 0.7):
                PlayerShoot.INSTANCE.kill()
                PlayerShoot.INSTANCE = None
                self.time = 0


        for _, node in self.children:
            
            node.update(dt)
        self.hud.update_sp(self.player.skillpoint)


    def breaksheild(self):
        self.S.kill()

    def collide(self, node):
        if node is not None:
            for other in self.collman.iter_colliding(node):
                node.collide(other)
                return True
        return False
    
    def respawn_player(self):
        self.lives -= 1
        if self.lives < 0:
            self.unschedule(self.update)
            self.hud.show_game_over()
        else:
            self.create_player()

class NPC(Actor):
    def __init__(self,x,y):
        super(NPC, self).__init__('resource/Aircraft_08.png',x,y)
        self._set_scale(0.5)
        self.position = pos = eu.Vector2(x, y)
        self.direction = eu.Vector2(0,1)
        self.speed = 80
        self.cshape = cm.CircleShape(pos, self.width/2)
        self.score = 1
        self.HP = 2
        self.canmove = True
    def setdirection(self,x,y):
        self.direction = eu.Vector2(x,y)

    def ongathering(self,x,y):
        self.moveto(x,y,50)
        self.tremble()
        
    def gathering(self):

            if(self.parent.Isgathering == True and self.canmove == False):
                #self.moveto(self.parent.width/2, self.parent.height/2,50)
                self.movetopoint()
                self.tremble()

    def movetopoint(self):
        if(self.parent.level == 1 or self.parent.level == 2):
            self.moveto(self.parent.width/2, self.parent.height/2,50)
        elif(self.parent.level == 3):
            if(self.position[1] >= self.parent.height/2):
                vecx, vecy = self.parent.width/2 - self.position[0], self.parent.height*3/4 - self.position[1]
                scale = np.linalg.norm([vecx, vecy])
                vecx = vecx/scale
                vecy = vecy/scale
                self.moveto(self.parent.width/2, self.parent.height*3/4,100)
                self.Rotate(vecx,vecy)

            else:
                vecx, vecy = self.parent.width/2 - self.position[0], self.parent.height*1/4 - self.position[1]
                scale = np.linalg.norm([vecx, vecy])
                vecx = vecx/scale
                vecy = vecy/scale
                self.moveto(self.parent.width/2, self.parent.height/4,100)
                self.Rotate(vecx,vecy)

        elif(self.parent.level == 4):
            if(self.position[0] < self.parent.width / 2 and self.position[1] < self.parent.height / 2):
                vecx, vecy = self.parent.width/4 - self.position[0], self.parent.height*1/4 - self.position[1]
                scale = np.linalg.norm([vecx, vecy])
                vecx = vecx/scale
                vecy = vecy/scale
                self.moveto(self.parent.width/4, self.parent.height/4,100)
                self.Rotate(vecx,vecy)
            elif(self.position[0] > self.parent.width /2 and self.position[1] < self.parent.height/2):
                vecx, vecy = self.parent.width/4*3 - self.position[0], self.parent.height/4 - self.position[1]
                scale = np.linalg.norm([vecx, vecy])
                vecx = vecx/scale
                vecy = vecy/scale
                self.moveto(self.parent.width/4*3,self.parent.height/4,100)
                self.Rotate(vecx,vecy)
            elif(self.position[0] < self.parent.width/2 and self.position[1] > self.parent.height /2):
                vecx, vecy = self.parent.width/4 - self.position[0], self.parent.height/4*3 - self.position[1]
                scale = np.linalg.norm([vecx, vecy])
                vecx = vecx/scale
                vecy = vecy/scale
                self.moveto(self.parent.width/4, self.parent.height/4*3,100)
                self.Rotate(vecx,vecy)
            else:
                vecx, vecy = self.parent.width/4*3 -  self.position[0], self.parent.height/4*3 - self.position[1]
                scale = np.linalg.norm([vecx, vecy])
                vecx = vecx/scale
                vecy = vecy/scale
                self.moveto(self.parent.width/4*3, self.parent.height/4*3,100)
                self.Rotate(vecx,vecy)
            
    def update(self,elapsed):
        if(self.parent.Isgathering == True):
            self.gathering()
        elif(self.canmove == False):
            self.movetopoint()
        if(self.parent.timer >= 45 and self.parent.level >= 3):
            self.movetopoint()
            return


        if(self.canmove == True):
            r = random.randint(0,100)
            if(r == 50):
                self.turn()

            if(self.position[0] <=0 or self.position[0] >= self.parent.width):
                self.direction[0] *= -1
                self.Rotate(self.direction[0],self.direction[1])
            elif(self.position[1] <= 10 or self.position[1] >= self.parent.height):
                self.direction[1] *= -1
                self.Rotate(self.direction[0],self.direction[1])
            self.move(self.speed * self.direction * elapsed)

    

    def turn(self):
        dx, dy = random.uniform(-1,1), random.uniform(-1,1)
        norm = np.linalg.norm([dx,dy])
        dx = dx/norm
        dy = dy/norm
        self.Rotate(dx,dy)
        self.direction = eu.Vector2(dx,dy)
        self.canmove = True

    def Rotate(self,x,y):
        dx, dy = 1,0
        p = np.array([x,y])
        dp = np.array([1,0])
        val = np.dot(p,dp) / ((x**2+y**2) + 0.000001 )/ ((dx**2+dy**2) + 0.000001)
        #print(val)
        if ( val > 1):
            val = 1
        elif(val <-1):
            val = -1
        #angle = math.acos(np.dot(p,dp) / ((x**2+y**2) + 0.000001 )/ ((dx**2+dy**2) + 0.000001))
        angle = math.acos(val)
        angle = math.degrees(angle)
        if(y >=0):
            angle = angle * -1
             
        self.do(ac.RotateTo(angle,0.001))




    

class lv2NPC(NPC):
    def __init__(self,x,y):
        super(NPC, self).__init__('resource/star.png',x,y)
        self._set_scale(0.02)
        self.score = 2
        self.HP = 4
        self.canmove = True
        self.position = pos = eu.Vector2(x, y)
        self.direction = eu.Vector2(0,1)
        self.speed = 80
        self.cshape = cm.CircleShape(pos, self.width/2)

    def update(self,elapsed):
        self.do(ac.RotateBy(1,elapsed))
        super().update(elapsed)

class lv3NPC(NPC):
    def __init__(self,x,y):
        super(NPC, self).__init__('resource/frame1.png',x,y)
        self._set_scale(0.06)
        self.score = 3
        self.HP = 4
        self.canmove = True
        self.position = pos = eu.Vector2(x,y)
        self.direction = eu.Vector2(0,1)
        self.speed = 160
        self.cshape = cm.CircleShape(pos, self.width/2)

class ghost(NPC):
    def __init__(self,x,y):
        super(NPC,self).__init__('resource/ghost.png',x,y)
        self._set_scale(0.5)
        self.score = 0
        self.HP = 100000000000
        self.canmove = False
        self.position = pos = eu.Vector2(x,y)
        self.direction = eu.Vector2(0,0)
        self.speed = 70
        self.cshape = cm.CircleShape(pos,self.width/2)
        self.max_force = 5
        self.max_velocity = 200
        self.remainingtime = 0
        
    def update(self,dt):
        self.target = self.parent.player
        if self.target is None:
            return
        targetposition = eu.Vector2(self.target.position[0] , self.target.position[1])
        distance = targetposition - eu.Vector2(self.x,self.y)
        steering = distance * self.speed - self.direction
        steering = Truncate(steering, self.max_force)
        self.direction = Truncate(self.direction + steering, self.max_velocity)
        self.Rotate(self.direction[0],self.direction[1])
        self.move(self.direction*dt)
        #self.position += self.direction*dt
        self.remainingtime+=dt

        if(self.remainingtime >=10 ):
            #self.kill()
            self.disapear()
    
    def disapear(self):
        self.parent.Blayer.killenemy(self.position[0],self.position[1])
        self.kill()

class lv4NPC(NPC):
    def __init__(self,x,y):
        super(NPC, self).__init__('resource/spaceship.png',x,y)
        self._set_scale(0.24)
        self.score = 4
        self.HP = 40
        self.canmove = True
        self.position = pos = eu.Vector2(x,y)
        self.direction = eu.Vector2(0,1)
        self.speed = 30
        self.cshape = cm.CircleShape(pos, self.width/2)


class blackhole(NPC):
    def load_animation(anim = vorteximage):
        return vorteximage

    def __init__(self,x,y):
        super(NPC, self).__init__(vorteximage,x,y)
        self.scale = random.uniform(1.0,3.0)
        self.remainingtime = random.randint(10,20)
        self.HP = 100000000000
        self.position = pos = eu.Vector2(x,y)
        self.cshape = cm.CircleShape(pos, self.width/2)
    def update(self,dt):
        distance = (self.position[0] - self.parent.player.position[0])**2 + (self.position[1] - self.parent.player.position[1]) **2
        self.remainingtime -= dt
        #self.scale += 0.0001
        #self._set_scale(self.scale)
        if(self.remainingtime <= 0):
            self.kill()
        if(distance < self.width**2 * 1.5):
            
            self.parent.player.moveto(self.position[0],self.position[1], 10)
        return

    def turn(self):
        return


class virus(NPC):
    def __init__(self,x,y):
        super(NPC, self).__init__('resource/Angryvirus6.png',x,y)
        self._set_scale(0.08)
        self.score = 100
        self.HP = 100
        self.canmove = False
        self.position = pos = eu.Vector2(x,y)
        self.direction = eu.Vector2(0,0)
        self.speed = 10
        self.cshape = cm.CircleShape(pos, self.width/2)
        self.wander_angle = 0
        self.circle_distance = 50
        self.circle_radius = 10
        self.angle_change = math.pi/4
        self.max_velocity = 50
        self.delay = 0

    def update(self,dt):
        
        circle_center = self.direction.normalized() * self.circle_distance
        dx = math.cos(self.wander_angle)
        dy = math.cos(self.wander_angle)
        displacement = eu.Vector2(dx,dy) * self.circle_radius
        self.wander_angle += (random.random() - 0.5) * self.angle_change
        self.direction += circle_center + displacement
        self.direction = Truncate(self.direction,self.max_velocity)
        self.move(self.direction*dt)
        self.delay+=dt
        if(self.delay >=2):
            self.shoot(dt)
            self.delay = 0


    def shoot(self,dt):
        temp = math.sqrt(20000)
        
        sh1 = Shoot(self.position[0],self.position[1])
        sh1.speed = eu.Vector2(200, 0)
        self.parent.add(sh1)
        sh2 = Shoot(self.position[0],self.position[1])
        sh2.speed = eu.Vector2(-200,0)
        self.parent.add(sh2)
        sh3 = Shoot(self.position[0],self.position[1])
        sh3.speed = eu.Vector2(0,200)
        self.parent.add(sh3)
        sh4 = Shoot(self.position[0],self.position[1])
        sh4.speed = eu.Vector2(0,-200)
        self.parent.add(sh4)
        sh5 = Shoot(self.position[0],self.position[1])
        sh5.speed = eu.Vector2(temp,temp)
        self.parent.add(sh5)
        sh6 = Shoot(self.position[0],self.position[1])
        sh6.speed = eu.Vector2(-temp,temp)
        self.parent.add(sh6)
        sh7 = Shoot(self.position[0],self.position[1])
        sh7.speed = eu.Vector2(temp,-temp)
        self.parent.add(sh7)
        sh8 = Shoot(self.position[0],self.position[1])
        sh8.speed = eu.Vector2(-temp,-temp)
        self.parent.add(sh8)



class Shoot(Actor):
    def __init__(self, x, y, img='resource/ball2.png'):
        super(Shoot, self).__init__(img, x, y)
        self._set_scale(0.4)
        self.color = (255,120,0)
        self.speed = eu.Vector2(0, -400)
        self.remainingtime = 0

    def update(self, elapsed):
        self.move(self.speed * elapsed)
        self.remainingtime += elapsed
        if(self.remainingtime>=1):
            self.kill()
    def collide(self,other):
        if(type(other) == PlayerCannon and self.parent.player.shield == 0):
            other.kill()
        elif(type(other) == PlayerCannon and self.parent.player.shield == 1):
            self.parent.player.shield = 0
            self.parent.breaksheild()
            self.kill() 
            return 

    def turn(self):
        return




class PlayerShoot(Shoot):
    INSTANCE = None

    def __init__(self, x, y):
        super(PlayerShoot, self).__init__(x, y, 'resource/bullet4.png')
        self._set_scale(0.5)
        self.speed *= -1
        PlayerShoot.INSTANCE = self
       # self.color = (128,255,255)

    def collide(self, other):
        if(type(other) == blackhole):
            return
        if isinstance(other, NPC):
            other.HP -= self.parent.player.damage
            if(other.HP <= 0):
                self.parent.update_score(other.score)
                self.parent.update_exp(other.score)
                self.parent.Blayer.killenemy(other.position[0],other.position[1])
                
                other.kill()          
                
            self.kill()
    def setspeed(self,x,y):
        self.speed = eu.Vector2(x,y)
    def on_exit(self):
        super(PlayerShoot, self).on_exit()
        PlayerShoot.INSTANCE = None


class skillWindowLayer(cocos.layer.Layer):
    def __init__(self):
        super().__init__()
        self.skw = None
        self.w, self.h = cocos.director.director.get_window_size()

    
    def displayskillwindow(self,x,y,skp,atk,b,bp,s,sp):
        self.skw = cocos.sprite.Sprite('resource/skw.png')
        self.skw.position = (x,y)
        self.add(self.skw) 
        self.skill_text = cocos.text.Label(' ', font_size = 24, color = (255,0,0,128))
        self.skill_text.position = (500, 200)
        self.skill_text.element.text = "Skill Points: %d" %skp

        self.atklevel_text = cocos.text.Label(' ', font_size = 24, color = (255,0,0,128))
        self.atklevel_text.element.text = "ATK : %d" %atk
        self.atklevel_text.position = (500,300)

        self.bombtext = cocos.text.Label(' ', font_size = 18, color = (255,0,0,128))
        self.bombtext.element.text = "폭탄개수(최대 1개) : %d / 폭탄가격 : %d" %(b,bp)
        self.bombtext.position = (500,260)

        self.shieldtext = cocos.text.Label(' ', font_size = 18, color = (255,0,0,128))
        self.shieldtext.position = (500,235)
        self.shieldtext.element.text = "실드개수(최대 1개) : %d / 실드가격: %d" %(s,sp)
        
        self.add(self.skill_text)
        self.add(self.atklevel_text)
        self.add(self.bombtext)
        self.add(self.shieldtext)



    def quitskillwindow(self):
        #self.remove(self.skw)
        
        #self.skw.on_exit()
        self.skw.kill()
        self.kill()
        


class HUD(cocos.layer.Layer):
    def __init__(self):
        super(HUD, self).__init__()
        w, h = cocos.director.director.get_window_size()
        self.score_text = cocos.text.Label('', font_size=18)
        self.score_text.position = (20, h - 40)
        self.sp_text = cocos.text.Label('', font_size=18)
        self.sp_text.position = (w - 200, h - 40)
        self.timer_text = cocos.text.Label('', font_size=18)
        self.timer_text.position = (w/2, h-40)
        self.level_text = cocos.text.Label('',font_size=24)
        self.level_text.position = (w-140, h - 100)
        self.add(self.score_text)
        self.add(self.sp_text)
        self.add(self.timer_text)
        self.add(self.level_text)

    def update_score(self, score):
        self.score_text.element.text = 'Score: %s' % score

    def update_sp(self, sp):
        self.sp_text.element.text = 'skillpoints: %s' % sp

    def update_time(self,time):
        self.timer_text.element.text = 'time: %ds' % time
    
    def update_level(self,level):
        self.level_text.element.text = 'level: %d' %level

    def show_game_over(self):
        w, h = cocos.director.director.get_window_size()
        game_over = cocos.text.Label('Game Over', font_size=50,
                                     anchor_x='center',
                                     anchor_y='center')
        game_over.position = w * 0.5, h * 0.5
        self.add(game_over)
        pygame.quit()




class backgroundlayer(cocos.layer.ScrollableLayer):
    def __init__(self):
        super().__init__()
        bg = cocos.sprite.Sprite('resource/starry-night-sky.jpg')
        self.add(bg)

class boomparticlelayer(cocos.layer.Layer):
    def __init__(self):
        super().__init__()
        

    def boom(self,x,y):
        self.particles  = ps.Explosion(fallback = False)
        self.particles.position = eu.Vector2(x,y)
        self.add(self.particles)
        self.particles.do(ac.Delay(0.7) + ac.CallFunc(self.particles.kill))
    def killenemy(self,x,y):
        self.smoke = ps.Smoke(fallback = None)
        self.smoke.position = eu.Vector2(x,y)
        self.add(self.smoke)
        self.smoke.do(ac.Delay(1.0) + ac.CallFunc(self.smoke.kill))
'''
    def makeshield(self,x,y):
        self.s = shield(x,y)
        self.add(self.s,z=-1)
    def updateshield(self,x,y):
        self.s.position = eu.Vector2(x,y)
    def breakshield(self):
        self.s.kill()

class shield(cocos.sprite.Sprite):
    def __init__(self,x,y):
        super(shield, self).__init__('resource/shield_Edit.png')
        self._set_scale(0.07)
        self.position = pos = eu.Vector2(x, y)
    def update(self,dt):
        self.position = eu.Vector2(self.parent.player.position[0] , self.parent.player.position[1])
        #self.cshape.center = self.position
'''



if __name__ == '__main__':
    cocos.director.director.init(caption='프로젝트-하떨별', 
                                 width=1280, height=960)
    main_scene = cocos.scene.Scene()
    hud_layer = HUD()
    bg_layer = backgroundlayer()
    skw_layer = skillWindowLayer()
    boom_layer = boomparticlelayer()
    #scroller = cocos.layer.ScrollingManager()
    #scroller.add(bg_layer)


    main_scene.add(bg_layer, z=0)
    #main_scene.add(scroller, z=0)
    main_scene.add(hud_layer, z=2)
    main_scene.add(skw_layer, z=3)
    main_scene.add(boom_layer, z=2)
    game_layer = GameLayer(hud_layer,skw_layer,boom_layer)
    main_scene.add(game_layer, z=1)


    cocos.director.director.run(main_scene)
