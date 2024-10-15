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
            elif print_clock:
                print(f"Device {device_id} - Clock Message: {msg}, Time since last clock message: {time_difference:.6f} seconds")
            
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

# Normalize timestamps to start from zero
if note_timestamps1 and note_timestamps2:
    start_time = min(note_timestamps1[0], note_timestamps2[0])
    note_timestamps1 = [ts - start_time for ts in note_timestamps1]
    note_timestamps2 = [ts - start_time for ts in note_timestamps2]


# Convert timestamps to a binary time series
def timestamps_to_binary_series(timestamps, duration, resolution=0.01):
    series = np.zeros(int(duration / resolution))
    for ts in timestamps:
        index = int(ts / resolution)
        if index < len(series):
            series[index] = 1
    return series

# Determine the duration of the recording
duration = max(note_timestamps1[-1], note_timestamps2[-1]) if note_timestamps1 and note_timestamps2 else 0

# Convert timestamps to binary series
binary_series1 = timestamps_to_binary_series(note_timestamps1, duration)
binary_series2 = timestamps_to_binary_series(note_timestamps2, duration)

# Calculate cross-correlation
cross_corr = np.correlate(binary_series1, binary_series2, mode='full')
lags = np.arange(-len(binary_series1) + 1, len(binary_series2))

# Find the lag with the maximum cross-correlation
max_corr_index = np.argmax(cross_corr)
max_corr_lag = lags[max_corr_index]
max_corr_value = cross_corr[max_corr_index]

print(f"Maximum cross-correlation: {max_corr_value:.2f} at lag {max_corr_lag}")

# Plot the cross-correlation
plt.figure()
plt.plot(lags, cross_corr)
plt.axvline(x=max_corr_lag, color='r', linestyle='--', label=f'Max Corr Lag: {max_corr_lag}')
plt.title('Cross-Correlation Between Devices')
plt.xlabel('Lag')
plt.ylabel('Cross-Correlation')
plt.legend()

# Show the plot
plt.show()