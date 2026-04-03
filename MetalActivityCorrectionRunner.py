import numpy as np


from collections import deque
from Conversions import CompositionInPpm, calculateMolarFraction, calculateMolesToPPM
from CustomTypes import AtomicWeightDictionary, ElementDictionary, KdDictionary
from dataclasses import dataclass
from GammaValues import GammaValues
from KdValues import KdValuesCorrected
from MetalActivityCalculator import CalculateGammaValues, ElementOnElementInteraction
from MidacoRunnerPlanetBuilder import MidacoKdOPlanetBuilder, MidacoPlanetBuilderResult
from OutputToExcelMidaco import ExcelWriterMidaco


@dataclass
class MetalActivityResult:
    newMantleValues: ElementDictionary
    newICoreValues: ElementDictionary
    KdOPB: float
    KdSi: float
    KdNi: float
    isOxidised: bool

# Function to check if there is an improvement in the results compared to the recent results. 
# Prevents an already balanced function from running longer than necessary.
def hasImprovement(recent_results: deque[MidacoPlanetBuilderResult], current_result: MidacoPlanetBuilderResult) -> bool:
    minImprovmentTreshold: float = 1e-3
    setToCheckICore: list[str] = ["Fe", "Si", "Ni", "O"]
    setToCheckMantle: list[str] = ["FeO", "SiO2", "NiO"]

    for recent_result in recent_results:
        for element in setToCheckMantle:
            difference = abs(current_result.newMantleValues[element] - recent_result.newMantleValues[element])
            if difference > minImprovmentTreshold:
                return True
        
        for element in setToCheckICore:
            difference = abs(current_result.newICoreValues[element] - recent_result.newICoreValues[element])
            if difference > minImprovmentTreshold:
                return True
            
        if abs(current_result.KdSi - recent_result.KdSi) > minImprovmentTreshold:
            return True
        
        if abs(current_result.KdNi - recent_result.KdNi) > minImprovmentTreshold:
            return True        
    
    return False

# Starts the equilibration process with Kd corrections. 
# Includes adjustments when the balance between equilibrium and Kd adjustments is reached, decreases the stepsize when necessary and checks if the results are oxidised.
def CallKdCorrectionEquilibration(
    molesMantle: ElementDictionary,
    molesICore: ElementDictionary,
    T: float,
    P: float,
    initialKdValues: KdDictionary,
    atomicWeights: AtomicWeightDictionary,
    epsDictionary: dict[ElementOnElementInteraction, float],
    timestep: int,
    excelWriter: ExcelWriterMidaco
) -> MetalActivityResult:
    maximumMacCalcCount: int = 10000
    macCalcStepsize: float = 0.1
    recent_results: deque[MidacoPlanetBuilderResult] = deque(maxlen=10)  # Used to check if we are running without improvement
    completeMolesMantle = molesMantle.copy()
    completeMolesICore = molesICore.copy()
    previousKdValues = initialKdValues.copy()
    previousMolesMantle = molesMantle.copy()
    previousMolesICore = molesICore.copy()
    kdValues = initialKdValues.copy()

    for macCalcCount in range(maximumMacCalcCount):
        result: MidacoPlanetBuilderResult = MidacoKdOPlanetBuilder(completeMolesMantle, completeMolesICore, T, P, kdValues)

        # Adjusts the stepsize of the Kd adjustments when the maximum time is reached
        if result.maxTimeReached:
            macCalcStepsize *= 0.5
            completeMolesMantle = previousMolesMantle.copy()
            completeMolesICore = previousMolesICore.copy()
            kdValues = previousKdValues.copy()
            KdSi = kdValues["Si"]
            KdNi = kdValues["Ni"]
            print("Max time reached, reducing stepsize to:", macCalcStepsize)
            continue

        # If the result is oxidised, return it with that flag
        if result.isOxidised:
            return MetalActivityResult(result.newMantleValues, result.newICoreValues, result.KdOPB, result.KdSi, result.KdNi, isOxidised=True)
        
        # If there is no further improvement and the balance between equilibrium and Kd adjustments is reached, return the current result
        if len(recent_results) == recent_results.maxlen and not hasImprovement(recent_results, result):
            return MetalActivityResult(result.newMantleValues, result.newICoreValues, result.KdOPB, KdSi, KdNi, isOxidised=False)             

        # Adjust Kd of Si and Ni
        recent_results.append(result)

        previousKdValues = kdValues.copy()
        previousMolesICore = completeMolesICore.copy()
        previousMolesMantle = completeMolesMantle.copy()
        
        completeMolesMantle.update(result.newMantleValues)
        completeMolesICore.update(result.newICoreValues)
        exportToExcel(completeMolesMantle, completeMolesICore, result.KdSi, result.KdNi, result.KdOPB, macCalcCount,  atomicWeights, timestep, excelWriter)

        moleFractionsICore = calculateMolarFraction(completeMolesMantle, completeMolesICore).core
        newGammaValues = CalculateGammaValues(epsDictionary, GammaValues, T, moleFractionsICore)
        gammaFe = np.exp(newGammaValues.solvent)
        gammaAll = newGammaValues.solute
        kdValues = KdValuesCorrected(T, P, gammaFe, gammaAll)

        KdSiDifference = kdValues["Si"] - result.KdSi
        KdNiDifference = kdValues["Ni"] - result.KdNi
        KdSi = result.KdSi + macCalcStepsize * KdSiDifference
        KdNi = result.KdNi + macCalcStepsize * KdNiDifference
        kdValues["Si"] = KdSi
        kdValues["Ni"] = KdNi
        print("MacCalcCount:", macCalcCount)
    return MetalActivityResult(result.newMantleValues, result.newICoreValues, result.KdOPB, KdSi, KdNi, isOxidised=False)

# Export the results of the equilibration process to Excel for every iteration cycle. This is not the final planetary composition
def exportToExcel(completeMolesMantle, completeMolesICore, KdSi, KdNi, KdOPB, macCalcCount, atomicWeights, timestep, excelWriter):
    ppmElements: CompositionInPpm = calculateMolesToPPM(completeMolesMantle, completeMolesICore, atomicWeights)
    ppmMantle: ElementDictionary = ppmElements.ppmMantle
    ppmICore: ElementDictionary = ppmElements.ppmCore

    outputParameters = {
        "Kd recalculation count": macCalcCount,
        "Kd Si": KdSi,
        "Kd Ni": KdNi,
        "Kd O": KdOPB,
    }

    excelWriter.AddDataToFrames(outputParameters, completeMolesMantle, ppmMantle, completeMolesICore, ppmICore)
    excelWriter.WriteToExcel(timestep)

        

    