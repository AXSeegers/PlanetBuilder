from typing import Any

from CustomTypes import ElementDictionary
from ReadExcelInput import Input
import pandas as pd

# Writer to sort and export all output data to an Excel file, writes the data away at the end of every timestep
class ExcelWriter():
    def __init__(self, input: Input):
        self.input = input

        # Creates empty dataframes to store output data
        self.parameterDataFrame = pd.DataFrame([])
        self.molesMantleDF = pd.DataFrame([])
        self.molesCoreDF = pd.DataFrame([])
        self.ppmMantleDF = pd.DataFrame([])
        self.ppmCoreDF = pd.DataFrame([])
        self.ppmICoreDF = pd.DataFrame([])
        self.molesICoreDF = pd.DataFrame([])

    # Add data to empty dataframes
    def AddDataToFrames(
        self,
        parameters: dict[str, Any],
        molesMantle: ElementDictionary,
        molesCore: ElementDictionary,
        ppmMantle: ElementDictionary,
        ppmCore: ElementDictionary,
        molesICore: ElementDictionary,
        ppmICore: ElementDictionary,
    ) -> None:
        self.parameterDataFrame = pd.concat([self.parameterDataFrame, pd.DataFrame([parameters])], ignore_index=True)
        self.molesMantleDF = pd.concat([self.molesMantleDF, pd.DataFrame([molesMantle])], ignore_index=True)
        self.molesCoreDF = pd.concat([self.molesCoreDF, pd.DataFrame([molesCore])], ignore_index=True)
        self.ppmMantleDF = pd.concat([self.ppmMantleDF, pd.DataFrame([ppmMantle])], ignore_index=True)
        self.ppmCoreDF = pd.concat([self.ppmCoreDF, pd.DataFrame([ppmCore])], ignore_index=True)
        self.ppmICoreDF = pd.concat([self.ppmICoreDF, pd.DataFrame([ppmICore])], ignore_index=True)
        self.molesICoreDF = pd.concat([self.molesICoreDF, pd.DataFrame([molesICore])], ignore_index=True)

    # Writer
    def WriteToExcel(self) -> None:
        self.molesMantleDF = self.molesMantleDF.loc[:, (self.molesMantleDF != 0).any(axis=0)] 
        self.molesCoreDF = self.molesCoreDF.loc[:, (self.molesCoreDF != 0).any(axis=0)]
        self.ppmMantleDF = self.ppmMantleDF.loc[:, (self.ppmMantleDF != 0).any(axis=0)] 
        self.ppmCoreDF = self.ppmCoreDF.loc[:, (self.ppmCoreDF != 0).any(axis=0)]
        self.ppmICoreDF = self.ppmICoreDF.loc[:, (self.ppmICoreDF != 0).any(axis=0)]
        self.molesICoreDF = self.molesICoreDF.loc[:, (self.molesICoreDF != 0).any(axis=0)]  

        self.parameterDataFrame.name = 'Conditions'
        self.molesMantleDF.name = 'Moles Mantle'
        self.molesCoreDF.name = 'Moles Core'
        self.ppmMantleDF.name = 'ppm Mantle'   
        self.ppmCoreDF.name = 'ppm Core'
        self.ppmICoreDF.name = 'Additional data: ppm Impactor Core'
        self.molesICoreDF.name = 'Additional data: Moles Impactor Core'

        dataFrameList = self.getDataFrameList()
        outputName = self.input.settings.outputName
        fileName = f'Output/{outputName}.xlsx'
            
        writer = pd.ExcelWriter(fileName, engine='xlsxwriter')
        column = 0
        for dataframe in dataFrameList:
            dataframe.to_excel(writer, sheet_name='Output Data', startrow=1, startcol=column, index=False)
            sheet = writer.sheets['Output Data']
            sheet.write(0,column,dataframe.name)
            column = column + len(dataframe.columns) + 1

        writer.close()   

    def getDataFrameList(self):
        return [self.parameterDataFrame, self.ppmMantleDF, self.ppmCoreDF, self.molesMantleDF, self.molesCoreDF, self.ppmICoreDF, self.molesICoreDF]