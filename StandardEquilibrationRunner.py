from dataclasses import dataclass
from CustomTypes import ElementDictionary, KdDictionary

from MidacoRunnerPlanetBuilder import MidacoKdOPlanetBuilder, MidacoPlanetBuilderResult

# Calculates the equilibrated major element composition without adjustments to the Kd values
@dataclass
class StandardEquilibrationResult:
    newMantleValues: ElementDictionary
    newICoreValues: ElementDictionary
    KdOPB: float
    KdSi: float
    KdNi: float
    isOxidised: bool

def CallStandardEquilibration(molesMantle: ElementDictionary, molesICore: ElementDictionary, T: float, P: float, kdValues: KdDictionary) -> StandardEquilibrationResult:
    result: MidacoPlanetBuilderResult = MidacoKdOPlanetBuilder(molesMantle, molesICore, T, P, kdValues)
    return StandardEquilibrationResult(result.newMantleValues, result.newICoreValues, result.KdOPB, result.KdSi, result.KdNi, isOxidised=result.isOxidised)
