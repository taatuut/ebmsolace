# ebmsolace
ebMS Solace PubSub+ or `ebmsolace` is a simple demo to show sending eBMS messages to a Python 'gateway' and Solace PubSub+ event broker in various ways and formats.

## Context
This demo is developed on Mac OS using Python (3.10.6+) and Colimna. Some terminal commands need to be adjusted to run on Linux or Windows. 

## Repo
`git clone https://github.com/taatuut/ebmsolace.git`

## Setup
Create and source a Python virtual environment, this demo use `~/.venv`.

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

## Set environment variables
Check `sample.env` and copy/create `.env` with own values, then run:

```
source .env
```

Add relevant information to configuration file `config.json`.

## Publishing
To run a Solace broker use Solace PubSub+ Cloud platform or a local Solace event broker container image. To run a local broker use a tool like Docker Desktop or Podman Desktop, or go without desktop and use something like `colima`.

This demo assumes using a local broker but configuration settings can be changed to work with a cloud broker too. 

1. To run a Solace PubSub+ Event Broker container image run the following command. Note that the usage of environment variables assumes these are sourced before, also on Mac OS port 55555 must be mapped to 55554 as this is a reserved port since MacOS Big Sur.

```
docker run -d -p 8080:8080 -p 55554:55555 -p 8008:8008 -p 1883:1883 -p 8000:8000 -p 5672:5672 -p 9000:9000 -p 2222:2222 --shm-size=2g --env username_admin_globalaccesslevel=$SOLACE_USER --env username_admin_password=$SOLACE_PASS --name=$SOLACE_NAME solace/solace-pubsub-standard
```

2. Open Solace PubSub+ Event Broker management console at http://localhost:8080/. To configure the Solace broker run `python3 ez_broker_configuration.py`. This creates required queue and subscription if not existing and will outoput something like below. Then check Broker management / Messaging / Queues for information on the configured queue.

```
Queue 'CUSTOM-QNAME-ebms' does not exist. Creating...
Queue 'CUSTOM-QNAME-ebms' created successfully.
Subscription 'ebms/messages/>' added to queue 'CUSTOM-QNAME-ebms'.
Done.
```

3. In one terminal run the ebmssolace gateway with `python3 ebmsolace_gateway.py`. Will output something like:

```
Connect to Solace broker...
Pubsliher started...
Starting HTTP server on port 54321...
```

4. Open another terminal to send messages from. Make sure environment variables are available (run `source .env`) and virtual environment is activated (run `source ~/.venv/bin/activate`). The messages are sent in two ways:

- directly to the Solace PubSub+ broker REST API, and 
- to the ebmssolace gateway started in the previous step: the gateway processes the message (conversion from XML to json, setting dynamic topic) and then sends it to the Solace PubSub+ broker using SMF protocol.

To execute once run `python3 ebMSSoapSender.py`, or run repeatedly every five seconds with `while true; do python3 ebMSSoapSender.py; sleep 5; done`

## Subscribing
Client applications you can use to subscribe to the topic or queue on the broker (see `config.json` for name) to display and/or consume the published messages:

