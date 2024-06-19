import os
import pickle
import time

from scipy.spatial import KDTree


class FoamKDTreeReader:
    """
    Read and write OpenFOAM data files using KDTree data structure.
    """

    class CoordinateLookup:
        def __init__(self, df):
            self.df = df
            self.tree = KDTree(df[['x', 'y', 'z']].values)

        def get_value(self, point):
            distance, index = self.tree.query(point)
            return [self.df.iloc[index]['u'], self.df.iloc[index]['v'], self.df.iloc[index]['w']]


    def __init__(self, openfoam_root):
        self.openfoam_root = openfoam_root
        self.df = None
        self.lookup = None
        self.index = None
        self.file_list = []

    def read_from_file(self, filename):
        """
        Read preprocessing data from pickle file
        :param filename:
        :return:
        """
        full_filename = os.path.join(self.openfoam_root, filename)
        with open(full_filename, 'rb') as f:
            self.lookup = pickle.load(f)


    def get_spacial_temporal_velocity_next_time_step(self, point):
        """
        Get the velocity at the next time step using KDTree
        :param point: drone position in openFoam coordinates. Do not have to be integers.
        :return: velocity at the next time step [u, v, w]
                """
        start_time = time.time()
        if not self.file_list:
            # first time being called, populate the time list
            # pattern match all files in self.openfoam_root with "wisp{time}.pkl" and add the filename to self.time_list
            for file in os.listdir(self.openfoam_root):
                if file.endswith(".pkl"):
                    self.file_list.append(file)

        self.load_next_df()
        result = self.lookup.get_value(point)
        print(f"Time taken: {time.time() - start_time}")
        return result

    def clear_time_list(self):
        self.file_list = []
        self.index = None

    def load_next_df(self):
        """
        Load the next dataframe in the sequence and update the KDTree
        """
        next_filename = self.__get_next_filename()
        if next_filename is not None:
            self.read_from_file(next_filename)

    def __get_next_filename(self):
        """
        Generate the filename for the next time step based on the current filename
        """
        if self.index is None:
            self.index = 0
            return self.file_list[0]
        else:
            self.index += 1
            if self.index < len(self.file_list):
                return self.file_list[self.index]
            else:
                return None



    @staticmethod
    def preprocess_and_save_df(df, save_filename):
        """
        preprocess data and save a single frame to a pickle file
        :param df: pandas dataframe [x, y, z, u, v, w]
        :param save_filename: path to save the pickle file
        :return:
        """
        # Build KDTree
        start_time = time.time()
        lookup = FoamKDTreeReader.CoordinateLookup(df)

        # Save to pickle file
        with open(save_filename, 'wb') as f:
            pickle.dump(lookup, f)

        print(f"KD-tree {save_filename} build, size {len(df)}, time taken to preprocess and save: {time.time() - start_time}")

if __name__ == "__main__":
    # Example usage
    reader = FoamKDTreeReader("openFoamCase")
    print(reader.get_spacial_temporal_velocity_next_time_step([1.0, 2.0, 3.0]))