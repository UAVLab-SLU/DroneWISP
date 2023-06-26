import random
import time
import pandas as pd


def read_csv(filename):
    # read csv
    start = time.time()
    df = pd.read_csv(filename)
    print("read csv time: " + str(time.time() - start))

    # preprocess
    start = time.time()
    # make columns 1, 2, 3 integers
    df = df.astype({df.columns[0]: int, df.columns[1]: int, df.columns[2]: int})

    # remove all rows with duplicate values in columns 1, 2, 3
    df = df.drop_duplicates(subset=[df.columns[0], df.columns[1], df.columns[2]], keep='first')

    # sort by columns 1, 2, 3
    df = df.sort_values(by=[df.columns[0], df.columns[1], df.columns[2]])

    print("preprocess time: " + str(time.time() - start))

    # save new csv
    # df.to_csv(filename+"_mod.csv", index=False)

    # columns 1 is x, 2 is y, 3 is z

    # integrity test
    # unique x values
    u_x = df[df.columns[0]].unique()
    print("unique x: " + str(len(u_x)))
    u_y = df[df.columns[1]].unique()
    print("unique y: " + str(len(u_y)))
    u_z = df[df.columns[2]].unique()
    print("unique z: " + str(len(u_z)))


    # access time test
    x = random.randint(-160, 160)
    y = random.randint(-160, 160)
    z = random.randint(0, 50)

    start = time.time()
    t = df.loc[(df[df.columns[0]] == x) & (df[df.columns[1]] == y) & (df[df.columns[2]] == z)]
    print("access", x, y, z)
    print(t)
    print("column search time: " + str(time.time() - start))



read_csv("../run/blockEnv/test5.csv")
