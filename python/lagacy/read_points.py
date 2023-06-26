import matplotlib.pyplot as plt
import plotly.express as px
import time
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

    points = [list(map(float, point.strip('()\n').split())) for point in points_data]
    print("points count:", len(points))

    return points


def plot_3d_interactive(path):
    points = read_points(path)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    x = [point[0] for point in points]
    y = [point[1] for point in points]
    z = [point[2] for point in points]
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    fig = px.scatter_3d(title="points")
    fig.add_scatter3d(x=x, y=y, z=z, name="points",mode = 'markers',marker=dict(size=1,color='red'))

    # use time + points.html as the file name
    current_local_time = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
    fig.write_html('points_'+ current_local_time + '.html')

    plt.close()


if __name__ == '__main__':
    plot_3d_interactive('../run/blockEnv/constant/polyMesh/points')



    # points = read_points('../run/motorBike/constant/polyMesh/points')
    #
    # # plot the points in line chart
    # import matplotlib.pyplot as plt
    # plt.plot([point[0] for point in points], [point[1] for point in points], [point[2] for point in points])
    # plt.show()

