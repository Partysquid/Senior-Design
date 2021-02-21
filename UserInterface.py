#Team 3- Model Train Railroad Controller - Chip Kline, Michael Kersting,
#                                     Tyler Gregory, Qingya Chen, Adam Durrett
#User Interface Program - Adam Durrett
#
#
# This Program runs the user interface portion on the main controller of our
# model train railroad controller. It allows the user to see a visual
# representation of different aspects about the railroad system including train
# position and speed, and status of different sensors and outputs.
#
#
# Inputs: Received from main controller software (temporarily from test bench)
#       - Sensor status
#       - Which train is detected
#
# Outputs: Sent to screen - or main script
#         - To Screen:
#             - track layout
#             - sensor position
#             - sensor status
#             - train position
#             - train speed
#             - visual elements of each
#         - To Main Script:
#             - train speed
#
#
from tkinter import Tk, Label, Button, Scale, Frame, PhotoImage, Radiobutton
from tkinter import *
import numpy as np
import pandas as pd
from numpy import nan
import time
from PIL import ImageTk,Image 
import math
from functools import partial
import trainlib_dummy as TLib

#---- PROGRAM PARAMETERS ----#
num_of_trains = 1
num_of_sensors = 11
num_of_lights = 6
color_list = ["red", "green", "blue", "yellow"]
train_order = [0,1,2,3,4,5,6,7,8,9,10,11,0,12,13,14,15,16,19,20,18,2,3,4,5,6,7,8,9,10,11] #sensor to sensor
order_index = 0
num_train_actions = 5
max_trains = 4
num_switches = 3
num_endcaps = 1
timer = 0
sync_passes = 0
timer_started = False
sensor_last_det = -1
#turning points used to guess train position based on speed
turning_point_coords = [[1,1], [475,1], [475,485], [1,485]] #cannot be 0, will mess up math
turn_threshold = 30

main_port = TLib.getCOMPorts()[0]
main_controller = TLib.Controller(main_port)
#----------------------------#
#---- DATA STRUCTURES ----#
# Sensor dataframe
# - 5 columns : sensor #, x position, y position, status, train detected
# - rows sorted by sensor # -- number of rows = number of sensors
sensor_df = pd.DataFrame(columns=['sensor_#', 'status', 'pos_x', 'pos_y',
                                  'train_detected', 'linked_for', 'linked_rev'])

# Train dataframe
# - 7 columns : train #, color, x position, y position, last sensor,
#                current sensor, speed in x direction, speed in y direction, realtime speed
# - rows sorted by train # -- number of rows = number of trains
train_df = pd.DataFrame(columns = ['train_#', 'color', 'pos_x', 'pos_y',
                                   'last_sensor', 'current_sensor',
                                   'speed_x', 'speed_y', 'real_speed',
                                   'ref_speed'])

# Light Signal dataframe
# - 5 columns : light #, x position, y position, status, switch number
# - rows sorted by light # -- number of rows = number of lights
light_df = pd.DataFrame(columns = ['light_#', 'pos_x', 'pos_y', 'status', 'switch_#'])

# Switches dataframe
# - 8 columns : switch #, x position, y position, selection, sel_0, sel_1, 
#               linked_rev, orientation
# - rows sorted by switch # -- number of rows = number of switches
switch_df = pd.DataFrame(columns = ['switch_#', 'pos_x', 'pos_y' , 'select',
                                    'sel_1', 'sel_2', 'linked_rev', 'orient'])

# Endcap dataframe
# - 4 columns : endcap #, x position, y position, link
# - rows sorted by endcap # -- number of rows = number of endcaps
endcap_df = pd.DataFrame(columns = ['endcap_#', 'pos_x', 'pos_y' , 'linked'])
#-------------------------#
def fill_dataframe(df, num_of_object):
    temp_dict = df.to_dict()
    for key in temp_dict:
        if('#' in key):
            temp_dict[key] = list(range(num_of_object))
        else:
            if('status' in key):
                temp_dict[key] = num_of_object*[False]
            else:
                if('color' in key):
                    temp_dict[key] = color_list[0:num_of_object]
                else:
                    temp_dict[key] = num_of_object*[0]
    
    return(pd.DataFrame.from_dict(temp_dict))

