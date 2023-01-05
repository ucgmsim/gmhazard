from typing import Sequence

import pandas as pd

import gmhazard_calc as gc

def load_stations_fault_data(
    imdb_ffps: Sequence[str], stations: Sequence[str], im: gc.im.IM, fault: str
):
    """
    Loads the IM data for the specified stations and fault from the IMDB's

    Parameters
    ----------
    imdb_ffps: Sequence[str]
        List of imdb full file paths to load
    stations: Sequence[str]
        List of station names to grab data for from the imdbs
    im: IM
        IM Object to extract values from the imdb
    fault: String
        Fault name to extract data from the imdb
    """
    # Obtain the IMDB with the correct fault information
    # Assuming only 1 GMM is being used so only 1 IMDB will have the fault information
    fault_imdbs = []
    for imdb_ffp in imdb_ffps:
        with gc.dbs.IMDB.get_imdb(imdb_ffp, writeable=False) as imdb:
            if fault in imdb.rupture_names():
                fault_imdbs.append(imdb_ffp)
    # Ensure only 1 IMDB has the given fault data
    assert len(fault_imdbs) == 1

    # Extract rupture data from imdb for each station and combine to a DataFrame
    site_rupture_data = []
    with gc.dbs.IMDB.get_imdb(fault_imdbs[0], writeable=False) as imdb:
        for station in stations:
            cur_data = imdb.im_data(station, im, incl_within_between_sigma=True)
            # Check fault data was found
            assert cur_data is not None
            site_rupture_data.append(cur_data.loc[fault])
    return pd.DataFrame(site_rupture_data, index=stations)
