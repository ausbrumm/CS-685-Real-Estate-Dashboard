# Changelog

## main.py — multi-region refactor + configurable parameters

### Multi-region support
- Expanded from single region (`395107`) to all 8 regions:
  `394463, 394910, 394338, 753899, 394357, 394466, 394596, 395107`
- Each region now runs in its own loop iteration with a labeled header
- Per-region results are collected into a `summaries` list

### Final summary table
- Added a formatted summary table printed after all regions complete
- Columns: Region, Correct, Total, Accuracy, MSE, RMSE

### Configurable group size and k
- `main()` now accepts `group_size` (default: 3) and `k` (default: 6)
- `run()`, `get_changes()`, and `predict()` calls use these variables instead of hardcoded values
- The training context prefix passed to `predict()` (`training_data[-N:]`) is now `group_size` entries instead of hardcoded 3
- `predict()` now receives an `extended_test` (prefix + test data) instead of raw test data

### CLI flags added
- `--group-size` / `-g`: choices `3`, `4`, `5` (default: `3`)
- `--k`: choices `1`, `3`, `5`, `7`, `9` (default: `6`)

### Debug output simplified
- Removed verbose first/last entry prints for full, training, and test sets
- Replaced with single-line training and test date range per region

---

## Code diff (main_original.py → main.py)

```diff
-async def main(cutoff: int, start_month: int):
-    regions = [395107]
-    data = []
+async def main(cutoff: int, start_month: int, group_size: int = 3, k: int = 6):
+    regions = [394463, 394910, 394338, 753899, 394357, 394466, 394596, 395107]
+    pred_service = PredictionService()
+    summaries = []
+
     for region in regions:
+        print(f"\n{'='*60}")
+        print(f"Region: {region}")
+        print(f"{'='*60}")
+
         async with AsyncPostgresConnector(...) as db:
             result = await db.fetch_all(...)

-            for r in result:
-                data.append([r[5], r[6]])
-
-    pred_service = PredictionService()
-    training_data = pred_service.generate_training_set(data, cutoff)
-    test_data = pred_service.generate_test_set(data, cutoff)
-
-    print(f"[DEBUG] Full set count: {len(data)}")
-    if training_data:
-        print(f"[DEBUG] First entry: {data[0][0]} -> ${data[0][1]:,.2f}")
-        print(f"[DEBUG] Last entry:  {data[-1][0]} -> ${data[-1][1]:,.2f}")
-    print(f"[DEBUG] Training set count: {len(training_data)}")
-    if training_data:
-        print(f"[DEBUG] First entry: {training_data[0][0]} -> ${training_data[0][1]:,.2f}")
-        print(f"[DEBUG] Last entry:  {training_data[-1][0]} -> ${training_data[-1][1]:,.2f}")
-    print(f"\n[DEBUG] Testing set count: {len(test_data)}")
-    if test_data:
-        print(f"[DEBUG] First entry: {test_data[0][0]} -> ${test_data[0][1]:,.2f}")
-        print(f"[DEBUG] Last entry:  {test_data[-1][0]} -> ${test_data[-1][1]:,.2f}")
-
-    _, patterns, _, _, _, training_frequencies, _, _, _ = pred_service.run(training_data, group_size=3)
-    print(f"Training frequencies: {training_frequencies}")
-
-    change_hist = pred_service.get_changes(training_data, group_size=3)
-    pred_service.predict(test_data, patterns, training_frequencies, start_month, change_hist)
+        data = []
+        for r in result:
+            data.append([r[5], r[6]])
+
+        training_data = pred_service.generate_training_set(data, cutoff)
+        test_data = pred_service.generate_test_set(data, cutoff)
+
+        print(f"[DEBUG] Full set count: {len(data)}")
+        if training_data:
+            print(f"[DEBUG] Training: {training_data[0][0]} -> {training_data[-1][0]}")
+        if test_data:
+            print(f"[DEBUG] Test:     {test_data[0][0]} -> {test_data[-1][0]}")
+
+        _, patterns, _, _, _, training_frequencies, _, _, _ = pred_service.run(training_data, group_size=group_size)
+        print(f"Training frequencies: {training_frequencies}")
+
+        change_hist = pred_service.get_changes(training_data, group_size=group_size)
+        extended_test = list(training_data[-group_size:]) + list(test_data)
+        summary = pred_service.predict(extended_test, patterns, training_frequencies, start_month, change_hist, group_size=group_size, k=k)
+        if summary:
+            summaries.append({"region": region, **summary})
+
+    if summaries:
+        print(f"\n\n{'='*75}")
+        print(f"FINAL SUMMARY")
+        print(f"{'='*75}")
+        print(f"{'Region':<12} {'Correct':>8} {'Total':>7} {'Accuracy':>10} {'MSE':>14} {'RMSE':>12}")
+        print(f"{'-'*75}")
+        for s in summaries:
+            print(f"{s['region']:<12} {s['correct']:>8} {s['total']:>7} {s['accuracy']:>9.0%} {s['mse']:>14,.2f} {s['rmse']:>12,.2f}")
+        print(f"{'='*75}")

 if __name__ == "__main__":
     parser = argparse.ArgumentParser(...)
     parser.add_argument("--year", ...)
     parser.add_argument("--month", ...)
+    parser.add_argument("--group-size", "-g", type=int, default=3, choices=[3, 4, 5],
+                        help="Group size for pattern matching (default: 3)")
+    parser.add_argument("--k", type=int, default=6, choices=[1, 3, 5, 7, 9],
+                        help="k nearest neighbors for magnitude estimation (default: 6)")
     args = parser.parse_args()
-    asyncio.run(main(args.year, args.month))
+    asyncio.run(main(args.year, args.month, args.group_size, args.k))
```
