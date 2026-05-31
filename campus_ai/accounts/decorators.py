from functools import wraps
from django.shortcuts import redirect
from accounts.models import User


def login_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user_id = request.session.get("user_id")

        if not user_id:
            return redirect("/")

        try:
            user = User.objects.get(user_id=user_id)

            if not user.is_active:
                request.session.flush()
                return redirect("/")

            request.current_user = user

        except User.DoesNotExist:
            request.session.flush()
            return redirect("/")

        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(*allowed_roles):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            user = getattr(request, "current_user", None)

            if not user:
                return redirect("/")

            if user.role not in allowed_roles:
                return redirect("/")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator