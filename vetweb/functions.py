import base64
import requests

PAYPAL_CLIENT_ID = 'AU3YbLPbXaZOrXqmYVsY3c1UEhNBrNGHKUxIWHuqMx0e_LKnqQKNCvUBF5JZhSBEky2DYpM6IzHcq09R'
PAYPAL_CLIENT_SECRET = 'EDo11bKLHaRbvOZ33V9058W8z3t05W61hkyopiHEoh9c5rkj0uT7LWj7Lh-4Z6kW5pbAVTmXlxSA6VFe'
BASE_URL = "https://api-m.sandbox.paypal.com"  # URL para testing

def generateAccessToken(): 
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise ValueError('No hay credenciales de PayPal configuradas.')

    auth = f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}"
    auth = base64.b64encode(auth.encode()).decode('utf-8')

    response = requests.post(
        f"{BASE_URL}/v1/oauth2/token",
        data={"grant_type": "client_credentials"},
        headers={"Authorization": f"Basic {auth}"}
    )
    data = response.json()
    return data['access_token']

def createOrder(productos):
    print(productos)

    try:
        access_token = generateAccessToken()
        url = f"{BASE_URL}/v2/checkout/orders"
        payload = {
            "intent": "CAPTURE",
            "purchase_units":[
                {
                    "amount": {
                        "currency_code": "CLP",
                        "value": "1"
                    }
                }
            ]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    except Exception as error:
        print(error)