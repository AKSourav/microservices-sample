from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token,get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
import os
import requests

from serializers import ItemSchema, ShopSchema, VariantSchema

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///shop.db')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'abcd')

db = SQLAlchemy(app)
jwt = JWTManager(app)

item_schema = ItemSchema()
shop_schema= ShopSchema()
variant_schema = VariantSchema()

class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    shopkeeper_id = db.Column(db.Integer, unique=True, nullable=False)
    items= db.relationship('Item', backref=db.backref('shop', lazy=True))
    def __repr__(self):
        return '<Shop %r>' % self.name

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),nullable=False)
    item_type = db.Column(db.String(80),nullable=False,default="icecream")
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)

    def __repr__(self):
        return '<Item %r>' % self.name
    
class Variant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),nullable=False)
    variant_type = db.Column(db.String(80),nullable=False,default="flavour")
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

    def __repr__(self):
        return '<Variant %r>' % self.name
    
# Initialize the database
with app.app_context():
    db.create_all()

# Shops
@app.route('/shop/create', methods=['POST'])
@jwt_required()
def createShop():
    data = request.get_json()
    try:
        hostname = os.environ.get('AUTH_SERVICE_HOST', 'localhost:5000')
        url= f"http://{hostname}/auth/verify"
        response = requests.get(url, headers=request.headers)

        if response.status_code >=  400:
            print(f"Error: {response.status_code} - {response.text}")
            return jsonify(response.json()),   response.status_code
        
        user=response.json()
        if user.get('user_type')!="SUPER":
            return jsonify({"message":"only superuser can create shop"}),   401
        existing_shop=Shop.query.filter_by(shopkeeper_id=data.get('shopkeeper_id')).first()
        if existing_shop:
            return jsonify({"message":"shopkeep can be assigned to only one shop"}),   400
        new_shop = Shop(name=data.get('name'), shopkeeper_id=data.get("shopkeeper_id"))
        db.session.add(new_shop)
        db.session.commit()
        print(new_shop)
        new_shop_dict=shop_schema.dump(new_shop)
        return jsonify(new_shop_dict),   200
    except Exception as e:
        print(e)
        return jsonify({'message': 'Some error occured'}),   401

@app.route('/shop/update/<int:shop_id>', methods=['PUT'])
@jwt_required()
def updateShop(shop_id):
    data = request.get_json()
    try:
        hostname = os.environ.get('AUTH_SERVICE_HOST', 'localhost:5000')
        url= f"http://{hostname}/auth/verify"
        response = requests.get(url, headers=request.headers)

        if response.status_code >=  400:
            print(f"Error: {response.status_code} - {response.text}")
            return jsonify(response.json()), response.status_code

        user = response.json()
        if user.get('user_type') != "SUPER":
            return jsonify({"message": "only superuser can update shop"}),  401

        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"message": "Shop not found"}),  404

        shop.name = data.get('name', shop.name)
        shop.shopkeeper_id = data.get("shopkeeper_id", shop.shopkeeper_id)

        db.session.commit()

        updated_shop_dict = shop_schema.dump(shop)
        return jsonify(updated_shop_dict),  200

    except Exception as e:
        print(e)
        return jsonify({'message': 'Some error occurred'}),  401

@app.route('/shop', methods=['GET'])
def listShops():

    name = request.args.get('name')
    shopkeeper_id = request.args.get('shopkeeper_id')

    query = Shop.query

    if name:
        query = query.filter(Shop.name.like(f'%{name}%'))
    if shopkeeper_id:
        query = query.filter(Shop.shopkeeper_id == shopkeeper_id)

    shops = query.all()

    shop_schema = ShopSchema(many=True)
    shops_dict = shop_schema.dump(shops)

    return jsonify(shops_dict),  200


# Items

@app.route('/shop/items', methods=['GET'])
def listItems():
    # Query the database for all items
    items = Item.query.all()

    # Serialize the items to JSON
    item_schema = ItemSchema(many=True)
    items_dict = item_schema.dump(items)

    return jsonify(items_dict),   200

