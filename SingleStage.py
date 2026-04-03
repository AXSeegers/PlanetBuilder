from dataclasses import dataclass

import numpy as np
import time
import warnings

from Conversions import CompositionInPpm, calculateMoles
from Conversions import calculateMolesToPPM
from Conversions import calculateRelativeMass
from Conversions import calculateMolarFraction
from CustomTypes import ElementDictionary, KdDictionary, MantleAndCoreDictionaries
from GammaValues import GammaValues
from KdValues import KdValuesCorrected
from KdValues import KdValuesUncorrected
from MetalActivityCalculator import ReadEpsValues
from MetalActivityCalculator import CalculatedGammaValues, CalculateGammaValues
from MinorElements import CalculateMinorElements
from OutputToExcel import ExcelWriter
from ReadExcelInputSingleStage import Input
from ReadExcelInputSingleStage import ImportInputFile
from StandardEquilibrationRunner import CallStandardEquilibration, StandardEquilibrationResult

warnings.filterwarnings("ignore", category=DeprecationWarning)
np.set_printoptions(legacy='1.25')

@dataclass
class SingleStageCalculation :
    gammaFe: float
    Pressure: float
    Temperature: float
    KdSiResult: float
    KdNiResult: float
    KdOResult: float
    fO2: float

class SingleStageCalculation :
    def __init__ (self, input : Input):
        elementsMantle: ElementDictionary = input.startingComposition.mantleCompositionDict
        elementsCore: ElementDictionary = input.startingComposition.coreCompositionDict
        startingRelativeSize: float = input.startingComposition.planetRelativeStartingMass
        startingCoreSize: float = input.startingComposition.planetCoreSize
        startingRelativeMass: float = calculateRelativeMass(elementsMantle, elementsCore, startingRelativeSize, startingCoreSize)
        massCore: float = startingRelativeMass.core
        massMantle: float = startingRelativeMass.mantle
        molesStart: MantleAndCoreDictionaries = calculateMoles(massMantle, massCore)

        self.input: Input = input
        self.relativeSize: float = startingRelativeSize
        self.molesMantle: ElementDictionary = molesStart[0].copy()
        self.molesCore: ElementDictionary = molesStart[1].copy()
        self.coreSize: float = startingCoreSize
        self.excelWriter: ExcelWriter = ExcelWriter(input)
    
    def RunSingleStage(self):
        i: int = 1
        start = time.time()
        molesMantleOld: ElementDictionary = {}
        for key in self.molesMantle:
            molesMantleOld[key] = self.molesMantle[key]

        molesCoreOld: ElementDictionary = {}
        for key in self.molesCore:
            molesCoreOld[key] = self.molesCore[key]
    
        singleStageResults: SingleStageCalculation = self.SingleStageEquilibration(molesMantleOld, molesCoreOld)

        ppmElements: CompositionInPpm = calculateMolesToPPM(self.molesMantle, self.molesCore)
        ppmMantle: ElementDictionary = ppmElements.ppmMantle
        ppmCore: ElementDictionary = ppmElements.ppmCore
        self.coreSize: float = ppmElements.relativeCoreSize
        self.fO2: float = singleStageResults.fO2
        end = time.time()
        print("Endtime:", (end-start)/60 )

        # Output parameters that should be put in the first block of the Excel file
        if self.input.settings.PTCalcutionOption == True:
            outputParameters = {'Timestep' : i, 
                        'P (GPa)' : singleStageResults.Pressure, 
                        'T(K)' : singleStageResults.Temperature, 
                        'M/Me' : self.relativeSize, 
                        'Core Size' : self.coreSize, 
                        'Gamma Fe' : singleStageResults.gammaFe,
                        'Kd Si' : singleStageResults.KdSiResult,
                        'Kd Ni' : singleStageResults.KdNiResult,
                        'Kd O' : singleStageResults.KdOResult,
                        'fO2' : singleStageResults.fO2}
        else: 
            outputParameters = {'Timestep' : i, 
                        'P (GPa)' : singleStageResults.Pressure, 
                        'T(K)' : singleStageResults.Temperature, 
                        'M/Me' : self.relativeSize, 
                        'Core Size' : self.coreSize, 
                        'Gamma Fe' : singleStageResults.gammaFe,
                        'Kd Si' : singleStageResults.KdSiResult,
                        'Kd Ni' : singleStageResults.KdNiResult,
                        'Kd O' : singleStageResults.KdOResult,
                        'fO2' : singleStageResults.fO2}

        # Add the data to the Excel file
        self.excelWriter.AddDataToFrames(outputParameters, self.molesMantle, self.molesCore, ppmMantle, ppmCore, 0, 0)
        self.excelWriter.WriteToExcel()
        
        #Finish and save the Excel file
        self.excelWriter.WriteToExcel()

    # If the event is an impactor, this function will be called
    def SingleStageEquilibration(self, molesMantleOld, molesCoreOld):
        # Update the three relevant phases of planet mantle, impactor core and if relevant the disequilibrated impactor core
        self.molesMantle: ElementDictionary = molesMantleOld.copy()
        self.molesCore: ElementDictionary = molesCoreOld.copy()

        # Calculate fO2 of unequilibrated mantle/core
        molarFractions: MantleAndCoreDictionaries = calculateMolarFraction(self.molesMantle, self.molesCore)
        xFeOMantle = molarFractions.mantle["FeO"]
        xFeCore = molarFractions.core["Fe"]
        xFeOMW: float = 1.148 * xFeOMantle + 1.319 * xFeOMantle * xFeOMantle 
        self.fO2: float = 2*np.log10(xFeOMW/xFeCore)   
                
        Pressure: float = self.input.startingComposition.pressure
        Temperature: float = self.input.startingComposition.temperature
 
        print('Pressure:', Pressure)
        print('Temperature:', Temperature)  

        # Gamma value calculation for major elements


        # Determine which KD setting should be used, either corrected or uncorrected for activity of Fe 
        if self.input.settings.KdCorrectionEnabled:
            moleFractionCore: MantleAndCoreDictionaries = calculateMolarFraction(self.molesMantle, self.molesCore).core
            newGammaValues: CalculatedGammaValues = CalculateGammaValues(self.epsDictionary, GammaValues, Temperature, moleFractionCore)
            gammaFe: float = np.exp(newGammaValues.solvent)
            gammaAll: ElementDictionary = newGammaValues.solute
            kdValues: KdDictionary = KdValuesCorrected(Temperature, Pressure, gammaFe, gammaAll)
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
            
        return(gammaFe, Pressure, Temperature, KdSiResult, KdNiResult, KdOResult, self.fO2)
    
#Start the program using the given input file
inputData = ImportInputFile('InputFile - SingleStage.xlsx')
SingleStageCalculation = SingleStageCalculation(inputData)
SingleStageCalculation.RunSingleStage()