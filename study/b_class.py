from a_class import A

class B:

    def __init__(self, a):
        self.a = a
        self.a.to_be_defined = self.func_3
    def func_3(self, a):
        print(self.a.height)
        print('i am func 3: ' + str(a))

    def display(self):
        self.a.height = 10
        self.a.func()
        self.a.func_2()


a = A()
b = B(a)
b.display()