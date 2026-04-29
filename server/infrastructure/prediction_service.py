from collections import Counter, defaultdict
import logging
import calendar
from itertools import product
import numpy as np
import datetime as dt
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

months = list(calendar.month_name)[1:]


class PredictionService:
    def run(self, data, start=0, group_size=4, repeats=9, k=5, pred_date=None):

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

        print(last_real_date)

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

        # calculate the frequencies
        for p in [0, 4, 8]:
            frequencies[p // group_size] = self.get_frequencies(
                change_hist, group_size, p
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
        for s in range(1, (12 // group_size)):
            years = 0
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
                        change_curr_year, frequencies[s - 1], patterns, idx, group_size
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

            month = month + 4

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

    def predict(self, test_set, patterns, training_frequencies, prediction_month, change_hist, group_size=3, k=6):
        correct_predictions = 0
        incorrect_predictions = 0
        change_curr_year = self.get_changes(test_set, group_size)
        summary_rows = []

        for i in range(4):
            print(f"\n----------Training round {i}--------------")
            print(f"trainging freqs: {training_frequencies}")
            # offset into each year so that the 3-month prefix ends at prediction_month
            start = i * 12 + prediction_month
            if start + group_size >= len(test_set):
                print(f"Not enough test data for round {i}, stopping.")
                break
            prefix = ""
            jan, feb, mar, apr = test_set[start][1], test_set[start+1][1], test_set[start+2][1], test_set[start+3][1]
            print(f"Months {test_set[start+1], test_set[start+2], test_set[start+3], test_set[start+4]}")
            prefix = ("U" if feb > jan else "D") + ("U" if mar > feb else "D")
            prefix_triple = ("U" if feb > jan else "D") + ("U" if mar > feb else "D") + ("U" if apr > mar else "D")
            prefix_triple_alt_case = ("U" if feb > jan else "D") + ("U" if mar > feb else "D") + ("U" if apr < mar else "D")
            jan_apr_training_freq = training_frequencies[0]
            # default to 0 if a pattern was never seen in training, avoids KeyError later
            training_dict = {
                prefix_triple: jan_apr_training_freq.get(prefix_triple, 0),
                prefix_triple_alt_case: jan_apr_training_freq.get(prefix_triple_alt_case, 0),
            }
            print(f"Our prefix is {prefix}, so we test probability between {prefix_triple} and {prefix_triple_alt_case}")
            for month in test_set[start:start+3]:
                print(f"Test month: {month}")
            print(f"training dict: {training_dict}")
            total = sum(training_dict.values())
            probability_dict = {}
            if total == 0:
                # neither pattern ever appeared in training — fall back to 50/50
                probability_dict[prefix_triple] = "0.50"
                probability_dict[prefix_triple_alt_case] = "0.50"
            else:
                for p in training_dict:
                    probability_dict[p] = f"{training_dict[p] / total:,.2f}"
            print(f"training_dict total months: {total}")
            print(f"{prefix_triple} probability: {probability_dict[prefix_triple]}")
            print(f"{prefix_triple_alt_case} probability: {probability_dict[prefix_triple_alt_case]}")

            score1 = 0
            score2 = 0
            p1 = float(probability_dict[prefix_triple_alt_case])
            for _ in range(5):
                rand = random.randrange(0,100)/100
                if rand <= p1:
                    score2 += 1
                else:
                    score1 += 1
            print(f"{prefix_triple} points | {score1}")
            print(f"{prefix_triple_alt_case} points | {score2}")
            if score1 > score2:
                winner = prefix_triple
            else:
                winner = prefix_triple_alt_case
            print(f"We predict {winner}")

            target_date = test_set[start][0]
            idx = next(
                (j for j, c in enumerate(change_curr_year) if c[0] == target_date),
                i * 12  # fallback
            )
            last_known_price = float(test_set[start + group_size - 1][1])
            mag = float(self.magnitude(change_hist, change_curr_year, winner[-1], idx, k, group_size))
            predicted_price = last_known_price + mag
            print(f"Last known price: ${last_known_price:,.2f} | Magnitude: {mag:,.2f} | Predicted price: ${predicted_price:,.2f}")
            actual_price = float(test_set[start + group_size][1])
            print(f"Actual price: ${actual_price:,.2f} | Error: ${abs(predicted_price - actual_price):,.2f}")
            print(f"Test case is {prefix_triple} for {test_set[start+3][0]}")
            correct = winner == prefix_triple
            if correct:
                print(f"Correct direction prediction of {prefix_triple[-1]} for {test_set[start+3][0]}")
                correct_predictions = correct_predictions + 1
            else:
                print("Incorrect prediction")
                incorrect_predictions = incorrect_predictions + 1
            print(i)
            print(f"succes rate: {correct_predictions/(i+1)}")

            summary_rows.append({
                "month": test_set[start+3][0],
                "last_known": last_known_price,
                "magnitude": mag,
                "predicted": predicted_price,
                "actual": actual_price,
                "error": abs(predicted_price - actual_price),
                "direction": winner[-1],
                "correct": correct,
            })

            pass

        print("\n" + "="*95)
        print(f"{'Month':<12} {'Last Known':>14} {'Magnitude':>12} {'Predicted':>14} {'Actual':>14} {'Error':>12} {'Dir':>4} {'OK':>4}")
        print("="*95)
        for r in summary_rows:
            ok = "✓" if r["correct"] else "✗"
            print(f"{str(r['month']):<12} ${r['last_known']:>13,.2f} ${r['magnitude']:>11,.2f} ${r['predicted']:>13,.2f} ${r['actual']:>13,.2f} ${r['error']:>11,.2f} {r['direction']:>4} {ok:>4}")
        print("="*95)
        total = correct_predictions + incorrect_predictions
        accuracy = correct_predictions / total if total > 0 else 0.0
        print(f"Success rate: {correct_predictions}/{total} ({accuracy:.0%})")

        mse = sum(r["error"] ** 2 for r in summary_rows) / len(summary_rows) if summary_rows else 0.0
        rmse = mse ** 0.5
        print(f"MSE:  {mse:,.2f}")
        print(f"RMSE: {rmse:,.2f}")

        return {
            "correct": correct_predictions,
            "wrong": incorrect_predictions,
            "total": total,
            "accuracy": accuracy,
            "mse": mse,
            "rmse": rmse,
            "rows": summary_rows,
        }

    def generate_training_set(self, data, cutoff):
        training_data = []
        for date, price in data:
            if date.year < cutoff:
                training_data.append((date,price))
        return training_data

    def generate_test_set(self, data, cutoff):
        testing_data = []
        for date, price in data:
            if date.year >= cutoff:
                testing_data.append((date,price))
        return testing_data

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
                changes[idx][1] = float(groups[idx][1]) - float(groups[idx - 1][1])

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
            curr_group = p + i  # p + current group

            # look the the range of current quarter (?) + group size
            for j in range(curr_group, curr_group + group_size):
                if j >= y:
                    break
                pattern += changes[j][2]  # create the pattern
            freq[pattern] += 1  # store off in the counter
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
        print(f"change value {change_value}")
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
