from dataclasses import dataclass
from typing import List

import pandas as pd
from CustomTypes import ElementDictionary
from EventsList import Event, EventList
from EventsList import Impactor

# This file contains the classes and functions for reading the input from the Excel file, ensuring it can be passed on to the program correctly

# Conditions of the events, currently only changing the PT conditions
class EventConditions :
    def __init__(self, pressure: dict[int, float], temperature: dict[int, float]):
        self.pressure: dict[int, float] = pressure
        self.temperature: dict[int, float] = temperature

# The output file names, and passing on the correct settings for the additional features for the calculations and output
class Settings:
    def __init__(self, outputName: str, KdCorrectionEnabled: bool):
        self.outputName: str = outputName
        self.KdCorrectionEnabled: bool = KdCorrectionEnabled

# Planetary starting compositions 
class PlanetStartingComposition:
    def __init__(self, mantleCompositionDict: ElementDictionary, coreCompositionDict: ElementDictionary, planetCoreSize: float, planetRelativeStartingMass: float):
        self.mantleCompositionDict: ElementDictionary = mantleCompositionDict
        self.coreCompositionDict: ElementDictionary = coreCompositionDict
        self.planetCoreSize: float = planetCoreSize
        self.planetRelativeStartingMass: float = planetRelativeStartingMass

# The main input class, passing the other classes on to the program
class Input:
    def __init__(self, eventList : EventList, settings : Settings, planetStartingComposition : PlanetStartingComposition, eventConditions : EventConditions) :
        self.eventList: EventList = eventList
        self.settings: Settings = settings
        self.planetStartingComposition: PlanetStartingComposition = planetStartingComposition
        self.timesteps: int = len(eventList.listOfEvents)
        self.eventConditions: EventConditions = eventConditions

@dataclass
class ExcelSheetData:
    settingsSheet: pd.DataFrame
    eventsSheet: pd.DataFrame
    planetStartCompSheet: pd.DataFrame
    impactorTypeSheet: pd.DataFrame
    impactorMantleSheet: pd.DataFrame
    impactorCoreSheet: pd.DataFrame

# Read the various input sheets as convert it to useable variables
def ReadInput (inputFile) -> ExcelSheetData:
    excelSheets = pd.ExcelFile(inputFile)
    settingsSheet = pd.read_excel(excelSheets, 'General settings')
    eventsSheet = pd.read_excel(excelSheets, 'Events')
    planetStartCompSheet = pd.read_excel(excelSheets, 'Planet starting composition')
    impactorTypeSheet = pd.read_excel(excelSheets, 'Impactor types')
    impactorMantleSheet = pd.read_excel(excelSheets, 'Impactor mantle compositions')
    impactorCoreSheet = pd.read_excel(excelSheets, 'Impactor core compositions')

    return ExcelSheetData(
        settingsSheet=settingsSheet,
        eventsSheet=eventsSheet,
        planetStartCompSheet=planetStartCompSheet,
        impactorTypeSheet=impactorTypeSheet,
        impactorMantleSheet=impactorMantleSheet,
        impactorCoreSheet=impactorCoreSheet
    )

# Locate the relevant information from the 'Settings' input sheet and convert it to useable variables
# Creates the Settings class
def ReadSettingsSheet(settingsSheet: pd.DataFrame) -> Settings:
    outputName = settingsSheet.iloc[0, 1]
    KdCorrectionEnabled = settingsSheet.iloc[3, 1].lower() == 'yes' #yes/no field
    return Settings(outputName, KdCorrectionEnabled)

@dataclass
class EventData:
    pressureDict: dict
    temperatureDict: dict
    impactorTypeDict: dict
    partialEqDict: dict
    equilibrateDict: dict

