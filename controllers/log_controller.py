from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.config import ChangeLogs, User, Role, Permission, UsersAndRoles, RolesAndPermissions
from schemas.log_schemas import ChangeLogResponse
from core.security import require_permission, get_current_user
from core.database import get_db
from datetime import datetime
import json
import ast
import re
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/logs", tags=["logs"])

def parse_value(value: str):
    """
    Парсит значение из строки, поддерживая разные форматы.
    """
    if not value:
        return {}
    
    try:
        # Пробуем сначала как JSON
        return json.loads(value)
    except json.JSONDecodeError:
        processed_value = value
        
        # Всегда пытаемся предварительно обработать строку для datetime объектов
        if "datetime.datetime" in value:
            # Упрощенное регулярное выражение для datetime.datetime: захватываем все содержимое скобок.
            datetime_pattern = r"datetime\.datetime\(([^)]*)\)"
            
            def replace_datetime(match):
                # match.group(1) будет содержать всю строку внутри скобок, например "2025, 6, 4, 15, 28, 12, 710095"
                args_str = match.group(1)
                # Разделяем аргументы и преобразуем их в int
                args = [int(arg.strip()) for arg in args_str.split(',')]
                
                # Убеждаемся, что у нас достаточно аргументов для datetime
                if len(args) < 3:
                    raise ValueError("Недостаточно аргументов для datetime.datetime")
                
                year, month, day = args[0], args[1], args[2]
                hour = args[3] if len(args) > 3 else 0
                minute = args[4] if len(args) > 4 else 0
                second = args[5] if len(args) > 5 else 0
                microsecond = args[6] if len(args) > 6 else 0
                
                dt_obj = datetime(year, month, day, hour, minute, second, microsecond)
                return f"'{dt_obj.isoformat()}'"
            
            processed_value = re.sub(datetime_pattern, replace_datetime, value)
        
        try:
            return ast.literal_eval(processed_value)
        except (SyntaxError, ValueError) as e:
            # Если после всех попыток это все еще не является литералом, выбрасываем ошибку
            raise ValueError(f"Не удалось распарсить значение как Python literal или JSON после предварительной обработки datetime: {value}. Ошибка: {e}")

def prepare_datetime_values(data):
    """
    Подготавливает значения datetime, удаляя информацию о часовом поясе и преобразуя строки в datetime объекты.
    """
    if not isinstance(data, dict):
        return data
    
    for key, value in data.items():
        if isinstance(value, str):
            try:
                # Попытка преобразовать строку в datetime, если она в ISO формате
                data[key] = datetime.fromisoformat(value)
            except ValueError:
                pass # Оставляем как строку, если не ISO формат
        elif isinstance(value, datetime):
            data[key] = value.replace(tzinfo=None)
        elif isinstance(value, dict):
            data[key] = prepare_datetime_values(value) # Рекурсивно обрабатываем вложенные словари
    return data

def apply_changes_to_entity(entity, old_values, db):
    """
    Применяет изменения к сущности и связанным объектам
    """
    # Обновляем основные поля сущности
    for key, value in old_values.items():
        # Теперь 'updated_at' не исключается, если это поле может быть откачено.
        # 'id' и 'created_at' по-прежнему исключаются.
        if hasattr(entity, key) and key not in ['id', 'created_at']:
            setattr(entity, key, value)
    
    # Обрабатываем специальные случаи для разных типов сущностей
    if isinstance(entity, User):
        # Обновляем связи с ролями
        if 'roles' in old_values:
            # Удаляем все текущие связи
            db.query(UsersAndRoles).filter(
                UsersAndRoles.user_id == entity.id,
                UsersAndRoles.is_deleted == False
            ).update({"is_deleted": True, "deleted_at": datetime.now()})
            
            # Создаем новые связи
            for role_code in old_values['roles']:
                role = db.query(Role).filter(Role.code == role_code).first()
                if role:
                    new_link = UsersAndRoles(
                        user_id=entity.id,
                        role_id=role.id,
                        created_at=datetime.now()
                    )
                    db.add(new_link)
    
    elif isinstance(entity, Role):
        # Обновляем связи с разрешениями
        if 'permissions' in old_values:
            # Удаляем все текущие связи
            db.query(RolesAndPermissions).filter(
                RolesAndPermissions.role_id == entity.id,
                RolesAndPermissions.is_deleted == False
            ).update({"is_deleted": True, "deleted_at": datetime.now()})
            
            # Создаем новые связи
            for perm_code in old_values['permissions']:
                perm = db.query(Permission).filter(Permission.code == perm_code).first()
                if perm:
                    new_link = RolesAndPermissions(
                        role_id=entity.id,
                        permission_id=perm.id,
                        created_at=datetime.now()
                    )
                    db.add(new_link)

    # Flush changes to the database before committing, to ensure they are tracked.
    db.flush()

@router.get("/{log_id}", response_model=ChangeLogResponse,
           dependencies=[Depends(require_permission("get_log")), Depends(get_current_user)])
def get_log_by_id(
    log_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить лог по его ID
    """
    try:
        log = db.query(ChangeLogs).filter(ChangeLogs.id == log_id).first()
        if not log:
            raise HTTPException(
                status_code=404,
                detail="Лог не найден"
            )
        return log
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении лога: {str(e)}"
        )

@router.post("/{log_id}/rollback", response_model=ChangeLogResponse,
            dependencies=[Depends(require_permission("rollback_log")), Depends(get_current_user)])
def rollback_log(
    log_id: int,
    db: Session = Depends(get_db)
):
    """
    Откатить изменения по ID лога
    """
    try:
        log = db.query(ChangeLogs).filter(ChangeLogs.id == log_id).first()
        if not log:
            raise HTTPException(
                status_code=404,
                detail="Лог не найден"
            )

        # Определяем тип сущности и получаем соответствующую модель
        entity_model = None
        if log.entity_type == "User":
            entity_model = User
        elif log.entity_type == "Role":
            entity_model = Role
        elif log.entity_type == "Permission":
            entity_model = Permission
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый тип сущности: {log.entity_type}"
            )

        # Получаем сущность
        entity = db.query(entity_model).filter(entity_model.id == log.entity_id).first()
        if not entity:
            raise HTTPException(
                status_code=404,
                detail=f"Сущность {log.entity_type} с ID {log.entity_id} не найдена"
            )

        # Парсим старое значение и подготавливаем datetime объекты
        old_values = parse_value(log.old_value)
        if not old_values:
            raise HTTPException(
                status_code=400,
                detail="Не удалось получить предыдущие значения для отката"
            )
        old_values = prepare_datetime_values(old_values)

        # Применяем изменения к сущности и связанным объектам
        apply_changes_to_entity(entity, old_values, db)

        # Убедимся, что изменения сущности отслеживаются сессией
        db.add(entity)

        # Создаем новый лог для отката
        rollback_log = ChangeLogs(
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            action="Rollback",
            old_value=log.new_value,
            new_value=log.old_value,
            created_at=datetime.now()
        )

        db.add(rollback_log)
        db.commit()
        db.refresh(rollback_log)
        db.refresh(entity)

        return rollback_log

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка базы данных: нарушение уникального ограничения или целостности данных. Детали: {str(e)}"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка обработки данных лога: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при откате лога: {str(e)}"
        ) 