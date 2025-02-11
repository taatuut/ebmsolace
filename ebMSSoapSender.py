import os
import requests
import uuid
import random
# ez
from ez_config_loader import ConfigLoader

def generate_uuid():
    return str(uuid.uuid4())

def getCPA():
    return random.choice(['cpa123456', 'cpa23456', 'cpa86420', 'cpa98765'])
def getService():
    return random.choice(['urn:services:SupplierOrderProcessing', 'urn:services:QuoteToCollect'])
def getAction():
    return random.choice(['NewPurchaseOrder', 'NewOrder', 'PurchaseOrderResponse'])

def create_ebms_soap_message(uuid_str, payload):
    # Define the SOAP envelope with ebMS headers and payload
    soap_env = f'''
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:eb="http://www.oasis-open.org/committees/ebxml-msg/schema/msg-header-2_0.xsd">
        <soapenv:Header>
            <eb:MessageHeader soapenv:mustUnderstand="1" eb:version="2.0">
                <eb:From>
                    <eb:PartyId>urn:example:sender</eb:PartyId>
                </eb:From>
                <eb:To>
                    <eb:PartyId>urn:example:receiver</eb:PartyId>
                </eb:To>
                <eb:CPAId>{getCPA()}</eb:CPAId>
                <eb:ConversationId>{uuid_str}</eb:ConversationId>
                <eb:Service>{getService()}</eb:Service>
                <eb:Action>{getAction()}</eb:Action>
                <eb:MessageData>
                    <eb:MessageId>{uuid_str}</eb:MessageId>
                    <eb:Timestamp>2025-02-10T12:00:00Z</eb:Timestamp>
                </eb:MessageData>
            </eb:MessageHeader>
        </soapenv:Header>
        <soapenv:Body>
            <eb:Manifest>
                <eb:Reference xlink:href="cid:{uuid_str}" xmlns:xlink="http://www.w3.org/1999/xlink"/>
            </eb:Manifest>
            <Payload>
                <Document>
                    <Digipoort-kenmerk>{uuid_str}</Digipoort-kenmerk>
                    <Content>{payload}</Content>
                </Document>
            </Payload>
        </soapenv:Body>
    </soapenv:Envelope>
    '''
    return soap_env

def send_ebms_message(url, message, uuid_str):
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'ebMS',
        'Digipoort-kenmerk': uuid_str
    }
    try:
        response = requests.post(url, data=message, headers=headers, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Request timed out: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    return None

def main():
    unique_id = generate_uuid()
    message_content = "Logius ipsum dolor sit amet, consectetur adipiscing elit. Phasellus mi nulla, commodo et porttitor eget, cursus eu arcu. In commodo augue eget ante vehicula tincidunt ut eget sapien."
    soap_message = create_ebms_soap_message(unique_id, message_content)
    response = send_ebms_message(EBMS_URL, soap_message, unique_id)    
    if response:
        print(f"SOAP request sent to gateway {EBMS_URL}")
        print("Gateway Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response text: {response.text}")
    else:
        print("Failed to send SOAP request to gateway.")
    response = send_ebms_message(f"{SOLACE_REST_URL}/{EBMS_TOPIC}/", soap_message, unique_id)
    if response:
        print(f"REST request sent to broker {SOLACE_REST_URL}/{EBMS_TOPIC}/")
        print("Broker Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response text: {response.text}")
    else:
        print("Failed to send REST request to broker.")

if __name__ == "__main__":
    # Load values from the configuration
    config = ConfigLoader("config.json")
    EBMS_URL = config.get("ebms.url")
    EBMS_TOPIC = config.get("ebms.topic")

    # NOTE: environment variables must be sourced in advance
    # Solace broker connection settings
    SOLACE_MESSAGE_VPN = os.environ["SOLACE_MESSAGE_VPN"]
    SOLACE_CLIENT_USER = os.environ["SOLACE_CLIENT_USER"]
    SOLACE_CLIENT_PASS = os.environ["SOLACE_CLIENT_PASS"]
    SOLACE_HOST = os.environ["SOLACE_HOST"]
    SOLACE_REST_PORT = os.environ["SOLACE_REST_PORT"]

    # Solace REST API URL
    SOLACE_REST_URL = f"http://{SOLACE_HOST}:{SOLACE_REST_PORT}"

    main()

