import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from scipy._lib.decorator import decorator as _decorator
import numpy as np
import warnings
warnings.filterwarnings("ignore")


def df2ref_init(df: pd.DataFrame):
    df_ref_init = df.copy()
    for i in range(1, len(df_ref_init)):
        df_ref_init.at[i, "longitude"] += df_ref_init.at[i - 1, "longitude"]
        df_ref_init.at[i, "latitude"] += df_ref_init.at[i - 1, "latitude"]
        df_ref_init.at[i, "altitude"] += df_ref_init.at[i - 1, "altitude"]
        if i == 1:
            df_ref_init.loc[i, "seconds"] = int(
                df_ref_init.at[i, "timestamp"].timestamp() - df.at[i - 1, "timestamp"].timestamp())
        else:
            df_ref_init.loc[i, "seconds"] = int(
                df_ref_init.at[i, "timestamp"].timestamp() - \
                df.at[i - 1, "timestamp"].timestamp()) + df_ref_init.at[i - 1, "seconds"]
    return df_ref_init


def df2ref_last(df: pd.DataFrame):
    df4machine = df.copy()
    for i in range(1, len(df4machine)):
        if i == 1:
            df4machine.loc[i, "seconds"] = int(
                df4machine.at[i, "timestamp"].timestamp() - df.at[i - 1, "timestamp"].timestamp()
            )
        else:
            df4machine.loc[i, "seconds"] = int(
                df4machine.at[i, "timestamp"].timestamp() -
                df.at[i - 1, "timestamp"].timestamp()
            ) + df4machine.at[i - 1, "seconds"]
    return df4machine


def print_2d(df: pd.DataFrame, x:str, y:str, c:str=None, titles:dict={"lines": "", "dots": ""}):
    df.plot(x=x, y=y, title=titles["lines"])
    plt.show()

    if c is not None:
        c = cm.rainbow(np.array(df[c]) / np.mean(df[c]))
    df.plot.scatter(x=x, y=y, s=5, c=c, title=titles["dots"])
    plt.show()


def print_clusters_tagged_2d(df: pd.DataFrame, title:str=""):
    xs, ys = [], []
    last_cluster = None
    latitude, longitude = 0, 0
    for idx, row in df.iterrows():
        latitude += df.at[idx, "latitude"]
        longitude += df.at[idx, "longitude"]
        cluster = df.at[idx, "cluster"]
        if cluster != last_cluster and cluster != -1:
            last_cluster = cluster
            xs.append(df.at[idx, "lng_cluster"])
            ys.append(df.at[idx, "lat_cluster"])
        elif cluster == -1:
            xs.append(longitude)
            ys.append(latitude)

    plt.plot(xs, ys)
    plt.title(title)
    plt.show()


def print_3d(df: pd.DataFrame, x:str, y:str, z:str, c:str=None, titles:dict={"lines": "", "dots": ""}):
    p3d = plt.figure().gca(projection='3d')
    p3d.plot(xs=df[x].values, ys=df[y].values, zs=df[z].values)
    p3d.set_xlabel(x)
    p3d.set_ylabel(y)
    p3d.set_zlabel(z)
    p3d.set_title(titles["lines"])
    plt.show()

    if c is not None:
        c = cm.rainbow(np.array(df[c]) / np.mean(df[c]))
    p3d = plt.figure().gca(projection='3d')
    p3d.scatter(xs=df[x].values, ys=df[y].values, zs=df[z].values, s=5, c=c)
    p3d.set_xlabel(x)
    p3d.set_ylabel(y)
    p3d.set_zlabel(z)
    p3d.set_title(titles["dots"])
    plt.show()


@_decorator
def _held_figure(func, obj, ax=None, **kw):
    import matplotlib.pyplot as plt

    if ax is None:
        fig = plt.figure()
        ax = fig.gca()
        return func(obj, ax=ax, **kw)
    # As of matplotlib 2.0, the "hold" mechanism is deprecated.
    # When matplotlib 1.x is no longer supported, this check can be removed.
    was_held = getattr(ax, 'ishold', lambda: True)()
    if was_held:
        return func(obj, ax=ax, **kw)
    try:
        ax.hold(True)
        return func(obj, ax=ax, **kw)
    finally:
        ax.hold(was_held)


