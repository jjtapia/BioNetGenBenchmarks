import pandas
import os
import fnmatch
import cPickle as pickle
import collections

if __name__ == "__main__":
    # get files in current directory
    matches = []
    for root, dirnames, filenames in os.walk('.'):
        for filename in fnmatch.filter(filenames, '*.{0}'.format('dump')):
            matches.append(os.path.join(root, filename))

    totalDict = collections.defaultdict(lambda: collections.defaultdict(list))
    for fileName in matches:
        with open(fileName, 'rb') as f:
            partialDict = pickle.load(f)
            for fileName in partialDict:
                for method in partialDict[fileName]:
                    totalDict[fileName][method].extend(partialDict[fileName][method])

    finalFrame = pandas.DataFrame.from_dict(totalDict)
    finalFrame.to_csv('egfr_net.cvs')
    with open('finalFrame.pandas', 'wb') as f:
        pickle.dump(finalFrame, f)
