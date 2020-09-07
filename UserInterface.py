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
from tkinter import Tk, Label, Button, Scale, Frame, PhotoImage
from tkinter import *
import numpy as np
import pandas as pd
from numpy import nan
import time
from PIL import ImageTk,Image 

#---- PROGRAM PARAMETERS ----#
num_of_trains = 1
num_of_sensors = 21
num_of_lights = 6
color_list = ["red", "green", "blue", "yellow"]
train_order = [0,1,2,3,4,5,6,7,8,9,10,11,0,12,13,14,15,16,19,20,18,2,3,4,5,6,7,8,9,10,11] #sensor to sensor
order_index = 0
#----------------------------#
#---- DATA STRUCTURES ----#
# Sensor dataframe
# - 5 columns : sensor #, x position, y position, status, train detected
# - rows sorted by sensor # -- number of rows = number of sensors
sensor_df = pd.DataFrame(columns=['sensor_#', 'status', 'pos_x', 'pos_y',
                                  'train_detected'])

# Train dataframe
# - 7 columns : train #, color, x position, y position, last sensor,
#                current sensor, speed in x direction, speed in y direction, realtime speed
# - rows sorted by train # -- number of rows = number of trains
train_df = pd.DataFrame(columns = ['train_#', 'color', 'pos_x', 'pos_y',
                                   'last_sensor', 'current_sensor',
                                   'speed_x', 'speed_y', 'real_speed'])

# Light Signal dataframe
# - 4 columns : light #, x position, y position, status
# - rows sorted by light # -- number of rows = number of lights
light_df = pd.DataFrame(columns = ['light_#', 'pos_x', 'pos_y', 'status'])

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

#------ Main User Interface Program -------#

sensor_df = fill_dataframe(sensor_df, num_of_sensors)
train_df = fill_dataframe(train_df, num_of_trains)
light_df = fill_dataframe(light_df, num_of_lights)

light_df = pd.read_csv("light_df.csv")
sensor_df = pd.read_csv("sensor_df.csv")

sensor_df['status'] = sensor_df['status'].astype(str)
sensor_df.at[0,'status'] = "Train 0"

window = Tk()

window.title("Train Controller 5000")

window.geometry('900x750')

#Each sim_step is one action during the simulation process. It updates everything per step
# and the train will move according to the train_order list. This function will not be in the final
# design, but it is a good way to show how the UI operates
def sim_step():
    global order_index
    global train_order
    
    train_df.at[0,'pos_x'] = sensor_df.at[train_order[order_index],'pos_x']
    train_df.at[0,'pos_y'] = sensor_df.at[train_order[order_index],'pos_y']
    track_train.place(x=train_df.at[0,'pos_x'],y=train_df.at[0,'pos_y'])
    
    sensor_df.at[train_order[order_index],'status'] = "Train 0"
    sensor_df.at[train_order[order_index-1],'status'] = "False"
    
    for i in range(len(sens_status_label_list)):
        sens_status_label_list[i].configure(text=sensor_df.at[i,'status'])
    
    for i in range(len(light_status_list)):
        if(light_df.at[i,'status']):
            track_lights_list[i].configure(image=green_light)
            track_lights_list[i].image = green_light
            light_status_list[i].configure(image=green_light)
            light_status_list[i].image = green_light
        else:
            track_lights_list[i].configure(image=red_light)
            track_lights_list[i].image = red_light
            light_status_list[i].configure(image=red_light)
            light_status_list[i].image = red_light
    
    if(order_index>=len(train_order)-1):
        order_index = 0
    else:
        order_index += 1
        
    if(order_index==19):
        light_df.at[5,'status'] = False
        sensor_df.at[18,'status'] = "Unknown Obj"
        warning_text.configure(text="Potential Collision at Sensor: 18")
        
    if(order_index==21):
        time.sleep(7)
        light_df.at[5,'status'] = True
        sensor_df.at[18,'status'] = "False"
        warning_text.configure(text="None")
        track_lights_list[5].configure(image=green_light)
        track_lights_list[5].image = green_light
        light_status_list[5].configure(image=green_light)
        light_status_list[5].image = green_light
    window.after(int(10000/(train_0_speed_slider.get()+1)), sim_step)
    
    
def sim_start():
    light_df['status'] = True
    sim_step()
    
#%%
#Frames
sliders_frame = Frame(window, bd=2)
sliders_frame.place(x=0, y=0)

