from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token,get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from Serializers import UserSchema,RoleSchema
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///users.db')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'abcd')

db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    user_type = db.Column(db.String(80), default="CUSTOMER")
    roles = db.relationship('Role', backref=db.backref('user', lazy=True))

    def __repr__(self):
        return '<User %r>' % self.username

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shop_id = db.Column(db.Integer, unique=True, nullable=False)

    def __repr__(self):
        return '<Role %r>' % self.name
    
# Initialize the database
with app.app_context():
    db.create_all()

user_schema=UserSchema()
role_schema=RoleSchema()


@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}),  400

    user = User.query.filter_by(username=data['username']).first()
    if user:
        return jsonify({'message': 'User already exists'}),  400

    new_user = User(username=data['username'], password=data['password'], user_type=data.get('user_type', "CUSTOMER"))
    db.session.add(new_user)

    if data.get('shop_id') and new_user.user_type == "SHOPKEEPER":
        try:
            # Start a new transaction
            db.session.begin_nested()

            new_role = Role(name="Shopkeeper", user_id=new_user.id, shop_id=data.get('shop_id'))
            db.session.add(new_role)
            db.session.commit()

            print("Role:", new_role)
        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()  # Rollback the transaction if an error occurs
            return jsonify({'message': 'Error occurred in role assignment'}),  400

    try:
        db.session.commit()  # Commit the outer transaction
    except SQLAlchemyError as e:
        print(e)
        return jsonify({'message': 'Error occurred while creating user'}),  400

    return jsonify({'message': 'User created'}),  201


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    print(data)
    user = User.query.filter_by(username=data['username']).first()
    print(user)
    if not user or user.password != data['password']:
        return jsonify({'message': 'Invalid credentials'}),   401

    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token),   200

@app.route('/auth/verify', methods=['GET'])
@jwt_required()
def protected():
    # Get the identity of the current user
    user_id = get_jwt_identity()

    # Assuming you have a User model with an id field
    user = User.query.get(user_id)
    userData= user_schema.dump(user)
    print("User:",userData)
    if user and user.user_type=="SHOPKEEPER":
        if len(user.roles)==0:
            return jsonify({'message': 'Role not found'}),  404
        role=role_schema.dump(user.roles[0])
        print("Here:",role)
        userData['role']=role
    if user:
        return jsonify(userData),  200
    else:
        return jsonify({'message': 'User not found'}),  404
    
@app.route('/auth/users', methods=['GET'])
def getAllUsers():
    try:
        query=User.query
        users = query.all()
        user_schema=UserSchema(many=True)
        user_dict = user_schema.dump(users)
        return jsonify(user_dict),  200
    except:
        return jsonify({"message":"ERRor"}),  400