def scan_sensors():
    sensors_triggered = []
    for i in range(num_of_sensors):
        sensor_num = i+1
        lc_address = sensor_df.at[i, 'lc_addr']
        pin_num = sensor_df.at[i, 'pin_#']
        
        sensor_reading = main_controller.readSensor(lc_address, pin_num)
        
        if(sensor_reading):
            sensors_triggered.append(sensor_num)
            sensor_df.at[i,'status'] = 'Train 1'
        else:
            sensor_df.at[i,'status'] = 'False'
            
        sens_status_label_list[i].configure(text=str(sensor_df.at[i,'status']))
    
    return sensors_triggered
    
def train_action_press(action_num):
    values_list = [False, False, False, False, False]
    for i in range(5):
        if(i==action_num):
            values_list[i] = True
    
    main_controller.sendFuncG1(1505, values_list[4], values_list[0], values_list[1], values_list[2], values_list[3])
    
    return
    
def light_button(light_num):
    mod_light = light_num%2
    other_light = 0
    switch_num = light_df.at[light_num-1,'switch_#']
    switch_sel = switch_df.at[switch_num-1, 'select']
    if(mod_light==1):
        other_light = light_num + 1
    else:
        other_light = light_num - 1
    
    
    this_status = light_df.at[light_num-1, 'status']
    other_status = light_df.at[other_light-1, 'status']
    
    
    if(this_status):
        light_df.at[light_num-1, 'status'] = False
        track_lights_list[light_num-1].configure(image=red_light)
        track_lights_list[light_num-1].image = red_light
        light_status_list[light_num-1].configure(image=red_light)
        light_status_list[light_num-1].image = red_light
    else:
        light_df.at[light_num-1, 'status'] = True
        track_lights_list[light_num-1].configure(image=green_light)
        track_lights_list[light_num-1].image = green_light
        light_status_list[light_num-1].configure(image=green_light)
        light_status_list[light_num-1].image = green_light
        
    if(other_status):
        light_df.at[other_light-1, 'status'] = False
        track_lights_list[other_light-1].configure(image=red_light)
        track_lights_list[other_light-1].image = red_light
        light_status_list[other_light-1].configure(image=red_light)
        light_status_list[other_light-1].image = red_light
    else:
        light_df.at[other_light-1, 'status'] = True
        track_lights_list[other_light-1].configure(image=green_light)
        track_lights_list[other_light-1].image = green_light
        light_status_list[other_light-1].configure(image=green_light)
        light_status_list[other_light-1].image = green_light
        
    if(switch_sel == 1):
        switch_sel = 2
        switch_labels_list[switch_num-1].configure(image=switch_2_img)
        switch_labels_list[switch_num-1].image = switch_2_img
    else:
        if(switch_sel == 2):
            switch_sel = 1
            switch_labels_list[switch_num-1].configure(image=switch_1_img)
            switch_labels_list[switch_num-1].image = switch_1_img
    switch_df.at[switch_num-1, 'select'] = switch_sel
    
    #use main controller class to switch track and lights
    first_light_lc = light_df.at[light_num-1, 'lc_addr']
    other_light_lc = light_df.at[other_light-1, 'lc_addr']
    
    first_light_pin = light_df.at[light_num-1, 'pin_#']
    other_light_pin = light_df.at[other_light-1, 'pin_#']
    
    main_controller.setLight(first_light_lc, first_light_pin, light_df.at[light_num-1, 'status'])
    main_controller.setLight(other_light_lc, other_light_pin, light_df.at[other_light-1, 'status'])
    
    switch_lc = switch_df.at[switch_num-1, 'lc_addr']
    switch_rev = switch_df.at[switch_num-1, 'rev_pin']
    switch_norm = switch_df.at[switch_num-1, 'norm_pin']
    switch_selection = switch_df.at[switch_num-1, 'select']
    
    main_controller.switchTurnout(switch_lc, switch_norm, switch_rev, switch_selection)
    print(switch_selection)
    
    

