def read_points(path_to_points):
    """
    Read the points file and return a list of tuples containing the coordinates
    :param path_to_points: path to the points file
    :return: list of 3d tuples coordinates
    """
    with open(path_to_points, 'r') as file:
        lines = file.readlines()

    points_start_index = lines.index('(\n') + 1
    points_end_index = lines.index(')\n')
    points_data = lines[points_start_index:points_end_index]

    points = [tuple(map(float, point.strip('()\n').split())) for point in points_data]
    print("points count:", len(points))

    return points

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import plotly.express as px

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    fig = px.scatter_3d()
    points = read_points('../run/motorBike/constant/polyMesh/points')
    # fig.add_scatter3d(x=[1, 2, 3], y=[1, 2, 3], z=[1, 2, 3])
    fig.add_scatter3d(x=[point[0] for point in points], y=[point[1] for point in points], z=[point[2] for point in points])

    # decrease dot size
    fig.update_traces(marker=dict(size=1))

    # disable connection line
    fig.update_traces(connectgaps=False)

    fig.write_html('test.html')
    plt.close()


    # Extracted points
    # points = read_points('../run/motorBike/constant/polyMesh/points')
    #
    # # Create a 3D plot
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    #
    # # Extract x, y, and z coordinates from the points
    # x_coords, y_coords, z_coords = zip(*points)
    #
    # # Plot the points
    # ax.scatter(x_coords, y_coords, z_coords, c='r', marker='o')
    #
    # # Set labels for the axes
    # ax.set_xlabel('X')
    # ax.set_ylabel('Y')
    # ax.set_zlabel('Z')
    #
    # # Show the plot
    # plt.show()

