'''
This object is used to store the output of the application and will be filled in by the various functions.
'''

class Output:
    def __init__(self):
        self.sw = None
        self.ne = None
        self.terrain_scaling_min = None
        self.terrain_scaling_max = None
        self.class_mapping = None

    def __str__(self):
        return str(self.__dict__)