#currently just pull it from the slider
def det_ref_speed(train_num):
    global timer
    current_sens = int(train_df.at[train_num, 'current_sensor'])-1
    last_sens = int(train_df.at[train_num, 'last_sensor'])-1
    
    current_sens_x = sensor_df.at[current_sens, 'pos_x']
    current_sens_y = sensor_df.at[current_sens, 'pos_y']
    last_sens_x = sensor_df.at[last_sens, 'pos_x']
    last_sens_y = sensor_df.at[last_sens, 'pos_y']
    
    diff__x = abs(current_sens_x - last_sens_x)
    diff__y = abs(current_sens_y - last_sens_y)
    
    distance = math.sqrt((diff__x * diff__x)+(diff__y * diff__y))
    
    ref_speed = distance/timer
    print("ref_speed: " + str(ref_speed))
    print("distance: " + str(distance))
    print("timer: " + str(timer))
    print("diff x: " + str(diff__x))
    print("diff y: " + str(diff__y))
    train_df.at[train_num, 'ref_speed'] = ref_speed
    
    
    return;
#move train based on speeds, thats it
def move_train(train_num):
    next_dest = predict_next_sens(train_num)
    train_speed = train_df.at[train_num, 'real_speed']
    train__x = train_df.at[train_num, 'pos_x']
    train__y = train_df.at[train_num, 'pos_y']
    train_direction = train_dir_variables[train_num].get()
    new_x = train__x
    new_y = train__y
    
    current_sensor = train_df.at[train_num, 'current_sensor']
    if(current_sensor!=0):
        train_df.at[train_num, 'pos_x'] = sensor_df.at[int(current_sensor)-1, 'pos_x']
        train_df.at[train_num, 'pos_y'] = sensor_df.at[int(current_sensor)-1, 'pos_y']
        track_train.place(x=train_df.at[train_num,'pos_x'],y=train_df.at[train_num,'pos_y'])
        train_df.at[train_num, 'current_sensor'] = 0
        
        return
        
    if('sw' in next_dest):
        next_dest_x = switch_df.at[int(next_dest[3:])-1, 'pos_x']
        next_dest_y = switch_df.at[int(next_dest[3:])-1, 'pos_y']
    else:
        if('endcap' in next_dest):
           next_dest_x = endcap_df.at[int(next_dest[6:])-1, 'pos_x']
           next_dest_y = endcap_df.at[int(next_dest[6:])-1, 'pos_y']
        else:
           next_dest_x = sensor_df.at[int(next_dest)-1, 'pos_x']
           next_dest_y = sensor_df.at[int(next_dest)-1, 'pos_y']
    frac_x = 0
    frac_y = 0
    diff__x = next_dest_x - train__x
    diff__y = next_dest_y - train__y
    
    total_diff = math.sqrt(abs(diff__x * diff__x) + abs(diff__y * diff__y))
    if(total_diff != 0):
        frac_x = abs(diff__x/total_diff)
        frac_y = abs(diff__y/total_diff)
    
    if(diff__x>0):
        new_x = int(train__x + (train_speed*frac_x))
    if(diff__x<0):
        new_x = int(train__x - (train_speed*frac_x))
    if(diff__y>0):
        new_y = int(train__y + (train_speed*frac_y))
    if(diff__y<0):
        new_y = int(train__y - (train_speed*frac_y))
    
    if((abs(diff__x)<20) and (abs(diff__y)<20)):
        train_df.at[train_num, 'last_sensor'] = str(next_dest)

    
    train_df.at[train_num,'pos_x'] = new_x
    train_df.at[train_num,'pos_y'] = new_y
    
    track_train.place(x=train_df.at[train_num,'pos_x'],y=train_df.at[train_num,'pos_y'])
    
    return


# PREDICT WHAT SENSOR THE TRAIN IS LIKELY TRAVELLING TO BASED ON ITS DIRECTION
# return closest sensor in the direction the train is heading, from the last sensor
# INPUTS: train number
# OUTPUTS: destination sensor number
def predict_next_sens(train_num):
    train_direct = train_dir_variables[train_num].get()
    sw_sel = 1
    last_snsr = train_df.at[train_num, 'last_sensor']
    sw_num = 0
    sw_orient = 0
    
    if 'sw' in str(last_snsr):
        sw_num = int(last_snsr[3:])-1
        sw_orient = int(switch_df.at[sw_num, 'orient'])
        sw_sel = switch_df.at[sw_num, 'select']
        if(sw_orient==0):
            if(train_direct == 0):
                next_snsr = switch_df.at[sw_num, 'linked_rev']
            else:
                next_snsr = switch_df.at[sw_num, ('select_'+str(sw_sel))]
        else:
            if(train_direct == 0):
                next_snsr = switch_df.at[sw_num, ('select_'+str(sw_sel))]
            else:
                next_snsr = switch_df.at[sw_num, 'linked_rev']
    else:
    
        if(train_direct==0): # train go forward
            next_snsr = sensor_df.at[int(last_snsr)-1, 'linked_for']
        else:
            next_snsr = sensor_df.at[int(last_snsr)-1, 'linked_rev']
    
    return next_snsr
        

