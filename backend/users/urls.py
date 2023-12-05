from django.urls import include, path
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path(
        'users/set_password/',
        BaseUserViewSet.as_view({'post': 'set_password'})
    ),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken'))
]
