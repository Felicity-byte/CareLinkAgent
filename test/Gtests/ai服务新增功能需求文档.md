````
我需要修改我的医疗病历生成代码，请帮我实现以下功能：

## 现有情况
- 我已经有一个函数可以调用 glm-4.7-flash 生成结构化病历（输入是医患对话文本，输出是病历JSON）
- 这部分代码已经能正常工作

## 需要新增的功能：图片分析 + 交互确认 + 图片本地存储

### 核心设计思路
当患者发送伤口图片时：
1. 保存图片到本地（自定义存储路径）
2. AI分析图片（glm-4v-flash）
3. 生成确认问题向患者提问
4. 患者回答问题
5. 结合图片分析+患者回答生成最终伤口评估
6. 将图片URL、图片分析结果、伤口评估融合到结构化病历中


## 提示词1：图片分析（调用 glm-4v-flash）

```markdown
你是一名专业的术后伤口分析助手。请分析这张伤口照片，输出JSON格式：

{
    "image_valid": true/false,
    "invalid_reason": "如果无效，说明原因（如：图片模糊、不是伤口部位、无法识别等）",
    "preliminary_analysis": {
        "suspected_body_part": "可能的身体部位（如：左膝、腹部，可多个）",
        "suspected_body_part_confidence": "高/中/低",
        "visible_features": ["可见特征1", "可见特征2"],
        "uncertain_items": ["不确定的项目1", "不确定的项目2"]
    },
    "questions_to_confirm": [
        {
            "question": "请问这张照片拍的是哪个部位？",
            "reason": "无法确定具体部位，需要患者确认"
        },
        {
            "question": "伤口是什么时候开始出现的？",
            "reason": "需要了解病程时间"
        },
        {
            "question": "目前伤口有没有疼痛感？疼痛程度如何（0-10分）？",
            "reason": "需要评估疼痛情况"
        }
    ]
}
````

## **提示词2：患者回答后综合评估（调用 glm-4.7-flash）**

markdown

```
你是一名专业的术后伤口评估助手。请结合以下信息，输出最终的伤口评估结果。

【图片初步分析】
{preliminary_analysis}

【患者确认信息】
{patient_answers}

请输出JSON格式：
{
    "confirmed_body_part": "患者确认的部位",
    "wound_assessment": {
        "location": "最终确定的部位",
        "onset_time": "患者描述的起病时间",
        "pain_score": "疼痛评分（如有）",
        "pain_description": "疼痛描述",
        "appearance": "结合图片和患者描述的外观",
        "exudate": "渗液情况（无/少量/中量/大量/无法判断）",
        "surrounding_skin": "周围皮肤情况（正常/红肿/发热/皮疹）",
        "inflammation_signs": ["红肿", "发热", "化脓"]
    },
    "healing_status": "正常/缓慢/需关注/无法判断",
    "risk_alerts": ["风险提示1", "风险提示2"],
    "recommendation": "建议措施",
    "missing_info": "仍缺失的关键信息（如有）",
    "suggest_next_question": "如需进一步确认，建议追问的问题"
}
```

## **提示词3：融合到结构化病历（调用 glm-4.7-flash）**

markdown

```
你是一名医疗病历整合助手，请将以下信息融合到结构化病历中。

【原有病历】
{original_report}

【伤口评估结果】
{wound_assessment}

【患者原始图片】
{image_url}

【融合规则】
1. 保留原有病历的所有字段
2. 新增字段 "images"，类型为数组，存放本次上传的所有图片信息，每张图片包含：
   - "url": 图片存储的相对路径
   - "absolute_path": 图片存储的绝对路径（可选）
   - "upload_time": 上传时间
   - "image_type": "伤口照片"
   - "analysis": 对应的图片分析结果（可选）
3. 新增字段 "wound_assessment"，存放伤口评估结果
4. 将伤口评估中的关键信息追加到 "present_illness" 字段
5. 将风险提示追加到 "advice" 字段，标注【AI辅助提示】
6. 输出完整的融合后JSON
```

## **需要实现的代码**

### **1. 图片本地存储管理器**

python

```
import os
import base64
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

