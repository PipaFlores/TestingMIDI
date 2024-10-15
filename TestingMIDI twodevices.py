import mido
import time
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import threading
import numpy as np

note = None # set as null if you want to consider all notes
print_clock = False # set false if you don't want to print clock messages
difference_threshold = 2 # set the threshold for the difference between the periods of the two devices in aggregated data

# Get the list of available MIDI input names
input_names = mido.get_input_names()
print("Available MIDI input ports:")
for index, name in enumerate(input_names):
    print(f"{index}: {name}")

# Prompt the user to select input ports by index
# selected_index_1 = int(input("Enter the index of the first MIDI input port you want to open: "))
# selected_index_2 = int(input("Enter the index of the second MIDI input port you want to open: "))

# Open the selected MIDI input ports
inport1 = mido.open_input(input_names[0])
inport2 = mido.open_input(input_names[3])

# Initialize the previous time variables and lists to store time differences and timestamps
previous_time1 = time.time()
previous_time2 = time.time()
all_time_differences1 = []
note_time_differences1 = []
note_timestamps1 = []
all_time_differences2 = []
note_time_differences2 = []
note_timestamps2 = []
# Shared flag to stop threads
stop_threads = False

# Function to process messages from a MIDI input port
def process_midi(inport, all_time_differences, note_time_differences, note_timestamps, device_id):
    previous_time = time.time()
    while not stop_threads:
        for msg in inport:
            # Get the current time
            current_time = time.time()
            
            # Calculate the time difference between the current and previous message
            time_difference = current_time - previous_time
            
            # Update the previous time
            previous_time = current_time
            
            # Store the time difference for all messages
            all_time_differences.append(time_difference)
            
            # Check if the message is a note-on message
            if msg.type == 'note_on' and (note is None or msg.note == note) and msg.velocity > 0:
                # Store the time difference for note messages
                note_time_differences.append(time_difference)
                
                # Store the timestamp for note-on messages
                note_timestamps.append(current_time)
                
                # Print the message and the time difference
                print(f"Device {device_id} - Note Message: {msg}, Time since last note message: {time_difference:.6f} seconds")
            elif msg.type == 'clock':
                print(f"Device {device_id} - Clock Message: {msg}, Time since last clock message: {time_difference:.6f} seconds")
            else:
                # Print the message and the time difference for all messages
                print(f"Device {device_id} - Message: {msg}, Time since last message: {time_difference:.6f} seconds")
            if stop_threads:
                break

# Create threads for each MIDI input port
thread1 = threading.Thread(target=process_midi, args=(inport1, all_time_differences1, note_time_differences1, note_timestamps1, 1))
thread2 = threading.Thread(target=process_midi, args=(inport2, all_time_differences2, note_time_differences2, note_timestamps2, 2))

# Start the threads
thread1.start()
thread2.start()

try:
    # Wait for both threads to finish
    while thread1.is_alive() or thread2.is_alive():
        time.sleep(0.1)
except KeyboardInterrupt:
    # Set the flag to stop threads
    stop_threads = True
    # Wait for threads to finish
    thread1.join()
    thread2.join()

# Define the time window size (in seconds)
time_window = 0.1

# Calculate the time differences between note-on messages based on timestamps for both devices
note_time_differences_from_timestamps1 = [
    t2 - t1 for t1, t2 in zip(note_timestamps1[:-1], note_timestamps1[1:])
]
note_time_differences_from_timestamps2 = [
    t2 - t1 for t1, t2 in zip(note_timestamps2[:-1], note_timestamps2[1:])
]

# Filter out differences above 2 seconds
note_time_differences1 = [diff for diff in note_time_differences1 if diff <= difference_threshold]
note_time_differences2 = [diff for diff in note_time_differences2 if diff <= difference_threshold]
note_time_differences_from_timestamps1 = [diff for diff in note_time_differences_from_timestamps1 if diff <= difference_threshold]
note_time_differences_from_timestamps2 = [diff for diff in note_time_differences_from_timestamps2 if diff <= difference_threshold]
period_differences = [
    abs(d1 - d2) for d1, d2 in zip(note_time_differences_from_timestamps1, note_time_differences_from_timestamps2)
    if abs(d1 - d2) <= difference_threshold
]
# Function to aggregate data over time windows
def aggregate_over_time_windows(timestamps, time_differences, window_size):
    if not timestamps:
        return []
    start_time = timestamps[0]
    end_time = timestamps[-1]
    current_time = start_time
    aggregated_data = []
    while current_time < end_time:
        window_end = current_time + window_size
        # Aggregate data within the current window
        window_data = [diff for ts, diff in zip(timestamps, time_differences) if current_time <= ts < window_end]
        aggregated_data.append(np.mean(window_data) if window_data else 0)
        current_time = window_end
    # Remove zeros from the aggregated data
    return [data for data in aggregated_data if data != 0]

# Aggregate data for both devices
aggregated_note_differences1 = aggregate_over_time_windows(note_timestamps1, note_time_differences1, time_window)
aggregated_note_differences2 = aggregate_over_time_windows(note_timestamps2, note_time_differences2, time_window)
aggregated_note_differences_from_timestamps1 = aggregate_over_time_windows(note_timestamps1, note_time_differences_from_timestamps1, time_window)
aggregated_note_differences_from_timestamps2 = aggregate_over_time_windows(note_timestamps2, note_time_differences_from_timestamps2, time_window)
aggregated_period_differences = aggregate_over_time_windows(note_timestamps1, period_differences, time_window)

# # Plot the aggregated time differences for note messages (real-time) for both devices
# plt.figure()
# plt.plot(aggregated_note_differences1, label='Device 1 - Aggregated Note Messages')
# plt.plot(aggregated_note_differences2, label='Device 2 - Aggregated Note Messages')
# plt.title('Aggregated Time Differences Between Note Messages (Real-Time considering clock messages)')
# plt.xlabel('Time Window Index')
# plt.ylabel('Average Time Difference (seconds)')
# plt.legend()

# Plot the aggregated time differences for note messages (from timestamps) for both devices
plt.figure()
plt.plot(aggregated_note_differences_from_timestamps1, label='Device 1 - Aggregated From Timestamps')
plt.plot(aggregated_note_differences_from_timestamps2, label='Device 2 - Aggregated From Timestamps')
plt.title('Time Differences Between Note Messages (From Timestamps)')
plt.xlabel('Time Window Index')
plt.ylabel('Average Time Difference (seconds)')
plt.legend()

# Plot the aggregated period differences between the two devices
plt.figure()
plt.plot(aggregated_period_differences, label='Period Differences')
plt.title('Aggregated Period Differences Between Devices')
plt.xlabel('Time Window Index')
plt.ylabel('Average Period Difference (seconds)')
plt.legend()

# Show all plots
plt.show()