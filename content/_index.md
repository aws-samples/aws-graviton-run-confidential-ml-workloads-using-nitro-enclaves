---
title: "Run Confidential ML Workloads using AWS Nitro Enclaves"
draft: false
weight: 1
---

Written by:
* Syl Taylor - Compute Specialist Solutions Architect
* Karan Shah - Cloud Infrastructure Architect

{{% notice note %}}

Solution's code repository: https://github.com/aws-samples/aws-graviton-run-confidential-ml-workloads-using-nitro-enclaves

{{% /notice %}}

## Run Confidential ML Workloads using AWS Nitro Enclaves

Customers from diverse industries collaborate with other parties to exchange sensitive information,
such as code and data. For artificial intelligence (AI), machine learning (ML), and data science
(DS) practitioners, the ability to experiment with externally-provided algorithms, models,
and datasets is key to improving business outcomes.

For example, medical research organizations had a need for better industry collaboration during the
COVID-19 pandemic, which was dependent on secure timely sharing of confidential algorithms and
healthcare data. Similarly, in a commercial setting in financial services, a company can use
multi-party computation to improve ML training outcomes by combining their own datasets with
a private dataset and algorithm owned by another party. Our goal is to enable customers to
respond more easily to such changing market conditions.

## Overview

Confidentiality is important to a party that owns sensitive information and wants to provide
 it to others. In this post, we will show how AWS Nitro Enclaves for isolated compute and AWS
KMS for cryptographic operations can ensure files are not visible in plaintext form and we
will provide an example solution.

We will demonstrate how you can share your sensitive AI/ML files in a manner that safeguards
application and data confidentiality. To present you with a familiar environment, we included
the ability to do seamless data transfers to accelerate ML and DS workloads, as well as run
software downloaded at runtime to process that data conveniently.

## AWS Nitro Enclaves

To enable AI/ML application owners to provide their sensitive files to application users,
we introduce Nitro Enclaves as a secure compute environment which addresses the confidentiality
requirement for software and data.

A Nitro Enclave is an isolated virtual machine created by an Amazon EC2 instance and connected
to it through a socket connection that allows them to communicate securely. An enclave has
dedicated CPU and memory allocated with no persistent storage and no external networking.
Because an enclave provides no interactive access by default, our open-source solution comes
with two applications for client-server communication that enable this feature.

## Shared Responsibility

![Shared responsability](/images/shared-responsability.png)

An owner is responsible for protecting their files by encrypting them and providing the enclave
file in which an application user can run the encrypted application without seeing the plaintext
code or data. This constraint poses some security considerations such as the possibility of
malicious intent or data exfiltration, so the application user is encouraged to use further
technical controls to isolate their working environment through host and network restrictions,
as well as put in place any procedures that minimize or mitigate the risks.

Their customers, on the other hand, require a method to run the owner’s software with minimal
overhead and with an intuitive interface. Owners can release new applications or upgrades to
existing ones and customers can download these files at their own convenience and use them at
runtime in the enclave for faster experimentation.

Both parties should review the
[AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/)
to understand security considerations for cloud workloads.

The **key features** we will highlight include:
*	downloading and using confidential Python applications at runtime inside a secure container whose
server application cannot be tampered with due to cryptographic attestation,
*	a remote virtual file system for easy bidirectional file transfers between the enclave and the
parent EC2 instance to enable frequent ML data changes and switching between multiple applications.

## Use Cases

Owners supply enclave image files to customers and control the cryptographic keys used to encrypt
the confidential applications and data allowed to run in the enclave. Customers then allocate EC2
compute and memory resources in their AWS accounts to run externally-provided enclaves and
applications.

This exchange model is required to secure the owner’s sensitive information, however, we’ve designed
the solution to accommodate several scenarios in which the owner always provides the confidential
application, however the datasets and ML files can be provided by either the owner or the customer
and the files can be either in encrypted or plaintext form as required.

The following Linux shell commands demonstrate the flexibility an application user has when operating
applications and data transfers from the EC2 instance.

To enable data transfers to the Nitro Enclave, sync a local directory to the enclave’s in-memory filesystem:
```shell
python3 client.py sync -d synced_folder
```
To copy confidential application packages (which can include ML models and datasets)  to the enclave:
```shell
cp app_package.encrypted synced_folder/encrypted
```
To copy optional plaintext datasets or ML models owned by the user to the enclave:
```shell
cp -r dataset/* synced_folder/dataset/
cp -r model/* synced_folder/model/
```
To run an example confidential application which uses an encrypted model (part of the encrypted
application package supplied by owner) with a plaintext data set (owned by user):
```shell
python3 client.py run -f app_package.encrypted -s ml_algorithm.py -a "-m model.h5 -d /dataset/ -o /output/"
```
As you can observe, the commands are similar to how you would run an application locally on an EC2 instance,
but in this case we leverage a client application which instructs the enclave to run the ML script in a
confidential manner in which the user can only see the results without seeing the code being run.

## Design

