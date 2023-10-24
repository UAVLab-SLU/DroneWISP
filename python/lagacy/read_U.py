# test file to read the U file and print the velocity values at each location
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
def read_u(path_to_u):
    """
    Read the U file and return a list of values
    :param path_to_u: path to the U file
    :return: list of velocity values
    """
    u = ParsedParameterFile(path_to_u)
    return u

def read_U_ofpp(path_to_u):
    u = Ofpp.parse_internal_field(path_to_u)
    print(u.shape)
    return u


def read_internal_field(path):
    bf = Ofpp.parse_boundary_field(path)
    print(bf)
    return bf

def plot_10_u():
    filePath = '../run/motorBike/10/U'
    U = read_u(filePath)
    # plot the velocity values in a line chart
    import matplotlib.pyplot as plt
    plt.plot(U)
    plt.show()


if __name__ == '__main__':


    path = '../../run/motorBike2/system/controlDict'
    u = read_u(path)
    #path_to_boundary = '../run/blockEnv/1/U'
    # read_U_ofpp(path_to_u)
    # read_internal_field(path_to_boundary)

    # u_field = ParsedParameterFile(path_to_u).content
    # print("u_field:", u_field)
    # u_field['internalField'].boundaryField


    # combine all processors data
    # total_num = 0
    # for i in range(0, 5):
    #     # run/motorBike/processor0/1/U
    #     filePath = '../run/motorBike/processor' + str(i) + '/1/U'
    #     total_num += len(read_u(filePath))
    # print("total_num:", total_num)

