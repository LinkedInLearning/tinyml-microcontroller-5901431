import math

totalSlices = 0

kSilenceIndex = const (0)
kUnknownIndex = const (1)
kYesIndex = const (2)
kNoIndex = const (3)

scoreThreshold = const (200)
startValue = const (0)

class Score:
    def __init__(self, kind, score):
        self.kind = kind
        self.score = score

class Results:
    def __init__(self, classes):
        self.data = {cls: [] for cls in classes}
        self.nextIndex = 0
        self.score = Score("unknown", startValue)
        for i in range(3):
            for cls in classes:
                self.data[cls].append(startValue)

    def _computeAverageTotal(self, array_data):
        total = sum(array_data)
        return math.floor(total / len(array_data))

    def computeResults(self):
        totals = {cls: sum(1 for score in scores if score > scoreThreshold) for cls, scores in self.data.items()}
        
        topScoreKind, topScore = max(totals.items(), key=lambda item: item[1])

        if topScore > 0:
            self.score.kind = topScoreKind
            self.score.score = topScore
        else:
            self.score.kind = "unknown"
            self.score.score = startValue
        return self.score

    def resetScore(self):
        self.nextIndex = 0
        for scores in self.data.values():
            scores[:] = [startValue] * len(scores)
        self.score.kind = "unknown"
        self.score.score = startValue

    def storeResults(self, scores):
        if self.nextIndex == 2:
            self.nextIndex = 0
        else:
            self.nextIndex += 1
        for cls, score in scores.items():
            self.data[cls][self.nextIndex] = score + 128

