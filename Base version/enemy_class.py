import math
import numpy
import pygame
import random
import time
import copy
from settings import *
from pygame.math import Vector2 as vec

class Enemy:
    # Costruttore
    def __init__(self, app, name, number, outside):
        self.app = app
        self.name = name
        self.number = number
        self.able_to_move = True
        self.grid_pos = self.get_grid_pos()
        self.starting_pos = self.get_grid_pos()
        self.pix_pos = self.get_pix_pos()
        self.colour = self.set_colour()
        self.direction = vec(1, 0)
        self.stored_direction = self.direction
        self.outside = outside
        self.state = "Chase"
        self.modifier = 1
    
    # Update
    def update(self):
        # Se il nemico può muoversi, allora effettua un movimento
        if self.able_to_move:
            self.pix_pos += self.direction*ENEMIES_SPEED*self.modifier
        # Se si trova al centro della casella, e pertanto può cambiare la sua direzione
        if self.time_to_move():
            # Controlla se si può muovere
            self.able_to_move = self.can_move()
            # Se non si può muovere di due caselle avanti oppure si trova vicino ad un incrocio
            # Decide la nuova direzione che terra` da parte
            if (not self.can_move_next()) or self.check_intersection_near():
                self.move()
            # Se non si può muovere di una casella avanti oppure si trova su un incrocio
            # usa la direzione che aveva deciso in precedenza
            if (not self.able_to_move) or self.check_intersection():
                self.direction = self.stored_direction
            # Se deve ancora uscire dalla zona di spawn
            # Calcola la direzione e la usa subito
            if (not self.outside):
                self.move()
                self.direction = self.stored_direction
        # Controlla se ha preso uno dei due corridoi che porta dall'altra parte della mappa
        if self.grid_pos == vec(28, 14) and self.direction == vec(1, 0):
            self.grid_pos = vec(0, 14)
            self.pix_pos[0] = (self.grid_pos[0]-1)*self.app.cell_width+TOP_BOTTOM_BUFFER
        if self.grid_pos == vec(-1, 14) and self.direction == vec(-1, 0):
            self.grid_pos = vec(27, 14)
            self.pix_pos[0] = (self.grid_pos[0]-1)*self.app.cell_width+TOP_BOTTOM_BUFFER
        # Calcola la posizione del fantasma nella griglia
        self.grid_pos[0] = (self.pix_pos[0]-TOP_BOTTOM_BUFFER)//self.app.cell_width+1
        self.grid_pos[1] = (self.pix_pos[1]-TOP_BOTTOM_BUFFER)//self.app.cell_height+1
        # Se il fantasma è nello stato di "Frightened", chiama la funzione per resettarlo
        if self.state == "Frightened":
            self.reset_to_chase()
        # Se il fantasma è stato mangiato ed è tornato della zona di spawn allora torna allo stato normale
        if self.state == "Eaten" and (self.grid_pos == vec(13, 14) or self.grid_pos == vec(14, 14)):
            self.state = "Chase"
            self.modifier = 1
            self.outside = False
    
    # Nel caso in cui il fantasma non sia ancora uscito dalla zona di spawn
    # Controlla solo se il fantasma è entrato nello stato di "Frightened"
    def update_state_only(self):
        if self.state == "Frightened":
            self.reset_to_chase()
    
    # Porta i fantasmi dallo stato di "Frightened" allo stato di "Chase"
    # Si occupa anche di far cambiare colore ai fantasmi
    def reset_to_chase(self):
        # Controlla se sono passati 6 secondi da quando i  
        # Fantasmi sono entrati nello stato di "Frightened"
        if (time.clock()-self.initial_time) > 6.0:
            # Effettua ad intervalli di 1 secondo il cambio
            # Di colore da bianco a blue viceversa
            if (time.clock()-self.initial_time) > (6.0+(self.counter/2)) and self.counter%2 == 0:
                self.counter += 1
                self.colour = WHITE
            elif (time.clock()-self.initial_time) > (6.0+(self.counter/2)) and self.counter%2 == 1:
                self.counter += 1
                self.colour = BLUE
        # Dopo 11 secondi resetta il fantasma allo stato di "Chase"
        if (time.clock()-self.initial_time) > 9.0:
            self.state = "Chase"
            self.modifier = 1
            self.colour = self.set_colour()
            self.app.player.counter = 1
    
    # Chiama la funzione per muoversi in base allo stato o al nome del fantasma
    def move(self):
        if self.state == "Frightened" and self.outside:
            self.frightened()
        elif self.state == "Eaten":
            self.choose_direction(vec(13.5, 14))
        else:
            if self.name == "Clyde":
                target_pos = self.chase_clyde()
            elif self.name == "Pinky":
                target_pos = self.chase_pinky()
            elif self.name == "Inky":
                target_pos = self.chase_inky()
            elif self.name == "Blinky":
                target_pos = self.chase_blinky()
            self.choose_direction(target_pos)
    
    # Funzione che disegna il fantasma sullo schermo
    # La seconda draw viene usata quando un fantasma viene mangiato
    def draw(self):
        if self.state == "Eaten":
            pygame.draw.circle(self.app.screen, self.colour, 
                           (int(self.pix_pos.x), int(self.pix_pos.y)), self.app.cell_width//2-2, 1)
        else:
            pygame.draw.circle(self.app.screen, self.colour, 
                           (int(self.pix_pos.x), int(self.pix_pos.y)), self.app.cell_width//2-2)
        
    
    '''
    Nel caso in cui due o più direzioni danno stesso valore delta,
    l'ordine di scleta di quale direzione prendere è
    Sopra -> Sinistra -> Sotto -> Destra
    '''
            
    # Quando sono spaventati, prenderanno una direzione diversa da quella da cui vengono
    # Per decidere quale direzione prende, si sceglie una direzione inziale
    # Nel caso in cui non vada bene, si ruota in senso antiorario
    def frightened(self):
        directions = [vec(0, -1), vec(-1, 0), vec(0, 1), vec(1, 0)]
        starting_idx = random.randint(0, 3) 
        actual_pos = self.grid_pos+self.direction
        for i in range(4):
            direction = directions[(starting_idx + i) % 4]
            if self.can_move_certain_direction(actual_pos, direction) and actual_pos+direction != self.grid_pos:
                self.stored_direction = direction
        
    # Decide quale direzione deve prendere il fantasma usando la posizione target che deve raggiungere
    # Esclude la direzione da cui il fantasma proviene
    def choose_direction(self, target_pos):
        distances = []
        directions = [vec(0, -1), vec(-1, 0), vec(0, 1), vec(1, 0)]
        # Controllo se il fantasma è al di fuori della zona di spawn oppure no
        # Se si` considero come posizione effettuiva la sua posizione più la sua direzione
        # Altrimenti considero la sua posizione effettiva
        if (not self.outside) or (not self.can_move()):
            actual_pos = self.grid_pos
        else:
            actual_pos = self.grid_pos+self.direction
        for direction in directions:
            # Controllo se si può muovere in una direzione, e se si` calcolo la distanza dalla casella target
            if self.can_move_certain_direction(actual_pos, direction) and self.direction != (-1*direction):
                # Se il fantasma si trova nella casella (14, 6), considera la posizione (14, 33) per
                # Calcolare la distanza effettiva dalla casella target
                if (actual_pos == vec(14, 6)) and direction == self.app.crossroad_L:
                    next_pos = vec(14, 33)
                # Se il fantasma si trova nella casella (14, 21), considera la posizione (14, -6) per
                # Calcolare la distanza effettiva dalla casella target
                elif (actual_pos == vec(14, 21)) and direction == self.app.crossroad_R:
                    next_pos = vec(14, -6)
                else:
                    next_pos = actual_pos+direction
                distances.append(round((next_pos.x-target_pos.x)**2+((next_pos.y-target_pos.y))**2))
            else:
                distances.append(3000)
        # Cerco l'indice dell'elemento con distanza minore, e lo uso per deicdere(0:)
        m = numpy.argmin(distances)
        if m == 0:
            self.stored_direction = vec(0, -1)
        elif m == 1:
            self.stored_direction = vec(-1, 0)
        elif m == 2:
            self.stored_direction = vec(0, 1)
        elif m == 3:
            self.stored_direction = vec(1, 0)
            
    # Clyde cerca di raggiungere la posizione in cui si trova il player
    def chase_clyde(self):
        if self.grid_pos == (13, 11) or self.grid_pos == (14, 11):
            self.outside = True
        if not self.outside:
            target_pos = vec(13, 11)
        else:
            target_pos = self.app.player.grid_pos
        return target_pos
        
    # Pinky punta 4 caselle in avanti rispetto a dove è il player
    # Ne considera la direzione, e se il player guarda su, il fantasma guardera` 4 caselle su e 4 a sinistra
    # (Behaviur dovuto ad un bug nelle prive versioni arcade)
    def chase_pinky(self):
        if self.grid_pos == (13, 11) or self.grid_pos == (14, 11):
            self.outside = True
        if not self.outside:
            target_pos = vec(13, 11)
        else:
            target_pos = self.app.player.grid_pos+(self.app.player.direction*4)
            if self.app.player.direction == vec(0, -1):
                target_pos += vec(-4, 0)
        return target_pos
    
    # Inky consuidera una casella avanti al player, punta una freccia da quella casella verso Clyde, e poi la ruota di 180 gradi
    # Ne considera la direzione, e se il player guarda su, il fantasma guardera` 4 caselle su e 4 a sinistra
    # (Behaviur dovuto ad un bug nelle prive versioni arcade)
    def chase_inky(self):
        if self.grid_pos == (13, 11) or self.grid_pos == (14, 11):
            self.outside = True
        if not self.outside:
            target_pos = vec(13, 11)
        else:
            cell_pos = self.app.player.grid_pos+self.app.player.direction*2
            if self.app.player.direction == vec(0, -1):
                cell_pos += vec(-2, 0)
            offset = cell_pos-self.app.enemies[0].grid_pos
            target_pos = self.app.enemies[0].grid_pos+(2*offset)
        return target_pos
    
    # Blinky si comporta come Clyde, ma se è troppo vicino al plaver (8 blocchi di raggio), punta alla casella (30, 0)
    def chase_blinky(self):
        if self.grid_pos == (13, 11) or self.grid_pos == (14, 11):
            self.outside = True
        if not self.outside:
            target_pos = vec(13, 11)
        else:
            if (self.grid_pos.x-self.app.player.grid_pos.x)**2+(self.grid_pos.x-self.app.player.grid_pos.y)**2 > 64:
                target_pos = self.app.player.grid_pos
            else:
                target_pos = vec(30, -1)
        return target_pos
    
########## HELPER FUNCTIONS ##########
       
    # Recupera dal file "setting.py" le coordinate da cui i fantasmi devono partire
    def get_grid_pos(self):
        if self.number == 0:
            return copy.deepcopy(CLYDE_START_POS)
        elif self.number == 1:
            return copy.deepcopy(PINKY_START_POS)
        elif self.number == 2:
            return copy.deepcopy(INKY_START_POS)
        elif self.number == 3:
            return copy.deepcopy(BLINKY_START_POS)
        
    # Calcola la posizione in cui deve disegnare il fantasma
    def get_pix_pos(self):
        draw_pos_x = self.grid_pos.x*self.app.cell_width+TOP_BOTTOM_BUFFER//2+self.app.cell_width//2
        draw_pos_y = self.grid_pos.y*self.app.cell_height+TOP_BOTTOM_BUFFER//2+self.app.cell_height//2
        return vec(draw_pos_x, draw_pos_y)
    
    # Seleziona dal file "settings.py" il colore del fantasma
    def set_colour(self):
        if self.number == 0:
            return CLYDE_C
        elif self.number == 1:
            return PINKY_C
        elif self.number == 2:
            return INKY_C
        elif self.number == 3:
            return BLINKY_C
    
    # Controlla se il fantasma può muoversi
    # (controlla se si trova al centro della casella della griglia)
    def time_to_move(self):
        if int(self.pix_pos.x+TOP_BOTTOM_BUFFER//2) % self.app.cell_width == 0:
            if self.direction == vec(1, 0) or self.direction == vec(-1, 0):
                return True
        if int(self.pix_pos.y+TOP_BOTTOM_BUFFER//2) % self.app.cell_height == 0:
            if self.direction == vec(0, 1) or self.direction == vec(0, -1):
                return True
    
    # Funzione che trasforma in stringa l'array delle distanze delta
    def distances_array_print(self, distances):
        n = len(distances)
        string = "{"
        for key, distance in enumerate(distances):
            if key == 0:
                string += str(key)+"(Up):"+str(distance)
            if key == 1:
                string += str(key)+"(Left):"+str(distance)
            if key == 2:
                string += str(key)+"(Down):"+str(distance)
            if key == 3:
                string += str(key)+"(Right):"+str(distance)
            if key+1 != n:
                string += "; "
        return string
    
########## CONDITION CHECK FUNCTIONS ##########
    
    # Controlla se il fantasma si può muovere in una certa direzione
    def can_move_certain_direction(self, position, direction):
        if vec(position+direction) in self.app.walls:
            if vec(position+direction) in self.app.barrier and ((not self.outside) or self.state == "Eaten"):
                return True
            else:
                return False
        return True
    
    # Controllase il fantasma può continuare a muoversi di due passi in una certa direzione
    def can_move_next(self):
        if vec(self.grid_pos+(self.direction*2)) in self.app.walls:
            if vec(self.grid_pos+(self.direction*2)) in self.app.barrier and ((not self.outside) or self.state == "Eaten"):
                return True
            else:
                return False
        return True
    
    # Controlla se il fantasma può continuare a muoversi di un passo in una certa direzione
    def can_move(self):
        if vec(self.grid_pos+self.direction) in self.app.walls:
            if vec(self.grid_pos+self.direction) in self.app.barrier and ((not self.outside) or self.state == "Eaten"):
                return True
            else:
                return False
        return True
    
    # Controllo se il fantasma si trova su un'intersezione
    def check_intersection(self):
        if self.grid_pos in self.app.crossroads:
            return True
        if self.grid_pos == self.app.crossroad_L or self.grid_pos == self.app.crossroad_R:
            return True
        if (self.grid_pos == vec(13, 11) or self.grid_pos == vec(14, 11)) and self.state == "Eaten":
            return True
        return False
    
    # Controllo se il fantasma si trova vicino ad un'intersezione
    def check_intersection_near(self):
        if self.grid_pos+self.direction in self.app.crossroads:
            return True
        if self.grid_pos+self.direction == self.app.crossroad_L or self.grid_pos+self.direction == self.app.crossroad_R:
            return True
        if (self.grid_pos+self.direction == vec(13, 11) or self.grid_pos+self.direction == vec(14, 11)) and self.state == "Eaten":
            return True
        return False