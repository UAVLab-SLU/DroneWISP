# test file to read the U file and print the velocity values at each location
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
def read_U(path_to_U):
    """
    Read the U file and return a list of values
    :param path_to_U: path to the U file
    :return: list of velocity values
    """
    U = ParsedParameterFile(path_to_U).content
    U_field = U['internalField'].val
    print("U count:",len(U_field))
    return U_field

if __name__ == '__main__':
    filePath = '../run/motorBike/10/U'
    U = read_U(filePath)
    # plot the velocity values in a line chart
    import matplotlib.pyplot as plt
    plt.plot(U)
    plt.show()