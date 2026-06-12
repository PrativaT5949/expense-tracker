from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Expense


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Expense
        fields = ["id", "title", "amount","currency","category", "category_name", "date", "notes"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def validate_currency(self, value):
        return value.upper()

    def validate_category(self, value):
        request = self.context.get("request")
        if request and value.user != request.user:
            raise serializers.ValidationError("Category not found.")
        return value