from dataclasses import dataclass

import numpy as np
import time
import warnings

from Conversions import CompositionInPpm, calculateMoles
from Conversions import calculateMolesToPPM
from Conversions import calculateRelativeMass
from Conversions import calculateMolarFraction
from Conversions import deconstructCompounds
from CustomTypes import AtomicWeightDictionary, ElementDictionary, KdDictionary, MantleAndCoreDictionaries
from GammaValues import GammaValues
from KdValues import KdValuesCorrected
from KdValues import KdValuesUncorrected
from MetalActivityCalculator import CalculateGammaValues, CalculatedGammaValues, CreateEpsDict, ElementOnElementInteraction, ReadEpsValues
from MetalActivityCorrectionRunner import CallKdCorrectionEquilibration, MetalActivityResult
from MinorElements import CalculateMinorElements
from OutputToExcel import ExcelWriter
from OutputToExcelMidaco import ExcelWriterMidaco
from ReadExcelInputSingleStage import Input
from ReadExcelInputSingleStage import ImportInputFile
from StandardEquilibrationRunner import CallStandardEquilibration, StandardEquilibrationResult

warnings.filterwarnings("ignore", category=DeprecationWarning)
np.set_printoptions(legacy='1.25')

# Adjust the file name to the name of your input Excel file (single stage file only)
# Please place the input file in the same directory as the code to avoid access issues 
inputData = ImportInputFile('InputFile - SingleStage.xlsx')

@dataclass
class singleStageResult :
    gammaFe: float
    pressure: float
    temperature: float
    KdSiResult: float
    KdNiResult: float
    KdOResult: float
    fO2: float

