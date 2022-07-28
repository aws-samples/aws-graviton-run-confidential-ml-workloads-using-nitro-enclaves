# Encryption

The sections below cover information related to the encryption methods used in this sample.

## Application Code

The proprietary application code that requires protection from being viewed in
 plaintext by external parties will be encrypted by its owner before being shared.

A form of envelope encryption will be used to facilitate this process.

### Prerequisites

The following services and tools are needed to perform the encryption and decryption:

* [Python3](https://www.python.org/about/)
* [AWS Key Management Service (KMS)](https://aws.amazon.com/kms/)
* [Fernet (symmetric encryption)](https://cryptography.io/en/latest/fernet/)
* [kmstool_enclave_cli](https://github.com/aws/aws-nitro-enclaves-sdk-c/blob/main/docs/kmstool.md)

### Encryption Mechanism

The [encryptor script](../src/encryption/envelope_encryptor.py) expects 2 input arguments:

* a directory where all the application related files reside
* a [KMS CMK key](https://docs.aws.amazon.com/whitepapers/latest/kms-best-practices/customer-keys.html)

The command to run the script is:

```shell
python3 envelope_encryptor.py encrypt -d <directory with application files> -k <KMS key alias>
```

Example: if the script *print-hello.py* is in directory *application*, then run command:

```shell
python3 envelope_encryptor.py encrypt -d application -k alias/enclavekey
```

The encryptor script will:

1. zip the contents of the directory given as argument
1. generate a new data key using the KMS CMK key given as argument
1. use the plaintext generated data key in step 2 to encrypt the zip file in step 1 using Fernet
1. concatenate a header, the encrypted data key from step 2 and the encrypted file from step 3 into one file
1. write the encrypted file from step 4 to disk as: ***application_code.zip.encrypted***

You can then share ***application_code.zip.encrypted*** to the external party as required, e.g.
 using an [Amazon S3](https://aws.amazon.com/s3/) bucket.

#### Automated application encryptor

An [AWS CloudFormation](https://aws.amazon.com/cloudformation/)
 [application encryptor template](../src/encryption/Deploy-ApplicationEncryptor-Cfn.yaml) is available for use
 where applicable. It can automate the process to create a new KMS CMK key to use for the application code encryption
 as well as decryption on the enclave at runtime. In addition, it also creates a CodeBuild project. If you manually
 trigger the CodeBuild project through the *Start build* button in the AWS Console, it will take the application
 code you supply through an [AWS CodeCommit](https://aws.amazon.com/codecommit/) Git repository and it will package,
 encrypt, and store the resulting encrypted file (***application_code.zip.encrypted***) in the S3 bucket you specify.

|Parameter Name                 |Description  |Default value                   |
|-------------------------------|-------------|--------------------------------|
|EncryptionKeyAlias             |Provide an unique alias name for the new KMS CMK key that will be created |*alias/enclavekey*|
|CodeCommitRepositoryName       |Provide the CodeCommit Git repository name which you created to upload in it the *envelope_encryptor.py* script and the directory with the application files you need to encrypt |*No default - must be specified*|
|ApplicationCodeDirectoryName   |Provide the path (including directory name) inside CodeCommitRepositoryName where the application files that need to be encrypted reside |*No default - must be specified*|
|ExternalBucketName             |Provide the S3 bucket name where to store resulting files that will be shared with external parties |*No default - must be specified*|
|ExternalBucketPath             |Provide the S3 path inside ExternalBucketName where to store the resulting encrypted file ***application_code.zip.encrypted*** that will be shared with external parties |*encrypted*|
|ExternalBucketEncryptionKeyArn |Provide the ARN for the encryption key used with the external bucket in which you are uploading the encrypted files for sharing |*No default - must be specified*|
|ExternalBucketAWSAccountNumber |Provide the AWS account number for the owner with whom you are sharing your protected application - this is the account in which you are uploading the encrypted files for sharing and to which you are granting controlled key access to |*No default - must be specified*|

### Decryption Mechanism

When the enclave server application receives a [**run**](./Client.md#3-run) script command from the
 client, it will process the ***application_code.zip.encrypted*** file shared and it will:

1. extract the encrypted data key based on header
1. decrypt the encrypted data key using the kmstool_enclave_cli by making a call to the AWS KMS service
1. decrypt the encrypted application code zip file using Fernet and the plaintext data key from step 2
1. unzip the decrypted application code zip file and invoke the script inside as requested by the client

## Key Policy

The AWS KMS customer-managed key used to encrypt the protected application code requires a key policy update
 to allow an enclave to decrypt the application code.

An example of the 2 policy statements required that allow controlled decryption from the enclave running in
 production mode (as the enclave cannot send attestation information when it's running in debug mode):

```json
{
    "Sid": "Required by kmstool-enclave-cli as a prerequisite for the parent EC2 instance that's running the enclave. Decryption from parent EC2 instance will not be allowed as long as a secondary policy exists with a Condition restricting decryption.",
    "Effect": "Allow",
    "Principal": {
        "AWS": "<AWS Account ID where enclave is running>"
    },
    "Action": "kms:Decrypt",
    "Resource": "*"
},
{
    "Sid": "Required by kmstool-enclave-cli. Restrict decryption to now only work from the enclave.",
    "Effect": "Deny",
    "Principal": {
        "AWS": "<AWS Account ID where enclave is running>"
    },
    "Action": "kms:Decrypt",
    "Resource": "*",
    "Condition": {
        "StringNotEqualsIgnoreCase": {
            "kms:RecipientAttestation:ImageSha384": "<PCR0 hash from the Nitro enclave image .eif file>"
        }
    }
}
```

To note the parent EC2 instance for the enclave will also need an IAM role allowing "kms:Decrypt" for
 the KMS CMK key ARN. While it won't be able to decrypt the encrypted code because of the Condition
 flag, this permission is needed by the kmstool_enclave_cli which uses the parent EC2 instance IAM role
 credentials from
 "http://169.254.169.254/latest/meta-data/iam/security-credentials/{instance_role_name}".

Example inline policy for the parent EC2 instance IAM role:

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
            "Resource": "<KMS CMK key ARN>"
        }
    ]
}
```

If the parent EC2 instance runs the decryption, it will get an *AccessDeniedException* like in the
 example below:

```shell
aws kms decrypt --ciphertext-blob fileb://data_key.encrypted --region eu-west-2

An error occurred (AccessDeniedException) when calling the Decrypt operation: The ciphertext refers
 to a customer master key that does not exist, does not exist in this region, or you are not allowed
 to access.
```

To run the test shown above, you need to extract the encrypted data key from the encrypted
 application code archive (assuming you used the application encryptor provided in *src/encryption*).
 You can create a new Python script called *extract_decryption_key.py* with the content below.
 Put this file in the same directory as the **application_code.zip.encrypted** file.

```python3
# Locate encrypted file
with open("application_code.zip.encrypted", 'rb') as file:
    data = file.read()

# Extract data key length from header
data_key_enc_len = int.from_bytes(data[:4], byteorder="big") + 4
# Extract encrypted data key
data_key_enc = data[4:data_key_enc_len]

# Store encrypted data key on disk
with open('data_key.encrypted', 'wb') as fh:
    fh.write(data_key_enc)
```

Then run `python3 extract_decryption_key.py` and you should see a **data_key.encrypted** file in the
 same directory.

You can then run the command `aws kms decrypt --ciphertext-blob fileb://data_key.encrypted --region eu-west-2`
 to ensure the parent EC2 instance cannot decrypt the data key which is the intended behaviour as only
 the enclave should be able to do this.

## IAM Policy

To run the encryptor script, a policy is needed to allow the required access to the KMS CMK key used for encryption:

```json
{
    "Sid": "Allow encryption using key",
    "Effect": "Allow",
    "Action": [
        "kms:Encrypt",
        "kms:GenerateDataKey"
    ],
    "Resource": "<KMS CMK key ARN>"
}
```
