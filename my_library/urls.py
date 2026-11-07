from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'My Library — Administração'
admin.site.site_title = 'My Library'
admin.site.index_title = 'Painel'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('account.urls')),
    path('home/', include('core.urls')),
]
