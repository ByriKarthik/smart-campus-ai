from django.contrib import admin
from .models import Stall, MenuItem, TimeSlot, Order, OrderItem


# =====================================================
# STALL ADMIN
# =====================================================
@admin.register(Stall)
class StallAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "max_orders_per_slot", "rating", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


# =====================================================
# MENU ITEM ADMIN
# =====================================================
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "stall", "price", "is_available")
    list_filter = ("stall", "is_available")
    search_fields = ("name",)


# =====================================================
# TIME SLOT ADMIN
# =====================================================
@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ("break_type", "start_time", "end_time", "is_active")
    list_filter = ("break_type", "is_active")
    ordering = ("start_time",)


# =====================================================
# ORDER ITEM INLINE
# =====================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


# =====================================================
# ORDER ADMIN
# =====================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "stall",
        "timeslot",
        "status",
        "order_time",
        "estimated_wait_time",
        "recommendation_used",
    )
    list_filter = ("status", "stall", "timeslot", "recommendation_used")
    search_fields = ("student__user_id",)
    inlines = [OrderItemInline]
