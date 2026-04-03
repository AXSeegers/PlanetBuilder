import os
from ReadExcelInput import Input
import pandas as pd

class ExcelWriterMidaco():
    def __init__(self, input: Input):
        self.fileName = input.settings.outputName
        self.parameterDataFrame = pd.DataFrame([])
        self.molesMantleDF = pd.DataFrame([])
        self.molesICoreDF = pd.DataFrame([])
        self.ppmMantleDF = pd.DataFrame([])
        self.ppmICoreDF = pd.DataFrame([])

    def AddDataToFrames(self, parameters, molesMantle, ppmMantle, molesICore, ppmICore):
        self.parameterDataFrame = pd.concat([self.parameterDataFrame, pd.DataFrame([parameters])], ignore_index=True)
        self.molesMantleDF = pd.concat([self.molesMantleDF, pd.DataFrame([molesMantle])], ignore_index=True)
        self.molesICoreDF = pd.concat([self.molesICoreDF, pd.DataFrame([molesICore])], ignore_index=True)
        self.ppmMantleDF = pd.concat([self.ppmMantleDF, pd.DataFrame([ppmMantle])], ignore_index=True)
        self.ppmICoreDF = pd.concat([self.ppmICoreDF, pd.DataFrame([ppmICore])], ignore_index=True)
        

    def WriteToExcel(self, sheet_number=None):
        self.molesMantleDF = self.molesMantleDF.loc[:, (self.molesMantleDF != 0).any(axis=0)] 
        self.molesICoreDF = self.molesICoreDF.loc[:, (self.molesICoreDF != 0).any(axis=0)]  
        self.ppmMantleDF = self.ppmMantleDF.loc[:, (self.ppmMantleDF != 0).any(axis=0)] 
        self.ppmICoreDF = self.ppmICoreDF.loc[:, (self.ppmICoreDF != 0).any(axis=0)]
        
        self.parameterDataFrame.name = 'Conditions'
        self.molesMantleDF.name = 'Moles Mantle'
        self.ppmMantleDF.name = 'ppm Mantle'   
        self.ppmICoreDF.name = 'ppm ICore'
        self.molesICoreDF.name = 'Moles ICore'
        dataFrameList = self.getDataFrameList()
        outputPath = f'Output/{self.fileName} - Midaco Output.xlsx'

        # Determine sheet name based on sheet_number parameter
        if sheet_number is not None:
            sheet_name = f'{sheet_number}'
        else:
            sheet_name = 'Output Data'

        # Prepare writer and figure out current sheet state
        sheet_exists = False
        existing_rows = 0
        if os.path.exists(outputPath):
            writer = pd.ExcelWriter(outputPath, engine='openpyxl', if_sheet_exists='overlay', mode='a')
            if sheet_name in writer.book.sheetnames:
                ws = writer.book[sheet_name]
                sheet_exists = True
                existing_rows = ws.max_row
        else:
            writer = pd.ExcelWriter(outputPath, engine='openpyxl')

        # Decide where to start writing and whether to include column headers
        write_header = not sheet_exists or existing_rows <= 1
        startrow = 1 if write_header else existing_rows

        column = 0
        for dataframe in dataFrameList:
            df_to_write = dataframe if write_header else dataframe.tail(1)
            df_to_write.to_excel(writer, sheet_name=sheet_name, startrow=startrow, startcol=column, index=False, header=write_header)
            # Only write the block title on first write
            if write_header:
                # Access worksheet via writer.sheets (created after first to_excel call)
                sheet = writer.sheets[sheet_name]
                sheet.cell(row=1, column=column+1, value=dataframe.name)
            column = column + len(dataframe.columns) + 1
        writer.close()   

        self.parameterDataFrame = pd.DataFrame([])
        self.molesMantleDF = pd.DataFrame([])
        self.molesICoreDF = pd.DataFrame([])
        self.ppmMantleDF = pd.DataFrame([])
        self.ppmICoreDF = pd.DataFrame([])

    def getDataFrameList(self):
        return [self.parameterDataFrame, self.ppmMantleDF, self.ppmICoreDF, self.molesMantleDF, self.molesICoreDF]
