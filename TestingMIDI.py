import mido
import time
# import rtmidi
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

input_names = mido.get_input_names()
print("Available MIDI input ports:")
for index, name in enumerate(input_names):
    print(f"{index}: {name}")

# Prompt the user to select an input port by index
# selected_index = int(input("Enter the index of the MIDI input port you want to open: "))

# Open the selected MIDI input port
inport = mido.open_input(input_names[0], virtual=False)


# Initialize the previous time variable and lists to store time differences and timestamps
previous_time = time.time()
all_time_differences = []
note_time_differences = []
note_timestamps = []

try:
    while True:
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
            if msg.type == 'note_on' and msg.velocity > 0:
                # Store the time difference for note messages
                note_time_differences.append(time_difference)
                
                # Store the timestamp for note-on messages
                note_timestamps.append(current_time)
                
                # Print the message and the time difference
                print(f"Note Message: {msg}, Time since last note message: {time_difference:.6f} seconds")
            else:
                # Print the message and the time difference for all messages
                print(f"Message: {msg}, Time since last message: {time_difference:.6f} seconds")
except KeyboardInterrupt:
    # Calculate the minimum time difference
    min_time_difference = min(all_time_differences) if all_time_differences else None
    print(f"Minimum time difference between messages: {min_time_difference:.6f} seconds")
    
    # Calculate the time differences between note-on messages based on timestamps
    note_time_differences_from_timestamps = [
        t2 - t1 for t1, t2 in zip(note_timestamps[:-1], note_timestamps[1:])
    ]
    
    # Smooth the data using Savitzky-Golay filter
    if len(all_time_differences) > 5:
        smoothed_all = savgol_filter(all_time_differences, window_length=5, polyorder=2)
    else:
        smoothed_all = all_time_differences

    if len(note_time_differences) > 5:
        smoothed_note = savgol_filter(note_time_differences, window_length=5, polyorder=2)
    else:
        smoothed_note = note_time_differences

    if len(note_time_differences_from_timestamps) > 5:
        smoothed_note_from_timestamps = savgol_filter(note_time_differences_from_timestamps, window_length=5, polyorder=2)
    else:
        smoothed_note_from_timestamps = note_time_differences_from_timestamps
    
    # Plot the time differences for all messages
    plt.figure()
    plt.plot(all_time_differences, label='Original')

    plt.title('Time Differences Between All MIDI Messages')
    plt.xlabel('Message Index')
    plt.ylabel('Time Difference (seconds)')
    plt.legend()
    
    # Plot the time differences for note messages (real-time)
    plt.figure()
    plt.plot(note_time_differences, label='Original')

    plt.title('Time Differences Between Note Messages (Real-Time)')
    plt.xlabel('Message Index')
    plt.ylabel('Time Difference (seconds)')
    plt.legend()
    
    # Plot the time differences for note messages (from timestamps)
    plt.figure()
    plt.plot(note_time_differences_from_timestamps, label='Original')
    plt.plot(smoothed_note_from_timestamps, label='Smoothed', linestyle='--')
    plt.title('Time Differences Between Note Messages (From Timestamps)')
    plt.xlabel('Message Index')
    plt.ylabel('Time Difference (seconds)')
    plt.ylim(0, 1)  # Set y-axis limits
    plt.legend()
    
    # Show all plots
    plt.show()