from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# 设置无头浏览器（无界面运行）
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# 启动浏览器
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 访问小红书搜索页面
search_keyword = "AI建筑设计图"
url = f"https://www.xiaohongshu.com/search/result/{search_keyword}"
driver.get(url)
time.sleep(5)  # 等待页面加载

# 模拟滚动加载更多内容（小红书动态加载）
for _ in range(3):  # 滚动3次，调整次数以获取更多数据
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # 等待内容加载

# 提取账号信息（需根据实际页面结构调整XPath）
accounts = driver.find_elements(By.XPATH, "//a[contains(@class, 'user-name')]")  # 假设用户名的XPath
data = []
for account in accounts:
    username = account.text.strip()
    profile_url = account.get_attribute("href")
    if username and profile_url:
        data.append({"Username": username, "Profile URL": profile_url})
        print(f"用户名: {username}, 链接: {profile_url}")

# 保存到Excel
import pandas as pd
df = pd.DataFrame(data)
df.to_excel("ai_architecture_accounts_xiaohongshu.xlsx", index=False)

# 关闭浏览器
driver.quit()