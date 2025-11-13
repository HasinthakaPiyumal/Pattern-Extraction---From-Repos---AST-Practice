# Cluster 3

def cleanData(inFile, outFile):
    count = 1
    stats = {}
    dropStats = defaultdict(int)
    print('cleaning {}'.format(inFile))
    with open(inFile, 'r') as csvfile:
        data = csvfile.readlines()
        totalRows = len(data)
        print('total rows read = {}'.format(totalRows))
        header = data[0]
        for line in data[1:]:
            line = line.strip()
            cols = line.split(',')
            key = cols[-1]
            if line.startswith('D') or line.find('Infinity') >= 0 or line.find('infinity') >= 0:
                dropStats[key] += 1
                continue
            dt = parser.parse(cols[2])
            epochs = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
            cols[2] = str(epochs)
            line = ','.join(cols)
            count += 1
            if key in stats:
                stats[key].append(line)
            else:
                stats[key] = [line]
            '\n            if count >= 1000:\n                break\n            '
    with open(outFile + '.csv', 'w') as csvoutfile:
        csvoutfile.write(header)
        with open(outFile + '.stats', 'w') as fout:
            fout.write('Total Clean Rows = {}; Dropped Rows = {}\n'.format(count, totalRows - count))
            for key in stats:
                fout.write('{} = {}\n'.format(key, len(stats[key])))
                line = '\n'.join(stats[key])
                csvoutfile.write('{}\n'.format(line))
                with open('{}-{}.csv'.format(outFile, key), 'w') as labelOut:
                    labelOut.write(header)
                    labelOut.write(line)
            for key in dropStats:
                fout.write('Dropped {} = {}\n'.format(key, dropStats[key]))
    print('all done writing {} rows; dropped {} rows'.format(count, totalRows - count))

def main(inputFile):
    results = []
    inputFile = os.path.join(folderPath, inputFile)
    outputFile = '{}.ordered'.format(inputFile)
    with open(inputFile, 'r') as fin:
        data = fin.readlines()
    for line in data:
        values = line.split()
        acc = values[1]
        std_dev = values[3]
        acc = acc.replace(':', '')
        std_dev = std_dev.replace(':', '')
        results.append([float(acc), float(std_dev)])
    results.sort(key=operator.itemgetter(1))
    results.sort(key=operator.itemgetter(0), reverse=True)
    with open(outputFile, 'w') as fout:
        for acc, std in results:
            fout.write('accuracy: {:.2f}% std_dev: {:.2f}\n'.format(acc, std))

