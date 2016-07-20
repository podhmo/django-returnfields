class AgainstDeepcopyWrapper(object):
    def __init__(self, value):
        self.value = value

    def __deepcopy__(self, m):
        return self

    def unwrap(self):
        return self.value

    def __getattr__(self, k):
        return getattr(self.value, k)

    @property
    def __class__(self):
        return self.value.__class__
