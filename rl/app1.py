import logging as log
from basic.environment import environment


if __name__ == "__main__":
    log.basicConfig(level=log.INFO)

    e = environment()
    e.get_reward()
    e.take_action()
