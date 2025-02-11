ebmsolace
---
ebMS Solace PubSub+

Repo
---
`git clone https://github.com/taatuut/ebmsolace.git`

Setup
---
Create and source a Python virtual environment, use `~/.venv`.

Open a terminal and run:

```
mkdir -p ~/.venv
python3 -m venv ~/.venv
source ~/.venv/bin/activate
```

Install Python modules (optional: `upgrade pip`)

```
python3 -m pip install --upgrade pip
python3 -m pip install requests lxml solace-pubsubplus pyyaml
```

Use `pipreqs` to collect and check required modules (do not use `freeze`).

```
python3 -m pip install pipreqs
```

Then use `which python` to find path to folder where pipreqs resides.

```
which python
˜/.venv/bin/python
```

So `pipreqs` is in folder `˜/.venv/bin/`. Now execute `pipreqs` using full paths.

```
~/.venv/bin/pipreqs ~/GitHub/taatuut/ebmsolace --force --savepath ~/GitHub/taatuut/ebmsolace/requirements.txt
```

Will respond with something like:

```
INFO: Not scanning for jupyter notebooks.
WARNING: Import named "PyYAML" not found locally. Trying to resolve it at the PyPI server.
WARNING: Import named "PyYAML" was resolved to "PyYAML:6.0.2" package (https://pypi.org/project/PyYAML/).
Please, verify manually the final list of requirements.txt to avoid possible dependency confusions.
WARNING: Import named "Requests" not found locally. Trying to resolve it at the PyPI server.
WARNING: Import named "Requests" was resolved to "requests:2.32.3" package (https://pypi.org/project/requests/).
Please, verify manually the final list of requirements.txt to avoid possible dependency confusions.
INFO: Successfully saved requirements file in /Users/emilzegers/GitHub/taatuut/ebmsolace/requirements.txt
```

As mentioned in the response, verify manually the final list of requirements.txt to avoid possible dependency confusions.

Prep
---
Check `sample.env` and copy/create `.env` with own values.

`source .env`

Add relevant information to configuration file (default config.json).

Run
---
A Solace broker must be running. Use PubSub+ cloud or a local broker. Can use a desktop tool like Docker and Podman, or go without desktop and use something like `colima`, see https://dev.to/mochafreddo/running-docker-on-macos-without-docker-desktop-64o

```
brew install docker
brew install colima
brew install qemu
brew services start colima
```

To fix issue with `colima` where running docker containers cannot be accessed on exposed ports, start `colima` with `--network-address`. This requires `qemu`. See https://github.com/abiosoft/colima/blob/main/docs/FAQ.md#the-virtual-machines-ip-is-not-reachable and https://github.com/abiosoft/colima/issues/801 for more information.

After `brew services start colima`, do a restart with `--network-address`.

```
colima stop
colima delete
colima start --cpu 8 --memory 12 --network-address
```

HINT: to watch the boot progress, see "~/.colima/_lima/<profile>/serial*.log"

Run `colima list` to check if it has an `ADDRESS`

```
PROFILE    STATUS     ARCH       CPUS    MEMORY    DISK      RUNTIME    ADDRESS
default    Running    aarch64    8       12GiB     100GiB    docker     192.168.64.2
```

Can do `colima ssh` to work in colima VM.

Do not use `--profile`, with this I could not find option to get colima running with an IP4 address (on a Apple M2 Max). 

Further testing with network driver not necessary now. Could look at `colima start --network-address --network-driver slirp --very-verbose` some time.

Run container with Solace PubSub+ Event Broker Standard edition. Note usage of environment variables assuming these are sourced and running on mac/linux.

```
docker run -d -p 8080:8080 -p 55554:55555 -p 8008:8008 -p 1883:1883 -p 8000:8000 -p 5672:5672 -p 9000:9000 -p 2222:2222 --shm-size=2g --env username_admin_globalaccesslevel=$SOLACE_USER --env username_admin_password=$SOLACE_PASS --name=$SOLACE_NAME solace/solace-pubsub-standard
```

NOTE: The VM environment `colima` needs some time for first start, has to download docker disk image, fire up stuff and become responsive, so `docker run...` might fail initially like:

```
brew services start colima <parameters>
==> Successfully started `colima` (label: homebrew.mxcl.colima)
docker run <parameters> solace/solace-pubsub-standard

docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?.
```

In that case just execute `docker run...` command again after a few seconds.

Check running containers with `docker ps -a`. To remove a container use `docker rm -f CONTAINER_ID`.

