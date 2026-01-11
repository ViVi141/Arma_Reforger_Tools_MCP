"""关系索引系统 - 用于查找 API 之间的关系"""

import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

from src.utils.helpers import get_data_path, load_json


class RelationshipIndex:
    """API 关系索引"""

    def __init__(self, api_source: str = "arma_reforger"):
        """
        初始化关系索引
        
        Args:
            api_source: API 来源
        """
        self.api_source = api_source
        self.data_path = get_data_path()
        self.api_data: Optional[Dict[str, Any]] = None
        self._inheritance_map: Dict[str, List[str]] = {}
        self._usage_map: Dict[str, Set[str]] = {}

    def load_data(self, json_file: Optional[str] = None) -> None:
        """
        加载 API 数据
        
        Args:
            json_file: JSON 文件名，如果为 None 则使用默认文件名
        """
        if json_file is None:
            json_file = f"{self.api_source}_api.json"
        
        self.api_data = load_json(json_file)
        if not self.api_data:
            raise FileNotFoundError(f"无法加载 API 数据: {json_file}")
        
        self._build_relationship_maps()

    def _build_relationship_maps(self) -> None:
        """构建关系映射"""
        if not self.api_data:
            return
        
        classes = self.api_data.get("classes", {})
        
        # 构建继承关系映射
        for class_name, class_data in classes.items():
            inheritance = class_data.get("inheritance", {})
            parent = inheritance.get("parent")
            ancestors = inheritance.get("ancestors", [])
            
            if parent:
                if parent not in self._inheritance_map:
                    self._inheritance_map[parent] = []
                self._inheritance_map[parent].append(class_name)
            
            for ancestor in ancestors:
                if ancestor not in self._inheritance_map:
                    self._inheritance_map[ancestor] = []
                self._inheritance_map[ancestor].append(class_name)
        
        # 构建使用关系映射（方法返回类型、参数类型等）
        for class_name, class_data in classes.items():
            if class_name not in self._usage_map:
                self._usage_map[class_name] = set()
            
            # 检查方法
            for method in class_data.get("methods", []):
                # 返回类型
                return_type = method.get("return_type", "")
                if return_type:
                    self._add_usage_relationship(class_name, return_type)
                
                # 参数类型
                for param in method.get("parameters", []):
                    param_type = param.get("type", "")
                    if param_type:
                        self._add_usage_relationship(class_name, param_type)

    def _add_usage_relationship(self, from_class: str, to_type: str) -> None:
        """添加使用关系"""
        # 清理类型字符串，提取类名
        to_type = to_type.strip()
        # 移除常见的前缀和后缀
        to_type = to_type.replace("proto external", "").strip()
        to_type = to_type.replace("array<", "").replace(">", "").strip()
        to_type = to_type.split()[0] if to_type.split() else ""
        
        if to_type and to_type != from_class:
            if to_type not in self._usage_map:
                self._usage_map[to_type] = set()
            self._usage_map[to_type].add(from_class)

    def find_related_apis(
        self,
        api_name: str,
        relation_type: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        查找相关的 API
        
        Args:
            api_name: API 名称
            relation_type: 关系类型 (inheritance/usage/similar/all)
            
        Returns:
            相关 API 列表
        """
        if not self.api_data:
            return []
        
        related = []
        
        if relation_type in ["inheritance", "all"]:
            # 查找继承关系
            # 子类
            children = self._inheritance_map.get(api_name, [])
            for child in children:
                related.append({
                    "name": child,
                    "relation": "child_class",
                    "api_source": self.api_source
                })
            
            # 父类和祖先
            class_data = self.api_data.get("classes", {}).get(api_name)
            if class_data:
                inheritance = class_data.get("inheritance", {})
                parent = inheritance.get("parent")
                if parent:
                    related.append({
                        "name": parent,
                        "relation": "parent_class",
                        "api_source": self.api_source
                    })
                for ancestor in inheritance.get("ancestors", []):
                    related.append({
                        "name": ancestor,
                        "relation": "ancestor_class",
                        "api_source": self.api_source
                    })
        
        if relation_type in ["usage", "all"]:
            # 查找使用关系
            users = self._usage_map.get(api_name, set())
            for user in users:
                related.append({
                    "name": user,
                    "relation": "used_by",
                    "api_source": self.api_source
                })
            
            # 查找被使用的类
            for class_name, used_classes in self._usage_map.items():
                if api_name in used_classes:
                    related.append({
                        "name": class_name,
                        "relation": "uses",
                        "api_source": self.api_source
                    })
        
        # 去重
        seen = set()
        unique_related = []
        for item in related:
            key = (item["name"], item["relation"])
            if key not in seen:
                seen.add(key)
                unique_related.append(item)
        
        return unique_related
