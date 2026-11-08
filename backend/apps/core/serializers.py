from rest_framework.response import Response


def page_response(qs, request, serializer_cls, **context) -> Response:
    try:
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
    except (TypeError, ValueError):
        page, page_size = 1, 20
    count = qs.count()
    rows = qs[(page - 1) * page_size: page * page_size]
    data = serializer_cls(rows, many=True, context=context).data
    return Response({"count": count, "page": page, "page_size": page_size, "results": data})
