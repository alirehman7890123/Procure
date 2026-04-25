import warnings

from medic.utilities.session_service import get_active_session_id


def get_current_session(self=None):
    """
    Backward-compatible wrapper.
    Legacy callers pass self; it is ignored.
    """
    warnings.warn(
        "get_current_session is deprecated. Use utilities.session_service.get_active_session_id instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    _ = self
    return get_active_session_id(strict=False)