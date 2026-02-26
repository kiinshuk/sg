from django.urls import path
from . import views

urlpatterns = [
    # Inbox
    path('', views.inbox, name='inbox'),

    # Direct messages
    path('dm/<str:username>/',          views.conversation,        name='conversation'),
    path('dm/<str:username>/send/',     views.send_message_ajax,   name='send_message_ajax'),
    path('dm/<str:username>/messages/', views.get_messages_ajax,   name='get_messages_ajax'),

    # Group chats
    path('group/create/',                        views.create_group,         name='create_group'),
    path('group/<int:group_id>/',                views.group_conversation,   name='group_conversation'),
    path('group/<int:group_id>/send/',           views.send_group_message,   name='send_group_message'),
    path('group/<int:group_id>/messages/',       views.get_group_messages,   name='get_group_messages'),
    path('group/<int:group_id>/add-member/',     views.add_group_member,     name='add_group_member'),
    path('group/<int:group_id>/remove-member/',  views.remove_group_member,  name='remove_group_member'),
    path('group/<int:group_id>/leave/',          views.leave_group,          name='leave_group'),
]
