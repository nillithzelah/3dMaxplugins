import requests
import json
import time
from urllib.parse import quote

def scrape_xiaohongshu_api(keyword, cookies_str):
    """
    Scrape Xiaohongshu using their actual API endpoint
    """
    
    # Parse cookies string into dictionary
    cookies = {}
    for cookie in cookies_str.split('; '):
        if '=' in cookie:
            name, value = cookie.split('=', 1)
            cookies[name] = value
    
    # URL encode the keyword
    encoded_keyword = quote(keyword)
    
    # API endpoint
    url = f'https://edith.xiaohongshu.com/api/sns/web/v1/search/filter?keyword={encoded_keyword}&search_id=2f27s2tdgp5dgjwtk9e0w'
    
    # Headers from the curl request
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-US,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',
        'origin': 'https://www.xiaohongshu.com',
        'priority': 'u=1, i',
        'referer': 'https://www.xiaohongshu.com/',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-b3-traceid': 'b3e58deaf98d8f25',
        'x-s': 'XYS_2UQhPsHCH0c1PjhlHjIj2erjwjQhyoPTqBPT49pjHjIj2eHjwjQgynEDJ74AHjIj2ePjwjQTJdPIP/ZlgMrU4SmH4BpIcAz3nomsLLL9/fbiwozQyfPMaDVEJn+HwoZMwrYop9SCpBl/LeZ3afEDJMmHP7m9JfH7t9+YJMmDPFMipBEapFRyyBS92/p0PaT+GnR8aoziznYEyLh7+rELnnTB/dY1cdSf8rTNn0cAzezkanTj/om0ydScNFLF+A+j/nG7GFh9PDlhzLYY+ruMyDl+wpYY+BrEJBSEpBThc7pC8Lkb2bz3HjIj2ecjwjHjKc==',
        'x-s-common': '2UQAPsHC+aIjqArjwjHjNsQhPsHCH0rjNsQhPaHCH0c1PjhlHjIj2eHjwjQgynEDJ74AHjIj2ePjwjQhyoPTqBPT49pjHjIj2ecjwjHFN0qUN0ZjNsQh+aHCH0rEweZhP0DEG/Hh4ncUqBEMqfTY+0Qj2/bkyA+jPfL94Bb9q/pCPB+f+/ZIPeZAPeWU+ecjNsQh+jHCHjHVHdW7H0ijHjIj2eWjwjQQPAYUaBzdq9k6qB4Q4fpA8b878FSet9RQzLlTcSiM8/+n4MYP8F8LagY/P9Ql4FpUzfpS2BcI8nT1GFbC/L88JdbFyrSiafprwLMra7pFLDDAa7+8J7QgabmFz7Qjp0mcwp4fanD68p40+fp8qgzELLbILrDA+9p3JpH9LLI3+LSk+d+DJfpSL98lnLYl49IUqgcMc0mrcDShtMmozBD6qM8FyFSh8o+h4g4U+obFyLSi4nbQz/+SPFlnPrDApSzQcA4SPopFJeQmzBMA/o8Szb+NqM+c4ApQzg8Ayp8FaDRl4AYs4g4fLomD8pzBpFRQ2ezLanSM+Skc47Qc4gcMag8VGLlj87PAqgzhagYSqAbn4FYQy7pTanTQ2npx87+8NM4L89L78p+l4BL6ze4AzB+IygmS8Bp8qDzFaLP98Lzn4AQQzLEAL7bFJBEVL7pwyS8Fag868nTl4e+0n04ApfuF8FSbL7SQyrpltASrpLS92dDFa/YOanS0+Mkc4F8Q4fSb+Bu6qFzP8oP9Lo4naLP78p+D+7+DcnIFaLp98/bIGFMFpd4panSDqA+AN7+hnDESyp8FGf+p8np8pd49ag8+/Bbm+9pfqg4MqrQwqFzM4MmQ2BlFagYyL9RM4FRdpd4Iq9pk/DT88o+xyDTApdbF/FSkJ7+g8ApSy9lb4LSk/d+/qo8SyFQgLDSkafpLLoz+anSUy7zM4BMF4gz9agYS8pzc4r8Qz/8SP7pFzDS389pDqgzaGM8FcgQc4bpQPMQ9ag8nqgzDapQt/o8SPMmFaLSbzBbQyAmSngp7Lpkjz/zPPemAyfpzPFSkqSklqgzNJ7b7PFDA/9phqgzxLLIM8nS0cgPAqBY7anYmqA+s/7PA4gzA/7bFnLS3a7+h4gzoaLPIq98dGd+Q2e+AnppdqM+c4FEQ4DkS+dbF4dz8ao+Q2bH6anVIqAb0J9pLcf4SySDA8n8n4M8QyMQBa/++nrll4okQ4f+aHjIj2eDjwjFlPALhwecAw/GVHdWlPsHCPsIj2erlH0ijJfRUJnbVHdF=',
        'x-t': '1752484678999',
        'x-xray-traceid': 'cc041d069f102e712c61d269ad01cd2c'
    }
    
    try:
        print(f"正在搜索关键词: {keyword}")
        print(f"API URL: {url}")
        
        response = requests.get(url, headers=headers, cookies=cookies)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功获取数据!")
            
            # 保存原始响应到文件
            with open('xiaohongshu_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("原始响应已保存到 xiaohongshu_response.json")
            
            # 解析数据
            parse_and_save_results(data, keyword)
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")

def parse_and_save_results(data, keyword):
    """
    解析API响应数据并保存结果
    """
    try:
        # 根据实际API响应结构解析数据
        # 这里需要根据实际的JSON结构来调整
        results = []
        
        # 尝试不同的可能的数据结构
        if 'data' in data:
            items = data['data'].get('items', [])
        elif 'items' in data:
            items = data['items']
        else:
            items = []
        
        print(f"找到 {len(items)} 个结果")
        
        for i, item in enumerate(items):
            try:
                # 提取用户信息
                user_info = {
                    'index': i + 1,
                    'user_id': item.get('user', {}).get('userId', ''),
                    'nickname': item.get('user', {}).get('nickname', ''),
                    'desc': item.get('user', {}).get('desc', ''),
                    'follows': item.get('user', {}).get('follows', 0),
                    'fans': item.get('user', {}).get('fans', 0),
                    'likes': item.get('user', {}).get('likes', 0),
                    'level': item.get('user', {}).get('level', {}).get('name', ''),
                    'avatar': item.get('user', {}).get('avatar', ''),
                }
                
                # 提取笔记信息
                note_info = {
                    'note_id': item.get('id', ''),
                    'title': item.get('title', ''),
                    'desc': item.get('desc', ''),
                    'likes': item.get('likes', 0),
                    'comments': item.get('comments', 0),
                    'shares': item.get('shares', 0),
                    'collects': item.get('collects', 0),
                    'time': item.get('time', ''),
                    'type': item.get('type', ''),
                }
                
                result = {**user_info, **note_info}
                results.append(result)
                
                print(f"{i+1}. {user_info['nickname']} - {note_info['title'][:50]}...")
                
            except Exception as e:
                print(f"解析第 {i+1} 个结果时出错: {str(e)}")
                continue
        
        # 保存解析后的结果
        if results:
            filename = f'xiaohongshu_{keyword}_{int(time.time())}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"✅ 解析结果已保存到 {filename}")
            
            # 保存为CSV格式
            csv_filename = f'xiaohongshu_{keyword}_{int(time.time())}.csv'
            save_as_csv(results, csv_filename)
            print(f"✅ CSV格式结果已保存到 {csv_filename}")
        else:
            print("❌ 没有找到有效的结果数据")
            
    except Exception as e:
        print(f"❌ 解析数据时出错: {str(e)}")

def save_as_csv(results, filename):
    """
    将结果保存为CSV格式
    """
    import csv
    
    if not results:
        return
    
    fieldnames = results[0].keys()
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    # 使用你提供的cookies
    cookies_str = 'abRequestId=d9399543-ed10-5209-a08e-42ca0c746de8; a1=19808299a28ud2pnurka62by1ik3b2e6tavq5z0cf50000308244; webId=51354e161ef20415042440bb922a69c2; gid=yjY8YJjDy09iyjY8YJjj00u8JY7fJUI7FT0KhSiJDvy3TA28qDJdK2888q8YJ448KD00JJjf; webBuild=4.72.0; acw_tc=0a4a9a7a17524836079662892e554b6e511aab61363c2722231d7d498c8b16; xsecappid=xhs-pc-web; unread={%22ub%22:%226874b1a600000000130130e8%22%2C%22ue%22:%226874c877000000000d027aca%22%2C%22uc%22:25}; websectiga=10f9a40ba454a07755a08f27ef8194c53637eba4551cf9751c009d9afb564467; sec_poison_id=7bb241c6-ade4-469a-8c85-85f969138c8a; loadts=1752484629075; web_session=040069b961b2b066d66b7783413a4ba65d3470'
    
    # 搜索关键词
    keyword = "AI建筑设计图"
    
    scrape_xiaohongshu_api(keyword, cookies_str) 