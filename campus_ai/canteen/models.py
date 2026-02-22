from django.db import models
from accounts.models import User


# =====================================================
# STALL MODEL
# =====================================================
class Stall(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=150)
    max_orders_per_slot = models.IntegerField()
    average_prep_time = models.IntegerField(help_text="In minutes")
    rating = models.FloatField(default=4.0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# =====================================================
# MENU ITEM MODEL
# =====================================================
class MenuItem(models.Model):
    stall = models.ForeignKey(
        Stall,
        on_delete=models.CASCADE,
        related_name="menu_items"
    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.CharField(max_length=50)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.stall.name})"


# =====================================================
# TIME SLOT MODEL
# =====================================================
class TimeSlot(models.Model):
    BREAK_TYPES = [
        ('SHORT', 'Short Break'),
        ('LUNCH', 'Lunch Break'),
        ('EVENING', 'Evening Break'),
    ]

    start_time = models.TimeField()
    end_time = models.TimeField()
    break_type = models.CharField(max_length=10, choices=BREAK_TYPES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.break_type} ({self.start_time} - {self.end_time})"


# =====================================================
# ORDER MODEL
# =====================================================
class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'}
    )
    stall = models.ForeignKey(Stall, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    order_time = models.DateTimeField(auto_now_add=True)

    estimated_wait_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Estimated wait time in minutes"
    )
    total_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    recommendation_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} - {self.student.user_id}"


# =====================================================
# ORDER ITEM MODEL
# =====================================================
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"
