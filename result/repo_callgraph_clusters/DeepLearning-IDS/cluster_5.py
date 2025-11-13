# Cluster 5

def cleanAllData():
    inputDataPath = '../ProcessedTrafficData'
    outputDataPath = '../NewCleanedData'
    if not os.path.exists(outputDataPath):
        os.mkdir(outputDataPath)
    files = os.listdir(inputDataPath)
    for file in files:
        if file.startswith('.'):
            continue
        if os.path.isdir(file):
            continue
        outFile = os.path.join(outputDataPath, file)
        inputFile = os.path.join(inputDataPath, file)
        cleanData(inputFile, outFile)

