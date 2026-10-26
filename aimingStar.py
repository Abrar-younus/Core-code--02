import pygame
import pandas as pd
import sys
import math
import time
import statistics
import pyautogui
import csv
import os
from openpyxl import load_workbook



# Function to calculate the vertices of a triangle (Shape 1)
def calculate_triangle_points(center, radius):
    points = []
    angle = -math.pi / 2  # Start at the top point
    for i in range(3):
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))
        angle += 2 * math.pi / 3  # 120 degrees for triangle
    return points

# Function to calculate the vertices of the 8-corner shape (Shape 2)
def calculate_eight_point_shape(center, outer_radius, inner_radius):
    points = []
    for i in range(8):
        angle = i * (math.pi / 4)  # Divide full circle into 8 segments (45 degrees)
        if i % 2 == 0:
            # Outer points
            x = center[0] + outer_radius * math.cos(angle)
            y = center[1] + outer_radius * math.sin(angle)
        else:
            # Inner points
            x = center[0] + inner_radius * math.cos(angle)
            y = center[1] + inner_radius * math.sin(angle)
        points.append((x, y))
    return points

# Function to calculate the vertices of a star (Shape 3)
def calculate_star_points(center, radius):
    points = []
    angle = -math.pi / 2  # Start at the top point
    for i in range(5):
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))
        angle += 2 * math.pi * 2 / 5  # Skip one point to create a star
    return points

def extract_demographics_from_excel(file_name):
    # Get the absolute path of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory where the script is located

    # Construct the correct file path
    file_path = os.path.join(script_dir, file_name)

    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    # Load the CSV file
    df = pd.read_csv(file_path)

    # Get the last row
    last_row = df.iloc[-1]

    # Extract relevant fields
    demographics = {
        "Name": last_row["Name"],
        "Age": last_row["Age"],
        "Gender": last_row["Gender"],
        "Dominant Hand": last_row["Dominant Hand"]
    }

    return demographics

def save_to_excel(participant_name, demographics, trial_number, movement_times, shape_points_count):
    # Create participant folder and 'Aiming' subfolder
    participant_folder = os.path.join(participant_name, "Aiming")
    os.makedirs(participant_folder, exist_ok=True)  # Ensure directory exists

    # Define the Excel file path
    trial_file = os.path.join(participant_folder, f"Trial_{trial_number}_(star).xlsx")

    # Prepare movement data in structured format (Single Column)
    df = pd.DataFrame({"Movement Time": movement_times[:shape_points_count]})  # Only first shape cycle

    # Save movement data to Excel
    df.to_excel(trial_file, index=False, sheet_name="Data")
    print(f"Trial data saved to '{trial_file}'.")

    # Load the workbook to append additional information
    wb = load_workbook(trial_file)
    sheet = wb.active  # Access the first (only) sheet

    # Find the first empty row
    empty_row = sheet.max_row + 2  # Leave a blank row for separation

    # Append demographics
    sheet.cell(row=empty_row, column=1, value="Demographics:")
    for i, (key, value) in enumerate(demographics.items(), start=1):
        sheet.cell(row=empty_row + i, column=1, value=f"{key}:")
        sheet.cell(row=empty_row + i, column=2, value=value)

    # Append reaction time, path accuracy, and path length (all set to 0)
    metrics = [("Reaction Time (s):", "0.00"),
               ("Path Accuracy (%):", "0.00"),
               ("Path Length (units):", "0.00")]

    for i, (label, value) in enumerate(metrics, start=len(demographics) + 1):
        sheet.cell(row=empty_row + i, column=1, value=label)
        sheet.cell(row=empty_row + i, column=2, value=value)

    # Save changes to the Excel file
    wb.save(trial_file)
    print(f"Demographics, reaction time, path accuracy, and path length appended to '{trial_file}'.")

