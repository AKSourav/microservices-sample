from marshmallow import Schema, fields, post_dump

class UserSchema(Schema):
    id = fields.Int(dump_only=True)  # This field is read-only
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)  # This field is write-only
    user_type= fields.Str(required=True)

    # Optionally, you can add a method to serialize the user object
    @post_dump
    def remove_password(self, data, **kwargs):
        data.pop('password', None)
        return data
