import os
import sys
import pygame
import pandas as pd
import numpy as np
import pyautogui
from scipy.optimize import fsolve
# rom pycpd import RigidRegistration
import time
from openpyxl import load_workbook
import scipy.signal

closest_points = []

def show_lost_contact_message(screen, width, height):
    font = pygame.font.SysFont(None, 50)
    text = font.render("You lost the contact! Restarting...", True, (255, 0, 0))
    screen.fill((255, 255, 255))
    screen.blit(text, (width // 2 - 200, height // 2))
    pygame.display.flip()

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
        "- This is a tracing task.",
        "- The shape will be displayed on the screen.",
        "- Try to trace the shape as precise as you can.",
        "- Start by clicking at the green point and end at the red point.",
        "- Start when the countdown completes.",
        "- Don't lose contact of stylus with screen once you have started .",
        "- Avoid to touch the hand with screen.",
        "- You will go through multiple trials.",
        "- Click the button below to begin."
    ]
    for i, line in enumerate(instructions):
        instr_text = font1.render(line, True, (0, 0, 0))
        screen.blit(instr_text, (screen_width // 2 - 500, screen_height // 2 - 200 + i * 50))

    pygame.draw.rect(screen, hover_color if hovering else button_color, button_rect)
    button_text = font1.render("Let's Begin", True, text_color)
    screen.blit(button_text, button_text.get_rect(center=button_rect.center))

    return button_rect


def write_shape_name(x, y, shape_name,screen):
    font = pygame.font.SysFont(None, 50)
    text = font.render(shape_name, True, (0, 0, 0))
    screen.blit(text, (x, y))
    time.sleep(3)  # Display for 1.5 seconds


def low_pass_filter(data, cutoff, sample_rate, order=2):
    """
    Applies a low-pass Butterworth filter to the given data.

    Args:
        data (array-like): The input data to filter.
        cutoff (float): The cutoff frequency in Hz.
        sample_rate (float): The sampling rate of the data in Hz.
        order (int, optional): The order of the filter. Defaults to 5.

    Returns:
        numpy.ndarray: The filtered data.
    """
    nyquist_rate = 0.5 * sample_rate
    normalized_cutoff = cutoff / nyquist_rate
    sos = scipy.signal.butter(order, normalized_cutoff, btype='low', analog=False, output='sos')
    filtered_data = scipy.signal.sosfiltfilt(sos, data)
    return filtered_data

# Function to extract demographics from the last row of an Excel file
def extract_demographics_from_excel(file_name):
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"The file '{file_name}' does not exist.")

    # Load the Excel file
    df = pd.read_csv(file_name)


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

# Generate infinity shape
def generate_infinity_shape(radius, spacing, num_points, center_x, center_y):
    points = []
    t = np.linspace(0, 2 * np.pi, num_points)
    for angle in t:
        x = center_x + radius * np.sin(angle) * 1.5  # Scale x to stretch horizontally
        y = center_y + radius * np.sin(2 * angle)
        points.append((int(x), int(y)))
    return points



# Euclidean distance function
def euclidean_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

# Function to find closest point on the infinity shape
def find_closest_point_on_infinity_shape(shape_point, traced_coords):
    min_distance = float('inf')
    closest_point = None
    for coord in traced_coords:
        distance = euclidean_distance(shape_point, coord)
        if distance < min_distance:
            min_distance = distance
            closest_point = coord
    return closest_point

# Error calculation using projection
def calculate_tracedPoints(traced_coords, shape_coords):

    closest_points.clear()
    for point in shape_coords:
        closest_point = find_closest_point_on_infinity_shape(point, traced_coords)
        if closest_point is not None:
            closest_points.append(closest_point)
        else:
            closest_points.append((None, None))
    return closest_points


def save_to_excel(traced_coords, closest_points, errors,participant_name, demographics, reaction_time, path_accuracy, path_length,fil_or_not,trial_number):
    # Create a DataFrame for the structured data
    max_length = max(len(traced_coords), len(closest_points), len(errors))
    traced_coords_padded = traced_coords + [(None, None)] * (max_length - len(traced_coords))
    closest_points_padded = closest_points + [(None, None)] * (max_length - len(closest_points))
    errors_padded = errors + [None] * (max_length - len(errors))

    data = {
        "Original_X": [coord[0] if coord else None for coord in closest_points_padded],
        "Original_Y": [coord[1] if coord else None for coord in closest_points_padded],
        "Traced_X": [coord[0] if coord else None for coord in traced_coords_padded],
        "Traced_Y": [coord[1] if coord else None for coord in traced_coords_padded],
        "Error": errors_padded,
    }
    df = pd.DataFrame(data)
    tracing_folder = os.path.join(participant_name, "Tracing")
      # Ensure participant directory exists
    if not os.path.exists(participant_name):
        os.makedirs(participant_name)

    # Define the Excel file path
    file_path = os.path.join(tracing_folder,  f"trial_{trial_number}_(infinity)_{fil_or_not}.xlsx")

    # Save the structured data using pandas
    df.to_excel(file_path, index=False, sheet_name="Data")
    print(f"Structured data saved to '{file_path}'.")

    # Load the workbook and append demographics
    wb = load_workbook(file_path)
    sheet = wb.active  # Get the first (and only) sheet

    # Find the first empty row
    empty_row = sheet.max_row + 2  # Leave one blank row for separation

    # Write demographics, reaction time, path accuracy, and path length
    sheet.cell(row=empty_row, column=1, value="Demographics:")
    for i, (key, value) in enumerate(demographics.items(), start=1):
        sheet.cell(row=empty_row + i, column=1, value=f"{key}:")
        sheet.cell(row=empty_row + i, column=2, value=value)
    sheet.cell(row=empty_row + len(demographics) + 1, column=1, value="Reaction Time (s):")
    sheet.cell(row=empty_row + len(demographics) + 1, column=2, value=f"{reaction_time:.2f}")

    # Add Path Accuracy and Path Length
    sheet.cell(row=empty_row + len(demographics) + 2, column=1, value="Path Accuracy (%):")
    sheet.cell(row=empty_row + len(demographics) + 2, column=2, value=f"{path_accuracy:.2f}")
    sheet.cell(row=empty_row + len(demographics) + 3, column=1, value="Path Length (units):")
    sheet.cell(row=empty_row + len(demographics) + 3, column=2, value=f"{path_length:.2f}")

    # Save changes to the Excel file
    wb.save(file_path)
    print(f"Demographics, reaction time, path accuracy, and path length appended to '{file_path}'.")

# Function to draw an arrow
def draw_arrow(screen, start, end,color=(0, 0, 0), arrow_size=10):
    pygame.draw.line(screen, color, start, end, 5)
    angle = np.arctan2(end[1] - start[1], end[0] - start[0])
    arrow_tip1 = (end[0] - 2*(arrow_size * np.cos(angle - np.pi / 6)), end[1] - 2*(arrow_size * np.sin(angle - np.pi / 6)))
    arrow_tip2 = (end[0] - 2*(arrow_size * np.cos(angle + np.pi / 6)), end[1] - 2*(arrow_size * np.sin(angle + np.pi / 6)))
    pygame.draw.line(screen, color, end, arrow_tip1, 5)
    pygame.draw.line(screen, color, end, arrow_tip2, 5)

# def draw_arrow(screen, start, end, color=(0, 0, 0), arrow_size=10, width=3):
#     """
#     Draws an arrow from start to end on the given screen.

#     Args:
#         screen: The Pygame surface to draw on.
#         start (tuple): Start coordinate (x, y).
#         end (tuple): End coordinate (x, y).
#         color (tuple): RGB color of the arrow.
#         arrow_size (int): Size of the arrowhead.
#         width (int): Thickness of the arrow line.
#     """
#     pygame.draw.line(screen, color, start, end, width)

#     # Compute direction of the arrow
#     angle = np.arctan2(end[1] - start[1], end[0] - start[0])

#     # Calculate arrowhead points
#     offset = 1.5 * arrow_size  # scale to elongate arrowhead
#     left = (
#         end[0] - offset * np.cos(angle - np.pi / 6),
#         end[1] - offset * np.sin(angle - np.pi / 6)
#     )
#     right = (
#         end[0] - offset * np.cos(angle + np.pi / 6),
#         end[1] - offset * np.sin(angle + np.pi / 6)
#     )

#     # Draw arrowhead
#     pygame.draw.polygon(screen, color, [end, left, right])

# def draw_direction_arrow_from_path(screen, path, start_idx=0, offset=10, color=(0, 0, 0), arrow_size=10, arrow_length=100):
#     if len(path) < start_idx + 2 * offset:
#         return  # Not enough points

#     p0 = path[start_idx]
#     p1 = path[start_idx + offset]
#     p2 = path[start_idx + 2 * offset]

#     v1 = np.array([p1[0] - p0[0], p1[1] - p0[1]])
#     v2 = np.array([p2[0] - p1[0], p2[1] - p1[1]])
#     avg_vec = (v1 + v2) / 2
#     norm = np.linalg.norm(avg_vec)
#     unit_vec = avg_vec / norm if norm != 0 else avg_vec

#     end_point = (int(p0[0] + unit_vec[0] * arrow_length),
#                  int(p0[1] + unit_vec[1] * arrow_length))

#     draw_arrow(screen, p0, end_point, color, arrow_size)

def countdown_animation(screen, font, screen_width, screen_height, original_coords, start_point, end_point,trial_number,total_trials):
    # Colors
    white = (255, 255, 255)
    blue = (0, 0, 255)
    green = (0, 255, 0)
    red = (255, 0, 0)
    black= (0, 0, 0)
    small_font = pygame.font.SysFont(None, 30)
    font2 = pygame.font.SysFont(None, 50)
    Task_text = font2.render(f'Tracing Task, Trial ({trial_number}/{total_trials})', True, blue)
    segments = split_continuous_segments(original_coords)
    for i in range(3, 0, -1):
        screen.fill(white)

      
        for seg in segments:
            if len(seg) > 1:
                    pygame.draw.lines(screen, blue, False, seg, 4)
        pygame.draw.circle(screen, green, start_point, 8)
        pygame.draw.circle(screen, red, end_point, 8)
        screen.blit(Task_text, (100, 100))
        screen.blit(small_font.render('Start Here', True, green), (start_point[0] + 15, start_point[1] - 15))
        screen.blit(small_font.render('End Here', True, red), (end_point[0] - 95, end_point[1] ))
        draw_arrow(screen, start_point, original_coords[45], black)
        # Countdown number
        countdown_text = font.render(str(i), True, (0, 0, 255))
        screen.blit(countdown_text, (screen_width // 2 , screen_height // 4))

        pygame.display.flip()
        time.sleep(1)

    # Display "Start!" message
    screen.fill(white)
    
    for seg in segments:
        if len(seg) > 1:
                pygame.draw.lines(screen, blue, False, seg, 4)
    pygame.draw.circle(screen, green, start_point, 8)
    pygame.draw.circle(screen, red, end_point, 8)
    screen.blit(Task_text, (100, 100))
    screen.blit(small_font.render('Start Here', True, green), (start_point[0] + 15, start_point[1] - 15))
    screen.blit(small_font.render('End Here', True, red), (end_point[0] - 95, end_point[1]))
    draw_arrow(screen, start_point, original_coords[45], black)
    start_message = font.render("Start!", True, (0, 255, 0))
    screen.blit(start_message, (screen_width // 2 -40, screen_height //4 ))

    pygame.display.flip()
    time.sleep(1)

def smart_filter_infinity_shape(coords, center_x, center_y, radius=40):
    """
    Keep:
    - All points in the right loop (x >= center_x)
    - All points in the top-left loop (y <= center_y)
    - In the bottom-left loop, keep only points that are OUTSIDE the center radius
    """
    filtered_coords = []
    for (x, y) in coords:
            #right top
        if (x >= center_x)  and (y <= center_y) :
            filtered_coords.append((x, y))
        #right bottom
        elif x >= center_x and y >= center_y and euclidean_distance((x, y), (center_x, center_y)) > radius:
        
            filtered_coords.append((x, y))
        #left top
        elif (x <= center_x)  and (y <= center_y) and euclidean_distance((x, y), (center_x, center_y)) > radius:
            # Top-left — keep all
            filtered_coords.append((x, y))
        else:
            # Bottom-left — keep only if far from center
            if (x <= center_x)  and (y >= center_y) :
                filtered_coords.append((x, y))
    return filtered_coords


def split_continuous_segments(coords, max_dist=20):
    """Split path into segments where large jumps (from point deletion) occur."""
    if not coords:
        return []

    segments = [[coords[0]]]
    for i in range(1, len(coords)):
        if euclidean_distance(coords[i], coords[i - 1]) > max_dist:
            # Start a new segment
            segments.append([coords[i]])
        else:
            segments[-1].append(coords[i])
    return segments

