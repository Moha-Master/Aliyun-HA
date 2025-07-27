# Home Assistant 阿里云账单与流量集成

这是一个 Home Assistant 自定义集成，用于查询和实时显示阿里云当月账单与公网流量使用情况。

## 功能特性

*   **当月账单总额**：实时显示阿里云账户当月总账单金额。
*   **当月公网流量消耗**：实时显示当月公网流量（出方向）的使用量。
*   **账单项目明细**：显示当月账单中各项服务的费用明细。

## 安装

本集成支持通过 HACS (Home Assistant Community Store) 进行安装。

1.  **添加自定义仓库**：
    *   打开 Home Assistant。
    *   进入 HACS。
    *   点击右上角的三个点，选择 "Custom repositories"。
    *   在 "Repository" 字段中粘贴本 Git 仓库的 URL。
    *   在 "Category" 中选择 "Integration"。
    *   点击 "ADD"。
2.  **搜索并安装**：
    *   在 HACS 中，进入 "Integrations" 页面。
    *   点击右下角的 "EXPLORE & DOWNLOAD REPOSITORIES"。
    *   搜索 "Aliyun Billing" 或 "阿里云"。
    *   点击找到的集成，然后点击 "DOWNLOAD" 进行安装。
3.  **重启 Home Assistant**：安装完成后，请重启 Home Assistant 以加载新的集成。

## 配置

本集成需要一个具有账单浏览权限的阿里云 RAM 用户。

1.  **创建阿里云 RAM 用户并授权**：
    *   登录阿里云控制台。
    *   进入 **RAM 访问控制**。
    *   在左侧导航栏选择 **用户** > **创建用户**。
    *   设置登录名称和显示名称，勾选 **为该用户自动生成AccessKey**。
    *   创建成功后，请务必保存好 **AccessKey ID** 和 **AccessKey Secret**，它们只显示一次。
    *   为新创建的 RAM 用户授权：
        *   在用户详情页，点击 **添加权限**。
        *   搜索并选择 `AliyunBSSFullAccess` 或 `AliyunBSSReadOnlyAccess` (推荐使用 `AliyunBSSReadOnlyAccess` 以最小化权限)。
        *   点击 **确定** 完成授权。
2.  **在 Home Assistant 中添加集成**：
    *   重启 Home Assistant 后，进入 **设置** > **设备与服务**。
    *   点击右下角的 **添加集成**。
    *   搜索 "Aliyun" 或 "阿里云"。
    *   按照提示输入您在步骤 1 中获取的 **AccessKey ID** 和 **AccessKey Secret**。
    *   完成配置后，系统将自动生成多个 `sensor` 实体，显示阿里云当月账单总额、当月公网流量消耗以及当月账单各项目费用。

## 传感器实体

集成成功后，将生成以下类型的传感器实体：

*   `sensor.aliyun_total_bill`：当月账单总额。
*   `sensor.aliyun_public_network_traffic`：当月公网流量消耗。
*   `sensor.aliyun_bill_item_xxx`：各项服务（如 ECS、RDS 等）的当月费用。

---
