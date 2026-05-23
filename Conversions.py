from AtomicWeights import AtomicWeights
import re
from CustomTypes import AtomicWeightDictionary, ElementDictionary, MantleAndCoreDictionaries
from dataclasses import dataclass

# This file contains the functions that convert units (e.g. from moles to ppm) and calculates the core/mantle masses

@dataclass
class CompositionInPpm:
    ppmMantle: ElementDictionary
    ppmCore: ElementDictionary
    relativeCoreSize: float

# Calculates the relative mass of the mantle and core. Based on the total planet mass, relative size, and concentrations
def calculateRelativeMass(elementsMantle: ElementDictionary, elementsCore: ElementDictionary, startingRelativeSize : float, startingCoreSize: float) -> MantleAndCoreDictionaries:
    massMantle: ElementDictionary = {}
    massCore: ElementDictionary = {}

    for key in elementsMantle:
        massMantle[key] = elementsMantle[key] * startingRelativeSize * (1-startingCoreSize)
    for key in elementsCore:
        massCore[key] = elementsCore[key] * startingRelativeSize * startingCoreSize

    return MantleAndCoreDictionaries(mantle = massMantle, core = massCore)    

# Deconstructs compounds (e.g. oxides in the mantle) to calculate the atomic weight of each element
def getAtomicWeightByDeconstruction(composedElement: str) -> float:
    elements = re.findall('[A-Z][^A-Z]*', composedElement)
     
    elementOccurence: ElementDictionary = {}
    for i in range(len(elements)):
        multipleAtoms: re.Match[str] = re.search(r'\d+', elements[i])
        if multipleAtoms:
            splitOccurence = re.findall('[a-zA-Z]+|[0-9]', multipleAtoms.string)
            elementOccurence.update({splitOccurence[0] : int(splitOccurence[1])})
        else:
            elementOccurence.update({elements[i]: 1})

    totalAtomicWeight: float = 0.0
    for j in elementOccurence:
        totalAtomicWeight += AtomicWeights[j] * elementOccurence[j]

    return totalAtomicWeight

# Reads all relevant compounds, calls the deconstruction function and creates a new dictionary with the atomic weights of all elements in the mantle and core
def deconstructCompounds(elementsMantle: ElementDictionary, elementsCore: ElementDictionary) -> AtomicWeightDictionary:
    mergedDictionaryKeys: list[str] = list(set(elementsMantle.keys()).union(set(elementsCore.keys())))
    atomicWeightDictionary: AtomicWeightDictionary = {}

    for key in mergedDictionaryKeys:
        atomicWeightDictionary[key] = getAtomicWeightByDeconstruction(key)

    return atomicWeightDictionary


# Calculates the moles of each element in the mantle and core. Based on the mass and atomic weights
def calculateMoles(elementsMantle : ElementDictionary, elementsCore :ElementDictionary, atomicWeights: AtomicWeightDictionary) -> MantleAndCoreDictionaries:
    molesMantle = {}
    for key in elementsMantle:
        molesMantle[key] = (elementsMantle[key] / atomicWeights[key])

    molesCore = {}
    for key in elementsCore:
        molesCore[key] = (elementsCore[key] / atomicWeights[key])

    return MantleAndCoreDictionaries(mantle = molesMantle, core = molesCore)

# Calculates the molar fraction of each element in the mantle and core. Based on the moles and total moles
def calculateMolarFraction(molesMantle : ElementDictionary, molesCore: ElementDictionary) -> MantleAndCoreDictionaries:
    moleFracMantle = {}
    moleFracCore = {}

    totalMantle: float = sum(molesMantle.values()) 
    totalCore: float = sum(molesCore.values())

    for key in molesMantle:
        moleFracMantle[key] = molesMantle[key] / totalMantle

    for key in molesCore:
        moleFracCore[key] = molesCore[key] / totalCore
    
    return MantleAndCoreDictionaries(mantle = moleFracMantle, core = moleFracCore)

# Calculates the ppm of each element in the mantle and core. Based on the moles, atomic weights, and total mass
def calculateMolesToPPM (molesMantle : ElementDictionary, molesCore: ElementDictionary, atomicWeights: AtomicWeightDictionary) -> CompositionInPpm:
    percentageMantle: ElementDictionary = {}
    percentageCore: ElementDictionary = {}
    ppmMantle: ElementDictionary = {}
    ppmCore: ElementDictionary = {}

    for key in molesMantle:
        percentageMantle[key] = molesMantle[key] * atomicWeights[key]

    for key in molesCore:
        percentageCore[key] = molesCore[key] * atomicWeights[key]

    totalMantle: float = sum(percentageMantle.values())
    totalCore: float = sum(percentageCore.values())
    relativeCoreSize: float = totalCore/(totalMantle + totalCore)

    for key in percentageMantle:
        ppmMantle[key] = percentageMantle[key] / totalMantle * 1000000

    for key in percentageCore:
       ppmCore[key] = percentageCore[key] / (totalCore) * 1000000
    
    return CompositionInPpm(ppmMantle=ppmMantle, ppmCore=ppmCore, relativeCoreSize=relativeCoreSize)

# Calculates the mass of the protoplanet relative to the completed planet. Based on relative masses and concentrations in ppm 
def massRelativePlanet(relativeMass: float, mantleInPPM: ElementDictionary, coreInPPM: ElementDictionary) -> MantleAndCoreDictionaries:
    mantleRelativeMassInPPM: ElementDictionary = {}
    coreRelativeMassInPPM: ElementDictionary = {}

    for key in mantleInPPM:
        mantleRelativeMassInPPM[key] = mantleInPPM[key] * relativeMass
    
    for key in coreInPPM:
        coreRelativeMassInPPM[key] = coreInPPM[key] * relativeMass
    
    return MantleAndCoreDictionaries(mantle=mantleRelativeMassInPPM, core=coreRelativeMassInPPM)

# Calculates the percentage of the total mass in the mantle and core. Based on the relative mass% of the protoplanet core and mantle
def coreMantlePercentage(relativeCoreSize: float, mantleInPPM: ElementDictionary, coreInPPM: ElementDictionary) -> MantleAndCoreDictionaries:
    mantlePercentageInPPM: ElementDictionary = {}
    corePercentageInPPM: ElementDictionary = {}
    relativeMantleSize: float = 1 - relativeCoreSize

    for key in mantleInPPM:
        mantlePercentageInPPM[key] = mantleInPPM[key] * relativeMantleSize
    
    for key in coreInPPM:
        corePercentageInPPM[key] = coreInPPM[key] * relativeCoreSize

    return MantleAndCoreDictionaries(mantle=mantlePercentageInPPM, core=corePercentageInPPM)