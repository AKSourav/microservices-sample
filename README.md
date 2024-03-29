# microservices-sample


## Setup and Installation

```sh
git clone https://github.com/AKSourav/microservices-sample.git
cd microservices-sample

minikube  start --driver=docker
minikube addons enable ingress

kubectl apply -f ./API/gateway.yaml -f ./auth/deployment.yaml -f ./shop/deployment.yaml

minikube tunnel
```

## Auth service
This is a simple authentication service that provides user registration and login functionality. It uses JWT for token.

### User Types
Shopkeeper: "SHOPKEEPER"
HEAD: "SUPER"
Customer: "CUSTOMER"

### Register
POST http://kubernetes.docker.internal/auth/register
#### Input (JSON)
{
    "username":String,
    "password":String,
    "user_type":String, 
    "shop_id": Integer // if user_type is SHOPKEEPER
}
#### Output
{
    "message":"user created"
}

### Login
POST http://kubernetes.docker.internal/auth/login
#### Input (JSON)
{
    "username":String,
    "password":String,
}
#### Output
{
    "access-token":String
}

### Verify
GET http://kubernetes.docker.internal/auth/verify
#### Header
Authorization: "Bearer  {access-token}"
#### Output
{
    "id": Integer
    "username":String,
    "user_type":String,
    "role": Object
}

## Shop service
This is a simple shop service that provides shop and items listing, creations, updates

### Create shop
POST http://kubernetes.docker.internal/shop/create
#### Header
Authorization: "Bearer  {access-token}"
#### Input (JSON)
{
    "name": String,
    "shopkeeper_id": Integer
}
#### Output
{
    "id": Integer
    "name": String,
    "shopkeeper_id": Integer
}

### Update Shop
PUT http://kubernetes.docker.internal/shop/update/<int:shop_id>
#### Header
Authorization: "Bearer  {access-token}"
#### Input (JSON)
{
    "name": String(optional),
    "shopkeeper_id": Integer (optional)
}
#### Output
{
    "id": Integer,
    "name": String,
    "shopkeeper_id": Integer
}

### Get  all shops
GET http://kubernetes.docker.internal/shop
#### Query Params
name: String
shopkeeper_id: Integer
#### Output
[
    {
        "id": Integer,
        "name": String,
        "shopkeeper_id": Integer
    }
]

### Create Item
POST http://kubernetes.docker.internal/shop/<int:shop_id>/item/create
#### Header
Authorization: "Bearer  {access-token}"
#### Input
{
    "name": String,
    "item_type": String
}
#### Output
{
    "id": Integer,
    "name": String,
    "item_type": String
}

### Update Item
GET http://kubernetes.docker.internal/shop/item/update/<int:item_id>
#### Header
Authorization: "Bearer  {access-token}"
#### Input
{
    "name": String (optional),
    "item_type": String (optional)
}
#### Output
{
    "id": Integer,
    "name": String,
    "item_type": String
}

### List Item
GET http://kubernetes.docker.internal/shop/items
#### Output
[
    {
    "id": Integer,
    "name": String,
    "item_type": String
    }
]