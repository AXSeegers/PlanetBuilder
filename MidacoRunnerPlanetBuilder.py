import numpy as np
import midacoPB

from CustomTypes import ElementDictionary
from dataclasses import dataclass
from MidacoRunnerFrost import MidacoKdOFrost


midacoKey = b'MIDACO_LIMITED_VERSION___[CREATIVE_COMMONS_BY-NC-ND_LICENSE]'
tolerance = 1e-8
np.set_printoptions(legacy='1.25')

@dataclass
class MidacoPlanetBuilderResult:
    newMantleValues: ElementDictionary
    newICoreValues: ElementDictionary
    KdOPB: float
    KdSi: float
    KdNi: float
    isOxidised: bool = False
    maxTimeReached: bool = False
  
def makeProblemFunction(molesMantle : ElementDictionary, molesICore : ElementDictionary, KdSi : float, KdNi : float, P : float, T : float):
    FeO = molesMantle["FeO"]
    SiO2 = molesMantle["SiO2"]
    NiO = molesMantle["NiO"]
    OtherMajorOxides = molesMantle["Al2O3"] + molesMantle["MgO"] + molesMantle["CaO"]

    Fe = molesICore["Fe"]
    Si = molesICore["Si"]
    Ni = molesICore["Ni"]
    O = molesICore["O"]

    def problemFunction(x):
        current_feo = x[0] # Current FeO value from optimization variable X
        f = [0.0]*1 # Initialize array for objectives F(X)
        g = [0.0]*8 # Initialize array for constraints G(X)

        # Objective functions F(X)
        FeNew = FeO + Fe - current_feo
        NiONew = current_feo * (NiO + Ni) / ((FeO + Fe - current_feo) * KdNi + current_feo) # Eq. 22
        NiNew = NiO + Ni - NiONew # Eq. 21

        # SiO2 new calculations as derived in Eq 26 - 36
        A = SiO2 + Si
        B = FeO + NiO + 2 * SiO2 + O - current_feo - NiONew        
        C = FeNew + NiNew
        D = current_feo + NiONew + OtherMajorOxides
        E = A + B + C

        SiO2NewPart1 = 3 * np.power(current_feo,2) - (KdSi * np.power(FeNew,2))
        SiO2NewPart2 = -(3 * np.power(current_feo,2) * A + np.power(current_feo,2) * E + np.power(FeNew,2) * D * KdSi)
        SiO2NewPart3 = np.power(current_feo,2) * A * E
        SiO2New = (-SiO2NewPart2 - np.sqrt(np.power(SiO2NewPart2,2) - 4 * SiO2NewPart1 * SiO2NewPart3))/(2 * SiO2NewPart1)

        SiNew = SiO2 + Si - SiO2New # Eq. 37
        ONew = FeO + NiO + 2 * SiO2 + O - current_feo - NiONew - 2 * SiO2New # Eq.38
        
        # Oxidation check, when the result is positive, the impactor core is no longer considered a metal liquid, but oxide liquid instead (Section 3.3)
        isOxidised = ONew - FeNew

        # Only major elements are used for these 'molar fraction' calculations, but the impact of trace elements is negligible for this purpose
        XFeONew = current_feo / (current_feo + NiONew + SiO2New + OtherMajorOxides)
        xFeOMW = 1.1478 * XFeONew + 1.3189 * XFeONew * XFeONew

        # Calculate the total core mass, the effect of trace elements is negligible for this purpose
        totalCore = FeNew + NiNew + ONew + SiNew

        # If there is almost no core, or the FeO in MW is below tolerance value of 1e-8, equilibration is not possible
        if totalCore < tolerance or xFeOMW < tolerance:
            KdOPB = 1e12
            KdOFrost = 0.0
        else:
            KdOPB = (FeNew * ONew) / (xFeOMW * np.power(totalCore, 2))
            KdOFrost = MidacoKdOFrost(xFeOMW, P, T) #Call Midaco Frost function for thermodynamic Kd

        # Midaco minimizes the difference between the two KdO values
        f[0] = abs(KdOPB - KdOFrost)
        # Midaco constraints
        g[0] = NiONew - tolerance
        g[1] = FeNew - tolerance
        g[2] = NiNew - tolerance
        g[3] = SiO2New - tolerance
        g[4] = SiNew - tolerance
        g[5] = ONew - tolerance
        g[6] = XFeONew - tolerance
        g[7] = -isOxidised

        return f, g
    return problemFunction
        
