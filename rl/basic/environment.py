import logging as log


class environment(object):

    def __init__(self, **kwargs):
        log.info("__init__")
        pass

    def get_reward(self, **kwargs):
        log.info("get_reward")
        pass

    def take_action(self, **kwargs):
        log.info("take_action")
        pass
