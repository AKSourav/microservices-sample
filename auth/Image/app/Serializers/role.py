from marshmallow import Schema, fields,post_dump

class RoleSchema(Schema):
    id = fields.Int(dump_only=True)  # This field is read-only
    name = fields.Str(required=True)
    user_id = fields.Int(required=True)
    shop_id = fields.Int(required=True)

    # Optionally, you can add a method to serialize the role object
    @post_dump
    def remove_user_id(self, data, **kwargs):
        data.pop('user_id', None)
        return data
