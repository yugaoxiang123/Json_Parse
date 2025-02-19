import json
import os
import re
from pathlib import Path
from translate import Translator
from tqdm import tqdm
import time
import hashlib
import random
import requests

class TranslatePokemonData:
    def __init__(self):
        # 为每种类型创建独立的缓存文件
        self.ability_cache_file = Path('translations/ability_desc_translations.json')
        self.item_cache_file = Path('translations/item_desc_translations.json')
        self.move_cache_file = Path('translations/move_desc_translations.json')
        
        # 加载所有缓存
        self.ability_cache = self._load_cache(self.ability_cache_file)
        self.item_cache = self._load_cache(self.item_cache_file)
        self.move_cache = self._load_cache(self.move_cache_file)
        
        self.appid = "20250220002279116"
        self.secretKey = "_OIVFx7OiUGpBPkoJG50"
        
    # 确保输出目录存在
    def ensure_output_dir(self):
        os.makedirs('output', exist_ok=True)

    # 读取翻译文件
    def load_translations(self,file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}

    # 读取需要翻译的文件
    def load_data(self,file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []
        
    def _load_cache(self, cache_file: Path) -> dict:
        """加载翻译缓存"""
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding='utf-8'))
        return {}

    def _save_cache(self, cache: dict, cache_file: Path):
        """保存翻译缓存"""
        cache_file.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    # 保存翻译后的文件
    def save_data(self,data, file_path):
        output_path = os.path.join('output', os.path.basename(file_path))
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Successfully saved: {output_path}")
        except Exception as e:
            print(f"Error saving {output_path}: {e}")

    def translate_desc(self, desc: str, name: str, cache: dict, cache_file: Path) -> str:
        """使用百度翻译API的描述翻译方法"""
        try:
            if name in cache:
                return cache[name], False
                
            # 生成签名
            salt = random.randint(32768, 65536)
            sign = hashlib.md5((self.appid + desc + str(salt) + self.secretKey).encode()).hexdigest()
            
            # 构造请求
            url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
            params = {
                'q': desc,
                'from': 'en',
                'to': 'zh',
                'appid': self.appid,
                'salt': salt,
                'sign': sign
            }
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if 'error_code' in result:
                if result['error_code'] == '54003':
                    print("QPS限制，等待1秒...")
                    time.sleep(1)  # QPS限制，等待更长时间
                    return self.translate_desc(desc, name, cache, cache_file)  # 重试
                elif result['error_code'] == '54004':
                    print("免费额度已用完，请明天再试或升级账户")
                    return desc, False
                else:
                    print(f"Translation failed: {result}")
                    return desc, False
                    
            if 'trans_result' in result:
                desc_chinese = result['trans_result'][0]['dst']
                time.sleep(1.5)  # 增加等待时间到1.5秒
                return desc_chinese, True

            return desc, False
            # return '-99', False
        except Exception as e:
            print(f"Translation error: {e}")
            return desc, False

    def translate_ability_desc(self,desc,name)->str:
        return self.translate_desc(desc, name, self.ability_cache, self.ability_cache_file)

    def clean_existing_translations(self, data: list, fields_to_clean: list) -> list:
        """清理已存在的翻译字段"""
        for item in data:
            for field in fields_to_clean:
                if field in item:
                    del item[field]
        return data

    def translate_abilities(self):
        print("Translating abilities...")
        ability_trans = self.load_translations('translations/ability_translations.json')
        abilities = self.load_data('json_data/gen4_abilities.json')
        
        # 清理已有的翻译
        abilities = self.clean_existing_translations(abilities, ['chineseDesc', 'chineseShortDesc'])
        
        for ability in tqdm(abilities, desc="Processing abilities"):
            keys = list(ability.keys())
            name_index = keys.index('name')
            desc_index = keys.index('desc') if 'desc' in keys else -1
            print(desc_index)
            shortDesc_index = keys.index('shortDesc') if 'shortDesc' in keys else -1
            if ability['name'] in ability_trans:
                # 在name字段后插入chineseName
                new_ability = {}
                for i, (key, value) in enumerate(ability.items()):
                    new_ability[key] = value
                    if i == name_index:
                        new_ability['chineseName'] = ability_trans[ability['name']]
                    if i == desc_index and 'desc' in ability:
                        print(ability['desc'])
                        is_translate = False
                        new_ability['chineseDesc'], is_translate = self.translate_desc(
                            ability['desc'], 
                            ability['name']+'_desc',
                            self.ability_cache,
                            self.ability_cache_file
                        )
                        if is_translate:
                            self.ability_cache[ability['name']+'_desc'] = new_ability['chineseDesc']
                            self._save_cache(self.ability_cache, self.ability_cache_file)
                    if i == shortDesc_index and 'shortDesc' in ability:
                        is_translate = False
                        new_ability['chineseShortDesc'],is_translate = self.translate_ability_desc(ability['shortDesc'],ability['name']+'_shortDesc')
                        if is_translate:
                            self.ability_cache[ability['name']+'_shortDesc'] = new_ability['chineseShortDesc']
                            self._save_cache(self.ability_cache, self.ability_cache_file)
                ability.clear()
                ability.update(new_ability)
        
        self.save_data(abilities, 'json_data/gen4_abilities.json')

    def translate_items(self):
        print("Translating items...")
        item_trans = self.load_translations('translations/item_translations.json')
        items = self.load_data('json_data/gen4_items.json')
        
        # 清理已有的翻译
        items = self.clean_existing_translations(items, ['chineseDesc', 'chineseShortDesc'])
        
        for item in tqdm(items, desc="Processing items"):
            keys = list(item.keys())
            name_index = keys.index('name')
            desc_index = keys.index('desc') if 'desc' in keys else -1
            shortDesc_index = keys.index('shortDesc') if 'shortDesc' in keys else -1
            
            if item['name'] in item_trans:
                new_item = {}
                for i, (key, value) in enumerate(item.items()):
                    new_item[key] = value
                    if i == name_index:
                        new_item['chineseName'] = item_trans[item['name']]
                    if i == desc_index and 'desc' in item:
                        is_translate = False
                        new_item['chineseDesc'], is_translate = self.translate_desc(
                            item['desc'],
                            item['name']+'_desc',
                            self.item_cache,
                            self.item_cache_file
                        )
                        if is_translate:
                            self.item_cache[item['name']+'_desc'] = new_item['chineseDesc']
                            self._save_cache(self.item_cache, self.item_cache_file)
                    if i == shortDesc_index and 'shortDesc' in item:
                        is_translate = False
                        new_item['chineseShortDesc'],is_translate = self.translate_desc(
                            item['shortDesc'],
                            item['name']+'_shortDesc',
                            self.item_cache,
                            self.item_cache_file
                            )
                        if is_translate:
                            self.item_cache[item['name']+'_shortDesc'] = new_item['chineseShortDesc']
                            self._save_cache(self.item_cache, self.item_cache_file)
                item.clear()
                item.update(new_item)
        
        self.save_data(items, 'json_data/gen4_items.json')

    def translate_moves(self):
        print("Translating moves...")
        move_trans = self.load_translations('translations/move_translations.json')
        moves = self.load_data('json_data/gen4_moves.json')
        
        # 清理已有的翻译
        moves = self.clean_existing_translations(moves, ['chineseDesc', 'chineseShortDesc'])
        
        for move in tqdm(moves, desc="Processing moves"):
            keys = list(move.keys())
            name_index = keys.index('name')
            desc_index = keys.index('desc') if 'desc' in keys else -1
            shortDesc_index = keys.index('shortDesc') if 'shortDesc' in keys else -1
            
            if move['name'] in move_trans:
                new_move = {}
                for i, (key, value) in enumerate(move.items()):
                    new_move[key] = value
                    if i == name_index:
                        new_move['chineseName'] = move_trans[move['name']]
                    if i == desc_index and 'desc' in move:
                        is_translate = False
                        new_move['chineseDesc'], is_translate = self.translate_desc(
                            move['desc'],
                            move['name']+'_desc',
                            self.move_cache,
                            self.move_cache_file
                        )
                        if is_translate:
                            self.move_cache[move['name']+'_desc'] = new_move['chineseDesc']
                            self._save_cache(self.move_cache, self.move_cache_file)
                    if i == shortDesc_index and 'shortDesc' in move:
                        is_translate = False
                        new_move['chineseShortDesc'],is_translate = self.translate_desc(
                            move['shortDesc'],
                            move['name']+'_shortDesc',
                            self.move_cache,
                            self.move_cache_file
                            )
                        if is_translate:
                            self.move_cache[move['name']+'_shortDesc'] = new_move['chineseShortDesc']
                            self._save_cache(self.move_cache, self.move_cache_file)
                move.clear()
                move.update(new_move)
            
        self.save_data(moves, 'json_data/gen4_moves.json')

    def translate_pokemons(self):
        print("Translating pokemons...")
        pokemon_trans = self.load_translations('translations/pokemon_translation.json')
        type_trans = self.load_translations('translations/type_translations.json')
        ability_trans = self.load_translations('translations/ability_translations.json')
        skill_up_trans = self.load_translations('translations/pokemon_moves_up.json')
        pokemons = self.load_data('json_data/gen4_pokemons.json')
        
        for pokemon in tqdm(pokemons, desc="Processing pokemons"):
            # 获取各字段的位置
            keys = list(pokemon.keys())
            name_index = keys.index('name')
            types_index = keys.index('types') if 'types' in keys else -1
            abilities_index = keys.index('abilities') if 'abilities' in keys else -1
            
            # 创建新的pokemon字典
            new_pokemon = {}
            for i, (key, value) in enumerate(pokemon.items()):
                new_pokemon[key] = value
                
                # 在name后添加chineseName
                if i == name_index and pokemon['name'] in pokemon_trans:
                    new_pokemon['chineseName'] = pokemon_trans[pokemon['name']]
                
                # 在types后添加chineseTypes
                if i == types_index and 'types' in pokemon:
                    new_pokemon['chineseTypes'] = [type_trans.get(t, t) for t in pokemon['types']]
                
                # 在abilities后添加chineseAbilities
                if i == abilities_index and 'abilities' in pokemon:
                    translated_abilities = {}
                    for key, ability in pokemon['abilities'].items():
                        translated_abilities[key] = ability_trans.get(ability, ability)
                    new_pokemon['chineseAbilities'] = translated_abilities
            if pokemon['name'] in skill_up_trans:
                new_pokemon['SkillUp'] = skill_up_trans[pokemon['name']]
            pokemon.clear()
            pokemon.update(new_pokemon)
        
        self.save_data(pokemons, 'json_data/gen4_pokemons.json')

    def delete_part_pokemon_name(self):
        pokemons = self.load_data('output/gen4_pokemons.json')
        # 使用列表推导式来过滤，而不是在遍历时删除
        filtered_pokemons = []
        for pokemon in pokemons:
            if 'chineseName' in pokemon:
                name = pokemon['chineseName']
                if '(' in name or '（' in name:
                    name = name.replace('（', '(').replace('）', ')')
                    form = re.search(r'\((.*?)\)', name)
                    if form:
                        form_name = form.group(1)
                        if form_name != '超级':
                            print(f"将删除: {name}")
                            continue
            filtered_pokemons.append(pokemon)
        
        self.save_data(filtered_pokemons, 'output/gen4_pokemons.json')

    def main(self):
        print("Starting translation process...")
        self.ensure_output_dir()
        
        # 执行所有翻译
        # self.translate_abilities()
        self.translate_items()
        self.translate_moves()
        # self.translate_pokemons()
        # self.delete_part_pokemon_name()

        print("Translation completed!")

if __name__ == "__main__":
    translator = TranslatePokemonData()
    translator.main()