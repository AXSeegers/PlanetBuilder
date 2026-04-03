import numpy as np
import warnings
import midacoFrost as midaco
warnings.filterwarnings("error")
warnings.filterwarnings("ignore", category=ResourceWarning)

tolerance = 1e-8
midacoKey = b'MIDACO_LIMITED_VERSION___[CREATIVE_COMMONS_BY-NC-ND_LICENSE]'

np.set_printoptions(legacy='1.25')

def make_problem_function(Mu0FeOCore : float, MuFeOMantle : float, WFeOFe : float, WFeFeO : float, VFeOCore : float, R : float, T : float):
    def problem_function(X):
        xFeOCoreGuess = X[0] # Current FeO value from optimization variable X
        f = [0.0]*1 # Initialize array for objectives F(X)
        g = [0.0]*1 # Initialize array for constraints G(X)

        # Calculate the mu of FeO in the core: Eq. 4 and 6 from Frost et al., (2010)
        RTGammaFeOCore = np.power((1 - xFeOCoreGuess), 2) * (WFeOFe + 2 * (WFeFeO - WFeOFe) * xFeOCoreGuess)
        MuFeOCore = Mu0FeOCore + R * T * np.log(xFeOCoreGuess) + RTGammaFeOCore + VFeOCore

        # Calculate the difference in chemical potential (mu) of FeO between mantle and impactor core
        deltaMuFeO = MuFeOMantle - MuFeOCore

        f[0] = abs(deltaMuFeO)

        g[0] = xFeOCoreGuess - tolerance

        return f, g
    return problem_function

def getMidacoProblem(xFeOCoreGuess):
    # Midaco settings. See midaco documentation
    problem = {}
    problem['o'] = 1 # Number of objectives
    problem['n'] = 1 # Number of variables
    problem['ni'] = 0 # Number of integer variables
    problem['m'] = 1 # Number of constraints
    problem['me'] = 0 # Number of Equality Constraints
    problem['xl'] = [tolerance] # Minimum value of variables - .00000001
    problem['xu'] = [1-tolerance] # Maximum value of variables - .99999999
    problem['x'] = [xFeOCoreGuess] # Starting value for variables -  first guess
    return problem

def getMidacoOptions():
    # Midaco options. See midaco documentation
    option  = {}
    option['maxeval'] = 1000000 # Max iterations
    option['maxtime'] = 60*20  # Max time in seconds
    option['printeval'] = 0 # Printing interval
    option['save2file'] = 1 # Midaco logging
    option['param1']  = 0.0  # ACCURACY  
    option['param2']  = 0.0  # SEED  
    option['param3']  = 1e-4  # FSTOP - allowed absolute difference between KdOPB and KdOFrost
    option['param4']  = 0.0  # ALGOSTOP  
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

def MidacoKdOFrost(xFeOMW : float, P : float, T : float) -> float:
    R = 8.314 #Gas constant in J/molK

    # Values from Table 3 in Frost et al., (2010)
    kPrimeCore = 4.397
    kPrimeMantle = 4.3 # Volume coefficients
    v0Core = 1.3244 #J/bar
    v0Mantle = 1.225 # Thermal expansion coefficients
    a0Core = 4.923E-5
    a1Core = 2.968E-9
    a2Core = -0.0806
    a3Core = -0.0014437
    a0Mantle = 3.481E-5
    a1Mantle = 2.968E-9
    a2Mantle = -0.0806
    a3Mantle = -0.0014437

    XFeOCoreStart = 0.0001 #arbitrary starting value

    # Equations from Table 3 in Frost et al., (2010)
    Mu0FeOMantle = -279318 + 252.848 * T - 46.12826 * T * np.log(T) - 0.0057402984 * np.power(T,2)
    Mu0FeOCore = Mu0FeOMantle + 34008 - 20.969 * T

    vTMantle =   v0Mantle * np.exp(a0Mantle  * (T-298) + 0.5 * a1Mantle  * (np.power(T,2) - np.power(298,2)) 
                             - a2Mantle  * (1/T - 1/298) + a3Mantle  * (np.log(T) - np.log(298))) 
    vTCore = v0Core * np.exp(a0Core * (T-298) + 0.5 * a1Core * (np.power(T,2) - np.power(298,2)) 
                             - a2Core * (1/T - 1/298) + a3Core * (np.log(T) - np.log(298)))
    
    k0Mantle = 1.5E6 - 264.0 * (T - 298) + 0.01906 * (T - 298) * (T - 298) 
    k0Core = 802655 - 100.0 * (T - 298)

    VFeOMantle  = vTMantle * (k0Mantle /(kPrimeMantle -1)) * (np.power(1 + kPrimeMantle / k0Mantle * P*1E4, (kPrimeMantle -1) / kPrimeMantle) -1) 
    VFeOCore =  vTCore * (k0Core /(kPrimeCore -1)) * (np.power(1 + kPrimeCore / k0Core * P*1E4, (kPrimeCore - 1) / kPrimeCore) -1)
    WFeOFe =  135943.0-31.122*T-0.0596*P*1E4 
    WFeFeO = 83307.0-8.978*T-0.096*P*1E4 

    #Mg rich mantle: Eq. 12 from Frost et al., (2010)
    WgFeOMantle = 11000 + 0.011*P*1E4

    #Mg rich mantle: Eq. 11 from Frost et al., (2010)
    RTGammaFeOMantle = WgFeOMantle * np.power((1-xFeOMW), 2)

    # Calculate the mu of FeO in the mantle: Eq. 5 from Frost et al., (2010)
    MuFeOMantle = Mu0FeOMantle + R*T*np.log(xFeOMW) + RTGammaFeOMantle + VFeOMantle

    #Call and run Midaco
    problem = getMidacoProblem(XFeOCoreStart)
    problem['@'] = make_problem_function(Mu0FeOCore, MuFeOMantle, WFeOFe, WFeFeO, VFeOCore, R, T)
    options = getMidacoOptions()
    midacoResult = midaco.run(problem, options, midacoKey)

    if midacoResult['iflag'] == 1 or midacoResult['iflag'] == 3:
        print(f"Feasible solution, but no convergence in mu (chemical potential) between mantle and core in thermodynamic KdO model. Check manually. See Frost et al. (2009)")
        raise Exception("Midaco did not converge to a solution within the specified time or evaluations.")
    if midacoResult['iflag'] == 2 or midacoResult['iflag'] == 4:
        print(f"Infeasible solution, xFeO Core is out of bounds")
        raise Exception("Midaco did not find a feasible solution within the specified time or evaluations.")

    bestxFeOCore = midacoResult['x'][0]  # Best xFeOCore value found by Midaco
    KdOFrost = bestxFeOCore / (np.power((1+bestxFeOCore),2) * xFeOMW) # This thermodynamically consistent KdO is derived from Frost et al., (2010); Rubie et al., (2011), (2015).

    return KdOFrost