# Sample application

This directory contains sample files that can be used with the
 [RUNBOOK](../RUNBOOK.md).

> Use case: A third party supplies a Python application (ML inference script)
> together with a ML model (ResNet50 - image classification) and a labels file.
> The enclave host will use their own dataset (one .jpg file) and will classify
> it with the confidential third party application running inside a Nitro enclave.

Check the [NOTICE](../NOTICE) file for external files attribution.

|File              |Description |Purpose       |
|:-----------------|:-----------|:-------------|
|resnet50-v1-7.onnx|Image classification ML model|Part of the encrypted application zip file|
|synset.txt|Labels for the ML model |Part of the encrypted application zip file|
|dataset/kitten.jpg|Input file to classify with the ML model|Plaintext file|
|output/results.txt|Expected output file from the ML model once run|Plaintext file|

## Usage

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

python3 client.py run -f application_code.zip.encrypted -s ml-inference.py -a "classify -m resnet50-v1-7.onnx -l synset.txt -d /dataset/ -o /output/"

cat ~/synced/output/results.txt
```

Check the *results.txt* file written by the enclave matches the contents from the
 *output/results.txt* file supplied in this sample.
 
