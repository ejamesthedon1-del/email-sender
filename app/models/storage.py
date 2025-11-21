"""
Simple file-based storage for the platform
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

STORAGE_DIR = Path(__file__).parent.parent.parent / 'data'
STORAGE_DIR.mkdir(exist_ok=True)

class Storage:
    """Simple JSON-based storage"""
    
    @staticmethod
    def _get_file(entity_type: str) -> Path:
        return STORAGE_DIR / f"{entity_type}.json"
    
    @staticmethod
    def load(entity_type: str) -> List[Dict[str, Any]]:
        """Load entities from storage"""
        file_path = Storage._get_file(entity_type)
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    @staticmethod
    def save(entity_type: str, data: List[Dict[str, Any]]):
        """Save entities to storage"""
        file_path = Storage._get_file(entity_type)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    @staticmethod
    def add(entity_type: str, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new entity"""
        entities = Storage.load(entity_type)
        if 'id' not in entity:
            entity['id'] = str(len(entities) + 1)
        if 'created_at' not in entity:
            entity['created_at'] = datetime.now().isoformat()
        entity['updated_at'] = datetime.now().isoformat()
        entities.append(entity)
        Storage.save(entity_type, entities)
        return entity
    
    @staticmethod
    def update(entity_type: str, entity_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an entity"""
        entities = Storage.load(entity_type)
        for i, entity in enumerate(entities):
            if str(entity.get('id')) == str(entity_id):
                entities[i].update(updates)
                entities[i]['updated_at'] = datetime.now().isoformat()
                Storage.save(entity_type, entities)
                return entities[i]
        return None
    
    @staticmethod
    def delete(entity_type: str, entity_id: str) -> bool:
        """Delete an entity"""
        entities = Storage.load(entity_type)
        original_len = len(entities)
        entities = [e for e in entities if str(e.get('id')) != str(entity_id)]
        if len(entities) < original_len:
            Storage.save(entity_type, entities)
            return True
        return False
    
    @staticmethod
    def get(entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get a single entity by ID"""
        entities = Storage.load(entity_type)
        for entity in entities:
            if str(entity.get('id')) == str(entity_id):
                return entity
        return None

