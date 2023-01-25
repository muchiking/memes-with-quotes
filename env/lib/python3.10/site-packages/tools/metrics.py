import pandas as pd
from glob import glob
import math
from pprint import pprint
import matplotlib.pyplot as plt
from pathlib import Path


class Metrics:
    def __init__(
        self,
    ) -> None:
        self.metrics: dict = {}

    def reset_metrics(self) -> None:
        self.metrics: dict = {}

    def dir_of_files(
        self,
        dir_path: str,
        results_path: str,
        verbose: int = 0
    ) -> None:
        self.metrics: dict = {}
        for path in glob(dir_path+"*", recursive=False):
            self.run(
                labeled_file=path,
                result_file=results_path.format(Path(path).name),
                verbose=verbose
            )

        resume = pd.DataFrame.from_dict(self.metrics, orient="index")
        tp_sum = resume["TP"].sum()
        tn_sum = resume["TN"].sum()
        fp_sum = resume["FP"].sum()
        fn_sum = resume["FN"].sum()
        self.metrics["resume"] = {
            "TP": tp_sum,
            "TN": tn_sum,
            "FP": fp_sum,
            "FN": fn_sum,
            "RF": resume["RF"].mean(),
            "RFE": resume["RFE"].mean(),
            "SDE": resume["SDE"].mean(),
            "MDE": resume["SDE"].sum() / resume["len"].sum(),
            "FNFP_MDE": resume["FNFP_MDE"].mean(),
            "F1": 2 * tp_sum / (2 * tp_sum + fn_sum + fp_sum),
            "MCC": (tp_sum * tn_sum - fp_sum * fn_sum) / (
                (tp_sum + fp_sum) * (tp_sum + fn_sum) * (tn_sum + fp_sum) * (tn_sum + fn_sum)
            ) ** 0.5
        }
        print(f"MCC/F1/FNFP_MDE/RFE/TN/TP/FN/FP/RF/SDE/MDE\n"
              f"{self.metrics['resume']['MCC']}\n"
              f"{self.metrics['resume']['F1']}\n"
              f"{self.metrics['resume']['FNFP_MDE']}\n"
              f"{self.metrics['resume']['RFE']}\n"
              f"{self.metrics['resume']['TN']}\n"
              f"{self.metrics['resume']['TP']}\n"
              f"{self.metrics['resume']['FN']}\n"
              f"{self.metrics['resume']['FP']}\n"
              f"{self.metrics['resume']['RF']}\n"
              f"{self.metrics['resume']['SDE']}\n"
              f"{self.metrics['resume']['MDE']}")

    def run(
        self,
        labeled_file: str,
        result_file: str,
        verbose: int = 0
    ):
        path: Path = Path(labeled_file)
        df: pd.DataFrame = pd.read_parquet(path)
        dfr: pd.DataFrame = pd.read_parquet(result_file)

        tp, tn, fp, fn = 0, 0, 0, 0
        for idx, row in df.iterrows():
            clustered: bool = df.at[idx, "cluster"] != -1
            in_cluster: bool = (idx not in dfr["index"].values or
                                dfr[dfr["index"] == idx]["cluster_time"].values[0] > 0
                                )
            if clustered and in_cluster:
                tp += 1
            elif not clustered and not in_cluster:
                tn += 1
            elif clustered and not in_cluster:
                fn += 1
            elif not clustered and in_cluster:
                fp += 1

        rf = 1 - len(dfr) / len(df)
        rfe = rf - get_rf(df)
        sde_dict: dict = get_sde(df, dfr)
        sde = sum(list(sde_dict.values()))
        mde = None if len(sde_dict) == 0 else sde / len(sde_dict)
        fnfp_mde = None if mde is None else (fp + fn) * 1e-4 + mde
        f1 = 2 * tp / (2 * tp + fn + fp)
        mcc = (tp * tn - fp * fn) / ((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) ** 0.5

        self.metrics[path.name] = {
            "TP": tp, "TN": tn, "FP": fp, "FN": fn,"RF": rf, "RFE": rfe, "sde_dict": sde_dict,
            "SDE": sde, "MDE": mde, "FNFP_MDE": fnfp_mde, "len": len(sde_dict), "F1": f1, "MCC": mcc}

        if verbose == 2:
            dfr.plot(x="longitude", y="latitude", title=f"Algorithm {path.parent} result")
            plt.show()

        if verbose in {1, 2}:
            pprint(self.metrics[path.name])


def get_rf(df: pd.DataFrame) -> float:
    _last, _num_rows = None, 0
    for idx, row in df.iterrows():
        if _last != df.at[idx, "cluster"] or _last == -1:
            _last = df.at[idx, "cluster"]
            _num_rows += 1
    return 1 - _num_rows / len(df)


def get_sde(df: pd.DataFrame, dfr: pd.DataFrame) -> dict:
    e_sum = {}
    for idx, row in dfr.iterrows():
        clusters: set = set()
        start_i: int = 0 if idx == 0 else dfr.at[idx - 1, "index"] + 1
        for i in range(start_i, dfr.at[idx, "index"]):
            cls = df.at[i, "cluster"]
            if cls not in clusters and cls != -1:
                clusters.add(cls)
                p1 = (dfr.at[idx, "latitude"], dfr.at[idx, "longitude"])
                p2 = (df.at[i, "lat_cluster"], df.at[i, "lng_cluster"])
                e_sum[f"{idx}-{cls}"] = math.dist(p1, p2)
    return e_sum


if __name__ == '__main__':
    metrics: Metrics = Metrics()

    # All files
    metrics.dir_of_files(
        dir_path="../data/tracks/",
        results_path="../data/tracks_spectral/{}_result",
        verbose=1 # verbose could be 0, 1 or 2
    )

    # One file
    metrics.run(
        labeled_file="../data/tracks/ejemplo1",
        result_file="../data/tracks_gts/ejemplo1_result",
        verbose=1
    )




