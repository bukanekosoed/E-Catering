from flask_login import UserMixin, current_user
from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

# Setup MongoDB connection
client = MongoClient(os.getenv('MONGO_URI'))
db = client[os.getenv('DB_NAME')]

# Define MongoDB collections
users_collection = db['users']
admins_collection = db['admin']
menus_collection = db['menus']
carts_collection = db['keranjang']
orders_collection = db['pesanan']

class User(UserMixin):
    def __init__(self, id, email, role):
        self.id = id
        self.email = email
        self.role = role

def get_cart_details():
    if current_user.is_authenticated:
        user_id = ObjectId(current_user.id)
        
        pipeline = [
            {
                '$match': {
                    'user_id': user_id  # Sesuaikan dengan nama field yang digunakan di collection carts
                }
            },
            {
        '$lookup': {
            'from': 'menus', 
            'localField': 'cart_items.menu_id', 
            'foreignField': '_id', 
            'as': 'cart_items_with_menus'
        }
    }, 
    {
        '$lookup': {
            'from': 'users', 
            'localField': 'user_id', 
            'foreignField': '_id', 
            'as': 'user'
        }
    },
    {
        '$addFields': {
            'cart_items': {
                '$map': {
                    'input': '$cart_items', 
                    'as': 'item', 
                    'in': {
                        '$mergeObjects': [
                            '$$item', {
                                '$arrayElemAt': [
                                    {
                                        '$filter': {
                                            'input': '$cart_items_with_menus', 
                                            'cond': {
                                                '$eq': [
                                                    '$$this._id', '$$item.menu_id'
                                                ]
                                            }
                                        }
                                    }, 0
                                ]
                            }
                        ]
                    }
                }
            }, 
            'cart_items_with_menus': '$$REMOVE', 
            'user': {
                '$arrayElemAt': [
                    '$user', 0
                ]
            }
        }
    }, 
    {
        '$addFields': {
            'cart_items': {
                '$map': {
                    'input': '$cart_items', 
                    'as': 'item', 
                    'in': {
                        '$mergeObjects': [
                            '$$item', {
                                'total': {
                                    '$multiply': [
                                        '$$item.quantity', '$$item.harga'
                                    ]
                                }
                            }
                        ]
                    }
                }
            }, 
            'grandTotal': {
                '$sum': {
                    '$map': {
                        'input': '$cart_items', 
                        'as': 'item', 
                        'in': {
                            '$multiply': [
                                '$$item.quantity', '$$item.harga'
                            ]
                        }
                    }
                }
            }
        }
    }, 
    {
        '$addFields': {
            'grandTotalWithPPN': {
                '$trunc': {
                    '$multiply': [
                        '$grandTotal', 1.11
                    ]
                }
            }
        }
    },
  	{
        '$addFields': {
            'ppn': {
                '$trunc': {
                    '$multiply': [
                        '$grandTotal', 0.11
                    ]
                }
            }
        }
    },
    {
        '$project': {
            'user_id': 1, 
            'cart_items': {
                'menu_id': 1, 
                'nama': 1, 
                'kategori': 1, 
                'quantity': 1, 
                'harga': 1, 
                'total': 1,
                'gambar': 1
            }, 
            'user': {
                'name': 1, 
                'email': 1, 
                'phone': 1
            }, 
            'grandTotal': 1,
          	'ppn': 1,
            'grandTotalWithPPN': 1,
        }
    }
    ]
        
        cart = carts_collection.aggregate(pipeline)
        
        # Since aggregate returns a cursor, we need to convert the result to a list
        cart = list(cart)
        
        # If there's exactly one result, return it; otherwise, handle as needed
        if cart:
            # Convert ObjectId to string
            for item in cart[0]['cart_items']:
                item['menu_id'] = str(item['menu_id'])
            
            return cart[0]
    
    return None

