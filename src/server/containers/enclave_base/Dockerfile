FROM public.ecr.aws/amazonlinux/amazonlinux:2 as builder

WORKDIR /builder

# Nitro KMS tool installation

## Required packages
RUN set -e \
    && amazon-linux-extras enable epel \
    && yum clean -y metadata && yum install -y epel-release \
    && yum install -y cmake3 gcc git tar make gcc-c++ go ninja-build \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y

## Dependency aws-lc
RUN set -e \
    && git clone -b v1.0.2 https://github.com/awslabs/aws-lc.git aws-lc \
    && cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja -S aws-lc -B aws-lc/build . \
    && go env -w GOPROXY=direct \
    && cmake3 --build aws-lc/build --target install

## Dependency s2n-tls
RUN set -e \
    && git clone -b v1.3.11 https://github.com/aws/s2n-tls.git \
    && cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -S s2n-tls -B s2n-tls/build \
    && cmake3 --build s2n-tls/build --target install

## Dependency aws-c-common
RUN set -e \
    && git clone -b v0.6.20 https://github.com/awslabs/aws-c-common.git \
    && cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja -S aws-c-common -B aws-c-common/build \
    && cmake3 --build aws-c-common/build --target install

## Dependency aws-c-sdkutils
RUN set -e \
    && git clone -b v0.1.2 https://github.com/awslabs/aws-c-sdkutils.git \
    && cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja -S aws-c-sdkutils -B aws-c-sdkutils/build \
    && cmake3 --build aws-c-sdkutils/build --target install

## Dependency aws-c-cal
RUN set -e \
    && git clone -b v0.5.17 https://github.com/awslabs/aws-c-cal.git \
    && cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja -S aws-c-cal -B aws-c-cal/build \
    && cmake3 --build aws-c-cal/build --target install

## Dependency aws-c-io
RUN set -e \
    && git clone -b v0.10.21 https://github.com/awslabs/aws-c-io.git \
    && cmake3 -DUSE_VSOCK=1 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja -S aws-c-io -B aws-c-io/build \
    && cmake3 --build aws-c-io/build --target install

## Dependency aws-c-compression
RUN set -e \
    && git clone -b v0.2.14 http://github.com/awslabs/aws-c-compression.git \
    && cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja -S aws-c-compression -B aws-c-compression/build \
    && cmake3 --build aws-c-compression/build --target install

## Dependency aws-c-http
RUN set -e \
    && git clone -b v0.6.13 https://github.com/awslabs/aws-c-http.git \
    && cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja -S aws-c-http -B aws-c-http/build \
    && cmake3 --build aws-c-http/build --target install

## Dependency aws-c-auth
RUN set -e \
    && git clone -b v0.6.11 https://github.com/awslabs/aws-c-auth.git \
    && cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja -S aws-c-auth -B aws-c-auth/build \
    && cmake3 --build aws-c-auth/build --target install

## Dependency json-c
RUN set -e \
    && git clone -b json-c-0.16-20220414 https://github.com/json-c/json-c.git \
    && cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_SHARED_LIBS=OFF -GNinja -S json-c -B json-c/build \
    && cmake3 --build json-c/build --target install

## Dependency aws-nitro-enclaves-nsm-api
RUN set -e \
    && git clone -b v0.2.1 https://github.com/aws/aws-nitro-enclaves-nsm-api.git \
    && source $HOME/.cargo/env && cd aws-nitro-enclaves-nsm-api && cargo build --release -p nsm-lib \
    && mv target/release/libnsm.so /usr/lib64 \
    && mv target/release/nsm.h /usr/include

## Dependency doxygen
RUN set -e \
    && yum install -y doxygen \
    && git clone --depth 1 -b v0.2.1  https://github.com/aws/aws-nitro-enclaves-sdk-c \
    && cmake3 -DCMAKE_PREFIX_PATH=/usr -DCMAKE_INSTALL_PREFIX=/usr -GNinja -S aws-nitro-enclaves-sdk-c -B aws-nitro-enclaves-sdk-c/build \
    && cmake3 --build aws-nitro-enclaves-sdk-c/build --target install \
    && cmake3 --build aws-nitro-enclaves-sdk-c/build --target docs

FROM public.ecr.aws/amazonlinux/amazonlinux:2 as enclave

WORKDIR /app

## kmstool-enclave-cli
COPY --from=builder /usr/lib64/libnsm.so /usr/lib64/libnsm.so
COPY --from=builder /usr/bin/kmstool_enclave_cli /app/kmstool_enclave_cli

# Enclave server requirements
RUN set -e \
    ### Install prerequisite packages
    && yum upgrade -y \
    && yum install python3 fuse fuse-devel iproute -y \
    && pip3 install fusepy six cryptography \
    ### Proxy settings
    && echo "127.0.0.1 kms.eu-west-1.amazonaws.com" >> /etc/hosts