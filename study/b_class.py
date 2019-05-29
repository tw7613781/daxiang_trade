from a_class import A

class B:

    def __init__(self, a):
        self.a = a
        self.a.to_be_defined = self.lala
    def func_3(self, a):
        print(self.a.height)
        print('i am func 3: ' + str(a))

    def display(self):
        self.a.height = 10
        self.a.func()
        self.a.func_2()
    
    def lala(self, a):
        print('hahahah: ', str(a))


a = A()
b = B(a)
b.a.func_2()