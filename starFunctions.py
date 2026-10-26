import os
import sys
import pygame
import pandas as pd
import numpy as np
import pyautogui
import time
from openpyxl import load_workbook
import scipy.signal
import matplotlib.pyplot as plt
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

closest_points=[]

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

# # Example usage:
# sample_rate = 120  # Hz
# cutoff_frequency = 5  # Hz
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

def generate_star_shape(center_x, center_y, outer_radius, inner_radius, num_points=5, resolution=103):
    points = []
    angle_step = np.pi / num_points  # Correct angle increment
    
    star_vertices = []
    
    for i in range(2 * num_points):  # Star has twice as many points (outer + inner)
        r = outer_radius if i % 2 == 0 else inner_radius  # Alternate radii
        theta = i * angle_step
        x = center_x + r * np.cos(theta)
        y = center_y + r * np.sin(theta)
        star_vertices.append((int(x), int(y)))

    # Increase number of points using interpolation
    interpolated_points = []
    for i in range(len(star_vertices)):
        start = np.array(star_vertices[i])
        end = np.array(star_vertices[(i + 1) % len(star_vertices)])  # Loop back to the start
        for j in range(resolution):  # Create intermediate points
            interp = start + (end - start) * (j / resolution)
            interpolated_points.append(tuple(interp.astype(int)))
    
    return interpolated_points[:-1]  # Keep end slightly before start

def euclidean_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

# Function to find the closest point on the star path
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
    file_path = os.path.join(tracing_folder, f"trial_{trial_number}_(star)_{fil_or_not}.xlsx")

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
    
# Function to draw an arrow
def draw_arrow(screen, start, end,color=(0, 0, 0), arrow_size=10):
    pygame.draw.line(screen, color, start, end, 3)
    angle = np.arctan2(end[1] - start[1], end[0] - start[0])
    arrow_tip1 = (end[0] - 2*(arrow_size * np.cos(angle - np.pi / 6)), end[1] - 2*(arrow_size * np.sin(angle - np.pi / 6)))
    arrow_tip2 = (end[0] - 2*(arrow_size * np.cos(angle + np.pi / 6)), end[1] - 2*(arrow_size * np.sin(angle + np.pi / 6)))
    pygame.draw.line(screen, color, end, arrow_tip1, 5)
    pygame.draw.line(screen, color, end, arrow_tip2, 5)

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
        pygame.draw.lines(screen, blue, False, original_coords, 4)
        pygame.draw.circle(screen, green, start_point, 8)
        pygame.draw.circle(screen, red, end_point, 8)
        screen.blit(Task_text, (100, 100))
        screen.blit(small_font.render('Start Here', True, green), (start_point[0] - 40, start_point[1] + 20))
        screen.blit(small_font.render('End Here', True, red), (end_point[0] - 40, end_point[1] - 50))
        draw_arrow(screen, start_point, original_coords[int(len(original_coords)*0.08)], black)
        # Countdown number
        countdown_text = font.render(str(i), True, (0, 0, 255))
        screen.blit(countdown_text, (screen_width // 2 , screen_height // 4))

        pygame.display.flip()
        time.sleep(1)

    # Display "Start!" message
    screen.fill(white)
    pygame.draw.lines(screen, blue, False, original_coords, 4)
    pygame.draw.circle(screen, green, start_point, 8)
    pygame.draw.circle(screen, red, end_point, 8)
    screen.blit(Task_text, (100, 100))
    screen.blit(small_font.render('Start Here', True, green), (start_point[0] - 40, start_point[1] + 20))
    screen.blit(small_font.render('End Here', True, red), (end_point[0] - 40, end_point[1] - 50))
    draw_arrow(screen, start_point, original_coords[int(len(original_coords)*0.08)], black)
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

