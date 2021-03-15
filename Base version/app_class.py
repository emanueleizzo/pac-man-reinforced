import pygame
import sys
import copy
import time
from settings import *
from player_class import *
from enemy_class import *

vec = pygame.math.Vector2

class App:
    # Costruttore
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'start'
        self.cell_width = MAZE_WIDTH//28
        self.cell_height = MAZE_HEIGHT//31
        self.walls = []
        self.barrier = []
        self.dots = []
        self.pellets = []
        self.crossroads = []
        self.crossroad_L = None
        self.crossroad_R = None
        self.total_dots = 0
        self.enemies = []
        self.enemies_names = ["Clyde", "Pinky", "Inky", "Blinky"]
        self.load()
        self.player = Player(self)
        self.make_enemies()

    # Funzione run: definisce cosa deve fare il gioco in base allo stato in cui si trova
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            if self.state == "start":
                self.start_events()
                self.start_update()
                self.start_draw()
            elif self.state == "playing":
                self.playing_events()
                self.playing_update()
                self.playing_draw()
            elif self.state == "game over":
                self.game_over_events()
                self.game_over_update()
                self.game_over_draw()
            elif self.state == "victory":
                self.victory_events()
                self.victory_update()
                self.victory_draw()
            else:
                self.running = False
        pygame.quit()
        sys.exit()

########## HELPER FUNCTIONS ##########

    # Disegna il testo sullo schermo nella posizione indicata
    # Viene usato il colore e il font passati come parametri
    def draw_text(self, words, screen, pos, size, colour, font_name, centered=False):
        font = pygame.font.SysFont(font_name, size)
        text = font.render(words, False, colour)
        text_size = text.get_size()
        if centered:
            pos[0] = pos[0]-text_size[0]//2
            pos[1] = pos[1]-text_size[1]//2
        screen.blit(text, pos)

    # Carica l'immagine "maze.png" e legge il file "walls.txt"
    # Traduce il file "walls.txt" in informazioni riguardo il labirinto
    def load(self):
        self.background = pygame.image.load("maze.png")
        self.background = pygame.transform.scale(self.background, (MAZE_WIDTH, MAZE_HEIGHT))
        # Identifica i punti importanti della mappa 
        # (pareti, barriera, incroci, dots, pellets)
        with open("walls.txt", "r") as file:
            for yidx, line in enumerate(file):
                for xidx, char in enumerate(line):
                    if char in ["1", "B"]:
                        self.walls.append(vec(xidx, yidx))
                        if char == "B":
                            self.barrier.append(vec(xidx, yidx))
                    elif char in ["D", "X", "L", "R", "P"]:
                        self.total_dots += 1
                        if char == "P":
                            self.pellets.append(vec(xidx, yidx))
                        else:
                            self.dots.append(vec(xidx, yidx))
                            if char == "X":
                                self.crossroads.append(vec(xidx, yidx))
                            elif char == "L":
                                self.crossroad_L = vec(xidx, yidx)
                            elif char == "R":
                                self.crossroad_R = vec(xidx, yidx)
                    elif char == "Y":
                        self.crossroads.append(vec(xidx, yidx))
                 
    # Crea gli oggetti "enemies" (i fantasmi)
    def make_enemies(self):
        for ind, name in enumerate(self.enemies_names):
            # Se il fantasma si chiama "Clyde" allora si trova all'esterno della 
            # Zona di spawn, altrimenti si trova all'intero della zona di spawn
            if name == "Clyde":
                self.enemies.append(Enemy(self, name, ind, True))
            else:
                self.enemies.append(Enemy(self, name, ind, False))

    # Resetta il gioco
    def reset(self):
        self.player = None
        self.enemies = []
        self.player = Player(self)
        self.make_enemies()
        self.load()
        self.state = "playing"

