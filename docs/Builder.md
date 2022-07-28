# Nitro Enclave Image Builder

## Prerequisites

Deploy the [automated application encryptor template](../src/encryption/Deploy-ApplicationEncryptor-Cfn.yaml)
 first. This builder automatically imports and uses the [AWS KMS](https://aws.amazon.com/kms/)
 CMK key created by the [automated application encryptor](./Encryption.md#automated-application-encryptor).

## Code

An [AWS CloudFormation](https://aws.amazon.com/cloudformation/)
 [automated enclave image builder template](../src/builder/Deploy-NitroImageBuilder-Cfn.yaml)
 is available for use where applicable.

It automates the process to create a Nitro enclave image file (.eif) that packages the server
 application code supplied through an [AWS CodeCommit](https://aws.amazon.com/codecommit/) Git
 repository. The Nitro enclave image file (.eif) will be stored in the
 [Amazon S3](https://aws.amazon.com/s3/) bucket you specify. The AWS KMS CMK key
 (used for decryption inside the enclave) will also be automatically updated
 with the Nitro enclave image file's PCR0 attestation hash.

|Parameter Name                  |Description  |Default value                   |
|--------------------------------|-------------|--------------------------------|
|CodeCommitRepositoryName        |Provide the CodeCommit Git repository name which you created to upload in it the contents of *src/server* |*No default - must be specified*|
|ExternalBucketName              |Provide the S3 bucket name where to store resulting files that will be shared with external parties |*No default - must be specified*|
|ExternalBucketPath              |Provide the S3 path inside ExternalBucketName where to store the resulting Nitro enclave image file ***nitro-enclave-image.eif*** that will be shared with external parties |*enclave*|
|ExternalBucketEncryptionKeyArn  |Provide the ARN for the encryption key associated with the external bucket in which you are uploading the enclave image file for sharing |*No default - must be specified*|
|ExternalBucketAWSAccountNumber  |Provide the AWS account number for the owner with whom you are sharing your protected application - this is the account in which you are uploading the encrypted files for sharing and to which you are granting controlled key access to |*No default - must be specified*|
