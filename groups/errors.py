from django.core.exceptions import PermissionDenied


class RuleError(Exception):
    """A request that breaks a product rule. The message is shown to the user."""


class NotAllowed(PermissionDenied):
    """The requester's role does not permit the action (HTTP 403)."""
