ebmsolace
---

ebMS Solace PubSub+

Repo
---

`git clone https://github.com/taatuut/ebmsolace.git`

Setup
---

Create and source a Python virtual environment, use `~/.venv`.

Open a Terminal and run:

```
mkdir -p ~/.venv
python3 -m venv ~/.venv
source ~/.venv/bin/activate
```

Using the Terminal install Python modules (optional: update `pip`)

```
python3 -m pip install --upgrade pip
python3 -m pip install lxml
# for ebmsolace gateway
python3 -m pip install solace-pubsubplus
# for ez modules
python3 -m pip install pyyaml
```

Commands
---

```
python3 -m pip list > pip_list.txt
```

Prep
---

`source .env`

Run
---

A Solace broker must be running. Use PubSub+ cloud or a local broker. Can use a desktop tool like Docker and Podman, or go without using `colima` see https://dev.to/mochafreddo/running-docker-on-macos-without-docker-desktop-64o

```
brew install docker
brew install colima
brew install qemu
brew services start colima
```

To fix issue with `colima` where running docker containers cannot be accessed on exposed ports, start `colima` with `--network-address`. This requires `qemu`. See https://github.com/abiosoft/colima/blob/main/docs/FAQ.md#the-virtual-machines-ip-is-not-reachable and https://github.com/abiosoft/colima/issues/801 for more information.

After `brew services start colima` restart using

```
colima stop
colima delete
colima start --cpu 8 --memory 12 --network-address
```

HINT: to watch the boot progress, see "/Users/emilzegers/.colima/_lima/<profile>/serial*.log"

Run `colima list` to check if it has an `ADDRESS`

```
PROFILE    STATUS     ARCH       CPUS    MEMORY    DISK      RUNTIME    ADDRESS
default    Running    aarch64    8       12GiB     100GiB    docker     192.168.64.2
```

Can do `colima ssh` to work in colima.

Not using `--profile`, with this I could not find option to get an IP for colima (on Apple M2 Max). 

For further testing can do something like `colima start --network-address --network-driver slirp --very-verbose`

Run Solace broker container.

```
docker run -d -p 8080:8080 -p 55554:55555 -p 8008:8008 -p 1883:1883 -p 8000:8000 -p 5672:5672 -p 9000:9000 -p 2222:2222 --shm-size=2g --env username_admin_globalaccesslevel=$SOLACE_USER --env username_admin_password=$SOLACE_PASS --name=$SOLACE_NAME solace/solace-pubsub-standard
```

NOTE: The VM environment `colima` needs some time to start, download docker disk image, fire up stuff and become responsive, so `docker run...` might fail initially like:

```
brew services start colima

==> Successfully started `colima` (label: homebrew.mxcl.colima)
docker run -d -p 8080:8080 -p 55554:55555 -p 8008:8008 -p 1883:1883 -p 8000:8000 -p 5672:5672 -p 9000:9000 -p 2222:2222 --shm-size=2g --env username_admin_globalaccesslevel=$SOLACE_USER --env username_admin_password=$SOLACE_PASS --name=$SOLACE_NAME solace/solace-pubsub-standard
docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?.
```

In that case just execute `docker run...` command again after a few seconds.

Check running containers with `docker ps -a`.

To remove use `docker rm -f CONTAINER_ID`

```
docker ps -a
CONTAINER ID   IMAGE                           COMMAND               CREATED         STATUS                     PORTS     NAMES
eff27f105325   solace/solace-pubsub-standard   "/usr/sbin/boot.sh"   2 minutes ago   Exited (2) 2 minutes ago             solacebms
```

Configure broker

```
python3 ez_broker_configuration.py
```

Check in Solace PubSub+ Event Broker management console at http://localhost:8080/ to see queue statistics.

Run the ebmssolace gateway

```
python3 ebmsolace_gateway.py
```

Send message to ebmssolace gateway

```
python3 ebMSSoapSender.py
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

For detailed implementation guidance, refer to:

- REST Messaging Protocol Documentation

https://docs.solace.com/API/RESTMessagingPrtl/Solace-REST-Overview.htm

- Message Transformation Connector Guide

https://docs.solace.com/API/Connectors/Self-Contained-Connectors/Message-Processor/Message-Processor-Overview.htm

- PubSub+ Messaging APIs

https://docs.solace.com/API/Messaging-APIs/Solace-APIs-Overview.htm