def getMidacoProblem(startFeO, max):
    # Midaco settings. See midaco documentation
    problem = {}
    problem['o'] = 1 # Number of objectives
    problem['n'] = 1 # Number of variables
    problem['ni'] = 0 # Number of integer variables
    problem['m'] = 8 # Number of constraints
    problem['me'] = 0 # Number of Equality Constraints
    problem['xl'] = [tolerance] # Minimum value of variables
    problem['xu'] = [max] # Maximum value of variables
    problem['x'] = [startFeO] # Starting value for variables
    return problem

def getMidacoOptions():
    # Midaco options. See midaco documentation
    option  = {}
    option['maxeval'] = 1000000 # Max iterations
    option['maxtime'] = 60*60  # Max time in seconds
    option['printeval'] = 1000 # Printing interval
    option['save2file'] = 0 # Midaco logging
    option['param1']  = 0.0  # ACCURACY  
    option['param2']  = 0.0  # SEED  
    option['param3']  = 1e-4 # FSTOP - allowed absolute difference between KdOPB and KdOFrost
    option['param4']  = 5  # ALGOSTOP  
    option['param5']  = 0.0  # EVALSTOP  
    option['param6']  = 0.0  # FOCUS  
    option['param7']  = 0.0  # ANTS  
    option['param8']  = 0.0  # KERNEL  
    option['param9']  = 0.0  # ORACLE  
    option['param10'] = 0.0  # PARETOMAX
    option['param11'] = 0.0  # EPSILON  
    option['param12'] = 0.0  # BALANCE
    option['param13'] = 0.0  # CHARACTER
    option['parallel'] = 1 # Serial: 0 or 1, Parallel: 2,3,4,5,6,7,8...
    return option


def MidacoKdOPlanetBuilder(molesMantle, molesICore, T, P, KdValues) -> MidacoPlanetBuilderResult:
    currentFeO = molesMantle["FeO"]
    KdSi = KdValues["Si"]
    KdNi = KdValues["Ni"]

    #Call and run Midaco
    problem = getMidacoProblem(currentFeO, currentFeO + molesICore['Fe'])
    problem['@'] = makeProblemFunction(molesMantle=molesMantle, molesICore=molesICore, KdSi=KdValues["Si"], KdNi=KdValues["Ni"], P=P, T=T)
    options = getMidacoOptions()
    midacoResult = midacoPB.run(problem, options, midacoKey)
    bestFeO = midacoResult['x'][0]  # Best FeO value found by Midaco
    result: MidacoPlanetBuilderObjectiveResult = objective(bestFeO, molesMantle, molesICore, KdNi, KdSi, P, T)

    # If maximum time or maximum evaluations is reached, return the best result with a flag
    if midacoResult['iflag'] == 1 or midacoResult['iflag'] == 2:
        return MidacoPlanetBuilderResult(newMantleValues=result.newMantleValues, newICoreValues=result.newICoreValues, KdOPB=result.KdOPB, KdSi=KdSi, KdNi=KdNi, maxTimeReached = True )

    # If the result is oxidised, add the oxidised impactor 'core' to the planetary mantle. Sets all Kd values to 1
    if midacoResult['iflag'] == 3 or midacoResult['iflag'] == 4 or result.isOxidised == True:     
        print(f"Metal liquid is too oxidized. Adding impactor core to mantle.")
        molesICore["FeO"] = molesICore["Fe"]
        molesICore["SiO2"] = molesICore["Si"]
        molesICore["NiO"] = molesICore["Ni"]
            
        del molesICore["Fe"]
        del molesICore["Si"]   
        del molesICore["Ni"]
        del molesICore["O"]
        
        newMantleValues = molesMantle
        for key in molesICore:
            newMantleValues[key] += molesICore[key]
        newICoreValues = {}
        KdSi = 1
        KdNi = 1
        KdOPB = 1

        return MidacoPlanetBuilderResult(newMantleValues=newMantleValues, newICoreValues=newICoreValues, KdOPB=KdOPB, KdSi=KdSi, KdNi=KdNi, isOxidised = True)
    
    return MidacoPlanetBuilderResult(
        newMantleValues=result.newMantleValues,
        newICoreValues=result.newICoreValues,
        KdOPB=result.KdOPB,
        KdSi=KdSi,
        KdNi=KdNi,
    )

