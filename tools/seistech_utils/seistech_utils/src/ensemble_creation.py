import argparse
import itertools
import math
import os
from collections.abc import Iterable

import six
import yaml

DEFAULT_VERSION_NUMBER = "2"

DATASETS_ENSEMBLE_LABEL = "datasets"


def iterable_but_not_string(arg):
    """
    :param arg: object
    :return: Returns True if arg is an iterable that isn't a string
    """
    return isinstance(arg, Iterable) and not isinstance(arg, six.string_types)


def flatten(coll):
    """
    Returns a generator to transform a lists (of lists (of lists ...)) to a 1d form
    :param coll: list that contains other lists
    :return: list that has been flattened
    """
    for i in coll:
        if iterable_but_not_string(i):
            for subc in flatten(i):
                yield subc
        else:
            yield i


def is_any_strings_in_string(haystack, needles):
    """
    :param haystack: string to search
    :param needles: list of strings to check for in the haystack
    :return: Returns True if there is any needle in the haystack
    """
    return any([cur_needle in haystack for cur_needle in needles])


def find_matching_dbs(db_list, model, tect_type, match_string, pert_str=""):
    """
    :param db_list: List of databases
    :param model: Models to search for in the filenames
    :param tect_type: tect_type to search for in the filenames
    :param match_string: a substring that should be in the db filename - generally searching for 'ds' or 'flt'
    :return: Returns a list of db filenames that match the parameters set
    """
    tect_type = tect_type if iterable_but_not_string(tect_type) else [tect_type]
    return [
        db
        for db in db_list
        if is_any_strings_in_string(db, tect_type)
        and model in db
        and match_string in db
        and pert_str in db
    ]


def calculate_branch_weight(emp_weight_dict, db_match, im, n_perts=1):
    """
    :param emp_weight_dict: dictionary of branch weights
    :param db_match: list of tuples containing (tect_types and models) to determine what is the content of the branch
    :param im: im that is being calculated
    :return: Weighted score for the branch
    """
    weight = 1 / n_perts
    for tect_types, model in db_match:
        if iterable_but_not_string(tect_types):
            for tect_type in tect_types:
                weight *= emp_weight_dict[im][tect_type][model]
        else:
            weight *= emp_weight_dict[im][tect_types][model]
    return weight


def read_gmm_weights(emp_weight_conf_ffp):
    """
    Reads the weights into a "flat" dictionary
    :param emp_weight_conf_ffp: ffp to yaml configuration file
    :return: dictionary of im, tect-type, model weighting
    """
    emp_wc_dict_orig = yaml.load(open(emp_weight_conf_ffp), Loader=yaml.Loader)
    emp_wc_dict = {}

    for ims in emp_wc_dict_orig:
        im_list = ims if iterable_but_not_string(ims) else [ims]
        for im in im_list:
            emp_wc_dict[im] = {}
            for tect_type in emp_wc_dict_orig[ims]:
                tect_type_list = (
                    tect_type if iterable_but_not_string(tect_type) else [tect_type]
                )
                for tt in tect_type_list:
                    if tt not in emp_wc_dict:
                        emp_wc_dict[im][tt] = emp_wc_dict_orig[ims][tect_type]
    return emp_wc_dict


def create_ensemble(
    ens_name,
    output_dir,
    empirical_weight_config_ffp,
    ds_ssdb_ffp="",
    flt_ssdb_ffp="",
    stat_list_ffp="",
    stat_vs30_ffp="",
    flt_erf_ffps="",
    ds_erf_ffp="",
    db_list=None,
    version=DEFAULT_VERSION_NUMBER,
    n_perts=1,
):
    """
    Main function to write content of yaml file

    writes a file called $ens_name.yaml containing the configuration for the ensemble
    in the directory specified by output_dir
    :return: None
    """
    emp_weight_dict = read_gmm_weights(empirical_weight_config_ffp)

    ens_dict = {
        "name": ens_name,
        "stations": stat_list_ffp,
        "vs30": stat_vs30_ffp,
        "ds_ssdb": ds_ssdb_ffp,
        "flt_ssdb": flt_ssdb_ffp,
        "version": version,
        DATASETS_ENSEMBLE_LABEL: {},
    }

    for im in emp_weight_dict:
        tect_types, branches = get_branches(emp_weight_dict, im, n_perts)
        pert_n_list = sorted(list(range(n_perts)) * (len(branches) // n_perts))
        im_dict = {}

        br_sig_figs = math.ceil(math.log10(len(branches)))
        for (i, branch), pert_n in zip(enumerate(branches), pert_n_list):
            branch_dict = {
                "flt_erf": flt_erf_ffps[pert_n] if n_perts > 1 else flt_erf_ffps[0],
                "flt_erf_type": "flt_nhm",
                "ds_erf": ds_erf_ffp,
                "ds_erf_type": "custom_ds_erf",
            }
            leaves = {}

            db_match = list(zip(tect_types, branch))

            pert_str = f"pert_{pert_n:02}"
            for j, (tect_type, model) in enumerate(db_match):
                ds_dbs = find_matching_dbs(db_list, model, tect_type, "ds")
                flt_dbs = find_matching_dbs(db_list, model, tect_type, "flt", pert_str)
                if len(flt_dbs) == 0:
                    flt_dbs = find_matching_dbs(db_list, model, tect_type, "flt")

                # Checks that there is no more than one matching DB for fault / ds for the given tect-type / model
                # And that there is at least one between fault / ds
                assert (
                    0 <= len(ds_dbs) <= 1
                    and 0 <= len(flt_dbs) <= 1
                    and len(ds_dbs) + len(flt_dbs) >= 1
                ), f"{ds_dbs}, {flt_dbs}, {tect_type}, {model}"

                leaves[f"leaf{j}"] = {
                    "model": model,
                    "tect-type": tect_type,
                    "ds_imdbs": ds_dbs,
                    "flt_imdbs": flt_dbs,
                }

            branch_dict["leaves"] = leaves
            branch_dict["weight"] = calculate_branch_weight(
                emp_weight_dict, db_match, im, n_perts
            )

            branch_name = f"branch_{i + 1:0{br_sig_figs}}_{'_'.join(branch)}"

            im_dict[branch_name] = branch_dict

        ens_dict[DATASETS_ENSEMBLE_LABEL][im] = im_dict
    yaml.dump(ens_dict, open(os.path.join(output_dir, f"{ens_name}.yaml"), "w"))


def get_branches(emp_weight_dict, im, n_perts=1):
    """
    Determines what branches there are for each im_type in the ensemble
    :param emp_weight_dict: weight dictionary for ensemble weights
    :param im: the im to see what possible combinations there are
    :return: a tuple of: [tectonics types], [models are supported by them] - for each branch
    """
    groups_of_models = {}
    for tect_type, model_dict in emp_weight_dict[im].items():
        model_list = [model for model, score in model_dict.items() if score > 0]
        groups_of_models[tect_type] = model_list

    if len(groups_of_models) <= 0:
        groups_of_models["_"] = list(emp_weight_dict[im].values())[0]

    tect_types = []
    model_branches = list(itertools.product(*groups_of_models.values()))

    if n_perts > 1:
        for i in range(n_perts):
            tect_types.extend([branch_name for branch_name in groups_of_models.keys()])
    else:
        tect_types = list(groups_of_models.keys())

    return (
        tect_types,
        model_branches * n_perts,
    )