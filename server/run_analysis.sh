#!/bin/zsh

PYTHON=/opt/anaconda3/bin/python3

GROUP_SIZES=(1 2 3 4 6 12)
K_VALUES=(1 3 5 7 9 11)
REGIONS=(394463 394910 394338 753899 394357 394466 394596 395107)

mkdir -p logs

for region in "${REGIONS[@]}"; do
  rm -f "logs/region_${region}.txt"
  echo ""
  echo "================================================================"
  echo "  region=${region}"
  echo "================================================================"

  for g in "${GROUP_SIZES[@]}"; do
    for k in "${K_VALUES[@]}"; do
      echo ""
      echo "  group_size=${g}  k=${k}"
      $PYTHON analyze.py --region "$region" --group-size "$g" --k "$k"
    done
  done
done
