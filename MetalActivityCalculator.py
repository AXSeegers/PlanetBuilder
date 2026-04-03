from dataclasses import dataclass

import pandas as pd
import numpy as np

from CustomTypes import ElementDictionary

# Read epsilon values from csv file
def ReadEpsValues():
    ReadEpsValues = pd.DataFrame(pd.read_csv('EValues.csv'))
    epsValues = ReadEpsValues.set_index('epsilons')
    return epsValues

@dataclass
class ElementOnElementInteraction:
    rowElement: str
    columnElement: str

    def __hash__(self) -> int:
        return hash((self.rowElement, self.columnElement))

# Create dictionary with the epsilon values
def CreateEpsDict(epsValues) -> dict[ElementOnElementInteraction, float]:
    epsDict: dict[ElementOnElementInteraction, float] = {}
    for x in range(len(epsValues.index)):
        for y in range(len(epsValues.columns)):
            rowElement = epsValues.index[x]
            columnElement = epsValues.columns[y]
            epsilonValue = epsValues.iloc[x,y]
            epsDict[ElementOnElementInteraction(rowElement, columnElement)] = epsilonValue
    return epsDict

# Create dictionary with the gamma0 values (reference value)
# If reference temperature is not 1873K, replace 1873 with a different value for the exceptions
def CreateGammaZeroDict(T, gammaValues) -> ElementDictionary:
    gammaZero = {}
    for key in gammaValues:
        gammaZero[key] = np.exp(1873 / T * np.log(gammaValues[key]))
    return gammaZero

# Adjust the epsilon values to the event temperature
# If reference temperature is not 1873K, replace 1873 with a different value for the exceptions
def CorrectEpsT(T, epsValues) -> dict[ElementOnElementInteraction, float]:
    adjustedEValues: dict[ElementOnElementInteraction, float] = {}
    for key in epsValues:
        adjustedEValues[key] = 1873 / T * epsValues[key]
    return adjustedEValues

# Adjust the epsilon value for a single point to the event temperature
# If reference temperature is not 1873K, replace 1873 with a different value for the exceptions
def CorrectEpsTSinglePoint(T, epsValue):
    return (1873 / T * epsValue)

# Calculate gamma value of solvent (Fe), based on Eq. 23 from Ma (2001), also shown as eq. 46 in our paper
# Variables i, j and k are the same as those in Ma (2001) and our paper
# The gamma solvent calculation is split up in parts, following the separate lines of eq. 46 in our paper
def CalculateGammaSolvent(epsValues, molarFracCore, T) -> float:
    gammaSolventPart1 = 0
    gammaSolventPart2 = 0
    gammaSolventPart3 = 0
    gammaSolventPart4 = 0
    gammaSolventPart5 = 0

    for i in molarFracCore:
        if molarFracCore[i] == 0 : continue
        i_i = ElementOnElementInteraction(i, i)
        if i_i in epsValues:
            if epsValues[i_i] == 0 : continue
            gammaSolventPart1 += epsValues[i_i] * (molarFracCore[i] + np.log(1 - molarFracCore[i]))

        for k in molarFracCore:
            if molarFracCore[k] == 0 : continue
            if i == k : continue
            i_k = ElementOnElementInteraction(i, k)
            if i_k in epsValues:
                epsik = epsValues[i_k]
                if epsik == 0 : continue
                gammaSolventPart3 += epsik * molarFracCore[i] * molarFracCore[k] * (1+ (np.log(1-molarFracCore[k])/molarFracCore[k] - 1 /(1-molarFracCore[i])))
                gammaSolventPart5 += epsik * molarFracCore[i]**2 * molarFracCore[k]**2 * (1/(1-molarFracCore[i]) + 1/(1-molarFracCore[k]) + molarFracCore[i]/(2*(1-molarFracCore[i])**2)-1)  

    coreElements = list(molarFracCore.keys())
    for j in range(len(coreElements)-1):
        for k in range(j+1, len(coreElements)):
            molarFracCorej = molarFracCore[coreElements[j]]
            molarFracCorek = molarFracCore[coreElements[k]]
            if molarFracCorej == 0 or molarFracCorek == 0 : continue
            j_k = ElementOnElementInteraction(coreElements[j], coreElements[k])
            if j_k not in epsValues : continue
            epsjk = epsValues[j_k]

            if (epsjk == 0) : continue

            gammaSolventPart2 += epsjk * molarFracCorej * molarFracCorek * (1+np.log(1-molarFracCorej)/molarFracCorej + np.log(1-molarFracCorek)/molarFracCorek)
            gammaSolventPart4 += epsjk *molarFracCorej**2 * molarFracCorek**2 * (1/(1-molarFracCorej) + 1/(1 - molarFracCorek)-1)
    GammaSolvent = gammaSolventPart1 - gammaSolventPart2 + gammaSolventPart3 + 0.5 * gammaSolventPart4 - gammaSolventPart5
    return GammaSolvent

# Calculate gamma values of the solutes, based on Eq. 24 from Ma (2001), also shown as eq. 47 in our paper
# Variables i, j and k are the same as those in Ma (2001) and our paper
# The gamma solute calculation is split up in parts, following the separate lines of eq. 47 in our paper
def CalculateGammaSolute(epsValues, gammaZero, molarFracCore, gammaSolvent) -> ElementDictionary:
    gammaSolute = {}
    gammaSolutePart1 = {}
    gammaSolutePart2 = {}
    gammaSolutePart3 = {}

    for i in molarFracCore:
        gammaSolutePart1[i] = 0
        gammaSolutePart2[i] = 0
        gammaSolutePart3[i] = 0

        for k in molarFracCore:
            i_k = ElementOnElementInteraction(i, k)
            if i_k in epsValues:
                if i == k :
                    gammaSolutePart1[i] += epsValues[i_k] * np.log(1 - molarFracCore[i])
                else:
                    gammaSolutePart2[i] += epsValues[i_k] * molarFracCore[k] * (1+ (np.log(1-molarFracCore[k]))/molarFracCore[k] - 1/(1-molarFracCore[i]))
                    gammaSolutePart3[i] += epsValues[i_k] * molarFracCore[k]**2 * molarFracCore[i] * (1/(1-molarFracCore[i]) + 1/(1-molarFracCore[k]) + molarFracCore[i]/(2*(1-molarFracCore[i])**2) -1)
        if i in gammaZero:
            gammaSolute[i] = np.exp(gammaSolvent + np.log(gammaZero[i]) - gammaSolutePart1[i] - gammaSolutePart2[i] + gammaSolutePart3[i])
    return gammaSolute

@dataclass
class CalculatedGammaValues:
    solvent: float
    solute: ElementDictionary

# Main function to calculate the gamma values of the solvent (Fe) and solutes
# As this is a generic calculation, the core type is not specified and can be an impactor core or if requested a planetary core, depending on the function calling it 
def CalculateGammaValues(epsilonDictionary: dict[ElementOnElementInteraction, float], gammaValues: ElementDictionary, T: float, molarFracCore: ElementDictionary) -> CalculatedGammaValues:
    # epsDictionary: dict[ElementOnElementInteraction, float] = CreateEpsDict(epsValues)
    gammaZero: ElementDictionary = CreateGammaZeroDict(T, gammaValues)
    epsT: dict[ElementOnElementInteraction, float] = CorrectEpsT(T, epsilonDictionary)
    solvent: float = CalculateGammaSolvent(epsT, molarFracCore, T)
    solute: ElementDictionary = CalculateGammaSolute(epsT, gammaZero, molarFracCore, solvent)
    return CalculatedGammaValues(solvent=solvent, solute=solute)