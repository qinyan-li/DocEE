#!/bin/bash

{
    MODEL_NAME='TriggerAwarePrunedCompleteGraph'
    TASK_NAME='PTPCG_P1-DuEE_fin'
    echo "('${TASK_NAME}', '${MODEL_NAME}'),    # $(date)" >> RECORDS.md
    echo "Task Name: $TASK_NAME"
    echo "Model Name: $MODEL_NAME"

    # GPU_SCOPE="0,1,2,3"
    # REQ_GPU_NUM=1
    GPUS="0"
    # GPUS=$(python wait.py --task_name="$TASK_NAME" --cuda=$GPU_SCOPE --wait="schedule" --req_gpu_num=$REQ_GPU_NUM)
    echo "GPUS: $GPUS"
    EPOCH_NUM=100

    if [[ -z "$GPUS" ]]; then
        echo "GPUS is empty, stop..."
        # python send_message.py "Task $TASK_NAME not started due to empty gpu assigning, please check the log."
        echo "Task $TASK_NAME not started due to empty gpu assigning, please check the log."
    else
        echo "GPU ready."
        # python send_message.py "Task $TASK_NAME started."
        echo "Task $TASK_NAME started."
       

        # run on inference dataset
        CUDA_VISIBLE_DEVICES=${GPUS} python -u run_dee_task.py \
            --data_dir='Data/news' \
            --task_name=${TASK_NAME} \
            --model_type=${MODEL_NAME} \
            --cpt_file_name=${MODEL_NAME} \
            --eval_batch_size=16 \
            --run_mode='news_without_trigger' \
            --filtered_data_types='o2o,o2m,m2m,unk' \
            --skip_train=True \
            --load_dev=False \
            --load_test=False \
            --load_inference=True \
            --inference_epoch=-1 \
            --run_inference=True \
            --inference_dump_filepath='news_submit_new.json' \
            --add_greedy_dec=False
    fi

    # check if the process has finished normally
    LOG_FILE="Logs/$TASK_NAME.log"
    if [[ -f "$LOG_FILE" ]]; then
        echo "$LOG_FILE exists."
        MATCHED=$(grep 'Combination' "$LOG_FILE")
        if [[ -z "$MATCHED" ]]; then
            # python send_message.py " Something's wrong in task $TASK_NAME, please check the log."
            echo " Something's wrong in task $TASK_NAME, please check the log."
        else
            # python send_message.py --send_result --task_name ${TASK_NAME} --model_name ${MODEL_NAME} --max_epoch ${EPOCH_NUM} "Task $TASK_NAME finished."
            echo "Task $TASK_NAME finished."
        fi
    else
        echo "$LOG_FILE not found."
        # python send_message.py "Task $TASK_NAME finished, but log is not found."
        echo "Task $TASK_NAME finished, but log is not found."
    fi

    exit
}
