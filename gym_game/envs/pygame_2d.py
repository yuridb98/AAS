import pygame
import os
import csv
import numpy as np
import os

SCREEN_WIDTH = 300
SCREEN_HEIGHT = 300

#define game variables
GRAVITY = 0.75
ROWS = 20
COLS = 20
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 20
LEVEL = 0

#define colours
BG = (145, 200, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

#scale
SCALE_BULLET = 1.1
SCALE_GRENADE = 0.9

#load images
#store tiles in a list
#tiles will 'decorate' the map, here we just load them
img_list = []
for x in range(TILE_TYPES):
	img = pygame.image.load(f'gym_game/envs/img/tile/{x}.png')
	img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	img_list.append(img)

#function to draw text on surface
def draw_text(text, text_col, x, y, disp, size):
	font = pygame.font.SysFont('Futura', size)
	img = font.render(text, True, text_col)
	disp.blit(img, (x, y))

#draw background on the surface
def draw_bg(disp):
	disp.fill(BLACK)

'''
Soldier is the class for both players, 
it implements all the functions we need to make them able to move, shoot, check if they are alive and so on...
'''
class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, direction, ammo, grenades=5):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.ammo = ammo
		self.start_ammo = ammo
		self.shoot_cooldown = 0
		self.grenades = grenades
		self.start_grenades = self.grenades
		self.health = 100
		self.max_health = self.health
		self.direction = direction
		if direction == 1:
			self.flip = False
		elif direction == -1:
			self.flip = True
		self.vel_y = 0
		self.jump = False
		self.moving_left = False
		self.moving_right = False
		self.grenade_thrown = False
		self.in_air = False
		self.animation_list = []
		self.frame_index = 0
		self.action = 0
		self.consecutive_equal_action = 0
		self.update_time = pygame.time.get_ticks()

		#load all images for the players
		animation_types = ['Idle', 'Run', 'Jump', 'Death']

		for animation in animation_types:
			#reset temporary list of images
			temp_list = []
			#count number of files in the folder
			num_of_frames = len(os.listdir(f'gym_game/envs/img/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(f'gym_game/envs/img/{self.char_type}/{animation}/{i}.png')
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.animation_list.append(temp_list)

		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x,y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
	
	def update(self, world):
		self.update_animation()
		self.check_alive()
		if self.alive:
			if self.in_air:
				self.update_action(2)#2: jump
			elif self.moving_left or self.moving_right:
				self.update_action(1)#1: run
			else:
				self.update_action(0)#0: idle

			self.move(world)
		#update cooldown
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1
	
	def throw_grenade(self, index):
		if self.grenade_thrown == False and self.grenades > 0:
				Grenade(self.rect.centerx + (0.5 * self.rect.size[0] * self.direction),\
						self.rect.top, self.direction, index)
				self.grenade_thrown = True
				#reduce grenades
				self.grenades -= 1
	
	def move(self, world):
		#reset movement variables
		dx = 0
		dy = 0
		#assign movement variables if moving left or right
		if self.moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if self.moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1
		#check inside the screen
		if self.rect.left + dx < 0:
			dx = -self.rect.left
		elif self.rect.right + dx > SCREEN_WIDTH:
			dx = SCREEN_WIDTH - self.rect.right

		#jump
		if self.jump == True and self.in_air == False:
			self.vel_y = -9
			self.jump = False
			self.in_air = True

		#apply gravity
		self.vel_y += GRAVITY
		if self.vel_y > 10:
			self.vel_y = 10
		dy += self.vel_y

		#check for collision 
		for tile in world.obstacle_list:
			#check collision in x direction
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0
			#check for collusion in y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				#check if below the ground, i.e jumping
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#check if above the ground, i.e. falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom
			
		#check inside the screen
		if self.rect.left + dx < 0:
			dx = -self.rect.left
		elif self.rect.right + dx > SCREEN_WIDTH:
			dx = SCREEN_WIDTH - self.rect.right
		

		#update rectangle position
		self.rect.x += dx
		self.rect.y += dy
	
	def update_animation(self):
		#update animation
		ANIMATION_COOLDOWN = 80
		#update image depending on current frame
		self.image = self.animation_list[self.action][self.frame_index]
		#check if enough time has passed since the las update
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1
		#if the animation has run out the reset back to the start
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action])-1
			else:
				self.frame_index = 0

	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 45
			self.ammo -= 1
			Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
		
	def update_action(self, new_action):
		#check if the new action is different to the previous one
		if new_action != self.action:
			self.action = new_action
			#update the animation settings
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()
	
	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)

	def draw(self, disp):
		disp.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


'''
HealthBar is just the class for player healthbar, we need it to keep track of the actual health of the players and we update it on the surface
every time one of them is hit
'''
class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health
	
	def draw(self, health, screen):
		self.health = health

		ratio = self.health / self.max_health
		pygame.draw.rect(screen, BLACK, (self.x-2, self.y-2, 40, 10))
		pygame.draw.rect(screen, RED, (self.x, self.y, 36, 6))
		pygame.draw.rect(screen, GREEN, (self.x, self.y, 36 * ratio, 6))

