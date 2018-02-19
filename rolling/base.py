import abc


class RollingObject(metaclass=abc.ABCMeta):
    """Baseclass for rolling iterator objects.

    All subclasses must implement the following methods
    with the following call signatures:

        - _init_fixed(self, iterable, window_size, **kwargs)
        - _init_variable(self, iterable, window_size, **kwargs)
        - _update(self)
        - _add_new(self)
        - _remove_old(self)
        - current_value(self) [this is a @property]

    Note: variable-length instances must also have a self._obs
    attribute to indicate the current size of the variable-length
    window.
    """
    def __new__(cls, iterable, window_size, **kwargs):
        window_type = kwargs.get('window_type', 'fixed')
        if window_type == 'fixed':
            cls.__init__ = cls._init_fixed
            cls.__next__ = cls._next_fixed
        elif window_type == 'variable':
            cls.__init__ = cls._init_variable
            cls.__next__ = cls._next_variable
        else:
            raise ValueError("Unknown window_type '{}'".format(window_type))

        self = super().__new__(cls)
        self.window_type = window_type
        self.window_size = self._validate_window_size(window_size)
        self._iterator = iter(iterable)
        if self.window_type == 'variable':
            self._filled = False
        return self

    def __repr__(self):
        return "Rolling(func='{}', window_size={}, window_type='{}')".format(
                    self.__class__.__name__, self.window_size, self.window_type)

    def __iter__(self):
        return self

    def _next_fixed(self):
        'return the next value for fixed-length windows'
        self._update()
        return self.current_value

    def _next_variable(self):
        'return the next value for variable-length windows'
        # while the window size is not reached, add new values
        if not self._filled and self._obs < self.window_size:
            self._add_new()
            if self._obs == self.window_size:
                self._filled = True
            return self.current_value
        # once the window size is reached, update window until the iterator finishes
        try:
            self._update()
            return self.current_value
        except StopIteration:
            # if the iterator finishes, remove the oldest values one by one
            if self._obs == 1:
                raise
            else:
                self._remove_old()
                return self.current_value

    @abc.abstractproperty
    def current_value(self):
        'return the current value of the window'
        pass

    @abc.abstractmethod
    def _init_fixed(self):
        'intialise as a fixed-size window'
        pass

    @abc.abstractmethod
    def _init_variable(self):
        'intialise as a variable-size window'
        pass

    @abc.abstractmethod
    def _remove_old(self):
        'remove the oldest value from the window'
        pass

    @abc.abstractmethod
    def _add_new(self):
        'take a new value from the iterator and add it to the window'
        pass

    @abc.abstractmethod
    def _update(self):
        'simultaneously add a new value and remove the old value'
        pass

    @staticmethod
    def _validate_window_size(k):
        'check if k is a positive integer'
        if not isinstance(k, int):
            raise TypeError('window_size must be integer type, got {}'.format(type(k).__name__))
        if k <= 0:
            raise ValueError('window_size must be positive')
        return k
