# module_8_ppo_agent.py
# pip install stable-baselines3 gymnasium

import numpy as np
try:
    import gymnasium as gym
except Exception:
    import gym as gym  # fallback if older gym

from gym.spaces import Box, Discrete
from stable_baselines3 import PPO

class TinyTradingEnv(gym.Env):
    """A toy trading environment for demonstration (NOT for live trading)."""
    metadata = {'render.modes': ['human']}
    def __init__(self, prices: np.ndarray, window=10):
        super().__init__()
        self.prices = prices
        self.window = window
        self.idx = window
        self.action_space = Discrete(3)  # 0: hold, 1: long, 2: short
        self.observation_space = Box(low=-np.inf, high=np.inf, shape=(window,), dtype=np.float32)
        self.position = 0  # -1, 0, +1
        self.entry_price = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.idx = self.window
        self.position = 0
        self.entry_price = None
        obs = self.prices[self.idx-self.window:self.idx].astype(np.float32)
        return obs, {}

    def step(self, action):
        reward = 0.0
        price = self.prices[self.idx]
        if action == 1 and self.position != 1:  # go long
            self.position = 1; self.entry_price = price
        elif action == 2 and self.position != -1:  # go short
            self.position = -1; self.entry_price = price
        elif action == 0:  # flat/hold -> realize PnL if we had a position for 1 step
            if self.entry_price is not None:
                reward = (price - self.entry_price) * self.position
                self.position = 0; self.entry_price = None
        self.idx += 1
        done = self.idx >= len(self.prices)
        obs = self.prices[self.idx-self.window:self.idx].astype(np.float32) if not done else np.zeros(self.window, dtype=np.float32)
        return obs, float(reward), done, False, {}

def train_ppo_on_prices(prices):
    env = TinyTradingEnv(prices)
    model = PPO("MlpPolicy", env, verbose=0)
    model.learn(total_timesteps=2000)
    return model

if __name__ == "__main__":
    prices = np.cumsum(np.random.randn(200)).astype(np.float32) + 100.0
    model = train_ppo_on_prices(prices)
    print("PPO trained on toy environment.")
