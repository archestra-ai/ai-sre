"""
Experimental Feature Module - AI SRE Demo

This module contains an experimental feature that has a bug.
The bug will cause the application to crash on startup when enabled.

To trigger this failure, set ENABLE_BUGGY_FEATURE=true in the ConfigMap.

The AI SRE agent should:
1. Detect the crash via Grafana alerts
2. Investigate logs to find the stack trace
3. Locate this file in the repository
4. Fix the bug by initializing the data variable properly
5. Push the fix to trigger ArgoCD deployment
"""


def process_experimental_data():
    """
    Process experimental data for the new analytics feature.
    
    This function is called on startup when ENABLE_BUGGY_FEATURE is enabled.
    
    BUG: The 'data' variable is not initialized, causing an AttributeError.
    FIX: Initialize 'data' with a proper string value, e.g., data = "initialized"
    """
    # TODO: Initialize this variable properly before using it
    data = None
    
    # This line will crash because 'data' is None
    return data.upper()
