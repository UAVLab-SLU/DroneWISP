import read_U
import read_points
import matplotlib.pyplot as plt
import plotly.express as px


def plot_vel_and_point_interactive(points, U):
    """
    :param points: list of 3d tuples coordinates
    :param U: list of velocity values
    Plot the points and U where color is the U value sum
    """
    # plot the points and U where color is the U value sum

    if len(points) > len(U):
        print("points count > U count")
        points = points[:len(U)]
    elif len(points) < len(U):
        print("points count < U count")
        U = U[:len(points)]

    color_abs = [abs(u[0]) + abs(u[1]) + abs(u[2]) for u in U]

    U_string = [str(u[0]) + " " + str(u[1]) + " " + str(u[2]) for u in U]


    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    fig = px.scatter_3d()
    points = read_points.read_points('../run/motorBike/constant/polyMesh/points')
    points = points[:1701]
    fig.add_scatter3d(x=[point[0] for point in points],
                      y=[point[1] for point in points],
                      z=[point[2] for point in points],
                      mode = 'markers',
                      marker=dict(size=1,color = color_abs),
                      hovertext = U_string[:1701])

    # show color legend
    fig.update_layout(coloraxis_colorbar=dict(
        title="Velocity",
        thicknessmode="pixels", thickness=50,
        lenmode="pixels", len=200,
        yanchor="top", y=1,
        ticks="outside", ticksuffix="",
        dtick=0.1
    ))



    # disable connection line
    fig.update_traces(connectgaps=False)
    # delete html file if exists
    import os
    if os.path.exists('test.html'):
        os.remove('test.html')
    fig.write_html('test.html')
    plt.close()



if __name__ == '__main__':
    # read the points
    points = read_points.read_points('../run/motorBike/constant/polyMesh/points')
    # read the U file
    U = read_U.read_u('../run/motorBike/1/U')
    if len(points) > len(U):
        print("difference:", len(points) - len(U))
        print("points count > U count")
        points = points[:len(U)]
    elif len(points) < len(U):
        print("difference:", len(U) - len(points))
        print("points count < U count")
        U = U[:len(points)]



    plot_vel_and_point_interactive(points, U)