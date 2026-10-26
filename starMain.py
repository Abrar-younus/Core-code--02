import os
import sys
import pygame
import pandas as pd
import numpy as np
import pyautogui
import time
import scipy.signal
from pycpd import RigidRegistration
import matplotlib.pyplot as plt

# from scipy.spatial import cKDTree
from openpyxl import load_workbook
from starFunctions import generate_star_shape, draw_arrow, extract_demographics_from_excel, euclidean_distance,calculate_tracedPoints
from starFunctions import low_pass_filter, countdown_animation, show_lost_contact_message
from starFunctions import save_to_excel,write_shape_name,write_instructions
from starFunctions import calculate_dtw_distance

def star_tracing_main(screen, trial_number, total_trials):
    global drawing, start_point_clicked

        # Colors
    white = (255, 255, 255)
    blue = (0, 0, 255)
    green = (0, 255, 0)
    red = (255, 0, 0)
    black = (0, 0, 0)

    res = pyautogui.size()
    screen_width, screen_height = res[0], res[1] - int(res[1] / 10)
    center_x, center_y = screen_width // 2, screen_height // 2


    original_coords = generate_star_shape(center_x, center_y, 180, 70)
    original_coords=original_coords[0:int(len(original_coords)-30)]
    # plt.figure(figsize=(10, 6))

    # # plt.scatter(Original_X, Original_Y, color='red', s=8, label='Original')
    # original_X, original_Y = zip(*original_coords)
    # plt.scatter(original_X, original_Y, color='blue', s=8, label='Traced')
    # plt.show()
    # original_coords = list(zip(original_X, original_Y))

    # Variables for tracing
    traced_coords = []    
    drawing = False
    start_point_clicked = False
    start_point = original_coords[0]
    end_point = original_coords[int(len(original_coords)-1)]
    if trial_number==1:
        shape_name = "Loading"
    else:
        shape_name = "Next Trial..."

    closest_projection_points=[]
    reaction_time= 0

    #filter parameters
    sample_rate = 60  # Hz
    cutoff_frequency = 3.5  # Hz
    order=1
    # Provide the correct file path
    demographics_file = "demographics.csv"

    # Extract demographics from the Excel file
    demographics = extract_demographics_from_excel(demographics_file)
    if demographics is None:
        print("Demographics could not be loaded. Exiting.")
        return

    participant_name = demographics["Name"]
    closest_projection_points=[]
    # pygame.init()
    # screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption('Tracing Task: Star Shape')
    
    
    font1 = pygame.font.SysFont(None, 30)
    font2 = pygame.font.SysFont(None, 50)
    Task_text = font2.render(f'Tracing Task, Trial ({trial_number}/{total_trials})', True, blue)
    start_text = font1.render('Start Here', True, green)
    end_text = font1.render('End Here', True, red)
    reaction_time= 0

    traced_coords = []
    drawing = False
    #-----------------------------------------------------------------------
    running = True     
    screen.fill(white)
    if trial_number == 1:
        button_rect = write_instructions(screen, font2, screen_width, screen_height)
        pygame.display.flip()

        waiting_for_click = True
        while waiting_for_click:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):
                    screen.fill((255, 255, 255))
                    write_shape_name(screen_width // 2 -100, screen_height // 2, shape_name, screen)
                    pygame.display.flip()
                    time.sleep(1)
                    pygame.event.clear()
                    waiting_for_click = False

    else:         
        
        screen.fill(white)
        write_shape_name(screen_width // 2 -100, screen_height // 2, shape_name, screen)
        pygame.display.flip()
        time.sleep(1)  # Optional: Let user see shape name

    
    countdown_animation(screen, font2, screen_width, screen_height, original_coords,start_point,end_point,trial_number,total_trials)        
    task_display_time = time.time()
    
    
    while running:
        screen.fill(white)
        pygame.draw.lines(screen, (0, 0, 255), False, original_coords, 4)
        pygame.draw.circle(screen, green, start_point, 8)
        pygame.draw.circle(screen, red, end_point, 8)
        screen.blit(Task_text, (100, 100))
        screen.blit(start_text, (start_point[0] - 40, start_point[1] +20))
        screen.blit(end_text, (end_point[0] - 40, end_point[1] -50))

                # Draw arrow indicating tracing direction
        draw_arrow(screen, start_point, original_coords[int(len(original_coords)*0.08)], black)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
    
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if not start_point_clicked and euclidean_distance((x, y), start_point) <= 15:
                    start_point_clicked = True
                    drawing = True
                    trace_start_time = time.time()
                    reaction_time = trace_start_time - task_display_time

                    traced_coords.clear()
                    print("Tracing started!")

            if event.type == pygame.MOUSEBUTTONUP:
                x, y = pygame.mouse.get_pos()
                if drawing and euclidean_distance((x, y), end_point) <= 15:
                    drawing = False
                    # if euclidean_distance((x, y), end_point) > 15:
                    #     # Show lost contact and restart trace loop
                    #     print("You lost the contact! Try again")
                    #     show_lost_contact_message(screen, screen_width, screen_height)
                    #     time.sleep(2)
                    #     traced_coords.clear()
                    #     start_point_clicked = False
                    #     drawing = False
                    #     pygame.event.clear()
                    #     countdown_animation(screen, font2, screen_width, screen_height, original_coords,start_point,end_point,trial_number,total_trials)
                    #     task_display_time = time.time()
                    #     continue  # Restart the while loop cleanly
                                     
                    # Calculate errors and path length
                    original_coords = np.array(original_coords, dtype=float)
                    # traced_points = calculate_tracedPoints(traced_coords, original_coords)
                    traced_coords_np = np.array(traced_coords, dtype=float)

                    result = calculate_dtw_distance(traced_coords_np, original_coords)
                    # visualize_dtw_alignment(original_coords,traced_coords_np, result)
                    # CPD on unfiltered
                    # reg1 = RigidRegistration(X=original_points, Y=traced_coords_np)
                    # TY1, _ = reg1.register()
                    # tree = cKDTree(original_points)
                    # errors, _ = tree.query(TY1)
                    # errors = list(errors)

                    path_accuracy = result['normalized_distance']
                    path_length = sum(
                        np.linalg.norm(np.array(traced_coords[i]) - np.array(traced_coords[i+1]))
                        for i in range(len(traced_coords) - 1)
                    )

                    # Filtered
                    Traced_X, Traced_Y = zip(*traced_coords)
                    fil_Traced_X = low_pass_filter(list(Traced_X), cutoff_frequency, sample_rate,order)
                    fil_Traced_Y = low_pass_filter(list(Traced_Y), cutoff_frequency, sample_rate,order)
                    fil_traced_coords = list(zip(fil_Traced_X, fil_Traced_Y))
                    # fil_traced_points = calculate_tracedPoints(fil_traced_coords, original_coords)
                    fil_traced_np = np.array(fil_traced_coords, dtype=float)

                    result1 = calculate_dtw_distance(fil_traced_np, original_coords, return_aligned_coords=True)
#                         visualize_dtw_comparison(
#     reference=original_coords,
#     traced_unfiltered=traced_coords_np,
#     traced_filtered=fil_traced_np,
#     result_unfiltered=result,
#     result_filtered=result1
# )
                    # visualize_dtw_alignment(original_coords,fil_traced_np, result1)
                    # reg2 = RigidRegistration(X=original_points, Y=fil_traced_np)
                    # TY2, _ = reg2.register()
                    # fil_errors, _ = tree.query(TY2)
                    # fil_errors = list(fil_errors)

                    dtw_aligned_coords=result1['aligned_trace']
                    # Example: converting dtw_aligned_coords
                    dtw_aligned_coords = [tuple(coord) for coord in dtw_aligned_coords]
                    dtw_aligned_coords = np.array(dtw_aligned_coords, dtype=float)
                    dtw_aligned_coords=dtw_aligned_coords.tolist()

                    fil_path_accuracy = result1['normalized_distance']
                    fil_path_length = sum(
                        np.linalg.norm(np.array(dtw_aligned_coords[i]) - np.array(dtw_aligned_coords[i+1]))
                        for i in range(len(dtw_aligned_coords) - 1)
                    )
                    original_coords=original_coords.tolist()
                    # Save both
                    save_to_excel(
                        traced_coords=traced_coords,
                        closest_points=original_coords,
                        participant_name=participant_name,
                        demographics=demographics,
                        reaction_time=reaction_time,
                        path_accuracy=path_accuracy,
                        path_length=path_length,
                        fil_or_not='unfil',
                        trial_number=trial_number,
                        dtw_aligned_coords=dtw_aligned_coords
                    )

                    save_to_excel(
                        traced_coords=fil_traced_coords,
                        closest_points=original_coords,
                        participant_name=participant_name,
                        demographics=demographics,
                        reaction_time=reaction_time,
                        path_accuracy=fil_path_accuracy,
                        path_length=fil_path_length,
                        fil_or_not='filtered',
                        trial_number=trial_number,
                        dtw_aligned_coords=dtw_aligned_coords
                    )
                    print('star, unfil-path_accuracy:', path_accuracy)
                    print('filtered-path_accuracy:', fil_path_accuracy)
                    running = False  # End function while post-processing continues


            if drawing and event.type == pygame.MOUSEMOTION:
                x, y = pygame.mouse.get_pos()
                traced_coords.append((x, y))
        
        if len(traced_coords) > 1:
            pygame.draw.lines(screen, (0, 255, 0), False, traced_coords, 2)
        
        pygame.display.flip()
    

    return
