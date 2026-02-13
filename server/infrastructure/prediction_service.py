from collections import Counter, defaultdict
import logging
import random
import json
import calendar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

months = list(calendar.month_name)[1:]


class PredictionService:
    def run(self, data, cluster_range=[0, 3]):
        print("\n------------Start-----------------\n")
        start, end = cluster_range
        print("Looking at months from", months[start], "to", months[end])
        # setting up yearly buckets
        # https://docs.python.org/3/library/collections.html#collections.defaultdict
        yearly_buckets = defaultdict(lambda: [0] * 12)
        for entry in data:
            yearly_buckets[entry.date.year][entry.date.month - 1] = entry.avg_cost

        # create subsets of data for the cluster range
        # slicing each year's subset and choosing if U or D for the 3 months prior
        subset = {
            year: "".join(
                "U" if next_m > curr_m else "D"
                for curr_m, next_m in zip(
                    months[start : end + 1], months[start + 1 : end + 1]
                )
            )
            for year, months in yearly_buckets.items()
        }
        print("Subsets", json.dumps(subset, indent=4, sort_keys=True))

        # using built in counter class to get counts
        # https://docs.python.org/3/library/collections.html#collections.Counter
        counts = Counter(subset.values())
        total_counts = len(subset.values())
        probabilities = {
            pattern: count / total_counts for pattern, count in counts.items()
        }
        print("Probabilities", (json.dumps(probabilities, indent=4, sort_keys=True)))

        # generate the probabilities
        predictions = defaultdict(lambda: [])
        for k in probabilities.keys():
            prob = probabilities[k]
            for _ in range(0, 5):
                rand_number = random.random()
                if 0 <= prob <= rand_number:
                    predictions[k].append("D")
                else:
                    predictions[k].append("U")

        predictions = {k: max(set(v), key=v.count) for k, v in predictions.items()}
        print("Predictions", json.dumps(predictions, indent=4, sort_keys=True))
        print("\n------------END-----------------\n")


class ZillowData:
    def __init__(self, region_id, region_name, state_name, date, avg_cost):
        self.region_id = region_id
        self.region_name = region_name
        self.state_name = state_name
        self.date = date
        self.avg_cost = avg_cost
