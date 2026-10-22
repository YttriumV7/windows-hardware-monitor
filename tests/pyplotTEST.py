import matplotlib.pyplot as plt #module for creating the graphs
import numpy as np

categories = np.array(["Grains", "Vegetables", "Fruits", "Protein", "Dairy"]) # Array to plot on the graph's x-axis
values = np.array([4, 2, 3, 5, 3]) # Values of each category to plot on the y-axis

plt.plot(categories, values) # plots the values on the graph
plt.show() #displays the graph