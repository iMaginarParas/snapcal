from posthog import Posthog
import os
import logging

logger = logging.getLogger(__name__)

# Initialize PostHog
# PostHog internally handles batching and asynchronous processing
api_key = os.getenv("POSTHOG_API_KEY")
host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")

posthog = None
if api_key:
    posthog = Posthog(
        project_api_key=api_key,
        host=host
    )
else:
    logger.warning("POSTHOG_API_KEY not set. Analytics and Feature Flags are disabled.")

def track_event(user_id: str, event_name: str, properties: dict = None):
    """
    Captures a user event and sends it to PostHog.
    Safe to call even if PostHog is not configured.
    """
    if not posthog:
        return

    try:
        posthog.capture(
            distinct_id=str(user_id),
            event=event_name,
            properties=properties or {}
        )
    except Exception as e:
        logger.error(f"Failed to track PostHog event {event_name}: {str(e)}")

def identify_user(user_id: str, properties: dict):
    """
    Sets person properties for a user.
    """
    if not posthog:
        return

    try:
        posthog.identify(str(user_id), properties)
    except Exception as e:
        logger.error(f"Failed to identify user {user_id} in PostHog: {str(e)}")

def is_feature_enabled(user_id: str, flag_name: str, default_value: bool = False) -> bool:
    """
    Checks if a feature flag is enabled for a specific user.
    Returns default_value if PostHog is unavailable or an error occurs.
    """
    if not posthog:
        return default_value

    try:
        return posthog.feature_enabled(
            flag_name,
            str(user_id),
            # In-memory evaluation is faster but might require local identities
            # PostHog handles this internally
        )
    except Exception as e:
        logger.error(f"Error checking feature flag {flag_name} for user {user_id}: {str(e)}")
        return default_value
