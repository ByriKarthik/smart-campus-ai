from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from decimal import Decimal

from accounts.models import User
from .models import MenuItem, Order, OrderItem, Stall, TimeSlot
from .services import StallRecommendationEngine


def test_recommendation(request):
    """
    Display stall recommendations for selected timeslot.
    """

    timeslots = TimeSlot.objects.filter(is_active=True)
    selected_timeslot = None
    recommendations = []

    timeslot_id = request.GET.get("timeslot")

    if timeslot_id:
        selected_timeslot = get_object_or_404(TimeSlot, id=timeslot_id)

        engine = StallRecommendationEngine(selected_timeslot)
        recommendations = engine.generate_recommendations()

    return render(request, "canteen/test_recommendation.html", {
        "timeslots": timeslots,
        "selected_timeslot": selected_timeslot,
        "recommendations": recommendations,
    })


def _get_session_user(request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or role not in {"STUDENT", "FACULTY"}:
        return None, redirect("login")

    user = User.objects.filter(
        user_id=user_id,
        role=role,
        is_active=True,
    ).first()

    if not user:
        return None, redirect("login")

    return user, None


def place_order(request):
    current_user, response = _get_session_user(request)
    if response:
        return response

    timeslots = TimeSlot.objects.filter(is_active=True).order_by("start_time")

    selected_timeslot = None
    selected_stall = None
    recommendations = []
    recommended_stall_ids = set()
    recommendation_lookup = {}
    menu_items = MenuItem.objects.none()
    menu_rows = []
    selected_quantities_map = {}
    order_preview_total = Decimal("0.00")

    selected_timeslot_id = request.POST.get("timeslot") if request.method == "POST" else request.GET.get("timeslot")
    selected_stall_id = request.POST.get("stall") if request.method == "POST" else request.GET.get("stall")

    if selected_timeslot_id:
        selected_timeslot = get_object_or_404(TimeSlot, id=selected_timeslot_id, is_active=True)
        engine = StallRecommendationEngine(selected_timeslot)
        recommendations = engine.generate_recommendations()
        recommended_stall_ids = {item["stall"].id for item in recommendations}
        recommendation_lookup = {item["stall"].id: item for item in recommendations}

    if selected_stall_id:
        selected_stall = get_object_or_404(Stall, id=selected_stall_id, is_active=True)
        menu_items = MenuItem.objects.filter(stall=selected_stall, is_available=True).order_by("name")

    if request.method == "POST":
        if not selected_timeslot or not selected_stall:
            messages.error(request, "Please select timeslot and stall before placing order.")
        else:
            selected_quantities = []
            for item in menu_items:
                quantity_raw = request.POST.get(f"qty_{item.id}", "0").strip()
                try:
                    quantity = int(quantity_raw)
                except ValueError:
                    quantity = 0

                if quantity > 0:
                    selected_quantities.append((item, quantity))
                selected_quantities_map[item.id] = quantity

            if not selected_quantities:
                messages.error(request, "Please select at least one item.")
            else:
                total_price = sum((item.price * quantity for item, quantity in selected_quantities), Decimal("0.00"))
                with transaction.atomic():
                    order = Order.objects.create(
                        student=current_user,
                        stall=selected_stall,
                        timeslot=selected_timeslot,
                        total_price=total_price,
                        recommendation_used=selected_stall.id in recommended_stall_ids,
                    )

                    OrderItem.objects.bulk_create(
                        [
                            OrderItem(order=order, menu_item=item, quantity=quantity)
                            for item, quantity in selected_quantities
                        ]
                    )

                    engine = StallRecommendationEngine(selected_timeslot)
                    current_load = engine.get_current_load(selected_stall)
                    estimated_wait = engine.estimate_wait_time(selected_stall, current_load)
                    order.estimated_wait_time = estimated_wait
                    order.save(update_fields=["estimated_wait_time"])

                messages.success(request, f"Order #{order.id} placed successfully.")
                return redirect("my_orders")

    if selected_stall and menu_items:
        for item in menu_items:
            value = request.POST.get(f"qty_{item.id}", "0") if request.method == "POST" else "0"
            try:
                qty = max(int(value), 0)
            except ValueError:
                qty = 0
            selected_quantities_map[item.id] = qty
            subtotal = item.price * qty
            order_preview_total += subtotal
            menu_rows.append(
                {
                    "item": item,
                    "qty": qty,
                    "subtotal": subtotal,
                }
            )

    return render(
        request,
        "canteen/place_order.html",
        {
            "timeslots": timeslots,
            "selected_timeslot": selected_timeslot,
            "selected_stall": selected_stall,
            "recommendations": recommendations,
            "menu_items": menu_items,
            "menu_rows": menu_rows,
            "selected_quantities_map": selected_quantities_map,
            "order_preview_total": order_preview_total,
            "selected_recommendation": recommendation_lookup.get(selected_stall.id) if selected_stall else None,
        },
    )


def my_orders(request):
    current_user, response = _get_session_user(request)
    if response:
        return response

    orders = (
        Order.objects.filter(student=current_user)
        .select_related("stall", "timeslot")
        .prefetch_related("items__menu_item")
        .order_by("-order_time")
    )

    return render(
        request,
        "canteen/my_orders.html",
        {
            "orders": orders,
        },
    )
