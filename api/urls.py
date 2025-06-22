from yaml import Token
from api import views as api_views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # 登录接口：使用自定义视图（MyTokenObtainPairView），返回 access 和 refresh Token
    # 请求方式：POST，常用于用户登录
    path('user/token/', api_views.MyTokenObtainPairView.as_view()),

    # Token 刷新接口：使用 SimpleJWT 内置视图，提交 refresh token 获取新的 access token
    # 请求方式：POST，参数格式为 {"refresh": "<your_refresh_token>"}
    path("user/token/refresh/", TokenRefreshView.as_view()),

    # 注册接口：使用自定义视图（RegisterView），创建新用户
    # 请求方式：POST，参数包含用户名、邮箱、密码等信息
    path("user/register/", api_views.RegisterView.as_view()),

    path("user/password-reset/<email>/",api_views.PasswordResetEmailVerifyAPIView.as_view()),
    path("user/password-change/",api_views.PasswordChangeAPIView.as_view())

]

