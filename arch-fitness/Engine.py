#!/usr/bin/env python3

import pygame
import sys
from pygame.locals import *
import pygame.freetype
import traceback
import logging

from Motion.Action import Action

def main():
    import Motion

    game = Game(1280, 720)
    
    testApp = Application()
    testApp.backgroundColor = (0, 0, 50, 255)

    testsurface = pygame.image.load("test.png")
    testSprite = Sprite(testsurface.convert(), 250, 250)
    testSprite.alpha = 255

    testApp.addSprite(testSprite, 0) # add to top layer - 0

    testText = Text("Hello World!", 200, 100, (255,255,255,255),
                    50, "consola.ttf")

    testApp.addSprite(testText, "default") # add to default layer

    testText = Text("Hello World!", 200, 200, (255,255,255,255),
                    50, "consola.ttf")

    testApp.addLayer("top layer", 0)

    testApp.addSprite(testText, "top layer")

    testSprite.addMotion(Motion.looped(Motion.In.Fade(5.0, 255), 1))

    #---------------------------------------
    import Interface

    global subjectSprite
    global subjectMotion

    subjectSprite = Sprite(testsurface.convert(), 500, 500)
    testApp.addSprite(subjectSprite)

    def start():
        subjectSprite.addMotion(Motion.looped(Motion.In.Fade(4.0, 255), 0))
    def stop():
        subjectSprite.removeMotion("in.fade")

    startButton = Interface.SolidButton(400, 600, 100, 50,
                              (0,255,0,255), (50,255,50,255), (100,255,100,255),
                              start)
    stopButton = Interface.SolidButton(600, 600, 100, 50,
                             (255,0,0,255), (255,50,50,255), (255,100,100,255),
                             stop)

    testApp.addSprite(startButton)
    testApp.addSprite(stopButton)
    
    game.startApp(testApp)
    game.run()

class Game(object):
    
    def __init__(self, width, height):
        logging.info("starting engine")
        
        pygame.init()
        
        self.canvas = pygame.display.set_mode((width, height))
        pygame.display.set_caption("My Game")
        self.clock = pygame.time.Clock()

        Application.canvas = self.canvas
        Application.game = self
        Sprite.game = self

        self.app = None
        
    def startApp(self, application):
        self.app = application

    def postEvent(self, event):
        pygame.event.post(pygame.event.Event(event))
        
    def run(self):
        while True:
            dt = self.clock.get_time()
            
            if self.app:
                self.app.update(dt)
                self.app.draw()

            for event in pygame.event.get():
                if event.type == QUIT:
                    self.quit()
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.postEvent(QUIT)

            pygame.display.update()
            self.clock.tick(0)

    def quit(self):
        pygame.quit()
        sys.exit(1)

class Application(object):
    canvas = None
    game = None
    def __init__(self):
        self._layers = []
        self.layers = {}
        
        self.width, self.height = Application.canvas.get_size()
        self.backgroundsurface = None
        self.backgroundColor = (0,0,0,255)
        
        self.canvas = Application.canvas

        self.addLayer("default")

    def getLayerlevel(self, layer):
        return self._layers.index(layer)

    def addLayer(self, name, level=0):
        layer = Layer(name)
        layer.app = self
        self.layers[name] = layer
        self._layers.append(layer)
        layer.level = len(self.layers) - 1
        # by default, new layers are created on top.
        # smaller level values mean higher up (cannot be negative)
        layer.setLevel(level)
        
    def removeLayer(self, layer):
        layer = self.getLayer(layer)
        self._layers.remove(layer)
        del self.layers[layer.name]
        
    def renameLayer(self, layer, name):
        del self.layers[layer.name]
        self.layers[name] = layer
        
    def moveLayer(self, layer, level):
        layer = self.getLayer(layer)
        
        if level < -1:
            level = len(self._layers) - level
        
        if level >= len(self._layers) or level == -1:
            self._layers.append(layer)
        else:
            self._layers = self._layers[:level] + [layer] + self._layers[level:]
            
        self.layers[layer.name] = layer

    def getLayer(self, layer):
        if isinstance(layer, Layer):
            return layer
        elif isinstance(layer, str):
            return self.layers[layer]
        elif isinstance(layer, int):
            return self._layers[layer]
        else:
            return None

    def addSprite(self, sprite, layer=0):
        if isinstance(layer, Layer):
            layer.addSprite(sprite)
        elif isinstance(layer, str):
            self.layers[layer].addSprite(sprite)
        elif isinstance(layer, int):
            self._layers[layer].addSprite(sprite)
        else:
            pass
        
    def removeSprite(self, sprite):
        self._layers[sprite.layer.level].removeSprite(sprite)
    
    def update(self, dt):
        dt /= 1000.0
        i = len(self._layers)
        while i > 0:
            i -= 1
            self._layers[i].update(dt)
                
    def draw(self):
        if self.backgroundsurface:
            self.canvas.blit(self.backgroundsurface, (0,0))
        elif self.backgroundColor:
            self.canvas.fill(self.backgroundColor)
        
        i = len(self._layers)
        while i > 0:
            i -= 1
            self._layers[i].draw(Application.canvas)

