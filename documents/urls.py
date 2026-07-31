from django.urls import path
from documents import views

urlpatterns = [
    path('documents/', views.DocumentListCreateView.as_view(), name='document-list-create'),
    path('documents/<uuid:document_id>/', views.DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<uuid:document_id>/sessions/', views.SessionCreateView.as_view(), name='session-create'),
    path('sessions/<uuid:session_id>/', views.SessionDetailView.as_view(), name='session-detail'),
    path('sessions/<uuid:session_id>/messages/', views.MessageCreateView.as_view(), name='message-create'),
]