#------ Main User Interface Program -------#

#sensor_df = fill_dataframe(sensor_df, num_of_sensors)
train_df = fill_dataframe(train_df, num_of_trains)
light_df = fill_dataframe(light_df, num_of_lights)

train_df['last_sensor'] = train_df['last_sensor'].astype('str')
train_df['current_sensor'] = train_df['current_sensor'].astype('str')
light_df = pd.read_csv("light_df.csv")
sensor_df = pd.read_csv("sensor_df.csv")
switch_df = pd.read_csv("switch_df.csv")
switch_df['linked_rev'] = switch_df['linked_rev'].astype('str')
switch_df['select_1'] = switch_df['select_1'].astype('str')
switch_df['select_2'] = switch_df['select_2'].astype('str')

endcap_df = pd.read_csv("endcap_df.csv")

sensor_df['status'] = sensor_df['status'].astype(str)
sensor_df.at[0,'status'] = "Train 1"

window = Tk()

window.title("Train Controller 5000")

window.geometry('1200x750')

#Each sim_step is one action during the simulation process. It updates everything per step
def sim_step():
    #%%
    global timer
    global sync_passes
    global timer_started
    global sensor_last_det
    
    if(timer_started):
        timer += 1
    tripped_sensors = scan_sensors()
    if(len(tripped_sensors)>0):
        for sens_numb in tripped_sensors:
            print(sens_numb)
            train_0_cs = train_df.at[0,'current_sensor']
            train_0_ls = train_df.at[0,'last_sensor']
            if(sync_passes <2):
                if((sens_numb != train_0_cs) and (sens_numb != train_0_ls)):
                    sync_passes += 1
                    if(sync_passes == 1):
                        timer_started = True
                        train_df.at[0,'last_sensor'] = sens_numb
                        print("passed sensor " + str(sens_numb))
                    else:
                        train_df.at[0,'current_sensor'] = sens_numb
                        print("passed sensor " + str(sens_numb))
                        det_ref_speed(0)
            else:
                if(sens_numb != sensor_last_det):
                    sensor_last_det = sens_numb
                    if(sens_numb != train_0_ls):
                        if(train_df.at[0,'current_sensor'] != 0):
                            train_df.at[0,'last_sensor'] = train_df.at[0,'current_sensor']
                        train_df.at[0,'current_sensor'] = sens_numb
    
    slider_speed = train_speed_sliders[0].get()    
    if(sync_passes>1):
           train_df.at[0, 'real_speed'] = slider_speed * train_df.at[0, 'ref_speed']/30
           move_train(0)
    
    main_controller.sendSpeed(1505, slider_speed, train_dir_variables[0].get())
    
    
    window.after(50, sim_step)
    
    
def sim_start():
    train_speed_sliders[0].set(30)
    train_df.at[0,'current_sensor'] = 0
    train_df.at[0,'last_sensor'] = 0


    main_controller.switchTurnout(12, 4, 5, 1)
    main_controller.switchTurnout(12, 1, 0, 1)
    main_controller.switchTurnout(12, 3, 2, 1)
    sim_step()
    
#%%
#Frames
sliders_frame = Frame(window, bd=2)
sliders_frame.grid(column=0, row=0, columnspan=6, rowspan=16+num_train_actions-5)

sensor_frame = Frame(window, bd=2, bg="white")
sensor_frame.grid(column=6, row = 0,columnspan=2, rowspan = num_of_sensors-2)

track_frame = Frame(window, width=606, height=595)
track_frame.grid(column=8, row=0, rowspan = 18)

warning_frame = Frame(window)
warning_frame.grid(column=0, row=16+num_train_actions-5, columnspan=6, rowspan=2, sticky="w")