@app.route('/shop/<int:shop_id>/item/create', methods=['POST'])
@jwt_required()
def createItem(shop_id):
    data = request.get_json()
    try:
        # Get the current user's identity from the JWT
        user_id = get_jwt_identity()

        # Verify the user's role and shopkeeper_id
        hostname = os.environ.get('AUTH_SERVICE_HOST', 'localhost:5000')
        url= f"http://{hostname}/auth/verify"
        response = requests.get(url, headers=request.headers)

        if response.status_code >=  400:
            print(f"Error: {response.status_code} - {response.text}")
            return jsonify(response.json()), response.status_code

        user = response.json()
        if user.get('user_type') not in ["SUPER", "SHOPKEEPER"]:
            return jsonify({"message": "Only superuser or shopkeeper can create items"}),  401

        # Check if the shopkeeper_id matches the shopkeeper_id of the shop
        shop = Shop.query.filter_by(id=shop_id).first()
        if not shop or shop.id != shop_id:
            return jsonify({"message": "Shop not found"}),  404
        if user.get('user_type')=="SHOPKEEPER" and shop.shopkeeper_id!=user_id:
            return jsonify({"message": "You are not authorized to create items for this shop"}),  401

        # Create the new item
        new_item = Item(name=data.get('name'), item_type=data.get('item_type'), shop_id=shop_id)
        db.session.add(new_item)
        db.session.commit()

        # Serialize the new item to JSON
        item_schema = ItemSchema()
        new_item_dict = item_schema.dump(new_item)
        return jsonify(new_item_dict),  201

    except Exception as e:
        print(e)
        return jsonify({'message': 'Some error occurred'}),  401



@app.route('/shop/item/update/<int:item_id>', methods=['PUT'])
@jwt_required()
def updateItem(item_id):
    data = request.get_json()
    try:
        user_id = get_jwt_identity()

        hostname = os.environ.get('AUTH_SERVICE_HOST', 'localhost:5000')
        url= f"http://{hostname}/auth/verify"
        response = requests.get(url, headers=request.headers)

        if response.status_code >=   400:
            print(f"Error: {response.status_code} - {response.text}")
            return jsonify(response.json()), response.status_code

        user = response.json()

        # Check user type before attempting to update the item
        if user.get('user_type') not in ["SUPER", "SHOPKEEPER"]:
            return jsonify({"message": "Only superuser or shopkeeper can update items"}),   401

        # Find the item by ID
        item = Item.query.get(item_id)
        if not item:
            return jsonify({"message": "Item not found"}),   404

        # Check if the shopkeeper_id matches the shopkeeper_id of the shop
        shop = Shop.query.filter_by(id=item.shop_id).first()
        if not shop or shop.shopkeeper_id != user_id:
            return jsonify({"message": "You are not authorized to update items for this shop"}),   401

        # Update the item's fields
        item.name = data.get('name', item.name)
        item.item_type = data.get('item_type', item.item_type)
        # Update other fields as needed

        db.session.commit()

        # Serialize the updated item to JSON
        item_schema = ItemSchema()
        updated_item_dict = item_schema.dump(item)
        return jsonify(updated_item_dict),   200

    except Exception as e:
        print(e)
        return jsonify({'message': 'Some error occurred'}),   401
    

@app.route('/shop/verify', methods=['GET'])
@jwt_required()
def protected():
    
    print(request.headers.get('Authorization'))
    try:
        hostname = os.environ.get('AUTH_SERVICE_HOST', 'localhost:5000')
        url= f"http://{hostname}/auth/verify"
        response = requests.get(url, headers=request.headers)

        if response.status_code >=  400:
            print(f"Error: {response.status_code} - {response.text}")
            # Handle the error as needed
        else:
            return jsonify(response.json()),  200
    except:
        return jsonify({'message':'Something went wrong!'})  ,503
    
@app.route('/shop/test', methods=['GET'])
def test():
    
    # print(request.headers.get('Authorization'))
    try:
        # url = os.environ.get('AUTH_SERVICE_HOST', 'http://localhost:5000/auth/verify')
        # response = requests.get(url, headers=request.headers)

        # if response.status_code >=  400:
        #     print(f"Error: {response.status_code} - {response.text}")
        #     # Handle the error as needed
        # else:
        data={}
        data['AUTH_SERVICE_HOST']=os.environ.get('AUTH_SERVICE_HOST', 'http://localhost:5000/auth/verify')
        return jsonify(data),  200
    except:
        return jsonify({'message':'Something went wrong!'})  ,503