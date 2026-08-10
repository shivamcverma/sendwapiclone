
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers



User = get_user_model()


class RegisterSerializer(serializers.Serializer):

    school_name = serializers.CharField(
        max_length=255
    )

    email = serializers.EmailField()

    phone = serializers.CharField(
        max_length=15
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    def validate_email(self, value):
        value = value.lower().strip()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def validate_phone(self, value):
        value = value.strip()

        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )

        return value

    @transaction.atomic
    def create(self, validated_data):

        school_name = validated_data["school_name"]
        email = validated_data["email"]
        phone = validated_data["phone"]
        password = validated_data["password"]

        user = User.objects.create_user(
            email=email,
            password=password,
            school_name=school_name,
            phone=phone,
        )
        # ---------------------------------

        self._seed_default_templates()

        return user

    def _seed_default_templates(self):

        templates = [
            {
                "name": "fee_payment",
                "body": (
                    "Dear Parent,\n\n"
                    "Fee payment of ₹{{1}} for {{2}} "
                    "has been received successfully.\n\n"
                    "Receipt No: {{3}}\n\n"
                    "Thank you."
                ),
                "category": "UTILITY",
            },
            {
                "name": "student_absent",
                "body": (
                    "Dear Parent,\n\n"
                    "Your ward {{1}} was absent from school "
                    "on {{2}}.\n\n"
                    "Regards,\n"
                    "School Administration"
                ),
                "category": "UTILITY",
            },
            {
                "name": "admission_confirmation",
                "body": (
                    "Dear Parent,\n\n"
                    "Admission of {{1}} in {{2}} for session "
                    "{{3}} has been successfully completed."
                ),
                "category": "UTILITY",
            },
        ]

    

class LoginSerializer(serializers.Serializer):

    email_or_phone = serializers.CharField()

    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):

        email_or_phone = attrs.get(
            "email_or_phone"
        )

        password = attrs.get(
            "password"
        )

        # -------------------------------
        # Find user by email
        # -------------------------------

        user = User.objects.filter(
            email=email_or_phone.lower().strip()
        ).first()

        # -------------------------------
        # If not found, find by phone
        # -------------------------------

        if not user:
            user = User.objects.filter(
                phone=email_or_phone.strip()
            ).first()

        # -------------------------------
        # User not found
        # -------------------------------

        if not user:
            raise serializers.ValidationError(
                "Invalid email/phone or password."
            )

        # -------------------------------
        # Check password
        # -------------------------------

        if not user.check_password(password):
            raise serializers.ValidationError(
                "Invalid email/phone or password."
            )

        # -------------------------------
        # Check active
        # -------------------------------

        if not user.is_active:
            raise serializers.ValidationError(
                "Your account is inactive."
            )

        attrs["user"] = user

        return attrs


class UserSerializer(serializers.ModelSerializer):

    class Meta:

        model = User

        fields = (
            "id",
            "school_name",
            "email",
            "phone",
            "role",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "role",
            "created_at",
            "updated_at",
        )
