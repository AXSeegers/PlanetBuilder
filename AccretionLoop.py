from dataclasses import dataclass
from typing import Any

import numpy as np
import time
import warnings

from Conversions import CompositionInPpm, MantleAndCoreDictionaries, calculateRelativeMass
from Conversions import calculateMoles, calculateMolarFraction, calculateMolesToPPM
from Conversions import deconstructCompounds
from CustomTypes import AtomicWeightDictionary, ElementDictionary, KdDictionary
from EventsList import Event, EventResult, Impactor
from GammaValues import GammaValues
from KdValues import KdValuesCorrected
from KdValues import KdValuesUncorrected
from MetalActivityCalculator import CalculateGammaValues, CalculatedGammaValues, CreateEpsDict, ElementOnElementInteraction, ReadEpsValues
from MetalActivityCorrectionRunner import CallKdCorrectionEquilibration, MetalActivityResult
from MinorElements import CalculateMinorElements
from OutputToExcel import ExcelWriter
from OutputToExcelMidaco import ExcelWriterMidaco
from ReadExcelInput import Input
from StandardEquilibrationRunner import CallStandardEquilibration, StandardEquilibrationResult

warnings.filterwarnings("ignore", category=DeprecationWarning)
np.set_printoptions(legacy = '1.25')

@dataclass
class ImpactorResult:
    gammaFe: float
    pressure: float
    temperature: float
    KdSiResult: float
    KdNiResult: float
    KdOResult: float
    fO2: float
    equilibrate: bool = True

