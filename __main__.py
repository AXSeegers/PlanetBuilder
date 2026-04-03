from AccretionLoop import PlanetBuilder
from ReadExcelInput import ImportInputFile, Input

# Adjust the file name to the name of your input Excel file
# Please place the input file in the same directory as the code to avoid access issues 
def main() -> None:
    file_name: str = 'InputFile.xlsx'
    inputData: Input = ImportInputFile(file_name)
    planet_builder: PlanetBuilder = PlanetBuilder(inputData)
    planet_builder.RunAccretionSteps()

if __name__ == "__main__":
    main()
