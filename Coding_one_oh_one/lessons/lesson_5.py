# WiFi name: Deni
# WiFi password: innovation

# Functions
def greet(name):
   """Function to greet a person."""
   return f"Hello, {name}!"

def add(a, b):
   """Function to add two numbers."""
   return a + b

# Example usage
if __name__ == "__main__":
   print(greet("Alice"))
   print("Sum of 5 and 3 is:", add(5, 3))
   
   # Demonstrating the use of functions
   x = 10
   y = 20
   print(f"The sum of {x} and {y} is: {add(x, y)}")
   
   # Using the greet function
   print(greet("Bob"))