from .models import Followers, CodeVerify, VIA_PHONE, VIA_EMAIL
from rest_framework import serializers
from shared_app.utility import check_email_or_phone, send_email
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

class FollowersSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user_type = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(FollowersSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(required=False)

    class Meta:
        model = Followers
        fields = ('id', 'user_type', 'user_status')


        extra_kwargs = {
            'user_type' : {'read_only': True, 'required': False},
            'user_status': {'read_only': True, 'required': False}
        }

    def create(self, validated_data):
        user = super(FollowersSerializer, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
        user.save()
        return user

    def validate(self, data):
        super(FollowersSerializer, self).validate(data)
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        print(data)
        user_input = str(data.get('email_phone_number')).lower()
        input_type = check_email_or_phone(user_input)
        print(input_type)
        if input_type == "email":
            data = {
                "email": user_input,
                "auth_type": VIA_EMAIL
            }
        elif input_type == "phone":
            data = {
                "phone_number": user_input,
                "auth_type": VIA_PHONE
            }
        else:
            data = {
                'success': False,
                'message': "You must send email or phone number"
            }
            raise ValidationError(data)

        return data

    def validate_email_phone_number(self, value):
        value = value.lower()
        if value and Followers.objects.filter(email=value).exists():
            data = {
                "success": False,
                "message": "Bu email allaqachon ma'lumotlar bazasida bor"
            }
            raise ValidationError(data)
        elif value and Followers.objects.filter(phone_number=value).exists():
            data = {
                "success": False,
                "message": "Bu telefon raqami allaqachon ma'lumotlar bazasida bor"
            }
            raise ValidationError(data)

        return value

    def to_representation(self, instance):
        data = super(FollowersSerializer, self).to_representation(instance)
        data.update(instance.token())
        return data

