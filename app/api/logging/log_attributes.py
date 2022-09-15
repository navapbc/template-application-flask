import flask

import api.util.string_utils as string_utils


def get_logging_context_attributes() -> dict:
    """
    Fetch any log attributes that should be attached
    to all logs for a given context (ie. during a request or ECS task)
    """
    attributes: dict = {}
    attributes |= get_request_attributes()
    attributes |= get_ecs_task_attributes()
    return attributes


def get_request_attributes() -> dict:
    request_attributes = {}
    if flask.has_request_context():
        request = flask.request

        # Request attributes
        request_attributes["request.method"] = string_utils.mask_pii(request.method)
        request_attributes["request.path"] = string_utils.mask_pii(request.path)
        request_attributes["request.url_rule"] = string_utils.mask_pii(request.url_rule)

        request_attributes["request_id"] = string_utils.mask_pii(
            request.headers.get("x-amzn-requestid", "")
        )

        user_attributes = flask.g.get("current_user_log_attributes")
        if user_attributes:
            request_attributes |= user_attributes

    return request_attributes


def get_ecs_task_attributes() -> dict:
    # TODO - If you want to attach
    # ECS task attributes, fetch them here
    return {}
