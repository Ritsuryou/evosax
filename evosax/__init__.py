from .strategy import Strategy, EvoState, EvoParams
from .strategies import (
    SimpleGA,
    SimpleES,
    CMA_ES,
    DE,
    PSO,
    OpenES,
    PGPE,
    PBT,
    PersistentES,
    ARS,
    Sep_CMA_ES,
    BIPOP_CMA_ES,
    IPOP_CMA_ES,
    Full_iAMaLGaM,
    Indep_iAMaLGaM,
    MA_ES,
    LM_MA_ES,
    RmES,
    GLD,
    SimAnneal,
    SNES,
    xNES,
    ESMC,
    DES,
    SAMR_GA,
    GESMR_GA,
    GuidedES,
    ASEBO,
    CR_FM_NES,
    MR15_GA,
    RandomSearch,
    LES,
    LGA,
    NoiseReuseES,
    HillClimber,
    EvoTF_ES,
    DiffusionEvolution,
    SV_CMA_ES
)
from .core import FitnessShaper, ParameterReshaper
from .utils import ESLog
from .networks import NetworkMapper
from .problems import ProblemMapper


Strategies = {
    "SimpleGA": SimpleGA,
    "SimpleES": SimpleES,
    "CMA_ES": CMA_ES,
    "DE": DE,
    "PSO": PSO,
    "OpenES": OpenES,
    "PGPE": PGPE,
    "PBT": PBT,
    "PersistentES": PersistentES,
    "ARS": ARS,
    "Sep_CMA_ES": Sep_CMA_ES,
    "BIPOP_CMA_ES": BIPOP_CMA_ES,
    "IPOP_CMA_ES": IPOP_CMA_ES,
    "Full_iAMaLGaM": Full_iAMaLGaM,
    "Indep_iAMaLGaM": Indep_iAMaLGaM,
    "MA_ES": MA_ES,
    "LM_MA_ES": LM_MA_ES,
    "RmES": RmES,
    "GLD": GLD,
    "SimAnneal": SimAnneal,
    "SNES": SNES,
    "xNES": xNES,
    "ESMC": ESMC,
    "DES": DES,
    "SAMR_GA": SAMR_GA,
    "GESMR_GA": GESMR_GA,
    "GuidedES": GuidedES,
    "ASEBO": ASEBO,
    "CR_FM_NES": CR_FM_NES,
    "MR15_GA": MR15_GA,
    "RandomSearch": RandomSearch,
    "LES": LES,
    "LGA": LGA,
    "NoiseReuseES": NoiseReuseES,
    "HillClimber": HillClimber,
    "EvoTF_ES": EvoTF_ES,
    "DiffusionEvolution": DiffusionEvolution,
    "SV_CMA_ES": SV_CMA_ES,
}

__all__ = [
    "Strategies",
    "EvoState",
    "EvoParams",
    "FitnessShaper",
    "ParameterReshaper",
    "ESLog",
    "NetworkMapper",
    "ProblemMapper",
    "Strategy",
    "SimpleGA",
    "SimpleES",
    "CMA_ES",
    "DE",
    "PSO",
    "OpenES",
    "PGPE",
    "PBT",
    "PersistentES",
    "ARS",
    "Sep_CMA_ES",
    "BIPOP_CMA_ES",
    "IPOP_CMA_ES",
    "Full_iAMaLGaM",
    "Indep_iAMaLGaM",
    "MA_ES",
    "LM_MA_ES",
    "RmES",
    "GLD",
    "SimAnneal",
    "SNES",
    "xNES",
    "ESMC",
    "DES",
    "SAMR_GA",
    "GESMR_GA",
    "GuidedES",
    "ASEBO",
    "CR_FM_NES",
    "MR15_GA",
    "RandomSearch",
    "LES",
    "LGA",
    "NoiseReuseES",
    "HillClimber",
    "EvoTF_ES",
    "DiffusionEvolution",
    "SV_CMA_ES"
]
