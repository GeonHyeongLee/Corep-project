import tkinter as tk
from tkinter import messagebox
from time import sleep
import RPi.GPIO as GPIO

# Motor Pins
PUL1 = 17
DIR1 = 27
ENA1 = 22

PUL2 = 23
DIR2 = 24
ENA2 = 25

# Footswitch Pins
STRONG_PEDAL_PIN = 4
MEDIUM_PEDAL_PIN = 5
WEAK_PEDAL_PIN = 6

# Buzzer Relay Pin
RELAY_PIN = 12  # 릴레이 제어 핀

# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUL1, GPIO.OUT)
GPIO.setup(DIR1, GPIO.OUT)
GPIO.setup(ENA1, GPIO.OUT)
GPIO.setup(PUL2, GPIO.OUT)
GPIO.setup(DIR2, GPIO.OUT)
GPIO.setup(ENA2, GPIO.OUT)
GPIO.setup(STRONG_PEDAL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MEDIUM_PEDAL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(WEAK_PEDAL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)  # 초기 상태에서 릴레이를 끔

print('Initialization Completed')

def move_motors(steps, direction, delay):
    # Enable Motors
    GPIO.output(ENA1, GPIO.HIGH)
    GPIO.output(ENA2, GPIO.HIGH)
    sleep(0.5)  # Delay to ensure motors are enabled

    # Set Direction
    dir_state = GPIO.HIGH if direction == 'down' else GPIO.LOW
    GPIO.output(DIR1, dir_state)
    GPIO.output(DIR2, dir_state)
    
    for _ in range(steps):
        GPIO.output(PUL1, GPIO.HIGH)
        GPIO.output(PUL2, GPIO.HIGH)
        sleep(delay)
        GPIO.output(PUL1, GPIO.LOW)
        GPIO.output(PUL2, GPIO.LOW)
        sleep(delay)
    
    # Disable Motors
    GPIO.output(ENA1, GPIO.LOW)
    GPIO.output(ENA2, GPIO.LOW)
    sleep(0.5)  # Delay to ensure motors are disabled

# Initial values
current_value = 0
limit_value = 100
goal_set = False
stop_requested = False  # Flag to check if stop is requested

# Increment and step values for different pedals
increment_values = {
    "strong": (150, 700),
    "medium": (106, 500),
    "weak": (45, 325)
}

def set_goal():
    global limit_value, goal_set
    try:
        limit_value = int(goal_entry.get())
        goal_set = True
        show_pedal_screen()
    except ValueError:
        messagebox.showerror("Invalid input", "Please enter a valid integer for the goal.")

def update_value(increment, steps):
    global current_value, stop_requested
    stop_requested = False  # Reset the stop flag
    if goal_set:
        current_value += increment
        value_label.config(text=f"현재 값: {current_value}")
        update_progress()
        if current_value >= limit_value:
            trigger_buzzer()
        
        # sleep time 설정 
        if increment == increment_values["strong"][0]:
            sleep_time = 2
        else:
            sleep_time = 0.05 / steps
            
        # Move motors
        move_motors(steps, 'down', 0.05 / steps)
        sleep(1)  # Stop for 1 second
        if not stop_requested:  # Check if stop was requested during sleep
            move_motors(steps, 'up', 0.05 / steps)
    else:
        messagebox.showwarning("목표가 설정되지 않았습니다.", "먼저 목표를 설정해 주세요.")

def update_progress():
    percentage = (current_value / limit_value) * 100
    progress_label.config(text=f"진행도: {percentage:.2f}%")
    
    # Calculate the width based on percentage
    progress_width = int((percentage / 100) * 400)  # 400 is the width of the canvas
    canvas.coords(progress_bar, (0, 0, progress_width, 30))  # Update the coordinates of the rectangle

def trigger_buzzer():
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # 릴레이를 통해 부저 켜기
    buzzer_label.config(text="충진 완료!!!")
    root.after(1000, lambda: GPIO.output(RELAY_PIN, GPIO.LOW))  # 1초 후 릴레이 끄기
    root.after(1000, lambda: buzzer_label.config(text=""))
    root.after(1000, reset_and_show_goal_screen)

def reset_and_show_goal_screen():
    global current_value, goal_set
    current_value = 0
    goal_set = False
    value_label.config(text=f"현재 값: {current_value}")
    progress_label.config(text="진행도: 0.00%")
    canvas.coords(progress_bar, (0, 0, 0, 30))  # Reset the progress bar
    show_goal_screen()

def show_goal_screen():
    goal_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=20, padx=20)
    keypad_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=20, padx=20)
    value_label.pack_forget()
    progress_label.pack_forget()
    buzzer_label.pack_forget()
    canvas.pack_forget()
    button_frame.pack_forget()

