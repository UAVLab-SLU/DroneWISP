import numpy as np
import matplotlib.pyplot as plt
from numpy.polynomial.polynomial import Polynomial
import matplotlib.ticker as ticker

# Data points for preparation time
number_of_points = np.array([11025, 65025, 255025, 570025, 1010025])
preparation_time = np.array([25.466166496276855, 41.009005546569824, 97.83929347991943, 191.2210750579834, 319.50931310653687])

scan_time = np.array([7.140237092971802, 9.17207670211792, 11.23307180404663, 13.291276454925537, 17.368849992752075])

# # Data points for CFD time
# time_length = np.array([1, 10, 50, 100, 200])
# cfd_time = np.array([32.30290222167969, 68.64088892936707, 246.1055448055267, 455.3200259208679, 889.4850943088531])

# Calculate area from number of points
area = np.sqrt(number_of_points / 25)

# Plotting the preparation time data
plt.figure(figsize=(8, 6))
plt.scatter(area, preparation_time, color='blue', label='Total Wind Vector Computation time')

# Fit a linear polynomial to the preparation time data
p1 = Polynomial.fit(area, preparation_time, 1)
x_new = np.linspace(area[0], area[-1], 500)
y_new_1 = p1(x_new)

# Plot the fitted curve for preparation time
plt.plot(x_new, y_new_1, color='green', linestyle='--', label='Linear Fit (Total Computation Time)')

# Plotting the scan time data
plt.scatter(area, scan_time, color='red', label='Scan Time')

# Fit a linear polynomial to the scan time data
p2 = Polynomial.fit(area, scan_time, 1)
y_new_2 = p2(x_new)

# Plot the fitted curve for scan time
plt.plot(x_new, y_new_2, color='orange', linestyle='--', label='Linear Fit (Scan Time)')

# Adjust axis labels
plt.xlabel('Area (meter squared)', fontsize=14)
plt.ylabel('Time (seconds)', fontsize=14)
plt.title('Wind Vector Computation time vs Area', fontsize=12)
plt.legend()

# Adjust x-axis to use regular format
ax = plt.gca()
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.1f}'))
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

# Save the combined plot
plt.savefig("preparation_and_scan_time_vs_area.png")

# Show the combined plot
plt.show()

# Display the polynomial coefficients for preparation and scan time
print("Linear Fit Coefficients (Preparation Time):", p1.convert().coef)
print("Linear Fit Coefficients (Scan Time):", p2.convert().coef)