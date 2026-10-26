import sys
import pygame
import numpy as np
# import win32api
import pyautogui
from counterbalancing import counterbalance
# sys.path.append('Codes')
from sineMain import sine_tracing_main
from infinityMain import infinity_tracing_main
from sawMain import saw_tracing_main
from starMain import star_tracing_main

from aimingTriangle import aiming_triangle
from aimingStar import aiming_star
from aimingPolygon import aiming_polygon

# sys.path.remove('Codes')

# Get display refresh rate and resolution
# def printInfo(device):
#     print((device.DeviceName, device.DeviceString))
#     settings = win32api.EnumDisplaySettings(device.DeviceName, -1)
#     for varName in ['Color', 'BitsPerPel', 'DisplayFrequency']:
#         print("%s: %s" % (varName, getattr(settings, varName)))

# device = win32api.EnumDisplayDevices()
# printInfo(device)

# Get screen resolution
res = pyautogui.size()
screen_width, screen_height = res[0], res[1] - int(res[1] / 10)  # Reduce height by 1/10th
print(f"Screen resolution: {screen_width}x{screen_height}")

# Colors
white = (255, 255, 255)
blue = (0, 0, 255)
green = (0, 255, 0)
red = (255, 0, 0)

trial_number=0
Task_order=counterbalance(1,['Tracing','Aiming','Tracking'])
Tracing_Trial_order=counterbalance (1,[1,2,3])
Aiming_Trial_order=counterbalance  (1,[1,2,3])
Tracking_Trial_order=counterbalance(1,[1,2,3])

Tracing_total_trials=len(Tracing_Trial_order)
Aiming_total_trials=len(Aiming_Trial_order)
Tracking_total_trials=len(Tracking_Trial_order)
print('Tracing_Trial_order: ', Tracing_Trial_order)


pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))


for i in Task_order:
# # #Tracing tasks
#     if i== 'Tracing':
#         for j in Tracing_Trial_order:
#             if j==1:
#                 continue

#             elif j==2:
#                 continue
#             elif j==3:
#                 continue
#         trial_number = 0
        #Tracing tasks
    if i== 'Tracing':
        for j in Tracing_Trial_order:
            if j==1: 
                    # continue
                trial_number+=1
                sine_tracing_main(screen, trial_number,Tracing_total_trials)
                print('sine tracing completed')
            elif j==2:
                # continue
                trial_number+=1
                saw_tracing_main(screen, trial_number,Tracing_total_trials)
                print('infinity tracing completed')
                # infinity_tracing_main(screen, trial_number,Tracing_total_trials)
            elif j==3:
                    # continue 
                trial_number+=1
                star_tracing_main(screen, trial_number,Tracing_total_trials)
                print('star tracing completed')
        trial_number = 0

        #     if j==1:

        #         trial_number+=1
        #         sine_tracing_main(screen, trial_number,Tracing_total_trials)
        #         print('sine tracing completed')

        #     elif j==2:
        #         # continue
        #         trial_number+=1
        #         infinity_tracing_main(screen, trial_number,Tracing_total_trials)
        #         print('infinity tracing completed')
        #     elif j==3:
        #         # continue
        #         trial_number+=1
        #         star_tracing_main(screen, trial_number,Tracing_total_trials)
        #         print('infinity tracing completed')
        # trial_number = 0

    elif i=='Aiming': 
        for j in Aiming_Trial_order:
            if j==1:
                trial_number+=1
                aiming_triangle(screen, trial_number,Aiming_total_trials)
                print('triangle aiming completed')
            elif j==2:
                trial_number+=1
                aiming_star(screen, trial_number,Aiming_total_trials)
                print('star aiming completed')
            elif j==3:
                trial_number+=1
                aiming_polygon(screen, trial_number,Aiming_total_trials)
                print('polygon aiming completed') #Aiming tasks
        trial_number = 0
        
        # for j in Aiming_Trial_order:
        #     if j==1:
        #             continue
        #         # trial_number+=1
        #         # aiming_triangle(screen, trial_number,Aiming_total_trials)
        #         # print('triangle aiming completed')
        #     elif j==2:
        #             continue
        #     elif j==3:
        #             continue 
        # trial_number = 0

    elif i=='Tracking':  #Tracking tasks
        for j in Tracking_Trial_order:
            if j==1:
                    continue
            elif j==2:
                    continue
            elif j==3:
                    continue 
        trial_number = 0
    pygame.display.flip()  # Update the screen                    

            
pygame.quit()
sys.exit()
            


