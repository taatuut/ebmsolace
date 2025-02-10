import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import xml.etree.ElementTree as ET
from solace.messaging.messaging_service import MessagingService
from solace.messaging.resources.topic import Topic
# ez
from ez_config_loader import ConfigLoader

def extract_soap_data(soap_xml):
    """Extracts Digipoort-kenmerk and body content from SOAP XML."""
    try:
        root = ET.fromstring(soap_xml)
        digipoort_kenmerk = root.find(".//Digipoort-kenmerk")
        payload = root.find(".//Payload")

        return (
            digipoort_kenmerk.text if digipoort_kenmerk is not None else "Unknown",
            payload.text if payload is not None else ""
        )
    except ET.ParseError:
        return "Unknown", ""

class SOAPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')        
        digipoort_kenmerk, payload = extract_soap_data(post_data)
        json_message = json.dumps({
            "Digipoort-kenmerk": digipoort_kenmerk,
            "Payload": payload
        })
        
        # TODO: create dynamic topic using SOLACE_TOPIC_EBMS as root based on incoming SOAP message properties
        topic_dest = Topic.of(SOLACE_TOPIC_EBMS) 
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
        print(f"Error publishing to Solace: {e}")
        return False

if __name__ == "__main__":
    # Load values from the configuration
    config = ConfigLoader("config.json")
    SOLACE_TOPIC_EBMS = config.get("ebms.topic")

    # Only print, write etc in debug modus, should be environment variable
    debug = True # True / False

    # NOTE: environment variables must be sourced in advance

    # Solace broker connection settings
    SOLACE_MESSAGE_VPN = os.environ["SOLACE_MESSAGE_VPN"]
    SOLACE_CLIENT_USER = os.environ["SOLACE_CLIENT_USER"]
    SOLACE_CLIENT_PASS = os.environ["SOLACE_CLIENT_PASS"]
    SOLACE_HOST = "localhost"
    SOLACE_PORT = 55554

    # Initialize Solace Messaging Service
    messaging_service = (
        MessagingService.builder()
        .from_properties({
            "solace.messaging.transport.host": f"tcp://{SOLACE_HOST}:{SOLACE_PORT}",
            "solace.messaging.service.vpn-name": SOLACE_MESSAGE_VPN,
            "solace.messaging.authentication.scheme.basic.username": SOLACE_CLIENT_USER,
            "solace.messaging.authentication.scheme.basic.password": SOLACE_CLIENT_PASS
        })
        .build()
    )

    # Connect to Solace broker
    messaging_service.connect()
    print("Connect to Solace broker...")

    # Create publisher
    publisher = messaging_service.create_persistent_message_publisher_builder().build()
    publisher.start()
    print("Pubsliher started...")

    server_address = ('localhost', 54321)
    httpd = HTTPServer(server_address, SOAPRequestHandler)
    print("Starting HTTP server on port 54321...")
    httpd.serve_forever()
