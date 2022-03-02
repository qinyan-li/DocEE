TASK_NAME='GIT_DuEE_fin_with_trigger'
CUDA='0'
NUM_GPU=1
MODEL_NAME='GITModel'
RUN_MODE='luge_with_trigger'
TEMPLATE='luge_with_trigger'
INFERENCE_DUMPPATH='git_duee_fin_with_trigger.json'


CUDA_VISIBLE_DEVICES=${CUDA} bash scripts/train_multi.sh ${NUM_GPU} --task_name ${TASK_NAME}\
    --data_dir='Data/DuEEData' \
    --bert_model='bert-base-chinese' \
    --model_type=${MODEL_NAME} \
    --cpt_file_name=${MODEL_NAME} \
    --add_greedy_dec=False \
    --ner_num_tf_layers=8 \
    --gradient_accumulation_steps=16 \
    --train_batch_size=16 \
    --eval_batch_size=2 \
    --resume_latest_cpt=False \
    --num_train_epochs=100 \
    --run_mode="${RUN_MODE}" \
    --event_type_template="${TEMPLATE}" \
    --skip_train=False \
    --load_dev=True \
    --load_test=True \
    --load_inference=False \
    --inference_epoch=-1 \
    --run_inference=False \
    --inference_dump_filepath="${INFERENCE_DUMPPATH}" \
    --skip_train=False \
    --parallel_decorate

# run on inference dataset
CUDA_VISIBLE_DEVICES=${GPUS} python -u run_dee_task.py \
    --data_dir='Data/DuEEData' \
    --task_name=${TASK_NAME} \
    --model_type=${MODEL_NAME} \
    --cpt_file_name=${MODEL_NAME} \
    --eval_batch_size=16 \
    --run_mode="${RUN_MODE}" \
    --filtered_data_types='o2o,o2m,m2m,unk' \
    --skip_train=True \
    --load_dev=False \
    --load_test=False \
    --load_inference=True \
    --inference_epoch=-1 \
    --run_inference=True \
    --inference_dump_filepath="${INFERENCE_DUMPPATH}" \
    --add_greedy_dec=False
