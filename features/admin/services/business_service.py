"""Admin feature business-service bridge.

This keeps the first feature migration low-risk by exposing the existing
service implementation through the new feature-owned import path.
"""

try:
    from medic.services.business_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.business_service import *  # noqa: F403
