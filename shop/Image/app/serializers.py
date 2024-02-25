from marshmallow import Schema, fields

class ItemSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    item_type = fields.Str(required=True, default="icecream")
    shop_id = fields.Int(required=True)

class VariantSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    variant_type = fields.Str(required=True, default="flavour")
    item_id = fields.Int(required=True)

class ShopSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, unique=True)
    shopkeeper_id = fields.Int(required=True, unique=True)
    items = fields.Nested(ItemSchema, many=True)