def get_shipment():
    
        user_id = ObjectId(current_user.id)
        pipeline = [
            {
                '$match': {
                    'user_id': user_id  # Sesuaikan dengan nama field yang digunakan di collection carts
                }
            },
            {
                '$lookup': {
                    'from': 'menus', 
                    'localField': 'item_details.id', 
                    'foreignField': '_id', 
                    'as': 'result'
                }
            }, {
                '$lookup': {
                    'from': 'users', 
                    'localField': 'user_id', 
                    'foreignField': '_id', 
                    'as': 'user'
                }
            }, {
                '$addFields': {
                    'item_details': {
                        '$map': {
                            'input': '$item_details', 
                            'as': 'item', 
                            'in': {
                                '$mergeObjects': [
                                    '$$item', {
                                        '$arrayElemAt': [
                                            {
                                                '$filter': {
                                                    'input': '$result', 
                                                    'cond': {
                                                        '$eq': [
                                                            '$$this._id', '$$item.id'
                                                        ]
                                                    }
                                                }
                                            }, 0
                                        ]
                                    }
                                ]
                            }
                        }
                    }, 
                    'cart_items_with_menus': '$$REMOVE', 
                    'user': {
                        '$arrayElemAt': [
                            '$user', 0
                        ]
                    }
                }
            }, {
                '$addFields': {
                    'item_details': {
                        '$map': {
                            'input': '$item_details', 
                            'as': 'item', 
                            'in': {
                                '$mergeObjects': [
                                    '$$item', {
                                        'total': {
                                            '$multiply': [
                                                '$$item.quantity', '$$item.harga'
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    }
                },
            }, {
            '$sort': {'order_date': DESCENDING}  # Ubah 'timestamp_field' sesuai dengan nama field timestamp Anda
            },
            {
                '$project': {
                    'user_id': 1, 
                    'item_details': {
                        'id': 1, 
                        'nama': 1, 
                        'kategori': 1, 
                        'quantity': 1, 
                        'harga': 1, 
                        'total': 1, 
                        'gambar': 1
                    }, 
                    'user': {
                        'name': 1, 
                        'email': 1, 
                        'phone': 1
                    }, 
                    'total_amount': 1,
                    'payment_status':1,
                    'expiry_time':1,
                    'order_id':1,
                    'snap_token':1
                }
            }
        ]
        orders = list(orders_collection.aggregate(pipeline))
        
        # If there's exactly one result, return it; otherwise, handle as needed
        
                
            
        return orders
    
def get_order():
    pipeline = [
            {
                '$lookup': {
                    'from': 'menus', 
                    'localField': 'item_details.id', 
                    'foreignField': '_id', 
                    'as': 'result'
                }
            }, {
                '$lookup': {
                    'from': 'users', 
                    'localField': 'user_id', 
                    'foreignField': '_id', 
                    'as': 'user'
                }
            }, {
                '$addFields': {
                    'item_details': {
                        '$map': {
                            'input': '$item_details', 
                            'as': 'item', 
                            'in': {
                                '$mergeObjects': [
                                    '$$item', {
                                        '$arrayElemAt': [
                                            {
                                                '$filter': {
                                                    'input': '$result', 
                                                    'cond': {
                                                        '$eq': [
                                                            '$$this._id', '$$item.id'
                                                        ]
                                                    }
                                                }
                                            }, 0
                                        ]
                                    }
                                ]
                            }
                        }
                    }, 
                    'cart_items_with_menus': '$$REMOVE', 
                    'user': {
                        '$arrayElemAt': [
                            '$user', 0
                        ]
                    }
                }
            }, {
                '$addFields': {
                    'item_details': {
                        '$map': {
                            'input': '$item_details', 
                            'as': 'item', 
                            'in': {
                                '$mergeObjects': [
                                    '$$item', {
                                        'total': {
                                            '$multiply': [
                                                '$$item.quantity', '$$item.harga'
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    }
                },
            }, 
            {
            '$sort': {'order_date': DESCENDING}  # Ubah 'timestamp_field' sesuai dengan nama field timestamp Anda
            },
            {
                '$project': {
                    'user_id': 1, 
                    'item_details': {
                        'id': 1, 
                        'nama': 1, 
                        'kategori': 1, 
                        'quantity': 1, 
                        'harga': 1, 
                        'total': 1, 
                        'gambar': 1
                    }, 
                    'user': {
                        'name': 1, 
                        'email': 1, 
                        'phone': 1
                    }, 
                    'total_amount': 1,
                    'payment_status':1,
                    'expiry_time':1,
                    'order_id':1,
                    'snap_token':1
                }
            }
        ]
        
    orders = list(orders_collection.aggregate(pipeline))
        
    return orders