lights_frame = Frame(window, bg="white")
lights_frame.grid(column=0, row=18+num_train_actions-5, sticky="w")
#%%
#simulation button
btn = Button(sliders_frame, text="Start Simulation", command=sim_start)
btn.grid(column=0, row=0)

#%%
#train speed controls

#Train Actions

train_action_variables = [[0 for _ in  range(num_train_actions)] for _ in range(max_trains)]
train_action_selects = [[0 for _ in  range(num_train_actions)] for _ in range(max_trains)]
train_action_buttons = [[0 for _ in  range(num_train_actions)] for _ in range(max_trains)]
train_speed_sliders = [0 for _ in range(max_trains)]
train_slider_labels = [0 for _ in range(max_trains)]
train_dir_buttons = [[0,0] for _ in range(max_trains)]
train_dir_variables = [0 for _ in range(max_trains)]
default_actions = ["F1", "F2", "F3", "F4", "FL"]
#loops through and creates buttons and selecters etc. for trains
for i in range(max_trains):#one section for each train
    temp_column = 0 #temp column decides how far left/right train options are placed
    if((i==1)|(i==3)):
        temp_column = 5
    temp_row = 1 #decides how far up or down train options are placed
    if((i==2)|(i==3)):
        temp_row = 9+num_train_actions-5

    #create label for train
    train_slider_labels[i] = Label(sliders_frame, text=("Train "+str(i+1)+" Controls"))
    train_slider_labels[i].grid(column=temp_column, row=temp_row, columnspan=3)
    #create the speed slider for train
    train_speed_sliders[i] = Scale(sliders_frame, from_=50, to=0, tickinterval=10)
    train_speed_sliders[i].grid(column=temp_column, row=temp_row+1, rowspan=5, columnspan=1, ipady=20, ipadx=10)
    
    #create forward/reverse options for train
    train_dir_variables[i] = IntVar()
    train_dir_buttons[i][0] = Radiobutton(sliders_frame, text="Forward",
                                          variable = train_dir_variables[i],
                                          value = 0, indicatoron = 0).grid(column = temp_column, row=temp_row+6)
    train_dir_buttons[i][1] = Radiobutton(sliders_frame, text="Reverse",
                                          variable = train_dir_variables[i],
                                          value = 1, indicatoron = 0).grid(column = temp_column, row=temp_row+7)
    
    
    for j in range(num_train_actions):#creates 5 action buttons and output selectors for each train
            #create selecter
            train_action_variables[i][j] = StringVar(sliders_frame)
            train_action_variables[i][j].set(default_actions[j]) #default value
            #create button
            train_action_buttons[i][j] = Button(sliders_frame, text="Action " + str(j+1), command =partial(train_action_press, j))
            
            
            #different output options available
            train_action_selects[i][j] = OptionMenu(sliders_frame, train_action_variables[i][j], "F1", "F2", "F3", "F4", "FL")
            
            
            train_action_buttons[i][j].grid(column = temp_column+1, row = temp_row+j+1, ipadx=5)
            train_action_selects[i][j].grid(column = temp_column+2, row = temp_row+j+1, ipadx=5)

#%%
#sensor status labels
sensor_heading = Label(sensor_frame, text="Sensor #:", anchor="n")
sensor_heading.grid(column=0,row=0)
sensor_label_list = []
for i in range(num_of_sensors):
    new_label = Label(sensor_frame, text=("Sensor " + str(i+1) + ":"))
    new_label.grid(column=0, row=i+1)
    sensor_label_list.append(new_label)
    
#sensor status outs
sensor_status_heading = Label(sensor_frame, text="Detecting:")
sensor_status_heading.grid(column=1,row=0)

sens_status_label_list = []
for i in range(num_of_sensors):
    new_label = Label(sensor_frame, text = str(sensor_df.at[i,'status']))
    new_label.grid(column=1, row=i+1)
    sens_status_label_list.append(new_label)

#%%
#track layout
red_light = PhotoImage(file="light_red.png")
green_light = PhotoImage(file="light_green.png")
track_img = PhotoImage(file="track.png")
sensor_false_img = PhotoImage(file="sensor_false.png")
sensor_true_img = PhotoImage(file="sensor_true.png")
train_img = PhotoImage(file="train.png")
turn_point = Image.open("smallcircle.png").resize((10,10))
turn_point = ImageTk.PhotoImage(turn_point)
switch_1_img = PhotoImage(file="switch_1.png")
switch_2_img = PhotoImage(file="switch_2.png")
endcap_img = PhotoImage(file="endcap.png")