def show_pedal_screen():
    goal_frame.pack_forget()
    keypad_frame.pack_forget()
    value_label.pack(pady=20)
    progress_label.pack(pady=20)
    buzzer_label.pack(pady=20)
    canvas.pack(pady=20)  # Ensure canvas is packed
    button_frame.pack(pady=20)

def on_close():
    GPIO.cleanup()
    root.destroy()

def append_digit(digit):
    goal_entry.insert(tk.END, str(digit))

def footswitch_callback(channel):
    if goal_set:
        if channel == STRONG_PEDAL_PIN:
            print("Strong pedal activated")
            increment, steps = increment_values["strong"]
        elif channel == MEDIUM_PEDAL_PIN:
            print("Medium pedal activated")
            increment, steps = increment_values["medium"]
        elif channel == WEAK_PEDAL_PIN:
            print("Weak pedal activated")
            increment, steps = increment_values["weak"]
        update_value(increment, steps)
    else:
        messagebox.showwarning("Goal not set", "Please set the goal first.")

def stop_operation():
    global stop_requested
    stop_requested = True  # Set the stop flag to True
    reset_and_show_goal_screen()  # Reset and return to the goal screen

# Set up event detection for footswitches
GPIO.add_event_detect(STRONG_PEDAL_PIN, GPIO.FALLING, callback=footswitch_callback, bouncetime=200)
GPIO.add_event_detect(MEDIUM_PEDAL_PIN, GPIO.FALLING, callback=footswitch_callback, bouncetime=200)
GPIO.add_event_detect(WEAK_PEDAL_PIN, GPIO.FALLING, callback=footswitch_callback, bouncetime=200)

root = tk.Tk()
root.title("Foot Pedal Input")

# Ensure the window fills the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}")

root.configure(bg="white")
root.resizable(False, False)

# Goal input frame
goal_frame = tk.Frame(root, bg="white")
goal_label = tk.Label(goal_frame, text="목표 값을 입력하세요 :", font=("Helvetica", 16), bg="white")
goal_label.pack(pady=10)
goal_entry = tk.Entry(goal_frame, font=("Helvetica", 16), width=10)
goal_entry.pack(pady=10)
set_goal_button = tk.Button(goal_frame, text="확인", command=set_goal, font=("Helvetica", 16), width=10)
set_goal_button.pack(pady=10)

# Load and display the image
image = tk.PhotoImage(file="88토이.png")
image_label = tk.Label(goal_frame, image=image, bg="white")
image_label.pack(pady=10)

# Numeric keypad
keypad_frame = tk.Frame(root, bg="white")
for i in range(1, 10):
    btn = tk.Button(keypad_frame, text=str(i), font=("Helvetica", 24), command=lambda i=i: append_digit(i), height=2, width=4)
    btn.grid(row=(i-1)//3, column=(i-1)%3, padx=5, pady=5, sticky="nsew")

zero_button = tk.Button(keypad_frame, text="0", font=("Helvetica", 24), command=lambda: append_digit(0), height=2, width=4)
zero_button.grid(row=3, column=1, padx=5, pady=5, sticky="nsew")

clear_button = tk.Button(keypad_frame, text="Clear", font=("Helvetica", 24), command=lambda: goal_entry.delete(0, tk.END), height=2, width=4)
clear_button.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

# Current value label
value_label = tk.Label(root, text=f"현재 값: {current_value}", font=("Helvetica", 24), bg="white")

# Progress percentage label
progress_label = tk.Label(root, text="진행도: 0.00%", font=("Helvetica", 24), bg="white")

# Buzzer label
buzzer_label = tk.Label(root, text="", font=("Helvetica", 24), fg="red", bg="white")

# Progress bar canvas
canvas = tk.Canvas(root, width=400, height=30, bg="white")
progress_bar = canvas.create_rectangle(0, 0, 0, 30, fill="blue")

# Button frame with Stop button
button_frame = tk.Frame(root, bg="white")
stop_button = tk.Button(button_frame, text="Stop", command=stop_operation, font=("Helvetica", 24), height=2, width=10)
stop_button.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", on_close)
show_goal_screen()  # Start with the goal screen
root.mainloop()
