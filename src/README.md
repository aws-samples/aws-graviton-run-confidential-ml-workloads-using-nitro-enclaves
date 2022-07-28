# Source Code Overview

|Directory           |Description |
|:-------------------|:-----------|
|builder             |Infrastructure-as-code template to deploy the automated Nitro enclave image builder|
|client              |Python client application running on the parent EC2 instance that is hosting the Nitro enclave|
|encryption          |Infrastructure-as-code template to deploy an encryption key and the automated application encryptor|
|onboarding          |Infrastructure-as-code template to deploy a S3 bucket in which a third-party uploads encrypted files and enclave images|
|server              |Docker files to build a Nitro enclave image as well as the Python server application running inside the Nitro enclave|
