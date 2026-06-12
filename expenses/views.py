from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings

from .models import Category, Expense
from .serializers import CategorySerializer, ExpenseSerializer, RegisterSerializer
from .currency import convert


# ── Auth endpoints ──

@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user_id": user.pk, "username": user.username},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {"error": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user_id": user.pk, "username": user.username})


# ── Categories ──

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def category_list(request):
    if request.method == "GET":
        categories = Category.objects.filter(user=request.user)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    serializer = CategorySerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ── Expenses ──

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def expense_list(request):
    if request.method == "GET":
        expenses = Expense.objects.filter(user=request.user)
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)
        serializer = ExpenseSerializer(expenses, many=True, context={"request": request})
        return Response(serializer.data)

    serializer = ExpenseSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def expense_detail(request, pk):
    try:
        expense = Expense.objects.get(pk=pk, user=request.user)
    except Expense.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = ExpenseSerializer(expense, context={"request": request})
        return Response(serializer.data)

    if request.method == "PUT":
        serializer = ExpenseSerializer(expense, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    expense.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Summary (with currency conversion) ──

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def expense_summary(request):
    base_currency = settings.BASE_CURRENCY
    expenses = Expense.objects.filter(user=request.user).select_related("category")

    category_totals = {}

    for expense in expenses:
        cat_name = expense.category.name
        converted_amount, rate, as_of = convert(
            float(expense.amount), expense.currency, base_currency
        )

        if cat_name not in category_totals:
            category_totals[cat_name] = {"total": 0.0, "as_of": as_of}
        category_totals[cat_name]["total"] += converted_amount

    result = [
        {"category": name, "total": round(data["total"], 2), "as_of": data["as_of"]}
        for name, data in sorted(category_totals.items())
    ]

    return Response({"base_currency": base_currency, "categories": result})