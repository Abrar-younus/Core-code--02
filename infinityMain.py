import os
import sys
import pygame
import pandas as pd
import numpy as np
import pyautogui
from scipy.optimize import fsolve
from pycpd import RigidRegistration
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
# from pycpd import RigidRegistration
import time
from openpyxl import load_workbook
import scipy.signal
from infinityFunctions import extract_demographics_from_excel, generate_infinity_shape, euclidean_distance, calculate_tracedPoints
from infinityFunctions import countdown_animation, save_to_excel,low_pass_filter,draw_arrow, write_instructions,write_shape_name
from infinityFunctions import smart_filter_infinity_shape, split_continuous_segments, show_lost_contact_message
# In your drawing section:



# Main function
def infinity_tracing_main(screen, trial_number, total_trials):
    global drawing, start_point_clicked

        # Get display refresh rate and resolution
    res = pyautogui.size()
    screen_width, screen_height = res[0], res[1] - int(res[1] / 10)  # Reduce height by 1/10th
    print(f"Screen resolution: {screen_width}x{screen_height}")

    # Colors
    white = (255, 255, 255)
    blue = (0, 0, 255)
    green = (0, 255, 0)
    red = (255, 0, 0)
    black = (0, 0, 0)
    # Infinity shape parameters
    radius = 100
    spacing = 200
    total_points = 1000


    # Adjust center of the screen
    center_x = screen_width // 2
    center_y = screen_height // 2

        # Generate original infinity shape coordinates
    original_coordinates = generate_infinity_shape(radius, spacing, total_points, center_x, center_y)
    original_coords = smart_filter_infinity_shape(original_coordinates, center_x, center_y, radius=40)

    # original_coords=original_coords[len(original_coords)//2+23:len(original_coords)]
    # Variables for tracing
    traced_coords = []
    closest_points = []  # Store closest points on the original path
    drawing = False
    start_point_clicked = False
    start_point = original_coords[7]
    end_point = original_coords[len(original_coords)  -6]

    # original_coords= original_coords[0:len(original_coords)//2+23]
    #filter parameters
    sample_rate = 120  # Hz
    cutoff_frequency = 5  # Hz
 # Provide the correct file path
    demographics_file = "demographics.csv"

    # Extract demographics from the Excel file
    demographics = extract_demographics_from_excel(demographics_file)
    if demographics is None:
        print("Demographics could not be loaded. Exiting.")
        return

    participant_name = demographics["Name"]

    # pygame.init()
    # screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption('Tracing Task: Infinity Shape')

    traced_coords.clear()
    font1 = pygame.font.SysFont(None, 30)
    font2 = pygame.font.SysFont(None, 50)
    Task_text = font2.render(f'Tracing Task, Trial ({trial_number}/{total_trials})', True, blue)
    start_text = font1.render('Start Here', True, green)
    end_text = font1.render('End Here', True, red)
    
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
                    write_shape_name(screen_width // 2 -100, screen_height // 2, " Infinity shape", screen)
                    pygame.display.flip()
                    time.sleep(1.5)
                    pygame.event.clear()
                    waiting_for_click = False

    else:         
            
        screen.fill(white)
        write_shape_name(screen_width // 2 -100, screen_height // 2, "Infinity shape", screen)
        pygame.display.flip()
        time.sleep(1.5)  # Optional: Let user see shape name

        

    # Countdown animation
    countdown_animation(screen, font2, screen_width, screen_height, original_coords,start_point,end_point,trial_number,total_trials)

    # Task display time
    task_display_time = time.time()

    
    while running:
        screen.fill(white)
        segments = split_continuous_segments(original_coords)
        for seg in segments:
            if len(seg) > 1:
                    pygame.draw.lines(screen, blue, False, seg, 4)
        # pygame.draw.lines(screen, blue, False, original_coords, 4)
        pygame.draw.circle(screen, green, start_point, 8)
        pygame.draw.circle(screen, red, end_point, 8)
        screen.blit(Task_text, (100, 100))
        screen.blit(start_text, (start_point[0] + 15, start_point[1] - 15))
        screen.blit(end_text, (end_point[0] - 95, end_point[1] ))
        
        draw_arrow(screen, start_point, original_coords[45], black)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if not start_point_clicked and euclidean_distance((x, y), start_point) <= 15:
                    drawing = True
                    start_point_clicked = True
                    trace_start_time = time.time()
                    reaction_time = trace_start_time - task_display_time

            if event.type == pygame.MOUSEBUTTONUP:
                x, y = pygame.mouse.get_pos()
                if drawing:
                    drawing = False
                    if euclidean_distance((x, y), end_point) > 15:
                        # Show lost contact and restart trace loop
                        print("You lost the contact! Restarting trial...")
                        show_lost_contact_message(screen, screen_width, screen_height)
                        time.sleep(2)
                        traced_coords.clear()
                        start_point_clicked = False
                        drawing = False
                        pygame.event.clear()
                        countdown_animation(screen, font2, screen_width, screen_height, original_coords,start_point,end_point,trial_number,total_trials)
                        task_display_time = time.time()
                        continue  # Restart the while loop cleanly
                    elif euclidean_distance((x, y), end_point) <= 15:

                        # plt.figure(figsize=(10, 6))

                        # # plt.scatter(Original_X, Original_Y, color='red', s=8, label='Original')
                        # Traced_X, Traced_Y = zip(*traced_coords)
                        # plt.scatter(Traced_X, Traced_Y, color='blue', s=8, label='Traced')
                        # plt.show()
                        # traced_coords = list(zip(Traced_X, Traced_Y))

    #------------------------------------------CPD on unfiltered coordinates------------------------------------------------------
                        traced_points = calculate_tracedPoints(traced_coords, original_coords)
                        # Apply CPD registration to find errors                      
                        original_points=np.array(original_coords,dtype=float)
                        traced_coords=np.array(traced_points,dtype=float)

                        reg1 = RigidRegistration(X=original_points, Y=traced_coords)
                        TY1, _ = reg1.register()
                        tree = cKDTree(original_points)  # Target
                        errors, indices = tree.query(TY1) 
                        errors=list(errors)

    # --------------------------------------- CPD on filtered traced coordinates-------------------------------------------------
                        Traced_X, Traced_Y = zip(*traced_coords)
                        fil_Traced_X=low_pass_filter(list(Traced_X),cutoff_frequency,sample_rate)
                        fil_Traced_Y=low_pass_filter(list(Traced_Y),cutoff_frequency,sample_rate)
                        fil_traced_coords = list(zip(fil_Traced_X, fil_Traced_Y))

                        #calculating the error, closest points= origninal coordinates
                        fil_traced_points = calculate_tracedPoints(fil_traced_coords, original_coords)
                        # Apply CPD registration to find errors                      
                        # fil_original_points=np.array(fil_original_points,dtype=float)
                        fil_traced_coords=np.array(fil_traced_points,dtype=float)

                        reg2 = RigidRegistration(X=original_points, Y=fil_traced_coords)
                        TY2, _ = reg2.register()
                        tree = cKDTree(original_points)  # Target
                        fil_errors, indices = tree.query(TY2)
                        fil_errors=list(fil_errors)

    #----------------------------------------------Calculate path accuracy and path length of unfiltered-----------------------------------------------------------------------
                        path_accuracy = sum(errors) / len(errors) if errors else 0
                        path_length = sum(
                            euclidean_distance(traced_coords[i], traced_coords[i + 1])
                            for i in range(len(traced_coords) - 1)
                        )
                        # Calculate path accuracy and path length of filtered data
                        fil_path_accuracy = sum(fil_errors) / len(fil_errors) if errors else 0
                        fil_path_length = sum(
                            euclidean_distance(fil_traced_coords[i], fil_traced_coords[i + 1])
                            for i in range(len(fil_traced_coords) - 1)
                        )

                        traced_coords = [(x, y) for x, y in traced_coords]
                        original_points = [(x, y) for x, y in original_points]
                        fil_traced_coords = [(x, y) for x, y in fil_traced_coords]
                        # fil_original_points = [(x, y) for x, y in fil_original_points]
                        # print('traced_coords: ',traced_coords)
                        save_to_excel(
                            traced_coords=traced_coords,
                            closest_points=original_points,
                            errors=errors,
                            participant_name=participant_name,
                            demographics=demographics,
                            reaction_time=reaction_time,
                            path_accuracy=path_accuracy,
                            path_length=path_length,
                            fil_or_not='unfil',
                            trial_number=trial_number
                        )

                        save_to_excel(
                            traced_coords=fil_traced_coords,
                            closest_points=original_points,
                            errors=fil_errors,
                            participant_name=participant_name,
                            demographics=demographics,
                            reaction_time=reaction_time,
                            path_accuracy=fil_path_accuracy,
                            path_length=fil_path_length,
                            fil_or_not='filtered',
                            trial_number=trial_number
                        )
                        
                        print("INFINITY Tracing task completed!")
                        running = False

            if drawing and event.type == pygame.MOUSEMOTION:
                x, y = pygame.mouse.get_pos()
                traced_coords.append((x, y))

        if len(traced_coords) > 1 and drawing:
            pygame.draw.lines(screen, green, False, traced_coords, 2)

        pygame.display.flip()
    # print("Segment length: ", len(seg))

    return
# if __name__ == "__main__":
#     # demographics = parse_arguments()
#     # folder_path = sys.argv[-1]  # Last argument is the folder path
#     main()
#     pygame.quit()