class Layer(object):
    def __init__(self, name):
        self.sprites = []
        self._name = name
        self.app = None

    def getLevel(self):
        return self.app.getLayerlevel(self)
    def setLevel(self, level):
        if level != self.getLevel():
            self.app.moveLayer(self, level)
    level = property(getLevel, setLevel)

    def getName(self):
        return self._name
    def setName(self, name):
        self._name = name
        self.app.renameLayer(self, name)
    name = property(getName, setName)

    def addSprite(self, sprite):
        sprite.app = self.app
        sprite.layer = self
        self.sprites.append(sprite)

    def removeSprite(self, sprite):
        if sprite in self.sprites:
            self.sprites.remove(sprite)

    def update(self, dt):
        for sprite in self.sprites:
            sprite.tick(dt)
    def draw(self, canvas):
        for sprite in self.sprites:
            sprite.draw(canvas)

class Sprite(object):
    game = None
    def __init__(self, surface, x, y):
        self.surface = surface
        self.x = x
        self.y = y

        self.alpha = 255

        self.hidden = False

        self.dx = 0
        self.dy = 0

        # App is a variable tracking the game application.
        # It is assigned when the sprite is added to the draw list.
        self.app = None
        self.layer = None

        self.motions = []

    def getHidden(self):
        return self._hidden
    def setHidden(self, hidden):
        self._hidden = hidden
    hidden = property(getHidden, setHidden)
    def hide(self):
        self.hidden = True
    def unhide(self):
        self.hidden = False

    def isActive(self):
        return (self.app != None)
    
    def getAlpha(self):
        return self._alpha
    def setAlpha(self, alpha):
        self._surface.set_alpha(alpha)
        self._alpha = alpha
    alpha = property(getAlpha, setAlpha)

    def addMotion(self, motion):
        self.motions.append(motion)
        motion.sprite = self
        motion.begin(self)
    def removeMotion(self, motion):
        if isinstance(motion, Action):
            motion.cancel()
            self.motions.remove(motion)
        elif isinstance(motion, str):
            for imotion in self.motions:
                print (imotion)
            for imotion in self.motions:
                if imotion.name == motion.lower():
                    imotion.cancel()
            self.motions = [imotion for imotion in self.motions if not imotion.canceled]
    
    def tick(self, dt):
        self.x += self.dx * dt
        self.y += self.dy * dt

        if self.motions:
            for motion in self.motions:
                motion.update(dt)

        self.update(dt)

    def update(self, dt):
        pass
    
    def draw(self, canvas):
        if not self.hidden:
            canvas.blit(self._surface, self._rect)
            
    def destroy(self):
        self.app.removeSprite(self)

    # ----------------------------------------------
    # Setup class properties
    
    def getX(self):
        return self._x
    def setX(self, x):
        self._rect.centerx = x
        self._x = x
    def getY(self):
        return self._y
    def setY(self, y):
        self._rect.centery = y
        self._y = y
        
    x = property(getX, setX)
    y = property(getY, setY)

    def getLeft(self):
        return self._x - self._rect.width / 2
    def setLeft(self, left):
        self._x = left + self._rect.width / 2
    def getRight(self):
        return self._x + self._rect.width / 2
    def setRight(self, right):
        self._x = right - self._rect.width / 2
    def getTop(self):
        return self._y - self._rect.height / 2
    def setTop(self, top):
        self._y = top + self._rect.height / 2
    def getBottom(self):
        return self._y + self._rect.height / 2
    def setBottom(self, bottom):
        self._y = bottom - self._rect.height / 2
        
    left = property(getLeft, setLeft)
    right = property(getRight, setRight)
    top = property(getTop, setTop)
    bottom = property(getBottom, setBottom)

    def getWidth(self):
        return self._rect.width
    def getHeight(self):
        return self._rect.height
    width = property(getWidth)
    height= property(getHeight)

    def getsurface(self):
        return self._surface
    def setsurface(self, surface):
        self._surface = surface
        self._rect = surface.get_rect()
    surface = property(getsurface, setsurface)

    def getRect(self):        
        return self._rect
    def setRect(self, rect):
        self._rect = rect
    rect = property(getRect, setRect)

    #---------------------------------------------

class Text(Sprite):
    game = None
    def __init__(self, value, x, y, color, size, font=None):
        # manually set values to avoid problems in auto render
        self._font = font
        self._value = value
        self._color = color
        self._size = size

        # setting prop values will auto render the text on each assignment
        self.font = font
        self.value = value
        self.color = color
        self.size = size

        super(Text, self).__init__(self._surface, x, y)

    def render(self):
        self._surface, self._rect = self._font.render(self._value, self._color, None,
                                                rotation = 0, ptsize = self._size)
    
    def getFont(self):
        return self._fontFilename
    def setFont(self, font):
        self._font = pygame.freetype.Font(font, ptsize = self._size)
        self._fontFilename = font
        self.render()
    font = property(getFont, setFont)

    def getValue(self):
        return self._value
    def setValue(self, value):
        self._value = value
        self.render()
    value = property(getValue, setValue)

    def getColor(self):
        return self._color
    def setColor(self, color):
        self._color = color
        self.render()
    color = property(getColor, setColor)

    def getSize(self):
        return self._size
    def setSize(self, size):
        self._size = size
        self.render()
    size = property(getSize, setSize)

if __name__ == "__main__":
    import Debug
    Debug.test(main)
