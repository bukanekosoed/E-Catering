from flask import Blueprint, request, redirect, url_for, flash, render_template,jsonify, session
from dotenv import load_dotenv
import os
from flask_login import login_required, current_user
from models import carts_collection,menus_collection,orders_collection,get_cart_details, get_shipment
from bson import ObjectId
from midtransclient import Snap
import uuid
import datetime
import pytz

user_bp = Blueprint('user', __name__)
load_dotenv()

midtrans_client = Snap(
    is_production=False,
    server_key=(os.getenv('MIDTRANS_SERVER_KEY')),
    client_key=(os.getenv('MIDTRANS_CLIENT_KEY'))
)


@user_bp.route('/add_to_cart/<menu_id>', methods=['POST'])
@login_required
def add_to_cart(menu_id):
    
    quantity = int(request.form.get('quantity', 1))
    query = {
        'user_id': ObjectId(current_user.id)
    }
    user_cart = carts_collection.find_one(query)

    if user_cart:
        updated = False
        for item in user_cart['cart_items']:
            if item['menu_id'] == ObjectId(menu_id):
                item['quantity'] += quantity
                updated = True
                break
        
        if not updated:
            new_item = {
                'menu_id': ObjectId(menu_id),
                'quantity': quantity
            }
            user_cart['cart_items'].append(new_item)

        carts_collection.update_one(query, {'$set': {'cart_items': user_cart['cart_items']}})
        flash('Menu Berhasil Ditambahkan','success')
    else:
        
        cart_item = {
            'user_id':ObjectId(current_user.id),
            'cart_items': [{
                'menu_id':  ObjectId(menu_id),
                'quantity': quantity
            }]
        }
        carts_collection.insert_one(cart_item)
        flash('Menu Berhasil Ditambahkan','success')

    # Redirect to the previous page or the cart page
    return redirect(url_for("index"))

@user_bp.route('/keranjang')
@login_required
def keranjang():
    cart_items_count = get_cart_items_count()
    cart_details = get_cart_details()

    return render_template('user/keranjang.html', cart_items_count=cart_items_count, cart_details=cart_details)

@user_bp.route('/menu')
@login_required
def menu():
    cart_items_count = get_cart_items_count()
    menus = list(menus_collection.find({}))
    categories = menus_collection.distinct('kategori')
    return render_template('user/menu.html', menus=menus, categories=categories, cart_items_count=cart_items_count)
    
@user_bp.route('/update_quantity/<menu_id>', methods=['POST'])
@login_required
def update_quantity(menu_id):
    action = request.form.get('action')
    quantity = int(request.form.get('quantity', 1))
    query = {
        'user_id': ObjectId(current_user.id)
    }
    user_cart = carts_collection.find_one(query)

    if user_cart:
        for item in user_cart['cart_items']:
            if item['menu_id'] == ObjectId(menu_id):
                if action == 'increase':
                    item['quantity'] += 1
                elif action == 'decrease' and item['quantity'] > 1:
                    item['quantity'] -= 1
                break

        carts_collection.update_one(query, {'$set': {'cart_items': user_cart['cart_items']}})
    return redirect(url_for('user.keranjang'))

@user_bp.route('/delete_menu/<menu_id>', methods=['POST'])
@login_required
def delete_menu(menu_id):
    query = {'user_id': ObjectId(current_user.id)}
    update = {'$pull': {'cart_items': {'menu_id': ObjectId(menu_id)}}}
    result = carts_collection.update_one(query, update)

    result.modified_count > 0
    
    return redirect(url_for('user.keranjang'))


