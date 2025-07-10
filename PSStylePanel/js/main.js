// 顶部tab切换逻辑

if (typeof CSInterface !== 'undefined') {
    window.csInterface = new CSInterface();
}

document.addEventListener('DOMContentLoaded', function() {
    var tabs = document.querySelectorAll('.ps-tab');
    var tabContents = document.querySelectorAll('.tab-content');
    var tabNames = ['室内', '建筑', '景观', '图像'];
    tabs.forEach(function(tab, idx) {
        tab.addEventListener('click', function() {
            tabs.forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');
            // 显示对应内容区
            tabContents.forEach(function(content, cidx) {
                content.style.display = (idx === cidx) ? 'block' : 'none';
            });
            // 切换tab时清空底部内容
            document.getElementById('ps-footer-content').innerHTML = '';
            // 切换tab时自动显示标题
            var select = document.getElementById('ps-select' + (idx+1));
            if(select) updateFooterForTab(idx, select.value);
        });
    });
    // 监听所有tab下拉框
    for(var i=1;i<=4;i++){
        (function(i){
            var select = document.getElementById('ps-select'+i);
            if(select){
                select.addEventListener('change', function(){
                    updateFooterForTab(i-1, select.value);
                });
                // 页面初始时也触发一次
                if(i===1) updateFooterForTab(0, select.value);
            }
        })(i);
    }
});

function updateFooterForTab(tabIdx, val) {
    var footer = document.getElementById('ps-footer-content');
    var tabContent = document.getElementById('tab'+(tabIdx+1)+'-content');
    // 统一移除所有可能的标题元素，防止叠加
    ['interior-cpt-title', 'building-cpt-title', 'landscape-cpt-title', 'image-cpt-title'].forEach(function(id){
        var el = document.getElementById(id);
        if(el) el.remove();
    });
    if(!footer) return;
    var tabNames = ['室内', '建筑', '景观', '图像'];
    var select = document.getElementById('ps-select'+(tabIdx+1));
    var showTitle = tabNames[tabIdx];
    if(select){
        var selectedText = select.options[select.selectedIndex].text;
        showTitle = tabNames[tabIdx] + '-' + selectedText;
    }
    // 标题插入到下拉框上方
    if(tabContent) {
        var titleDiv = document.createElement('div');
        titleDiv.className = 'footer-title';
        titleDiv.id = ['interior-cpt-title', 'building-cpt-title', 'landscape-cpt-title', 'image-cpt-title'][tabIdx];
        titleDiv.innerText = showTitle;
        var selectLabel = tabContent.querySelector('label');
        if(selectLabel && selectLabel.parentNode) {
            selectLabel.parentNode.insertBefore(titleDiv, selectLabel);
        } else {
            tabContent.parentNode.insertBefore(titleDiv, tabContent);
        }
    }
    
    // 根据不同的标签页显示不同的内容
    if(tabIdx === 0) {
        // 室内设计
        var select1 = document.getElementById('ps-select1');
        if(select1) updateFooterForInterior(select1.value);
    } else {
        // 其他标签页显示默认内容
        updateFooterForOtherTabs(tabIdx, val);
    }
}

