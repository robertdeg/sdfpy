from math import gcd
from sdfpy.integers import lcm

class Cyclic( tuple ):
    def __new__(self, *arg):
        try:
            return super().__new__(self, tuple(*arg))
        except TypeError as e:
            return super().__new__(self, tuple(arg))

    def __init__(self, *arg):
        self.__sum = sum(self)
    
    def __getitem__(self, idx):
        if type(idx) is slice:
            start = idx.start or 0
            start_mod = start % len(self)

            step = idx.step or 1
            period = len(self) // gcd( step, len(self) )

            pattern = []
            for i in range(period):
                if (idx.stop or 1) > 0:
                    pattern.append(super().__getitem__((start + i * step) % len(self)))
                else:
                    pattern.append(super().__getitem__((start - i * step) % len(self)))
            
            if idx.stop is not None:
                # return tuple
                if idx.stop >= 0:
                    result_len = max(0, 1 + (idx.stop - start - 1) // step)
                    num_periods = result_len // period
                    mod_periods = result_len % period
                    return tuple( pattern * num_periods + pattern[:mod_periods] )
                else:
                    result_len = max(0, 1 + (start - idx.stop - 1) // step)
                    num_periods = result_len // period
                    mod_periods = result_len % period
                    return tuple( pattern * num_periods + pattern[:mod_periods] )
            else:
                # return cyclic pattern
                return Cyclic( pattern )
        else:
            return super().__getitem__(idx % len(self))

    def sum(self, start = 0, stop = None, step = 1):
        start_mod = start % len(self)
        period = len(self) // gcd( step, len(self) )

        pattern = self
        psum = self.__sum
        if start_mod > 0 or step != 1:
            pattern = []
            psum = 0
            for i in range(period):
                elem = super().__getitem__((start + i * step) % len(self))
                psum += elem
                pattern.append(elem)
        
        if stop is None:
            stop = len(self)

        # return tuple
        result_len = max(0, 1 + (stop - start - 1) // step)
        num_periods = result_len // period
        mod_periods = result_len % period
        return num_periods * psum + sum(pattern[:mod_periods])
    
    def as_list(self):
    	return list(self)
