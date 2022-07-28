# Server application

> Note: this application has only been tested on OS: Amazon Linux 2 on architecture: arm64

The server application, written in Python3, should be used inside a
 [Nitro enclave](https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave.html).

The *server.py* script is the entry point that will be invoked when the Nitro enclave is
 started using `nitro-cli run-enclave`. This is the defined in
 *src/server/containers/enclave_app/Dockerfile*.

## Constraints

* AWS region is fixed: eu-west-1
* The KMS proxy port is fixed: 8001
* The RPC port for sync commands is fixed: 5000
* The RPC port for run commands is fixed: 6000
* Only one enclave should be running on one EC2 instance

## Prerequisites

Use an EC2 instance running the Amazon Linux 2 OS (arm64).

> Note: Ensure your EC2 instance type has sufficient
> disk storage, CPU cores and memory to accommodate the needs of the Nitro enclave
> image file.

The initial setup for the EC2 instance that will run the Nitro enclave:

```shell
sudo amazon-linux-extras install aws-nitro-enclaves-cli -y
sudo yum install aws-nitro-enclaves-cli-devel -y
sudo systemctl start docker && sudo systemctl enable docker
```

Confirm the nitro-cli tool has been installed successfully using command:

```shell
nitro-cli --version
```

The Nitro enclave allocator service needs to be able to reserve the resources you
 specify in the `nitro-cli run-enclave --cpu-count <CPUs> --memory <MemorySize>...`
 command. To change the configuration file to accommodate your memory needs,
 either use the following commands or for more options, manually edit the
 */etc/nitro_enclaves/allocator.yaml* file:

```
sudo systemctl stop nitro-enclaves-allocator.service
ALLOCATOR_CONFIG=/etc/nitro_enclaves/allocator.yaml
MEM_KEY=memory_mib
DEFAULT_MEM=20480
sudo sed -r "s/^(\s*${MEM_KEY}\s*:\s*).*/\1${DEFAULT_MEM}/" -i "${ALLOCATOR_CONFIG}"
sudo systemctl start nitro-enclaves-allocator.service && sudo systemctl enable nitro-enclaves-allocator.service
```

## Source Code

### Server application

|File Name             |Path                                                |Description  |
|:---------------------|:---------------------------------------------------|:------------|
|server.py             |src/server/containers/enclave_app/server/           |Main entrypoint to run the application. Invoked by *src/server/containers/enclave_app/Dockerfile* when the enclave starts. It runs as a service (always on while the enclave image running) and it listens to incoming client connections. |
|rpc_server.py         |src/server/containers/enclave_app/server/network    |Basic RPC server that listens to incoming client commands. |
|proxy.py              |src/server/containers/enclave_app/server/network    |Allows the enclave to communicate with the client's vsocks proxy to send key decryption requests to the configured AWS KMS endpoint.             |
|rfs_server.py         |src/server/containers/enclave_app/server/filesystem |Implements how to process incoming client filesystem commands related to the directory synced between client and enclave. |
|run.py                |src/server/containers/enclave_app/server/process    |Implements the processing for the [client command **run**](./Client.md#3-run). In summary, it will decrypt the application code provided and execute the required script on the enclave. |
|socket.py             |src/server/containers/enclave_app/server/common     |Defines a network socket of type VSOCK that is used by the RPC server to listen to client commands. Must be implemented by both client and server.             |
|unpickler.py          |src/server/containers/enclave_app/server/common     |Custom deserializer for pickle. It restricts objects that can be deserialised after transfer over the RPC connection. The restriction aims to prevent unauthorised code execution on the server. Must be implemented by both client and server.             |
|rpc.py                |src/server/containers/enclave_app/server/common     |Custom classes related to RPC. Must be implemented by both client and server.             |

### Nitro image file

|File Name             |Path                                     |Description  |
|:---------------------|:----------------------------------------|:------------|
|Dockerfile            |src/server/containers/enclave_base       |Defines the base container which installs the required packages for the server application and configures proxy settings. |
|Dockerfile            |src/server/containers/enclave_app        |Defines the custom application container. It should be used to install all additional packages required by the encrypted application code that will be executed at runtime on the enclave. |
|requirements.txt      |src/server/containers/enclave_app        |Defines the list of pip packages to install as required by the encrypted application code that will be executed at runtime on the enclave. |

## Enclave

The following are examples of commands that can be run to build and operate the Nitro enclave.

1. Build the base image

```shell
# In directory containing the files from *src/server/containers/enclave_base*
sudo docker build -t enclavebase .
```

2. Build the enclave image

```shell
# In directory containing the files from *src/server/containers/enclave_app*
sudo nitro-cli build-enclave --docker-uri enclaveapp --docker-dir ./ --output-file nitro-enclave.eif
```

3. Run the enclave image

```shell
sudo nitro-cli run-enclave --cpu-count 2 --memory 14000 --eif-path nitro-enclave.eif
```

4. Ensure the enclave is running

```shell
sudo nitro-cli describe-enclaves
```

If the output is "[]", then the enclave is not running. This is likely due to incorrect server
 application code or dependencies being packaged in the .eif file. Modify these and re-build
 as instructed in step 1 in this list.

5. Optional: Debug the enclave

If you add an additional argument `--debug-mode` to the step 3 command, you can then use the console
 for debugging.

```shell
sudo nitro-cli console --enclave-name nitro-enclave
```

6. Terminate the enclave

```shell
sudo nitro-cli terminate-enclave --enclave-name nitro-enclave
```

## Troubleshooting

If you run into container-related issues where either Docker or nitro-cli build-enclave is not behaving as expected
 and no standard measures are effective, then do a clean-up using `sudo docker system prune` and try again.

For a full list of nitro-cli commands and other guidance, please review the
 [AWS Nitro Enclaves User Guide](https://docs.aws.amazon.com/enclaves/latest/user/cmd-nitro-terminate-enclave.html).
