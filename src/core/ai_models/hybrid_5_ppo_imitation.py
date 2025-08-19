# hybrid_5_ppo_imitation.py
# Train PPO in a sim env, collect (state, action), fit a fast classifier to imitate.

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from module_8_ppo_agent import TinyTradingEnv
from stable_baselines3 import PPO

def collect_expert_dataset(model, env, episodes=10):
    X, y = [], []
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            X.append(obs.copy()); y.append(action)
            obs, reward, done, _, _ = env.step(action)
    return np.array(X), np.array(y)

def train_imitation(prices):
    env = TinyTradingEnv(prices)
    expert = PPO("MlpPolicy", env, verbose=0)
    expert.learn(total_timesteps=2000)
    X, y = collect_expert_dataset(expert, env, episodes=5)
    clf = RandomForestClassifier(n_estimators=200, random_state=42).fit(X, y)
    return clf

if __name__ == "__main__":
    prices = np.cumsum(np.random.randn(300)).astype(np.float32)+100
    clf = train_imitation(prices)
    print("Trained imitation classifier from PPO rollouts.")
