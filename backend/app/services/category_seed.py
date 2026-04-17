"""
Category Seeding Service.

Seeds system categories and subcategories from the ML taxonomy.
"""

from __future__ import annotations

from typing import Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.categories import CATEGORY_HIERARCHY, CategoryType
from app.models.category import Category
from app.utils.helpers import generate_slug


async def seed_system_categories(db: AsyncSession) -> Dict[str, Category]:
    """
    Seed system categories and subcategories if none exist.

    Returns:
        Mapping of category name to created parent Category objects.
    """
    existing = await db.execute(
        select(func.count()).where(Category.is_system == True)  # noqa: E712
    )
    if (existing.scalar() or 0) > 0:
        return {}

    parents: Dict[str, Category] = {}

    for name, definition in CATEGORY_HIERARCHY.items():
        is_income = definition.category_type == CategoryType.INCOME
        parent = Category(
            name=definition.name,
            slug=generate_slug(definition.name),
            description=definition.description,
            icon=definition.icon,
            color=definition.color,
            is_system=True,
            is_income=is_income,
            keywords=list(definition.keywords),
            merchant_patterns=[],
            display_order=definition.priority,
        )
        db.add(parent)
        await db.flush()

        parents[name] = parent

        for subcategory in definition.subcategories:
            child = Category(
                name=subcategory,
                slug=generate_slug(subcategory),
                description=f"{definition.name} > {subcategory}",
                icon=definition.icon,
                color=definition.color,
                is_system=True,
                is_income=is_income,
                parent_id=parent.id,
                keywords=[subcategory.lower()],
                merchant_patterns=[],
                display_order=definition.priority,
            )
            db.add(child)

    await db.flush()
    return parents
