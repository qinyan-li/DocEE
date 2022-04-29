#!/bin/bash

# lr : 0.0005
# ner_loss: 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.02
# dropout: 0.1, 0.2, 0.3
# batch size & GAS: 32 & 4, 64 & 8

t="_"
log=".log"
model_type="duee"
for dropout in "0.1" "0.2" "0.3"
do
    for ner_loss in "0.0005" "0.001" "0.0025" "0.005" "0.01" "0.02"
    do
        for batch_size in "64" "32"
        do
            for gas in "4" "8"
            do
                log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
                log_path=./Logs/${log_version}
                nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
                wait
            done
            wait
        done
        wait
    done
    wait
done

echo 'ok'
