#!/bin/bash

# AI任务自动化测试平台 - GitHub推送脚本
# 使用方法: ./push_to_github.sh YOUR_GITHUB_USERNAME

if [ $# -eq 0 ]; then
    echo "❌ 错误: 请提供您的GitHub用户名"
    echo "使用方法: ./push_to_github.sh YOUR_GITHUB_USERNAME"
    echo "示例: ./push_to_github.sh john-doe"
    exit 1
fi

USERNAME=$1
REPO_NAME="ai-task-testing-platform"

echo "🚀 开始推送AI任务自动化测试平台到GitHub..."
echo "📁 仓库: https://github.com/$USERNAME/$REPO_NAME"
echo ""

# 检查是否已经添加了remote
if git remote get-url origin > /dev/null 2>&1; then
    echo "⚠️  检测到已存在的remote origin，正在移除..."
    git remote remove origin
fi

# 添加GitHub remote
echo "🔗 添加GitHub remote..."
git remote add origin https://github.com/$USERNAME/$REPO_NAME.git

# 重命名分支为main
echo "🌿 重命名分支为main..."
git branch -M main

# 推送到GitHub
echo "📤 推送代码到GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 成功推送到GitHub!"
    echo "🌐 访问您的仓库: https://github.com/$USERNAME/$REPO_NAME"
    echo "📖 查看README: https://github.com/$USERNAME/$REPO_NAME/blob/main/README.md"
    echo "🎯 演示文档: https://github.com/$USERNAME/$REPO_NAME/blob/main/DEMO.md"
else
    echo ""
    echo "❌ 推送失败，请检查："
    echo "1. GitHub仓库是否已创建"
    echo "2. 用户名是否正确"
    echo "3. 是否有推送权限"
    echo "4. 网络连接是否正常"
fi