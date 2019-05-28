class A:

    name = None
    age = None
    height = None

    def __init__(self):
        self.name = 'test'
        self.age = 2
    
    def func(self):
        print(self.height)

    def func_2(self):
        a = 888
        self.to_be_defined(a)

    def to_be_defined(self, a):
        pass