########## INTRO FUNCTIONS ##########

    def start_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.state = "playing"

    def start_update(self):
        pass

    def start_draw(self):
        self.screen.fill(BLACK)
        self.draw_text("PUSH SPACE BAR", self.screen, [
                       WIDTH//2, HEIGHT//2-50], START_TEXT_SIZE, (170, 132, 58), START_FONT, centered=True)
        self.draw_text("1 PLAYER ONLY", self.screen, [
                       WIDTH//2, HEIGHT//2+50], START_TEXT_SIZE, (44, 167, 198), START_FONT, centered=True)
        self.draw_text("HIGH SCORE", self.screen, [4, 0],
                       START_TEXT_SIZE, (255, 255, 255), START_FONT)
        pygame.display.update()

########## PLAYING FUNCTIONS ##########

    def playing_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.player.move(vec(-1, 0))
                if event.key == pygame.K_RIGHT:
                    self.player.move(vec(1, 0))
                if event.key == pygame.K_UP:
                    self.player.move(vec(0, -1))
                if event.key == pygame.K_DOWN:
                    self.player.move(vec(0, 1))

    def playing_update(self):
        # Effettua l'udpate del player
        self.player.update()
        # Effettua lúpdate dei fantasmi
        for enemy in self.enemies:
            # Se il fantasma si chiama Inky e sono stati mangiati meno di 30 dots
            # Allora il fantasma non può essere aggiornato
            if enemy.name == "Inky" and self.player.eaten_dots < 30:
                enemy.update_state_only()
            # Se il fantasma si chiama Inky e sono stati mangiati meno di 1/3 dei dots
            # Allora il fantasma non può essere aggiornato
            elif enemy.name == "Blinky" and self.player.eaten_dots < self.total_dots//3:
                enemy.update_state_only()
            else:
                enemy.update()
            # Se il fantasma ènella stessa casella del player
            if self.player.grid_pos == enemy.grid_pos:
                # Se il fantasma è nello stato di "Chase"
                # Allora viene tolta una vita al player
                if enemy.state == "Chase":
                    self.remove_life()
                # Se il fantasma è nello stato di "Frightened"
                # Allora il fantasma viene mangiato
                elif enemy.state == "Frightened":
                    self.player.eat_enemy(enemy)
        # Se il player ha mangiato tutti i dots, allora il player ha vinto
        if self.player.eaten_dots == self.total_dots:
            self.state = "victory"

    def playing_draw(self):
        self.screen.fill(BLACK)
        self.screen.blit(self.background, (TOP_BOTTOM_BUFFER//2, TOP_BOTTOM_BUFFER//2))
        self.draw_dots()
        self.draw_pellets()
        self.draw_text("CURRENT SCORE: {}".format(self.player.current_score),
                       self.screen, [60, 0], 18, WHITE, START_FONT)
        self.player.draw()
        for enemy in self.enemies:
            enemy.draw()
        pygame.display.update()

    # Rimuove una vita al player e riposiziona player e fantasmi
    # Se le vite del player vanno a 0, allora il giocatore perdfe
    def remove_life(self):
        self.player.lives -= 1
        if self.player.lives == 0:
            self.state = "game over"
        else:
            self.player.grid_pos = copy.deepcopy(self.player.starting_pos)
            self.player.pix_pos = self.player.get_pix_pos()
            self.player.direction = vec(1, 0)
            for enemy in self.enemies:
                enemy.grid_pos = vec(enemy.starting_pos)
                enemy.pix_pos = enemy.get_pix_pos()
                enemy.direction = vec(1, 0)
                if enemy.name == "Clyde":
                    enemy.outside = True
                else:
                    enemy.outside = False
    
    def draw_dots(self):
        for dot in self.dots:
            pygame.draw.circle(self.screen, DOT_PELLET_COLOUR,
                               (int(dot.x*self.cell_width)+self.cell_width//2+TOP_BOTTOM_BUFFER//2,
                                int(dot.y*self.cell_height)+self.cell_height//2+TOP_BOTTOM_BUFFER//2), 2)
            
    def draw_pellets(self):
        for pellet in self.pellets:
            pygame.draw.circle(self.screen, DOT_PELLET_COLOUR,
                               (int(pellet.x*self.cell_width)+self.cell_width//2+TOP_BOTTOM_BUFFER//2,
                                int(pellet.y*self.cell_height)+self.cell_height//2+TOP_BOTTOM_BUFFER//2), 4)

########## GAME OVER FUNCTIONS ##########

    def game_over_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.reset()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def game_over_update(self):
        pass

    def game_over_draw(self):
        self.screen.fill(BLACK)
        quit_text = "Press the escape button to QUIT"
        again_text = "Press SPACE bar to PLAY AGAIN"
        self.draw_text("GAME OVER", self.screen, [WIDTH//2, 100],  52, RED, "arial", centered=True)
        self.draw_text(again_text, self.screen, [
                       WIDTH//2, HEIGHT//2],  36, (190, 190, 190), "arial", centered=True)
        self.draw_text(quit_text, self.screen, [
                       WIDTH//2, HEIGHT//1.5],  36, (190, 190, 190), "arial", centered=True)
        pygame.display.update()
        
########## VICTORY FUNCTIONS ##########

    def victory_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.reset()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def victory_update(self):
        pass

    def victory_draw(self):
        self.screen.fill(BLACK)
        quit_text = "Press the escape button to QUIT"
        again_text = "Press SPACE bar to PLAY AGAIN"
        self.draw_text("VICTORY!", self.screen, [WIDTH//2, 100],  52, VICTORY_COLOUR, "arial", centered=True)
        self.draw_text(again_text, self.screen, [
                       WIDTH//2, HEIGHT//2],  36, (190, 190, 190), "arial", centered=True)
        self.draw_text(quit_text, self.screen, [
                       WIDTH//2, HEIGHT//1.5],  36, (190, 190, 190), "arial", centered=True)
        pygame.display.update()