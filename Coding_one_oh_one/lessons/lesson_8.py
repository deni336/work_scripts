# WiFi name: Deni
# WiFi password: innovation

# Final Project - To Do List

def display_tasks(tasks):
    if not tasks:
        print("No tasks available.")
    else:
        print("Tasks:")
        for index, task in enumerate(tasks, start=1):
            print(f"{index}. {task}")

def add_task(tasks):
    task = input("Enter the task to add: ")
    tasks.append(task)
    print(f"Task '{task}' added.")

def remove_task(tasks):
    display_tasks(tasks)
    if tasks:
        try:
            task_index = int(input("Enter the task number to remove: ")) - 1
            if 0 <= task_index < len(tasks):
                removed_task = tasks.pop(task_index)
                print(f"Task '{removed_task}' removed.")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid number.")

def main():
    tasks = []
    while True:
        print("\nTo-Do List Menu:")
        print("1. Display Tasks")
        print("2. Add Task")
        print("3. Remove Task")
        print("4. Exit")
        
        choice = input("Choose an option (1-4): ")
        
        if choice == '1':
            display_tasks(tasks)
        elif choice == '2':
            add_task(tasks)
        elif choice == '3':
            remove_task(tasks)
        elif choice == '4':
            print("Exiting the To-Do List application.")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()