def show_message(window, font, message, color, WIDTH ,HEIGHT, duration=2):
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    window.blit(text, text_rect)
    pygame.display.update()
    pygame.time.wait(int(duration * 500))

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
def write_instructions(screen, font1, screen_width, screen_height):
    button_color = (70, 130, 180)
    hover_color = (100, 160, 210)
    text_color = (255, 255, 255)
    Font_button=pygame.font.Font(None, 40)
    # Button rect
    button_rect = pygame.Rect(screen_width  - 300, screen_height  - 100, 200, 50)
    mouse_pos = pygame.mouse.get_pos()
    hovering = button_rect.collidepoint(mouse_pos)

    # Instruction text
    instructions = [
        "Instructions:",
        "- This is a aiming task.",
        "- Try to reach from one target point to another as timely as you can.",
        "- Start at the green point by clicking it.",
        "- Avoid losing the contact with screen once the green point is clicked.",
        "- Drag the stylus to reach next target.",
        "- You will go through multiple trials.",
        "- Avoid to touch the hand with screen.",
        "- Click the button below to begin."
    ]
    for i, line in enumerate(instructions):
        instr_text = font1.render(line, True, (0, 0, 0))
        screen.blit(instr_text, (screen_width // 2 - 500, screen_height // 2 -200 + i * 50))

    pygame.draw.rect(screen, hover_color if hovering else button_color, button_rect)
    button_text = Font_button.render("Let's Begin", True, text_color)
    screen.blit(button_text, button_text.get_rect(center=button_rect.center))

    return button_rect


def write_shape_name(x, y, shape_name,screen):
    font = pygame.font.SysFont(None, 50)
    text = font.render(shape_name, True, (0, 0, 0))
    screen.blit(text, (x, y))
    time.sleep(3)  # Display for 1.5 seconds


# Main function to handle shape movement task
def aiming_star(WINDOW,trial_number,Aiming_total_trials):
        # Get screen resolution
    res = pyautogui.size()
    WIDTH, HEIGHT = res[0], res[1] - int(res[1] / 10)  # Reduce height by 1/10th

    # Set up the display
    # WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Aiming task: Star shape")

    # Define colors
    BLACK = (0, 0, 0)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)

    movement_times = []
    current_point_index = 0
    movement_count = 0
    trial_active = False
    movement_start_time = None
    total_start_time = None

    demographics_file = "demographics.csv"
    demographics = extract_demographics_from_excel(demographics_file)
    if demographics is None:
        print("Demographics could not be loaded. Exiting.")
        return

    participant_name = demographics["Name"]
    star_center = (WIDTH // 2, HEIGHT // 2)
    triangle_radius = 150
    outer_star_radius = 200
    inner_star_radius = 70
    
    shape_points = calculate_star_points(star_center, outer_star_radius)
    shape_points.append(shape_points[0])  # Ensure the start point is the last target position
    print(shape_points)
    total_movements_required = len(shape_points) - 1  # Movement count should exclude initial start point

    
    font = pygame.font.Font(None, 36)
    font2=pygame.font.Font(None,50)
    font_instr=pygame.font.Font(None,60)
    clock = pygame.time.Clock()
    start_clicked = False  # Track if the start point was clicked

    WINDOW.fill(WHITE)
    if trial_number == 1:
        button_rect = write_instructions(WINDOW, font_instr, WIDTH, HEIGHT)
        pygame.display.flip()

        waiting_for_click = True
        while waiting_for_click:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):
                    WINDOW.fill((255, 255, 255))
                    write_shape_name(WIDTH // 2 - 100, HEIGHT // 2, "Star", WINDOW)
                    pygame.display.flip()
                    time.sleep(1.5)
                    pygame.event.clear()
                    waiting_for_click = False

    else:         
        
        WINDOW.fill(WHITE)
        write_shape_name(WIDTH // 2 - 100, HEIGHT // 2 , "Star", WINDOW)
        pygame.display.flip()
        time.sleep(1.5) 

    while True:
        WINDOW.fill(WHITE)
        task_label = font2.render(f'Aiming Task, Trial ({trial_number}/{Aiming_total_trials})', True, BLUE)
        WINDOW.blit(task_label, (100, 100))

        pygame.draw.lines(WINDOW, BLACK, True, shape_points, 3)
        if not start_clicked:
            instruction_text = font.render("Press and hold left mouse button to start", True, BLACK)
            text_rect = instruction_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200))
            WINDOW.blit(instruction_text, text_rect)
            pygame.draw.circle(WINDOW, GREEN, (int(shape_points[0][0]), int(shape_points[0][1])), 10)  # Start position

        
        
        if start_clicked:
            target_position = shape_points[current_point_index + 1]
            pygame.draw.circle(WINDOW, GREEN, (int(target_position[0]), int(target_position[1])), 10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            # Detect loss of contact
            if event.type == pygame.MOUSEBUTTONUP and trial_active:
                show_message(WINDOW, font, "You lost contact! Please start again.", RED,WIDTH, HEIGHT)
                # Reset trial
                movement_times.clear()
                movement_count = 0
                current_point_index = 0
                trial_active = False
                movement_start_time = None
                total_start_time = None
                start_clicked = False

            if event.type == pygame.MOUSEBUTTONDOWN and not start_clicked:
                mouse_pos = pygame.mouse.get_pos()
                if distance(mouse_pos, shape_points[0]) <= 15:
                    start_clicked = True
                    trial_active = True
                    movement_start_time = time.time()
                    total_start_time = time.time()
                    current_point_index = 0

        if trial_active and pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            if distance(mouse_pos, shape_points[current_point_index + 1]) <= 15:
                movement_end_time = time.time()
                if movement_start_time:
                    movement_times.append(movement_end_time - movement_start_time)
                movement_count += 1

                if movement_count >= total_movements_required:
                    total_end_time = time.time()
                    total_time_taken = total_end_time - total_start_time
                    median_mt = statistics.median(movement_times)

                    save_to_excel(participant_name, demographics, trial_number, movement_times,len(shape_points))
                    show_message(WINDOW, font, f"Task Complete! Median MT: {median_mt:.3f} s, Total Time: {total_time_taken:.3f} s", BLUE,WIDTH, HEIGHT, duration=5)
                    movement_times.clear()
                    # pygame.quit()
                    return
                else:
                    current_point_index += 1
                    movement_start_time = time.time()

        pygame.display.update()
        clock.tick(60)



# # Main function to handle shape movement task
# def main():
#         # Initialize Pygame
#     pygame.init()

#     # Get screen resolution
#     res = pyautogui.size()
#     WIDTH, HEIGHT = res[0], res[1] - int(res[1] / 10)  # Reduce height by 1/10th

#     # Set up the display
#     WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("Shape Movement Task")

#     # Define colors
#     BLACK = (0, 0, 0)
#     GREEN = (0, 255, 0)
#     RED = (255, 0, 0)
#     BLUE = (0, 0, 255)
#     WHITE = (255, 255, 255)
#     movement_times = []
#     current_point_index = 0
#     movement_count = 0
#     trial_active = False
#     movement_start_time = None
#     total_start_time = None

#     demographics_file = "demographics.csv"
#     demographics = extract_demographics_from_excel(demographics_file)
#     if demographics is None:
#         print("Demographics could not be loaded. Exiting.")
#         return

#     participant_name = demographics["Name"]
#     star_center = (WIDTH // 2, HEIGHT // 2)
#     triangle_radius = 150
#     outer_star_radius = 200
#     inner_star_radius = 70

#     shape_points = calculate_triangle_points(star_center, triangle_radius)  # Shape 1
#     shape_repeat=4
#     total_movements_required =shape_repeat*len(shape_points)
#     shape_name='Triangle'
#     # eight_point_shape = calculate_eight_point_shape(star_center, outer_star_radius, inner_star_radius)  # Shape 2
#     # star_points = calculate_star_points(star_center, outer_star_radius)  # Shape 3
#     font = pygame.font.Font(None, 36)
#     clock = pygame.time.Clock()

#     while True:
#         WINDOW.fill(WHITE)
#         task_label = font.render(f"{shape_name} Task", True, BLACK)
#         WINDOW.blit(task_label, (20, 20))

#         if movement_count == 0 and not trial_active:
#            instruction_text = font.render("Press and hold left mouse button to start", True, BLACK)
#            text_rect = instruction_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200))
#            WINDOW.blit(instruction_text, text_rect)

#         pygame.draw.lines(WINDOW, BLACK, True, shape_points, 3)

#         target_position = shape_points[current_point_index]
#         pygame.draw.circle(WINDOW, GREEN, (int(target_position[0]), int(target_position[1])), 10)

#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 pygame.quit()
#                 sys.exit()

#             # Detect loss of contact
#             if event.type == pygame.MOUSEBUTTONUP and trial_active:
#                 show_message(WINDOW, font, "You lost contact! Please start again.", RED)
#                 # Reset trial
#                 movement_times.clear()
#                 movement_count = 0
#                 current_point_index = 0
#                 trial_active = False
#                 movement_start_time = None
#                 total_start_time = None

#             if event.type == pygame.MOUSEBUTTONDOWN and not trial_active:
#                 mouse_pos = pygame.mouse.get_pos()
#                 if distance(mouse_pos, target_position) <= 15:
#                     trial_active = True
#                     movement_start_time = time.time()
#                     if total_start_time is None:
#                         total_start_time = time.time()

#         if trial_active and pygame.mouse.get_pressed()[0]:
#             mouse_pos = pygame.mouse.get_pos()
#             if distance(mouse_pos, target_position) <= 15:
#                 movement_end_time = time.time()
#                 if movement_start_time:
#                     movement_times.append(movement_end_time - movement_start_time)
#                 movement_count += 1

#                 if movement_count >= total_movements_required:
#                     total_end_time = time.time()
#                     total_time_taken = total_end_time - total_start_time
#                     median_mt = statistics.median(movement_times)
#                     print (len(movement_times))

#                     save_to_excel(participant_name, demographics, 1, movement_times, len(shape_points),shape_repeat)
#                     show_message(WINDOW, font, f"Task Complete! Median MT: {median_mt:.3f} s, Total Time: {total_time_taken:.3f} s", BLUE, duration=5)
#                         # Move to next level
#                             # level += 1
#                     movement_times.clear()
#                     movement_count = 0
#                     current_point_index = 0
#                     trial_active = False
#                     total_start_time = None
#                     pygame.quit()
#                     sys.exit()
#                 else:
#                     current_point_index = (current_point_index + 1) % len(shape_points)
#                     movement_start_time = time.time()

#         pygame.display.update()
#         clock.tick(60)


# Function to calculate distance


# if __name__ == "__main__":
#     main()



# import pygame
# import pandas as pd
# import sys
# import math
# import time
# import statistics
# import pyautogui
# import csv
# import os
# from openpyxl import load_workbook

# # Initialize Pygame
# pygame.init()

# # Get screen resolution
# res = pyautogui.size()
# WIDTH, HEIGHT = res[0], res[1] - int(res[1] / 10)  # Reduce height by 1/10th

# # Set up the display
# WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
# pygame.display.set_caption("Shape Movement Task")

# # Define colors
# BLACK = (0, 0, 0)
# GREEN = (0, 255, 0)
# RED = (255, 0, 0)
# BLUE = (0, 0, 255)
# WHITE = (255, 255, 255)

# # Function to calculate the vertices of a triangle (Shape 1)
# def calculate_triangle_points(center, radius):
#     points = []
#     angle = -math.pi / 2  # Start at the top point
#     for i in range(3):
#         x = center[0] + radius * math.cos(angle)
#         y = center[1] + radius * math.sin(angle)
#         points.append((x, y))
#         angle += 2 * math.pi / 3  # 120 degrees for triangle
#     return points

# # Function to calculate the vertices of the 8-corner shape (Shape 2)
# def calculate_eight_point_shape(center, outer_radius, inner_radius):
#     points = []
#     for i in range(8):
#         angle = i * (math.pi / 4)  # Divide full circle into 8 segments (45 degrees)
#         if i % 2 == 0:
#             # Outer points
#             x = center[0] + outer_radius * math.cos(angle)
#             y = center[1] + outer_radius * math.sin(angle)
#         else:
#             # Inner points
#             x = center[0] + inner_radius * math.cos(angle)
#             y = center[1] + inner_radius * math.sin(angle)
#         points.append((x, y))
#     return points

# # Function to calculate the vertices of a star (Shape 3)
# def calculate_star_points(center, radius):
#     points = []
#     angle = -math.pi / 2  # Start at the top point
#     for i in range(5):
#         x = center[0] + radius * math.cos(angle)
#         y = center[1] + radius * math.sin(angle)
#         points.append((x, y))
#         angle += 2 * math.pi * 2 / 5  # Skip one point to create a star
#     return points

# def extract_demographics_from_excel(file_name):
#     # Get the absolute path of the script
#     script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory where the script is located

#     # Construct the correct file path
#     file_path = os.path.join(script_dir, file_name)

#     # Check if the file exists
#     if not os.path.exists(file_path):
#         raise FileNotFoundError(f"The file '{file_path}' does not exist.")

#     # Load the CSV file
#     df = pd.read_csv(file_path)

#     # Get the last row
#     last_row = df.iloc[-1]

#     # Extract relevant fields
#     demographics = {
#         "Name": last_row["Name"],
#         "Age": last_row["Age"],
#         "Gender": last_row["Gender"],
#         "Dominant Hand": last_row["Dominant Hand"]
#     }

#     return demographics

# def save_to_excel(participant_name, demographics, trial_number, movement_times, shape_points_count):
#     # Create participant folder and 'Aiming' subfolder
#     participant_folder = os.path.join(participant_name, "Aiming")
#     os.makedirs(participant_folder, exist_ok=True)  # Ensure directory exists

#     # Define the Excel file path
#     trial_file = os.path.join(participant_folder, f"Trial{trial_number:02d}.xlsx")

#     # Prepare movement data in structured format (Single Column)
#     df = pd.DataFrame({"Movement Time": movement_times[:shape_points_count]})  # Only first shape cycle

#     # Save movement data to Excel
#     df.to_excel(trial_file, index=False, sheet_name="Data")
#     print(f"Trial data saved to '{trial_file}'.")

#     # Load the workbook to append additional information
#     wb = load_workbook(trial_file)
#     sheet = wb.active  # Access the first (only) sheet

#     # Find the first empty row
#     empty_row = sheet.max_row + 2  # Leave a blank row for separation

#     # Append demographics
#     sheet.cell(row=empty_row, column=1, value="Demographics:")
#     for i, (key, value) in enumerate(demographics.items(), start=1):
#         sheet.cell(row=empty_row + i, column=1, value=f"{key}:")
#         sheet.cell(row=empty_row + i, column=2, value=value)

#     # Append reaction time, path accuracy, and path length (all set to 0)
#     metrics = [("Reaction Time (s):", "0.00"),
#                ("Path Accuracy (%):", "0.00"),
#                ("Path Length (units):", "0.00")]

#     for i, (label, value) in enumerate(metrics, start=len(demographics) + 1):
#         sheet.cell(row=empty_row + i, column=1, value=label)
#         sheet.cell(row=empty_row + i, column=2, value=value)

#     # Save changes to the Excel file
#     wb.save(trial_file)
#     print(f"Demographics, reaction time, path accuracy, and path length appended to '{trial_file}'.")

# def show_message(window, font, message, color, duration=2):
#     text = font.render(message, True, color)
#     text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
#     window.blit(text, text_rect)
#     pygame.display.update()
#     pygame.time.wait(int(duration * 500))

# def distance(p1, p2):
#     return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

# # Main function to handle shape movement task
# def main():
#     movement_times = []
#     current_point_index = 0
#     movement_count = 0
#     trial_active = False
#     movement_start_time = None
#     total_start_time = None

#     demographics_file = "demographics.csv"
#     demographics = extract_demographics_from_excel(demographics_file)
#     if demographics is None:
#         print("Demographics could not be loaded. Exiting.")
#         return

#     participant_name = demographics["Name"]
#     star_center = (WIDTH // 2, HEIGHT // 2)
#     triangle_radius = 150
    
#     shape_points = calculate_triangle_points(star_center, triangle_radius)
#     shape_points.append(shape_points[0])  # Ensure the start point is the last target position
#     print(shape_points)
#     total_movements_required = len(shape_points) - 1  # Movement count should exclude initial start point
#     shape_name = 'Triangle'
    
#     font = pygame.font.Font(None, 36)
#     clock = pygame.time.Clock()
#     start_clicked = False  # Track if the start point was clicked

#     while True:
#         WINDOW.fill(WHITE)
#         task_label = font.render(f"{shape_name} Task", True, BLACK)
#         WINDOW.blit(task_label, (20, 20))

#         pygame.draw.lines(WINDOW, BLACK, True, shape_points, 3)
#         if not start_clicked:
#             instruction_text = font.render("Press and hold left mouse button to start", True, BLACK)
#             text_rect = instruction_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200))
#             WINDOW.blit(instruction_text, text_rect)
#             pygame.draw.circle(WINDOW, GREEN, (int(shape_points[0][0]), int(shape_points[0][1])), 10)  # Start position


        
#         if start_clicked:
#             target_position = shape_points[current_point_index + 1]
#             pygame.draw.circle(WINDOW, GREEN, (int(target_position[0]), int(target_position[1])), 10)

#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 pygame.quit()
#                 sys.exit()

#             if event.type == pygame.MOUSEBUTTONDOWN and not start_clicked:
#                 mouse_pos = pygame.mouse.get_pos()
#                 if distance(mouse_pos, shape_points[0]) <= 15:
#                     start_clicked = True
#                     trial_active = True
#                     movement_start_time = time.time()
#                     total_start_time = time.time()
#                     current_point_index = 0

#         if trial_active and pygame.mouse.get_pressed()[0]:
#             mouse_pos = pygame.mouse.get_pos()
#             if distance(mouse_pos, shape_points[current_point_index + 1]) <= 15:
#                 movement_end_time = time.time()
#                 if movement_start_time:
#                     movement_times.append(movement_end_time - movement_start_time)
#                 movement_count += 1

#                 if movement_count >= total_movements_required:
#                     total_end_time = time.time()
#                     total_time_taken = total_end_time - total_start_time
#                     median_mt = statistics.median(movement_times)

#                     save_to_excel(participant_name, demographics, 2, movement_times,len(shape_points))
#                     show_message(WINDOW, font, f"Task Complete! Median MT: {median_mt:.3f} s, Total Time: {total_time_taken:.3f} s", BLUE, duration=5)
#                     movement_times.clear()
#                     pygame.quit()
#                     sys.exit()
#                 else:
#                     current_point_index += 1
#                     movement_start_time = time.time()

#         pygame.display.update()
#         clock.tick(60)

# # # Main function to handle shape movement task
# # def main():
# #         # Initialize Pygame
# #     pygame.init()

# #     # Get screen resolution
# #     res = pyautogui.size()
# #     WIDTH, HEIGHT = res[0], res[1] - int(res[1] / 10)  # Reduce height by 1/10th

# #     # Set up the display
# #     WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
# #     pygame.display.set_caption("Shape Movement Task")

# #     # Define colors
# #     BLACK = (0, 0, 0)
# #     GREEN = (0, 255, 0)
# #     RED = (255, 0, 0)
# #     BLUE = (0, 0, 255)
# #     WHITE = (255, 255, 255)
# #     movement_times = []
# #     current_point_index = 0
# #     movement_count = 0
# #     trial_active = False
# #     movement_start_time = None
# #     total_start_time = None

# #     demographics_file = "demographics.csv"
# #     demographics = extract_demographics_from_excel(demographics_file)
# #     if demographics is None:
# #         print("Demographics could not be loaded. Exiting.")
# #         return

# #     participant_name = demographics["Name"]
# #     star_center = (WIDTH // 2, HEIGHT // 2)
# #     triangle_radius = 150
# #     outer_star_radius = 200
# #     inner_star_radius = 70

# #     shape_points = calculate_triangle_points(star_center, triangle_radius)  # Shape 1
# #     shape_repeat=4
# #     total_movements_required =shape_repeat*len(shape_points)
# #     shape_name='Triangle'
# #     # eight_point_shape = calculate_eight_point_shape(star_center, outer_star_radius, inner_star_radius)  # Shape 2
# #     # star_points = calculate_star_points(star_center, outer_star_radius)  # Shape 3
# #     font = pygame.font.Font(None, 36)
# #     clock = pygame.time.Clock()

# #     while True:
# #         WINDOW.fill(WHITE)
# #         task_label = font.render(f"{shape_name} Task", True, BLACK)
# #         WINDOW.blit(task_label, (20, 20))

# #         if movement_count == 0 and not trial_active:
# #            instruction_text = font.render("Press and hold left mouse button to start", True, BLACK)
# #            text_rect = instruction_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200))
# #            WINDOW.blit(instruction_text, text_rect)

# #         pygame.draw.lines(WINDOW, BLACK, True, shape_points, 3)

# #         target_position = shape_points[current_point_index]
# #         pygame.draw.circle(WINDOW, GREEN, (int(target_position[0]), int(target_position[1])), 10)

# #         for event in pygame.event.get():
# #             if event.type == pygame.QUIT:
# #                 pygame.quit()
# #                 sys.exit()

# #             # Detect loss of contact
# #             if event.type == pygame.MOUSEBUTTONUP and trial_active:
# #                 show_message(WINDOW, font, "You lost contact! Please start again.", RED)
# #                 # Reset trial
# #                 movement_times.clear()
# #                 movement_count = 0
# #                 current_point_index = 0
# #                 trial_active = False
# #                 movement_start_time = None
# #                 total_start_time = None

# #             if event.type == pygame.MOUSEBUTTONDOWN and not trial_active:
# #                 mouse_pos = pygame.mouse.get_pos()
# #                 if distance(mouse_pos, target_position) <= 15:
# #                     trial_active = True
# #                     movement_start_time = time.time()
# #                     if total_start_time is None:
# #                         total_start_time = time.time()

# #         if trial_active and pygame.mouse.get_pressed()[0]:
# #             mouse_pos = pygame.mouse.get_pos()
# #             if distance(mouse_pos, target_position) <= 15:
# #                 movement_end_time = time.time()
# #                 if movement_start_time:
# #                     movement_times.append(movement_end_time - movement_start_time)
# #                 movement_count += 1

# #                 if movement_count >= total_movements_required:
# #                     total_end_time = time.time()
# #                     total_time_taken = total_end_time - total_start_time
# #                     median_mt = statistics.median(movement_times)
# #                     print (len(movement_times))

# #                     save_to_excel(participant_name, demographics, 1, movement_times, len(shape_points),shape_repeat)
# #                     show_message(WINDOW, font, f"Task Complete! Median MT: {median_mt:.3f} s, Total Time: {total_time_taken:.3f} s", BLUE, duration=5)
# #                         # Move to next level
# #                             # level += 1
# #                     movement_times.clear()
# #                     movement_count = 0
# #                     current_point_index = 0
# #                     trial_active = False
# #                     total_start_time = None
# #                     pygame.quit()
# #                     sys.exit()
# #                 else:
# #                     current_point_index = (current_point_index + 1) % len(shape_points)
# #                     movement_start_time = time.time()

# #         pygame.display.update()
# #         clock.tick(60)


# # Function to calculate distance


# if __name__ == "__main__":
#     main()