class ImageStorage:
    """图片本地存储管理器"""
    
    def __init__(self, base_path: str = "./medical_images"):
        """
        初始化
        :param base_path: 自定义存储根目录，可通过配置文件设置
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_image(self, image_base64: str, session_id: str, image_type: str = "wound") -> dict:
        """
        保存图片到本地
        :return: 包含相对路径、绝对路径、文件名的字典
        """
        # 按日期创建子目录
        date_path = self.base_path / datetime.now().strftime("%Y-%m-%d")
        date_path.mkdir(exist_ok=True)
        
        # 按会话创建子目录
        session_path = date_path / f"session_{session_id}"
        session_path.mkdir(exist_ok=True)
        
        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}.jpg"
        file_path = session_path / filename
        
        # 解码并保存
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        image_data = base64.b64decode(image_base64)
        
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # 获取文件大小
        file_size = file_path.stat().st_size
        
        return {
            "url": str(file_path.relative_to(self.base_path)),  # 相对路径，存数据库
            "absolute_path": str(file_path.absolute()),         # 绝对路径
            "filename": filename,
            "file_size": file_size,
            "upload_time": datetime.now().isoformat()
        }
```

### **2. 图片分析服务**

python

```
class WoundAnalysisService:
    def __init__(self, api_key: str, image_storage: ImageStorage):
        self.client = ZhipuAI(api_key=api_key)
        self.image_storage = image_storage
    
    async def process_patient_image(self, image_base64: str, session_id: str) -> dict:
        """
        处理患者上传的图片
        步骤1: 保存图片
        步骤2: AI分析图片
        步骤3: 返回确认问题
        """
        # 保存图片
        image_info = self.image_storage.save_image(image_base64, session_id, "wound")
        
        # 调用 glm-4v-flash 分析图片
        analysis = await self._analyze_image(image_base64)
        
        # 保存待确认信息到会话
        pending_data = {
            "image_info": image_info,
            "preliminary_analysis": analysis.get("preliminary_analysis"),
            "questions": analysis.get("questions_to_confirm", [])
        }
        await self._save_pending_analysis(session_id, pending_data)
        
        return {
            "need_confirmation": True,
            "image_url": image_info["url"],
            "questions": analysis.get("questions_to_confirm", []),
            "preliminary_findings": analysis.get("preliminary_analysis")
        }
    
    async def process_patient_answers(self, session_id: str, user_answers: dict) -> dict:
        """
        处理患者的确认回答
        步骤1: 获取之前保存的初步分析
        步骤2: 结合患者回答生成最终评估
        步骤3: 融合到结构化病历
        """
        # 获取待确认信息
        pending = await self._get_pending_analysis(session_id)
        
        # 调用 glm-4.7-flash 综合评估
        wound_assessment = await self._generate_assessment(
            pending["preliminary_analysis"], 
            user_answers
        )
        
        # 获取原有病历
        original_report = await self._get_existing_report(session_id)
        
        # 融合到结构化病历
        final_report = await self._merge_to_report(
            original_report, 
            wound_assessment, 
            pending["image_info"]
        )
        
        return final_report
```

### **3. 配置文件示例（config.yaml）**

yaml

```
storage:
  # 图片存储根目录（可自定义）
  image_base_path: "D:/medical_data/wound_images"  # Windows
  # image_base_path: "/var/www/medical_data/wound_images"  # Linux
  max_file_size_mb: 10
  allowed_formats: [".jpg", ".jpeg", ".png"]
  
zhipuai:
  api_key: "your-api-key"
  timeout: 30
```

## **容错处理要求**

代码中需要实现以下容错：

1. **图片无效时**：返回明确提示，不继续提问流程
2. **部位识别失败时**：`suspected_body_part` 设为"无法确定"，置信度为"低"
3. **API调用失败时**：捕获异常，返回降级结果，不影响原有病历生成
4. **超时处理**：图片分析设置30秒超时
5. **存储路径权限不足**：抛出明确错误提示
6. **磁盘空间不足**：检查并提示

## **结构化病历最终输出示例**

json

```
{
    "session_id": "sess_123456",
    "present_illness": "患者术后第3天，左膝伤口... 伤口情况：左膝可见一约3cm切口，周围皮肤轻微红肿",
    "symptoms": ["伤口疼痛"],
    "vital_signs": {},
    "medications": [],
    "advice": "保持伤口清洁干燥。【AI辅助提示】建议关注伤口红肿情况，如加重请及时就医",
    "images": [
        {
            "url": "2026-04-07/session_sess_123456/abc123def456.jpg",
            "absolute_path": "D:/medical_data/wound_images/2026-04-07/session_sess_123456/abc123def456.jpg",
            "upload_time": "2026-04-07T14:30:00",
            "image_type": "伤口照片",
            "analysis": {
                "confirmed_body_part": "左膝",
                "healing_status": "正常",
                "risk_alerts": []
            }
        }
    ],
    "wound_assessment": {
        "confirmed_body_part": "左膝",
        "wound_assessment": {
            "location": "左膝",
            "appearance": "约3cm切口，边缘整齐，周围皮肤轻微红肿",
            "exudate": "无",
            "inflammation_signs": ["红肿"]
        },
        "healing_status": "正常",
        "risk_alerts": [],
        "recommendation": "保持清洁干燥，定期换药"
    }
}
```

## **数据库表设计建议**

sql

```
-- 图片表（单独存储，与病历解耦）
CREATE TABLE medical_images (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    file_path VARCHAR(500) NOT NULL,      -- 相对路径
    absolute_path VARCHAR(500),            -- 绝对路径（可选）
    file_name VARCHAR(200),
    file_size INT,
    upload_time DATETIME,
    image_type VARCHAR(50),                -- "wound", "medical_record"
    analysis_result JSON,                  -- 图片分析结果
    INDEX idx_session_id (session_id)
);
```

请基于以上需求给出完整的代码修改方案，包括：

1. 完整的 `ImageStorage` 类
2. 完整的 `WoundAnalysisService` 类
3. 与现有病历生成代码的集成方式
4. 配置文件读取逻辑

<br />

检查一下ai服务中关于 `d:\Trea\medical systems\CareLinkAgent\xdocs\ai服务新增功能需求文档.md` 所提到的功能是否实现完整，是否还有bug和代码逻辑问题
