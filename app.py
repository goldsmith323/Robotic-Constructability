"""
Author: Hossein Zargar
Date: June 2024
Version: 1.0

This script is part of my PhD dissertation in the Architectural Engineering program at Penn State.
Title: Incorporating Robotic Constructability in Computational Design Optimization
Link to dissertation: https://etda.libraries.psu.edu/catalog/26038szz188

Description:
This script provides a graphical user interface (GUI) for generating Pareto plots from a given dataset.
It allows users to select columns for the X and Y axes and highlights points on the plot.

Abstract:
This research explores the inclusion of constructability metrics in early computational design exploration, 
focusing on how structures should be built with robots. It includes studies on robotic construction tasks, 
construction-aware design exploration, evaluation of constructability based on assembly sequences. 
The goal is to incorporate robotic constructability knowledge into early-stage design workflows 
to provide adaptable construction-related suggestions and guidance.
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageGrab
import itertools
import os
import matplotlib.font_manager as font_manager
plt.style.use('ggplot')

class ParetoPlotGeneratorApp:
    def __init__(self, master, dataframe):
        self.master = master
        self.dataframe = dataframe
        self.highlighted_points = {}
        self.marker_list = ['^', 's', 'o', 'P', 'X', 'v']
        self.marker_cycle = itertools.cycle(self.marker_list)
        
        master.title('Select Columns for Scatter Plot')
        master.geometry("1000x1000")
        
        style = ttk.Style()
        for widget in ['TLabel', 'TButton', 'TCombobox']:
            style.configure(widget, font=('Century Gothic', 12))
    
        input_frame = ttk.Frame(master)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
        master.grid_columnconfigure(0, weight=1)
        
        ttk.Label(input_frame, text="Select X-axis column:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.x_var = tk.StringVar(master)
        self.x_dropdown = ttk.Combobox(input_frame, textvariable=self.x_var, state="readonly", width=50)
        self.x_dropdown['values'] = list(dataframe.columns)
        self.x_dropdown.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Select Y-axis column:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.y_var = tk.StringVar(master)
        self.y_dropdown = ttk.Combobox(input_frame, textvariable=self.y_var, state="readonly", width=50)
        self.y_dropdown['values'] = list(dataframe.columns)
        self.y_dropdown.grid(row=1, column=1, padx=5, pady=5)
        
        self.plot_button = ttk.Button(master, text="Create Scatter Plot", command=self.on_plot)
        self.plot_button.grid(row=1, column=0, pady=5, sticky='ew')
    
    def on_plot(self):
        column_x = self.x_var.get()
        column_y = self.y_var.get()
        self.create_scatter_plot(column_x, column_y)
    
    def create_scatter_plot(self, column_x, column_y):
        excluded_columns = ['index', 'Ru1', 'Ru2', 'Ru3', 'v1', 'v2', 'v3', 'v4', 'v5', 'boundrary area (m2)', 'length (m)', 'width (m)']
        if column_x in excluded_columns or column_y in excluded_columns:
            self.fig, self.ax = plt.subplots()
            x = self.dataframe[column_x]
            y = self.dataframe[column_y]

            self.scatter = self.ax.scatter(x, y, label='data points')
            self.ax.set_xlabel(column_x)
            self.ax.set_ylabel(column_y)
            self.ax.legend(fontsize='6') 

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.grid(row=3, column=0, columnspan=2)
            self.canvas.draw()

            self.canvas.mpl_connect('button_press_event', self.on_click)
        else:
            self.fig, self.ax = plt.subplots()
            x = self.dataframe[column_x]
            y = self.dataframe[column_y]

            scores = np.vstack((x, y)).T
            if (column_x in ['robot viability rating [wall panels] (0 to 1)', 'robot viability rating [roof panels] (0 to 1)']) and (column_y in ['robot viability rating [wall panels] (0 to 1)', 'robot viability rating [wall panels] (0 to 1)']):
                pareto_front = self.identify_pareto(scores.copy(), True, True)
            elif (column_x in ['robot viability rating [wall panels] (0 to 1)', 'robot viability rating [roof panels] (0 to 1)']):
                pareto_front = self.identify_pareto(scores.copy(), True, False)
            elif (column_y in ['robot viability rating [wall panels] (0 to 1)', 'robot viability rating [roof panels] (0 to 1)']):
                pareto_front = self.identify_pareto(scores.copy(), False, True)
            else:
                pareto_front = self.identify_pareto(scores.copy(), False, False)

            font_prop = font_manager.FontProperties(family='Century Gothic', size=12)
            plt.rcParams['font.family'] = font_prop.get_family()
            plt.rcParams['font.size'] = 12

            self.scatter = self.ax.scatter(x, y, color='#daa622', label='data points')
            pareto_scatter = self.ax.scatter(x[pareto_front], y[pareto_front], color='#008080', label='pareto front')

            self.ax.set_xlabel(column_x, fontproperties=font_prop)
            self.ax.set_ylabel(column_y, fontproperties=font_prop)

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.grid(row=3, column=0, columnspan=2)
            self.canvas.draw()

            save_button = tk.Button(self.master, text="Save Canvas", command=lambda: self.save_scatter())
            save_button.grid(row=4, column=0, pady=4)

            self.canvas.mpl_connect('button_press_event', self.on_click)
    
    def save_scatter(self):
        self.fig.savefig('scatter_plot.png')
        print("Canvas saved as 'scatter_plot.png'")

    def on_click(self, event):
        if self.scatter.contains(event)[0]:
            ind = self.scatter.contains(event)[1]["ind"][0]
            # Retrieve the 'index' column value from the DataFrame and convert it to an integer
            index_value = int(self.dataframe.iloc[ind]['index'])
            print(index_value)
            x, y = self.dataframe.iloc[ind][self.x_var.get()], self.dataframe.iloc[ind][self.y_var.get()]
            
            marker = next(self.marker_cycle)
            self.highlight_point(x, y, marker, index_value)
    
    def marker_to_unicode(self, marker):
        symbols = {
            '^': '▲',
            's': '■',
            'o': '●',
            'P': '✚',
            'X': '✖',
            'v': '▼',
        }
        return symbols.get(marker, '?')

    def highlight_point(self, x, y, marker, index):
        highlight, = self.ax.plot(x, y, marker, markersize=10, markerfacecolor='black', markeredgecolor='black', markeredgewidth=2)
        self.highlighted_points[index] = highlight
        self.canvas.draw()

        image_path = f"models/{index}.png"

        if os.path.exists(image_path):
            img = Image.open(image_path)
            max_size = (800, 600)
            img.thumbnail(max_size)
            img_width, img_height = img.size

            popup = tk.Toplevel()
            popup.title('Image Display')
            popup.geometry(f'{int(1.5 * img_width)}x{int(1.1 *img_height)}')
            canvas = tk.Canvas(popup, width=int(1.5 * img_width), height=img_height)
            canvas.pack()
            
            tkimage = ImageTk.PhotoImage(img)
            image_offset = 150 
            canvas.create_rectangle(0, 0, int(image_offset*8), img_height, fill='white', outline='')
            canvas.create_image(image_offset, 0, anchor='nw', image=tkimage)

            max_bar_width = 100
            max_bar_height = 12

            canvas.image = tkimage
            
            # index_value = int(self.dataframe.iloc[index]['index'])
            index_value = self.dataframe[self.dataframe['index'] == index].index[0]
            print('index_value:', index_value)  
            

            max_values = {
                'travel_time': self.dataframe['mobile robot travel time (min)'].max(),
                'wall_rating': self.dataframe['robot viability rating [wall panels] (0 to 1)'].max(),
                'roof_rating': self.dataframe['robot viability rating [roof panels] (0 to 1)'].max(),
                'EC': self.dataframe['embodied carbon (kgCO2e)'].max()
            }

            # Normalize values
            normalized_values = {
                'travel_time': (self.dataframe['mobile robot travel time (min)'] - self.dataframe['mobile robot travel time (min)'].min()) / (max_values['travel_time'] - self.dataframe['mobile robot travel time (min)'].min()),
                'wall_rating': (self.dataframe['robot viability rating [wall panels] (0 to 1)'] - self.dataframe['robot viability rating [wall panels] (0 to 1)'].min()) / (max_values['wall_rating'] - self.dataframe['robot viability rating [wall panels] (0 to 1)'].min()),
                'roof_rating': (self.dataframe['robot viability rating [roof panels] (0 to 1)'] - self.dataframe['robot viability rating [roof panels] (0 to 1)'].min()) / (max_values['roof_rating'] - self.dataframe['robot viability rating [roof panels] (0 to 1)'].min()),
                'EC': (self.dataframe['embodied carbon (kgCO2e)'] - self.dataframe['embodied carbon (kgCO2e)'].min()) / (max_values['EC'] - self.dataframe['embodied carbon (kgCO2e)'].min())
            }


            # Get values for the selected index
            values = {
                'travel_time': self.dataframe['mobile robot travel time (min)'].iloc[index_value],
                'wall_rating': self.dataframe['robot viability rating [wall panels] (0 to 1)'].iloc[index_value],
                'roof_rating': self.dataframe['robot viability rating [roof panels] (0 to 1)'].iloc[index_value],
                'EC': self.dataframe['embodied carbon (kgCO2e)'].iloc[index_value]
            }

            # Get normalized values for the selected index
            normalized_values_index = {
                'travel_time': normalized_values['travel_time'].iloc[index_value],
                'wall_rating': normalized_values['wall_rating'].iloc[index_value],
                'roof_rating': normalized_values['roof_rating'].iloc[index_value],
                'EC': normalized_values['EC'].iloc[index_value]
            }

            # Calculate ratios
            ratios = {
                'travel_time': 1 - normalized_values_index['travel_time'],
                'wall_rating': normalized_values_index['wall_rating'],
                'roof_rating': normalized_values_index['roof_rating'],
                'EC': 1 - normalized_values_index['EC']
            }

            bar_widths = {key: ratio * max_bar_width for key, ratio in ratios.items()}

            for i, key in enumerate(['EC', 'travel_time', 'wall_rating', 'roof_rating']):
                canvas.create_rectangle(10, 30 + i * 20, 10 + max_bar_width, 30 + i * 20 + max_bar_height, fill='lightgrey', outline='')

            for i, key in enumerate(['EC', 'travel_time', 'wall_rating', 'roof_rating']):
                canvas.create_rectangle(10, 30 + i * 20, 10 + bar_widths[key], 30 + i * 20 + max_bar_height, fill='#333333', outline='')

            marker_symbol = self.marker_to_unicode(marker)

            labels = {
                'EC': f'embodied carbon (kgCO2e): {values["EC"]}',
                'travel_time': f'mobile robot travel time (min): {values["travel_time"]}',
                'wall_rating': f'robot viability rating [wall panels] (0 to 1): {values["wall_rating"]}',
                'roof_rating': f'robot viability rating [roof panels] (0 to 1): {values["roof_rating"]}'
            }

            for i, (key, label) in enumerate(labels.items()):
                canvas.create_text(10 + max_bar_width + 5, 30 + i * 20 + max_bar_height / 2, anchor='w', text=label, fill='black', font=('Century Gothic', '8'))
                canvas.create_text(10 + max_bar_width + 5, 30 + i * 20 + max_bar_height / 2 + 20, anchor='w', text=f'{values[key]}', fill='white', font=('Century Gothic', '8'))

            canvas.create_text(10, 5, anchor='nw', text=f'{marker_symbol}', fill='black', font=('Century Gothic', '14', 'bold'))
            canvas.create_text(30, 10, anchor='nw', text=f"       index : {index}", fill='black', font=('Century Gothic', 8))

            canvas.image = tkimage

            save_button = tk.Button(popup, text="Save Canvas", command=lambda: self.save_canvas(canvas, popup))
            save_button.pack()

            popup.bind('<Destroy>', lambda event, index=index: self.remove_highlight(index))
    
    def save_canvas(self, canvas, popup):
        x = popup.winfo_rootx() + canvas.winfo_x()
        y = popup.winfo_rooty() + canvas.winfo_y()
        x1 = x + canvas.winfo_width()
        y1 = y + canvas.winfo_height()

        image = ImageGrab.grab().crop((x, y, x1, y1))
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if save_path:
            try:
                image.save(save_path)
                messagebox.showinfo("Save Canvas", "Canvas successfully saved!")
            except Exception as e:
                messagebox.showerror("Save Canvas", "Failed to save canvas.\n" + str(e))

    def remove_highlight(self, index):
        if index in self.highlighted_points:
            self.highlighted_points[index].remove()
            del self.highlighted_points[index]
            self.canvas.draw()

    @staticmethod
    def identify_pareto(scores, bigger_is_better_x, bigger_is_better_y):
        is_pareto = np.ones(scores.shape[0], dtype=bool)
        
        if bigger_is_better_x and bigger_is_better_y:
            for i in range(scores.shape[0]):
                for j in range(scores.shape[0]):
                    if all(scores[j] >= scores[i]) and any(scores[j] > scores[i]) and i != j:
                        is_pareto[i] = False
                        break
        elif bigger_is_better_x:
            for i in range(scores.shape[0]):
                for j in range(scores.shape[0]):
                    if scores[j][0] >= scores[i][0] and scores[j][1] < scores[i][1] and i != j:
                        is_pareto[i] = False
                        break
        elif bigger_is_better_y:
            for i in range(scores.shape[0]):
                for j in range(scores.shape[0]):
                    if scores[j][0] < scores[i][0] and scores[j][1] >= scores[i][1] and i != j:
                        is_pareto[i] = False
                        break
        else:
            for i in range(scores.shape[0]):
                for j in range(scores.shape[0]):
                    if all(scores[j] <= scores[i]) and any(scores[j] < scores[i]) and i != j:
                        is_pareto[i] = False
                        break

        return is_pareto

def main():
    file_path = 'data/Final Model Info.csv' 
    df = pd.read_csv(file_path)

    root = tk.Tk()
    app = ParetoPlotGeneratorApp(root, df)
    root.mainloop()

if __name__ == "__main__":
    main()