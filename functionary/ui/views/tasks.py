import csv

from django.core.exceptions import BadRequest
from django.shortcuts import render
from django_htmx import http

from core.models import Task

from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)

FINISHED_STATUS = ["COMPLETE", "ERROR"]


def _detect_csv(result):
    """Attempt to determine if the provided result is a valid CSV"""
    try:
        csv.Sniffer().sniff(result, delimiters=",")
    except Exception:
        return False

    return True


def _format_csv_table(result: str) -> dict:
    """Convert a string of CSV into a format suitable for table rendering"""
    csv_data = csv.reader(result.splitlines())
    formatted_result = {
        "headers": next(csv_data),
        "data": [row for row in csv_data],
    }

    return formatted_result


def _format_json_table(result: list) -> dict:
    """Convert a JSON list into a format suitable for table rendering"""
    headers = [key for key in result[0].keys()]
    res_data = []

    for row in result:
        r = []
        for key in headers:
            r.append(row[key])
        res_data.append(r)

    return {"headers": headers, "data": res_data}


def _format_table(result):
    """Convert a result to a table friendly format

    This will take in a "string" or "json" result and return
    the headers and a list of rows for the data. A result_type of
    string is assumed to be csv formatted data - a csv reader
    parses the data into the resulting header and data.

    A result type of json should be of the following format:
    [
        {"prop1":"value1", "prop2":"value2"},
        {"prop1":"value3", "prop2":"value4"}
    ]
    The headers are derived from the keys of the first entry in the list.
    """
    if type(result) is str:
        return _format_csv_table(result)
    elif type(result) is list and len(result) > 0:
        return _format_json_table(result)
    else:
        raise ValueError("Unable to convert result to table")


def _show_output_selector(result):
    """Determines if the output format selector should be rendered"""
    result_type = type(result)

    if result_type is list:
        # Don't offer a table for a list of non-dictionaries
        show_selector = result and type(result[0]) is dict
    elif result_type is str:
        show_selector = _detect_csv(result)
    else:
        show_selector = False

    return show_selector


def _format_result(result, format):
    """Inspects the task result and formats the result data for in the desired format
    as appropriate"""
    output_format = "table"
    formatted_result = None
    format_error = None

    match format:
        case "display_raw":
            if type(result) in [list, dict]:
                output_format = "json"
            else:
                output_format = "string"
        case "display_table":
            try:
                formatted_result = _format_table(result)
            except Exception:
                format_error = "Result data is unsuitable for table output"
        case _:
            raise BadRequest("Invalid display format")

    return output_format, format_error, formatted_result


def _get_result_context(context, format):
    task = context["task"]

    completed = task.status in FINISHED_STATUS

    output_format, format_error, formatted_result = _format_result(task.result, format)

    context["completed"] = completed
    context["show_output_selector"] = (
        False if not completed else _show_output_selector(task.result)
    )
    context["format_error"] = format_error
    context["formatted_result"] = formatted_result
    context["output_format"] = output_format
    return context


class TaskListView(PermissionedEnvironmentListView):
    model = Task
    order_by_fields = ["-created_at"]
    queryset = Task.objects.select_related("environment", "function", "creator").all()


class TaskDetailView(PermissionedEnvironmentDetailView):
    model = Task

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "environment", "creator", "function", "taskresult", "environment__team"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        format = (
            self.request.GET["output"]
            if "output" in self.request.GET
            else "display_raw"
        )

        return _get_result_context(context, format)


class TaskResultsView(PermissionedEnvironmentDetailView):
    """View for retrieving the results in a given output format."""

    model = Task

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "environment",
                "taskresult",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return _get_result_context(context, self.request.GET["output"])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()

        if "poll" in request.GET:
            return http.retarget(
                render(request, "core/task_detail.html", context=context),
                "#task_detail",
            )

        return render(request, "partials/task_result.html", context=context)
