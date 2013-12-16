from Motion.Action import Action

import logging

log = logging.getLogger("R.Engine.Motion")

class Appear(Action):
    name = "in.appear"
    def __init__(self, sprite):
        super(Fade, self).__init__()
        
    def update(self, dt):
        self.sprite.unhide()
        self.finish()

class Fade(Action):
    name = "in.fade"
    def __init__(self, time, alpha):
        self.time = time
        self.alpha = alpha
        self.m = float(alpha)/float(time)

        super(Fade, self).__init__()

    def begin(self, sprite):
        log.debug("Fade.begin")
        self.x = 0.0
        sprite.alpha = 0.0
        sprite.unhide()

    def cancel(self):
        log.debug("Fade.cancel")
        self.sprite.alpha = self.alpha
        super(Fade, self).cancel()
        
    def update(self, dt):
        self.x += dt
        if self.x >= self.time:
            self.sprite.alpha = self.alpha
            self.finish()
        else:
            self.sprite.alpha = self.m * self.x
        
