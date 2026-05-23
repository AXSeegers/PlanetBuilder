# PlanetBuilder
## Introduction

PlanetBuilder 1.0 is a free-to-use tool for modelling the differentiation of elements during planetary core formation processes. Adjusting the conditions and compositions of both the planetary body and impactors, as well as changing several other settings, can be done using an Excel file which is loaded into the program. However, additions to the program and/or more complex adjustments will have to be made within the code itself. As the model was built and tested for Earth-like conditions, working with extreme compositions/conditions (e.g. modelling exoplanets) might require the user to make code adjustments to accommodate these unique circumstances. For any of these more complex changes, we recommend that you be knowledgeable in Python. 

The PlanetBuilder code is fully annotated to help users understand how each section of the model works. The theories and equations behind the model are explained in Seegers et al. (under review), whereas this guide is written to help users work with the model. All mentions of specific sections, tables and figures in this guide refer to that paper. 

If you have any further questions, you can contact the authors by sending an e-mail to a.x.seegers.vu@gmail.com.


## Installing Python
PlanetBuilder was tested in Python 3.9, and requires at least Numpy 2.2.5 and Pandas 2.2.3 to work. For more details, please refer to '*requirements.txt'*.

In this section we will go over some useful links and guides for those who do not have Python installed yet. There are several ways to install Python on Windows, and many users have their own preferences for how to install it and/or which IDE (integrated development environment) to use. Although there are many good Python installation guides available on the web, below is a quick reference guide: 

