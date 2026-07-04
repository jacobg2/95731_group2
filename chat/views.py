import json

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import QuestionForm
from .services import AssistantError, ask_question


def index(request: HttpRequest):
    """Chat form: GET renders the form, POST submits a question."""
    answer = None
    error = None
    form = QuestionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            answer = ask_question(form.cleaned_data["question"])
        except AssistantError as exc:
            error = str(exc)

    return render(
        request,
        "chat/index.html",
        {"form": form, "answer": answer, "error": error},
    )


# CSRF is exempted so external clients (curl, scripts, graders) can call the
# JSON API without first fetching a token. The endpoint is stateless and
# performs no privileged action on behalf of a session.
@csrf_exempt
@require_POST
def api_ask(request: HttpRequest) -> JsonResponse:
    """JSON API: POST {"question": "..."} -> {"answer": "..."}."""
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Request body must be valid JSON."}, status=400)

    question = str(payload.get("question", "")).strip()
    if not question:
        return JsonResponse(
            {"error": 'Missing "question" field in JSON body.'}, status=400
        )

    try:
        answer = ask_question(question)
    except AssistantError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({"question": question, "answer": answer})
