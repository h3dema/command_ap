import logging as log
from basic.environment import environment

log.basicConfig(level=log.INFO)

if __name__ == "__main__":
    e = environment()
    e.get_reward()
    e.take_action()
