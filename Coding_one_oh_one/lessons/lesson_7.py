# WiFi name: Deni
# WiFi password: innovation

# File I/O

# Open a file for writing
with open("example.txt", "w") as file:
    file.write("Hello, World!\n")
    file.write("This is a test file.\n")

# Open a file for reading
with open("example.txt", "r") as file:
    content = file.read()
    print("File content:")
    print(content)

# Append to a file
with open("example.txt", "a") as file:
    file.write("Appending a new line.\n")

# Read the file again to see the changes
with open("example.txt", "r") as file:
    content = file.read()
    print("Updated file content:")
    print(content)

# Error Handling
try:
    # Attempt to open a non-existent file
    with open("non_existent_file.txt", "r") as file:
        content = file.read()
except FileNotFoundError:
    print("Error: The file does not exist.")

# Exception handling example
try:
    # Division by zero
    result = 10 / 0
except ZeroDivisionError:
    print("Error: Division by zero is not allowed.")