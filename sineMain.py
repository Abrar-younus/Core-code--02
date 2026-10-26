import os
import sys
import pygame
import pandas as pd
import numpy as np
import pyautogui
import time
from sineFunctions import generate_sine_wave,euclidean_distance, calculate_tracedPoints,low_pass_filter
from sineFunctions import save_to_excel, extract_demographics_from_excel,countdown_animation, write_instructions, write_shape_name
from sineFunctions import show_lost_contact_message,calculate_dtw_distance, visualize_dtw_comparison


def sine_tracing_main(screen, trial_number, total_trials):
    global drawing, start_point_clicked

    # Get screen resolution
    res = pyautogui.size()
    screen_width, screen_height = res[0], res[1] - int(res[1] / 10)  # Reduce height by 1/10th
    pygame.display.set_caption("Tracing Task: Sine Wave")
    # Colors
    white = (255, 255, 255)
    blue = (0, 0, 255)
    green = (0, 255, 0)
    red = (255, 0, 0)

    # Sine wave parameters
    amplitude = 100
    crest_distance = 200
    x_length=500
    total_points = 1000

    #filter parameters
    sample_rate = 60  # Hz
    cutoff_frequency = 3 # Hz
    order=2
    # Generate sine wave coordinates
    original_coords = generate_sine_wave(amplitude, crest_distance,x_length, total_points, 
                                         screen_width=screen_width, screen_height=screen_height)

    # Initialize tracing variables
    traced_coords = []
    closest_points = []  # Store closest points on the original path
    drawing = False
    start_point_clicked = False
    start_point = original_coords[0]
    end_point = original_coords[-1]
    if trial_number==1:
        shape_name = "Loading"
    else:
        shape_name = "Next Trial..."
    # Load participant demographics
    demographics_file = "demographics.csv"
    demographics = extract_demographics_from_excel(demographics_file)
    if demographics is None:
        print("Demographics could not be loaded. Exiting.")
        return

    participant_name = demographics["Name"]

    # # Refresh rate
    # refresh_rate = 60  # Common refresh rate
    # last_refresh_time = 0

    # Pygame fonts
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
                    write_shape_name(screen_width // 2 - 100, screen_height // 2, shape_name, screen)
                    pygame.display.flip()
                    time.sleep(1)
                    pygame.event.clear()
                    waiting_for_click = False

    else:         
        
        screen.fill(white)
        write_shape_name(screen_width // 2 - 100, screen_height // 2 , shape_name, screen)
        pygame.display.flip()
        time.sleep(1)  # Optional: Let user see shape name

    

        #-------------------------------------------------------------------------------------------------------------------------------
    # Countdown animation
    countdown_animation(screen, font2, screen_width, screen_height, original_coords,start_point,end_point,trial_number,total_trials)
    # Task display time
    task_display_time = time.time()
    
    while running:

        screen.fill(white)
        pygame.draw.lines(screen, blue, False, original_coords, 3)
        pygame.draw.circle(screen, green, start_point, 8)
        pygame.draw.circle(screen, red, end_point, 8)
        screen.blit(Task_text, (100, 100))
        screen.blit(start_text, (start_point[0] - 50, start_point[1] + 15))
        screen.blit(end_text, (end_point[0] - 40, end_point[1] + 10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if not start_point_clicked and euclidean_distance((x, y), start_point) <= 15:
                    drawing = True
                    start_point_clicked = True
                    trace_start_time = time.time()
                    reaction_time = trace_start_time - task_display_time
                    print(f"Reaction Time: {reaction_time:.2f} seconds")

            if event.type == pygame.MOUSEBUTTONUP:
                x, y = pygame.mouse.get_pos()
                if drawing and euclidean_distance((x, y), end_point) <= 15:
                    drawing = False
                    # if euclidean_distance((x, y), end_point) > 15:
                    #     # Show lost contact and restart trace loop
                    #     print("You lost the contact! Restarting trial...")
                    #     show_lost_contact_message(screen, screen_width, screen_height)
                    #     time.sleep(2)
                    #     traced_coords.clear()
                    #     start_point_clicked = False
                    #     drawing = False
                    #     pygame.event.clear()
                    #     countdown_animation(screen, font2, screen_width, screen_height, original_coords,start_point,end_point,trial_number,total_trials)
                    #     task_display_time = time.time()
                    #     continue  # Restart the while loop cleanly

    # try:
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
                    # visualize_dtw_alignment(original_coords,fil_traced_np, result1)
#                         visualize_dtw_comparison(
#     reference=original_coords,
#     traced_unfiltered=traced_coords_np,
#     traced_filtered=fil_traced_np,
#     result_unfiltered=result,
#     result_filtered=result1
# )
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
                    # Save data
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
                    print('sine, unfil-path_accuracy:', path_accuracy)
                    print('filtered-path_accuracy:', fil_path_accuracy)


                    running = False  

            if drawing and event.type == pygame.MOUSEMOTION:
                x, y = pygame.mouse.get_pos()
                traced_coords.append((x, y))

        if len(traced_coords) > 1:
            pygame.draw.lines(screen, green, False, traced_coords, 2)

        pygame.display.flip()

    return
    
