def get_instructions() -> str:
    """
    Returns the instructions for the root agent.

    This function provides a brief description of the root agent's purpose and capabilities.

    Returns:
        str: Instructions for the root agent.
    """
    return (
        "You are a search agent. Your task is to search the web for high-quality visual references "
        "that match the user's fashion concept. Use the available tool to gather relevant runway images, editorials, "
        "lookbooks, or fashion blog content that could inspire a moodboard based on the user's query."
    )