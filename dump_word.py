import json
import re
from gtts import gTTS
import os
from tqdm import tqdm
# 设置 Clash 代理地址 (使用 HTTP 代理)
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

class DumpWord:
    def __init__(self):
        self.input_file = "WordData_GraduateStudent.json"
        self.output_file = "WordData.json"

    def clean_translation(self, text):
        # 移除特殊字符和多余的空格
        text = re.sub(r'[<>/]', '', text)
        return text.strip()

    def get_first_meaning(self, translation_str):
        # 首先清理特殊字符
        translation_str = self.clean_translation(translation_str)
        
        # 如果清理后为空，直接返回空字符串
        if not translation_str:
            return ""
            
        # 处理所有可能的分隔符
        separators = ['；', ';', '，', ',']
        result = translation_str
        
        # 依次尝试每个分隔符
        for sep in separators:
            if sep in result:
                result = result.split(sep)[0]
        
        # 去除可能的空白字符
        result = result.strip()
        
        # 如果结果中还包含其他标点符号，进一步处理
        if '(' in result or '（' in result:
            result = result.split('(')[0].split('（')[0].strip()
        return result

    def sort_key(self, word):
        # 移除非字母数字的字符，转换为小写进行排序
        return re.sub(r'[^a-zA-Z0-9]', '', word).lower()

    def dump(self):
        with open(self.input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        try:
            new_data = {}
            for item in data:
                if 'translations' in item and item['translations']:
                    word = item['word']
                    translation = item['translations'][0]['translation']
                    first_meaning = self.get_first_meaning(translation)
                    # 只有在有意义的翻译时才添加
                    if first_meaning:
                        new_data[word] = first_meaning

            # 使用自定义排序键进行排序
            sorted_items = sorted(new_data.items(), key=lambda x: self.sort_key(x[0]))
            sorted_data = dict(sorted_items)
            
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(sorted_data, f, ensure_ascii=False, indent=4)
            print("处理完成！")
        except Exception as e:
            print(f"发生错误：{e}")

    def get_word_audio(self):
        # 确保输出目录存在
        if not os.path.exists('output'):
            os.makedirs('output')
        
        with open(self.output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    
        # 使用 tqdm 创建进度条
        for word, meaning in tqdm(data.items(), desc="下载单词音频"):
            # 检查音频文件是否已存在
            audio_file = f"output/{word}.mp3"
            if os.path.exists(audio_file):
                print(f"跳过 {word} - 音频文件已存在")
                continue
            
            print(f"当前单词: {word} - {meaning}")
            
            # 添加重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 改用美国服务器
                    tts = gTTS(text=word, lang='en', tld='co.uk')  # 改为美式发音
                    tts.save(audio_file)
                    break  # 如果成功就跳出重试循环
                except Exception as e:
                    print(f"下载 {word} 时出错 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt == max_retries - 1:  # 如果是最后一次尝试
                        print(f"警告: {word} 下载失败，跳过此单词")
                    else:
                        import time
                        time.sleep(2)  # 等待2秒后重试
                        continue
            
            # com	 美式英语
            # co.uk	 英式英语
            # com.au 澳大利亚英语
            # co.in	 印度英语

    def main(self):
        # self.dump()
        self.get_word_audio()

if __name__ == "__main__":
    word = DumpWord()
    word.main()
