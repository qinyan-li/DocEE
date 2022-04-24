# GPU Resources

# AWS

aws,siemens.cloud
[han.zhen@siemens.com](mailto:han.zhen@siemens.com)
?ExTKGTeamPWD2021?

ec2

密钥

1h的一个空闲关闭监视
instance stoppen是关闭
beenden是销毁

# Connect VPN or Connect CIP Pool

- VPN, eduVPN [link](https://doku.lrz.de/pages/viewpage.action?pageId=87425051)
- CIP Pool
    
    ```bash
    ssh chensh@remote.cip.ifi.lmu.de
    ```
    

# Connect File Server

```bash
ssh zhang@crestfall.dbs.ifi.lmu.de

# or 

ssh zhang@balor.dbs.ifi.lmu.de # with GPU on server 

ssh zhang@darkmoon.dbs.ifi.lmu.de # with GPU on server 

ssh zhang@astranaar.dbs.ifi.lmu.de # with GPU on server and conda 

ssh zhang@zandalar.dbs.ifi.lmu.de # use this to submit task to the GPU cluster 

# oettingen67

ssh zhang@darkmoon.dbs.ifi.lmu.de
```

# Edit bash script

```bash
#!/usr/bin/env bash
#
#SBATCH --job-name torch-test
#SBATCH --output=res.txt
#SBATCH --ntasks=1
#SBATCH --time=10:00
#SBATCH --gres=gpu:1

# debug info
hostname
which python3
nvidia-smi

env

# venv
python3 -m venv ./venv/test
source ./venv/test/bin/activate
pip install -U pip setuptools wheel
pip install requests
# For CUDA 11, we need to explicitly request the correct version
pip install torch==1.8.0+cu111 torchvision==0.9.0+cu111 -f https://download.pytorch.org/whl/torch_stable.html

# test cuda
python3 -c "import torch; print(torch.cuda.device_count())"

# download example script for CNN training
SRC=src/${SLURM_ARRAY_JOB_ID}
mkdir -p ${SRC}
wget https://raw.githubusercontent.com/pytorch/examples/master/mnist/main.py -O ${SRC}/torch-test.py
cd ${SRC}

# train
python3 ./torch-test.py
```

## Remarks

```bash
In your HOME is a file slurmtest.sh for example.
Run it with:
sbatch slurmtest.sh
or
srun slurmtest.sh (maybe easier for debugging)

Use always this header in your slurm-environment:

#!/usr/bin/env bash
#
#SBATCH --job-name torch-test
#SBATCH --output=res.txt
#SBATCH --ntasks=1
#SBATCH --time=10:00
#SBATCH --gres=gpu:1
```

```bash
Please use virtual environments for Python. You can either use venv
("python3 -m venv") or install Anaconda in your home directory.

You may need to update your existing Python environments. For PyTorch,
the default pip version is for CUDA 10. You can follow the instructions
on https://pytorch.org/get-started/locally/ to obtain a CUDA 11
compatible installation. For tensorflow, the default version seems to be
CUDA 11 (cf. https://www.tensorflow.org/install/gpu).
```

# File Directory

```bash
zhang@zandalar.dbs.ifi.lmu.de:/mnt/data3/zhang 
```

## Remark

```bash
zandalar ist nur der Fileserver und Slurm-Client. Die eigentlichen GPU-Server sind "worker-1" und "worker-2", auf die man aber keinen direkten Zugriff hat.

Die aktuelle Auslastung sieht man hier:
https://www.dbs.ifi.lmu.de/~krojer/share/gpu.html

Siehe auch:
https://gitlab.lrz.de/dbs/tools/slurm
Here, for example Max Berrendorf or Julian Busch, can give you some helps and discussions. Here is also the FAQ.
```