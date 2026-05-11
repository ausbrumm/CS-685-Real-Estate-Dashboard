from collections import Counter, defaultdict
import logging
import calendar
from itertools import product
import numpy as np
import datetime as dt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

months = list(calendar.month_name)[1:]


class PredictionService:
    def run(self, data, start=0, group_size=4, repeats=9, k=5, pred_date=None):
        self.validate_group_size(group_size)
        self.validate_k(k)

        data = sorted(data, key=lambda e: e[0])

        # store last real date for the ui to mark projected months
        last_real_date = str(data[-1][0]) if data else None

        if pred_date is not None and data and pred_date < data[-1][0]:
            data = [d for d in data if d[0] <= pred_date]
            last_real_date = str(data[-1][0]) if data else None

        if pred_date is not None and data and pred_date > data[-1][0]:
            data = self.chain_predictions(
                data, pred_date, start, group_size, repeats, k
            )

        if len(data) < group_size:
            return (
                [],
                {},
                {},
                {},
                [],
                {},
                {
                    "correct": 0,
                    "wrong": 0,
                    "total": 0,
                    "accuracy": 0.0,
                    "mse": 0.0,
                    "rmse": 0.0,
                },
                [],
                last_real_date,
            )
        # sort data by date
        data = sorted(data, key=lambda e: e[0])

        # generate all possible patterns
        patterns = self.generate_patterns(group_size)

        # group into _group_size_ groups
        groups = self.create_groups(data, start, group_size)

        # calculate the change count
        changes = self.get_changes(data, group_size)

        # get all the years
        years = sorted({item[0].year for item in data})

        if not years:
            return []

        # get 6 years ago for the cutoff
        last_year = years[-6]

        # split changes into historical/training set

        change_hist = [c for c in changes if c[0].year < last_year]

        # split changes into test set
        change_curr_year = [c for c in changes if c[0].year >= last_year]

        z = len(change_curr_year)
        if z == 0:
            return (
                [],
                patterns,
                groups,
                changes,
                data,
                {},
                {
                    "correct": 0,
                    "wrong": 0,
                    "total": 0,
                    "accuracy": 0.0,
                    "mse": 0.0,
                    "rmse": 0.0,
                },
                [],
                last_real_date,
            )

        # lookup for prediction comparison, for accuracy
        chg_by_date = {c[0]: c for c in change_curr_year}

        frequencies = {}

        groups_per_year = 12 // group_size
        group_starts = range(0, 12, group_size)

        # calculate the frequencies for each position within the year
        for group_index, start_month in enumerate(group_starts):
            frequencies[group_index] = self.get_frequencies(
                change_hist, group_size, start_month
            )

        month = 0
        results = [{"date": None, "predictions": {}} for _ in range(z)]
        results[z - 1]["date"] = change_curr_year[-1][0]

        correct = 0
        wrong = 0

        # need to add an offset for the groups in order to make it start on the correct year for predicting
        start_date = change_curr_year[0][0]

        # calculate the start date offset
        groups_offset = next(i for i, g in enumerate(groups) if g[0] >= start_date)
        prediction_cycles = max(1, groups_per_year - 1)
        for step in range(prediction_cycles):
            for i in range(month, z):
                predictions = defaultdict(int)
                idx = i
                if idx >= len(change_curr_year):
                    break

                # get date assignment
                if idx < len(change_curr_year):
                    results[i]["date"] = change_curr_year[idx][0]

                for _ in range(repeats):
                    letter = self.predict_change(
                        change_curr_year, frequencies[step], patterns, idx, group_size
                    )
                    predictions[letter] += 1

                letter = max(predictions, key=lambda k: predictions[k])
                groups_idx = min(groups_offset + idx + group_size - 2, len(groups) - 1)
                last_known_price = float(groups[groups_idx][1])
                mag = abs(
                    float(
                        self.magnitude(
                            change_hist, change_curr_year, letter, idx, k, group_size
                        )
                    )
                )

                # magnitude still but total
                m = last_known_price + mag if letter == "U" else last_known_price - mag

                results[i]["date"] = change_curr_year[idx][0]
                results[i]["predictions"][month] = {"direction": letter, "price": m}

                target_date = (
                    change_curr_year[idx][0] if idx < len(change_curr_year) else None
                )
                if target_date and target_date in chg_by_date:
                    actual = chg_by_date[target_date][2]
                    if letter == actual:
                        correct += 1
                    else:
                        wrong += 1

            month += group_size

        total = correct + wrong
        accuracy = correct / total if total > 0 else 0.0

        mse, rmse, error_band = self.mse(data, results)

        acc_summary = {
            "correct": correct,
            "wrong": wrong,
            "total": total,
            "accuracy": accuracy,
            "mse": mse,
            "rmse": rmse,
        }

        data = [d for d in data if d[0].year >= last_year]
        return (
            results,
            patterns,
            groups,
            changes,
            data,
            frequencies,
            acc_summary,
            error_band,
            last_real_date,
        )

    @staticmethod
    def validate_group_size(group_size):
        if group_size <= 0 or 12 % group_size != 0:
            raise ValueError("group_size must be a positive divisor of 12")

    @staticmethod
    def validate_k(k):
        if k <= 0 or k >= 12 or k % 2 == 0:
            raise ValueError("k must be an odd positive integer less than 12")

    def create_groups(self, entries, start=0, group_size=4, k=6):
        """
        Group data into groups of m consecutive months
        """

        n = len(entries)

        groups = [
            [None, None, None] for _ in range(n + group_size)
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
            [None, 0, None] for _ in range(n + group_size)
        ]  # n years * 12 months, price difference, and change direction
        # adding group size to deal with if there is a partial group

        # go over each group
        for i in range(1, (n // group_size) + 1):
            # loop through group members
            for j in range(group_size):
                # calculate the index for the changes
                # current group * size of group + current group item
                idx = i * group_size + j

                if idx >= n:
                    break
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

        start_offset = p // group_size

        # walk fully-indexable windows aligned to the selected within-year group offset
        for curr_group in range(start_offset + 1, y - group_size + 1, group_size):
            pattern = "".join(
                changes[j][2] for j in range(curr_group, curr_group + group_size)
            )
            freq[pattern] += 1
        return freq

    def predict_change(self, change_curr_year, frequency, patterns, index, group_size):
        pattern = "".join(
            change_curr_year[j][2]
            for j in range(index + 1, index + group_size - 2)
            if j < len(change_curr_year)
        )

        # patter 1 and pattern 2
        p1 = pattern + "D"
        p2 = pattern + "U"

        # frequency of pattern 1 and pattern 2
        f1 = frequency.get(p1, 1)
        f2 = frequency.get(p2, 1)

        # random number between 0 and 1
        x = np.random.rand()
        return "D" if x <= f1 / (f1 + f2) else "U"

    def magnitude(self, change_hist, change_curr_year, letter, index, k, group_size):
        y = len(change_hist)
        num_rows = (y - 1) // group_size  # safe number of fully indexable groups

        diffs = [
            [0] * group_size for _ in range(num_rows + 1)
        ]  # group_size columns, not group_size-1
        dists = [0.0] * (num_rows + 1)

        for j in range(num_rows + 1):
            for l in range(group_size - 1):
                hist_idx = j * group_size + l + 1
                if hist_idx >= y:
                    break
                diffs[j][l + 1] = change_hist[hist_idx][1]

            dists[j] = np.sqrt(
                sum(
                    (diffs[j][t] - change_curr_year[index + t][1])
                    ** 2  # [1] to get price
                    for t in range(1, group_size)
                    if index + t < len(change_curr_year)
                )
            )

        last_col = group_size - 1  # last valid column index

        if letter == "D":
            candidates = [j for j in range(num_rows + 1) if diffs[j][last_col] < 0]
        else:
            candidates = [j for j in range(num_rows + 1) if diffs[j][last_col] >= 0]

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

    def chain_predictions(self, data, pred_date, start, group_size, repeats, k):
        """Chain predictions forward month by month until pred_date is reached."""
        data = sorted(data, key=lambda e: e[0])
        last_date = data[-1][0]

        while last_date < pred_date:
            # advance to next month
            if last_date.month == 12:
                next_date = dt.date(last_date.year + 1, 1, 31)
            else:
                next_month = last_date.month + 1
                last_day = calendar.monthrange(last_date.year, next_month)[1]
                next_date = dt.date(last_date.year, next_month, last_day)

            # run prediction on data up to this point
            (
                results,
                patterns,
                groups,
                changes,
                filtered_data,
                frequencies,
                acc_summary,
                error_band,
                last_real_date,
            ) = self.run(data, start, group_size, repeats, k)

            if not results or not results[-1]["predictions"]:
                break

            # get the last prediction's average price to use as the "actual" data
            last_preds = results[-1]["predictions"]
            prices = [
                p["price"] for p in last_preds.values() if p.get("price") is not None
            ]
            if not prices:
                break
            predicted_price = sum(prices) / len(prices)

            # append predicted month to data
            data.append((next_date, predicted_price))
            data = sorted(data, key=lambda e: e[0])
            last_date = next_date

        return data

    def mse(self, data, results):
        # Collect paired (actual, predicted) for all results that have both
        paired = []

        actual_price_by_date = {}
        for item in data:
            date_key = item[0]
            actual_price_by_date[date_key] = float(item[1])

        for result in results:
            if result["date"] is None or not result["predictions"]:
                continue

            # Average all prediction prices for this result
            pred_prices = [
                p["price"]
                for p in result["predictions"].values()
                if p.get("price") is not None
            ]
            if not pred_prices:
                continue
            avg_pred = sum(pred_prices) / len(pred_prices)
            # Find the actual price for this date
            if result["date"] in actual_price_by_date:
                actual = actual_price_by_date[result["date"]]
                paired.append((actual, avg_pred))

        if paired:
            mse = sum((a - p) ** 2 for a, p in paired) / len(paired)
            rmse = float(np.sqrt(mse))
        else:
            mse = 0.0
            rmse = 0.0

        # Build error_band: for each result with a prediction, add upper/lower
        error_band = []
        for result in results:
            if result["date"] is None or not result["predictions"]:
                continue
            pred_prices = [
                p["price"]
                for p in result["predictions"].values()
                if p.get("price") is not None
            ]
            if not pred_prices:
                continue
            avg_pred = sum(pred_prices) / len(pred_prices)
            error_band.append(
                {
                    "date": result["date"],
                    "predicted": avg_pred,
                    "upper": avg_pred + rmse,
                    "lower": avg_pred - rmse,
                }
            )
        return mse, rmse, error_band