```
docker ps -a
CONTAINER ID   IMAGE                           COMMAND               CREATED         STATUS                     PORTS     NAMES
eff27f105325   solace/solace-pubsub-standard   "/usr/sbin/boot.sh"   2 minutes ago   Exited (2) 2 minutes ago             solacebms
```

To configure the Solace broker run:

```
python3 ez_broker_configuration.py
```

Check in Solace PubSub+ Event Broker management console at http://localhost:8080/ to see queue statistics.

Run the ebmssolace gateway:

```
python3 ebmsolace_gateway.py
```

Send a message, will go to both ebmssolace gateway and Solace broker.

```
python3 ebMSSoapSender.py
```

Run repeatedly every 10 seconds 

```
while true; do python3 ebMSSoapSender.py; sleep 10; done
```

Commands
---
```
python3 -m pip list > pip_list.txt
```

UML
---
https://www.planttext.com/

```
@startuml
participant "ebMS Sender" as Sender
participant "ebMS-Solace Gateway" as Gateway
participant "Solace Broker" as Broker
participant "CUSTOM-QNAME-ebms Queue" as Queue
participant "Solace Try Me!" as Consumer1
participant "MQTT Consumer" as Consumer2
participant "Custom Microservice" as Consumer3

Sender -> Gateway: Send ebMS SOAP Message
Gateway -> Gateway: Extract Digipoort-kenmerk & Convert to JSON
Gateway -> Broker: Publish JSON to topix "ebms/messages" (SMF Protocol)
Broker -> Queue: CUSTOM-QNAME-ebms attracts messages with subscription to "ebms/messages"
Queue -> Consumer1: Solace Try Me! consumes message from queue "CUSTOM-QNAME-ebms"
Queue -> Consumer2: MQTT Consumer consumes message from queue "CUSTOM-QNAME-ebms"
Queue -> Consumer3: A custom microservice consumes message from queue "CUSTOM-QNAME-ebms"

Gateway -> Sender: Acknowledge SOAP Response (200 OK)
@enduml
```

Notes
---
Handling SOAP messages with Solace PubSub+ broker:

```
1. REST Integration Options:
   - Use PubSub+ REST capabilities to bridge SOAP services
   - Leverage HTTP/HTTPS support with REST Delivery Points (RDPs)
   - Utilize HTTP 1.1 persistent connections
   - Supports both basic and client certificate authentication

2. Message Transformation Approach:
   - Use the Connector for Message Transformations to convert SOAP messages
   - Transform data on PubSub+ queues and topic endpoints
   - Configure workflows for message processing
   - Supports high availability with active-standby or active-active redundancy

3. Third-Party Integration Options:
   - Enterprise Service Bus (ESB) solutions that support both SOAP and Solace protocols
   - API gateways that can handle protocol translation
   - Integration platforms that support message transformation between SOAP and supported Solace protocols

4. Recommended Architecture Patterns:
   - Use REST as an intermediary protocol between SOAP and Solace
   - Implement message transformation workflows for protocol conversion
   - Leverage PubSub+ supported protocols like JMS or AMQP for integration
```

For detailed implementation guidance, refer to:

- REST Messaging Protocol Documentation

https://docs.solace.com/API/RESTMessagingPrtl/Solace-REST-Overview.htm

- Message Transformation Connector Guide

https://docs.solace.com/API/Connectors/Self-Contained-Connectors/Message-Processor/Message-Processor-Overview.htm

- PubSub+ Messaging APIs

https://docs.solace.com/API/Messaging-APIs/Solace-APIs-Overview.htm

Opentelemetry
---
To enable context propagation for distributed tracing, you must first add the Solace PubSub+ OpenTelemetry Python Integration package as a dependency in your application. You can also add this package with the following command:

```
python3 -m pip install pubsubplus-opentelemetry-integration
```

Then add the OpenTelemetry API and SDK libraries required for context propagation with the following commands:

```
python3 -m pip install opentelemetry-api==1.22.0 opentelemetry-sdk==1.22.0 opentelemetry-exporter-otlp
```

Note that `pubsubplus-opentelemetry-integration 1.0.1` requires `opentelemetry-api==1.22.0`.

Source: https://docs.solace.com/API/API-Developer-Guide-Python/Python-API-Distributed-Tracing.htm

Next steps
---
1.
Explore  Message Transformation Approach using connector.

https://docs.solace.com/API/Connectors/Self-Contained-Connectors/Message-Processor/Message-Processor-Overview.htm

2.
OpenTelemetry