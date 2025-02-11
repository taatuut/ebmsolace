import os
import requests
import json
# ez
from ez_config_loader import ConfigLoader

def queue_exists():
    """Check if the queue already exists in the VPN."""
    response = requests.get(f"{BASE_URL}/queues/{QUEUE_NAME}", auth=AUTH)
    return response.status_code == 200

def create_queue():
    """Create the queue if it does not exist."""
    # See https://docs.solace.com/Cloud/Event-Portal/event-portal-runtime-config.htm for Queue Configuration Properties
    data = {
        "queueName": QUEUE_NAME,
        "accessType": "non-exclusive",
    	"maxMsgSpoolUsage": 15000,
        "owner": SOLACE_CLIENT_USER,
        "egressEnabled": True,
        "ingressEnabled": True
    }
    response = requests.post(f"{BASE_URL}/queues", headers=HEADERS, auth=AUTH, json=data)
    
    if response.status_code == 200 or response.status_code == 201:
        print(f"Queue '{QUEUE_NAME}' created successfully.")
        return True
    else:
        print(f"Failed to create queue '{QUEUE_NAME}': {response.text}")
        return False

def subscription_exists():
    """Check if the queue already has the topic subscription."""
    response = requests.get(f"{BASE_URL}/queues/{QUEUE_NAME}/subscriptions", auth=AUTH)
    
    if response.status_code == 200:
        subscriptions = response.json().get("data", [])
        return any(sub["subscriptionTopic"] == TOPIC_SUBSCRIPTION for sub in subscriptions)
    
    return False

def add_subscription():
    """Add the topic subscription to the queue."""
    data = {"subscriptionTopic": TOPIC_SUBSCRIPTION}
    response = requests.post(f"{BASE_URL}/queues/{QUEUE_NAME}/subscriptions", headers=HEADERS, auth=AUTH, json=data)

    if response.status_code == 200 or response.status_code == 201:
        print(f"Subscription '{TOPIC_SUBSCRIPTION}' added to queue '{QUEUE_NAME}'.")
    else:
        print(f"Failed to add subscription: {response.text}")

# Main Execution
if __name__ == "__main__":
    # Load values from the configuration
    config = ConfigLoader("config.json")
    # Queue and Subscription Details
    QUEUE_NAME = config.get("ebms.queue")
    TOPIC_SUBSCRIPTION = config.get("ebms.subscription")
    # Only print, write etc in debug modus, using config variable
    APP_DEBUG = config.get("app.debug")
    
    # NOTE: environment variables must be sourced in advance
    # Solace broker connection settings
    SOLACE_VPN = os.environ["SOLACE_MESSAGE_VPN"]
    SOLACE_USER = os.environ["SOLACE_USER"]
    SOLACE_PASS = os.environ["SOLACE_PASS"]
    SOLACE_CLIENT_USER = os.environ["SOLACE_CLIENT_USER"]
    SOLACE_HOST = os.environ["SOLACE_HOST"]
    SOLACE_MANAGEMENT_PORT = os.environ["SOLACE_MANAGEMENT_PORT"]

    # Base API URL
    BASE_URL = f"http://{SOLACE_HOST}:{SOLACE_MANAGEMENT_PORT}/SEMP/v2/config/msgVpns/{SOLACE_VPN}"

    # Headers
    HEADERS = {
        "Content-Type": "application/json"
    }

    # Authentication Tuple
    AUTH = (SOLACE_USER, SOLACE_PASS)

    if not queue_exists():
        print(f"Queue '{QUEUE_NAME}' does not exist. Creating...")
        if create_queue():
            add_subscription()
    else:
        print(f"Queue '{QUEUE_NAME}' already exists.")
        if not subscription_exists():
            print(f"Adding missing subscription '{TOPIC_SUBSCRIPTION}'...")
            add_subscription()
        else:
            print(f"Subscription '{TOPIC_SUBSCRIPTION}' already exists.")

    print("Done.")