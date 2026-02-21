from collections import Counter, defaultdict
import logging
import random
import json
import calendar
from itertools import product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

months = list(calendar.month_name)[1:]


class PredictionService:
    def run(self, data, cluster_range=[0, 3]):
        print("\n------------Start-----------------\n")
        start, end = cluster_range
        print("Looking at months from", months[start % 12], "to", months[end % 12])
        # setting up yearly buckets
        # https://docs.python.org/3/library/collections.html#collections.defaultdict
        yearly_buckets = defaultdict(lambda: [0] * 12)
        for entry in data:
            yearly_buckets[entry.date.year][entry.date.month - 1] = entry.avg_cost

        # create subsets of data for the cluster range
        # slicing each year's subset and choosing if U or D for the 3 months prior
        subset = {} 
        for year, monthly_costs in yearly_buckets.items():
            pattern_chars = []
            
            for i in range(start, end):
                # bug fix to handle wrap around if we start in the last 3 months of the year
                curr_idx = i % 12
                next_idx = (i + 1) % 12
                
                curr_val = monthly_costs[curr_idx]
                next_val = monthly_costs[next_idx]
                
                pattern_chars.append("U" if next_val > curr_val else "D")
            
            subset[year] = "".join(pattern_chars)
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
        return predictions, probabilities, subset, counts


    def run2(self, data, start=0, group_size=4, repeats=5):
        print("\n------------Start-----------------\n")
        data = sorted(data, key=lambda e: (e[0]))
        patterns = self.generate_patterns(group_size)
        groups = self.create_groups(data, start, group_size)
        changes = self.get_changes(data, group_size)

        years = sorted({item[0].year for item in data})

        if not years:
            return []
        
        last_year = years[-1]

        change_hist = [c for c in changes if c[0].year != last_year]
        change_curr_year = [c for c in changes if c[0].year == last_year]
        
        y = len(change_hist)
        z = len(change_curr_year)

        frequencies = {}
        # need to ask Arash what p is for here
        for p in [0, 4, 8]:
            frequencies[p // group_size] = self.get_frequencies(change_hist, group_size, p)

        month = 0
        results = [[None, 0, None] for _ in range(z)]
        results[z - 1][0] = change_curr_year[z - 1][0]
        
        for s in range(1, 12//group_size):
            for i in range(0, z-1):
                predictions = defaultdict(int)
                idx = i * 12 + month
                for i in range(1,5):
                    letter = self.predict_change(change_curr_year, frequencies[s - 1], patterns, idx, group_size)
                    predictions[letter] += 1
                print(predictions)
        



        print("\n-------------End-------------------\n")

    def create_groups(self, entries, start=0, group_size=4):
        """
        Group data into groups of m consecutive months
        """

        n = len(entries)

        groups = [[None,None,None] for _ in range(n)] # number of entries, real estate prices, and group
      
        for idx in range(n):
            date, price = entries[idx]
            month_offset = date.month - 1
            groups[idx][0] = date
            groups[idx][1] = price
            groups[idx][2] = ((month_offset - start) % 12) // group_size

        # filter out unset months 
        groups = [g for g in groups if g[0] is not None]
        return groups

    def get_changes(self, groups, group_size):
        
        n = len(groups)

        changes = [[None, 0, None] for _ in range(n)]# n years * 12 months, price difference, and change direction
    
        for i in range(n // group_size):
            for j in range(group_size):
                idx = i * group_size + j 
                changes[idx][0] = groups[idx][0]
                changes[idx][1] = groups[idx][1] - groups[idx - 1][1]
                
                changes[idx][2] = "U" if changes[idx][1] > 0 else "D"
        changes = [c for c in changes if c[0] is not None]
        return changes
 
    def get_frequencies(self, changes, group_size, p):
        y = len(changes)
        freq = Counter()
        
        for i in range(1, y//group_size):
            pattern = ""
            l = p + i
            for j in range(l, l + group_size):
                pattern += changes[j][2]
            freq[pattern] += 1
        return freq 

    def predict_change(self, change_curr_year, frequency, patterns, index, group_size):
        pattern = ""
        for j in range(index + 1, index+group_size -2):
            pattern += change_curr_year[j][2]
        
        p1 = pattern + 'D'
        p2 = pattern + 'U'

        f1 = frequency.get(p1, 1)
        f2 = frequency.get(p2, 1)

        x = random.random()
        return "D" if x <= f1 / (f1 + f2) else "U"

    def generate_patterns(self, group_size):
        return ["".join(p) for p in product("UD", repeat=group_size)]

class ZillowData:
    def __init__(self, region_id, region_name, state_name, date, avg_cost):
        self.region_id = region_id
        self.region_name = region_name
        self.state_name = state_name
        self.date = date
        self.avg_cost = avg_cost