function updateFooterForInterior(val) {
    var footer = document.getElementById('ps-footer-content');
    var tab1Content = document.getElementById('tab1-content');
    ['interior-cpt-title', 'building-cpt-title', 'landscape-cpt-title', 'image-cpt-title'].forEach(function(id){
        var el = document.getElementById(id);
        if(el) el.remove();
    });
    if(!footer) return;
    var titleMap = {
        '1': '室内-彩平',
        '2': '室内-毛坯房',
        '3': '室内-线稿',
        '4': '室内-白模',
        '5': '室内-多角度（白模）',
        '6': '室内-多角度（线稿）',
        '7': '室内-多风格（白模）',
        '8': '室内-多风格（线稿）',
        '9': '室内-风格转换',
        '10': '室内-360出图'
    };
    var showTitle = titleMap[val] || '室内设计';
    if(tab1Content) {
        var titleDiv = document.createElement('div');
        titleDiv.className = 'footer-title';
        titleDiv.id = 'interior-cpt-title';
        titleDiv.innerText = showTitle;
        var selectLabel = tab1Content.querySelector('label[for="ps-select1"]');
        if(selectLabel && selectLabel.parentNode) {
            selectLabel.parentNode.insertBefore(titleDiv, selectLabel);
        } else {
            tab1Content.parentNode.insertBefore(titleDiv, tab1Content);
        }
    }
    // 360出图只显示立即生成按钮，无上传区
    if(String(val) === '10') {
        footer.innerHTML = `
            <div class=\"footer-title\">室内-360出图</div>
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        return;
    }
    var advanceRowHtml = `<div class=\"ps-form-block\"><div class=\"ps-advance-row\">\n<label class=\"ps-form-label\" style=\"font-weight:bold;margin-bottom:6px;\">高级参数设置</label>\n<button class=\"ps-advance-btn\" id=\"advanceBtn\">▶</button>\n</div></div>`;
    footer.innerHTML = `
        ${generateUploadSection(val, 0)}
        ${generatePromptSection(val, 0)}
        <div class=\"ps-form-block\">\n                <label class=\"ps-form-label\">控制强度</label>\n                <div class=\"ps-slider-row\">\n                    <span class=\"ps-slider-label\">弱</span>\n                    <input type=\"range\" min=\"0\" max=\"1\" step=\"0.01\" value=\"0.55\" class=\"ps-slider\" id=\"strengthSlider\">\n                    <span class=\"ps-slider-label\">强</span>\n                    <input type=\"text\" class=\"ps-slider-value\" id=\"sliderValue\" value=\"0.55\">\n                </div>\n            </div>
        <div class=\"ps-form-block\" style=\"text-align:center;margin:16px 0 0 0;\">
            <button class=\"ps-generate-btn\" id=\"btnDuplicateScaleLayer\" style=\"width:100%;max-width:320px;min-width:180px;margin:0 auto;display:block;\">获取并放大当前图层</button>
            <div id=\"ps-dup-scale-result\" style=\"margin-top:8px;color:#4fc3f7;text-align:left;max-width:320px;margin-left:auto;margin-right:auto;\"></div>
        </div>
        <div class=\"ps-form-block\" style=\"text-align:center;margin:0 0 0 0;\">
            <button class=\"ps-generate-btn\" id=\"btnExportCurrentLayer\" style=\"width:100%;max-width:320px;min-width:180px;margin:0 auto 8px auto;display:block;\">导出当前图层为PNG</button>
        </div>
        <div class=\"ps-form-block\" style=\"text-align:center;margin:0 0 0 0;\">
            <button class=\"ps-generate-btn\" id=\"btnImportImageToLayer\" style=\"width:100%;max-width:320px;min-width:180px;margin:0 auto;display:block;\">插入图片为新图层</button>
            <input type=\"file\" id=\"importImageInput\" style=\"display:none;\" accept=\"image/*\">
            <div id=\"ps-export-import-result\" style=\"margin-top:8px;color:#4fc3f7;text-align:left;max-width:320px;margin-left:auto;margin-right:auto;word-break:break-all;\"></div>
        </div>
        ${advanceRowHtml}
        <div id=\"advancePanelContainer\"></div>
        <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">
            <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>
        </div>
    `;
    // 初始化上传区域的交互逻辑
    initializeUploadInteractions();
    // 获取图层列表并填充下拉框
    loadLayerList();
    // 切换按钮逻辑
    var customBtn = document.getElementById('customRefBtn');
    var libBtn = document.getElementById('libRefBtn');
    if(customBtn && libBtn) {
        customBtn.onclick = function() {
            customBtn.classList.add('active');
            libBtn.classList.remove('active');
        };
        libBtn.onclick = function() {
            libBtn.classList.add('active');
            customBtn.classList.remove('active');
        };
    }
    // 滑块与数值联动
    var slider = document.getElementById('strengthSlider');
    var sliderValue = document.getElementById('sliderValue');
    if(slider && sliderValue) {
        slider.addEventListener('input', function() {
            sliderValue.value = parseFloat(slider.value).toFixed(2);
        });
        sliderValue.addEventListener('change', function(){
            let v = parseFloat(sliderValue.value);
            if(isNaN(v) || v < 0 || v > 1) {
                sliderValue.value = parseFloat(slider.value).toFixed(2);
                return;
            }
            v = Math.round(v * 100) / 100;
            sliderValue.value = v.toFixed(2);
            slider.value = v;
        });
        sliderValue.addEventListener('keydown', function(e){
            if(e.key==='Enter'){
                sliderValue.blur();
            }
        });
    }
    // 高级参数下拉栏逻辑
    var advanceBtn = document.getElementById('advanceBtn');
    var advanceOpen = false;
    if(advanceBtn) {
        advanceBtn.onclick = function() {
            advanceOpen = !advanceOpen;
            if(advanceOpen) {
                advanceBtn.innerHTML = '▼';
                showAdvancePanel();
            } else {
                advanceBtn.innerHTML = '▶';
                hideAdvancePanel();
            }
        };
    }
    // 其他按钮事件绑定
    bindButtonEvents();
}

// 为其他标签页（建筑、景观、图像）显示默认内容
function updateFooterForOtherTabs(tabIdx, val) {
    var footer = document.getElementById('ps-footer-content');
    if(!footer) return;
    var tabNames = ['室内', '建筑', '景观', '图像'];
    var select = document.getElementById('ps-select'+(tabIdx+1));
    var showTitle = tabNames[tabIdx];
    if(select){
        var selectedText = select.options[select.selectedIndex].text;
        showTitle = tabNames[tabIdx] + '-' + selectedText;
    }
    // 特殊case保留，其他全部统一
    if(tabIdx === 2 && val === '3') {
        footer.innerHTML = `
            ${generateUploadSection(val, tabIdx)}
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        initializeUploadInteractions();
        loadLayerList();
        var customBtn = document.getElementById('customRefBtn');
        var libBtn = document.getElementById('libRefBtn');
        if(customBtn && libBtn) {
            customBtn.onclick = function() {
                customBtn.classList.add('active');
                libBtn.classList.remove('active');
            };
            libBtn.onclick = function() {
                libBtn.classList.add('active');
                customBtn.classList.remove('active');
            };
        }
        bindButtonEvents();
        return;
    }
    // 图像处理tab的AI去除万物和AI去水印只显示按钮
    if (tabIdx === 3 && (String(val) === '3' || String(val) === '4' || String(val) === '15')) {
    footer.innerHTML = `
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        bindButtonEvents();
        return;
    }
    // 图像处理tab的修改局部只显示提示词和按钮
    if (tabIdx === 3 && String(val) === '2') {
        footer.innerHTML = `
            ${generatePromptSection(val, tabIdx)}
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        bindButtonEvents();
        return;
    }
    // 图像处理tab的增加物体只显示提示词和按钮
    if (tabIdx === 3 && String(val) === '5') {
        footer.innerHTML = `
            ${generatePromptSection(val, tabIdx)}
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        bindButtonEvents();
        return;
    }
    // 图像处理tab的替换（产品）只显示一个图像上传区和按钮
    if (tabIdx === 3 && String(val) === '7') {
        footer.innerHTML = `
            ${generateUploadSection(val, tabIdx)}
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        initializeUploadInteractions();
        loadLayerList();
        var customBtn = document.getElementById('customRefBtn');
        var libBtn = document.getElementById('libRefBtn');
        if(customBtn && libBtn) {
            customBtn.onclick = function() {
                customBtn.classList.add('active');
                libBtn.classList.remove('active');
            };
            libBtn.onclick = function() {
                libBtn.classList.add('active');
                customBtn.classList.remove('active');
            };
        }
        bindButtonEvents();
        return;
    }
    // 图像处理tab的替换（背景天花）只显示一个图像上传区和按钮
    if (tabIdx === 3 && String(val) === '8') {
        footer.innerHTML = `
            ${generateUploadSection(val, tabIdx)}
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        initializeUploadInteractions();
        loadLayerList();
        var customBtn = document.getElementById('customRefBtn');
        var libBtn = document.getElementById('libRefBtn');
        if(customBtn && libBtn) {
            customBtn.onclick = function() {
                customBtn.classList.add('active');
                libBtn.classList.remove('active');
            };
            libBtn.onclick = function() {
                libBtn.classList.add('active');
                customBtn.classList.remove('active');
            };
        }
        bindButtonEvents();
        return;
    }
    // 图像处理tab的扩图只显示扩展像素和按钮
    if (tabIdx === 3 && String(val) === '9') {
        footer.innerHTML = `
            ${generatePromptSection(val, tabIdx)}
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        bindButtonEvents();
        return;
    }
    // 图像处理tab的溶图（局部）需要高级参数
    if (tabIdx === 3 && String(val) === '13') {
        var advanceRowHtml = `<div class=\"ps-form-block\"><div class=\"ps-advance-row\">\n<label class=\"ps-form-label\" style=\"font-weight:bold;margin-bottom:6px;\">高级参数设置</label>\n<button class=\"ps-advance-btn\" id=\"advanceBtn\">▶</button>\n</div></div>`;
        footer.innerHTML = `
            ${generateUploadSection(val, tabIdx)}
            ${generatePromptSection(val, tabIdx)}
            ${advanceRowHtml}
            <div id=\"advancePanelContainer\"></div>
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        initializeUploadInteractions();
        loadLayerList();
        var customBtn1 = document.getElementById('customRefBtn1');
        var libBtn1 = document.getElementById('libRefBtn1');
        var customBtn2 = document.getElementById('customRefBtn2');
        var libBtn2 = document.getElementById('libRefBtn2');
        if(customBtn1 && libBtn1) {
            customBtn1.onclick = function() {
                customBtn1.classList.add('active');
                libBtn1.classList.remove('active');
            };
            libBtn1.onclick = function() {
                libBtn1.classList.add('active');
                customBtn1.classList.remove('active');
            };
        }
        if(customBtn2 && libBtn2) {
            customBtn2.onclick = function() {
                customBtn2.classList.add('active');
                libBtn2.classList.remove('active');
            };
            libBtn2.onclick = function() {
                libBtn2.classList.add('active');
                customBtn2.classList.remove('active');
            };
        }
        // 高级参数下拉栏逻辑
        var advanceBtn = document.getElementById('advanceBtn');
        var advanceOpen = false;
        if(advanceBtn) {
            advanceBtn.onclick = function() {
                advanceOpen = !advanceOpen;
                if(advanceOpen) {
                    advanceBtn.innerHTML = '▼';
                    showAdvancePanelForDualImage();
                } else {
                    advanceBtn.innerHTML = '▶';
                    hideAdvancePanel();
                }
            };
        }
        bindButtonEvents();
        return;
    }
    // 图像处理tab的溶图需要高级参数
    if (tabIdx === 3 && String(val) === '12') {
        var advanceRowHtml = `<div class=\"ps-form-block\"><div class=\"ps-advance-row\">\n<label class=\"ps-form-label\" style=\"font-weight:bold;margin-bottom:6px;\">高级参数设置</label>\n<button class=\"ps-advance-btn\" id=\"advanceBtn\">▶</button>\n</div></div>`;
        footer.innerHTML = `
            ${generateUploadSection(val, tabIdx)}
            ${generatePromptSection(val, tabIdx)}
            ${advanceRowHtml}
            <div id=\"advancePanelContainer\"></div>
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        loadLayerList();
        // 高级参数下拉栏逻辑
        var advanceBtn = document.getElementById('advanceBtn');
        var advanceOpen = false;
        if(advanceBtn) {
            advanceBtn.onclick = function() {
                advanceOpen = !advanceOpen;
                if(advanceOpen) {
                    advanceBtn.innerHTML = '▼';
                    showAdvancePanelForDualImage();
                } else {
                    advanceBtn.innerHTML = '▶';
                    hideAdvancePanel();
                }
            };
        }
        bindButtonEvents();
        return;
    }
    // 图像处理tab的洗图需要控制强度和高级参数
    if (tabIdx === 3 && String(val) === '10') {
        var advanceRowHtml = `<div class=\"ps-form-block\"><div class=\"ps-advance-row\">\n<label class=\"ps-form-label\" style=\"font-weight:bold;margin-bottom:6px;\">高级参数设置</label>\n<button class=\"ps-advance-btn\" id=\"advanceBtn\">▶</button>\n</div></div>`;
        footer.innerHTML = `
            ${generateUploadSection(val, tabIdx)}
            ${generatePromptSection(val, tabIdx)}
            <div class=\"ps-form-block\">\n                <label class=\"ps-form-label\">控制强度</label>\n                <div class=\"ps-slider-row\">\n                    <span class=\"ps-slider-label\">弱</span>\n                    <input type=\"range\" min=\"0\" max=\"1\" step=\"0.01\" value=\"0.55\" class=\"ps-slider\" id=\"strengthSlider\">\n                    <span class=\"ps-slider-label\">强</span>\n                    <input type=\"text\" class=\"ps-slider-value\" id=\"sliderValue\" value=\"0.55\">\n                </div>\n            </div>
            ${advanceRowHtml}
            <div id=\"advancePanelContainer\"></div>
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        loadLayerList();
        // 高级参数下拉栏逻辑
        var advanceBtn = document.getElementById('advanceBtn');
        var advanceOpen = false;
        if(advanceBtn) {
            advanceBtn.onclick = function() {
                advanceOpen = !advanceOpen;
                if(advanceOpen) {
                    advanceBtn.innerHTML = '▼';
                    showAdvancePanel();
                } else {
                    advanceBtn.innerHTML = '▶';
                    hideAdvancePanel();
                }
            };
        }
        bindButtonEvents();
        return;
    }
    // 建筑规划tab补全高级参数
    if(tabIdx === 1) {
        var advanceRowHtml = `<div class=\"ps-form-block\"><div class=\"ps-advance-row\">\n<label class=\"ps-form-label\" style=\"font-weight:bold;margin-bottom:6px;\">高级参数设置</label>\n<button class=\"ps-advance-btn\" id=\"advanceBtn\">▶</button>\n</div></div>`;
        footer.innerHTML = `
            ${generateUploadSection(val, tabIdx)}
        ${generatePromptSection(val)}
            <div class=\"ps-form-block\">\n                <label class=\"ps-form-label\">控制强度</label>\n                <div class=\"ps-slider-row\">\n                    <span class=\"ps-slider-label\">弱</span>\n                    <input type=\"range\" min=\"0\" max=\"1\" step=\"0.01\" value=\"0.55\" class=\"ps-slider\" id=\"strengthSlider\">\n                    <span class=\"ps-slider-label\">强</span>\n                    <input type=\"text\" class=\"ps-slider-value\" id=\"sliderValue\" value=\"0.55\">\n                </div>\n            </div>
            ${advanceRowHtml}
            <div id=\"advancePanelContainer\"></div>
            <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n                <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n            </div>
        `;
        initializeUploadInteractions();
        loadLayerList();
        var customBtn = document.getElementById('customRefBtn');
        var libBtn = document.getElementById('libRefBtn');
        if(customBtn && libBtn) {
            customBtn.onclick = function() {
                customBtn.classList.add('active');
                libBtn.classList.remove('active');
            };
            libBtn.onclick = function() {
                libBtn.classList.add('active');
                customBtn.classList.remove('active');
            };
        }
        // 高级参数下拉栏逻辑
        var advanceBtn = document.getElementById('advanceBtn');
        var advanceOpen = false;
        if(advanceBtn) {
            advanceBtn.onclick = function() {
                advanceOpen = !advanceOpen;
                if(advanceOpen) {
                    advanceBtn.innerHTML = '▼';
                    showAdvancePanel();
                } else {
                    advanceBtn.innerHTML = '▶';
                    hideAdvancePanel();
                }
            };
        }
        bindButtonEvents();
        return;
    }
    // 其余全部统一
    var advanceRowHtml = `<div class=\"ps-form-block\"><div class=\"ps-advance-row\">\n<label class=\"ps-form-label\" style=\"font-weight:bold;margin-bottom:6px;\">高级参数设置</label>\n<button class=\"ps-advance-btn\" id=\"advanceBtn\">▶</button>\n</div></div>`;
    footer.innerHTML = `
        ${generateUploadSection(val, tabIdx)}
        ${generatePromptSection(val, tabIdx)}
        <div class=\"ps-form-block\">\n                <label class=\"ps-form-label\">控制强度</label>\n                <div class=\"ps-slider-row\">\n                    <span class=\"ps-slider-label\">弱</span>\n                    <input type=\"range\" min=\"0\" max=\"1\" step=\"0.01\" value=\"0.55\" class=\"ps-slider\" id=\"strengthSlider\">\n                    <span class=\"ps-slider-label\">强</span>\n                    <input type=\"text\" class=\"ps-slider-value\" id=\"sliderValue\" value=\"0.55\">\n                </div>\n            </div>
        ${advanceRowHtml}
        <div id=\"advancePanelContainer\"></div>
        <div class=\"ps-form-block\" style=\"margin-top:32px;text-align:center;\">\n            <button class=\"ps-generate-btn\" id=\"generateBtn\">立即生成 ✨</button>\n        </div>
    `;
    initializeUploadInteractions();
    loadLayerList();
    var customBtn = document.getElementById('customRefBtn');
    var libBtn = document.getElementById('libRefBtn');
    if(customBtn && libBtn) {
        customBtn.onclick = function() {
            customBtn.classList.add('active');
            libBtn.classList.remove('active');
        };
        libBtn.onclick = function() {
            libBtn.classList.add('active');
            customBtn.classList.remove('active');
        };
    }
    // 高级参数下拉栏逻辑
    var advanceBtn = document.getElementById('advanceBtn');
    var advanceOpen = false;
    if(advanceBtn) {
        advanceBtn.onclick = function() {
            advanceOpen = !advanceOpen;
            if(advanceOpen) {
                advanceBtn.innerHTML = '▼';
                showAdvancePanel();
            } else {
                advanceBtn.innerHTML = '▶';
                hideAdvancePanel();
            }
        };
    }
    bindButtonEvents();
}

// 根据选项生成不同的上传区域
function generateUploadSection(optionValue, tabIdx) {
    // 只有图像处理tab下的特殊选项才不显示上传区
    if (tabIdx === 3 && ['3','4','9','11','14'].includes(String(optionValue))) {
        return '';
    }
    // 图像处理tab的溶图使用双图层选择区域
    if (tabIdx === 3 && String(optionValue) === '12') {
        return generateDualLayerSelectSection();
    }
    // 图像处理tab的溶图（局部）使用双图上传区域
    if (tabIdx === 3 && String(optionValue) === '13') {
        return generateDualImageUploadSection();
    }
    // 只有室内设计tab的多角度和多风格选项才使用特殊上传区域
    if (tabIdx === 0) {
    var uploadSections = {
        '5': generateMultiAngleUploadSection(), // 多角度（白模）
        '6': generateMultiAngleUploadSection(), // 多角度（线稿）
        '7': generateMultiStyleUploadSection(), // 多风格（白模）
        '8': generateMultiStyleUploadSection()  // 多风格（线稿）
    };
    return uploadSections[optionValue] || generateDefaultUploadSection();
    }
    // 其他tab都使用默认上传区域
    return generateDefaultUploadSection();
}

// 根据选项生成不同的提示词区域
function generatePromptSection(optionValue, tabIdx) {
    // 图像处理tab的放大出图不需要提示词
    if (tabIdx === 3 && String(optionValue) === '14') {
        return '';
    }
    // 图像处理tab的图像增强不需要提示词
    if (tabIdx === 3 && String(optionValue) === '11') {
        return '';
    }
    // 图像处理tab的替换（背景天花）不需要提示词
    if (tabIdx === 3 && String(optionValue) === '8') {
        return '';
    }
    // 图像处理tab的替换（产品）不需要提示词
    if (tabIdx === 3 && String(optionValue) === '7') {
        return '';
    }
    // 图像处理tab的扩图显示扩展像素数值输入框
    if (tabIdx === 3 && String(optionValue) === '9') {
        return `<div class=\"ps-form-block\">\n    <label class=\"ps-form-label\">扩展像素</label>\n    <input type=\"number\" class=\"ps-form-input\" id=\"expandPixelInput\" value=\"200\" min=\"1\" step=\"1\">\n</div>`;
    }
    // 图像处理tab的溶图增加横竖图切换
    if (tabIdx === 3 && String(optionValue) === '12') {
        return `<div class=\"ps-form-block\">\n    <label class=\"ps-form-label\">提示词</label>\n    <input type=\"text\" class=\"ps-form-input\" id=\"promptInput\" value=\"\">\n</div>\n<div class=\"ps-form-block\">\n    <label class=\"ps-form-label\">横竖图切换</label>\n    <div style=\"display:flex;align-items:center;margin-top:8px;\">\n        <input type=\"checkbox\" id=\"condSwitch\" checked style=\"width:18px;height:18px;margin-right:8px;\">\n        <span style=\"font-size:16px;color:#fff;\">Cond</span>\n    </div>\n</div>`;
    }
    // 只有室内设计tab的多角度和多风格选项才使用特殊提示词区域
    if (tabIdx === 0) {
    var promptSections = {
        '5': generateMultiAnglePromptSection(), // 多角度（白模）
        '6': generateMultiAnglePromptSection(), // 多角度（线稿）
        '7': generateMultiStylePromptSection(), // 多风格（白模）
        '8': generateMultiStylePromptSection()  // 多风格（线稿）
    };
    return promptSections[optionValue] || generateDefaultPromptSection();
    }
    // 其他tab都使用默认提示词区域
    return generateDefaultPromptSection();
}

// 生成默认上传区域（单张图片）
function generateDefaultUploadSection() {
    return `<div class=\"upload-section\">\n                <div class=\"upload-header\">\n                    <span class=\"upload-label\">参考图像</span>\n                    <span class=\"upload-switch\">\n                        <button class=\"switch-btn active\" id=\"customRefBtn\">自定义参考图</button>\n                        <button class=\"switch-btn\" id=\"libRefBtn\">参考图片库</button>\n                    </span>\n                </div>\n                <div class=\"upload-box\">\n                    <input type=\"file\" id=\"uploadInput\" style=\"display:none;\" accept=\"image/*\">\n                    <div class=\"upload-placeholder\" id=\"uploadPlaceholder\">\n                        <div style=\"display:flex;flex-direction:column;align-items:center;justify-content:center;\">\n                            <span style=\"font-size:40px;color:#8fa0ff;\">📷</span>\n                            <span style=\"font-size:16px;color:#aaa;\">拖放文件到此处上传</span>\n                            <span style=\"font-size:13px;color:#666;\">或点击选择文件</span>\n                        </div>\n                    </div>\n                </div>\n            </div>`;
}

// 生成多角度上传区域（4张图片）
function generateMultiAngleUploadSection() {
    return `<div class="upload-section">
                <div class="multi-upload-vertical">
                    <div class="upload-section-original">
                        <div class="upload-header">
                            <span class="upload-label">原始图像1</span>
                        </div>
                        <select class="ps-form-select" id="layerSelect1">
                            <option value="">请选择图层</option>
                        </select>
                        <div class="upload-header" style="margin-top:12px;">
                            <span class="upload-label">原始图像2</span>
                        </div>
                        <select class="ps-form-select" id="layerSelect2">
                            <option value="">请选择图层</option>
                        </select>
                        <div class="upload-header" style="margin-top:12px;">
                            <span class="upload-label">原始图像3</span>
                        </div>
                        <select class="ps-form-select" id="layerSelect3">
                            <option value="">请选择图层</option>
                        </select>
                    </div>
                    <div class="upload-section-reference">
                        <div class="upload-header">
                            <span class="upload-label">参考图像</span>
                            <span class="upload-switch">
                                <button class="switch-btn active" id="customRefBtn">自定义参考图</button>
                                <button class="switch-btn" id="libRefBtn">参考图片库</button>
                            </span>
                        </div>
                        <div class="upload-box small">
                            <input type="file" id="uploadInput4" style="display:none;" accept="image/*">
                            <div class="upload-placeholder" id="uploadPlaceholder4">
                                <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
                                    <span style="font-size:40px;color:#8fa0ff;">📷</span>
                                    <span style="font-size:16px;color:#aaa;">拖放文件到此处上传</span>
                                    <span style="font-size:13px;color:#666;">或点击选择文件</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
}

// 生成多风格上传区域（三张参考图，每组有切换按钮和上传框）
function generateMultiStyleUploadSection() {
    return `
        <div class="multi-style-vertical">
            <div class="upload-section">
                <div class="upload-section-reference">
                    <div class="upload-header">
                        <span class="upload-label">参考图像1</span>
                        <span class="upload-switch">
                            <button class="switch-btn active" id="customRefBtn1">自定义参考图</button>
                            <button class="switch-btn" id="libRefBtn1">参考图片库</button>
                        </span>
                    </div>
                    <div class="upload-box">
                        <input type="file" id="uploadInput1" style="display:none;" accept="image/*">
                        <div class="upload-placeholder" id="uploadPlaceholder1">
                            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
                                <span style="font-size:40px;color:#8fa0ff;">📷</span>
                                <span style="font-size:16px;color:#aaa;">拖放文件到此处上传</span>
                                <span style="font-size:13px;color:#666;">或点击选择文件</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="upload-section">
                <div class="upload-section-reference">
                    <div class="upload-header">
                        <span class="upload-label">参考图像2</span>
                        <span class="upload-switch">
                            <button class="switch-btn active" id="customRefBtn2">自定义参考图</button>
                            <button class="switch-btn" id="libRefBtn2">参考图片库</button>
                        </span>
                    </div>
                    <div class="upload-box">
                        <input type="file" id="uploadInput2" style="display:none;" accept="image/*">
                        <div class="upload-placeholder" id="uploadPlaceholder2">
                            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
                                <span style="font-size:40px;color:#8fa0ff;">📷</span>
                                <span style="font-size:16px;color:#aaa;">拖放文件到此处上传</span>
                                <span style="font-size:13px;color:#666;">或点击选择文件</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="upload-section">
                <div class="upload-section-reference">
                    <div class="upload-header">
                        <span class="upload-label">参考图像3</span>
                        <span class="upload-switch">
                            <button class="switch-btn active" id="customRefBtn3">自定义参考图</button>
                            <button class="switch-btn" id="libRefBtn3">参考图片库</button>
                        </span>
                    </div>
                    <div class="upload-box">
                        <input type="file" id="uploadInput3" style="display:none;" accept="image/*">
                        <div class="upload-placeholder" id="uploadPlaceholder3">
                            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
                                <span style="font-size:40px;color:#8fa0ff;">📷</span>
                                <span style="font-size:16px;color:#aaa;">拖放文件到此处上传</span>
                                <span style="font-size:13px;color:#666;">或点击选择文件</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 生成双图上传区域（两张图片，用于溶图局部等）
function generateDualImageUploadSection() {
    return `
        <div class="dual-image-vertical">
            <div class="upload-section">
                <div class="upload-section-reference">
                    <div class="upload-header">
                        <span class="upload-label">原始图像</span>
                        <span class="upload-switch">
                            <button class="switch-btn active" id="customRefBtn1">自定义参考图</button>
                            <button class="switch-btn" id="libRefBtn1">参考图片库</button>
                        </span>
                    </div>
                    <div class="upload-box">
                        <input type="file" id="uploadInput1" style="display:none;" accept="image/*">
                        <div class="upload-placeholder" id="uploadPlaceholder1">
                            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
                                <span style="font-size:40px;color:#8fa0ff;">📷</span>
                                <span style="font-size:16px;color:#aaa;">拖放文件到此处上传</span>
                                <span style="font-size:13px;color:#666;">或点击选择文件</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="upload-section">
                <div class="upload-section-reference">
                    <div class="upload-header">
                        <span class="upload-label">参考图像</span>
                        <span class="upload-switch">
                            <button class="switch-btn active" id="customRefBtn2">自定义参考图</button>
                            <button class="switch-btn" id="libRefBtn2">参考图片库</button>
                        </span>
                    </div>
                    <div class="upload-box">
                        <input type="file" id="uploadInput2" style="display:none;" accept="image/*">
                        <div class="upload-placeholder" id="uploadPlaceholder2">
                            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
                                <span style="font-size:40px;color:#8fa0ff;">📷</span>
                                <span style="font-size:16px;color:#aaa;">拖放文件到此处上传</span>
                                <span style="font-size:13px;color:#666;">或点击选择文件</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 生成双图层选择区域（两个下拉栏，用于溶图等）
function generateDualLayerSelectSection() {
    return `
        <div class="dual-layer-vertical">
            <div class="upload-section">
                <div class="upload-section-original">
                    <div class="upload-header">
                        <span class="upload-label">原始图像1</span>
                    </div>
                    <select class="ps-form-select" id="layerSelect1">
                        <option value="">请选择图层</option>
                    </select>
                </div>
            </div>
            <div class="upload-section">
                <div class="upload-section-original">
                    <div class="upload-header">
                        <span class="upload-label">原始图像2</span>
                    </div>
                    <select class="ps-form-select" id="layerSelect2">
                        <option value="">请选择图层</option>
                    </select>
                </div>
            </div>
        </div>
    `;
}

// 生成多角度提示词区域（3个输入框，带分组标题）
function generateMultiAnglePromptSection() {
    return `
        <div class="ps-form-block">
            <div class="prompt-group">
                <label class="prompt-label">提示词1</label>
                <input type="text" class="ps-form-input small" id="promptInput1" value="卧室，现代风格" placeholder="请输入提示词1">
            </div>
            <div class="prompt-group">
                <label class="prompt-label">提示词2</label>
                <input type="text" class="ps-form-input small" id="promptInput2" value="客厅，现代风格" placeholder="请输入提示词2">
            </div>
            <div class="prompt-group">
                <label class="prompt-label">提示词3</label>
                <input type="text" class="ps-form-input small" id="promptInput3" value="书房，现代风格" placeholder="请输入提示词3">
            </div>
        </div>
    `;
}

// 生成多风格提示词区域（三个分组，带标题和分组样式）
function generateMultiStylePromptSection() {
    return `
        <div class="ps-form-block">
            <div class="prompt-group">
                <label class="prompt-label">提示词1</label>
                <input type="text" class="ps-form-input small" id="promptInput1" value="风格1，现代风格" placeholder="请输入提示词1">
            </div>
            <div class="prompt-group">
                <label class="prompt-label">提示词2</label>
                <input type="text" class="ps-form-input small" id="promptInput2" value="风格2，现代风格" placeholder="请输入提示词2">
            </div>
            <div class="prompt-group">
                <label class="prompt-label">提示词3</label>
                <input type="text" class="ps-form-input small" id="promptInput3" value="风格3，现代风格" placeholder="请输入提示词3">
            </div>
        </div>
    `;
}

// 生成默认提示词区域（单个输入框）
function generateDefaultPromptSection() {
    return `<div class=\"ps-form-block\">
                <label class=\"ps-form-label\">提示词</label>
                <input type=\"text\" class=\"ps-form-input\" id=\"promptInput\" value=\"彩平图\">
            </div>`;
}

// 获取图层列表并填充下拉框
function loadLayerList() {
    if (!window.csInterface) {
        console.error('CSInterface不可用');
        return;
    }
    
    // 获取所有图层选择下拉框
    var layerSelects = document.querySelectorAll('select[id^="layerSelect"]');
    if (layerSelects.length === 0) {
        return; // 没有图层选择框，不需要加载
    }
    
    // 调用JSX脚本获取图层列表
    window.csInterface.evalScript('getLayerList()', function(result) {
        console.log('图层列表结果:', result); // 调试日志
        
        if (result && result.startsWith('SUCCESS:')) {
            try {
                // 解析成功结果
                var layerData = result.substring(8); // 去掉"SUCCESS:"
                var layers = layerData.split(';');
                
                // 为每个下拉框填充图层选项
                layerSelects.forEach(function(select) {
                    select.innerHTML = '<option value="">请选择图层</option>';
                    // 移除size、onfocus、onblur、onchange逻辑，保持原生下拉菜单体验
                    layers.forEach(function(layerStr) {
                        if (layerStr.trim()) {
                            var parts = layerStr.split('|');
                            if (parts.length >= 4) {
                                var option = document.createElement('option');
                                option.value = parts[0]; // 图层索引
                                var layerName = parts[1]; // 图层名称
                                var isVisible = parts[2] === '1'; // 可见性
                                var isLocked = parts[3] === '1'; // 锁定状态
                                var displayText = layerName;
                                if (!isVisible) displayText += ' (隐藏)';
                                if (isLocked) displayText += ' (锁定)';
                                option.textContent = displayText;
                                select.appendChild(option);
                            }
                        }
                    });
                });
            } catch (error) {
                console.error('解析图层列表失败:', error);
                layerSelects.forEach(function(select) {
                    select.innerHTML = '<option value="">解析图层列表失败</option>';
                });
            }
        } else if (result && result.startsWith('ERROR:')) {
            // 显示错误信息
            var errorMsg = result.substring(6); // 去掉"ERROR:"
            layerSelects.forEach(function(select) {
                select.innerHTML = '<option value="">' + errorMsg + '</option>';
            });
        } else {
            // 未知错误
            layerSelects.forEach(function(select) {
                select.innerHTML = '<option value="">获取图层列表失败</option>';
            });
        }
    });
}

// 初始化上传区域的交互逻辑
function initializeUploadInteractions() {
    // 批量为所有.upload-box下的input[type=file]和.upload-placeholder绑定点击事件
    var uploadBoxes = document.querySelectorAll('.upload-box');
    uploadBoxes.forEach(function(box) {
        var input = box.querySelector('input[type="file"]');
        var placeholder = box.querySelector('.upload-placeholder');
        if(input && placeholder) {
            placeholder.onclick = function() {
                input.click();
            };
            input.onchange = function(e) {
                var file = e.target.files[0];
                if(file) {
                    // 显示文件名或图片预览
                    if(placeholder.querySelector('img')) {
                        // 如果已有预览，替换
                        placeholder.querySelector('img').remove();
                    }
                    if(file.type.startsWith('image/')) {
                        var reader = new FileReader();
                        reader.onload = function(ev) {
                            placeholder.innerHTML = `<img src="${ev.target.result}" alt="预览" style="max-width:100%;max-height:80px;display:block;margin:auto;">`;
                        };
                        reader.readAsDataURL(file);
                    } else {
                        placeholder.innerText = file.name;
                    }
                }
            };
        }
    });
}

function showUploadPreview(file, container) {
    if(!file.type.startsWith('image/')) return;
    var reader = new FileReader();
    reader.onload = function(e) {
        container.innerHTML = `<img src="${e.target.result}" alt="预览" style="max-width:100%;max-height:80px;display:block;margin:auto;">`;
    };
    reader.readAsDataURL(file);
}

// 高级参数面板显示函数
function showAdvancePanel() {
    var container = document.getElementById('advancePanelContainer');
    // 判断是否为景观-现场出图（tab2，value=2）
    var tabIdx = 2;
    var select = document.getElementById('ps-select3');
    var isLandscapeScene = false;
    if(select && select.value === '2' && select.parentNode && select.parentNode.id === 'tab3-content') {
        isLandscapeScene = true;
    }
    if(container) {
        if(isLandscapeScene) {
            container.innerHTML = `<div class='ps-advance-panel' id='ps-advance-panel'>
                <div class='ps-advance-title'>参考图权重</div>
                <div class='ps-slider-row'>
                    <span class='ps-slider-label'>弱</span>
                    <input type='range' min='0' max='1' step='0.01' value='0.8' class='ps-slider' id='refWeightSlider'>
                    <span class='ps-slider-label'>强</span>
                    <input type='text' class='ps-slider-value' id='refWeightValue' value='0.8'>
                </div>
            </div>`;
        } else {
            container.innerHTML = `<div class='ps-advance-panel' id='ps-advance-panel'>
                <div class='ps-advance-title'>参考图权重</div>
                <div class='ps-slider-row'>
                    <span class='ps-slider-label'>弱</span>
                    <input type='range' min='0' max='1' step='0.01' value='0.8' class='ps-slider' id='refWeightSlider'>
                    <span class='ps-slider-label'>强</span>
                    <input type='text' class='ps-slider-value' id='refWeightValue' value='0.8'>
                </div>
                <div class='ps-advance-title'>控制开始时间</div>
                <div class='ps-slider-row'>
                    <span class='ps-slider-label'>弱</span>
                    <input type='range' min='0' max='1' step='0.01' value='0' class='ps-slider' id='startTimeSlider'>
                    <span class='ps-slider-label'>强</span>
                    <input type='text' class='ps-slider-value' id='startTimeValue' value='0'>
                </div>
                <div class='ps-advance-title'>控制结束时间</div>
                <div class='ps-slider-row'>
                    <span class='ps-slider-label'>弱</span>
                    <input type='range' min='0' max='1' step='0.01' value='1' class='ps-slider' id='endTimeSlider'>
                    <span class='ps-slider-label'>强</span>
                    <input type='text' class='ps-slider-value' id='endTimeValue' value='1'>
                </div>
            </div>`;
        }
        // 滑块联动
        var refSlider = document.getElementById('refWeightSlider');
        var refValue = document.getElementById('refWeightValue');
        if(refSlider && refValue) {
            refSlider.oninput = function(){ refValue.value = refSlider.value; };
            refValue.onchange = function(){
                let v = parseFloat(refValue.value);
                if(isNaN(v) || v < 0 || v > 1) { refValue.value = parseFloat(refSlider.value).toFixed(2); return; }
                v = Math.round(v * 100) / 100;
                refValue.value = v.toFixed(2);
                refSlider.value = v;
            };
            refValue.onkeydown = function(e){ if(e.key==='Enter'){ refValue.blur(); } };
        }
        var startSlider = document.getElementById('startTimeSlider');
        var startValue = document.getElementById('startTimeValue');
        if(startSlider && startValue) {
            startSlider.oninput = function(){ startValue.value = startSlider.value; };
            startValue.onchange = function(){
                let v = parseFloat(startValue.value);
                if(isNaN(v) || v < 0 || v > 1) { startValue.value = parseFloat(startSlider.value).toFixed(2); return; }
                v = Math.round(v * 100) / 100;
                startValue.value = v.toFixed(2);
                startSlider.value = v;
            };
            startValue.onkeydown = function(e){ if(e.key==='Enter'){ startValue.blur(); } };
        }
        var endSlider = document.getElementById('endTimeSlider');
        var endValue = document.getElementById('endTimeValue');
        if(endSlider && endValue) {
            endSlider.oninput = function(){ endValue.value = endSlider.value; };
            endValue.onchange = function(){
                let v = parseFloat(endValue.value);
                if(isNaN(v) || v < 0 || v > 1) { endValue.value = parseFloat(endSlider.value).toFixed(2); return; }
                v = Math.round(v * 100) / 100;
                endValue.value = v.toFixed(2);
                endSlider.value = v;
            };
            endValue.onkeydown = function(e){ if(e.key==='Enter'){ endValue.blur(); } };
        }
        }
}

// 双图高级参数面板显示函数
function showAdvancePanelForDualImage() {
    var container = document.getElementById('advancePanelContainer');
    if(container) {
        container.innerHTML = `<div class='ps-advance-panel' id='ps-advance-panel'>
            <div class='ps-advance-title'>参考图1权重</div>
            <div class='ps-slider-row'>
                <span class='ps-slider-label'>弱</span>
                <input type='range' min='0' max='1' step='0.01' value='0.8' class='ps-slider' id='refWeight1Slider'>
                <span class='ps-slider-label'>强</span>
                <input type='text' class='ps-slider-value' id='refWeight1Value' value='0.8'>
            </div>
            <div class='ps-advance-title'>参考图2权重</div>
            <div class='ps-slider-row'>
                <span class='ps-slider-label'>弱</span>
                <input type='range' min='0' max='1' step='0.01' value='0.8' class='ps-slider' id='refWeight2Slider'>
                <span class='ps-slider-label'>强</span>
                <input type='text' class='ps-slider-value' id='refWeight2Value' value='0.8'>
            </div>
        </div>`;
        // 滑块联动
        var ref1Slider = document.getElementById('refWeight1Slider');
        var ref1Value = document.getElementById('refWeight1Value');
        if(ref1Slider && ref1Value) {
            ref1Slider.oninput = function(){ ref1Value.value = ref1Slider.value; };
            ref1Value.onchange = function(){
                let v = parseFloat(ref1Value.value);
                if(isNaN(v) || v < 0 || v > 1) { ref1Value.value = parseFloat(ref1Slider.value).toFixed(2); return; }
                v = Math.round(v * 100) / 100;
                ref1Value.value = v.toFixed(2);
                ref1Slider.value = v;
            };
            ref1Value.onkeydown = function(e){ if(e.key==='Enter'){ ref1Value.blur(); } };
        }
        var ref2Slider = document.getElementById('refWeight2Slider');
        var ref2Value = document.getElementById('refWeight2Value');
        if(ref2Slider && ref2Value) {
            ref2Slider.oninput = function(){ ref2Value.value = ref2Slider.value; };
            ref2Value.onchange = function(){
                let v = parseFloat(ref2Value.value);
                if(isNaN(v) || v < 0 || v > 1) { ref2Value.value = parseFloat(ref2Slider.value).toFixed(2); return; }
                v = Math.round(v * 100) / 100;
                ref2Value.value = v.toFixed(2);
                ref2Slider.value = v;
            };
            ref2Value.onkeydown = function(e){ if(e.key==='Enter'){ ref2Value.blur(); } };
        }
    }
}

// 高级参数面板隐藏函数
function hideAdvancePanel() {
    var container = document.getElementById('advancePanelContainer');
    if(container) container.innerHTML = '';
}

// 绑定按钮事件函数
function bindButtonEvents() {
    // 获取并放大当前图层按钮逻辑
    var btnDup = document.getElementById('btnDuplicateScaleLayer');
    var resultDiv = document.getElementById('ps-dup-scale-result');
    if(btnDup && resultDiv && window.csInterface){
        btnDup.onclick = function(){
            var scale = prompt('请输入放大倍数（如2，默认2）','2') || '2';
            resultDiv.innerHTML = '正在复制并放大当前图层...';
            window.csInterface.evalScript('main(' + scale + ')', function(result){
                if(result && result.indexOf('success')===0){
                    resultDiv.innerHTML = '✅ ' + result;
                }else{
                    resultDiv.innerHTML = '❌ ' + result;
                }
            });
        };
    }
    
    // 导出当前图层为PNG按钮逻辑
    var btnExport = document.getElementById('btnExportCurrentLayer');
    var exportImportResult = document.getElementById('ps-export-import-result');
    if(btnExport && exportImportResult && window.csInterface){
        btnExport.onclick = function(){
            exportImportResult.innerHTML = '正在导出当前图层...';
            window.csInterface.evalScript('exportCurrentLayerToTemp()', function(result){
                if(result && !result.startsWith('error')){
                    exportImportResult.innerHTML = '✅ 已导出到: ' + result;
                }else{
                    exportImportResult.innerHTML = '❌ ' + result;
                }
            });
        };
    }
    
    // 插入图片为新图层按钮逻辑
    var btnImport = document.getElementById('btnImportImageToLayer');
    var importInput = document.getElementById('importImageInput');
    if(btnImport && importInput && exportImportResult && window.csInterface){
        btnImport.onclick = function(){
            importInput.value = '';
            importInput.click();
        };
        importInput.onchange = function(e){
            var file = e.target.files[0];
            if(file){
                // 兼容Windows路径分隔符
                var path = (file.path || file.name).replace(/\\/g, '/');
                exportImportResult.innerHTML = '正在插入图片...';
                window.csInterface.evalScript('importImageToNewLayer("' + path + '")', function(result){
                    if(result && result.indexOf('success')===0){
                        exportImportResult.innerHTML = '✅ ' + result;
                    }else{
                        exportImportResult.innerHTML = '❌ ' + result;
                    }
                });
            }
        };
    }
} 