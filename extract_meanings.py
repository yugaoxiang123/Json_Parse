import json
import re

def extract_chinese_meanings():
    # 读取JSON文件
    with open('WordData.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取所有的中文释义并去重
    meanings = set(data.values())
    
    # 清理字符串：去除括号及其内容，去除空格和顿号
    cleaned_meanings = set()
    for meaning in meanings:
        # 去除各种括号及其内容
        cleaned = re.sub(r'[\[【].+?[\]】]', '', meaning)
        # 去除空格和顿号
        cleaned = cleaned.replace(' ', '').replace('、', '').replace('…', '')
        cleaned_meanings.add(cleaned)
    
    # 将处理后的释义写入txt文件
    with open('chinese_meanings.txt', 'w', encoding='utf-8') as f:
        f.write(''.join(cleaned_meanings))
    
    print(f"已提取 {len(cleaned_meanings)} 个不重复的中文释义到 chinese_meanings.txt")

if __name__ == "__main__":
    extract_chinese_meanings() 