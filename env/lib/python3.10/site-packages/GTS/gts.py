from scipy.spatial import Voronoi
import pandas as pd
import numpy as np
from glob import glob
from pathlib import Path

import alphashape
from shapely.geometry import Point
from geopy.distance import geodesic

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from inspect import currentframe
from dateutil.parser import parse

from GTS.tools import df2ref_init

import warnings
warnings.filterwarnings("ignore")


class GTS:
    def __init__(self) -> None:
        self.df: pd.DataFrame = None
        self.win_size: int = None
        self.threshold: float = None
        self.min_cluster_radio: float = None
        self.vor: Voronoi = None
        self.dfx_batch: pd.DataFrame = None
        self.verbose: int = 0

    def get_area(self, x, y) -> float:
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    def location_in(self, longitude: float, latitude: float, regions: list) -> int:
        point = Point(longitude, latitude)
        for i, reg in enumerate(regions):
            if point.within(reg):
                return i
        return None

    def cluster2row(self, cluster: pd.DataFrame) -> pd.DataFrame:
        new_row = cluster.loc[len(cluster) - 1].copy()
        mean_long = cluster["longitude"].mean()
        new_row["longitude"] = mean_long
        mean_lat = cluster["latitude"].mean()
        new_row["latitude"] = mean_lat
        if type(cluster.loc[len(cluster) - 1, ["timestamp"]].values[0]) in [int, float]:
            new_row["cluster_time"] = cluster.loc[len(cluster) - 1, ["timestamp"]].values[0] - \
                                      cluster.loc[0, ["timestamp"]].values[0]
        elif type(cluster.loc[len(cluster) - 1, ["timestamp"]].values[0]) == pd.Timestamp:
            new_row["cluster_time"] = (cluster.loc[len(cluster) - 1, ["timestamp"]].values[0] -
                                       cluster.loc[0, ["timestamp"]].values[0]).seconds
        else:
            new_row["cluster_time"] = parse(cluster.loc[len(cluster) - 1, ["timestamp"]].values[0]) - \
                                      parse(cluster.loc[0, ["timestamp"]].values[0])
        return new_row

    def last_row_behaviour(
        self,
        idx: int,
        cluster: pd.DataFrame,
        dfx: pd.DataFrame,
        df_batch: pd.DataFrame,
        row: pd.Series,
        reg_2: int,
        reg_3: int,
        rows_added: list) -> tuple:

        dist = geodesic(tuple([cluster.loc[0, ["latitude"]].values, cluster.loc[0, ["longitude"]].values]),
                        tuple([row["latitude"], row["longitude"]])).m

        # Conditions
        is_near: bool = dist < self.min_cluster_radio
        is_reg23_equals: bool = reg_2 == reg_3
        is_reg3_none: bool = reg_3 is None

        # keep and save
        if is_near or (is_reg23_equals and not is_reg3_none):
            cluster.loc[len(cluster)] = df_batch.iloc[idx]  # save 3 in cluster
            # save cluster
            dfx.loc[len(dfx)] = self.cluster2row(cluster)
            if self.verbose == 2:
                rows_added.append(idx)
                print(f"{currentframe().f_back.f_lineno}: cluster:add {idx} of region {reg_3}")
                print(f"- {currentframe().f_back.f_lineno} dfx {len(dfx)} :add cluster of region {reg_2}")
        # new and save
        elif is_reg3_none or not is_reg23_equals:
            # save cluster
            dfx.loc[len(dfx)] = self.cluster2row(cluster)
            # create new cluster
            cluster = pd.DataFrame(columns=df_batch.columns)
            cluster.loc[len(cluster)] = df_batch.iloc[idx]  # save 3 in cluster
            # save last cluster
            dfx.loc[len(dfx)] = self.cluster2row(cluster)
            if self.verbose == 2:
                rows_added.append(idx)
                print(f"- {currentframe().f_back.f_lineno} dfx {len(dfx) - 1} :add cluster of region {reg_2}")
                print(f"{currentframe().f_back.f_lineno}: cluster:add {idx} of region {reg_3}")
                print(f"- {currentframe().f_back.f_lineno} dfx {len(dfx)} :add cluster of region {reg_3}")
        else:
            raise Exception()

        return dfx, rows_added

    def locations_clustering(self, df_batch, regions):
        dfx = pd.DataFrame(columns=list(df_batch.columns) + ["cluster_time"])
        reg_1 = None
        reg_2 = None
        reg_3 = None
        cluster = None
        rows_added = []

        for idx, row in df_batch.iterrows():
            if idx == 0:
                reg_1 = self.location_in(row["longitude"], row["latitude"], regions)
                cluster = pd.DataFrame(columns=df_batch.columns)
                cluster.loc[len(cluster)] = row.values
                # Last location actions
                if idx == len(df_batch) - 1:
                    dfx.loc[len(dfx)] = self.cluster2row(cluster)
                if self.verbose == 2:
                    rows_added.append(idx)
                    print(f"{currentframe().f_back.f_lineno}: cluster:add {idx}")
                    if idx == len(df_batch) - 1:
                        print(f"- {currentframe().f_back.f_lineno} dfx {len(dfx)} :add cluster of region {reg_1}")

            elif idx == 1:
                reg_2 = self.location_in(row["longitude"], row["latitude"], regions)
                if idx == len(df_batch) - 1:
                    dfx, rows_added = self.last_row_behaviour(
                        idx, cluster, dfx, df_batch, row, reg_1, reg_2, rows_added)
            elif idx >= 2:
                reg_3 = self.location_in(row["longitude"], row["latitude"], regions)
                assert len(cluster) > 0
                dist = geodesic(tuple([cluster.at[0, "latitude"],
                                       cluster.at[0, "longitude"]]),
                                tuple([df_batch.at[idx - 1, "latitude"],
                                       df_batch.at[idx - 1, "longitude"]])).m

                # Conditions
                is_reg1_none: bool = reg_1 is None
                is_reg3_none: bool = reg_3 is None
                is_near: bool = dist < self.min_cluster_radio
                is_reg12_equals: bool = reg_1 == reg_2
                is_reg13_equals: bool = reg_1 == reg_3

                # keep
                if (is_reg1_none and is_near) or (not is_reg1_none and is_reg12_equals):
                    cluster.loc[len(cluster)] = df_batch.iloc[idx - 1]  # save 2 in cluster
                    if self.verbose == 2:
                        rows_added.append(idx - 1)
                        print(f"{currentframe().f_back.f_lineno}: cluster:add {idx - 1} of region {reg_2}")
                # new cluster
                elif is_reg1_none or (
                        not is_reg13_equals and not is_reg12_equals and (is_reg3_none or not is_reg1_none)):
                    # save cluster
                    dfx.loc[len(dfx)] = self.cluster2row(cluster)
                    # create new cluster
                    cluster = pd.DataFrame(columns=df_batch.columns)
                    cluster.loc[len(cluster)] = df_batch.iloc[idx - 1]  # save 2 in cluster
                    if self.verbose == 2:
                        rows_added.append(idx - 1)
                        print(f"- {currentframe().f_back.f_lineno} dfx {len(dfx)} :add cluster of region {reg_1}")
                        print(f"{currentframe().f_back.f_lineno}: cluster:add {idx - 1} of region {reg_2}")
                # skip location
                elif not is_reg12_equals and not is_reg1_none and is_reg13_equals:
                    if self.verbose == 2:
                        print(f"{currentframe().f_back.f_lineno}: cluster: skip {idx - 1} of region {reg_2}")
                    reg_2 = reg_3

                # update reg 1 and 2 with the next, except last
                if idx != len(df_batch) - 1:
                    reg_1 = reg_2
                    reg_2 = reg_3

            # Last location actions
            if idx == len(df_batch) - 1:
                dfx, rows_added = self.last_row_behaviour(
                    idx=idx,
                    cluster=cluster,
                    dfx=dfx,
                    df_batch=df_batch,
                    row=row,
                    reg_2=reg_2,
                    reg_3=reg_3,
                    rows_added=rows_added
                )
        return dfx

    def get_regions(self) -> list:
        relation_ver2cell: dict = {}
        relation_cell2region: dict = {}
        reg: list = []

        for id_pnt, id_cell in enumerate(self.vor.point_region):
            cell: list = self.vor.regions[id_cell].copy()
            if len(cell) > 0 and -1 not in cell:
                np_cell: np.ndarray = np.array([self.vor.vertices[id_ver] for id_ver in cell])
                area: float = self.get_area(np_cell[:, 0], np_cell[:, 1])
                if area < self.threshold:
                    current_relations: list = []  # relations with another regions
                    # relations
                    for ver in cell:
                        if ver in relation_ver2cell:
                            current_relations += relation_ver2cell[ver]
                            relation_ver2cell[ver].append(id_cell)
                        elif ver not in relation_ver2cell:
                            relation_ver2cell[ver] = [id_cell]

                    # merge
                    current_relations: set = set(current_relations)
                    reg_used: list = []
                    for key_id_cell in current_relations:
                        if relation_cell2region[key_id_cell] not in reg_used:
                            if len(reg_used) == 0:
                                reg[relation_cell2region[key_id_cell]] += cell
                                reg_used.append(relation_cell2region[key_id_cell])
                                relation_cell2region[id_cell] = relation_cell2region[key_id_cell]
                            else:
                                reg[reg_used[0]] += reg[relation_cell2region[key_id_cell]]
                                reg[relation_cell2region[key_id_cell]] = []
                                new_value_for_region = relation_cell2region[key_id_cell]
                                for key in relation_cell2region:
                                    if relation_cell2region[key] == new_value_for_region:
                                        relation_cell2region[key] = reg_used[0]

                    if len(current_relations) == 0:
                        relation_cell2region[id_cell] = len(reg)
                        reg.append(cell)
        regions: list = []
        for n_r in reg:
            if n_r:
                points_draw: list = [self.vor.vertices[id_ver] for id_ver in n_r]
                alpha_shape = alphashape.alphashape(points_draw, alpha=0)
                regions.append(alpha_shape)
        if self.verbose == 2:
            print("new_regions", len(regions))
        return regions

    def get_groups(self, i: int, j: int) -> pd.DataFrame:
        regions: list = self.get_regions()

        # group and discard locations
        df_batch: pd.DataFrame = self.df[i:j].copy().reset_index(drop=False)
        dfx: pd.DataFrame = self.locations_clustering(df_batch, regions)
        if self.verbose == 2:
            print(f"dfx {len(dfx)}, df_batch {len(df_batch)}")
        return dfx

    def locations_inside_windows(self, i: int) -> pd.DataFrame:
        # get regions
        if self.verbose == 2:
            print(f"\n{i - self.win_size}-{i}")
        self.vor: object = Voronoi(self.df.loc[:, ['longitude', 'latitude']].iloc[:, :].to_numpy()[i - self.win_size:i])
        return self.get_groups(i=i-self.win_size, j=i)

    def last_locations(self, i: int) -> pd.DataFrame:
        if len(self.df) - i < 4:
            i_vor: int = len(self.df) - 4 if len(self.df) - self.win_size < 0 else len(self.df) - self.win_size
        else:
            i_vor: int = i
        if self.verbose == 2:
            print(f"\n{i}-{len(self.df)}")
        self.vor = Voronoi(self.df.loc[:, ['longitude', 'latitude']].iloc[:, :].to_numpy()[i_vor:len(self.df)])
        return self.get_groups(i=i, j=len(self.df))

    def print_graph(self) -> None:
        self.dfx_batch.plot(x="longitude", y="latitude")
        plt.show()
        self.df.plot(x="longitude", y="latitude")
        plt.show()

    def save_data(self, path: str) -> None:
        self.dfx_batch.to_parquet(path)

    def dir_of_files(
        self,
        dir_path: str,
        save_path: str,
        win_size: int = 50,
        threshold: float = 5e-7,
        min_cluster_radio: int = 10,
        verbose: int = 0
    ) -> None:
        for path in glob(dir_path+"*", recursive=False):
            self.run(
                path=path,
                win_size=win_size,
                threshold=threshold,
                min_cluster_radio=min_cluster_radio,
                verbose=verbose
            )
            self.save_data(save_path.format(Path(path).name))

    def run(
        self,
        path: str,
        win_size: int,
        threshold: float,
        min_cluster_radio: float,
        verbose: int
    ) -> pd.DataFrame:
        self.verbose = verbose
        self.win_size = win_size
        self.threshold = threshold
        self.min_cluster_radio = min_cluster_radio


        # Preprocess data
        self.df = pd.read_parquet(path)
        self.df = self.df.sort_values(by=['timestamp'])
        self.df = df2ref_init(self.df)
        self.df = self.df.reset_index(drop=True).loc[:, ["latitude", "longitude", "altitude", "timestamp", "seconds"]]
        self.dfx_batch = pd.DataFrame(columns=self.df.columns)
        # Locations inside processing windows
        i: int = 0
        for i in range(0 + self.win_size, len(self.df), self.win_size):
            dfx: pd.DataFrame = self.locations_inside_windows(i)
            self.dfx_batch = pd.concat([self.dfx_batch, dfx], ignore_index=True)
        # Last locations to process
        if i < len(self.df):
            dfx: pd.DataFrame = self.last_locations(i)
            self.dfx_batch = pd.concat([self.dfx_batch, dfx], ignore_index=True)

        if verbose == 1:
            print(f"dfx_batch {len(self.dfx_batch)}, df {len(self.df)}")

        if verbose == 3:
            self.print_graph()

        return self.dfx_batch

if __name__ == '__main__':
    gts: GTS = GTS()

    # All files in folder
    gts.dir_of_files(
        dir_path="../data/tracks/",
        save_path="../data/tracks_gts/{}_result",
        win_size=50,
        threshold=5e-7,
        min_cluster_radio=10,
        verbose=1
    )

    # One file
    gts.run(
        path="../data/tracks/ejemplo1",
        win_size=50,
        threshold=5e-7,
        min_cluster_radio=10,
        verbose=1
    )
