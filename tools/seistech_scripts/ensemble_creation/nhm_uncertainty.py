"""
Generates nhm file permutations based on the uncertainty in the input NHM file

"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from qcore import nhm


def main(plots=False):
    n_rels, nhm_ffp, out_dir = parse_args()

    nhm_obj_dict = nhm.load_nhm(nhm_ffp)

    results = {}
    for i in range(n_rels):
        pert_results = {}

        with open(out_dir / f"{nhm_ffp.stem}_pert{i:0>2d}.txt", "w") as out_fp:

            header = True
            for fault, fault_data in nhm_obj_dict.items():

                ###
                # Easy way to disable perturbations - only used for verification / testing
                ###
                # fault_data.dtop_min = fault_data.dtop_max = fault_data.dtop
                # fault_data.dbottom_sigma = 0
                # fault_data.length_sigma = 0
                # fault_data.slip_rate_sigma = 0
                # fault_data.coupling_coeff_sigma = 0
                # fault_data.dip_sigma = 0

                pert = fault_data.sample_2012(
                    mw_area_scaling=True, mw_perturbation=True
                )

                pert_results[(fault, i)] = {
                    "mw": pert.mw,
                    "recurrance_interval": pert.recur_int_median,
                    "nhm_reccurance_interval": fault_data.recur_int_median,
                    "tecttype": pert.tectonic_type,
                    "pert_no": i,
                }

                pert.write(out_fp, header)
                header = False

            results.update(pert_results)

    if plots:
        plot_nhm_distribution(n_rels, nhm_obj_dict, results)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("nhm-ffp", type=Path)
    parser.add_argument(
        "out-dir", help="Output directory for the new NHM files", type=Path
    )
    parser.add_argument(
        "n-rels", help="Number of realisations to generate", default=20, nargs="?"
    )
    args = parser.parse_args()
    nhm_ffp = getattr(args, "nhm-ffp")
    out_dir = getattr(args, "out-dir")
    n_rels = getattr(args, "n-rels")
    return n_rels, nhm_ffp, out_dir


def plot_nhm_distribution(n_rels, nhm_obj_dict, results):
    mw_recur = pd.DataFrame.from_dict(results, orient="index")
    mw_recur["exceedance"] = 1 / mw_recur.recurrance_interval
    nhm_mw_recur_dict = {
        fault: {
            "mw": fault_data.mw,
            "recurrance_interval": fault_data.recur_int_median,
        }
        for fault, fault_data in nhm_obj_dict.items()
    }
    nhm_mw_recur = pd.DataFrame.from_dict(nhm_mw_recur_dict, orient="index")
    nhm_mw_recur["exceedance"] = 1 / nhm_mw_recur.recurrance_interval

    ###
    # Plotting Figure 4 from Bradley 2012 - Epistemic Uncertainties NZ PSHA
    # Cumulatively sum/select the exceedances by magnitude - used for both this plot and the second one below
    ###
    mags = np.linspace(5, 9.0)
    axes = plt.axes()
    all_exceedances = np.ones([n_rels, len(mags)])
    for i in range(n_rels):
        exceedances = np.array(
            [
                mw_recur[
                    np.logical_and(mw_recur.mw > mag, mw_recur.pert_no == i)
                ].exceedance.sum()
                for mag in mags
            ]
        )
        all_exceedances[i, :] = exceedances
        exceedances_mask = exceedances > 0
        axes.plot(mags[exceedances_mask], exceedances[exceedances_mask], color="grey")
    exceedances = np.array(
        [mw_recur[mw_recur.mw > mag].exceedance.sum() / n_rels for mag in mags]
    )
    exceedances_mask = exceedances > 0
    axes.plot(
        mags[exceedances_mask],
        exceedances[exceedances_mask],
        color="red",
        linewidth="2",
        label="Mean",
    )
    exceedances = np.array(
        [nhm_mw_recur[nhm_mw_recur.mw > mag].exceedance.sum() for mag in mags]
    )
    exceedances_mask = exceedances > 0
    axes.plot(
        mags[exceedances_mask],
        exceedances[exceedances_mask],
        color="black",
        linewidth="2",
        label="NHM",
    )
    axes.set_yscale("log")
    axes.set_xlabel("Perturbated Magnitude")
    axes.set_ylabel(r"Annual exceedance frequency, $\lambda M_w$")
    axes.grid()
    axes.legend()

    ###
    # Plot of Figure 5.
    ###
    fig, axes = plt.subplots()
    axes.plot(mags, np.std(np.log(all_exceedances), axis=0))
    axes.set_xlabel("Perturbated Magnitude")
    axes.set_ylabel(r"Sigma, $\sigma ln\lambda$")
    axes.grid()

    ###
    # Plot to show the 1to1 of NHM Recurrance vs perturbated Recurrance
    ###
    fig, axes = plt.subplots()
    axes.scatter(mw_recur.recurrance_interval, mw_recur.nhm_reccurance_interval)
    axes.set_xlabel("Calculated Recurrance")
    axes.set_ylabel("NHM Recurrance")
    plt.show()


if __name__ == "__main__":
    main()
