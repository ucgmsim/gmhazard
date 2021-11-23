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
    "ACTIVE_SHALLOW": {"rake": 0, "dip": 90, "ztor": 0, "hdepth": 10, "zbot": 11,},
    "SUBDUCTION_SLAB": {"rake": -90, "dip": 45, "ztor": 50, "hdepth": 60, "zbot": 70,},
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

# Based on db_creation/empirical_db/empirical_model_configs/21p10.yaml
ss_spectral_models = [
    "ZA_06",
    "BCH_16",
    "A_18",
    "P_20",
    "AG_20",
    "AG_20_NZ",
    "K_20",
    "K_20_NZ",
]
si_spectral_models = [
    "ZA_06",
    "BCH_16",
    "A_18",
    "P_20",
    "AG_20",
    "AG_20_NZ",
    "K_20",
    "K_20_NZ",
]
MODELS_DICT = {
    "ACTIVE_SHALLOW": {
        "PGV": ["Br_10", "ASK_14", "BSSA_14", "CB_14", "CY_14"],
        "PGA": ["Br_10", "ASK_14", "BSSA_14", "CB_14", "CY_14"],
        "pSA": ["Br_10", "ASK_14", "BSSA_14", "CB_14", "CY_14"],
    },
    "SUBDUCTION_SLAB": {
        "PGV": ["P_20", "K_20", "K_20_NZ"],
        "PGA": ss_spectral_models,
        "pSA": ss_spectral_models,
    },
    "SUBDUCTION_INTERFACE": {
        "PGV": ["P_20", "K_20", "K_20_NZ"],
        "PGA": si_spectral_models,
        "pSA": si_spectral_models,
    },
}

DEFAULT_LABEL_COLOR = [
    "#d62728",
    "#2ca02c",
    "#ffe119",
    "#0082c8",
    "#ff7f0e",
    "#911eb4",
    "#46f0f0",
    "#f032e6",
    "#d2f53c",
    "#fabebe",
    "#008080",
    "#e6beff",
    "#aa6e28",
    "#800000",
    "#aaffc3",
    "#808000",
    "#ffd8b1",
    "#000080",
    "#808080",
    "#000000",
]