Once high-level consensus is established between two parties willing to collaborate on a project,
they will use this solution to enable the security guardrails required to share sensitive artefacts.
The AWS environment setup is shown in the diagram below.

![Architecture diagram](/images/solution-architecture-diagram.png)

The **high-level workflow** is the following:
1.	An application user creates and shares an Amazon S3 bucket with the application owner in
which they can store encrypted applications and enclave image files.
1.	An application owner uploads their sensitive plaintext files, along with utilities
supplied with this solution, into their private AWS CodeCommit Git repository.
1.	An application owner deploys AWS CodeBuild projects for automated encryption and
enclave image builds using Infrastructure-as-Code supplied with this solution. The output files
are automatically shared with the application user via the shared S3 bucket. The application
owner’s account owns the KMS key used to encrypt applications. Access to decrypt data using this
key is controlled using its resource policy. The enclave image build process keeps the policy
condition up-to-date with the PCR0 hash of the latest built enclave image file.
1.	An IT administrator allocates compute, and memory resources for the EC2 instance that will
host the enclave and grants the required AWS IAM permissions.
1.	An application user downloads the client application supplied with this solution, so they
can interact with the running enclave.
1.	An application user can download externally-provided sensitive files, as well as their own data,
and transfer them to the enclave for usage. Applications are only decrypted within the boundary of the
running enclave, which the user does not have access to. The output files returned by the applications
will be stored in a shared directory between the enclave and the parent EC2 instance, from where the
user can process them without restrictions.

{{% notice info %}}

On one hand, the design of the solution puts the application owner in control of who can use their
application code, when, and how. On the other hand, the application user is in control of which files
they run and which external services a running enclave can access.

{{% /notice %}}

## Solution

To enable our use cases, we need the following components:
1.	A client application to run from the EC2 Linux instance to send instructions to the enclave
1.	A server application to restrict what software the enclave can run and how

![Client server diagram](/images/client-server-diagram.png)

The client and server applications communicate through remote procedure calls (RPC) leveraging vsock
sockets. RPC functionality was added to support a FUSE virtual file system that intercepts Linux filesystem
commands from the client side and instructs the server on the enclave to replicate those actions. Similarly,
an RPC connection is used to support runtime code ingestion and program execution on the enclave. Other features
and commands can be added using the same RPC framework-based mechanism to extend the solution.

While the solution we provide only runs Python applications, the server code packaged with the enclave can be
adjusted with minimal changes to support other types of applications too.

### Client Application

We implemented a Python client utility to allow interactions with the server application packaged within the
enclave. The following 2 commands enable a user to interactively operate the enclave:
1.	**sync**: maps an empty local directory to the enclave’s filesystem for bidirectional data transfers using
standard Linux filesystem commands such as ls, cp, and rm
1.	**run**: instructs the enclave to run a confidential application with the arguments supplied

Following a sync command, the user can easily copy or remove files such as encrypted application packages or
optional plaintext data while maintaining visibility over what the enclave sees and uses. This is important
for machine learning and data science experiments which require frequent data operations.

The run command enables the user to interactively run Python scripts from shared encrypted packages at runtime.
Only one application can be executed at any given time on the enclave. The user can also provide a list of
arguments specifying which input or output resides either on the synced folder or the encrypted package.

To learn more about the client application, read the documentation on the
[solution’s open-source repository](https://github.com/aws-samples/aws-graviton-run-confidential-ml-workloads-using-nitro-enclaves/blob/main/docs/Client.md).

### Server Application

The Python server application packaged inside the enclave image file acts as a control plane to support
runtime code ingestion and usage.  We advise using the code in the example solution until you are familiar
with the security layers and constructs before making any changes.

To learn more about the server application, read the documentation on the
[solution’s open-source repository](https://github.com/aws-samples/aws-graviton-run-confidential-ml-workloads-using-nitro-enclaves/blob/main/docs/Server.md).

### Usage

To follow a detailed walkthrough, visit the
[solution’s runbook](https://github.com/aws-samples/aws-graviton-run-confidential-ml-workloads-using-nitro-enclaves/blob/main/RUNBOOK.md)
and use the sample ML inference application.

### Clean-Up

Visit the [solution’s runbook](https://github.com/aws-samples/aws-graviton-run-confidential-ml-workloads-using-nitro-enclaves/blob/main/RUNBOOK.md)
for steps to delete the infrastructure created in both the application owner and user accounts.

## Conclusion

Organizations require a mechanism to share sensitive code and data artifacts while maintaining assurances
around the confidentiality of those artifacts. With AI/ML and DS workloads, they also need to preserve the
ability to experiment fast and with minimal upskilling. In this blog post we provide an example solution
using AWS Nitro Enclaves that enables application owners to continuously share confidential files with users
that use their applications at their own convenience, whilst operating in a familiar environment.

To learn more about how AWS Nitro Enclaves enables customers to protect highly sensitive data,
please check the [official user guide](https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave.html).

## Appendix

### Business Process

![Business process](/images/solution-business-process.png)
