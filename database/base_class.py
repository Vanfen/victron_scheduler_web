from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr
import re

@as_declarative()
class Base:
    id: Any
    __name__: str

    # to generate tablename from classname
    @declared_attr
    def __tablename__(cls) -> str:
        split_name = re.findall('[A-Z][^A-Z]*', cls.__name__)
        table_name = ""
        for part in split_name:
            table_name += ("_" if table_name != "" else "") + part.lower()
        return table_name