- Solace `SDKPerf`
- The Solace `Try Me!` functionality available in the broker manager user interface, easy way to see both the XML and JSON messages and dynamic topic defintion
- `MQTTX` (https://mqttx.app/)
- Or your custom microservice (a simple Python script)

Using the SDKPerf for Java & JMS, for more information on SDKPerf see https://docs.solace.com/API/SDKPerf/SDKPerf.htm Again reusing the environment variables so these must be sourced.

```
cd ~/sdkperf/sdkperf-jcsmp-8.4.17.5
while true; do ./sdkperf_java.sh -cip=tcp://$SOLACE_HOST:$SOLACE_SMF_PORT -cu=$SOLACE_CLIENT_USER -cp=$SOLACE_CLIENT_PASS -sql='CUSTOM-QNAME-ebms' -md; sleep 5; done
```

For Try Me! and MQTTX see folder `./images` for related screenshots.

## Extra: using Solace PubSub+ CLoud platform

In Solace PubSub+ Cloud platform Cloud Console get the required parameter values for `.env.solace.cloud` file, then run `source .env.solace.cloud`

To configure the Solace PubSub+ Cloud broker service run `python3 ez_broker_configuration.py`.

Error message as below indicates something is wrong with port value and `http` protocol setting.

```
Queue 'CUSTOM-QNAME-ebms' does not exist. Creating...
Failed to create queue 'CUSTOM-QNAME-ebms': <html>
<head><title>400 The plain HTTP request was sent to HTTPS port</title></head>
<body>
<center><h1>400 Bad Request</h1></center>
<center>The plain HTTP request was sent to HTTPS port</center>
<hr><center>nginx</center>
</body>
</html>
```

If all is good check Broker management / Messaging / Queues for information on the configured queue.

In all open terminals run `source .env.solace.cloud` and start scripts `python3 ebmsolace_gateway.py` and `while true; do python3 ebMSSoapSender.py; sleep 5; done` again.

Error message as below indicates something is wrong with port value and `tcp` protocol setting.

```
2025-04-24 00:29:33,172 [WARNING] solace.messaging.core: [_solace_transport.py:89]  [[SERVICE: 0x10691f440] - [APP ID: ezSolace.local/41267/00000001/3q8Zy8WmZC]] {'caller_description': 'From service event callback', 'return_code': 'Ok', 'sub_code': 'SOLCLIENT_SUBCODE_COMMUNICATION_ERROR', 'error_info_sub_code': 14, 'error_info_contents': 'TCP: Could not read from socket 8, error = Connection reset by peer (54)'}
2025-04-24 00:29:33,172 [WARNING] solace.messaging.core: [_solace_transport.py:89]  [[SERVICE: 0x10691f440] - [APP ID: ezSolace.local/41267/00000001/3q8Zy8WmZC]] {'caller_description': 'do_connect', 'return_code': 'Not ready', 'sub_code': 'SOLCLIENT_SUBCODE_COMMUNICATION_ERROR', 'error_info_sub_code': 14, 'error_info_contents': 'TCP: Could not read from socket 8, error = Connection reset by peer (54)'}
2025-04-24 00:29:33,172 [WARNING] solace.messaging.connections: [messaging_service.py:1262]  [[SERVICE: 0x10691f440] - [APP ID: ezSolace.local/41267/00000001/3q8Zy8WmZC]] Connection failed. Status code: 3
Traceback (most recent call last):
  File "~/GitHub/taatuut/ebmsolace/ebmsolace_gateway.py", line 116, in <module>
    messaging_service.connect()
  File "~/.venv/lib/python3.12/site-packages/solace/messaging/messaging_service.py", line 1263, in connect
    raise error
solace.messaging.errors.pubsubplus_client_error.PubSubPlusCoreClientError: {'caller_description': 'do_connect', 'return_code': 'Not ready', 'sub_code': 'SOLCLIENT_SUBCODE_COMMUNICATION_ERROR', 'error_info_sub_code': 14, 'error_info_contents': 'TCP: Could not read from socket 8, error = Connection reset by peer (54)'}
```

Error message as below indicates something is wrong with secure connection setup related to (missing)) trust store PEM file and (missing)) import statements.

```
2025-04-24 00:35:13,103 [WARNING] solace.messaging.core: [_solace_session.py:885]  [[SERVICE: 0x103a66450] - [APP ID: None]] SOLCLIENT_SUBCODE_FAILED_LOADING_TRUSTSTORE
2025-04-24 00:35:13,103 [WARNING] solace.messaging.core: [_solace_session.py:887]  [[SERVICE: 0x103a66450] - [APP ID: None]] SESSION CREATION UNSUCCESSFUL. Failed to load trust store.
Traceback (most recent call last):
  File "~/GitHub/taatuut/ebmsolace/ebmsolace_gateway.py", line 114, in <module>
    .build()
     ^^^^^^^
  File "~/.venv/lib/python3.12/site-packages/solace/messaging/messaging_service.py", line 1770, in build
    return _BasicMessagingService(config=self._stored_config, application_id=application_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.venv/lib/python3.12/site-packages/solace/messaging/messaging_service.py", line 1064, in __init__
    self._session.create_session(self._config)  # create the session as part of Messaging Service build process
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.venv/lib/python3.12/site-packages/solace/messaging/core/_solace_session.py", line 888, in create_session
    raise PubSubPlusCoreClientError(message=FAILED_TO_LOAD_TRUST_STORE, sub_code=info_sub_code)
solace.messaging.errors.pubsubplus_client_error.PubSubPlusCoreClientError: SESSION CREATION UNSUCCESSFUL. Failed to load trust store.
```

Specific import statements for Solace secure connection:

```
from solace.messaging.messaging_service import RetryStrategy
from solace.messaging.config.transport_security_strategy import TLS
from solace.messaging.config.authentication_strategy import ClientCertificateAuthentication
```

For now using secure connection without certificate validation.

