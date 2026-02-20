# Cluster 2

def ensure_event_loop() -> None:
    """Ensure there is a current asyncio event loop in this thread.
    Some libraries call asyncio.get_event_loop() during construction
    and expect a loop to be set.
    """
    try:
        asyncio.get_running_loop()
        return
    except RuntimeError:
        pass
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

# Node: get_running_loop
# Node: get_event_loop
# Node: new_event_loop
# Node: set_event_loop
def ensure_event_loop() -> None:
    """Ensure there is a current asyncio event loop in this thread.
    Some libraries call asyncio.get_event_loop() during construction
    and expect a loop to be set.
    """
    try:
        asyncio.get_running_loop()
        return
    except RuntimeError:
        pass
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