'''
Every bullet is an istance of class Bullet, we add them in bullet_group in order to check their actual position and so also
when they hit a player or go out of the screen
'''
bullet_group = pygame.sprite.Group()
class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		self.group = bullet_group
		pygame.sprite.Sprite.__init__(self, self.group)
		self.speed = 5
		image = pygame.image.load('gym_game/envs/img/icons/bullet.png')
		self.image = pygame.transform.scale(image, (int(image.get_width() * SCALE_BULLET), int(image.get_height() * SCALE_BULLET)))
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self, world):
		#move bullet
		self.rect.x += (self.direction * self.speed)

		#check if bullet has gone off screen
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			self.kill()

		#check for collision with level
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()
	
		
	def check_collision(self, players):
		rewards = [0, 0]
		#check collision with characters
		for i, player in enumerate(players):
			if pygame.Rect.colliderect(player.rect, self.rect):
				self.kill()
				if player.alive:
					player.health -= 25
					if player.health <= 0:
						player.alive = False
					if i==0:
						rewards[0] += -50
						rewards[1] += 100
					elif i==1:
						rewards[0] += 100
						rewards[1] += -50
			if np.abs(player.rect.center[0] - self.rect.center[0]) <= (TILE_SIZE // 2) and np.abs(player.rect.center[1] - self.rect.center[1]) >= TILE_SIZE:
				if i==0:
					rewards[0] += 50
				elif i==1:
					rewards[1] += 50

		return rewards


'''
Grenade class and grenade_group work the same as Bullet and bullet_group, but of course for grenades
'''
grenade_group = pygame.sprite.Group()
class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction, belongto):
		self.group = grenade_group
		pygame.sprite.Sprite.__init__(self, self.group)
		self.timer = 40
		self.vel_y = -8
		self.speed = 6
		image = pygame.image.load('gym_game/envs/img/icons/grenade.png')
		self.image = pygame.transform.scale(image, (int(image.get_width() * SCALE_GRENADE), int(image.get_height() * SCALE_GRENADE)))
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction
		self.belongto = belongto
	
	def update(self, world):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y

		#check for collision with level
		for tile in world.obstacle_list:
			#check collision with walls
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				self.speed = self.speed // 1.75
				self.direction *= -1
				dx = self.direction * self.speed
			#check for collusion in y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.speed = self.speed//1.5
				#check if below the ground
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#check if above the ground
				elif self.vel_y >= 0:
					self.vel_y = 0
					dy = tile[1].top - self.rect.bottom
	
		
		#update grenade position
		self.rect.x += dx
		self.rect.y += dy

	def check_collision(self, players):
		#countdown timer
		rewards = [0, 0]
		self.timer -= 1
		if self.timer <= 0:
			self.kill()
			players[self.belongto].grenade_thrown = False
			Explosion(self.rect.x, self.rect.y, 0.25)
			#do damage to anyone that is nearby
			for i, player in enumerate(players):
				if abs(self.rect.centerx - player.rect.centerx) < 2 * TILE_SIZE and\
					abs(self.rect.centery - player.rect.centery) < 2 * TILE_SIZE:
						player.health += -50
						if player.health <= 0:
							player.alive = False
						if i == 0:
							rewards[0] += -100
							rewards[1] += 200
						elif i == 1:
							rewards[0] += 200
							rewards[1] += -100
		
		return rewards
		

'''
We use Explosion class and explosion_group just to animate all the grenade explo
'''
explosion_group = pygame.sprite.Group()
class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		self.group = explosion_group
		pygame.sprite.Sprite.__init__(self, self.group)
		self.images = []
		for num in range(1, 6):
			img = pygame.image.load(f"gym_game/envs/img/explosion/exp{num}.png")
			img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
			self.images.append(img)
		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0
	
	def update(self):
		EXPLOSION_SPEED = 3
		#update explosion animation
		self.counter += 1
		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index += 1
			#if the animation is completed then delete the explosion
			if self.frame_index >= len(self.images):
				self.kill()
			else:
				self.image = self.images[self.frame_index]

		
