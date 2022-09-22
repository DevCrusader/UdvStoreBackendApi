from django.contrib import admin
from .models import Product, ProductItem, ProductPhoto


# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'state', 'have_size', )


@admin.register(ProductItem)
class ProductItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'size_list', 'state', )
    list_display_links = ('id', 'type')
    empty_value_display = "-empty-"


@admin.register(ProductPhoto)
class ProductPhotoAdmin(admin.ModelAdmin):
    pass
