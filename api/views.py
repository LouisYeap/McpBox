import random

from django.shortcuts import render
from api import serializer as api_serializer  # 导入序列化器模块并重命名为 api_serializer
from rest_framework_simplejwt.views import TokenObtainPairView  # 引入 JWT 登录视图
from rest_framework import generics,status # 引入泛型视图（如 CreateAPIView）
from rest_framework.permissions import AllowAny  # 引入权限类，允许所有用户访问
from rest_framework_simplejwt.tokens import RefreshToken
from userauths.models import User  # 导入用户模型
from rest_framework.response import Response

# Create your views here.  # 这是 Django 自动生成的注释，表示你可以在这里写视图逻辑


class MyTokenObtainPairView(TokenObtainPairView):
    """
    自定义 JWT 登录视图。
    继承自 SimpleJWT 提供的 TokenObtainPairView。
    """
    # 告诉 DRF 使用自定义的序列化器（MyTokenObtainPairSerializer）
    # 这个序列化器中添加了额外字段（如用户名、邮箱、全名等）
    serializer_class = api_serializer.MyTokenObtainPairSerializer

    # 注释说明：
    # serializer_class 不是 Python 关键字，但在 DRF 中是“约定俗成”的属性名，
    # 视图调用时会自动使用这里指定的序列化器来处理请求数据（如登录验证）。


class RegisterView(generics.CreateAPIView):
    """
    用户注册视图
    使用 DRF 提供的通用类视图 CreateAPIView 来处理 POST 注册请求
    """

    # 该视图操作的查询集（CreateAPIView 不直接使用，但是 DRF 的要求）
    queryset = User.objects.all()

    # 设置权限为允许任意用户访问（即使未登录也能注册）
    permission_classes = (AllowAny,)

    # 指定用于处理请求的序列化器
    serializer_class = api_serializer.RegisterSerializer



def generate_random_otp(length =7):
    otp = ''.join(str(random.randint(0,9)) for _ in range(length))
    return otp


class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView):
    """
    密码重置邮件验证视图
    """
    permission_classes = [AllowAny]
    serializer_class =  api_serializer.UserSerializer
    def get_object(self):
        email = self.kwargs['email']
        user = User.objects.filter(email=email).first()
        if user:
            uuidb64 = user.pk
            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh.access_token)

            user.refresh_token = refresh_token
            user.otp = generate_random_otp()
            user.save()
            link = f'http://localhost:5173/create-new-password/?otp{user.otp}&uuidb64 = {uuidb64}&=refresh_token{refresh_token}'

            print("link =======",link)

        return user



class PasswordChangeAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = api_serializer.UserSerializer
    def create(self, request, *args, **kwargs):
        otp = request.data['otp']
        uuidb64 = request.data['uuidb64']
        password = request.data['password']
        user = User.objects.get(id=uuidb64,otp =otp)
        if user:
            user.set_password(password)
            user.otp = ""
            user.save()
            return Response({"message":"Password Changed Successfully"},status=status.HTTP_201_CREATED)
        else:
            return Response({"message":"Invalid OTP"},status=status.HTTP_400_BAD_REQUEST)

