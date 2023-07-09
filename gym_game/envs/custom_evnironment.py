import gym
from gym import spaces
from gym_game.envs.pygame_2d import Pygame2D
import numpy as np

np.random.seed(42)

frame_skip = 4

class CustomEnv(gym.Env):
    def __init__(self):
        self.pygame             = Pygame2D()
        self.action_space       = spaces.Discrete(12)
        self.observation_space  = spaces.Box(low = 0, high = 255, shape = (300,300,3), dtype=np.uint8)

    def reset(self):
        del self.pygame
        self.pygame = Pygame2D()
        obs = self.pygame.observe()
        return obs
    
    '''
    The step function accepts a list comprising two actions. The initial element represents the action taken by the green player, 
    which is the player controlled by our agent.
    The second element corresponds to the action undertaken by the red player, who serves as the opponent.
    '''
    def step(self, actions):
        rewards = np.array([0, 0], dtype=np.int32)
        for _ in range(frame_skip):
            self.pygame.action(actions)
            obs = self.pygame.observe()
            rewards += self.pygame.evaluate()
            done, victory = self.pygame.is_done()
            if self.pygame.screen != None:
                self.pygame.view()
                if done and victory!="Tie" and victory!=None:
                    #Death animations
                    for _ in range(32):
                        self.pygame.view()
            if done:
                return obs, rewards, done, {"victory": victory}
        if np.array_equal(rewards, [0, 0]):
            rewards += np.array([-5, -5])
        return obs, rewards, done, {"victory": victory}

    def render(self, mode="human", close=False):
        self.pygame.view()

    def close(self):
        self.pygame.close()