sensor_frame = Frame(window, bd=2, bg="white", height=350)
sensor_frame.place(x=210, y=0)

track_frame = Frame(window)
track_frame.place(x=375, y=0, width=500, height=500)

warning_frame = Frame(window)
warning_frame.place(x=0,y=300)

lights_frame = Frame(window, bg="white")
lights_frame.place(x=0, y=350)
#%%
#simulation button
btn = Button(sliders_frame, text="Start Simulation", command=sim_start)
btn.grid(column=0, row=0)

#%%
#train speed controls
train_0_speed_slider = Scale(sliders_frame, from_=30, to=0, tickinterval=10)
train_0_speed_slider.grid(column=0,row=2)
slider_label_0 = Label(sliders_frame, text="Train 0 Speed")
slider_label_0.grid(column=0, row=1)

train_1_speed_slider = Scale(sliders_frame, from_=30, to=0, tickinterval=10)
train_1_speed_slider.grid(column=1,row=2)
slider_label_1 = Label(sliders_frame, text="Train 1 Speed")
slider_label_1.grid(column=1, row=1)

train_2_speed_slider = Scale(sliders_frame, from_=30, to=0, tickinterval=10)
train_2_speed_slider.grid(column=0,row=4)
slider_label_2 = Label(sliders_frame, text="Train 2 Speed")
slider_label_2.grid(column=0, row=3)

train_3_speed_slider = Scale(sliders_frame, from_=30, to=0, tickinterval=10)
train_3_speed_slider.grid(column=1,row=4)
slider_label_3 = Label(sliders_frame, text="Train 3 Speed")
slider_label_3.grid(column=1, row=3)

#%%
#sensor status labels
sensor_heading = Label(sensor_frame, text="Sensor #:", anchor="n")
sensor_heading.grid(column=0,row=0)
sensor_label_list = []
for i in range(num_of_sensors):
    new_label = Label(sensor_frame, text=("Sensor " + str(i) + ":"))
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
    new_label = Label(track_frame, text = "Light #" + str(i))
    new_label.place(x=light_df.at[i,'pos_x']-15, y=light_df.at[i,'pos_y']+30)
    track_light_labels_list.append(new_label)

track_sensor_labels_list = []
track_sensors_list =[]
for i in range(num_of_sensors):
    new_label = Label(track_frame, image=sensor_false_img)
    new_label.image = sensor_false_img
    
    new_label.place(x=sensor_df.at[i,'pos_x'], y=sensor_df.at[i,'pos_y'])
    track_sensors_list.append(new_label)  
    new_label = Label(track_frame, text = str(i), width=1, height=1)
    new_label.place(x=sensor_df.at[i,'pos_x']+7, y=sensor_df.at[i,'pos_y']+5)
    track_sensor_labels_list.append(new_label)
    
train_df.at[0,'pos_x'] = sensor_df.at[0,'pos_x']
train_df.at[0,'pos_y'] = sensor_df.at[0,'pos_y']
track_train = Label(track_frame, image=train_img)
track_train.place(x=train_df.at[0,'pos_x'],y=train_df.at[0,'pos_y'])

train_label = Label(track_frame, text="Train 0")
train_label.place(x=train_df.at[0,'pos_x']-50,y=train_df.at[0,'pos_y'])
#%%
#warning labels
warning_title = Label(warning_frame, text="Warnings:", anchor="nw")
warning_title.grid(column=0, row=0)
warning_text = Label(warning_frame, text="None", anchor="nw")
warning_text.grid(column=0, row=1)

#%%
#Lights labels

light_title = Label(lights_frame, text="Light Statuses:", anchor="center")
light_title.grid(column=0, row=0)
current_row = 1
light_labels_list =[]
light_status_list = []
for i in range(num_of_lights):
    new_label = Label(lights_frame, text="Light #" + str(i+1), anchor="nw")
    new_label.grid(column=i%2, row=int((i/2)+1)*2)
    light_labels_list.append(new_label)
    
    #light statuses
    if(light_df.at[i, 'status']): #light is green
        new_label = Label(lights_frame, image=green_light, anchor="nw")
        new_label.image = green_light
    else: #light is red
        new_label = Label(lights_frame, image=red_light, anchor="nw")
        new_label.image = red_light
    new_label.grid(column=i%2, row=(int((i/2)+1)*2)+1)
    light_status_list.append(new_label)
        

window.mainloop()
