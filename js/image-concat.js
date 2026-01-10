// custom_nodes/ImageConcat/image-Concat.js
import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";
console.log("✅ [ImageConcatNode] V1.0 QQ:2540968810");
// 为ImageConcatNode添加文件夹选择按钮
app.registerExtension({
    name: "Comfy.ImageConcatNode",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 匹配英文版本的Concat节点类名
        if (nodeData.name === "ImageConcatNode") {
            // 保存原始的addWidget方法
            const origAddWidget = nodeType.prototype.addWidget;
            
            // 重写addWidget方法
            nodeType.prototype.addWidget = function (type, name, value, callback, options) {
                // 调用原始方法创建控件
                const widget = origAddWidget.call(this, type, name, value, callback, options);
                
                // 只处理image_dir参数（英文节点的参数名保持不变）
                if (name === "image_dir" && type === "STRING") {
                    // 兼容不同版本的Widget DOM元素
                    let inputElement = null;
                    if (widget.inputEl) {
                        inputElement = widget.inputEl; // 旧版本
                    } else if (widget.element) {
                        inputElement = widget.element; // 新版本
                    } else {
                        // 兜底：查找输入框
                        inputElement = widget.parentEl?.querySelector("input") || widget.domElement?.querySelector("input");
                    }

                    if (inputElement) {
                        // 创建选择文件夹按钮（英文文本适配）
                        const btn = document.createElement("button");
                        btn.textContent = "Select Folder";
                        btn.style.marginLeft = "8px";
                        btn.style.padding = "2px 8px";
                        btn.style.fontSize = "12px";
                        btn.style.cursor = "pointer";
                        btn.style.border = "1px solid #ccc";
                        btn.style.borderRadius = "4px";
                        btn.style.backgroundColor = "#f5f5f5";
                        btn.style.color = "#333";
                        
                        // 按钮hover效果
                        btn.addEventListener("mouseover", () => {
                            btn.style.backgroundColor = "#e0e0e0";
                        });
                        btn.addEventListener("mouseout", () => {
                            btn.style.backgroundColor = "#f5f5f5";
                        });

                        // 按钮点击事件（兼容Electron和浏览器）
                        btn.addEventListener("click", async () => {
                            try {
                                // 方案1：Electron环境（ComfyUI桌面版）
                                if (window.electronAPI?.showOpenDialog) {
                                    const result = await window.electronAPI.showOpenDialog({
                                        properties: ['openDirectory'],
                                        title: "Select Image Folder" // 英文标题
                                    });
                                    if (!result.canceled && result.filePaths.length > 0) {
                                        const path = result.filePaths[0];
                                        // 更新widget值和输入框
                                        widget.value = path;
                                        if (typeof callback === "function") {
                                            callback(path);
                                        }
                                        inputElement.value = path;
                                        // 触发输入框change事件（确保节点感知到值变化）
                                        inputElement.dispatchEvent(new Event('change'));
                                    }
                                } 
                                // 方案2：浏览器环境（有限支持）
                                else if (window.showDirectoryPicker) {
                                    const dirHandle = await window.showDirectoryPicker({
                                        startIn: 'desktop',
                                        id: 'image-Concat-folder-picker',
                                        title: "Select Image Folder"
                                    });
                                    if (dirHandle) {
                                        // 处理路径格式
                                        let path = dirHandle.name;
                                        try {
                                            // 部分浏览器支持获取完整路径
                                            path = dirHandle.path || path;
                                        } catch (e) {
                                            alert("Browser does not support full path access. Please enter the path manually.");
                                        }
                                        widget.value = path;
                                        if (typeof callback === "function") {
                                            callback(path);
                                        }
                                        inputElement.value = path;
                                        inputElement.dispatchEvent(new Event('change'));
                                    }
                                } else {
                                    // 不支持的环境提示
                                    alert("Folder selection is not supported in this environment. Please enter the path manually (e.g., /home/user/images or C:\\images).");
                                }
                            } catch (e) {
                                console.warn("ImageConcat Extension - Folder selection failed:", e);
                                alert("Failed to select folder: " + e.message);
                            }
                        });

                        // 将按钮添加到输入框旁边
                        inputElement.parentNode.appendChild(btn);
                    }
                }

                return widget;
            };
        }
    },
    async nodeCreated(node) {
        // 移除不存在的方法调用，修复报错
        if (node.comfyClass === "ImageConcatNode") {
            console.log("✅ ImageConcatNode initialized successfully");
        }
    },
    async setup() {
        console.log("✅ [ImageConcat Extension( V1.0)] Initialized successfully");
    }
});