import numpy as np
import matplotlib.pyplot as plt
from numpy.polynomial.polynomial import Polynomial
import matplotlib.ticker as ticker

# Data points for preparation time
number_of_points = np.array([11025, 65025, 255025, 570025, 1010025])
preparation_time = np.array([25.466166496276855, 41.009005546569824, 97.83929347991943, 191.2210750579834, 319.50931310653687])

# Data points for CFD time
time_length = np.array([1, 10, 50, 100, 200])
cfd_time = np.array([32.30290222167969, 68.64088892936707, 246.1055448055267, 455.3200259208679, 889.4850943088531])

# Plotting the preparation time data
plt.figure(figsize=(8, 6))
plt.scatter(number_of_points, preparation_time, color='blue', label='Preparation Time')

# Fit a linear polynomial to the preparation time data
p1 = Polynomial.fit(number_of_points, preparation_time, 1)
x_new = np.linspace(number_of_points[0], number_of_points[-1], 500)
y_new_1 = p1(x_new)

# Plot the fitted curve for preparation time
plt.plot(x_new, y_new_1, color='green', linestyle='--', label='Linear Fit (Preparation Time)')

# Adjust axis labels
plt.xlabel('Number of Points (log scale)', fontsize=14)
plt.ylabel('Time (seconds)', fontsize=14)
plt.title('Wind Simulation Preparation Time vs Number of Points', fontsize=12)
plt.legend()

# Adjust x-axis to use 10^x format
ax = plt.gca()
ax.set_xscale('log')
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'$10^{{{int(np.log10(x))}}}$'))
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

# Save the preparation time plot
plt.savefig("preparation_time_vs_points.png")

# Show the preparation time plot
plt.show()

# Display the polynomial coefficients for preparation time
print("Linear Fit Coefficients (Preparation Time):", p1.convert().coef)
