import requests
import json
import time
from urllib.parse import quote

def scrape_xiaohongshu_simple(keyword):
    """
    简化版小红书爬虫，需要手动获取最新的cookies和headers
    """
    
    # 请从浏览器开发者工具中复制最新的cookies和headers
    # 1. 打开小红书网站
    # 2. 按F12打开开发者工具
    # 3. 在Network标签页中搜索关键词
    # 4. 找到对应的API请求，复制cookies和headers
    
    print("=" * 60)
    print("使用说明:")
    print("1. 打开浏览器访问 https://www.xiaohongshu.com")
    print("2. 登录你的账号")
    print("3. 搜索关键词: " + keyword)
    print("4. 按F12打开开发者工具")
    print("5. 在Network标签页中找到API请求")
    print("6. 复制cookies和headers到下面的变量中")
    print("=" * 60)
    
    # 请在这里填入从浏览器复制的cookies
    cookies_str = input("请粘贴cookies字符串: ").strip()
    
    # 解析cookies
    cookies = {}
    for cookie in cookies_str.split('; '):
        if '=' in cookie:
            name, value = cookie.split('=', 1)
            cookies[name] = value
    
    # API URL
    encoded_keyword = quote(keyword)
    url = f'https://edith.xiaohongshu.com/api/sns/web/v1/search/filter?keyword={encoded_keyword}'
    
    # 基础headers
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'origin': 'https://www.xiaohongshu.com',
        'referer': 'https://www.xiaohongshu.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
    }
    
    # 请在这里填入从浏览器复制的额外headers
    print("\n请从浏览器复制以下headers的值:")
    print("- x-s")
    print("- x-t") 
    print("- x-s-common")
    print("- x-b3-traceid")
    print("- x-xray-traceid")
    
    x_s = input("x-s: ").strip()
    x_t = input("x-t: ").strip()
    x_s_common = input("x-s-common: ").strip()
    x_b3_traceid = input("x-b3-traceid: ").strip()
    x_xray_traceid = input("x-xray-traceid: ").strip()
    
    if x_s:
        headers['x-s'] = x_s
    if x_t:
        headers['x-t'] = x_t
    if x_s_common:
        headers['x-s-common'] = x_s_common
    if x_b3_traceid:
        headers['x-b3-traceid'] = x_b3_traceid
    if x_xray_traceid:
        headers['x-xray-traceid'] = x_xray_traceid
    
    try:
        print(f"\n正在请求API...")
        print(f"URL: {url}")
        
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功获取数据!")
            
            # 保存原始响应
            with open('xiaohongshu_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("原始响应已保存到 xiaohongshu_response.json")
            
            # 解析数据
            parse_results(data, keyword)
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")

def parse_results(data, keyword):
    """
    解析API响应数据
    """
    try:
        print("\n正在解析数据...")
        
        # 打印数据结构以便调试
        print("数据结构:")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1000] + "...")
        
        results = []
        
        # 尝试不同的数据结构
        if 'data' in data and 'items' in data['data']:
            items = data['data']['items']
        elif 'items' in data:
            items = data['items']
        elif 'data' in data:
            items = data['data']
        else:
            items = []
        
        print(f"\n找到 {len(items)} 个结果")
        
        for i, item in enumerate(items):
            try:
                # 提取基本信息
                result = {
                    'index': i + 1,
                    'raw_data': item  # 保存原始数据
                }
                
                # 尝试提取用户信息
                if 'user' in item:
                    user = item['user']
                    result.update({
                        'user_id': user.get('userId', ''),
                        'nickname': user.get('nickname', ''),
                        'desc': user.get('desc', ''),
                        'follows': user.get('follows', 0),
                        'fans': user.get('fans', 0),
                        'likes': user.get('likes', 0),
                    })
                
                # 尝试提取笔记信息
                result.update({
                    'note_id': item.get('id', ''),
                    'title': item.get('title', ''),
                    'desc': item.get('desc', ''),
                    'likes': item.get('likes', 0),
                    'comments': item.get('comments', 0),
                    'shares': item.get('shares', 0),
                    'collects': item.get('collects', 0),
                })
                
                results.append(result)
                
                nickname = result.get('nickname', 'Unknown')
                title = result.get('title', 'No title')[:50]
                print(f"{i+1}. {nickname} - {title}...")
                
            except Exception as e:
                print(f"解析第 {i+1} 个结果时出错: {str(e)}")
                continue
        
        # 保存结果
        if results:
            timestamp = int(time.time())
            filename = f'xiaohongshu_{keyword}_{timestamp}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 结果已保存到 {filename}")
        else:
            print("\n❌ 没有找到有效的结果数据")
            
    except Exception as e:
        print(f"❌ 解析数据时出错: {str(e)}")

if __name__ == "__main__":
    keyword = "AI建筑设计图"
    scrape_xiaohongshu_simple(keyword) 