def _bounds(points):
    margin = 0.1 * points.ptp(axis=0)
    xy_min = points.min(axis=0) - margin
    xy_max = points.max(axis=0) + margin
    return [xy_min[0], xy_max[0], xy_min[1], xy_max[1]]


@_held_figure
def voronoy_plot_2d(vor, ax=None, **kw):
    from matplotlib.collections import LineCollection

    if vor.points.shape[1] != 2:
        raise ValueError("Voronoi diagram is not 2-D")

    if kw.get('show_points', True):
        point_size = kw.get('point_size', None)
        point_colors = kw.get('point_colors', "dodgerblue")
        ax.plot(vor.points[:, 0], vor.points[:, 1], '.', color=point_colors, markersize=point_size)
    if kw.get('show_vertices', True):
        vertices_colors = kw.get('vertices_colors', "orange")
        ax.plot(vor.vertices[:, 0], vor.vertices[:, 1], 'o', color=vertices_colors)

    line_colors = kw.get('line_colors', 'k')
    line_width = kw.get('line_width', 1.0)
    line_alpha = kw.get('line_alpha', 1.0)

    center = vor.points.mean(axis=0)
    ptp_bound = vor.points.ptp(axis=0)

    finite_segments = []
    infinite_segments = []
    for pointidx, simplex in zip(vor.ridge_points, vor.ridge_vertices):
        simplex = np.asarray(simplex)
        if np.all(simplex >= 0):
            finite_segments.append(vor.vertices[simplex])
        else:
            i = simplex[simplex >= 0][0]  # finite end Voronoi vertex

            t = vor.points[pointidx[1]] - vor.points[pointidx[0]]  # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = vor.points[pointidx].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            if (vor.furthest_site):
                direction = -direction
            far_point = vor.vertices[i] + direction * ptp_bound.max()

            infinite_segments.append([vor.vertices[i], far_point])

    if kw.get("show_segments", True):
        ax.add_collection(LineCollection(finite_segments,
                                         colors=line_colors,
                                         lw=line_width,
                                         alpha=line_alpha,
                                         linestyle='solid'))
        ax.add_collection(LineCollection(infinite_segments,
                                         colors=line_colors,
                                         lw=line_width,
                                         alpha=line_alpha,
                                         linestyle='dashed'))

    # Adjust bounds
    _xy_lims = kw.get("adjust_to", _bounds(vor.points))
    ax.set_xlim(_xy_lims[0], _xy_lims[1])
    ax.set_ylim(_xy_lims[2], _xy_lims[3])

    return ax.figure, _xy_lims


def print_regions(regions, vor, _xy_lims=None):
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    for points_draw in regions:
        np_points = np.array(vor.points)
        ax.scatter(np_points[:, 0], np_points[:, 1], s=2)

        ax.plot(*points_draw.exterior.xy)
        ax.scatter(*points_draw.exterior.xy, s=10)
        if _xy_lims is not None:
            ax.set_xlim(_xy_lims[0], _xy_lims[1])
            ax.set_ylim(_xy_lims[2], _xy_lims[3])
    plt.show()

if __name__ == '__main__':
    path = "../../data/tracks/ejemplo1"
    df = pd.read_parquet(path)
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    df_ref_init = df2ref_init(df)
    df_ref_last = df2ref_last(df)

    # print with altitude
    print_2d(df_ref_init, x="longitude", y="latitude", titles={"lines": "reference init", "dots": "reference init"})
    print_3d(df_ref_init, x="longitude", y="latitude", z="altitude", titles={"lines": "reference init", "dots": "reference init"})
    # print with seconds
    print_3d(df_ref_init, x="longitude", y="latitude", z="seconds", titles={"lines": "reference init", "dots": "reference init"})

    # print altitude and ref_last
    # print with altitude
    print_2d(df_ref_last, x="longitude", y="latitude", titles={"lines": "relative to last point",
                                                           "dots": "relative to last point"})
    print_3d(df_ref_last, x="longitude", y="latitude", z="altitude", titles={"lines": "relative to last point",
                                                                       "dots": "relative to last point"})
    # print with seconds
    print_3d(df_ref_last, x="longitude", y="latitude", z="seconds", titles={"lines": "relative to last point",
                                                                        "dots": "relative to last point"})
