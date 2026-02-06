from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard, name="index"),
    path("demo/", views.demo_dashboard, name="demo"),
    path("conversations/", views.conversations_list, name="conversations"),
    path(
        "conversations/<uuid:conversation_id>/",
        views.conversation_detail,
        name="conversation_detail",
    ),
    path("upload/", views.documents_upload, name="upload"),
    path("settings/", views.settings_page, name="settings"),
    path("config/", views.dashboard_config, name="config"),
    
    # API Configuration Check (for debugging)
    path("api/config-check/", views.api_config_check, name="api_config_check"),
    
    # Chat widget (public access for embedding)
    path("chat-widget/", views.chat_widget, name="chat_widget"),
]