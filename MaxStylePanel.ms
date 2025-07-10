-- MaxStylePanel.ms
-- 3ds Max 现代化多Tab面板（顶部4个可切换Tab，每个Tab下方有下拉栏）
macroScript MaxStylePanelMacro
category:"StyleTools"
toolTip:"Max Style Panel"
(
    global MaxStylePanelRefs
    global setChineseFont
    fn setChineseFont ctrl =
    (
        local font = dotNetObject "System.Drawing.Font" "Microsoft YaHei" 12 ((dotNetClass "System.Drawing.FontStyle").Regular)
        try(ctrl.font = font) catch()
        if isProperty ctrl #controls do
        (
            local n = ctrl.controls.Count
            for i = 0 to n-1 do
            (
                local c = ctrl.controls.Item i
                setChineseFont c
            )
        )
    )
    -- 全局事件处理函数
    fn MaxStylePanel_DragEnter sender args =
    (
        if args.Data.GetDataPresent (dotNetClass "System.Windows.Forms.DataFormats").FileDrop do
        (
            args.Effect = (dotNetClass "System.Windows.Forms.DragDropEffects").Copy
            sender.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 80 120 200
        )
    )
    fn MaxStylePanel_DragLeave sender args =
    (
        sender.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 60 60 60
    )
    fn MaxStylePanel_DragDrop sender args =
    (
        local idx = sender.Tag as string
        local picPanel = MaxStylePanelRefs.Item["picPanel"+idx]
        local picText = MaxStylePanelRefs.Item["picText"+idx]
        local picNameLabel = MaxStylePanelRefs.Item["picNameLabel"+idx]
        local files = args.Data.GetData (dotNetClass "System.Windows.Forms.DataFormats").FileDrop
        if files.count > 0 do
        (
            local imgPath = files.GetValue 0
            if matchPattern imgPath pattern:"*.jpg;*.jpeg;*.png;*.bmp;*.gif" ignoreCase:true do
            (
                local img = dotNetObject "System.Drawing.Bitmap" imgPath
                if picPanel != undefined do
                (
                    picPanel.BackgroundImage = img
                    picPanel.BackgroundImageLayout = (dotNetClass "System.Windows.Forms.ImageLayout").Stretch
                    picPanel.Refresh()
                    if picPanel.Parent != undefined do picPanel.Parent.Refresh()
                )
                if picText != undefined do
                (
                    local parentPanel = picText.Parent
                    if parentPanel != undefined do parentPanel.Controls.Remove picText
                )
                if picNameLabel != undefined do
                (
                    picNameLabel.Text = getFilenameFile imgPath
                )
            )
        )
        sender.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 60 60 60
    )
    fn MaxStylePanel_MouseClick sender args =
    (
        local idx = sender.Tag as string
        local picPanel = MaxStylePanelRefs.Item["picPanel"+idx]
        local picText = MaxStylePanelRefs.Item["picText"+idx]
        local picNameLabel = MaxStylePanelRefs.Item["picNameLabel"+idx]
        local ofd = dotNetObject "System.Windows.Forms.OpenFileDialog"
        ofd.Filter = "图片文件|*.jpg;*.jpeg;*.png;*.bmp;*.gif"
        if ofd.ShowDialog() == (dotNetClass "System.Windows.Forms.DialogResult").OK do
        (
            local imgPath = ofd.FileName
            local img = dotNetObject "System.Drawing.Bitmap" imgPath
            if picPanel != undefined do
            (
                picPanel.BackgroundImage = img
                picPanel.BackgroundImageLayout = (dotNetClass "System.Windows.Forms.ImageLayout").Stretch
                picPanel.Refresh()
                if picPanel.Parent != undefined do picPanel.Parent.Refresh()
            )
            if picText != undefined do
            (
                picText.Visible = false -- 上传后隐藏提示文字
            )
            if picNameLabel != undefined do
            (
                picNameLabel.Text = getFilenameFile imgPath
            )
        )
    )
    fn MaxStylePanel_MouseEnter sender args = (
        sender.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 80 120 200
    )
    fn MaxStylePanel_MouseLeave sender args = (
        sender.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 60 60 60
    )
    fn MaxStylePanel_TrackStrengthChanged sender args =
    (
        local idx = sender.Tag as string
        local txtStrength = MaxStylePanelRefs.Item["txtStrength"+idx]
        if txtStrength != undefined do
            txtStrength.Text = formattedPrint (sender.Value/100.0) format:".2f"
    )
    fn MaxStylePanel_StrengthTextChanged sender args =
    (
        local idx = sender.Tag as string
        local trackStrength = MaxStylePanelRefs.Item["trackStrength"+idx]
        local v = try (execute sender.Text as string) catch (undefined)
        if v != undefined and isKindOf v Number and v >= 0.0 and v <= 1.0 do
        (
            local newVal = (v * 100) as integer
            if trackStrength != undefined and trackStrength.Value != newVal do trackStrength.Value = newVal
        )
        -- 内容为空或非法时不做处理，允许用户编辑
    )
    fn createTabPanel = (
        MaxStylePanelRefs = dotNetObject "System.Collections.Hashtable"
        local form = dotNetObject "System.Windows.Forms.Form"
        form.Text = "多Tab演示面板"
        form.Size = dotNetObject "System.Drawing.Size" 600 600
        form.MinimumSize = dotNetObject "System.Drawing.Size" 600 500
        form.MaximumSize = dotNetObject "System.Drawing.Size" 600 1200
        form.FormBorderStyle = (dotNetClass "System.Windows.Forms.FormBorderStyle").Sizable
        form.MaximizeBox = false
        form.MinimizeBox = false
        form.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 34 34 34

        -- TabControl
        local tabControl = dotNetObject "System.Windows.Forms.TabControl"
        tabControl.Dock = (dotNetClass "System.Windows.Forms.DockStyle").Fill
        tabControl.Appearance = (dotNetClass "System.Windows.Forms.TabAppearance").FlatButtons
        tabControl.ItemSize = dotNetObject "System.Drawing.Size" 120 36
        tabControl.SizeMode = (dotNetClass "System.Windows.Forms.TabSizeMode").Fixed
        tabControl.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 34 34 34

        -- 4个Tab页
        local contentStartY = 100
        for i = 1 to 4 do (
            local tabPage = dotNetObject "System.Windows.Forms.TabPage"
            tabPage.Text = case i of (
                1: "室内设计"
                2: "材质库"
                3: "模型库"
                4: "设置"
            )
            tabPage.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 34 34 34
            -- 下拉栏
            local combo = dotNetObject "System.Windows.Forms.ComboBox"
            combo.Items.AddRange #(tabPage.Text + "选项1", tabPage.Text + "选项2", tabPage.Text + "选项3")
            combo.SelectedIndex = 0
            local label = dotNetObject "System.Windows.Forms.Label"
            label.Text = tabPage.Text + "选项："
            label.ForeColor = (dotNetClass "System.Drawing.Color").White
            label.Location = dotNetObject "System.Drawing.Point" 40 34
            label.Size = dotNetObject "System.Drawing.Size" 260 28
            tabPage.Controls.Add label

            combo.Location = dotNetObject "System.Drawing.Point" 310 30
            combo.Size = dotNetObject "System.Drawing.Size" 220 32
            combo.Anchor = (dotNetClass "System.Enum").ToObject (dotNetClass "System.Windows.Forms.AnchorStyles") ((dotNetClass "System.Windows.Forms.AnchorStyles").Top.value__ + (dotNetClass "System.Windows.Forms.AnchorStyles").Left.value__)
            combo.DropDownStyle = (dotNetClass "System.Windows.Forms.ComboBoxStyle").DropDownList
            combo.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 50 50 50
            combo.ForeColor = (dotNetClass "System.Drawing.Color").White
            tabPage.Controls.Add combo
            -- 用Panel替换GroupBox
            -- 标题Label
            local labelTitle = dotNetObject "System.Windows.Forms.Label"
            labelTitle.Text = "这里是“" + tabPage.Text + "”内容区"
            labelTitle.ForeColor = (dotNetClass "System.Drawing.Color").Gray
            labelTitle.Font = dotNetObject "System.Drawing.Font" "Microsoft YaHei" 14 ((dotNetClass "System.Drawing.FontStyle").Bold)
            labelTitle.AutoSize = true
            labelTitle.Location = dotNetObject "System.Drawing.Point" 40 contentStartY

            -- 副标题Label（参考图像）
            local labelSubTitle = dotNetObject "System.Windows.Forms.Label"
            labelSubTitle.Text = "参考图像"
            labelSubTitle.Font = dotNetObject "System.Drawing.Font" "Microsoft YaHei" 12 ((dotNetClass "System.Drawing.FontStyle").Regular)
            labelSubTitle.ForeColor = (dotNetClass "System.Drawing.Color").White
            labelSubTitle.Location = dotNetObject "System.Drawing.Point" 40 (contentStartY + 40)
            labelSubTitle.Size = dotNetObject "System.Drawing.Size" 200 28
            tabPage.Controls.Add labelTitle
            tabPage.Controls.Add labelSubTitle

            -- 子TabControl
            local subTab = dotNetObject "System.Windows.Forms.TabControl"
            local uploadWidth = 300
            subTab.Location = dotNetObject "System.Drawing.Point" 40 (contentStartY + 80)
            subTab.Size = dotNetObject "System.Drawing.Size" uploadWidth 40
            subTab.Appearance = (dotNetClass "System.Windows.Forms.TabAppearance").Normal
            subTab.ItemSize = dotNetObject "System.Drawing.Size" 120 32
            subTab.SizeMode = (dotNetClass "System.Windows.Forms.TabSizeMode").Fixed

            local tab1 = dotNetObject "System.Windows.Forms.TabPage"
            tab1.Text = "自定义参考图"
            local tab2 = dotNetObject "System.Windows.Forms.TabPage"
            tab2.Text = "参考图片库"
            subTab.TabPages.Add tab1
            subTab.TabPages.Add tab2
            tabPage.Controls.Add subTab

            -- 上传区整体下移
            local groupImgY = contentStartY + 80 + 50  -- 标题高40+Tab高40+间隔10
            local groupImgH = 120
            local groupImg = dotNetObject "System.Windows.Forms.Panel"
            groupImg.Location = dotNetObject "System.Drawing.Point" 40 groupImgY
            groupImg.Size = dotNetObject "System.Drawing.Size" uploadWidth groupImgH
            groupImg.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 44 44 44
            groupImg.BorderStyle = (dotNetClass "System.Windows.Forms.BorderStyle").FixedSingle

            local picPanel = dotNetObject "System.Windows.Forms.Panel"
            -- 放大picPanel覆盖整个上传区内容区，并居中
            local picPanelW = 180
            local picPanelH = 90
            local picPanelX = (uploadWidth - picPanelW) / 2
            local picPanelY = (groupImgH - picPanelH) / 2
            picPanel.Location = dotNetObject "System.Drawing.Point" picPanelX picPanelY
            picPanel.Size = dotNetObject "System.Drawing.Size" picPanelW picPanelH
            picPanel.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 60 60 60
            picPanel.AllowDrop = true
            picPanel.BorderStyle = (dotNetClass "System.Windows.Forms.BorderStyle").FixedSingle
            picPanel.Tag = i -- 用于事件回调区分Tab

            local picText = dotNetObject "System.Windows.Forms.Label"
            -- 美化提示文字
            picText.Text = "拖拽或点击此区域上传图片"
            picText.ForeColor = (dotNetClass "System.Drawing.Color").Gray
            picText.TextAlign = (dotNetClass "System.Drawing.ContentAlignment").MiddleCenter
            picText.Dock = (dotNetClass "System.Windows.Forms.DockStyle").Fill
            picText.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 60 60 60
            picText.Font = dotNetObject "System.Drawing.Font" "Microsoft YaHei" 11 ((dotNetClass "System.Drawing.FontStyle").Regular)
            picText.Tag = i
            picText.Enabled = false

            MaxStylePanelRefs.Add ("picPanel" + i as string) picPanel
            MaxStylePanelRefs.Add ("picText" + i as string) picText
            -- 上传区文件名Label
            local picNameLabel = dotNetObject "System.Windows.Forms.Label"
            picNameLabel.Text = ""
            picNameLabel.ForeColor = (dotNetClass "System.Drawing.Color").Gray
            picNameLabel.Location = dotNetObject "System.Drawing.Point" 20 (groupImgY + groupImgH) -- Panel下方
            picNameLabel.Size = dotNetObject "System.Drawing.Size" 180 18
            picNameLabel.TextAlign = (dotNetClass "System.Drawing.ContentAlignment").MiddleCenter
            groupImg.Controls.Add picNameLabel
            MaxStylePanelRefs.Add ("picNameLabel" + i as string) picNameLabel

            -- 拖拽进入高亮
            dotNet.addEventHandler picPanel "DragEnter" MaxStylePanel_DragEnter
            -- 拖拽离开恢复
            dotNet.addEventHandler picPanel "DragLeave" MaxStylePanel_DragLeave
            -- 拖拽释放处理图片
            dotNet.addEventHandler picPanel "DragDrop" MaxStylePanel_DragDrop
            -- 点击弹出文件选择
            dotNet.addEventHandler picPanel "MouseClick" MaxStylePanel_MouseClick
            -- 设置鼠标手型光标
            picPanel.Cursor = (dotNetClass "System.Windows.Forms.Cursors").Hand
            picText.Cursor = (dotNetClass "System.Windows.Forms.Cursors").Hand
            -- 悬停高亮
            dotNet.addEventHandler picPanel "MouseEnter" MaxStylePanel_MouseEnter
            dotNet.addEventHandler picPanel "MouseLeave" MaxStylePanel_MouseLeave

            groupImg.Controls.Add picPanel
            picPanel.Controls.Add picText
            tabPage.Controls.Add groupImg
            -- 提示词区域
            local yBase = groupImgY + groupImgH + 20 -- 提示词区域Y坐标自动跟随
            local labelPrompt = dotNetObject "System.Windows.Forms.Label"
            labelPrompt.Text = "提示词"
            labelPrompt.ForeColor = (dotNetClass "System.Drawing.Color").White
            labelPrompt.Location = dotNetObject "System.Drawing.Point" 40 yBase
            labelPrompt.Size = dotNetObject "System.Drawing.Size" 100 28

            local txtPrompt = dotNetObject "System.Windows.Forms.TextBox"
            txtPrompt.Location = dotNetObject "System.Drawing.Point" 150 yBase
            txtPrompt.Size = dotNetObject "System.Drawing.Size" 180 28
            txtPrompt.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 40 40 40
            txtPrompt.ForeColor = (dotNetClass "System.Drawing.Color").White
            txtPrompt.BorderStyle = (dotNetClass "System.Windows.Forms.BorderStyle").FixedSingle
            txtPrompt.Font = dotNetObject "System.Drawing.Font" "Microsoft YaHei" 12 ((dotNetClass "System.Drawing.FontStyle").Regular)

            -- 控制强度区域
            local yBase2 = yBase + 28 + 30 -- 控制强度区域Y坐标
            local labelStrength = dotNetObject "System.Windows.Forms.Label"
            labelStrength.Text = "控制强度"
            labelStrength.ForeColor = (dotNetClass "System.Drawing.Color").White
            labelStrength.Location = dotNetObject "System.Drawing.Point" 40 yBase2
            labelStrength.Size = dotNetObject "System.Drawing.Size" 100 28

            local labelWeak = dotNetObject "System.Windows.Forms.Label"
            labelWeak.Text = "弱"
            labelWeak.ForeColor = (dotNetClass "System.Drawing.Color").Gray
            labelWeak.Location = dotNetObject "System.Drawing.Point" 40 (yBase2+35)
            labelWeak.Size = dotNetObject "System.Drawing.Size" 30 22

            local trackStrength = dotNetObject "System.Windows.Forms.TrackBar"
            trackStrength.Location = dotNetObject "System.Drawing.Point" 75 (yBase2+30)
            trackStrength.Size = dotNetObject "System.Drawing.Size" 140 30
            trackStrength.Minimum = 0
            trackStrength.Maximum = 100
            trackStrength.Value = 55
            trackStrength.TickFrequency = 10
            trackStrength.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 40 40 40
            trackStrength.Tag = i
            MaxStylePanelRefs.Add ("txtStrength" + i as string) txtStrength
            MaxStylePanelRefs.Add ("trackStrength" + i as string) trackStrength

            local labelStrong = dotNetObject "System.Windows.Forms.Label"
            labelStrong.Text = "强"
            labelStrong.ForeColor = (dotNetClass "System.Drawing.Color").Gray
            labelStrong.Location = dotNetObject "System.Drawing.Point" 220 (yBase2+35)
            labelStrong.Size = dotNetObject "System.Drawing.Size" 30 22

            local txtStrength = dotNetObject "System.Windows.Forms.TextBox"
            txtStrength.Location = dotNetObject "System.Drawing.Point" 260 (yBase2+30)
            txtStrength.Size = dotNetObject "System.Drawing.Size" 50 30
            txtStrength.Text = formattedPrint (trackStrength.Value/100.0) format:".2f"
            txtStrength.ReadOnly = false
            txtStrength.TextAlign = (dotNetClass "System.Windows.Forms.HorizontalAlignment").Center
            txtStrength.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 40 40 40
            txtStrength.ForeColor = (dotNetClass "System.Drawing.Color").White
            txtStrength.BorderStyle = (dotNetClass "System.Windows.Forms.BorderStyle").FixedSingle
            txtStrength.Font = dotNetObject "System.Drawing.Font" "Microsoft YaHei" 12 ((dotNetClass "System.Drawing.FontStyle").Regular)
            txtStrength.Tag = i
            dotNet.addEventHandler txtStrength "TextChanged" MaxStylePanel_StrengthTextChanged

            dotNet.addEventHandler trackStrength "ValueChanged" MaxStylePanel_TrackStrengthChanged

            tabPage.Controls.Add labelPrompt
            tabPage.Controls.Add txtPrompt
            tabPage.Controls.Add labelStrength
            tabPage.Controls.Add labelWeak
            tabPage.Controls.Add trackStrength
            tabPage.Controls.Add labelStrong
            tabPage.Controls.Add txtStrength
            -- 占位内容
            tabControl.TabPages.Add tabPage
        )

        form.Controls.Add tabControl
        setChineseFont form
        form.Show()
    )

    on execute do (
        createTabPanel()
    )
) 