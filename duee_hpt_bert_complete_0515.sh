#!/bin/bash

# lr : 0.0005,0.00075, 0.001
# ner_loss:  0.01, 0.02
# dropout: 0.1, 0.2, 0.3
# batch size & GAS: 32 & 4

t="_"
log=".log"
model_type="duee_hpt_bert_lr"
#a64="64"
#a32="32"
batch_size="32"
dropout="0.3"
ner_loss="0.01"
lr="0.001"
gas="4"
########################### this is the best hp setting #####################
                log_version=$model_type$t$lr$t$dropout$t$ner_loss$t$batch_size$t$gas$log
                log_path=./Logs/${log_version}
                echo "task name: ${log_version}"
                nohup sh ./scripts/run_ptpcg_dueefin_hpt_bert_complete_0508.sh ${dropout} ${ner_loss} ${batch_size} ${gas} ${lr}> ${log_path} 2>&1 &
                wait $!	
##############################################################################

lr="0.00075"
gas="4"
                log_version=$model_type$t$lr$t$dropout$t$ner_loss$t$batch_size$t$gas$log
                log_path=./Logs/${log_version}
                echo "task name: ${log_version}"
                nohup sh ./scripts/run_ptpcg_dueefin_hpt_bert_complete_0508.sh ${dropout} ${ner_loss} ${batch_size} ${gas} ${lr}> ${log_path} 2>&1 &
                wait $!

ner_loss="0.02"
gas="4"
                log_version=$model_type$t$lr$t$dropout$t$ner_loss$t$batch_size$t$gas$log
                log_path=./Logs/${log_version}
                echo "task name: ${log_version}"
                nohup sh ./scripts/run_ptpcg_dueefin_hpt_bert_complete_0508.sh ${dropout} ${ner_loss} ${batch_size} ${gas} ${lr}> ${log_path} 2>&1 &
                wait $!
lr="0.0005"
gas="4"
                log_version=$model_type$t$lr$t$dropout$t$ner_loss$t$batch_size$t$gas$log
                log_path=./Logs/${log_version}
                echo "task name: ${log_version}"
                nohup sh ./scripts/run_ptpcg_dueefin_hpt_bert_complete_0508.sh ${dropout} ${ner_loss} ${batch_size} ${gas} ${lr}> ${log_path} 2>&1 &
                wait $!
lr="0.001"
gas="4"
                log_version=$model_type$t$lr$t$dropout$t$ner_loss$t$batch_size$t$gas$log
                log_path=./Logs/${log_version}
                echo "task name: ${log_version}"
                nohup sh ./scripts/run_ptpcg_dueefin_hpt_bert_complete_0508.sh ${dropout} ${ner_loss} ${batch_size} ${gas} ${lr}> ${log_path} 2>&1 &
                wait $!
echo 'ok'