# Main class of the single stage core formation program, calls all other necessary functions
class SingleStageCalculation :
    def __init__ (self, input : Input):
        elementsMantle: ElementDictionary = input.startingComposition.mantleCompositionDict
        elementsCore: ElementDictionary = input.startingComposition.coreCompositionDict
        startingRelativeSize: float = input.startingComposition.planetRelativeStartingMass
        startingCoreSize: float = input.startingComposition.planetCoreSize
        startingRelativeMass: float = calculateRelativeMass(elementsMantle, elementsCore, startingRelativeSize, startingCoreSize)
        massCore: float = startingRelativeMass.core
        massMantle: float = startingRelativeMass.mantle
        self.updatedAtomicWeights: AtomicWeightDictionary = deconstructCompounds(elementsMantle, elementsCore)
        molesStart: MantleAndCoreDictionaries = calculateMoles(massMantle, massCore, self.updatedAtomicWeights)

        self.input: Input = input
        self.relativeSize: float = startingRelativeSize
        self.molesMantle: ElementDictionary = molesStart.mantle.copy()
        self.molesCore: ElementDictionary = molesStart.core.copy()
        self.coreSize: float = startingCoreSize
        self.excelWriter: ExcelWriter = ExcelWriter(input)
        self.midacoWriter: ExcelWriterMidaco = ExcelWriterMidaco(input)

        epsValues = ReadEpsValues()
        self.epsDictionary: dict[ElementOnElementInteraction, float] = CreateEpsDict(epsValues)

    
    def RunSingleStage(self):
        i: int = 1
        start: float = time.time()

        #Store old compositions
        molesMantleOld: ElementDictionary = {}
        for key in self.molesMantle:
            molesMantleOld[key] = self.molesMantle[key]

        molesCoreOld: ElementDictionary = {}
        for key in self.molesCore:
            molesCoreOld[key] = self.molesCore[key]
    
        # Calculate new compositions of the mantle and core
        singleStageResult: SingleStageCalculation = self.SingleStageEquilibration(molesMantleOld, molesCoreOld)

        # Calculate concentrations of the new compositions in ppm
        ppmElements: CompositionInPpm = calculateMolesToPPM(self.molesMantle, self.molesCore, self.updatedAtomicWeights)
        ppmMantle: ElementDictionary = ppmElements.ppmMantle
        ppmCore: ElementDictionary = ppmElements.ppmCore
        self.coreSize: float = ppmElements.relativeCoreSize
        self.fO2: float = singleStageResult.fO2

        end: float = time.time()
        print("Endtime:", (end-start)/60, "minutes")

        # Output parameters that should be put in the first block of the Excel file
        outputParameters = {'Timestep' : i, 
                    'P (GPa)' : singleStageResult.pressure, 
                    'T(K)' : singleStageResult.temperature, 
                    'M/Me' : self.relativeSize, 
                    'Core Size' : self.coreSize, 
                    'Gamma Fe' : singleStageResult.gammaFe,
                    'Kd Si' : singleStageResult.KdSiResult,
                    'Kd Ni' : singleStageResult.KdNiResult,
                    'Kd O' : singleStageResult.KdOResult,
                    'fO2' : singleStageResult.fO2}

        # Add the data to the Excel file
        self.excelWriter.AddDataToFrames(outputParameters, self.molesMantle, self.molesCore, ppmMantle, ppmCore, 0, 0)
        self.excelWriter.WriteToExcel()

    # If the event is an impactor, this function will be called
    def SingleStageEquilibration(self, molesMantleOld, molesCoreOld) -> singleStageResult:
        # Update the three relevant phases of planet mantle, impactor core and if relevant the disequilibrated impactor core
        self.molesMantle: ElementDictionary = molesMantleOld.copy()
        self.molesCore: ElementDictionary = molesCoreOld.copy()

        # Equilibration pressure and temperature     
        Pressure: float = self.input.startingComposition.pressure
        Temperature: float = self.input.startingComposition.temperature
        print('Pressure:', Pressure)
        print('Temperature:', Temperature)  

        # Calculate the new equilibrated major element composition
        # Kd Correction on: the Kd values are corrected for the activity of Fe in metal liquid 
        if self.input.settings.KdCorrectionEnabled:
            moleFractionCore: MantleAndCoreDictionaries = calculateMolarFraction(self.molesMantle, self.molesCore).core
            newGammaValues: CalculatedGammaValues = CalculateGammaValues(self.epsDictionary, GammaValues, Temperature, moleFractionCore)
            gammaFe: float = np.exp(newGammaValues.solvent)
            gammaAll: ElementDictionary = newGammaValues.solute
            kdValues: KdDictionary = KdValuesCorrected(Temperature, Pressure, gammaFe, gammaAll)
            solverData: MetalActivityResult = CallKdCorrectionEquilibration(self.molesMantle, self.molesCore, Temperature, Pressure, kdValues, self.updatedAtomicWeights, self.epsDictionary, 1, self.midacoWriter)

        else:
            gammaFe: float = 1
            kdValues: KdDictionary = KdValuesUncorrected(Temperature, Pressure)
            solverData : StandardEquilibrationResult = CallStandardEquilibration(self.molesMantle, self.molesCore, Temperature, Pressure, kdValues)
        
        KdOResult: float = solverData.KdOPB
        KdSiResult: float = solverData.KdSi
        KdNiResult: float = solverData.KdNi
        
        # Save solver data, regardless of which solver was used and add to appropriate phases
        newMantleData: ElementDictionary = solverData.newMantleValues
        for key in newMantleData:
            self.molesMantle[key] = newMantleData[key]   

        newCoreData: ElementDictionary = solverData.newICoreValues
        for key in newCoreData:
            self.molesCore[key] = newCoreData[key]    

        # Calculate minor elements using solver data and KD values
        minorElements: MantleAndCoreDictionaries = CalculateMinorElements(self.molesMantle, self.molesCore, kdValues) 
        newMantleMinor: ElementDictionary = minorElements.mantle
        newCoreMinor: ElementDictionary = minorElements.core
        for key in newMantleMinor:
            self.molesMantle[key] = newMantleMinor[key]
        for key in newCoreMinor:
            self.molesCore[key] = newCoreMinor[key]

        # Calculate the new fO2
        molarFractions: MantleAndCoreDictionaries = calculateMolarFraction(self.molesMantle, self.molesCore)
        xFeOMantle = molarFractions.mantle["FeO"]
        xFeCore = molarFractions.core["Fe"]
        xFeOMW: float = 1.148 * xFeOMantle + 1.319 * xFeOMantle * xFeOMantle 
        self.fO2: float = 2*np.log10(xFeOMW/xFeCore)       
            
        return singleStageResult(
            gammaFe=gammaFe, 
            pressure=Pressure, 
            temperature=Temperature,
            KdSiResult=KdSiResult, 
            KdNiResult=KdNiResult, 
            KdOResult=KdOResult, 
            fO2=self.fO2)
    
#Start the program using the given input file
SingleStageCalculation = SingleStageCalculation(inputData)
SingleStageCalculation.RunSingleStage()