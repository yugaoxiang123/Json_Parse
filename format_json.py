import json

def format_json_file(input_file, output_file=None):
    # 如果没有指定输出文件，则覆盖原文件
    if output_file is None:
        output_file = input_file
    
    try:
        # 读取JSON文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 写入格式化后的JSON，使用4个空格缩进
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"JSON文件已成功格式化：{output_file}")
    except Exception as e:
        print(f"处理文件时发生错误：{str(e)}")

if __name__ == "__main__":
    # 处理文件
    format_json_file("WordData_GraduateStudent.json") 