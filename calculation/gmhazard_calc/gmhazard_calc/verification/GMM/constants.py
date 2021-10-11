""" PSHA verification for the following Models
- AS_16
- CB_10
- CB_12
- CB_14
- Br_10
- ZA_06
- BCH_16
- BSSA_14
- ASK_14
- P_20_SI
- P_20_SS
- PH_20_SI
- PH_20_SS
- CH_20_SI
- CH_20_SS
- HA_20_SI
- HA_20_SS
Possible tectonic types
- ACTIVE_SHALLOW
- SUBDUCTION_INTERFACE
- SUBDUCTION_SLAB
"""
CONST_SITE_PARAMS = {
    "rtvz": 0,
}

CONST_FAULT_PARAMS = {
    "ACTIVE_SHALLOW": {
        "rake": 0,
        "dip": 90,
        "ztor": 0,
        "hdepth": 10,
        "zbot": 11,
    },
    "SUBDUCTION_SLAB": {
        "rake": -90,
        "dip": 45,
        "ztor": 50,
        "hdepth": 60,
        "zbot": 70,
    },
    "SUBDUCTION_INTERFACE": {
        "rake": 90,
        "dip": 20,
        "ztor": 10,
        "hdepth": 20,
        "zbot": 30,
    },
}

# Just for psha_psa_plots.py
PSA_IM_NAME = "pSA"

# Based on empirical_db/empirical_model_configs/20p11.yaml
ss_spectral_models = [
    "ZA_06",
    "A_18",
    "BCH_16",
    "P_20_SS",
    "HA_20_SS",
    "PH_20_SS",
    "CH_20_SS",
    "AG_20_SS",
    "AG_20_SS_NZ",
    "K_20_SS",
    "K_20_SS_NZ",
]
si_spectral_models = [
    "ZA_06",
    "A_18",
    "BCH_16",
    "P_20_SI",
    "HA_20_SI",
    "PH_20_SI",
    "CH_20_SI",
    "AG_20_SI",
    "AG_20_SI_NZ",
    "K_20_SI",
    "K_20_SI_NZ",
]
MODELS_DICT = {
    "ACTIVE_SHALLOW": {
        "PGV": ["Br_10", "ASK_14", "BSSA_14", "CB_14", "CY_14"],
        "PGA": ["Br_10", "ASK_14", "BSSA_14", "CB_14", "CY_14"],
        "pSA": ["Br_10", "ASK_14", "BSSA_14", "CB_14", "CY_14"],
        "CAV": ["CB_10"],
        "AI": ["CB_12"],
        "Ds575": ["AS_16"],
        "Ds595": ["AS_16"],
    },
    "SUBDUCTION_SLAB": {
        "PGV": ["P_20_SS", "HA_20_SS", "CH_20_SS", "K_20_SS", "K_20_SS_NZ"],
        "PGA": ss_spectral_models,
        "pSA": ss_spectral_models,
        "CAV": ["CB_10"],
        "AI": ["CB_12"],
        "Ds575": ["AS_16"],
        "Ds595": ["AS_16"],
    },
    "SUBDUCTION_INTERFACE": {
        "PGV": ["P_20_SI", "HA_20_SI", "CH_20_SI", "K_20_SI", "K_20_SI_NZ"],
        "PGA": si_spectral_models,
        "pSA": si_spectral_models,
        "CAV": ["CB_10"],
        "AI": ["CB_12"],
        "Ds575": ["AS_16"],
        "Ds595": ["AS_16"],
    },
}

DEFAULT_LABEL_COLOR = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]
