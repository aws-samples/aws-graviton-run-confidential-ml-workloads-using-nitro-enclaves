# Client Application

> Note: this application has only been tested on OS: Amazon Linux 2 on architecture: x86_64

The client application, written in Python3, can be used on a parent EC2 instance
 that runs a [Nitro enclave](https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave.html).

The *client.py* script is the entry point to invoke
 commands. Depending on the functionality implemented, the command will be run either
 on the client (EC2 instance) or the server (Nitro enclave), the latter using a [RPC
 connection](https://en.wikipedia.org/wiki/Remote_procedure_call) over a
 [VSOCK network socket](https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave-concepts.html).

## Constraints

* AWS region is fixed: eu-west-2
* The KMS proxy port is fixed: 8001
* The RPC port for sync commands is fixed: 5000
* The RPC port for run commands is fixed: 6000
* Only one enclave should be running on one EC2 instance

## Prerequisites

Use an EC2 instance running the Amazon Linux 2 OS (x86_64).

Packages required:
* fuse (`sudo yum install fuse`)
* fuse-libs (`sudo yum install fuse-libs`)
* fusepy (`pip3 install fusepy`)
* requests (`pip3 install requests`)

## Commands

Three commands are currently supported:

1. **proxy**: runs a
 [vsock-proxy utility](https://github.com/aws/aws-nitro-enclaves-cli/blob/main/vsock_proxy/README.md)
 on the client side to allow the enclave to
 communicate with AWS services (only [KMS](https://aws.amazon.com/kms/) is supported and
 implemented at this time)
1. **sync**: mounts a local empty folder on the client and syncs it with the enclave's
 */tmp/client* directory. It uses the
 [FUSE library](https://www.kernel.org/doc/html/latest/filesystems/fuse.html)
 to intercept filesystem commands
 and additional code will ensure the filesystem state changes between client
 and enclave are updated over the network channel (RPC connection over a
 VSOCK network socket)
1. **run**: used to tell the enclave to decrypt an encrypted script, execute it and
 then return the results. Alternatively, the script can also write output files to
 the synced folder (created using the **sync** command).

## Source Code

|File Name             |Path                  |Description  |
|:---------------------|:---------------------|:------------|
|client.py             |src/client            |Main entry point to run the application. Expects an enclave running on the system. Supports 3 commands: **proxy**, **sync** and **run**. |
|rpc_client.py         |src/client/network    |Basic RPC client that is used to send commands to the server. The commands will be executed in the enclave. Used by the client **sync** and **run** commands. |
|proxy-config-kms.yaml |src/client/network    |Used by the vsock-proxy tool. It defines the allowed endpoints list. The vsock-proxy tool is invoked by the client **proxy** command. |
|rfs_client.py         |src/client/filesystem |Defines filesystem functions that FUSE can invoke over the RPC connection when it intercepts Linux I/O commands on the FUSE mounted directory. Used by the client **sync** command. |
|socket.py             |src/client/common     |Defines a network socket of type VSOCK that is used by the RPC client to allow client to communicate with the server on the enclave. Must be implemented by both client and server. |
|unpickler.py          |src/client/common     |Custom deserializer for pickle. It restricts objects that can be deserialised after transfer over the RPC connection. The restriction aims to prevent unauthorised code execution on the server. Must be implemented by both client and server. |
|rpc.py                |src/client/common     |Custom classes related to RPC. Must be implemented by both client and server. |

## Application Usage

### 1. Proxy

```shell
python3 client.py proxy -s kms
```

Arguments:

* **-s** or **--svc** : provide which AWS service to allow the enclave access to,
 currently only supports connections to KMS in region eu-west-2 (London) over a
 fixed port: 8001

The proxy that will be created is a detached background process:
 *vsock-proxy 8001 kms.eu-west-2.amazonaws.com 443 --config network/proxy-config-kms.yaml*.

Can verify this background process is running using command:

```shell
sudo ps -ef | grep 'vsock-proxy'
```

### 2. Sync

Example, create on the client (parent EC2 instance), an empty directory called
 */home/ec2-user/enclave/shared*.

```shell
python3 client.py sync -d /home/ec2-user/enclave/shared
```

Arguments:

* **-d** or **--dir** : provide an empty local folder to sync to the enclave's
 */tmp/client* directory to use for bidirectional data transfers between client
 and enclave

The directory */home/ec2-user/enclave/shared* on the client is now bidirectionally
 synced with the enclave's */tmp/client* directory. You can use the
 */home/ec2-user/enclave/shared* directory to transfer data (e.g. datasets,
 encrypted application code, etc.) to the enclave and check results (e.g. output
 from the encrypted application code run on the enclave).

Upon running this command, confirm it has worked by listing the files
 in */home/ec2-user/enclave/shared*. You should see a file *from_server.txt*
 with the message "Enclave Server Initialised". For additional verification,
 you can use `cp` to move a sample file to the synced directory, `rm` to
 delete *from_server.txt* or `cp` *from_server.txt* from the enclave to the
 parent EC2 instance.

***Warning***: when using the synced directory do not share any sensitive
 data or application code (unless encrypted). The user is responsible for
 the safe use of the tools and commands at their disposal.

To unmount the synced directory, use the following command:

```shell
fusermount -u /home/ec2-user/enclave/shared
```

### 3. Run

An example using a tested use case is provided below. The scenario allows
 a third party to provide you with an encrypted proprietary application that
 can only be run in the enclave in a protected manner (e.g. you won't be able
 to see the code being executed).

```shell
python3 client.py run -f application_code.zip.encrypted -s main/ml_inference.py -a "-m model/classifier.h5 -d /dataset/ -o /output/"
```

Arguments:

* **-f** or **--file** : provide the encrypted application code file name,
 likely called *application_code.zip.encrypted* as created by the
 *src/encryption/envelope_encryptor.py* script
* **-s** or **--script** : provide the name of the script from the application
 code that should be executed (e.g. an entrypoint). This name is not visible
 as the application code is encrypted, so it must be known in advance from
 the owner of the encrypted application code
* **-a** or **--script_args** : provide a string that defines the list of
 arguments to pass to the script in argument **-s**. The list of supported
 arguments and the appropriate values must be known in advance from
 the owner of the encrypted application code

There are two important types of arguments being passed using **-a**:

* relative paths: e.g. *model/classifier.h5*, the enclave assumes this
 file is part of the encrypted application code (zip file) and is protected
 from view. The enclave server will locate the file from */tmp/decrypted/app*
 (current working directory), a directory on the enclave that is not accessible
 to the client
* absolute paths: e.g. */dataset/*, the enclave assumes this is a directory
 pre-created on the client side in the synced folder (using command **sync**).
 For the example above, this argument will be used to read all data (.jpg images)
 from */tmp/client/dataset* (which syncs with e.g. */home/ec2-user/enclave/shared/dataset*)

The summary for the example command above:

* *application_code.zip.encrypted* contains a few dozen python files and a model file
* *main/ml_inference.py* (part of *application_code.zip.encrypted*) is the encrypted script
 that is an entrypoint and performs ML inference
* *model/classifier.h5* (part of *application_code.zip.encrypted*) is the encrypted model
 file used by the *main/ml_inference.py* script
* */dataset/* is the location in the synced directory where the input data for the ML
 inference resides. Directory must be manually created on the client side using e.g.
 `mkdir -p /home/ec2-user/enclave/shared/dataset` before executing the client's *run* command.
 The data (e.g. .jpg images) by design is not encrypted and belongs to the owner of
 the parent EC2 instance where the enclave is running
* */output/* is the location in the synced directory where the output results for the ML
 inference can be written to. Directory must be manually created on the client side using e.g.
 `mkdir -p /home/ec2-user/enclave/shared/output` before executing the client's **run** command.
 This data (e.g. output files) by design is not encrypted and should be visible to the owner
 of the parent EC2 instance where the enclave is running

> Note: the **run** command is a blocking one, meaning the client will wait for the enclave server
> to respond with an output message, but only after it finished executing the script provided as input

***Warning***: when using the synced directory do not share any sensitive
 data or application code (unless encrypted). The user is responsible for
 the safe use of the tools and commands at their disposal.