track_layout = Label(track_frame, image=track_img)
track_layout.image = track_img
track_layout.place(x=0, y=0, relwidth=1, relheight=1)

track_light_labels_list = []
track_lights_list =[]
for i in range(num_of_lights):
    if(light_df.at[i, 'status']): #light is green
        new_label = Label(track_frame, image=green_light)
        new_label.image = green_light
    else: #light is red
        new_label = Label(track_frame, image=red_light)
        new_label.image = red_light
    new_label.place(x=light_df.at[i,'pos_x'], y=light_df.at[i,'pos_y'])
    track_lights_list.append(new_label)
    new_label = Label(track_frame, text = "#" + str(i+1))
    new_label.place(x=light_df.at[i,'pos_x'], y=light_df.at[i,'pos_y']+30)
    track_light_labels_list.append(new_label)

track_sensor_labels_list = []
track_sensors_list =[]
for i in range(num_of_sensors):
    new_label = Label(track_frame, image=sensor_false_img)
    new_label.image = sensor_false_img
    
    new_label.place(x=sensor_df.at[i,'pos_x'], y=sensor_df.at[i,'pos_y'])
    track_sensors_list.append(new_label)  
    new_label = Label(track_frame, text = str(i+1), width=1, height=1)
    new_label.place(x=sensor_df.at[i,'pos_x']+7, y=sensor_df.at[i,'pos_y']+5)
    track_sensor_labels_list.append(new_label)
    
train_df.at[0,'pos_x'] = sensor_df.at[0,'pos_x']
train_df.at[0,'pos_y'] = sensor_df.at[0,'pos_y']
track_train = Label(track_frame, image=train_img)
track_train.place(x=train_df.at[0,'pos_x'],y=train_df.at[0,'pos_y'])

train_label = Label(track_frame, text="Train 1")
train_label.place(x=train_df.at[0,'pos_x']-50,y=train_df.at[0,'pos_y'])
#%%
#warning labels
warning_title = Label(warning_frame, text="   Warnings:", anchor="w")
warning_title.grid(column=0, row=0,sticky="w", columnspan=1)
warning_text = Label(warning_frame, text="   None", anchor="w")
warning_text.grid(column=0, row=1, sticky="w", columnspan=3)


     
#%%
# Switches labels
switch_labels_list = []
switch_buttons_list = []
for i in range(num_switches):
    new_label = Label(track_frame, image=switch_1_img)
    new_label.image = switch_1_img
    new_label.place(x=switch_df.at[i,'pos_x'], y=switch_df.at[i,'pos_y'])
    
    switch_labels_list.append(new_label)
#%%
#Lights labels

light_title = Label(lights_frame, text="  Light Statuses:", anchor="w")
light_title.grid(column=0, row=0, columnspan=2, sticky="w")
current_row = 1
light_labels_list =[]
light_status_list = []
light_buttons_list = []
for i in range(num_of_lights):
    new_label = Label(lights_frame, text="  Light #" + str(i+1), anchor="nw")
    new_label.grid(column=i, row=2)
    light_labels_list.append(new_label)
    
    new_button = Button(lights_frame, text="Change", command=partial(light_button,i+1))
    new_button.grid(column=i, row=4)
    light_buttons_list.append(new_button)
    #light statuses
    if(light_df.at[i, 'status']): #light is green
        new_label = Label(lights_frame, image=green_light, anchor="nw")
        new_label.image = green_light
    else: #light is red
        new_label = Label(lights_frame, image=red_light, anchor="nw")
        new_label.image = red_light
    new_label.grid(column=i, row=3)
    light_status_list.append(new_label)   
#%%
# Endcap Labels
endcap_labels_list = []
for i in range(num_endcaps):
    new_label = Label(track_frame, image=endcap_img)
    new_label.image = endcap_img
    new_label.place(x=endcap_df.at[i,'pos_x'], y=endcap_df.at[i,'pos_y'])
    
    endcap_labels_list.append(new_label)
    
window.mainloop()
