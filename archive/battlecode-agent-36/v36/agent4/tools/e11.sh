#!/bin/bash
# E11: near-miss confirmations on p-confirm maps 201-700 (engine 1.0.1)
for d in "APEX_TRIBUTE_CARRY=48" "APEX_END_BANK=400" "NOVA_GOLD_UNSEEN=0.05f"; do
  OFFSET=200 LIMIT=500 bash tune.sh "e11_$(echo $d | tr '=.' '__')" p-confirm "$d"
done
