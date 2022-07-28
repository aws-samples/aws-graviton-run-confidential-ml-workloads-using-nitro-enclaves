- [Runbook](#runbook)
  - [AWS Accounts](#aws-accounts)
  - [User Personas](#user-personas)
  - [User Guide](#user-guide)
    - [1. Enclave Administrator](#1-enclave-administrator)
      - [1.1. Setup Third Party Storage](#11-setup-third-party-storage)
    - [2. Third Party](#2-third-party)
      - [2.1. Create Git Repository and Upload Files](#21-create-git-repository-and-upload-files)
      - [2.2. Deploy Automated Builders](#22-deploy-automated-builders)
        - [2.2.1. Application Encryptor](#221-application-encryptor)
        - [2.2.2. Enclave Image Builder](#222-enclave-image-builder)
      - [2.3. Run Automated Builders](#23-run-automated-builders)
        - [2.3.1. Encrypt and Share Application](#231-encrypt-and-share-application)
        - [2.3.2. Create and Share Enclave Image](#232-create-and-share-enclave-image)
    - [3. Enclave Administrator](#3-enclave-administrator)
      - [3.1. Create EC2 Linux Instance with Nitro Enclaves Support](#31-create-ec2-linux-instance-with-nitro-enclaves-support)
      - [3.2. Update IAM Role](#32-update-iam-role)
      - [3.3. Reserve Enclave Resources](#33-reserve-enclave-resources)
    - [4. Enclave User](#4-enclave-user)
      - [4.1. Download Files](#41-download-files)
      - [4.2. Install Packages](#42-install-packages)
      - [4.3. Start Enclave](#43-start-enclave)
      - [4.4. Start KMS Proxy](#44-start-kms-proxy)
      - [4.5. Use Enclave](#45-use-enclave)
    - [5. Clean Up](#5-clean-up)
      - [5.1. Enclave User](#51-enclave-user)
      - [5.2. Enclave Administrator](#52-enclave-administrator)
    - [6. Revoke Access](#6-revoke-access)
      - [6.1. Enclave Administrator](#61-enclave-administrator)
      - [6.2. Third Party](#62-third-party)

---

# Runbook

---

---

## AWS Accounts

---

|Account Name        |Description |
|:-------------------|:-----------|
|Enclave Host Account|Hosts EC2 Linux instances running Nitro enclaves and S3 buckets shared with Third Party Accounts|
|Third Party Account |Hosts proprietary sensitive applications and data. It builds Nitro image files capable of running the encrypted applications and shares these files with an Enclave Host Account|

---

## User Personas

---

|Role Name            |Description |AWS Account|
|:--------------------|:-----------|:----------|
|Enclave Administrator|Creates S3 buckets to share with Third Parties and performs the required setup for EC2 instances running Nitro enclaves  | Enclave Host Account |
|Enclave User         |Runs Nitro enclaves on EC2 instances and performs activities on the running enclave using the provided client application| Enclave Host Account |
|Third Party          |Encrypts and shares applications and data alongside Nitro enclave image files that can run the encrypted applications    | Third Party Account  |

> Note: The Enclave Administrator and Enclave User roles can be assumed by the same person

---

## User Guide

---

> Important Note: In this use case, the host trusts the files shared
 by the Third Party as it can't verify the contents of either the
 Nitro image file nor the encrypted applications and data. If required,
 the trust relationship must be established through additional technical
 controls to mitigate any risks (should any exist) or through legal means.

This user guide provides the end to end process to create and operate
 an enclave designed to run encrypted third party applications that must
 remain confidential to the enclave resources owner (host).

Follow the steps provided in sequential order first. Some instructions
 can be run ad-hoc and there will be notes where that is applicable.

---

### 1. Enclave Administrator

---

---

#### 1.1. Setup Third Party Storage

---

On the host's AWS account, the Enclave Administrator will create a S3 bucket
 for a third party for sharing purposes. The Third Party can use it to upload
 files as many times as needed, such as the Nitro enclave image file and any
 encrypted applications and data.

Log in to the [AWS Management Console](https://console.aws.amazon.com/) using
 sufficient privileges or Admin access.

- [ ] Go to service AWS CloudFormation
- [ ] Select the *Stacks* menu option
- [ ] Use button *Create Stack with new resources*
- [ ] Select option *Upload a template file* to upload the
 [third party sharing bucket](../src/onboarding/Deploy-ApplicationSharingBucket-Cfn.yaml) and press on *Next*
- [ ] Provide *Stack name*: "ProjectName-FileSharing-ThirdPartyName". Add the parameters required.
 Press on button *Next* twice and then press on button *Create stack*.

|Parameter Name|Description|Default value|
|:-----------------|:-----------|:-------------|
|ThirdPartyAWSAccountNumber|AWS Account number provided by Third Party. This is the account number the third party will use to upload the encrypted applications and enclave images|*No default - must be specified*|
|ThirdPartyName|A short string to identify which Third Party supplies the files that will be put in this bucket|*No default - must be specified*|

Once the CloudFormation stack is created, note the bucket name and the KMS key ARN listed as outputs.

---

### 2. Third Party

---

Use the automated builders provided to package and encrypt applications and
 build enclave image files. The resulting protected files will be shared
 with the enclave host using the S3 bucket they provided in
 [Step 1.1](#11-setup-third-party-storage).

---

#### 2.1. Create Git Repository and Upload Files

---

Create an AWS CodeCommit Git repository to host the source code.

Log in to the [AWS Management Console](https://console.aws.amazon.com/) using
 sufficient privileges or Admin access.

- [ ] Go to service AWS CodeCommit
- [ ] Click on the *Create repository* button. Provide a repository name and
 press on the *Create* button.

Use the AWS Management Console or another Git utility to upload the following
 files in this proposed directory structure:

- [ ] *src/* - upload your application code and data (e.g. machine learning model)
- [ ] *containers/* - upload the [server application code](../src/server/containers/)
- [ ] top-level - upload [envelope_encryptor.py](../src/encryption/envelope_encryptor.py)

Helper commands:
```
git clone codecommit://repo-name repo-name
```

---

#### 2.2. Deploy Automated Builders

---

Deploy the infrastructure-as-code CloudFormation templates that provide the automation
 to encrypt applications and build enclave image files.

---

##### 2.2.1. Application Encryptor

---

Log in to the [AWS Management Console](https://console.aws.amazon.com/) using
 sufficient privileges or Admin access.

- [ ] Go to service AWS CloudFormation
- [ ] Select the *Stacks* menu option
- [ ] Use button *Create Stack with new resources*
- [ ] Select option *Upload a template file* to upload the
 [application encryptor](../src/encryption/Deploy-ApplicationEncryptor-Cfn.yaml) and press on *Next*
- [ ] Provide *Stack name*: "ApplicationEncryptor". Add the parameters required.
 Press on button *Next* twice and then press on button *Create stack*.

|Parameter Name|Description|Default value|
|:-----------------|:-----------|:-------------|
|CodeCommitRepositoryName|The name of the CodeCommit repository created in [Step 2.1](#21-create-git-repository-and-upload-files)|*No default - must be specified*|
|ApplicationCodeDirectoryName|The name of the directory in the CodeCommit repo where you uploaded your files in [Step 2.1](#21-create-git-repository-and-upload-files)|*No default - must be specified*|
|ApplicationCodeS3Path|Amazon S3 path where the confidential application should be uploaded to be shared with the enclave host.|*No default - must be specified*|
|EncryptionKeyAlias|The KMS key used to encrypt the application code and data|*alias/enclavekey*|
|HostAWSAccountNumber|Enclave Administrator will provide the value based on [Step 1.1](#11-setup-third-party-storage) Outputs|*No default - must be specified*|
|HostEncryptionKeyArn|Enclave Administrator will provide the value based on [Step 1.1](#11-setup-third-party-storage) Outputs|*No default - must be specified*|

---

##### 2.2.2. Enclave Image Builder

---

Log in to the [AWS Management Console](https://console.aws.amazon.com/) using
 sufficient privileges or Admin access.

- [ ] Go to service AWS CloudFormation
- [ ] Select the *Stacks* menu option
- [ ] Use button *Create Stack with new resources*
- [ ] Select option *Upload a template file* to upload the
 [enclave image builder](../src/builder/Deploy-NitroImageBuilder-Cfn.yaml) and press on *Next*
- [ ] Provide *Stack name*: "NitroImageBuilder". Add the parameters required.
 Press on button *Next* twice and then press on button *Create stack*.

|Parameter Name|Description|Default value|
|:-----------------|:-----------|:-------------|
|CodeCommitRepositoryName|The name of the CodeCommit repository created in [Step 2.1](#21-create-git-repository-and-upload-files)|*No default - must be specified*|
|NitroImageS3Path|Amazon S3 path where the enclave image should be uploaded to.|*No default - must be specified*|
|HostEncryptionKeyArn|Enclave Administrator will provide the value based on [Step 1.1](#11-setup-third-party-storage) Outputs|*No default - must be specified*|

---

#### 2.3. Run Automated Builders

---

[Step 2.2](#22-deploy-automated-builders) just creates the necessary
 infrastructure to run the automation.
 A manual action to start the automated process is required as per the
 instructions below. These steps can be run as many times as necessary
 when they make sense. For example:

- When the server application changes or the packages and libraries are changed
 for the enclave image file, you can trigger the enclave image builder again.
- When you have a new application version or want to change the application,
 you can run the automated encryptor again.

---

##### 2.3.1 Encrypt and Share Application

---

Run the AWS CodeBuild project to encrypt and upload the encrypted application
 into the enclave host's account in the storage area provided in
 [Step 1.1](#11-setup-third-party-storage).

Log in to the [AWS Management Console](https://console.aws.amazon.com/) using
 sufficient privileges or Admin access.

- [ ] Go to service AWS CodeBuild
- [ ] Select the radio button for the **application-encryptor** CodeBuild project.
 Press on *Start Build -> Start Now*.

While the build is in progress, logs will be printed as the job progresses.
 In around 2-3 minutes, the status of the build should change to **Succeeded**.
 At this point an encrypted version of the application directory has been
 uploaded to the S3 bucket owned by the enclave host account and shared in
 [Step 1.1](#11-setup-third-party-storage).

---

##### 2.3.2. Create and Share Enclave Image

---

Run the AWS CodeBuild project to create and upload the nitro enclave image file
 into the enclave host's account in the storage area provided in
 [Step 1.1](#11-setup-third-party-storage).

Log in to the [AWS Management Console](https://console.aws.amazon.com/) using
 sufficient privileges or Admin access.

- [ ] Go to service AWS CodeBuild
- [ ] Select the radio button for the **nitro-image-builder** CodeBuild project.
 Press on *Start Build -> Start Now*.

While the build is in progress, logs will be printed as the job progresses.
 In around 20-25 minutes, the status of the build should change to **Succeeded**.
 At this point the Nitro enclave image file (.eif) has been uploaded to the S3
 bucket owned by the enclave host account and shared in
 [Step 1.1](#11-setup-third-party-storage).

The KMS key used to encrypt the applications using the automated application
 encryptor as per [Step 2.2.1](#221-application-encryptor) has a resource-based
 policy. This builder will update the policy to only allow this updated enclave
 image to decrypt using this key.

---

### 3. Enclave Administrator

---

---

#### 3.1. Create EC2 Linux Instance with Nitro Enclaves Support

---

> Note: Only EC2 instances with the Amazon Linux 2 AMI have been tested
 (example AMI: amzn2-ami-kernel-5.10-hvm-2.0.20221004.0-arm64-gp2)

Log in to the [AWS Management Console](https://console.aws.amazon.com/) using
 sufficient privileges or Admin access.

- [ ] Go to service Amazon EC2
- [ ] Create a Linux EC2 instance for the Arm64 architecture (e.g. c6g, c7g, etc.)
 with Nitro Enclaves support enabled (In the step where you *Configure Instance Details*
 under *Advanced Details", ensure *Nitro Enclave* is enabled)

> Note: Select an instance type which has at least 4 times the memory of the size
> of the enclave image supplied by the Third Party in
 [Step 2.3.2](#232-create-and-share-enclave-image).

---

### 3.2. Update IAM Role

---

The EC2 instance created in
 [Step 3.1](#31-create-ec2-linux-instance-with-nitro-enclaves-support)
 needs an additional policy for its IAM role.
 This inline policy is used by the kmstool-enclave-cli tool in the server application
 to make decrypt calls to AWS KMS.

If there is no IAM role attached to the EC2 instance already, create a new one and
 use *Modify IAM role* on the EC2 instance to attach it.

Log in to the [AWS Management Console](https://console.aws.amazon.com/) using
 sufficient privileges or Admin access.

- [ ] Go to service Amazon EC2
- [ ] Select the EC2 instance from
 [Step 3.1](#31-create-ec2-linux-instance-with-nitro-enclaves-support)
 and view the *Security* tab
- [ ] Click on the link for the *IAM role* which should open AWS IAM
- [ ] Select *Add permissions -> Create inline policy -> JSON*. Copy and paste the
 policy provided below. Press on *Review policy*. Add a name for the policy
 e.g. "ThirdPartyKMSKeyAccessPolicy". Press on button *Create policy*.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "RequiredByKmstoolEnclaveCliToAllowDecryptionFromTheEnclave",
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": "*"
        }
    ]
}
```

> Notice the policy is set to allow the action specified on all resources. Ideally,
> the Enclave Administrator should know the KMS CMK ARN name for the Third
> Party's key that was used to encrypt the shared application. This could be used
> to restrict the policy to least privilege rights.

---

### 3.3. Reserve Enclave Resources

---

- [ ] Log in to the Linux EC2 instance created in
 [Step 3.1](#31-create-ec2-linux-instance-with-nitro-enclaves-support).
- [ ] Change the max limit for memory allocation in the Nitro enclave allocator service
 by running the command below. Note the value "20480" is just an example.

> The value must be at least 4 times larger than the size of the Nitro enclave
> image file (.eif) provided by the Third Party in
> [Step 2.3.2](#232-create-and-share-enclave-image), otherwise the
> `sudo nitro-cli run-enclave` command to start the enclave will fail.

```console
sudo amazon-linux-extras install aws-nitro-enclaves-cli -y
sudo sed -r "s/^(\s*memory_mib\s*:\s*).*/\120480/" -i /etc/nitro_enclaves/allocator.yaml
```

- [ ] Restart the allocator service for the change to take effect:

```console
sudo systemctl restart nitro-enclaves-allocator.service && sudo systemctl enable nitro-enclaves-allocator.service &&
sudo systemctl status nitro-enclaves-allocator.service
```

Follow a similar procedure if you need to adjust the CPU cores used.

---

### 4. Enclave User

---

Run the following steps on the Linux EC2 instance created in
 [Step 3.1](#31-create-ec2-linux-instance-with-nitro-enclaves-support).

---

### 4.1. Download Files

---

- [ ] Install the AWS CLI using these
 [instructions](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [ ] Using the AWS CLI, download the files shared by the Third Party
 in the S3 bucket provisioned in [Step 1.1](#11-setup-third-party-storage)
- [ ] Download the open-source client application
- [ ] Download any additional data you might need (e.g. datasets from S3)

---

### 4.2. Install Packages

---

- [ ] Verify that the nitro-cli is installed by running `nitro-cli --version`

- [ ] Run these commands to install the prerequisites for the client application:

```console
sudo yum update
sudo yum install fuse
sudo yum install fuse-libs
sudo yum -y install python3-pip
pip3 install requests
pip3 install fusepy
```

---

### 4.3. Start Enclave

---

Use the Nitro enclave image (.eif) provided by the Third Party in
 [Step 2.3.2](#232-create-and-share-enclave-image). One way to do so
 is to copy the file from the S3 bucket onto this EC2 instance using e.g.:
```
aws s3api get-object --bucket bucket_name --key enclave/nitro-enclave-image.eif nitro-enclave-image.eif
```

- [ ] Start the enclave. Replace ENCLAVE_CPU_COUNT, ENCLAVE_MEMORY, and
 ENCLAVE_IMAGE_PATH with the number of vCPUs to allocate to the enclave, the amount
 of memory (in MiB) to allocate to the enclave, and the path to the enclave
 image file respectively.

```console
sudo nitro-cli run-enclave --cpu-count ENCLAVE_CPU_COUNT --memory ENCLAVE_MEMORY --eif-path ENCLAVE_IMAGE_PATH
```

Refer to the [nitro-cli documentation](https://docs.aws.amazon.com/enclaves/latest/user/cmd-nitro-run-enclave.html)
 to learn more about the command line options.

- [ ] Verify if the enclave is indeed running. You should see the status: RUNNING.

```console
sudo nitro-cli describe-enclaves
```

---

### 4.4. Start KMS Proxy

---

- [ ] Download from this repository the [client application](./src/client) and use it to start the
 [vsock_proxy program](https://github.com/aws/aws-nitro-enclaves-cli/tree/main/vsock_proxy)
 that allows the enclave to communicate with the AWS KMS service.

```console
python3 client.py proxy -s kms
```

- [ ] Verify the vsock_proxy has started:

```console
ps -ef | grep [v]sock-proxy
```

---

### 4.5. Use Enclave

---

- [ ] Use the client application to interact with the running enclave.
 Details on the commands that the client supports can be found in the
 [technical documentation](./docs/Client.md#Commands)

For example, to create a directory that is synced bidirectionally with
 the enclave and to prepare the directories needed to operate with the
 enclave, you can use the following commands:

```console
mkdir ~/synced && python3 client.py sync -d ~/synced && cat ~/synced/from_server.txt && mkdir -p ~/synced/dataset ~/synced/output ~/synced/encrypted
```

A possible flow would be:
1. copy input datasets to *~/synced/dataset*
1. copy the Third Party's applications to *~/synced/encrypted*
1. use the client's `run` command to execute the Third Party's application
1. wait for the process to complete and verify the output in directory *~/synced/output*

---

### 5. Clean Up

---

Run these steps to clean-up the enclave related resources.

---

#### 5.1. Enclave User

---

Once the activities requiring the enclave are completed, the Enclave User can
 [terminate](https://docs.aws.amazon.com/enclaves/latest/user/cmd-nitro-terminate-enclave.html)
 the running enclave.

- [ ] Use `sudo nitro-cli describe-enclaves` to identify the correct enclave id.
- [ ] Terminate the running enclave from [Step 4.3](#43-start-enclave):

```console
sudo nitro-cli terminate-enclave --enclave-id enclave_id
```

- [ ] Terminate the vsock_proxy started in [Step 4.4](#44-start-kms-proxy):

```console
kill $(ps aux | grep '[v]sock-proxy' | awk '{print $2}')
```

---

#### 5.2. Enclave Administrator

---

Revert the steps done in [Step 3.2](#32-update-iam-role) by deleting the
 inline IAM policy attached to the EC2 instance's IAM role.

If required, stop or terminate the EC2 instance used to host the enclave.

---

### 6. Revoke Access

---

---

#### 6.1. Enclave Administrator

---

The Enclave Administrator can remove the Third Party's access to the S3 bucket shared with them in
 [Step 1.1](#11-setup-third-party-storage).
 To note the existing shared files (encrypted applications and enclave image files) will be preserved.

To revoke Third Party access, follow instructions to
 [update the bucket policy](https://docs.aws.amazon.com/AmazonS3/latest/userguide/add-bucket-policy.html)
 by removing the policy statement with SID **EnableThirdPartyAccess** from the bucket policy.

To remove the existing files from the S3 bucket from [Step 1.1](#11-setup-third-party-storage).,
 follow the instructions to
 [empty a bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/empty-bucket.html).

Once the bucket is empty, follow the steps below to remove the infrastructure associated
 with the Third Party onboarding.

- [ ] Go to service AWS CloudFormation
- [ ] Select the *Stacks* menu option
- [ ] Select the radio button for the stack created in
 [Step 1.1](#11-setup-third-party-storage) and press *Delete*

---

#### 6.2. Third Party

---

The Third Party can choose to stop sharing their files with the enclave host account.

Log in to the [AWS Management Console](https://console.aws.amazon.com/) using
 sufficient privileges or Admin access.

- [ ] Go to service AWS CloudFormation
- [ ] Select the *Stacks* menu option
- [ ] Select the radio button for *NitroImageBuilder* and press *Delete*.
 Wait until the stack is deleted
- [ ] Select the radio button for *ApplicationEncryptor* and press *Delete*.
 Wait until the stack is deleted

Optionally, go to service AWS CodeCommit and delete the repository created in
 [Step 2.1](#21-create-git-repository-and-upload-files).

> Note: Deleting the stacks does not delete any encrypted applications
> or enclave image files already shared with the enclave host. They will continue
> to have access to these files unless they delete them as per
 [Step 6.1](#61-enclave-administrator).

To revoke the enclave access to decrypt your encrypted applications, you need
 to update your KMS key policy.

- [ ] Locate the KMS key created in [Step 2.2.1](#221-application-encryptor).
- [ ] Remove the hash string in the key's policy in the line containing **kms:RecipientAttestation:ImageSha384**

Follow the [technical documentation covering the encryption process](./docs/Encryption.md) for more details.
