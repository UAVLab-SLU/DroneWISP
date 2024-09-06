import pandas as pd

def approximate_integer(x):
    """
    Approximate a floating point number to the closest integer
    :param x: floating point number
    :return: the closest integer
    """
    if x - int(x) < 0.5:
        return int(x)
    else:
        return int(x) + 1


file_path = 'turb.csv'
result_path = 'turb_preprocessed.csv'

# Load the data
data = pd.read_csv(file_path)
df = pd.DataFrame(data)

# remove all rows with 0 in columns 4, 5, 6. those are points inside the mesh
df = df[(df[df.columns[3]] != 0) & (df[df.columns[4]] != 0) & (df[df.columns[5]] != 0)]

# cast columns 1, 2, 3 to nearest integer using manhattan distance
df.loc[:, df.columns[0]] = df[df.columns[0]].apply(approximate_integer)
df.loc[:, df.columns[1]] = df[df.columns[1]].apply(approximate_integer)
df.loc[:, df.columns[2]] = df[df.columns[2]].apply(approximate_integer)

# remove all rows with duplicate values in columns 1, 2, 3
df = df.drop_duplicates(subset=[df.columns[0], df.columns[1], df.columns[2]], keep='first')

# sort by columns 1, 2, 3
df = df.sort_values(by=[df.columns[0], df.columns[1], df.columns[2]])

# save the data
df.to_csv(result_path, index=False)




