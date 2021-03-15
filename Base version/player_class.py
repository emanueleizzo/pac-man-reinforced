import pygame
import time
import copy
from settings import *

vec = pygame.math.Vector2

class Player:
    # Costruttore
    def __init__(self, app):
        self.app = app
        self.grid_pos = copy.deepcopy(PLAYER_START_POS)
        self.starting_pos = copy.deepcopy(PLAYER_START_POS)
        self.pix_pos = self.get_pix_pos()
        self.direction = vec(1, 0)
        self.stored_direction = None
        self.able_to_move = True
        self.current_score = 0
        self.eaten_dots = 0
        self.speed = 1
        self.lives = 3
        self.counter = 1

    # Update
    def update(self):
        # Se il player può muoversi, allora effettua un moviemnto
        if self.able_to_move:
            self.pix_pos += self.direction*self.speed
        # Se si trova al  centro della casella, e pertanto può cambiare  la sua direzione
        if self.time_to_move():
            # Cambia la direzione
            if self.stored_direction != None:
                self.direction = self.stored_direction
            # Controlla se può continuare a muoversi
            self.able_to_move = self.can_move()
        # Controlla se ha preso uno dei due corridoi che porta dall'altra parte della mappa
        if self.grid_pos == vec(28, 14) and self.stored_direction == vec(1, 0):
            self.grid_pos = vec(0, 14)
            self.pix_pos[0] = (self.grid_pos[0]-1)*self.app.cell_width+TOP_BOTTOM_BUFFER
        if self.grid_pos == vec(-1, 14) and self.stored_direction == vec(-1, 0):
            self.grid_pos = vec(27, 14)
            self.pix_pos[0] = (self.grid_pos[0]-1)*self.app.cell_width+TOP_BOTTOM_BUFFER
        # Calcola la posizione del fantasma nella griglia
        self.grid_pos[0] = (self.pix_pos[0]-TOP_BOTTOM_BUFFER +
                            self.app.cell_width//2)//self.app.cell_width+1
        self.grid_pos[1] = (self.pix_pos[1]-TOP_BOTTOM_BUFFER +
                            self.app.cell_height//2)//self.app.cell_height+1
        # Se si trova su un dot, allora chiama la funzione per mangiare il dot
        if self.on_dot():
            self.eat_dot()
        # Se si trova su un pellet, allora chiama la funzione per mangiare un pellet
        if self.on_pellet():
            self.eat_pellet()

    # Funzione che disegna il player sullo schermo
    # La seconda draw disegna le vite di cui dispone il player
    def draw(self):
        pygame.draw.circle(self.app.screen, PLAYER_COLOUR, (int(self.pix_pos.x), int(self.pix_pos.y)), self.app.cell_width//2-2)
        for x in range(self.lives):
            pygame.draw.circle(self.app.screen, PLAYER_COLOUR, (30 + 20*x, HEIGHT - 15), 7)
        
    # Verifica se il player si trova si un dot
    # (ossia se si trova al centro della casella dove si trova il dot)
    def on_dot(self):
        if self.grid_pos in self.app.dots:
            if int(self.pix_pos.x+TOP_BOTTOM_BUFFER//2) % self.app.cell_width == 0:
                if self.direction == vec(1, 0) or self.direction == vec(-1, 0):
                    return True
            if int(self.pix_pos.y+TOP_BOTTOM_BUFFER//2) % self.app.cell_height == 0:
                if self.direction == vec(0, 1) or self.direction == vec(0, -1):
                    return True
        return False

    # Verifica se il player si trova si un pellet
    # (ossia se si trova al centro della casella dove si trova il pellet)
    def on_pellet(self):
        if self.grid_pos in self.app.pellets:
            if int(self.pix_pos.x+TOP_BOTTOM_BUFFER//2) % self.app.cell_width == 0:
                if self.direction == vec(1, 0) or self.direction == vec(-1, 0):
                    return True
            if int(self.pix_pos.y+TOP_BOTTOM_BUFFER//2) % self.app.cell_height == 0:
                if self.direction == vec(0, 1) or self.direction == vec(0, -1):
                    return True
        return False

    # Mangia il dot su cui si trova
    # (rimuove il pellet dall'array e incrementa il numero di dot mangiati)
    def eat_dot(self):
        self.app.dots.remove(self.grid_pos)
        self.current_score += DOT_PTS
        self.eaten_dots += 1

    # Mangia il pellet su cui si trova (rimuove il pellet dall'array e incrementa il numero di dot mangiati)
    # Inoltre setta tutti i fantasmi sullo stato di "Frightened"
    def eat_pellet(self):
        initial_time = time.clock()
        self.app.pellets.remove(self.grid_pos)
        self.current_score += PELLET_PTS
        self.eaten_dots += 1
        # Per ogni fantasma vado a settare il suo stato in "Frightened", a cambiargli colore e a decrementare la sua velocita` 
        for enemy in self.app.enemies:
            # Controllo se il fantasma è nello stato di "Chase"
            if enemy.state == "Chase":
                enemy.state = "Frightened"
                # Se si trova all'esterno della zona di spawn, allora inverto la sua direzione
                if enemy.outside:
                    enemy.direction *= -1
                enemy.modifier = 0.75
                # Alloco alcune variabili all'interno dell'oggetto del fantasma
                enemy.colour = BLUE
                enemy.initial_time = initial_time
                enemy.counter = 0

    # Mangia il fantasma concui si incrocia, e setta il fantasma nello stato di "Eaten"
    # Inoltre incrementa il numero di fantasmi mangiati e calcola il percorso per arrivare alla zona di spawn
    def eat_enemy(self, enemy):
        self.current_score += VULNERABLE_GHOST_PTS*self.counter
        self.counter += 1
        enemy.state = "Eaten"
        enemy.colour = enemy.set_colour()
        enemy.modifier = 1

    # Salva la direzione appena ricevuta
    def move(self, direction):
        self.stored_direction = direction

########## HELPER FUNCTIONS ##########

    # Calcola la posizione in cui deve disegnare il player
    def get_pix_pos(self):
        return vec((self.grid_pos[0]*self.app.cell_width)+TOP_BOTTOM_BUFFER//2+self.app.cell_width//2,
                   (self.grid_pos[1]*self.app.cell_height) +
                   TOP_BOTTOM_BUFFER//2+self.app.cell_height//2)

        print(self.grid_pos, self.pix_pos)

    # Controlla se il player può muoversi
    # (controlla se si trova al centro della casella della griglia)
    def time_to_move(self):
        if int(self.pix_pos.x+TOP_BOTTOM_BUFFER//2) % self.app.cell_width == 0:
            if self.direction == vec(1, 0) or self.direction == vec(-1, 0) or self.direction == vec(0, 0):
                return True
        if int(self.pix_pos.y+TOP_BOTTOM_BUFFER//2) % self.app.cell_height == 0:
            if self.direction == vec(0, 1) or self.direction == vec(0, -1) or self.direction == vec(0, 0):
                return True

    # Controlla se il fantasma può continuare a muoversi in una certa direzione
    def can_move(self):
        if vec(self.grid_pos+self.direction) in self.app.walls:
            return False
        return True
