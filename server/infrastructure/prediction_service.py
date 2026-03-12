from collections import Counter, defaultdict
import logging
import random
import json
import calendar
from itertools import product
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

months = list(calendar.month_name)[1:]


class PredictionService:
    # take first 20 years as training set for computing freq
    # for test next 6 years
    # so training ~76%
    # test ~24%
    # use 3 months before jan feb march 2020 to make prediction for april 2020
    # predict and compare to actual data
    # get count of predict correct vs predict wrong for accuracy

    def run(self, data, start=0, group_size=3, repeats=5, k=6):
        print("\n------------Start-----------------\n")
        data = sorted(data, key=lambda e: (e[0]))
        patterns = self.generate_patterns(group_size)
        groups = self.create_groups(data, start, group_size)
        changes = self.get_changes(data, group_size)

        years = sorted({item[0].year for item in data})

        if not years:
            return []

        last_year = years[-6]

        change_hist = [c for c in changes if c[0].year < last_year]
        change_curr_year = [c for c in changes if c[0].year >= last_year]


        y = len(change_hist)
        z = len(change_curr_year)

        frequencies = {}
        # need to ask Arash what p is for here
        for p in [0, 4, 8]:
            frequencies[p // group_size] = self.get_frequencies(
                change_hist, group_size, p
            )

        month = 0
        results = [[None, 0, None] for _ in range(z)]
        results[z - 1][0] = change_curr_year[z - 1][0]

        for s in range(1, 12 // group_size):
            for i in range(0, z - 1):
                predictions = defaultdict(int)
                idx = i * 12 + month
                for _ in range(1, repeats):
                    letter = self.predict_change(
                        change_curr_year, frequencies[s - 1], patterns, idx, group_size
                    )
                    predictions[letter] += 1

                letter = max(predictions, key=lambda k: predictions[k])
                groups_idx = idx + group_size - 2
                if groups_idx >= len(groups):
                    continue
                last_known_price = float(groups[groups_idx][1])
                mag = float(
                    self.magnitude(
                        change_hist, change_curr_year, letter, idx, k, group_size
                    )
                )

                # magnitude still but total
                m = last_known_price + mag if letter == "U" else last_known_price - mag

                results[i].append([letter, m, month])

            month = month + 4
        # i.e model
        # [results, groups, changes, blah blah]
        #print("frequencies: ",frequencies)
        """jan_apr = frequencies
        print(f"Sum: {sum(jan_apr.values())}")
        total = sum(jan_apr.values())
        ranges_dict = {}
        tracker = 1
        for pattern, count in jan_apr.items():
            #print(f"Range: {tracker}-{tracker+count-1}")
            #ranges_dict.update({pattern:()})
            print(f"{pattern}: {count}  | {count/total:,.2f}")
            tracker = tracker+count"""

        #for n in range(5):
            #print(n)


        #print(data)

        return results, patterns, groups, changes, data, frequencies

    def predict(self, test_set, patterns, training_frequencies, prediction_month):
        correct_predictions = 0
        incorrect_predictions = 0
        
        for i in range(4):
            print(f"\n----------Training round {i}--------------")
            print(f"trainging freqs: {training_frequencies}")
            start = i *12
            prefix = ""
            jan, feb, mar, apr = test_set[start][1], test_set[start+1][1], test_set[start+2][1], test_set[start+3][1]
            print(f"Months {test_set[start+1], test_set[start+2], test_set[start+3], test_set[start+4]}")
            prefix = ("U" if feb > jan else "D") + ("U" if mar > feb else "D")
            prefix_triple = ("U" if feb > jan else "D") + ("U" if mar > feb else "D") + ("U" if apr > mar else "D")
            prefix_triple_alt_case = ("U" if feb > jan else "D") + ("U" if mar > feb else "D") + ("U" if apr < mar else "D")
            jan_apr_training_freq = training_frequencies[0]
            training_dict = {}
            print(f"Our prefix is {prefix}, so we test probability between {prefix_triple} and {prefix_triple_alt_case}")
            for p in jan_apr_training_freq:
                if p == prefix_triple or p == prefix_triple_alt_case:
                    training_dict[p] = jan_apr_training_freq[p]
            for month in test_set[start:start+3]:
                print(f"Test month: {month}")
            print(f"training dict: {training_dict}")
            print(f"training_dict total months: {sum(training_dict.values())}")
            probability_dict = {}
            for p in training_dict:
                probability = f"{(training_dict[p]/sum(training_dict.values())):,.2f}"
                probability_dict[p] = probability
            print(f"{prefix_triple} probability: {probability_dict[prefix_triple]}")
            print(f"{prefix_triple_alt_case} probability: {probability_dict[prefix_triple_alt_case]}")
            
            score1 = 0
            score2 = 0
            p1 = float(probability_dict[prefix_triple_alt_case])
            for _ in range(5):
                rand = random.randrange(0,100)/100
                if rand <= p1:
                    score2 += 1
                    #print(f"Score for {prefix_triple_alt_case}:")
                else:
                    #print(f"Score for {prefix_triple}")
                    score1 += 1 
            print(f"{prefix_triple} points | {score1}")
            print(f"{prefix_triple_alt_case} points | {score2}")
            if score1 > score2:
                winner = prefix_triple
            else:
                winner = prefix_triple_alt_case
            print(f"We predict {winner}")
            print(f"Test case is {prefix_triple} for {test_set[start+3][0]}")
            if winner == prefix_triple:
                print(f"Correct direction prediction of {prefix_triple[-1]} for {test_set[start+3][0]}") 
                correct_predictions = correct_predictions + 1
            else:
                print("Incorrect prediction")
                incorrect_predictions = incorrect_predictions +1
            print(i)
            print(f"succes rate: {correct_predictions/(i+1)}")

            """print(f"jan-apr training frequencies {jan_apr_training_freq}")
            print(f"Prefix: {prefix}")
            print(f"Prefix_triple: {prefix_triple}")
            print(f"Prefix_triple_alt_case: {prefix_triple_alt_case}")"""
            #print(f"Patterns: {patterns}")
            #print(len(test_set))
            
            pass

    def generate_training_set(self, data, cutoff):
        training_data = []
        for date, price in data:
            if date.year < cutoff:
                training_data.append((date,price))

        """print(f"\n--- Training Data Generation (Cutoff: {cutoff}) ---")
        print(f"Total Training Months: {len(training_data)}")
        print(f"Start Date: {training_data[0][0]} Price {training_data[0][0]:,.2f}")"""

        return training_data

    def generate_test_set(self, data, cutoff):
        testing_data = []
        for date, price in data:
            if date.year >= cutoff:
                testing_data.append((date,price))

        """print(f"\n--- Testing Data Generation (Cutoff: {cutoff}) ---")
        print(f"Total Testing Months: {len(testing_data)}")
        print(f"Start Date: {testing_data[0][0]} Price {testing_data[0][0]:,.2f}")"""
        return testing_data

    def create_groups(self, entries, start=0, group_size=4, k=6):
        """
        Group data into groups of m consecutive months
        """

        n = len(entries)

        groups = [
            [None, None, None] for _ in range(n)
        ]  # date, real estate price, and group

        # store the date and price
        # calculate the group number
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
        """
        Get the changes for the groups
        """
        # number of groups
        n = len(groups)

        changes = [
            [None, 0, None] for _ in range(n)
        ]  # n years * 12 months, price difference, and change direction

        # go over each group
        for i in range(n // group_size):
            # loop through group members
            for j in range(group_size):
                # calculate the index for the changes
                # current group * size of group + current group item
                idx = i * group_size + j

                # store the date
                changes[idx][0] = groups[idx][0]

                # calculate the price difference
                changes[idx][1] = groups[idx][1] - groups[idx - 1][1]

                # store the direction based off the differences
                changes[idx][2] = "U" if changes[idx][1] > 0 else "D"

        # filter out unset months
        changes = [c for c in changes if c[0] is not None]
        return changes

    def get_frequencies(self, changes, group_size, p):
        # number of changes
        y = len(changes)

        # counter to store the change frequencies of the patterns
        freq = Counter()

        # for each roup
        for i in range(1, y // group_size):
            pattern = ""
            # p is 0, 4, and 8... is this just starting point for quartering the data?
            l = p + i  # p + current group

            # look the the range of current quarter (?) + group size
            for j in range(l, l + group_size):
                pattern += changes[j][2]  # create the pattern
            freq[pattern] += 1  # store off in the counter
        return freq

    def predict_change(self, change_curr_year, frequency, patterns, index, group_size):
        pattern = ""
        for j in range(index + 1, index + group_size - 2):
            pattern += change_curr_year[j][2]
        # patter 1 and pattern 2
        p1 = pattern + "D"
        p2 = pattern + "U"

        # frequency of pattern 1 and pattern 2
        f1 = frequency.get(p1, 1)
        f2 = frequency.get(p2, 1)

        # random number between 0 and 1
        x = random.random()
        return "D" if x <= f1 / (f1 + f2) else "U"

    def magnitude(self, change_hist, change_curr_year, letter, index, k, group_size):
        y = len(change_hist)
        num_rows = (y - 1) // group_size  # safe number of fully indexable groups

        diffs = [
            [0] * group_size for _ in range(num_rows)
        ]  # group_size columns, not group_size-1
        dists = [0.0] * num_rows

        for j in range(num_rows):
            for l in range(group_size - 1):
                hist_idx = j * group_size + l + 1
                if hist_idx >= y:
                    break
                diffs[j][l + 1] = change_hist[hist_idx][1]

            dists[j] = np.sqrt(
                sum(
                    (diffs[j][t] - change_curr_year[index + t][1])
                    ** 2  # [1] to get price
                    for t in range(1, group_size - 1)
                    if index + t < len(change_curr_year)
                )
            )

        last_col = group_size - 1  # last valid column index

        if letter == "D":
            candidates = [j for j in range(num_rows) if diffs[j][last_col] < 0]
        else:
            candidates = [j for j in range(num_rows) if diffs[j][last_col] >= 0]

        # kth nearest neighbors in each group
        candidates = sorted(candidates, key=lambda j: dists[j])[:k]

        if not candidates:
            return 0.0

        # average value of the k nearest neighbors
        change_value = sum(diffs[j][last_col] for j in candidates) / k
        return change_value

    def generate_patterns(self, group_size):
        """
        Generates the patterns using itertools.product which takes in an iterable and
        does the cartesian product
        Sources:
        https://docs.python.org/3/library/itertools.html#itertools.product
        https://stackoverflow.com/questions/2541401/pairwise-crossproduct-in-python#:~:text=You're%20looking%20for%20itertools.
        """
        return ["".join(p) for p in product("UD", repeat=group_size)]


class ZillowData:
    def __init__(self, region_id, region_name, state_name, date, avg_cost):
        self.region_id = region_id
        self.region_name = region_name
        self.state_name = state_name
        self.date = date
        self.avg_cost = avg_cost