## Some useful commands
```
python3 -m pip list > pip_list.txt
```

To find a `pid` for a script run `ps aux | grep <name>.py`. To stop a process run `kill -9 <pid>`

## UML
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

## Notes
Handling SOAP messages with Solace PubSub+ broker:

```
1. REST Integration Options:
- Use PubSub+ REST capabilities to bridge SOAP services
- Leverage HTTP/HTTPS support with REST Delivery Points (RDPs)
- Utilize HTTP 1.1 persistent connections
- Supports both basic and client certificate authentication

2. Message Transformation Approach:
- Use the Connector for Message Transformations to convert SOAP messages
- Transform data on PubSub+ queues and topic endpoints
- Configure workflows for message processing
- Supports high availability with active-standby or active-active redundancy

3. Third-Party Integration Options:
- Enterprise Service Bus (ESB) solutions that support both SOAP and Solace protocols
- API gateways that can handle protocol translation
- Integration platforms that support message transformation between SOAP and supported Solace protocols

4. Recommended Architecture Patterns:
- Use REST as an intermediary protocol between SOAP and Solace
- Implement message transformation workflows for protocol conversion
- Leverage PubSub+ supported protocols like JMS or AMQP for integration
```

For detailed implementation guidance, refer to:

- REST Messaging Protocol Documentation

https://docs.solace.com/API/RESTMessagingPrtl/Solace-REST-Overview.htm

- Message Transformation Connector Guide

https://docs.solace.com/API/Connectors/Self-Contained-Connectors/Message-Processor/Message-Processor-Overview.htm

- PubSub+ Messaging APIs

https://docs.solace.com/API/Messaging-APIs/Solace-APIs-Overview.htm

OpenTelemetry
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

## Next steps
1.
Explore Message Transformation Approach using connector.

https://docs.solace.com/API/Connectors/Self-Contained-Connectors/Message-Processor/Message-Processor-Overview.htm

2.
Observability Log fowarding, Insights monitoring, Distributed Tracing OpenTelemetry

## Appendices

### Appendix Python
Use `pipreqs` to collect and check required modules (do not use `freeze`).

```
python3 -m pip install pipreqs
```

Then use `which python` to find path to folder where pipreqs resides.

```
which python
 ~/.venv/bin/python
```

So `pipreqs` is in folder ` ~/.venv/bin/`. Now execute `pipreqs` using full paths.

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

### Appendix colima
See https://dev.to/mochafreddo/running-docker-on-macos-without-docker-desktop-64o

```
brew install docker
brew install colima
brew install qemu
brew services start colima
```

To fix issue with `colima` where running docker containers cannot be accessed on exposed ports, start `colima` with `--network-address`. This requires `qemu`. See https://github.com/abiosoft/colima/blob/main/docs/FAQ.md#the-virtual-machines-ip-is-not-reachable and https://github.com/abiosoft/colima/issues/801 for more information.

After `brew services start colima`, do a restart with `--network-address`.

```
colima stop -f
colima start --cpu 4 --memory 4 --network-address
```

HINT: to watch the boot progress, see "~/.colima/_lima/<profile>/serial*.log"

NOTE: Only use `colima delete` if you need to start with a clean sheet again. Will remove local images so needs to download again. 

Run `colima list` to check if it has an `ADDRESS`

```
PROFILE    STATUS     ARCH       CPUS    MEMORY    DISK      RUNTIME    ADDRESS
default    Running    aarch64    8       12GiB     100GiB    docker     192.168.64.2
```

Can do `colima ssh` to work in colima VM.

Do not use `--profile`, with this I could not find option to get colima running with an IP4 address (on a Apple M2 Max). 

Further testing with network driver not necessary now. Could look at `colima start --network-address --network-driver slirp --very-verbose` some time.

NOTE: The VM environment `colima` needs some time for first start, has to download docker disk image, fire up stuff and become responsive, so `docker run...` might fail initially like:

```
brew services start colima <parameters>
==> Successfully started `colima` (label: homebrew.mxcl.colima)
docker run <parameters> solace/solace-pubsub-standard
docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?.
```

In that case just execute `docker run...` command again after a few seconds.

List all containers with `docker ps -a`. To remove a container use `docker rm -f CONTAINER_ID`.

```
docker ps -a
CONTAINER ID   IMAGE                           COMMAND               CREATED         STATUS                     PORTS     NAMES
eff27f105325   solace/solace-pubsub-standard   "/usr/sbin/boot.sh"   2 minutes ago   Exited (2) 2 minutes ago             solacebms
```

