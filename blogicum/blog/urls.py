from django.urls import path, include
from . import views

app_name = 'blog'

urlpatterns = [
    path("", views.index, name='index'),
    path("posts/<int:id>/", views.post_detail, name='post_detail'),
    path("category/<slug:category_slug>/", views.category_posts,
         name='category_posts'),
    path('profile/<str:username>/', views.ProfileView.as_view(),
         name='profile'),
    path('posts/create/', views.create_post, name='create_post'),
    path('edit_profile/', views.edit_profile,
         name='edit_profile'),
    path('posts/<int:pk>/comment', views.add_comment, name='add_comment'),
    path('posts/<int:pk>/edit_comment/<int:comment_id>/',
         views.edit_comment, name='edit_comment'),
    path('posts/<int:pk>/delete_comment/<int:comment_id>/',
         views.delete_comment, name='delete_comment'),
    path('posts/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post')
]
