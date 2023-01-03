from qiskit import QuantumCircuit, ClassicalRegister
from abc import ABCMeta, abstractmethod
import numpy as np

__all__ = ['TwoState', 'Naive4Q', 'Naive3Q', 'Optimised', 'Parallel']
 

class MODpBase(QuantumCircuit, metaclass=ABCMeta):
    def __init__(
            self, 
            p: int, 
            word_length: int, 
            qubit_number: int,
        ):

        self.theta = 2*np.pi/p
        self.p = p
        self.word_length = word_length
        
        super().__init__(qubit_number)

        self.left_marker()

        for wl in range(word_length):
            self.ua(wl)

        self.right_marker()

    @abstractmethod
    def left_marker(self):
        pass

    @abstractmethod
    def right_marker(self):
        pass

    @abstractmethod
    def ua(self, current_character: int):
        pass


class TwoState(MODpBase):
    def __init__(self, **kwargs):
        kwargs['qubit_number']=1
        super().__init__(**kwargs)

    def left_marker(self):
        pass

    def right_marker(self):
        self.measure_active()

    def ua(self, _):
        self.ry(2*self.theta, 0)
        self.barrier()



class NaiveBase(MODpBase):
    def __init__( self, ks: tuple[int, int, int, int], **kwargs):
        self.ks = ks
        super().__init__(**kwargs)

    def left_marker(self):
        self.h(0)
        self.h(1)
        self.barrier()

    @abstractmethod
    def ccry(self, theta, target, control1, control2):
        pass
    
    def ua(self, current_character: int):
        ks = [self.ks[i] for i in (3, 2, 0, 1)]
        if current_character % 2:
            ks.reverse()
    
        for i, k in enumerate(ks):
            self.ccry(2*self.theta*k, 2, 0, 1)

            if i in (0, 2):
                self.x(1)
            elif i == 1:
                self.x(0)
        
        self.barrier()

    def right_marker(self):
        if self.word_length % 2:
            self.x(0)

        self.h(0)
        self.h(1)

        self.barrier()
        
        self.add_register(ClassicalRegister(3))
        self.measure((0, 1, 2), (0, 1, 2))



class Naive4Q(NaiveBase):
    def __init__(self, **kwargs):
        kwargs['qubit_number']=4
        super().__init__(**kwargs)

    def ccry(self, theta, target, control1, control2):
        self.ccx(0, 1, 3)
        self.cry(theta, 3, 2)
        self.ccx(0, 1, 3)


class Naive3Q(NaiveBase):
    def __init__( self, *args, **kwargs):
        kwargs['qubit_number']=3
        super().__init__(*args, **kwargs)

    def ccry(self, theta, target, control1, control2):
        self.ry(theta/2, 2)
        self.ccx(control1, control2, target)
        self.ry(-theta/2, 2)
        self.ccx(control1, control2, target)



class Optimised(MODpBase):
    def __init__( self, ks: tuple[int, int, int], **kwargs):
        self.ks = ks
        kwargs['qubit_number']=3
        super().__init__(**kwargs)

    def left_marker(self):
        self.h(0)
        self.h(1)
        self.barrier()

    def ua(self, _):
        self.ry(2*self.theta*self.ks[0], 2)
        self.cry(2*self.theta*self.ks[1], 1, 2)
        self.cry(2*self.theta*self.ks[2], 0, 2)
        self.barrier()

    def right_marker(self):
        if self.word_length % 2:
            self.x(0)

        self.h(0)
        self.h(1)

        self.barrier()
        
        self.add_register(ClassicalRegister(3))
        self.measure((0, 1, 2), (0, 1, 2))


class Parallel(QuantumCircuit):
    def __init__(
            self,
            p: int, 
            word_length: int, 
            ks: tuple[int, int, int],
        ):
        
        super().__init__(3,3)

        for i, k in enumerate(ks):
           self.compose(
                TwoState(
                    p = p/k,
                    word_length=word_length,
                ),
                qubits = [i],
                clbits = [i],
                inplace = True,
            )
