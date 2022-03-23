from logger import logger
class Hook:
    def __init__(self):
        self.hook = []
    def regist(self, func):
        self.hook.append(func)
    def __call__(self, *args, **kw):
        result = []
        for h in self.hook:
            logger.debug('hook: %s', h.__name__)
            result.append(h(*args, **kw))
        return result