@dataclass
class MidacoPlanetBuilderObjectiveResult:
    newMantleValues: ElementDictionary
    newICoreValues: ElementDictionary
    KdOPB: float
    isOxidised: bool

# This function runs once at the end with the equilibrated composition
def objective(current_feo, molesMantle, molesICore, KdNi, KdSi, P, T) -> MidacoPlanetBuilderObjectiveResult:
    FeO = molesMantle["FeO"]
    SiO2 = molesMantle["SiO2"]
    NiO = molesMantle["NiO"]
    OtherMajorOxides = molesMantle["Al2O3"] + molesMantle["MgO"] + molesMantle["CaO"]
    
    Fe = molesICore["Fe"]
    Si = molesICore["Si"]
    Ni = molesICore["Ni"]
    O = molesICore["O"]

    FeNew = FeO + Fe - current_feo # Eq. 17
    NiONew = current_feo * (NiO + Ni) / ((FeO + Fe - current_feo) * KdNi + current_feo)  # Eq. 22
    NiNew = NiO + Ni - NiONew # Eq. 21

    # SiO2 new calculations as derived in Eq 26 - 36
    A = SiO2 + Si
    B = FeO + NiO + 2 * SiO2 + O - current_feo - NiONew        
    C = FeNew + NiNew
    D = current_feo + NiONew + OtherMajorOxides
    E = A + B + C
    SiO2NewPart1 = 3 * np.power(current_feo,2) - (KdSi * np.power(FeNew,2))
    SiO2NewPart2 = -(3 * np.power(current_feo,2) * A + np.power(current_feo,2) * E + np.power(FeNew,2) * D * KdSi)
    SiO2NewPart3 = np.power(current_feo,2) * A * E
    SiO2New = (-SiO2NewPart2 - np.sqrt(np.power(SiO2NewPart2,2) - 4 * SiO2NewPart1 * SiO2NewPart3))/(2 * SiO2NewPart1)

    SiNew = SiO2 + Si - SiO2New  # Eq. 37
    ONew = FeO + NiO + 2 * SiO2 + O - current_feo - NiONew - 2 * SiO2New # Eq. 38
   
    # Oxidation check, when the result is positive, the impactor core is no longer considered a metal liquid, but oxide liquid instead (Section 3.3)
    isOxidised = ONew - FeNew

    # Only major elements are used for these 'molar fraction' calculations, but the impact of trace elements is negligible for this purpose
    xFeONew = current_feo / (current_feo + NiONew + SiO2New + OtherMajorOxides)
    xFeOMW = 1.1478 * xFeONew + 1.3189 * xFeONew * xFeONew

    #Calculate the KdO value once more for export
    KdOPB = (FeNew * ONew) / (xFeOMW * np.power((FeNew + NiNew + ONew + SiNew),2))

    newMantleValues = molesMantle.copy()
    newMantleValues.update({
        "FeO" : current_feo,
        "SiO2" : SiO2New,
        "NiO" : NiONew
    })
    
    newICoreValues = molesICore.copy()
    newICoreValues.update({
        "Fe" : FeNew,
        "Si" : SiNew,
        "O" : ONew,
        "Ni" : NiNew
    })

    return MidacoPlanetBuilderObjectiveResult(
        newMantleValues=newMantleValues,
        newICoreValues=newICoreValues,
        KdOPB=KdOPB,
        isOxidised=isOxidised
    )
