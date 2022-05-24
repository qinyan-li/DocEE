#!/bin/bash

# lr : 0.0005
# ner_loss: 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.02
# dropout: 0.1, 0.2, 0.3
# batch size & GAS: 32 & 4, 64 & 8

t="_"
log=".log"
model_type="duee_hpt_lr0.0005"
batch_size="32"
gas="4"
#1
dropout="0.1"
ner_loss="0.02"
log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
log_path=./Logs/${log_version}
echo "task name: ${log_version}"
nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
wait $!
#2
dropout="0.2"
ner_loss="0.02"
log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
log_path=./Logs/${log_version}
echo "task name: ${log_version}"
nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
wait $!
#3
dropout="0.1"
ner_loss="0.01"
log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
log_path=./Logs/${log_version}
echo "task name: ${log_version}"
nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
wait $!
#4
dropout="0.1"
ner_loss="0.0025"
log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
log_path=./Logs/${log_version}
echo "task name: ${log_version}"
nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
wait $!
#5
dropout="0.1"
ner_loss="0.005"
log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
log_path=./Logs/${log_version}
echo "task name: ${log_version}"
nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
wait $!
#6
dropout="0.2"
ner_loss="0.005"
log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
log_path=./Logs/${log_version}
echo "task name: ${log_version}"
nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
wait $!
#7
dropout="0.3"
ner_loss="0.01"
log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
log_path=./Logs/${log_version}
echo "task name: ${log_version}"
nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
wait $!
#8
dropout="0.2"
ner_loss="0.01"
log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
log_path=./Logs/${log_version}
echo "task name: ${log_version}"
nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
wait $!
#9
dropout="0.3"
ner_loss="0.02"
log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
log_path=./Logs/${log_version}
echo "task name: ${log_version}"
nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
wait $!
#10
dropout="0.3"
ner_loss="0.005"
log_version=$model_type$t$dropout$t$ner_loss$t$batch_size$t$gas$log
log_path=./Logs/${log_version}
echo "task name: ${log_version}"
nohup sh ./scripts/run_ptpcg_dueefin_hpt_0.0005_0429.sh ${dropout} ${ner_loss} ${batch_size} ${gas} > ${log_path} 2>&1 &
wait $!

echo 'ok'
