from django.db.models import Count
from .models import Stall, Order


class StallRecommendationEngine:
    """
    Intelligent stall ranking engine.

    Ranking factors:
    1. Current load
    2. Stall capacity
    3. Average preparation time
    4. Stall rating
    5. Break type weight
    """

    ACTIVE_STATUSES = ["PENDING", "PREPARING"]

    def __init__(self, timeslot):
        self.timeslot = timeslot
        self.stalls = Stall.objects.filter(is_active=True)

    # ------------------------------------------------------
    # Current Load
    # ------------------------------------------------------
    def get_current_load(self, stall):
        return Order.objects.filter(
            stall=stall,
            timeslot=self.timeslot,
            status__in=self.ACTIVE_STATUSES
        ).count()

    # ------------------------------------------------------
    # Estimated Wait Time
    # ------------------------------------------------------
    def estimate_wait_time(self, stall, current_load):
        if stall.max_orders_per_slot <= 0:
            return 0

        load_ratio = current_load / stall.max_orders_per_slot
        estimated_wait = load_ratio * stall.average_prep_time

        return round(estimated_wait, 2)

    # ------------------------------------------------------
    # Break Type Weight
    # ------------------------------------------------------
    def break_weight(self):
        if self.timeslot.break_type == "LUNCH":
            return 1.2
        elif self.timeslot.break_type == "SHORT":
            return 1.0
        return 0.8

    # ------------------------------------------------------
    # Score Calculation
    # ------------------------------------------------------
    def calculate_score(self, stall, current_load, estimated_wait):
        """
        Higher score = better stall
        """

        weight = self.break_weight()

        # Load normalization
        if stall.max_orders_per_slot > 0:
            load_factor = 1 - (current_load / stall.max_orders_per_slot)
            load_factor = max(load_factor, 0)  # avoid negative
        else:
            load_factor = 1

        # Wait normalization
        wait_factor = 1 / (1 + estimated_wait)

        # Rating normalization (scale 0-5 → 0-10)
        rating_factor = stall.rating * 2

        score = (
            rating_factor * 0.5 +
            load_factor * 10 * 0.3 +
            wait_factor * 10 * 0.2
        )

        return round(score * weight, 2)

    # ------------------------------------------------------
    # Generate Ranked Results
    # ------------------------------------------------------
    def generate_recommendations(self):
        results = []

        for stall in self.stalls:
            current_load = self.get_current_load(stall)
            estimated_wait = self.estimate_wait_time(stall, current_load)
            score = self.calculate_score(stall, current_load, estimated_wait)

            results.append({
                "stall": stall,
                "current_load": current_load,
                "estimated_wait": estimated_wait,
                "score": score
            })

        ranked = sorted(results, key=lambda x: x["score"], reverse=True)

        for index, item in enumerate(ranked, start=1):
            item["rank"] = index

        return ranked
