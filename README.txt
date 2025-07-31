# Max Style Panel 插件安装指南

## 安装方法

### 方法一：使用安装脚本（推荐）

1. 双击运行 `install_plugin.bat`
2. 等待安装完成
3. 重启3ds Max

### 方法二：手动安装

1. 将 `MaxStylePanelQt.py` 复制到以下目录：
   `C:\Users\[用户名]\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\usermacros\`

2. 将 `MaxStylePanelQtLauncher.ms` 复制到以下目录：
   `C:\Users\[用户名]\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\scripts\Startup\`

3. 重启3ds Max

## 使用方法

1. 启动3ds Max后，插件会自动加载
2. 在首次使用时，会显示登录窗口
3. 如果您是新用户，请点击"注册"按钮创建账户
4. 登录成功后，插件主界面会显示出来

## 故障排除

如果插件无法正常加载，请尝试以下步骤：

1. 确保Python文件和启动器脚本已正确复制到指定目录
2. 检查3ds Max的脚本错误日志
3. 尝试手动运行脚本：在3ds Max中，打开MAXScript编辑器，输入并运行：
   ```
   macros.run "StyleTools" "MaxStylePanelQtLauncher"
   ```

## 联系支持

如有任何问题，请联系技术支持。