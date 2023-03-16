from django.urls import path

from goods.views import ProductViewSet, CategoryViewSet

urlpatterns = [
    path('products/', ProductViewSet.as_view({'get': 'list', 'post': 'create'}), name="product-list-create"),
    path('products/<int:pk>', ProductViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
         name="product-delete-update"),
    path('categories/', CategoryViewSet.as_view({'get': 'list', 'post': 'create'}),
         name="categories-list-create"),
    path('categories/<int:pk>',
         CategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
         name="categories-delete-update"),
]
