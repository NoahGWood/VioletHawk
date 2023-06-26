from api import file, sub, comment, post

routes = [
    file.ROUTE,
    sub.ROUTE,
    comment.ROUTE,
    post.ROUTE
]


ROUTES = [

]
    
for route in routes:
    route["prefix"] = "/api" + route["prefix"]
    ROUTES.append(route)