# Locate the relevant information from the 'Events' input sheet
def ReadEventsSheet(eventsSheet: pd.DataFrame) -> EventData:
    timestep = eventsSheet['Timestep']
    pressure = eventsSheet['Pressure (GPa)']
    temperature = eventsSheet['Temperature (K)']
    impactorType = eventsSheet['Impactor type']
    partialEq = eventsSheet['Full/partial equilibration']
    equilibrate = eventsSheet['Equilibrate (yes/no only)'] #yes/no field

    # Create dictionaries for the event conditions and impactor types, uses timestep as keys
    pressureDict = dict(zip(timestep, pressure))
    temperatureDict = dict(zip(timestep, temperature))
    impactorTypeDict = dict(zip(timestep, impactorType))
    partialEqDict = dict(zip(timestep, partialEq))
    equilibrateDict = dict(zip(timestep, equilibrate))

    return EventData(pressureDict=pressureDict, temperatureDict=temperatureDict, impactorTypeDict=impactorTypeDict, partialEqDict=partialEqDict, equilibrateDict=equilibrateDict)

# Read and convert the planetary starting data from the 'Planet starting composition' input sheet
# Creates the PlanetStartingComposition class 
def ReadPlanetStartingComposition(planetStartCompSheet) -> PlanetStartingComposition:
    mantleElement: pd.DataFrame = planetStartCompSheet['Mantle: Element/oxide']
    mantleConcentration: pd.DataFrame = planetStartCompSheet['Mantle: concentration (ppm)']
    coreElement: pd.DataFrame = planetStartCompSheet['Core: element']
    coreConcentration: pd.DataFrame = planetStartCompSheet['Core: concentration (ppm)']

    # Create dictionaries for the mantle and core compositions, uses element/oxide as keys. Remove any empty fields
    mantleCompositionDict: ElementDictionary = dict(zip(mantleElement, mantleConcentration))
    mantleCompositionDict = {k: v for k, v in mantleCompositionDict.items() if not (pd.isna(k) or pd.isna(v))}
    coreCompositionDict: ElementDictionary = dict(zip(coreElement, coreConcentration))
    coreCompositionDict = {k: v for k, v in coreCompositionDict.items() if not (pd.isna(k) or pd.isna(v))}

    # Locate the planetary core size, relative starting mass and total mass
    planetCoreSize: float = planetStartCompSheet.iloc[0, 7]
    planetRelativeStartingMass: float = planetStartCompSheet.iloc[1, 7]

    return PlanetStartingComposition(mantleCompositionDict, coreCompositionDict, planetCoreSize, planetRelativeStartingMass)

@dataclass
class ImpactorType:
    relativeMass: float
    relativeCoreSize: float

# Read data from the 'Impactor types' input sheet
# Returns dictionary with relative mass and core mass percentages for each impactor (key)
def ReadImpactorTypes(impTypeSheet: pd.DataFrame) -> dict[int, ImpactorType]:
    impactorDict: dict[int, ImpactorType] = {}

    impnumber: pd.DataFrame = impTypeSheet['Impactor number']
    relativeMass: pd.DataFrame = impTypeSheet['Relative mass percentage']
    coreMass: pd.DataFrame = impTypeSheet['Core mass percentage']

    # Create combined dictionary for the relative and core mass percentages
    for i in range(len(impnumber)):
        impactorDict[impnumber[i]] = ImpactorType(relativeMass[i], coreMass[i])

    return impactorDict

# Read the mantle compositions, either in elements or oxides, from the 'Impactor mantle compositions' input sheet. 
# Returns nested dictionary with composition (in elements/oxides) for each impactor (key)
def ReadImpMantleData(impMantleSheet: pd.DataFrame) -> dict[int, ElementDictionary]:
    elementsMantle: pd.DataFrame = impMantleSheet['Elements/oxides']
    impactMantleDict: dict[int, ElementDictionary] = {}
    for rowName in impMantleSheet[1:]:
        if rowName == 'Elements/oxides':
            continue
        if isinstance(rowName, (str)):
            break
        else:
            impactMantleDict[rowName] = dict(zip(elementsMantle, impMantleSheet[rowName]))
    return impactMantleDict

