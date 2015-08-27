'''
Created on 7 Jul 2015

@author: oche
'''
import abc

class PowerMeter(object):
    '''
    classdocs
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        '''
        Constructor
        '''
        pass
    
    @abc.abstractmethod
    def getReading(self):
        pass
     
    @abc.abstractmethod  
    def initDevice(self):
        pass