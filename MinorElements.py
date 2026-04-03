import numpy as np

from CustomTypes import ElementDictionary, KdDictionary, MantleAndCoreDictionaries
from ValenceStates import ValenceState

# Calculates the minor element compositions based on the equilibrated major element compositions
def CalculateMinorElements(molesMantle: ElementDictionary, molesICore: ElementDictionary, KDValues: KdDictionary) -> MantleAndCoreDictionaries:
    molesTotalTraceElements: ElementDictionary = {}
    molesRatioTraceElements: ElementDictionary = {}
    molesMantleTraceElements: ElementDictionary = {}
    molesICoreTraceElements: ElementDictionary = {}

    #Skip these major elements that have already been calculated by the solver
    skipElements: list[str] = ["FeO", "Fe", "SiO2", "Si", "NiO", "Ni", "O", "Al2O3", "MgO", "CaO"]

    # Calculate the approximate molar fractions of FeO mantle and Fe core, used for KD calculations of the minor elements based on Eq. 7 in our paper
    # The total moles of every trace elements is calculated, alongside the partitioning ratio based on the KD, dividing the total amount of moles over the impactor core and planetary mantle
    totalMolesMajorMantle: float = molesMantle["FeO"] + molesMantle["SiO2"] + molesMantle["NiO"] + molesMantle["Al2O3"] + molesMantle["MgO"] + molesMantle["CaO"]
    totalMolesMajorICore: float = molesICore["Fe"] + molesICore["Si"] + molesICore["Ni"] + molesICore["O"]

    xFeO: float = molesMantle["FeO"] / totalMolesMajorMantle
    xFe: float = molesICore["Fe"] / totalMolesMajorICore

    for key in molesMantle:
        if key in skipElements:
            continue
        if key in molesICore:     
            molesTotalTraceElements[key] = molesMantle[key] + molesICore[key]
        else:
            molesTotalTraceElements[key] = molesMantle[key]
    
    for key in molesTotalTraceElements:
        if not key in KDValues:
            molesMantleTraceElements[key] = molesTotalTraceElements[key]
            continue
        molesRatioTraceElements[key] = KDValues[key] * ((np.power(xFe, (ValenceState[key]/2)))/(np.power(xFeO, (ValenceState[key]/2)))) * totalMolesMajorICore / totalMolesMajorMantle
        molesICoreTraceElements[key] = molesTotalTraceElements[key] / (1/molesRatioTraceElements[key] + 1)
        molesMantleTraceElements[key] = molesTotalTraceElements[key] - molesICoreTraceElements[key]

    return MantleAndCoreDictionaries(mantle=molesMantleTraceElements, core=molesICoreTraceElements)
