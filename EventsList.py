from __future__ import annotations
from dataclasses import dataclass
from Conversions import MantleAndCoreDictionaries, deconstructCompounds, massRelativePlanet
from Conversions import coreMantlePercentage
from Conversions import calculateMoles
from CustomTypes import AtomicWeightDictionary, ElementDictionary

@dataclass
class EventResult:
    molesMantle: ElementDictionary
    ICoreToPMantle: ElementDictionary
    ICoreToPCore: ElementDictionary
    equilibrate: bool

# Imports the list of events based on the input from the Excel files
class EventList:
    def __init__(self, listOfEvents: list[Event]):
        self.listOfEvents = listOfEvents
    
    def GetEvent(self, timeStep) -> Event:
        for key in self.listOfEvents:
            if key == timeStep :
                return self.listOfEvents[key]
        raise Exception("No event")

# Class for the events from the events list. In the current version the only events are impacts     
class Event:
    def DoEvent(self, molesMantle):
        pass

# Class for the definition and execution of impact events 
class Impactor(Event):
    # Initialises the impactor with relative mass, core size and potential partial equilibration
    # Converts the ppm concentrations from the input to moles 
    def __init__(self,
            impactorMantle: ElementDictionary,
            impactorCore: ElementDictionary,
            relativeMass: float,
            relativeCoreSize: float,
            partialEquilibrationFactor: float,
            equilibrate: bool
    ):
        super().__init__()
        relativeMassBothPhases: MantleAndCoreDictionaries = massRelativePlanet(relativeMass, impactorMantle, impactorCore)
        percentageCoreMantle: MantleAndCoreDictionaries = coreMantlePercentage(relativeCoreSize, relativeMassBothPhases.mantle, relativeMassBothPhases.core)
        updatedAtomicWeights: AtomicWeightDictionary = deconstructCompounds(impactorMantle, impactorCore)
        calculatedMoles: MantleAndCoreDictionaries = calculateMoles(percentageCoreMantle.mantle, percentageCoreMantle.core, updatedAtomicWeights) 

        self.impactorMantleMoles: ElementDictionary = calculatedMoles.mantle
        self.impactorCoreMoles: ElementDictionary = calculatedMoles.core
        self.ICoreToPMantle: ElementDictionary = {}
        self.ICoreToPCore: ElementDictionary = {}
        self.partialEquilibration: float = partialEquilibrationFactor
        self.relativeMass: float = relativeMass
        self.equilibrate: bool = equilibrate
        
    # Adds the impactor mantle to the planetary mantle, and if necessary, the part of the impactor core that does not participate in equilibration to the planet core
    def DoEvent(self, molesMantle) -> EventResult:
        for key in self.impactorMantleMoles:
            if key in molesMantle:
                molesMantle[key] += self.impactorMantleMoles[key]
            else :
                molesMantle[key] = self.impactorMantleMoles[key]
    
        for key in self.impactorCoreMoles: 
            self.ICoreToPMantle[key] = self.impactorCoreMoles[key] * self.partialEquilibration

            if self.partialEquilibration != 1:
                self.ICoreToPCore[key] = self.impactorCoreMoles[key] * (1 - self.partialEquilibration)
            
        # If there is no impactor core, or equilibration is turned off for a different reason, add the entire impactor core to the planetary core
        if not self.equilibrate:
            for key in self.ICoreToPMantle:
                if key in molesMantle:
                    molesMantle[key] += self.ICoreToPMantle[key]
                elif key == 'Fe':
                    molesMantle['FeO'] += self.ICoreToPMantle[key]
                elif key == 'Ni':
                    molesMantle['NiO'] += self.ICoreToPMantle[key]
                elif key == 'Si':
                    molesMantle['SiO2'] += self.ICoreToPMantle[key]
                elif key == 'O':
                    continue
                else:
                    molesMantle[key] = self.ICoreToPMantle[key]
            self.ICoreToPCore[key] = {}
            self.ICoreToPMantle[key] = {}

        return EventResult(molesMantle=molesMantle, ICoreToPMantle=self.ICoreToPMantle, ICoreToPCore=self.ICoreToPCore, equilibrate=self.equilibrate)