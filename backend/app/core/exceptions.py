class ResourceNotFoundError(Exception):
    def __init__(self, resource: str, resource_id: object) -> None:
        super().__init__(f"{resource} {resource_id} was not found")
        self.resource = resource
        self.resource_id = resource_id


class ApplicationError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