class World():
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		#iterate through each values in level data file
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile >= 0:
					img = img_list[tile]
					img_rect = img.get_rect()
					img_rect.x = x * TILE_SIZE
					img_rect.y = y * TILE_SIZE
					tile_data = (img, img_rect)
					if tile <= 8:
						self.obstacle_list.append(tile_data)
					elif tile == 15:
						player = Soldier(char_type='player', x=x*TILE_SIZE, y=y*TILE_SIZE, scale=1, speed=2, direction=1, ammo=10)
						health_bar_player = HealthBar(65, 10, player.health, player.max_health)
					elif tile == 16:
						enemy = Soldier(char_type='enemy', x=x*TILE_SIZE, y=y*TILE_SIZE, scale=1, speed=2, direction=-1, ammo=10)
						health_bar_enemy = HealthBar((SCREEN_WIDTH // 2 + 65), 10, enemy.health, enemy.max_health)

		return player, health_bar_player, enemy, health_bar_enemy
	
	def draw(self,disp):
		for tile in self.obstacle_list:
			disp.blit(tile[0], tile[1])


def loadLevel():
    world_data = []
    for row in range(ROWS):
        r = [-1] * COLS
        world_data.append(r)

    #load in level data and create world
    with open(f'gym_game/envs/levels/level{LEVEL}_data.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for x, row in enumerate(reader):
            for y, tile in enumerate(row):
                world_data[x][y] = int(tile)
	
    return world_data

#Game
class Pygame2D:
	def __init__(self):
		pygame.init()
		self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
		self.clock = pygame.time.Clock()
		self.screen = None
		world_data = loadLevel()
		self.world = World()
		player, health_bar_player, enemy, health_bar_enemy = self.world.process_data(world_data)
		self.players = [player, enemy]
		self.health_bars = [health_bar_player, health_bar_enemy]
		self.fps = 60
		self.done = False
		self.draw(self.surface)
		for grenade in grenade_group:
			grenade.kill()
		for bullet in bullet_group:
			bullet.kill()
		for explosion in explosion_group:
			explosion.kill()


	def action(self, actions):
		for i, action in enumerate(actions):
			if self.players[i].alive:
				self.players[i].jump = False
				self.players[i].moving_right = False
				self.players[i].moving_left = False
				if action == 0:# None
					pass
				elif action == 1:# Jump
					self.players[i].jump = True
				elif action == 2:# Right
					self.players[i].moving_right = True
				elif action == 3:# Left
					self.players[i].moving_left = True
				elif action == 4:# Shoot
					self.players[i].shoot()
				elif action == 5:# Jump and right
					self.players[i].jump = True
					self.players[i].moving_right = True
				elif action == 6:# Jump and left
					self.players[i].jump = True
					self.players[i].moving_left = True
				elif action == 7:# Jump and shoot
					self.players[i].jump = True
					self.players[i].shoot()
				elif action == 8:# Right and shoot
					self.players[i].moving_right = True
					self.players[i].shoot()
				elif action == 9:# Left and shoot
					self.players[i].moving_left = True
					self.players[i].shoot()
				elif action == 10:# Jump, right and shoot
					self.players[i].jump = True
					self.players[i].moving_right = True
					self.players[i].shoot()
				elif action == 11:# Jump, left and shoot
					self.players[i].jump = True
					self.players[i].moving_left = True
					self.players[i].shoot()
				elif action == 12:# Grenade
					self.players[i].throw_grenade(index = i)
				
				
			
	def evaluate(self):
		rewards = np.array([0, 0], dtype=np.int32)

		#check bullet collision
		for bullet in bullet_group:
			rewards += bullet.check_collision(self.players)
		
		#check grenade collision
		for grenade in grenade_group:
			rewards += grenade.check_collision(self.players)

		if not self.players[0].alive:
			return [-1000, int(4000 * self.players[1].health/self.players[1].max_health)]
		if not self.players[1].alive:
			return [int(4000 * self.players[0].health/self.players[0].max_health), -1000]

		return rewards

	def is_done(self):
		if not self.players[0].alive and not self.players[1].alive:
			return True, "Tie"
		if not self.players[0].alive:
			return True, "Player 2"
		if not self.players[1].alive:
			return True, "Player 1"
		if len(bullet_group)>0:
			return False, None
		if len(grenade_group)>0:
			return False, None
		if self.players[0].ammo == 0 and self.players[1].ammo == 0:
			return True, "Tie"
		return False, None
	
	def draw(self, display):
		draw_bg(display)
		bullet_group.update(self.world)
		grenade_group.update(self.world)
		explosion_group.update()
		self.world.draw(display)
		bullet_group.draw(display)
		grenade_group.draw(display)
		explosion_group.draw(display)
		for i, player in enumerate(self.players):
			player.update(self.world)
			player.draw(display)
			draw_text(f'Player {i+1}: ', WHITE, (SCREEN_WIDTH // 2)*i + 5, 5, display, 20)
			self.health_bars[i].draw(player.health, display)
			#show ammo
			draw_text(f'Ammo: {player.ammo}', WHITE, (SCREEN_WIDTH // 2)*i + 5, 20, display, 16)
			#show grenades
			#draw_text(f'Grenades: {player.grenades}', WHITE, (SCREEN_WIDTH // 2)*i + 5, 35, display, 16)

	def observe(self):
		self.draw(self.surface)
		img = pygame.surfarray.array3d(self.surface)
		img = img.swapaxes(0,1)
		return np.array(img) 

	def view(self):
		if self.screen == None:
			self.screen = pygame.display.set_mode((SCREEN_HEIGHT, SCREEN_WIDTH))
		self.draw(self.screen)
		pygame.display.update()
		self.clock.tick(self.fps)
		
	
	def close(self):
		self.screen = None
		pygame.display.quit()