import requests
import uuid
# ez
from ez_config_loader import ConfigLoader

def generate_uuid():
    return str(uuid.uuid4())

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
                <eb:CPAId>ExampleCPA</eb:CPAId>
                <eb:ConversationId>{uuid_str}</eb:ConversationId>
                <eb:Service>ExampleService</eb:Service>
                <eb:Action>ExampleAction</eb:Action>
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
                <Document Digipoort-kenmerk="{uuid_str}">{payload}</Document>
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
    ebms_url = EBMS_URL
    unique_id = generate_uuid()
    soap_message = create_ebms_soap_message(unique_id, "Hallo wereld")
    response = send_ebms_message(ebms_url, soap_message, unique_id)
    
    if response:
        print("SOAP Request Sent:")
        print(soap_message)
        print("\nServer Response:")
        print(f"Status Code: {response.status_code}")
        print(response.text)
    else:
        print("Failed to send SOAP request.")

if __name__ == "__main__":
    # Load values from the configuration
    config = ConfigLoader("config.json")
    EBMS_URL = config.get("ebms.url")

    main()

