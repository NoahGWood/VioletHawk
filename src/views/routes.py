from views import auth, home, sub, user

ROUTES = [
    auth.router,
    home.router,
    sub.ROUTE,
    user.ROUTE
]
