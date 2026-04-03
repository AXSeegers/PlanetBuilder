import numpy  as np
from CustomTypes import KdDictionary
from ValenceStates import ValenceState

#Uncorrected for activity of Fe in metal
def KdValuesUncorrected (T: float, P: float) -> KdDictionary:
    KdUncorrected: KdDictionary = {
        "Si" : 10**(1.3 - 13500/T), # Fischer et al. (2015)
        "Ni" : 10**(0.46 + 2700/T - 61*P/T), # Fischer et al. (2015)
        "Co" : 10**(0.36 + 1500/T - 33*P/T), # Fischer et al. (2015)
        "Cr" : 10**(-2900/T +9*P/T), # Fischer et al. (2015)
        "V" : 10**(-0.3 - 5400/T), # Fischer et al. (2015)
        "Nb" : 10**(2.66 - 14032/T - 199*P/T), # Mann et al. (2009)
        "Ta" : 10**(0.84 - 13806/T - 101*P/T), # Mann et al. (2009)
        "W" : 10**(-0.35 + 1209/T - 114*P/T) # Cottrell et al. (2009, 2010)
    }
    return KdUncorrected

# Corrected for activity of Fe in metal, using the method from Wade and Wood (2005) and Ma (2001), explained in section 2.4 of our paper
def KdValuesCorrected (T: float, P: float, GammaFe: float, GammaAll: dict[str, float]) -> KdDictionary:
    KdCorrected: KdDictionary = {
        "Si" : 10**((1.3 - 13500/T) - (np.log10(GammaAll["Si"]/(np.power(GammaFe, (ValenceState["Si"]/2)))))), # Fischer et al. (2015)
        "Ni" : 10**((0.46 + 2700/T - 61*P/T) - (np.log10(GammaAll["Ni"]/(np.power(GammaFe, (ValenceState["Ni"]/2)))))), # Fischer et al. (2015)
        "Co" : 10**((0.36 + 1500/T - 33*P/T) - (np.log10(GammaAll["Co"]/(np.power(GammaFe, (ValenceState["Co"]/2)))))), # Fischer et al. (2015)
        "Cr" : 10**((-2900/T +9*P/T)- (np.log10(GammaAll["Cr"]/(np.power(GammaFe, (ValenceState["Cr"]/2)))))), # Fischer et al. (2015)
        "V" : 10**((-0.3 - 5400/T + 19*P/T) - (np.log10(GammaAll["V"]/(np.power(GammaFe, (ValenceState["V"]/2)))))), # Fischer et al. (2015)
        "Nb" : 10**((2.66 - 14032/T - 199*P/T) - ( np.log10(GammaAll["Nb"]/(np.power(GammaFe, (ValenceState["Nb"]/2)))))), # Mann et al. (2009)
        "Ta" : 10**((0.84 - 13806/T - 105*P/T) - ( np.log10(GammaAll["Ta"]/(np.power(GammaFe, (ValenceState["Ta"]/2)))))), # Mann et al. (2009)
        "W" : 10**((-0.35 + 1209/T - 114*P/T) - (np.log10(GammaAll["W"]/(np.power(GammaFe, (ValenceState["W"]/2)))))), # Cottrell et al. (2009, 2010)
    }
    return KdCorrected