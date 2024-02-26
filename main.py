import requests
import yaml
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Query
import re
from urllib.parse import urlparse, unquote

from starlette.responses import PlainTextResponse


class SubscriptionMixin:
    def __init__(self, mixin_file_path: str = 'mixin.yaml'):
        self.is_loaded = False
        self.mixin_data = {}
        try:
            self.mixin_data = self.load_mixin_data(mixin_file_path)
            self.is_loaded = True
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Failed to load mixin data: {e}")

    @staticmethod
    def load_mixin_data(file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            return data

    @staticmethod
    def filter_and_rename_proxy_groups(proxy_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for group in proxy_groups:
            # 检查name键是否存在，并且值为"代理"、"proxy"或"Proxy"
            if group.get('name') in ['代理', 'proxy', 'Proxy']:
                # 重命名为"Selection"
                group['name'] = 'Selection'
                # 仅保留该元素，删除其余元素
                return [group]
        return []

    def inject_mixin(self, original_data: str) -> str:
        if not self.is_loaded:
            raise RuntimeError("Mixin data was not loaded successfully, cannot inject mixin.")

        # 解析原始订阅数据
        original_yaml = yaml.safe_load(original_data)

        # 查找并处理proxy-groups
        proxy_groups = original_yaml.get('proxy-groups', [])
        filtered_proxy_groups = self.filter_and_rename_proxy_groups(proxy_groups)

        # 如果有满足条件的proxy-group，则替换原来的列表
        if filtered_proxy_groups:
            original_yaml['proxy-groups'] = filtered_proxy_groups

        # 清空rules键
        original_yaml.pop('rules', None)

        # 混合其他键
        for key, value in self.mixin_data.items():
            if key in original_yaml and isinstance(original_yaml[key], list) and isinstance(value, list):
                # 合并列表
                original_yaml[key].extend(x for x in value if x not in original_yaml[key])
            else:
                # 设置或更新键值
                original_yaml[key] = value

        # 将合并后的数据转换回yaml格式的字符串
        converted_data = yaml.dump(original_yaml, allow_unicode=True)
        return converted_data


app = FastAPI()
subscription_mixin = SubscriptionMixin()

# 定义一个URL正则表达式
url_regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
    r'\[?[A-F0-9]*:[A-F0-9:]+]?)'  # ...or ipv6
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def is_valid_url(url: str) -> bool:
    # 使用urllib.parse来解析URL
    parsed = urlparse(url)
    # 检查scheme和netloc是否存在
    return bool(parsed.scheme) and bool(parsed.netloc) and re.match(url_regex, url)


@app.get("/convert", response_class=PlainTextResponse)
async def convert(subscription_url: str = Query(..., alias="subscription_url")):
    # 解码URL
    subscription_url = unquote(subscription_url)

    # 使用is_valid_url函数来验证URL
    if not is_valid_url(subscription_url):
        raise HTTPException(status_code=400, detail="Invalid subscription URL")

    # 向原始订阅链接发送请求获取内容
    try:
        response = requests.get(subscription_url)
        response.raise_for_status()  # 确保响应状态码是200
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching subscription: {e}")

    original_data = response.text

    # 进行yaml注入和转换
    try:
        converted_data = subscription_mixin.inject_mixin(original_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting subscription: {e}")

    # 返回转换后的结果
    return converted_data


if __name__ == "__main__":
    with open(r'test.yaml', 'r', encoding='utf-8') as file:
        data = file.read()
        result = subscription_mixin.inject_mixin(data)

    with open(r'new_text.yaml', 'w', encoding='utf-8') as file:
        file.write(result)
