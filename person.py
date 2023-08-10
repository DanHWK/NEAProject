class Person:
    name = "James"
    age = 10

    def __init__(self, age):
        self.age = age

    def printDetails(self):
        return(self.name + "is" + str(self.age) + "years old")


john = Person(17)
print(john.printDetails())
