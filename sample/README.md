# Sample application

This directory contains sample files that can be used with the
 [RUNBOOK](../RUNBOOK.md).

> Use case: A third party supplies a Python application (ML inference script)
> together with a ML model (ResNet50 - image classification) and a labels file.
> The enclave host will use their own dataset (one .jpg file) and will classify
> it with the confidential third party application running inside a Nitro enclave.

Check the [NOTICE](../NOTICE) file for external files attribution.

## Setup

Tested on a c7g.4xlarge EC2 instance in region eu-west-1 (Ireland) with
 AMI: amzn2-ami-kernel-5.10-hvm-2.0.20221004.0-arm64-gp2.

The nitro-enclave-image.eif built for this sample should be 2.2GB.

The sample cmd to start the enclave:
```
sudo nitro-cli run-enclave --cpu-count 2 -memory 10000 --eif-path nitro-enclave-image.eif 
```

## Usage

Download these 3 files:
- dataset: https://s3.amazonaws.com/model-server/inputs/kitten.jpg
- model: https://storage.googleapis.com/tensorflow/keras-applications/resnet/resnet50_weights_tf_dim_ordering_tf_kernels.h5
- labels: https://storage.googleapis.com/download.tensorflow.org/data/imagenet_class_index.json

Copy *ml-inference.py*, *resnet50_weights_tf_dim_ordering_tf_kernels.h5*,
 and *imagenet_class_index.json* to the */src* directory in the CodeCommit
 repo from the
 [RUNBOOK - Step 2.1](../RUNBOOK.md#21-create-git-repository-and-upload-files).

Ensure you replace the 2 files: *Dockerfile* and *requirements.txt*
 from the */src/server/containers/enclave_app* with the version
 supplied in the *enclave_app* folder provided for this sample.
 This step is required to ensure all the prerequisite packages
 are installed correctly before you can run the ML inference
 script in this sample.

Follow all the instructions in the [RUNBOOK](../RUNBOOK.md).
 For [Step 4.5.](../RUNBOOK.md#45-use-enclave), after syncing the
 local directory to the enclave, follow these steps:

```console
cp <location>/application_code.zip.encrypted ~/synced/encrypted/

cp <location>/kitten.jpg ~/synced/dataset

python3 client.py run -f application_code.zip.encrypted -s ml-inference.py -a "classify -m resnet50_weights_tf_dim_ordering_tf_kernels.h5 -l imagenet_class_index.json -d /dataset/ -o /output/"

cat ~/synced/output/results.txt
```