@user_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    timezone = pytz.timezone('Asia/Jakarta')
    current_datetime = datetime.datetime.now(timezone)
    expiry_time = current_datetime + datetime.timedelta(days=1)
    expiry_time_str = expiry_time.strftime('%Y-%m-%d %H:%M:%S %z')
    delivery_date = request.form.get('deliveryDate')
    delivery_address = {
        'province': request.form.get('province'),
        'district': request.form.get('district'),
        'sub_district': request.form.get('subDistrict'),
        'village': request.form.get('village'),
        'zipcode': request.form.get('zipcode'),
        'street_address': request.form.get('streetAddress')
    }
    if current_user.is_authenticated:
        user_id = ObjectId(current_user.id)
        cart_details = get_cart_details()
    
        if cart_details:
            items_details = []
            item_details = [
                            {
                                "id": item['menu_id'],
                                "price": item['harga'],
                                "quantity": item['quantity'],
                                "name": item['nama'],
                                "category": item['kategori']
                            }
                            for item in cart_details['cart_items']
                        ]
            for item in cart_details['cart_items']:
                item_detail = {
                    'id': ObjectId(item['menu_id']),  # Sesuaikan dengan field yang sesuai dari MongoDB
                    # 'price': item['harga'],  # Harga per item
                    'quantity': item['quantity'],  # Jumlah item
                    # 'name': item['nama'],  # Nama item
                    # 'category': item['kategori']  # Kategori item (opsional)
                }
                items_details.append(item_detail)

            # Prepare customer details
            customer_details = {
                'first_name': cart_details['user']['name'],
                'email': cart_details['user']['email'],
                'phone': cart_details['user']['phone'],
                "billing_address": {
                    "first_name": cart_details['user']['name'],
                    "email": cart_details['user']['email'],
                    "phone": cart_details['user']['phone'],
                },
                "shipping_address": {
                    "first_name": cart_details['user']['name'],
                    "email": cart_details['user']['email'],
                    "phone": cart_details['user']['phone'],
                    "address": f'{delivery_address["street_address"]}, {delivery_address["village"]},',
                    "city": f'{delivery_address["sub_district"]}, {delivery_address["district"]}, {delivery_address["province"]}',
                    "postal_code": delivery_address['zipcode'],
                    "country_code": "IDN"
                }
            }

            # Create transaction token using Snap API
            transaction_details = {
                'transaction_details': {
                    'order_id': f'LanggengCatering-{uuid.uuid4().hex[:4]}',
                    'gross_amount': cart_details['grandTotal']
                },
                
                "item_details": item_details,
                'customer_details': customer_details,
                'credit_card': {
                    'secure': True
                },
                "callbacks": {
                    "finish": "{{url_for('user.order')}}",
                    "error": "https://your-domain.com/midtrans/error"
                }
            }

            try:
                # Create Snap token
                snap_token = midtrans_client.create_transaction(transaction_details)['token']
                
                # Save order details to orders_collection
                order_data = {
                    'user_id': ObjectId(user_id),
                    'order_id': transaction_details['transaction_details']['order_id'],
                    'order_date': current_datetime.strftime('%Y-%m-%d %H:%M:%S %z'),
                    'expiry_time':expiry_time_str,
                    'delivery_date': delivery_date,
                    'total_amount': int(cart_details['grandTotal']),
                    'payment_status': 'pending',
                    'snap_token': snap_token,
                    "item_details": items_details,  # Save cart items to order
                    'delivery_address': delivery_address,
                }
                orders_collection.insert_one(order_data)

                # Clear the user's cart
                carts_collection.delete_one({'user_id': user_id})

                return jsonify({'snap_token': snap_token}), 200

            except Exception as e:
                print(f"Error: {str(e)}")
                return jsonify({'error': 'Failed to initiate payment'}), 500

    return jsonify({'error': 'Cart not found'}), 404


@user_bp.route('/midtrans_webhook', methods=['POST'])
def midtrans_webhook():
    webhook_data = request.get_json()

    # Log the received webhook dat
    # Process data from webhook Midtrans
    order_id = webhook_data.get('order_id')
    transaction_time = webhook_data.get('transaction_time')
    gross_amount = webhook_data.get('gross_amount')
    transaction_status = webhook_data.get('transaction_status')
    expiry_time = webhook_data.get('expiry_time')


    # Prepare data to be saved
    order_data = {
        'order_id': order_id,
        'order_date': transaction_time,
        'expiry_time' : expiry_time,
        'payment_status': transaction_status,
        
    }
    if expiry_time:
        order_data['expiry_time'] = expiry_time

    orders_collection.update_one(
        {"order_id": order_id},
        {"$set": order_data},
        upsert=True
    )

    return jsonify({"message": "Webhook received"}), 200


@user_bp.route('/orders', methods=['GET'])
@login_required
def get_order():
    user_id = ObjectId(current_user.id)  # Sesuaikan dengan cara Anda mendapatkan user ID
    orders = get_shipment()
    cart_items_count = get_cart_items_count()
    return render_template('user/pesanan.html', orders=orders, cart_items_count=cart_items_count,)


def get_cart_items_count():
    if current_user.is_authenticated:
        user_id = ObjectId(current_user.id)
        cart = carts_collection.find_one({'user_id': user_id})
        if cart:
            return len(cart.get('cart_items', []))
    return 0
