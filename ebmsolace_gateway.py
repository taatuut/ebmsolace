import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import xml.etree.ElementTree as ET
from solace.messaging.messaging_service import MessagingService, RetryStrategy
from solace.messaging.resources.topic import Topic
from solace.messaging.config.transport_security_strategy import TLS
from solace.messaging.config.authentication_strategy import ClientCertificateAuthentication
import time
# ez
from ez_config_loader import ConfigLoader
from ez_opentelemetry import *

def tprint(string):
    """Takes a string and prints it with a timestamp prefixt."""
    print('[{}] {}'.format(time.strftime("%Y-%m-%d %H:%M:%S"), string))

def extract_soap_data(soap_xml):
    """Extracts Digipoort-kenmerk and body content from SOAP XML."""
    try:
        root = ET.fromstring(soap_xml)
        digipoort_kenmerk = root.find(".//Digipoort-kenmerk")
        payload = root.find(".//Content")
        # Create dynamic topic using EBMS_TOPIC as root based on incoming SOAP message properties
        # Ok to have namespsaces and elements hardcoded as this is dedicated ebmsolace gateway script
        namespaces = {'eb': 'http://www.oasis-open.org/committees/ebxml-msg/schema/msg-header-2_0.xsd'} # add more as needed
        cpaid = root.find('.//eb:CPAId', namespaces)
        conversationid = root.find('.//eb:ConversationId', namespaces)
        service = root.find('.//eb:Service', namespaces)
        action = root.find('.//eb:Action', namespaces)
        return (
            digipoort_kenmerk.text if digipoort_kenmerk is not None else "Unknown",
            payload.text if payload is not None else "Unknown",
            cpaid.text if cpaid is not None else "Unknown",
            conversationid.text if conversationid is not None else "Unknown",
            service.text if service is not None else "Unknown",
            action.text if action is not None else "Unknown"
        )
    except ET.ParseError:
        return "Unknown", ""

class SOAPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        digipoort_kenmerk, payload, cpaid, conversationid, service, action = extract_soap_data(post_data)
        json_message = json.dumps({
            "Digipoort-kenmerk": digipoort_kenmerk,
            "Payload": payload,
            "CPAId": cpaid,
            "ConversationId": conversationid,
            "Service": service,
            "Action": action
        })
        topic = (
            f"{EBMS_TOPIC}/req/v1/"
            f"{digipoort_kenmerk}/{cpaid}/"
            f"{conversationid}/{service}/{action}"
        )        
        topic_dest = Topic.of(topic)
        if publish_to_solace(topic_dest, json_message):
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.end_headers()
            response_xml = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
                <soapenv:Body>
                    <Response>
                        <Message>Message acknowledged</Message>
                        <Digipoort-kenmerk>{digipoort_kenmerk}</Digipoort-kenmerk>
                    </Response>
                </soapenv:Body>
            </soapenv:Envelope>
            """
            self.wfile.write(response_xml.encode('utf-8'))
        else:
            self.send_response(500)
            self.end_headers()

def publish_to_solace(topic, message):
    """Publishes message to Solace broker using SMF protocol."""
    try:
        # Publish message
        publisher.publish(message, topic)
        return True
    except Exception as e:
        tprint(f"Error publishing to Solace: {e}")
        return False

if __name__ == "__main__":
    # Load values from the configuration
    config = ConfigLoader("config.json")
    EBMS_TOPIC = config.get("ebms.topic")
    # Only print, write etc in debug modus, using config variable
    APP_DEBUG = config.get("app.debug")

    # NOTE: environment variables must be sourced in advance
    # Solace broker connection settings
    SOLACE_MESSAGE_VPN = os.environ["SOLACE_MESSAGE_VPN"]
    SOLACE_CLIENT_USER = os.environ["SOLACE_CLIENT_USER"]
    SOLACE_CLIENT_PASS = os.environ["SOLACE_CLIENT_PASS"]
    SOLACE_HOST = os.environ["SOLACE_HOST"]
    SOLACE_SMF_PORT = os.environ["SOLACE_SMF_PORT"]
    SOLACE_TRUSTSTORE_PEM = os.environ["SOLACE_TRUSTSTORE_PEM"]

    tcp_protocol = 'tcps://' if SOLACE_SMF_PORT[-2:] == '43' else 'tcp://'

    broker_props = {
        "solace.messaging.transport.host": f"{tcp_protocol}{SOLACE_HOST}:{SOLACE_SMF_PORT}",
        "solace.messaging.service.vpn-name": SOLACE_MESSAGE_VPN,
        "solace.messaging.authentication.scheme.basic.username": SOLACE_CLIENT_USER,
        "solace.messaging.authentication.scheme.basic.password": SOLACE_CLIENT_PASS,
        #"solace.messaging.tls.trust-store-path": SOLACE_TRUSTSTORE_PEM
    }

    if tcp_protocol == 'tcp://': # TODO: sloppy... todo: proper check/setup
        # Initialize Solace Messaging Service
        messaging_service = (
            MessagingService.builder()
            .from_properties(broker_props)
            .build()
        )
    else:
        # In case of secure connection, still without certificate validation...
        transport_security_strategy = TLS.create().without_certificate_validation() # TLS.create().with_certificate_validation(True, validate_server_name=False, trust_store_file_path=f"{SOLACE_TRUSTSTORE_PEM}")
        messaging_service = (
            MessagingService.builder()
            .from_properties(broker_props)
            .with_reconnection_retry_strategy(RetryStrategy.parametrized_retry(20,3))
            .with_transport_security_strategy(transport_security_strategy)
            #.with_authentication_strategy(ClientCertificateAuthentication.of(certificate_file=f"{SOLACE_TRUSTSTORE_PEM}",key_file="key_file",key_password="key_store_password"))
            .build()   
        )
    
    # Connect to Solace broker
    messaging_service.connect()
    tprint("Connect to Solace broker...")

    # Create publisher
    publisher = messaging_service.create_persistent_message_publisher_builder().build()
    publisher.start()
    tprint("Pubsliher started...")

    server_address = ('localhost', 54321)
    httpd = HTTPServer(server_address, SOAPRequestHandler)
    tprint("Starting HTTP server on port 54321...")
    httpd.serve_forever()