# Read the core compositions, either in elements, from the 'Impactor core compositions' input sheet. 
# Returns nested dictionary with composition (in elements/) for each impactor (key)
def ReadImpCoreData(impCoreSheet) -> dict[int, ElementDictionary]:
    elementsCore = impCoreSheet['Elements']
    impactCoreDict: dict[int, ElementDictionary] = {}
    for rowName in impCoreSheet[1:]:
        if rowName == 'Elements':
            continue
        if isinstance(rowName, (str)):
            break
        else:
            impactCoreDict[rowName] = dict(zip(elementsCore, impCoreSheet[rowName]))
    return impactCoreDict

@dataclass
class TotalImpactorData:
    relativeMass: float
    relativeCoreSize: float
    mantleConcentrationsInPPM: ElementDictionary
    coreConcentrationsInPPM: ElementDictionary

# Combine impactor information dictionaries into one callable dictionary
# Returns nested dictionaries for each impactor (key)
def CombineImpactorData(impactorInfoDict: dict[int, ImpactorType], impactorMantleDict: dict[int, ElementDictionary], impactorCoreDict: dict[int, ElementDictionary]) -> dict[int, TotalImpactorData]:
    impNumberDict: dict[int, TotalImpactorData] = {}
    for i in range(len(impactorInfoDict)):
        index: int = i + 1
        impNumberDict[index] = TotalImpactorData(
            relativeMass=impactorInfoDict[index].relativeMass,
            relativeCoreSize=impactorInfoDict[index].relativeCoreSize,
            mantleConcentrationsInPPM=impactorMantleDict[index],
            coreConcentrationsInPPM=impactorCoreDict[index]
        )
    return impNumberDict

# Creates the EventList assigning the impactor data to each event
def CreateEventList(eventData: EventData, totalImpactorData: dict[int, TotalImpactorData]) -> EventList:
    events: List[Event] = {}
    for i in range(len(eventData.pressureDict)):
        index: int = i + 1
        impactorIndex: int = eventData.impactorTypeDict[index]
        impactor: TotalImpactorData = totalImpactorData[impactorIndex]
        equilibrate: bool = eventData.equilibrateDict[index].lower() == 'yes' #yes/no field
        events[index] = Impactor(
            impactor.mantleConcentrationsInPPM,
            impactor.coreConcentrationsInPPM,
            impactor.relativeMass,
            impactor.relativeCoreSize,
            eventData.partialEqDict[index],
            equilibrate
            )
        
    return EventList(events)

# Creates the EventConditions class
def CreateEventCondtions(eventData: EventData) -> EventConditions:
    pressure: dict[int, float] = eventData.pressureDict
    temperature: dict[int, float] = eventData.temperatureDict
    return EventConditions(pressure, temperature)

# Main import function, calls all the others to read and organise the input data
def ImportInputFile(path) -> Input:
    excelInput: ExcelSheetData = ReadInput(path)
    settings: Settings = ReadSettingsSheet(excelInput.settingsSheet)
    events: EventData = ReadEventsSheet(excelInput.eventsSheet)
    startcomp: PlanetStartingComposition = ReadPlanetStartingComposition(excelInput.planetStartCompSheet)
    imptype: dict[int, ImpactorType] = ReadImpactorTypes(excelInput.impactorTypeSheet)
    mantle: dict[int, ElementDictionary] = ReadImpMantleData(excelInput.impactorMantleSheet)
    core: dict[int, ElementDictionary] = ReadImpCoreData(excelInput.impactorCoreSheet)
    totalImpData: dict[int, TotalImpactorData] = CombineImpactorData(imptype, mantle, core)
    eventList: EventList = CreateEventList(events, totalImpData)
    eventConditions: EventConditions = CreateEventCondtions(events)
    return Input(eventList, settings, startcomp, eventConditions)
