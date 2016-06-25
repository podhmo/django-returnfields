class AgainstDeepcopyWrapper(object):
    def __init__(self, value, once=True):
        self.value = value
        self.once = once

    def __deepcopy__(self, m):
        if self.once:
            return self.unwrap()
        else:
            return self

    def unwrap(self):
        return self.value

    def __getattr__(self, k):
        return getattr(self.value, k)

    @property
    def __class__(self):
        return self.value.__class__
