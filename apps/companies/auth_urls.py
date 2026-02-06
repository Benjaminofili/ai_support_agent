from django.urls import path
from django.contrib.auth.views import LogoutView

from . import auth_views

urlpatterns = [
    path('login/', auth_views.login_view, name='login'),
    path('signup/', auth_views.signup_view, name='signup'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
