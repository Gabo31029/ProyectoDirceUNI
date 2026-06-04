from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Retrieves a single record by its primary key.
        """
        return db.get(self.model, id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Retrieves multiple records with optional pagination.
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> ModelType:
        """
        Creates a new record.
        """
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.flush()  # Flushes to generate default values / check constraints
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[Dict[str, Any], Any]
    ) -> ModelType:
        """
        Updates an existing record.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = {
                k: v for k, v in obj_in.__dict__.items()
                if not k.startswith("_")
            }

        columns = {c.name for c in self.model.__table__.columns}
        for field in update_data:
            if field in columns:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        db.flush()
        return db_obj

    def remove(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """
        Deletes a record.
        """
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.flush()
        return obj
