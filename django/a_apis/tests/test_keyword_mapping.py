#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
키워드 매핑 테스트

ProductService.suggest_categories 메서드의 키워드 매핑을 확인하는 단순 스크립트
"""
from a_apis.service.products import ProductService

# 테스트할 키워드 목록
test_keywords = ["칼", "차", "책", "쌀", "개", "밥", "컴", "아이폰", "고양이", "식칼"]

print("=== 키워드별 카테고리 매핑 테스트 ===")
print("키워드: 카테고리 ID (카테고리 이름)")
print("-" * 40)

for keyword in test_keywords:
    result = ProductService.suggest_categories(keyword)
    categories = []

    if result["success"] and result["data"]:
        for cat in result["data"]:
            categories.append(f"{cat.get('id')} ({cat.get('name', 'Unknown')})")

        categories_str = ", ".join(categories)
    else:
        categories_str = "매핑 없음"

    print(f"{keyword}: {categories_str}")

print("-" * 40)
print("✓ 테스트 완료")
