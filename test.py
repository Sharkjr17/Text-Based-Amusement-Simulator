import threading
import time

# Function to run repeatedly ("every tick")
def tick_function(stop_event):
    while not stop_event.is_set():
        print("Tick!")
        time.sleep(1)  # Simulate some work or a desired interval

# Function that runs for a longer duration
def main_function():
    print("Main function started...")
    time.sleep(5)  # Simulate a long-running task
    print("Main function finished.")

if __name__ == "__main__":
    # Create an event to signal the tick_function to stop
    stop_event = threading.Event()

    # Create and start the thread for the tick_function
    tick_thread = threading.Thread(target=tick_function, args=(stop_event,))
    tick_thread.start()

    # Run the main function in the primary thread
    main_function()

    # Signal the tick_function to stop and wait for it to finish
    stop_event.set()
    tick_thread.join()

    print("Program finished.")