function main(scale) {
    try {
        if (!scale) scale = 2;
        scale = parseFloat(scale);
        if (isNaN(scale) || scale <= 0) scale = 2;
        var doc = app.activeDocument;
        if (!doc) {
            return 'no document';
        }
        var bottomLayer = doc.layers[doc.layers.length - 1];
        var dupLayer = bottomLayer.duplicate();
        dupLayer.name = bottomLayer.name + '_copy';
        dupLayer.move(doc, ElementPlacement.PLACEATBEGINNING);
        dupLayer.resize(scale * 100, scale * 100, AnchorPosition.MIDDLECENTER);
        // 导出为PNG到桌面
        var desktopPath = Folder.desktop + '/最底层图层导出.png';
        // 只导出该图层
        for(var i=0; i<doc.layers.length; i++) {
            if(doc.layers[i] !== dupLayer) doc.layers[i].visible = false;
            else doc.layers[i].visible = true;
        }
        var file = new File(desktopPath);
        var opts = new PNGSaveOptions();
        opts.compression = 9;
        doc.saveAs(file, opts, true, Extension.LOWERCASE);
        // 恢复所有图层可见性
        for(var i=0; i<doc.layers.length; i++) { doc.layers[i].visible = true; }
        return 'success: 已复制最底层图层并放大' + scale + '倍，并导出为PNG到桌面';
    } catch (e) {
        return 'error: ' + e.message;
    }
}

// 导出当前图层为PNG到临时目录，返回文件路径
function exportCurrentLayerToTemp() {
    try {
        var doc = app.activeDocument;
        var layer = doc.activeLayer;
        var tempPath = Folder.temp + '/ps_export.png';
        // 只保留当前图层可见
        for(var i=0; i<doc.layers.length; i++) {
            doc.layers[i].visible = (doc.layers[i] === layer);
        }
        var file = new File(tempPath);
        var opts = new PNGSaveOptions();
        opts.compression = 9;
        doc.saveAs(file, opts, true, Extension.LOWERCASE);
        // 恢复可见性
        for(var i=0; i<doc.layers.length; i++) doc.layers[i].visible = true;
        return tempPath;
    } catch(e) {
        return 'error:' + e.message;
    }
}

// 将图片插入为新图层
function importImageToNewLayer(imgPath) {
    try {
        var file = new File(imgPath);
        app.open(file);
        var newDoc = app.activeDocument;
        newDoc.activeLayer.duplicate(app.documents[0], ElementPlacement.PLACEATBEGINNING);
        newDoc.close(SaveOptions.DONOTSAVECHANGES);
        return 'success';
    } catch(e) {
        return 'error:' + e.message;
    }
}

// 获取图层列表函数
function getLayerList() {
    try {
        // 检查是否有打开的文档
        if (app.documents.length === 0) {
            return "ERROR:没有打开的文档";
        }
        
        var doc = app.activeDocument;
        
        // 检查文档是否有图层
        if (doc.layers.length === 0) {
            return "ERROR:文档中没有图层";
        }
        
        // 构建图层列表字符串
        var result = "SUCCESS:";
        for (var i = 0; i < doc.layers.length; i++) {
            var layer = doc.layers[i];
            var layerInfo = i + "|" + layer.name + "|" + (layer.visible ? "1" : "0") + "|" + (layer.locked ? "1" : "0");
            if (i > 0) result += ";";
            result += layerInfo;
        }
        
        return result;
        
    } catch (error) {
        return "ERROR:获取图层列表时出错: " + error.message;
    }
}

// 测试函数 - 用于调试
function testGetLayerList() {
    return getLayerList();
}

// 简单测试函数
function simpleTest() {
    try {
        if (app.documents.length > 0) {
            var doc = app.activeDocument;
            return "文档名称: " + doc.name + ", 图层数量: " + doc.layers.length;
        } else {
            return "没有打开的文档";
        }
    } catch (e) {
        return "错误: " + e.message;
    }
} 