# Main class of the program, calls all other necessary functions
class PlanetBuilder:
    def __init__ (self, input: Input):
        elementsMantle: ElementDictionary = input.planetStartingComposition.mantleCompositionDict
        elementsCore: ElementDictionary = input.planetStartingComposition.coreCompositionDict
        startingRelativeSize: float = input.planetStartingComposition.planetRelativeStartingMass
        startingCoreSize: float = input.planetStartingComposition.planetCoreSize
        startingRelativeMass: MantleAndCoreDictionaries = calculateRelativeMass(elementsMantle, elementsCore, startingRelativeSize, startingCoreSize)
        massCore: ElementDictionary = startingRelativeMass.core
        massMantle: ElementDictionary = startingRelativeMass.mantle
        self.updatedAtomicWeights: AtomicWeightDictionary = deconstructCompounds(elementsMantle, elementsCore)
        molesStart : MantleAndCoreDictionaries = calculateMoles(massMantle, massCore, self.updatedAtomicWeights)

        self.input: Input = input
        self.relativeSize: float = startingRelativeSize
        self.molesMantle: ElementDictionary = molesStart.mantle.copy()
        self.molesCore: ElementDictionary = molesStart.core.copy()
        self.coreSize: float = startingCoreSize
        self.excelWriter: ExcelWriter = ExcelWriter(input)
        self.midacoWriter: ExcelWriterMidaco = ExcelWriterMidaco(input)

        epsValues = ReadEpsValues()
        self.epsDictionary: dict[ElementOnElementInteraction, float] = CreateEpsDict(epsValues)

        
    def RunAccretionSteps(self):
        i: int = 0
        
        while i < self.input.timesteps:
            start: float = time.time()
            i += 1
            print(i)

            event: Event = self.input.eventList.GetEvent(i)

            # Store planetary compositions before event
            molesMantleOld: ElementDictionary = {}
            for key in self.molesMantle:
                molesMantleOld[key] = self.molesMantle[key]

            molesCoreOld: ElementDictionary = {}
            for key in self.molesCore:
                molesCoreOld[key] = self.molesCore[key]
    
            # If the event is an impactor, add and calculate the new compositions and conditions
            # In this version of PlanetBuilder, the only events are impactors, but in the future others could be added here as well
            if isinstance(event, Impactor): 
                impactorResult: ImpactorResult = self.DoImpactor(event, i)

            # Calculate concentrations of the new compositions in ppm
            if impactorResult.equilibrate:
                ppmElements: CompositionInPpm = calculateMolesToPPM(self.molesMantle, self.molesCore, self.updatedAtomicWeights)
                ppmMantle: ElementDictionary = ppmElements.ppmMantle
                ppmCore: ElementDictionary = ppmElements.ppmCore
                self.coreSize: float = ppmElements.relativeCoreSize
                ppmICore: ElementDictionary = calculateMolesToPPM(self.molesMantle, self.storeMolesICore, self.updatedAtomicWeights).ppmCore
                self.fO2: float = impactorResult.fO2
                end: float = time.time()
                print("Endtime:", (end-start)/60, "minutes")
            if impactorResult.equilibrate == False:
                    ppmElements: CompositionInPpm = calculateMolesToPPM(self.molesMantle, self.molesCore, self.updatedAtomicWeights)
                    ppmMantle: ElementDictionary = ppmElements.ppmMantle
                    ppmCore: ElementDictionary = ppmElements.ppmCore
                    self.coreSize: float = ppmElements.relativeCoreSize
                    ppmICore: ElementDictionary = self.storeMolesICore.copy()
                    self.fO2: float = impactorResult.fO2
                    end: float = time.time()
                    print("Endtime:", (end-start)/60, "minutes")

            # Output parameters that should be put in the first information block of the Excel file
            outputParameters: dict[str,Any] = {'Timestep' : i, 
                        'P (GPa)' : impactorResult.pressure, 
                        'T(K)' : impactorResult.temperature, 
                        'M/Me' : self.relativeSize, 
                        'Core Size' : self.coreSize, 
                        'Gamma Fe' : impactorResult.gammaFe,
                        'Kd Si' : impactorResult.KdSiResult,
                        'Kd Ni' : impactorResult.KdNiResult,
                        'Kd O' : impactorResult.KdOResult,
                        'fO2' : impactorResult.fO2}
            
            # Add the data to the Excel file
            self.excelWriter.AddDataToFrames(outputParameters, self.molesMantle, self.molesCore, ppmMantle, ppmCore, self.storeMolesICore, ppmICore)
            self.excelWriter.WriteToExcel()

        #Finish program and write last time
        self.excelWriter.WriteToExcel()


    # If the event is an impactor, this function will be called
    def DoImpactor(self, event : Impactor, timestep: int) -> ImpactorResult:
        # Calculate the new mantle composition after impact (old planetary mantle + impactor mantle)
        # If applicable: split the impactor core into part that equilibrates with the planetary mantle, 
        #       and portion that's in disequilibration and should be added to the planetary core
        currentEvent: EventResult = event.DoEvent(self.molesMantle)
        
        # Add atomic weights for elements that are introduced by the impactors and are not present in the planet yet
        for key in currentEvent.molesMantle:
            if not key in self.updatedAtomicWeights:
                self.updatedAtomicWeights[key] = deconstructCompounds({key: currentEvent.molesMantle[key]}, {}).get(key, 0)
        for key in currentEvent.ICoreToPMantle:
            if not key in self.updatedAtomicWeights:
                self.updatedAtomicWeights[key] = deconstructCompounds({}, {key: currentEvent.ICoreToPMantle[key]}).get(key, 0)
        for key in currentEvent.ICoreToPCore:
            if not key in self.updatedAtomicWeights:
                self.updatedAtomicWeights[key] = deconstructCompounds({}, {key: currentEvent.ICoreToPCore[key]}).get(key, 0)

        # Update the relative size of the planet with the impactor
        self.relativeSizeOld: float = self.relativeSize        
        self.relativeSize += event.relativeMass

        # Pressure and temperature associated with the event
        Pressure: float = self.input.eventConditions.pressure[timestep]
        Temperature: float = self.input.eventConditions.temperature[timestep]
        print('Pressure:', Pressure)
        print('Temperature:', Temperature)  

        # Update the planet mantle, impactor core that equilibrates and if necessary the disequilibrated impactor core
        self.molesMantle: ElementDictionary = currentEvent.molesMantle

        if not currentEvent.equilibrate:
             # Calculate the new fO2
            molarFractions: MantleAndCoreDictionaries = calculateMolarFraction(self.molesMantle, self.molesCore)
            xFeOMantle = molarFractions.mantle["FeO"]
            xFeCore = molarFractions.core["Fe"]
            xFeOMW: float = 1.148 * xFeOMantle + 1.319 * xFeOMantle * xFeOMantle 
            self.fO2: float = 2*np.log10(xFeOMW/xFeCore)
            self.storeMolesICore: ElementDictionary = self.molesCore.copy()
            for key in self.storeMolesICore:
                self.storeMolesICore[key] = 0

            return ImpactorResult(gammaFe=1, pressure=Pressure, temperature=Temperature, KdSiResult=0, KdNiResult=0, KdOResult=0, fO2=self.fO2, equilibrate=False)
        
        molesICore: ElementDictionary = currentEvent.ICoreToPMantle

        molesICoreToPCore: ElementDictionary = currentEvent.ICoreToPCore
        self.storeMolesICore: ElementDictionary = self.molesCore.copy()

        # Add the disequilibrated portion of the impactor core to the planet core
        for key in molesICoreToPCore:
            if key in self.molesCore:
                self.molesCore[key] += molesICoreToPCore[key]
            else:
                self.molesCore[key] = molesICoreToPCore[key]

        # Calculate the new equilibrated major element composition
        # Kd Correction on: the Kd values are corrected for the activity of Fe in metal liquid 
        if self.input.settings.KdCorrectionEnabled:
            moleFractionCore: MantleAndCoreDictionaries = calculateMolarFraction(self.molesMantle, molesICore).core
            newGammaValues: CalculatedGammaValues = CalculateGammaValues(self.epsDictionary, GammaValues, Temperature, moleFractionCore)
            gammaFe: float = np.exp(newGammaValues.solvent)
            gammaAll: ElementDictionary = newGammaValues.solute
            kdValues: KdDictionary = KdValuesCorrected(Temperature, Pressure, gammaFe, gammaAll)
            solverData: MetalActivityResult = CallKdCorrectionEquilibration(self.molesMantle, molesICore, Temperature, Pressure, kdValues, self.updatedAtomicWeights, self.epsDictionary, timestep, self.midacoWriter)
        else:
            gammaFe: float = 1
            kdValues: KdDictionary = KdValuesUncorrected(Temperature, Pressure)
            solverData: StandardEquilibrationResult = CallStandardEquilibration(self.molesMantle, molesICore, Temperature, Pressure, kdValues)

        KdOResult: float = solverData.KdOPB
        KdSiResult: float = solverData.KdSi
        KdNiResult: float = solverData.KdNi
        isOxidised: bool = solverData.isOxidised

        # Save solver data, regardless of which solver was used and add to appropriate phases
        newMantleData: ElementDictionary = solverData.newMantleValues
        for key in newMantleData:
            self.molesMantle[key] = newMantleData[key]   

        # If impactor core is not oxidised, update the impactor core composition with the new major element values from the solver
        newICoreData: ElementDictionary = solverData.newICoreValues
        if not isOxidised:
            for key in newICoreData:
                molesICore[key] = newICoreData[key]
        else:
            molesICore = newICoreData

        # Derive new KD values for the updated composition
        if self.input.settings.KdCorrectionEnabled and not isOxidised:
            moleFractionCore: ElementDictionary = calculateMolarFraction(self.molesMantle, molesICore).core
            afterSolverGammaValues: CalculatedGammaValues = CalculateGammaValues(self.epsDictionary, GammaValues, Temperature, moleFractionCore)
            afterSolverGammaFe: float = np.exp(afterSolverGammaValues.solvent)
            afterSolverGammaAll: ElementDictionary = afterSolverGammaValues.solute
            kdValues: KdDictionary = KdValuesCorrected(Temperature, Pressure, afterSolverGammaFe, afterSolverGammaAll)

        # If the impactor core is not oxidised, calculate the new minor element compositions and add the impactor core to the planetary core
        if not isOxidised:
            minorElements: MantleAndCoreDictionaries = CalculateMinorElements(self.molesMantle, molesICore, kdValues) 
            newMantleMinor: ElementDictionary = minorElements.mantle
            newICoreMinor: ElementDictionary = minorElements.core
            for key in newMantleMinor:
                self.molesMantle[key] = newMantleMinor[key]
            for key in newICoreMinor:
                molesICore[key] = newICoreMinor[key]
                self.storeMolesICore[key] = newICoreMinor[key]
            for key in molesICore:
                if key in self.molesCore:
                    self.molesCore[key] += molesICore[key]  
                else:
                    self.molesCore[key] = molesICore[key]
                self.storeMolesICore[key] = molesICore[key]

        # Calculate the new fO2
        molarFractions: MantleAndCoreDictionaries = calculateMolarFraction(self.molesMantle, self.molesCore)
        xFeOMantle = molarFractions.mantle["FeO"]
        xFeCore = molarFractions.core["Fe"]
        xFeOMW: float = 1.148 * xFeOMantle + 1.319 * xFeOMantle * xFeOMantle 
        self.fO2: float = 2*np.log10(xFeOMW/xFeCore)    

        return ImpactorResult(
            gammaFe=gammaFe,
            pressure=Pressure,
            temperature=Temperature, 
            KdSiResult=KdSiResult,
            KdNiResult=KdNiResult,
            KdOResult=KdOResult,
            fO2=self.fO2
        )
