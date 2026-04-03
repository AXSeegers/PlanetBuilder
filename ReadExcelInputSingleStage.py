from dataclasses import dataclass
import pandas as pd
from CustomTypes import ElementDictionary

@dataclass
class Settings:
    outputName: str
    KdCorrectionEnabled: bool

@dataclass
class StartingComposition:
    mantleCompositionDict: ElementDictionary
    coreCompositionDict: ElementDictionary
    planetCoreSize: float
    planetRelativeStartingMass: float
    pressure: float
    temperature: float

@dataclass
class Input:
    settings: Settings
    startingComposition: StartingComposition
        

def ReadInput (inputFile):
    excelSheets = pd.ExcelFile(inputFile)
    settingsSheet = pd.read_excel(excelSheets, 'General settings')
    StartCompSheet = pd.read_excel(excelSheets, 'Starting composition')

    return(settingsSheet, StartCompSheet)

def ReadSettingsSheet(settingsSheet) -> Settings:
    outputName = settingsSheet.iloc[0, 1]
    KdCorrectionEnabled = settingsSheet.iloc[3, 1].lower() == 'yes' #yes/no field

    return Settings(outputName, KdCorrectionEnabled)

def ReadPlanetStartingComposition(planetStartCompSheet) -> StartingComposition:
    mantleElement: pd.DataFrame = planetStartCompSheet['Mantle: Element/oxide']
    mantleConcentration: pd.DataFrame = planetStartCompSheet['Mantle: concentration (ppm)']
    coreElement: pd.DataFrame = planetStartCompSheet['Core: element']
    coreConcentration: pd.DataFrame = planetStartCompSheet['Core: concentration (ppm)']

    mantleCompositionDict: ElementDictionary = dict(zip(mantleElement, mantleConcentration))
    mantleCompositionDict = {k: v for k, v in mantleCompositionDict.items() if not (pd.isna(k) or pd.isna(v))}
    coreCompositionDict: ElementDictionary = dict(zip(coreElement, coreConcentration))
    coreCompositionDict = {k: v for k, v in coreCompositionDict.items() if not (pd.isna(k) or pd.isna(v))}

    planetCoreSize: float = planetStartCompSheet.iloc[0, 7]
    planetRelativeStartingMass: float = planetStartCompSheet.iloc[1, 7]

    pressure: float = planetStartCompSheet.iloc[3, 7]
    temperature: float = planetStartCompSheet.iloc[4, 7]

    return StartingComposition(mantleCompositionDict, coreCompositionDict, planetCoreSize, planetRelativeStartingMass, pressure, temperature)

def ImportInputFile(path):
    excelInput = ReadInput(path)
    settings = ReadSettingsSheet(excelInput[0])
    startcomp = ReadPlanetStartingComposition(excelInput[1])

    return Input(settings, startcomp)