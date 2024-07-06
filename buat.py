from flask import Flask, request, jsonify
from midtransclient import CoreApi
from pymongo import MongoClient
from models import orders_collection
app = Flask(__name__)

# Konfigurasi MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client.nama_database  # Ganti dengan nama database yang sesuai
orders_collection  # Ganti dengan nama koleksi yang sesuai

# Inisialisasi API client Midtrans
api_client = CoreApi(
    is_production=False,
    server_key='SB-Mid-server-z8FSfLzdnI_a7iqoVorBidcJ',
    client_key='SB-Mid-client-ZeSro0aAvX_ctrEe'
)

@app.route('/midtrans/notification', methods=['POST'])
def midtrans_notification():
    notification_data = request.get_json()

    # Handle notification JSON sent by Midtrans, it auto verifies it by doing get status
    status_response = api_client.transactions.notification(notification_data)

    order_id = status_response['order_id']
    transaction_status = status_response['transaction_status']
    fraud_status = status_response['fraud_status']

    print('Transaction notification received. Order ID: {0}. Transaction status: {1}. Fraud status: {2}'.format(
        order_id, transaction_status, fraud_status))

    # Sample transaction_status handling logic
    if transaction_status == 'capture':
        if fraud_status == 'challenge':
            # TODO: set transaction status on your database to 'challenge'
            pass
        elif fraud_status == 'accept':
            # TODO: set transaction status on your database to 'success'
            pass
    elif transaction_status in ['cancel', 'deny', 'expire']:
        # TODO: set transaction status on your database to 'failure'
        pass
    elif transaction_status == 'pending':
        # TODO: set transaction status on your database to 'pending' / waiting payment
        pass

    return jsonify({'status': 'OK'}), 200

if __name__ == '__main__':
    app.run(debug=True)
