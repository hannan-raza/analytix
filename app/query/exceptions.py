class PipelineError(Exception):
    """Raised by any pipeline stage when it cannot continue.

    Attributes:
        message: Human-readable explanation safe to return to the client.
        stage:   Which stage failed — "intent" | "planner" | "executor" | "formatter"
    """

    def __init__(self, message: str, stage: str):
        super().__init__(message)
        self.message = message
        self.stage = stage
