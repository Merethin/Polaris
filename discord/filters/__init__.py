import re
from typing import Self, Optional

class FilterComponent:
    def create(*args) -> Optional[Self]:
        return None
    
    def matches(self, *args) -> bool:
        return False

    def explain(self, type: str) -> str:
        return "Matches none"
    
class FilterError(Exception):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)
    
class Filter:
    def __init__(self, types: list[type], regex: re.Pattern) -> None:
        self.filters: list[FilterComponent] = []
        self.types = types
        self.regex = regex
        
    def parse(self, filter: str) -> Self:
        for statement in filter.split():
            match = self.regex.match(statement)
            if match is not None:
                for filterType in self.types:
                    component = filterType.create(*match.groups())
                    if component is not None:
                        self.filters.append(component)
                        break
                else:
                    raise FilterError(f"`{statement}` is not a valid filter statement!")
            else:
                raise FilterError(f"`{statement}` is not a valid filter statement!")
        return self
            
    def matches(self, *args) -> bool:
        for filter in self.filters:
            if filter.matches(*args):
                return True
        
        return False
            
    def explain(self) -> str:
        explanation = ""
        for filter in self.filters:
            explanation += filter.explain() + "\n"
        return explanation