Installation for new Python users:
1.	Download Python from the official website (https://www.python.org/downloads) for your OS. Depending on the rights you have on your (office) computer, custom installation might be necessary. If this is the case, it is preferable to ensure the ‘pip’ option is installed.
2.	Choose and install an IDE: 
	For using PlanetBuilder, no advanced IDEs are required, so it mostly comes down to personal preference. Two good free-to-use options are:
	- Visual Studio Code (https://code.visualstudio.com/) 
	- PyCharm Community Edition (https://www.jetbrains.com/pycharm/) 
3.	Download a package installer to manage the additional packages required for PlanetBuilder, such as pip (https://packaging.python.org/en/latest/tutorials/installing-packages/) or Anaconda (https://www.anaconda.com/download)


4.	Install numpy using Anaconda or a similar package installer/pip (https://numpy.org/install/#python-numpy-install-guide) 
5.	Install Pandas using Anaconda or a similar package installer/pip (https://pandas.pydata.org/docs/getting_started/install.html) 
6.	Check if Python is set as the interpreter language in your IDE, even though most IDEs will ask when the model is started or recognise the code as Python. 

## Add MIDACO to PlanetBuilder
We used MIDACO solvers for the creation of PlanetBuilder, as it is fast and easy to install. However, it is possible to implement other solvers as well. To get started with MIDACO, please follow the steps below.

The MIDACO files are not included in PlanetBuilder. Please download the correct file depending on your OS from: https://www.midaco-solver.com/index.php/download. For Windows: *'midacopy.dll'*, and for Linux/Mac:  *'midacopy.so'*

PlanetBuilder uses two MIDACO solvers, one for the main solver of the equilibrated composition, and a smaller version for the thermodynamic KdO (Frost et al. 2010) calculations. As these run simultaneously, two versions of the MIDACO file have to be placed in the main directory of PlanetBuilder:
- MIDACO file for the main solver should be renamed to: *'midacopyPB.dll'* for Windows or *'midacopyPB.so'* for Linux/Mac
- MIDACO file for the thermodynamic KdO should be renamed to: *'midacopyFrost.dll'*

## Using the PlanetBuilder input files
The *'InputFile.xlsx'* file is located in the main directory of PlanetBuilder. All the options and information needed to run the program are in this file. Basic data and settings can be adjusted if this is done within the appropriate cells dedicated for these variables. Other cells are not read or taken into account, and missing or wrong input will raise exceptions or errors that need to be addressed. Adjusting the names of any of the yellow-coloured cells will cause the program to crash. We advise keeping the input file in the main directory to avoid permission errors. It is not necessary to keep the original name of the input file, as long as the filename is also adjusted in '\__main\__.py.'

Although the minor elements are optional and can be adjusted, the major elements/oxides: FeO, SiO2 and NiO in the mantle, and Fe, Si, Ni and O in the core are mandatory. If the starting composition lacks one of these elements, please enter a very small number to avoid the cell reading as empty. 

### Input file
*'General settings'*: This sheet contains the primary options for running the program. 
-	Output file name: 
	The name should adhere to naming conventions of e.g. Word and Excel. Do not add .xlsx or other extensions behind the name, as this will be automatically generated.
-	Program settings:
	The Kd corrected for γFe field gives the option to run PlanetBuilder with or without the corrections for the activity of Fe in metal. It’s not possible to run both at the same time. More information on the implications of these adjustments for Kd values is provided in Seegers et al., (under review) 

*'Planet starting composition'*: This sheet describes the composition and state of the planetary body at the start of the program. 
-	Mantle elements/oxides: Which elements/oxides make up the planetary mantle at the start of the program? It is important to only use elements and their official notation from the periodic table. For oxides and other compounds, subscripts should be entered as numbers, and will be taken into account when calculating the molecular weight of the oxide or compound. 
-	Mantle concentration: The concentration of the element/oxide in the mantle on the same row. All data should be entered in ppm and written out as numbers. Using the scientific notation is not recommended. PlanetBuilder will normalise the entered concentrations as if it describes the full composition, even when elements are missing from the input. 
-	Core elements: Which elements make up the planetary core at the start of the program? Data entered here should adhere to the same standards as the mantle elements/oxides. If this field is empty without the '*Equilibrate'* is not turn off, this will cause errors.
-	Core concentration: The concentration in the planetary core of the element on the same row. It should adhere to the same standards as the mantle concentrations.

-	Other settings:
	Planet core mass fraction: The portion of the total mass of the planetary body at the start of the program that makes up the core (0 < value < 1).
	Planet starting relative mass fraction: It is not necessary to know the absolute mass of the planetary body at the start or finish. Instead, the size of the starting protoplanet should be expressed relative to the fully formed planetary body (0 < value < 1). Here, 0 indicates no protoplanet, and 1 indicates a fully formed planet. Using these end-values will prevent the program from running. 


*'Events':* This sheet contains information regarding the events and changes that happen throughout the evolution of the planetary body. In the current version of PlanetBuilder, the only important events are the impactors added to the growing planet. Every row in this sheet represents the conditions at that given accretion step and the circumstances under which the impactor is added to the planetary body. 
-	Pressure: The pressure (in GPa) at the depth where the user wants the equilibration between the planetary mantle and impactor to occur. 
-	Temperature: The temperature (in K) accompanying the pressure at the depth of the equilibration processes between the planetary mantle and impactor. 
-	Impactor type: In several of the following sheets, the details for each impactor can be entered. Every type of impactor needs a unique number (no decimals) that is also used on the impactor types and impactor composition sheets.
-	Full/partial equilibration: The fraction of the impactor core that equilibrates with the planetary mantle (0 < value ≤ 1), where 1 indicates full equilibration of the impactor core and planetary mantle. The use and purpose of a disequilibrium factor is explained in Sect. 2.
-	Equilibrate: When an impactor does not have a core due to, e.g. oxidation, there is no equilibration possible. Marking this column appropriately is recommended to avoid potential errors. The only accepted variables in this column are *'yes'* and *'no'*. If 'no' is selected, all information regarding the impactor will be ignored for the given accretion step and equilibration process.

*'Impactor Types':* This sheet is relatively small and straightforward. Every impactor number, which correlates with the number on the other sheets, has a relative mass fraction and a core mass fraction. The relative mass fraction indicates the size of the impactor relative to the fully grown planet (0 < value < 1). The core mass fraction indicates the impactor core mass relative to the total impactor size (0 ≤ value < 1), where 0 indicates the impactor has no core. Without the 'Equilibrate' option in the *'Events'* sheet, this will cause errors. 

 
### Epsilon value file
The values in this file are the interaction parameters (ε values) between individual elements, and are used to calculate the metal activity coefficients to correct for non-ideal behaviour of elements in metal liquid (Sect. 2.4). We use an updated version of the interaction parameters matrix from Norris (2017), with updated values as presented in Table 2. Especially for the major elements, we advise against making uninformed adjustments to the interaction parameters. Please note that changing the name or location of this file will result in errors.

### Single-stage core formation
For single-stage core formation there is an additional input file called *'InputFile – SingleStage.xlsx'*. This file can only be used for quick single-stage core formation calculations in its simplest form: a core and mantle of specific compositions and specified core-mantle ratio fully equilibrate at provided PT conditions. While these calculations use the solvers of the main files, it is a separate piece of code that can only be started through *'SingleStage.py'* and adjusting the name of the input file at the bottom of the code. All files for this small side project have *'SingleStage'* in their names. 

## Running the PlanetBuilder program
After opening the folder with the program in the installed IDE, the model should be started from *'\__main\__.py'*. This is also where the correct input file must be called on.

## PlanetBuilder files overview
There are multiple files in the PlanetBuilder folder, each with its own part of the calculations and/or data. Although the code is annotated, and most IDEs help to quickly navigate where the functions originate, understanding their connections can be beneficial when searching for errors (debugging) or add new (sub-)routines to the code. More information regarding the equilibration processes and calculations themselves can be found in the paper. 

The program starts with '\__main\__.py', which reads the input file and passes the processed input to *'AccretionLoop.py'*. The *'AccretionLoop.py'* is responsible for connecting most of the other files. It is sorted into accretion steps and arranges everything that needs to be taken care of to calculate the equilibrated planetary composition for each accretion step. At the start of every step, it reads the *'EventsList.py'*, which provides the information on which event must take place. Although adding an impactor to the planet is the only type of possible event in the current version of PlanetBuilder, *'EventsList.py'* is written in a way that allows other types of events to be added. 

Once the impactor is added to the planetary mantle, the equilibration between the impactor core and the new planetary mantle can start. If ideal activity behaviour is assumed, the Kd values are calculated from *'KdValuesUncorrected'* function in *'KdValues.py'*, and passed to *'StandardEquilibrationRunner.py'*. When corrections for activity behaviour in metal have to be incorporated, the γ values are calculated in *MetalActivityCalculator.py*, and the *'KdValuesCorrected'* function in *KdValues.py* is used instead. Subsequently the *MetalActivityCorrectionRunner.py* is used to systematically adjust metal activity corrections and recalculate equilibrated compositions (Sect. 2.4 and Sect. 3.2). *'MidacoRunnerPlanetBuilder.py'* is the primary MIDACO solver (Schleuter et al., 2013) that equilibrates the major element compositions (Sect. 2.3 and Fig. 2). This solver uses a smaller secondary MIDACO solver (*MidacoRunnerFrost.py*) for deriving the thermodynamic KdO and using it to check if the hypothetical compositions are in equilibrium (Sect. 2.3.2). Afterwards, the equilibrated compositions are returned to either the *'StandardEquilibrationRunner.py'* or *'MetalActivityCorrectionRunner.py'* files. While the former will immediately return the equilibrated compositions to *'AccretionLoop.py'*, the latter adjusts the metal activity corrections and calls on *'MidacoRunnerPlanetBuilder.py'* multiple times. If the composition cannot equilibrate due to oxidation (Sect 3.3), this file will add the impactor core composition to the planetary mantle. 

*'MinorElements.py'* is responsible for calculating the equilibration of the minor elements based on the equilibrated major element composition returned by *'MidacoRunnerPlanetBuilder.py'*. Afterwards, the equilibrated impactor core is added to the planetary core, and the resulting planetary composition is written to an output Excel file through *'OutputToExcel.py'*.

When using the option to correct data for non-ideality, a second Excel output file with the addition *‘- Midaco Output’* will be created by *'OutputToExcelMidaco.py'*. This file is created by *'MetalActivityCorrectionRunner.py'* after each adjustment to the Kd values, and provides an overview of the equilibration process. 

The other files in the folder are support files that are called upon in various places:
-	*'AtomicWeights.py'*: data file with atomic weights of all elements in the periodic table.
-	'*Conversions.py'*: support file handling all functions that convert units (e.g. moles to ppm) and calculating the core/mantle masses.
-	*'EValues.csv'*: Excel data file with the epsilon values necessary for the corrected Kd calculations.
-	*'GammaValues.py'*: data file with gamma values necessary for the corrected Kd calculations.
-	*'ValenceStates.py'*: data file with prevalent mantle valence states of all currently used elements.

## Errors and troubleshooting
Within any program or model, errors can occur. For inexperienced users, these might be hard to identify and solve. Fortunately, most IDEs will give an error message with regard to which line of code returns the error. This allows for backtracing the error. When you find any significant errors, please send a message to the authors with the error message, when you received these errors, and a copy of your input file. We ask for the latter, as errors are often caused by incorrect variable settings in the input file. 

We always recommend running the program again in debug mode and using breakpoints to pause the model and review the data up until that point manually. More information on debugging code can be found on the websites of the IDEs and Python itself. 

## Notes on additions and advanced adjustments to the model
Adding new modules, data, combining models or making other adjustments will require modification of the code. We advise only doing this with sufficient experience in Python. 

Below is a short list with several recommendations on where to add common calculations and/or data:
-	Adding or adjusting Kd calculations requires changes to the *'KdValues.py'*. When adding new elements and using them to calculate the corrected Kd values, it is important to ensure that the *'ValenceState.py'* and *'GammaValues.py'* files are updated to include the new element as well. If there are no Kd values accompanying the new elements, they are assumed not to participate in the equilibration processes and remain in the phase in which they were added.
-	Changes to the file *'EValues.csv'* can be made in most IDEs, though it is recommended to use Excel to avoid conversion issues when loading the data. It is advised to adjust the interaction values on both sides of the diagonal of the table.
-	Adding a new event type is preferably done by adding a new class to the *'EventsList.py'* file and returning the correct information back to *'AccretionLoop.py'*. Listing it as an option in the input file requires adjusting *'ReadExcelInput.py'* as well, to accept the option and allow the *'Event'* class in '*EventsList.py'* to run.

## References
- 	Norris, C. A.: Metal Activity Calculator, http://www.earth.ox.ac.uk/ expet/metalact/, 2017.
- 	Schlueter, M., Erb, S., Gerdts, M., Kemble, S., and Ruckmann, J. J.: MIDACO on MINLP Space Applications, Advances in Space Research, 51, 1116–1131, https://doi.org/10.1016/j.asr.2012.11.006, 2013
- 	Seegers, A. X., Vroon, P. Z., van Westrenen, W.: PlanetBuilder 1.0: An open-source model to analyse the geochemical evolution of rocky planets during accretion and core formation, under review
