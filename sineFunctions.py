import pandas as pd
import os
import pygame
import numpy as np
from scipy.optimize import fsolve
from openpyxl import load_workbook
import time
import math 
import scipy.signal
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
import matplotlib.pyplot as plt

closest_points = []

def show_lost_contact_message(screen, width, height):
    font = pygame.font.SysFont(None, 50)
    text = font.render("You lost the contact! Restarting...", True, (255, 0, 0))
    screen.fill((255, 255, 255))
    screen.blit(text, (width // 2 - 200, height // 2))
    pygame.display.flip()
# Generate sine wave shape
# def generate_sine_wave(amplitude, crest_distance, path_length, screen_width,screen_height,start_x=None, start_y=None):
#     points = []
#     if start_x is None:
#         start_x = screen_width // 2 - path_length // 2  # Center horizontally
#     if start_y is None:
#         start_y = screen_height // 2  # Center vertically

#     x = start_x
#     i = 0
#     while len(points) == 0 or x - start_x < path_length:
#         x = start_x + i
#         y = start_y + int(amplitude * np.sin(2 * np.pi * (x - start_x) / crest_distance))
#         points.append((x, y))
#         i += 1
#     return points
   #-----------------------------------------------Instructions for each task------------------------------------------------------


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
        "- Don't lose contact with screen once you have started .",
        "- Avoid to touch the hand with screen.",
        "- You will go through multiple trials.",
        "- Click the button below to begin."
    ]
    for i, line in enumerate(instructions):
        instr_text = font1.render(line, True, (0, 0, 0))
        screen.blit(instr_text, (screen_width // 2 - 500, screen_height // 2 -200 + i * 50))

    pygame.draw.rect(screen, hover_color if hovering else button_color, button_rect)
    button_text = font1.render("Let's Begin", True, text_color)
    screen.blit(button_text, button_text.get_rect(center=button_rect.center))

    return button_rect


def write_shape_name(x, y, shape_name,screen):
    font = pygame.font.SysFont(None, 50)
    text = font.render(shape_name, True, (0, 0, 0))
    screen.blit(text, (x, y))
    time.sleep(1)  # Display for 1.5 seconds

def low_pass_filter(data, cutoff, sample_rate, order):
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



def generate_sine_wave(amplitude, crest_distance, x_length, num_points, screen_width, screen_height, start_x=None, start_y=None):
    points = []
    if start_x is None:
        start_x = screen_width // 2 - x_length // 2  # Center horizontally
    if start_y is None:
        start_y = screen_height // 2  # Center vertically

    # total_arc_length = 0
    # prev_x, prev_y = None, None

    # Generate evenly spaced points along x for the desired number of points
    x_spacing = x_length / num_points

    for i in range(num_points):
        x = start_x + i * x_spacing
        y = start_y + amplitude * np.sin(2 * np.pi * x / crest_distance)

        # if prev_x is not None:
        #     dx = x - prev_x
        #     dy = y - prev_y
        #     total_arc_length += math.sqrt(dx**2 + dy**2)

        points.append((int(x), int(y)))
        # prev_x, prev_y = x, y

    return points


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

# /////////////////////////////////////////
def calculate_slope(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    if x2 - x1 == 0:
        return float('inf')  # Infinite slope for vertical line
    return (y2 - y1) / (x2 - x1)

def sine_wave_y(x, amplitude, crest_distance, start_x, center_y):
    return center_y + amplitude * np.sin(2 * np.pi * (x - start_x) / crest_distance)

def find_intersection_with_sine_wave(traced_point, traced_coords, amplitude, crest_distance, start_x, center_y):
    if len(traced_coords) < 2:
        return None  # Not enough points to calculate tangent

    index = traced_coords.index(traced_point)
    if index == 0 or index == len(traced_coords) - 1:
        return None  # Can't calculate tangent at first or last point
    p0 = traced_coords[index]
    p1 = traced_coords[index - 1]
    p2 = traced_coords[index + 1]

    x0, y0= p0
    tangent_slope = calculate_slope(p1, p2)

    if tangent_slope == float('inf'):
        perpendicular_slope = 0
    elif tangent_slope == 0:
        perpendicular_slope = float('inf')
    else:
        perpendicular_slope = -1 / tangent_slope

    x1, y1 = traced_point

    def perpendicular_y(x):
        # if perpendicular_slope == float('inf'):
        #     return None
        # else:
            return y1 + perpendicular_slope * (x - x1)

    def intersection_function(x):
        if perpendicular_slope == float('inf'):
            return None
        return perpendicular_y(x) - sine_wave_y(x, amplitude, crest_distance, start_x, center_y)

    initial_guess = x0
    if perpendicular_slope == float('inf'):
        intersection_x = x0
        intersection_y = sine_wave_y(x0, amplitude, crest_distance, start_x, center_y)
        return intersection_x, intersection_y
    else:
        intersection_x = fsolve(intersection_function, initial_guess)
        intersection_y = sine_wave_y(intersection_x, amplitude, crest_distance, start_x, center_y)
        return intersection_x[0], intersection_y[0]

def calculate_error_using_sine_wave_projection(traced_coords, amplitude, crest_distance, closest_points, start_point, center_y):
    errors = []
    closest_points.clear()
    for traced_point in traced_coords:
        if traced_coords.index(traced_point) == 0:
            closest_point = start_point
        else:
            closest_point = find_intersection_with_sine_wave(traced_point, traced_coords, amplitude, crest_distance, start_point[0], center_y)
        if closest_point is not None:
            closest_points.append(closest_point)
            error = euclidean_distance(traced_point, closest_point)
            errors.append(error)
        else:
            errors.append(None)
            closest_points.append((None, None))
    return errors

# Save data to Excel
def save_to_excel(traced_coords, closest_points, participant_name, demographics,
                   reaction_time, path_accuracy, path_length, fil_or_not, trial_number,
                   dtw_aligned_coords):

    # Create a DataFrame for the structured data
    max_length = max(len(traced_coords), len(closest_points),len(dtw_aligned_coords))
    traced_coords_padded = traced_coords + [(None, None)] * (max_length - len(traced_coords))
    closest_points_padded = closest_points + [(None, None)] * (max_length - len(closest_points))
    dtw_coords_padded = dtw_aligned_coords + [(None, None)] * (max_length - len(dtw_aligned_coords)) 
    if fil_or_not== 'unfil':
            
        data = {
            "Original_X": [coord[0] if coord else None for coord in closest_points_padded],
            "Original_Y": [coord[1] if coord else None for coord in closest_points_padded],
            "Traced_X": [coord[0] if coord else None for coord in traced_coords_padded],
            "Traced_Y": [coord[1] if coord else None for coord in traced_coords_padded],
        }
    elif fil_or_not== 'filtered':
        data = {
            "Original_X": [coord[0] if coord else None for coord in closest_points_padded],
            "Original_Y": [coord[1] if coord else None for coord in closest_points_padded],
            "Traced_X": [coord[0] if coord else None for coord in traced_coords_padded],
            "Traced_Y": [coord[1] if coord else None for coord in traced_coords_padded],
            "DTW_X": [coord[0] for coord in dtw_coords_padded],
            "DTW_Y": [coord[1] for coord in dtw_coords_padded],

        }

    df = pd.DataFrame(data)
    tracing_folder = os.path.join(participant_name, "Tracing")
    # Ensure participant directory exists
    if not os.path.exists(participant_name):
        os.makedirs(participant_name)

    # Define the Excel file path
    file_path = os.path.join(tracing_folder, f"trial_{trial_number}_(sine)_{fil_or_not}.xlsx")

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
    sheet.cell(row=empty_row + len(demographics) + 2, column=1, value="Path Accuracy (%):")
    sheet.cell(row=empty_row + len(demographics) + 2, column=2, value=f"{path_accuracy:.2f}")
    sheet.cell(row=empty_row + len(demographics) + 3, column=1, value="Path Length (units):")
    sheet.cell(row=empty_row + len(demographics) + 3, column=2, value=f"{path_length:.2f}")

    # Save changes to the Excel file
    wb.save(file_path)
    print(f"Demographics, reaction time, path accuracy, and path length appended to '{file_path}'.")
    
def extract_demographics_from_excel(file_name):
    # Get the absolute path of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory where the script is located

    # Move up **one level** to `KAT_Python/Codes`
    # parent_dir = os.path.abspath(os.path.join(script_dir, ".."))

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

# def countdown_animation(screen, font, screen_width, screen_height):
#     for i in range(3, 0, -1):
#         screen.fill((255, 255, 255))
#         countdown_text = font.render(str(i), True, (0, 0, 255))
#         screen.blit(countdown_text, (screen_width // 2 - 20, screen_height // 2 - 30))
#         pygame.display.flip()
#         time.sleep(1)

#     screen.fill((255, 255, 255))
#     start_message = font.render("Start!", True, (0, 255, 0))
#     screen.blit(start_message, (screen_width // 2 - 50, screen_height // 2 - 30))
#     pygame.display.flip()
#     time.sleep(1)

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

    for i in range(3, 0, -1):
        screen.fill(white)

        # Draw the infinity shape and markers
        pygame.draw.lines(screen, blue, False, original_coords, 3)
        pygame.draw.circle(screen, green, start_point, 8)
        pygame.draw.circle(screen, red, end_point, 8)
        screen.blit(Task_text, (100, 100))
        screen.blit(small_font.render('Start Here', True, green), (start_point[0] - 50, start_point[1] + 15))
        screen.blit(small_font.render('End Here', True, red), (end_point[0] - 40, end_point[1] + 10))
        # draw_arrow(screen, start_point, original_coords[int(len(original_coords)*0.45)], black)
        # Countdown number
        countdown_text = font.render(str(i), True, (0, 0, 255))
        screen.blit(countdown_text, (screen_width // 2 , screen_height // 4))

        pygame.display.flip()
        time.sleep(1)

    # Display "Start!" message
    screen.fill(white)
    pygame.draw.lines(screen, blue, False, original_coords, 3)
    pygame.draw.circle(screen, green, start_point, 8)
    pygame.draw.circle(screen, red, end_point, 8)
    screen.blit(Task_text, (100, 100))
    screen.blit(small_font.render('Start Here', True, green), (start_point[0] - 50, start_point[1] + 15))
    screen.blit(small_font.render('End Here', True, red), (end_point[0] - 40, end_point[1] + 10))
    # draw_arrow(screen, start_point, original_coords[int(len(original_coords)*0.45)], black)
    start_message = font.render("Start!", True, (0, 255, 0))
    screen.blit(start_message, (screen_width // 2 -40, screen_height //4 ))

    pygame.display.flip()
    time.sleep(1)


def calculate_dtw_distance(seq1, seq2, return_aligned_coords=False):
    dtw_distance, path = fastdtw(seq1, seq2, dist=euclidean)
    normalized_distance = dtw_distance / len(path) if path else 0.0

    result = {
        'dtw_distance': dtw_distance,
        'normalized_distance': normalized_distance,
        'alignment_path': path
    }

    if return_aligned_coords:
        aligned_ref = [seq2[j] for i, j in path]
        aligned_trace = [seq1[i] for i, j in path]
        result['aligned_ref'] = aligned_ref
        result['aligned_trace'] = aligned_trace

    return result

def visualize_dtw_alignment(reference, traced, result):
    """
    Visualizes the DTW alignment between reference and traced paths.

    Parameters:
        reference (list of tuple): Reference 2D points.
        traced (list of tuple): Traced 2D points.
        result (dict): Output from calculate_dtw_distance().
    """
    alignment_path = result['alignment_path']
    ref_x, ref_y = zip(*reference)
    traced_x, traced_y = zip(*traced)

    plt.figure(figsize=(8, 6))
    plt.plot(ref_x, ref_y, 'bo-', label='Reference Path')
    plt.plot(traced_x, traced_y, 'ro-', label='Traced Path')

    for i, j in alignment_path:
        plt.plot([traced[i][0], reference[j][0]], [traced[i][1], reference[j][1]], 'k--', linewidth=0.5)

    plt.legend()
    plt.title(f"DTW Alignment\nNormalized Error: {result['normalized_distance']:.4f}")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.axis("equal")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def visualize_dtw_comparison(reference, traced_unfiltered, traced_filtered, result_unfiltered, result_filtered):
    """
    Visualizes the DTW alignment for both unfiltered and filtered traced paths compared to the reference.

    Parameters:
        reference (list of tuple): Reference 2D points.
        traced_unfiltered (list of tuple): Unfiltered traced 2D points.
        traced_filtered (list of tuple): Filtered traced 2D points.
        result_unfiltered (dict): DTW result for unfiltered path.
        result_filtered (dict): DTW result for filtered path.
    """
    ref_x, ref_y = zip(*reference)

    fig, axs = plt.subplots(1, 2, figsize=(14, 6))

    # Plot unfiltered
    traced_x_unfil, traced_y_unfil = zip(*traced_unfiltered)
    axs[0].plot(ref_x, ref_y, 'bo-', label='Reference')
    axs[0].plot(traced_x_unfil, traced_y_unfil, 'ro-', label='Unfiltered')
    for i, j in result_unfiltered['alignment_path']:
        axs[0].plot([traced_unfiltered[i][0], reference[j][0]], 
                    [traced_unfiltered[i][1], reference[j][1]], 'k--', linewidth=0.5)
    axs[0].set_title(f"Unfiltered DTW\nError: {result_unfiltered['normalized_distance']:.4f}")
    axs[0].legend()
    axs[0].axis("equal")
    axs[0].grid(True)

    # Plot filtered
    traced_x_fil, traced_y_fil = zip(*traced_filtered)
    axs[1].plot(ref_x, ref_y, 'bo-', label='Reference')
    axs[1].plot(traced_x_fil, traced_y_fil, 'go-', label='Filtered')
    for i, j in result_filtered['alignment_path']:
        axs[1].plot([traced_filtered[i][0], reference[j][0]], 
                    [traced_filtered[i][1], reference[j][1]], 'k--', linewidth=0.5)
    axs[1].set_title(f"Filtered DTW\nError: {result_filtered['normalized_distance']:.4f}")
    axs[1].legend()
    axs[1].axis("equal")
    axs[1].grid(True)

    for ax in axs:
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

    plt.tight_layout()
    plt.show()

